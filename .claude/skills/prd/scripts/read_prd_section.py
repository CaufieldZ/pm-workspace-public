#!/usr/bin/env python3
"""按章节号读 PRD md 片段（single / split 模式统一接口）。

用法：
    python3 read_prd_section.py <prd.md> --toc         # 列章节 TOC
    python3 read_prd_section.py <prd.md> -s 5.1        # 读 5.1（场景章）
    python3 read_prd_section.py <prd.md> -s 4          # 读第 4 章全文
    python3 read_prd_section.py <prd.md> -s 3.2        # 读 3.2 节
    python3 read_prd_section.py <prd.md> --grep "一帖一卡"  # 定位关键词

行为：
- split 模式下读 5/6/7.x 章节自动去 scenes/ 找对应文件
- 读章（不带点，如 `-s 4`）返回整章内容
- 读节（带点，如 `-s 3.2`）返回该节内容（下一个同级 heading 前为止）
- --toc 输出 `章节号 · 白话名` 列表

供主线 Opus / sub-agent 按需读 baseline / PRD 章节，不全量 Read 大文件。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_HEADING_RE = re.compile(r"^(#{1,4})\s+(\d+(?:\.\d+)*)[.\s]\s*(.*)$")
# 无编号 H2 章（如 baseline 的「## 变更记录」），编号位留空，用标题文字定位。
# 限 H2：H1 无编号的是文档主标题，不进章节 TOC。
_HEADING_NONUM_RE = re.compile(r"^(#{2})\s+(?!\d)(.+?)\s*$")
_SCENE_LINK_RE = re.compile(
    r"^\s*-\s*\[([0-9]+\.[0-9]+)\s+([A-Z][-\w]*)\s*·\s*([^\]]+?)\]\(([^)]+\.md)\)"
)

# PRD 动态章关键词（baseline / delta 通用）：命中即标「动态」，否则「静态」。
# 对标 check_static_chapter.py 的 NON_STATIC_KEYWORDS，PRD 语境裁剪。
_DYNAMIC_CH_KEYWORDS = (
    "变更记录", "变更日志", "迭代记录", "changelog",
    "决策记录", "决策", "里程碑", "排期",
    "价值论证", "价值", "本轮需求", "核心变更", "反向合并指引",
    "已交付", "已上线",
)


def _chapter_kind(title: str) -> str:
    """按标题关键词判静态 / 动态。动态章 = 决策演化 / 计划 / 本轮变更（不描述线上现状）。"""
    return "动态" if any(k in title for k in _DYNAMIC_CH_KEYWORDS) else "静态"


def _is_split_mode(prd_path: Path) -> tuple[bool, Path]:
    scenes_dir = prd_path.parent / f"{prd_path.stem}-scenes"
    return scenes_dir.is_dir(), scenes_dir


def _list_toc(prd_path: Path) -> list[tuple[str, str, int]]:
    """返回 [(章节号, 标题文字, heading_level), ...]

    主 md 的章节 + split 模式子文件的章节一起输出。
    """
    toc: list[tuple[str, str, int]] = []
    text = prd_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            hashes, num, rest = m.groups()
            toc.append((num, rest.strip(), len(hashes)))
            continue
        # 无编号 H1/H2 章（如 baseline「变更记录」），用标题文字当 key
        m = _HEADING_NONUM_RE.match(line)
        if m:
            hashes, rest = m.groups()
            title = rest.strip()
            # 跳过引用 / 表格里的伪标题（已被 _HEADING_RE 漏过的正常）
            toc.append(("", title, len(hashes)))

    # split 模式：把 5/6/7 章里的场景链接也列进去
    is_split, scenes_dir = _is_split_mode(prd_path)
    if is_split:
        # 主 md 里的场景链接行就是 TOC 项（不用打开子文件）
        for line in text.splitlines():
            m = _SCENE_LINK_RE.match(line)
            if m:
                num, scene_id, name, _ = m.groups()
                toc.append((num, f"{scene_id} · {name.strip()}", 3))
    return sorted(toc, key=lambda t: _num_to_sortkey(t[0]))


def _num_to_sortkey(num: str) -> tuple:
    """'5.1' → (5, 1)；'5' → (5, 0)"""
    parts = num.split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return (999, 0)


def _extract_section_from_text(text: str, section: str) -> str:
    """从 md 字符串里提取 `section` 对应的片段（到下一个同级或上级 heading 前为止）。

    section: "4" 读整章；"4.1" 读该节。
    """
    lines = text.splitlines()
    in_section = False
    start = -1
    target_level = 0
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if not m:
            continue
        hashes, num, rest = m.groups()
        hlevel = len(hashes)
        if num == section and not in_section:
            in_section = True
            start = i
            target_level = hlevel
            continue
        if in_section and hlevel <= target_level:
            return "\n".join(lines[start:i]).rstrip()
    if in_section:
        return "\n".join(lines[start:]).rstrip()
    return ""


def read_section(prd_path: Path, section: str) -> str:
    """读任意章节号的内容。split 模式下 5/6/7.x 自动去 scenes/ 找。"""
    is_split, scenes_dir = _is_split_mode(prd_path)
    main_text = prd_path.read_text(encoding="utf-8")

    # split 模式 + 子章节（5.x / 6.x / 7.x）：找对应子文件
    if is_split and "." in section:
        chapter = section.split(".")[0]
        if chapter in ("5", "6", "7"):
            # 从主 md 里找场景链接
            for line in main_text.splitlines():
                m = _SCENE_LINK_RE.match(line)
                if m and m.group(1) == section:
                    rel_path = m.group(4)
                    scene_file = prd_path.parent / rel_path
                    if scene_file.exists():
                        return scene_file.read_text(encoding="utf-8").rstrip()
                    return f"⚠ 子文件不存在：{rel_path}"
            return f"⚠ 未在主 md 中找到场景 {section} 的引用"

    # 其他情况：从主 md 提取
    section_text = _extract_section_from_text(main_text, section)
    return section_text or f"⚠ 未找到章节 {section}"


def grep_prd(prd_path: Path, keyword: str) -> list[str]:
    """全 PRD（含子文件）grep 关键词，返回 `path:line:content` 列表。"""
    hits: list[str] = []
    main_text = prd_path.read_text(encoding="utf-8")
    for i, line in enumerate(main_text.splitlines(), 1):
        if keyword in line:
            hits.append(f"{prd_path.name}:{i}: {line.strip()}")

    is_split, scenes_dir = _is_split_mode(prd_path)
    if is_split:
        for scene_file in sorted(scenes_dir.glob("*.md")):
            sf_text = scene_file.read_text(encoding="utf-8")
            for i, line in enumerate(sf_text.splitlines(), 1):
                if keyword in line:
                    hits.append(f"{scene_file.name}:{i}: {line.strip()}")
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="按章节号读 PRD md 片段")
    ap.add_argument("prd", help="主 PRD md 路径")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--toc", action="store_true", help="列章节 TOC")
    g.add_argument("-s", "--section", help="章节号，如 4 / 5.1 / 3.2")
    g.add_argument("--grep", help="全文 grep 关键词")
    args = ap.parse_args()

    prd_path = Path(args.prd).resolve()
    if not prd_path.exists():
        raise SystemExit(f"PRD 不存在：{prd_path}")

    if args.toc:
        toc = _list_toc(prd_path)
        # 去重（split 模式下场景链接会在主 md 出现，toc 不重复）
        seen = set()
        for num, title, lvl in toc:
            key = (num, title)
            if key in seen:
                continue
            seen.add(key)
            indent = "  " * max(0, lvl - 1)
            # 仅章级（H1 / H2）标静态 / 动态；场景小节（lvl≥3）不标
            tag = ""
            if lvl <= 2:
                tag = f"  [{_chapter_kind(title)}]"
            print(f"{indent}{num:6s} {title}{tag}")
        return 0

    if args.section:
        print(read_section(prd_path, args.section))
        return 0

    if args.grep:
        hits = grep_prd(prd_path, args.grep)
        for h in hits:
            print(h)
        return 0 if hits else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
