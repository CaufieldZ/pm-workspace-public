"""渲染 UI 屏内「开发注解」检测 — 防止开发把注解误读为真实文案。

问题：模型在 prototype / IMAP 的实际渲染屏里写开发注解（如
「带单战绩（无资格则不展示，此处隐藏占位）」「广告位（灰条占位）」），
读起来像真实产品文案，开发误以为该处真有这段文字。

口径：
- prototype：整份就是 UI，注解不该出现在任何渲染壳内（.app-mock/.web-front/.layout）。
- IMAP：注解是合法一等功能，但只能在 mockup 外（.ann-card/.flow-note）；
  .phone/.webframe 屏内禁。编号锚点（.phone-label/.anno-n）由 visible_text._is_in_anchor 跳过。

调用方：
- scripts/check_ui_annotation.py（ui-annotation-gate hook）
- scripts/lib/run_voice_checks.py（check_proto.sh / check_imap.sh 手动自检）

规则源：.claude/skills/prototype/SKILL.md + .claude/skills/interaction-map/SKILL.md
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup, Comment, Tag

from .visible_text import SKIP_TAGS, _is_in_anchor

# mockup 根容器：屏内文本 = 渲染 UI，注解禁入
MOCKUP_CLASSES = {
    'proto': {'app-mock', 'web-front', 'layout'},
    'imap': {'phone', 'webframe'},
}

# ── 检测模式（高精度，宁缺毋滥）─────────────────────────────────────────

# 前缀标记：注：/ 说明：/ 备注：/ TODO / FIXME / XXX:（全/半角冒号，前置边界防词中误命中）
ANNOTATION_PREFIX_RE = re.compile(
    r'(?:^|[\s（()【\[、，。])'
    r'(注[:：]|说明[:：]|备注[:：]|TODO|FIXME|XXX[:：])'
)

# 元括注：括号内含元说明词（开发/前后端/占位/示意/动态/接口…）
_META_WORDS = (
    r'此处|这里|示意|占位|待定|待补|'
    r'动态(?:展示|加载|渲染)|接口返回|'
    r'开发(?:注意|时|填)|前端(?:注意|实现)|后端(?:返回|提供)|'
    r'默认显示|实际(?:为|是|文案|数据)|仅(?:为)?示例|示例数据|'
    r'mock|placeholder|可替换|按需替换'
)
ANNOTATION_PAREN_RE = re.compile(
    r'[（(][^）)]*(?:' + _META_WORDS + r')[^）)]*[）)]',
    re.IGNORECASE,
)


def scan_ui_annotation(text):
    """扫描文本，返回命中的 (category, match_str) 列表。

    category ∈ {annotation_prefix, annotation_paren}
    """
    hits = []
    for m in ANNOTATION_PREFIX_RE.finditer(text):
        hits.append(('annotation_prefix', m.group(1)))
    for m in ANNOTATION_PAREN_RE.finditer(text):
        hits.append(('annotation_paren', m.group(0)))
    return hits


def find_mockup_annotations(html_text, kind):
    """在 mockup 渲染屏内查找开发注解。

    kind: 'proto' | 'imap'
    返回 list[(loc, snippet, hits)]，hits = scan_ui_annotation 输出。
    """
    if kind not in MOCKUP_CLASSES:
        raise ValueError(f"kind must be 'proto' or 'imap', got {kind!r}")
    mockup_classes = MOCKUP_CLASSES[kind]

    soup = BeautifulSoup(html_text, 'html.parser')
    selector = ', '.join(f'.{c}' for c in mockup_classes)
    roots = soup.select(selector)
    if not roots:
        return []

    seen = set()  # 去重：节点可能被嵌套 mockup 根重复覆盖
    findings = []
    for root in roots:
        for node in root.descendants:
            if isinstance(node, Tag):
                continue
            # HTML 注释不渲染，开发看不到，不算 UI 文案
            if isinstance(node, Comment):
                continue
            text = str(node).strip()
            if not text:
                continue
            parent = node.parent
            if parent is None:
                continue
            node_id = id(node)
            if node_id in seen:
                continue
            seen.add(node_id)
            # 跳过 script/style 等不可见子树
            if any(a.name in SKIP_TAGS for a in [parent] + list(parent.parents)
                   if isinstance(a, Tag)):
                continue
            # 跳过编号锚点（phone-label / anno-n 等合法 "A-1 · xxx"）
            if _is_in_anchor(node):
                continue
            hits = scan_ui_annotation(text)
            if hits:
                raw_cls = parent.get('class')
                if isinstance(raw_cls, str):  # bs4 单 class 返回 str
                    parent_cls = [raw_cls]
                else:
                    parent_cls = raw_cls or ["?"]
                loc = f"{parent.name}.{parent_cls[0]}"
                findings.append((loc, text[:80], hits))
    return findings
