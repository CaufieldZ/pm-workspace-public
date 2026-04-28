#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
# pm-ws-canary-236a5364
"""
PRD 通用框架函数库
各项目的 gen_prd_vN.py 通过 import 使用，只需写内容区。

用法：
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../.claude/skills/prd/scripts'))
    from gen_prd_base import *
"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json, os, pathlib, re

def get_author() -> str:
    cfg = pathlib.Path(__file__).resolve().parents[4] / ".claude" / "skills" / "_shared" / "workspace.json"
    try:
        return json.loads(cfg.read_text(encoding='utf-8')).get("author", "")
    except Exception:
        return ""

# ── 颜色常量 ──────────────────────────────────────────────────────────────
# 对齐 Anthropic 官方 brand-guidelines + claude.ai chat UI:
# textHeading 用官方 Dark #141413, accent 用官方 terra cotta #D97757
# 注：accentBlue / tagChange 等 key 名保留是历史 alias，下游脚本（gen_sop_v1/v2）
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

# ── 底层工具 ──────────────────────────────────────────────────────────────

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

# ── 字体三分工配置（与 anti-ai-slop.md / prd-docx-styles.md 对齐）────────
# Word 渲染时根据字符自动选 ascii（英文/数字）或 eastAsia（中文）字体
# Anthropic 官方 brand-guidelines 钦定的免费字体（github.com/anthropics/skills/skills/brand-guidelines）：
# 用户系统没装这些字体时 Word 自动 fallback：
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


_MD_BOLD_RE = __import__("re").compile(r"\*\*(.+?)\*\*")

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

# ── 段落级 ────────────────────────────────────────────────────────────────

def add_p(doc, text="", size_pt=10, bold=False, color=None, italic=False,
          align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=4):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    if text:
        para_run(p, text, size_pt=size_pt, bold=bold, color=color, italic=italic)
    return p

def h1(doc, text):
    """章标题。出版物语言：加粗字号 + 加厚下边框 terra cotta 横线，留白拉开。"""
    p = doc.add_paragraph(style='Heading 1')
    p.paragraph_format.space_before = Pt(20)
    p.paragraph_format.space_after = Pt(12)
    para_run(p, text, font='title', size_pt=18, bold=True, color=C["textHeading"])
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '12')           # 1.5pt 粗线（原 6 = 0.75pt）
    bottom.set(qn('w:space'), '4')
    bottom.set(qn('w:color'), C["accentBlue"])  # terra cotta
    pBdr.append(bottom)
    pPr.append(pBdr)

def h2(doc, text):
    """节标题。加 6pt 左色块 border 作 anchor（出版物锚点用法），文字走 terra cotta。"""
    p = doc.add_paragraph(style='Heading 2')
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Cm(0.3)  # 让左色块和文字有空隙
    para_run(p, text, font='title', size_pt=13, bold=True, color=C["accentBlue"])
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single')
    left.set(qn('w:sz'), '24')           # 3pt 短色块
    left.set(qn('w:space'), '6')
    left.set(qn('w:color'), C["accentBlue"])
    pBdr.append(left)
    pPr.append(pBdr)

def h3(doc, text):
    p = doc.add_paragraph(style='Heading 3')
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    para_run(p, text, font='title', size_pt=11, bold=True, color=C["textHeading"])

def pullquote(doc, text):
    """重点金句块，替代正文里堆 bold。出版物 pullquote 语言：
    左 3pt terra cotta border + Lora italic + 12pt + textHeading 暗色"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.left_indent = Cm(0.6)
    para_run(p, text, font='title', size_pt=12, italic=True, color=C["textHeading"])
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single')
    left.set(qn('w:sz'), '24')           # 3pt
    left.set(qn('w:space'), '12')
    left.set(qn('w:color'), C["accentBlue"])
    pBdr.append(left)
    pPr.append(pBdr)
    return p

def metric_run(p, value):
    """在段落内插入 mono terra cotta 数字（如 "47%" "5%+"），
    替代正文全 bold，让数字像 FT/经济学人那样亮起来。"""
    return para_run(p, value, font='mono', size_pt=10, bold=True, color=C["accentBlue"])


