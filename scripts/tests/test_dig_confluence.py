"""dig_confluence 纯函数测试：CQL 拼接 / 标题版本键 / 排序 / 语料头 SOP。"""

import pytest
from dig_confluence import SOP_BLOCK, build_cql, render_corpus, sort_pages, title_version_key


@pytest.mark.parametrize("kw,space,parent,expected_parts", [
    ("红包雨", "Platform C", None, ['space="Platform C"', 'text ~ "红包雨"', "type=page"]),
    ("邀请返佣", "Platform C", "151429067", ['space="Platform C"', "ancestor=151429067"]),
])
def test_build_cql_contains(kw, space, parent, expected_parts):
    cql = build_cql(kw, space, parent)
    for part in expected_parts:
        assert part in cql
    assert cql.endswith("order by created desc")


def test_build_cql_no_ancestor_when_none():
    assert "ancestor" not in build_cql("x", "Platform C", None)


def test_build_cql_escapes_quotes():
    assert '\\"' in build_cql('a"b', "Platform C", None)


def test_build_cql_text_vs_title():
    assert 'text ~ "x"' in build_cql("x", "Platform C", None, in_title=False)
    assert 'title ~ "x"' in build_cql("x", "Platform C", None, in_title=True)


def test_build_cql_no_keyword_pure_parent():
    # 纯父页考古：无关键词，只按 ancestor 拉子树，不含 text/title 子句
    cql = build_cql(None, "Platform C", "6723063")
    assert "ancestor=6723063" in cql
    assert " ~ " not in cql
    assert cql.endswith("order by created desc")


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
    import dig_confluence
    monkeypatch.setattr(dig_confluence, "base_url", lambda: "https://wiki.example.com")
    md = render_corpus("红包", "Platform C", None, [], with_images=False)
    assert SOP_BLOCK.strip() in md
    # SOP 在命中清单之前
    assert md.index("下一步 SOP") < md.index("命中清单")
