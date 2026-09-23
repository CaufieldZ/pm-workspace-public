"""lib.visible_text 的可见文本抽取 / 锚点跳过单测。

锁住：工区按钮基类 `.b`（prototype.css）不得进 ANCHOR_CLASSES——一旦收进去，
`<button class="b b-blue">` 的文案对开发注解门 / 行文门整体不可见。
锚点与外壳容器的既有跳过行为不回归。
"""
from lib.visible_text import iter_visible_text


def _texts(html):
    return [t for t, _ in iter_visible_text(html)]


def _wrap(inner):
    return f'<html><body><div class="app-mock">{inner}</div></body></html>'


# ── 按钮基类不得被当锚点跳过 ─────────────────────────────
def test_button_base_class_text_is_visible():
    html = _wrap('<button class="b b-blue">提交打分</button>')
    assert "提交打分" in _texts(html)


def test_button_without_base_class_still_visible():
    html = _wrap('<button class="b-blue">保存草稿</button>')
    assert "保存草稿" in _texts(html)


def test_annotation_inside_button_is_scannable():
    """按钮里的开发注解必须能被扫到（门依赖可见文本命中）。"""
    from lib.ui_annotation import scan_ui_annotation

    html = _wrap('<button class="b">提交（占位，待开发补）</button>')
    hits = [h for t in _texts(html) for h in scan_ui_annotation(t)]
    assert hits, "按钮文案里的开发注解未被抽到"


# ── 既有跳过行为不回归 ───────────────────────────────────
def test_phone_label_anchor_still_skipped():
    html = _wrap('<div class="phone-label">B-1 · 入口</div><div class="x">正文</div>')
    texts = _texts(html)
    assert "B-1 · 入口" not in texts
    assert "正文" in texts


def test_script_subtree_still_skipped():
    html = _wrap('<script>var a = "不该出现";</script><div class="x">正文</div>')
    texts = _texts(html)
    assert "不该出现" not in texts
    assert "正文" in texts


def test_html_comment_is_not_visible_text():
    """HTML 注释不渲染 —— 扫进来会让 <!-- 待删 --> / <!-- A-1 --> 之类误报。"""
    html = _wrap('<!-- 待补：A-1 的截图 --><div class="x">正文</div>')
    texts = _texts(html)
    assert "正文" in texts
    assert not any("待补" in t for t in texts), texts


# ── 屏内「内部编号」：原型禁，IMAP 放行 ───────────────────
def _proto(inner):
    return f'<html><body><div class="app-mock">{inner}</div></body></html>'


def _imap(inner):
    return f'<html><body><div class="phone">{inner}</div></body></html>'


def test_proto_screen_flags_internal_ids():
    from lib.ui_annotation import find_mockup_annotations

    findings = find_mockup_annotations(
        _proto('<div class="card-title">A-1 下注弹层</div>'
               '<div class="tip">见 baseline.md 的口径</div>'
               '<div class="note">沿用决策 #3 的口径</div>'),
        'proto',
    )
    cats = {c for _loc, _snip, hits in findings for c, _v in hits}
    assert cats == {'internal_scene_code', 'internal_file_name', 'internal_decision_num'}, cats


def test_imap_screen_allows_scene_code_anchor():
    """IMAP 屏内的「C-3 ↗」是合法跳转写法，不拦。"""
    from lib.ui_annotation import find_mockup_annotations

    assert find_mockup_annotations(_imap('<div class="jump">C-3 ↗</div>'), 'imap') == []


def test_proto_skips_anchor_container_for_internal_ids():
    """编号锚点容器里的「A-1 · xxx」是合法形态（屏标签），不当内部编号报。"""
    from lib.ui_annotation import find_mockup_annotations

    assert find_mockup_annotations(
        _proto('<div class="phone-label">A-1 · 下注弹层</div><div class="x">正文</div>'), 'proto'
    ) == []
