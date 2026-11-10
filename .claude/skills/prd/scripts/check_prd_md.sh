#!/bin/bash
# PRD md 自检（内容扫描 + 截图存在性 / freshness + CJK 标点，FAIL/WARN 分级）
# 完整用法说明：bash check_prd_md.sh -h

usage() {
    cat <<'EOF'
PRD md 自检：只查会把文档弄坏的硬错（占位符 / Confluence 渲染 / 埋点表 /
文档结构 / 截图 / CJK 标点），写法不管。
交付 / 推 Confluence 前手动跑完整形态；写入时的增量检查由 prd-content-gate 承担
（hook_check_prd_content.py，维度与本脚本同源，只查本次新增行）。

用法：
    bash .claude/skills/prd/scripts/check_prd_md.sh <prd.md> [--skeleton]

示例：
    bash .claude/skills/prd/scripts/check_prd_md.sh projects/<活动线>/deliverables/<季度>/<版本>/prd-<活动>-<版本>.md
    bash .claude/skills/prd/scripts/check_prd_md.sh projects/<产品线>/deliverables/<季度>/<版本>/prd-<产品线>-<版本>.md
    bash .claude/skills/prd/scripts/check_prd_md.sh projects/{项目}/deliverables/prd-{简称}-v{N}.md --skeleton

参数：
    <prd.md>    必填。PRD md 路径（baseline / delta / 12 章 PRD 均可）。
                profile 按文件名判：prd-*-baseline.md 走 baseline 豁免集，其余按 delta
    --skeleton  骨架阶段模式：占位符残留从 FAIL 降 WARN、跳过截图存在性与 freshness 检查。
                缺省（不带）= 完整检查

前置：
    - <prd.md> 存在
    - 同目录 screenshot_for_prd.py / humanize/{md_scan,patterns}.py、
      仓库根 scripts/check_cjk_punct.py（check_cjk_punct 缺失时该项跳过并报 ⚠）
    - 环境逃生阀：SKIP_PRD_STRUCT_GATE=1 跳过文档结构维（章节完整性 + 渲染卫生，确非误报时用）
    - --help 本身无前置

退出码：
    0 — 全部通过（仅剩 WARN 也算通过：WARN 只提示不阻断）
    2 — 有 FAIL 级命中 / 文件不存在
EOF
    exit 0
}

case "${1:-}" in
    -h|--help) usage ;;
esac

# 不用 set -e：bash 3.2 在 heredoc / 中文路径下 set -e 会提前退出导致最终 exit code 不准
set -uo pipefail

# skill-log: 完成率埋点（EXIT trap）
_SL_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
source "$_SL_ROOT/.claude/hooks/lib/log.sh" 2>/dev/null
_cleanup() {
    _rc=$?
    log_event skill "prd" "$([ $_rc -eq 0 -o $_rc -eq 2 ] && echo completed || echo failed)" "fail_total=${fail:-0}" 2>/dev/null
}
trap _cleanup EXIT

fail=0
PY_EXIT=0
IMG_EXIT=0

FILE="${1:?用法: bash check_prd_md.sh <prd.md> [--skeleton]（-h 看完整说明）}"
SKELETON_MODE=0
shift
for arg in "$@"; do
    case "$arg" in
        --skeleton) SKELETON_MODE=1 ;;
    esac
done

if [ ! -f "$FILE" ]; then
    echo "❌ 文件不存在：${FILE}" >&2
    exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# ── profile 判定：baseline（living 全量真相）vs delta（单轮迭代，默认）──
# baseline 存量豁免引用块 / 埋点平台两维（历史 living 文档）。
PROFILE="delta"
case "$(basename "$FILE")" in
    prd-*-baseline.md) PROFILE="baseline" ;;
esac
echo "=========================================="
echo "  PRD md 自检: $(basename "$FILE")  [profile: $PROFILE]"
echo "=========================================="

