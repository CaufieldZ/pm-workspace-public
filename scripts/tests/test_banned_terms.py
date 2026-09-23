"""banned_terms 回归：AI_SLOP_TAIL_RE 后缀豁免（真相源）防误拦。

防类 1 误拦：「真相源」是工作区 IDENTITY 级术语（single source of truth），
负向断言豁免；单独「真相」仍命中。此豁免逻辑最绕、最易回归。
"""
import pytest
from lib.banned_terms import AI_SLOP_TAIL_RE, AI_SLOP_TAILS, DEFENSIVE_TRIO_RE


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


# ── 防御性三连：真三连命中 / 并列枚举放行 ──────────────────────

@pytest.mark.parametrize("line", [
    "交互大图（IMAP / interaction map）",          # 规则文档规范示例
    "产品需求文档（PRD / product requirements document）",
    "交互大图(IMAP / interaction map)",           # 半角括号
    "交互大图（IMAP ／ interaction map）",         # 全角斜杠
])
def test_trio_blocked(line):
    assert DEFENSIVE_TRIO_RE.search(line) is not None


@pytest.mark.parametrize("line", [
    "全端一致（App / Web / H5）",                          # 首项非全大写
    "抵押币（USDT / BTC / ETH 等）从温钱包充值",            # 次项非全小写
    "其他来源（IM / 搜索 / 分享链接 / 牛人榜）",             # 次项为中文
    "回落（BTC / ETH）",                                  # 全大写缩写对
    "切换事件（from / to）",                               # 首项非全大写
    "正文出现的工具调用名（Read/Write/Bash）",              # 混合大小写枚举
])
def test_trio_enumeration_exempt(line):
    # 并列枚举不是「一个概念的两种叫法」，不得判为防御性三连
    assert DEFENSIVE_TRIO_RE.search(line) is None
