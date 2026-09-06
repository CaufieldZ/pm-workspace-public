#!/usr/bin/env python3
"""词表成员清单快照 — 扫三类异构词表导出统一 JSON。

供 analyze_term_hits 做死词检测（词表成员 − 近 N 天命中词 = 死词候选）。
只读快照，不动词表本身。

覆盖：
- banned_terms.py 离散词 list（AI_SLOP_TAILS / AI_SLOP_WARN / AI_FILLER_OPENINGS）
  → check_plain_language 消费，死词检测主目标（唯一已埋点 hits_words 的通道）
- ui_jargon.py *_WORDS（COMPONENT / INTERACTION / LAYOUT / DESIGN_SYSTEM / ANIMATION / VISUAL_DETAIL）
  → check_static_chapter 消费（埋点 follow-up 后纳入死词检测）
- tech_jargon/*.txt（infra / livestream / social / trading / web-frontend）
  → business_voice / check_static_chapter 消费（埋点 follow-up）

不收：regex pattern（SEMANTIC_REDUNDANCY_PATTERNS / TRANSLATION_ESE_PATTERNS 等）——
pattern 不是离散词，死词检测对 pattern 无意义。
不收：BUSINESS_EXEMPT_WORDS（豁免词 = 允许用，不该当死词）。

用法：
    python3 scripts/dump_term_inventory.py            # stdout JSON
    python3 scripts/dump_term_inventory.py --flat      # 扁平 cat<TAB>word（diff 友好）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.banned_terms import (  # noqa: E402
    AI_FILLER_OPENINGS,
    AI_SLOP_TAILS,
    AI_SLOP_WARN,
)
from lib.ui_jargon import (  # noqa: E402
    ANIMATION_WORDS,
    COMPONENT_WORDS,
    DESIGN_SYSTEM_WORDS,
    INTERACTION_WORDS,
    LAYOUT_WORDS,
    VISUAL_DETAIL_WORDS,
)


def _banned() -> list[str]:
    return sorted(set(AI_SLOP_TAILS + AI_SLOP_WARN + AI_FILLER_OPENINGS))


def _ui_jargon() -> list[str]:
    return sorted(set(
        COMPONENT_WORDS + INTERACTION_WORDS + LAYOUT_WORDS
        + DESIGN_SYSTEM_WORDS + ANIMATION_WORDS + VISUAL_DETAIL_WORDS
    ))


def _tech_jargon() -> list[str]:
    """读 5 domain txt，剥 # 注释 / 空行（不依赖 tech_jargon 内部缓存 API）。"""
    out: list[str] = []
    for txt in sorted((ROOT / "scripts" / "lib" / "tech_jargon").glob("*.txt")):
        for line in txt.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                out.append(s)
    return sorted(set(out))


def inventory() -> dict[str, list[str]]:
    return {
        "banned": _banned(),
        "ui_jargon": _ui_jargon(),
        "tech_jargon": _tech_jargon(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="词表成员清单快照")
    ap.add_argument("--flat", action="store_true", help="扁平 cat<TAB>word 输出（diff 友好）")
    args = ap.parse_args()
    inv = inventory()
    if args.flat:
        for cat, words in inv.items():
            for w in words:
                print(f"{cat}\t{w}")
    else:
        print(json.dumps(inv, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
