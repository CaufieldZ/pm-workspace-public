#!/usr/bin/env python3
"""bullet / 段落挤话检测（AI 味「挤话一团」维度）。

四条判定（任一命中即挤话，优先级按序）：
  1. bullet 行中文句号 。≥ period_limit（默认 3）→ 一行塞多件独立事。
     只管 bullet：段落用同一把尺子会拦下「三句完整短句」这种正常散文，反过来教人
     把三件事用逗号焊成一句绕检测——所以段落改由下面两条判。
  2. 分号 ；/ ; ≥ semicolon_limit（默认 2）→ 分号串多子句，该拆嵌套 bullet
     （父行只留「标签：」冒号收尾 + 全部子句平级降为子 bullet；父行别留正文，
     「父行留一句 + 剩下降级」是非对称错法），不是合法豁免。
  3. 单句 ≥ long_sentence_chars（默认 100）→ 长句 run-on，拆成几句短句用句号断开。
  4. 段落句数 ≥ fragment_min_sentences 且句长中位数 < fragment_median_chars
     → 碎句（一顿一顿的短句堆成段），连成完整的话或改列表。
换标点绕检测（分号改逗号 / 顿号焊多件独立事）检测器数不到逗号、误伤高，靠 SKILL 行为规则兜。

跳过：> 引用 / | 表格 / # 标题 / ``` 代码块 / ::: 容器 / frontmatter / 空行 / 纯图片。
  表格行豁免关键——cell 内 ; 是 md_to_confluence 切 <li> 的约定分隔符。
章节豁免只给「长句」这一维：决策 / 变更 / 埋点章的论证叙事（`方案。理由。阻塞。`）一句
  本就长，硬砍割裂推理。句号 / 分号 / 碎句不给整章开口子——3 句焊一行、碎成一顿一顿，
  哪章都该拆，拆成「标签：」+ 子 bullet 反而更好读。
行级逃生口：行尾 <!-- lint-skip:density -->（归因口径 / 合法长枚举等极少数）。

hook 走 --added-file <path>（diff-based：只报本次新增/修改行，存量不卡）；人手跑传文件路径全文扫。

用法：
    python3 scripts/check_bullet_density.py projects/<产品线>/scene-list.md
    python3 scripts/check_bullet_density.py projects/<产品线>/prd-<产品线>-baseline.md --strict
    python3 scripts/check_bullet_density.py projects/<产品线>/scene-list.md --json-out -
    ADDED=$(mktemp); git diff -U0 HEAD -- projects/<产品线>/scene-list.md \
      | grep '^+' | grep -v '^+++' | sed 's/^+//' > "$ADDED"
    python3 scripts/check_bullet_density.py projects/<产品线>/scene-list.md --added-file "$ADDED" --strict

参数：
    <file>...            要扫的 md 文件（可多个；promo- 前缀营销稿豁免不扫）
    --strict             有违规 exit 2（hook 阻断用）
    --json-out <path|->  命中明细写 JSON（- 走 stdout）
    --added-file <path>  diff-based：「本次新增/修改行」清单（一行一条行文本），
                         只报命中该集合的行，存量行不报（hook 传 git diff 抠出的 + 行）

前置：无（纯本地文件扫描；--help 本身不需要）。

退出码：
    0 — clean / warn（未传 --strict）
    2 — 传 --strict 且有违规（hook 用）

hook：.claude/hooks/lib/post-checks.sh pc_bullet_density（block）。
规则：.claude/runbooks/human-voice-rules.md ⑥。
阈值：scripts/lib/thresholds.yaml bullet_density.{period_limit, semicolon_limit,
      long_sentence_chars, fragment_min_sentences, fragment_median_chars}。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.json_out import emit  # noqa: E402
from lib.thresholds import T  # noqa: E402

# 挤话治理 SSOT——计数原语与 humanize/patterns.py 共用（避免副本漂移）。
# 与 md_scan WARN 层同一口径：is_exempt_chapter 只作用于「长句」这一维。
_HUMANIZE = Path(__file__).resolve().parent.parent / ".claude/skills/prd/scripts/humanize"
sys.path.insert(0, str(_HUMANIZE.parent))
from humanize.patterns import (  # noqa: E402
    count_periods,
    count_semicolons,
    is_exempt_chapter,
    median_sentence_len,
    sentence_lengths,
)

PERIOD_LIMIT: int = int(T.get("bullet_density", {}).get("period_limit", 3))
SEMICOLON_LIMIT: int = int(T.get("bullet_density", {}).get("semicolon_limit", 2))
LONG_SENTENCE_CHARS: int = int(T.get("bullet_density", {}).get("long_sentence_chars", 100))
FRAGMENT_MIN_SENTENCES: int = int(T.get("bullet_density", {}).get("fragment_min_sentences", 3))
FRAGMENT_MEDIAN_CHARS: int = int(T.get("bullet_density", {}).get("fragment_median_chars", 9))

BLOCKQUOTE_RE = re.compile(r"^\s*>")
TABLE_RE = re.compile(r"^\s*\|")
HEADING_ANY_RE = re.compile(r"^#{1,6}\s")
CONTAINER_RE = re.compile(r"^:::")
IMAGE_ONLY_RE = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s")
CODE_FENCE_RE = re.compile(r"^\s*```")
FRONTMATTER_DELIM_RE = re.compile(r"^---\s*$")
SKIP_MARKER_RE = re.compile(r"<!--\s*lint-skip:density\s*-->")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def check_text(text: str, only_line_texts: set[str] | None = None
               ) -> list[tuple[int, str, int, str]]:
    """全文扫描，返回 [(lineno, kind, cnt, excerpt), ...]。

    kind ∈ {bullet, 段落} 后缀 {·分号, ·长句, ·碎句}；cnt = 该类判据的计数
    （句号数 / 分号数 / 最长句字数 / 句数）。四条判据任一命中即报，优先级按此序：
    ① bullet 句号 ≥3 ② 分号 ≥2 ③ 单句 ≥100 字 ④ 段落碎句。

    章节 / 代码块 / frontmatter 状态机需要完整上下文，故始终吃全文。
    章节豁免只给「长句」这一维（决策 / 变更 / 埋点章的论证句本就长）；句号 / 分号 /
    碎句一视同仁——决策章 3 句焊一行、碎成一顿一顿的，哪章都该拆。
    only_line_texts 非空时（diff-based）：只报文本命中该集合的行，存量行不报。
    """
    lines = text.splitlines()
    hits: list[tuple[int, str, int, str]] = []
    in_code = False     # ``` 代码块
    in_frontmatter = False
    h1 = h2 = ""        # 当前一级 / 二级标题（只给长句维用）

    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip()

        # frontmatter 状态机（仅首行 --- 激活）
        if i == 1 and FRONTMATTER_DELIM_RE.match(line):
            in_frontmatter = True
            continue
        if in_frontmatter:
            if FRONTMATTER_DELIM_RE.match(line):
                in_frontmatter = False
            continue

        # 代码块开关
        if CODE_FENCE_RE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue

        # 标题状态机（长句豁免按 H1 / H2 判）
        m_head = HEADING_RE.match(line)
        if m_head:
            if len(m_head.group(1)) == 1:
                h1, h2 = m_head.group(2), ""
            else:
                h2 = m_head.group(2)
            continue

        # 行级跳过：非内容 / 已知误报源
        if not line.strip():
            continue
        if BLOCKQUOTE_RE.match(line) or TABLE_RE.match(line):
            continue
        if CONTAINER_RE.match(line):
            continue
        if IMAGE_ONLY_RE.match(line):
            continue
        if SKIP_MARKER_RE.search(line):
            continue

        # diff-based：只报本次新增/修改行，存量行跳过
        if only_line_texts is not None and line.strip() not in only_line_texts:
            continue

        periods = count_periods(line)
        semis = count_semicolons(line)
        is_bullet = bool(BULLET_RE.match(line))
        kind = "bullet" if is_bullet else "段落"
        lens = sentence_lengths(line)
        longest = max(lens) if lens else 0
        excerpt = line.strip()[:120]

        if is_bullet and periods >= PERIOD_LIMIT:
            hits.append((i, kind, periods, excerpt))
        elif semis >= SEMICOLON_LIMIT:
            # 分号串：A；B；C 列举焊一行该拆嵌套 bullet
            hits.append((i, f"{kind}·分号", semis, excerpt))
        elif longest >= LONG_SENTENCE_CHARS and not (is_exempt_chapter(h1) or is_exempt_chapter(h2)):
            hits.append((i, f"{kind}·长句", longest, excerpt))
        elif not is_bullet and len(lens) >= FRAGMENT_MIN_SENTENCES \
                and median_sentence_len(line, quote_mode="fill") < FRAGMENT_MEDIAN_CHARS:
            hits.append((i, f"{kind}·碎句", len(lens), excerpt))

    return hits


def check_file(path: Path, only_line_texts: set[str] | None = None
               ) -> list[tuple[int, str, int, str]]:
    # 营销稿（promo-）豁免：营销散文要连贯成段，拆 bullet 反而丢节奏。
    # 该 gate 为 PRD / 结构化产物设计，对营销文案是系统性误报。
    if path.name.startswith("promo-"):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return []
    return check_text(text, only_line_texts)


def report(hits: list[tuple[int, str, int, str]], rel: str) -> None:
    by_kind: dict[str, int] = {}
    for _ln, kind, _c, _e in hits:
        by_kind[kind] = by_kind.get(kind, 0) + 1
    summary = " / ".join(f"{k} {v}" for k, v in by_kind.items())
    print(f"\n🚫 [bullet-density] {rel} — {len(hits)} 处挤话（{summary}；bullet 句号 ≥{PERIOD_LIMIT} / "
          f"分号 ≥{SEMICOLON_LIMIT} / 单句 ≥{LONG_SENTENCE_CHARS} 字 / 段落碎句）", file=sys.stderr)
    for lineno, kind, cnt, excerpt in hits[:20]:
        print(f"  L{lineno} [{kind}·{cnt}] {excerpt}", file=sys.stderr)
    if len(hits) > 20:
        print(f"  ... 共 {len(hits)} 处，仅显示前 20", file=sys.stderr)
    print(file=sys.stderr)
    print("   → 分号串：拆嵌套 bullet——父行只留「标签：」冒号收尾，全部子句平级降为子 bullet（父行别留任何一句正文；「父行留一句 + 剩下降级」是非对称错法）", file=sys.stderr)
    print("   → bullet 句号 ≥3：一行塞多件独立事，拆多条 bullet 或砍成一句概述", file=sys.stderr)
    print(f"   → 长句·单句 ≥{LONG_SENTENCE_CHARS} 字：拆成几句短句，用句号断开——别换成逗号（换标点只骗过检测，认知负荷更高）", file=sys.stderr)
    print("     改前: 机器人按固定节奏刷屏，配置默认值全是 0、开关默认关，运营每场手动配，按语种分不了文案", file=sys.stderr)
    print("     改后: 机器人按固定节奏刷屏。配置默认值全是 0、开关默认关，运营每场手动配。文案按语种分不了", file=sys.stderr)
    print(f"   → 碎句·三句以上且句子普遍很短（<{FRAGMENT_MEDIAN_CHARS} 字）：连成完整的话，或改成列表", file=sys.stderr)
    print("     改前: **背景**：补丁包。表单缺校验。推流加白锁死。假重开。", file=sys.stderr)
    print("     改后: **背景**：补丁包三处修复——表单缺校验、推流加白锁死、直播结束后假重开。", file=sys.stderr)
    print("   → 拆成哪种列表看语义：有先后 / 步骤 / 优先级 / 正文要回指编号 → 有序 1. 2. 3.；并列无序（字段枚举 / 平级规则 / 取舍点）→ 无序 -。别为「不单调」滥用编号（给读者假的顺序信号，比单调更糟）", file=sys.stderr)
    print("   → 别把分号换成逗号 / 顿号焊同一行——那是绕检测不是精简，认知负荷更高", file=sys.stderr)
    print("   → 表格 cell 内 ; 是渲染分隔符（本就豁免）；归因口径 / 合法枚举：行尾加 <!-- lint-skip:density -->", file=sys.stderr)
    print("   → 临时绕过：SKIP_BULLET_DENSITY_GATE=1", file=sys.stderr)


def _opt_val(args: list[str], name: str) -> str | None:
    if name in args:
        i = args.index(name)
        return args[i + 1] if i + 1 < len(args) else None
    return None


def main() -> int:
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__, end="")
        return 0
    strict = "--strict" in args
    json_out = _opt_val(args, "--json-out")

    # --added-file <path>：diff-based，只报文本命中该文件所列行的命中（存量不报）
    added_path = _opt_val(args, "--added-file")
    only_line_texts: set[str] | None = None
    if added_path:
        try:
            only_line_texts = {
                ln.strip() for ln in Path(added_path).read_text(
                    encoding="utf-8", errors="replace").splitlines() if ln.strip()
            }
        except OSError:
            # fail-open 保护：--added-file 读不到时静默空集 = 所有行都跳过 = 恒通过
            print(f"⚠️  --added-file 无法读取: {added_path}（本次按全文扫描，非 diff）", file=sys.stderr)
            only_line_texts = None

    skip_next = {json_out, added_path}
    files = [Path(a) for a in args
             if not a.startswith("-") and a not in skip_next]

    if not files:
        print("未传要扫的文件。用法见 python3 scripts/check_bullet_density.py --help", file=sys.stderr)
        return 1

    file_hits: list[tuple[Path, list]] = []
    for fp in files:
        if not fp.exists():
            continue
        hits = check_file(fp, only_line_texts)
        if hits:
            file_hits.append((fp, hits))

    emit(json_out, "bullet-density",
         [(ln, kind, excerpt) for _fp, hits in file_hits
          for (ln, kind, _cnt, excerpt) in hits])

    for fp, hits in file_hits:
        report(hits, fp.name)

    return 2 if (strict and file_hits) else 0


if __name__ == "__main__":
    sys.exit(main())
