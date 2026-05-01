#!/usr/bin/env python3
"""scene-list.md → HTML 视觉版渲染器（按需触发）。

用法：
    python3 .claude/skills/scene-list/scripts/render_scene_list.py <项目名>

输入：projects/{项目名}/scene-list.md
输出：projects/{项目名}/deliverables/scene-list-{项目名}.html

设计原则：
- md 是 source of truth，HTML 是消费视图
- 自适应表头：不假设固定列数，按表头第一行动态生成 <th>
- 列语义识别：编号 / 优先级 / 设备 / 端 → 加 class
- 兼容现有 8 个项目（含 proj-queen 专属结构）
"""
from __future__ import annotations

import datetime
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.lib.html_builder import expand_css_imports, get_author, write_html  # noqa: E402

CSS_PATH = ROOT / ".claude" / "skills" / "scene-list" / "assets" / "scene-list.css"
FONTS_HREF = (
    "https://fonts.googleapis.com/css2"
    "?family=Noto+Sans+SC:wght@300;400;500;700;900"
    "&family=Noto+Serif+SC:wght@300;400;500;600;900"
    "&family=Lora:ital,wght@0,400..700;1,400..700"
    "&family=Poppins:wght@300;400;500;600;700"
    "&family=JetBrains+Mono:wght@400;500;600;700"
    "&display=swap"
)

TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
TABLE_DIVIDER_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$")


