#!/bin/bash
# PRD docx 自检脚本
# 用法: bash scripts/check_prd.sh <docx> <scene-list> [项目scripts目录]
set -euo pipefail

FILE="${1:?用法: bash scripts/check_prd.sh <docx> <scene-list> [scripts_dir]}"
SCENE_LIST="${2:?缺少 scene-list.md 路径}"
SCRIPTS_DIR="${3:-$(dirname "$FILE")/../scripts}"

echo "=========================================="
echo "  PRD 自检: $(basename "$FILE")"
echo "=========================================="

# 用 -E（POSIX ERE）兼容 macOS BSD grep，[0-9] 替代 \d；2>&1 暴露 pattern 错误
SCENE_COUNT=$(grep -cE '^\|.*[A-Z]-?[0-9]' "$SCENE_LIST" 2>&1)
if ! [[ "$SCENE_COUNT" =~ ^[0-9]+$ ]]; then
    echo "❌ scene-list 计数失败（grep 报错）: $SCENE_COUNT"
    exit 2
fi
echo "scene-list 中场景数: $SCENE_COUNT"
if [ "$SCENE_COUNT" -eq 0 ]; then
    echo "❌ scene-list 中未匹配到任何场景行（pattern: ^\|.*[A-Z]-?[0-9]）"
    echo "   排查：检查 $SCENE_LIST 表格是否用 | 分隔 / 编号是否 A-1 / B-2 这种格式"
    exit 2
fi

fail=0

