"""gen_weekly_all.step_path 单元测试。

锁回归：step_path 返回路径落在系统临时目录（tempfile.gettempdir()），
不硬编码 /tmp —— Windows 原生 Python 不映射 /tmp，Path("/tmp/x") 落到 C:\tmp 失败。
"""

import inspect
import json
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

# gen_weekly_all 是 data-report skill 的脚本（不在 scripts/ 根），显式加路径以 import
_SKILL_SCRIPTS = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "data-report" / "scripts"
sys.path.insert(0, str(_SKILL_SCRIPTS))

import confluence_sync  # noqa: E402
import fetch_weekly_youshu  # noqa: E402
import gen_weekly_all  # noqa: E402
import gen_weekly_md  # noqa: E402
import gen_weekly_metrics  # noqa: E402


def test_step_path_lands_under_tempdir():
    """返回路径的祖父目录必须是 tempfile.gettempdir()，锁住不硬编码 /tmp。"""
    p = gen_weekly_all.step_path("0619", 3)
    assert p.parent.parent == Path(tempfile.gettempdir())


def test_step_path_creates_dir_and_names_file():
    """副作用：建目录；返回文件名 step{n}.json，目录名 weekly-{mmdd}。"""
    p = gen_weekly_all.step_path("0619", 7)
    assert p.parent.is_dir()
    assert p.parent.name == "weekly-0619"
    assert p.name == "step7.json"


# ── 渲染回归 + business 隔离保险 ──────────────────────────────────────────────
# 锁住「推 Confluence 那张看板」的渲染输出。边界：带单漏斗（社区交易卡 / 直播策略卡）
# 逐周窗口进明细表；引流类业务指标（summary.business, 28d 滚动）只走洞察引用不进表。
# 这组测试把该边界钉死：谁改 gen_weekly_all 碰到周报表,立即红。

# 明细表口径（= step9_metrics 产出的 key 全集，冻结）
_COMMUNITY_KEYS = {
    "feed_dau", "penetration", "duration", "retention", "exposure_count",
    "pctr", "uctr", "like_rate", "comment_rate", "share_rate", "post_rate", "post_count",
}
_LIVE_KEYS = {
    "penetration", "watch_uv_app", "sessions", "streamers", "viewers", "watch_duration",
    "interact_rate", "chat_rate", "like_rate", "trade_rate", "trade_vol",
    "per_streamer_viewers", "per_streamer_trade_vol",
    "trtc_cur", "trtc_w1",
    "mic_apply_uv",
    "feed_livecard_expose_uv", "feed_livecard_click_uv", "feed_livecard_ctr",
    "mic_join_cnt", "mic_avg_join_per_session", "mic_avg_duration_min",
}
_COMMUNITY_ROW_LABELS = [
    "Feed DAU", "Feed 渗透率", "人均停留时长", "次日复访率", "Feed 曝光量",
    "Feed PCTR", "Feed UCTR", "点赞渗透率", "评论渗透率",
    "发帖渗透率", "发帖量",
    # 帖内交易卡带单：逐环节各一行，率行在其 UV 行之前（止于面板，提交 / 成交埋点未注册）
    "曝光 UV", "点击率", "点击 UV", "进面板率", "面板 UV", "整体转化率",
]
_LIVE_ROW_LABELS = [
    # 社区 Feed 直播卡（G-5）：数的是社区 Feed 里的卡，不是直播间内
    "直播卡曝光 UV", "直播卡点击 UV", "卡点击率",
    # 渗透两行只在本地 md，不进 LIVE_ROWS_SPEC / 不上 Confluence
    "直播渗透率", "App 观众端 UV",
    "日均直播场次", "活跃主播数", "TRTC 主播覆盖率",
    "日均观看人数", "平均观看时长", "互动率", "单主播日均观看人数",
    # 连麦并进观众活跃：举手申请人数走行为分析平台（2.2 新功能，只覆盖 App 观众端举手，
    # 主播端审批事件未注册）；后三行来有数逐场明细（只含有举手的场次 + 近 10 天滚动窗）
    "举手申请人数", "上麦人次", "场均上麦人次", "人均在麦时长（分钟）",
    # 策略卡转化（真实归因）：逐环节各一行 + 成交一行
    "曝光 UV", "点击率", "点击 UV", "进面板率", "面板 UV",
    "提交率", "提交 UV", "整体转化率", "成交（笔 / U）",
    # 市场背景：行情拉空时为「本周缺数」占位行，行集恒在（confluence_sync 按指标名断言）
    "BTC 行情", "ETH 行情",
]
# 共现口径「观看当日交易转化率 / 交易额」已永久撤出周报（易被误读成直播归因）：
# 数据仍进 history.json，但不上表、不进洞察，出现在任一渲染产物即红
_RETIRED_ROW_LABELS = ["观看当日交易转化率", "观看当日交易额"]
# business 字段名 / 标签 —— 任一漏进渲染产物即「业务指标泄漏到看板」
# 带单漏斗已正式入表,其业务标签不在此列；这里只管引流类指标 + 所有技术字段名
_BUSINESS_MARKERS = [
    "live_gendan", "comm_to_live", "completion_rate", "card_show_users",
    "livecard_show_users", "引流点击率", "28d 滚动",
]


