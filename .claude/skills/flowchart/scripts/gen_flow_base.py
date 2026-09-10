"""gen_flow_base.py · 流程图 mermaid 生成器

声明 nodes/edges/lanes 或 states/transitions，输出 `.mmd` + `.mmd.svg` + `.mmd.png`。
单一引擎 mermaid（mmdc），按 chart `type` 自动选图型：

    branch   → flowchart TB        单角色 DAG / 决策分支
    swimlane → swimlane-beta TB    多角色泳道（顶层 subgraph = 一条泳道）
    state    → stateDiagram-v2     状态机 / 生命周期（回路天然支持）

视觉由随脚本生成的 mermaid 配置决定：base 主题 + 本工区色板 + neo look +
顶层 `htmlLabels: false`（产出真 `<text>` 而非 foreignObject，Confluence / Inkscape 可读）。
mmdc 需要的 Chromium 由 `_find_chromium()` 探测后写 puppeteer config 传入；渲染失败直接抛错。

用法（项目侧 gen_flow_v1.py 调用）:
    from gen_flow_base import render_flowchart
    render_flowchart(
        output_path="deliverables/flow-xxx-v1",   # 扩展名会被剥离
        title="流程图 · XXX",
        subtitle="...",
        charts=[
            {"type": "branch",   "nodes": [...],  "edges": [...]},
            {"type": "swimlane", "lanes": [...],  "nodes": [...], "edges": [...]},
            {"type": "state",    "states": [...], "transitions": [...]},
        ],
    )
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

# ── 视觉常量（与 PRD / IMAP / 原型同一套 Claude Design 色板）──
FONT = "PingFang SC, Noto Sans SC, Helvetica Neue, Arial, sans-serif"
INK = "#1F2329"
EDGE_INK = "#1F2329"

# 节点语义：type → (mermaid 形状, fill, stroke)
NODE_STYLE = {
    "terminal": ("stadium", "#E8E5FF", INK),
    "process":  ("rect",    "#E7EFFE", INK),
    "decision": ("diamond", "#FDF3D5", INK),
    "success":  ("rect",    "#D9F5E5", "#0ECB81"),
    "fail":     ("rect",    "#FEE3E6", "#F6465D"),
}

# 状态机 kind → (fill, stroke)。active 强调态 / terminal 普通终态 / rejected 异常终态
STATE_KIND_STYLE = {
    "active":   ("#D9F5E5", "#0ECB81"),
    "terminal": ("#E8E5FF", INK),
    "rejected": ("#FEE3E6", "#F6465D"),
}

_SHAPE_WRAP = {
    "stadium": ("([", "])"),
    "rect":    ("[", "]"),
    "diamond": ("{", "}"),
}

# classDef 只吃颜色部分
_NODE_COLORS = {t: (fill, stroke) for t, (_, fill, stroke) in NODE_STYLE.items()}


def _node_shape(typ: str) -> tuple[str, str]:
    """节点 type → mermaid 形状包裹。拼错时列出有效取值，不抛裸 KeyError。"""
    if typ not in NODE_STYLE:
        raise ValueError(
            f"unknown node type: {typ!r}; supported: {sorted(NODE_STYLE)}"
        )
    return _SHAPE_WRAP[NODE_STYLE[typ][0]]


# ── mmdc 的 Chromium 探测 ────────────────────────────────
# mmdc 不带浏览器，必须给 -p puppeteer config 指路，否则报
# "Could not find chrome-headless-shell" 且退出码非 0。
_CHROMIUM_GLOBS = [
    "~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell",
    "~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell",
    "~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium",
    "~/.cache/ms-playwright/chromium-*/chrome-linux/chrome",
    "~/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def _find_chromium():
    """环境变量优先，再扫 Playwright / puppeteer 缓存，最后系统 Chrome。找不到返回 None。"""
    env = os.environ.get("PUPPETEER_EXECUTABLE_PATH")
    if env and Path(env).exists():
        return env
    for pattern in _CHROMIUM_GLOBS:
        hits = sorted(glob.glob(str(Path(pattern).expanduser())))
        if hits:
            return hits[-1]
    return None


def _write_mermaid_config(tmp: Path) -> Path:
    """本工区统一的 mermaid 主题。htmlLabels 必须在顶层——嵌在 flowchart 下不生效。"""
    cfg = {
        "theme": "base",
        "look": "neo",
        "htmlLabels": False,
        "securityLevel": "strict",
        # 0 = 每次随机。路径控制点会抖动，几何等价但 SVG/PNG 字节每跑一次都不同
        # （产出的 .svg 进 git，会制造无意义 diff）。钉死种子换可复现，肉眼无差。
        "handDrawnSeed": 42,
        "themeVariables": {
            "fontFamily": FONT,
            "fontSize": "15px",
            "primaryColor": "#E7EFFE",
            "primaryTextColor": INK,
            "primaryBorderColor": INK,
            "lineColor": EDGE_INK,
            "secondaryColor": "#E8E5FF",
            "tertiaryColor": "#FDF3D5",
            "background": "#FFFFFF",
            "mainBkg": "#E7EFFE",
            "nodeBorder": INK,
            "clusterBkg": "#F7F8FA",
            "clusterBorder": INK,
            "edgeLabelBackground": "#FFFFFF",
            "titleColor": INK,
            # neo look 默认给节点描边挂渐变：primaryBorderColor → secondaryBorderColor。
            # 不设 secondaryBorderColor 时末端是 mermaid 自派的浅绿，表现为「边框一半深一半绿」。
            # 关掉渐变，描边就是 nodeBorder 纯色。
            "useGradient": False,
        },
        "flowchart": {
            "curve": "basis",
            "nodeSpacing": 50,
            "rankSpacing": 35,
            "padding": 15,
            "wrappingWidth": 220,
        },
    }
    path = tmp / "mermaid-config.json"
    path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return path


def _write_puppeteer_config(tmp: Path, chromium: str) -> Path:
    path = tmp / "puppeteer-config.json"
    path.write_text(
        json.dumps({"executablePath": chromium, "args": ["--no-sandbox"]}),
        encoding="utf-8",
    )
    return path


# ── 文案 → mermaid 标签 ──────────────────────────────────
def _q(text) -> str:
    """引号包住标签（flowchart 节点 / flowchart 边 / stateDiagram 状态名）。

    引号内是字面量：`/` `()` `：` `1.` 都不再触发布局语法，mermaid 渲染时脱掉引号不显示。
    半角双引号是唯一不能出现的字符（mermaid 不支持 \\" 转义），统一换单引号。
    `\\n` 按多行处理，转 mermaid 的 `<br/>`。

    唯一不能用引号的是 **stateDiagram 的边 label**——mermaid 不脱那里的引号，会原文渲染。
    """
    s = str(text).replace('"', "'").replace("\n", "<br/>")
    return f'"{s}"'


def _class_lines(ids_by_kind, style_map) -> list[str]:
    """classDef + class 绑定。每个 classDef 必带 color，否则 mermaid 自选字色（浅底上会糊）。"""
    lines = []
    for kind, ids in ids_by_kind.items():
        fill, stroke = style_map[kind]
        lines.append(
            f"    classDef {kind} fill:{fill},stroke:{stroke},stroke-width:1.5px,color:{INK}"
        )
        lines.append(f"    class {','.join(ids)} {kind}")
    return lines


def _edge_line(edge) -> str:
    label = edge.get("label")
    arrow = f"-->|{_q(label)}|" if label else "-->"
    return f"    {edge['s']} {arrow} {edge['t']}"


# ── 三种图型 → mermaid 源 ────────────────────────────────
def _branch_to_mermaid(chart) -> str:
    """单角色 DAG / 决策分支 → flowchart TB。"""
    lines = ["flowchart TB"]
    ids_by_type = defaultdict(list)
    for n in chart["nodes"]:
        open_, close_ = _node_shape(n["type"])
        lines.append(f"    {n['id']}{open_}{_q(n['label'])}{close_}")
        ids_by_type[n["type"]].append(n["id"])
    lines += [_edge_line(e) for e in chart.get("edges", [])]
    lines += _class_lines(ids_by_type, _NODE_COLORS)
    return "\n".join(lines) + "\n"


def _swimlane_to_mermaid(chart) -> str:
    """多角色泳道 → swimlane-beta：顶层每个 subgraph 是一条泳道。

    `col` = 泳道内左右次序偏好（按 col 排序后声明）；边上的 `sp` / `tp` 端口字段不读，
    泳道路由交给 mermaid 布局。
    """
    lanes = chart["lanes"]
    nodes = chart["nodes"]
    lane_set = set(lanes)
    for n in nodes:
        if n["lane"] not in lane_set:
            raise ValueError(
                f"swimlane 节点 {n['id']!r} 的 lane={n['lane']!r} 未在 lanes={lanes} 声明——"
                f"补进 chart['lanes'] 或修正 node lane 名"
            )

    by_lane = defaultdict(list)
    for n in nodes:
        by_lane[n["lane"]].append(n)

    lines = ["swimlane-beta TB"]
    ids_by_type = defaultdict(list)
    for i, lane in enumerate(lanes):
        lines.append(f"    subgraph lane_{i} [{_q(lane)}]")
        for n in sorted(by_lane[lane], key=lambda x: x.get("col", 0)):
            open_, close_ = _node_shape(n["type"])
            lines.append(f"        {n['id']}{open_}{_q(n['label'])}{close_}")
            ids_by_type[n["type"]].append(n["id"])
        lines.append("    end")
    lines += [_edge_line(e) for e in chart.get("edges", [])]
    lines += _class_lines(ids_by_type, _NODE_COLORS)
    return "\n".join(lines) + "\n"


def _state_to_mermaid(chart) -> str:
    """状态机 / 生命周期 → stateDiagram-v2。回路 / 多源汇聚 / 扇出无需手工布局。"""
    lines = ["stateDiagram-v2", "    direction LR"]
    ids_by_kind = defaultdict(list)
    for s in chart.get("states", []):
        lines.append(f"    state {_q(s['label'])} as {s['id']}")
        kind = s.get("kind")
        if kind in STATE_KIND_STYLE:
            ids_by_kind[kind].append(s["id"])
    for t in chart.get("transitions", []):
        # 状态机边 label 不能加引号：mermaid 不脱引号，会原文渲染成 ""业务系统同步入库""
        label = str(t.get("label", "")).replace(":", "：")
        if label:
            lines.append(f"    {t['from']} --> {t['to']} : {label}")
        else:
            lines.append(f"    {t['from']} --> {t['to']}")
    lines += _class_lines(ids_by_kind, STATE_KIND_STYLE)
    return "\n".join(lines) + "\n"


_BUILDERS = {
    "branch": _branch_to_mermaid,
    "swimlane": _swimlane_to_mermaid,
    "state": _state_to_mermaid,
}


# ── 渲染 ─────────────────────────────────────────────────
def _render_mermaid(mmd_path: Path, mermaid_cfg: Path, puppeteer_cfg: Path,
                    formats=("svg", "png")):
    """mmdc 渲染 .mmd → .mmd.svg + .mmd.png。任一步失败直接抛错，不静默跳过。"""
    mmdc = shutil.which("mmdc")
    if not mmdc:
        raise RuntimeError(
            "mmdc 未安装，无法渲染流程图：npm i -g @mermaid-js/mermaid-cli"
        )
    base = mmd_path.with_suffix("")  # 去掉 .mmd
    outputs = []
    for fmt in formats:
        out_path = base.parent / f"{base.name}.mmd.{fmt}"
        cmd = [
            mmdc, "-i", str(mmd_path), "-o", str(out_path),
            "-p", str(puppeteer_cfg), "-c", str(mermaid_cfg),
            "-b", "white", "-q",
        ]
        if fmt == "png":
            # -w 撑大页面，否则宽图会被压到 mmdc 默认 800px 再 ×scale，糊成一团
            cmd += ["-s", "2", "-w", "4000"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0 or not out_path.exists():
            raw = (result.stderr or result.stdout or "").strip().splitlines()
            # 有效诊断（mermaid 的 `Parse error on line N`）在 stderr 开头，末尾全是
            # puppeteer 调用栈——先剔栈帧行再取前几行，别让尾部噪音把有用信息挤掉
            detail = [ln for ln in raw if ln.strip() and not ln.lstrip().startswith("at ")]
            raise RuntimeError(
                f"mmdc 渲染 {fmt} 失败：{mmd_path.name}\n  " + "\n  ".join(detail[:6])
            )
        outputs.append(out_path)
    return outputs


# ── 主入口 ───────────────────────────────────────────────
def render_flowchart(output_path, title, subtitle, charts):
    """生成一组流程图。

    output_path: 路径 base，扩展名会被剥离（.html / 无扩展都接受）
    title/subtitle: 调用方在 PRD/HTML 容器侧加标注，引擎层不渲染
    charts: list[dict]，每条 type ∈ {branch, swimlane, state}

    输出文件命名按 chart index（多图才带序号）：
        单图  flow-xxx-v1.mmd      + .mmd.svg / .mmd.png
        多图  flow-xxx-v1-1.mmd    + .mmd.svg / .mmd.png
    """
    out = Path(output_path)
    if out.suffix:
        out = out.with_suffix("")
    out.parent.mkdir(parents=True, exist_ok=True)

    unknown = [c["type"] for c in charts if c["type"] not in _BUILDERS]
    if unknown:
        raise ValueError(
            f"unknown chart type(s): {unknown}; supported: {sorted(_BUILDERS)}"
        )

    chromium = _find_chromium()
    if not chromium:
        raise RuntimeError(
            "找不到 mmdc 可用的 Chromium。二选一：\n"
            "  npx puppeteer browsers install chrome-headless-shell\n"
            "  export PUPPETEER_EXECUTABLE_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'"
        )

    multi = len(charts) > 1
    all_outputs = []
    with tempfile.TemporaryDirectory(prefix="flowchart-") as tmpdir:
        tmp = Path(tmpdir)
        mermaid_cfg = _write_mermaid_config(tmp)
        puppeteer_cfg = _write_puppeteer_config(tmp, chromium)
        for i, chart in enumerate(charts):
            suffix = f"-{i + 1}" if multi else ""
            mmd_path = out.parent / f"{out.name}{suffix}.mmd"
            mmd_path.write_text(_BUILDERS[chart["type"]](chart), encoding="utf-8")
            all_outputs.extend(_render_mermaid(mmd_path, mermaid_cfg, puppeteer_cfg))

    print(f"[flowchart] {title} — {len(charts)} chart(s)"
          + (f" · {subtitle}" if subtitle else ""))
    for path in all_outputs:
        print(f"           + {path}")
    try:
        from lib.skill_log import emit as _sl
        _sl("flowchart", True)
    except Exception:
        pass
    return all_outputs
