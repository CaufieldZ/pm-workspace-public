#!/usr/bin/env python3
r"""
产出物「讲人话」自检 — 全 PM-WORKSPACE 唯一规则源（新）。

适用：deliverables/ 下对外产出物（leader / 业务 / 设计 / 研发读）
规则来源：.claude/runbooks/human-voice-rules.md「人读产出物讲人话铁律」

违禁词（strict 全部阻断）：
  1. 内部文件名：baseline.md / scene-list.md / SKILL.md / CLAUDE.md / pm-methodology.md / artifact-conventions.md
  2. 决策 / 章节锚点：决策 N / 第 N 章|节|条 / §X.Y（西文小节锚点）
  3. 场景编号裸引用：A-1 / B-2a / M-1 / D-1 / F-1（在正文段落里出现，需配白话名）
  4. 骨架锚点：PART A / PART 1 / PART B2（IMAP / 原型骨架内部编号外泄）
  5. 残留占位：[待补充*] / FIXME / TODO

免扫区域：
  - markdown 代码块 ``` ... ```
  - 行内代码 `xxx`
  - markdown 链接 / 图片：[text](url) / ![alt](path) 整体豁免（含 alt 与 text）
  - markdown 表格行（以 | 起的行）—— 场景编号在场景地图表是允许锚点
  - markdown 标题行（## / ###）—— 标题允许「编号 · 白话名」格式
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.banned_terms import (  # noqa: E402
    AI_FILLER_OPENING_RE,
    AI_SLOP_TAIL_RE,
    AI_SLOP_WARN_RE,
    BANNED_WARN_EXTRA,
    CHAPTER_RE,
    CIRCLED_DIGIT_RE,
    DECISION_RE,
    DEFENSIVE_TRIO_RE,
    FIXME_RE,
    INTERNAL_FILES_RE,
    PART_ANCHOR_RE,
    PLACEHOLDER_RE,
    PROMO_VERSION_RE,
    SCENE_ANCHOR_RE,
    TODO_RE,
    TRANSLATION_ESE_PATTERNS,
)
from lib.diagram_text import extract_scan_lines  # noqa: E402
from lib.json_out import emit  # noqa: E402
from lib.lint_exempt import EXEMPT_BASENAME, EXEMPT_PATHSEGMENT, is_lint_exempt  # noqa: E402
from lib.path_skip import is_skipped  # noqa: E402
from lib.thresholds import CHECKER_MAX_LINES  # noqa: E402

STRICT_PATTERNS = [
    (INTERNAL_FILES_RE, "内部文件名"),
    (DECISION_RE, "决策编号"),
    (CHAPTER_RE, "章节锚点"),
    (PART_ANCHOR_RE, "PART 骨架锚点"),
    (PLACEHOLDER_RE, "待补充占位"),
    (FIXME_RE, "FIXME 残留"),
    (TODO_RE, "TODO 残留"),
    (CIRCLED_DIGIT_RE, "圈数字禁用"),
    (AI_SLOP_TAIL_RE, "AI slop 词"),
    (AI_FILLER_OPENING_RE, "AI 空话起手"),
    (DEFENSIVE_TRIO_RE, "防御性三连拼写"),
]

# 软提醒（不阻断，仅 stderr 输出）
WARN_PATTERNS = [
    (AI_SLOP_WARN_RE, "AI slop 词（软提醒）"),
] + TRANSLATION_ESE_PATTERNS + BANNED_WARN_EXTRA

# 场景编号检测对 scene-list / imap 文件不生效（它们就是承载编号的载体）
SCENE_ANCHOR_PATTERN = (SCENE_ANCHOR_RE, "场景编号裸引用")
SCENE_ANCHOR_EXEMPT_GLOBS = ["scene-list-*.html", "scene-list-*.md", "imap-*.html"]

# ── 数据报告专属违禁（仅 deliverables/reports/weekly-* 路径生效）────────────
# 数据报告 AI 八股拦截：
#   1) 段尾"下周/建议/持续观察"等行动项模板（领导版全删，规则已禁但产出失守）
#   2) 段标题"X，但 Y"对仗（AI 句式套路）
#   3) 段标题拟人化（"人/用户/主播"作主语）
#   4) 段标题名词性单维度 + AI 词（XX 信号 / XX 典型模式 / XX 疲软）
# 规则源：.claude/skills/data-report/references/insight-writing-guide.md「禁用句式」段

ACTION_TAIL_RE = re.compile(
    r"(下周(?:建议|关注|观察|跟进|继续|补|看)|"
    r"建议(?:拆解|跟进|补|关注|追踪)|"
    r"(?:需|待)(?:关注|补充|追踪|观察)|"
    r"持续(?:观察|跟进|追踪))"
)

TITLE_DUEI_RE = re.compile(
    r"^#{2,4}\s+\d+\.\s+[^，#]+，但[^#]+$"
)

TITLE_PERSONIFY_RE = re.compile(
    r"^#{2,4}\s+\d+\.\s+(?:人|用户|主播|观众|创作者|粉丝)"
    r"(?:少了|多了|跑了|走了|更少了|更多了|不爱|不玩|没兴趣|累了|疲了)\s*$"
)

TITLE_AI_NOUN_RE = re.compile(
    r"^#{2,4}\s+\d+\.\s+.+(?:信号|典型模式|疲软|端有.{0,10}信号)\s*$"
)

WEEKLY_PATTERNS = [
    (ACTION_TAIL_RE, "数据报告禁段尾下周/建议"),
    (TITLE_DUEI_RE, "段标题对仗式「X，但 Y」"),
    (TITLE_PERSONIFY_RE, "段标题拟人化"),
    (TITLE_AI_NOUN_RE, "段标题名词性 AI 词"),
]


def _is_weekly_report(path: Path) -> bool:
    """判定是否数据周报（路径含 weekly- 且文件名匹配 *-weekly-*.md）。"""
    if not path.suffix.lower() == ".md":
        return False
    if "weekly-" not in str(path):
        return False
    # 文件名形如 community-weekly-0508.md / live-weekly-0508.md
    return bool(re.search(r"-weekly-\d{4}\.md$", path.name))


def _is_promo(path: Path) -> bool:
    """判定是否营销/宣发稿（promo- 前缀 md）。

    营销语境：AI_SLOP_TAIL（全新升级 / 焕新等）从 strict 降 warn，
    但新增 PROMO_VERSION_RE（内部迭代版本号）strict 拦。
    """
    return path.suffix.lower() == ".md" and path.name.startswith("promo-")

# ── 免扫剥离 ─────────────────────────────────────────────────

# markdown 链接 [text](url) 仅剥 URL（text 保留扫描）
MD_LINK_RE = re.compile(r"(\[[^\]\n]+\])\(([^)\n]+)\)")
# markdown 行内代码 `xxx`
MD_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
# HTML <code> / <pre> 标签块（含内容）
HTML_CODE_RE = re.compile(r"<(code|pre)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
# 裸 URL
URL_RE = re.compile(r"https?://[^\s)）」』】>\"']+")

# ── 跳过的文件 / 目录 → lib.path_skip ───────────────────────

MAX_LINES = CHECKER_MAX_LINES

# ── 豁免文件名 glob → lib.lint_exempt（bash 侧 guards.sh 共读同一份规则表）──

DEFAULT_EXEMPTIONS_BASENAME = EXEMPT_BASENAME
DEFAULT_EXEMPTIONS_PATHSEGMENT = EXEMPT_PATHSEGMENT

is_exempted = is_lint_exempt


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


def _scan_lines(lines: list[str], patterns: list = None) -> list[tuple[int, str, str, str]]:
    """返回 [(lineno, category, matched_text, excerpt), ...]
    patterns: 可选，默认用 STRICT_PATTERNS。数据周报会传 STRICT_PATTERNS + WEEKLY_PATTERNS。
    """
    if patterns is None:
        patterns = STRICT_PATTERNS

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

        # markdown 标题行豁免：
        #  - ACTION_TAIL_RE（段尾行动项规则只针对正文段落，模板固定章节标题如「## 洞察 & 下周关注」豁免）
        #  - 场景编号裸引用（标题允许「编号 · 白话名」格式，如「### 2.1 A-4 · 推荐卡露出」，见本文件 docstring 标题豁免）
        is_md_heading = bool(re.match(r"^\s{0,3}#{1,6}\s", raw_line))
        HEADING_EXEMPT = {"数据报告禁段尾下周/建议", "场景编号裸引用"}
        # 表格行：场景地图表（§2.0 索引 / 反向合并指引等）的「编号」列就是合法锚点，
        # 编号配同行白话名 = check_prd_md.sh 认可的「编号 + 白话名」形态（跨列等价）。
        is_md_table_row = bool(re.match(r"^\s{0,3}\|", raw_line))
        TABLE_EXEMPT = {"场景编号裸引用"}

        for pat, category in patterns:
            if is_md_heading and category in HEADING_EXEMPT:
                continue
            if is_md_table_row and category in TABLE_EXEMPT:
                continue
            for m in pat.finditer(line):
                matched = raw_line[m.start():m.end()] \
                    if m.end() <= len(raw_line) else m.group()
                excerpt = raw_line.strip()[:120]
                hits.append((i, category, matched, excerpt))
    return hits


def check_file(path: Path) -> tuple[list, list]:
    """返回 (strict_hits, warn_hits) 两个列表。"""
    if is_skipped(path):
        return [], []
    if is_exempted(path):
        return [], []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], []
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        return [], []
    # .drawio / .mmd 只扫 label 文本（跳过 XML / mermaid 语法噪音），行号回原文件
    diag = extract_scan_lines(path.suffix, lines)
    if diag is not None:
        lines = diag

    # 数据周报追加 WEEKLY_PATTERNS（段尾"下周/建议" + 标题禁句式）
    patterns = list(STRICT_PATTERNS)
    if _is_weekly_report(path):
        patterns = patterns + WEEKLY_PATTERNS
    # 场景编号检测：scene-list / imap 类承载锚点，豁免
    name = path.name
    is_anchor_carrier = any(Path(name).match(g) for g in SCENE_ANCHOR_EXEMPT_GLOBS)
    if not is_anchor_carrier:
        patterns = patterns + [SCENE_ANCHOR_PATTERN]
    warn_patterns = WARN_PATTERNS
    # 营销稿语境分流：AI slop 收尾词降 warn（营销语境合法），改拦内部版本号
    if _is_promo(path):
        patterns = [p for p in patterns if p[0] is not AI_SLOP_TAIL_RE]
        patterns = patterns + [(PROMO_VERSION_RE, "内部版本号外泄")]
        warn_patterns = warn_patterns + [(AI_SLOP_TAIL_RE, "AI slop 词（营销语境软提醒）")]
    strict_hits = _scan_lines(lines, patterns)
    warn_hits = _scan_lines(lines, warn_patterns)
    return strict_hits, warn_hits


# 修法指引：按命中 category 前缀分族，只输出实际命中的族（对症，不一刀切）
_FIX_HINTS = [
    (("内部文件名", "决策编号", "章节锚点", "PART 骨架锚点", "场景编号裸引用",
      "待补充占位", "FIXME 残留", "TODO 残留", "圈数字禁用", "防御性三连拼写"),
     "内部锚点 → 改成业务白话（A-1 → 「下注弹层」，决策 7 → 删引用）；脚本化产物改源后重 build"),
    (("AI slop", "AI 空话起手", "过渡废话", "自媒体腔"),
     "AI 套话 → 删空壳抬句，把抽象动词换成可验证的具体动作：\n"
     "   「显著提升稳定性」→「峰值 CPU 从 85% 降至 40%」\n"
     "   「无缝对接」→「A 调用 B 的 /api/xxx，透传 user_id 字段」\n"
     "   「体验升级」→「首屏加载从 3.2s 降至 1.1s（P90）」\n"
     "   「深度融合」→「A 的数据实时写入 B 的展示模块，刷新频率 T+1」"),
    (("无源引用",),
     "无源引用 → 给具体数据 / 来源，或删权威铺垫，别补虚构出处"),
    (("翻译腔",),
     "翻译腔 → 缩短主语和动作，少用长定语链 / 被动 / 「基于…」「通过…来…」"),
]


def _fix_hints(categories: set) -> list:
    """命中 category 集合 → 对症修法行（保序，去重）。"""
    out = []
    for keys, hint in _FIX_HINTS:
        if any(cat.startswith(k) for cat in categories for k in keys):
            out.append(hint)
    return out


def _report(file_hits: list[tuple[str, list, list]], strict: bool) -> None:
    """file_hits: [(label, strict_hits, warn_hits), ...]
    strict_hits 计入退出码；warn_hits 只输出不阻断。
    """
    strict_total = 0
    warn_total = 0
    for label, strict_hits, warn_hits in file_hits:
        if strict_hits:
            strict_total += len(strict_hits)
            print(f"\n{label} — 命中 {len(strict_hits)} 处", file=sys.stderr)
            for lineno, category, matched, excerpt in strict_hits[:20]:
                print(f"  ❌ L{lineno} [{category}] 匹配：{matched!r}", file=sys.stderr)
                print(f"     {excerpt}", file=sys.stderr)
            if len(strict_hits) > 20:
                print(f"  ... （共 {len(strict_hits)} 处，仅显示前 20）", file=sys.stderr)
        if warn_hits:
            warn_total += len(warn_hits)
            print(f"\n{label} — 软提醒 {len(warn_hits)} 处", file=sys.stderr)
            for lineno, category, matched, excerpt in warn_hits[:10]:
                print(f"  ⚠️  L{lineno} [{category}] 匹配：{matched!r}", file=sys.stderr)
                print(f"     {excerpt}", file=sys.stderr)
            if len(warn_hits) > 10:
                print(f"  ... （共 {len(warn_hits)} 处，仅显示前 10）", file=sys.stderr)

    seen_categories = {h[1] for _, sh, wh in file_hits for h in sh + wh}
    hints = _fix_hints(seen_categories)

    if strict_total:
        print("", file=sys.stderr)
        print("❌ 违反「人读产出物讲人话」规则。读者是 leader / 业务，看不懂内部代号 / AI 套话。",
              file=sys.stderr)
        for h in hints:
            print(f"   修法：{h}", file=sys.stderr)
        print("   临时绕过：SKIP_PLAIN_LANGUAGE_GATE=1", file=sys.stderr)
    elif warn_total and hints:
        # 仅 warn（不阻断）：给对症改写方向，PM 自行斟酌
        print("", file=sys.stderr)
        print("⚠️  以上为软提醒（不阻断），改写方向：", file=sys.stderr)
        for h in hints:
            print(f"   · {h}", file=sys.stderr)

    if strict_total == 0:
        # 仅有软提醒（或全无）不阻断
        sys.exit(0)
    sys.exit(2 if strict else 1)


def main():
    args = sys.argv[1:]
    strict = "--strict" in args
    use_stdin = "--stdin" in args
    json_out = None
    skip_idx = set()
    if "--json-out" in args:
        i = args.index("--json-out")
        json_out = args[i + 1] if i + 1 < len(args) else None
        skip_idx.add(i + 1)  # 输出路径不是待检文件（否则二次运行会扫自己上次的输出）
    files = [Path(a) for i, a in enumerate(args)
             if not a.startswith("-") and i not in skip_idx]

    if use_stdin:
        content = sys.stdin.read()
        lines = content.splitlines()
        strict_hits = _scan_lines(lines)
        warn_hits = _scan_lines(lines, WARN_PATTERNS)
        emit(json_out, "plain-language", [h[:3] for h in strict_hits + warn_hits])
        _report([("<stdin>", strict_hits, warn_hits)], strict)
        return

    if not files:
        print("用法: check_plain_language.py <file>... [--strict] [--stdin] [--json-out <path|->]",
              file=sys.stderr)
        sys.exit(0)

    file_hits = []
    collected = []
    for f in files:
        if not f.exists():
            continue
        strict_hits, warn_hits = check_file(f)
        file_hits.append((str(f), strict_hits, warn_hits))
        collected += [h[:3] for h in strict_hits + warn_hits]

    emit(json_out, "plain-language", collected)
    _report(file_hits, strict)


if __name__ == "__main__":
    main()