def _sensors_with_business():
    """带 summary.business 的行为分析平台取数输出（fetch_weekly_sensors 扩展后的形态）。"""
    return {"summary": {
        "community": {"feed_dau": 11456, "penetration": 8.3, "retention": 26.4,
                      "exposure_count": 102191, "like_rate": 1.3, "comment_rate": 1.9,
                      "share_rate": 0.6, "post_rate": 1.5},
        "live": {"penetration": 2.4, "watch_uv_app": 3338,
                 # 社区 Feed 直播卡（周区间去重，card_source=community_feed）
                 "feed_livecard_expose_uv": 4856, "feed_livecard_click_uv": 45,
                 "feed_livecard_ctr": 0.93},
        "business": {
            "comm_to_live": {"livecard_show_users": 59061, "click_rate": 1.88},
            "_window": "2026-05-27~2026-06-23 (28d 滚动)",
        },
        # 带单漏斗：逐周窗口（本周 + W-1..W-3），进明细表
        "trade_funnel": {
            "community": {"weeks": [
                {"show_uv": 13, "step1_uv": 2, "step1_rate": 15.38,
                 "step2_uv": 0, "step2_rate": 0.0},
                {"show_uv": 6, "step1_uv": 2, "step1_rate": 33.33,
                 "step2_uv": 1, "step2_rate": 50.0},
                {}, {},
            ]},
            "live": {"weeks": [
                {"show_uv": 1169, "step1_uv": 166, "step1_rate": 14.2,
                 "step2_uv": 124, "step2_rate": 74.7,
                 "step3_uv": 4, "step3_rate": 3.23},
                {"show_uv": 1283, "step1_uv": 159, "step1_rate": 12.39,
                 "step2_uv": 129, "step2_rate": 81.13,
                 "step3_uv": 2, "step3_rate": 1.55},
                {}, {},
            ]},
        },
    }}


def _csv_data():
    return {
        "community": {"duration": 43, "pctr": 11.4, "uctr": 24.5, "post_count": 407},
        "live": {"sessions": 76.6, "streamers": 80, "viewers": 9610, "watch_duration": 7.4,
                 "interact_rate": 9.4, "chat_rate": 2.4, "like_rate": 5.5,
                 "trade_rate": 39.1, "trade_vol": 33631,
                 "per_streamer_viewers": 120, "per_streamer_trade_vol": 420,
                 # 商分 BI 逐卡明细：成交笔数 / 成交额，只覆盖本周 + W-1
                 "card_deals": {"cur": {"deals": 3, "amount": 93.33},
                                "w1": {"deals": 1, "amount": 19.63},
                                "latest_date": "2026-06-19"},
                 # 商分 BI「直播连麦」逐场明细：只含有举手的场次 + 近 10 天滚动窗
                 "mic": {"join_cnt": 14, "active_sessions": 8,
                         "avg_join_per_session": 1.8, "avg_duration_min": 42.0}},
    }


