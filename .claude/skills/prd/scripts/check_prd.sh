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

# PM 内部编号扫描(memory feedback_prd_no_scene_id_in_body.md)
# scene_table 第 0 列是场景标题 anchor,允许「📱 X-N · 名称」编号;其他位置出现即违规
DECISION_RE = re.compile(r'决策\s*\d+')
SCENE_ID_BODY_RE = re.compile(r'[A-G]-\d+(?:\s*/\s*[A-G]-\d+){0,5}')
banned_decisions = []
banned_scene_ids = []
for ti, t in enumerate(doc.tables):
    for ri, row in enumerate(t.rows):
        for ci, cell in enumerate(row.cells):
            if ci == 0:
                continue  # 第 0 列是场景标题 anchor
            txt = cell.text
            if DECISION_RE.search(txt):
                banned_decisions.append(f'T{ti}R{ri}C{ci}: {txt[:40]!r}')
            # T0=封面属性表, T1=1.x 元信息, T2=第 2 章场景地图(允许 A-N/B-N 罗列), T3+=scene_table
            if ti >= 3 and SCENE_ID_BODY_RE.search(txt):
                banned_scene_ids.append(f'T{ti}R{ri}C{ci}: {txt[:40]!r}')
# 段落扫决策编号(排除 Heading 标题,允许章节编号 2.1 / 6.3)
for p in doc.paragraphs:
    style = p.style.name if p.style else ''
    if style.startswith('Heading'):
        continue
    if DECISION_RE.search(p.text):
        banned_decisions.append(f'P[{style}]: {p.text[:40]!r}')

if banned_decisions:
    samples = banned_decisions[:5]
    print(f'❌ 正文残留决策编号 {len(banned_decisions)} 处(SKILL.md 硬规则 #11): 样例 {samples}')
    fail = 1
if banned_scene_ids:
    samples = banned_scene_ids[:5]
    print(f'❌ 正文残留场景编号 {len(banned_scene_ids)} 处(SKILL.md 硬规则 #11, 仅第 2 章场景地图允许): 样例 {samples}')
    fail = 1

# 中文相邻半角标点(soul.md 禁止)
CJK = r'[\u4e00-\u9fff]'
half_punct = re.findall(rf'{CJK}[,:()]|[,:()]{CJK}', full_text)
if half_punct:
    samples = list(set(half_punct))[:5]
    print(f'❌ 中文相邻半角标点({len(half_punct)} 处, 调 normalize_punctuation): 样例 {samples}')
    fail = 1

flat = []
no_numbered = []
NUMBERED = re.compile(r'^\d+\.\s')
for ti, t in enumerate(doc.tables):
    if len(t.columns) != 2 or len(t.rows) < 1:
        continue
    right = t.rows[0].cells[1]
    ps = [p for p in right.paragraphs if p.text.strip()]
    if len(ps) == 1 and len(ps[0].text) > 100:
        flat.append(f'T{ti}({len(ps[0].text)}字)')
        continue
    # scene 右列段落数 >= 4 但没有任何段以 "N. " 开头 = 违反 numbered list 规范
    if len(ps) >= 4:
        has_num = any(NUMBERED.match(p.text) for p in ps)
        if not has_num:
            no_numbered.append(f'T{ti}({len(ps)}段)')
if flat:
    print(f'❌ Scene 右列扁平化(单段落>100字符, 用 set_cell_blocks 重建): {", ".join(flat)}')
    fail = 1
if no_numbered:
    print(f'❌ Scene 右列缺 numbered list(≥4 段且无 "N." 编号, prd-template 强制): {", ".join(no_numbered)}')
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

# ── 字体三件套自检（commit 5192b83 后所有 PRD 必须通过）──
import zipfile
from docx.oxml.ns import qn
with zipfile.ZipFile(sys.argv[1]) as z:
    if 'word/theme/theme1.xml' not in z.namelist():
        print('❌ 缺 word/theme/theme1.xml(老 python-docx 模板漏注入,导致 docDefaults themed 失效→ Word fallback Arial)。')
        print('   修复: from update_prd_base import ensure_theme; ensure_theme(docx_path)')
        fail = 1

LEGACY_FONTS = {'Arial', 'Calibri', 'Times New Roman', 'Times', 'Helvetica',
                'Microsoft YaHei', '微软雅黑', 'SimSun', '宋体', 'SimHei', '黑体'}
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
legacy_count = 0
for r in doc.element.body.iter(f'{{{W}}}r'):
    rPr = r.find(qn('w:rPr'))
    if rPr is None: continue
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None: continue
    for slot in ('ascii', 'hAnsi', 'eastAsia'):
        if rFonts.get(qn(f'w:{slot}')) in LEGACY_FONTS:
            legacy_count += 1
            break
if legacy_count:
    print(f'❌ 正文残留老字体 run {legacy_count} 个(Arial/Calibri/Microsoft YaHei 等,会渲染成 Arial 风)。')
    print('   修复: from update_prd_base import normalize_fonts; normalize_fonts(doc)')
    fail = 1

if fail:
    print('❌ PRD 自检未通过')
    sys.exit(1)
print('✅ PRD 自检通过')
PY
