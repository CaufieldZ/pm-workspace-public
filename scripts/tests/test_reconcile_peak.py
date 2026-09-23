"""reconcile_peak 纯函数回归：成交价反推 / 规则判定 / 判读分级 / 对账范围收敛。

只测纯函数（吃结构 → 返回结构），不触网络——取数在 fetch_day 的 I/O 层。
锁定两件事：① 反推要用该条自带的倍率把输出 / 缓存折回输入当量；
② 分不出档的小时不能进判据（否则「个别条目看不懂」会被说成「站点没在收高峰价」）。
"""
import datetime
import json

import pytest

import reconcile_peak as r


def _entry(prompt=0, completion=0, quota=0, model_ratio=0.5, model="deepseek-flash",
           cache=0, cache_ratio=0.02, cache_creation=0, cache_creation_ratio=1.25,
           completion_ratio=4, created_at=None):
    other = {"model_ratio": model_ratio, "completion_ratio": completion_ratio,
             "cache_ratio": cache_ratio, "cache_creation_ratio": cache_creation_ratio,
             "cache_tokens": cache, "cache_creation_tokens": cache_creation}
    return {"id": 1, "model_name": model, "quota": quota, "prompt_tokens": prompt,
            "completion_tokens": completion, "other": json.dumps(other),
            "created_at": created_at}


# ── realized_price ────────────────────────────────────────────────────

def test_realized_price_plain_input():
    """1M 输入 token、quota 400000 → ¥0.80/1M。"""
    assert r.realized_price(_entry(prompt=1000000, quota=400000)) == 0.8


def test_realized_price_weights_output_and_cache():
    """输出按 completion_ratio 折回输入当量：4×completion + 0.02×cache。"""
    e = _entry(prompt=0, completion=250000, cache=5000000, quota=400000)
    # 当量 = 250000×4 + 5000000×0.02 = 1,100,000 → 400000/500000/(1.1) = 0.7272…
    assert r.realized_price(e) == pytest.approx(0.7272727272727273)


def test_realized_price_zero_tokens_is_none():
    assert r.realized_price(_entry(prompt=0, completion=0, quota=999)) is None


def test_realized_price_zero_quota_is_none():
    assert r.realized_price(_entry(prompt=1000000, quota=0)) is None


def test_realized_price_non_token_pricing_is_none():
    """按张计价的形态（model_ratio ≤ 0）不参与对账。"""
    assert r.realized_price(_entry(prompt=1000000, quota=400000, model_ratio=-1)) is None
    assert r.realized_price(_entry(prompt=1000000, quota=400000, model_ratio=0)) is None


def test_realized_price_bad_other_is_none():
    e = _entry(prompt=1000000, quota=400000)
    e["other"] = "{not json"
    assert r.realized_price(e) is None


# ── expected_peak ─────────────────────────────────────────────────────

def test_expected_peak_weekday_off_holiday_is_peak():
    assert r.expected_peak(datetime.date(2026, 9, 15), set()) is True      # 周二


def test_expected_peak_weekend_is_valley():
    assert r.expected_peak(datetime.date(2026, 9, 19), set()) is False     # 周六
    assert r.expected_peak(datetime.date(2026, 9, 20), set()) is False     # 周日（调休补班日）


def test_expected_peak_holiday_weekday_is_valley():
    hol = {"2026-09-25"}
    assert r.expected_peak(datetime.date(2026, 9, 25), hol) is False       # 中秋（周五）


# ── judge ─────────────────────────────────────────────────────────────

def _hours(mapping):
    import collections
    return {h: collections.Counter({p: n}) for h, (p, n) in mapping.items()}


def test_judge_all_peak_window_doubled():
    per_hour = _hours({0: (0.8, 10), 11: (1.6, 5), 17: (1.6, 7)})
    assert r.judge(per_hour, 2)[0] == "peak"


def test_judge_all_peak_window_flat():
    per_hour = _hours({0: (0.8, 10), 11: (0.8, 5), 15: (0.8, 7)})
    assert r.judge(per_hour, 2)[0] == "valley"


def test_judge_mixed_peak_window():
    per_hour = _hours({0: (0.8, 10), 11: (1.6, 5), 15: (0.8, 7)})
    assert r.judge(per_hour, 2)[0] == "mixed"


def test_judge_outliers_do_not_vote():
    """×31 这类分不出档的小时不进判据 —— 不能因为有个看不懂的条目就说「没在收高峰价」。"""
    per_hour = _hours({0: (0.8, 10), 11: (1.6, 5), 15: (25.0, 1)})
    verdict, lines = r.judge(per_hour, 2)
    assert verdict == "peak"
    assert any("不在本规则内" in x for x in lines)