def chapter_story(doc, text):
    """章节用户故事引言（pm-workflow.md「PART/章节用户故事陈述」强制）。
    紧跟 h1 后调用，斜体浅灰一句话 ≤ 30 字，告诉读者这章在讲谁、做什么、为什么。
    技术骨架章（背景/排期/非功能）可省略。"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.left_indent = Cm(0.3)
    para_run(p, text, size_pt=10, italic=True, color="6F7A85")
    return p

def bullet(doc, text, size_pt=10):
    lines = text.split('\n')
    first = True
    for line in lines:
        line = line.strip()
        if not line:
            continue
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0 if first else 0)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.left_indent = Cm(0.5)
        para_run(p, f"• {line}", size_pt=size_pt, color=C["textPrimary"])
        first = False

# ── 表格级 ────────────────────────────────────────────────────────────────

def cell_text(cell, text, size_pt=9, bold=False, color=None, italic=False,
              align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    para_run(p, text, size_pt=size_pt, bold=bold, color=color, italic=italic)
    return p

def make_table(doc, headers, rows_data, col_widths_cm, row_height_cm=None,
               mono_first_col=False):
    """通用表格生成：headers=列名列表, rows_data=二维列表, col_widths_cm=每列宽度。
    mono_first_col=True 时首列走 mono（适合编号 / 角色 ID / 路径，让节奏感出来）"""
    tbl = doc.add_table(rows=1 + len(rows_data), cols=len(headers))
    tbl.style = 'Table Grid'
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    for j, (hdr, w) in enumerate(zip(headers, col_widths_cm)):
        cell = tbl.rows[0].cells[j]
        cell.width = Cm(w)
        set_cell_bg(cell, C["tableHeaderBg"])
        cell_text(cell, hdr, size_pt=9, bold=True, color=C["tableHeaderText"],
                  align=WD_ALIGN_PARAGRAPH.CENTER)
    for i, row in enumerate(rows_data):
        for j, (val, w) in enumerate(zip(row, col_widths_cm)):
            cell = tbl.rows[i+1].cells[j]
            cell.width = Cm(w)
            if i % 2 == 1:
                set_cell_bg(cell, C["tableAltRow"])
            # 首列 mono 渲染（编号节奏）
            if mono_first_col and j == 0:
                cell.text = ""
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                para_run(p, str(val), font='mono', size_pt=9, bold=True,
                         color=C["textHeading"])
            else:
                cell_text(cell, str(val), size_pt=9, color=C["textPrimary"])
        if row_height_cm:
            tbl.rows[i+1].height = Cm(row_height_cm)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return tbl

def scene_table(doc, scene_id, scene_name, right_blocks):
    """
    两列 Scene 表格
    right_blocks: list of (title, lines) -- title 可含「（变更）」或「（新增）」
    """
    tbl = doc.add_table(rows=1, cols=2)
    tbl.style = 'Table Grid'
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    left_cell = tbl.rows[0].cells[0]
    right_cell = tbl.rows[0].cells[1]
    left_cell.width = Cm(8.5)
    right_cell.width = Cm(13.0)
    set_cell_bg(left_cell, C["tableAltRow"])
    left_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = left_cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    para_run(p, f"\U0001f4f1 {scene_id} \u00b7 {scene_name}", size_pt=9, color=C["textMuted"], italic=True)
    p2 = left_cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para_run(p2, "\u2190 \u6b64\u5904\u7c98\u8d34\u539f\u578b\u622a\u56fe", size_pt=8, color=C["textMuted"], italic=True)

    right_cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    fill_cell_blocks(right_cell, right_blocks)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


_NUMBERED_PREFIX_RE = re.compile(r"^\d+\.\s")

def fill_cell_blocks(cell, blocks, numbered=True):
    """
    在已存在的 cell 内填充结构化 blocks（title 粗体 + 子条目缩进）。
    假设 cell 的首段已为空或将被覆写。不清空 cell，不会处理旧内容。
    被 scene_table 和 update_prd_base.set_cell_blocks 共用。

    blocks: list[tuple[str, list[str]]]
    numbered: True 时自动给每个 block 内的主级 line 加 "1./2./3." 前缀
              （已含 "N. " 前缀的 line 保持原样，二级缩进行 "  - " 不编号）。
              prd-template.md 规定"每个模块下用 1./2./3. 数字编号"，默认开启。
    """
    first = True
    for (title, lines) in blocks:
        p = cell.paragraphs[0] if first else cell.add_paragraph()
        is_first_block = first
        first = False
        # \u7b2c\u4e00\u4e2a block \u9876\u8d34 cell \u9876\u90e8\uff0c\u540e\u7eed block \u524d\u7559 6pt \u62c9\u5f00\u5c42\u7ea7
        p.paragraph_format.space_before = Pt(0) if is_first_block else Pt(6)
        p.paragraph_format.space_after = Pt(2)
        if "\uff08\u53d8\u66f4\uff09" in title or "\uff08\u65b0\u589e\uff09" in title:
            tag = "\uff08\u53d8\u66f4\uff09" if "\uff08\u53d8\u66f4\uff09" in title else "\uff08\u65b0\u589e\uff09"
            base = title.replace(tag, "")
            # title 11pt + bold + textHeading\uff1btag \u8d70 mono \u67d3\u8272
            para_run(p, base, font='title', size_pt=11, bold=True, color=C["textHeading"])
            para_run(p, tag, font='mono', size_pt=11, bold=True, color=C["tagChange"])
        else:
            para_run(p, title, font='title', size_pt=11, bold=True, color=C["textHeading"])
        counter = 0
        for line in lines:
            pl = cell.add_paragraph()
            pl.paragraph_format.space_before = Pt(0)
            pl.paragraph_format.space_after = Pt(1)
            stripped = line.lstrip()
            is_sublevel = stripped.startswith("- ") and line != stripped
            if is_sublevel:
                pl.paragraph_format.left_indent = Cm(1.2)
                body = stripped
            else:
                pl.paragraph_format.left_indent = Cm(0.6)
                if numbered and not _NUMBERED_PREFIX_RE.match(line):
                    counter += 1
                    body = f"{counter}. {line}"
                else:
                    body = line
            para_run_md(pl, body, size_pt=9, color=C["textPrimary"])

# ── 文档初始化 ────────────────────────────────────────────────────────────

def init_doc(landscape=True):
    """创建并返回一个配置好页面的 Document 对象"""
    doc = Document()
    section = doc.sections[0]
    if landscape:
        section.page_width  = Cm(27.94)
        section.page_height = Cm(21.59)
        section.orientation = WD_ORIENT.LANDSCAPE
    section.left_margin   = Cm(2.54)
    section.right_margin  = Cm(2.54)
    section.top_margin    = Cm(1.905)
    section.bottom_margin = Cm(1.905)
    return doc

def cover_page(doc, title, subtitle="产品需求文档（PRD）", scope="", meta_rows=None):
    """
    生成封面页
    meta_rows: list of [label, value] 用于文档属性表
    """
    if meta_rows is None:
        meta_rows = []
    _author = get_author()
    if _author and not any(r[0] == "作者" for r in meta_rows):
        meta_rows = [["作者", _author]] + list(meta_rows)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(60)
    p.paragraph_format.space_after = Pt(4)
    para_run(p, title, font='title', size_pt=24, bold=True, color=C["textHeading"])

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    para_run(p, subtitle, font='title', size_pt=14, color=C["textSecondary"])

    if scope:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(30)
        para_run(p, scope, size_pt=10, color=C["textMuted"], italic=True)

    if meta_rows:
        meta_tbl = doc.add_table(rows=len(meta_rows), cols=2)
        meta_tbl.style = 'Table Grid'
        meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, (label, value) in enumerate(meta_rows):
            cell_text(meta_tbl.rows[i].cells[0], label, size_pt=9, bold=True,
                      color=C["textSecondary"], align=WD_ALIGN_PARAGRAPH.RIGHT)
            meta_tbl.rows[i].cells[0].width = Cm(4)
            cell_text(meta_tbl.rows[i].cells[1], value, size_pt=9,
                      color=C["textPrimary"])
            meta_tbl.rows[i].cells[1].width = Cm(14)
