#!/usr/bin/env python3
r"""
批量修复文件中「CJK 旁半角标点」违规。
复用 check_cjk_punct.py 的检测模式，自动将半角标点替换为全角。

特殊保护：
- 代码块（```...```）内不改
- 行内代码（`...`）内不改
- URL 内不改
- 比例写法 1:1、10:1、N:1 不改冒号
- 公式函数 min()/max() 内不改
- 选项标记 A) B) C) 不改
- 代码标识符如 Float(8) 不改
- Markdown 标题行正常修复

Usage:
    python3 scripts/fix_cjk_punct.py <file1> [<file2> ...]
    python3 scripts/fix_cjk_punct.py --dry-run <file1>   # 只显示会改什么，不写文件
"""
import re
import sys
from pathlib import Path

CJK = r'[一-鿿]'
_CJK_RE = re.compile(CJK)

SKIP_FILE_SUFFIXES = {".docx", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip",
                      ".pyc", ".woff", ".woff2", ".ttf", ".ico", ".svg"}
SKIP_DIR_NAMES = {"__pycache__", "node_modules", ".git", "archive", ".public"}
MAX_LINES = 5000


def _is_cjk(ch: str) -> bool:
    return bool(_CJK_RE.match(ch))


def _prev_non_space(s: str, idx: int) -> int:
    j = idx - 1
    while j >= 0 and s[j] == ' ':
        j -= 1
    return j


def _next_non_space(s: str, idx: int) -> int:
    j = idx + 1
    while j < len(s) and s[j] == ' ':
        j += 1
    return j if j < len(s) else -1


def _build_protected(line_str: str) -> set[int]:
    """构建保护区域索引集合"""
    protected: set[int] = set()

    def _mark(start: int, end: int):
        for j in range(start, end):
            protected.add(j)

    # 行内代码 `...`
    in_bt = False
    bt_start = 0
    for i, c in enumerate(line_str):
        if c == '`':
            if not in_bt:
                in_bt = True
                bt_start = i
            else:
                _mark(bt_start, i + 1)
                in_bt = False

    # URL
    for m in re.finditer(r'https?://\S+', line_str):
        _mark(m.start(), m.end())

    # 比例写法 数字:数字、N:数字
    for m in re.finditer(r'\d+:\d+', line_str):
        _mark(m.start(), m.end())
    for m in re.finditer(r'[NnMm]:\d+', line_str):
        _mark(m.start(), m.end())

    # 选项标记 A) B) C) — 前面必须是行首、空格、|，不能紧跟其他字母
    for m in re.finditer(r'(?:^|(?<=[\s|]))([A-Z]\))', line_str):
        _mark(m.start(1), m.end(1))

    # 函数调用 min()/max()/sum()/avg()/count()
    for m in re.finditer(r'(?:min|max|sum|avg|count)\([^)]*\)', line_str, re.IGNORECASE):
        _mark(m.start(), m.end())

    # 代码标识符：英文单词紧跟括号如 Float(8)、dict(key=val)
    for m in re.finditer(r'[A-Za-z_]\w*\([^)]*\)', line_str):
        # 只保护左侧非 CJK 的情况（真正的代码调用）
        left = _prev_non_space(line_str, m.start())
        if left < 0 or not _is_cjk(line_str[left]):
            _mark(m.start(), m.end())

    # 纯英文括号内容如 (USDT)、(normal) —— 两侧跳空格后都非 CJK 才保护
    for m in re.finditer(r'\([A-Za-z0-9_.+\-/%\s]{1,30}\)', line_str):
        content = m.group()[1:-1].strip()
        if not re.match(r'^[A-Za-z0-9_.+\-/%\s]+$', content):
            continue
        left = _prev_non_space(line_str, m.start())
        right = _next_non_space(line_str, m.end() - 1)
        left_cjk = left >= 0 and _is_cjk(line_str[left])
        right_cjk = right >= 0 and _is_cjk(line_str[right])
        if not left_cjk and not right_cjk:
            _mark(m.start(), m.end())

    return protected


