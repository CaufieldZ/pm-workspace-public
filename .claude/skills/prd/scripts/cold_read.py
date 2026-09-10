#!/usr/bin/env python3
"""冷读反测打包器（两种模式：叶子完整性盲区 / 语义赘述）。

把 cross-check「Reader Testing」的隐性手艺固化成可复现工序，承担**确定性部分**：
1. 复用 prd_compose 把 PRD（single / split）拼成自包含全文 + 附 scene-list → 落临时 context 文件。
2. 按模式生成结构化探针 prompt（注入「干净上下文 / 只看过这份文档 / 禁读写 session-state」隔离约束）。
3. 落报告模板（不覆盖已存在的）。

LLM 判断部分（实际冷读）由 prd SKILL.md 编排 Agent 干净子代理执行，本脚本不调 Agent。

两种模式（`--mode`）：
    leaf （默认）— 按 target 分章逐个探针，问「哪里写得不够，读者要脑补」。7 类叶子盲区。
    dedup        — 全文单个探针，问「哪条规则被完整讲了不止一次」。赘述是全文属性，
                   不分 target；机械检测只能抓「验收复述规格」这一种形状，跨章重复靠语义判断。

输出（stdout）：
    - context 文件路径（自包含全文 + scene-list，交给子代理 Read）
    - 报告模板路径（leaf → cold-read-{date}.md / dedup → dedup-scan-{date}.md）
    - 探针 prompt：leaf 每个 target 一段 `=== PROBE target=X ===`；dedup 一段 `=== PROBE mode=dedup ===`

前置：
    - <prd.md> 存在（single / split 均可）
    - scene-list.md 可选：PRD 同目录 → 项目根 → 产品线根 三级自动探测，找到才附进 context
    - --help 本身无前置

退出码 / 产物：
    0 — 打包完成。产物落点：context 文件 {系统临时目录}/cold-read-context-{stem}.md、
        报告模板 <PRD 同目录>/{cold-read|dedup-scan}-{YYYY-MM-DD}.md（探针 prompt 走 stdout）
    1 — PRD 路径不存在 / leaf 模式未能自动选出 target 且未传 --targets

盲区 7 类（权威定义在 prd-scene-templates.md「叶子完整性自查」节；此处是探针逻辑表达，不构成第二定义源）。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from prd_compose import compose  # noqa: E402
from read_prd_section import _chapter_kind, _list_toc, read_section  # noqa: E402

# 7 类盲区探针（与 prd-scene-templates.md 权威 taxonomy 一一对应）。
# 每类 = (类名, 该类要逼问的具体问题)。子代理按类逐条追问 target。
PROBE_CLASSES: list[tuple[str, str]] = [
    ("时机/触发/周期",
     "实时 / 动态字段的刷新触发点写明了吗？是「查一次」还是「持续刷新」？"
     "轮询间隔 / 推送 vs 拉取 / 定时任务节奏有没有定？读者会不会把「异步更新」误读成「实时刷新」？"),
    ("字段生命周期",
     "每个字段是快照还是实时？发布即冻结、还是跟随行情变？"
     "翻态 / 平仓 / 下线后，旧字段是定型锁定还是继续刷新？最后已知态怎么缓存？"),
    ("边界/默认/空值",
     "阈值端点含不含（≥ 还是 >、区间开闭）？默认值是什么？"
     "空态 / 首次 / 离线 / 超期 / 无数据时怎么表现？最大 / 最小 / 溢出时截断还是报错？"),
    ("跨位置定义一致性",
     "同一概念在多章口径是否打架（如 A 章写 SLA ≤ 5 分钟、B 章写异步无保证）？"
     "读者要横跳几处才能拼全一个规则？有没有一处写法会让人误推出另一处不成立的结论？"),
    ("状态全集穷举",
     "状态机漏了哪个态？自环（同态内字段刷新）、离线再上线、并发改动、超时回退有没有覆盖？"
     "每个「终止状态」真的终止了吗，还是存在再次迁出的暗门？"),
    ("分支穷举",
     "条件规则覆盖了否定面 / 边界面吗？每个「当 X」是否写了「当非 X」的反面分支？"
     "枚举值 / 阈值档位 / 多业务态是否逐个穷举，还是只写了 happy path？"),
    ("数据对齐/保留期",
     "展示窗口与底层数据保留期是否一致（如展示 N 个月但数据只留 M 个月）？"
     "超出保留期 / 窗口怎么降级？两个数据源（如实时接口 vs binlog）口径 / 时间轴对得齐吗？"),
]

# 赘述 6 类（dedup 模式）。判据是「单一真相位」：一条规则只该有一个完整讲述位，
# 其余位置退化成指针。机械检测只覆盖第 2 类（acceptance_echo），其余靠语义判断。
DEDUP_CLASSES: list[tuple[str, str]] = [
    ("跨章重复定义",
     "同一条业务规则 / 字段口径 / 状态流转，在多个章节各写了一遍**完整表述**（而非一处写全、别处引用）？"
     "列出全部出现位置，并指认哪一处该是真相位。"),
    ("验收复述规格",
     "验收条目是不是把上方规格换个说法又说一遍？验收该写「做 X 观察到 Y」的可验证判定点，"
     "能从规格直读的结论不该占一条验收。"),
    ("同节自我重复",
     "同一个区块 / 同一段 bullet 列表里，有没有两条讲的是同一件事，只是切分角度不同？"),
    ("反向声明噪音",
     "有没有「本轮不改 X」「Y 保持现状」「Z 不受影响」这类否定式复述？"
     "没写的本就不改，声明「不改」是纯噪音——除非该处正在纠正一个读者会有的具体误解。"),
    ("决策理由外溢",
     "决策记录章的「为什么这么定」，有没有在场景块 / 全局规则里又论证了一遍？"
     "场景块只该讲「是什么」，取舍归决策章、一句指针带过。"),
    ("指针写成了重写",
     "文中说「见 X 章」「同 Y」「沿用 Z」的地方，有没有在指针旁边又把被指向的内容抄了一遍？"),
]

# 语义级 judge rubric（机械检测管不到，靠 LLM 判断）
JUDGE_RUBRIC: list[tuple[str, str]] = [
    ("反复讲",
     "同一规则 / 字段 / 流程在本章和其他章是否重复定义（非引用而是重写）？"
     "读者在 A 处已知的事，B 处再出现全文是不是废话？"),
    ("夸夸其谈",
     "有没有包装词 / 空泛动词 / 无源铺垫在产品规格文档里不该出现的？"),
    ("跨章一致性",
     "本章的口径 / 阈值 / 角色权限与 baseline 或其他章是否打架？读者按本章写的去做会不会和别处矛盾？"),
]


def _default_targets(prd_path: Path) -> list[str]:
    """无 --targets 时，自动挑最易埋叶子洞的章：有编号的「静态」实体 / 规则 / 状态机章。"""
    toc = _list_toc(prd_path)
    picked: list[str] = []
    for num, title, lvl in toc:
        if not num:  # 跳无编号章（变更记录等）
            continue
        if lvl > 2:  # 只取章 / 大节级，场景小节由其所属章覆盖
            continue
        if _chapter_kind(title) != "静态":
            continue
        picked.append(num)
    return picked


def _build_context_file(prd_path: Path, scene_list: Path | None) -> Path:
    """compose PRD 全文 + 附 scene-list，落临时文件供子代理 Read。"""
    composed, missing = compose(prd_path, check_only=False)
    if missing:
        print(f"⚠ compose 时 {len(missing)} 个子文件缺失（继续）：{missing}", file=sys.stderr)

    parts = [f"<!-- 冷读自包含上下文：{prd_path.name} compose 全文 -->", "", composed]
    if scene_list and scene_list.exists():
        parts += [
            "", "---", "",
            "<!-- 附：scene-list（场景编号 / View / 优先级真相源，仅供对照，非 PRD 正文）-->",
            "", scene_list.read_text(encoding="utf-8"),
        ]
    ctx = Path(tempfile.gettempdir()) / f"cold-read-context-{prd_path.stem}.md"
    ctx.write_text("\n".join(parts), encoding="utf-8")
    return ctx


def _probe_prompt(prd_name: str, ctx_path: Path, target: str, target_excerpt: str) -> str:
    """为单个 target 生成干净子代理探针 prompt。"""
    classes_block = "\n".join(
        f"{i}. 【{name}】{q}" for i, (name, q) in enumerate(PROBE_CLASSES, 1)
    )
    judge_block = "\n".join(
        f"{i}. 【{name}】{q}" for i, (name, q) in enumerate(JUDGE_RUBRIC, len(PROBE_CLASSES) + 1)
    )
    excerpt = target_excerpt.strip()
    if len(excerpt) > 1800:
        excerpt = excerpt[:1800] + "\n…（节选，完整内容在 context 文件）"

    return f"""你是第一次看这份 PRD 的研发 / 测试工程师，**没有任何对话上下文**，只读过这一份文档。