def _dates():
    return {"period": "2026-06-13 ~ 2026-06-19", "period_label": "06.13~06.19",
            "week_end": "2026-06-19"}


def _metrics():
    """走真实 step9_metrics 合并，history 留空（历史列渲染为 —）。"""
    return gen_weekly_all.step9_metrics(_dates(), _sensors_with_business(), _csv_data(), [])


def _data_rows(md: str) -> list:
    """md 表格数据行（| 开头，排除表头与分隔行）。"""
    return [ln for ln in md.splitlines()
            if ln.startswith("| ") and "---" not in ln and "分类" not in ln]


def test_step9_metrics_drops_business():
    """summary.business 不得进入 metrics —— 业务指标走洞察引用,不进明细表。"""
    m = _metrics()
    assert "business" not in m
    assert set(m["community"].keys()) == _COMMUNITY_KEYS
    assert set(m["live"].keys()) == _LIVE_KEYS


def test_community_table_locked(monkeypatch):
    """社区明细表行集 + 行数固定（增删行即红）。"""
    # 必须打 gen_weekly_md 上的名字：它 import 时已把 _gen_insight_stubs 绑进自己命名空间,
    # 打 gen_weekly_insights 那份不生效（洞察生成会真跑，扫 projects 拖慢并污染断言）
    monkeypatch.setattr(gen_weekly_md, "_gen_insight_stubs", lambda *a, **k: "[stub]")
    md = gen_weekly_all.gen_community_md("0619", _metrics(), [])
    for label in _COMMUNITY_ROW_LABELS:
        assert label in md, f"社区表缺行: {label}"
    assert len(_data_rows(md)) == len(_COMMUNITY_ROW_LABELS)


def test_live_table_locked(monkeypatch):
    """直播明细表行集 + 行数固定;共现口径两行已撤出,复活即红。"""
    # 必须打 gen_weekly_md 上的名字：它 import 时已把 _gen_insight_stubs 绑进自己命名空间,
    # 打 gen_weekly_insights 那份不生效（洞察生成会真跑，扫 projects 拖慢并污染断言）
    monkeypatch.setattr(gen_weekly_md, "_gen_insight_stubs", lambda *a, **k: "[stub]")
    md = gen_weekly_all.gen_live_md("0619", _metrics(), [])
    for label in _LIVE_ROW_LABELS:
        assert label in md, f"直播表缺行: {label}"
    for label in _RETIRED_ROW_LABELS:
        assert label not in md, f"已撤出的共现口径复活: {label}"
    assert len(_data_rows(md)) == len(_LIVE_ROW_LABELS)


def test_business_not_leak_into_tables(monkeypatch):
    """business 字段名 / 标签不得出现在任一周报渲染产物里。"""
    # 必须打 gen_weekly_md 上的名字：它 import 时已把 _gen_insight_stubs 绑进自己命名空间,
    # 打 gen_weekly_insights 那份不生效（洞察生成会真跑，扫 projects 拖慢并污染断言）
    monkeypatch.setattr(gen_weekly_md, "_gen_insight_stubs", lambda *a, **k: "[stub]")
    m = _metrics()
    comm = gen_weekly_all.gen_community_md("0619", m, [])
    live = gen_weekly_all.gen_live_md("0619", m, [])
    for marker in _BUSINESS_MARKERS:
        assert marker not in comm, f"business 泄漏进社区周报: {marker}"
        assert marker not in live, f"business 泄漏进直播周报: {marker}"


# ── 洞察渲染回归（锁 leader 改稿对齐的那套排版）────────────────────────────────
# 社区 = 两句整体蓝（首句加粗）；直播 = `### N. 判断句` 蓝+加粗、bullet 不套色；
# `==x==` → 绿色高亮。谁改 extract_insights_xhtml 弄丢这几种形态，立即红。

def _render(tmp_path, body: str) -> str:
    p = tmp_path / "x-weekly-0000.md"
    p.write_text(f"# t\n\n## 洞察\n\n{body}\n", encoding="utf-8")
    return confluence_sync.extract_insights_xhtml(p)


