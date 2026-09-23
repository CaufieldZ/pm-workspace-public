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


def test_cross_row_derivation_passes():
    """同样两个数，做成跨行比值就不算复读——这正是该写的那句。"""
    assert _kinds(_doc(
        "- 上麦观众人均在麦 42 分钟，是普通观众平均观看时长 10.2 分钟的 4 倍"
    )) == []


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
