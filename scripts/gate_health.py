#!/usr/bin/env python3
"""Gate 遥测健康度 —— 让 usage.jsonl 反过来管住 gate 名册。

56K 行日志一直没有消费者，于是两种腐化都能无声发生：hook 的 .sh 删了、日志里
的名字还在（死 gate），或者退役名册里的键早已没有任何历史事件（死豁免）。两边
都靠人记，人不记就烂在那儿。本脚本把这两种漂移变成可算的红灯。

第一层 · 红灯（机械可判，--strict 拦 commit）：
  死 gate  — 日志里有事件，注册表查无此名，退役名册也没登记。要么补 hook，
             要么登记进 dashboard.py 的 GHOST_GATES 并写明来历。
  死豁免   — GHOST_GATES 里的键在全量日志中 0 事件。豁免存在的唯一理由是
             「过滤历史事件」，没有历史事件就没有存在理由 → 删。

第二层 · 黄灯（只报不拦，季度 rules-review 消费）：
  零触发     — 注册表里的 gate 在观察窗口内一次没响。要么规则已无人违反（可退役），
               要么触发条件写错了（假安全）。
  skip 失衡  — skip/(skip+block) 超阈值且样本足够。门槛定太松，正在被绕。
  无解释 skip — 同一 gate 的 skip 事件 detail 为空超过阈值次数。绕过没留理由。

两个注册表刻意分开，不能混用：
  known（宽）= gate 名 ∪ hook 文件名 stem。只喂死 gate 判定 —— dispatcher 类
              hook 用自己的文件名 emit（post-writeedit-dispatch），不兜住就假红。
  gates（窄）= 真 gate 名。只喂黄灯判定 —— hook 文件名不是 gate，
              拿它算「零触发」会冒出十几条纯噪音。

用法：
    python3 scripts/gate_health.py
    python3 scripts/gate_health.py --strict    # 有红灯 exit 2（pre-commit / audit 类 25 用）
    python3 scripts/gate_health.py --days 30   # 改黄灯观察窗口

退出码：
    0 — clean / 只有黄灯（未传 --strict）
    2 — 传 --strict 且有红灯（死 gate / 死豁免）
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard import GHOST_GATES  # noqa: E402
from gen_hooks_readme import HOOK_DIR, SKIP_PREFIXES, gates_in, hook_gates  # noqa: E402
from lib.repo import find_root  # noqa: E402

TZ = timezone(timedelta(hours=8))

WINDOW_DAYS = 90          # 黄灯观察窗口
SKIP_RATIO = 0.6          # skip/(skip+block) 超此值 = 过松（同 dashboard.py 诊断公式）
SKIP_MIN_SAMPLE = 5       # skip+block 少于此值不下结论
UNEXPLAINED_SKIP_MAX = 3  # 同一 gate 无 detail 的 skip 超此次数才报


def parse_events(text: str) -> list[dict]:
    """usage.jsonl 文本 → hook / gate 事件列表。

    `-shadow` 后缀是影子并跑产物（新旧 hook 对比用），不算数——同 dashboard 口径。
    坏行跳过：日志是追加式的，历史脏行不该让整个检查瘫掉。
    """
    events = []
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if not isinstance(e, dict) or e.get("type") not in ("hook", "gate"):
            continue
        name = e.get("name") or ""
        if not name or name.endswith("-shadow"):
            continue
        events.append(e)
    return events


def analyze(
    events: list[dict],
    gates: set[str],
    known: set[str],
    ghost: set[str],
    now: datetime,
    days: int = WINDOW_DAYS,
) -> dict:
    """五条判定的纯逻辑。events 已过滤，gates/known/ghost 由调用方给，不碰文件系统。"""
    cutoff = now - timedelta(days=days)

    all_names: set[str] = set()
    recent: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    unexplained: dict[str, int] = defaultdict(int)
    for e in events:
        name = e["name"]
        all_names.add(name)
        try:
            ts = datetime.fromisoformat(e.get("ts", ""))
        except ValueError:
            continue
        if ts < cutoff:
            continue
        action = e.get("action", "")
        recent[name][action] += 1
        if action == "skip" and not str(e.get("detail") or "").strip():
            unexplained[name] += 1

    loose = []
    for g in sorted(gates):
        a = recent.get(g, {})
        sample = a.get("skip", 0) + a.get("block", 0)
        if sample >= SKIP_MIN_SAMPLE:
            rate = a.get("skip", 0) / sample
            if rate > SKIP_RATIO:
                loose.append((g, rate, sample))

    return {
        "gates": gates,
        "known": known,
        "events": len(events),
        "days": days,
        "dead_gates": sorted(all_names - known - ghost),
        "dead_exempt": sorted(g for g in ghost if g not in all_names),
        "zero": sorted(g for g in gates if not recent.get(g)),
        "loose": loose,
        "silent": sorted(
            (g, n) for g, n in unexplained.items()
            if n > UNEXPLAINED_SKIP_MAX and g in gates
        ),
    }


def registries(root: Path) -> tuple[set[str], set[str]]:
    """扫仓库拿 (gates, known)：窄集喂黄灯，宽集喂死 gate 红灯。"""
    gates: set[str] = set()
    stems: set[str] = set()
    for f in sorted(HOOK_DIR.glob("*.sh")):
        if f.name.startswith(SKIP_PREFIXES):
            continue
        gates |= set(hook_gates(f))
        stems.add(f.stem)
    for f in [*root.glob(".githooks/**/*.sh"), *root.glob("scripts/*.sh")]:
        gates |= gates_in(f)
    return gates, gates | stems


def has_red(result: dict) -> bool:
    return bool(result["dead_gates"] or result["dead_exempt"])


def report(r: dict) -> None:
    print(f"Gate 健康度 —— 注册表 {len(r['gates'])} 个 gate（宽集 {len(r['known'])}）"
          f"· 日志 {r['events']} 条事件 · 黄灯窗口 {r['days']} 天\n")

    if r["dead_gates"]:
        print(f"🔴 死 gate（{len(r['dead_gates'])}）—— 日志有事件但注册表查无此名：")
        for g in r["dead_gates"]:
            print(f"  · {g}")
        print("  修：hook 还在就查它为何扫不到；已退役则登记进 scripts/dashboard.py "
              "的 GHOST_GATES 并注明来历\n")
    else:
        print("🟢 死 gate：无\n")

    if r["dead_exempt"]:
        print(f"🔴 死豁免（{len(r['dead_exempt'])}）—— GHOST_GATES 登记了但全量日志 0 事件：")
        for g in r["dead_exempt"]:
            print(f"  · {g}")
        print("  修：豁免的存在理由是过滤历史事件，没有历史事件 = 该删了\n")
    else:
        print("🟢 死豁免：无\n")

    if r["zero"]:
        print(f"🟡 零触发（{len(r['zero'])}）—— 近 {r['days']} 天一次没响，"
              "要么规则已无人违反（可退役），要么触发条件写错了（假安全）：")
        for g in r["zero"]:
            print(f"  · {g}")
        print()

    if r["loose"]:
        print(f"🟡 skip 失衡（{len(r['loose'])}）—— 门槛偏松，正在被绕：")
        for g, rate, sample in r["loose"]:
            print(f"  · {g} — skip {rate:.0%}（样本 {sample}）")
        print()

    if r["silent"]:
        print(f"🟡 无解释 skip（{len(r['silent'])}）—— 绕过时没留理由：")
        for g, n in r["silent"]:
            print(f"  · {g} — {n} 次 detail 为空")
        print()

    if not (r["zero"] or r["loose"] or r["silent"]):
        print("🟢 黄灯：无")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="gate 遥测健康度（死 gate / 死豁免 / 零触发 / skip 失衡）"
    )
    ap.add_argument("--strict", action="store_true", help="有红灯时 exit 2")
    ap.add_argument("--days", type=int, default=WINDOW_DAYS,
                    help=f"黄灯观察窗口天数（默认 {WINDOW_DAYS}）")
    args = ap.parse_args()

    root = find_root()
    log = root / ".claude" / "logs" / "usage.jsonl"
    if not log.is_file():
        print("⚠ 无 .claude/logs/usage.jsonl，skip")
        return 0

    gates, known = registries(root)
    events = parse_events(log.read_text(encoding="utf-8", errors="replace"))
    result = analyze(events, gates, known, set(GHOST_GATES), datetime.now(TZ), args.days)
    report(result)
    return 2 if (args.strict and has_red(result)) else 0


if __name__ == "__main__":
    sys.exit(main())