def test_community_insight_two_blue_paragraphs(tmp_path):
    """社区：两句都蓝，首句加粗、次句不加粗，且首句不出现嵌套 <strong>。"""
    html = _render(tmp_path, "**社区流量继续下探，但留存盘稳在季度基线。**\n\n发帖量下降，卡片以现货持仓为主。\n")
    assert html.count('style="color: #0000FF"') == 2
    assert '<p><span style="color: #0000FF"><strong>社区流量继续下探' in html
    assert "<strong><strong>" not in html
    assert '<p><span style="color: #0000FF">发帖量下降' in html


def test_community_insight_bolds_first_paragraph_without_md_marker(tmp_path):
    """首句没手写 ** 时也要加粗（历史 md 兼容）。"""
    html = _render(tmp_path, "社区流量继续下探。\n\n发帖量下降。\n")
    assert '<span style="color: #0000FF"><strong>社区流量继续下探。</strong></span>' in html


def test_live_insight_numbered_heading_blue_bold(tmp_path):
    """直播：`### N. 判断句` → 蓝色 + 序号不粗、判断句加粗；普通段落不套色。"""
    html = _render(tmp_path, "### 1. 观众规模环比稳定\n\n- 日均观看人数 7,306 人\n\n业务原因这截不套色\n")
    assert '<p><span style="color: #0000FF">1. <strong>观众规模环比稳定</strong></span></p>' in html
    assert "<ul><li>日均观看人数 7,306 人</li></ul>" in html
    assert "<p>业务原因这截不套色</p>" in html


def test_insight_green_highlight(tmp_path):
    """`==x==` → 绿色高亮；行内 ** 仍转加粗。"""
    html = _render(tmp_path, "### 1. 标题\n\n- ==人均观看时长 10.2 分钟，连续 8 周走高==\n")
    assert '<span style="color: #008000">人均观看时长 10.2 分钟，连续 8 周走高</span>' in html


# ── 环比口径：率给百分点 ──────────────────────────────────────────────────────
# 率用相对变化会把 1.1% → 5.2% 报成「+349%」（读成涨 3.5 倍，实际 8 人变 48 人）。
# 同页「1 拉新转化」节用 pt，本表对齐。低基数率补一个相对值括号。

@pytest.mark.parametrize("cur,prev,expect", [
    (71.6, 24.2, "+47.4pt（+196%）"),   # 漏斗率大幅变动：pt 主，相对值进括号
    (1.2, 1.1, "+0.1pt（+9%）"),        # 低基数率：pt 看着像噪音，相对值才是读数
    (27.6, 27.0, "+0.6pt"),            # 相对变化不足 5%，括号省掉
    (7.1, 7.2, "-0.1pt"),
])
def test_mom_rate_uses_percentage_points(cur, prev, expect):
    assert gen_weekly_metrics.mom(cur, prev, True) == expect


@pytest.mark.parametrize("cur,prev,expect", [
    (7368, 7850, "-6.1%"),   # 计数型不变：相对变化就是正确表达
    (48, 8, "+500.0%"),
])
def test_mom_count_keeps_relative_change(cur, prev, expect):
    assert gen_weekly_metrics.mom(cur, prev) == expect
    assert "pt" not in gen_weekly_metrics.mom(cur, prev)


# ── 趋势列：真跨周形态 ────────────────────────────────────────────────────────
# 老实现是 arrow()，只看上一周却挂在写着「4 周形态」的列下。

@pytest.mark.parametrize("series,expect", [
    # 回归锚：人均停留时长实测序列，跌-涨-跌。arrow() 给 ↘，会被读成持续走低
    ([40.1, 45.1, 35.4, 37.4], "震荡"),
    ([7368, 7850, 8913, 9373], "连续 4 周走低"),
    ([10.2, 9.4, 9.2, 7.9], "连续 4 周走高"),
    # 并列极值不算新低：提交率 0 与另两周持平，标「4 周最低」会被读成刚创新低
    ([0, 0, 8.3, 0], "震荡"),
    ([72.7, 83.6, 75.9, 87.1], "4 周最低"),
    ([27.6, 27.0, 26.1, 27.5], "4 周最高"),
    # 首周指标历史不足：必须是 —，不能是「持平」语义的 →
    ([14, None, None, None], "—"),
    ([14, 12, None, None], "—"),
])
def test_shape_from_series(series, expect):
    assert gen_weekly_metrics.shape_from_series(series) == expect


