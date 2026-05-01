#!/usr/bin/env python3
"""原型 update 工具包 — prototype 版 update_prd_base.py。

在 HtmlPatcher 之上封装 prototype DOM 结构感知操作。

用法（项目 patch 脚本）：
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, os.path.join(_ROOT, 'scripts'))
    sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/prototype/scripts'))

    from update_proto_base import ProtoUpdater

    u = ProtoUpdater('deliverables/xxx_v4.7.html', 'deliverables/xxx_v4.9.html')
    u.bump_version('v4.7', 'v4.9')
    u.replace_element_by_id('acDev0', '<new content>', '替换 Web 设备壳内容')
    u.replace_form_field('其他标签', '<new field html>', '外显标签改单选')
    u.save()
"""
import os
import re
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(_ROOT, 'scripts'))

from lib.html_patcher import HtmlPatcher


class ProtoUpdater(HtmlPatcher):
    """原型结构感知更新器。"""

    def _view_range(self, view_id: str) -> tuple[int, int]:
        """返回 View 区块的 (start, end) 字符偏移。"""
        pattern = rf'id="{re.escape(view_id)}"'
        m = re.search(pattern, self._html)
        if not m:
            sys.exit(f'[FAIL] View #{view_id} not found')
        start = m.start()
        next_view = re.search(r'id="[^"]*-view"', self._html[m.end():])
        end = (m.end() + next_view.start()) if next_view else len(self._html)
        return start, end

    def replace_element_by_id(self, element_id: str, new_inner_html: str, desc: str) -> None:
        """替换指定 id 元素的内部内容。
        定位 id="xxx"，找到对应的开标签和闭标签，替换内部 HTML。"""
        pattern = rf'(id="{re.escape(element_id)}"[^>]*>)(.*?)(</div>)'
        m = re.search(pattern, self._html, re.DOTALL)
        if not m:
            sys.exit(f'[FAIL] {desc}: element #{element_id} not found')
        old = m.group(0)
        new = f'{m.group(1)}{new_inner_html}{m.group(3)}'
        self._html = self._html.replace(old, new, 1)
        self._count += 1
        print(f'[OK] {desc}')

    def replace_form_field(self, field_label: str, new_field_html: str, desc: str) -> None:
        """替换包含指定 label 文本的表单字段行（.f-row）。"""
        pattern = rf'<div class="f-row">.*?{re.escape(field_label)}.*?</div>\s*</div>'
        m = re.search(pattern, self._html, re.DOTALL)
        if not m:
            sys.exit(f'[FAIL] {desc}: form field "{field_label}" not found')
        self._html = self._html.replace(m.group(0), new_field_html, 1)
        self._count += 1
        print(f'[OK] {desc}')

    def replace_gnav_tab(self, old_label: str, new_label: str, desc: str) -> None:
        """替换全局导航 Tab 文本。"""
        self.patch(old_label, new_label, desc)

    def replace_sidebar_item(self, old_text: str, new_html: str, desc: str) -> None:
        """替换侧栏导航项。"""
        pattern = rf'<div class="sb-item[^"]*"[^>]*>.*?{re.escape(old_text)}.*?</div>'
        m = re.search(pattern, self._html, re.DOTALL)
        if not m:
            sys.exit(f'[FAIL] {desc}: sidebar item "{old_text}" not found')
        self._html = self._html.replace(m.group(0), new_html, 1)
        self._count += 1
        print(f'[OK] {desc}')
