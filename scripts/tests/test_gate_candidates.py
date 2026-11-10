"""projects/moderation/scripts 挖掘与准入测试：对比挖掘 / 刷屏 / 准入判定。"""

import sys
from pathlib import Path

MOD = str(Path(__file__).resolve().parents[2] / "projects/moderation/scripts")
if MOD not in sys.path:
    sys.path.insert(0, MOD)

import gate_candidates  # noqa: E402
import mine_quality_leaks as mq  # noqa: E402


def rec(text, value=1.0, count=1, scene="IM"):
    return {"text": text, "value": value, "count": count, "scene": scene,
            "harm": {"divert": 0.9, "scam": 0.1, "solicit": 0.1, "abuse": 0.0}}


def test_contrastive_mining_keeps_leak_phrase_not_clean_words():
    pos_texts = ["需要的口口我，今天行情", "需要的口口我 明天再看", "口口我，有福利",
                 "今天行情不错 需要的口口我"]
    neg_texts = ["今天行情不错", "明天再看看", "有福利活动吗"]
    pos = [(mq.view(t), rec(t)) for t in pos_texts]
    neg = [(mq.view(t), rec(t)) for t in neg_texts]
    rows, _ = mq.mine_ngrams(pos, neg, [], min_df=2)
    words = {r["keyword"] for r in rows}
    assert "口口我" in words
    assert not words & {"今天行情", "明天再看", "有福利"}


def test_platform_boilerplate_is_stripped():
    text = "看涨 🎃 Platform C 万圣惊魂夜 · 200USDT 瓜分令 发帖赚佣金"
    assert "瓜分令" not in mq.view(text)
    assert "发帖赚佣金" not in mq.view(text)


def test_entities_skip_benign_domains_and_need_impact():
    pos = [(mq.view(t), rec(t, count=2)) for t in
           ["钱包 0x" + "a" * 40, "看 https://www.cnbc.com/x", "加 qq 3504741401"]]
    rows = mq.mine_entities(pos, ["正常内容"])
    found = {(r["source"], r["keyword"]) for r in rows}
    assert ("实体-钱包", "0x" + "a" * 40) in found
    assert ("实体-号码", "3504741401") in found
    assert not any(k == "cnbc.com" for _, k in found)


def test_gate_verdict_direct_and_review_layers():
    v = gate_candidates.verdict
    stats = {"hits": 5, "judged": 5, "harmful": 5, "clean": 0, "clean_valuable": 0}
    assert v({"layer": "P0a", "pos_df": 4}, stats)[0] == "pass"
    stats_thin = {"hits": 0, "judged": 0, "harmful": 0, "clean": 0, "clean_valuable": 0}
    assert v({"layer": "P0a", "pos_df": 2}, stats_thin)[0] == "review"
    stats_bad = {"hits": 9, "judged": 9, "harmful": 1, "clean": 6, "clean_valuable": 4}
    assert v({"layer": "P0a", "pos_df": 9}, stats_bad)[0] == "fail"
    stats_p3 = {"hits": 9, "judged": 9, "harmful": 4, "clean": 5, "clean_valuable": 3}
    assert v({"layer": "P3", "pos_df": 9}, stats_p3)[0] == "pass"
    assert v({"layer": "B1", "pos_df": 9}, stats_p3)[0] == "report_only"
