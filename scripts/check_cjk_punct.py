#!/usr/bin/env python3
r"""
中文产出物排版自检 — 全 PM-WORKSPACE 唯一规则源。

规则参考：
  - vinta/pangu.js（中英文混排空格规范）
  - sivan/heti（CJK + ANS 排版增强）
  - chinese-copywriting-guidelines（中文文案排版指北）
  - PM-WORKSPACE soul.md（中文标点全角硬规则）

分级（exit code 只受 strict 命中影响）：
  strict — 必改：CJK 旁半角 ,:;()!?  /  重复标点 ！！ ？？ ？！？！  /  全角数字字母 １０００ ＡＢＣ
           水平分割线 ---（传 Confluence 渲染崩，改空行 / ## 标题）
  warn   — 建议改：中英文间漏空格 / 中数字间漏空格 / 数字与单位间漏空格 / 全角标点旁多余空格 /
           中文省略号 ... → …… / 专有名词大小写（GitHub 不写 github）
  full   — 风格层（默认不查，--full 开启）：英文整句内部应用半角

Usage:
    python3 scripts/check_cjk_punct.py <file> [<file>...] [--strict] [--full]
    python3 scripts/check_cjk_punct.py --fix <file>         # 自动修 strict 级标点
    python3 scripts/check_cjk_punct.py --fix-spaces <file>  # 自动补空格（中英/中数/单位，幂等）

退出码：
    0 — 无 strict 级违规（warn 命中也返 0）
    2 — 传 --strict 且有 strict 级违规
"""

# route-log: 调用埋点（scripts/lib/route_log.py）
import pathlib as _pl
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("check_cjk_punct"))
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.diagram_text import extract_scan_lines  # noqa: E402
from lib.path_skip import is_skipped  # noqa: E402
from lib.thresholds import CHECKER_MAX_LINES  # noqa: E402

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
    # 半角 ! ? 紧跟 CJK（chinese-copywriting-guidelines：中文里用全角 ！？）
    # 只查「CJK 后紧跟半角 !?」这一无歧义场景（你知道嘛? / 真的!），
    # 英文整句结尾的 !? 由其前导英文承担，不在此报；markdown 图片 ![]() 已在 strip 阶段剥离
    (re.compile(rf"{CJK}([!?])"), "CJK 后半角 ! ?（应全角 ！ ？）"),
    # 重复标点（pangu 规则：标点不重复使用）
    (re.compile(r"！{2,}"), "全角叹号重复"),
    (re.compile(r"？{2,}"), "全角问号重复"),
    (re.compile(r"[!?]{3,}"), "英文标点重复 ≥3"),
    (re.compile(r"[！？!?][！？!?]{2,}"), "中英标点混合重复"),
    # 全角数字 / 全角拉丁字母（guidelines：数字字母用半角，全角仅排版对齐场景）
    (re.compile(r"[０-９Ａ-Ｚａ-ｚ]"), "全角数字 / 字母（应半角）"),
    # 圈数字 / 实心圈数字 / 括号数字（CLAUDE.md 格式规范禁用）
    # 行内代码 `①②③` 已在 INLINE_STRIP_PATTERNS 剥离，描述性引用包成 `xxx` 即可豁免
    # ①-⒇ 覆盖普通圆 + 带括号 + 带点 / ❶-❿ 实心 / ⓫-⓿ 双圈 + 实心 11-20 / ㉑-㊿ 21-50
    (re.compile(r"[①-⒇❶-❿⓫-⓿㉑-㊿]"),
     "圈数字 / 实心圈数字 / 括号数字（CLAUDE.md 禁用，按场景化规则改写）"),
]

