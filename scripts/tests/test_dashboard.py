"""dashboard 四渲染函数单测（C8 回归锚）：

锁住 2026-08 脚本深审轮 setdefault 类 bug 的修复面——「最近一次」必须取
时间正序流水的最后一条（render_hub / render_skills / render_agents /
render_routes 四处同发过「取最旧当最近」）；顺带锁 dead / hot 阈值、
detail 多包解析、HAS_CHECKER 完成率、KNOWN_ROUTES 固定枚举与
load_events 的窗过滤 / 坏行容错。
"""
from datetime import timedelta

import dashboard as d

TS_OLD = "2026-08-01T09:00:00+08:00"
TS_NEW = "2026-08-14T18:30:00+08:00"


def _row(text, name):
    """取 markdown 表里 `name` 所在行，便于断言该行内容。"""
    return next(l for l in text.splitlines() if name in l)


# ── render_hub：最近一次 / 阈值 / detail 多包 ────────────────
def _hub_ev(ts, detail):
    return {"type": "skill", "name": "hub-repack", "action": "triggered",
            "detail": detail, "ts": ts}


def test_hub_last_touch_keeps_latest(tmp_path, monkeypatch):
    hub = tmp_path / "hub"
    (hub / "alpha").mkdir(parents=True)
    monkeypatch.setattr(d, "HUB_DIR", hub)
    out = d.render_hub([_hub_ev(TS_OLD, "alpha"), _hub_ev(TS_NEW, "alpha")], 14)
    assert "2026-08-14" in _row(out, "`alpha`")


def test_hub_dead_warm_hot_thresholds(tmp_path, monkeypatch):
    hub = tmp_path / "hub"
    for name in ("dead-pkg", "warm-pkg", "hot-pkg"):
        (hub / name).mkdir(parents=True)
    monkeypatch.setattr(d, "HUB_DIR", hub)
    events = ([_hub_ev(TS_NEW, "warm-pkg")] * 4
              + [_hub_ev(TS_NEW, "hot-pkg")] * 5)
    out = d.render_hub(events, 14)
    assert "🔘 dead" in _row(out, "`dead-pkg`") and "| 0 |" in _row(out, "`dead-pkg`")
    assert "🔘" not in _row(out, "`warm-pkg`") and "🔥" not in _row(out, "`warm-pkg`")
    assert "🔥 hot" in _row(out, "`hot-pkg`")


def test_hub_detail_multi_pkg_and_hub_slash_token(tmp_path, monkeypatch):
    """detail="prd scene-list"（repack 批量）与 "hub/prd"（vet 传目录）两种形态都按包计数。"""
    hub = tmp_path / "hub"
    for name in ("prd", "scene-list"):
        (hub / name).mkdir(parents=True)
    monkeypatch.setattr(d, "HUB_DIR", hub)
    out = d.render_hub([_hub_ev(TS_NEW, "prd scene-list"),
                        _hub_ev(TS_NEW, "hub/prd")], 14)
    assert "| 2 |" in _row(out, "`prd`")  # 空格式 token + hub/ 前缀各 1
    assert "| 1 |" in _row(out, "`scene-list`")


# ── render_skills：最近一次 / 阈值 / HAS_CHECKER 完成率 ─────
def _skill_ev(name, action, ts):
    return {"type": "skill", "name": name, "action": action, "ts": ts}


def test_skills_last_trigger_latest_and_checker_rate(tmp_path, monkeypatch):
    skills = tmp_path / "skills"
    for name in ("prd", "zz-noop"):
        (skills / name).mkdir(parents=True)
    monkeypatch.setattr(d, "SKILLS_DIR", skills)
    events = (
        [_skill_ev("prd", "triggered", TS_OLD)]
        + [_skill_ev("prd", "triggered", TS_NEW)] * 2
        + [_skill_ev("prd", "completed", TS_NEW)] * 3
        + [_skill_ev("prd", "failed", TS_NEW)]
    )
    out = d.render_skills(events, 14)
    prd = _row(out, "| prd |")
    assert "2026-08-14" in prd              # 最近触发取新 ts
    assert "3 / 1" in prd and "75%" in prd  # checker：完成率列
    noop = _row(out, "| zz-noop |")
    assert "🔘 dead" in noop                # 0 触发
    assert "| — | — | — |" in noop          # 非 checker：完成 / 失败、完成率、最近完成均 —


def test_skills_hot_threshold_and_latest_complete(tmp_path, monkeypatch):
    skills = tmp_path / "skills"
    (skills / "zz-noop").mkdir(parents=True)
    monkeypatch.setattr(d, "SKILLS_DIR", skills)
    events = ([_skill_ev("zz-noop", "triggered", TS_OLD)] * 9
              + [_skill_ev("zz-noop", "triggered", TS_NEW)]
              + [_skill_ev("zz-noop", "completed", TS_OLD)]
              + [_skill_ev("zz-noop", "completed", TS_NEW)])
    out = d.render_skills(events, 14)
    row = _row(out, "| zz-noop |")
    assert "🔥 hot" in row                 # 10 触发达标
    assert row.count("2026-08-14") == 2    # 最近触发 + 最近完成都取新


# ── render_agents：最近一次 / 占比 / top2 描述 ──────────────
def test_agents_latest_pct_and_top2_desc():
    events = [
        {"type": "agent", "name": "Explore", "ts": TS_OLD, "detail": "d" * 40},
        {"type": "agent", "name": "Explore", "ts": TS_NEW, "detail": "查 CSS 裸字体"},
        {"type": "agent", "name": "Plan", "ts": TS_NEW, "detail": "设计方案"},
    ]
    out = d.render_agents(events, 14)
    explore = _row(out, "| Explore |")
    assert "2026-08-14" in explore and "| 66% |" in explore  # 2*100//3 整除向下
    assert ("d" * 30 + " / 查 CSS 裸字体") in explore        # top2 各截 30 字


def test_agents_empty_returns_note():
    assert "无 sub-agent 调度记录" in d.render_agents([], 14)


# ── render_routes：最近一次 / 阈值 / 固定枚举 ────────────────
def test_routes_latest_thresholds_and_known_only():
    events = (
        [{"type": "route", "name": "slack", "ts": TS_OLD},
         {"type": "route", "name": "slack", "ts": TS_NEW}]
        + [{"type": "route", "name": "dashboard", "ts": TS_NEW}] * 10
        + [{"type": "route", "name": "ghost-route", "ts": TS_NEW}]
    )
    out = d.render_routes(events, 14)
    assert "2026-08-14" in _row(out, "| slack |")
    assert "🔥 hot" in _row(out, "| dashboard |")
    assert "ghost-route" not in out               # 固定枚举：未登记 name 不产生行
    assert "🔘 dead" in _row(out, "| publish |")  # 零调用路由仍可见


# ── load_events：窗过滤 + 坏行容错 ──────────────────────────
def test_load_events_filters_window_and_bad_lines(tmp_path, monkeypatch):
    recent = d.NOW - timedelta(hours=1)
    stale = d.NOW - timedelta(days=20)
    f = tmp_path / "usage.jsonl"
    lines = [
        '{"type": "route", "name": "ok", "ts": "%s"}' % recent.isoformat(),
        '{"type": "route", "name": "stale", "ts": "%s"}' % stale.isoformat(),
        "{not json",
        "",
        '{"no_ts_key": 1}',
    ]
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.setattr(d, "LOG_FILE", f)
    events = d.load_events(14)
    assert [e["name"] for e in events] == ["ok"]