@pytest.mark.parametrize("trend,color", [
    ("连续 9 周走高", "#00B050"),
    ("4 周最高", "#00B050"),
    ("连续 4 周走低", "#F53F3F"),
    ("4 周最低", "#F53F3F"),
])
def test_colorize_trend_words(trend, color):
    assert color in confluence_sync._colorize_trend(trend)


@pytest.mark.parametrize("trend", ["震荡", "—"])
def test_colorize_trend_neutral_not_colored(trend):
    assert confluence_sync._colorize_trend(trend) == trend


# ── Confluence 表口径（本地 md 全量 → 上报收窄）────────────────────────────────
# 这两个行数断言是防漏行的唯一闸门，改错会让整条推送链路静默少推。

def _report_dir(tmp_path, monkeypatch) -> Path:
    monkeypatch.setattr(gen_weekly_md, "_gen_insight_stubs", lambda *a, **k: "[stub]")
    m = _metrics()
    (tmp_path / "community-weekly-0619.md").write_text(
        gen_weekly_all.gen_community_md("0619", m, []), encoding="utf-8")
    (tmp_path / "live-weekly-0619.md").write_text(
        gen_weekly_all.gen_live_md("0619", m, []), encoding="utf-8")
    return tmp_path


def test_confluence_row_counts_locked(tmp_path, monkeypatch):
    """社区 14 行 / 直播 18 行。本地 md 是 17 / 27 项全量,上报按三条收窄。"""
    rows = confluence_sync.extract_rows(_report_dir(tmp_path, monkeypatch))
    assert len(rows["community"]) == 14
    assert len(rows["live"]) == 18


def test_confluence_drops_md_only_rows(tmp_path, monkeypatch):
    """TRTC 覆盖率 / 行情两行 / 直播渗透率只留本地 md,不上 Confluence。"""
    rows = confluence_sync.extract_rows(_report_dir(tmp_path, monkeypatch))
    live_labels = [r[1] for r in rows["live"]]
    for dropped in ("TRTC 主播覆盖率", "BTC 行情", "ETH 行情", "直播渗透率", "App 观众端 UV"):
        assert dropped not in live_labels, f"该行不该上 Confluence: {dropped}"


def test_confluence_merges_rate_into_uv_cell(tmp_path, monkeypatch):
    """率并进 UV 行：标签成「点击 UV(点击率)」,四个周列逐列拼成「2(15.4%)」。"""
    rows = confluence_sync.extract_rows(_report_dir(tmp_path, monkeypatch))
    merged = [r for r in rows["community"] if r[1] == "点击 UV(点击率)"]
    assert merged, [r[1] for r in rows["community"]]
    assert merged[0][2] == "2(15.4%)"
    # 率不再单独占行
    assert "点击率" not in [r[1] for r in rows["community"]]


def test_confluence_table_has_no_note_column(tmp_path, monkeypatch):
    """Confluence 表 9 列，不带说明列。"""
    rows = confluence_sync.extract_rows(_report_dir(tmp_path, monkeypatch))
    assert all(len(r) == 9 for r in rows["community"] + rows["live"])
    html = confluence_sync._build_table(rows["community"], ["a", "b", "c", "d"])
    assert "<th>说明</th>" not in html
    assert html.count("</th>") == 9


# ── 推前门槛：默认不写 wiki，须显式 --push ────────────────────────────────────
# 门槛的意义全在「默认值」上——这组测试钉死默认，谁把默认改回「推」立即红。
# 决策见 .claude/decisions/implemented/2026-09-28-weekly-push-human-review-gate.md

_SCRIPT = _SKILL_SCRIPTS / "confluence_sync.py"


