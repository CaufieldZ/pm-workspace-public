"""check_insight_value 单元测试。

锁两条正向内容规则：洞察不许把明细表翻译成中文句子；不许跨口径相除。
周报的其他门全是负向的（只管不许说什么），这两条是唯一管「必须说出什么」的。
"""

import check_insight_value as civ
import pytest

_TABLE = """## 数据明细

| 分类 | 指标 | 本周 | 09.05~09.11 | 08.29~09.04 | 08.22~08.28 | 环比 | 趋势 | Q2 周均 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 观众活跃 | 平均观看时长（分钟） | 10.2 | 9.4 | 9.2 | 7.9 | +8.4% | 连续 9 周走高 | 7.4 |
|   | 举手申请人数 ^6 | 66 | — | — | — | — | — | — |
|   | 上麦人次 ^8 | 14 | — | — | — | — | — | — |
|   | 人均在麦时长（分钟） | 42 | — | — | — | — | — | — |
"""


def _doc(insight: str) -> str:
    return f"# t\n\n## 洞察\n\n{insight}\n\n{_TABLE}"


def _kinds(text: str) -> list[str]:
    return [h[1] for h in civ.check_text(text)]


# ── 规则 1：表格复读 ──────────────────────────────────────────────────────────

def test_flags_pure_table_readout():
    """回归锚：0918 实际写出来的那条，三个数全在表里、零判断。"""
    hits = civ.check_text(_doc("- 连麦上麦 14 人次、8 个场次有人上麦，人均在麦 42 分钟"))
    assert [h[1] for h in hits] == ["表格复读"]
    assert "14" in hits[0][2] and "42" in hits[0][2]


def test_numbers_under_judgment_heading_pass():
    """领导改稿原样：判断标题下，表内数 + 环比做证据是正常写法，不算复读。"""
    assert _kinds(_doc(
        "### 1. 观看时长在涨，上麦观众更愿意留下来\n\n"
        "- 平均观看时长 10.2 分钟，上麦 14 人次\n"
        "- 人均在麦 42 分钟，平均观看时长 10.2 分钟"
    )) == []


def test_heading_listing_numbers_flagged():
    """标题本身在罗列表里的数，没有判断。"""
    hits = civ.check_text(_doc("### 1. 上麦 14 人次、人均在麦 42 分钟\n\n- 主播缺少接麦意愿"))
    assert [h[1] for h in hits] == ["表格复读"]
    assert "标题" in hits[0][2]


def test_bullet_after_numeric_heading_still_flagged():
    """数字标题不构成判断，下面的复读 bullet 照报。"""
    kinds = _kinds(_doc("### 1. 上麦 14 人次、在麦 42 分钟\n\n- 上麦 14 人次、人均在麦 42 分钟"))
    assert kinds == ["表格复读", "表格复读"]


# ── 规则：分析腔 ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("line", [
    "- 上麦观众人均在麦 42 分钟，是普通观众平均观看时长 10.2 分钟的 4 倍",
    "- 曝光降幅是 Feed DAU 的近 5 倍",
    "- 社区 Feed 点击率 0.9%，行情 Feed 10.8%，差 11 倍",
    "- 次日复访率 27.6% 创 4 周新高，掉的是边缘流量",
    "- 两位数 UV 的小盘只读形态",
    "- 点击被更多曝光摊薄",
    "- 只剩季度基线六成",
])
def test_flags_analyst_phrasing(line):
    assert "分析腔" in _kinds(_doc(line))


@pytest.mark.parametrize("line", [
    "### 1. 帖内交易卡进面板率在两个档位之间波动",
    "### 1. 社区流量连续 4 周下降（留存盘没跟着缩）",
    "- 本周对比上周转化率翻倍（主要是上周异常低）",
])
def test_leader_kept_words_pass(line):
    """领导改稿里保留的说法不拦。"""
    assert "分析腔" not in _kinds(_doc(line))


# ── 规则：营销腔 ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("line", [
    "- 本周直播侧表现出极其积极的「去肥增瘦、触底反弹」信号",
    "- 本周直播侧打出了极为漂亮的剪刀差",
    "- 社区生态正从「流量围观」向「深度行情博弈」的质变",
    "- 观看人次从 1.25 万报复性反弹至 1.73 万",
])
def test_flags_marketing_phrasing(line):
    """语料锚：领导 Q2 改稿里整句删掉的原话。"""
    assert "营销腔" in _kinds(_doc(line))


