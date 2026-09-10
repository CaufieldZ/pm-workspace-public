"""nav_confluence 纯函数测试：find CQL 拼接 / URL 拼接 / 树遍历 / 渲染。"""

import nav_confluence
import pytest
from nav_confluence import build_find_cql, page_url, render_find, render_tree, walk_tree


@pytest.mark.parametrize("kw,space,expected_parts", [
    ("直播竞品", "Platform C", ['space="Platform C"', 'title ~ "直播竞品"', "type=page"]),
    ("红包雨", None, ['title ~ "红包雨"', "type=page"]),
])
def test_build_find_cql_contains(kw, space, expected_parts):
    cql = build_find_cql(kw, space)
    for part in expected_parts:
        assert part in cql
    assert cql.endswith("order by created desc")


def test_build_find_cql_no_space_omits_space_clause():
    assert "space=" not in build_find_cql("x", None)


def test_build_find_cql_escapes_quotes():
    assert '\\"' in build_find_cql('a"b', "Platform C")


def test_page_url_prefers_webui(monkeypatch):
    monkeypatch.setattr(nav_confluence, "base_url", lambda: "https://wiki.example.com")
    p = {"id": "123", "_links": {"webui": "/display/Platform C/Foo"}}
    assert page_url(p) == "https://wiki.example.com/display/Platform C/Foo"


def test_page_url_fallback_viewpage(monkeypatch):
    monkeypatch.setattr(nav_confluence, "base_url", lambda: "https://wiki.example.com")
    p = {"id": "123", "_links": {}}
    assert page_url(p) == "https://wiki.example.com/pages/viewpage.action?pageId=123"


def test_render_find_empty():
    assert "命中 0 篇" in render_find([])


def test_render_find_table(monkeypatch):
    monkeypatch.setattr(nav_confluence, "base_url", lambda: "https://wiki.example.com")
    hits = [{"id": "1", "title": "A", "space": {"key": "Platform C"}, "_links": {"webui": "/x"}}]
    out = render_find(hits)
    assert "| A | Platform C | 1 |" in out


def _children_map(mapping):
    """返回一个 list_child_pages 替身：parent_id -> [pages]。"""
    def fake(parent_id, limit=100):
        return mapping.get(parent_id, [])
    return fake


def _pg(pid, title):
    return {"id": pid, "title": title, "_links": {"webui": f"/p/{pid}"}}


def test_walk_tree_direct_only(monkeypatch):
    monkeypatch.setattr(nav_confluence, "list_child_pages", _children_map({
        "root": [_pg("a", "A"), _pg("b", "B")],
        "a": [_pg("a1", "A1")],
    }))
    nodes = walk_tree("root", recursive=False, max_depth=0)
    assert [n["page"]["id"] for n in nodes] == ["a", "b"]
    assert all(n["depth"] == 0 for n in nodes)


def test_walk_tree_recursive_preorder(monkeypatch):
    monkeypatch.setattr(nav_confluence, "list_child_pages", _children_map({
        "root": [_pg("a", "A"), _pg("b", "B")],
        "a": [_pg("a1", "A1")],
    }))
    nodes = walk_tree("root", recursive=True, max_depth=0)
    assert [n["page"]["id"] for n in nodes] == ["a", "a1", "b"]
    depths = {n["page"]["id"]: n["depth"] for n in nodes}
    assert depths == {"a": 0, "a1": 1, "b": 0}


def test_walk_tree_max_depth_caps(monkeypatch):
    monkeypatch.setattr(nav_confluence, "list_child_pages", _children_map({
        "root": [_pg("a", "A")],
        "a": [_pg("a1", "A1")],
        "a1": [_pg("a2", "A2")],
    }))
    # max_depth=1 等价只列直接子页
    nodes = walk_tree("root", recursive=True, max_depth=1)
    assert [n["page"]["id"] for n in nodes] == ["a"]
    # max_depth=2 到孙层为止
    nodes = walk_tree("root", recursive=True, max_depth=2)
    assert [n["page"]["id"] for n in nodes] == ["a", "a1"]


def test_render_tree_empty():
    assert "没有子页" in render_tree([], show_url=False)


def test_render_tree_indent(monkeypatch):
    monkeypatch.setattr(nav_confluence, "base_url", lambda: "https://wiki.example.com")
    nodes = [
        {"page": _pg("a", "A"), "depth": 0},
        {"page": _pg("a1", "A1"), "depth": 1},
    ]
    out = render_tree(nodes, show_url=False).splitlines()
    assert out[0] == "- A  [a]"
    assert out[1] == "  - A1  [a1]"


def test_render_tree_show_url(monkeypatch):
    monkeypatch.setattr(nav_confluence, "base_url", lambda: "https://wiki.example.com")
    nodes = [{"page": _pg("a", "A"), "depth": 0}]
    out = render_tree(nodes, show_url=True)
    assert "https://wiki.example.com/p/a" in out
