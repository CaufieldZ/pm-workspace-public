#!/usr/bin/env python3
"""Workspace Dashboard — 聚合 .claude/logs/usage.jsonl + projects/ 状态。

Usage:
    python3 scripts/dashboard.py [--days 14]

输出：.claude/workspace-dashboard.md
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = ROOT / ".claude" / "logs" / "usage.jsonl"
DASHBOARD = ROOT / ".claude" / "workspace-dashboard.md"
PROJECTS_DIR = ROOT / "projects"
SKILLS_DIR = ROOT / ".claude" / "skills"

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


def extract_blocking(ctx_path: Path) -> str:
    """从 context.md 第 8 章抽第一条阻塞 / 待办。"""
    try:
        text = ctx_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    m = re.search(r"##\s*8[^\n]*\n(.*?)(?=\n##\s|\Z)", text, re.DOTALL)
    if not m:
        return ""
    chapter = m.group(1)
    for line in chapter.split("\n"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if re.match(r"^[-*]\s", s) or re.match(r"^\d+\.\s", s):
            clean = re.sub(r"^[-*]\s+|^\d+\.\s+", "", s)
            return clean[:80] + ("…" if len(clean) > 80 else "")
    return ""


def count_scenes(scene_list: Path) -> int:
    try:
        text = scene_list.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0
    ids = set(re.findall(r"\b[A-Z]-\d+[a-z]?\b", text))
    return len(ids)


def project_mtime(ctx_path: Path) -> float:
    """取 context.md 自身 + 同目录 scene-list + deliverables 目录的最大 mtime。"""
    mtimes = [ctx_path.stat().st_mtime]
    parent = ctx_path.parent
    for name in ("scene-list.md", "deliverables"):
        p = parent / name
        if p.exists():
            mtimes.append(p.stat().st_mtime)
    return max(mtimes)


def count_deliverables(deliv_dir: Path) -> int:
    if not deliv_dir.exists():
        return 0
    n = 0
    for p in deliv_dir.iterdir():
        if p.is_file() and p.suffix in (".md", ".html", ".docx", ".pdf"):
            if "archive" not in p.parts:
                n += 1
    return n


def collect_projects():
    if not PROJECTS_DIR.exists():
        return []
    projects = []
    for ctx in PROJECTS_DIR.glob("**/context.md"):
        rel = ctx.relative_to(PROJECTS_DIR)
        if any(part == "archive" for part in rel.parts):
            continue
        parent = ctx.parent
        scene_list = parent / "scene-list.md"
        projects.append({
            "path": str(rel.parent),
            "scene_count": count_scenes(scene_list) if scene_list.exists() else 0,
            "deliv_count": count_deliverables(parent / "deliverables"),
            "mtime": project_mtime(ctx),
            "blocking": extract_blocking(ctx),
        })
    projects.sort(key=lambda p: p["mtime"], reverse=True)
    return projects


def render_projects(projects):
    if not projects:
        return "_无项目_"
    lines = [
        "| 项目 | scene | 已交付 | 最近活动 | 当前阻塞 |",
        "|------|-------|--------|----------|----------|",
    ]
    for p in projects:
        age_days = int((NOW.timestamp() - p["mtime"]) / 86400)
        age_str = "今天" if age_days == 0 else f"{age_days}d 前"
        blocking = p["blocking"] or "—"
        lines.append(
            f"| {p['path']} | {p['scene_count']} | {p['deliv_count']} | {age_str} | {blocking} |"
        )
    return "\n".join(lines)


def render_skills(events, days):
    skill_events = [e for e in events if e.get("type") == "skill"]
    counter = Counter(e["name"] for e in skill_events)
    last_seen = {}
    for e in skill_events:
        last_seen.setdefault(e["name"], e["ts"])

    all_skills = sorted(
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and d.name != "_shared"
    )
    lines = [
        f"| Skill | {days}d 触发 | 最近一次 | 状态 |",
        "|-------|-----------|----------|------|",
    ]
    for skill in sorted(all_skills, key=lambda s: -counter.get(s, 0)):
        n = counter.get(skill, 0)
        last = last_seen.get(skill, "—")[:10] if skill in last_seen else "—"
        if n >= 10:
            status = "🔥 hot"
        elif n == 0:
            status = "🔘 dead"
        else:
            status = ""
        lines.append(f"| {skill} | {n} | {last} | {status} |")
    return "\n".join(lines)


def render_hooks(events, days):
    hook_events = [e for e in events if e.get("type") in ("hook", "gate")]
    by_name = defaultdict(lambda: defaultdict(int))
    for e in hook_events:
        by_name[e["name"]][e["action"]] += 1

    if not by_name:
        return "_过去 {} 天无 hook 触发_".format(days)

    lines = [
        f"| Hook | triggered | warn | block | clean | skip | 诊断 |",
        "|------|-----------|------|-------|-------|------|------|",
    ]
    for name in sorted(by_name.keys()):
        a = by_name[name]
        total = sum(a.values())
        diag = ""
        if a["block"] > 5:
            diag = "🛡 真护栏"
        elif a["warn"] > 0 and a["block"] == 0:
            diag = "⚠️ 只警告未升级"
        elif total == 0:
            diag = "🔘 未触发"
        lines.append(
            f"| {name} | {a['triggered']} | {a['warn']} | {a['block']} | {a['clean']} | {a['skip']} | {diag} |"
        )
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

    events = load_events(days=args.days)
    projects = collect_projects()

    parts = []
    parts.append("# Workspace Dashboard")
    parts.append("")
    parts.append(
        f"生成于 {NOW.isoformat(timespec='seconds')} · 过去 {args.days} 天数据 · "
        f"events={len(events)} · projects={len(projects)}"
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
    parts.append(f"## Hook 健康度（{args.days} 天）")
    parts.append("")
    parts.append(render_hooks(events, args.days))
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
