#!/usr/bin/env python3
r"""
中文产出物排版自检 — 全 PM-WORKSPACE 唯一规则源。

规则参考：
  - vinta/pangu.js（中英文混排空格规范）
  - sivan/heti（CJK + ANS 排版增强）
  - chinese-copywriting-guidelines（中文文案排版指北）
  - PM-WORKSPACE soul.md（中文标点全角硬规则）

分级（exit code 只受 strict 命中影响）：
  strict — 必改：CJK 旁半角 ,:;()  /  重复标点 ！！ ？？ ？！？！
  warn   — 建议改：中英文间漏空格 / 中数字间漏空格 / 全角标点旁多余空格
  full   — 风格层（默认不查，--full 开启）：英文整句内部应用半角

Usage:
    python3 scripts/check_cjk_punct.py <file> [<file>...] [--strict] [--full]

退出码：
    0 — 无 strict 级违规（warn 命中也返 0）
    2 — 传 --strict 且有 strict 级违规
"""
import re
import sys
from pathlib import Path

# CJK 字符范围（参考 heti，覆盖到 CJK 扩展 A + 兼容汉字；日文假名 / 注音 PM 文档用不到，省略）
# 一-鿿  CJK 统一汉字
# 㐀-䶿  CJK 扩展 A
# 豈-﫿  CJK 兼容汉字
CJK = r"[㐀-䶿一-鿿豈-﫿]"

# ── strict 级：必须修，deliverable 阻断 ──────────────────────
# 半角 : , ; 旁 CJK：用 regex 命中即报
# 半角括号：放到独立配对判定（_check_parens），只在「内部含 CJK」时报，
#          避免 `(cnt=20142805)` `(A-1)` 这类纯英数数据括号被误报。
STRICT_PATTERNS = [
    (re.compile(rf"{CJK}\s*([:,;])\s*{CJK}"), "半角 : , ; 夹 CJK"),
    (re.compile(rf"{CJK}\s*([:,;])\s*[A-Za-z0-9]"), "CJK + 半角 : , ; + 英文/数字"),
    (re.compile(rf"[A-Za-z0-9]\s*([:,;])\s*{CJK}"), "英文/数字 + 半角 : , ; + CJK"),
    # 重复标点（pangu 规则：标点不重复使用）
    (re.compile(r"[！？]{2,}"), "全角标点重复"),
    (re.compile(r"[!?]{3,}"), "英文标点重复 ≥3"),
    (re.compile(r"[！？!?][！？!?]{2,}"), "中英标点混合重复"),
]

# ── warn 级：建议修，hook stderr 提示但不阻断 ──────────────────
# pangu 核心：中英文 / 中数字之间需要空格；全角标点不加空格
WARN_PATTERNS = [
    (re.compile(rf"{CJK}[A-Za-z]"), "中英文间漏空格"),
    (re.compile(rf"[A-Za-z]{CJK}"), "中英文间漏空格"),
    (re.compile(rf"{CJK}[0-9]"), "中文与数字间漏空格"),
    # 数字 + CJK：例外是「90°」「15%」（pangu 明文），所以排除百分号 / 度数后再判
    (re.compile(rf"(?<![°%])[0-9]{CJK}"), "数字与中文间漏空格"),
    # 全角标点旁多余空格（pangu：全角标点与其他字符之间不加空格）
    (re.compile(rf"{CJK}\s+[，。：；！？、》】」』）]"), "全角标点前多余空格"),
    (re.compile(rf"[，。：；！？、《【「『（]\s+{CJK}"), "全角标点后多余空格"),
]

# ── full 级：风格层，默认不查 ─────────────────────────────────
# 英文整句内部用半角（pangu 例外）：「Stay hungry，stay foolish。」应改半角
# 检测：成对全角标点中间夹纯英文 → 提示
FULL_PATTERNS = [
    (re.compile(r"[「『《]([A-Za-z][A-Za-z0-9 ,;'\"]*?[，。：；！？])[」』》]"),
     "英文整句内部应用半角标点"),
]

