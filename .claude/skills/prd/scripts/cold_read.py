#!/usr/bin/env python3
"""冷读反测打包器（叶子完整性盲区，算法化版）。

把 cross-check「Reader Testing」的隐性手艺固化成可复现工序，承担**确定性部分**：
1. 复用 prd_compose 把 PRD（single / split）拼成自包含全文 + 附 scene-list → 落临时 context 文件。
2. 按 7 类盲区为每个 target 生成结构化探针 prompt（注入「干净上下文 / 只看过这份文档 / 禁读写 session-state」隔离约束）。
3. 落 `cold-read-{date}.md` 盲点清单模板（不覆盖已存在的）。

LLM 判断部分（实际冷读）由 prd SKILL.md 新 Step 编排 Agent 干净子代理执行，本脚本不调 Agent。

用法：
    python3 cold_read.py --prepare <prd.md> [--targets 3.1,4.1,5.1]
        # 不带 --targets 时按 TOC 自动选「静态」实体 / 规则章（最易埋叶子洞的章）

输出（stdout）：
    - context 文件路径（自包含全文 + scene-list，交给子代理 Read）
    - 报告模板路径（cold-read-{date}.md）
    - 每个 target 一段 `=== PROBE target=X ===` 探针 prompt，直接喂 Agent 工具

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


def cmd_prepare(prd_path: Path, targets: list[str]) -> int:
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


def main() -> int:
    ap = argparse.ArgumentParser(description="冷读反测打包器（叶子完整性盲区）")
    ap.add_argument("--prepare", metavar="PRD", required=True, help="PRD md 路径")
    ap.add_argument("--targets", default="",
                    help="逗号分隔章节号（如 3.1,4.1,5.1）；缺省自动选静态章")
    args = ap.parse_args()

    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    return cmd_prepare(Path(args.prepare).resolve(), targets)


if __name__ == "__main__":
    sys.exit(main())
