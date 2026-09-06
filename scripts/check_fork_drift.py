#!/usr/bin/env python3
"""同源脚本副本漂移登记（源头改了、脱敏副本没跟上的可见化）。

工区里同一能力最多 4 份副本：源头 + hub 分发包 + 项目侧。这些副本**不做自动同源**
—— 脱敏是有意的语义分叉（`hub/README.md` 明确禁盲跑 `sync --apply` 回灌内部措辞）。
本脚本只回答一个问题：**哪些副本落后于源头了，需要人去看一眼**。

判据（内容 + 时间双信号，单信号都会误报）：

  内容相同            → 🟢 无漂移
  内容不同 + 源头更新  → ⚠️  待人工判断（多半有 backport 没做，也可能只是脱敏改造）
  内容不同 + 副本更新  → ℹ️  副本领先（脱敏改造 / 分发侧独有修复，通常正常）

「内容年龄」取 `min(git 最后改动, 文件 mtime)`——两个信号各有失真方向，取早的才可信：
git 时间在文件刚入库时等于入库日（hub 首次纳管全是同一天，无区分度）；mtime 在
clone / checkout 后被重置成 checkout 时间。取 min 让任一信号保真即整体保真。
两者都取不到则只报「内容不同」不判方向。

输出是**待人工判断的清单**，不是 fail。exit 恒 0（warn 级）。

用法：
    python3 scripts/check_fork_drift.py
    python3 scripts/check_fork_drift.py --diff        # 顺带打印每组的 diff 摘要
    python3 scripts/check_fork_drift.py --group youshu_cli
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.repo import find_root  # noqa: E402

# 副本组登记表：{组名: (源头, [副本...])}
# 加新组前先 `find . -name <脚本名>` 确认全部落点，别漏项目侧副本。
FORK_GROUPS: dict[str, tuple[str, list[str]]] = {
    "youshu_cli": (
        "scripts/youshu_cli.py",
        ["hub/youshu-cli/scripts/youshu_cli.py", "hub/tracking-design/scripts/youshu_cli.py"],
    ),
    "query_analytics": (
        "projects/sensors-metrics/scripts/query_analytics.py",
        ["hub/sensors-cli/scripts/query_analytics.py", "hub/tracking-design/scripts/query_analytics.py"],
    ),
    "probe_event_properties": (
        "projects/sensors-metrics/scripts/probe_event_properties.py",
        ["hub/sensors-cli/scripts/probe_event_properties.py",
         "hub/tracking-design/scripts/probe_event_properties.py"],
    ),
    "check_cjk_punct": (
        "scripts/check_cjk_punct.py",
        ["hub/data-report/scripts/check_cjk_punct.py", "hub/prd/scripts/check_cjk_punct.py"],
    ),
    "export_tracking_xlsx": (
        ".claude/skills/prd/scripts/export_tracking_xlsx.py",
        ["hub/tracking-design/scripts/export_tracking_xlsx.py",
         "projects/community/scripts/export_tracking_xlsx.py"],
    ),
    "render_scene_list": (
        ".claude/skills/scene-list/scripts/render_scene_list.py",
        ["hub/scene-list/scripts/render_scene_list.py"],
    ),
    "gen_prd_skeleton": (
        ".claude/skills/prd/scripts/gen_prd_skeleton.py",
        ["hub/prd/scripts/gen_prd_skeleton.py"],
    ),
    "fetch_confluence": (
        "scripts/fetch_confluence.py",
        ["hub/confluence-cli/scripts/fetch_confluence.py"],
    ),
    "md_to_confluence": (
        "scripts/md_to_confluence.py",
        ["hub/confluence-cli/scripts/md_to_confluence.py"],
    ),
}


def git_mtime(root: Path, rel: str) -> str | None:
    """git 最后改动时间（ISO 日期）；未跟踪 / 无历史 → None。"""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", rel],
            cwd=root, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    val = out.stdout.strip()
    return val[:10] if val else None


def fs_mtime(path: Path) -> str | None:
    """文件系统 mtime（ISO 日期）；不存在 → None。"""
    if not path.exists():
        return None
    from datetime import date
    return date.fromtimestamp(path.stat().st_mtime).isoformat()


def content_age(root: Path, rel: str) -> str | None:
    """内容年龄 = min(git 最后改动, 文件 mtime)。

    两个信号各有失真方向（git 在首次入库时偏晚、mtime 在 checkout 后偏晚），
    取早的那个：任一信号保真则整体保真。都取不到 → None。
    """
    dates = [d for d in (git_mtime(root, rel), fs_mtime(root / rel)) if d]
    return min(dates) if dates else None


def compare(root: Path, src_rel: str, copy_rel: str) -> dict:
    """比一个源头-副本对，返回 {status, src_date, copy_date}。"""
    src, copy = root / src_rel, root / copy_rel
    if not src.exists():
        return {"status": "src-missing", "src_date": None, "copy_date": None}
    if not copy.exists():
        return {"status": "copy-missing", "src_date": None, "copy_date": None}

    if src.read_bytes() == copy.read_bytes():
        return {"status": "same", "src_date": None, "copy_date": None}

    s_date, c_date = content_age(root, src_rel), content_age(root, copy_rel)
    if s_date and c_date:
        if s_date > c_date:
            return {"status": "src-ahead", "src_date": s_date, "copy_date": c_date}
        if c_date > s_date:
            return {"status": "copy-ahead", "src_date": s_date, "copy_date": c_date}
    return {"status": "diff-unknown", "src_date": s_date, "copy_date": c_date}


def diff_summary(root: Path, src_rel: str, copy_rel: str, max_lines: int = 6) -> list[str]:
    """diff 摘要（只取变更行首几条，给人一眼判断是不是脱敏改造）。"""
    try:
        out = subprocess.run(
            ["diff", "-u", str(root / src_rel), str(root / copy_rel)],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    lines = [ln for ln in out.stdout.splitlines()
             if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))]
    return lines[:max_lines]


def main() -> int:
    ap = argparse.ArgumentParser(description="同源脚本副本漂移登记")
    ap.add_argument("--diff", action="store_true", help="打印每组 diff 摘要")
    ap.add_argument("--group", help="只查一组（如 youshu_cli）")
    args = ap.parse_args()

    root = find_root()
    groups = {args.group: FORK_GROUPS[args.group]} if args.group and args.group in FORK_GROUPS else FORK_GROUPS
    if args.group and args.group not in FORK_GROUPS:
        print(f"⚠ 未登记的组：{args.group}（已登记：{', '.join(FORK_GROUPS)}）")
        return 0

    需人工看: list[str] = []
    副本领先: list[str] = []
    异常: list[str] = []
    n_same = 0

    for name, (src_rel, copies) in groups.items():
        for copy_rel in copies:
            r = compare(root, src_rel, copy_rel)
            st = r["status"]
            if st == "same":
                n_same += 1
            elif st == "src-ahead":
                需人工看.append(
                    f"  ⚠️  [{name}] 源头 {r['src_date']} > 副本 {r['copy_date']}\n"
                    f"      {src_rel}\n      → {copy_rel}"
                )
                if args.diff:
                    需人工看.extend(f"        {ln}" for ln in diff_summary(root, src_rel, copy_rel))
            elif st == "copy-ahead":
                副本领先.append(f"  · [{name}] {copy_rel}（副本 {r['copy_date']} > 源头 {r['src_date']}）")
            elif st == "diff-unknown":
                需人工看.append(f"  ⚠️  [{name}] 内容不同但时间判不出方向：{copy_rel}")
            else:
                异常.append(f"  ❌ [{name}] {st}：{src_rel if st == 'src-missing' else copy_rel}")

    total = sum(len(c) for _, c in groups.values())
    print(f"副本组 {len(groups)} 个 / 源头-副本对 {total} 组")
    print()

    if 需人工看:
        print(f"⚠️  源头更新、副本停滞（{len(需人工看) if not args.diff else '见下'}）—— 人工看一眼要不要 backport：")
        print("   （不做自动同源：脱敏是有意的语义分叉，禁 sync --apply 回灌内部措辞）")
        for s in 需人工看:
            print(s)
        print()
    else:
        print("🟢 无「源头更新而副本停滞」的组")

    if 副本领先:
        print(f"ℹ️  副本领先源头（{len(副本领先)}）—— 多半是脱敏改造 / 分发侧独有修复，通常正常：")
        for s in 副本领先:
            print(s)
        print()

    if 异常:
        print(f"❌ 登记表与实际不符（{len(异常)}）—— 改 FORK_GROUPS：")
        for s in 异常:
            print(s)
        print()

    if n_same:
        print(f"🟢 内容完全一致：{n_same} 组")

    return 0


if __name__ == "__main__":
    sys.exit(main())
