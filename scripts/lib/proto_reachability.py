"""原型页面可达性 — 检出「页面存在但点不到」与「跳转指向不存在的页面」。

骨架原型（build_proto_skeleton）把每个页面渲染成 `<div class="p-page" data-page="{id}">`，
页面间跳转全靠 `goPage('{id}')`。若某页无任何 goPage 指向它，评审时只能改代码才能看到，
等同于没做；若 goPage 指向不存在的 id，点了直接黑屏。

可达性按 BFS 算：入口页（class 含 `show`）→ 页内 goPage → 逐层展开；
页面块以外的 goPage（顶栏 logo / 抽屉 / footer）算全局链接，任意页都能点到。

死链分两级：静态 HTML 里的 onclick 是真死链（页面上就有这个按钮）；只出现在 <script>
里的，多端拆分时常是另一端的共享 JS 片段（被 `if(!el) return` 兜住跑不到），只给 warn。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_PAGE_OPEN_RE = re.compile(r'<div\b[^>]*\bdata-page="([^"]+)"[^>]*>')
_DIV_TAG_RE = re.compile(r'<div\b[^>]*>|</div>')
_SCRIPT_RE = re.compile(r'<script\b.*?</script>', re.S)
# 同时覆盖 onclick="goPage('x')" 与 JS 字符串内 goPage(\'x\')
_GOPAGE_RE = re.compile(r'goPage\(\s*\\?[\'"]([^\'"\\]+)')


@dataclass
class Reachability:
    """检查结果。entry 为 None 表示非骨架原型（无 data-page），调用方跳过。"""

    entry: str | None = None
    unreachable: list[str] = field(default_factory=list)
    dead_static: list[str] = field(default_factory=list)
    dead_script: list[str] = field(default_factory=list)


def _page_end(html: str, start: int) -> int:
    """从页面 div 开标签起做 div 深度配对，返回闭合 </div> 之后的索引。"""
    depth = 0
    for m in _DIV_TAG_RE.finditer(html, start):
        if m.group().startswith('</'):
            depth -= 1
            if depth == 0:
                return m.end()
        else:
            depth += 1
    return len(html)


def _targets(text: str) -> set[str]:
    return set(_GOPAGE_RE.findall(text))


def check_page_reachability(html_text: str) -> Reachability:
    spans: list[tuple[str, int, int]] = []
    entry: str | None = None
    for m in _PAGE_OPEN_RE.finditer(html_text):
        pid = m.group(1)
        spans.append((pid, m.start(), _page_end(html_text, m.start())))
        if entry is None and re.search(r'class="[^"]*\bshow\b', m.group()):
            entry = pid

    if not spans:
        return Reachability()
    if entry is None:
        entry = spans[0][0]

    page_links = {pid: _targets(html_text[s:e]) for pid, s, e in spans}

    # 全局链接 = 页面块以外的 goPage（顶栏 / 抽屉 / footer / 脚本）
    outside, cursor = [], 0
    for _, s, e in spans:
        outside.append(html_text[cursor:s])
        cursor = e
    outside.append(html_text[cursor:])
    global_links = _targets(''.join(outside))

    all_ids = {pid for pid, _, _ in spans}
    all_targets = set().union(global_links, *page_links.values())
    static_targets = _targets(_SCRIPT_RE.sub('', html_text))

    dead_static = sorted(t for t in static_targets if t not in all_ids)
    dead_script = sorted(
        t for t in all_targets - static_targets if t not in all_ids
    )

    # 可达性取全集（含脚本内跳转），宁可漏报也不误判「点不到」
    reached = {entry} | (global_links & all_ids)
    frontier = list(reached)
    while frontier:
        for nxt in page_links.get(frontier.pop(), set()) & all_ids:
            if nxt not in reached:
                reached.add(nxt)
                frontier.append(nxt)

    return Reachability(
        entry=entry,
        unreachable=sorted(all_ids - reached),
        dead_static=dead_static,
        dead_script=dead_script,
    )
