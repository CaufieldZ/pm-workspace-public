"""PM 内部场景编号清理 + 圈数字归一。

SKILL.md 硬规则 #11：正文禁用 PM 内部场景编号（A-N/B-N/C-N/D-N/E-N/F-N/M-N），
本模块是该规则的执行入口。
"""
import re

from core.patch import replace_para_text

from .patterns import CIRCLE_NUMS


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
    text = re.sub(r'(\s*\)|\(\s*)', lambda m: '' if m.group() in ('（）', '()') else m.group(), text)
    text = re.sub(r'（\s*）|\(\s*\)', '', text)
    text = re.sub(r'\s+([，。；：、])', r'\1', text)
    return text


def humanize_doc(doc, scene_to_human: list = None):
    """全文 humanize：去 PM 内部场景编号、归一圈数字。

    保留位置：
      - H1/H2/H3 章节标题（章节 anchor 保留场景编号合规）
      - scene_table cell[0] anchor 标题（📱/🖥/🔧 开头）
      - 场景地图表 cell[0] 编号列（纯编号格式）

    Args:
        doc: python-docx Document
        scene_to_human: 见 _humanize_text；None 时不做白话替换
    """
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
                cell_full_text = cell.text
                if ci == 0 and (
                    cell_full_text.startswith('📱') or
                    cell_full_text.startswith('🖥') or
                    cell_full_text.startswith('🔧')
                ):
                    continue
                if ci == 0 and ri >= 1 and re.match(
                        r'^[A-GM]-\d+[a-z]?$', cell_full_text.strip()):
                    continue
                for p in cell.paragraphs:
                    style_name = p.style.name if (p.style and p.style.name) else ''
                    if style_name.startswith('Heading'):
                        continue
                    new_text = _humanize_text(p.text, scene_to_human)
                    if new_text != p.text:
                        replace_para_text(p, new_text)