# 数字+单位白名单（WARN_PATTERN 检测与空格自动插入共用同一份，SSOT）
# 只对多字符单位生效，避免误伤 L3 / Q3 / 3.2 / 5G / H5 / 2FA 这类标识/版本/缩写
_UNIT_ALT = r"TB|GB|MB|KB|PB|Gbps|Mbps|Kbps|bps|GHz|MHz|kHz|mAh|fps|dpi|ppi|kg|km|cm|mm|ms"

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
    # 中文省略号：应使用「……」（两个 U+2026），而非半角点「...」
    (re.compile(rf"{CJK}\.\.\.|\.\.\.{CJK}"), "中文省略号应用「……」而非「...」"),
    # 数字与单位间漏空格（guidelines：10 Gbps / 20 TB）
    (re.compile(rf"\b\d+(?:{_UNIT_ALT})\b"),
     "数字与单位间漏空格（如 20 TB / 10 Gbps）"),
]

# ── warn 级：专有名词大小写（guidelines：GitHub 不写 github / GITHUB）──
# 只收「内部含大小写混合」的品牌名 —— 这类被全小写/全大写写错时无歧义；
# 纯缩写（API / URL / HTML）日常散文里大小写宽松，不收，避免噪声。
PROPER_NOUNS = [
    "GitHub", "GitLab", "JavaScript", "TypeScript", "WebSocket", "PostgreSQL",
    "MySQL", "GraphQL", "OAuth", "iOS", "macOS", "iPadOS", "watchOS",
]
_PROPER_LOOKUP = {n.lower(): n for n in PROPER_NOUNS}
_PROPER_RE = re.compile(r"\b(" + "|".join(re.escape(n) for n in PROPER_NOUNS) + r")\b", re.IGNORECASE)

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

# ── 水平分割线 --- 禁用（传 Confluence 渲染崩）──────────────────
# 放过三种合法语义：
#   ① YAML frontmatter 边界（文件首行 --- 开闸 / 再遇 --- 关闸）
#   ② Setext 标题下划线（紧邻上一行非空 → h2 下划线，非 HR）
#   ③ 表格分隔行 | --- |（含 |，不匹配纯 -{3,}）
# CommonMark：HR 前必有空行 → 紧邻上一行非空即判 setext，保守放过（漏报优于误报）
HR_RE = re.compile(r"^ {0,3}-{3,}\s*$")


def _hr_classify(raw_line: str, prev_raw, in_frontmatter: bool) -> tuple[str, bool]:
    """判定 raw_line 属于哪类 ---。返回 (kind, new_in_frontmatter)。

    kind:
      'hr'          — 应禁的水平分割线（strict 报 / fixer 改空行）
      'frontmatter' — YAML 边界（开闸或关闸），放过
      'setext'      — 标题下划线，放过
      'none'        — 非 --- 行
    """
    if not HR_RE.match(raw_line):
        return ("none", in_frontmatter)
    if prev_raw is None and not in_frontmatter:
        return ("frontmatter", True)    # 文件首行 → 开闸
    if in_frontmatter:
        return ("frontmatter", False)   # 闭合
    if prev_raw is not None and prev_raw.strip() != "":
        return ("setext", in_frontmatter)
    return ("hr", in_frontmatter)

# 整行替换为占位（剥离掉这些片段后再跑规则）
INLINE_STRIP_PATTERNS = [
    # markdown 图片 ![alt](url) — 必须先于链接，否则只剥 [alt](url) 残下 `!` 触发「CJK 后半角 !」假阳
    re.compile(r"!\[[^\]\n]*\]\([^)\n]+\)"),
    # 引用式图片 / 链接 ![alt][id] / [text][id] — 同样剥掉前导 `!`，避免误判
    re.compile(r"!?\[[^\]\n]*\]\[[^\]\n]*\]"),
    # markdown 链接 [text](url) — 必须先于裸 URL，避免 \S+ 吞掉右括号导致残形
    re.compile(r"\[([^\]\n]+)\]\([^)\n]+\)"),
    re.compile(r"`[^`\n]+`"),                     # 行内代码 `xxx`
    re.compile(r"<[^<>\n]{1,200}>"),              # HTML 标签
    # HTML 实体 &amp; &lt; &#39; 等 —— 否则 `amp;` 的 `;` 被判「英文 + 半角 ; + CJK」假阳
    re.compile(r"&(?:[a-zA-Z][a-zA-Z0-9]*|#[0-9]+|#x[0-9a-fA-F]+);"),
    # 裸 URL — 不吃右括号 / 全角括号 / 引号 / 空格
    re.compile(r"https?://[^\s)）」』】>\"']+"),
]