def split_row(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [c.strip() for c in inner.split("|")]


def col_class(header: str) -> str:
    """根据列名识别语义类。"""
    h = header.strip().lower()
    if h in ("编号", "#", "id") or "编号" in header:
        return "col-id"
    if h in ("场景", "场景名", "场景名称") or header in ("场景", "场景名"):
        return "col-name"
    if h == "p" or "优先级" in header or h in ("priority", "pri"):
        return "col-pri"
    if h in ("设备", "端", "platform", "plat") or "设备" in header or header in ("端",):
        return "col-dev"
    if "触发端" in header or "来源端" in header or header == "from" or "源端" in header:
        return "col-flow-from"
    if "响应端" in header or "目标端" in header or header == "to":
        return "col-flow-to"
    if header == "动作" or "动作" in header or header == "action":
        return "col-action"
    return ""


SCENE_ID_RE = re.compile(r"^([A-Z][A-Z0-9-]*[a-z]?)$")
VIEW_REF_RE = re.compile(
    r"View\s*\d+\s*[·•・]?\s*([A-Z][A-Z0-9]*-?\d*[a-z]?(?:/[A-Z][A-Z0-9]*-?\d*[a-z]?)*)"
)


def collect_id_map(sections: list[dict]) -> dict[str, str]:
    """从所有主表收集 编号 → 场景名 字典，供 flow 表反查。"""
    id_map: dict[str, str] = {}
    for sec in sections:
        for table in sec["tables"]:
            if not table:
                continue
            header = table[0]
            classes = [col_class(h) for h in header]
            try:
                id_idx = classes.index("col-id")
            except ValueError:
                continue
            name_idx = -1
            for idx, cls in enumerate(classes):
                if cls == "col-name":
                    name_idx = idx
                    break
            if name_idx < 0:
                for idx, h in enumerate(header):
                    if idx != id_idx and h.strip() not in ("", "View", "模块"):
                        name_idx = idx
                        break
            if name_idx < 0:
                continue
            for row in table[1:]:
                if id_idx >= len(row) or name_idx >= len(row):
                    continue
                sid = row[id_idx].strip()
                name = row[name_idx].strip()
                if sid and name and sid not in id_map:
                    id_map[sid] = name
    return id_map


def render_priority(text: str) -> str:
    """优先级 badge。"""
    raw = text.strip()
    if not raw:
        return ""
    norm = raw.upper().replace(" ", "")
    if norm in ("P0", "P0必做", "P0必上"):
        cls = "pri-p0"
    elif norm in ("P1",):
        cls = "pri-p1"
    elif norm in ("P2",):
        cls = "pri-p2"
    elif "V2" in norm or "V3" in norm:
        cls = "pri-v2"
    elif "后续" in raw or "迭代" in raw or norm in ("LATER", "FUTURE"):
        cls = "pri-future"
    elif raw in ("—", "-", "不做"):
        cls = "pri-skip"
    else:
        cls = "pri-p2"
    return f'<span class="pri {cls}">{html.escape(raw)}</span>'


def render_device(text: str) -> str:
    raw = text.strip()
    if not raw:
        return ""
    if "📱" in raw or "phone" in raw.lower() or raw in ("App", "app", "iOS", "Android", "H5"):
        cls = "dev-mob"
    elif "🖥" in raw or "web" in raw.lower() or raw in ("Web", "CMS", "MGT"):
        cls = "dev-web"
    else:
        cls = ""
    return f'<span class="dev {cls}">{html.escape(raw)}</span>'


def md_inline(text: str) -> str:
    """处理 markdown inline 元素（**bold** / `code` / 转义 HTML）。"""
    s = html.escape(text)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def render_cell(text: str, cls: str) -> str:
    if cls == "col-pri":
        return render_priority(text)
    if cls == "col-dev":
        return render_device(text)
    return md_inline(text)


def parse_md(md_text: str) -> dict:
    """解析 md → {title, note_lines, sections: [{title, paragraphs, table}]}."""
    lines = md_text.splitlines()
    title = ""
    note_lines: list[str] = []
    sections: list[dict] = []

    cur: dict | None = None
    in_table = False
    table_rows: list[list[str]] = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("# ") and not title:
            title = line[2:].strip()
            i += 1
            continue

        if line.startswith("> ") and cur is None and not sections:
            note_lines.append(line[2:].strip())
            i += 1
            continue

        if line.strip() == "---":
            i += 1
            continue

        if line.startswith("## "):
            if cur:
                if table_rows:
                    cur["tables"].append(table_rows)
                sections.append(cur)
            cur = {"title": line[3:].strip(), "paragraphs": [], "tables": []}
            in_table = False
            table_rows = []
            i += 1
            continue

        if cur is None:
            i += 1
            continue

        if TABLE_ROW_RE.match(line):
            row = split_row(line)
            if i + 1 < len(lines) and TABLE_DIVIDER_RE.match(lines[i + 1]):
                if table_rows:
                    cur["tables"].append(table_rows)
                table_rows = [row]
                in_table = True
                i += 2
                continue
            if in_table:
                table_rows.append(row)
                i += 1
                continue

        if line.strip() and cur is not None:
            in_table = False
            if table_rows:
                cur["tables"].append(table_rows)
                table_rows = []
            cur["paragraphs"].append(line.strip())

        i += 1

    if cur:
        if table_rows:
            cur["tables"].append(table_rows)
        sections.append(cur)

    return {"title": title, "note_lines": note_lines, "sections": sections}


def count_priorities(sections: list[dict]) -> dict:
    """统计 P0 / P1 / P2 / 后续 / 总场景数。"""
    counts = {"total": 0, "P0": 0, "P1": 0, "P2": 0, "later": 0}
    for sec in sections:
        for table in sec["tables"]:
            if not table:
                continue
            header = [h.strip() for h in table[0]]
            pri_idx = -1
            for idx, h in enumerate(header):
                if col_class(h) == "col-pri":
                    pri_idx = idx
                    break
            id_idx = -1
            for idx, h in enumerate(header):
                if col_class(h) == "col-id":
                    id_idx = idx
                    break
            for row in table[1:]:
                if id_idx >= 0 and id_idx < len(row):
                    if not row[id_idx].strip():
                        continue
                else:
                    continue
                counts["total"] += 1
                if pri_idx >= 0 and pri_idx < len(row):
                    p = row[pri_idx].strip().upper().replace(" ", "")
                    if p == "P0":
                        counts["P0"] += 1
                    elif p == "P1":
                        counts["P1"] += 1
                    elif p == "P2":
                        counts["P2"] += 1
                    elif "后续" in row[pri_idx] or "迭代" in row[pri_idx]:
                        counts["later"] += 1
    return counts


def render_flow_endpoint(text: str, id_map: dict[str, str]) -> str:
    """把 'View 1 · A-2' / 'A-2' / 'View 1 · A-1 + View 2 · D-1' 渲染成 chip + 下方场景名。"""
    raw = text.strip()
    if not raw:
        return '<div class="flow-ep flow-ep-empty">—</div>'

    parts = re.split(r"\s*[+]\s*", raw)
    chips = []
    for part in parts:
        m = VIEW_REF_RE.search(part)
        view_label = ""
        ids: list[str] = []
        if m:
            view_match = re.match(r"View\s*\d+", part)
            view_label = view_match.group(0) if view_match else ""
            id_str = m.group(1)
            ids = [s.strip() for s in id_str.split("/") if s.strip()]
        else:
            id_match = re.match(r"([A-Z][A-Z0-9-]*[a-z]?)", part.strip())
            if id_match:
                ids = [id_match.group(1)]

        if ids:
            id_html = " / ".join(f'<span class="flow-id">{html.escape(i)}</span>' for i in ids)
            names = [id_map.get(i, "") for i in ids]
            name_text = " / ".join(n for n in names if n)
            view_html = (
                f'<span class="flow-view">{html.escape(view_label)}</span>' if view_label else ""
            )
            name_html = (
                f'<div class="flow-name">{md_inline(name_text)}</div>' if name_text else ""
            )
            chips.append(
                f'<div class="flow-ep">{view_html}{id_html}{name_html}</div>'
            )
        else:
            chips.append(
                f'<div class="flow-ep flow-ep-text">{md_inline(part.strip())}</div>'
            )
    return "".join(chips) if len(chips) == 1 else f'<div class="flow-multi">{"".join(chips)}</div>'


def render_flow_table(table: list[list[str]], id_map: dict[str, str]) -> str:
    """跨端关联表：每行渲染成 [from] → [to] + 动作 + 描述 的 flow 卡片。"""
    if not table:
        return ""
    header = table[0]
    classes = [col_class(h) for h in header]

    def find_idx(target: str) -> int:
        for idx, cls in enumerate(classes):
            if cls == target:
                return idx
        return -1

    from_idx = find_idx("col-flow-from")
    to_idx = find_idx("col-flow-to")
    action_idx = find_idx("col-action")
    other_idxs = [
        i for i in range(len(header))
        if i not in (from_idx, to_idx, action_idx)
    ]

    rows_html = []
    for row in table[1:]:
        from_html = render_flow_endpoint(row[from_idx] if from_idx < len(row) else "", id_map)
        to_html = render_flow_endpoint(row[to_idx] if to_idx < len(row) else "", id_map)
        action_html = (
            md_inline(row[action_idx]) if 0 <= action_idx < len(row) else ""
        )
        other_html = []
        for idx in other_idxs:
            if idx < len(row) and row[idx].strip():
                other_html.append(f'<div class="flow-extra">{md_inline(row[idx])}</div>')

        rows_html.append(
            f'<div class="flow-row">'
            f'<div class="flow-line">'
            f'{from_html}'
            f'<div class="flow-arrow"><span class="flow-action">{action_html}</span></div>'
            f'{to_html}'
            f'</div>'
            f'{"".join(other_html)}'
            f'</div>'
        )
    return f'<div class="flow-tbl">{"".join(rows_html)}</div>'


def render_table(table: list[list[str]], id_map: dict[str, str]) -> str:
    if not table:
        return ""
    header = table[0]
    classes = [col_class(h) for h in header]

    if "col-flow-from" in classes and "col-flow-to" in classes:
        return render_flow_table(table, id_map)

    th_html = "".join(f"<th>{html.escape(h)}</th>" for h in header)
    body_rows: list[str] = []
    for row in table[1:]:
        cells = []
        for idx, val in enumerate(row):
            cls = classes[idx] if idx < len(classes) else ""
            inner = render_cell(val, cls)
            cell_cls = f' class="{cls}"' if cls else ""
            cells.append(f"<td{cell_cls}>{inner}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    tbl_cls = "tbl tbl-compact" if len(table) <= 5 else "tbl"
    return (
        f'<table class="{tbl_cls}">'
        f"<thead><tr>{th_html}</tr></thead>"
        f'<tbody>{"".join(body_rows)}</tbody>'
        "</table>"
    )


def render_section(sec: dict, id_map: dict[str, str]) -> str:
    parts = [f'<section class="sec">']
    parts.append(f"<h2>{md_inline(sec['title'])}</h2>")
    for p in sec["paragraphs"]:
        parts.append(f"<p>{md_inline(p)}</p>")
    for table in sec["tables"]:
        parts.append(render_table(table, id_map))
    parts.append("</section>")
    return "".join(parts)


def render_stats(counts: dict, n_sections: int) -> str:
    items = [
        ("Sections", str(n_sections), ""),
        ("Total scenes", str(counts["total"]), ""),
        ("P0", str(counts["P0"]), "must-ship"),
        ("P1", str(counts["P1"]), "enhance"),
        ("P2", str(counts["P2"]), "polish"),
        ("Later", str(counts["later"]), "future"),
    ]
    cards = []
    for lbl, val, sub in items:
        sub_html = f'<span class="sub">{html.escape(sub)}</span>' if sub else ""
        cards.append(
            f'<div class="stat"><div class="lbl">{lbl}</div>'
            f'<div class="val">{val}{sub_html}</div></div>'
        )
    return f'<div class="stats">{"".join(cards)}</div>'


def render_html(project: str, parsed: dict, css: str, gen_time: str, author: str) -> str:
    title = parsed["title"] or f"{project} · 场景清单"
    note_html = ""
    if parsed["note_lines"]:
        note_paras = "".join(f"<p>{md_inline(line)}</p>" for line in parsed["note_lines"])
        note_html = f'<div class="note">{note_paras}</div>'

    counts = count_priorities(parsed["sections"])
    stats_html = render_stats(counts, len(parsed["sections"]))
    id_map = collect_id_map(parsed["sections"])
    sections_html = "".join(render_section(s, id_map) for s in parsed["sections"])

    meta_bits = [
        f'<span>项目<strong>{html.escape(project)}</strong></span>',
        f'<span>生成<strong>{html.escape(gen_time)}</strong></span>',
    ]
    if author:
        meta_bits.append(f'<span>by<strong>{html.escape(author)}</strong></span>')

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS_HREF}" rel="stylesheet">
<style>
{css}
</style>
</head>
<body>
<div class="page">
  <header class="hd">
    <div class="eyebrow">scene list · 场景清单</div>
    <h1>{md_inline(title)}</h1>
    <div class="meta">{"".join(meta_bits)}</div>
  </header>
  {note_html}
  {stats_html}
  {sections_html}
  <footer>
    source: <code>projects/{html.escape(project)}/scene-list.md</code> · 修改请改 md 后重生
  </footer>
</div>
</body>
</html>
"""


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: render_scene_list.py <项目名>", file=sys.stderr)
        return 1
    project = sys.argv[1]
    md_path = ROOT / "projects" / project / "scene-list.md"
    if not md_path.exists():
        print(f"[err] not found: {md_path}", file=sys.stderr)
        return 2

    md_text = md_path.read_text(encoding="utf-8")
    parsed = parse_md(md_text)

    css = expand_css_imports(CSS_PATH.read_text(encoding="utf-8"), CSS_PATH.parent)

    gen_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    author = get_author()

    html_content = render_html(project, parsed, css, gen_time, author)

    out_path = ROOT / "projects" / project / "deliverables" / f"scene-list-{project}.html"
    write_html(str(out_path), html_content)

    counts = count_priorities(parsed["sections"])
    print(
        f"[ok] {out_path.relative_to(ROOT)} · "
        f"{len(parsed['sections'])} sections · "
        f"{counts['total']} scenes (P0×{counts['P0']} P1×{counts['P1']} "
        f"P2×{counts['P2']} later×{counts['later']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
