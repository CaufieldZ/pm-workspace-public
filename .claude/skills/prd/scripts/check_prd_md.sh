#!/bin/bash
# PRD md 自检脚本（对等 check_prd.sh 但只跑 md 路径）
# 用法: bash check_prd_md.sh <prd.md> [scene-list.md]
#
# split 模式：自动检测 {stem}-scenes/ 子目录，先 prd_compose 拼成完整 md 再扫
# scene-list 可选：缺省时从 PRD 第 2.1 表自动数

# 不用 set -e：bash 3.2 在 heredoc / 中文路径下 set -e 会提前退出导致最终 exit code 不准
set -uo pipefail

# skill-log: 完成率埋点 + tmpfile 清理（合并进一个 EXIT trap，避免后注册的 trap 覆盖前者）
_SL_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
source "$_SL_ROOT/.claude/hooks/lib/log.sh" 2>/dev/null
TMPFILE=""
_cleanup() {
    _rc=$?
    [ -n "$TMPFILE" ] && rm -f "$TMPFILE" "${TMPFILE%.md}"
    log_event skill "prd" "$([ $_rc -eq 0 -o $_rc -eq 2 ] && echo completed || echo failed)" "fail_total=${fail:-0}" 2>/dev/null
}
trap _cleanup EXIT

fail=0
PY_EXIT=0
IMG_EXIT=0

FILE="${1:?用法: bash check_prd_md.sh <prd.md> [--skeleton]}"
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
# baseline 合法用 §X.Y 具名锚点（单文件内可跳）+ 模块树按场景编号索引，
# 这两类对 delta 是 FAIL（split 跨页死链 / 裸编号），对 baseline 是设计模式 → 豁免。
PROFILE="delta"
case "$(basename "$FILE")" in
    prd-*-baseline.md) PROFILE="baseline" ;;
esac
echo "=========================================="
echo "  PRD md 自检: $(basename "$FILE")  [profile: $PROFILE]"
echo "=========================================="

# ── 0. 模式判定 + compose ────────────────────────────
STEM="${FILE%.md}"
SCENES_DIR="${STEM}-scenes"
COMPOSED_FILE="$FILE"
IS_SPLIT=0  # 死链 / 裸编号风险只在 split（多文件拼接，§X.Y 跨页失效），单文件 delta 内跳合法

if [ -d "$SCENES_DIR" ]; then
    IS_SPLIT=1
    echo "→ split 模式（子目录：$(basename "$SCENES_DIR")）"
    TMPFILE="$(mktemp).md"
    if ! python3 "$SCRIPT_DIR/prd_compose.py" "$FILE" -o "$TMPFILE" 2>&1; then
        echo "❌ compose 失败"
        exit 2
    fi
    COMPOSED_FILE="$TMPFILE"
    LINE_COUNT=$(wc -l < "$COMPOSED_FILE" | tr -d ' ')
    echo "→ 拼接后 ${LINE_COUNT} 行"
else
    echo "→ single 模式"
fi

# ── 1. md_scan：human voice + structural ─────────────
echo
echo "── 1. 内容扫描（讲人话 + 结构）──"
python3 - "$COMPOSED_FILE" "$SCRIPT_DIR" "$SKELETON_MODE" "$PROFILE" "$IS_SPLIT" <<'PY' || PY_EXIT=$?
import sys, os
sys.path.insert(0, sys.argv[2])
SKELETON = sys.argv[3] == '1'
PROFILE = sys.argv[4] if len(sys.argv) > 4 else 'delta'
IS_SPLIT = len(sys.argv) > 5 and sys.argv[5] == '1'
from humanize.md_scan import scan_human_voice_md, scan_prd_structural_md

md = open(sys.argv[1], encoding='utf-8').read()
voice = scan_human_voice_md(md)
struct = scan_prd_structural_md(md)

# FAIL 级（命中即阻断；--skeleton 模式下 placeholders 降级到 WARN）
fail_keys = [
    ('date_tag_hits', '流水账日期 / 版本标记'),
    ('zombie_heading_hits', '僵尸 heading（应物理删除）'),
    ('v_tag_heading_hits', 'heading 含 V 版本流水'),
    ('tech_field_hits', '5 段式禁用研发字段（触发/读/写/事件/API）'),
    ('circle_nums', '圈数字 ①②③（CLAUDE.md 全局禁）'),
    ('decision_nums', '正文「决策 N」（应在 baseline 决策记录 / delta §6）'),
    ('route_urls', '正文具体 URL / 路由（PM 不定义技术实现，应用「独立页 / 独立路由」业务语义）'),
    ('pm_overreach_hits', 'PM 角色越界禁词（hover / DOM / i18n / modal / cache / dirty / @media 等）'),
    ('visual_overreach_hits', 'PM 视觉细节越界（颜色 / 尺寸 / 描边 / 圆角 / 设备壳 / ✕ 等，应由设计规范定）'),
    ('iteration_traces', '§1.4 核心变更迭代流水词'),
    ('broken_image_alt', '图片 alt 为空'),
    ('nested_subscenes', '5/6/7 章两层嵌套（##### N.x.y.z 禁，一层 #### N.x.y 物理分组放行）'),
    ('horizontal_rule_hits', '水平线 ---（Confluence 渲染丑，章节用 h1/h2 自然分隔；表格 |---| 不算）'),
]
# 场景正文串句（FAIL）：§2.x 需求正文 现状 / 本轮 标签 bullet 焊多句。逃生阀 SKIP_SCENE_PROSE_GATE=1
# （连贯叙事确实该保留时用，用前先向用户说明原因——知会制，非审批制）。
if os.environ.get('SKIP_SCENE_PROSE_GATE') != '1':
    fail_keys.append(('scene_prose_runon_hits', '场景正文标签 bullet 焊多句（一 bullet 一原子事实 / 多阶段用 →；逃生阀 SKIP_SCENE_PROSE_GATE=1）'))