## 隔离铁律（违反则结论无效）
- 只 Read 这一个文件：`{ctx_path}`（{prd_name} 的自包含全文 + scene-list）。
- **严禁** Read / Write `.claude/session-state.md` 或仓库里任何其他文件。
- 不要联想「作者本意」「应该是这个意思」——你不知道作者想什么，只能依据白纸黑字。
- 凡是文档没写死、要你脑补才能填上的，就是一个盲点，照实记下来。

## 任务
针对本 PRD 的 **第 {target} 章 / 节**，做叶子完整性冷读反测。先读 context 文件全文建立背景，再聚焦该章。

聚焦章节原文节选（仅定位用，以 context 文件为准）：
```
{excerpt}
```

逐条过下面 7 类盲区，每类问自己「这份文档把它写死了吗？还是要我脑补？」：

{classes_block}

再过下面 3 类语义级判断（机械检测管不到，靠你读懂意思）：

{judge_block}

## 输出格式（只输出命中的盲点，没有就说「本章无盲点」）
每个盲点一条，四件套：
- **位置**：第几章 / 节 + 原文片段（一句）
- **盲区类别**：上面 10 类里的哪一类（7 类叶子 + 3 类语义）
- **冷读者会怎么误读 / 卡在哪**：具体说一个会被读错或读不出的结论
- **建议补法**：补一句 / 一列 / 一行什么内容能堵上（业务语言，不写 SQL / 接口）

