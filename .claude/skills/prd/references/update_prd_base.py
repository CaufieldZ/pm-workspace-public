#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""
update_prd_base.py — PRD 升版/更新的通用辅助函数

与 gen_prd_base.py（新建 PRD）互补，本文件处理「修改已有 docx」场景。

用法（从 projects/{项目}/scripts/ 执行）：
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/prd/references'))
    from update_prd_base import *
"""

from docx.shared import Cm
from docx.oxml.ns import qn

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


def set_cell_blocks(cell, blocks):
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
    fill_cell_blocks(cell, blocks)


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