# ── 行级跳过 ────────────────────────────────────────────
SKIP_LINE_PATTERNS = [
    re.compile(r"^\s*```"),       # 代码块栅栏（in_code_block 也会处理，双保险）
    re.compile(r"^\s*//"),        # C 系单行注释
    re.compile(r"^\s*<!--"),      # HTML 注释
]

# 整行替换为占位（剥离掉这些片段后再跑规则）
INLINE_STRIP_PATTERNS = [
    # markdown 链接 [text](url) — 必须先于裸 URL，避免 \S+ 吞掉右括号导致残形
    re.compile(r"\[([^\]\n]+)\]\([^)\n]+\)"),
    re.compile(r"`[^`\n]+`"),                     # 行内代码 `xxx`
    re.compile(r"<[^<>\n]{1,200}>"),              # HTML 标签
    # 裸 URL — 不吃右括号 / 全角括号 / 引号 / 空格
    re.compile(r"https?://[^\s)）」』】>\"']+"),
]

# 跳过的文件扩展 / 目录
SKIP_FILE_SUFFIXES = {".docx", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip",
                      ".pyc", ".woff", ".woff2", ".ttf", ".ico", ".svg"}
SKIP_DIR_NAMES = {"__pycache__", "node_modules", ".git", "archive", ".public",
                  "_site", "lib", "dist", "build"}
MAX_LINES = 5000


def strip_inline(line: str) -> str:
    """剥离行内代码 / HTML 标签 / 链接 URL / 函数调用整段，避免误报。

    用 \\x01 占位而非空格 —— 否则 `跳转说明：</b>点击` 被剥成 `跳转说明：    点击`，
    会假阳「全角标点后多余空格」。\\x01 不入 \\s / CJK / 标点任何 class，
    不会被相邻规则匹配，同时保留原始字符 offset 以保 line 报告位置准确。
    """
    spans = _protected_spans(line)
    if not spans:
        return line
    spans = sorted(set(spans))
    out = []
    pos = 0
    for s, e in spans:
        if s < pos:
            continue
        out.append(line[pos:s])
        out.append("\x01" * (e - s))
        pos = e
    out.append(line[pos:])
    return "".join(out)


# ── 自动修复 ──────────────────────────────────────────
# 仅修 strict 级（半角→全角 + 重复标点收敛），warn 级（中英文/中数字间空格）
# 改了会动文档物理结构，误伤大（专有名词、命名等），不自动改。
FIX_MAP = {',': '，', ':': '：', ';': '；', '(': '（', ')': '）'}
_CJK_RE = re.compile(CJK)


def _protected_spans(line: str) -> list[tuple[int, int]]:
    spans = []
    for pat in INLINE_STRIP_PATTERNS:
        for m in pat.finditer(line):
            spans.append(m.span())
    spans.extend(_fn_call_spans(line, spans))
    return spans


