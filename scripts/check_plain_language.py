#!/usr/bin/env python3
r"""
产出物「讲人话」自检 — 全 PM-WORKSPACE 唯一规则源（新）。

适用：deliverables/ 下对外产出物（leader / 业务 / 设计 / 研发读）
规则来源：.claude/rules/pm-workflow.md「人读产出物讲人话（强制）」

违禁词（strict 全部阻断）：
  1. 内部文件名：context.md / scene-list.md / SKILL.md / CLAUDE.md / pm-workflow.md
  2. 决策 / 章节锚点：决策 N / 第 N 章|节|条
  3. 骨架锚点：PART A / PART 1 / PART B2（IMAP / 原型骨架内部编号外泄）
  4. 残留占位：[待补充*] / FIXME / TODO

免扫区域：
  - markdown 代码块 ``` ... ```
  - 行内代码 `xxx`
  - markdown 链接 URL 部分：[text](url) 只扫 text，URL 忽略
  - HTML <code> / <pre> 标签内容

Usage:
    python3 scripts/check_plain_language.py <file>... [--strict]
    cat foo.md | python3 scripts/check_plain_language.py --stdin [--strict]

退出码：
    0 — 无违规
    1 — 有违规但未传 --strict
    2 — 传 --strict 且有违规（hook 用）
"""
import re
import sys
from pathlib import Path

# ── 违禁 pattern ─────────────────────────────────────────────

# 1. 内部文件名（以 .md 结尾的 PM-WORKSPACE 内部文档）
INTERNAL_FILES_RE = re.compile(
    r"\b(?:context|scene-list|SKILL|CLAUDE|pm-workflow)\.md\b"
)

# 2. 决策编号 / 章节锚点
DECISION_RE = re.compile(r"决策\s*\d+")
CHAPTER_RE = re.compile(r"第\s*\d+\s*[章节条]")

# 3. 骨架锚点（PART A / PART 1 / PART B2），前后需有空格 / 行首 / 中文标点边界
# 避免误伤 "PART-TIME" 或正文里的 "a part" 这类用法
PART_ANCHOR_RE = re.compile(r"(?<![A-Za-z\-])PART\s+[A-Z0-9]+(?![A-Za-z\-])")

# 4. 残留占位
PLACEHOLDER_RE = re.compile(r"\[待补充[^\]]*\]")
FIXME_RE = re.compile(r"\bFIXME\b")
TODO_RE = re.compile(r"\bTODO\b")

STRICT_PATTERNS = [
    (INTERNAL_FILES_RE, "内部文件名"),
    (DECISION_RE, "决策编号"),
    (CHAPTER_RE, "章节锚点"),
    (PART_ANCHOR_RE, "PART 骨架锚点"),
    (PLACEHOLDER_RE, "待补充占位"),
    (FIXME_RE, "FIXME 残留"),
    (TODO_RE, "TODO 残留"),
]

# ── 免扫剥离 ─────────────────────────────────────────────────

