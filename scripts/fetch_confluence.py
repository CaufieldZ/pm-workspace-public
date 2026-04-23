#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""从 Confluence URL 拉取页面内容。

用法:
  python3 scripts/fetch_confluence.py <url>                          # markdown 到 stdout
  python3 scripts/fetch_confluence.py <url> -p 项目名                # markdown 存到 inputs/
  python3 scripts/fetch_confluence.py <url> -p 项目名 --images       # markdown + 图片目录
  python3 scripts/fetch_confluence.py <url> -p 项目名 --html         # 单 HTML 文件（图片 base64 内嵌）
  python3 scripts/fetch_confluence.py <url> -p 项目名 -o custom.md   # 指定文件名

支持的 URL 格式:
  https://INTERNAL_URL_REDACTED
  https://INTERNAL_URL_REDACTED

直调 Confluence REST API，不需要加载 MCP server。
"""

import argparse, base64, html, json, mimetypes, os, re, sys, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_creds():
    for src in [ROOT / ".mcp.json", ROOT / ".mcp-disabled.json"]:
        if src.exists():
            cfg = json.loads(src.read_text())
            env = cfg.get("mcpServers", {}).get("confluence", {}).get("env")
            if env and "CONF_BASE_URL" in env:
                return env["CONF_BASE_URL"].rstrip("/"), env["CONF_TOKEN"]
    sys.exit("错误：找不到 confluence 配置（.mcp.json 和 .mcp-disabled.json 都没有）")


def api_get(base_url, token, path):
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def api_download_bytes(base_url, token, path):
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


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


def fetch_attachments(base_url, token, page_id, download=False):
    """获取附件列表，可选下载。返回 {filename: {dl_path, bytes?, mime}}。"""
    mapping = {}
    start = 0
    while True:
        data = api_get(base_url, token,
            f"/rest/api/content/{page_id}/child/attachment?start={start}&limit=50")
        for att in data.get("results", []):
            fname = att["title"]
            if not re.search(r"\.(png|jpg|jpeg|gif|svg|webp)$", fname, re.I):
                continue
            dl_path = att["_links"]["download"]
            mime = mimetypes.guess_type(fname)[0] or "image/png"
            entry = {"dl_path": dl_path, "mime": mime}
            if download:
                entry["bytes"] = api_download_bytes(base_url, token, dl_path)
                print(f"  图片: {fname} ({len(entry['bytes']) // 1024}KB)", file=sys.stderr)
            mapping[fname] = entry
        total = data.get("totalCount", data.get("size", 0))
        if data.get("size", 0) + start >= total:
            break
        start += data["size"]
    return mapping


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
            fname = m.group(1)
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
    text = re.sub(r"<img[^>]*alt=\"([^\"]+)\"[^>]*>", r"![\1]", text)
    text = re.sub(r"<img[^>]*src=\"([^\"]+)\"[^>]*>", r"![image](\1)", text)
    text = re.sub(r"<ac:structured-macro[^>]*ac:name=\"code\"[^>]*>.*?<ac:plain-text-body>\s*<!\[CDATA\[(.*?)\]\]>\s*</ac:plain-text-body>\s*</ac:structured-macro>",
                  r"\n```\n\1\n```\n", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── HTML 单文件输出 ──────────────────────────────────────────

def build_self_contained_html(title, version, page_id, body_html, attachments):
    """Confluence storage HTML → 自包含 HTML，图片 base64 内嵌。"""

    def replace_ac_image(m):
        fname = m.group(1)
        width = m.group(2)
        info = attachments.get(fname)
        if info and "bytes" in info:
            b64 = base64.b64encode(info["bytes"]).decode()
            style = f' style="max-width:{width}px"' if width else ""
            return f'<img src="data:{info["mime"]};base64,{b64}" alt="{fname}"{style} />'
        return f'<p>[图片缺失: {fname}]</p>'

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


def main():
    parser = argparse.ArgumentParser(description="从 Confluence 拉取页面内容")
    parser.add_argument("url", help="Confluence 页面 URL")
    parser.add_argument("--project", "-p", help="项目名（存到 inputs/）")
    parser.add_argument("--output", "-o", help="输出文件名（默认用页面标题）")
    parser.add_argument("--images", action="store_true", help="markdown + 图片目录（需 -p）")
    parser.add_argument("--html", action="store_true", help="单 HTML 文件，图片 base64 内嵌（需 -p）")
    parser.add_argument("--raw", action="store_true", help="输出原始 Confluence 存储 HTML")
    args = parser.parse_args()

    if (args.images or args.html) and not args.project:
        sys.exit("错误：--images / --html 需要配合 -p 指定项目")

    base_url, token = load_creds()

    result = parse_url(args.url)
    if isinstance(result, tuple):
        _, space, title_q = result
        search = api_get(base_url, token,
            f"/rest/api/content?spaceKey={space}&title={urllib.parse.quote(title_q)}&expand=body.storage,version")
        results = search.get("results", [])
        if not results:
            sys.exit(f"错误：未找到页面 {space}/{title_q}")
        page = results[0]
    else:
        page_id = result
        page = api_get(base_url, token,
            f"/rest/api/content/{page_id}?expand=body.storage,version")

    title = page["title"]
    body_html = page["body"]["storage"]["value"]
    version = page.get("version", {}).get("number", "?")
    page_id = page["id"]
    safe_title = re.sub(r'[/:*?"<>|]', '-', title).strip()

    need_download = args.images or args.html
    attachments = fetch_attachments(base_url, token, page_id, download=need_download) if need_download else {}

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
        if args.images and args.project:
            img_dir_name = f"confluence-{safe_title}-images"
            img_dir = ROOT / "projects" / args.project / "inputs" / img_dir_name
            img_mapping = save_images_to_dir(attachments, img_dir)
            img_rel_dir = img_dir_name
            print(f"下载了 {len(img_mapping)} 张图片到 {img_dir}", file=sys.stderr)
        content = f"# {title}\n\n> Confluence v{version} | pageId: {page_id}\n\n{html_to_markdown(body_html, img_mapping, img_rel_dir)}"
        ext = ".md"

    if args.project:
        project_dir = ROOT / "projects" / args.project
        if not project_dir.is_dir():
            sys.exit(f"错误：项目目录不存在 {project_dir}")
        inputs_dir = project_dir / "inputs"
        inputs_dir.mkdir(exist_ok=True)
        filename = args.output or f"confluence-{safe_title}{ext}"
        path = inputs_dir / filename
        path.write_text(content)
        print(f"已保存: {path}（{len(content) // 1024}KB）", file=sys.stderr)
    else:
        print(content)


if __name__ == "__main__":
    main()