def _fn_call_spans(line: str, base_spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """识别函数调用 `xxx(...)` 整段（含括号），作为 protected span。
    避免函数参数列表里的 `, ; :` 被错改全角。
    """
    spans: list[tuple[int, int]] = []
    stack: list[tuple[int, bool]] = []  # (左括号位置, 是否函数调用)
    for i, c in enumerate(line):
        if any(s <= i < e for s, e in base_spans):
            continue
        if c == '(':
            is_fn = bool(_FN_CALL_RE.search(line[:i]))
            stack.append((i, is_fn))
        elif c == ')' and stack:
            l, is_fn = stack.pop()
            if is_fn:
                # 把整个 xxx(...) 段（含函数名）保护起来
                fn_match = _FN_CALL_RE.search(line[:l])
                fn_start = fn_match.start() if fn_match else l
                spans.append((fn_start, i + 1))
    return spans


def _in_any_span(idx: int, spans: list[tuple[int, int]]) -> bool:
    for s, e in spans:
        if s <= idx < e:
            return True
    return False


_FN_CALL_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*$")


def _paren_pairs_with_cjk(line: str, spans: list[tuple[int, int]]) -> set[int]:
    """找出「应改全角的半角括号」位置集。判定规则：
      1. 左右成对
      2. 内部含 CJK
      3. 左括号前不是 ASCII 标识符（排除 `abs(x)` `query_xxx(...)` 这类函数调用）
    举例：
      - `用户(VIP用户)进入` → 改（中文上下文）
      - `编号(A-1)` → 不改（内部纯英数）
      - `abs(授信应还)` → 不改（函数调用）
      - `query_retention_report(second_event=同上)` → 不改（函数调用）
    """
    positions: set[int] = set()
    stack: list[int] = []
    for i, c in enumerate(line):
        if _in_any_span(i, spans):
            continue
        if c == '(':
            stack.append(i)
        elif c == ')' and stack:
            l = stack.pop()
            inner = line[l+1:i]
            if not _CJK_RE.search(inner):
                continue
            # 函数调用排除：左括号前是 ASCII 标识符
            if _FN_CALL_RE.search(line[:l]):
                continue
            positions.add(l)
            positions.add(i)
    return positions


def fix_line(line: str) -> str:
    """对单行做 strict 级修复：半角→全角 + 重复标点收敛。代码 / URL / 行内代码区域不动。"""
    spans = _protected_spans(line)
    paren_fix = _paren_pairs_with_cjk(line, spans)
    out = list(line)
    for i, c in enumerate(line):
        if c not in FIX_MAP:
            continue
        if _in_any_span(i, spans):
            continue
        if c in '()':
            # 括号必须成对处理，且内部含 CJK 才改
            if i not in paren_fix:
                continue
            out[i] = FIX_MAP[c]
            continue
        # `, : ;`：旁 CJK 才改
        prev = line[i-1] if i > 0 else ''
        nxt = line[i+1] if i+1 < len(line) else ''
        if not (_CJK_RE.match(prev) or _CJK_RE.match(nxt)):
            continue
        if c == ':':
            window = line[max(0, i-6):i].lower()
            if 'http' in window or 'ftp' in window:
                continue
        out[i] = FIX_MAP[c]
    new = ''.join(out)
    # 重复标点收敛（≥2 同类 → 单个全角）
    new = re.sub(r'([！？])\1+', r'\1', new)
    new = re.sub(r'!{2,}', '！', new)
    new = re.sub(r'\?{2,}', '？', new)
    new = re.sub(r'([！？])([！？])(?:\1\2)+', r'\1\2', new)  # ？！？！→？！
    return new


def fix_file(path: Path) -> int:
    """对文件做 strict 级修复，写回原文件。返回改动行数。"""
    if path.suffix.lower() in SKIP_FILE_SUFFIXES:
        return 0
    for part in path.parts:
        if part in SKIP_DIR_NAMES:
            return 0
    try:
        original = path.read_text(encoding="utf-8")
    except Exception:
        return 0
    lines = original.splitlines(keepends=True)
    if len(lines) > MAX_LINES:
        return 0

    in_code_block = False
    changed = 0
    for i, raw in enumerate(lines):
        body = raw.rstrip('\n').rstrip('\r')
        eol = raw[len(body):]
        if body.lstrip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if any(p.search(body) for p in SKIP_LINE_PATTERNS):
            continue
        new_body = fix_line(body)
        if new_body != body:
            lines[i] = new_body + eol
            changed += 1

    if changed:
        path.write_text(''.join(lines), encoding="utf-8")
    return changed


def check_text(text: str, full: bool = False) -> list[tuple[int, str, str, str]]:
    """对文本块跑规则。给 docx / pptx 等二进制文件提取 full_text 后调用。"""
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        return []
    return _scan_lines(lines, full=full)


def check_file(path: Path, full: bool = False) -> list[tuple[int, str, str, str]]:
    """返回 [(lineno, level, reason, line_excerpt), ...]"""
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
    return _scan_lines(lines, full=full)


def _scan_lines(lines: list[str], full: bool = False) -> list[tuple[int, str, str, str]]:
    pattern_groups = [("strict", STRICT_PATTERNS), ("warn", WARN_PATTERNS)]
    if full:
        pattern_groups.append(("full", FULL_PATTERNS))

    in_code_block = False
    hits = []
    for i, raw_line in enumerate(lines, 1):
        if raw_line.lstrip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if any(p.search(raw_line) for p in SKIP_LINE_PATTERNS):
            continue

        line = strip_inline(raw_line)
        recorded_levels = set()

        # 括号配对独立判定（与 fixer 同源）：内含 CJK 即报 strict
        spans = _protected_spans(raw_line)
        if _paren_pairs_with_cjk(raw_line, spans):
            excerpt = raw_line.strip()[:120]
            hits.append((i, "strict", "半角括号包 CJK 内容", excerpt))
            recorded_levels.add("strict")

        # 同行多级命中：strict 优先；同级只取第一个
        for level, patterns in pattern_groups:
            if level in recorded_levels:
                continue
            for pat, reason in patterns:
                if pat.search(line):
                    excerpt = raw_line.strip()[:120]
                    hits.append((i, level, reason, excerpt))
                    recorded_levels.add(level)
                    break
    return hits


LEVEL_ICON = {"strict": "❌", "warn": "⚠️ ", "full": "💡"}


def _report(file_hits: list[tuple[str, list]], strict: bool) -> None:
    strict_total = warn_total = full_total = 0
    for label, hits in file_hits:
        if not hits:
            continue
        s_n = sum(1 for h in hits if h[1] == "strict")
        w_n = sum(1 for h in hits if h[1] == "warn")
        f_n = sum(1 for h in hits if h[1] == "full")
        strict_total += s_n; warn_total += w_n; full_total += f_n
        summary = []
        if s_n: summary.append(f"strict {s_n}")
        if w_n: summary.append(f"warn {w_n}")
        if f_n: summary.append(f"style {f_n}")
        print(f"\n{label} — {' / '.join(summary)}", file=sys.stderr)
        for lineno, level, reason, excerpt in hits[:20]:
            print(f"  {LEVEL_ICON[level]} L{lineno} [{reason}]", file=sys.stderr)
            print(f"     {excerpt}", file=sys.stderr)
        if len(hits) > 20:
            print(f"  ... (共 {len(hits)} 处，仅显示前 20)", file=sys.stderr)

    if strict_total or warn_total or full_total:
        print("", file=sys.stderr)
        if strict_total:
            print("❌ strict（必改）: 半角 → 全角  : → ：  , → ，  ; → ；  ( → （  ) → ）",
                  file=sys.stderr)
            print("                  重复标点 → 单个全角  ！！→ ！  ？？→ ？", file=sys.stderr)
        if warn_total:
            print("⚠️  warn（建议改）: 中英文 / 中数字间加空格；全角标点旁去空格",
                  file=sys.stderr)
        if full_total:
            print("💡 style: 英文整句内部用半角逗号 / 句号", file=sys.stderr)

    if strict_total == 0:
        sys.exit(0)
    sys.exit(2 if strict else 0)


def main():
    args = sys.argv[1:]
    strict = "--strict" in args
    full = "--full" in args
    use_stdin = "--stdin" in args
    do_fix = "--fix" in args
    files = [Path(a) for a in args if not a.startswith("-")]

    if do_fix:
        if not files:
            print("--fix 需要传文件路径", file=sys.stderr)
            sys.exit(1)
        total = 0
        for fp in files:
            if not fp.exists():
                continue
            n = fix_file(fp)
            if n:
                print(f"  fixed {n} lines  {fp}", file=sys.stderr)
                total += n
        print(f"\n✅ strict 级自动修复完成，{total} 行改动。warn 级（中英文/中数字间空格）不自动改，需手动判断。",
              file=sys.stderr)
        return

    if use_stdin:
        text = sys.stdin.read()
        _report([("<stdin>", check_text(text, full=full))], strict=strict)
        return

    if not files:
        print("usage: check_cjk_punct.py <file> [<file>...] [--strict] [--full]\n"
              "       cat text | check_cjk_punct.py --stdin [--strict] [--full]\n"
              "       check_cjk_punct.py --fix <file> [<file>...]   # 自动修 strict 级",
              file=sys.stderr)
        sys.exit(1)

    file_hits = [(str(fp), check_file(fp, full=full)) for fp in files if fp.exists()]
    _report(file_hits, strict=strict)


if __name__ == "__main__":
    main()
