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
    # 走 para_run 默认 body role（HarmonyOS Sans SC + Plus Jakarta Sans）
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


# ── 标题样式归一化 ─────────────────────────────────────────────────────────────

def normalize_headings(doc):
    """
    修旧 docx 的 H1/H2 样式:补 run 级字色/字号/粗体 + H1 补下划线 pBdr。
    旧脚本常用 add_paragraph(style='Heading 1') 直接产段落,run 级属性缺失,
    渲染效果取决于 Word 默认 style(黑无线),和 gen_prd_base.h1()/h2() 产出的标准
    视觉不一致。本函数幂等:已有 run 属性的跳过不覆盖。

    H1: fg=#1A1A2E + 16pt + bold + 段落下边框 #2E75B6
    H2: fg=#2E75B6 + 13pt + bold

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
    字体强制刷成 title role（Source Serif 4 + Noto Serif SC）对齐 gen_prd_base.h1/h2。
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
