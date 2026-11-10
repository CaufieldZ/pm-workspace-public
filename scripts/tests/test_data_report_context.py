"""data-report 写作素材正确性回归。

锁住喂给模型的注释块 / 表格标签不出错：排期解析、业务上下文分桶、节假周趋势、
季度基线注分流、关键变化覆盖、帖龄分类、附件清理归属、节假日拆解。
"""

import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

_SKILL_SCRIPTS = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "data-report" / "scripts"
sys.path.insert(0, str(_SKILL_SCRIPTS))

import confluence_sync  # noqa: E402
import gen_weekly_insights as gwi  # noqa: E402
import gen_weekly_md  # noqa: E402
import gen_weekly_metrics as gwm  # noqa: E402
from lib import truth_source as ts  # noqa: E402

_SCHEDULE = """# 8. 排期 / 上线节奏

## 8.1 排期

| 阶段 | 起止 | 进度 | 状态 | 影响指标 |
| :--- | :--- | :--- | :--- | :--- |
| 前端 | 待定 | 0% | 待启 | — |
| 上线 | 2026-10-20 | — | 待启 | Feed 点击率 |

## 8.2 验收

| 指标 | 基线 | 目标 | 口径 | 备注 |
| --- | --- | --- | --- | --- |
| 发言率 | 4.6% | 6% | 7 天中位数 | — |

# 9. 附录

| 阶段 | 起止 | 进度 | 状态 | 影响指标 |
| 不该被收 | — | — | — | — |
"""


# ── 排期解析 ─────────────────────────────────────────────────────────────────

def test_schedule_section_spans_subsections():
    """`# 8.` 下紧跟 `## 8.1`：章节截到下一个同级 `# 9.`，不在子节处截断。"""
    sec = ts._extract_schedule_section(_SCHEDULE)
    assert "8.1 排期" in sec and "8.2 验收" in sec and "附录" not in sec


def test_schedule_rows_only_stage_table():
    rows = ts._parse_schedule_rows(ts._extract_schedule_section(_SCHEDULE))
    assert [r["stage"] for r in rows] == ["前端", "上线"]


def test_version_key_numeric():
    assert sorted(["2.10", "2.9", "2.3.2"], key=ts._version_key) == ["2.3.2", "2.9", "2.10"]


def _write_delta(root: Path, quarter: str, version: str, status: str, body: str = "") -> None:
    d = root / "livestream" / "deliverables" / quarter / version
    d.mkdir(parents=True)
    (d / f"prd-livestream-{version}.md").write_text(
        f"| PRD 版本 | {version} | 状态 | {status} |\n\n{body}", encoding="utf-8"
    )


def test_current_deltas_latest_quarter_all_versions(tmp_path):
    (tmp_path / "livestream").mkdir()
    (tmp_path / "livestream" / "prd-livestream-baseline.md").write_text("x", encoding="utf-8")
    _write_delta(tmp_path, "2026Q2", "2.1", "已上线", _SCHEDULE)
    _write_delta(tmp_path, "2026Q3", "2.10", "待排期", _SCHEDULE)
    _write_delta(tmp_path, "2026Q3", "2.4", "待评审")
    _write_delta(tmp_path, "2026Q3", "2.3.2", "{{ 待填：状态 }}")
    seed = tmp_path / "livestream" / "deliverables" / "2026Q3" / "2.10" / "prd-livestream-2.10-seed.md"
    seed.write_text("附属文件", encoding="utf-8")

    got = ts.current_deltas(ts.resolve("livestream", tmp_path))
    assert [e["version"] for e in got] == ["2.3.2", "2.4", "2.10"]      # 只取最新季度，数值排序
    assert [e["status"] for e in got] == ["", "待评审", "待排期"]          # 占位符视为空
    assert got[1]["rows"] == [] and len(got[2]["rows"]) == 2


@pytest.mark.parametrize("status, bucket", [
    ("待评审", "D"), ("待排期", "D"), ("", "D"), ("开发中", "C"), ("已上线", None), ("已合并", None),
])
def test_bucket_without_dates(status, bucket):
    assert gwi._bucket_without_dates(status) == bucket


def test_business_context_filtered_by_line(monkeypatch):
    calls = []
    monkeypatch.setattr(gwi, "current_deltas", lambda t: calls.append(t.line) or [])
    gwi._scan_business_context(date(2026, 10, 9), gwi.REPORT_LINES["live"])
    assert calls == ["livestream"]


