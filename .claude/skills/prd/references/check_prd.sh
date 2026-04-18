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

SCENE_COUNT=$(grep -cP '^\|.*[A-Z]-?\d' "$SCENE_LIST" 2>/dev/null || echo "0")
echo "scene-list 中场景数: $SCENE_COUNT"

fail=0

# ── 1. 项目脚本禁止重定义框架函数 ─────────────────
if [ -d "$SCRIPTS_DIR" ]; then
    banned_defs=$(grep -lE '^def +(set_cell_text|set_cell_blocks|replace_para_text|fill_cell_blocks|fix_dpi|set_cell_bg|para_run|para_run_md|scene_table|make_table|bullet|h1|h2|h3|cover_page|normalize_headings|normalize_punctuation) *\(' "$SCRIPTS_DIR"/*.py 2>/dev/null || true)
    if [ -n "$banned_defs" ]; then
        echo "❌ 项目脚本重定义框架函数(SKILL.md 禁止, 必须 from gen_prd_base/update_prd_base import *):"
        echo "$banned_defs" | sed 's/^/   /'
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
python3 - "$FILE" "$SCENE_COUNT" <<'PY'
import re, sys
from docx import Document
FILE = sys.argv[1]
SCENES = int(sys.argv[2])

doc = Document(FILE)
paras = len(doc.paragraphs)
tables = len(doc.tables)
print(f'段落数: {paras}')
print(f'表格数: {tables}')

fail = 0
if paras < max(20, SCENES * 3):
    print(f'❌ 段落数异常: {paras}, 期望 > {max(20, SCENES * 3)}')
    fail = 1
if tables < SCENES:
    print(f'❌ 表格数异常: {tables}, 期望 > {SCENES}')
    fail = 1

chunks = [p.text for p in doc.paragraphs]
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            chunks.append(c.text)
full_text = '\n'.join(chunks)

for kw in ['待填充', 'TBD', 'TODO', 'FIXME', '← 此处粘贴']:
    if kw in full_text:
        print(f'❌ 残留占位符: {kw}')
        fail = 1

CIRCLE = re.compile(r'[\u2460-\u2473\u24eb-\u24ff]')
if CIRCLE.search(full_text):
    uniq = sorted(set(CIRCLE.findall(full_text)))
    print(f'❌ 圈数字残留(CLAUDE.md 禁止产出物用 ①②③, 统一 1./2./3.): {"".join(uniq)}')
    fail = 1

# 中文相邻半角标点(soul.md 禁止)
CJK = r'[\u4e00-\u9fff]'
half_punct = re.findall(rf'{CJK}[,:()]|[,:()]{CJK}', full_text)
if half_punct:
    samples = list(set(half_punct))[:5]
    print(f'❌ 中文相邻半角标点({len(half_punct)} 处, 调 normalize_punctuation): 样例 {samples}')
    fail = 1

flat = []
for ti, t in enumerate(doc.tables):
    if len(t.columns) != 2 or len(t.rows) < 1:
        continue
    right = t.rows[0].cells[1]
    ps = [p for p in right.paragraphs if p.text.strip()]
    if len(ps) == 1 and len(ps[0].text) > 100:
        flat.append(f'T{ti}({len(ps[0].text)}字)')
if flat:
    print(f'❌ Scene 右列疑似扁平化(单段落>100字符, 用 set_cell_blocks 重建): {", ".join(flat)}')
    fail = 1

import io
from PIL import Image
bad_dpi = 0
for rel in doc.part.rels.values():
    if 'image' not in rel.target_ref:
        continue
    try:
        img = Image.open(io.BytesIO(rel.target_part.blob))
        dpi = img.info.get('dpi', (None, None))
        if not dpi[0] or dpi[0] < 130:
            bad_dpi += 1
    except Exception:
        pass
if bad_dpi:
    print(f'❌ 截图 DPI<130 有 {bad_dpi} 张(Playwright 默认 72, 需 fix_dpi 到 144)')
    fail = 1

if fail:
    print('❌ PRD 自检未通过')
    sys.exit(1)
print('✅ PRD 自检通过')
PY
