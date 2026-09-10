"""banned_terms 回归：AI_SLOP_TAIL_RE 后缀豁免（真相源）防误拦。

防类 1 误拦：「真相源」是工作区 IDENTITY 级术语（single source of truth），
负向断言豁免；单独「真相」仍命中。此豁免逻辑最绕、最易回归。
"""
import pytest
from lib.banned_terms import AI_SLOP_TAIL_RE, AI_SLOP_TAILS


@pytest.mark.parametrize("word", AI_SLOP_TAILS)
def test_tail_blocked(word):
    # 词表里所有词单独出现都应命中（除被后缀豁免改写的）
    assert AI_SLOP_TAIL_RE.search(word) is not None


def test_truth_source_exempt():
    # 「真相源」整体是合法术语 → 不命中
    assert AI_SLOP_TAIL_RE.search("真相源是唯一事实来源") is None
    # 单独「真相」→ 命中
    assert AI_SLOP_TAIL_RE.search("揭示真相") is not None


def test_truth_source_mid_sentence():
    # 句中「真相源」也不误拦
    assert AI_SLOP_TAIL_RE.search("以真相源为准进行对齐") is None