# ── 节假周趋势 ───────────────────────────────────────────────────────────────

_UCTR = {"2026-09-04": 24.62, "2026-09-11": 26.22, "2026-09-18": 26.21,
         "2026-09-25": 25.19, "2026-10-02": 28.78}
_HOL = {"2026-09-25", "2026-10-02"}


def _metrics(cur_holiday: bool) -> dict:
    weekly = {k: {"is_holiday": k in _HOL, "community": {"uctr": v}} for k, v in _UCTR.items()}
    return {"community": {"uctr": 27.57}, "weekly_all": weekly,
            "week_end": "2026-10-09", "is_holiday": cur_holiday}


def test_shape_holiday_week_compares_with_adjacent_weeks():
    """本周是节假周：不跳上周（28.78 > 27.57），不能标「4 周最高」。"""
    assert gwm.shape("uctr", "community", _metrics(True)) == "震荡"


def test_shape_normal_week_skips_holiday_weeks():
    assert gwm.shape("uctr", "community", _metrics(False)) == "4 周最高"


# ── 季度基线注 ───────────────────────────────────────────────────────────────

def test_quarter_notes_split_by_line_and_deduped():
    weekly = {}
    for d in (date(2026, 7, 3) + timedelta(weeks=i) for i in range(13)):
        live = {"viewers": 7000}
        if d >= date(2026, 9, 18):
            live.update(mic_join_cnt=14, mic_avg_join_per_session=1.8, mic_avg_duration_min=42,
                        feed_livecard_expose_uv=4856)
        weekly[d.isoformat()] = {"community": {"feed_dau": 8000}, "live": live}
    notes = gwm.prev_quarter_avg(date(2026, 10, 9), weekly)["notes"]
    assert notes["community"] == []
    assert len(notes["live"]) == 2                      # 连麦一条 + Feed 直播卡一条，不按 key 重复
    assert any("连麦" in n for n in notes["live"])


# ── 关键变化 ─────────────────────────────────────────────────────────────────

def test_key_changes_include_feed_livecard():
    m = {"community": {}, "hist_c": [{}],
         "live": {"feed_livecard_expose_uv": 7564, "mic_join_cnt": 47},
         "hist_l": [{"feed_livecard_expose_uv": 34665, "mic_join_cnt": 36}]}
    _, live = gwm._key_changes(m)
    assert any("社区 Feed 直播卡曝光 UV" in x for x in live)
    assert any("上麦人次" in x for x in live)           # +30.6% 过 20% 阈值


def test_key_changes_mic_uses_higher_threshold():
    m = {"community": {}, "hist_c": [{}], "live": {"mic_join_cnt": 40}, "hist_l": [{"mic_join_cnt": 36}]}
    assert gwm._key_changes(m)[1] == []                 # +11% 不足 20%


# ── extra 帖龄 ───────────────────────────────────────────────────────────────

def test_extra_post_age_by_days_not_year(tmp_path):
    rows = "\n".join(
        f"| {i} | {100 + i} | 中文 | {d} | 1,000 | 100 | 10% |"
        for i, d in enumerate(["2026-03-26", "2026-09-20", "2026-10-05"], 1)
    )
    f = tmp_path / "extra-1009.md"
    f.write_text(f"> 周期 2026-10-03 ~ 2026-10-09。\n\n## 一、热门帖子 Top 20\n\n{rows}\n\n## 二、x\n",
                 encoding="utf-8")
    age = gen_weekly_md._extract_extra_facts(f)["top_post_age"]
    assert age == {"new": 2, "old": 1, "oldest": "2026-03-26"}


# ── 附件清理归属 ─────────────────────────────────────────────────────────────

def test_prune_only_owned_trend_charts():
    atts = [{"title": t} for t in (
        "community-trends-1002.png", "live-trends-1002.png", "community-trends-1009.png",
        "trend-invite-rebate-0924.png", "image2026-9-28_11-22-1.png",
    )]
    body = '<ri:attachment ri:filename="community-trends-1009.png" />'
    owned = confluence_sync._select_orphans(atts, body, confluence_sync.OWNED_ATTACHMENT_RE)
    assert [a["title"] for a in owned] == ["community-trends-1002.png", "live-trends-1002.png"]
    assert len(confluence_sync._select_orphans(atts, body)) == 4   # 手动 prune 不过滤


