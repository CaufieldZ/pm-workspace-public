#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""PPT 信息文档 update 工具包。

PPT HTML 结构：NAV = JSON 数组，内容在 PAGE_RENDERERS = { 'id': function(c){ c.innerHTML = "..."; }, ... }。
本模块在 HtmlPatcher 之上封装 PPT DOM 结构感知操作。

用法（项目 patch 脚本）：
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, os.path.join(_ROOT, 'scripts'))
    sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/ppt/scripts'))

    from update_ppt_base import PptUpdater

    u = PptUpdater('deliverables/ppt-xxx-v1.html', 'deliverables/ppt-xxx-v2.html')
    u.bump_version('v1', 'v2')
    u.insert_nav_item('risk-core', {'id': 'coin-risk', 'icon': '📉', 'label': '币种差异'})
    u.replace_page_content('overview', '<new page html>')
    u.add_page_renderer('coin-risk', '<page html>', before='risk-core')
    u.save()
"""
import json
import os
import re
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(_ROOT, 'scripts'))

from lib.html_patcher import HtmlPatcher


class PptUpdater(HtmlPatcher):
    """PPT 信息文档结构感知更新器。"""

    def insert_nav_item(self, before_id: str, item: dict, desc: str = "") -> None:
        """在 NAV JSON 数组中 before_id 项前插入新 nav item。
        item: {"id": "xxx", "icon": "📉", "label": "标签"}"""
        marker = f'"id": "{before_id}"'
        idx = self._html.find(marker)
        if idx == -1:
            sys.exit(f'[FAIL] insert_nav_item: nav item "{before_id}" not found')
        brace = self._html.rfind('{', 0, idx)
        indent = '      '
        new_item = json.dumps(item, ensure_ascii=False, indent=8).replace('        ', indent + '  ')
        insertion = f'{indent}{new_item},\n{indent}'
        self._html = self._html[:brace] + insertion + self._html[brace:]
        self._count += 1
        desc = desc or f'insert nav item before {before_id}'
        print(f'[OK] {desc}')

    def remove_nav_item(self, item_id: str, desc: str = "") -> None:
        """从 NAV JSON 数组中移除指定 id 的项。"""
        pattern = rf'\s*\{{\s*"id"\s*:\s*"{re.escape(item_id)}"[^}}]*\}},?'
        m = re.search(pattern, self._html)
        if not m:
            sys.exit(f'[FAIL] remove_nav_item: "{item_id}" not found')
        self._html = self._html[:m.start()] + self._html[m.end():]
        self._count += 1
        desc = desc or f'remove nav item {item_id}'
        print(f'[OK] {desc}')

    def replace_page_content(self, page_id: str, new_html: str, desc: str = "") -> None:
        """替换 PAGE_RENDERERS 中指定 page 的 innerHTML 内容。"""
        escaped_new = self._escape_for_renderer(new_html)
        pattern = rf"('{re.escape(page_id)}'\s*:\s*function\(c\)\s*\{{\s*c\.innerHTML\s*=\s*\").*?(\"\s*;\s*\}})"
        m = re.search(pattern, self._html, re.DOTALL)
        if not m:
            sys.exit(f'[FAIL] replace_page_content: renderer "{page_id}" not found')
        old = m.group(0)
        new = f'{m.group(1)}{escaped_new}{m.group(2)}'
        self._html = self._html.replace(old, new, 1)
        self._count += 1
        desc = desc or f'replace page content: {page_id}'
        print(f'[OK] {desc}')

    def add_page_renderer(self, page_id: str, page_html: str, before: str = "", desc: str = "") -> None:
        """添加新的 PAGE_RENDERER。before 指定插入位置（在哪个 renderer 前面）。"""
        escaped = self._escape_for_renderer(page_html)
        renderer = f"  '{page_id}': function(c) {{ c.innerHTML = \"{escaped}\"; }},\n"
        if before:
            marker = f"  '{before}':"
            idx = self._html.find(marker)
            if idx == -1:
                sys.exit(f'[FAIL] add_page_renderer: renderer "{before}" not found')
            self._html = self._html[:idx] + renderer + self._html[idx:]
        else:
            marker = '};\n\nfunction renderPage'
            idx = self._html.find(marker)
            if idx == -1:
                sys.exit(f'[FAIL] add_page_renderer: could not find PAGE_RENDERERS end')
            self._html = self._html[:idx] + renderer + self._html[idx:]
        self._count += 1
        desc = desc or f'add page renderer: {page_id}'
        print(f'[OK] {desc}')

    def remove_page_renderer(self, page_id: str, desc: str = "") -> None:
        """移除指定 page_id 的 PAGE_RENDERER。"""
        pattern = rf"\s*'{re.escape(page_id)}'\s*:\s*function\(c\)\s*\{{.*?\}},?\n"
        m = re.search(pattern, self._html, re.DOTALL)
        if not m:
            sys.exit(f'[FAIL] remove_page_renderer: "{page_id}" not found')
        self._html = self._html[:m.start()] + self._html[m.end():]
        self._count += 1
        desc = desc or f'remove page renderer: {page_id}'
        print(f'[OK] {desc}')

    @staticmethod
    def _escape_for_renderer(html: str) -> str:
        """将 HTML 转义为 JS 字符串（双引号内）。"""
        return (html
                .replace('\\', '\\\\')
                .replace('"', '\\"')
                .replace('\n', '\\n'))