# section_anchors / bare_scene_codes 是 split（多文件拼接）才有的死链 / 裸编号风险：
# §X.Y 锚点拼页后跨文件失效，裸编号在 scenes/ 散件里无上下文。单文件（single delta /
# baseline）内 §X.Y 是合法内跳、编号索引是设计模式 → 只对 split 查，不按 profile 名判。
if IS_SPLIT:
    fail_keys.append(('section_anchors', '正文「§X.Y」章节锚点（应用白话章节名）'))
    fail_keys.append(('bare_scene_codes', '正文裸场景编号（应用「编号 + 白话名」或纯白话）'))
if not SKELETON:
    fail_keys.append(('placeholders', '占位符残留（TBD/TODO/{{ 待填）'))
# 引用块 >：baseline 历史 living 文档存量豁免（等迭代消化），delta / single / split 都拦
if PROFILE != 'baseline':
    fail_keys.append(('blockquote_hits', '引用块 >（Confluence 渲染丑，业务故事用 **业务故事**：正文；表格 | 不算）'))

warn_keys = [
    ('snake_field_hits', 'snake_case 字段名（字段表已豁免）'),
    ('css_impl_hits', 'CSS 实现细节（PM 不应写）'),
    ('cjk_half_punct', 'CJK 旁半角标点'),
    ('semicolon_abuse_hits', '分号滥用（单行 ≥ 2 分号 → 拆成 bullet 或 1.2.3. 编号；表格行豁免）'),
    ('long_sentence_hits', '长句 run-on（句段 ≥ 100 字 → 拆句或转列表；表格行豁免）'),
    ('bullet_runon_hits', 'bullet 串句（行内句号串并列项 → 一项一 bullet，句号只落行尾；表格行豁免）'),
    ('branch_prose_hits', '条件分支散文规则（全局规则章单行 ≥ 2 分支标记 → 改「给定｜当｜则」可断言表，见 prd-scene-templates §4.5；表格行豁免）'),
    ('label_li_runs', '场景块 li 重复标签前缀（同一标签 ≥ 3 条连排 → 标签做组头一次、子项缩一级 bullet，见 prd-scene-template-quickref）'),
]
if SKELETON:
    warn_keys.append(('placeholders', '占位符残留（骨架阶段允许，PM 填完前要清掉）'))

merged = {**voice, **struct}
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

# ── 1.5. 叶子完整性启发式（WARN，不阻断）──────────────
# 机械化子集：字段表出现行情 / 实时词，但表头没有「刷新 / 生命周期 / 周期」列 →
# 多半漏了刷新触发点 / 字段生命周期（叶子完整性 7 类之 #1 #2）。提示跑「交付前冷读」。
# 只挑高命中低误报：限「字段表」（表头含「字段」），且行内含行情实时词。
echo
echo "── 1.5. 叶子完整性启发式（WARN）──"
python3 - "$COMPOSED_FILE" <<'PY'
import re, sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding='utf-8')
lines = text.splitlines()
MARKET = ('实时', '当前价', '未实现盈亏', '盈亏率', '行情')
LIFECYCLE_COL = ('刷新', '生命周期', '周期', '更新')

def is_row(s): return s.strip().startswith('|') and s.strip().endswith('|')

warns = []
i = 0
n = len(lines)
while i < n:
    s = lines[i].strip()
    # 表头行：含「字段」+ 下一行是分隔行
    if is_row(s) and '字段' in s and i + 1 < n and re.match(r'^\s*\|[\s:|-]+\|\s*$', lines[i+1]):
        header = s
        header_has_lifecycle = any(k in header for k in LIFECYCLE_COL)
        # 收集表体
        body = []
        j = i + 2
        while j < n and is_row(lines[j].strip()):
            body.append(lines[j]); j += 1
        body_text = '\n'.join(body)
        if not header_has_lifecycle and any(w in body_text for w in MARKET):
            warns.append(f"L{i+1}: 字段表含行情 / 实时词但表头无「刷新 / 生命周期」列 → 核对刷新触发点 / 字段生命周期是否写死")
        i = j
        continue
    i += 1

