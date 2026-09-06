#!/usr/bin/env python3
"""bullet / 段落挤话检测（AI 味「挤话一团」维度）。

两条判定（任一命中即挤话）：
  1. 中文句号 。≥ period_limit（默认 3）→ 一行塞多件独立事。
  2. 分号 ；/ ; ≥ semicolon_limit（默认 2）→ 分号串多子句，该拆嵌套 bullet
     （父行只留「标签：」冒号收尾 + 全部子句平级降为子 bullet；父行别留正文，
     「父行留一句 + 剩下降级」是非对称错法），不是合法豁免。
换标点绕检测（分号改逗号 / 顿号焊多件独立事）检测器数不到逗号、误伤高，靠 SKILL 行为规则兜。

跳过：> 引用 / | 表格 / # 标题 / ``` 代码块 / ::: 容器 / frontmatter / 空行 / 纯图片。
  表格行豁免关键——cell 内 ; 是 md_to_confluence 切 <li> 的约定分隔符。
无章节豁免：决策 / 变更 / 埋点章也配写好看——3 句焊一行、分号串列举，哪章都是挤话该拆，
  拆成「标签：」+ 子 bullet 反而更好读。决策章唯一的不同（论证句可以长）只在 WARN 层放过，
  block 不给整章开口子（论证段本就该 2 句号内、分号 <2，自然过）。
行级逃生口：行尾 <!-- lint-skip:density -->（归因口径 / 合法长枚举等极少数）。

hook 走 --stdin（diff-based：只喂本次新增/修改行，存量不卡）；人手跑传文件路径全文扫。

用法：
    python3 scripts/check_bullet_density.py <prd-*.md>... [--strict] [--json-out <path|->]
    git diff -U0 HEAD -- f.md | ...取 added... | python3 scripts/check_bullet_density.py --stdin [--strict]

退出码：
    0 — clean / warn（未传 --strict）
    2 — 传 --strict 且有违规（hook 用）

hook：.claude/hooks/lib/post-checks.sh pc_bullet_density（block）。
规则：.claude/runbooks/human-voice-rules.md ⑥。
阈值：scripts/lib/thresholds.yaml bullet_density.period_limit。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.json_out import emit  # noqa: E402
from lib.thresholds import T  # noqa: E402

# 挤话治理 SSOT——计数原语与 humanize/patterns.py 共用（避免副本漂移）。
# block 不用 is_exempt_chapter：章节豁免只在 WARN 层给「长句可以长」开口子，block 一视同仁。
_HUMANIZE = Path(__file__).resolve().parent.parent / ".claude/skills/prd/scripts/humanize"
sys.path.insert(0, str(_HUMANIZE.parent))
from humanize.patterns import count_periods, count_semicolons  # noqa: E402

PERIOD_LIMIT: int = int(T.get("bullet_density", {}).get("period_limit", 3))
SEMICOLON_LIMIT: int = int(T.get("bullet_density", {}).get("semicolon_limit", 2))

BLOCKQUOTE_RE = re.compile(r"^\s*>")
TABLE_RE = re.compile(r"^\s*\|")
HEADING_ANY_RE = re.compile(r"^#{1,6}\s")
CONTAINER_RE = re.compile(r"^:::")
IMAGE_ONLY_RE = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s")
CODE_FENCE_RE = re.compile(r"^\s*```")
FRONTMATTER_DELIM_RE = re.compile(r"^---\s*$")
SKIP_MARKER_RE = re.compile(r"<!--\s*lint-skip:density\s*-->")


def check_text(text: str, only_line_texts: set[str] | None = None
               ) -> list[tuple[int, str, int, str]]:
    """全文扫描，返回 [(lineno, kind, cnt, excerpt), ...]，kind ∈ {bullet, 段落, ...·分号}。

    章节 / 代码块 / frontmatter 状态机需要完整上下文，故始终吃全文。
    only_line_texts 非空时（diff-based）：只报文本命中该集合的行，存量行不报。
    """
    lines = text.splitlines()
    hits: list[tuple[int, str, int, str]] = []
    in_code = False     # ``` 代码块
    in_frontmatter = False

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

        # 行级跳过：非内容 / 已知误报源（无章节豁免——决策 / 埋点章一视同仁）
        if not line.strip():
            continue
        if BLOCKQUOTE_RE.match(line) or TABLE_RE.match(line):
            continue
        if HEADING_ANY_RE.match(line) or CONTAINER_RE.match(line):
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
        kind = "bullet" if BULLET_RE.match(line) else "段落"
        if periods >= PERIOD_LIMIT:
            hits.append((i, kind, periods, line.strip()[:120]))
        elif semis >= SEMICOLON_LIMIT:
            # 分号串：A；B；C 列举焊一行该拆嵌套 bullet
            hits.append((i, f"{kind}·分号", semis, line.strip()[:120]))

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
    print(f"\n🚫 [bullet-density] {rel} — {len(hits)} 处挤话（{summary}；句号 ≥{PERIOD_LIMIT} 或 分号 ≥{SEMICOLON_LIMIT}）",
          file=sys.stderr)
    for lineno, kind, cnt, excerpt in hits[:20]:
        print(f"  L{lineno} [{kind}·{cnt}] {excerpt}", file=sys.stderr)
    if len(hits) > 20:
        print(f"  ... 共 {len(hits)} 处，仅显示前 20", file=sys.stderr)
    print(file=sys.stderr)
    print("   → 分号串：拆嵌套 bullet——父行只留「标签：」冒号收尾，全部子句平级降为子 bullet（父行别留任何一句正文；「父行留一句 + 剩下降级」是非对称错法）", file=sys.stderr)
    print("   → 句号 ≥3：一行塞多件独立事，拆多条 bullet 或砍成一句概述", file=sys.stderr)
    print("   → 拆成哪种列表看语义：有先后 / 步骤 / 优先级 / 正文要回指编号 → 有序 1. 2. 3.；并列无序（字段枚举 / 平级规则 / 取舍点）→ 无序 -。别为「不单调」滥用编号（给读者假的顺序信号，比单调更糟）", file=sys.stderr)
    print("   → 别把分号换成逗号 / 顿号焊同一行——那是绕检测不是精简，认知负荷更高", file=sys.stderr)
    print("   → 表格 cell 内 ; 是渲染分隔符（本就豁免）；归因口径 / 合法枚举：行尾加 <!-- lint-skip:density -->", file=sys.stderr)
    print("   → 临时绕过：SKIP_BULLET_DENSITY_GATE=1", file=sys.stderr)


def _opt_val(args: list[str], name: str) -> str | None:
    if name in args:
        i = args.index(name)
        return args[i + 1] if i + 1 < len(args) else None
    return None


USAGE = ("usage: check_bullet_density.py <prd-*.md>... "
         "[--strict] [--json-out <path|->] [--added-file <path>]")


def main() -> int:
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(USAGE)
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
        print(USAGE, file=sys.stderr)
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
