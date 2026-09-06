#!/usr/bin/env python3
"""Confluence storage XML 图片语法读写共享层。

fetch_confluence（读：扫 storage 拿 ri:attachment 引用集）与 md_to_confluence（写：
渲染 ac:image）两端共用同一套图片语法，收口此处避免正则/模板各自硬编码漂移。
"""
from __future__ import annotations

import html
import re


def extract_referenced_images(storage_html: str) -> set[str]:
    """扫 storage 拿 <ri:attachment ri:filename="X"/> 真实引用集合。

    属性值反转义回真实文件名（含 & " 的名字写入时被转义），保证与 Confluence
    attachment API 返回的 title 可直接比对。
    """
    return {
        html.unescape(m)
        for m in re.findall(r'<ri:attachment\s+ri:filename="([^"]+)"', storage_html)
    }


def render_ac_image(filename: str, width: int | str) -> str:
    """单图 → Confluence storage ac:image XML（外层 <p> 包裹 + width 属性 + ri:attachment 自闭合）。

    filename 走 XML 属性转义：含 & " < > 的文件名不转义会生成非法 storage，
    Confluence 直接返 400。普通文件名转义后不变，与 extract_referenced_images 反转义配对。
    """
    return (f'<p><ac:image ac:width="{width}">'
            f'<ri:attachment ri:filename="{html.escape(str(filename), quote=True)}" />'
            f'</ac:image></p>')
