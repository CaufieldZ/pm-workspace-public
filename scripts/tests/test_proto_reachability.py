"""proto_reachability — 页面可达性 / 跳转死链检测。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.proto_reachability import check_page_reachability  # noqa: E402


def _page(pid, body, show=False):
    cls = 'p-page show' if show else 'p-page'
    return f'<div class="{cls}" id="page-{pid}" data-page="{pid}">{body}</div>'


def _doc(*pages, nav='', script=''):
    return (
        f'<body><div class="p-nav">{nav}</div>'
        + ''.join(pages)
        + f'<script>{script}</script></body>'
    )


def test_no_data_page_returns_empty():
    r = check_page_reachability('<html><body><div>hi</div></body></html>')
    assert r.entry is None
    assert r.unreachable == [] and r.dead_static == []


def test_all_reachable():
    html = _doc(
        _page('a', "<span onclick=\"goPage('b')\">去 b</span>", show=True),
        _page('b', '详情'),
    )
    r = check_page_reachability(html)
    assert r.entry == 'a'
    assert r.unreachable == []
    assert r.dead_static == [] and r.dead_script == []


def test_page_without_entry_is_unreachable():
    html = _doc(_page('a', '首页', show=True), _page('b', '详情'))
    r = check_page_reachability(html)
    assert r.unreachable == ['b']


def test_global_nav_link_makes_page_reachable():
    html = _doc(
        _page('a', '首页', show=True),
        _page('b', '详情'),
        nav="<i onclick=\"goPage('b')\">b</i>",
    )
    assert check_page_reachability(html).unreachable == []


def test_transitive_reachability():
    html = _doc(
        _page('a', "<i onclick=\"goPage('b')\"></i>", show=True),
        _page('b', "<i onclick=\"goPage('c')\"></i>"),
        _page('c', '末页'),
    )
    assert check_page_reachability(html).unreachable == []


def test_chain_from_unreachable_page_stays_unreachable():
    html = _doc(
        _page('a', '首页', show=True),
        _page('b', "<i onclick=\"goPage('c')\"></i>"),
        _page('c', '末页'),
    )
    assert check_page_reachability(html).unreachable == ['b', 'c']


def test_static_dead_link():
    html = _doc(_page('a', "<i onclick=\"goPage('ghost')\"></i>", show=True))
    r = check_page_reachability(html)
    assert r.dead_static == ['ghost']
    assert r.dead_script == []


def test_script_only_dead_link_is_separated():
    """多端共享 JS 里引用另一端的页面 id — 只 warn，不算真死链。"""
    html = _doc(
        _page('a', '首页', show=True),
        script=r"var s = '<div onclick=\"goPage(\'room\')\">';",
    )
    r = check_page_reachability(html)
    assert r.dead_static == []
    assert r.dead_script == ['room']


def test_entry_falls_back_to_first_page_when_no_show():
    html = _doc(_page('a', '首页'), _page('b', '详情'))
    r = check_page_reachability(html)
    assert r.entry == 'a'
    assert r.unreachable == ['b']


def test_nested_divs_do_not_leak_across_pages():
    """页面块按 div 深度配对切分，嵌套不会把下一页的跳转算进本页。"""
    html = _doc(
        _page('a', '<div><div>深层</div></div>', show=True),
        _page('b', "<i onclick=\"goPage('a')\"></i>"),
    )
    assert check_page_reachability(html).unreachable == ['b']