def test_judge_only_outliers_is_nodecision():
    per_hour = _hours({0: (0.8, 10), 11: (25.0, 1)})
    assert r.judge(per_hour, 2)[0] == "nodecision"


def test_judge_no_off_hour_data_is_nodecision():
    """没有基准价（全在高峰窗）→ 判据不足，不硬判。"""
    assert r.judge(_hours({11: (1.6, 5)}), 2)[0] == "nodecision"


def test_judge_no_peak_window_data_is_nodecision():
    assert r.judge(_hours({0: (0.8, 10), 22: (0.8, 3)}), 2)[0] == "nodecision"


# ── summarize ─────────────────────────────────────────────────────────

def _ts(hour, day=15):
    return int(datetime.datetime(2026, 9, day, hour, tzinfo=r.SH).timestamp())


def test_summarize_buckets_by_hour_and_filters_prefix():
    """前缀过滤是对账范围收敛的闸：按张计价的图像类不能被算进判读。"""
    entries = [
        _entry(prompt=1000000, quota=400000, created_at=_ts(10)),
        _entry(prompt=1000000, quota=400000, created_at=_ts(22)),
        _entry(prompt=1000000, quota=400000, model="gpt-image-2.5", created_at=_ts(10)),
    ]
    out = r.summarize(entries, ["deepseek-"], 500000.0)
    assert set(out) == {10, 22}
    assert out[10][0.8] == 1          # 图像类那条没混进来
    assert out[22][0.8] == 1


def test_summarize_empty_prefixes_keeps_all():
    entries = [_entry(prompt=1000000, quota=400000, model="whatever-x", created_at=_ts(10))]
    assert set(r.summarize(entries, [], 500000.0)) == {10}


def test_summarize_skips_unpriceable_and_untimed():
    entries = [
        _entry(prompt=0, completion=0, quota=999, created_at=_ts(10)),               # 无 token
        _entry(prompt=1000000, quota=400000, model_ratio=-1, created_at=_ts(11)),    # 按张计价
        _entry(prompt=1000000, quota=400000, created_at=None),                       # 无时间戳
    ]
    assert not r.summarize(entries, ["deepseek-"], 500000.0)


def test_summarize_honours_per_unit():
    """配额单位走 provider 配置 —— 写死第二份会让印刷价与账单对不上。"""
    e = [_entry(prompt=1000000, quota=200000, created_at=_ts(10))]
    assert r.summarize(e, ["deepseek-"], 250000.0)[10][0.8] == 1


# ── discriminating_power / mismatch_hint ──────────────────────────────

def test_power_peak_day_is_baseline():
    assert "基线" in r.discriminating_power(datetime.date(2026, 9, 15), True)


def test_power_holiday_on_weekday_is_the_only_holiday_probe():
    """放假日落在工作日 = 按周几规则本该 ×2 却该是低谷 —— 唯一能验节假日豁免的日子。"""
    p = r.discriminating_power(datetime.date(2026, 9, 25), False)      # 中秋周五
    assert "节假日豁免" in p


def test_power_weekend_mentions_makeup_case():
    p = r.discriminating_power(datetime.date(2026, 9, 20), False)      # 周日
    assert "周末豁免" in p and "补班" in p


def test_hint_makeup_weekend_points_at_workday_calendar():
    h = r.mismatch_hint(datetime.date(2026, 9, 20), False, 2)          # 周日
    assert "国务院日历" in h and "工作日历" in h


def test_hint_holiday_on_weekday_offers_both_fixes():
    """整段不豁免 vs 只认法定日 —— 两种修法不同，提示里必须都给出。"""
    h = r.mismatch_hint(datetime.date(2026, 9, 25), False, 2)          # 周五
    assert "holidays_mode" in h and "法定日" in h


def test_hint_expected_peak_but_flat_mentions_peak_active():
    h = r.mismatch_hint(datetime.date(2026, 9, 15), True, 2)
    assert "peak_active" in h


# ── channel_prefixes ──────────────────────────────────────────────────

def test_channel_prefixes_scoped_to_provider():
    cfg = {"channels": [
        {"provider": "p1", "rates_off_peak": {"deepseek-flash": {}, "deepseek-v4-pro": {}}},
        {"provider": "p2", "rates_off_peak": {"other-model": {}}},
        {"provider": "p1", "models": ["claude"], "rates_off_peak": {}},
    ]}
    assert r.channel_prefixes(cfg, "p1") == ["claude", "deepseek-flash", "deepseek-v4-pro"]
    assert r.channel_prefixes(cfg, "p3") == []


def test_channel_prefixes_tolerates_junk():
    assert r.channel_prefixes({"channels": [None, "x", {"provider": "p"}]}, "p") == []