# markdown 链接 [text](url) 仅剥 URL（text 保留扫描）
MD_LINK_RE = re.compile(r"(\[[^\]\n]+\])\(([^)\n]+)\)")
# markdown 行内代码 `xxx`
MD_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
# HTML <code> / <pre> 标签块（含内容）
HTML_CODE_RE = re.compile(r"<(code|pre)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
# 裸 URL
URL_RE = re.compile(r"https?://[^\s)）」』】>\"']+")

# ── 跳过的文件 / 目录 ───────────────────────────────────────

SKIP_FILE_SUFFIXES = {".docx", ".pdf", ".png", ".jpg", ".jpeg", ".gif",
                      ".zip", ".pyc", ".woff", ".woff2", ".ttf", ".ico", ".svg"}
SKIP_DIR_NAMES = {"__pycache__", "node_modules", ".git", "archive",
                  ".public", "_site", "dist", "build"}
MAX_LINES = 5000

# ── 豁免文件名 glob ────────────────────────────────────────

DEFAULT_EXEMPTIONS_BASENAME = [
    "audit-*.md",           # workspace-audit 产出物（PM 自用）
    "fix-plan-*.md",        # audit 配套 fix plan（PM 自用）
    "imap-*.html",          # IMAP 走 check_imap.sh
    "interaction-*.html",
    "*-imap.html",
    "*-interaction.html",
]

# 整个目录豁免（workspace-audit 产出目录下所有内容都按内部文档处理）
DEFAULT_EXEMPTIONS_PATHSEGMENT = [
    "audits",
]


def is_exempted(path: Path) -> bool:
    name = path.name
    for pat in DEFAULT_EXEMPTIONS_BASENAME:
        if Path(name).match(pat):
            return True
    for seg in DEFAULT_EXEMPTIONS_PATHSEGMENT:
        if seg in path.parts:
            return True
    return False


def strip_inline(line: str) -> str:
    """剥离免扫区域，用 \\x01 占位保留原长度，保证 col 报告位置准确。"""
    result = line

    # HTML <code> / <pre>（跨行 match 时单行处理依然覆盖单行内）
    result = HTML_CODE_RE.sub(lambda m: "\x01" * len(m.group()), result)

    # markdown 链接：保留 [text]，剥 (url)
    def _strip_link_url(m):
        text_part = m.group(1)  # 含方括号
        url_part = m.group(2)
        return text_part + "(" + "\x01" * len(url_part) + ")"
    result = MD_LINK_RE.sub(_strip_link_url, result)

    # markdown 行内代码
    result = MD_INLINE_CODE_RE.sub(lambda m: "\x01" * len(m.group()), result)

    # 裸 URL
    result = URL_RE.sub(lambda m: "\x01" * len(m.group()), result)

    return result


def _scan_lines(lines: list[str]) -> list[tuple[int, str, str, str]]:
    """返回 [(lineno, category, matched_text, excerpt), ...]"""
    hits: list[tuple[int, str, str, str]] = []
    in_code_block = False
    in_html_code_block = False

    for i, raw_line in enumerate(lines, 1):
        # markdown 代码块栅栏
        if raw_line.lstrip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # 跨行 HTML <pre> / <code>（简单状态机，不覆盖嵌套）
        if "<pre" in raw_line.lower() or "<code" in raw_line.lower():
            # 同行开闭由 strip_inline 处理；跨行打开则标记
            if not re.search(r"</(pre|code)>", raw_line, re.IGNORECASE):
                in_html_code_block = True
        if in_html_code_block:
            if re.search(r"</(pre|code)>", raw_line, re.IGNORECASE):
                in_html_code_block = False
            continue

        line = strip_inline(raw_line)

        for pat, category in STRICT_PATTERNS:
            for m in pat.finditer(line):
                matched = raw_line[m.start():m.end()] \
                    if m.end() <= len(raw_line) else m.group()
                excerpt = raw_line.strip()[:120]
                hits.append((i, category, matched, excerpt))
    return hits


def check_file(path: Path) -> list[tuple[int, str, str, str]]:
    if path.suffix.lower() in SKIP_FILE_SUFFIXES:
        return []
    for part in path.parts:
        if part in SKIP_DIR_NAMES:
            return []
    if is_exempted(path):
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    if len(lines) > MAX_LINES:
        return []
    return _scan_lines(lines)


def _report(file_hits: list[tuple[str, list]], strict: bool) -> None:
    total = 0
    for label, hits in file_hits:
        if not hits:
            continue
        total += len(hits)
        print(f"\n{label} — 命中 {len(hits)} 处", file=sys.stderr)
        for lineno, category, matched, excerpt in hits[:20]:
            print(f"  ❌ L{lineno} [{category}] 匹配：{matched!r}", file=sys.stderr)
            print(f"     {excerpt}", file=sys.stderr)
        if len(hits) > 20:
            print(f"  ... （共 {len(hits)} 处，仅显示前 20）", file=sys.stderr)

    if total:
        print("", file=sys.stderr)
        print("❌ 违反「人读产出物讲人话」规则。读者是 leader / 业务，看不懂内部代号。",
              file=sys.stderr)
        print("   修法：把内部锚点（文件名 / 决策 N / 第 N 章 / PART / 占位）改成业务白话。",
              file=sys.stderr)
        print("   临时绕过：SKIP_PLAIN_LANGUAGE_GATE=1", file=sys.stderr)

    if total == 0:
        sys.exit(0)
    sys.exit(2 if strict else 1)


def main():
    args = sys.argv[1:]
    strict = "--strict" in args
    use_stdin = "--stdin" in args
    files = [Path(a) for a in args if not a.startswith("-")]

    if use_stdin:
        content = sys.stdin.read()
        lines = content.splitlines()
        hits = _scan_lines(lines)
        _report([("<stdin>", hits)], strict)
        return

    if not files:
        print("用法: check_plain_language.py <file>... [--strict] [--stdin]",
              file=sys.stderr)
        sys.exit(0)

    file_hits = []
    for f in files:
        if not f.exists():
            continue
        hits = check_file(f)
        file_hits.append((str(f), hits))

    _report(file_hits, strict)


if __name__ == "__main__":
    main()
