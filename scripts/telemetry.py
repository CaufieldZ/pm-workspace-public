#!/usr/bin/env python3
"""工区遥测分析统一 CLI —— 让 .claude/logs/usage.jsonl 反过来管住规则层。

五个子命令共读同一份事件流，按需运行，不进任何注入：

    gate-health     gate 名册健康度（死 gate / 死豁免红灯 + 零触发 / skip 失衡黄灯）
    funnel          闸门漏斗（block→resolved 转化率 / 会话维度 / 慢闸）
    terms           词表命中率（死词 / 漏收 / 高频，带样本量门槛）
    term-inventory  词表成员快照（JSON / --flat），terms 的输入
    learned         LEARNED.md 教训→规则转化视图

用法：
    python3 scripts/telemetry.py gate-health [--strict] [--days 30]
    python3 scripts/telemetry.py funnel [--days 7] [--gate <名>]
    python3 scripts/telemetry.py terms [--days 90] [--gate <名>] [--min-scans N]
    python3 scripts/telemetry.py term-inventory [--flat]
    python3 scripts/telemetry.py learned [--learned <path>]

前置：无 .env / 凭证依赖，纯本地扫描（--help 本身不需要日志存在）。
    输入 = .claude/logs/usage.jsonl 遥测（缺失时 gate-health skip、其余报空结果）
    + gate 注册表（.claude/hooks/*.sh · .githooks/ · scripts/*.sh）
    + scripts/dashboard.py 的 GHOST_GATES + scripts/lib/ 词表本体 + LEARNED.md。
输出形态：全部 stdout 报告，不写文件（term-inventory 出 JSON / TSV）。
退出码：
    0 — clean / 只有黄灯 / 分析类报告
    2 — gate-health --strict 且有红灯（死 gate / 死豁免）
    1 — learned --learned 指向的文件不存在
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from dashboard import GHOST_GATES  # noqa: E402
from gen_hooks_readme import HOOK_DIR, SKIP_PREFIXES, gates_in, hook_gates  # noqa: E402
from lib.banned_terms import (  # noqa: E402
    AI_FILLER_OPENINGS,
    AI_SLOP_TAILS,
    AI_SLOP_WARN,
)
from lib.repo import find_root  # noqa: E402
from lib.ui_jargon import (  # noqa: E402
    ANIMATION_WORDS,
    COMPONENT_WORDS,
    DESIGN_SYSTEM_WORDS,
    INTERACTION_WORDS,
    LAYOUT_WORDS,
    VISUAL_DETAIL_WORDS,
)

LOG_FILE = ROOT / ".claude" / "logs" / "usage.jsonl"
TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ)


# ═══════════ 共用：事件流读取 ═══════════

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


# ═══════════ 词表清单（term-inventory）═══════════

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


def _inventory() -> dict[str, set[str]]:
    """词表成员快照。合并前走子进程调独立脚本，现同进程直接取。"""
    return {k: set(v) for k, v in inventory().items()}


# ═══════════ 词表命中率（terms）═══════════

# gate → 该 gate 命中词对应的 inventory 词表类别。
# 一个 gate 可映射多个词表（context-static-lint 同时扫 ui_jargon + tech_jargon）。
GATE_INVENTORY: dict[str, list[str]] = {
    "plain-language-gate": ["banned"],
    "context-static-lint": ["ui_jargon", "tech_jargon"],
}

# 死词判定的最小扫描样本量：该 gate 累计「带埋点的扫描」< 此值时，
# 0 命中只是「没机会命中」，结论不可信，降级 observe 不报删。
MIN_SCANS_DEFAULT = 50


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


# ═══════════ LEARNED.md 转化视图（learned）═══════════

LEARNED = ROOT / "LEARNED.md"

# 规则文件目录（grep 覆盖判断的目标）
RULE_DIRS = [
    ROOT / "CLAUDE.md",
    ROOT / ".claude" / "runbooks",
    ROOT / ".claude" / "skills",
    ROOT / "scripts" / "SCRIPTS_WRITING.md",
    ROOT / ".claude" / "hooks" / "HOOK_WRITING.md",
]

ENTRY_RE = re.compile(r'^- \*\*\[(\d{4}-\d{2}-\d{2})\]\*\* (.+)', re.MULTILINE)


def parse_entries(text: str) -> list[tuple[str, str]]:
    """返回 [(date, rule_text), ...]。"""
    return [(m.group(1), m.group(2).strip()) for m in ENTRY_RE.finditer(text)]


def extract_keywords(rule: str, min_len: int = 4) -> list[str]:
    """从规则文本提取候选关键词（≥4 字的中文 / 英文 token）。"""
    tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_-]{3,}|[一-鿿]{2,}', rule)
    return [t for t in tokens if len(t) >= min_len][:5]


def check_covered(rule: str, rule_files: list[Path]) -> tuple[bool, str]:
    """检查规则文本是否被现行规则文件覆盖（关键词 grep 命中 ≥ 2 个）。"""
    keywords = extract_keywords(rule)
    if not keywords:
        return False, ""
    for f in rule_files:
        if not f.exists():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits = sum(1 for kw in keywords if kw in text)
        if hits >= 2:
            return True, str(f.relative_to(ROOT))
    return False, ""


def find_duplicates(entries: list[tuple[str, str]]) -> dict[str, list[str]]:
    """检测重复主题（相同关键词集 ≥ 2 条）。"""
    by_keywords: dict[tuple[str, ...], list[str]] = {}
    for date, rule in entries:
        kws = tuple(sorted(extract_keywords(rule)[:3]))
        by_keywords.setdefault(kws, []).append(date)
    return {f"{'/'.join(k)}": dates for k, dates in by_keywords.items() if len(dates) >= 2}


# ═══════════ gate 名册健康度（gate-health）═══════════

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


# ═══════════ 子命令 handler ═══════════

def cmd_funnel(args) -> int:
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

    return 0


def cmd_terms(args) -> int:
    events = load_events(args.days)
    inv = _inventory()

    gates = [args.gate] if args.gate else list(GATE_INVENTORY)
    print(f"# 词表命中率分析 · 过去 {args.days} 天 · 死词门槛 ≥ {args.min_scans} 次扫描")
    for gate in gates:
        _analyze_gate(gate, events, inv, args.min_scans)
    return 0


def cmd_term_inventory(args) -> int:
    inv = inventory()
    if args.flat:
        for cat, words in inv.items():
            for w in words:
                print(f"{cat}\t{w}")
    else:
        print(json.dumps(inv, ensure_ascii=False, indent=2))
    return 0


def cmd_learned(args) -> int:
    if not args.learned.is_file():
        print(f"❌ {args.learned} 不存在", file=sys.stderr)
        return 1

    text = args.learned.read_text(encoding="utf-8", errors="replace")
    entries = parse_entries(text)

    # 收集规则文件
    rule_files = []
    for rd in RULE_DIRS:
        if rd.is_file():
            rule_files.append(rd)
        elif rd.is_dir():
            rule_files.extend(rd.rglob("*.md"))
        elif rd.is_dir():
            rule_files.extend(rd.rglob("*.sh"))

    covered = 0
    pending = []
    for date, rule in entries:
        is_covered, where = check_covered(rule, rule_files)
        if is_covered:
            covered += 1
        else:
            pending.append((date, rule[:80]))

    duplicates = find_duplicates(entries)

    print("=== LEARNED.md 统计 ===")
    print(f"总条目: {len(entries)}")
    print(f"已覆盖（≥2 关键词命中规则文件）: {covered}")
    print(f"待归位（未命中 / 纯临时教训）: {len(pending)}")
    print(f"重复主题组: {len(duplicates)}")
    if duplicates:
        print()
        for kw, dates in duplicates.items():
            print(f"  ⚠ {kw}: {', '.join(dates)}")
    if pending:
        print()
        print("待归位条目:")
        for date, rule in pending[:10]:
            print(f"  [{date}] {rule}...")
    return 0


def cmd_gate_health(args) -> int:
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


# ═══════════ CLI ═══════════

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    gh = sub.add_parser("gate-health", help="gate 名册健康度（死 gate / 死豁免 / 零触发 / skip 失衡）")
    gh.add_argument("--strict", action="store_true", help="有红灯时 exit 2（默认关，warn 不阻断）")
    gh.add_argument("--days", type=int, default=WINDOW_DAYS,
                    help=f"黄灯观察窗口天数（默认 {WINDOW_DAYS}）")

    fn = sub.add_parser("funnel", help="闸门漏斗（block→resolved 转化率 / 会话维度 / 慢闸）")
    fn.add_argument("--days", type=int, default=30, help="回看天数（默认 30）")
    fn.add_argument("--gate", default=None, help="只看单个 gate 名")

    tm = sub.add_parser("terms", help="词表命中率（死词 / 漏收 / 高频）")
    tm.add_argument("--days", type=int, default=30, help="回看天数（默认 30）")
    tm.add_argument("--gate", default=None,
                    help="只分析某个 gate（取值：GATE_INVENTORY 键，如 plain-language-gate / "
                         "context-static-lint；默认全跑）")
    tm.add_argument("--min-scans", type=int, default=MIN_SCANS_DEFAULT,
                    help=f"死词判定最小扫描样本量（默认 {MIN_SCANS_DEFAULT}，不足则降级 observe）")

    ti = sub.add_parser("term-inventory", help="词表成员快照（terms 的输入）")
    ti.add_argument("--flat", action="store_true", help="扁平 cat<TAB>word 输出（diff 友好）")

    ln = sub.add_parser("learned", help="LEARNED.md 教训→规则转化视图")
    ln.add_argument("--learned", type=Path, default=LEARNED,
                    help="LEARNED.md 路径（默认 仓库根 LEARNED.md）")

    args = ap.parse_args()
    return {
        "gate-health": cmd_gate_health,
        "funnel": cmd_funnel,
        "terms": cmd_terms,
        "term-inventory": cmd_term_inventory,
        "learned": cmd_learned,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
