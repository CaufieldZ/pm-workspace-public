#!/usr/bin/env python3
"""真相源静态章写作纪律 lint（baseline 模块章 / 现状章 / scene-list）。

四类违规（详见 .claude/runbooks/artifact-conventions.md §四 静态章四不细节）：
  1. 流水标注：（v5.1 新增）/ 反转决策 #N / 本轮 / V3.1 vs V3.0
  2. 思考过程：（变更）/ 改名原因 / 审视后 / 起初 / 曾经
  3. 技术实现：binlog / RPC / WebSocket / SDK / TUILiveKit 组件 / Apollo / pageId=
  4. UI 视觉：颜色 hex / px / font-family / IBM Plex Mono / <input type=

只扫静态章（H2 标题命中「方案决策 / 设计决策 / 关键设计决策 / 本轮方案决策 / 版本历史 /
变更记录」或「## 7. / ## 8. / ## 9.」前的内容）。

章节级豁免：HTML 注释 `<!-- lint-allow: TRTC, OBS -->` 把词加入当前章节白名单
（到下一个 H2 失效）。

全部命中走 warn，exit 0（hook 不阻断）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# 共享 lib 接入（tech_jargon by domain + ui_jargon）
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.json_out import emit  # noqa: E402
from lib.tech_jargon import infer_domains, load_jargon  # noqa: E402
from lib.ui_jargon import ALL_PATTERNS as UI_JARGON_PATTERNS  # noqa: E402
from lib.ui_visual import (  # noqa: E402
    CSS_PROP_RE,
    FONT_FAMILY_RE,
    HEX_COLOR_RE,
    HTML_ATTR_RAW_RE,
    PX_RE,
    SPECIFIC_FONT_RE,
)

# ── 模式集 ──────────────────────────────────────────────────────────

# 1. 流水标注 / 版本对比
FLOW_PATTERNS = [
    (re.compile(r"（v?\d+\.\d+[^）]*(新增|反转|更新|变更|覆盖|删除|废止)[^）]*）"), "流水标注"),
    (re.compile(r"反转决策\s*#?\d+"), "流水标注"),
    (re.compile(r"决策\s*#?\d+\s*[）)]"), "流水标注"),
    (re.compile(r"（决策\s*#?\d+"), "流水标注"),
    (re.compile(r"V\d+(\.\d+)?\s*vs\s*V\d+(\.\d+)?"), "流水标注"),
    (re.compile(r"（\d{4}-\d{2}-\d{2}[^）]*(新增|反转|更新|变更|覆盖|删除|废止)[^）]*）"), "流水标注"),
    (re.compile(r"（覆盖决策\s*\d+"), "流水标注"),
    (re.compile(r"（局部反转"), "流水标注"),
]

# 2. 思考过程 / 历史对比
PROCESS_PATTERNS = [
    (re.compile(r"（新增）|（变更）|（覆盖）|（废止）|（删除）"), "思考过程"),
    (re.compile(r"改名原因|审视后|权衡后|纠结|曾经|起初|最初"), "思考过程"),
    (re.compile(r"反思|此次评审|本次评审|讨论结果|经讨论|思考下来|斟酌"), "思考过程"),
    # 「本轮」单独命中思考过程；但 baseline 模型下「本轮 … delta」是承重交叉引用
    # （现状章标注哪些对象本轮 delta 触及、待反向合并），同行含 delta 时在 check_file 豁免
    (re.compile(r"本轮(?!输入|输出|主题)"), "思考过程"),
    (re.compile(r"\bv\d+\.\d+\s+(从|改|新增|删除)"), "思考过程"),
]


def _build_tech_patterns(text: str) -> list[tuple[re.Pattern, str]]:
    """从文件头 1-2 章关键字推断 domain，加载 tech_jargon 词表。"""
    head = "\n".join(text.splitlines()[:200])  # 头 200 行用于 domain 推断
    domains = infer_domains(head)
    pats = load_jargon(domains=domains)
    return [(p, "技术实现") for p in pats]


# 4. UI 视觉 — 正则唯一源 lib/ui_visual（hex/px/font/css/specific_font/html_attr）
# 全部映射回 "UI 视觉" 类沿用 static 报告格式。
# 不取 ui_visual 的 ms/pt/rgba/opacity——静态章无 exempt_h2，会误伤性能契约行（≤500ms / P95）；
# gradient/box-shadow 等仍由 ui_jargon 词表覆盖。UI 越界词接 ui_jargon。
UI_PATTERNS = [(p, "UI 视觉") for p in (
    HEX_COLOR_RE, PX_RE, FONT_FAMILY_RE, CSS_PROP_RE, SPECIFIC_FONT_RE, HTML_ATTR_RAW_RE,
)]
UI_PATTERNS.extend([(p, "UI 视觉") for p, _cat in UI_JARGON_PATTERNS])

# 反馈提示类组件词：在业务规则静态章里描述「系统弹什么提示」= 反馈功能行为（非外观），
# 如「校验失败 → Toast「请先登录」」。这些词在 HTML 产物注解里仍由 ui_visual 拦（PM 越界写
# 控件名），仅静态章 md 豁免。布局 / 承载类（Drawer / Modal / Bottom Sheet 等选型）不在此列。
FEEDBACK_UI_WORDS = {"Toast", "Snackbar", "Tooltip", "Spinner", "Loader", "Skeleton"}

# 业务常识技术词：已沉淀为产品高频词、无自然中文替代，静态章描述现状时合理使用。
# 如「TRTC 失败降级 CDN」「含 SDK 的新版 App」。仅静态章 md 豁免；HTML 产物注解与其它项目
# 仍按全域 tech_jargon 词表拦截。实现选型（厂商组件名 TUILiveKit / 配置中心 Apollo 等有业务
# 语义替代的词）不入此白名单。
BUSINESS_TECH_WORDS = {"CDN", "SDK"}

ALL_PATTERNS = FLOW_PATTERNS + PROCESS_PATTERNS + UI_PATTERNS
# TECH_PATTERNS 按 domain 动态构造，check_file 内部拼接

# ── 章节边界 ────────────────────────────────────────────────────────

# 任一命中即视为非静态章（动态 / 混合 / 元章节），后续行不扫
# 设计原则：静态章描述「项目本质 = 产品现状 / 场景 / 角色 / 术语 / 业务规则 / IA / 数据枚举」；
# 非静态章描述「决策演化 / 计划 / 已交付 / 竞品 / 模板示例 / 元信息」——后者的内容 PM 写
# 「产出物属性 / 自用 todo / 里程碑」时合理夹带技术 / UI 词，应整章跳过。
NON_STATIC_KEYWORDS = (
    # 决策 / 变更（动态）
    "方案决策", "设计决策", "关键设计决策", "本轮方案决策",
    "版本历史", "变更记录", "迭代记录",
    # 计划 / 状态（混合的动态部分 + 元信息）
    "已交付", "已上线", "待办", "下一步", "待排期", "排期", "里程碑",
    "项目状态", "项目元信息", "交付物清单", "维护节奏", "执行计划",
    "阻塞", "外部依赖",
    # 参考 / 模板（PM 自用，非业务描述）
    "竞品参考", "竞品分析", "技术说明",
    "PRD 6 章", "紧凑模板", "PRD 模板",
)

DYNAMIC_H2 = re.compile(
    r"^##\s+(?:[0-9]+\.\s+)?.*(?:"
    + "|".join(re.escape(k) for k in NON_STATIC_KEYWORDS)
    + r").*$"
)

H2 = re.compile(r"^##\s+")

# ── 豁免 ────────────────────────────────────────────────────────────

# HTML 注释格式：<!-- lint-allow: TRTC, OBS, RPC -->
LINT_ALLOW = re.compile(r"<!--\s*lint-allow:\s*([^>]+?)\s*-->")


def check_file(path: Path) -> list[tuple[int, str, str, str, str]]:
    """返回命中列表 [(lineno, level, category, excerpt, matched), ...]。

    matched = 命中的离散词 / 片段（m.group(0)），供词表防腐化埋点反查死词；
    ui_jargon / tech_jargon 命中词与 dump_term_inventory 词形一致，可直接闭环。
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    # 按 domain 加载 tech_jargon（从文件头推断）
    tech_patterns = _build_tech_patterns(text)
    patterns = ALL_PATTERNS + tech_patterns

    lines = text.splitlines()
    hits: list[tuple[int, str, str, str, str]] = []
    in_dynamic = False  # 是否进入动态章（停止扫描）
    chapter_allow: set[str] = set()  # 当前章节内的豁免词

    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip()

        # 章节切换
        if H2.match(line):
            if DYNAMIC_H2.match(line):
                in_dynamic = True
            else:
                in_dynamic = False
            chapter_allow = set()  # 每个 H2 章节清空豁免
            continue

        if in_dynamic:
            continue

        # 累积本章节的 lint-allow
        m = LINT_ALLOW.search(line)
        if m:
            for tok in m.group(1).split(","):
                tok = tok.strip()
                if tok:
                    chapter_allow.add(tok)

        # 跳过纯空行 / 纯标记行
        if not line.strip():
            continue

        # 引用块行（> 开头）= 章节写作纪律导言（「> 静态章。…」），meta 说明非业务现状，整行跳过
        if line.lstrip().startswith(">"):
            continue

        # 逐 pattern 匹配
        for pat, category in patterns:
            m = pat.search(line)
            if not m:
                continue
            matched_text = m.group(0)
            # 章节级豁免
            if any(allow in matched_text for allow in chapter_allow):
                continue
            # baseline 承重写法豁免：「本轮 … delta」交叉引用是合法现状标注，非思考过程
            if matched_text.startswith("本轮") and "delta" in line:
                continue
            # 反馈提示类组件词在静态章描述功能行为（弹什么提示），非外观，豁免
            if matched_text in FEEDBACK_UI_WORDS:
                continue
            # 业务常识技术词（CDN / SDK 等无中文替代的产品高频词）静态章合理使用，豁免
            if matched_text in BUSINESS_TECH_WORDS:
                continue
            excerpt = line.strip()[:140]
            hits.append((i, "warn", category, excerpt, matched_text))
            break  # 同一行命中第一个就停，不重复报

    return hits


