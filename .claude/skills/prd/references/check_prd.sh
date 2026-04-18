#!/bin/bash
# PRD docx 自检脚本
# 用法: bash scripts/check_prd.sh <docx文件路径> <scene-list.md路径>
set -euo pipefail

FILE="${1:?用法: bash scripts/check_prd.sh <docx> <scene-list>}"
SCENE_LIST="${2:?缺少 scene-list.md 路径}"

echo "=========================================="
echo "  PRD 自检: $(basename "$FILE")"
echo "=========================================="

# 计算 scene 数量
SCENE_COUNT=$(grep -cP '^\|.*[A-Z]-?\d' "$SCENE_LIST" 2>/dev/null || echo "0")
echo "scene-list 中场景数: $SCENE_COUNT"

python3 -c "
from docx import Document
doc = Document('$FILE')
paras = len(doc.paragraphs)
tables = len(doc.tables)
scenes = $SCENE_COUNT

print(f'段落数: {paras}')
print(f'表格数: {tables}')

fail = False
if paras < max(20, scenes * 3):
    print(f'❌ 段落数异常：{paras}，期望 > {max(20, scenes * 3)}')
    fail = True
if tables < scenes:
    print(f'❌ 表格数异常：{tables}，期望 > {scenes}')
    fail = True

# 检查术语一致性：看看是否有 待填充/TBD
full_text = '\n'.join([p.text for p in doc.paragraphs])
for kw in ['待填充', 'TBD', 'TODO', 'FIXME']:
    if kw in full_text:
        print(f'❌ 残留占位符: {kw}')
        fail = True

if not fail:
    print('✅ PRD 自检通过')
else:
    print('❌ PRD 自检未通过')
    exit(1)
"
