#!/usr/bin/env python3
"""md_to_html.py — 把 md 转成带 "Copy for LLM" 按钮的自包含 HTML
用法:
    python3 scripts/lib/md_to_html.py <input.md> <output.html>

设计:
- 主要受众: 研发团队 (PRD/MRD 等技术文档)
- 右上角 sticky Copy 按钮 → 复制原始 md 到剪贴板，研发粘给自己 Claude Code
- 原始 md inline 在 <script type="text/plain" id="raw-md"> 避免额外 fetch
- 风格: Claude Design 暖浅色 + GitHub 排版规范
"""
from __future__ import annotations

import html as html_lib
import json
import sys
from datetime import datetime
from pathlib import Path

import markdown

CSS = r"""
:root {
  --bg: #FAF9F5;
  --surface: #FFFFFF;
  --hairline: #E5E3DA;
  --ink: #1F1F1E;
  --ink-82: #3A3A37;
  --ink-58: #6F6E68;
  --ink-40: #9E9D95;
  --accent: #D97757;
  --accent-glow: rgba(217, 119, 87, 0.12);
  --ok: #2F8B5B;
  --err: #C94F3D;
  --code-bg: #F5F4EF;
  --sans: 'Noto Sans SC','Poppins',system-ui,-apple-system,sans-serif;
  --serif: 'Noto Serif SC','Lora',Georgia,serif;
  --mono: 'JetBrains Mono','SF Mono',ui-monospace,Menlo,monospace;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: var(--sans);
  background: var(--bg);
  color: var(--ink);
  font-size: 15px;
  line-height: 1.75;
  -webkit-font-smoothing: antialiased;
}

/* sticky header */
.doc-header {
  position: sticky; top: 0; z-index: 50;
  background: var(--bg);
  border-bottom: 1px solid var(--hairline);
  padding: 14px 28px;
  display: flex; align-items: center; justify-content: space-between;
  gap: 20px;
}
.doc-header-meta { min-width: 0; flex: 1; }
.doc-header-name {
  font-family: var(--mono); font-size: 13px; font-weight: 600;
  color: var(--ink); letter-spacing: .01em;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.doc-header-sub {
  font-size: 11px; color: var(--ink-58); margin-top: 2px;
  font-family: var(--mono); letter-spacing: .04em;
}
.copy-btn {
  flex: none; display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 16px; font-family: var(--mono); font-size: 12px;
  font-weight: 600; color: var(--ink);
  background: var(--surface);
  border: 1px solid var(--hairline); border-radius: 6px;
  cursor: pointer; transition: all .15s ease;
  letter-spacing: .02em;
}
.copy-btn:hover { border-color: var(--accent); color: var(--accent); }
.copy-btn.copied { background: var(--accent-glow); border-color: var(--accent); color: var(--accent); }
.copy-btn svg { width: 14px; height: 14px; stroke: currentColor; stroke-width: 2; fill: none; stroke-linecap: round; stroke-linejoin: round; }

/* main */
main {
  max-width: 860px; margin: 0 auto; padding: 40px 28px 120px;
}
main > :first-child { margin-top: 0; }

/* headings */
h1, h2, h3, h4, h5, h6 { font-family: var(--sans); color: var(--ink); font-weight: 700; line-height: 1.35; margin: 2em 0 .6em; }
h1 { font-size: 30px; border-bottom: 1px solid var(--hairline); padding-bottom: .4em; margin-top: 0; }
h2 { font-size: 22px; border-bottom: 1px solid var(--hairline); padding-bottom: .3em; margin-top: 2.2em; }
h3 { font-size: 18px; margin-top: 1.8em; }
h4 { font-size: 16px; color: var(--ink-82); }
h5, h6 { font-size: 14px; color: var(--ink-58); text-transform: uppercase; letter-spacing: .08em; }

/* text */
p { margin: 0 0 1em; }
strong { color: var(--ink); font-weight: 700; }
em { color: var(--ink-82); }
a { color: var(--accent); text-decoration: none; border-bottom: 1px solid transparent; }
a:hover { border-bottom-color: var(--accent); }

/* lists */
ul, ol { margin: 0 0 1em; padding-left: 1.6em; }
li { margin: .3em 0; }
li > ul, li > ol { margin: .3em 0; }

/* blockquote */
blockquote {
  margin: 1em 0; padding: .8em 1.2em;
  border-left: 3px solid var(--accent);
  background: var(--accent-glow);
  color: var(--ink-82);
}
blockquote p:last-child { margin-bottom: 0; }

/* code */
code { font-family: var(--mono); font-size: .9em; background: var(--code-bg); padding: 2px 6px; border-radius: 3px; color: var(--ink); }
pre { background: var(--code-bg); border: 1px solid var(--hairline); border-radius: 6px; padding: 14px 16px; overflow-x: auto; line-height: 1.6; margin: 1em 0; }
pre code { background: transparent; padding: 0; font-size: 13px; }
.codehilite pre { margin: 0; border: 0; }
.codehilite { background: var(--code-bg); border: 1px solid var(--hairline); border-radius: 6px; margin: 1em 0; overflow: hidden; }

/* tables */
table { width: 100%; border-collapse: collapse; margin: 1.2em 0; font-size: 14px; }
th, td { border: 1px solid var(--hairline); padding: 8px 12px; text-align: left; vertical-align: top; }
th { background: var(--surface); font-weight: 700; color: var(--ink); }
td { color: var(--ink-82); }
tr:nth-child(even) td { background: var(--surface); }

/* hr */
hr { border: 0; border-top: 1px solid var(--hairline); margin: 2.5em 0; }

/* toast */
.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%) translateY(80px);
  background: var(--ink); color: var(--bg);
  padding: 10px 20px; border-radius: 6px;
  font-family: var(--mono); font-size: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,.15);
  opacity: 0; transition: all .25s ease; pointer-events: none;
  z-index: 100;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

/* pygments 代码高亮 (浅色主题) */
.codehilite .k, .codehilite .kd, .codehilite .kn, .codehilite .kr, .codehilite .kt { color: #A23E48; }
.codehilite .s, .codehilite .s1, .codehilite .s2 { color: #2F8B5B; }
.codehilite .c, .codehilite .c1, .codehilite .cm { color: var(--ink-40); font-style: italic; }
.codehilite .nf, .codehilite .fm { color: #5B6CC9; }
.codehilite .nb { color: #B57B3C; }
.codehilite .mi, .codehilite .mf { color: #8C5B3F; }
.codehilite .o, .codehilite .ow { color: var(--ink-82); }

@media (max-width: 680px) {
  .doc-header { padding: 12px 16px; }
  main { padding: 24px 16px 80px; }
  h1 { font-size: 24px; }
  h2 { font-size: 19px; }
  table { font-size: 13px; display: block; overflow-x: auto; }
}
"""


