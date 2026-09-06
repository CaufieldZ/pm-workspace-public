"""gen_weekly_all.step_path 单元测试。

锁回归：step_path 返回路径落在系统临时目录（tempfile.gettempdir()），
不硬编码 /tmp —— Windows 原生 Python 不映射 /tmp，Path("/tmp/x") 落到 C:\tmp 失败。
"""

import sys
import tempfile
from pathlib import Path

# gen_weekly_all 是 data-report skill 的脚本（不在 scripts/ 根），显式加路径以 import
_SKILL_SCRIPTS = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "data-report" / "scripts"
sys.path.insert(0, str(_SKILL_SCRIPTS))

import gen_weekly_all  # noqa: E402
import gen_weekly_md  # noqa: E402


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
}
_COMMUNITY_ROW_LABELS = [
    "Feed DAU", "Feed 渗透率", "人均停留时长", "次日复访率", "Feed 曝光量",
    "Feed PCTR", "Feed UCTR", "点赞渗透率", "评论渗透率",
    "发帖渗透率", "发帖量",
    # 帖内交易卡带单：逐环节各一行，率行在其 UV 行之前（止于面板，提交 / 成交埋点未注册）
    "曝光 UV", "点击率", "点击 UV", "进面板率", "面板 UV", "整体转化率",
]
_LIVE_ROW_LABELS = [
    # 渗透两行只在本地 md，不进 LIVE_ROWS_SPEC / 不上 Confluence
    "直播渗透率", "App 观众端 UV",
    "日均直播场次", "活跃主播数", "TRTC 主播覆盖率",
    "日均观看人数", "平均观看时长", "互动率", "单主播日均观看人数",
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
    """带 summary.business 的神策取数输出（fetch_weekly_sensors 扩展后的形态）。"""
    return {"summary": {
        "community": {"feed_dau": 11456, "penetration": 8.3, "retention": 26.4,
                      "exposure_count": 102191, "like_rate": 1.3, "comment_rate": 1.9,
                      "share_rate": 0.6, "post_rate": 1.5},
        "live": {"penetration": 2.4, "watch_uv_app": 3338},
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
                                "latest_date": "2026-06-19"}},
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