只报真正要脑补的硬缺口，不报文风 / 排版 / 错别字。宁可少报、每条都站得住，不要为凑数报模糊项。"""


def _dedup_prompt(prd_name: str, ctx_path: Path) -> str:
    """全文赘述探针 prompt（不分 target —— 赘述是全文属性，切章就看不见）。"""
    classes_block = "\n".join(
        f"{i}. 【{name}】{q}" for i, (name, q) in enumerate(DEDUP_CLASSES, 1)
    )
    return f"""你是第一次看这份 PRD 的研发 / 测试工程师，**没有任何对话上下文**，只读过这一份文档。

## 隔离铁律（违反则结论无效）
- 只 Read 这一个文件：`{ctx_path}`（{prd_name} 的自包含全文 + scene-list）。
- **严禁** Read / Write `.claude/session-state.md` 或仓库里任何其他文件。
- 不要联想「作者本意」，只依据白纸黑字。

## 任务
通读**全文**，找出「同一件事被反复讲」的地方。这是全文级判断，必须先完整读完再下结论——
只看单章看不出赘述，一条规则散在六处、每处单看都合理。

判据是**单一真相位**：一条业务规则只该有一个完整讲述位，其余位置退化成一句指针
（「按某某规则」「见某章」）。同一条规则出现 N 次不等于赘述，**出现 N 次完整表述**才是。

逐类过一遍：

{classes_block}

## 不算赘述（别报这些）
- 同一术语在不同场景讲的是**不同的事**（如「挂单卡进限价态」与「市价卡进市价态」是两条规则，不是重复）。
- 指针本身（「见第 X 章」「取舍见决策 N」）—— 那正是收敛后的正确形态。
- 全局规则章列一条 + 场景块引一句 —— 这是设计要求的双位置，不是重复。
- 埋点表 / 字段表里的重复列值。

## 输出格式（只输出命中的，没有就说「全文无明显赘述」）
每条一个五件套：
- **被重复的那条规则**：一句话概括它讲的是什么
- **全部出现位置**：章节 + 原文片段（每处一行，标明是「完整表述」还是「指针」）
- **赘述类别**：上面 6 类里的哪一类
- **建议保留位**：哪一处该做真相位，为什么是它（通常是全局规则章 / 决策章 / 最先定义处）
- **其余处怎么收**：改成什么样的一句指针，或直接删

按「重复次数 × 篇幅」从重到轻排。只报真站得住的，宁可少报——
把「相关但不同的两条规则」误判成重复，会让 PM 删掉真正需要的内容，代价比漏报大。"""


def _dedup_report_template(prd_path: Path, date: str) -> str:
    return f"""# 赘述清单 · {prd_path.name} · {date}

**产物说明**：语义赘述扫描（prd skill 冷读工序 dedup 模式）。
干净上下文子代理通读全文跑出 → 本表聚合 → PM 逐条 triage（收成指针 / 删除 / 误报）。

## 赘述清单

| # | 被重复的规则 | 出现位置（标完整 / 指针） | 类别 | 建议保留位 | 其余处怎么收 | triage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | {{{{ 待填 }}}} | {{{{ 待填 }}}} | {{{{ 6 类之一 }}}} | {{{{ 待填 }}}} | {{{{ 待填 }}}} | {{{{ 收 / 删 / 误报 }}}} |

## triage 小结

- 已发现：N
- 已收敛：M
- 误报 / 保留：K（附理由）
"""


def _report_template(prd_path: Path, targets: list[str], date: str) -> str:
    targets_line = " / ".join(targets) if targets else "（自动选静态章）"
    return f"""# 冷读盲点清单 · {prd_path.name} · {date}

> 叶子完整性冷读反测产物（prd skill「交付前冷读」工序）。
> 干净上下文子代理逐 target 跑出 → 本表聚合 → PM 逐条 triage（补文档 / 标记留版本）。
> target 范围：{targets_line}

