#!/usr/bin/env python3
"""从 Confluence URL 拉取页面内容，自动适配 4 种形态。

凭证（任一即可）：
  - env var：CONF_BASE_URL + CONF_TOKEN（开发推荐，不依赖私有配置）
  - 仓库根 .mcp.json 的 mcpServers.confluence.env（PM 工作流默认）

最常用：
  python3 scripts/fetch_confluence.py <url> --out-dir ./dump
  # auto 嗅探形态：
  #   父+子页 PRD → split-restore（还原本地 split 目录结构）
  #   单页 markdown 宏 PRD → md-macro（CDATA 原样还原）
  #   人编辑文档 → pandoc（保留 HTML 复杂表 + 精准下图）

可选：
  --no-images                                    纯文字模式，不下图（md 引用保留为占位）
  --view-map "4:broadcaster-h5,5:audience,..."   split-restore 模式 view 前缀映射
  -p 项目名 / --out-dir 目录                      落盘位置（互斥）
  --mode {auto,simple,md-macro,pandoc,split-restore}  强制指定模式
  --html / --raw / --with-children               旧能力保留

详细说明见同目录 README-fetch-confluence.md。
"""

# route-log: 调用埋点（scripts/lib/route_log.py）
import pathlib as _pl
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("fetch_confluence"))

import argparse
import base64
import html
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "scripts"))
from lib.confluence import (  # noqa: E402 （HTTP 层 + 凭据发现收口 lib）
    api_get,
    fetch_attachments,
    fetch_children,
    load_creds,
)
from lib.confluence_storage import extract_referenced_images


def parse_url(url):
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if "pageId" in qs:
        return qs["pageId"][0]
    m = re.search(r"/display/([^/]+)/(.+)", parsed.path)
    if m:
        space, title = m.group(1), urllib.parse.unquote(m.group(2).replace("+", " "))
        return None, space, title
    sys.exit(f"错误：无法从 URL 解析 pageId: {url}")


def save_images_to_dir(attachments, img_dir):
    """将已下载的附件写入目录，返回 {filename: filename} 映射。"""
    img_dir.mkdir(parents=True, exist_ok=True)
    mapping = {}
    for fname, info in attachments.items():
        (img_dir / fname).write_bytes(info["bytes"])
        mapping[fname] = fname
    return mapping


# ── markdown 输出 ────────────────────────────────────────────

