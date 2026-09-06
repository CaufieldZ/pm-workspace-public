#!/usr/bin/env python3
"""Workspace Dashboard — 聚合 .claude/logs/usage.jsonl + projects/ 状态。

Usage:
    python3 scripts/dashboard.py [--days 14]

输出：.claude/workspace-dashboard.md
"""
import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = ROOT / ".claude" / "logs" / "usage.jsonl"
DASHBOARD = ROOT / ".claude" / "workspace-dashboard.md"
PROJECTS_DIR = ROOT / "projects"
SKILLS_DIR = ROOT / ".claude" / "skills"
HUB_DIR = ROOT / "hub"
# 退役 gate 名册：dashboard 不渲染，gate_health.py 当「死 gate 豁免」读。
# 入册资格：该名字在 usage.jsonl 里有历史事件，但注册表（hook .sh / lib / .githooks）
# 里已不存在——即「事件是真的，gate 没了」。每条注明来历。
# 生命周期：gate_health.py 校验每条仍有历史事件；0 事件 = 豁免本身死了，报红逼删。
GHOST_GATES = {
    "version-sync-gate",   # 已退役的骨架版本号同步 gate，留 68 条历史事件
    "dedup-format-test",   # 2026-08-01 log 去重机制的测试残留（/tmp/pmws_dedup_test_key）
}
HUB_SKIP = {"zips", "references", "AI中台-规范及帮助文档"}

TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ)


def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def load_events(days: int):
    if not LOG_FILE.exists():
        return []
    cutoff = NOW - timedelta(days=days)
    events = []
    with LOG_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                ts = parse_ts(e["ts"])
                if ts >= cutoff:
                    events.append(e)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    return events


def count_scenes(scene_list: Path) -> int:
    try:
        text = scene_list.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    ids = set(re.findall(r"\b[A-Z]-\d+[a-z]?\b", text))
    ids |= set(re.findall(r"\bM\d+\b", text))
    return len(ids)


def dir_mtime(parent: Path, extra: list[Path]) -> float:
    """取项目目录关键文件（baseline / scene-list / deliverables）的最大 mtime。"""
    mtimes = [p.stat().st_mtime for p in extra if p.exists()]
    for name in ("scene-list.md", "deliverables"):
        p = parent / name
        if p.exists():
            mtimes.append(p.stat().st_mtime)
    return max(mtimes) if mtimes else parent.stat().st_mtime


def count_deliverables(deliv_dir: Path) -> int:
    if not deliv_dir.exists():
        return 0
    n = 0
    for p in deliv_dir.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".html", ".docx", ".pdf"):
            if "archive" not in p.parts:
                n += 1
    return n


