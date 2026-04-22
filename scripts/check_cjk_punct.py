#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
r"""
扫描文件中「CJK 旁半角标点」违规。用于 hook / 自检 / CI。

规则(soul.md):中文标点统一用全角,中英混排也不和半角混排。
例外:代码/路径/英文术语内部的符号保留半角(如 P:\path, http://, pageId:123)。

Usage:
    python3 scripts/check_cjk_punct.py <file_path>
    python3 scripts/check_cjk_punct.py <file1> <file2> ...

退出码:
    0 — 无违规或纯 warning(本工具默认 warn 不 block)
    2 — 传 --strict 且有违规时返回(给 CI / pre-commit 用)
"""
import re
import sys
from pathlib import Path

CJK = r"[一-鿿]"
# 匹配「CJK 旁半角标点」的模式。命中 → 违规。
# 思路:半角标点两侧至少一侧是 CJK(或者 CJK+空格+半角+空格+CJK 这种变体)
PATTERNS = [
    (re.compile(rf"{CJK}\s*([:,;])\s*{CJK}"), "半角 : , ; 夹 CJK"),
    (re.compile(rf"{CJK}\s*([:,;])\s*[A-Za-z0-9]"), "CJK + 半角 : , ; + 英文/数字"),
    (re.compile(rf"[A-Za-z0-9]\s*([:,;])\s*{CJK}"), "英文/数字 + 半角 : , ; + CJK"),
    (re.compile(rf"{CJK}\s*\("), "CJK 后半角左括号 ("),
    (re.compile(rf"\)\s*{CJK}"), "半角右括号 ) 后 CJK"),
    (re.compile(rf"{CJK}\s*\)"), "CJK 后半角右括号 )"),
    (re.compile(rf"\(\s*{CJK}"), "半角左括号 ( 后 CJK"),
]

# 跳过的行(url / scene-id 范围 / 代码片段等常见误报)
SKIP_LINE_PATTERNS = [
    re.compile(r"https?://"),
    re.compile(r"^\s*```"),  # 代码块栅栏
    re.compile(r"^\s*[#/]"),  # 注释行(虽然可能也有中文)
]

# 跳过的文件扩展 / 目录
SKIP_FILE_SUFFIXES = {".docx", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip",
                      ".pyc", ".woff", ".woff2", ".ttf", ".ico", ".svg"}
SKIP_DIR_NAMES = {"__pycache__", "node_modules", ".git", "archive", ".public"}
MAX_LINES = 5000  # 超大文件跳过


def check_file(path: Path) -> list[tuple[int, str, str]]:
    """返回 [(lineno, reason, line_excerpt), ...]"""
    if path.suffix.lower() in SKIP_FILE_SUFFIXES:
        return []
    for part in path.parts:
        if part in SKIP_DIR_NAMES:
            return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    if len(lines) > MAX_LINES:
        return []

    # 跟踪代码块状态,代码块内跳过
    in_code_block = False
    hits = []
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if any(p.search(line) for p in SKIP_LINE_PATTERNS):
            continue
        for pat, reason in PATTERNS:
            m = pat.search(line)
            if m:
                # 去重:同一行只报第一个命中
                excerpt = line.strip()[:120]
                hits.append((i, reason, excerpt))
                break
    return hits


def main():
    args = sys.argv[1:]
    strict = "--strict" in args
    files = [Path(a) for a in args if not a.startswith("-")]
    if not files:
        print("usage: check_cjk_punct.py <file> [<file>...] [--strict]", file=sys.stderr)
        sys.exit(1)

    total = 0
    for fp in files:
        if not fp.exists():
            continue
        hits = check_file(fp)
        if hits:
            print(f"\n⚠️  {fp} — {len(hits)} 处 CJK 旁半角标点", file=sys.stderr)
            for lineno, reason, excerpt in hits[:20]:
                print(f"  L{lineno} [{reason}]", file=sys.stderr)
                print(f"    {excerpt}", file=sys.stderr)
            if len(hits) > 20:
                print(f"  ... (共 {len(hits)} 处,仅显示前 20)", file=sys.stderr)
            total += len(hits)

    if total == 0:
        sys.exit(0)
    print(f"\n💡 修复建议：半角 → 全角\n  : → ：    , → ，    ; → ；    ( → （    ) → ）", file=sys.stderr)
    sys.exit(2 if strict else 0)


if __name__ == "__main__":
    main()
