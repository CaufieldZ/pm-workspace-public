#!/usr/bin/env python3
"""冷读打包器：让一个没有上下文的「开发者」读 PRD，说出开工前要问什么。

承担确定性部分：
1. 读 PRD 全文，附 scene-list 与产品线 baseline
   （baseline 让冷读者分得清「PRD 没写」和「线上已有、PRD 不该重写」）→ 落临时 context 文件。
2. 生成一段探针 prompt（注入干净上下文 / 禁读写 session-state 约束）。
3. 落报告模板（不覆盖已存在的）。

实际冷读由 prd SKILL.md 编排 Agent 干净子代理执行，本脚本不调 Agent。

输出（stdout）：context 文件路径、报告模板路径、一段 `=== PROBE ===` 探针 prompt。

前置：
    - <prd.md> 存在
    - scene-list.md / prd-*-baseline.md 可选：从 PRD 目录逐级向上探测，找到才附进 context
    - --help 本身无前置

退出码 / 产物：
    0 — 打包完成。产物落点：context 文件 {系统临时目录}/cold-read-context-{stem}.md、
        报告模板 <PRD 同目录>/cold-read-{YYYY-MM-DD}.md（探针 prompt 走 stdout）
    1 — PRD 路径不存在
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
import tempfile
from pathlib import Path


def _find_upwards(start: Path, pattern: str, max_up: int = 5) -> Path | None:
    """从 start 逐级向上找第一个匹配 pattern 的文件（到 projects/ 为止）。"""
    cur = start
    for _ in range(max_up):
        hits = sorted(cur.glob(pattern))
        if hits:
            return hits[0]
        if cur.name == "projects" or cur.parent == cur:
            return None
        cur = cur.parent
    return None


def _build_context_file(prd_path: Path, scene_list: Path | None, baseline: Path | None) -> Path:
    """PRD 全文 + 附 scene-list / baseline，落临时文件供子代理 Read。"""
    parts = [f"<!-- 冷读上下文 · 正文：{prd_path.name} -->", "", prd_path.read_text(encoding="utf-8")]
    for label, path in (("scene-list（场景编号真相源）", scene_list),
                        ("产品线 baseline（线上现状，仅供对照）", baseline)):
        if path and path.exists() and path.resolve() != prd_path.resolve():
            parts += ["", f"<!-- 附：{label} · {path.name} -->", "", path.read_text(encoding="utf-8")]
    ctx = Path(tempfile.gettempdir()) / f"cold-read-context-{prd_path.stem}.md"
    ctx.write_text("\n".join(parts), encoding="utf-8")
    return ctx


def _line_count(path: Path) -> int:
    try:
        return sum(1 for _ in path.open(encoding="utf-8"))
    except OSError:
        return 0


def _probe_prompt(prd_name: str, ctx_path: Path, has_baseline: bool) -> str:
    baseline_note = (
        "文件后半部分附了产品线 baseline（线上现状）。PRD 只写本轮改动，线上已有的东西 PRD 不重写是对的——"
        "某件事 PRD 没写但 baseline 里写了，不算缺失。"
        if has_baseline else "没有附 baseline，判断「缺失」时只看 PRD 本身。"
    )
    return f"""你是要按这份 PRD 开发的工程师，没有任何对话上下文，只拿到这一份文档。

## 隔离要求
- 只 Read 这一个文件：`{ctx_path}`（{prd_name} 全文 + 附件，约 {_line_count(ctx_path)} 行，用 offset / limit 分页读完）。
- 不读写 `.claude/session-state.md` 或仓库里其他任何文件。
- {baseline_note}

## 任务
读完全文，站在「明天就要开工」的位置回答四个问题：

1. **开工前必须问 PM 的问题**：哪些地方不问清楚就没法写代码或写测试用例（缺取值、缺条件、缺失败时怎么办、缺谁负责）。
2. **前后矛盾**：同一件事在两处写得不一样，你不知道以哪个为准。
3. **重复**：同一件事在多处完整写了不止一遍（指过去的一句「见某某」不算）。
4. **可以不看的段落**：读了不影响开发和测试的内容（过程叙述、和规格重复的理由、不归本团队做的事）。

## 输出
每一类列条目，没有就写「无」。每条两行：
- 位置：章节 + 原文一句
- 说明：问什么 / 哪两处冲突 / 哪几处重复 / 为什么可以不看

只报真会影响开工的。宁可少报，每条都站得住。不评文风和排版。"""


def _report_template(prd_path: Path, date: str) -> str:
    return f"""# 冷读清单 · {prd_path.name} · {date}

干净上下文子代理以开发者视角读全文 → 本表聚合 → PM 逐条处理（补 / 删 / 误报）。

| # | 类别 | 位置 | 说明 | 处理 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | {{{{ 要问的问题 / 矛盾 / 重复 / 可不看 }}}} | {{{{ 章节 + 原文 }}}} | {{{{ 待填 }}}} | {{{{ 补 / 删 / 误报 }}}} |
"""


def cmd_prepare(prd_path: Path) -> int:
    if not prd_path.exists():
        raise SystemExit(f"PRD 不存在：{prd_path}")

    scene_list = _find_upwards(prd_path.parent, "scene-list.md")
    baseline = _find_upwards(prd_path.parent, "prd-*-baseline.md")
    ctx = _build_context_file(prd_path, scene_list, baseline)
    date = _dt.date.today().isoformat()
    report_path = prd_path.parent / f"cold-read-{date}.md"

    print(f"# 冷读准备完成：{prd_path.name}")
    print(f"context 文件（喂子代理 Read）：{ctx}")
    for label, path in (("scene-list", scene_list), ("baseline", baseline)):
        if path:
            print(f"已附 {label}：{path}")
    if report_path.exists():
        print(f"报告模板已存在（不覆盖）：{report_path}")
    else:
        report_path.write_text(_report_template(prd_path, date), encoding="utf-8")
        print(f"报告模板已生成：{report_path}")

    has_baseline = bool(baseline) and baseline.resolve() != prd_path.resolve()
    print()
    print("# 以下 PROBE = 一个干净子代理（Agent 工具，general-purpose）的 prompt：")
    print()
    print("=== PROBE ===")
    print(_probe_prompt(prd_path.name, ctx, has_baseline))
    print("=== END PROBE ===")
    return 0


_EPILOG = """\
示例：
    python3 .claude/skills/prd/scripts/cold_read.py --prepare projects/<产品线>/deliverables/<季度>/<版本>/prd-<产品线>-<版本>.md
"""


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--prepare", metavar="PRD", required=True,
                    help="PRD md 路径")
    args = ap.parse_args()
    return cmd_prepare(Path(args.prepare).resolve())


if __name__ == "__main__":
    sys.exit(main())
