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