@pytest.mark.parametrize(
    "dry_run,push,pending,expect",
    [
        (True, False, [], "dry-run"),
        (True, True, [], "dry-run"),          # dry-run 优先级最高，演练语义不被 --push 抢走
        (False, False, [], "gated"),          # 默认路径
        (False, False, ["a.md"], "gated"),    # 没带 --push 时 pending 不改变结论
        (False, True, ["a.md"], "blocked"),
        (False, True, [], "push"),
    ],
)
def test_push_decision_matrix(dry_run, push, pending, expect):
    assert gen_weekly_all._push_decision(dry_run, push, pending) == expect


def test_sync_full_signature_frozen():
    """sync_full 不加 push 参数——授权是会话层的事，塞进函数体会让程序化调用方静默变 no-op。"""
    params = inspect.signature(confluence_sync.sync_full).parameters
    assert list(params) == ["report_dir", "history_path", "dry_run", "week_end"]
    assert params["dry_run"].default is False


def _run(*argv):
    return subprocess.run(
        [sys.executable, str(argv[0]), *argv[1:]], capture_output=True, text=True
    )


def test_confluence_cli_exposes_push_flag():
    assert "--push" in _run(_SCRIPT, "--help").stdout


def test_sync_full_without_push_writes_nothing(tmp_path):
    """默认路径：打 [push-gate]、不碰网络（空目录也能跑通）、明说 wiki 未改动。"""
    r = _run(_SCRIPT, "--sync-full", str(tmp_path))
    assert r.returncode == 0
    assert "push-gate" in r.stderr
    assert "未写 Confluence" in r.stderr


def test_sync_full_push_blocked_on_insight_stub(tmp_path):
    """洞察还是 [待补充] 桩时 --push 也不许推——堵住主推路径绕开 gen_weekly_all 检查的口子。"""
    (tmp_path / "community-weekly-0925.md").write_text(
        "## 洞察\n\n[待补充 · 洞察写法]\n\n## 数据明细\n\n", encoding="utf-8"
    )
    r = _run(_SCRIPT, "--sync-full", str(tmp_path), "--push")
    assert r.returncode == 0
    assert "阻断" in r.stderr
    assert "community-weekly-0925.md" in r.stderr


def test_confluence_pending_stub_detector(tmp_path):
    (tmp_path / "live-weekly-0925.md").write_text("## 洞察\n[待补充\n", encoding="utf-8")
    (tmp_path / "community-weekly-0925.md").write_text("## 洞察\n### 1. 判断句\n", encoding="utf-8")
    assert confluence_sync._pending_insight_stubs(tmp_path) == ["live-weekly-0925.md"]


