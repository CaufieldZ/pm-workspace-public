"""md_to_confluence 纯函数测试（覆盖任务列表转换 + 提示面板宏 + 推送前断表检测）。"""
from pathlib import Path

import pytest
from lib.confluence_md import _convert_task_lists, _split_md_around_fences, render_md_full
from md_to_confluence import broken_tables, warn_broken_tables


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


# ── 推送前断表检测 ──────────────────────────────────────────────

@pytest.mark.parametrize("md,expected", [
    # 断表：表体后空行，空行后落回表格行且不是新表头
    ("| a | b |\n|---|---|\n| 1 | 2 |\n\n| 3 | 4 |\n", [5]),
    ("| a | b |\n|---|---|\n| 1 | 2 |\n\n| 3 | 4 |\n| 5 | 6 |\n", [5]),
    # 逐行夹空行：每处孤立行都要报出来，不能只报第一处
    ("| a | b |\n|---|---|\n| 1 | 2 |\n\n| 3 | 4 |\n\n| 5 | 6 |\n", [5, 7]),
    # 空行不止一行时报落回后的那一行
    ("| a | b |\n|---|---|\n| 1 | 2 |\n\n\n| 3 | 4 |\n", [6]),
    # 省略尾管的写法同样判为断表
    ("| a | b\n|--- | ---|\n| 1 | 2\n\n| 3 | 4\n", [5]),
])
def test_broken_tables_detected(md, expected):
    assert broken_tables(md) == expected


@pytest.mark.parametrize("md", [
    # 空行后是另一张表的表头（后面紧跟分隔行）→ 合法双表
    "| a | b |\n|---|---|\n| 1 | 2 |\n\n| c | d |\n|---|---|\n| 3 | 4 |\n",
    "| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n",
    "| a | b |\n|---|---|\n| 1 | 2 |\n\n正文段落\n",
    "段落\n\n| a | b |\n|---|---|\n| 1 | 2 |\n",
    # 围栏代码块内的 | 行不是表格
    "| a | b |\n|---|---|\n| 1 | 2 |\n\n```\n| x | y |\n```\n",
    # Confluence 转出的「每单元格独占一行」形态：每行只解析出 1 格，不是 md 表格
    " | \n |\n 2 | 赵雪超 | 6月\n | 186\n\n | 刘益玮\n",
    ' | Toast"下单成功"\n | -\n | \n | \n\n |\n',
])
def test_broken_tables_not_flagged(md):
    assert broken_tables(md) == []


def test_warn_broken_tables_silent_when_clean(capsys):
    warn_broken_tables("| a | b |\n|---|---|\n| 1 | 2 |\n", Path("x.md"))
    assert capsys.readouterr().err == ""


def test_warn_broken_tables_reports_lines(capsys):
    warn_broken_tables("| a | b |\n|---|---|\n| 1 | 2 |\n\n| 3 | 4 |\n", Path("x.md"))
    err = capsys.readouterr().err
    assert "x.md" in err and "L5" in err

