"""blacklist 模式抽取 HTML 可见文本节点。

替代旧的 BODY_CLASSES 白名单（check_imap.sh:54 / check_proto.sh:57）。
旧方案问题：q2-update V14 用 `<span class="note">`、activity-center V5.3 用
`<div class="bn-title">` 等容器不在白名单 → 完全不扫。

新方案：遍历 body 下所有可见文本节点，按规则跳过：
- 不可见标签（script/style/noscript/template/svg/code）
- 锚点容器（phone-label / gd-num / id="scene-*"/.st > h2 等）整个子树
- 框架/设备外壳容器（app-shell / gnav / gnav-view-section 等）整个子树
  ← 不含业务文本，只是布局

调用方拿到节点后可：
- 获取 text: node.get_text(' ', strip=True)
- 获取 location: 父节点 class 列表（用于报错定位）

实际效果：
- q2-update V14 `<span class="note">TRTC/OBS 双轨...</span>` ✓ 扫到
- activity-center `<div class="bn-title">BTC 巅峰赛 S12</div>` ✓ 扫到
- leaderboard `<div class="card-title">...</div>` ✓ 扫到（原白名单也覆盖）
"""
from __future__ import annotations

from bs4 import BeautifulSoup, Tag

# 完全跳过的 HTML 标签（含子树）
SKIP_TAGS = {
    'script', 'style', 'noscript', 'template', 'svg', 'code', 'pre',
    'head', 'meta', 'link', 'title',
}

# 锚点容器类（编号 / 设备标签 / Tab 标签 - 内容是 "A · xxx" 合法形态，跳过）
ANCHOR_CLASSES = {
    'phone-label',     # IMAP 屏幕标签 "B-1 · 入口"
    'gd-num',          # PART 编号 "PART 0"
    'gd-num-cd',       # 同上变体
    'cm-box-num',      # swimlane 编号
    'tab-num',         # Tab 编号
    'ann-num',         # 注释编号
    'anno-n',          # 标注编号
    'badge',           # 通用标签
    'b',               # 粗体编号容器
    'gd-tag',          # 分组 tag
    'gnav-ver',        # 导航版本号
}

# 框架/外壳容器（布局壳，跳过整个子树以减少噪音）
# 注意：这些容器内部业务可见文本仍会被其内层 class 容器扫到
# 这里只过滤"直接挂在外壳上的"碎片文本（导航 logo / 状态栏 / 版本号等）
SHELL_CLASSES = {
    'app-navbar', 'app-status', 'app-shell', 'app-wrap',
    'gnav', 'gnav-tabs', 'gnav-ic', 'gnav-logo', 'gnav-right',
    'gnav-sep', 'gnav-tab',
    'back', 'close', 'dot',
}


def _class_set(node: Tag) -> set[str]:
    raw = node.get('class')
    if isinstance(raw, str):  # bs4 单 class 返回 str
        classes = [raw]
    else:
        classes = raw or []
    return set(classes)


def _ancestor_has_class(node, target: set) -> bool:
    cur = node.parent
    while cur is not None and isinstance(cur, Tag):
        if _class_set(cur) & target:
            return True
        cur = cur.parent
    return False


def _is_in_anchor(node) -> bool:
    """是否在锚点容器内（含本身 + 任意祖先）。"""
    if not isinstance(node, Tag):
        return _ancestor_has_class(node, ANCHOR_CLASSES) or _is_in_st_h2(node)
    if _class_set(node) & ANCHOR_CLASSES:
        return True
    if _ancestor_has_class(node, ANCHOR_CLASSES):
        return True
    if _is_in_st_h2(node):
        return True
    return False


def _is_in_st_h2(node) -> bool:
    """IMAP `.st > h2` 容器是合法锚点（场景标题），跳过。"""
    cur = node if isinstance(node, Tag) else node.parent
    while cur is not None and isinstance(cur, Tag):
        if cur.name == 'h2':
            parent = cur.parent
            if parent is not None and 'st' in (parent.get('class') or []):
                return True
        cur = cur.parent
    return False


def _is_direct_shell_child(node) -> bool:
    """节点是否是 SHELL 容器的直接文本子节点（跳过这种碎片）。"""
    if not isinstance(node, Tag):
        parent = node.parent
        if parent is not None and isinstance(parent, Tag):
            if _class_set(parent) & SHELL_CLASSES:
                return True
    return False


def iter_visible_text(html_text: str):
    """生成器：yield (text, location_hint) 元组。

    location_hint = 形如 "div.flow-note" 或 "span.note"，用于报错定位。
    """
    soup = BeautifulSoup(html_text, 'html.parser')
    body = soup.body or soup
    for node in body.descendants:
        # 跳过 Tag 节点本身（只处理文本节点）
        if isinstance(node, Tag):
            continue
        # 必须是非空文本
        text = str(node).strip()
        if not text:
            continue
        parent = node.parent
        if parent is None:
            continue
        # 跳过整段 SKIP_TAGS（含其子文本）
        if any(a.name in SKIP_TAGS for a in [parent] + list(parent.parents) if isinstance(a, Tag)):
            continue
        # 跳过锚点容器
        if _is_in_anchor(node):
            continue
        # 跳过外壳容器的直接文本子节点（导航/状态栏碎片）
        if _is_direct_shell_child(node):
            continue
        # 定位提示
        parent_cls = _class_set(parent)
        loc = f"{parent.name}.{next(iter(parent_cls)) if parent_cls else '?'}"
        yield text, loc


def iter_code_tags(html_text: str):
    """单独抽 <code> 标签内容（业务话语层用，独立处理）。"""
    soup = BeautifulSoup(html_text, 'html.parser')
    for code in soup.find_all('code'):
        if _is_in_anchor(code):
            continue
        txt = code.get_text(strip=True)
        if txt:
            yield txt
