#!/usr/bin/env python3
"""Markdown → Confluence storage XML 渲染层（md_to_confluence 写入端拆分）。

调用方：
- scripts/md_to_confluence.py（push：md → storage 推 wiki）
- scripts/tests/test_md_to_confluence.py（纯函数回归）

职责：md 段落 / 区块表 / :::leftright / :::steps / :::info|note|tip|warning
面板围栏 → 原生 storage XML（markdown-it commonmark+table，wiki 可视化编辑）。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import cast


def wrap_markdown(md: str) -> str:
    """单段 md → markdown 宏 storage XML（fallback：markdown-it 不可用时降级用）。

    正常路径走 render_prose 出原生 storage HTML（wiki 可视化编辑）；仅当环境缺
    markdown-it-py 时 render_prose 回落到本函数，把 md 塞进 Confluence markdown
    宏由服务端渲染（灰框、不可视化编辑）。
    """
    if "]]>" in md:
        md = md.replace("]]>", "]]]]><![CDATA[>")
    return (
        '<ac:structured-macro ac:name="markdown">'
        "<ac:plain-text-body><![CDATA["
        f"{md}"
        "]]></ac:plain-text-body></ac:structured-macro>"
    )


_MDIT = None
_MDIT_UNAVAILABLE = False


def _get_mdit():
    """懒加载 markdown-it（commonmark + table + 允许内嵌 HTML 直通）。

    缺包时返回 None → render_prose 降级回 markdown 宏。
    """
    global _MDIT, _MDIT_UNAVAILABLE
    if _MDIT is None and not _MDIT_UNAVAILABLE:
        try:
            from markdown_it import MarkdownIt
            _MDIT = MarkdownIt("commonmark", {"html": True}).enable("table")
        except ImportError:
            _MDIT_UNAVAILABLE = True
            print("  ⚠ 未检测到 markdown-it-py，正文降级为 markdown 宏（灰框、wiki 不可视化编辑）。"
                  "pip install markdown-it-py 后可推原生可编辑内容。", file=sys.stderr)
    return _MDIT


def _xhtml_self_close(html: str) -> str:
    """storage 是 XHTML，void 元素补自闭合（<br>/<hr>/<col>/<img>/<input>/<meta>/<link>）。"""
    html = re.sub(r"<(br|hr)\s*>", r"<\1 />", html)
    html = re.sub(r"<(col|img|input|meta|link)((?:\s[^>]*?)?)(?<!/)>", r"<\1\2 />", html)
    return html


def _convert_task_lists(html: str) -> str:
    """把 GFM 任务列表（commonmark 渲成 `<li>[ ] 文本`）转 Confluence 原生 <ac:task-list>。

    commonmark 不认 `- [ ]` 语法，渲染成字面 `<li>[ ] 文本</li>`，推到 wiki 是丑文本。
    仅当一个 <ul> 里所有 <li> 都以 [ ] / [x] 开头才整块转任务列表（混排 ul 不动）。
    """
    checkbox = re.compile(r"^\s*\[(?P<mark>[ xX])\]\s*(?P<body>.*)$", re.DOTALL)

    def _repl(m: re.Match) -> str:
        inner = m.group("inner")
        items = re.findall(r"<li>(.*?)</li>", inner, re.DOTALL)
        if not items:
            return m.group(0)
        parsed = [checkbox.match(it) for it in items]
        if not all(parsed):
            return m.group(0)  # 非纯任务列表，保持原 <ul>
        tasks = []
        for p in parsed:
            assert p is not None  # all(parsed) 已保证非 None（mypy 收窄）
            status = "complete" if p.group("mark").lower() == "x" else "incomplete"
            body = p.group("body").strip()
            tasks.append(
                f"<ac:task><ac:task-status>{status}</ac:task-status>"
                f"<ac:task-body>{body}</ac:task-body></ac:task>"
            )
        return "<ac:task-list>" + "".join(tasks) + "</ac:task-list>"

    return re.sub(r"<ul>(?P<inner>.*?)</ul>", _repl, html, flags=re.DOTALL)


def render_prose(
    md: str,
    attachment_names: set[str] | None = None,
    image_width: int = None,  # type: ignore[assignment]
    attachment_dims: dict[str, tuple[int, int]] | None = None,
) -> str:
    """普通散文段 md → 原生 storage HTML（markdown-it commonmark+table）。

    出原生 <h*>/<table>/<ul>/<ol>/<strong> 等元素，Confluence 编辑器可直接可视化
    编辑。内嵌 HTML（如场景卡的 <table>）直通。<img src=attachment> → ac:image
    storage（复用 render_ac_image + 智能宽度）。markdown-it 不可用时降级回 markdown 宏。
    """
    if not md.strip():
        return ""
    if attachment_names is None:
        attachment_names = set()
    if image_width is None:
        image_width = DEFAULT_IMAGE_WIDTH
    mdit = _get_mdit()
    if mdit is None:
        return wrap_markdown(md)
    html = _xhtml_self_close(mdit.render(md))
    html = _convert_task_lists(html)

    def _img(m: re.Match) -> str:
        src = m.group("src")
        if src in attachment_names:
            if attachment_dims is not None:
                w = _smart_image_width(src, attachment_dims.get(src), image_width)
            else:
                w = image_width
            # markdown-it 已把 <img> 包在 <p>/<li> 里，这里只出裸 ac:image，避免嵌套 <p>
            return (f'<ac:image ac:width="{w}">'
                    f'<ri:attachment ri:filename="{src}" /></ac:image>')
        return m.group(0)

    return re.sub(r'<img\s+[^>]*?src="(?P<src>[^"]+)"[^>]*?/?>', _img, html)


# wiki 内嵌图片默认宽度（PRD 子场景示意图，研发看大图点 attachment 看原图；
# Confluence 不支持 storage layout，缩图后 5 段式能更靠上不用滚太久）
DEFAULT_IMAGE_WIDTH = 360  # fallback：无法判断类型时（如 SVG 或读 PNG 失败）


def _png_dims(path: Path) -> tuple[int, int] | None:
    """读 PNG header 取 (width, height)。纯标准库无依赖。"""
    try:
        data = path.read_bytes()[:24]
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        import struct
        return struct.unpack(">II", data[16:24])
    except OSError:
        return None


def _smart_image_width(fname: str, dims: tuple[int, int] | None, fallback: int) -> int:
    """按文件名前缀 + PNG 实际纵横比选 Confluence 显示宽度。

    | 维度 | 类型 | 宽度 |
    |---|---|---|
    | 前缀 flow- / arch- / state- / imap- | 流程图 / 架构图 / 状态机 / 交互大图 | 900 |
    | 前缀 proto- / scene- | PRD 原型 / 场景截图（示意图，不铺满） | 700 |
    | W/H > 1.5 | 其他横屏宽图 | 900 |
    | 0.8 ≤ W/H ≤ 1.5 | 其他标准比例图 | 700 |
    | W/H < 0.8 | 手机 App 竖屏 | 360 |
    | 无尺寸信息 | fallback（DEFAULT_IMAGE_WIDTH） | fallback |
    """
    if fname.startswith(("flow-", "arch-", "state-", "imap-")):
        return 900
    if fname.startswith(("proto-web-", "proto-h5-", "scene-")):
        return 700
    if not dims:
        return fallback
    w, h = dims
    if h == 0:
        return fallback
    ratio = w / h
    if ratio > 1.5:
        return 900
    if ratio >= 0.8:
        return 700
    return 360


# ── PRD 区块表原生 storage <table> 渲染（绕开 markdown 宏）─────────────────
# PRD 子场景模板的「区块表」4 列：区块 / 元素 + 规则 / 文案 / 数据来源
# Confluence Markdown 宏对 table cell 内 HTML（<br> / <ul>）一律转义为字面量，
# 长文本 cell 全挤一坨。解法：识别区块表，整段切走，原生 <table> + <ul><li>
# 渲染（按『；』拆 cell 为 bullet）。其他普通表（枚举 / 埋点）继续走 markdown 宏。
_BLOCK_TABLE_HEADER_RE = re.compile(
    r"^\s*\|\s*区块\s*\|\s*元素\s*\+\s*规则\s*\|\s*文案\s*\|\s*数据来源\s*\|\s*$"
)
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|[\s:|\-]+\|\s*$")


def _xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cell_to_storage(cell: str) -> str:
    """单 cell 内容 → storage XML。
    - 含 ≥ 2 段（按『；』拆）→ <ul><li>...</li></ul>
    - 否则纯文本（XML escape）
    """
    cell = cell.strip()
    if "；" in cell:
        chunks = [c.strip() for c in cell.split("；") if c.strip()]
        if len(chunks) >= 2:
            items = "".join(f"<li>{_xml_escape(c)}</li>" for c in chunks)
            return f"<ul>{items}</ul>"
    return _xml_escape(cell)


def _parse_pipe_row(line: str) -> list[str] | None:
    raw = line.strip()
    if not (raw.startswith("|") and raw.endswith("|")):
        return None
    return [c.strip() for c in raw[1:-1].split("|")]


def _render_block_table_storage(table_md: str) -> str:
    """完整区块表 md（header + sep + N data row）→ 原生 <table> storage XML。"""
    lines = table_md.strip().splitlines()
    if len(lines) < 2:
        return table_md  # malformed
    header_cells = _parse_pipe_row(lines[0])
    if header_cells is None:
        return table_md
    data_rows = [r for r in (_parse_pipe_row(row) for row in lines[2:]) if r]
    th = "".join(f"<th>{_xml_escape(c)}</th>" for c in header_cells)
    body = "".join(
        "<tr>" + "".join(f"<td>{_cell_to_storage(c)}</td>" for c in row) + "</tr>"
        for row in data_rows
    )
    return f"<table><tbody><tr>{th}</tr>{body}</tbody></table>"


def _split_md_around_block_tables(md: str) -> list[tuple[str, str]]:
    """切 md 为段：('table', table_md_block) | ('text', text_md)。
    区块表起点：当前行匹配 _BLOCK_TABLE_HEADER_RE 且下一行是 |---|---| 分隔符。
    """
    lines = md.splitlines(keepends=True)
    out: list[tuple[str, str]] = []
    text_buf: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (
            _BLOCK_TABLE_HEADER_RE.match(line.rstrip("\n"))
            and i + 1 < len(lines)
            and _TABLE_SEPARATOR_RE.match(lines[i + 1].rstrip("\n"))
        ):
            if text_buf:
                out.append(("text", "".join(text_buf)))
                text_buf = []
            table_lines = [lines[i], lines[i + 1]]
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                table_lines.append(lines[j])
                j += 1
            out.append(("table", "".join(table_lines)))
            i = j
            continue
        text_buf.append(line)
        i += 1
    if text_buf:
        out.append(("text", "".join(text_buf)))
    return out


# ── PRD :::leftright 块 → 带表头原生 storage <table>（存量兼容）─────────────
# 语法（存量 PRD 用；新内容由生成器直接吐 HTML table，见 core/md_renderer.py）：
#   :::leftright
#   ![alt](../assets/scene-X.png)
#   :::col
#   **顶部主栏**
#   - bullet
#   :::
# 原理：左列 render_prose（attachment → ac:image + 区块表原生 <table>），右列
# render_prose（markdown-it 原生嵌套列表，wiki 可视化编辑）。
_LEFTRIGHT_OPEN_RE = re.compile(r"^\s*:::leftright\s*$")
_LEFTRIGHT_SPLIT_RE = re.compile(r"^\s*:::col\s*$")
_LEFTRIGHT_CLOSE_RE = re.compile(r"^\s*:::\s*$")
# :::info / :::note / :::tip / :::warning [标题] → Confluence 原生彩色提示面板宏。
# 元信息头（整理人 / 数据来源 / 版本状态）、口径警告等前置提醒用。标题可选。
_PANEL_OPEN_RE = re.compile(r"^\s*:::(?P<ptype>info|note|tip|warning)(?:\s+(?P<title>\S.*?))?\s*$")
# callout blockquote `> **【类型】** 正文` → 原生面板宏（手册 docx 靠 callout.lua 渲底纹框，
# Confluence 单纯 blockquote 是丑灰条，这里转成同义面板宏）。类型 → 宏色 + 标题映射：
_CALLOUT_BQ_RE = re.compile(r"^\s*>\s*\*\*【(?P<label>[^】]+)】\*\*\s*(?P<body>.*)$")
_CALLOUT_PANEL_MAP = {
    "说明": ("info", "说明"),
    "提示": ("tip", "提示"),
    "重要": ("note", "重要"),
    "风险提示": ("warning", "风险提示"),
}
LEFTRIGHT_LEFT_IMAGE_WIDTH = 320  # 左列图片宽度
# colgroup 固定左窄右宽：不设列宽时 Confluence 50/50 均分，右列三段式嵌套编号被挤窄。
# 左列 = 图宽 + 留白，右列吃掉剩余，三段式才有地方铺开。
LEFTRIGHT_LEFT_COL_WIDTH = 360
LEFTRIGHT_RIGHT_COL_WIDTH = 780
# :::steps 手册步骤图表格：多列并排「第一步 / 第二步…」，cell 内图收窄（并排两三列时
# 文本流宽度会撑满半屏，观感过大）。竖屏 260 / 横屏 340，比文本流 360/900 各收一档。
_STEPS_OPEN_RE = re.compile(r"^\s*:::steps\s*$")
STEPS_IMG_WIDTH_PORTRAIT = 260
STEPS_IMG_WIDTH_LANDSCAPE = 340


def _render_cell_md(
    md: str,
    attachment_names: set[str],
    image_width: int,
    attachment_dims: dict[str, tuple[int, int]] | None = None,
) -> str:
    """单 cell md → storage：区块表预切原生 <table>，其余走 render_prose（原生可编辑）。

    attachment_dims 仅在「文本流图」启用 smart 宽度路由；左图右文模板的左列固定宽度
    （由调用方传 image_width=LEFTRIGHT_LEFT_IMAGE_WIDTH + attachment_dims=None 实现）。
    """
    parts: list[str] = []
    for kind, content in _split_md_around_block_tables(md):
        if kind == "table":
            parts.append(_render_block_table_storage(content))
        else:
            parts.append(render_prose(
                content, attachment_names, image_width, attachment_dims=attachment_dims
            ))
    return "".join(parts)


def _render_leftright_storage(
    left_md: str,
    right_md: str,
    attachment_names: set[str],
    image_width: int = LEFTRIGHT_LEFT_IMAGE_WIDTH,
) -> str:
    """:::leftright 块 → 带表头的原生 storage <table> 两列（存量兼容分支）。

    新内容由生成器直接吐 HTML table（改动二后 md 里不再有 :::leftright）；本函数
    只服务存量已用围栏的 PRD。左 cell = 图 + 区块表原生 storage；右 cell = render_prose
    （原生嵌套列表，wiki 可视化编辑）。表头「示意图 / 页面元素 & 规则」与生成器产物一致。
    """
    left_cell = _render_cell_md(left_md, attachment_names, image_width)
    right_text = right_md.strip("\n")
    right_cell = render_prose(right_text, attachment_names) if right_text else ""
    # colgroup 固定左窄右宽，右列三段式不被挤窄（默认 50/50 均分会压扁右列）
    return (
        '<table>'
        '<colgroup>'
        f'<col style="width: {LEFTRIGHT_LEFT_COL_WIDTH}px;" />'
        f'<col style="width: {LEFTRIGHT_RIGHT_COL_WIDTH}px;" />'
        '</colgroup>'
        '<thead><tr><th>示意图</th><th>页面元素 &amp; 规则</th></tr></thead>'
        '<tbody><tr>'
        f'<td>{left_cell}</td>'
        f'<td>{right_cell}</td>'
        '</tr></tbody></table>'
    )


def _render_steps_table_storage(
    table_md: str,
    attachment_names: set[str],
    attachment_dims: dict[str, tuple[int, int]] | None,
) -> str:
    """:::steps 内的 markdown 表格 → 原生 <table>，cell 内图片按步骤收窄宽度。

    表头行 = 「第一步…」「第二步…」等步骤标题；数据行 cell = 图片（或图 + 短说明）。
    竖屏图 260 / 横屏图 340，均分列宽。非图片 cell 走 render_prose 保持格式。
    """
    lines = [line for line in table_md.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return _render_cell_md(table_md, attachment_names, DEFAULT_IMAGE_WIDTH,
                               attachment_dims=attachment_dims)
    header = _parse_pipe_row(lines[0])
    if header is None:
        return _render_cell_md(table_md, attachment_names, DEFAULT_IMAGE_WIDTH,
                               attachment_dims=attachment_dims)
    data_rows = [r for r in (_parse_pipe_row(row) for row in lines[2:]) if r]
    ncol = len(header)

    def _steps_cell(cell: str) -> str:
        cell = cell.strip()
        if not cell:
            return ""
        html = render_prose(cell, attachment_names)

        def _narrow(m: re.Match) -> str:
            src = m.group("src")
            dims = (attachment_dims or {}).get(src)
            w = STEPS_IMG_WIDTH_LANDSCAPE
            if dims and dims[1] and dims[0] / dims[1] < 0.8:
                w = STEPS_IMG_WIDTH_PORTRAIT
            return f'<ac:image ac:width="{w}"><ri:attachment ri:filename="{src}" /></ac:image>'

        return re.sub(
            r'<ac:image[^>]*>\s*<ri:attachment ri:filename="(?P<src>[^"]+)"\s*/>\s*</ac:image>',
            _narrow, html,
        )

    colgroup = "<colgroup>" + f'<col style="width: {round(100/ncol)}%;" />' * ncol + "</colgroup>"
    th = "".join(f'<th style="text-align:center">{_xml_escape(c)}</th>' for c in header)
    body = ""
    for row in data_rows:
        cells = "".join(
            f'<td style="text-align:center">{_steps_cell(c)}</td>' for c in row
        )
        body += f"<tr>{cells}</tr>"
    return f"<table>{colgroup}<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


def _render_panel_storage(
    ptype: str,
    title: str | None,
    body_md: str,
    attachment_names: set[str],
) -> str:
    """:::info|note|tip|warning [标题] 块 → Confluence 原生提示面板宏 storage。

    面板体走 render_prose（markdown-it 原生 storage，wiki 可视化编辑）。title 可选，
    走 ac:parameter；无标题时不出该参数（Confluence 用宏类型默认标题）。
    """
    body_cell = render_prose(body_md.strip("\n"), attachment_names) if body_md.strip() else ""
    title_param = ""
    if title:
        esc = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        title_param = f'<ac:parameter ac:name="title">{esc}</ac:parameter>'
    return (
        f'<ac:structured-macro ac:name="{ptype}">'
        f'{title_param}'
        f'<ac:rich-text-body>{body_cell}</ac:rich-text-body>'
        '</ac:structured-macro>'
    )


def _split_md_around_fences(md: str) -> list[tuple[str, object]]:
    """切 md 为 ('text', md) | ('leftright', (left, right)) | ('panel', (ptype, title, body))。
    缺 :::col 或闭合 ::: 的 leftright、缺闭合 ::: 的 panel 当普通文本处理。"""
    lines = md.splitlines(keepends=True)
    out: list[tuple[str, object]] = []
    text_buf: list[str] = []
    i = 0
    while i < len(lines):
        stripped_i = lines[i].rstrip("\n")
        if _LEFTRIGHT_OPEN_RE.match(stripped_i):
            split_idx = -1
            close_idx = -1
            j = i + 1
            while j < len(lines):
                stripped = lines[j].rstrip("\n")
                if _LEFTRIGHT_CLOSE_RE.match(stripped):
                    close_idx = j
                    break
                if split_idx < 0 and _LEFTRIGHT_SPLIT_RE.match(stripped):
                    split_idx = j
                j += 1
            if split_idx > 0 and close_idx > split_idx:
                if text_buf:
                    out.append(("text", "".join(text_buf)))
                    text_buf = []
                left = "".join(lines[i + 1 : split_idx])
                right = "".join(lines[split_idx + 1 : close_idx])
                out.append(("leftright", (left, right)))
                i = close_idx + 1
                continue
        if _STEPS_OPEN_RE.match(stripped_i):
            close_idx = -1
            j = i + 1
            while j < len(lines):
                if _LEFTRIGHT_CLOSE_RE.match(lines[j].rstrip("\n")):
                    close_idx = j
                    break
                j += 1
            if close_idx > i:
                if text_buf:
                    out.append(("text", "".join(text_buf)))
                    text_buf = []
                body = "".join(lines[i + 1 : close_idx])
                out.append(("steps", body))
                i = close_idx + 1
                continue
        panel_m = _PANEL_OPEN_RE.match(stripped_i)
        if panel_m:
            close_idx = -1
            j = i + 1
            while j < len(lines):
                if _LEFTRIGHT_CLOSE_RE.match(lines[j].rstrip("\n")):
                    close_idx = j
                    break
                j += 1
            if close_idx > i:
                if text_buf:
                    out.append(("text", "".join(text_buf)))
                    text_buf = []
                body = "".join(lines[i + 1 : close_idx])
                out.append(("panel", (panel_m.group("ptype"), panel_m.group("title"), body)))
                i = close_idx + 1
                continue
        callout_m = _CALLOUT_BQ_RE.match(stripped_i)
        if callout_m:
            label = callout_m.group("label").strip().lstrip("⚠️").strip()
            mapping = _CALLOUT_PANEL_MAP.get(label)
            if mapping:
                if text_buf:
                    out.append(("text", "".join(text_buf)))
                    text_buf = []
                ptype, title = mapping
                body_lines = [callout_m.group("body")]
                j = i + 1
                while j < len(lines) and lines[j].lstrip().startswith(">"):
                    body_lines.append(re.sub(r"^\s*>\s?", "", lines[j].rstrip("\n")))
                    j += 1
                out.append(("panel", (ptype, title, "\n".join(body_lines))))
                i = j
                continue
        text_buf.append(lines[i])
        i += 1
    if text_buf:
        out.append(("text", "".join(text_buf)))
    return out


def render_raw_html(md: str) -> str:
    """HTML 为主的文档（多为从 Confluence pandoc 抓回的裸 <table> 文档）→ storage XML。

    走 pandoc md→html（gfm），裸 <table> / <col> / <br> 原样直通，
    不进 markdown 宏（宏会把 HTML 转义成字面源码，表格全挤一坨）。
    再把非自闭合标签修成 XHTML 自闭合（storage 是 XHTML，<br>/<col>/<img>/<hr> 必须自闭）。

    适用：原文就是 wiki 富文本表格的文档原样回推。
    不适用：含本地图片需上传附件的 md（图片走主流程 ac:image）。
    """
    try:
        html = subprocess.run(
            ["pandoc", "-f", "gfm", "-t", "html"],
            input=md, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        sys.exit(f"pandoc 转换失败（--raw-html 模式依赖 pandoc）：{e}")
    # XHTML 自闭合修正：仅对「未自闭合」的 void 元素补 /（已是 <x ... /> 的不动）
    # 负向先行断言 (?<!/) 确保结尾不是已有的 /
    html = re.sub(r"<(br|hr)\s*>", r"<\1 />", html)
    html = re.sub(r"<(col|img|input|meta|link)((?:\s[^>]*?)?)(?<!/)>", r"<\1\2 />", html)
    return html


def render_md_full(
    md: str,
    attachment_names: set[str] | None = None,
    image_width: int = DEFAULT_IMAGE_WIDTH,
    attachment_dims: dict[str, tuple[int, int]] | None = None,
) -> str:
    """顶层渲染：leftright → 带表头原生 <table>；:::info/note/tip/warning → 原生提示面板宏；
    区块表 → 原生 <table>；其余段 → render_prose（markdown-it 原生 storage，wiki 可视化编辑）。

    attachment_dims: {filename: (w, h)} PNG 实际尺寸，传入启用文本流图智能宽度
    （按前缀 + 纵横比选 360 / 700 / 900）。leftright 模板左列保持固定 320，不受影响。
    """
    if attachment_names is None:
        attachment_names = set()
    parts: list[str] = []
    for kind, content in _split_md_around_fences(md):
        if kind == "leftright":
            left_md, right_md = cast(tuple[str, str], content)
            parts.append(
                _render_leftright_storage(left_md, right_md, attachment_names)
            )
        elif kind == "panel":
            ptype, title, body_md = cast(tuple[str, str, str], content)
            parts.append(
                _render_panel_storage(ptype, title, body_md, attachment_names)
            )
        elif kind == "steps":
            parts.append(
                _render_steps_table_storage(cast(str, content), attachment_names, attachment_dims)
            )
        else:
            parts.append(
                _render_cell_md(cast(str, content), attachment_names, image_width,
                                attachment_dims=attachment_dims)  # type: ignore[arg-type]
            )
    return "".join(parts)


def extract_title(md: str) -> str:
    for line in md.splitlines():
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    raise ValueError("No H1 title found in markdown; pass --title explicitly")
