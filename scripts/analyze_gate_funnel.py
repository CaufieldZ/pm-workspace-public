#!/usr/bin/env python3
"""闸门漏斗分析 — 按 session 把 block 配对 resolved，量化「闸门在帮人还是在烦人」。

读 .claude/logs/usage.jsonl，按 session_id 把扁平事件流串成会话，回答三件
dashboard 答不了的事：

  1. block→resolved 转化率：每条 gate 拦截后，同会话内是否再 clean（=改对放行）。
     高 abandon-rate = 拦了但没帮人改对（文案不清 / 误报 / 规则过严）。
  2. 会话维度真相：distinct session 数（修「session-start triggered 计数虚高」），
     events/session、sessions/day。
  3. 慢闸：dur_ms 聚合，定位多秒级 checker。

按需运行，不进任何注入。历史事件（instrument 之前）无 session_id，自动排除出
会话分析并单独报数。

Usage:
    python3 scripts/analyze_gate_funnel.py [--days 30] [--gate <name>]
"""
import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = ROOT / ".claude" / "logs" / "usage.jsonl"
TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ)


def load_events(days):
    cutoff = NOW - timedelta(days=days)
    out = []
    if not LOG_FILE.exists():
        return out
    with LOG_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if datetime.fromisoformat(e["ts"]) >= cutoff:
                    out.append(e)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    return out


def funnel(events, only_gate=None):
    """每会话内，把同名 gate 的 block 贪心配对其后的 clean = resolved。"""
    # session -> gate -> {"block":[ts...], "clean":[ts...]}
    sess = defaultdict(lambda: defaultdict(lambda: {"block": [], "clean": []}))
    for e in events:
        sid = e.get("session_id")
        if not sid or e.get("type") not in ("hook", "gate"):
            continue
        name = e.get("name", "")
        if only_gate and name != only_gate:
            continue
        act = e.get("action")
        if act in ("block", "clean"):
            sess[sid][name][act].append(e["ts"])

    agg = defaultdict(lambda: {"blocks": 0, "resolved": 0})
    for _sid, gates in sess.items():
        for name, ba in gates.items():
            blocks = sorted(ba["block"])
            cleans = sorted(ba["clean"])
            agg[name]["blocks"] += len(blocks)
            # 贪心：每个 clean 认领它之前最早一个未配对 block
            ci = 0
            for bts in blocks:
                while ci < len(cleans) and cleans[ci] < bts:
                    ci += 1
                if ci < len(cleans):
                    agg[name]["resolved"] += 1
                    ci += 1
    return agg


def slow_gates(events):
    durs = defaultdict(list)
    for e in events:
        d = e.get("dur_ms")
        if isinstance(d, int) and d > 0:
            durs[e.get("name", "")].append(d)
    rows = []
    for name, ds in durs.items():
        rows.append((name, max(ds), sum(ds) // len(ds), len(ds)))
    rows.sort(key=lambda r: -r[1])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--gate", default=None, help="只看单个 gate 名")
    args = ap.parse_args()

    events = load_events(args.days)
    with_sid = [e for e in events if e.get("session_id")]
    without_sid = len(events) - len(with_sid)
    sessions = {e["session_id"] for e in with_sid}

    print(f"# 闸门漏斗分析 · 过去 {args.days} 天")
    print(f"\n事件 {len(events)} 条 · 带 session_id {len(with_sid)} · "
          f"无 session_id（instrument 前历史）{without_sid}")

    # ── 会话维度 ──
    print("\n## 会话维度（distinct session_id）\n")
    print(f"- 活跃会话数：**{len(sessions)}**")
    if sessions:
        per_sess = len(with_sid) / len(sessions)
        print(f"- 平均事件/会话：{per_sess:.0f}")
        days_span = max((NOW - min(datetime.fromisoformat(e["ts"]) for e in with_sid)).days, 1)
        print(f"- 会话/天：{len(sessions) / days_span:.1f}")
        ss = Counter(e["session_id"] for e in with_sid
                     if e.get("name") == "session-start")
        if ss:
            print(f"- session-start triggered {sum(ss.values())} 次 ↔ "
                  f"实际 {len(ss)} 个会话（差值=resume/compact 重触发，非新会话）")

    # ── block→resolved ──
    agg = funnel(with_sid, args.gate)
    print("\n## block → resolved 漏斗（同会话同闸 block 后再 clean = 改对放行）\n")
    if not agg:
        print("_暂无带 session_id 的 block 事件——instrument 上线后累积几天再看_")
    else:
        print("| 闸门 | block | resolved | abandon | 转化率 | 诊断 |")
        print("|------|-------|----------|---------|--------|------|")
        for name in sorted(agg, key=lambda n: -agg[n]["blocks"]):
            b = agg[name]["blocks"]
            r = agg[name]["resolved"]
            ab = b - r
            rate = r / b if b else 0
            if b < 3:
                diag = "样本少"
            elif rate >= 0.7:
                diag = "✅ 有效摩擦"
            elif rate <= 0.3:
                diag = "⚠️ 拦而未帮（查文案/误报/过严）"
            else:
                diag = ""
            print(f"| {name} | {b} | {r} | {ab} | {rate:.0%} | {diag} |")

    # ── 慢闸 ──
    rows = slow_gates(with_sid)
    print("\n## 慢闸（dur_ms · 整秒分辨率）\n")
    if not rows:
        print("_暂无 dur_ms 数据——runner.sh 计时上线后累积_")
    else:
        print("| 闸门 | max(ms) | avg(ms) | 次数 |")
        print("|------|---------|---------|------|")
        for name, mx, av, n in rows[:10]:
            print(f"| {name} | {mx} | {av} | {n} |")


if __name__ == "__main__":
    main()