# 跳过的文件扩展 / 目录 → lib.path_skip
MAX_LINES = CHECKER_MAX_LINES


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
# strict 级（半角→全角 + 重复标点收敛）由 fix_line 默认档处理。
# 空格级（中英/中数/数字单位）由 fix_line(spaces=True) 处理，机械可补、幂等。
FIX_MAP = {',': '，', ':': '：', ';': '；', '(': '（', ')': '）', '!': '！', '?': '？'}
# 全角数字 / 拉丁字母 → 半角（U+FF10-FF19 / U+FF21-FF3A / U+FF41-FF5A，偏移 0xFEE0）
FULLWIDTH_MAP = {chr(c): chr(c - 0xFEE0)
                 for r in (range(0xFF10, 0xFF1A), range(0xFF21, 0xFF3B), range(0xFF41, 0xFF5B))
                 for c in r}
_CJK_RE = re.compile(CJK)

# 空格自动插入规则（幂等）：零宽边界正则，每个 match.start() = 应插空格的位置。
# 单字母紧贴中文视为型号/变量名（D值/R公式/C模式），不插；仅 ≥2 连续拉丁字母的
# 英文词（GitHub/TRTC）插空格。已有空格时 lookaround 不相邻、天然不重复插（幂等）。
SPACE_BOUNDARY_PATTERNS = [
    re.compile(rf"(?<={CJK})(?=[A-Za-z]{{2,}})"),   # 中 → 英文词（≥2 字母）
    re.compile(rf"(?<=[A-Za-z]{{2}})(?={CJK})"),    # 英文词（≥2 字母）→ 中
    re.compile(rf"(?<={CJK})(?=[0-9])"),            # 中 → 数字
    # 数字 → 中：中文数量级字（万/亿/千/百/兆）是数字构成部分（597万=5.97M），不插空格
    re.compile(rf"(?<=[0-9])(?=(?![万亿千百兆]){CJK})"),
    # 数字 → 单位（20TB → 20 TB）：单位后须是非字母数字（含 CJK / 空格 / 标点 / 行尾），
    # 不能用 \b —— 单位后紧跟 CJK 时（TB文）无词边界，会漏匹配导致非幂等
    re.compile(rf"(?<=[0-9])(?=(?:{_UNIT_ALT})(?![A-Za-z0-9]))"),
]


def _insert_spaces(line: str, spans: list[tuple[int, int]]) -> str:
    """按 SPACE_BOUNDARY_PATTERNS 在中英/中数/数字单位边界插空格。
    保护区（代码 / URL / 行内代码 / 函数调用）内的边界跳过；从右向左插入保持索引有效。"""
    positions: set[int] = set()
    for pat in SPACE_BOUNDARY_PATTERNS:
        for m in pat.finditer(line):
            p = m.start()
            if not _in_any_span(p, spans):
                positions.add(p)
    if not positions:
        return line
    out = line
    for p in sorted(positions, reverse=True):
        out = out[:p] + " " + out[p:]
    return out


