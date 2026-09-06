#!/usr/bin/env python3
"""LEARNED.md 教训→规则转化视图。

分析 LEARNED.md 条目，检测重复主题 + 与现行规则文件的覆盖关系。
输出：已覆盖 / 待归位 / 重复 三档统计。

Usage:
    python3 scripts/learned_stats.py [--learned .claude/LEARNED.md]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0].parent
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


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--learned", type=Path, default=LEARNED)
    args = ap.parse_args()

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


if __name__ == "__main__":
    sys.exit(main())
