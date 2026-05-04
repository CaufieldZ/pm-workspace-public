"""gen_flow_base.py · 流程图 drawio 生成器

声明 nodes/edges/lanes，输出 .drawio + .drawio.svg + .drawio.png。

设计哲学（参 jgraph/drawio-mcp/shared/xml-reference.md）：
- rigid grid: x = col*180+40, y = row*120+40
- branch 默认自动布局（topo BFS + decision 侧分支）
- swimlane 走官方 flat lane 模式（lane_height=150, x=120+col*180, y=45）
- 不算坐标细节、不写 exitX/entryX——drawio 内置 ELK 接管 edge routing

用法（项目侧 gen_flow_v1.py 调用）:
    from gen_flow_base import render_flowchart
    render_flowchart(
        output_path="deliverables/flow-xxx-v1",  # 或 .drawio / .html 都行,自动剥离扩展名
        title="...",
        subtitle="...",
        charts=[
            {"type": "branch",   "title": "...", "nodes": [...], "edges": [...]},
            {"type": "swimlane", "title": "...", "lanes": [...], "nodes": [...], "edges": [...]},
        ],
    )
"""

import html
import os
import shutil
import subprocess
from collections import defaultdict, deque
from pathlib import Path

# ── draw.io CLI 定位 ─────────────────────────────────────
_DRAWIO_CANDIDATES = [
    "/Applications/draw.io.app/Contents/MacOS/draw.io",
    "draw.io",
    "drawio",
]


def _find_drawio_cli():
    for c in _DRAWIO_CANDIDATES:
        if c.startswith("/") and Path(c).exists():
            return c
        if shutil.which(c):
            return c
    return None


# ── Claude Design 视觉常量 ───────────────────────────────
FONT = "PingFang SC,Noto Sans SC,sans-serif"
INK = "#1F2329"
EDGE_INK = "#1F2329"

NODE_STYLE = {
    "terminal": ("rounded=1;arcSize=40;",            "#E8E5FF", INK),
    "process":  ("rounded=1;arcSize=18;",            "#E7EFFE", INK),
    "decision": ("rhombus;",                         "#FDF3D5", INK),
    "success":  ("rounded=1;arcSize=18;",            "#D9F5E5", "#0ECB81"),
    "fail":     ("rounded=1;arcSize=18;",            "#FEE3E6", "#F6465D"),
}
NODE_SIZE_MIN = {
    "terminal": (140, 50),
    "process":  (140, 50),
    "decision": (160, 70),
    "success":  (140, 50),
    "fail":     (140, 50),
}

LANE_COLORS = ["#F5F5F5", "#E8F4F8", "#FFF0E6", "#E8F5E9", "#FFF9E6", "#FCE4EC"]

GRID_X = 200  # 列间距 (中心到中心)
GRID_Y = 140  # 行间距 (branch 模式)
LANE_H = 150  # swimlane 单泳道高度
LANE_TITLE_W = 110  # swimlane 左侧 title 区宽度


def _label_size(label: str, typ: str):
    """按文字长度估算节点尺寸. CJK 1 字符占 14px, 多行高度按行数累加."""
    lines = str(label).split("\n")
    max_chars = max((len(line) for line in lines), default=0)
    min_w, min_h = NODE_SIZE_MIN[typ]
    pad_x = 28 if typ != "decision" else 50
    pad_y = 18 if typ != "decision" else 30
    w = max(min_w, max_chars * 14 + pad_x)
    h = max(min_h, len(lines) * 22 + pad_y)
    return w, h


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True).replace("\n", "&#xa;")


def _node_style(typ: str) -> str:
    shape, fill, stroke = NODE_STYLE[typ]
    return (
        f"{shape}whiteSpace=wrap;html=1;"
        f"fillColor={fill};strokeColor={stroke};strokeWidth=1.5;"
        f"fontSize=12;fontFamily={FONT};fontColor={INK};"
    )


_PORT_MAP = {
    "top":    ("0.5", "0"),
    "bottom": ("0.5", "1"),
    "left":   ("0", "0.5"),
    "right":  ("1", "0.5"),
}


