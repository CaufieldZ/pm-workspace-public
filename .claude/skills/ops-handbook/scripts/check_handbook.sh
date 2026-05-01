#!/bin/bash
# 运营手册 docx 自检脚本（独立于 PRD 的 humanize 路径）
# 用法：bash check_handbook.sh <docx>
set -euo pipefail

FILE="${1:?用法: bash check_handbook.sh <docx>}"

echo "=========================================="
echo "  运营手册自检: $(basename "$FILE")"
echo "=========================================="

# ── 内嵌 Python：字体三件套 + 圈数字 + 半角标点 + DPI + 章节数 ──
python3 - "$FILE" <<'PY'
import io, re, sys, zipfile
from docx import Document
from docx.oxml.ns import qn

FILE = sys.argv[1]
doc = Document(FILE)
fail = 0

paras = len(doc.paragraphs)
tables = len(doc.tables)
print(f'段落数: {paras}')
print(f'表格数: {tables}')

# ── 1. 章节数最低 5 章（模板基础骨架） ─────────────────────────
h1_count = sum(1 for p in doc.paragraphs
               if p.style and p.style.name == 'Heading 1' and p.text.strip())
print(f'H1 章数: {h1_count}')
if h1_count < 5:
    print(f'❌ H1 章数不足: {h1_count}, 模板基础骨架要求 ≥ 5（模块概览 + 角色权限 + 操作流程 + 字段定义 + FAQ）')
    fail = 1

# ── 2. 字体三件套（与 PRD 同款规则） ──────────────────────────
with zipfile.ZipFile(FILE) as z:
    if 'word/theme/theme1.xml' not in z.namelist():
        print('❌ 缺 word/theme/theme1.xml（python-docx 老模板漏注入，docDefaults themed 失效 → Word fallback Arial）')
        print('   修复: from core.normalize import ensure_theme; ensure_theme(docx_path)')
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
    print(f'❌ 正文残留老字体 run {legacy_count} 个（Arial/Calibri/微软雅黑 等）')
    print('   修复: from core.normalize import normalize_fonts; normalize_fonts(doc)')
    fail = 1

# ── 3. 全文扫圈数字 + 半角标点 + 占位符 ─────────────────────
chunks = [p.text for p in doc.paragraphs]
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            chunks.append(c.text)
full_text = '\n'.join(chunks)

CIRCLE = re.compile(r'[①-⑳⓫-⓿]')
if CIRCLE.search(full_text):
    uniq = sorted(set(CIRCLE.findall(full_text)))
    print(f'❌ 圈数字残留（CLAUDE.md 禁止 ①②③，统一 1./2./3.）: {"".join(uniq)}')
    fail = 1

CJK = r'[一-鿿]'
half_punct = re.findall(rf'{CJK}[,:()]|[,:()]{CJK}', full_text)
if half_punct:
    samples = list(set(half_punct))[:5]
    print(f'❌ 中文相邻半角标点（{len(half_punct)} 处，调 normalize_punctuation）: 样例 {samples}')
    fail = 1

for kw in ['待填充', 'TBD', 'TODO', 'FIXME', '← 此处粘贴']:
    if kw in full_text:
        print(f'❌ 残留占位符: {kw}')
        fail = 1

# ── 4. 截图 DPI ≥ 130 ────────────────────────────────────────
try:
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
        print(f'❌ 截图 DPI<130 有 {bad_dpi} 张（Playwright 默认 72，需 fix_dpi 到 144）')
        fail = 1
except ImportError:
    print('⚠️  PIL 未安装，跳过 DPI 检查')

# ── 收尾 ─────────────────────────────────────────────────────
if fail:
    print('❌ 运营手册自检未通过')
    sys.exit(1)
print('✅ 运营手册自检通过')
PY
