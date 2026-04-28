#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""
update_prd_base.py — PRD 升版/更新的通用辅助函数

与 gen_prd_base.py（新建 PRD）互补，本文件处理「修改已有 docx」场景。

用法（从 projects/{项目}/scripts/ 执行）：
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/prd/scripts'))
    from update_prd_base import *
"""

from docx.shared import Cm, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ── 锚点定位 + 纯插入(反 #6 踩坑) ─────────────────────────────────────────────

def _find_anchor_paragraph(doc, anchor_keyword: str):
    """按 text.strip().startswith(anchor_keyword) 找到第一个匹配段落。
    找不到抛 ValueError,不静默失败(patch 脚本最忌锚点错位)。"""
    for p in doc.paragraphs:
        if p.text.strip().startswith(anchor_keyword):
            return p
    raise ValueError(f"anchor 未命中: {anchor_keyword!r}")


def insert_heading_before(anchor, text: str, level: int = 2):
    """在 anchor 段落之前插入 Heading {level} 段落,run 级样式和 gen_prd_base.h1/h2/h3 一致。

    用途:patch 脚本给 PRD 新增章节(如 6.4 归因漏斗 / 8.3 事件列表)。
    不传 level 默认 H2。anchor 不可为 None。

    对比 anchor.insert_paragraph_before(text):默认产 Normal style,
    Confluence 识别不出层级 → 大纲树失效(memory #2 踩坑)。
    """
    import sys, os
    _DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _DIR)
    from gen_prd_base import C, para_run

    p = anchor.insert_paragraph_before('')
    # 直接改底层 pStyle,绕过 python-docx styles[key] 在重复 styleId 文档下误报
    # KeyError 的 bug(部分 gen_prd_base 产出的 docx 有 Heading1/2 重复定义)
    pPr = p._p.get_or_add_pPr()
    from docx.oxml import OxmlElement
    pStyle = pPr.find(qn('w:pStyle'))
    if pStyle is None:
        pStyle = OxmlElement('w:pStyle')
        pPr.insert(0, pStyle)
    pStyle.set(qn('w:val'), f'Heading{level}')
    # style 只套模板,run 级样式还得手动刷(和 gen_prd_base.h1/h2/h3 对齐)
    if level == 1:
        color, size_pt = C["textHeading"], 16
        _apply_heading_border(p, C["accentBlue"])
    elif level == 2:
        color, size_pt = C["accentBlue"], 13
    else:
        color, size_pt = C["textHeading"], 11
    # 走 para_run + font='title' 确保字体三分工和 gen_prd_base.h1/h2/h3 一致
    para_run(p, text, font='title', size_pt=size_pt, bold=True, color=color)
    return p


def _apply_heading_border(p, hex_color: str):
    """H1 专用的段落下边框。幂等:已有 pBdr 不覆盖。"""
    pPr = p._p.get_or_add_pPr()
    if pPr.find(qn('w:pBdr')) is not None:
        return
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), hex_color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def insert_paragraph_before(anchor, text: str, size_pt: int = 10,
                             bold: bool = False, color: str = None):
    """在 anchor 前插入 Normal 段落。纯插入不覆盖已有段 text。

    设计意图:替代"查下一段落覆盖 text"这种模糊定位(memory #6 踩坑 —
    patch_prd_v3_3.py 因为跳过 2.x 条件太宽,咬到 3. 大标题把 H1 text 覆盖了)。

    硬规则(配 SKILL.md):patch 脚本插入新段落一律用本函数,
    禁止 anchor.insert_paragraph_before(...) 裸调用(会产 Normal 无格式),
    禁止遍历 paragraphs[i+1:i+5] 找"下一段"改 text。
    """
    import sys, os
    _DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _DIR)
    from gen_prd_base import para_run
    p = anchor.insert_paragraph_before('')
    # 走 para_run 默认 body role（Noto Sans SC + Poppins）
    para_run(p, text, size_pt=size_pt, bold=bold, color=color)
    return p


def insert_scene_blocks(anchor, blocks, heading_level: int = 3):
    """在 anchor 段前批量插入「H{level} 小节标题 + numbered list」结构,
    用于 body 级别的 Scene 详细说明(纯后台 / CMS / 无截图场景降级写法,
    替代 scene_table 2 列表格)。视觉与 gen_prd_base.fill_cell_blocks 对齐。

    blocks: list[tuple[str, list[str]]]
            [(section_title, [line1, line2, ...]), ...]
            line 支持 `**label**：content` 内联 bold(通过 para_run_md 解析);
            以 `  - ` 开头的行作为二级缩进,不编号;
            已含 `N. ` 前缀的行保持原样(不重复编号)。
    heading_level: 默认 H3(3)。

    用途场景:CMS 管理后台等「本次无 UI 改动 / 无独立截图」的 Scene 章节,
    用 H2 场景标题 + 本函数展开子章节,避免 scene_table 左列空截图占位符冗余。
    """
    import sys, os
    _DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _DIR)
    from gen_prd_base import para_run_md, C
    from docx.shared import Cm
    import re
    _NUMBERED_PREFIX_RE = re.compile(r"^\d+\.\s")

    for (title, lines) in blocks:
        insert_heading_before(anchor, title, level=heading_level)
        counter = 0
        for line in lines:
            stripped = line.lstrip()
            is_sublevel = stripped.startswith("- ") and line != stripped
            p = anchor.insert_paragraph_before('')
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(1)
            if is_sublevel:
                p.paragraph_format.left_indent = Cm(0.9)
                body = stripped
            else:
                p.paragraph_format.left_indent = Cm(0.3)
                if not _NUMBERED_PREFIX_RE.match(line):
                    counter += 1
                    body = f"{counter}. {line}"
                else:
                    body = line
            para_run_md(p, body, size_pt=10, color=C["textPrimary"])


def remove_table(table):
    """从 body 中移除整张 table(含所有 row / cell)。
    配合 insert_scene_blocks 做「去 scene_table、改 H3 + numbered list」重构。
    """
    table._element.getparent().remove(table._element)


def insert_description_after(doc, anchor_keyword: str, text: str,
                              size_pt: int = 10) -> 'Paragraph':
    """找到 anchor_keyword 段,在其后插入描述段。锚点未命中抛异常,
    不做"跳过若干段找位置"的模糊定位。

    实现:定位到 anchor 的下一段,在下一段之前插入 → 等价于 anchor 后插入。
    anchor 已经是文档最后一段时直接 doc.add_paragraph。
    """
    anchor = _find_anchor_paragraph(doc, anchor_keyword)
    # python-docx 没有 insert_paragraph_after,用 anchor 下一段的 before 代替
    body = anchor._p.getparent()
    idx = list(body).index(anchor._p)
    if idx + 1 < len(body):
        next_elem = body[idx + 1]
        # 构造 Paragraph wrapper 用 insert_paragraph_before
        from docx.text.paragraph import Paragraph
        next_para = Paragraph(next_elem, anchor._parent)
        p = next_para.insert_paragraph_before('')
    else:
        p = doc.add_paragraph()
    import sys, os
    _DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _DIR)
    from gen_prd_base import para_run
    # 走 para_run 默认 body role
    para_run(p, text, size_pt=size_pt)
    return p


# ── 上游工具(保持原位) ──────────────────────────────────────────────────────

# ── fix_dpi ────────────────────────────────────────────────────────────────────

def fix_dpi(png_path: str, dpi: int = 144) -> str:
    """
    修正 @2x 截图 DPI 元数据（Playwright deviceScaleFactor=2 输出 72dpi，
    python-docx 按 DPI 推算尺寸会导致截图虚化）。

    原地修改，返回原路径。
    """
    from PIL import Image
    img = Image.open(png_path)
    img.save(png_path, dpi=(dpi, dpi))
    return png_path


# ── 段落级操作 ─────────────────────────────────────────────────────────────────

def replace_para_text(para, new_text: str):
    """
    整体替换段落文字，保留第一个 run 的格式（字号/粗体/颜色）。
    后续 run 清空。
    """
    if para.runs:
        para.runs[0].text = new_text
        for r in para.runs[1:]:
            r.text = ''
    else:
        para.add_run(new_text)


def search_replace_para(para, old: str, new: str) -> bool:
    """
    段落内搜索替换（跨 run 拼接后匹配）。
    替换成功返回 True，未命中返回 False。保留第一个 run 的格式。
    """
    full = ''.join(r.text for r in para.runs)
    if old not in full:
        return False
    new_full = full.replace(old, new)
    if para.runs:
        para.runs[0].text = new_full
        for r in para.runs[1:]:
            r.text = ''
    return True


# ── 单元格级操作 ──────────────────────────────────────────────────────────────

def set_cell_text(cell, text: str):
    """
    清空单元格所有内容，在首段写入纯文本。
    保留首段首 run 的格式；无 run 则新建。
    """
    # 清空所有段落文字
    for para in cell.paragraphs:
        for run in para.runs:
            run.text = ''
    # 移除多余段落（只留第一个）
    while len(cell.paragraphs) > 1:
        p = cell.paragraphs[-1]
        p._element.getparent().remove(p._element)
    # 写入
    p = cell.paragraphs[0]
    if p.runs:
        p.runs[0].text = text
    else:
        p.add_run(text)


def set_cell_blocks(cell, blocks, numbered=True):
    """
    清空单元格，按结构化 blocks 重建（title 粗体 + 子条目缩进 + 「（变更）」「（新增）」染色）。
    视觉和 gen_prd_base.scene_table 的右列一致。

    用途：升版/更新 PRD 时，给 Scene 表格右列或后台 table 的复杂内容做结构化替换，
          替代 set_cell_text —— 后者只能单 run 纯文本，没有层次。

    参数：
        cell   — python-docx Table cell
        blocks — list[tuple[str, list[str]]]
                 [(title, [line1, line2, ...]), ...]
                 title 含「（变更）」或「（新增）」会自动拆 run 染成强调色。

    示例：
        set_cell_blocks(cell, [
            ("合格投资者校验（R1/R2）", [
                "进入认购流程前后端双重校验：QI 认证 + 风险匹配",
                "校验通过：展示绿色 Badge；失败：拦截 + 引导认证",
            ]),
            ("基金信息展示（变更）", [
                "产品全称 + 风险等级标签",
                "单位净值 + 成立以来收益率",
            ]),
        ])
    """
    # 清空 cell 所有现有内容（文字 + 图片）
    for para in cell.paragraphs:
        para.clear()
    # 仅保留第一个段落壳
    while len(cell.paragraphs) > 1:
        p = cell.paragraphs[-1]
        p._element.getparent().remove(p._element)
    # 调用 gen_prd_base 的公共填充逻辑（避免 DRY 违反）
    import os, sys
    _DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _DIR)
    from gen_prd_base import fill_cell_blocks
    fill_cell_blocks(cell, blocks, numbered=numbered)


def replace_cell_image(cell, img_path: str, width_cm: float = 7.0):
    """
    清空单元格（文字+旧图），插入新截图。
    内部强制调用 fix_dpi()，确保 docx 里不虚化。

    参数：
        cell       — python-docx Table cell
        img_path   — PNG 文件路径（str 或 Path）
        width_cm   — 插入宽度，前端 Scene 建议 7.0，App 建议 5.0
    """
    img_path = str(img_path)
    fix_dpi(img_path)

    # 清空所有段落内容（文字 + drawing）
    for para in cell.paragraphs:
        para.clear()
    # 移除多余段落，只留一个
    while len(cell.paragraphs) > 1:
        p = cell.paragraphs[-1]
        p._element.getparent().remove(p._element)
    # 插入图片
    p = cell.paragraphs[0]
    run = p.add_run()
    run.add_picture(img_path, width=Cm(width_cm))


def replace_cell_image_keep_title(cell, scene_title: str, img_path: str, width_cm: float = 5.0):
    """清空 cell 占位 → 保留场景标题（首段）→ 插入截图（次段）。

    替代 replace_cell_image 用于 scene_table 左列：后者会把 scene_table 写在 cell 内的
    场景标题段（"📱 B-1 · ..."）也清掉，导致 Confluence 页面看不出图属于哪个场景。

    Felix 反馈（memory `feedback_prd_iter_screenshot_pitfalls.md` 坑 2）：
        「你这些怎么都没写具体是哪个页面？」

    用法：
        from update_prd_base import replace_cell_image_keep_title
        # 从 cell 首段提取场景标题
        title = cell.paragraphs[0].text.split('\\n')[0].strip()
        replace_cell_image_keep_title(cell, title, png_path, width_cm=5.0)

    prd_screenshots.py 的 insert_into_docx 已自动在 cell 首段含 `📱 X-N · ...` 时调用本函数。
    """
    import sys, os
    _DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _DIR)
    from gen_prd_base import C, para_run
    from docx.shared import Cm, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    fix_dpi(str(img_path))
    for para in cell.paragraphs:
        para.clear()
    while len(cell.paragraphs) > 1:
        p = cell.paragraphs[-1]
        p._element.getparent().remove(p._element)

    p1 = cell.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(4)
    p1.paragraph_format.space_after = Pt(4)
    para_run(p1, scene_title, size_pt=9, color=C["textMuted"], italic=True)

    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.add_run().add_picture(str(img_path), width=Cm(width_cm))


# ── 标题样式归一化 ─────────────────────────────────────────────────────────────

def normalize_headings(doc):
    """
    修旧 docx 的 H1/H2 样式:补 run 级字色/字号/粗体 + H1 补下划线 pBdr。
    旧脚本常用 add_paragraph(style='Heading 1') 直接产段落,run 级属性缺失,
    渲染效果取决于 Word 默认 style(黑无线),和 gen_prd_base.h1()/h2() 产出的标准
    视觉不一致。本函数幂等:已有 run 属性的跳过不覆盖。

    H1: fg=#141413 (Anthropic Dark) + 16pt + bold + 段落下边框 #D97757 (terra cotta)
    H2: fg=#D97757 + 13pt + bold

    返回修复数 (h1_count, h2_count)。
    """
    import sys, os
    _DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _DIR)
    from gen_prd_base import C

    h1_fixed = h2_fixed = 0
    for p in doc.paragraphs:
        s = p.style.name if p.style else ""
        if s == "Heading 1":
            _apply_heading_style(p, C["textHeading"], 16, add_border=C["accentBlue"])
            h1_fixed += 1
        elif s == "Heading 2":
            _apply_heading_style(p, C["accentBlue"], 13, add_border=None)
            h2_fixed += 1
    return h1_fixed, h2_fixed


def _apply_heading_style(p, hex_color, size_pt, add_border=None):
    """给 heading 段落强制刷 run 样式,可选追加段落下边框。
    强制覆盖颜色/字号/粗体/字体:老 docx 里即使 H1 已设错颜色(如黑色)也统一刷成标准色,
    字体强制刷成 title role（Lora + Noto Serif SC）对齐 gen_prd_base.h1/h2。
    """
    import sys, os
    _DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _DIR)
    from gen_prd_base import FONT
    cfg = FONT['title']
    for r in p.runs:
        r.font.color.rgb = RGBColor.from_string(hex_color)
        r.font.size = Pt(size_pt)
        r.bold = True
        r.font.name = cfg['ascii']
        # 强制刷 rFonts，让中英文都走 title 字体
        rPr = r._r.get_or_add_rPr()
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = OxmlElement('w:rFonts')
            rPr.insert(0, rFonts)
        rFonts.set(qn('w:ascii'), cfg['ascii'])
        rFonts.set(qn('w:hAnsi'), cfg['ascii'])
        rFonts.set(qn('w:eastAsia'), cfg['eastAsia'])
    # 无 run(段落只有 text 没 run)时新建一个 - 走 para_run 含字体配置
    if not p.runs and p.text:
        text = p.text
        for child in list(p._p):
            if child.tag.endswith('}r') or child.tag.endswith('}t'):
                p._p.remove(child)
        from gen_prd_base import para_run
        para_run(p, text, font='title', size_pt=size_pt, bold=True, color=hex_color)
    # 段落下边框(H1 专用)
    if add_border:
        pPr = p._p.get_or_add_pPr()
        if pPr.find(qn('w:pBdr')) is None:
            pBdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), '6')
            bottom.set(qn('w:space'), '1')
            bottom.set(qn('w:color'), add_border)
            pBdr.append(bottom)
            pPr.append(pBdr)


def normalize_fonts(doc):
    """老 docx 升版：把硬编码 Arial / Microsoft YaHei 替换为 prd-docx-styles 设计字体。

    覆盖：
    1. styles.xml docDefaults rFonts 写死 → 改为 themed (minorHAnsi/minorEastAsia)。
       让 Word 找不到 run 级字体时 fallback 到主题字体（Mac 走 PingFang+Calibri，
       Win 走 Microsoft YaHei+Calibri），而不是 substitute 成 Arial。
    2. 所有 run rFonts：老 ascii (Arial/Calibri/Times/Source Serif 4/Plus Jakarta Sans) → Poppins；
       老 eastAsia (Arial/Microsoft YaHei/SimSun/HarmonyOS Sans SC 等) → Noto Sans SC。
       已是设计字体的 run 不动。

    背景：framework 美学切到 Anthropic 官方 brand-guidelines 后，PRD 字体规范升到
    Lora / Poppins / Noto Serif SC / Noto Sans SC / JetBrains Mono。本函数把老字体
    （含上一代 Source Serif 4 / Plus Jakarta Sans / HarmonyOS Sans SC）一次刷成新规范。

    幂等。返回 (run_changed, defaults_changed)。
    """
    LEGACY_ASCII = {'Arial', 'Calibri', 'Times New Roman', 'Times',
                    'Helvetica', 'Roboto', 'Open Sans',
                    'Source Serif 4', 'Plus Jakarta Sans', 'Inter'}
    LEGACY_EAST = {'Arial', 'Microsoft YaHei', '微软雅黑', 'SimSun', '宋体',
                   'SimHei', '黑体', 'STSong', 'STHeiti',
                   'HarmonyOS Sans SC'}
    DESIGN = {'Lora', 'Poppins', 'Noto Serif SC',
              'Noto Sans SC', 'JetBrains Mono', 'PingFang SC'}

    # 1. docDefaults → themed
    defaults_changed = False
    styles_el = doc.styles.element
    docDefaults = styles_el.find(qn('w:docDefaults'))
    if docDefaults is not None:
        rPrDefault = docDefaults.find(qn('w:rPrDefault'))
        if rPrDefault is not None:
            rPr = rPrDefault.find(qn('w:rPr'))
            if rPr is not None:
                rFonts = rPr.find(qn('w:rFonts'))
                if rFonts is not None:
                    has_legacy = any(
                        rFonts.get(qn(f'w:{k}')) in (LEGACY_ASCII | LEGACY_EAST)
                        for k in ('ascii', 'hAnsi', 'eastAsia', 'cs')
                    )
                    if has_legacy:
                        for k in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
                            attr = qn(f'w:{k}')
                            if attr in rFonts.attrib:
                                del rFonts.attrib[attr]
                        rFonts.set(qn('w:asciiTheme'), 'minorHAnsi')
                        rFonts.set(qn('w:hAnsiTheme'), 'minorHAnsi')
                        rFonts.set(qn('w:eastAsiaTheme'), 'minorEastAsia')
                        rFonts.set(qn('w:cstheme'), 'minorBidi')
                        defaults_changed = True

    # 2. 所有 run rFonts：老字体 / 缺失 → 强制设 body 设计字体
    #    rFonts 缺失的 run 不能让它走 docDefaults themed（Cambria + 宋体），
    #    必须显式写 design 字体让 Word for Mac 走系统 substitute（SF Pro / PingFang），
    #    跟 SOP 手册渲染一致。
    run_changed = 0
    W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    for r in doc.element.body.iter(f'{{{W}}}r'):
        rPr = r.find(qn('w:rPr'))
        if rPr is None:
            rPr = OxmlElement('w:rPr')
            r.insert(0, rPr)
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = OxmlElement('w:rFonts')
            rFonts.set(qn('w:ascii'), 'Poppins')
            rFonts.set(qn('w:hAnsi'), 'Poppins')
            rFonts.set(qn('w:eastAsia'), 'Noto Sans SC')
            rPr.insert(0, rFonts)
            run_changed += 1
            continue
        changed = False
        for slot, default_font, legacy_set in (
            ('ascii',    'Poppins',       LEGACY_ASCII),
            ('hAnsi',    'Poppins',       LEGACY_ASCII),
            ('eastAsia', 'Noto Sans SC',  LEGACY_EAST),
        ):
            v = rFonts.get(qn(f'w:{slot}'))
            if v is None or (v in legacy_set and v not in DESIGN):
                rFonts.set(qn(f'w:{slot}'), default_font)
                changed = True
        if changed:
            run_changed += 1

    return run_changed, defaults_changed


def ensure_theme(docx_path):
    """python-docx 生成的 docx 缺 word/theme/theme1.xml；docDefaults 的 themed 引用
    （minorHAnsi/minorEastAsia）会悬空，Word 只能 fallback 到 Arial。

    本函数把 .claude/skills/prd/scripts/assets/theme1.xml 标准 Office 主题注入 docx zip：
      - 写 word/theme/theme1.xml
      - [Content_Types].xml 加 theme override
      - word/_rels/document.xml.rels 加 theme relationship

    幂等：已有 theme1.xml 直接返回 False。

    用法：doc.save() **之后**调用，传入 docx 文件路径（不能传 Document 对象）。
    """
    import zipfile
    import shutil
    import os
    _DIR = os.path.dirname(os.path.abspath(__file__))
    THEME_XML = os.path.join(_DIR, 'assets', 'theme1.xml')
    if not os.path.exists(THEME_XML):
        return False

    docx_path = str(docx_path)
    with zipfile.ZipFile(docx_path) as z:
        if 'word/theme/theme1.xml' in z.namelist():
            return False

    with open(THEME_XML, 'rb') as f:
        theme_bytes = f.read()

    THEME_OVERRIDE = (
        '<Override PartName="/word/theme/theme1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
    )
    THEME_REL = (
        '<Relationship Id="rIdTheme1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" '
        'Target="theme/theme1.xml"/>'
    )

    temp_path = docx_path + '.temp'
    with zipfile.ZipFile(docx_path) as zin:
        with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == '[Content_Types].xml':
                    s = data.decode('utf-8')
                    if 'theme/theme1.xml' not in s:
                        s = s.replace('</Types>', THEME_OVERRIDE + '</Types>')
                    data = s.encode('utf-8')
                elif item.filename == 'word/_rels/document.xml.rels':
                    s = data.decode('utf-8')
                    if 'theme1.xml' not in s:
                        s = s.replace('</Relationships>', THEME_REL + '</Relationships>')
                    data = s.encode('utf-8')
                zout.writestr(item, data)
            zout.writestr('word/theme/theme1.xml', theme_bytes)
    shutil.move(temp_path, docx_path)
    return True


def normalize_punctuation(doc):
    """
    中文标点规范化:中文相邻的半角 , : ( ) 改为全角 ，：（）。
    遵循 soul.md「中文里禁止混半角逗号冒号括号」。
    幂等;保留 run 级样式(bold / color 不变)。

    段落级判定:拼接段落所有 run 的文字后做上下文判断,避免 run 边界把
    「中文<run1 end>:<run2 start>英文」这种场景看成孤立冒号漏改。

    判定规则:
      - 半角 , : ( ) 只要左右任一是中文字符 → 替换全角
      - 排除 URL 场景:前 6 字符含 http / ftp
    代码/URL/纯英文上下文不触发(两侧都没中文)。
    """
    import re
    CJK_RE = re.compile(r'[\u4e00-\u9fff]')
    MAP = {',': '\uff0c', ':': '\uff1a', '(': '\uff08', ')': '\uff09'}

    def process_paragraph(p):
        runs = p.runs
        if not runs: return 0
        # 拼接 + 记录 run 边界
        full = ''.join(r.text or '' for r in runs)
        if not any(c in MAP for c in full): return 0

        out = list(full)
        for i, c in enumerate(full):
            if c not in MAP: continue
            prev = full[i-1] if i > 0 else ''
            nxt  = full[i+1] if i+1 < len(full) else ''
            if not (CJK_RE.match(prev) or CJK_RE.match(nxt)):
                continue
            if c == ':':
                window = full[max(0, i-6):i].lower()
                if 'http' in window or 'ftp' in window:
                    continue
            out[i] = MAP[c]

        new_full = ''.join(out)
        if new_full == full: return 0

        # 按原 run 边界切回写入;替换都是 1:1 字符,偏移不变
        n = 0
        pos = 0
        for r in runs:
            L = len(r.text or '')
            new_slice = new_full[pos:pos+L]
            if new_slice != (r.text or ''):
                r.text = new_slice
                n += sum(1 for a, b in zip(r.text, full[pos:pos+L]) if a != b)
            pos += L
        return n

    total = 0
    for p in doc.paragraphs:
        total += process_paragraph(p)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    total += process_paragraph(p)
    return total


# ── humanize / scene-cell helpers（讲人话规则 + cell 拆分）────────────────

CIRCLE_NUMS = {'①': '1.', '②': '2.', '③': '3.', '④': '4.', '⑤': '5.',
               '⑥': '6.', '⑦': '7.', '⑧': '8.', '⑨': '9.', '⑩': '10.'}


def _humanize_text(text: str, scene_to_human: list = None) -> str:
    """正文文本去 PM 内部场景编号 + 圈数字归一。

    步骤：
      1. 多编号串括号整体删（「（A-1 ~ A-4）」「（D-0 / D-1 / D-3）」）
      2. 单编号括号删（「(D-2)」「（A-3b）」）
      3a. 编号紧跟中文 → 仅删编号（保留中文实词，避免「编号→白话」与原文重复）
      3b. 剩余孤立编号 → 查 scene_to_human 表替换为白话
      4. 圈数字 ①②③ → 1./2./3.
      5. cleanup（连续空格 / 残留空括号）

    Args:
        text: 原始段落文本
        scene_to_human: list of (code, human) tuples, 长前缀优先排序
                        如 [('A-3b', '红包弹窗'), ('A-1', '直播间主页'), ...]
                        None 时跳过孤立编号替换（仅做删括号 + 圈数字）
    """
    import re
    if not text:
        return text
    text = re.sub(
        r'(?:（|\()\s*[A-GM]-\d+[a-z]?(?:\s*[~～\-/／、，,]\s*[A-GM]-\d+[a-z]?)+\s*(?:）|\))',
        '', text)
    text = re.sub(r'(?:（|\()\s*[A-GM]-\d+[a-z]?\s*(?:）|\))', '', text)
    text = re.sub(
        r'(?<![A-Za-z0-9-])[A-GM]-\d+[a-z]?\s+(?=[一-鿿])',
        '', text)
    if scene_to_human:
        for code, human in scene_to_human:
            text = re.sub(
                rf'(?<![A-Za-z0-9-]){re.escape(code)}(?![A-Za-z0-9-])',
                human, text)
    for old, new in CIRCLE_NUMS.items():
        text = text.replace(old, new)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'（\s*）|\(\s*\)', '', text)
    text = re.sub(r'\s+([，。；：、])', r'\1', text)
    return text


def humanize_doc(doc, scene_to_human: list = None):
    """全文 humanize：去 PM 内部场景编号、归一圈数字。

    保留位置：
      - H1/H2/H3 章节标题（章节 anchor 保留场景编号合规）
      - scene_table cell[0] anchor 标题（📱/🖥/🔧 开头）
      - 场景地图表 cell[0] 编号列（纯编号格式）

    SKILL.md 硬规则 #11：正文禁用 PM 内部场景编号（A-N/B-N/C-N/D-N/E-N/F-N/M-N），
    本 helper 是该规则的执行入口。

    Args:
        doc: python-docx Document
        scene_to_human: 见 _humanize_text；None 时不做白话替换
    """
    import re
    for p in doc.paragraphs:
        style_name = p.style.name if (p.style and p.style.name) else ''
        if style_name.startswith('Heading'):
            continue
        new_text = _humanize_text(p.text, scene_to_human)
        if new_text != p.text:
            replace_para_text(p, new_text)
    for t in doc.tables:
        for ri, row in enumerate(t.rows):
            for ci, cell in enumerate(row.cells):
                cell_text = cell.text
                if ci == 0 and (
                    cell_text.startswith('📱') or
                    cell_text.startswith('🖥') or
                    cell_text.startswith('🔧')
                ):
                    continue
                if ci == 0 and ri >= 1 and re.match(
                        r'^[A-GM]-\d+[a-z]?$', cell_text.strip()):
                    continue
                for p in cell.paragraphs:
                    style_name = p.style.name if (p.style and p.style.name) else ''
                    if style_name.startswith('Heading'):
                        continue
                    new_text = _humanize_text(p.text, scene_to_human)
                    if new_text != p.text:
                        replace_para_text(p, new_text)


def cell_paragraphs_to_blocks(cell):
    """识别 scene_table 右列 cell 内的 (title, lines) 块结构。

    兼容两种 V2.7-era docx 的 cell 模式：

    模式 A（title=bold + 无空段 + line 自带 1./2./3.）— T9/E-2 风格：
        title (bold) → 1. line → 2. line → next title (bold) → ...
    模式 B（title=普通 + 空段分隔 + line 平铺无编号）— T20/C-3 风格：
        title → line → line → 空段 → next title → ...

    通用规则：空段 OR bold 段 = block 强分隔符；
            分隔符之间第一段是 title，其余是 lines。

    返回 list[tuple[str, list[str]]] 格式，可直接喂 set_cell_blocks(cell, blocks)。
    """
    blocks = []
    cur_title = None
    cur_lines = []

    def flush():
        nonlocal cur_title, cur_lines
        if cur_title is not None:
            blocks.append((cur_title, cur_lines))
        cur_title = None
        cur_lines = []

    for p in cell.paragraphs:
        t = p.text.strip()
        if not t:
            flush()
            continue
        is_bold = bool(p.runs) and bool(p.runs[0].bold)
        if is_bold and (cur_title is not None or cur_lines):
            flush()
        if cur_title is None:
            cur_title = t
        else:
            cur_lines.append(t)
    flush()
    return blocks


def fix_scene_cell_numbering(doc):
    """扫所有 scene_table 右列，≥4 段时用 cell_paragraphs_to_blocks 拆分后
    用 set_cell_blocks 重写，统一为「title 11pt bold + lines 9pt 0.6cm 缩进 + 自动编号」。

    跳过条件：
      - 表第一列非 scene_table anchor（不以 📱/🖥/🔧 开头）
      - cell 段 < 4（描述太短，加 numbered 反而冗余）
      - 单 block 且 lines < 2（无意义层次）

    背景：V2.7-era docx 的 scene_table 右列内容 mixed 风格不一致（有 numbered
    有平铺）。本 helper 统一为 set_cell_blocks 风格，配合 fill_cell_blocks 的
    11pt title + 9pt 缩进编号渲染。
    """
    import re
    for t in doc.tables:
        if not t.rows:
            continue
        if len(t.rows[0].cells) < 2:
            continue
        cell0_text = t.rows[0].cells[0].text.strip()
        if not (cell0_text.startswith('📱') or cell0_text.startswith('🖥') or cell0_text.startswith('🔧')):
            continue
        cell = t.rows[0].cells[1]
        if len(cell.paragraphs) < 4:
            continue
        blocks = cell_paragraphs_to_blocks(cell)
        if not blocks:
            continue
        if len(blocks) == 1 and len(blocks[0][1]) < 2:
            continue
        set_cell_blocks(cell, blocks, numbered=True)
