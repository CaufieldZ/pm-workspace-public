#!/usr/bin/env python3
"""Mermaid 流程图 → PNG 截图（PRD 嵌图专用）。

设计动机：当前 flowchart skill 用 AntV X6 + dagre 渲染 .whiteboard 容器，
docx 嵌入按 15.5 cm 等比例缩后字号偏小且留白巨大，PM review 直接拒绝
（v5.3 反馈）。本模块用 Mermaid 横排（LR）替代，节点紧凑、字号大、Playwright
直接截 svg 容器，docx 嵌入可读性显著优于 X6/dagre。

边界：
- 仅服务 PRD skill 嵌图。flowchart skill（IMAP / arch / PPT 消费场景）保留 X6/dagre
- Mermaid 主题用 Claude Design 暖近黑 + terra cotta accent
- 字体强制 'Poppins','Noto Sans SC' 跟 PRD docx 字体栈对齐

使用：
    from mermaid_screenshots import render_mermaid
    png = render_mermaid(
        source='''flowchart LR
          A[开始] --> B[结束]
        ''',
        out_path=Path('.../journey.png'),
    )
"""
import argparse
import hashlib
import sys
from pathlib import Path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
  body {{
    margin: 0;
    padding: 24px;
    background: #FAF9F5;
    font-family: 'Poppins','Noto Sans SC','PingFang SC',sans-serif;
  }}
  pre.mermaid {{
    margin: 0;
    background: transparent;
  }}
  /* 让 mermaid 节点字号 + 字体跟 PRD docx 对齐 */
  .node text, .label text, .edgeLabel text {{
    font-family: 'Poppins','Noto Sans SC','PingFang SC',sans-serif !important;
    font-size: 15px !important;
    font-weight: 500 !important;
  }}
  /* edgeLabel 背景 → 跟画布同色，避免白盒子盖在线上 */
  .edgeLabel {{
    background-color: #FAF9F5 !important;
  }}
  .edgeLabel rect {{
    fill: #FAF9F5 !important;
  }}
</style>
</head>
<body>
<pre class="mermaid">
{SOURCE}
</pre>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{
    startOnLoad: true,
    theme: 'base',
    themeVariables: {{
      // Claude Design 暖近黑 + terra cotta
      primaryColor:        '#E7EFFE',   // 默认 process 节点 浅蓝
      primaryTextColor:    '#1F1F1E',   // 暖近黑
      primaryBorderColor:  '#1F1F1E',
      lineColor:           '#1F1F1E',
      tertiaryColor:       '#FAF9F5',
      background:          '#FAF9F5',
      mainBkg:             '#E7EFFE',
      // 节点类型色（跟原 flowchart skill 5 类色板对齐）
      // terminal 浅紫 / process 浅蓝 / decision 浅黄 / success 浅绿 / fail 浅红
      // 通过 classDef 在源码里自定义，不靠 themeVariables
      fontFamily: "'Poppins','Noto Sans SC','PingFang SC',sans-serif",
      fontSize: '15px',
    }},
    flowchart: {{
      curve: 'basis',
      htmlLabels: true,
      nodeSpacing: 50,
      rankSpacing: 60,
      padding: 8,
    }},
  }});
  // 渲染完打个标记，方便 Playwright 等
  window.addEventListener('load', async () => {{
    // mermaid v11 startOnLoad 是异步，等一会儿
    await new Promise(r => setTimeout(r, 800));
    document.body.dataset.mermaidReady = '1';
  }});
</script>
</body>
</html>
"""


def _set_dpi(png_path: Path, dpi: int = 200):
    """PIL 写 DPI 元数据。"""
    from PIL import Image
    img = Image.open(png_path)
    img.save(png_path, dpi=(dpi, dpi))


def _content_hash(source: str) -> str:
    return hashlib.sha1(source.encode('utf-8')).hexdigest()[:12]


def render_mermaid(source: str, out_path: Path, dpi: int = 200,
                   width: int = 1600) -> Path:
    """渲染 mermaid 源码到 PNG。

    内置内容 hash 缓存：源码 sha1 写到 PNG sidecar `.hash`，命中跳过 Playwright。

    Args:
        source: mermaid 源码（含 flowchart LR / classDef / 节点 / 边）
        out_path: 输出 PNG 路径（.png）
        dpi: PNG DPI 元数据，默认 200
        width: 浏览器视口宽度，默认 1600（横排 LR 留够空间）

    Returns:
        out_path（原路径）
    """
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sig = _content_hash(source)
    sidecar = out_path.with_suffix('.png.hash')
    if out_path.exists() and sidecar.exists() and sidecar.read_text().strip() == sig:
        return out_path  # 缓存命中

    from playwright.sync_api import sync_playwright

    html = HTML_TEMPLATE.format(SOURCE=source.strip())

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={'width': width, 'height': 1200},
            device_scale_factor=2,
        )
        page.set_content(html, wait_until='networkidle')
        # 等 mermaid 渲染完成（脚本 load 后 setTimeout 800ms 设标记）
        page.wait_for_function(
            "document.body.dataset.mermaidReady === '1'",
            timeout=15000,
        )
        # mermaid 渲染出的 svg 容器
        svg = page.locator('pre.mermaid svg').first
        svg.wait_for(state='visible', timeout=5000)
        # 截 svg bbox + 一点 padding（避免边贴边）
        bbox = svg.bounding_box()
        if bbox is None:
            raise RuntimeError(f'mermaid svg bbox 为空: {out_path}')
        pad = 16
        page.screenshot(
            path=str(out_path),
            clip={
                'x': max(0, bbox['x'] - pad),
                'y': max(0, bbox['y'] - pad),
                'width': bbox['width'] + pad * 2,
                'height': bbox['height'] + pad * 2,
            },
        )
        browser.close()

    _set_dpi(out_path, dpi=dpi)
    sidecar.write_text(sig)
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('source', type=Path, help='mermaid 源码文件（.mmd）')
    ap.add_argument('--out', type=Path, required=True, help='输出 PNG 路径')
    ap.add_argument('--dpi', type=int, default=200)
    ap.add_argument('--width', type=int, default=1600)
    args = ap.parse_args()

    src = args.source.read_text(encoding='utf-8')
    out = render_mermaid(src, args.out, dpi=args.dpi, width=args.width)
    size_kb = out.stat().st_size // 1024
    print(f'  {out.name}  {size_kb}KB')


if __name__ == '__main__':
    main()