# ── 1. md_scan：硬错 ─────────────
echo
echo "── 1. 内容扫描（硬错）──"
python3 - "$FILE" "$SCRIPT_DIR" "$SKELETON_MODE" "$PROFILE" <<'PY' || PY_EXIT=$?
import sys
sys.path.insert(0, sys.argv[2])
SKELETON = sys.argv[3] == '1'
PROFILE = sys.argv[4] if len(sys.argv) > 4 else 'delta'
from humanize.md_scan import scan_prd_structural_md
from humanize.patterns import prd_fail_keys, prd_warn_keys

md = open(sys.argv[1], encoding='utf-8').read()
merged = scan_prd_structural_md(md)

# 维度清单唯一真源 = humanize/patterns.py（hook 侧新门 / fuzz 测试共用同一份），
# 此处只按本次运行条件取子集，不再维护清单副本。
fail_keys = prd_fail_keys(skeleton=SKELETON, profile=PROFILE)
warn_keys = prd_warn_keys(skeleton=SKELETON)
fail_total = 0
warn_total = 0

for key, label in fail_keys:
    hits = merged.get(key, [])
    if hits:
        fail_total += len(hits)
        print(f'  ❌ {label}（{len(hits)}）')
        for h in hits[:5]:
            print(f'     - {h}')
        if len(hits) > 5:
            print(f'     ... +{len(hits) - 5}')

for key, label in warn_keys:
    hits = merged.get(key, [])
    if hits:
        warn_total += len(hits)
        print(f'  ⚠️  {label}（{len(hits)}）')
        for h in hits[:3]:
            print(f'     - {h}')
        if len(hits) > 3:
            print(f'     ... +{len(hits) - 3}')

print()
print(f'  → 场景数（实际数到 ## N.x A-y · ...）：{merged["scene_count_observed"]}')
print(f'  → FAIL 总数：{fail_total}')
print(f'  → WARN 总数：{warn_total}')

sys.exit(2 if fail_total > 0 else 0)
PY
PY_EXIT="${PY_EXIT:-0}"
if [ "$PY_EXIT" -ne 0 ]; then fail=1; fi

# ── 1.7 文档结构：章节完整性 + 渲染卫生（FAIL）──────────
# 拦两类「写坏但内容扫描全绿」的坏法：
#   ① 文档被脚本写残（整段章节丢失）——按头部「迭代档位」判定 delta 后查必备章节号
#   ② 渲染卫生——标题前缺空行（紧跟 HTML 块会被吞进块内、不再当标题渲染）、<td> 内空行
#      （Confluence 截断 HTML 块 → 表格花屏）
echo
echo "── 1.7. 文档结构（完整性 + 渲染卫生）──"
STRUCT_EXIT=0
if [ "${SKIP_PRD_STRUCT_GATE:-0}" = "1" ]; then
    echo "  → SKIP_PRD_STRUCT_GATE=1，跳过"
else
python3 - "$FILE" "$SCRIPT_DIR" "$REPO_ROOT" "$SKELETON_MODE" <<'PY' || STRUCT_EXIT=$?
import sys
sys.path.insert(0, sys.argv[2])
from humanize.prd_struct_scan import previous_version, scan_structure

text = open(sys.argv[1], encoding='utf-8').read()
prev = None if sys.argv[4] == '1' else previous_version(sys.argv[3], sys.argv[1])
problems, warns = scan_structure(text, prev)

for w in warns:
    print(f'  ⚠️  {w}')
if problems:
    for p in problems[:10]:
        print(f'  ❌ {p}')
    if len(problems) > 10:
        print(f'  ... +{len(problems) - 10}')
    print(f'  → 共 {len(problems)} 处')
    sys.exit(2)
if not warns:
    print('  ✓ 章节与上一版一致、渲染卫生无命中')
PY
fi
if [ "$STRUCT_EXIT" -ne 0 ]; then fail=1; fi