## 盲点清单

| # | 位置（章节 + 原文片段） | 盲区类别 | 冷读者会怎么误读 / 卡在哪 | 建议补法 | triage（补 / 留版本 / 误报） |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | {{{{ 待填 }}}} | {{{{ 7 类叶子 + 3 类语义 }}}} | {{{{ 待填 }}}} | {{{{ 待填 }}}} | {{{{ 待填 }}}} |

## triage 小结

- 已发现：N
- 已补文档：M
- 留版本：K（附原因）
- 误报 / 不补：L（附理由）
"""


def cmd_prepare(prd_path: Path, targets: list[str], mode: str = "leaf") -> int:
    if not prd_path.exists():
        raise SystemExit(f"PRD 不存在：{prd_path}")

    # scene-list 探测：先同目录，再产品线根（baseline 模型）
    scene_list = None
    for cand in (prd_path.parent / "scene-list.md",
                 prd_path.parent.parent / "scene-list.md",
                 prd_path.parent.parent.parent / "scene-list.md"):
        if cand.exists():
            scene_list = cand
            break

    if mode == "dedup":
        ctx = _build_context_file(prd_path, scene_list)
        date = _dt.date.today().isoformat()
        report_path = prd_path.parent / f"dedup-scan-{date}.md"

        print(f"# 赘述扫描准备完成：{prd_path.name}")
        print(f"context 文件（喂子代理 Read）：{ctx}")
        if scene_list:
            print(f"已附 scene-list：{scene_list}")
        print("范围：全文（赘述是全文属性，不分 target）")

        if report_path.exists():
            print(f"报告模板已存在（不覆盖）：{report_path}")
        else:
            report_path.write_text(_dedup_report_template(prd_path, date), encoding="utf-8")
            print(f"报告模板已生成：{report_path}")

        print()
        print("# 以下 PROBE = 一个干净子代理（Agent 工具，general-purpose）的 prompt：")
        print()
        print("=== PROBE mode=dedup ===")
        print(_dedup_prompt(prd_path.name, ctx))
        print("=== END PROBE mode=dedup ===")
        return 0

    if not targets:
        targets = _default_targets(prd_path)
        if not targets:
            raise SystemExit("未能自动选出 target，请用 --targets 指定（如 3.1,4.1,5.1）")

    ctx = _build_context_file(prd_path, scene_list)
    date = _dt.date.today().isoformat()
    report_path = prd_path.parent / f"cold-read-{date}.md"

    print(f"# 冷读准备完成：{prd_path.name}")
    print(f"context 文件（喂子代理 Read）：{ctx}")
    if scene_list:
        print(f"已附 scene-list：{scene_list}")
    print(f"target：{', '.join(targets)}")

    if report_path.exists():
        print(f"报告模板已存在（不覆盖）：{report_path}")
    else:
        report_path.write_text(_report_template(prd_path, targets, date), encoding="utf-8")
        print(f"报告模板已生成：{report_path}")

    print()
    print("# 以下每段 PROBE = 一个干净子代理（Agent 工具，Explore / general-purpose）的 prompt：")
    for t in targets:
        excerpt = read_section(prd_path, t)
        print()
        print(f"=== PROBE target={t} ===")
        print(_probe_prompt(prd_path.name, ctx, t, excerpt))
        print(f"=== END PROBE target={t} ===")
    return 0


_EPILOG = """\
示例：
    python3 .claude/skills/prd/scripts/cold_read.py --prepare projects/<产品线>/deliverables/<季度>/<版本>/prd-<产品线>-<版本>.md
    python3 .claude/skills/prd/scripts/cold_read.py --prepare projects/<产品线>/prd-<产品线>-baseline.md --targets 3.1,4.1,5.1
        # 不带 --targets 时按 TOC 自动选「静态」实体 / 规则章（最易埋叶子洞的章）
    python3 .claude/skills/prd/scripts/cold_read.py --prepare <prd.md> --mode dedup
        # 赘述扫描：全文单探针，找「同一条规则被完整讲了不止一次」；--targets 在此模式忽略
"""


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--prepare", metavar="PRD", required=True,
                    help="PRD md 路径（single / split 均可，split 自动拼全文）")
    ap.add_argument("--targets", default="",
                    help="逗号分隔章节号（如 3.1,4.1,5.1）；默认空 = 自动选静态章。--mode dedup 时忽略")
    ap.add_argument("--mode", choices=("leaf", "dedup"), default="leaf",
                    help="leaf（默认）= 叶子完整性盲区，按 target 分章；dedup = 语义赘述，全文单探针")
    args = ap.parse_args()

    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    return cmd_prepare(Path(args.prepare).resolve(), targets, args.mode)


if __name__ == "__main__":
    sys.exit(main())