def fix_line(line: str) -> str:
    """对单行执行 CJK 旁半角标点修复"""
    chars = list(line)
    length = len(chars)
    line_str = ''.join(chars)

    protected = _build_protected(line_str)
    result = list(chars)

    # Pass 1：逗号、冒号、分号（独立字符，不需要配对）
    for i in range(length):
        if i in protected:
            continue
        c = chars[i]
        if c not in (',', ':', ';'):
            continue
        p = _prev_non_space(line_str, i)
        n = _next_non_space(line_str, i)
        p_cjk = p >= 0 and _is_cjk(chars[p])
        n_cjk = n >= 0 and _is_cjk(chars[n])
        if not p_cjk and not n_cjk:
            continue
        if c == ',':
            result[i] = '，'
        elif c == ':':
            result[i] = '：'
        elif c == ';':
            result[i] = '；'

    # Pass 2：括号成对处理——找配对的 ()，任一侧旁有 CJK 则两个都改全角
    stack: list[int] = []
    pairs: list[tuple[int, int]] = []
    for i in range(length):
        if i in protected:
            continue
        if chars[i] == '(':
            stack.append(i)
        elif chars[i] == ')' and stack:
            pairs.append((stack.pop(), i))

    for left_i, right_i in pairs:
        lp = _prev_non_space(line_str, left_i)
        rn = _next_non_space(line_str, right_i)
        left_cjk = lp >= 0 and _is_cjk(chars[lp])
        right_cjk = rn >= 0 and _is_cjk(chars[rn])
        # 括号内首尾字符也检查
        ln = _next_non_space(line_str, left_i)
        rp = _prev_non_space(line_str, right_i)
        inner_left_cjk = ln >= 0 and _is_cjk(chars[ln])
        inner_right_cjk = rp >= 0 and _is_cjk(chars[rp])
        if left_cjk or right_cjk or inner_left_cjk or inner_right_cjk:
            result[left_i] = '（'
            result[right_i] = '）'
            # 全角括号自带视觉间距，清除紧邻的单个空格
            if left_i > 0 and result[left_i - 1] == ' ' and left_i - 2 >= 0 and _is_cjk(chars[left_i - 2]):
                result[left_i - 1] = ''
            if right_i + 1 < length and result[right_i + 1] == ' ' and right_i + 2 < length and _is_cjk(chars[right_i + 2]):
                result[right_i + 1] = ''

    return ''.join(result)


def fix_file(path: Path, dry_run: bool = False) -> int:
    """修复单个文件，返回修改行数"""
    if path.suffix.lower() in SKIP_FILE_SUFFIXES:
        return 0
    for part in path.parts:
        if part in SKIP_DIR_NAMES:
            return 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0
    lines = text.splitlines(keepends=True)
    if len(lines) > MAX_LINES:
        return 0

    in_code_block = False
    changed_count = 0
    new_lines = []

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue
        if in_code_block:
            new_lines.append(line)
            continue

        fixed = fix_line(line)
        if fixed != line:
            changed_count += 1
            if dry_run:
                lineno = len(new_lines) + 1
                print(f"  L{lineno}: {line.rstrip()}")
                print(f"     → {fixed.rstrip()}")
        new_lines.append(fixed)

    if changed_count > 0 and not dry_run:
        path.write_text(''.join(new_lines), encoding="utf-8")

    return changed_count


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    files = [Path(a) for a in args if not a.startswith("-")]
    if not files:
        print("usage: fix_cjk_punct.py [--dry-run] <file> [<file>...]", file=sys.stderr)
        sys.exit(1)

    total = 0
    for fp in files:
        if not fp.exists():
            continue
        count = fix_file(fp, dry_run=dry_run)
        if count > 0:
            action = "would fix" if dry_run else "fixed"
            print(f"  {fp}: {action} {count} lines")
            total += count

    if total == 0:
        print("No CJK punctuation issues found.")
    else:
        action = "would be fixed" if dry_run else "fixed"
        print(f"\nTotal: {total} lines {action}.")


if __name__ == "__main__":
    main()
