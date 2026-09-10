"""gate_health 回归：五条判定各自可命中 + 注册表宽窄集不混用。

锁定：① parse_events 只收 hook/gate 且滤掉 -shadow 与坏行；② 五个维度（死 gate /
死豁免 / 零触发 / skip 失衡 / 无解释 skip）都有正例能点亮，也都有负例不误报；
③ 黄灯只认窄集 gates，hook 文件名 stem 只兜死 gate 判定不进黄灯。
"""
from datetime import datetime, timedelta, timezone

import pytest
from gate_health import (
    SKIP_MIN_SAMPLE,
    SKIP_RATIO,
    UNEXPLAINED_SKIP_MAX,
    analyze,
    has_red,
    parse_events,
)

TZ = timezone(timedelta(hours=8))
NOW = datetime(2026, 8, 30, 12, 0, tzinfo=TZ)


def ev(name, action="triggered", days_ago=1, detail="x", type_="gate"):
    ts = (NOW - timedelta(days=days_ago)).isoformat()
    return {"ts": ts, "type": type_, "name": name, "action": action, "detail": detail}


def run(events, gates=None, known=None, ghost=None, days=90):
    gates = {"a-gate"} if gates is None else gates
    known = gates if known is None else known
    return analyze(events, gates, known, ghost or set(), NOW, days)


# ─── parse_events ───

@pytest.mark.parametrize("line,kept", [
    ('{"type":"gate","name":"a-gate","action":"block"}', True),
    ('{"type":"hook","name":"a-gate","action":"warn"}', True),
    ('{"type":"skill","name":"prd","action":"completed"}', False),   # 非 hook/gate
    ('{"type":"gate","name":"a-gate-shadow","action":"block"}', False),  # 影子并跑
    ('{"type":"gate","action":"block"}', False),                      # 无 name
    ('{"type":"gate","name":"","action":"block"}', False),
    ("not json at all", False),                                       # 历史脏行
    ('"a bare string"', False),                                       # 合法 JSON 非 dict
])
def test_parse_events_filters(line, kept):
    assert len(parse_events(line)) == (1 if kept else 0)


def test_parse_events_survives_mixed_garbage():
    text = '\n'.join([
        '{"type":"gate","name":"a-gate","action":"block"}',
        '{{{ broken',
        '{"type":"gate","name":"b-gate","action":"skip"}',
    ])
    assert [e["name"] for e in parse_events(text)] == ["a-gate", "b-gate"]


# ─── 红灯一：死 gate ───

def test_dead_gate_when_logged_but_unknown():
    r = run([ev("ghost-gate")], gates={"a-gate"}, known={"a-gate"})
    assert r["dead_gates"] == ["ghost-gate"]
    assert has_red(r)


def test_dead_gate_suppressed_by_wide_registry():
    """hook 文件名 stem 在宽集里 → 不算死 gate（dispatcher 自报名的场景）。"""
    r = run([ev("post-writeedit-dispatch")],
            gates={"a-gate"}, known={"a-gate", "post-writeedit-dispatch"})
    assert r["dead_gates"] == []
    assert not has_red(r)


def test_dead_gate_suppressed_by_exemption():
    r = run([ev("retired-gate")], gates={"a-gate"}, known={"a-gate"},
            ghost={"retired-gate"})
    assert r["dead_gates"] == []


def test_dead_gate_counts_events_outside_window():
    """死 gate 看全量历史，不受黄灯窗口影响——老尸体也是尸体。"""
    r = run([ev("ghost-gate", days_ago=400)], gates={"a-gate"}, known={"a-gate"})
    assert r["dead_gates"] == ["ghost-gate"]


# ─── 红灯二：死豁免（生命周期断言）───

def test_dead_exemption_when_roster_key_has_no_events():
    r = run([ev("a-gate")], ghost={"long-gone"})
    assert r["dead_exempt"] == ["long-gone"]
    assert has_red(r)


def test_live_exemption_kept():
    r = run([ev("retired-gate", days_ago=400)], ghost={"retired-gate"})
    assert r["dead_exempt"] == []
    assert not has_red(r)


# ─── 黄灯一：零触发 ───

def test_zero_trigger_reported_and_scoped_to_narrow_set():
    r = run([ev("a-gate")], gates={"a-gate", "b-gate"},
            known={"a-gate", "b-gate", "some-hook-stem"})
    assert r["zero"] == ["b-gate"]          # 宽集独有的 stem 不进黄灯
    assert not has_red(r)


def test_zero_trigger_counts_only_within_window():
    r = run([ev("a-gate", days_ago=120)], gates={"a-gate"}, days=90)
    assert r["zero"] == ["a-gate"]


# ─── 黄灯二：skip 失衡 ───

def test_skip_ratio_flags_loose_gate():
    events = [ev("a-gate", "skip") for _ in range(4)] + [ev("a-gate", "block")]
    r = run(events)
    assert [g for g, _, _ in r["loose"]] == ["a-gate"]
    assert r["loose"][0][1] == pytest.approx(0.8)


def test_skip_ratio_needs_minimum_sample():
    events = [ev("a-gate", "skip") for _ in range(SKIP_MIN_SAMPLE - 1)]
    assert run(events)["loose"] == []


def test_skip_ratio_at_threshold_is_not_flagged():
    """严格大于才报：3 skip / 2 block = 0.6 恰在阈值上，放过。"""
    events = [ev("a-gate", "skip") for _ in range(3)] + \
             [ev("a-gate", "block") for _ in range(2)]
    r = run(events)
    assert 3 / 5 == SKIP_RATIO and r["loose"] == []


# ─── 黄灯三：无解释 skip ───

def test_unexplained_skip_flagged():
    events = [ev("a-gate", "skip", detail="") for _ in range(UNEXPLAINED_SKIP_MAX + 1)]
    assert run(events)["silent"] == [("a-gate", UNEXPLAINED_SKIP_MAX + 1)]


def test_explained_skip_not_flagged():
    events = [ev("a-gate", "skip", detail="赶发布") for _ in range(10)]
    assert run(events)["silent"] == []


def test_unexplained_skip_at_threshold_is_not_flagged():
    events = [ev("a-gate", "skip", detail=" ") for _ in range(UNEXPLAINED_SKIP_MAX)]
    assert run(events)["silent"] == []


# ─── 全绿 ───

def test_clean_workspace_reports_nothing():
    r = run([ev("a-gate", "block")], gates={"a-gate"}, known={"a-gate"})
    assert not has_red(r)
    assert (r["dead_gates"], r["dead_exempt"], r["zero"], r["loose"], r["silent"]) \
        == ([], [], [], [], [])