def _edge_style(sp=None, tp=None, exit_dy=0) -> str:
    base = (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
        f"strokeColor={EDGE_INK};strokeWidth=1.2;"
        "endArrow=block;endFill=1;endSize=7;"
        f"fontSize=11;fontFamily={FONT};fontColor={INK};"
        "labelBackgroundColor=#FFFFFF;"
    )
    if sp and sp in _PORT_MAP:
        x, y = _PORT_MAP[sp]
        base += f"exitX={x};exitY={y};exitDx=0;exitDy={exit_dy};"
    if tp and tp in _PORT_MAP:
        x, y = _PORT_MAP[tp]
        base += f"entryX={x};entryY={y};entryDx=0;entryDy={-exit_dy};"
    return base


# ── branch 自动布局: topo BFS + decision 侧分支 ──────────
def _layout_branch(nodes, edges):
    """返回 {node_id: (col, row)}.

    用户在 node 上提供 col/row 则覆盖自动值.
    """
    explicit = {n["id"]: (n.get("col"), n.get("row")) for n in nodes}
    out_adj = defaultdict(list)
    in_count = defaultdict(int)
    for e in edges:
        out_adj[e["s"]].append(e["t"])
        in_count[e["t"]] += 1

    row = {}
    queue = deque()
    for n in nodes:
        if in_count[n["id"]] == 0:
            row[n["id"]] = 0
            queue.append(n["id"])
    while queue:
        nid = queue.popleft()
        for child in out_adj[nid]:
            new_r = row[nid] + 1
            if child not in row or row[child] < new_r:
                row[child] = new_r
                queue.append(child)
    for n in nodes:
        row.setdefault(n["id"], 0)

    by_row = defaultdict(list)
    for nid, r in row.items():
        by_row[r].append(nid)

    col = {}
    parent_first = {n["id"]: None for n in nodes}
    for e in edges:
        if parent_first[e["t"]] is None:
            parent_first[e["t"]] = e["s"]

    for r in sorted(by_row):
        siblings_seen = defaultdict(list)
        for nid in by_row[r]:
            p = parent_first[nid]
            siblings_seen[p].append(nid)

        for p, children in siblings_seen.items():
            if p is None:
                for i, nid in enumerate(children):
                    col[nid] = i
                continue
            p_col = col.get(p, 0)
            offsets = [0, -1, 1, -2, 2, -3, 3]
            for i, nid in enumerate(children):
                c = p_col + offsets[min(i, len(offsets) - 1)]
                while c in col.values() and any(
                    col.get(other) == c and row.get(other) == r
                    for other in by_row[r] if other != nid
                ):
                    c += 1 if c >= p_col else -1
                col[nid] = c

    result = {}
    for n in nodes:
        nid = n["id"]
        ec, er = explicit.get(nid, (None, None))
        result[nid] = (ec if ec is not None else col[nid],
                       er if er is not None else row[nid])
    return result


# ── XML 构建 ────────────────────────────────────────────
def _branch_diagram(chart):
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']

    pos = _layout_branch(chart["nodes"], chart["edges"])

    cols = [pos[n["id"]][0] for n in chart["nodes"]]
    rows = [pos[n["id"]][1] for n in chart["nodes"]]
    min_col = min(cols)
    min_row = min(rows)
    x_offset = -min_col * GRID_X + 40
    y_offset = -min_row * GRID_Y + 40

    for n in chart["nodes"]:
        nid = n["id"]
        c, r = pos[nid]
        w, h = _label_size(n["label"], n["type"])
        x = c * GRID_X + x_offset - w // 2 + 70
        y = r * GRID_Y + y_offset - h // 2 + 25
        cells.append(
            f'<mxCell id="{_esc(nid)}" value="{_esc(n["label"])}" '
            f'style="{_node_style(n["type"])}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>'
            f'</mxCell>'
        )
    for i, e in enumerate(chart["edges"]):
        eid = f"e_{i}"
        label = _esc(e.get("label", ""))
        style = _edge_style(e.get("sp"), e.get("tp"))
        cells.append(
            f'<mxCell id="{eid}" value="{label}" style="{style}" '
            f'edge="1" parent="1" source="{_esc(e["s"])}" target="{_esc(e["t"])}">'
            f'<mxGeometry relative="1" as="geometry"/></mxCell>'
        )
    return cells