def html_to_markdown(html_str, img_mapping=None, img_rel_dir=None):
    text = html_str

    if img_mapping and img_rel_dir:
        def replace_ac_image(m):
            fname = html.unescape(m.group(1))  # 属性值转义态 → 真实文件名（配 render_ac_image）
            if fname in img_mapping:
                return f"\n![{fname}]({img_rel_dir}/{img_mapping[fname]})\n"
            return f"\n![{fname}](attachment:{fname})\n"
        text = re.sub(
            r'<ac:image[^>]*>\s*<ri:attachment\s+ri:filename="([^"]+)"\s*/>\s*</ac:image>',
            replace_ac_image, text)

    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"\n# \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n## \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n### \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<h4[^>]*>(.*?)</h4>", r"\n#### \1\n", text, flags=re.DOTALL)
    text = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", text, flags=re.DOTALL)
    text = re.sub(r"<b[^>]*>(.*?)</b>", r"**\1**", text, flags=re.DOTALL)
    text = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", text, flags=re.DOTALL)
    text = re.sub(r"<a[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", r"[\2](\1)", text, flags=re.DOTALL)
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n", text, flags=re.DOTALL)
    text = re.sub(r"<tr[^>]*>(.*?)</tr>", lambda m: m.group(1) + "\n", text, flags=re.DOTALL)
    text = re.sub(r"<t[hd][^>]*>(.*?)</t[hd]>", r" \1 |", text, flags=re.DOTALL)
    def _img_to_md(m):
        tag = m.group(0)
        alt_m = re.search(r'alt="([^"]*)"', tag)
        src_m = re.search(r'src="([^"]*)"', tag)
        alt = alt_m.group(1) if alt_m else "image"
        src = src_m.group(1) if src_m else ""
        return f"![{alt}]({src})" if src else f"![{alt}]"
    text = re.sub(r"<img[^>]*>", _img_to_md, text)
    text = re.sub(r"<ac:structured-macro[^>]*ac:name=\"code\"[^>]*>.*?<ac:plain-text-body>\s*<!\[CDATA\[(.*?)\]\]>\s*</ac:plain-text-body>\s*</ac:structured-macro>",
                  r"\n```\n\1\n```\n", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── 形态嗅探 + md-macro / pandoc / split-restore 模式 ──────

_MD_MACRO_RE = re.compile(
    r'<ac:structured-macro[^>]*ac:name="markdown"[^>]*>'
    r'\s*<ac:plain-text-body>\s*<!\[CDATA\[(.*?)\]\]>\s*</ac:plain-text-body>'
    r'\s*</ac:structured-macro>',
    re.DOTALL,
)

# 子页内场景 heading：## 5.1 A-1 · 直播间完整全貌（split_prd 拆时降 ### → ##）
# re.M：heading 在 CDATA 提取出的 md 文本中不在串首（调用方先剥 macro 再匹配）
_CHILD_SCENE_HEAD_RE = re.compile(
    r"^##\s+\*{0,2}(\d+\.\d+)\s+(?:Scene\s+)?([A-Z][-\w]*)\s*·\s*(.+?)\*{0,2}\s*$",
    re.MULTILINE,
)
# 父页 §4-7 章 heading：# 4. 开播链路
_PARENT_CHAPTER_HEAD_RE = re.compile(r"^#\s+\*{0,2}([4-7])\.\s+(.+?)\*{0,2}\s*$")
# 父页 scene link 行（push 时被 rewrite_scene_links_to_confluence 改写为 Confluence URL）
_PARENT_SCENE_LINK_RE = re.compile(
    r"^- \[(\d+\.\d+)\s+([A-Z][-\w]*)\s*·\s*([^\]]+?)\]\(([^)]+)\)\s*$"
)
# 场景名清理：剥末尾追溯标记（同 split_prd._PHASE_TAG_RE）
_PHASE_TAG_RE = re.compile(
    r"\s*\*{0,2}[（(](?:Phase\s*\d+|变更|新增|后续迭代)[^）)]*[）)]\*{0,2}\s*$"
)


def _safe_filename(name):
    """场景白话名 → 文件名 safe 部分（复制自 split_prd._safe_filename，避免跨目录依赖）。"""
    name = _PHASE_TAG_RE.sub("", name)
    name = re.sub(r"\s*[（(][^）)]*[）)]\s*", "", name)
    name = re.sub(r"[\s/\\:*?<>|+]", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def detect_mode(body_html, has_split_children=False):
    """按 storage 指纹返回 'split-restore' / 'md-macro' / 'pandoc'。

    - 父+子页 + 父页有 markdown 宏 + 子页含 ## N.x SID 场景 heading → split-restore
    - 单页 + markdown 宏占比 ≥ 50% → md-macro
    - 其他 → pandoc

    阈值 50% 是安全裕度（实测 PM push 的 PRD markdown 宏占比 ≥ 95%；人编辑文档为 0%）。
    """
    has_md_macro = "<ac:structured-macro" in body_html
    if has_md_macro and has_split_children:
        return "split-restore"
    if not has_md_macro:
        return "pandoc"
    md_macro_chars = sum(len(m) for m in re.findall(
        r'<ac:structured-macro[^>]*ac:name="markdown".*?</ac:structured-macro>',
        body_html, re.DOTALL,
    ))
    if md_macro_chars / max(len(body_html), 1) > 0.5:
        return "md-macro"
    return "pandoc"


def parse_view_map(spec):
    """'4:broadcaster-h5,5:audience,6:broadcaster-web,7:cms'
       → {4: 'broadcaster-h5', 5: 'audience', 6: 'broadcaster-web', 7: 'cms'}
    """
    out = {}
    for kv in spec.split(","):
        kv = kv.strip()
        if not kv:
            continue
        k, _, v = kv.partition(":")
        if not k.strip().isdigit() or not v.strip():
            sys.exit(f"--view-map 格式错: {kv!r}（应为 'N:prefix' 逗号分隔）")
        out[int(k.strip())] = v.strip()
    if not out:
        sys.exit("--view-map 为空")
    return out


def split_child_into_scenes(child_md, view):
    """子页 md 按 `## N.x ID · 名` 切场景块。返回 [{fname, sid, content}, ...]。

    fname = '{view}-{sid}-{safe_name}.md'，跟 split_prd 推上去时的文件名一致。
    """
    lines = child_md.splitlines()
    scenes = []
    current = None
    for line in lines:
        m = _CHILD_SCENE_HEAD_RE.match(line)
        if m:
            if current is not None:
                scenes.append(current)
            sid = m.group(2)
            name = m.group(3).strip()
            current = {
                "fname": f"{view}-{sid}-{_safe_filename(name)}.md",
                "sid": sid,
                "lines": [line],
            }
            continue
        if current is not None:
            current["lines"].append(line)
    if current is not None:
        scenes.append(current)
    for s in scenes:
        s["content"] = "\n".join(s["lines"]).rstrip() + "\n"
        del s["lines"]
    return scenes


def infer_chapter_from_child(child_md):
    """扫子页第一个 `## N.x ID · ...` 推断章节号。"""
    for line in child_md.splitlines():
        m = _CHILD_SCENE_HEAD_RE.match(line)
        if m:
            return int(m.group(1).split(".")[0])
    return None


def rewrite_parent_links_to_local(parent_md, chapters_in_scope, scenes_dir_name, sid_to_fname):
    """父页 §4-7 章下的 `- [N.x ID · 名](Confluence URL)` 反向改写为本地相对路径。

    返回 (新 md, 改写行数, 未匹配 sid 列表)。
    """
    lines = parent_md.splitlines()
    out = []
    current_chapter = 0
    rewritten = 0
    unresolved = []
    for line in lines:
        m_ch = _PARENT_CHAPTER_HEAD_RE.match(line)
        if m_ch:
            current_chapter = int(m_ch.group(1))
            out.append(line)
            continue
        if line.startswith("# ") and not m_ch:
            current_chapter = 0
            out.append(line)
            continue
        if current_chapter in chapters_in_scope:
            m = _PARENT_SCENE_LINK_RE.match(line)
            if m:
                num, sid, name, _url = m.groups()
                fname = sid_to_fname.get(sid)
                if fname:
                    anchor = f"{num} {sid} · {name.strip()}"
                    out.append(f"- [{anchor}]({scenes_dir_name}/{fname})")
                    rewritten += 1
                    continue
                else:
                    unresolved.append(sid)
        out.append(line)
    tail = "\n" if not parent_md.endswith("\n") else ""
    return "\n".join(out) + tail, rewritten, unresolved


def ensure_h1(md, title):
    """主 md 首个非空行若不是 `# `，补一行 `# {title}`。"""
    for line in md.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("# "):
            return md
        break
    return f"# {title}\n\n{md.lstrip()}"


def extract_md_macro(storage_html, img_mapping=None, img_rel_dir=None):
    """逆 lib.confluence_md.wrap_markdown：把 storage 里的 markdown 宏 CDATA 拼回 md。

    - 宏内 CDATA 原样输出（push 时 escape 的 `]]]]><![CDATA[>` 还原回 `]]>`）
    - 宏之间的 HTML 段（含 ac:image / 原生 table）走 html_to_markdown 兜底
    """
    if "<ac:structured-macro" not in storage_html:
        return html_to_markdown(storage_html, img_mapping, img_rel_dir)
    parts = []
    last = 0
    for m in _MD_MACRO_RE.finditer(storage_html):
        between = storage_html[last:m.start()]
        if between.strip():
            converted = html_to_markdown(between, img_mapping, img_rel_dir).strip()
            if converted:
                parts.append(converted)
        cdata = m.group(1).replace("]]]]><![CDATA[>", "]]>")
        if cdata.strip():
            parts.append(cdata.strip())
        last = m.end()
    rest = storage_html[last:]
    if rest.strip():
        converted = html_to_markdown(rest, img_mapping, img_rel_dir).strip()
        if converted:
            parts.append(converted)
    return "\n\n".join(parts) + "\n"


def pandoc_render(storage_html, img_rel_dir):
    """人编辑文档专用：HTML → GFM markdown。

    - ac:image → <img src="{img_rel_dir}/X" width="N">，markdown 表格 cell 内也能渲染
    - 通配剥所有 ac:* / ri:* 私有标签
    - 调 pandoc gfm+pipe_tables，复杂表（rowspan/colspan）自动 fallback 保留 HTML
    """
    if not shutil.which("pandoc"):
        sys.exit(
            "错误：--mode pandoc 需要 pandoc。\n"
            "  macOS:  brew install pandoc\n"
            "  Linux:  apt install pandoc / yum install pandoc"
        )

    def _replace_image(m):
        width = m.group(1)
        fname = html.unescape(m.group(2))  # 属性值转义态 → 真实文件名
        src = f"{img_rel_dir}/{fname}" if img_rel_dir else fname
        attrs = f' width="{width}"' if width else ""
        return f'<img src="{src}" alt="{fname}"{attrs}>'

    prep = re.sub(
        r'<ac:image(?:\s+ac:width="(\d+)")?[^>]*>\s*<ri:attachment\s+ri:filename="([^"]+)"\s*/>\s*</ac:image>',
        _replace_image, storage_html,
    )
    # 剥残留私有标签（嵌入 ri:user / ri:page 等）
    prep = re.sub(r'</?ac:[^>]+>|</?ri:[^>]+>', '', prep)

    html_doc = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        f'<body>{prep}</body></html>'
    )
    try:
        result = subprocess.run(
            ["pandoc", "-f", "html-native_divs-native_spans",
             "-t", "gfm+pipe_tables", "--wrap=preserve"],
            input=html_doc, capture_output=True, text=True, check=True,
        )
        return result.stdout
    except FileNotFoundError:
        sys.exit("错误：pandoc 未找到。安装：brew install pandoc")
    except subprocess.CalledProcessError as e:
        sys.exit(f"错误：pandoc 渲染失败 (rc={e.returncode})\n{e.stderr[:500]}")


# ── HTML 单文件输出 ──────────────────────────────────────────

def build_self_contained_html(title, version, page_id, body_html, attachments):
    """Confluence storage HTML → 自包含 HTML，图片 base64 内嵌。"""

    def replace_ac_image(m):
        fname = html.unescape(m.group(1))  # 转义态 → 真实文件名（查 attachments 用）
        width = m.group(2)
        info = attachments.get(fname)
        alt = html.escape(fname, quote=True)  # 回写进 HTML 属性/正文需重新转义
        if info and "bytes" in info:
            b64 = base64.b64encode(info["bytes"]).decode()
            style = f' style="max-width:{width}px"' if width else ""
            return f'<img src="data:{info["mime"]};base64,{b64}" alt="{alt}"{style} />'
        return f'<p>[图片缺失: {alt}]</p>'

    body = re.sub(
        r'<ac:image(?:\s+ac:width="(\d+)")?[^>]*>\s*<ri:attachment\s+ri:filename="([^"]+)"\s*/>\s*</ac:image>',
        lambda m: replace_ac_image(type("M", (), {"group": lambda s, i: [None, m.group(2), m.group(1)][i]})()),
        body_html)

    body = re.sub(r"<ac:structured-macro[^>]*ac:name=\"code\"[^>]*>.*?<ac:plain-text-body>\s*<!\[CDATA\[(.*?)\]\]>\s*</ac:plain-text-body>\s*</ac:structured-macro>",
                  r"<pre><code>\1</code></pre>", body, flags=re.DOTALL)
    body = re.sub(r"<ac:[^>]+>|</ac:[^>]+>|<ri:[^>]+>|</ri:[^>]+>", "", body)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
  body {{ font-family: 'HarmonyOS Sans SC', -apple-system, system-ui, sans-serif; max-width: 960px; margin: 0 auto; padding: 24px; color: #1d1d1f; line-height: 1.7; }}
  h1 {{ font-size: 28px; border-bottom: 2px solid #e5e5e5; padding-bottom: 12px; }}
  h2 {{ font-size: 22px; margin-top: 32px; }}
  h3 {{ font-size: 18px; }}
  img {{ max-width: 100%; height: auto; border: 1px solid #e5e5e5; border-radius: 6px; margin: 12px 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
  th, td {{ border: 1px solid #d1d1d6; padding: 8px 12px; text-align: left; }}
  th {{ background: #f5f5f7; font-weight: 600; }}
  pre {{ background: #f5f5f7; padding: 16px; border-radius: 8px; overflow-x: auto; }}
  code {{ font-family: 'IBM Plex Mono', monospace; font-size: 14px; }}
  .meta {{ color: #86868b; font-size: 14px; margin-bottom: 24px; }}
</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
<p class="meta">Confluence v{version} · pageId: {page_id}</p>
{body}
</body>
</html>"""


def page_to_md_block(page, heading_offset=0, img_mapping=None, img_rel_dir=None):
    """页面转 markdown 块：标题 + 元信息 + 正文。

    heading_offset: 子页 # → 子页用 ## 的 offset（拼到父页时避免标题层级混乱）
    img_mapping / img_rel_dir: 图片本地化（同 html_to_markdown 参数）

    正文优先走 extract_md_macro（还原 md-macro CDATA 宏 + 宏间 HTML 兜底），
    这样 PM 用 md_to_confluence 推上去的 PRD 语料是可读 markdown，而不是原始 XML。
    """
    title = page["title"]
    body_html = page["body"]["storage"]["value"]
    version = page.get("version", {}).get("number", "?")
    page_id = page["id"]
    md_body = extract_md_macro(body_html, img_mapping, img_rel_dir)
    if heading_offset > 0:
        prefix = "#" * heading_offset
        md_body = re.sub(r"^(#+ )", lambda m: prefix + m.group(1), md_body, flags=re.MULTILINE)
    heading_level = "#" * (1 + heading_offset)
    return f"{heading_level} {title}\n\n> Confluence v{version} | pageId: {page_id}\n\n{md_body}"


def main():
    parser = argparse.ArgumentParser(description="从 Confluence 拉取页面内容")
    parser.add_argument("url", help="Confluence 页面 URL")
    parser.add_argument("--project", "-p", help="项目名（存到 projects/{项目}/inputs/docs/）")
    parser.add_argument("--output", "-o", help="输出文件名（默认用页面标题）")
    parser.add_argument("--out-dir", help="通用输出目录（与 -p 互斥）；md 落 {dir}/{title}.md，pandoc/md-macro 模式图落 {dir}/assets/")
    parser.add_argument("--images", action="store_true", help="markdown + 图片目录（需 -p；pandoc/md-macro 模式默认下图，无需此 flag）")
    parser.add_argument("--no-images", action="store_true", help="纯文字模式：不下载图，md 内图引用保留为占位（仅 pandoc/md-macro 模式生效）")
    parser.add_argument("--html", action="store_true", help="单 HTML 文件，图片 base64 内嵌（需 -p）")
    parser.add_argument("--raw", action="store_true", help="输出原始 Confluence 存储 HTML")
    parser.add_argument(
        "--mode",
        choices=["auto", "simple", "md-macro", "pandoc", "split-restore"],
        default="auto",
        help=(
            "auto（默认）按 storage 嗅探：父+子页+md宏 -> split-restore，单页+md宏 -> md-macro，其余 -> pandoc；"
            "simple = 旧 html_to_markdown（向后兼容）；"
            "md-macro = 剥 markdown 宏 CDATA 直出（PM push 的单页 PRD）；"
            "pandoc = HTML -> GFM，保留 HTML 复杂表 + 全图本地预览（人编辑文档）；"
            "split-restore = 还原本地 split 目录结构（主 md + scenes/{view}-{id}-{name}.md），父+子页 PRD 专用"
        ),
    )
    parser.add_argument(
        "--view-map",
        help='split-restore 模式必填：章节号 -> view 前缀，逗号分隔。例: "4:broadcaster-h5,5:audience,6:broadcaster-web,7:cms"',
    )
    parser.add_argument(
        "--stem",
        help="split-restore 模式：主 md 文件名 stem（默认从父页标题派生）。最终产物 = {stem}.md + {stem}-scenes/",
    )
    parser.add_argument(
        "--with-children",
        action="store_true",
        help="递归抓父页 + 所有子页合并 markdown（按 wiki 上 position 顺序拼接，"
             "子页 heading 自动下沉一级）；与 --mode pandoc/md-macro 不兼容",
    )
    args = parser.parse_args()

    # ── 互斥守门 ──
    if args.project and args.out_dir:
        sys.exit("错误：-p / --project 与 --out-dir 互斥")
    if (args.images or args.html) and not (args.project or args.out_dir):
        sys.exit("错误：--images / --html 需要配合 -p 或 --out-dir 指定输出位置")
    if args.with_children and (args.html or args.raw):
        sys.exit("错误：--with-children 仅支持 markdown 输出，不能配合 --html / --raw")
    if args.with_children and args.images and not (args.project or args.out_dir):
        sys.exit("错误：--with-children --images 需要 -p 或 --out-dir")
    if args.mode in ("md-macro", "pandoc", "split-restore") and (args.html or args.raw):
        sys.exit("错误：--mode md-macro/pandoc/split-restore 不能与 --html / --raw 组合")
    if args.with_children and args.mode in ("md-macro", "pandoc", "split-restore"):
        sys.exit("错误：--with-children 与 --mode md-macro/pandoc/split-restore 互斥（split-restore 自己拉子页）")
    if args.view_map and args.mode not in ("auto", "split-restore"):
        sys.exit("错误：--view-map 仅 --mode split-restore 使用")

    base_url, token = load_creds()

    result = parse_url(args.url)
    if isinstance(result, tuple):
        _, space, title_q = result
        search = api_get(
            f"/rest/api/content?spaceKey={space}&title={urllib.parse.quote(title_q)}&expand=body.storage,version")
        results = search.get("results", [])
        if not results:
            sys.exit(f"错误：未找到页面 {space}/{title_q}")
        page = results[0]
    else:
        page_id = result
        page = api_get(
            f"/rest/api/content/{page_id}?expand=body.storage,version")

    title = page["title"]
    body_html = page["body"]["storage"]["value"]
    version = page.get("version", {}).get("number", "?")
    page_id = page["id"]
    safe_title = re.sub(r'[/:*?"<>|]', '-', title).strip()

    # ── with-children: 父页 + 所有子页合并 markdown ──
    if args.with_children:
        children = fetch_children(page_id)

        # --images：每个 page 的 attachment 落到 inputs/{img_dir}/{page_id}/，避免同名冲突
        page_imgs: dict[str, tuple[dict, str]] = {}  # page_id → (mapping, rel_dir)
        if args.images and args.project:
            project_dir = ROOT / "projects" / args.project
            if not project_dir.is_dir():
                sys.exit(f"错误：项目目录不存在 {project_dir}")
            img_root_name = f"confluence-{safe_title}-images"
            img_root = project_dir / "inputs" / "docs" / img_root_name

            for pg in [page] + children:
                pid = pg["id"]
                atts = fetch_attachments(pid, download=True)
                if not atts:
                    page_imgs[pid] = ({}, "")
                    continue
                subdir = img_root / pid
                mapping = save_images_to_dir(atts, subdir)
                rel_dir = f"{img_root_name}/{pid}"
                page_imgs[pid] = (mapping, rel_dir)
            total = sum(len(m) for m, _ in page_imgs.values())
            print(f"下载了 {total} 张图片到 {img_root}", file=sys.stderr)

        def _imgs(pid):
            return page_imgs.get(pid, ({}, ""))

        m, d = _imgs(page["id"])
        parts = [page_to_md_block(page, heading_offset=0, img_mapping=m, img_rel_dir=d)]
        for child in children:
            cm, cd = _imgs(child["id"])
            parts.append(page_to_md_block(child, heading_offset=1, img_mapping=cm, img_rel_dir=cd))
        content = "\n\n---\n\n".join(parts)
        ext = ".md"
        print(f"父页 + {len(children)} 子页合并完成", file=sys.stderr)
        if args.project:
            project_dir = ROOT / "projects" / args.project
            inputs_dir = project_dir / "inputs" / "docs"
            inputs_dir.mkdir(exist_ok=True)
            filename = args.output or f"confluence-{safe_title}-full{ext}"
            path = inputs_dir / filename
            path.write_text(content, encoding="utf-8")
            print(f"已保存: {path}（{len(content) // 1024}KB）", file=sys.stderr)
        else:
            print(content)
        return

    # ── 模式决议（auto 时先探子页判断 split 形态）──
    effective_mode = args.mode
    children_cache = None  # 复用避免重复 API 调用
    if effective_mode == "auto":
        children_cache = fetch_children(page_id)
        # 子页 split 形态判定：至少 1 个子页 body 含场景 heading
        split_children_detected = False
        for ch in children_cache:
            ch_body = ch.get("body", {}).get("storage", {}).get("value", "")
            # md-macro 子页：storage 是 <ac:structured-macro markdown><CDATA[md]>，先剥出 md 再匹配
            # raw-html 子页：storage 直接是 <h2>5.1 A-1 · …</h2>，按 storage 形态匹配
            md_segs = _MD_MACRO_RE.findall(ch_body)
            if any(_CHILD_SCENE_HEAD_RE.search(seg) for seg in md_segs) or re.search(
                r"<h2[^>]*>\s*\d+\.\d+\s+[A-Z][-\w]*\s*·", ch_body
            ):
                split_children_detected = True
                break
        effective_mode = detect_mode(body_html, has_split_children=split_children_detected)
        print(f"  → auto 嗅探 → mode={effective_mode}", file=sys.stderr)

    # ── split-restore: 父+子页还原本地 split 目录结构 ──
    if effective_mode == "split-restore":
        if children_cache is None:
            children_cache = fetch_children(page_id)
        children = children_cache
        if not children:
            sys.exit("错误：split-restore 模式需要父+子页结构，当前页无子页")

        view_map = parse_view_map(args.view_map) if args.view_map else {5: "front", 6: "back", 7: "cross"}
        if not args.view_map:
            print(
                "  ⚠ --view-map 未传，使用默认 {5:front,6:back,7:cross}；"
                "看子页标题对应不上时显式传 --view-map 精确还原",
                file=sys.stderr,
            )

        # 输出路径
        if args.out_dir:
            out_root = Path(args.out_dir).resolve()
        elif args.project:
            project_dir = ROOT / "projects" / args.project
            if not project_dir.is_dir():
                sys.exit(f"错误：项目目录不存在 {project_dir}")
            out_root = project_dir / "inputs" / "docs"
        else:
            sys.exit("错误：split-restore 模式需要 -p 或 --out-dir 指定输出位置")
        out_root.mkdir(parents=True, exist_ok=True)

        stem = args.stem or _safe_filename(title)
        main_md_path = out_root / f"{stem}.md"
        scenes_dir_name = f"{stem}-scenes"
        scenes_dir = out_root / scenes_dir_name
        assets_dir = out_root / "assets"
        scenes_dir.mkdir(parents=True, exist_ok=True)

        # 拉父页 attachments（仅 storage 引用的图）
        parent_refs = extract_referenced_images(body_html)
        if parent_refs and not args.no_images:
            parent_atts = fetch_attachments(page_id, download=True, filter_names=parent_refs)
            parent_img_map = save_images_to_dir(parent_atts, assets_dir)
        else:
            parent_img_map = {}
        parent_md = extract_md_macro(body_html, parent_img_map, "./assets")
        parent_md = ensure_h1(parent_md, title)

        # 处理子页：拉 storage + attachments + 切场景
        chapters_in_scope = set()
        sid_to_fname = {}
        total_scenes = 0
        total_imgs = len(parent_img_map)

        for child in children:
            child_id = child["id"]
            child_title = child["title"]
            child_body_html = child["body"]["storage"]["value"]
            child_refs = extract_referenced_images(child_body_html)
            if child_refs and not args.no_images:
                child_atts = fetch_attachments(child_id, download=True, filter_names=child_refs)
                child_img_map = save_images_to_dir(child_atts, assets_dir)
                total_imgs += len(child_img_map)
            else:
                child_img_map = {}
            child_md = extract_md_macro(child_body_html, child_img_map, "../assets")
            chapter = infer_chapter_from_child(child_md)
            if chapter is None:
                print(f"  ⚠ 子页 pageId={child_id}「{child_title}」无场景 heading，跳过", file=sys.stderr)
                continue
            view = view_map.get(chapter)
            if not view:
                print(f"  ⚠ §{chapter}「{child_title}」未在 --view-map 中声明，跳过", file=sys.stderr)
                continue
            chapters_in_scope.add(chapter)
            scenes = split_child_into_scenes(child_md, view)
            for s in scenes:
                (scenes_dir / s["fname"]).write_text(s["content"], encoding="utf-8")
                sid_to_fname[s["sid"]] = s["fname"]
            total_scenes += len(scenes)
            print(f"  → §{chapter}「{child_title}」→ view={view}, {len(scenes)} 场景", file=sys.stderr)

        # 主 md scene link 反向改写
        main_md_final, n_rewritten, unresolved = rewrite_parent_links_to_local(
            parent_md, chapters_in_scope, scenes_dir_name, sid_to_fname
        )
        main_md_path.write_text(main_md_final, encoding="utf-8")

        print("\n✓ split-restore 完成", file=sys.stderr)
        print(f"  主 md: {main_md_path}", file=sys.stderr)
        print(f"  场景目录: {scenes_dir} ({total_scenes} 文件)", file=sys.stderr)
        print(f"  图片目录: {assets_dir} ({total_imgs} 张)", file=sys.stderr)
        print(f"  scene link 改写: {n_rewritten} 条", file=sys.stderr)
        if unresolved:
            print(f"  ⚠ 未匹配 sid: {sorted(set(unresolved))}", file=sys.stderr)
        return

    # pandoc/md-macro 模式：默认只下载 storage 实际引用的图（不下页 attachment 全集）
    if effective_mode in ("pandoc", "md-macro"):
        # 输出位置：--out-dir 优先，其次 -p，再次 stdout（仅 md）
        if args.out_dir:
            out_root = Path(args.out_dir).resolve()
            assets_dir = out_root / "assets"
            img_rel_dir = "assets"
            out_root.mkdir(parents=True, exist_ok=True)
            download_imgs = not args.no_images
        elif args.project:
            project_dir = ROOT / "projects" / args.project
            if not project_dir.is_dir():
                sys.exit(f"错误：项目目录不存在 {project_dir}")
            out_root = project_dir / "inputs" / "docs"
            assets_dir = out_root / "assets"
            img_rel_dir = "assets"
            out_root.mkdir(parents=True, exist_ok=True)
            download_imgs = not args.no_images
        else:
            out_root = None
            assets_dir = None
            img_rel_dir = None
            download_imgs = False
            if not args.no_images:
                print(
                    "  ⚠ stdout 模式不下载图片，md 内 <img>/![]() 引用无效；"
                    "建议加 --out-dir <目录> 或 -p <项目>，或显式 --no-images 走纯文字",
                    file=sys.stderr,
                )

        img_mapping = None
        if download_imgs:
            referenced = extract_referenced_images(body_html)
            if referenced:
                print(f"  → storage 引用 {len(referenced)} 张图，仅下载这些（忽略页 attachment 全集）", file=sys.stderr)
                atts = fetch_attachments(page_id, download=True, filter_names=referenced)
                img_mapping = save_images_to_dir(atts, assets_dir)
                print(f"下载了 {len(img_mapping)} 张图片到 {assets_dir}", file=sys.stderr)
            else:
                img_mapping = {}
                print("  → storage 无图片引用，跳过下载", file=sys.stderr)
        elif args.no_images:
            print("  → --no-images：跳过图片下载（md 内引用保留为占位）", file=sys.stderr)

        if effective_mode == "md-macro":
            body_md = extract_md_macro(body_html, img_mapping, img_rel_dir)
        else:  # pandoc
            body_md = pandoc_render(body_html, img_rel_dir)

        content = (
            f"# {title}\n\n"
            f"> Confluence v{version} | pageId: {page_id}\n"
            f"> 源：{base_url}/pages/viewpage.action?pageId={page_id}\n\n"
            f"{body_md.strip()}\n"
        )

        if out_root is not None:
            filename = args.output or f"{safe_title}.md"
            path = out_root / filename
            path.write_text(content, encoding="utf-8")
            print(f"已保存: {path}（{len(content) // 1024}KB）", file=sys.stderr)
        else:
            print(content)
        return

    # ── 旧分支：simple / html / raw（向后兼容） ──
    need_download = args.images or args.html
    attachments = fetch_attachments(page_id, download=need_download) if need_download else {}

    if args.html:
        content = build_self_contained_html(title, version, page_id, body_html, attachments)
        ext = ".html"
        if attachments:
            total_kb = sum(len(v.get("bytes", b"")) for v in attachments.values()) // 1024
            print(f"内嵌 {len(attachments)} 张图片（{total_kb}KB）", file=sys.stderr)
    elif args.raw:
        content = body_html
        ext = ".html"
    else:
        img_mapping = None
        img_rel_dir = None
        if args.images and (args.project or args.out_dir):
            img_dir_name = f"confluence-{safe_title}-images"
            if args.project:
                img_dir = ROOT / "projects" / args.project / "inputs" / "docs" / img_dir_name
            else:
                img_dir = Path(args.out_dir).resolve() / img_dir_name
            img_mapping = save_images_to_dir(attachments, img_dir)
            img_rel_dir = img_dir_name
            print(f"下载了 {len(img_mapping)} 张图片到 {img_dir}", file=sys.stderr)
        content = f"# {title}\n\n> Confluence v{version} | pageId: {page_id}\n\n{html_to_markdown(body_html, img_mapping, img_rel_dir)}"
        ext = ".md"

    if args.project:
        project_dir = ROOT / "projects" / args.project
        if not project_dir.is_dir():
            sys.exit(f"错误：项目目录不存在 {project_dir}")
        inputs_dir = project_dir / "inputs" / "docs"
        inputs_dir.mkdir(exist_ok=True)
        filename = args.output or f"confluence-{safe_title}{ext}"
        path = inputs_dir / filename
        path.write_text(content, encoding="utf-8")
        print(f"已保存: {path}（{len(content) // 1024}KB）", file=sys.stderr)
    elif args.out_dir:
        # 守门已放行 --html/--images 配 --out-dir，这里落盘（原实现静默丢到 stdout）
        out_root = Path(args.out_dir).resolve()
        out_root.mkdir(parents=True, exist_ok=True)
        filename = args.output or f"confluence-{safe_title}{ext}"
        path = out_root / filename
        path.write_text(content, encoding="utf-8")
        print(f"已保存: {path}（{len(content) // 1024}KB）", file=sys.stderr)
    else:
        print(content)


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        sys.exit(f"错误：Confluence HTTP {e.code}\n  {body}\n  检查 CONF_BASE_URL / CONF_TOKEN / 页面权限")
    except urllib.error.URLError as e:
        sys.exit(f"错误：Confluence 请求失败 ({e})\n  检查网络 / CONF_BASE_URL")