# 每类违规的修法模板（短句，给 Claude 直接看就能改）
FIX_HINTS = {
    "流水标注": "删行内 (vX.Y 新增) / 反转决策 #N / V3 vs V4 标注；如这条信息仍需保留，改写到 ## 7. 方案决策对应决策段或 ## 9. 版本历史",
    "思考过程": "删 (变更) / 起初 / 经讨论 / 反思 等过程词；静态章只描述当前结论，过程文字搬到 ## 7. 决策段「为什么」段",
    "技术实现": "删 binlog / RPC / API / 组件名 等实现细节，改成业务语义（如「下单后系统记录」而非「下单触发 binlog 同步」）；纯技术方案归 inputs/docs/ 下技术文档",
    "UI 视觉":  "删 #RRGGBB / px / font-family / 组件标签等视觉细节；静态章只描述功能不描述外观；视觉规范归设计系统或各产物 PRD §4",
}


def report(file_hits: list[tuple[str, list]]) -> None:
    """warn 全部走 stderr，exit 0 永不阻断。"""
    total = 0
    for label, hits in file_hits:
        if not hits:
            continue
        total += len(hits)
        by_cat: dict[str, int] = {}
        for _, _, cat, _, _ in hits:
            by_cat[cat] = by_cat.get(cat, 0) + 1
        summary = " / ".join(f"{c} {n}" for c, n in by_cat.items())
        print(f"\n{label} — warn {len(hits)}（{summary}）", file=sys.stderr)
        for lineno, _level, cat, excerpt, _matched in hits[:20]:
            print(f"  ⚠️  L{lineno} [{cat}]", file=sys.stderr)
            print(f"     原文: {excerpt}", file=sys.stderr)
            fix = FIX_HINTS.get(cat, "见 .claude/runbooks/artifact-conventions.md §四")
            print(f"     修法: {fix}", file=sys.stderr)
        if len(hits) > 20:
            print(f"  ... (共 {len(hits)} 处，仅显示前 20)", file=sys.stderr)

    if total > 0:
        print(
            "\n章节级豁免：在章节顶部加 <!-- lint-allow: 词A, 词B -->\n"
            "运行级豁免：SKIP_CONTEXT_LINT_GATE=1（仅 false positive 时使用）",
            file=sys.stderr,
        )

    sys.exit(0)  # warn never blocks


USAGE = ("usage: check_static_chapter.py <projects/{项目}/prd-*-baseline.md | scene-list.md> "
         "[<file>...] [--json-out <path|->]")


def main() -> None:
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(USAGE)
        sys.exit(0)
    files = [Path(a) for a in args if not a.startswith("-")]

    json_out = None
    if "--json-out" in args:
        i = args.index("--json-out")
        json_out = args[i + 1] if i + 1 < len(args) else None

    if not files:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    file_hits = [(str(fp), check_file(fp)) for fp in files if fp.exists()]
    emit(json_out, "context-static-lint",
         [(ln, cat, matched)
          for _label, hits in file_hits
          for (ln, _lvl, cat, _exc, matched) in hits])
    report(file_hits)


if __name__ == "__main__":
    main()