def _swimlane_diagram(chart):
    """泳道图 (drawio 原生 swimlane). 一次性几何模型, 不打补丁:

    - 节点固定尺寸: process/terminal/success/fail 160x60, decision 180x80
    - 同 lane 同 col 重复 → 自动 bump 后续节点到下一个 col
    - 节点 parent=lane (swimlane), 坐标相对 lane content 区 (startSize=110 之后)
    - 边端口自动分配:
        * 同 lane: sp=right/left, tp=left/right (按 col 方向)
        * 跨 lane: sp=top/bottom, tp=bottom/top (按 lane idx 方向)
        * 用户给的 sp/tp 优先
    - 同源多带 label 边: 出口 y 上下错开 (exitDy ±15) + label y 偏移
    - 跨 ≥2 col 边的 label: 移到 x=-0.5 (靠 source 1/4 处)
    - 边 label 带白底
    """
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']

    lanes = chart["lanes"]
    LH = 130
    TITLE_W = 110
    PAD = 30
    NODE_W, NODE_H = 160, 60
    DEC_W, DEC_H = 180, 80
    COL_GAP = 80

    def nw(n):
        return DEC_W if n["type"] == "decision" else NODE_W
    def nh(n):
        return DEC_H if n["type"] == "decision" else NODE_H

    nodes = [dict(n) for n in chart["nodes"]]
    seen = {}
    for n in nodes:
        c = n["col"]
        while (n["lane"], c) in seen:
            c += 1
        if c != n["col"]:
            print(f"[flowchart] auto-bump {n['id']} col {n['col']} -> {c}")
        n["col"] = c
        seen[(n["lane"], c)] = n["id"]

    all_cols = sorted({n["col"] for n in nodes})
    col_w = {c: max((nw(n) for n in nodes if n["col"] == c), default=NODE_W) + COL_GAP
             for c in all_cols}
    col_cx_in_lane = {}  # x relative to lane left edge (lane left = 0, content area starts at TITLE_W)
    cur = TITLE_W + PAD
    for c in all_cols:
        col_cx_in_lane[c] = cur + col_w[c] // 2
        cur += col_w[c]
    canvas_w = cur + PAD

    lane_id = {}
    for i, lane in enumerate(lanes):
        lid = f"lane_{i}"
        lane_id[lane] = lid
        color = LANE_COLORS[i % len(LANE_COLORS)]
        cells.append(
            f'<mxCell id="{lid}" value="{_esc(lane)}" '
            f'style="swimlane;horizontal=0;startSize={TITLE_W};fillColor={color};'
            f'strokeColor=#E5E6EB;swimlaneFillColor=#FFFFFF;html=1;fontSize=13;fontStyle=1;'
            f'fontFamily={FONT};fontColor={INK};align=center;verticalAlign=middle;" '
            f'vertex="1" parent="1">'
            f'<mxGeometry x="0" y="{i * LH}" width="{canvas_w}" height="{LH}" as="geometry"/>'
            f'</mxCell>'
        )

    for n in nodes:
        w, h = nw(n), nh(n)
        x = col_cx_in_lane[n["col"]] - w // 2
        y = (LH - h) // 2
        cells.append(
            f'<mxCell id="{_esc(n["id"])}" value="{_esc(n["label"])}" '
            f'style="{_node_style(n["type"])}" vertex="1" parent="{lane_id[n["lane"]]}">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>'
            f'</mxCell>'
        )

    node_col_map = {n["id"]: n["col"] for n in nodes}
    node_lane_map = {n["id"]: n["lane"] for n in nodes}
    lane_idx = {l: i for i, l in enumerate(lanes)}

    src_total_label = defaultdict(int)
    for e in chart["edges"]:
        if e.get("label"):
            src_total_label[e["s"]] += 1

    src_label_seq = defaultdict(int)
    for i, e in enumerate(chart["edges"]):
        eid = f"e_{i}"
        label = _esc(e.get("label", ""))
        s_id, t_id = e["s"], e["t"]
        s_li = lane_idx[node_lane_map[s_id]]
        t_li = lane_idx[node_lane_map[t_id]]
        cross = s_li != t_li
        col_span = abs(node_col_map[t_id] - node_col_map[s_id])

        sp = e.get("sp") or ("bottom" if cross and t_li > s_li else
                             "top" if cross else
                             "right" if node_col_map[t_id] >= node_col_map[s_id] else "left")
        tp = e.get("tp") or ("top" if cross and t_li > s_li else
                             "bottom" if cross else
                             "left" if node_col_map[t_id] >= node_col_map[s_id] else "right")

        nth = src_label_seq[s_id] if e.get("label") else -1
        if e.get("label"):
            src_label_seq[s_id] += 1
        total = src_total_label[s_id]

        exit_dy = 0
        if total >= 2 and nth >= 0 and sp in ("right", "left"):
            exit_dy = [-15, 15, -30, 30][min(nth, 3)]

        style = _edge_style(sp, tp, exit_dy)

        if label:
            x_pos = "-0.5" if col_span >= 2 else "0"
            y_off = [0, -18, 18, -36, 36][min(nth, 4)] if total >= 2 else 0
            x_attr = f' x="{x_pos}"' if x_pos != "0" else ""
            offset_xml = f'<mxPoint x="0" y="{y_off}" as="offset"/>' if y_off else ""
            geom = f'<mxGeometry relative="1"{x_attr} as="geometry">{offset_xml}</mxGeometry>'
        else:
            geom = '<mxGeometry relative="1" as="geometry"/>'

        cells.append(
            f'<mxCell id="{eid}" value="{label}" style="{style}" '
            f'edge="1" parent="1" source="{_esc(s_id)}" target="{_esc(t_id)}">'
            f'{geom}</mxCell>'
        )
    return cells


