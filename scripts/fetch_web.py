#!/usr/bin/env python3
"""通过 Firecrawl 抓取网页（替代 firecrawl MCP，省 ~6K token）。

适用场景（CLAUDE.md「Web 工具选择」）：
  - SPA 页面 JS 渲染（WebFetch 返空）
  - 多页站点批量抓取
  - 需要 onlyMainContent / waitFor / 截图

用法:
  # 抓单页（默认 markdown）
  python3 scripts/fetch_web.py <url>
  python3 scripts/fetch_web.py <url> -p 项目名               # 存到 projects/{项目}/inputs/web/
  python3 scripts/fetch_web.py <url> -o page.md              # 指定输出文件

  # 多种 format（逗号分隔）
  python3 scripts/fetch_web.py <url> --formats markdown,html
  python3 scripts/fetch_web.py <url> --formats links         # 只抓页面所有链接

  # 截图
  python3 scripts/fetch_web.py <url> --screenshot            # 视口截图（PNG）
  python3 scripts/fetch_web.py <url> --screenshot --full     # 全页截图

  # SPA 渲染等待
  python3 scripts/fetch_web.py <url> --wait-for 2000         # 等 2s 让 JS 跑完

  # 关掉 onlyMainContent（默认 true）
  python3 scripts/fetch_web.py <url> --no-main-content

  # 找站点所有 URL（map endpoint）
  python3 scripts/fetch_web.py <url> --map
  python3 scripts/fetch_web.py <url> --map --search "blog"   # 按关键词过滤

  # 批量抓多页（避免一个个调）
  python3 scripts/fetch_web.py - --batch urls.txt -p 项目名  # urls.txt 一行一个 URL

凭证读取优先级:
  1. 环境变量 FIRECRAWL_API_KEY
  2. .mcp-disabled.json → mcpServers.firecrawl.env.FIRECRAWL_API_KEY
  3. .mcp.json → mcpServers.firecrawl.env.FIRECRAWL_API_KEY
"""

import argparse, json, os, re, sys, time, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_BASE = "https://api.firecrawl.dev/v1"


# ── 凭证 ──────────────────────────────────────────────────────

def load_api_key():
    key = os.environ.get("FIRECRAWL_API_KEY")
    if key:
        return key
    for src in [ROOT / ".mcp-disabled.json", ROOT / ".mcp.json"]:
        if src.exists():
            cfg = json.loads(src.read_text())
            env = cfg.get("mcpServers", {}).get("firecrawl", {}).get("env", {})
            if "FIRECRAWL_API_KEY" in env:
                return env["FIRECRAWL_API_KEY"]
    sys.exit(
        "错误：找不到 FIRECRAWL_API_KEY。\n"
        "三种配法任选一：\n"
        "  1. export FIRECRAWL_API_KEY=fc-xxx\n"
        "  2. .mcp-disabled.json → mcpServers.firecrawl.env.FIRECRAWL_API_KEY\n"
        "  3. .mcp.json → mcpServers.firecrawl.env.FIRECRAWL_API_KEY"
    )


# ── HTTP ──────────────────────────────────────────────────────

def api_post(api_key, path, body, timeout=120):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"错误：Firecrawl API {e.code}：{body[:300]}")


