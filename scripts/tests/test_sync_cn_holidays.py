"""sync_cn_holidays 纯函数回归：源 JSON 解析 / 年份区间 / 产物 diff。

只测纯函数（吃结构 → 返回结构），不触网络——取数在 fetch_year 的 I/O 层。
锁定的是「放假日 vs 工作日标记」这个方向性约定：表里只能是 isOffDay 的那些天，
拿错标记会让补班日被错判成高峰。
"""
import pytest

import sync_cn_holidays as s


def _doc(year, days):
    return {"year": year, "days": days}


# ── parse_year_payload ────────────────────────────────────────────────

def test_parse_keeps_only_off_days():
    """调休补班日 isOffDay=false —— 必须丢掉。它本就是周末，判定里用不上；
    而标记语义相反，误收会把周末算成高峰。"""
    doc = _doc(2026, [
        {"name": "国庆节", "date": "2026-10-01", "isOffDay": True},
        {"name": "补班", "date": "2026-09-20", "isOffDay": False},
    ])
    assert s.parse_year_payload(doc, 2026) == ["2026-10-01"]


def test_parse_sorts_and_dedups():
    doc = _doc(2026, [
        {"date": "2026-01-02", "isOffDay": True},
        {"date": "2026-01-01", "isOffDay": True},
        {"date": "2026-01-01", "isOffDay": True},
    ])
    assert s.parse_year_payload(doc, 2026) == ["2026-01-01", "2026-01-02"]


def test_parse_empty_days_is_empty_not_error():
    """次年安排未公布 → 空表。空表是合法读数，由调用方决定不写它（写了会被当成已覆盖）。"""
    assert s.parse_year_payload(_doc(2027, []), 2027) == []


@pytest.mark.parametrize("doc", [
    {"year": 2025, "days": []},                 # 年份对不上
    {"year": 2026},                             # 缺 days
    {"year": 2026, "days": "2026-01-01"},       # days 不是数组
    {"year": 2026, "days": [{"date": "2026-1-1", "isOffDay": True}]},   # 日期格式不合法
    {"days": []},                               # 缺 year
])
def test_parse_rejects_bad_structure(doc):
    """结构认不出必须抛错 —— 静默返回空表会让「源坏了」看起来像「该年没假期」。"""
    with pytest.raises(ValueError):
        s.parse_year_payload(doc, 2026)


def test_parse_rejects_non_dict():
    with pytest.raises(ValueError):
        s.parse_year_payload(["2026-01-01"], 2026)


# ── parse_year_arg ────────────────────────────────────────────────────

@pytest.mark.parametrize("spec,expect", [
    ("2026", [2026]),
    ("2025-2027", [2025, 2026, 2027]),
    ("2025,2027", [2025, 2027]),
    ("2027, 2025-2026", [2025, 2026, 2027]),
])
def test_parse_year_arg(spec, expect):
    assert s.parse_year_arg(spec) == expect


@pytest.mark.parametrize("spec", ["", ",", "  "])
def test_parse_year_arg_rejects_empty(spec):
    with pytest.raises(ValueError):
        s.parse_year_arg(spec)


# ── diff_years ────────────────────────────────────────────────────────

def test_diff_no_change():
    same = {"2026": ["2026-01-01"]}
    assert s.diff_years(same, {"2026": ["2026-01-01"]}) == []


def test_diff_new_year_and_removed_date():
    old = {"2026": ["2026-01-01", "2026-05-01"]}
    new = {"2026": ["2026-01-01"], "2027": ["2027-01-01"]}
    out = s.diff_years(old, new)
    assert any("2026" in x and "- 2026-05-01" in x for x in out)
    assert any("2027" in x and "+ 2027-01-01" in x for x in out)


def test_diff_ignores_key_order():
    a = {"2026": ["2026-01-02", "2026-01-01"]}
    b = {"2026": ["2026-01-01", "2026-01-02"]}
    assert s.diff_years(a, b) == []
