"""md_to_html「Copy for LLM」原始 md 嵌入往返回归。

锁回归：raw md 用 JSON 嵌入 <script>（而非 html.escape）。<script> 是 raw-text 元素，
浏览器不解码字符实体——若 html.escape，textContent 拿到 &lt; / &gt; / &amp; 字面量，
复制出的 md 损坏。JSON 嵌入 + JSON.parse（Python json.loads 等价）完整还原任意内容。
"""
import json
import re
import tempfile
from pathlib import Path

from lib.md_to_html import md_to_html


def _render_and_extract(md_text: str) -> str:
    """渲染后从 <script id="raw-md"> 取回嵌入文本，模拟浏览器 JSON.parse 还原。"""
    with tempfile.TemporaryDirectory() as d:
        mp = Path(d) / "in.md"
        op = Path(d) / "out.html"
        mp.write_text(md_text, encoding="utf-8")
        md_to_html(mp, op)
        html = op.read_text(encoding="utf-8")
    m = re.search(
        r'<script type="application/json" id="raw-md">(.*?)</script>', html, re.S)
    assert m, "raw-md script 标签缺失"
    embedded = m.group(1)
    # 安全性：嵌入文本不能出现裸 </script（会提前闭合标签）
    assert "</script" not in embedded
    # 正确性：不能出现 HTML 实体（否则复制损坏）
    assert "&lt;" not in embedded and "&amp;" not in embedded
    return json.loads(embedded)  # 浏览器侧 JSON.parse 的等价


def test_roundtrip_angle_and_amp():
    md = "# T\n\n`List<T> && a > b`\n"
    assert _render_and_extract(md) == md


def test_roundtrip_literal_script_close():
    md = "正文里有 </script> 字样也要完整保留\n"
    assert _render_and_extract(md) == md


def test_roundtrip_braces_and_cjk():
    # {} 不能被 str.format 误当占位符；中文正常
    md = 'JSON 示例 {"key": 1} 与中文标点，测试。\n'
    assert _render_and_extract(md) == md
