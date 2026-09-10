"""md_to_confluence 纯函数测试（覆盖任务列表转换 + 提示面板宏）。"""
import pytest
from lib.confluence_md import _convert_task_lists, _split_md_around_fences, render_md_full


def test_pure_task_list_converts():
    html = "<ul>\n<li>[ ] 未完成项</li>\n<li>[x] 已完成项</li>\n</ul>"
    out = _convert_task_lists(html)
    assert "<ac:task-list>" in out
    assert out.count("<ac:task>") == 2
    assert "<ac:task-status>incomplete</ac:task-status>" in out
    assert "<ac:task-status>complete</ac:task-status>" in out
    assert "<ac:task-body>未完成项</ac:task-body>" in out
    assert "[ ]" not in out and "[x]" not in out


@pytest.mark.parametrize("mark,status", [("x", "complete"), ("X", "complete"), (" ", "incomplete")])
def test_checkbox_mark_maps_to_status(mark, status):
    out = _convert_task_lists(f"<ul>\n<li>[{mark}] 项</li>\n</ul>")
    assert f"<ac:task-status>{status}</ac:task-status>" in out


def test_plain_list_untouched():
    html = "<ul>\n<li>普通项 A</li>\n<li>普通项 B</li>\n</ul>"
    assert _convert_task_lists(html) == html


def test_mixed_list_not_converted():
    """一个 ul 里混了 checkbox 与普通项 → 不转，保持原样。"""
    html = "<ul>\n<li>[ ] 任务</li>\n<li>普通项</li>\n</ul>"
    assert _convert_task_lists(html) == html
    assert "<ac:task-list>" not in _convert_task_lists(html)


def test_no_list_passthrough():
    html = "<p>没有列表的段落</p>"
    assert _convert_task_lists(html) == html


# ── :::info / :::note 提示面板围栏 → Confluence 原生面板宏 ─────────────────────
def test_panel_with_title():
    parts = _split_md_around_fences(":::info 文档信息\n内容\n:::")
    assert parts[0][0] == "panel"
    ptype, title, body = parts[0][1]
    assert ptype == "info"
    assert title == "文档信息"
    assert body == "内容\n"


def test_panel_without_title():
    parts = _split_md_around_fences(":::note\n警告内容\n:::")
    assert parts[0][0] == "panel"
    ptype, title, body = parts[0][1]
    assert ptype == "note" and title is None


def test_panel_unterminated_is_text():
    """缺闭合 ::: 当普通文本，不误判为面板。"""
    parts = _split_md_around_fences(":::info\n没闭合的内容")
    assert parts[0][0] == "text"


def test_panel_renders_storage_macro():
    out = render_md_full(":::info 文档信息\n正文段落\n:::")
    assert 'ac:name="info"' in out
    assert '<ac:parameter ac:name="title">文档信息</ac:parameter>' in out
    assert "<ac:rich-text-body>" in out


def test_panel_and_leftright_coexist():
    """面板与 leftright 混排：两种围栏闭合 ::: 互不干扰。"""
    out = render_md_full(":::note\n提醒\n:::\n\n:::leftright\n左\n:::col\n右\n:::")
    assert 'ac:name="note"' in out
    assert "<table>" in out


def test_panel_title_escaped():
    out = render_md_full(":::info A<B & C\n正文\n:::")
    assert "<ac:parameter ac:name=\"title\">A&lt;B &amp; C</ac:parameter>" in out


# ── :::steps 手册步骤图表格 → 收窄图片的原生 <table> ───────────────────────────
_STEPS_MD = (
    ":::steps\n"
    "| 第一步：点头像 | 第二步：点主播中心 |\n"
    "| :---: | :---: |\n"
    "| ![图：首页](a.png) | ![图：中心](b.png) |\n"
    ":::"
)


def test_steps_splits_as_steps():
    parts = _split_md_around_fences(_STEPS_MD)
    assert parts[0][0] == "steps"


def test_steps_portrait_image_narrowed():
    """竖屏图（W/H<0.8）在步骤表格里收窄到 260。"""
    dims = {"a.png": (860, 1800), "b.png": (860, 1800)}
    out = render_md_full(_STEPS_MD, {"a.png", "b.png"}, attachment_dims=dims)
    assert '<ac:image ac:width="260">' in out
    assert "<th style=\"text-align:center\">第一步：点头像</th>" in out
    assert "width: 50%;" in out


def test_steps_landscape_image_narrowed():
    """横屏图（W/H≥0.8）在步骤表格里收窄到 340。"""
    dims = {"a.png": (1800, 900), "b.png": (1800, 900)}
    out = render_md_full(_STEPS_MD, {"a.png", "b.png"}, attachment_dims=dims)
    assert '<ac:image ac:width="340">' in out


def test_steps_unterminated_is_text():
    """缺闭合 ::: 当普通文本，不误判为步骤表格。"""
    parts = _split_md_around_fences(":::steps\n| a | b |\n没闭合")
    assert all(k != "steps" for k, _ in parts)

