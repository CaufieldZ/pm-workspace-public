"""PRD 底层样式工具：颜色 / 字体 / 段落 run / 单元格 run / inline bold。

被 core.{headings, tables, images, normalize, patch} 依赖，也被 sections.py 间接复用。

对齐 Anthropic 官方 brand-guidelines + claude.ai chat UI：
- textHeading 用官方 Dark #141413
- accent 用官方 terra cotta #D97757
- 字体三分工：title=Lora+Noto Serif SC / body=Poppins+Noto Sans SC / mono=JetBrains Mono
"""
import re

from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ── 颜色常量 ──────────────────────────────────────────────────────────────
# 注：accentBlue / tagChange 等 key 名保留是历史 alias，下游脚本（如 gen_sop_v1/v2）
# 依赖键名稳定，只换 value 不换 key（同 ppt-template.html --blue 处理思路）
C = {
    "textPrimary":   "333333",
    "textSecondary": "666666",
    "textMuted":     "888888",
    "textHeading":   "141413",     # Anthropic 官方 Dark
    "textLink":      "D97757",     # Anthropic terra cotta
    "tableHeaderBg": "141413",     # 表头深底白字（Anthropic 官方 Dark）
    "tableHeaderText": "FFFFFF",
    "tableAltRow":   "F8FAFB",
    "tableBorder":   "CCCCCC",
    "tagNew":        "15803D",     # Arco 语义绿（跨主题保留）
    "tagChange":     "D97757",     # terra cotta
    "tagGreen":      "15803D",
    "accentBlue":    "D97757",     # 键名保留兼容下游，值切到 terra cotta
}


# ── 字体三分工配置 ────────────────────────────────────────────────────────
# Word 渲染时根据字符自动选 ascii（英文/数字）或 eastAsia（中文）字体。
# Anthropic 官方 brand-guidelines 钦定的免费字体。用户系统没装时 Word 自动 fallback：
#   Noto Sans SC / Noto Serif SC 没装 → PingFang SC（Mac）/ 微软雅黑（Windows）
#   Lora 没装 → Georgia / 系统默认衬线
#   Poppins 没装 → 系统默认 sans
FONT = {
    'title': {'ascii': 'Lora',          'eastAsia': 'Noto Serif SC'},  # 标题 / 章节 / 重点（衬线，对标 Tiempos / Copernicus）
    'body':  {'ascii': 'Poppins',       'eastAsia': 'Noto Sans SC'},   # 正文 / 表格 / 段落（无衬线，对标 Styrene B）
    'mono':  {'ascii': 'JetBrains Mono','eastAsia': 'JetBrains Mono'}, # 代码 / 路由 / 事件名 / 状态标签 / kicker
    # 兼容旧脚本：font="Arial" 走 body 配置兜底
    'Arial': {'ascii': 'Poppins',       'eastAsia': 'Noto Sans SC'},
}


# ── 单元格底层操作 ──────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for old in tcPr.findall(qn('w:shd')):
        tcPr.remove(old)
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def set_cell_border(cell, **kwargs):
    """设置单元格边框。用法：set_cell_border(cell, bottom={'val':'single','sz':4,'color':'D97757'})"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        if edge in kwargs:
            tag = OxmlElement(f'w:{edge}')
            tag.set(qn('w:val'), kwargs[edge].get('val', 'single'))
            tag.set(qn('w:sz'), str(kwargs[edge].get('sz', 4)))
            tag.set(qn('w:space'), '0')
            tag.set(qn('w:color'), kwargs[edge].get('color', 'CCCCCC'))
            tcBorders.append(tag)
    tcPr.append(tcBorders)


# ── 段落 run 渲染（核心 API）──────────────────────────────────────────────

def para_run(para, text, font="body", size_pt=10, bold=False, color=None, italic=False):
    """渲染一段文本。font 接受 'title' / 'body' / 'mono' 三种 role（推荐），
    或老接口的具体字体名（'Arial' 等，自动映射到 body 配置兜底）。"""
    run = para.add_run(text)
    cfg = FONT.get(font, FONT['body'])
    run.font.name = cfg['ascii']
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    r = run._r
    rPr = r.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), cfg['ascii'])
    rFonts.set(qn('w:hAnsi'), cfg['ascii'])
    rFonts.set(qn('w:eastAsia'), cfg['eastAsia'])
    rPr.insert(0, rFonts)
    return run


_MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def para_run_md(para, text, size_pt=10, color=None):
    """渲染内联 **bold** 片段。非 bold 段落继承默认颜色，bold 段落用 textHeading。"""
    pos = 0
    for m in _MD_BOLD_RE.finditer(text):
        if m.start() > pos:
            para_run(para, text[pos:m.start()], size_pt=size_pt, color=color)
        para_run(para, m.group(1), size_pt=size_pt, bold=True,
                 color=C["textHeading"] if color is None else color)
        pos = m.end()
    if pos < len(text):
        para_run(para, text[pos:], size_pt=size_pt, color=color)


# ── 单元格文本（清空 + 写入）───────────────────────────────────────────────

def cell_text(cell, text, size_pt=9, bold=False, color=None, italic=False,
              align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    para_run(p, text, size_pt=size_pt, bold=bold, color=color, italic=italic)
    return p