if warns:
    for w in warns[:5]:
        print(f"  ⚠️  {w}")
    if len(warns) > 5:
        print(f"     ... +{len(warns) - 5}")
    print("     建议：跑「交付前冷读」Step（cold_read.py + 干净子代理），按 prd-scene-templates §4.6 七类逐条反测")
else:
    print("  ✓ 字段表刷新 / 生命周期列启发式无命中")
PY
# 纯 WARN，不进 fail

# ── 1.6. delta 分量伸缩启发式（WARN，不阻断）──────────────
# 补丁包（patch）档：§2.0 索引表收口轻项，只有重项才配另起 ### 2.N 需求块。
# 抓两类：① 该塌没塌（块小得跟表行一样，还占一个 H3）② 表里写「详见 2.N」却没那个块。
# 分量是判断题，只报 WARN 不 FAIL——用 FAIL 拦判断题只会催生逃生阀。
echo
echo "── 1.6. delta 分量伸缩启发式（WARN）──"
python3 - "$COMPOSED_FILE" <<'PY'
import re, sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding='utf-8')

# 头部块 = 首个 H1 行尾 ~ 下一个顶级标题；档位写在协作表「迭代档位」格（旧骨架是 bullet）
tops = [m.start() for m in re.finditer(r'^# ', text, re.MULTILINE)]
if not tops:
    print("  ✓ 无顶级章节，跳过"); sys.exit(0)
_nl = text.find("\n", tops[0])
_hs = len(text) if _nl < 0 else _nl + 1
_he = tops[1] if len(tops) > 1 else len(text)
header = text[_hs:_he]
if '补丁包' not in header:
    print("  ✓ 非补丁包档，跳过（本维只对 patch 开）"); sys.exit(0)

# §2 本轮需求 区间
m2 = re.search(r'^# 2\.\s', text, re.MULTILINE)
if not m2:
    print("  ✓ 无 §2 本轮需求章，跳过"); sys.exit(0)
nxt = re.search(r'^# (?!2\.)', text[m2.start() + 1:], re.MULTILINE)
sec2 = text[m2.start(): m2.start() + 1 + nxt.start()] if nxt else text[m2.start():]

# ① 该塌没塌：块非空行 ≤ 14 且无表格、无「数据影响」段 = 分量与表行相当
# 阈值按真实补丁包标定：一句话改动的块 11-12 行，含跨端 / 兜底逻辑的重项 17-19 行。
LIGHT_MAX_LINES = 14
blocks = list(re.finditer(r'^### (2\.\d+)\s+(.*)$', sec2, re.MULTILINE))
warns = []
for i, b in enumerate(blocks):
    end = blocks[i + 1].start() if i + 1 < len(blocks) else len(sec2)
    body = sec2[b.end():end]
    if re.search(r'^\s*\|', body, re.MULTILINE):
        continue  # 有表格 = 结构化内容，塌不进单行
    if '数据影响' in body:
        continue  # 有数据变化 = 重项
    n = len([ln for ln in body.splitlines() if ln.strip()])
    if n <= LIGHT_MAX_LINES:
        warns.append(f"§{b.group(1)}「{b.group(2)[:24]}」块仅 {n} 行且无表格 / 无数据影响 → 可塌进 §2.0 表（修改点 + 验收两列）")

# ② 悬空指针：表里「详见 2.N」找不到对应 ### 2.N
have = {b.group(1) for b in blocks}
for cm in re.finditer(r'详见\s*(2\.\d+)', sec2):
    if cm.group(1) not in have:
        warns.append(f"§2.0 表写「详见 {cm.group(1)}」但全文无 ### {cm.group(1)} 需求块（悬空指针）")

if warns:
    for w in dict.fromkeys(warns):
        print(f"  ⚠️  {w}")
    print("     判据：新增 / 变更业务对象 · 涉状态流转 · 跨端行为不一致 · 有取舍要在决策记录章交代 —— 四条都不命中即轻项")
else:
    print("  ✓ 补丁包分量伸缩无异常")
PY
# 纯 WARN，不进 fail

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
python3 - "$FILE" "$SCENES_DIR" <<'PY' || IMG_EXIT=$?
import os, re, sys
from pathlib import Path

prd_path = Path(sys.argv[1])
scenes_dir = Path(sys.argv[2])

md_files = [prd_path]
if scenes_dir.is_dir():
    md_files += sorted(scenes_dir.glob('*.md'))

img_re = re.compile(r'!\[[^\]]*\]\((\.{1,2}/assets/[^)]+)\)')
total = 0
missing = []
prd_dir = prd_path.parent

for md in md_files:
    text = md.read_text(encoding='utf-8')
    for m in img_re.finditer(text):
        rel = m.group(1)
        total += 1
        if rel.startswith('./'):
            full = prd_dir / rel[2:]
        elif rel.startswith('../'):
            full = prd_dir / rel[3:]
        else:
            continue
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
    if ! python3 "$PUNCT_CHECKER" "$COMPOSED_FILE" --strict; then
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
