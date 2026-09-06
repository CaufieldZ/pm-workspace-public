"""审核语料「命中内容」列的拆词口径（多词合写拆分）。

调用方：
- projects/moderation/scripts/check_against_corpus.py
- projects/moderation/scripts/audit_existing_keywords.py
"""
import re

_SPLIT_RE = re.compile(r"[,，、]")


def split_hit_keywords(raw: str) -> list[str]:
    """命中内容可多词合写（「币安， Binance」「Kraken, Coinbase」「X、Bit」），
    按 , ， 、 三种分隔符拆分，去空白项。"""
    if not raw:
        return []
    return [w.strip() for w in _SPLIT_RE.split(raw) if w.strip()]
