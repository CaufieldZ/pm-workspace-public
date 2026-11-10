"""PRD md 硬错扫描：只查「会把文档弄坏」的几类，写法交给作者。

查什么：
    - 占位符没填完（{{ 待填 / TODO / TBD）
    - Confluence 渲染不了的写法：mermaid / PlantUML 代码块、水平线 ---、引用块 >
    - 图片 alt 为空
    - 埋点「应埋点平台」填了服务端 / 后台（Platform C 只做 APP / Web 端埋点）
    - 埋点表表头不是固定的 10 列（推送合并单元格与 xlsx 导出按表头认表，改了就失效）

暴露：
    scan_prd_structural_md(md_text) -> dict  # 各维度命中列表 + scene_count_observed

调用方：check_prd_md.sh（交付前全量）、scripts/hook_check_prd_content.py（写入时只看新增行）。
"""
from __future__ import annotations

import re
from typing import Iterator

from .patterns import PLACEHOLDER_TOKENS

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE_RE = re.compile(r"^```")
_DIAGRAM_FENCE_RE = re.compile(r"^```\s*(mermaid|plantuml|puml)\b", re.IGNORECASE)
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
# 水平线：一行仅 3+ 个连字符。表格分隔行 |---| 含 | 不匹配，天然豁免。
_HORIZONTAL_RULE_RE = re.compile(r"^-{3,}\s*$")


def _iter_lines_with_h2(text: str) -> Iterator[tuple[int, str, str, str, bool]]:
    """逐行迭代 md，产生 (line_no, line_text, current_h1, current_h2, in_heading)。

    跳过 fenced codeblock 内容 + HTML 注释块（<!-- ... -->）。
    """
    in_fence = False
    in_html_comment = False
    current_h1 = ""
    current_h2 = ""
    for i, line in enumerate(text.splitlines(), 1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not in_html_comment and "<!--" in line and "-->" not in line:
            in_html_comment = True
            continue
        if in_html_comment:
            if "-->" in line:
                in_html_comment = False
            continue
        if "<!--" in line and "-->" in line:
            continue
        m = _HEADING_RE.match(line)
        if m:
            hashes, title = m.groups()
            if len(hashes) == 1:
                current_h1 = title.strip()
                current_h2 = ""
            elif len(hashes) == 2:
                current_h2 = title.strip()
            yield i, line, current_h1, current_h2, True
            continue
        yield i, line, current_h1, current_h2, False


def _gather_table_cells(text: str) -> list[tuple[str, str, int, dict[str, str]]]:
    """提取 md 表格 cell：[(cell_text, header_text, line_no, row_dict), ...]"""
    cells: list[tuple[str, str, int, dict[str, str]]] = []
    in_fence = False
    table_headers: list[str] = []
    in_table_body = False
    for i, line in enumerate(text.splitlines(), 1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if _HEADING_RE.match(line) or not _TABLE_ROW_RE.match(line):
            in_table_body = False
            table_headers = []
            continue
        if _TABLE_SEP_RE.match(line):
            in_table_body = True
            continue
        cells_in_line = [c.strip() for c in line.strip("|").split("|")]
        if not in_table_body and not table_headers:
            table_headers = cells_in_line
            continue
        row_dict = {
            (table_headers[ci] if ci < len(table_headers) else f"_col{ci}"): ct
            for ci, ct in enumerate(cells_in_line)
        }
        for col_idx, cell_text in enumerate(cells_in_line):
            if not cell_text:
                continue
            header = table_headers[col_idx] if col_idx < len(table_headers) else ""
            cells.append((cell_text, header, i, row_dict))
    return cells


def _scan_server_platform_tracking(md_text: str) -> list[str]:
    """埋点表「应埋点平台」列写了服务端 / 后台类（CMS）→ 命中。"""
    hits: list[str] = []
    for cell_text, header, line_no, row_dict in _gather_table_cells(md_text):
        if header != "应埋点平台":
            continue
        low = cell_text.lower()
        if not (("服务端" in cell_text) or ("后台" in cell_text) or ("cms" in low)):
            continue
        ev = row_dict.get("事件英文名", "").strip("`")
        ctx = f"事件 {ev}" if ev else cell_text
        hits.append(f"L{line_no}: 应埋点平台={cell_text}（{ctx}）→ 只做 APP / Web 端埋点")
    return hits


TRACKING_HEADER = ["所属页面", "事件中文名", "事件英文名", "属性中文名", "属性英文名",
                   "数据类型", "是否必填", "数据值示例", "应埋点平台", "触发机制"]


def _scan_tracking_header(md_text: str) -> list[str]:
    """表头含「事件英文名」的表必须是固定 10 列表头（列名、顺序、列数都不能变）。"""
    hits: list[str] = []
    lines = md_text.splitlines()
    in_fence = False
    for i, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or not _TABLE_ROW_RE.match(line) or "事件英文名" not in line:
            continue
        if i + 1 >= len(lines) or not _TABLE_SEP_RE.match(lines[i + 1]):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells != TRACKING_HEADER:
            hits.append(f"L{i + 1}: 埋点表头应为「{' | '.join(TRACKING_HEADER)}」，实际「{' | '.join(cells)}」")
    return hits


def scan_prd_structural_md(md_text: str) -> dict:
    """扫 md PRD 的硬错。哪些算 FAIL 由调用方按 patterns.prd_fail_keys 决定。"""
    placeholders = [kw for kw in PLACEHOLDER_TOKENS if kw in md_text]
    if "{{ 待填" in md_text:
        placeholders.append("{{ 待填")

    diagram_code_hits = [
        f"L{i}: {line.strip()}"
        for i, line in enumerate(md_text.splitlines(), 1)
        if _DIAGRAM_FENCE_RE.match(line)
    ]

    broken_image_alt: list[str] = []
    horizontal_rule_hits: list[str] = []
    blockquote_hits: list[str] = []
    scene_count_observed = 0

    for line_no, line, _h1, _h2, in_heading in _iter_lines_with_h2(md_text):
        if in_heading:
            if re.search(r"^##+ \d+\.\d+\s+[A-Z][-\w]*\s*·", line):
                scene_count_observed += 1
            continue
        for m in re.finditer(r"!\[\]\(([^)]+)\)", line):
            broken_image_alt.append(f"L{line_no}: empty alt for {m.group(1)}")
        if _HORIZONTAL_RULE_RE.match(line):
            horizontal_rule_hits.append(f"L{line_no}: {line.rstrip()}")
        if re.match(r"^\s*>", line):
            blockquote_hits.append(f"L{line_no}: {line.rstrip()}")

    return {
        "placeholders": placeholders,
        "diagram_code_hits": diagram_code_hits,
        "broken_image_alt": broken_image_alt,
        "horizontal_rule_hits": horizontal_rule_hits,
        "blockquote_hits": blockquote_hits,
        "server_platform_tracking": _scan_server_platform_tracking(md_text),
        "tracking_header_hits": _scan_tracking_header(md_text),
        "scene_count_observed": scene_count_observed,
    }
