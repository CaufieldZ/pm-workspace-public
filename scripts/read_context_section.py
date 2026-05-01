"""
context.md 按需读取工具——生成富目录 / 按章节选读 / 关键词定位。

用法（{项目} 占位符指项目路径片段，单层如 `sensors-metrics`、两层如 `livestream/q2-update`）:
  # 富目录（首次接触项目必跑）
  python3 scripts/read_context_section.py {项目} --toc

  # 按章节名选读（模糊匹配，支持 ## 和 ### 两级）
  python3 scripts/read_context_section.py {项目} \\
    --sections "场景编号,技术架构,业务规则/连麦"

  # 关键词定位（返回命中章节 + 上下文行）
  python3 scripts/read_context_section.py {项目} \\
    --grep "连麦" --context 5
"""

import argparse
import os
import re
import sys
from pathlib import Path


def find_context(project: str) -> Path:
    root = Path(__file__).resolve().parent.parent
    path = root / "projects" / project / "context.md"
    if not path.exists():
        sys.exit(f"找不到 {path}")
    return path


# ---------------------------------------------------------------------------
# Section tree parsing
# ---------------------------------------------------------------------------

class Section:
    def __init__(self, level: int, title: str, start: int):
        self.level = level
        self.title = title
        self.start = start      # 1-based line number of the header
        self.end: int = 0       # 1-based, inclusive last line
        self.children: list["Section"] = []

    @property
    def line_count(self) -> int:
        return self.end - self.start + 1


def parse_sections(lines: list[str]) -> list[Section]:
    """Parse ## and ### headers into a tree. Returns top-level (##) sections."""
    h2_list: list[Section] = []
    all_sections: list[Section] = []

    for i, line in enumerate(lines):
        lineno = i + 1
        if line.startswith("## ") and not line.startswith("### "):
            title = line[3:].strip()
            sec = Section(2, title, lineno)
            h2_list.append(sec)
            all_sections.append(sec)
        elif line.startswith("### "):
            title = line[4:].strip()
            sec = Section(3, title, lineno)
            if h2_list:
                h2_list[-1].children.append(sec)
            all_sections.append(sec)

    # Compute end lines (flat pass first)
    for idx, sec in enumerate(all_sections):
        if idx + 1 < len(all_sections):
            sec.end = all_sections[idx + 1].start - 1
        else:
            sec.end = len(lines)
        # Trim trailing blank lines
        while sec.end > sec.start and not lines[sec.end - 1].strip():
            sec.end -= 1

    # ## sections should span all their ### children
    for h2 in h2_list:
        if h2.children:
            h2.end = h2.children[-1].end

    return h2_list


# ---------------------------------------------------------------------------
# --toc
# ---------------------------------------------------------------------------

def cmd_toc(lines: list[str], sections: list[Section]) -> None:
    total = len(lines)
    print(f"# context.md 章节索引 ({total}行)\n")
    for sec in sections:
        print(f"## {sec.title} (L{sec.start}-L{sec.end}, {sec.line_count}行)")
        for child in sec.children:
            print(f"   ### {child.title} (L{child.start}-L{child.end}, {child.line_count}行)")


# ---------------------------------------------------------------------------
# --sections
# ---------------------------------------------------------------------------

def match_section(query: str, sec: Section) -> bool:
    """Check if query is a case-insensitive substring of the section title."""
    return query.lower() in sec.title.lower()


def resolve_sections(queries: list[str], h2_list: list[Section]) -> list[Section]:
    """Resolve comma-separated queries to matching sections.

    Query formats:
      "术语"           -> match any ## or ### title
      "业务规则/连麦"  -> match ## first, then ### within it
    """
    result: list[Section] = []
    seen_starts: set[int] = set()

    for raw_q in queries:
        raw_q = raw_q.strip()
        if not raw_q:
            continue

        if "/" in raw_q:
            parent_q, child_q = raw_q.split("/", 1)
            for h2 in h2_list:
                if match_section(parent_q.strip(), h2):
                    for child in h2.children:
                        if match_section(child_q.strip(), child):
                            if child.start not in seen_starts:
                                result.append(child)
                                seen_starts.add(child.start)
        else:
            for h2 in h2_list:
                if match_section(raw_q, h2):
                    if h2.start not in seen_starts:
                        result.append(h2)
                        seen_starts.add(h2.start)
                for child in h2.children:
                    if match_section(raw_q, child):
                        if child.start not in seen_starts:
                            result.append(child)
                            seen_starts.add(child.start)

    return result