def _protected_spans(line: str) -> list[tuple[int, int]]:
    spans = []
    for pat in INLINE_STRIP_PATTERNS:
        for m in pat.finditer(line):
            spans.append(m.span())
    spans.extend(_fn_call_spans(line, spans))
    # 比例写法 数字:数字 / N:数字（fix_cjk_punct 合并过来的保护规则）
    for m in re.finditer(r'\d+:\d+', line):
        spans.append(m.span())
    for m in re.finditer(r'[NnMm]:\d+', line):
        spans.append(m.span())
    # 选项标记 A) B) C) — 行首或 | 后
    for m in re.finditer(r'(?:^|(?<=[\s|]))([A-Z]\))', line):
        spans.append((m.start(1), m.end(1)))
    # 排序 + 合并重叠/包含段：图片 ![alt](url) 同时命中图片与链接两条 pattern 产生嵌套 span，
    # 下游切片重组（fix_line 重复标点收敛）假设 span 互斥，重叠会把已输出片段再拼一遍
    # （图片行被写成 ![X](Y)[X](Y)）
    spans.sort()
    merged: list[tuple[int, int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            if e > merged[-1][1]:
                merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged


def _fn_call_spans(line: str, base_spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """识别函数调用 `xxx(...)` 整段（含括号），作为 protected span。
    避免函数参数列表里的 `, ; :` 被错改全角。
    """
    spans: list[tuple[int, int]] = []
    stack: list[tuple[int, bool]] = []  # (左括号位置, 是否函数调用)
    for i, c in enumerate(line):
        if any(s <= i < e for s, e in base_spans) or any(s <= i < e for s, e in spans):
            continue
        if c == '(':
            is_fn = bool(_FN_CALL_RE.search(line[:i]))
            stack.append((i, is_fn))
        elif c == ')' and stack:
            open_pos, is_fn = stack.pop()
            if is_fn:
                # 把整个 xxx(...) 段（含函数名）保护起来
                fn_match = _FN_CALL_RE.search(line[:open_pos])
                fn_start = fn_match.start() if fn_match else open_pos
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
            open_pos = stack.pop()
            inner = line[open_pos + 1:i]
            if not _CJK_RE.search(inner):
                continue
            # 函数调用排除：左括号前是 ASCII 标识符
            if _FN_CALL_RE.search(line[:open_pos]):
                continue
            positions.add(open_pos)
            positions.add(i)
    return positions


def fix_line(line: str, skip_paren: bool = False, punct: bool = True, spaces: bool = False) -> str:
    """对单行做修复。代码 / URL / 行内代码区域不动。

    punct=True  ：strict 级半角→全角标点 + 重复标点收敛（默认）
    spaces=True ：空格级中英/中数/数字单位间插空格（幂等）
    skip_paren=True 时跳过半角括号→全角的修复（.py 文件 tuple / 函数调用语法保留）。
    """
    spans = _protected_spans(line)
    if not punct:
        return _insert_spaces(line, spans) if spaces else line
    paren_fix = set() if skip_paren else _paren_pairs_with_cjk(line, spans)
    out = list(line)
    for i, c in enumerate(line):
        if c in FULLWIDTH_MAP and not _in_any_span(i, spans):
            out[i] = FULLWIDTH_MAP[c]
            continue
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
        # `, : ; ! ?`：旁 CJK 才改
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
    # 重复标点收敛（≥2 同类 → 单个全角）——逐保护段外切片跑，行内代码/URL 里的 !! ?? 不动
    # （上方字符替换均为 1:1 单字符替换，span 索引对 new 仍有效）
    def _collapse(s):
        s = re.sub(r'([！？])\1+', r'\1', s)
        s = re.sub(r'!{2,}', '！', s)
        s = re.sub(r'\?{2,}', '？', s)
        return re.sub(r'([！？])([！？])(?:\1\2)+', r'\1\2', s)  # ？！？！→？！
    if spans:
        pieces, prev = [], 0
        for s_, e_ in spans:
            pieces.append(_collapse(new[prev:s_]))
            pieces.append(new[s_:e_])
            prev = e_
        pieces.append(_collapse(new[prev:]))
        new = ''.join(pieces)
    else:
        new = _collapse(new)
    if spaces:
        new = _insert_spaces(new, _protected_spans(new))
    return new


def fix_file(path: Path, dry_run: bool = False, punct: bool = True, spaces: bool = False) -> int:
    """对文件做修复。punct=strict 标点+HR，spaces=空格级。dry_run 只输出不写盘。返回改动行数。"""
    if is_skipped(path):
        return 0
    try:
        # 不用 errors="replace"：修复要回写，容错读会把非法字节替换成 U+FFFD 写死
        original = path.read_text(encoding="utf-8")
    except OSError:
        return 0
    except UnicodeDecodeError:
        print(f"  跳过 {path}（非 UTF-8，避免 --fix 回写腐蚀原字节）", file=sys.stderr)
        return 0
    lines = original.splitlines(keepends=True)
    if len(lines) > MAX_LINES:
        return 0

    skip_paren = path.suffix.lower() == ".py"
    in_code_block = False
    in_frontmatter = False      # YAML frontmatter（首行 --- 开闸）
    prev_raw = None             # 紧邻上一行（setext 判定）
    changed = 0
    for i, raw in enumerate(lines):
        body = raw.rstrip('\n').rstrip('\r')
        eol = raw[len(body):]
        if body.lstrip().startswith("```"):
            in_code_block = not in_code_block
            prev_raw = body
            continue
        if in_code_block:
            prev_raw = body
            continue
        if any(p.search(body) for p in SKIP_LINE_PATTERNS):
            prev_raw = body
            continue
        # 水平分割线 --- → 空行（strict 修复，仅 punct 档；空格档不碰结构）
        _kind, in_frontmatter = _hr_classify(body, prev_raw, in_frontmatter)
        if _kind == "hr":
            if punct:
                if dry_run:
                    print(f"  L{i+1}: {body[:80]}", file=sys.stderr)
                    print("     -> (空行)", file=sys.stderr)
                else:
                    lines[i] = eol
                changed += 1
            prev_raw = body
            continue
        new_body = fix_line(body, skip_paren=skip_paren, punct=punct, spaces=spaces)
        if new_body != body:
            if dry_run:
                print(f"  L{i+1}: {body[:80]}", file=sys.stderr)
                print(f"     -> {new_body[:80]}", file=sys.stderr)
            else:
                lines[i] = new_body + eol
            changed += 1
        prev_raw = body

    if changed:
        if dry_run:
            print(f"  ({changed} lines would change, --dry-run)", file=sys.stderr)
        else:
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
    if is_skipped(path):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        return []
    skip_paren = path.suffix.lower() == ".py"
    # .drawio / .mmd 只扫 label 文本（跳过 XML / mermaid 语法噪音），行号回原文件
    diag = extract_scan_lines(path.suffix, lines)
    if diag is not None:
        return _scan_lines(diag, full=full)
    return _scan_lines(lines, full=full, skip_paren=skip_paren)


def _scan_lines(lines: list[str], full: bool = False, skip_paren: bool = False) -> list[tuple[int, str, str, str]]:
    pattern_groups = [("strict", STRICT_PATTERNS), ("warn", WARN_PATTERNS)]
    if full:
        pattern_groups.append(("full", FULL_PATTERNS))

    in_code_block = False
    in_frontmatter = False      # YAML frontmatter（首行 --- 开闸）
    prev_raw = None             # 紧邻上一行（setext 判定）
    hits = []
    for i, raw_line in enumerate(lines, 1):
        if raw_line.lstrip().startswith("```"):
            in_code_block = not in_code_block
            prev_raw = raw_line
            continue
        if in_code_block:
            prev_raw = raw_line
            continue
        if any(p.search(raw_line) for p in SKIP_LINE_PATTERNS):
            prev_raw = raw_line
            continue

        # 水平分割线 --- 禁用（frontmatter / setext / 表格已放过）
        _kind, in_frontmatter = _hr_classify(raw_line, prev_raw, in_frontmatter)
        if _kind == "hr":
            hits.append((i, "strict",
                         "水平分割线 ---（Confluence 渲染崩；改用空行或 ## 小标题分节）",
                         raw_line.strip()[:120]))
            prev_raw = raw_line
            continue

        line = strip_inline(raw_line)
        recorded_levels = set()

        # 括号配对独立判定（与 fixer 同源）：内含 CJK 即报 strict
        # .py 文件跳过：tuple / 函数调用语法用半角括号是 Python 合法语法
        if not skip_paren:
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

        # 专有名词大小写（warn）：让位于空格类 warn，仅本行无 warn 时补报
        if "warn" not in recorded_levels:
            for m in _PROPER_RE.finditer(line):
                correct = _PROPER_LOOKUP[m.group(0).lower()]
                if m.group(0) != correct:
                    hits.append((i, "warn", f"专有名词大小写应为 {correct}", raw_line.strip()[:120]))
                    break
        prev_raw = raw_line
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
        strict_total += s_n
        warn_total += w_n
        full_total += f_n
        summary = []
        if s_n:
            summary.append(f"strict {s_n}")
        if w_n:
            summary.append(f"warn {w_n}")
        if f_n:
            summary.append(f"style {f_n}")
        print(f"\n{label} — {' / '.join(summary)}", file=sys.stderr)
        for lineno, level, reason, excerpt in hits[:20]:
            print(f"  {LEVEL_ICON[level]} L{lineno} [{reason}]", file=sys.stderr)
            print(f"     {excerpt}", file=sys.stderr)
        if len(hits) > 20:
            print(f"  ... (共 {len(hits)} 处，仅显示前 20)", file=sys.stderr)

    if strict_total or warn_total or full_total:
        print("", file=sys.stderr)
        if strict_total:
            print("❌ strict（必改）: 半角 → 全角  : → ：  , → ，  ; → ；  ( → （  ) → ）  ! → ！  ? → ？",
                  file=sys.stderr)
            print("                  重复标点 → 单个全角  ！！→ ！  ？？→ ？；全角数字字母 → 半角  １→1  Ａ→A", file=sys.stderr)
            print("                  水平分割线 --- → 删行 / 换 ## 标题（传 Confluence 渲染崩）",
                  file=sys.stderr)
        if warn_total:
            print("⚠️  warn（建议改）: 中英文 / 中数字间加空格；数字与单位间加空格（20 TB）；全角标点旁去空格；省略号 ... → ……；专有名词大小写（GitHub）",
                  file=sys.stderr)
        if full_total:
            print("💡 style: 英文整句内部用半角逗号 / 句号", file=sys.stderr)

    if strict_total == 0:
        sys.exit(0)
    sys.exit(2 if strict else 0)


USAGE = (
    "usage: check_cjk_punct.py <file> [<file>...] [--strict] [--full]\n"
    "       cat text | check_cjk_punct.py --stdin [--strict] [--full]\n"
    "       check_cjk_punct.py --fix <file> [<file>...] [--dry-run]         # 自动修 strict 级标点\n"
    "       check_cjk_punct.py --fix-spaces <file> [<file>...] [--dry-run]  # 自动补空格（中英/中数/单位）"
)


def main():
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(USAGE)
        sys.exit(0)
    strict = "--strict" in args
    full = "--full" in args
    use_stdin = "--stdin" in args
    do_fix = "--fix" in args
    do_fix_spaces = "--fix-spaces" in args
    dry_run = "--dry-run" in args
    files = [Path(a) for a in args if not a.startswith("-")]

    if do_fix or do_fix_spaces:
        if not files:
            print("--fix / --fix-spaces 需要传文件路径", file=sys.stderr)
            sys.exit(1)
        total = 0
        for fp in files:
            if not fp.exists():
                continue
            n = fix_file(fp, dry_run=dry_run, punct=do_fix, spaces=do_fix_spaces)
            if n:
                print(f"  fixed {n} lines  {fp}", file=sys.stderr)
                total += n
        parts = []
        if do_fix:
            parts.append("strict 标点")
        if do_fix_spaces:
            parts.append("空格级（中英/中数/单位）")
        print(f"\n✅ 自动修复完成（{' + '.join(parts)}），{total} 行改动。", file=sys.stderr)
        return

    if use_stdin:
        text = sys.stdin.read()
        _report([("<stdin>", check_text(text, full=full))], strict=strict)
        return

    if not files:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    file_hits = [(str(fp), check_file(fp, full=full)) for fp in files if fp.exists()]
    _report(file_hits, strict=strict)


if __name__ == "__main__":
    main()
