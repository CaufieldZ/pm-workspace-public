#!/usr/bin/env python3
"""LEARNED.md 已沉淀规则的硬阻断检查器（按文件类型分发）。

接入：.claude/hooks/post-plain-language-check.sh 在原 checker 后并行调用。
退出码：0 通过 / 2 阻断。

支持规则：
- scene-list*.md：所有 `^## ` 必须匹配 `^## View \\d+ · `（LEARNED 2026-05-12 L7）
- prd-*.md：正文裸 snake_case 字段（排除代码块/术语表段）— warn 不 block（LEARNED 2026-05-12 L9）

（真相源静态章版本流水标注 / 四不检查已由 check_static_chapter.py 承接，对 baseline / scene-list 生效）
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def check_scene_list(path: Path) -> list[str]:
    """scene-list.md 一级分组（## 标题）必须 `## View N · 白话名`。

    豁免段（显式 H2 前缀）：跨端 / 附录 / 备注 / 关键说明 / 流程说明 /
    图例 / 说明 / 范式声明 / 变更 —— 这些是辅助章，不是 View 分组。
    方案型项目（无 UI、主题索引而非 View）用 主题 / 产出物 前缀，同样豁免。

    旧版"不含端语义关键词→豁免"太宽（## 1. 顶部入口 也被放过），改为显式前缀。
    """
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return errors

    in_code = False
    view_re = re.compile(r"^##\s+View\s+\d+\s+·\s+")
    # 辅助段 H2 前缀显式豁免
    aux_prefix_re = re.compile(
        r"^##\s+(?:跨端|附录|备注|关键说明|流程说明|图例|说明|范式声明|"
        r"变更|变更记录|版本|数据流|跨场景规则|数据规则|统计|"
        r"编号锁定|编号|术语|跨项目|交互大图|PRD|prototype|原型|"
        r"主题|产出物)"
    )
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not line.startswith("## "):
            continue
        if view_re.match(line):
            continue
        if aux_prefix_re.match(line):
            continue
        errors.append(
            f"  L{i}: 一级标题应为 `## View N · 白话名` 或显式辅助段（跨端 / 附录 / 备注 / 关键说明 等），实际：{line.strip()[:80]}"
        )
    return errors


def check_prd_snake_case(path: Path) -> list[str]:
    """PRD 正文裸 snake_case 字段（warn）。排除代码块 / 行内 code / md 链接 URL / 术语表段（## 3.）。"""
    warns: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return warns

    snake_re = re.compile(r"\b[a-z]+_[a-z_]+\b")
    inline_code_re = re.compile(r"`[^`]+`")
    md_link_re = re.compile(r"\]\(([^)]+)\)")
    url_re = re.compile(r"https?://\S+")

    h_re = re.compile(r"^##\s+(\d+)[\.\s]")
    in_code = False
    in_glossary = False  # ## 3. 术语表内
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = h_re.match(line)
        if m:
            in_glossary = int(m.group(1)) == 3
            continue
        if in_glossary:
            continue
        # 剥 inline code / md link url / 裸 URL
        clean = inline_code_re.sub("", line)
        clean = md_link_re.sub("", clean)
        clean = url_re.sub("", clean)
        hits = snake_re.findall(clean)
        if hits:
            warns.append(
                f"  L{i}: 裸 snake_case：{', '.join(set(hits))[:80]} | {line.strip()[:80]}"
            )
    return warns


def main() -> int:
    parser = argparse.ArgumentParser(description="LEARNED.md 沉淀规则检查器")
    parser.add_argument("file", type=Path, help="要检查的文件路径")
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="即使有 strict 命中也只 warn 不 exit 2（默认严格模式）",
    )
    args = parser.parse_args()

    if not args.file.exists():
        return 0

    name = args.file.name
    fail = False

    # 路由：按文件类型分发
    if name.startswith("scene-list") and name.endswith(".md"):
        errs = check_scene_list(args.file)
        if errs:
            print(f"🚫 [learned-rules] {args.file}: scene-list view 前缀违例", file=sys.stderr)
            for e in errs:
                print(e, file=sys.stderr)
            fail = True

    if name.startswith("prd-") and name.endswith(".md"):
        warns = check_prd_snake_case(args.file)
        if warns:
            print(
                f"⚠️  [learned-rules] {args.file}: PRD 正文裸 snake_case（warn，{len(warns)} 处）",
                file=sys.stderr,
            )
            for w in warns[:10]:
                print(w, file=sys.stderr)
            if len(warns) > 10:
                print(f"  ...... 还有 {len(warns) - 10} 处", file=sys.stderr)

    if fail and not args.warn_only:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