@pytest.mark.parametrize("line", [
    "- 满意度明显拉升：Q1 均值 89.56%，4 月三周均在 92%~94%",
    "- 工单量日均从 872 单增至 969 单，承压明显高于 Q1 基线",
    "- KOL 渠道注册与转化相对稳定，为当前最健康渠道",
    "- 归因优先挂刚上线的项目，其次看行情",
])
def test_marketing_rule_keeps_leader_words(line):
    """明显 / 健康 / 归因 是领导和我方正常用词，不能拦。"""
    assert "营销腔" not in _kinds(_doc(line))


@pytest.mark.parametrize("line", [
    "- 日均观看人数 14 人，相比 Q2 周均 42 下滑 30%",   # 跨期参照
    "- 上麦 14 人次，连续 4 周走低",                    # 跨周形态
    "- 举手 66 人，八周里四周落在这一档",                # 中文数字的跨周形态
])
def test_derivation_words_exempt(line):
    assert _kinds(_doc(line)) == []


def test_single_digit_numbers_ignored():
    """个位数满表都是，算进去会把任意一句话判成复读。"""
    assert _kinds(_doc("- 本周有 1 场活动、2 个入口")) == []


def test_footnote_markers_not_counted_as_data():
    """脚注上标 ^6 / ^8 不是数据——否则洞察里任意一个 6 或 8 都算命中。"""
    assert "6" not in civ.table_numbers(_TABLE)
    assert "8" not in civ.table_numbers(_TABLE)


def test_week_range_header_not_counted():
    """表头是周区间列标题，不是指标值。"""
    assert "09.05" not in civ.table_numbers(_TABLE)


# ── 规则 2：跨口径相除 ────────────────────────────────────────────────────────

def test_flags_cross_caliber_ratio():
    """举手申请人数（行为分析平台周去重人数）÷ 上麦人次（有数人次）= 两个源，不可相除。"""
    hits = civ.check_text(_doc("- 举手申请人数 66 里只有 14 人次真上了麦，转化率 21%"))
    assert "跨口径相除" in [h[1] for h in hits]


def test_same_source_funnel_passes():
    """有数连麦表内部「举手人数 → 连麦人数」同源同口径，BI 自带转化率列，不该拦。

    规则写宽（裸词「举手」÷「上麦」）会把本周最有价值的一条洞察一起挡掉。
    """
    hits = civ.check_text(_doc("- 举手 69 人次、实际上麦 14 人次，举手上麦率 20%"))
    assert "跨口径相除" not in [h[1] for h in hits]


def test_cross_caliber_split_into_two_bullets_passes():
    """各自陈述不相除就放行。"""
    assert "跨口径相除" not in _kinds(_doc("- 举手 66 人\n- 上麦 14 人次"))


def test_flags_expose_over_dau():
    hits = civ.check_text(_doc("- 直播卡曝光 4,856 人，占 Feed DAU 7,368 的 66%"))
    assert "跨口径相除" in [h[1] for h in hits]


# ── 边界 ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "",
    "# 只有洞察\n\n## 洞察\n\n- 上麦 14 人次、人均在麦 42 分钟\n",   # 无明细表
    _TABLE,                                                        # 无洞察
])
def test_non_weekly_report_returns_empty(text):
    assert civ.check_text(text) == []


def test_html_comments_stripped():
    """洞察段的 HTML 注释里有大量数字（趋势检测 / 行情上下文），不该被扫。"""
    doc = _doc("<!-- 通道趋势检测：平均观看时长 10.2，上麦 14 人次，人均在麦 42 -->\n\n- 判断句")
    assert civ.check_text(doc) == []


def test_main_missing_path_is_not_reported_clean(monkeypatch, capsys):
    """路径不存在时不能打 ✅——zsh 不拆分未加引号变量，两个路径会粘成一个不存在的参数。"""
    monkeypatch.setattr(civ.sys, "argv", ["check_insight_value.py", "/nope/a.md /nope/b.md"])
    assert civ.main() == 0
    err = capsys.readouterr().err
    assert "文件不存在" in err and "✅" not in err


@pytest.mark.parametrize("heading", [
    # 领导 1016 终稿句式：表内数 + 表里查不到的 Q 对比
    "### 1. 平均观看时长 10.2 分钟（+8.4%），相比 Q2 提升 38%",
    # 表内数 + 不含数字的判断分句
    "### 1. 上麦 14 人次、人均在麦 42 分钟，主播缺少接麦意愿",
])
def test_heading_with_judgment_may_carry_table_numbers(heading):
    assert _kinds(_doc(heading + "\n\n- 举手申请 66 人")) == []


def test_heading_with_trend_words_counts_as_judgment():
    """「4 周最低」这类跨周形态算判断，标题下的 bullet 不按复读报。"""
    assert _kinds(_doc("### 1. 上麦 14 人次，4 周最低\n\n- 平均观看时长 10.2 分钟，环比 +8.4%")) == []
