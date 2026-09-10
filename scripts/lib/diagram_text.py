"""从 .drawio / .mmd 抽取可扫描的自然语言文本（跳过 XML / mermaid 语法噪音）。

.drawio：只取 mxCell `value="..."` 内容。
.mmd：取双引号标签（flowchart 节点 / flowchart 边 / stateDiagram 状态名 / subgraph 标题
      都走引号）+ stateDiagram 不引号的边 label（`A --> B : 文案`）。
返回与原文件等长的行列表（非命中行用空串占位，保行号对齐）。

调用方：check_cjk_punct.py / check_plain_language.py
"""
from __future__ import annotations

import re

_DRAWIO_VALUE_RE = re.compile(r'\bvalue="([^"]*)"')
_MMD_QUOTED_RE = re.compile(r'"([^"]*)"')
_MMD_TRANS_RE = re.compile(r'-->\s*\w+\s*:\s*(.+?)\s*$')


def extract_scan_lines(suffix: str, lines: list[str]) -> list[str] | None:
    """.drawio / .mmd 返回抽取后的扫描行；其他后缀返回 None（调用方按原文扫）。"""
    sfx = suffix.lower()
    if sfx == ".drawio":
        out = []
        for line in lines:
            m = _DRAWIO_VALUE_RE.search(line)
            out.append(m.group(1).replace("&#xa;", " ") if m else "")
        return out
    if sfx == ".mmd":
        out = []
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("%%"):
                out.append("")  # init 指令行，含 JSON 引号，跳过免得误扫
                continue
            parts = _MMD_QUOTED_RE.findall(line)
            m_trans = _MMD_TRANS_RE.search(line)
            if m_trans:
                parts.append(m_trans.group(1))
            out.append(" ".join(parts))
        return out
    return None
