"""projects/moderation/scripts/mine_llm_leaks 测试：归一化 / 分层 / 覆盖 / 候选抽取。"""

import sys
from pathlib import Path

MOD = str(Path(__file__).resolve().parents[2] / "projects/moderation/scripts")
if MOD not in sys.path:
    sys.path.insert(0, MOD)

import mine_llm_leaks as mine  # noqa: E402


def test_sepless_keeps_cjk_latin_digits():
    assert mine.sepless("加 我！QQ123") == "加我qq123"
    assert mine.sepless("<p>a b</p>") == "ab"


def test_covered_uses_substring():
    library = [mine.sepless("返费用"), mine.sepless("加助理扣扣")]
    assert mine.covered("需要返费用的加我", library)
    assert mine.covered("加助理扣扣，她给你安装bao", library)
    assert not mine.covered("今天 BTC 怎么看", library)


def test_layer_for():
    assert mine.layer_for("加助理扣扣") == "P0a"
    assert mine.layer_for("试听课") == "P3"
    assert mine.layer_for("开一百一十") == "P3"
    assert mine.layer_for("公🀄豪") == "P4"
    assert mine.layer_for("подпишитесь на прямую") == "foreign"


def test_extract_candidates_counts_and_filters():
    uncovered = [
        {"text": "加助理扣扣，她给你安装bao", "confidence": 0.9},
        {"text": "加助理扣扣，让助力给你发安装包", "confidence": 0.8},
        {"text": "今天 BTC 怎么看", "confidence": 0.9},
    ]
    rows = mine.extract_candidates(uncovered, library=[], min_df=2)
    words = {row["keyword"]: row for row in rows}
    assert "加助理扣扣" in words
    assert words["加助理扣扣"]["df"] == 2
    assert all(row["df"] >= 2 for row in rows)


def test_extract_candidates_respects_library():
    uncovered = [{"text": "加助理扣扣", "confidence": 0.9}] * 2
    rows = mine.extract_candidates(uncovered, library=[mine.sepless("助理扣扣")], min_df=2)
    assert all("助理扣扣" not in row["keyword"] for row in rows)