@pytest.mark.parametrize(
    "argv,expect_pushed",
    [([], False), (["--skip-push"], False), (["--dry-run"], True), (["--push"], True)],
)
def test_kefu_default_does_not_push(tmp_path, monkeypatch, argv, expect_pushed):
    """客服通道默认不推（与主链路对称）；--dry-run 仍保留「演练 h3 断言不写回」语义。"""
    import gen_kefu_weekly as gk

    monkeypatch.setattr(gk, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(gk, "pull_bi", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(gk, "pull_homepage_uv", lambda *a, **k: 0)
    monkeypatch.setattr(gk, "compute_week", lambda *a, **k: {})
    monkeypatch.setattr(gk, "gen_kefu_md", lambda *a, **k: "md")
    monkeypatch.setattr(gk, "merge_history", lambda *a, **k: None)
    monkeypatch.setattr(gk, "_read_history", lambda: {})
    pushed = []
    monkeypatch.setattr(gk, "push", lambda *a, **k: pushed.append(a))

    monkeypatch.setattr(sys, "argv", ["gen_kefu_weekly.py", "--week-end", "2026-09-04", *argv])
    gk.main()
    assert bool(pushed) is expect_pushed


# ── 4.1 客服：开场分析 + 表行截断 ────────────────────────────────────────────

@pytest.mark.parametrize("raw,expect", [
    (232535, "23.25万"),
    (140000, "14万"),
    (10000, "1万"),
])
def test_wan_format(raw, expect):
    assert confluence_sync._wan(raw) == expect


@pytest.mark.parametrize("cur,prev,expect", [
    (110, 100, "，较上周增加10.0%"),
    (90, 100, "，较上周减少10.0%"),
    (100, 100, "，与上周持平"),
    (100, None, ""),        # 无上周可比 → 不出环比从句
    (None, 100, ""),
])
def test_mom_txt(cur, prev, expect):
    assert confluence_sync._mom_txt(cur, prev) == expect


@pytest.mark.parametrize("cur,prev,expect", [
    ({"center_pv": 110, "app_dau": 101}, {"center_pv": 100, "app_dau": 100},
     "客服访问回升幅度高于App周活跃增幅"),
    ({"center_pv": 101, "app_dau": 110}, {"center_pv": 100, "app_dau": 100},
     "客服访问回升幅度低于App周活跃增幅"),
    ({"center_pv": 98, "app_dau": 99}, {"center_pv": 100, "app_dau": 100},
     "客服访问回落幅度大于App周活跃降幅"),
    ({"center_pv": 100, "app_dau": 100}, {"center_pv": 100, "app_dau": 100},
     "客服访问与App周活跃同步变化"),
    ({"center_pv": 100}, {"center_pv": 100}, ""),   # 缺 app_dau → 不做比较
])
def test_kefu_access_vs_dau(cur, prev, expect):
    assert confluence_sync._kefu_access_vs_dau(cur, prev) == expect


def _kefu_rows(n_weeks: int, end: date = date(2026, 10, 16)) -> list[dict]:
    rows = [{"label": "Q1周均", "app_dau": 400000}]
    for i in range(n_weeks, 0, -1):
        d = end - timedelta(days=7 * (i - 1))
        rows.append({
            "label": f"{(d - timedelta(days=7)).strftime('%m%d')}-{(d - timedelta(days=1)).strftime('%m%d')}",
            "app_dau": 200000 + i * 100,
            "center_pv": 14000 + i * 10,
            "human_pv": 4000 + i,
            "intercept_rate": 49.0 + i / 100,
        })
    return rows


def test_kefu_lead_uses_target_week():
    lead = confluence_sync._kefu_lead(_kefu_rows(3), date(2026, 10, 16))
    assert lead.startswith("<p>本周App周活跃为")
    assert "进线拦截率" in lead


def test_kefu_lead_refuses_stale_week():
    """当期 kefu 没落盘时，「本周」会指向上一周 —— 必须报错而不是静默推错数。"""
    with pytest.raises(RuntimeError, match="不是目标周"):
        confluence_sync._kefu_lead(_kefu_rows(3), date(2026, 10, 23))


def test_kefu_lead_needs_two_weeks():
    assert confluence_sync._kefu_lead(_kefu_rows(1), date(2026, 10, 16)) == ""


def test_kefu_rows_keep_all_baselines_and_three_weeks(tmp_path):
    hist = {
        "kefu_baseline": {
            "_note": "元数据行不进表",
            "q1": {"app_dau": 1}, "q2": {"app_dau": 2}, "q3": {"app_dau": 3},
        },
        "weekly": {
            (date(2026, 1, 2) + timedelta(days=7 * i)).isoformat():
                {"kefu": {"app_dau": 100 + i}}
            for i in range(5)
        },
    }
    p = tmp_path / "history.json"
    p.write_text(json.dumps(hist), encoding="utf-8")
    labels = [r["label"] for r in confluence_sync._kefu_rows_from_history(p)]
    assert labels == ["Q1周均", "Q2周均", "Q3周均", "0109-0115", "0116-0122", "0123-0129"]


# ── 取数守卫：缺天 / 回流 / 未计入口径 ──────────────────────────────────────

def _live_rows(days: int, per_day: int = 2, offline: int = 0) -> list[list]:
    """造有数「直播逐场」形态的 rows（header + 明细）。"""
    rows = [["预计开播时间", "直播id", "直播状态", "主播uid", "观看人数", "平均观看分钟"]]
    for i in range(days):
        day = f"2026-10-{17 + i:02d}"
        for j in range(per_day):
            rows.append([f"{day} 10:00:00", f"L{i}-{j}", "直播结束", f"U{j}", "100", "10"])
        for k in range(offline):
            rows.append([f"{day} 12:00:00", f"O{i}-{k}", "下线", f"V{k}", "100", "10"])
    return rows


def test_parse_live_daily_average_uses_days_with_data():
    """只有 5 天有数据时，日均按 5 天折算——固定除以 7 会把日均压低三成。"""
    weekly, _ = fetch_weekly_youshu.parse_live(
        _live_rows(5), date(2026, 10, 17), date(2026, 10, 23)
    )
    assert weekly["days_with_data"] == 5
    assert weekly["sessions"] == 2.0      # 2 场/天 × 5 天 ÷ 5
    assert weekly["viewers"] == 200.0     # 200 人/天 × 5 天 ÷ 5


def test_parse_live_reports_offline_sessions_separately():
    """「下线」场次不进指标（口径未变），但数量和观看人数要带回供披露。"""
    weekly, _ = fetch_weekly_youshu.parse_live(
        _live_rows(7, per_day=2, offline=1), date(2026, 10, 17), date(2026, 10, 23)
    )
    assert weekly["sessions"] == 2.0
    assert weekly["viewers"] == 200.0
    assert weekly["offline_sessions"] == 7
    assert weekly["offline_viewers"] == 700


def test_sanity_flags_three_day_zero():
    sensors = {
        "summary": {"community": {"feed_dau": 100, "penetration": 5.0}, "live": {}},
        "daily": {"feed_dau": [100, 0, 0, 0, 100, 100, 100],
                  "exposure_count": [1] * 7},
    }
    fails = gen_weekly_metrics.step8_sanity(sensors, {})
    assert any("连续 3 天为 0" in f for f in fails)


def test_sanity_flags_wow_over_200():
    sensors = {
        "summary": {"community": {"feed_dau": 400, "penetration": 5.0}, "live": {"viewers": 100}},
        "daily": {"feed_dau": [400] * 7, "exposure_count": [1] * 7},
    }
    history = [{"community": {"feed_dau": 100}, "live": {"viewers": 100}}]
    fails = gen_weekly_metrics.step8_sanity(sensors, {"live": {"viewers": 100}}, history)
    assert any("> 200%" in f for f in fails)


def test_sanity_skips_wow_without_history():
    sensors = {
        "summary": {"community": {"feed_dau": 400, "penetration": 5.0}, "live": {"viewers": 100}},
        "daily": {"feed_dau": [400] * 7, "exposure_count": [1] * 7},
    }
    assert gen_weekly_metrics.step8_sanity(sensors, {"live": {"viewers": 100}}) == []


def test_live_md_discloses_offline_and_pull_time(monkeypatch):
    monkeypatch.setattr(gen_weekly_md, "_gen_insight_stubs", lambda *a, **k: "[stub]")
    m = _metrics()
    m["live_data_quality"] = {
        "days_with_data": 7, "days_in_period": 7, "latest_date": "2026-06-19",
        "offline_sessions": 47, "offline_viewers": 1904,
    }
    m["data_pulled_at"] = "2026-06-21 10:30"
    md = gen_weekly_all.gen_live_md("0619", m, [])
    assert "47 场状态为「下线」的直播" in md
    assert "取数时点" in md
    assert "只覆盖 6 天" not in md


def test_readback_problems_flags_missing_title_and_chart(tmp_path):
    (tmp_path / "live-weekly-1106.md").write_text(
        "## 洞察\n\n### 1. 观众跟着主播走，==场次少了==观众没少\n\n- x\n\n## 数据明细\n", encoding="utf-8")
    (tmp_path / "live-trends-1106.png").write_bytes(b"")
    ok_text = "1. 观众跟着主播走，场次少了观众没少\n[图] live-trends-1106.png"
    assert confluence_sync._readback_problems(tmp_path, ok_text) == []
    bad = confluence_sync._readback_problems(tmp_path, "[待补充 x")
    assert len(bad) == 3
