# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""
gen_flow_base.py · 流程图 HTML 生成器

用法(项目侧 gen_flow_v1.py 调用):
    from gen_flow_base import render_flowchart
    render_flowchart(
        output_path="deliverables/flow-xxx-v1.html",
        title="流程图 Demo · 私募",
        subtitle="...",
        charts=[
            {"type": "branch",   "title": "...", "subtitle": "...", "nodes": [...], "edges": [...]},
            {"type": "swimlane", "title": "...", "subtitle": "...", "lanes": [...], "nodes": [...], "edges": [...]},
        ],
    )

依赖 CDN:
- @antv/x6@2.18.1
- dagre@0.8.5

节点类型: terminal / process / decision / success / fail
节点字段: id, type, label; swimlane 额外需要 lane + col
边字段:   s(source), t(target), label(可选); swimlane 可选 sp/tp 端口覆盖
"""

import json
import os
import sys
from pathlib import Path

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(_ROOT, 'scripts'))

from lib.html_builder import expand_css_imports, write_html

BASE_DIR = Path(__file__).parent

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<script src="https://unpkg.com/@antv/x6@2.18.1/dist/index.js"></script>
<script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
<style>
{css}
</style>
</head>
<body>

<div class="page-title">{title}</div>
<div class="page-sub">{subtitle}</div>

{sections}

<script>
{core_js}

// ── 数据注入 ───────────────────────────────
const CHARTS = {charts_json};

// ── 渲染 ──────────────────────────────────
CHARTS.forEach((chart, idx) => {{
  if (chart.type === 'branch') {{
    window.FLOWCHART.renderBranch(`g-flow-${{idx}}`, chart);
  }} else if (chart.type === 'swimlane') {{
    window.FLOWCHART.renderSwimlane({{
      laneBgId: `lane-bg-${{idx}}`,
      laneInnerId: `lane-inner-${{idx}}`,
      laneWrapSelector: `#lane-wrap-${{idx}}`,
      graphId: `g-lane-${{idx}}`,
      checkOutId: `check-out-${{idx}}`,
    }}, chart);
  }}
}});
</script>

</body>
</html>
"""

BRANCH_SECTION = """<div class="section-label">—— {num} · 分支流程图 · {short_title} ——</div>
<div class="whiteboard">
  <div class="wb-title">{title}</div>
  <div class="wb-sub">{subtitle}</div>
  <div id="g-flow-{idx}" class="g-flow"></div>
</div>
"""

SWIMLANE_SECTION = """<div class="section-label">—— {num} · 泳道图 · {short_title} ——</div>
<div class="whiteboard">
  <div class="wb-title">{title}</div>
  <div class="wb-sub">{subtitle}</div>
  <div class="lane-wrap" id="lane-wrap-{idx}">
    <div class="lane-inner" id="lane-inner-{idx}">
      <div class="lane-bg" id="lane-bg-{idx}"></div>
      <div class="lane-header-col">
{lane_headers}
      </div>
      <div class="g-lane" id="g-lane-{idx}"></div>
    </div>
  </div>
  <div class="check-out" id="check-out-{idx}"></div>
</div>
"""


def render_flowchart(output_path, title, subtitle, charts):
    """把 charts 列表渲染成单个 HTML 文件。

    charts: list of dict,每条 dict 必须含 type ∈ {'branch','swimlane'}
    """
    css = expand_css_imports(
        (BASE_DIR / "flowchart.css").read_text(encoding="utf-8"),
        BASE_DIR,
    )
    core_js = (BASE_DIR / "flowchart-core.js").read_text(encoding="utf-8")

    sections = []
    for idx, chart in enumerate(charts):
        num = f"{idx + 1:02d}"
        short = chart.get("short_title") or chart.get("title", "")[:20]
        if chart["type"] == "branch":
            sections.append(BRANCH_SECTION.format(
                idx=idx, num=num,
                short_title=short,
                title=chart["title"],
                subtitle=chart.get("subtitle", ""),
            ))
        elif chart["type"] == "swimlane":
            lane_headers = "\n".join(
                f"        <div>{lane}</div>" for lane in chart["lanes"]
            )
            sections.append(SWIMLANE_SECTION.format(
                idx=idx, num=num,
                short_title=short,
                title=chart["title"],
                subtitle=chart.get("subtitle", ""),
                lane_headers=lane_headers,
            ))
        else:
            raise ValueError(f"unknown chart type: {chart['type']}")

    html = HTML_TEMPLATE.format(
        title=title,
        subtitle=subtitle,
        css=css,
        core_js=core_js,
        sections="\n".join(sections),
        charts_json=json.dumps(charts, ensure_ascii=False),
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"[flowchart] wrote {out} ({len(charts)} charts, {len(html)} chars)")
    return out
