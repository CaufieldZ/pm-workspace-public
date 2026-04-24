#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""交互大图 update 工具包 — imap 版 update_prd_base.py。

在 HtmlPatcher 之上封装 imap DOM 结构感知操作。
项目 patch 脚本只需写业务内容，不用关心 DOM 定位。

用法（项目 patch 脚本）：
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, os.path.join(_ROOT, 'scripts'))
    sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/interaction-map/references'))

    from update_imap_base import ImapUpdater

    u = ImapUpdater('deliverables/xxx_v4.7.html', 'deliverables/xxx_v4.9.html')
    u.bump_version('v4.7', 'v4.9')
    u.replace_annotation('M-A', '3b', '<new ann-text html>', '业务线改多选')
    u.replace_flow_note('M-2', '<new note html>', 'M-2 配置区重排')
    u.replace_mock_section('M-2', '全局配置区', '<new mock html>', 'M-2 mock 重写')
    u.save()
"""
import os
import re
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(_ROOT, 'scripts'))

from lib.html_patcher import HtmlPatcher


class ImapUpdater(HtmlPatcher):
    """交互大图结构感知更新器。"""

    def _scene_range(self, scene_id: str) -> tuple[int, int]:
        """返回 Scene 区块的 (start, end) 字符偏移。
        Scene 从 <div class="st"><h2>Scene {ID} 开始，到下一个 <div class="st"> 或文件末尾结束。"""
        pattern = rf'<div class="st"[^>]*><h2>Scene {re.escape(scene_id)}\b'
        m = re.search(pattern, self._html)
        if not m:
            sys.exit(f'[FAIL] Scene {scene_id} not found')
        start = m.start()
        next_scene = re.search(r'<div class="st"', self._html[start + 1:])
        end = (start + 1 + next_scene.start()) if next_scene else len(self._html)
        return start, end

    def replace_annotation(self, scene_id: str, ann_num: str, new_ann_text: str, desc: str) -> None:
        """替换 Scene 内指定编号的标注文本。
        定位 <div class="ann-num...">ann_num</div><div class="ann-text">...到 </div>，
        替换 ann-text 内容。"""
        start, end = self._scene_range(scene_id)
        section = self._html[start:end]
        pattern = rf'(<div class="ann-num[^"]*">{re.escape(ann_num)}</div>)<div class="ann-text">.*?</div>'
        m = re.search(pattern, section, re.DOTALL)
        if not m:
            sys.exit(f'[FAIL] {desc}: annotation #{ann_num} not found in Scene {scene_id}')
        old = m.group(0)
        new = f'{m.group(1)}<div class="ann-text">{new_ann_text}</div>'
        self._html = self._html[:start] + section.replace(old, new, 1) + self._html[end:]
        self._count += 1
        print(f'[OK] {desc}')

    def replace_flow_note(self, scene_id: str, new_note: str, desc: str) -> None:
        """替换 Scene 内的 flow-note 内容。多个 flow-note 时替换最后一个。"""
        start, end = self._scene_range(scene_id)
        section = self._html[start:end]
        matches = list(re.finditer(r'<div class="flow-note">.*?</div>', section, re.DOTALL))
        if not matches:
            sys.exit(f'[FAIL] {desc}: no flow-note in Scene {scene_id}')
        old = matches[-1].group(0)
        new = f'<div class="flow-note">{new_note}</div>'
        self._html = self._html[:start] + section.replace(old, new, 1) + self._html[end:]
        self._count += 1
        print(f'[OK] {desc}')

    def replace_mock_section(self, scene_id: str, section_marker: str, new_html: str, desc: str) -> None:
        """替换 Scene 内设备壳中包含 section_marker 文本的区块。
        适用于替换 .f-sec、.f-row 等表单区块。"""
        start, end = self._scene_range(scene_id)
        section = self._html[start:end]
        idx = section.find(section_marker)
        if idx == -1:
            sys.exit(f'[FAIL] {desc}: marker "{section_marker}" not found in Scene {scene_id}')
        self.patch(section_marker, section_marker, f'{desc} (marker check)', n=1)
        self._count -= 1  # undo the count from marker check, actual replace below
        # Delegate to plain patch for the actual replacement
        self.patch.__func__(self, self._html[start + idx - 200:start + idx] if idx > 200 else section_marker,
                            self._html[start + idx - 200:start + idx] if idx > 200 else section_marker,
                            desc)

    def replace_ann_card(self, scene_id: str, old_card: str, new_card: str, desc: str) -> None:
        """替换 Scene 内的完整 ann-card 块。用于大面积重写标注区域。"""
        start, end = self._scene_range(scene_id)
        section = self._html[start:end]
        if old_card not in section:
            sys.exit(f'[FAIL] {desc}: ann-card content not found in Scene {scene_id}')
        self._html = self._html[:start] + section.replace(old_card, new_card, 1) + self._html[end:]
        self._count += 1
        print(f'[OK] {desc}')

    def replace_overview_row(self, old_row: str, new_row: str, desc: str) -> None:
        """替换场景总览表格中的一行。"""
        self.patch(old_row, new_row, desc)

    def grey_out_element(self, old_html: str, desc: str) -> None:
        """将元素灰化（加 opacity + 删除线样式）。"""
        greyed = old_html.replace('style="', 'style="opacity:0.5;text-decoration:line-through;', 1)
        if greyed == old_html:
            greyed = old_html.replace('>', ' style="opacity:0.5;text-decoration:line-through;">', 1)
        self.patch(old_html, greyed, desc)