def baseline_blocking(product_line: str) -> str:
    """baseline 项目的「阻塞」= 流程新鲜度第一层 STALE（已上线 delta 未反向合并）。"""
    try:
        out = subprocess.run(
            ["python3", str(ROOT / "scripts" / "check_baseline_fresh.py"), product_line],
            capture_output=True, text=True, timeout=20,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return ""
    if "🔴" in out:
        n = out.count("❌")
        return f"**baseline 未合并**：{n} 个已上线 delta 未反向合并（跑 check_baseline_fresh.py）"
    return ""


def collect_projects():
    if not PROJECTS_DIR.exists():
        return []
    projects = []
    baseline_roots = set()
    # baseline 项目：任意深度的产品线根 / 活动目录有 prd-*-baseline.md
    # （community / livestream / liquidity 在 depth-1；campaign 变体如 growth/queen 在 depth-2）
    for bl in PROJECTS_DIR.glob("**/prd-*-baseline.md"):
        rel = bl.relative_to(PROJECTS_DIR)
        if any(part == "archive" for part in rel.parts):
            continue
        parent = bl.parent
        baseline_roots.add(parent)
        projects.append({
            "path": str(parent.relative_to(PROJECTS_DIR)) + " (baseline)",
            "scene_count": count_scenes(bl),
            "deliv_count": count_deliverables(parent / "deliverables"),
            "mtime": dir_mtime(parent, [bl]),
            "blocking": baseline_blocking(str(parent.relative_to(PROJECTS_DIR))),
            "cold_read": _cold_read_status(parent),
        })
    # EXEMPT 协调容器：有 deliverables 但无 baseline（biweekly 等 truth_source EXEMPT_LINES）
    for dl in PROJECTS_DIR.glob("*/deliverables"):
        parent = dl.parent
        if parent in baseline_roots:
            continue
        rel = parent.relative_to(PROJECTS_DIR)
        if any(part == "archive" for part in rel.parts):
            continue
        scene_list = parent / "scene-list.md"
        projects.append({
            "path": str(rel),
            "scene_count": count_scenes(scene_list) if scene_list.exists() else 0,
            "deliv_count": count_deliverables(dl),
            "mtime": dir_mtime(parent, []),
            "blocking": "",
            "cold_read": _cold_read_status(parent),
        })
    projects.sort(key=lambda p: p["mtime"], reverse=True)
    return projects


def _cold_read_status(parent: Path) -> str:
    """扫 deliverables 下的 cold-read-*.md，返回最近日期或「未跑」。"""
    latest = ""
    for cr in parent.rglob("deliverables/**/cold-read-*.md"):
        if "archive" in str(cr):
            continue
        stem = cr.stem  # cold-read-2026-07-30
        date_part = stem.replace("cold-read-", "")
        if date_part > latest:
            latest = date_part
    if not latest:
        # 也扫项目根（delta 可能落同目录）
        for cr in parent.rglob("cold-read-*.md"):
            if "archive" in str(cr):
                continue
            stem = cr.stem
            date_part = stem.replace("cold-read-", "")
            if date_part > latest:
                latest = date_part
    return f"✅ {latest[5:]}" if latest else "未跑"


def render_projects(projects):
    if not projects:
        return "_无项目_"
    lines = [
        "| 项目 | scene | 已交付 | 冷读 | 最近活动 | 当前阻塞 |",
        "|------|-------|--------|------|----------|----------|",
    ]
    for p in projects:
        age_days = int((NOW.timestamp() - p["mtime"]) / 86400)
        age_str = "今天" if age_days == 0 else f"{age_days}d 前"
        blocking = p["blocking"] or "—"
        lines.append(
            f"| {p['path']} | {p['scene_count']} | {p['deliv_count']} | {p['cold_read']} | {age_str} | {blocking} |"
        )
    return "\n".join(lines)


def render_hub(events, days):
    """AIHUB 包生产线活跃度：hub-* 脚本埋点的 detail 记的是包名，按包聚合。

    回答「哪些包还在维护、哪些已经死了」——长期 0 命中的包该退休。
    """
    if not HUB_DIR.is_dir():
        return "（无 hub/ 目录）"

    touched = Counter()
    last_touch = {}
    for e in events:
        if e.get("type") != "skill" or not str(e.get("name", "")).startswith("hub-"):
            continue
        # detail 可能是 "prd scene-list ..."（repack 批量）或 "hub/prd"（vet 传目录）
        for tok in str(e.get("detail", "")).split():
            pkg = tok.rsplit("/", 1)[-1]
            if not pkg:
                continue
            touched[pkg] += 1
            last_touch[pkg] = e["ts"]  # 事件按时间正序，直接覆盖 → 保留最近一次

    pkgs = sorted(
        d.name for d in HUB_DIR.iterdir()
        if d.is_dir() and d.name not in HUB_SKIP and not d.name.startswith((".", "__"))
    )
    lines = [
        f"| 包 | {days}d 动过 | 最近一次 | 状态 |",
        "|----|-----------|----------|------|",
    ]
    for pkg in sorted(pkgs, key=lambda p: -touched.get(p, 0)):
        n = touched.get(pkg, 0)
        last = last_touch.get(pkg, "—")[:10] if pkg in last_touch else "—"
        status = "🔘 dead" if n == 0 else ("🔥 hot" if n >= 5 else "")
        lines.append(f"| `{pkg}` | {n} | {last} | {status} |")
    return "\n".join(lines)


def render_skills(events, days):
    # 区分 triggered（post-skill-load 监听 Read SKILL.md）vs completed/failed（Step C checker 末尾 trap）
    skill_events = [e for e in events if e.get("type") == "skill"]
    triggered = Counter(e["name"] for e in skill_events if e.get("action") == "triggered")
    completed = Counter(e["name"] for e in skill_events if e.get("action") == "completed")
    failed = Counter(e["name"] for e in skill_events if e.get("action") == "failed")

    last_trigger = {}
    last_complete = {}
    for e in skill_events:
        if e.get("action") == "triggered":
            last_trigger[e["name"]] = e["ts"]  # 正序覆盖 → 最近一次
        elif e.get("action") == "completed":
            last_complete[e["name"]] = e["ts"]

    # 已埋 Step C checker 的 skill 才显示完成率列；其他 skill 显示 — 表示无 checker
    HAS_CHECKER = {"prd", "interaction-map", "prototype", "cross-check", "workspace-audit"}

    all_skills = sorted(
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and d.name != "_shared"
    )
    lines = [
        f"| Skill | {days}d 触发 | 完成 / 失败 | 完成率 | 最近触发 | 最近完成 | 状态 |",
        "|-------|-----------|------------|--------|----------|----------|------|",
    ]
    for skill in sorted(all_skills, key=lambda s: -triggered.get(s, 0)):
        n_trig = triggered.get(skill, 0)
        n_done = completed.get(skill, 0)
        n_fail = failed.get(skill, 0)
        last_t = last_trigger.get(skill, "—")[:10] if skill in last_trigger else "—"
        last_c = last_complete.get(skill, "—")[:10] if skill in last_complete else "—"

        if skill in HAS_CHECKER:
            done_cell = f"{n_done} / {n_fail}"
            total = n_done + n_fail
            rate = f"{n_done * 100 // total}%" if total > 0 else "—"
        else:
            done_cell = "—"
            rate = "—"

        if n_trig >= 10:
            status = "🔥 hot"
        elif n_trig == 0:
            status = "🔘 dead"
        else:
            status = ""

        lines.append(f"| {skill} | {n_trig} | {done_cell} | {rate} | {last_t} | {last_c} | {status} |")
    return "\n".join(lines)


def render_agents(events, days):
    """Sub-agent 调度热度（type=agent）——pre-agent-log.sh 在 Task tool 调用时 emit。

    跟踪 Explore / general-purpose 通用 agent 派发次数 + 最近 description 摘要。
    """
    agent_events = [e for e in events if e.get("type") == "agent"]
    if not agent_events:
        return "_过去 {} 天无 sub-agent 调度记录_".format(days)

    counter = Counter(e["name"] for e in agent_events)
    last_seen = {}
    recent_descs = defaultdict(list)
    for e in agent_events:
        last_seen[e["name"]] = e["ts"]  # 正序覆盖 → 最近一次
        if e.get("detail"):
            recent_descs[e["name"]].append(e["detail"])

    total = sum(counter.values())
    lines = [
        f"| Sub-agent | {days}d 调用 | 占比 | 最近一次 | 最近描述（top 2） |",
        "|-----------|-----------|------|----------|-------------------|",
    ]
    for name, n in counter.most_common():
        pct = f"{n * 100 // total}%"
        last = last_seen.get(name, "—")[:10]
        top_descs = recent_descs[name][:2]
        descs = " / ".join(d[:30] for d in top_descs) if top_descs else "—"
        lines.append(f"| {name} | {n} | {pct} | {last} | {descs} |")
    return "\n".join(lines)


def render_routes(events, days):
    """快捷路由脚本热度（type=route）——CLAUDE.md「快捷路由」表对应脚本调用频次。

    14 天零调用 = 死路由候选，建议从 CLAUDE.md 表里移除。
    """
    route_events = [e for e in events if e.get("type") == "route"]
    counter = Counter(e["name"] for e in route_events)
    last_seen = {}
    for e in route_events:
        last_seen[e["name"]] = e["ts"]  # 正序覆盖 → 最近一次

    # CLAUDE.md 快捷路由表声明的全部脚本 name（埋点 name 与脚本绑定，dashboard 侧固定枚举）
    # 新加快捷路由脚本时同步加进来，否则 dashboard 看不到「未触发 → 🔘 dead」状态
    KNOWN_ROUTES = [
        "pull_meeting_notes", "fetch_confluence", "fetch_figma",
        "doc_to_md", "pack_for_opus", "md_to_confluence", "slack",
        "youshu_cli", "check_cjk_punct",
        "render_scene_list", "fetch_weekly_sensors",
        "sync_growth_demand_pool", "sync_ux_demand_pool",
        "impact-check", "publish", "sync_pools",
        "dashboard",
    ]
    lines = [
        f"| 路由 | {days}d 调用 | 最近一次 | 状态 |",
        "|------|-----------|----------|------|",
    ]
    for name in sorted(KNOWN_ROUTES, key=lambda n: -counter.get(n, 0)):
        n = counter.get(name, 0)
        last = last_seen.get(name, "—")[:10] if name in last_seen else "—"
        if n >= 10:
            status = "🔥 hot"
        elif n == 0:
            status = "🔘 dead"
        else:
            status = ""
        lines.append(f"| {name} | {n} | {last} | {status} |")
    return "\n".join(lines)


def render_hooks(events, days):
    # `-shadow` 后缀：影子并跑机制（HOOK_CHECKER_SHADOW=1 时新 hook 静默 emit `<gate>-shadow`
    # 供日志对比 vs 旧 hook）。不进主表 — 对比走 jq -r '.name' usage.jsonl | sort | uniq -c
    hook_events = [
        e for e in events
        if e.get("type") in ("hook", "gate")
        and e.get("name") not in GHOST_GATES
        and not str(e.get("name", "")).endswith("-shadow")
    ]
    by_name = defaultdict(lambda: defaultdict(int))
    for e in hook_events:
        by_name[e["name"]][e["action"]] += 1

    if not by_name:
        return "_过去 {} 天无 hook 触发_".format(days)

    lines = [
        "| Hook | triggered | warn | block | clean | skip | 诊断 |",
        "|------|-----------|------|-------|-------|------|------|",
    ]
    for name in sorted(by_name.keys()):
        a = by_name[name]
        total = sum(a.values())
        # 诊断优先级：skip 失衡 > warn 噪音 > 真护栏 > 软提示 > 未触发
        # warn-only 是 post 类 hook 的设计（HOOK_WRITING §H 软 warn 永不 block），不是缺陷；
        # 真正该警示的是「高频 warn 无人处理」= 告警疲劳源，与 block 与否无关。
        diag = ""
        if a["skip"] > 0 and a["block"] > 0:
            rate = a["skip"] / (a["skip"] + a["block"])
            if rate > 0.6:
                diag = f"⚠️ 过松 skip {rate:.0%}"
            elif rate < 0.2:
                diag = f"🔒 偏紧 skip {rate:.0%}"
            else:
                diag = f"skip {rate:.0%}"
        elif a["warn"] >= 50:
            diag = f"⚠️ warn 噪音高（{a['warn']}/{days}d，反复警告无人处理）"
        elif a["block"] > 5:
            diag = "🛡 真护栏"
        elif a["warn"] > 0 and a["block"] == 0:
            diag = "💡 软提示（warn-only by design）"
        elif total == 0:
            diag = "🔘 未触发"
        lines.append(
            f"| {name} | {a['triggered']} | {a['warn']} | {a['block']} | {a['clean']} | {a['skip']} | {diag} |"
        )
    return "\n".join(lines)


def render_gate_trend(events, days):
    """按周分桶各 gate 的 block 率（block/(block+clean)），只列有 block 的 gate。"""
    import datetime
    gate_events = [
        e for e in events
        if e.get("type") in ("hook", "gate")
        and e.get("name") not in GHOST_GATES
        and not str(e.get("name", "")).endswith("-shadow")
    ]
    if not gate_events:
        return "_无 gate 事件_"

    # 按周分桶：ts → week_offset (0=最近7天, 1=7-14天前, ...)
    now = NOW.timestamp()
    by_gate_week = defaultdict(lambda: defaultdict(lambda: {"block": 0, "clean": 0}))
    for e in gate_events:
        ts_str = e.get("ts", "")
        try:
            ts = datetime.datetime.fromisoformat(ts_str).timestamp()
        except (ValueError, TypeError):
            continue
        week_offset = int((now - ts) // 86400 // 7)
        if week_offset < 0 or week_offset >= days // 7:
            continue
        action = e.get("action", "")
        if action in ("block", "clean"):
            by_gate_week[e["name"]][week_offset][action] += 1

    # 只列有 block 的 gate
    active_gates = [
        g for g, weeks in by_gate_week.items()
        if any(w["block"] > 0 for w in weeks.values())
    ]
    if not active_gates:
        return "_过去 {} 天无 gate block 事件_".format(days)

    n_weeks = max(days // 7, 1)
    headers = ["Gate"] + [f"W-{i}" if i > 0 else "本周" for i in range(n_weeks - 1, -1, -1)]
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(["------"] * len(headers)) + "|"]
    for name in sorted(active_gates):
        row = [name]
        for w in range(n_weeks - 1, -1, -1):
            stats = by_gate_week[name].get(w, {"block": 0, "clean": 0})
            total = stats["block"] + stats["clean"]
            if total == 0:
                row.append("—")
            else:
                rate = stats["block"] * 100 // total
                row.append(f"{rate}% ({stats['block']}/{total})")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_anomalies(events, projects):
    items = []

    # 长时间不动项目（> 14d）
    stale = [p for p in projects if (NOW.timestamp() - p["mtime"]) > 14 * 86400]
    if stale:
        items.append("**长期未动项目（> 14 天）**：")
        for p in stale[:10]:
            age = int((NOW.timestamp() - p["mtime"]) / 86400)
            items.append(f"- {p['path']} （{age}d 前）")
        items.append("")

    # 反复 warn 同一文件 top 5
    warn_files = Counter()
    for e in events:
        if e.get("action") in ("warn", "block") and e.get("detail"):
            warn_files[e["detail"]] += 1
    repeat_warns = [(f, n) for f, n in warn_files.most_common(5) if n >= 3]
    if repeat_warns:
        items.append("**同一文件反复 warn/block（≥ 3 次）**：")
        for f, n in repeat_warns:
            items.append(f"- {n}× — {f}")
        items.append("")

    # 有 deliverables 无 scene-list（结构缺失）
    missing_scene = [
        p for p in projects
        if p["deliv_count"] > 0 and p["scene_count"] == 0
    ]
    if missing_scene:
        items.append("**有产出物但无 scene-list**：")
        for p in missing_scene[:10]:
            items.append(f"- {p['path']} （{p['deliv_count']} 交付物）")
        items.append("")

    return "\n".join(items) if items else "_无异常_"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    args = parser.parse_args()

    try:
        import sys as _s
        _s.path.insert(0, str(ROOT / "scripts"))
        from lib.route_log import emit as _emit
        _emit("dashboard")
    except (ImportError, OSError):
        pass

    events = load_events(days=args.days)
    projects = collect_projects()

    parts = []
    parts.append("# Workspace Dashboard")
    parts.append("")
    n_sessions = len({e["session_id"] for e in events if e.get("session_id")})
    parts.append(
        f"生成于 {NOW.isoformat(timespec='seconds')} · 过去 {args.days} 天数据 · "
        f"events={len(events)} · sessions={n_sessions} · projects={len(projects)}"
    )
    parts.append("")
    parts.append("## 项目视图")
    parts.append("")
    parts.append(render_projects(projects))
    parts.append("")
    parts.append(f"## Skill 使用（{args.days} 天）")
    parts.append("")
    parts.append(render_skills(events, args.days))
    parts.append("")
    parts.append(f"## hub 包生产线（{args.days} 天）")
    parts.append("")
    parts.append(render_hub(events, args.days))
    parts.append("")
    parts.append(f"## Sub-agent 调度（{args.days} 天）")
    parts.append("")
    parts.append(render_agents(events, args.days))
    parts.append("")
    parts.append(f"## 快捷路由热度（{args.days} 天）")
    parts.append("")
    parts.append(render_routes(events, args.days))
    parts.append("")
    parts.append(f"## Hook 健康度（{args.days} 天）")
    parts.append("")
    parts.append(render_hooks(events, args.days))
    parts.append("")
    if args.days >= 28:
        parts.append(f"## Gate 周 block 率趋势（{args.days} 天）")
        parts.append("")
        parts.append(render_gate_trend(events, args.days))
        parts.append("")
    parts.append("## 异常告警")
    parts.append("")
    parts.append(render_anomalies(events, projects))
    parts.append("")

    DASHBOARD.write_text("\n".join(parts), encoding="utf-8")
    print(f"✅ Dashboard: {DASHBOARD.relative_to(ROOT)}")
    print(f"   events={len(events)} projects={len(projects)}")


if __name__ == "__main__":
    main()
