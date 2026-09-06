#!/usr/bin/env python3
"""词表命中率分析 — 反查 usage.jsonl 的 hits_words，报死词 / 漏收 / 高频。

复用 analyze_gate_funnel.load_events 读扁平事件流。回答三件 dashboard 答不了的事：

  1. 死词候选：词表成员（dump_term_inventory）− 近 N 天命中词 = 长期 0 命中，该删
     （0 命中的规则是维护负担不是价值，HOOK_WRITING §四 同款纪律）。
  2. 漏收 / pattern 派生：命中词 − 词表成员 = 命中了但不在离散词表。
  3. 高频命中 TOP：哪个词最常命中（规则是否过严 / 该降级 warn 参考）。

死词结论带样本量门槛：分母是该 gate 的「扫描次数」（clean + warn + block 事件总数），
不是「命中事件数」。扫描次数 < MIN_SCANS 时，0 命中词只是「没机会命中」，不等于死词，
结论降级为「样本不足·observe」不报删，免得照假数据真删词。

gate → 词表映射（GATE_INVENTORY）：
  - plain-language-gate → banned
  - context-static-lint → ui_jargon + tech_jargon
两个通道都已埋 hits_words。--gate 不传则全跑。

按需运行，不进任何注入。埋点上线前的历史事件无 hits_words，自动排除。

Usage:
    python3 scripts/analyze_term_hits.py [--days 30] [--gate <name>] [--min-scans 50]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_gate_funnel import load_events  # noqa: E402

# gate → 该 gate 命中词对应的 inventory 词表类别。
# 一个 gate 可映射多个词表（context-static-lint 同时扫 ui_jargon + tech_jargon）。
GATE_INVENTORY: dict[str, list[str]] = {
    "plain-language-gate": ["banned"],
    "context-static-lint": ["ui_jargon", "tech_jargon"],
}

# 死词判定的最小扫描样本量：该 gate 累计「带埋点的扫描」< 此值时，
# 0 命中只是「没机会命中」，结论不可信，降级 observe 不报删。
MIN_SCANS_DEFAULT = 50


def _inventory() -> dict[str, set[str]]:
    """调 dump_term_inventory.py 取词表成员快照（子进程，隔离 import 副作用）。"""
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "dump_term_inventory.py")],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    try:
        raw = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}
    return {k: set(v) for k, v in raw.items()}


def _analyze_gate(gate: str, events: list, inv: dict[str, set[str]],
                  min_scans: int) -> None:
    """单 gate 分析：埋点扫描次数（分母）+ 命中词反查 + 样本量门槛下的死词结论。

    分母只数「带 hits_words 字段」的事件 —— 该字段是埋点上线后才有的，
    零命中也 emit []（标记「扫了 + 有埋点」）。埋点上线前的历史扫描无此字段，
    自动排除，不被误算进死词分母（否则历史扫描会把全词表诬陷成「达标死词」）。
    """
    n_scans = 0           # 带埋点的扫描次数（分母）：含 hits_words 字段即算，[] 也算
    n_events_with_hits = 0
    hit_words: Counter[str] = Counter()
    for e in events:
        if e.get("name") != gate:
            continue
        words = e.get("hits_words")
        if not isinstance(words, list):
            continue  # 无 hits_words 字段 = 埋点前历史事件，不计入分母
        n_scans += 1
        if words:
            n_events_with_hits += 1
            for w in words:
                if isinstance(w, str):
                    hit_words[w] += 1

    hit_set = set(hit_words)
    cats = GATE_INVENTORY.get(gate, [])
    members: set[str] = set()
    for cat in cats:
        members |= inv.get(cat, set())

    print(f"\n{'=' * 60}")
    print(f"## gate={gate} · 词表 {'+'.join(cats) or '（无映射）'}")
    print(f"扫描次数：{n_scans} · 命中事件：{n_events_with_hits} · distinct 命中词：{len(hit_set)}")

    enough = n_scans >= min_scans
    if not members:
        print("  （该 gate 无离散词表映射，跳过死词分析）")
        return

    if not enough:
        # 样本不足：不报「该删」，只列「待观察」清单 + 明确标注不可信
        observe = sorted(members - hit_set)
        print(f"\n### ⏳ 样本不足 · observe（扫描 {n_scans} < {min_scans}，死词结论不可信）")
        print(f"   0 命中词 {len(observe)}/{len(members)} 个 —— 可能只是「还没机会命中」，先别删。")
        print(f"   攒够 {min_scans} 次扫描后再跑（建议每周看一次扫描计数增长）。")
    else:
        dead = sorted(members - hit_set)
        if dead:
            print(f"\n### 🪦 死词候选（{len(dead)}/{len(members)} 长期 0 命中，样本量达标，可删）\n")
            print("  " + " / ".join(dead))
        else:
            print("\n### ✅ 无死词，全部词近期有命中")

    # 漏收 / pattern 派生：命中但不在离散词表（与样本量无关，始终有参考价值）
    if hit_set:
        orphan = sorted(hit_set - members)
        if orphan:
            print(f"\n### 漏收 / pattern 派生（{len(orphan)}）：命中但不在离散词表\n")
            print("  " + " / ".join(orphan))

    # 高频命中 TOP（规则是否过严参考）
    if hit_words:
        print("\n### 高频命中 TOP 20（规则是否过严 / 该降级 warn 参考）\n")
        for w, c in hit_words.most_common(20):
            print(f"  {c:>4}  {w}")


def main() -> int:
    ap = argparse.ArgumentParser(description="词表命中率分析（死词 / 漏收 / 高频）")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--gate", default=None,
                    help="只分析某个 gate（默认全跑 GATE_INVENTORY 里的所有 gate）")
    ap.add_argument("--min-scans", type=int, default=MIN_SCANS_DEFAULT,
                    help=f"死词判定最小扫描样本量（默认 {MIN_SCANS_DEFAULT}，不足则降级 observe）")
    args = ap.parse_args()

    events = load_events(args.days)
    inv = _inventory()

    gates = [args.gate] if args.gate else list(GATE_INVENTORY)
    print(f"# 词表命中率分析 · 过去 {args.days} 天 · 死词门槛 ≥ {args.min_scans} 次扫描")
    for gate in gates:
        _analyze_gate(gate, events, inv, args.min_scans)
    return 0


if __name__ == "__main__":
    sys.exit(main())