def download_bytes(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


# ── core ──────────────────────────────────────────────────────

def scrape(api_key, url, formats=None, only_main_content=True, wait_for=None,
           timeout=30000):
    """单页抓取，返回 {markdown, html, links, screenshot URL, metadata, ...}。"""
    body = {
        "url": url,
        "formats": formats or ["markdown"],
        "onlyMainContent": only_main_content,
    }
    if wait_for:
        body["waitFor"] = int(wait_for)
    if timeout:
        body["timeout"] = int(timeout)
    resp = api_post(api_key, "/scrape", body)
    if not resp.get("success", True):
        sys.exit(f"错误：Firecrawl 返回失败：{resp.get('error', resp)}")
    return resp.get("data", {})


def map_site(api_key, url, search=None, limit=5000):
    """抓站点 URL 列表（map endpoint）。"""
    body = {"url": url, "limit": limit}
    if search:
        body["search"] = search
    resp = api_post(api_key, "/map", body)
    if not resp.get("success", True):
        sys.exit(f"错误：Firecrawl 返回失败：{resp.get('error', resp)}")
    return resp.get("links", [])


def safe_filename_from_url(url, ext="md"):
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.replace(":", "_")
    path = re.sub(r"[^\w\-]+", "_", parsed.path).strip("_") or "index"
    return f"{host}_{path}.{ext}"[:200]


# ── 输出 helpers ──────────────────────────────────────────────

def determine_out_path(args, url, default_ext):
    """根据 -p / -o / 默认 stdout 决定输出位置。返回 Path 或 None（stdout）。"""
    if args.output:
        return Path(args.output)
    if args.project:
        out_dir = ROOT / "projects" / args.project / "inputs" / "web"
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / safe_filename_from_url(url, ext=default_ext)
    return None


def write_or_print(content, out_path, binary=False):
    if out_path is None:
        if binary:
            sys.stdout.buffer.write(content)
        else:
            sys.stdout.write(content)
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        out_path.write_bytes(content)
    else:
        out_path.write_text(content)
    print(f"已保存: {out_path}", file=sys.stderr)


# ── 单 URL 处理 ───────────────────────────────────────────────

def handle_single(api_key, url, args):
    formats = []
    if args.screenshot:
        formats = ["screenshot@fullPage"] if args.full else ["screenshot"]
    elif args.formats:
        formats = [f.strip() for f in args.formats.split(",") if f.strip()]
    else:
        formats = ["markdown"]

    data = scrape(
        api_key, url,
        formats=formats,
        only_main_content=not args.no_main_content,
        wait_for=args.wait_for,
    )

    # 截图模式：从返回 URL 下载 PNG
    if "screenshot" in formats[0]:
        shot_url = data.get("screenshot")
        if not shot_url:
            sys.exit("错误：Firecrawl 未返回截图 URL")
        img_bytes = download_bytes(shot_url)
        out = determine_out_path(args, url, default_ext="png")
        write_or_print(img_bytes, out, binary=True)
        return

    # 多 format → JSON 输出
    if len(formats) > 1:
        out = determine_out_path(args, url, default_ext="json")
        write_or_print(json.dumps(data, ensure_ascii=False, indent=2), out)
        return

    # 单 format 文本（markdown / html / rawHtml / links）
    fmt = formats[0]
    content = data.get(fmt, "")
    if isinstance(content, list):
        content = "\n".join(content)
    if not content:
        sys.exit(f"错误：Firecrawl 未返回 {fmt} 字段（页面可能为空 / 渲染失败）")
    ext_map = {"markdown": "md", "html": "html", "rawHtml": "html", "links": "txt"}
    out = determine_out_path(args, url, default_ext=ext_map.get(fmt, "txt"))
    write_or_print(content, out)


# ── 批量 URL 处理 ─────────────────────────────────────────────

def handle_batch(api_key, urls, args):
    if args.project:
        out_dir = ROOT / "projects" / args.project / "inputs" / "web"
    elif args.output:
        out_dir = Path(args.output)
    else:
        out_dir = Path("web-export")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"批量抓取 {len(urls)} 个页面 → {out_dir}", file=sys.stderr)

    for i, url in enumerate(urls, 1):
        try:
            data = scrape(
                api_key, url,
                formats=["markdown"],
                only_main_content=not args.no_main_content,
                wait_for=args.wait_for,
            )
            md = data.get("markdown", "")
            if not md:
                print(f"  [{i}/{len(urls)}] ⚠ 跳过 {url}：无 markdown", file=sys.stderr)
                continue
            fname = safe_filename_from_url(url, ext="md")
            (out_dir / fname).write_text(md)
            print(f"  [{i}/{len(urls)}] ✓ {fname}", file=sys.stderr)
        except SystemExit as e:
            print(f"  [{i}/{len(urls)}] ✗ {url}: {e}", file=sys.stderr)
        # 简单节流，避免触发限速
        if i < len(urls):
            time.sleep(0.5)


def load_batch_urls(arg):
    """支持 --batch <file>（一行一个 URL）或 --batch -（stdin）。"""
    if arg == "-":
        raw = sys.stdin.read()
    else:
        p = Path(arg)
        if not p.exists():
            sys.exit(f"错误：批量 URL 文件不存在：{arg}")
        raw = p.read_text()
    return [line.strip() for line in raw.splitlines() if line.strip() and not line.startswith("#")]


# ── CLI ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Firecrawl 网页抓取脚本（替代 firecrawl MCP）")
    parser.add_argument("url", help="目标 URL；批量模式传 '-'")
    parser.add_argument("--formats", help="逗号分隔，可选 markdown,html,rawHtml,links,json")
    parser.add_argument("--screenshot", action="store_true", help="抓截图（PNG）")
    parser.add_argument("--full", action="store_true", help="--screenshot 时取全页（screenshot@fullPage）")
    parser.add_argument("--wait-for", type=int, help="渲染等待毫秒（SPA 必备）")
    parser.add_argument("--no-main-content", action="store_true",
                        help="关闭 onlyMainContent（默认 true，会去掉导航/页脚）")
    parser.add_argument("--map", action="store_true", help="map 模式：返回站点所有 URL")
    parser.add_argument("--search", help="--map 时按关键词过滤")
    parser.add_argument("--limit", type=int, default=5000, help="--map 限制 URL 数量")
    parser.add_argument("--batch", metavar="FILE|-", help="批量模式：从文件 / stdin 读 URL 列表")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("-p", "--project", help="项目名，存到 projects/{项目}/inputs/web/")
    args = parser.parse_args()

    api_key = load_api_key()

    # 批量模式
    if args.batch:
        urls = load_batch_urls(args.batch)
        if not urls:
            sys.exit("错误：批量列表为空")
        handle_batch(api_key, urls, args)
        return

    # map 模式
    if args.map:
        links = map_site(api_key, args.url, search=args.search, limit=args.limit)
        if args.output:
            Path(args.output).write_text("\n".join(links))
            print(f"已保存 {len(links)} 个 URL → {args.output}", file=sys.stderr)
        else:
            print("\n".join(links))
        return

    # 单页模式
    handle_single(api_key, args.url, args)


if __name__ == "__main__":
    main()