def cmd_sections(lines: list[str], h2_list: list[Section], queries: list[str]) -> None:
    total = len(lines)
    matched = resolve_sections(queries, h2_list)

    if not matched:
        print(f"未匹配到任何章节。可用章节：")
        for sec in h2_list:
            print(f"  - {sec.title}")
            for child in sec.children:
                print(f"    - {child.title}")
        sys.exit(1)

    selected_lines = sum(s.line_count for s in matched)
    if selected_lines > total * 0.8:
        print(f"⚠ 选读量 {selected_lines}/{total} 行（{selected_lines*100//total}%），接近全文，建议直接 Read 全文\n")

    for sec in matched:
        level_mark = "##" if sec.level == 2 else "###"
        print(f"{'='*60}")
        print(f"{level_mark} {sec.title} (L{sec.start}-L{sec.end}, {sec.line_count}行)")
        print(f"{'='*60}")
        for i in range(sec.start - 1, sec.end):
            print(lines[i], end="")
        if not lines[sec.end - 1].endswith("\n"):
            print()
        print()


# ---------------------------------------------------------------------------
# --grep
# ---------------------------------------------------------------------------

def cmd_grep(lines: list[str], h2_list: list[Section], keyword: str, ctx: int) -> None:
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    hits: list[tuple[Section, int]] = []  # (section, 1-based lineno)

    all_sections: list[Section] = []
    for h2 in h2_list:
        all_sections.append(h2)
        all_sections.extend(h2.children)

    def find_section(lineno: int) -> Section | None:
        best = None
        for sec in all_sections:
            if sec.start <= lineno <= sec.end:
                if best is None or sec.level > best.level:
                    best = sec
            elif sec.start > lineno:
                break
        return best

    for i, line in enumerate(lines):
        if pattern.search(line):
            lineno = i + 1
            sec = find_section(lineno)
            if sec:
                hits.append((sec, lineno))

    if not hits:
        print(f"未找到 \"{keyword}\"")
        return

    # Group by section
    from collections import OrderedDict
    grouped: OrderedDict[int, tuple[Section, list[int]]] = OrderedDict()
    for sec, lineno in hits:
        key = sec.start
        if key not in grouped:
            grouped[key] = (sec, [])
        grouped[key][1].append(lineno)

    print(f"找到 \"{keyword}\" 共 {len(hits)} 处，分布在 {len(grouped)} 个章节：\n")

    for sec, linenos in grouped.values():
        parent_info = ""
        if sec.level == 3:
            for h2 in h2_list:
                if sec in h2.children:
                    parent_info = f" (属于 {h2.title})"
                    break
        level_mark = "##" if sec.level == 2 else "###"
        print(f"📍 {level_mark} {sec.title}{parent_info} — {len(linenos)} 处命中")

        for ln in linenos:
            start = max(0, ln - 1 - ctx)
            end = min(len(lines), ln - 1 + ctx + 1)
            for j in range(start, end):
                marker = ">>>" if j == ln - 1 else "   "
                print(f"  {marker} L{j+1}: {lines[j]}", end="")
                if not lines[j].endswith("\n"):
                    print()
            print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="context.md 按需读取——富目录 / 章节选读 / 关键词定位"
    )
    parser.add_argument("project", help="项目名（projects/ 下的目录名）")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--toc", action="store_true", help="输出章节索引")
    group.add_argument("--sections", type=str, help="按章节名选读（逗号分隔，支持 父/子 格式）")
    group.add_argument("--grep", type=str, help="关键词定位")

    parser.add_argument("--context", type=int, default=3, help="--grep 上下文行数（默认 3）")

    args = parser.parse_args()
    path = find_context(args.project)

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    h2_list = parse_sections(lines)

    if args.toc:
        cmd_toc(lines, h2_list)
    elif args.sections:
        queries = [q.strip() for q in args.sections.split(",")]
        cmd_sections(lines, h2_list, queries)
    elif args.grep:
        cmd_grep(lines, h2_list, args.grep, args.context)


if __name__ == "__main__":
    main()
