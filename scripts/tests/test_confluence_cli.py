"""confluence.py 读侧 CLI 纯函数测试：URL 拼接 / 树遍历 / 渲染 / 标题版本键 / 排序 / 语料头 SOP。

CQL 拼接已上提 lib.confluence_rest.build_cql，测试在 test_confluence_rest.py。
"""

import confluence
import pytest
from confluence import (
    SOP_BLOCK,
    page_url,
    render_corpus,
    render_find,
    render_tree,
    sort_pages,
    title_version_key,
    walk_tree,
)

# ═══════════ find / URL 拼接 ═══════════


def test_page_url_prefers_webui(monkeypatch):
    monkeypatch.setattr(confluence, "base_url", lambda: "https://wiki.example.com")
    p = {"id": "123", "_links": {"webui": "/display/Platform C/Foo"}}
    assert page_url(p) == "https://wiki.example.com/display/Platform C/Foo"


def test_page_url_fallback_viewpage(monkeypatch):
    monkeypatch.setattr(confluence, "base_url", lambda: "https://wiki.example.com")
    p = {"id": "123", "_links": {}}
    assert page_url(p) == "https://wiki.example.com/pages/viewpage.action?pageId=123"


def test_render_find_empty():
    assert "命中 0 篇" in render_find([])


def test_render_find_table(monkeypatch):
    monkeypatch.setattr(confluence, "base_url", lambda: "https://wiki.example.com")
    hits = [{"id": "1", "title": "A", "space": {"key": "Platform C"}, "_links": {"webui": "/x"}}]
    out = render_find(hits)
    assert "| A | Platform C | 1 |" in out


# ═══════════ tree 遍历 / 渲染 ═══════════


def _children_map(mapping):
    """返回一个 list_child_pages 替身：parent_id -> [pages]。"""
    def fake(parent_id, limit=100):
        return mapping.get(parent_id, [])
    return fake


def _pg(pid, title):
    return {"id": pid, "title": title, "_links": {"webui": f"/p/{pid}"}}


def test_walk_tree_direct_only(monkeypatch):
    monkeypatch.setattr(confluence, "list_child_pages", _children_map({
        "root": [_pg("a", "A"), _pg("b", "B")],
        "a": [_pg("a1", "A1")],
    }))
    nodes = walk_tree("root", recursive=False, max_depth=0)
    assert [n["page"]["id"] for n in nodes] == ["a", "b"]
    assert all(n["depth"] == 0 for n in nodes)


def test_walk_tree_recursive_preorder(monkeypatch):
    monkeypatch.setattr(confluence, "list_child_pages", _children_map({
        "root": [_pg("a", "A"), _pg("b", "B")],
        "a": [_pg("a1", "A1")],
    }))
    nodes = walk_tree("root", recursive=True, max_depth=0)
    assert [n["page"]["id"] for n in nodes] == ["a", "a1", "b"]
    depths = {n["page"]["id"]: n["depth"] for n in nodes}
    assert depths == {"a": 0, "a1": 1, "b": 0}


def test_walk_tree_max_depth_caps(monkeypatch):
    monkeypatch.setattr(confluence, "list_child_pages", _children_map({
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
    monkeypatch.setattr(confluence, "base_url", lambda: "https://wiki.example.com")
    nodes = [
        {"page": _pg("a", "A"), "depth": 0},
        {"page": _pg("a1", "A1"), "depth": 1},
    ]
    out = render_tree(nodes, show_url=False).splitlines()
    assert out[0] == "- A  [a]"
    assert out[1] == "  - A1  [a1]"


def test_render_tree_show_url(monkeypatch):
    monkeypatch.setattr(confluence, "base_url", lambda: "https://wiki.example.com")
    nodes = [{"page": _pg("a", "A"), "depth": 0}]
    out = render_tree(nodes, show_url=True)
    assert "https://wiki.example.com/p/a" in out


# ═══════════ dig 标题版本键 / 排序 ═══════════


@pytest.mark.parametrize("title,expected", [
    ("红包雨方案 2026-05-12", (0, 2026, 5, 12)),
    ("红包雨 2026/05", (0, 2026, 5, 0)),
    ("红包雨 Q3", (1, 0, 3)),
    ("红包雨 2026Q2", (1, 2026, 2)),
    ("红包雨 v2", (2, 2)),
    ("红包雨 v2.1.3", (2, 2, 1, 3)),
    ("红包雨初版", None),
])
def test_title_version_key(title, expected):
    assert title_version_key(title) == expected


def test_title_version_key_date_beats_version():
    # 同时含日期和 vN，日期优先
    assert title_version_key("方案 v2 2026-05-01")[0] == 0


def _item(title, created):
    return {"page": {"title": title}, "created": created, "updated": created}


def test_sort_pages_by_created_time():
    items = [
        _item("B", "2026-03-01T00:00:00.000+08:00"),
        _item("A", "2026-01-01T00:00:00.000+08:00"),
        _item("C", "2026-02-01T00:00:00.000+08:00"),
    ]
    titles = [it["page"]["title"] for it in sort_pages(items)]
    assert titles == ["A", "C", "B"]


def test_sort_pages_version_tiebreak_same_time():
    # 创建时间相同 → 标题版本号细分正序
    t = "2026-01-01T00:00:00.000+08:00"
    items = [_item("方案 v3", t), _item("方案 v1", t), _item("方案 v2", t)]
    titles = [it["page"]["title"] for it in sort_pages(items)]
    assert titles == ["方案 v1", "方案 v2", "方案 v3"]


def test_sort_pages_no_version_key_stable():
    t = "2026-01-01T00:00:00.000+08:00"
    items = [_item("无版本甲", t), _item("无版本乙", t)]
    # 无版本键 → tie-break 退化为空 tuple，保持稳定序不报错
    assert len(sort_pages(items)) == 2


def test_sop_block_carries_key_rules():
    # 语料头 SOP 必须点到两件事：喂 agent 重建 + 反哺前先 gap 比对（指向 runbook）
    assert "general-purpose" in SOP_BLOCK
    assert "现状真相" in SOP_BLOCK and "演进时间线" in SOP_BLOCK
    assert "gap 全量比对" in SOP_BLOCK
    assert "confluence-archaeology.md" in SOP_BLOCK


def test_render_corpus_puts_sop_before_hit_list(monkeypatch):
    monkeypatch.setattr(confluence, "base_url", lambda: "https://wiki.example.com")
    md = render_corpus("红包", "Platform C", None, [], with_images=False)
    assert SOP_BLOCK.strip() in md
    # SOP 在命中清单之前
    assert md.index("下一步 SOP") < md.index("命中清单")


# ═══════════ 子命令装配（合并后三个入口共用一个 parser）═══════════


@pytest.mark.parametrize("cmd", ["find", "search", "tree", "get", "dig"])
def test_subcommand_help_exits_clean(cmd):
    """五个子命令的 --help 都零副作用退出 0（不触发凭据加载）。

    合并前是三个独立脚本，任一子命令在装配时掉了 parser 或 handler，这里立刻红。
    """
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "confluence.py"
    r = subprocess.run(
        [sys.executable, str(script), cmd, "--help"],
        capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"},
    )
    assert r.returncode == 0, f"{cmd} --help 退出码 {r.returncode}：{r.stderr[:300]}"
    assert cmd in r.stdout or "usage" in r.stdout.lower()
