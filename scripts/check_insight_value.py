#!/usr/bin/env python3
"""周报洞察内容门：抓「把明细表翻译成中文句子」的复读和跨口径相除。

周报的其他门（check_plain_language / check_bullet_density）全是负向的——只管
「不许说什么」。唯一两条内容规则（每句都是表外增量 / 跨期对比给了）写在
insight-writing-guide.md 的必检清单里靠人肉自查，于是新指标进表那周的洞察
常写成「上麦 14 人次、8 个场次、人均在麦 42 分钟」这种三个数全在表里的复读。

本脚本只认同时含「## 洞察」和「## 数据明细」两节的文件（即周报 md），
其余文件直接返回 0，不必挑路径。

用法：
    python3 scripts/check_insight_value.py <周报.md>... [--strict]
    cat live-weekly-0918.md | python3 scripts/check_insight_value.py --stdin

前置：无（只读本地文件）。

退出码：
    0 — clean，或有命中但未传 --strict（默认 warn 不阻断）
    2 — 传 --strict 且有命中
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# 一条 bullet 里有这么多个数字能在明细表里原样查到，就按复读处理。
# 取 2 而不是「全部」：复读句往往混一个表外的数（「8 个场次」不在表里），
# 要求全部命中会让最典型的复读逃掉。
VERBATIM_LIMIT = 2

# 跨期 / 跨行推导词。出现任一个就说明这句在做表给不了的事，不算复读。
# 「环比」不在此列——环比本身就是表里的一列，写出来不构成增量。
DERIVE_RE = re.compile(
    r"倍|占比|占|相比|对比|连续|周最高|周最低|周新高|周新低|新高|新低|"
    r"数量级|Q2|Q3|季度|基线|pt|翻|腰斩|不成比例|按比例|"
    r"[一二三四五六七八九十两]+\s*周"  # 「八周里四周落在」这类跨周形态用的是中文数字
)

# 数字 token：1,234 / 40.1 / 71.6% / 0.93 —— 逗号在归一时去掉
NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")

# 脚注上标（`发帖渗透率 ^1`）不是数据，扫表时先剥掉——否则 ^8 会让洞察里
# 任何一个「8」都算成「表里原样可查」，制造巧合命中。
FOOTNOTE_RE = re.compile(r"\^\d+")

# 同一条 bullet 里同时出现配对双方 + 运算词 = 跨口径相除。
# 两边口径不同（周去重 vs 日均 / 人数 vs 人次 / 行为分析平台 vs 有数），比值无意义。
FORBIDDEN_PAIRS: list[tuple[tuple[str, ...], tuple[str, ...], str]] = [
    # 只禁「行为分析平台举手 UV ÷ 有数上麦人次」这一种：两个数据源、人数 vs 人次。
    # 有数连麦表**内部**的「举手人数 → 连麦人数」同源同口径（BI 自带「举手上麦
    # 转化率」列），那是本周最有价值的一条洞察，不能连带挡掉——所以锚行为分析平台那侧的
    # 行名「举手申请人数」，不用裸词「举手」。
    (("举手申请人数",), ("上麦人次", "上了麦"),
     "举手申请人数是行为分析平台周去重人数、上麦人次是有数人次，两侧不同源不可相除"),
    (("直播卡曝光", "卡曝光"), ("Feed DAU", "日活"), "周去重 UV ÷ 日均 DAU"),
    (("直播渗透率", "App 观众端"), ("日均观看人数",), "行为分析平台日去重 UV ÷ 有数跨场人次"),
    (("发帖量",), ("发帖渗透率",), "绝对量 ÷ 漏斗转化率，分母不同源"),
]

# 相除 / 取比的表述
RATIO_RE = re.compile(r"倍|占|转化率|覆盖率|渗透到|除以|／|/|%的")


def _norm_nums(text: str) -> set[str]:
    return {m.group(0).replace(",", "") for m in NUM_RE.finditer(text)}


def _section(text: str, title: str) -> str:
    """取 `## {title}` 到下一个 `## ` 之间的正文（洞察标题可能带后缀）。"""
    m = re.search(rf"##\s*{title}.*?\n(.+?)(?=\n## |\Z)", text, re.DOTALL)
    return m.group(1) if m else ""


def table_numbers(text: str) -> set[str]:
    """明细表数据单元格里的数字 token（归一去逗号）。

    跳表头行（列标题是 09.05~09.11 这类周区间，不是指标值）、剥脚注上标。
    个位数不计——「0」「1」满表都是，算进去会把任意一句话判成复读。
    """
    nums: set[str] = set()
    for line in _section(text, "数据明细").splitlines():
        if not line.startswith("|") or "---" in line or "| 分类 |" in line:
            continue
        nums |= _norm_nums(FOOTNOTE_RE.sub("", line))
    return {n for n in nums if len(n) > 1}


def insight_lines(text: str) -> list[tuple[int, str]]:
    """洞察段里承载判断的行（bullet + 编号小标题 + 普通段落），剥 HTML 注释。"""
    body = _section(re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL), "洞察")
    offset = text.split("## 洞察")[0].count("\n") if "## 洞察" in text else 0
    out = []
    for i, raw in enumerate(body.splitlines(), start=offset + 1):
        line = raw.strip()
        if not line or line.startswith(("|", ">", "```")):
            continue
        out.append((i, line))
    return out


def check_text(text: str) -> list[tuple[int, str, str, str]]:
    """返回 [(行号, 类别, 说明, 原文), ...]。非周报 md（缺任一节）返回空。"""
    if "## 洞察" not in text or "## 数据明细" not in text:
        return []

    tbl = table_numbers(text)
    hits: list[tuple[int, str, str, str]] = []

    for lineno, line in insight_lines(text):
        body = re.sub(r"^#{1,6}\s*\d*\.?\s*|^[-*]\s+", "", line)

        for a_terms, b_terms, why in FORBIDDEN_PAIRS:
            if (any(a in body for a in a_terms) and any(b in body for b in b_terms)
                    and RATIO_RE.search(body)):
                hits.append((lineno, "跨口径相除", why, line))
                break

        nums = _norm_nums(body)
        if not nums or DERIVE_RE.search(body):
            continue
        verbatim = nums & tbl
        if len(verbatim) >= VERBATIM_LIMIT:
            hits.append((
                lineno, "表格复读",
                f"{len(verbatim)} 个数在明细表里原样可查（{'、'.join(sorted(verbatim))}），"
                "整句没有跨期 / 跨行推导",
                line,
            ))
    return hits


def check_file(path: Path) -> list[tuple[int, str, str, str]]:
    return check_text(path.read_text(encoding="utf-8", errors="replace"))


def report(hits: list[tuple[int, str, str, str]], label: str) -> None:
    print(f"\n🚫 [insight-value] {label} — {len(hits)} 处", file=sys.stderr)
    for lineno, kind, why, line in hits:
        snippet = line if len(line) <= 60 else line[:60] + "…"
        print(f"   L{lineno} [{kind}] {snippet}", file=sys.stderr)
        print(f"        → {why}", file=sys.stderr)
    print(
        "   → 修法：把表里的原值换成跨行 / 跨期推导（比值、差值、占比、N 周形态），"
        "或补一个横向参照；跨口径的比值算不出来就写进「数据能力缺口」",
        file=sys.stderr,
    )


def main() -> int:
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        print(__doc__)
        return 0
    strict = "--strict" in args
    total: list[tuple[int, str, str, str]] = []

    if "--stdin" in args:
        hits = check_text(sys.stdin.read())
        if hits:
            report(hits, "<stdin>")
            total += hits
    else:
        for a in args:
            if a.startswith("-"):
                continue
            p = Path(a)
            if not p.is_file():
                continue
            hits = check_file(p)
            if hits:
                report(hits, str(p))
                total += hits

    if not total:
        print("✅ [insight-value] 洞察无表格复读 / 跨口径相除", file=sys.stderr)
    return 2 if (strict and total) else 0


if __name__ == "__main__":
    sys.exit(main())