def _build_mxfile(charts):
    diagrams = []
    for i, chart in enumerate(charts):
        name = chart.get("title", f"page-{i+1}")[:40]
        if chart["type"] == "branch":
            cells = _branch_diagram(chart)
        elif chart["type"] == "swimlane":
            cells = _swimlane_diagram(chart)
        else:
            raise ValueError(f"unknown chart type: {chart['type']}")
        body = "\n        ".join(cells)
        diagrams.append(
            f'  <diagram id="d_{i}" name="{_esc(name)}">\n'
            f'    <mxGraphModel adaptiveColors="auto" dx="1400" dy="900" grid="0" '
            f'pageWidth="1400" pageHeight="900" math="0" shadow="0">\n'
            f'      <root>\n'
            f'        {body}\n'
            f'      </root>\n'
            f'    </mxGraphModel>\n'
            f'  </diagram>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxfile host="drawio" version="28.2.8">\n'
        + "\n".join(diagrams)
        + '\n</mxfile>\n'
    )


# ── 导出 ─────────────────────────────────────────────────
def _export(drawio_path: Path, page_count: int, formats=("svg", "png")):
    cli = _find_drawio_cli()
    if not cli:
        print(f"[flowchart] WARN draw.io CLI not found, skip export")
        return []
    outputs = []
    base = drawio_path.with_suffix("")
    for fmt in formats:
        for p in range(1, page_count + 1):
            suffix = f"-{p}" if page_count > 1 else ""
            out_path = base.parent / f"{base.name}{suffix}.drawio.{fmt}"
            cmd = [cli, "-x", "-f", fmt, "-e", "-b", "20", "-p", str(p - 1),
                   "-o", str(out_path), str(drawio_path)]
            if fmt == "png":
                cmd[7:7] = ["-s", "2"]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode != 0 or not out_path.exists():
                print(f"[flowchart] WARN export {fmt} p{p} failed: {r.stderr[:200]}")
                continue
            outputs.append(out_path)
            if fmt == "png":
                _repair_png_iend(out_path)
    return outputs


def _repair_png_iend(p: Path):
    """draw.io CLI 在 -e 模式下偶发截断 PNG IEND 块, 修一下."""
    data = p.read_bytes()
    IEND = b"\x00\x00\x00\x00IEND\xaeB`\x82"
    if data.endswith(IEND):
        return
    if data.endswith(b"\x00\x00\x00\x00"):
        data = data[:-4]
    p.write_bytes(data + IEND)


# ── 主入口 ───────────────────────────────────────────────
def render_flowchart(output_path, title, subtitle, charts):
    """生成 .drawio + .drawio.svg + .drawio.png.

    output_path: 路径 base, 扩展名会被剥离 (.html / .drawio / 无扩展都接受)
    title/subtitle: 当前未直接渲染到 drawio 内, 调用方在 PRD/HTML 容器侧加标注
    charts: list[dict], 每条 type ∈ {branch, swimlane}
    """
    out = Path(output_path)
    if out.suffix:
        out = out.with_suffix("")
    out.parent.mkdir(parents=True, exist_ok=True)

    xml = _build_mxfile(charts)
    drawio_path = out.with_suffix(".drawio")
    drawio_path.write_text(xml, encoding="utf-8")

    exported = _export(drawio_path, page_count=len(charts))
    print(f"[flowchart] wrote {drawio_path} ({len(charts)} charts)")
    for p in exported:
        print(f"           + {p}")
    return drawio_path
