"""逐 Scene 组件计数（IMAP 专项）。

迁移自 scripts/check_html.sh:137-167 / audit-fast.sh:137-158。

规则：
IMAP 每个 `id="scene-*"` 块内必须含 `.aw`（流向箭头）/ `.anno`（标注框）/
`.ann-tag`（优先级标签）/ `.flow-note`（屏幕说明）四类。
"""
from __future__ import annotations

import re

REQUIRED_CLASSES = ('aw', 'anno', 'ann-tag', 'flow-note')


def _split_scenes(html_text: str) -> dict[str, str]:
    """按 id="scene-*" 切分，返回 {scene_id: block_text}。"""
    scenes: dict[str, str] = {}
    # 找出所有 scene id 位置
    matches = list(re.finditer(r'id="scene-([^"]+)"', html_text))
    if not matches:
        return scenes
    for i, m in enumerate(matches):
        sid = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html_text)
        scenes[sid] = html_text[start:end]
    return scenes


def count_per_scene_components(html_text: str) -> list[tuple[str, list[str]]]:
    """返回 [(scene_id, missing_classes), ...]，仅含缺组件的 scene。"""
    out: list[tuple[str, list[str]]] = []
    scenes = _split_scenes(html_text)
    for sid, block in scenes.items():
        missing: list[str] = []
        for cls in REQUIRED_CLASSES:
            # class="aw" / class="aw ..." / class="... aw" 都算
            if cls == 'ann-tag':
                # ann-tag 可带后缀（ann-tag-p0 等）
                pat = re.compile(r'class="[^"]*\bann-tag\b')
            else:
                pat = re.compile(rf'class="[^"]*\b{re.escape(cls)}\b')
            if not pat.search(block):
                missing.append(cls)
        if missing:
            out.append((sid, missing))
    return out


def count_global_components(html_text: str) -> dict[str, int]:
    """返回全局组件计数（IMAP 整体卫生扫描）。"""
    counts: dict[str, int] = {}
    for cls in ('aw', 'anno', 'card-title', 'ann-item', 'ann-tag',
                'flow-note', 'info-box'):
        if cls == 'ann-tag':
            pat = re.compile(r'class="[^"]*\bann-tag\b')
        else:
            pat = re.compile(rf'class="[^"]*\b{re.escape(cls)}\b')
        counts[cls] = len(pat.findall(html_text))
    counts['scene'] = len(re.findall(r'id="scene-', html_text))
    return counts