# ── 2. 截图存在性（委托 Python，避免 bash + 中文路径 quirk）──
echo
echo "── 2. 截图存在性 ──"
# references/ 下的模板文件跳过（模板 demo 图片本就不存在，PM 用时会替换）
# skeleton 模式（骨架阶段）也跳过 —— PM 还没做截图
SKIP_IMG=0
case "$FILE" in
    *references/*) echo "  → 模板文件，跳过截图检查"; SKIP_IMG=1 ;;
esac
if [ "$SKELETON_MODE" -eq 1 ]; then
    echo "  → skeleton 模式，跳过截图检查（PM 填完前先做截图）"
    SKIP_IMG=1
fi
if [ "$SKIP_IMG" -eq 0 ]; then
python3 - "$FILE" <<'PY' || IMG_EXIT=$?
import os, re, sys
from pathlib import Path

prd_path = Path(sys.argv[1])
md_files = [prd_path]

img_re = re.compile(r'!\[[^\]]*\]\((\.{1,2}/assets/[^)]+)\)')
total = 0
missing = []
prd_dir = prd_path.parent

for md in md_files:
    text = md.read_text(encoding='utf-8')
    for m in img_re.finditer(text):
        rel = m.group(1)
        total += 1
        full = prd_dir / rel
        if not full.exists():
            missing.append((rel, md.name))

print(f'  → 总图片数：{total}，缺失：{len(missing)}')
for rel, mname in missing[:10]:
    print(f'  ❌ 缺失：{rel}（在 {mname}）')
if len(missing) > 10:
    print(f'  ... +{len(missing) - 10}')

sys.exit(2 if missing else 0)
PY
IMG_EXIT="${IMG_EXIT:-0}"
if [ "$IMG_EXIT" -ne 0 ]; then fail=1; fi
fi  # SKIP_IMG

# ── 2.5 截图 freshness（v2：按 .flow DOM 子树 hash；缺 .freshness.json 降级 mtime）──
# 同样跳过 references/ 模板和 skeleton 模式（PM 还没截图）
echo
echo "── 2.5. 截图 freshness ──"
FRESH_EXIT=0
if [ "$SKIP_IMG" -eq 1 ]; then
    echo "  → 跳过（同截图存在性的跳过规则）"
else
    PRD_DIR="$(dirname "$FILE")"
    ASSETS_DIR="$PRD_DIR/assets"
    if [ ! -d "$ASSETS_DIR" ] || [ -z "$(find "$ASSETS_DIR" -maxdepth 1 -name '*.png' -print -quit 2>/dev/null)" ]; then
        echo "  → assets/ 为空，跳过"
    else
        # 委托 Python discover_source_html（合并 prototype + IMAP 候选，取 mtime 最新）
        SOURCE_HTML=$(python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from screenshot_for_prd import discover_source_html
r = discover_source_html('$PRD_DIR')
print(r if r else '')
" 2>/dev/null)

        if [ -z "$SOURCE_HTML" ]; then
            echo "  → 未找到源 HTML（*原型*.html / *交互大图*.html），跳过"
        else
            echo "  → 源 HTML: $(basename "$SOURCE_HTML")"
            python3 "$SCRIPT_DIR/screenshot_for_prd.py" --assert-fresh \
                --source "$SOURCE_HTML" --assets "$ASSETS_DIR" 2>&1 || FRESH_EXIT=$?
            if [ "$FRESH_EXIT" -eq 0 ]; then
                echo "  ✓ 截图 fresh"
            fi
        fi
    fi
fi
if [ "$FRESH_EXIT" -ne 0 ]; then fail=1; fi

# ── 3. CJK 标点（strict）────────────────────────────
echo
echo "── 3. CJK 标点检查（strict）──"
PUNCT_CHECKER="$REPO_ROOT/scripts/check_cjk_punct.py"
if [ -f "$PUNCT_CHECKER" ]; then
    if ! python3 "$PUNCT_CHECKER" "$FILE" --strict; then
        fail=1
    fi
else
    echo "  ⚠️  check_cjk_punct.py 不存在（跳过）"
fi

# ── 总结 ─────────────────────────────────────────────
echo
echo "=========================================="
if [ "$fail" -eq 0 ]; then
    echo "  ✅ 全部检查通过"
    exit 0
else
    echo "  ❌ 检查未通过 (fail=${fail})"
    exit 2
fi
