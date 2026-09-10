#!/usr/bin/env python3
"""pre-commit 强制 code review 门槛 — 重大代码变更（infra 桶或总 churn 超阈值）未经 review 拦截提交。

拦的是流程不是质量：bash hook 跑不了模型，本 gate 只保证「重大变更 commit 前走一遍
code-review skill」这个动作发生。跑法见 stderr 指引；小改动 / 已人工审过用
SKIP_CODE_REVIEW_GATE=1 放行（沿 decision-pair-gate 的 SKIP 约定）。

阈值（lib/thresholds.yaml `code_review`，运行时读取）：
    infra_lines  infra 桶（scripts/lib · .claude/hooks · .githooks）churn 合计下限
    total_lines  在审范围（scripts/ 根 + skills/*/scripts + projects/*/scripts）总 churn 下限
    命中任一即拦。churn = numstat added+deleted，只统计 .py/.sh；hub/ 与非代码文件不进谓词。

用法：
    python3 scripts/check_code_review_gate.py          # 检查当前 staged（pre-commit 自动调）
    SKIP_CODE_REVIEW_GATE=1 python3 scripts/<本脚本>   # 审过后的放行通道

前置：无（读 git index）。退出码：0 放行 / 1 拦截 —— .githooks 侧约定（decision-pair /
staged-large-files 同口径）；post-writeedit 链的 0/2 约定不适用本侧。
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.thresholds import T  # noqa: E402

INFRA_LINES: int = T["code_review"]["infra_lines"]
TOTAL_LINES: int = T["code_review"]["total_lines"]

GATE = "code-review-gate"
SKIP_ENV = "SKIP_CODE_REVIEW_GATE"


def _is_infra(path: str) -> bool:
    """高爆炸半径桶：共享模块与 hook 链——改动会波及所有下游消费者。"""
    return (
        path.startswith("scripts/lib/")
        or path.startswith(".claude/hooks/")
        or path.startswith(".githooks/")
    )


def _in_scope(path: str) -> bool:
    """code-review skill 的在审范围（hub/ 分发包走自己的管线，不进）。"""
    if _is_infra(path):
        return True
    parts = PurePosixPath(path).parts
    if parts[:1] == ("scripts",):
        return True
    if len(parts) >= 5 and parts[:2] == (".claude", "skills") and parts[3] == "scripts":
        return True
    return parts[:1] == ("projects",) and "scripts" in parts


def is_significant(rows) -> tuple[bool, list[str]]:
    """谓词：numstat 行 [(added, deleted, path), ...] → (是否重大, 理由列表)。

    added/deleted 为 "-"（二进制 / rename 空统计）或路径非 py/sh 的行直接跳过。
    """
    infra_churn = 0
    total_churn = 0
    biggest: list[tuple[int, str]] = []

    for added, deleted, path in rows:
        if added == "-" or deleted == "-":
            continue
        # .githooks/ 下全是 shell 脚本（pre-commit / post-commit 无扩展名），不按扩展名筛
        if not path.endswith((".py", ".sh")) and not path.startswith(".githooks/"):
            continue
        churn = int(added) + int(deleted)
        if not _in_scope(path):
            continue
        total_churn += churn
        if _is_infra(path):
            infra_churn += churn
        biggest.append((churn, path))

    reasons: list[str] = []
    if infra_churn >= INFRA_LINES:
        reasons.append(f"infra 路径（scripts/lib · .claude/hooks · .githooks）churn {infra_churn} 行 ≥ {INFRA_LINES}")
    if total_churn >= TOTAL_LINES:
        reasons.append(f"在审范围总 churn {total_churn} 行 ≥ {TOTAL_LINES}")
    if reasons:
        return True, reasons
    return False, []


def _top_files(rows, n: int = 8) -> list[str]:
    ranked = sorted(
        ((int(a) + int(d), p) for a, d, p in rows
         if a != "-" and d != "-"
         and (p.endswith((".py", ".sh")) or p.startswith(".githooks/")) and _in_scope(p)),
        reverse=True,
    )[:n]
    return [f"{p}（{c} 行）" for c, p in ranked]


def main() -> int:
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print(__doc__)
        return 0

    out = subprocess.run(
        ["git", "diff", "--cached", "--numstat", "--diff-filter=ACMR"],
        capture_output=True,
    ).stdout
    rows = []
    for line in out.decode("utf-8", "surrogateescape").splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            rows.append((parts[0], parts[1], parts[2]))

    hit, reasons = is_significant(rows)
    if not hit:
        return 0

    if os.environ.get(SKIP_ENV, "0") == "1":
        print(f"⚠️  [{GATE}] 重大代码变更经 SKIP 豁免放行（应已跑过 code-review）", file=sys.stderr)
        return 0

    print(f"🚫 [{GATE}] 重大代码变更未过 code review", file=sys.stderr)
    for r in reasons:
        print(f"   {r}", file=sys.stderr)
    print("   文件（按 churn 排序）：", file=sys.stderr)
    for f in _top_files(rows):
        print(f"     {f}", file=sys.stderr)
    print("", file=sys.stderr)
    print("   → 修法 1: python3 .claude/skills/code-review/scripts/scan_changes.py --staged", file=sys.stderr)
    print("             按 code-review skill 出报告并处理 findings，再重新 commit", file=sys.stderr)
    print(f"   → 修法 2: 确认小改动 / 已人工审过 → {SKIP_ENV}=1 git commit ...", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