# ── 0. 截图新鲜度检查（升版 patch 路线必查，放最前面避免被 python heredoc 早退掩盖）──
PROJ_DIR=$(dirname "$(dirname "$FILE")")
PROTO_HTML=$(ls "$PROJ_DIR"/deliverables/*可交互原型*.html 2>/dev/null | head -1 || true)
SHOT_DIR="$PROJ_DIR/screenshots"
if [ -n "$PROTO_HTML" ] && [ -d "$SHOT_DIR" ]; then
    _mtime() { stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null; }
    PROTO_T=$(_mtime "$PROTO_HTML")
    OLDEST_PNG_T=$(find "$SHOT_DIR" -name '*.png' -type f 2>/dev/null \
      | grep -Ev '/(.*_v[0-9]+|archive|deprecated|old)/' \
      | while read -r f; do _mtime "$f"; done | sort -n | head -1)
    if [ -n "$PROTO_T" ] && [ -n "$OLDEST_PNG_T" ] && [ "$PROTO_T" -gt "$OLDEST_PNG_T" ]; then
        DELTA_H=$(( (PROTO_T - OLDEST_PNG_T) / 3600 ))
        echo "❌ 截图过期：原型 $(basename "$PROTO_HTML") 比 screenshots/ 中最旧截图新 ${DELTA_H}h"
        echo "   修复：跑 screenshot_*.py 重拍 + insert_*.py 回填到 docx"
        echo "   或在 update_*.py 末尾调 assert_screenshots_fresh() 强制断言"
        fail=1
    fi
fi

# ── 1. 项目脚本禁止重定义框架函数 ─────────────────
if [ -d "$SCRIPTS_DIR" ]; then
    banned_defs=$(grep -lE '^def +(set_cell_text|set_cell_blocks|replace_para_text|fill_cell_blocks|fix_dpi|set_cell_bg|para_run|para_run_md|scene_table|make_table|bullet|h1|h2|h3|cover_page|normalize_headings|normalize_punctuation) *\(' "$SCRIPTS_DIR"/*.py 2>/dev/null || true)
    if [ -n "$banned_defs" ]; then
        echo "❌ 项目脚本重定义框架函数(SKILL.md 禁止, 必须 from gen_prd_base/update_prd_base import *):"
        echo "$banned_defs" | sed 's/^/   /'
        fail=1
    fi

    # ── 1b. 项目脚本禁止硬编码 BASE 路径(memory #1) ──
    # `BASE = Path('/Users/xxx/pm-workspace')` 换机器/换用户名即炸,
    # 统一用 Path(__file__).resolve().parents[N] 相对定位
    hardcoded=$(grep -lE "^BASE\s*=\s*(Path\()?['\"]?/Users/[^'\"]+pm-workspace" "$SCRIPTS_DIR"/*.py 2>/dev/null || true)
    if [ -n "$hardcoded" ]; then
        echo "❌ 项目脚本硬编码 /Users/xxx/pm-workspace 路径(换机器即炸, 见 prd SKILL.md 硬规则 #9):"
        echo "$hardcoded" | sed 's/^/   /'
        echo "   修法: BASE = Path(__file__).resolve().parents[3]  # pm-workspace 根"
        fail=1
    fi

    # ── gen_prd_v*.py 单脚本体积告警 ───────────────
    for f in "$SCRIPTS_DIR"/gen_prd_v*.py; do
        [ -f "$f" ] || continue
        lines=$(wc -l < "$f")
        if [ "$lines" -gt 700 ]; then
            echo "⚠️  $(basename "$f") $lines 行过长(> 700),考虑抽重复 scene 为函数"
        fi
    done
fi

# ── 2. docx 内容扫描 ─────────────────────────────────
# ── 2. docx 内容扫描（统一委托 humanize.scan_prd_structural + scan_human_voice）─
_HUMAN_VOICE_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 - "$FILE" "$SCENE_COUNT" "$_HUMAN_VOICE_DIR" <<'PY'
import sys
from docx import Document

FILE = sys.argv[1]
SCENES = int(sys.argv[2])
sys.path.insert(0, sys.argv[3])

doc = Document(FILE)
print(f'段落数: {len(doc.paragraphs)}')
print(f'表格数: {len(doc.tables)}')
print(f'scene-list 期望场景数: {SCENES}')

fail = 0

# 结构性 / 内容性扫描:圈数字 / 决策编号 / 占位符 / 1.3 流水账 / 章节故事引言 /
# Scene 右列层次 / 段落表格数 / 截图 DPI / CJK 半角 / theme / 老字体 / 多端章节
from humanize import scan_prd_structural, report_structural_violations
struct = scan_prd_structural(doc, scene_count=SCENES, docx_path=FILE)
if report_structural_violations(struct, file=sys.stdout):
    fail = 1

# 系统设计字体可用性(本机环境 warn,docx 文件本身不受影响)
import shutil, subprocess
if shutil.which('fc-list'):
    DESIGN_FONTS = ['Poppins', 'Lora', 'Noto Sans SC', 'Noto Serif SC', 'JetBrains Mono']
    missing = []
    for f in DESIGN_FONTS:
        r = subprocess.run(['fc-list', f], capture_output=True, text=True)
        if not r.stdout.strip():
            missing.append(f)
    if missing:
        print(f'⚠️  本机未装 {len(missing)}/{len(DESIGN_FONTS)} 个设计字体: {", ".join(missing)}')
        print('   Word 会 fallback 到系统衬线/sans 替代,docx 字距 / 字形可能与设计稿不同(docx 文件本身正确)')
        print('   装齐: brew install --cask font-poppins font-lora font-noto-sans-sc font-noto-serif-sc font-jetbrains-mono')

# 讲人话扫描(流水账日期 / snake_case / CSS 实现细节)— 与 push gate 共享同一份规则
try:
    from humanize import scan_human_voice, report_violations
    voice_result = scan_human_voice(doc)
    if report_violations(voice_result, file=sys.stdout):
        fail = 1
except ImportError as e:
    print(f'⚠️  讲人话扫描跳过({e})')

if fail:
    print('❌ PRD 自检未通过')
    sys.exit(1)
print('✅ PRD 自检通过')
PY

# ── 3. context.md 第 6 章业务规则联动自检（PR2 预留三条，warn 不阻断）──
# PR2 改造 context-template 第 6 章：主表三件套 + 5 类白名单子章。本节兜底检查
# 项目 context.md 是否符合 PR2 模板。老项目（context.md 旧格式）warn 提示重写。
CONTEXT_MD="$(dirname "$SCENE_LIST")/context.md"
if [ -f "$CONTEXT_MD" ]; then
python3 - "$CONTEXT_MD" <<'PY'
import re, sys
from pathlib import Path

ctx = Path(sys.argv[1])
text = ctx.read_text(encoding='utf-8')

# 提取第 6 章「业务规则」内容
m = re.search(r'^##\s+(?:6\.|六、)\s*业务规则[^\n]*\n', text, re.MULTILINE)
if not m:
    print('ℹ️  context.md 无第 6 章业务规则，跳过 PR2 模板自检')
    sys.exit(0)
start = m.end()
nx = re.search(r'^##\s+(?:7\.|七、)', text[start:], re.MULTILINE)
section = text[start:(start + nx.start()) if nx else len(text)]

warns = []

# ① 找主表（第一个 markdown 表格，表头含「条件 + 行为 + 异常态」）
TABLE_HEADER_RE = re.compile(r'^\|.*条件.*\|.*行为.*\|.*异常态.*\|', re.MULTILINE)
header_match = TABLE_HEADER_RE.search(section)
if not header_match:
    warns.append('① context.md 第 6 章缺主表（表头需含「条件 / 行为 / 异常态」三列）')
else:
    # 主表必须先于所有子章
    first_subsection = re.search(r'^###\s+', section, re.MULTILINE)
    if first_subsection and header_match.start() > first_subsection.start():
        warns.append('① 主表位置错误：必须先于所有 ### 子章（PR2 模板硬规则）')

    # ② 提取主表行（| ... | 但跳过分隔行 |---|）
    rows = []
    for ln in section[header_match.end():].splitlines():
        if not ln.startswith('|'):
            break
        cells = [c.strip() for c in ln.strip('|').split('|')]
        if all(set(c) <= set('-: ') for c in cells if c):
            continue  # 分隔行
        rows.append(cells)
    real_rules = [r for r in rows if len(r) >= 4]  # 规则 ID / 条件 / 行为 / 异常态
    if not real_rules:
        warns.append('② 主表无规则行（Rule 数 ≥ 1）')
    else:
        empty_cell_rows = []
        for r in real_rules:
            # 跳过示例行（含「示例」字样）
            if any('示例' in c for c in r):
                continue
            cond, behav, fallback = r[1], r[2], r[3]
            if not (cond and behav and fallback):
                empty_cell_rows.append(r[0] if r[0] else '?')
        if empty_cell_rows:
            warns.append(
                f'② 主表 {len(empty_cell_rows)} 条 Rule 三列有空（条件/行为/异常态需均非空）：'
                f'{empty_cell_rows[:5]}'
            )

# ③ 子章前缀白名单（6 类穷举）
WHITELIST = {'设计原则', '数据契约', 'UI 形态', '字段定义', '跨端架构', '关键假设'}
sub_titles = re.findall(r'^###\s+(\d+(?:\.\d+)?)\s+([^\n·]+?)(?:\s*·|\s*$)',
                        section, re.MULTILINE)
out_of_whitelist = []
for num, prefix in sub_titles:
    p = prefix.strip()
    if p in ('子章类型白名单（5 类，穷举）', '子章类型白名单（6 类，穷举）'):
        continue  # 模板自身的元数据子章（5/6 类穷举均跳过，迁移期兼容）
    if p not in WHITELIST:
        out_of_whitelist.append(f'### {num} {p}')
if out_of_whitelist:
    warns.append(
        f'③ 子章前缀不在白名单（{", ".join(WHITELIST)}）：'
        f'{out_of_whitelist[:5]}'
    )

if warns:
    print(f'⚠️  context.md 第 6 章 PR2 模板自检（{len(warns)} 处，warn 不阻断）')
    for w in warns:
        print(f'   {w}')
    print(f'   规范：.claude/chat-templates/context-template.md 第 6 章')
else:
    print('✅ context.md 第 6 章符合 PR2 模板')
PY
fi

# 截图新鲜度检查已挪到脚本开头第 0 步