def test_week_end_from_dir():
    assert confluence_sync._week_end_from_dir("x/weekly-0102").month == 1
    assert confluence_sync._week_end_from_dir("x/other") is None


# ── 节假日拆解 ───────────────────────────────────────────────────────────────

def _daily() -> dict:
    days = [date(2026, 9, 12) + timedelta(days=i) for i in range(28)]
    feed, home = [], []
    for d in days:
        if date(2026, 10, 3) <= d <= date(2026, 10, 5):
            feed.append(6400); home.append(96000)
        elif d >= date(2026, 10, 6):
            feed.append(6700); home.append(99000)
        else:
            feed.append(7600); home.append(106000)
    return {"dates": [d.isoformat() for d in days], "feed_dau": feed, "homepage_uv": home}


def test_holiday_breakdown_three_segments():
    hol = {"2026-09-25", "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05"}
    b = gwi.holiday_breakdown(_daily(), hol, date(2026, 10, 3), date(2026, 10, 9))
    assert b["holidays"] == ["2026-10-03", "2026-10-04", "2026-10-05"]
    assert b["work_label"] == "节后工作日"
    assert b["base_days"][0] == "2026-09-14"            # 09.21 那周含中秋、09.28 那周含国庆，都跳过
    assert b["feed_dau"] == {"hol": 6400, "work": 6700, "base": 7600}


def test_holiday_breakdown_none_without_holiday():
    assert gwi.holiday_breakdown(_daily(), set(), date(2026, 10, 3), date(2026, 10, 9)) is None


def test_holiday_comment_renders_relative_diffs():
    m = {"daily_28d": _daily(), "week_end": "2026-10-09", "is_holiday": True,
         "events": [{"date": d, "type": "holiday", "region": "cn", "label": "国庆节"}
                    for d in ("2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05")]
         + [{"date": "2026-09-25", "type": "holiday", "region": "cn", "label": "中秋节"}]}
    out = gwi._gen_holiday_breakdown(m)
    assert "本周含 3 天法定假期：国庆节" in out
    assert re.search(r"节后工作日比节前同期：-11\.8%；同期 App 主入口 UV -6\.6%", out)


# ── 防覆盖：推送前检查人工修改 ───────────────────────────────────────────────

def _page(sec2: str) -> str:
    return (f"<h2>1 拉新转化</h2><p>别的区块</p>{confluence_sync.SECTION_START}{sec2}"
            "<h2>3 火伴 AI</h2><p>x</p>")


_SEC = ('<h3>1. 社区流量降到 4 周最低</h3><ul><li>Feed DAU 6,579</li></ul>'
        '<p><ac:image><ri:attachment ri:filename="community-trends-1009.png" /></ac:image></p>')


def test_section2_text_ignores_markup_changes():
    """编辑器保存会重排标记 / 加样式，没改字就不算人工修改。"""
    restyled = _SEC.replace("<h3>", '<h3 style="color: rgb(0,0,255)">').replace("<li>", "<li><span>")
    assert confluence_sync._section2_text(_page(_SEC)) == confluence_sync._section2_text(_page(restyled))


def test_manual_text_edit_detected():
    edited = _SEC.replace("降到 4 周最低", "降到 4 周最低（国庆假期影响）")
    a = confluence_sync._section2_text(_page(_SEC))
    b = confluence_sync._section2_text(_page(edited))
    diff = confluence_sync._manual_edit_diff(a, b)
    assert any(ln.startswith("+") and "国庆假期影响" in ln for ln in diff)
    assert confluence_sync._manual_edit_diff(a, a) == []


def test_image_swap_detected():
    swapped = _SEC.replace("community-trends-1009.png", "manual-chart.png")
    a = confluence_sync._section2_text(_page(_SEC))
    assert confluence_sync._manual_edit_diff(a, confluence_sync._section2_text(_page(swapped)))


def test_section2_text_scoped_to_section():
    """其他区块被改不影响「2 内容平台」的比对。"""
    other = _page(_SEC).replace("别的区块", "领导改了拉新")
    assert confluence_sync._section2_text(other) == confluence_sync._section2_text(_page(_SEC))