COPY_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>'
CHECK_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>'


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<header class="doc-header">
  <div class="doc-header-meta">
    <div class="doc-header-name">{filename}</div>
    <div class="doc-header-sub">更新 · {updated} &middot; 给研发 AI 消费</div>
  </div>
  <button class="copy-btn" id="copy-btn" type="button" onclick="copyMd()">
    <span class="copy-btn-icon">{copy_icon}</span>
    <span class="copy-btn-text">Copy for LLM</span>
  </button>
</header>

<main>
{body}
</main>

<div class="toast" id="toast">已复制 · 粘到你的 Claude Code / Chat 即可</div>

<script type="application/json" id="raw-md">{raw_md}</script>

<script>
const COPY_ICON = `{copy_icon}`;
const CHECK_ICON = `{check_icon}`;

async function copyMd() {{
  const raw = JSON.parse(document.getElementById('raw-md').textContent);
  const btn = document.getElementById('copy-btn');
  const toast = document.getElementById('toast');
  try {{
    await navigator.clipboard.writeText(raw);
  }} catch (e) {{
    const ta = document.createElement('textarea');
    ta.value = raw; document.body.appendChild(ta);
    ta.select(); document.execCommand('copy'); ta.remove();
  }}
  btn.classList.add('copied');
  btn.querySelector('.copy-btn-icon').innerHTML = CHECK_ICON;
  btn.querySelector('.copy-btn-text').textContent = 'Copied';
  toast.classList.add('show');
  setTimeout(() => {{
    btn.classList.remove('copied');
    btn.querySelector('.copy-btn-icon').innerHTML = COPY_ICON;
    btn.querySelector('.copy-btn-text').textContent = 'Copy for LLM';
    toast.classList.remove('show');
  }}, 2000);
}}
</script>
</body>
</html>
"""


def md_to_html(md_path: Path, out_path: Path) -> None:
    md_text = md_path.read_text(encoding='utf-8')

    md = markdown.Markdown(extensions=[
        'extra',           # tables, fenced_code, footnotes, abbr, attr_list, def_list
        'sane_lists',
        'toc',
        'codehilite',      # pygments 代码高亮
    ], extension_configs={
        'codehilite': {
            'css_class': 'codehilite',
            'guess_lang': False,
            'linenums': False,
        },
    })

    body = md.convert(md_text)

    # 文件元信息
    filename = md_path.name
    title = md_path.stem
    try:
        mtime = md_path.stat().st_mtime
        updated = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
    except OSError:
        updated = datetime.now().strftime('%Y-%m-%d %H:%M')

    # raw md 用 JSON 嵌入 <script>：json.dumps 后把 '<' 转 <，
    # 既防 </script> 提前闭合，又能被 JSON.parse 完整还原。
    # 不能直接 html.escape——<script> 是 raw-text 元素，浏览器不解码其中的字符实体，
    # textContent 拿到的是 &lt; / &gt; / &amp; 字面量，复制出的 md 会损坏。
    raw_md_json = json.dumps(md_text, ensure_ascii=False).replace('<', '\\u003c')

    html_out = HTML_TEMPLATE.format(
        title=html_lib.escape(title),
        filename=html_lib.escape(filename),
        updated=updated,
        css=CSS,
        body=body,
        raw_md=raw_md_json,
        copy_icon=COPY_ICON,
        check_icon=CHECK_ICON,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_out, encoding='utf-8')


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("用法: python3 md_to_html.py <input.md> <output.html>", file=sys.stderr)
        return 1
    src = Path(argv[1]).resolve()
    dst = Path(argv[2]).resolve()
    if not src.is_file():
        print(f"✗ 源文件不存在: {src}", file=sys.stderr)
        return 1
    md_to_html(src, dst)
    print(f"✓ {src.name} → {dst}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
