#!/usr/bin/env python3
"""周报洞察内容门：抓四类问题——没有判断的表格复读、分析腔、营销腔、跨口径相除。

洞察的写法是「判断 → 证据 → 说明」（insight-writing-guide.md）：标题是业务判断，
bullet 用表里的数 + 环比 / Q 对比做证据。所以表内数出现在判断标题下面是正常的
证据，不算复读；只有标题本身在罗列表里的数、或 bullet 不挂在任何判断标题下时，
才按「表格复读」报。

「分析腔」抓领导改稿里反复删掉的自造说法（摊薄 / 浏览盘 / 基线 / 小盘 / 进表 /
「降幅是 X 的 N 倍」），换成业务说法见 guide 的人话替换表。

「营销腔」抓她只删不加的那类词（极其 / 惊人 / 剪刀差 / 破局 / 触底反弹 …）——
形容词本身不违禁，违禁的是把业务变化写成宣发稿。

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

# 分析腔：领导改稿里删掉的自造说法。「档位」「留存盘」「翻倍」她自己保留，不在此列。
ANALYST_RE = re.compile(
    r"摊薄|浏览盘|边缘流量|小盘|进表|基线|形态|表态|"
    r"(?:降|增|涨|跌)幅是.{0,16}?倍|"
    r"的近?\s*\d+(?:\.\d+)?\s*倍|差\s*\d+(?:\.\d+)?\s*倍"
)

# 营销腔：领导改稿里只删不加的一类词。用她 Q2~Q4 的 78 个编辑版本校准过——
# 新增句 520 条命中 0、删除句 585 条命中 15。「归因」「洞察」故意不收：
# 那是我方正常业务词，收进来会误杀自己的分析句。
MARKETING_RE = re.compile(
    r"极其|惊人|漂亮|彻底|质变|剪刀差|破局|诊断报告|信号|爆发|飙升|焦虑|闭环|拐点|"
    r"去肥增瘦|触底反弹|报复性"
)

# 编号小标题：`### 1. 判断句`
HEADING_RE = re.compile(r"^#{2,4}\s*\d+\.\s*")
CJK_RE = re.compile(r"[一-鿿]")


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


def _heading_has_judgment(body: str, tbl: set[str]) -> bool:
    """标题带判断才能装数（领导要「标题能装下的数就装进去」）。

    判断 = 有一个不含数字的分句（「是在播主播开得少了」）、跨周形态 / 推导词
    （「4 周最低」，DERIVE_RE），或表里查不到的推导数（「相比 Q3 提升 57%」）。
    三样都没有 = 在罗列表里的数。
    """
    if DERIVE_RE.search(body):
        return True
    clauses = re.split(r"[，,；;、：:]", body)
    if any(len(CJK_RE.findall(c)) >= 4 and not NUM_RE.search(c) for c in clauses):
        return True
    return bool({n for n in _norm_nums(body) if len(n) > 1} - tbl)


def check_text(text: str) -> list[tuple[int, str, str, str]]:
    """返回 [(行号, 类别, 说明, 原文), ...]。非周报 md（缺任一节）返回空。"""
    if "## 洞察" not in text or "## 数据明细" not in text:
        return []

    tbl = table_numbers(text)
    hits: list[tuple[int, str, str, str]] = []
    under_judgment = False  # 当前行是否挂在一个判断标题下

    for lineno, line in insight_lines(text):
        is_heading = bool(HEADING_RE.match(line))
        body = re.sub(r"^#{1,6}\s*\d*\.?\s*|^[-*]\s+", "", line)

        for a_terms, b_terms, why in FORBIDDEN_PAIRS:
            if (any(a in body for a in a_terms) and any(b in body for b in b_terms)
                    and RATIO_RE.search(body)):
                hits.append((lineno, "跨口径相除", why, line))
                break

        m = ANALYST_RE.search(body)
        if m:
            hits.append((lineno, "分析腔", f"「{m.group(0)}」是自造的分析说法，换成业务说法", line))

        m = MARKETING_RE.search(body)
        if m:
            hits.append((lineno, "营销腔", f"「{m.group(0)}」是营销稿用词，换成业务陈述", line))

        verbatim = _norm_nums(body) & tbl
        restates = len(verbatim) >= VERBATIM_LIMIT and not DERIVE_RE.search(body)
        if is_heading:
            under_judgment = _heading_has_judgment(body, tbl)
        if restates and not under_judgment:
            hits.append((
                lineno, "表格复读",
                f"{len(verbatim)} 个数在明细表里原样可查（{'、'.join(sorted(verbatim))}），"
                + ("标题在罗列数字，没有业务判断" if is_heading else "没有挂在判断标题下"),
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
        "   → 修法：标题写成业务判断（用户 / 主播 / 内容在发生什么），bullet 用表里的数"
        " + 环比或 Q 对比做证据；分析腔换成业务说法（guide「人话替换表」）；"
        "营销腔换成业务陈述；跨口径的比值算不出来就写进「数据能力缺口」",
        file=sys.stderr,
    )


def main() -> int:
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        print(__doc__)
        return 0
    strict = "--strict" in args
    total: list[tuple[int, str, str, str]] = []
    checked = 0

    if "--stdin" in args:
        checked = 1
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
                print(f"⚠️  文件不存在，未检查: {p}", file=sys.stderr)
                continue
            checked += 1
            hits = check_file(p)
            if hits:
                report(hits, str(p))
                total += hits

    if not checked:
        print("⚠️  [insight-value] 没有检查任何文件", file=sys.stderr)
    elif not total:
        print("✅ [insight-value] 洞察无表格复读 / 跨口径相除", file=sys.stderr)
    return 2 if (strict and total) else 0


if __name__ == "__main__":
    sys.exit(main())
