#!/usr/bin/env python3
"""Confluence 页面导航：不知道 pageId/URL 时按标题 / 内容词定位页面、按父页看子页树。

dig_confluence 靠 CQL 拉正文语料；本脚本只做「定位 + 结构导航」，不拉 body，
输出 pageId / URL 供后续 fetch_confluence / dig_confluence / md_to_confluence 用。

用法：
    # 按标题找页面（拿 pageId + URL）
    python3 scripts/nav_confluence.py find "直播竞品" [--space DEMO_SPACE_KEY] [--limit 20]

    # 按内容词全文搜索（返回 space + 高亮摘要 + pageId + URL，适合「哪个 space 的哪页提过 X」）
    python3 scripts/nav_confluence.py search "结算延迟" [--space DEMO_SPACE_KEY] [--limit 20]

    # 看父页下的子页树（默认只列直接子页；--recursive 递归）
    python3 scripts/nav_confluence.py tree <parentId> [--recursive] [--max-depth N] [--show-url]

示例：
    python3 scripts/nav_confluence.py find "WoodPecker" --limit 3
    python3 scripts/nav_confluence.py search "对拍" --limit 10
    python3 scripts/nav_confluence.py tree 151429067 --recursive --max-depth 3

前置：Confluence 凭证 CONF_BASE_URL + CONF_TOKEN（env，或仓库根 .mcp.json / .mcp-disabled.json
的 mcpServers.confluence.env）；--help 本身不需要。
输出形态：stdout——find 出 markdown 表（标题 | space | pageId | URL），search 出表格
（标题 | 类型 | 空间 | 摘要 | URL，摘要为净化后的高亮片段），tree 出缩进树；不落盘。
退出码：0（子命令均已给定时；命中 0 篇提示在 stdout，不算失败）。
"""
from __future__ import annotations

import pathlib as _pl

# route-log: 调用埋点（scripts/lib/route_log.py）
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("nav_confluence"))

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.confluence import base_url, list_child_pages, search_content, search_pages  # noqa: E402


def page_url(page: dict) -> str:
    """从 page 的 _links.webui 拼完整 URL；缺失回退 viewpage.action。"""
    webui = page.get("_links", {}).get("webui")
    if webui:
        return f"{base_url()}{webui}"
    return f"{base_url()}/pages/viewpage.action?pageId={page['id']}"


def build_find_cql(title_kw: str, space: str | None) -> str:
    """按标题模糊匹配拼 CQL；可选限定 space。"""
    safe = title_kw.replace('"', '\\"')
    parts = ["type=page", f'title ~ "{safe}"']
    if space:
        parts.insert(0, f'space="{space}"')
    return " AND ".join(parts) + " order by created desc"


def render_find(hits: list[dict]) -> str:
    """渲染 find 结果为一张表（标题 | space | pageId | URL）。"""
    if not hits:
        return "命中 0 篇。放宽关键词，或确认 --space 是否正确。"
    lines = ["| 标题 | space | pageId | URL |", "|------|-------|--------|-----|"]
    for p in hits:
        space_key = p.get("space", {}).get("key", "—")
        lines.append(f"| {p['title']} | {space_key} | {p['id']} | {page_url(p)} |")
    return "\n".join(lines)


def walk_tree(parent_id: str, recursive: bool, max_depth: int, _depth: int = 0) -> list[dict]:
    """递归收集子页，返回 [{page, depth}, ...]（前序）。

    max_depth 从 1 起（1 = 只直接子页）；recursive=False 等价 max_depth=1。
    """
    out: list[dict] = []
    for p in list_child_pages(parent_id):
        out.append({"page": p, "depth": _depth})
        deeper = recursive and (max_depth <= 0 or _depth + 1 < max_depth)
        if deeper:
            out.extend(walk_tree(p["id"], recursive, max_depth, _depth + 1))
    return out


def build_search_cql(keyword: str, space: str | None) -> str:
    """按内容词全文匹配拼 CQL；可选限定 space。"""
    safe = keyword.replace('"', '\\"')
    parts = [f'text ~ "{safe}"']
    if space:
        parts.insert(0, f'space="{space}"')
    return " AND ".join(parts)


def clean_excerpt(excerpt: str) -> str:
    """净化高亮摘要：去 HTML 实体翻转、剥 @@@hl@@@ 标记、压缩空白、截 80 字。"""
    text = html.unescape(excerpt)
    text = re.sub(r"@@@(?:hl|endhl)@@@", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= 80 else text[:80] + "…"


def search_space_key(result: dict) -> str:
    """从 resultGlobalContainer.displayUrl（/display/<key>）取 space key，缺失回退空间名。"""
    cont = result.get("resultGlobalContainer") or {}
    m = re.search(r"/display/([^/?#]+)", cont.get("displayUrl") or "")
    if m:
        return m.group(1)
    return cont.get("title") or "—"


def search_page_id(result: dict) -> str:
    """从 url 的 pageId= 参数取父页 id（attachment 结果指向其父页）；回退 content.id。"""
    m = re.search(r"pageId=(\d+)", result.get("url") or "")
    if m:
        return m.group(1)
    content = result.get("content")
    if isinstance(content, dict) and content.get("type") == "page" and content.get("id"):
        return str(content["id"])
    return "—"


def render_search(hits: list[dict]) -> str:
    """渲染 search 结果为一张表（标题 | 类型 | 空间 | 摘要 | URL）。"""
    if not hits:
        return "命中 0 篇。放宽关键词，或确认 --space 是否正确。"
    lines = ["| 标题 | 类型 | 空间 | 摘要 | URL |", "|------|------|------|------|-----|"]
    for r in hits:
        content = r.get("content")
        kind = content.get("type", "—") if isinstance(content, dict) else "—"
        url = f"{base_url()}{r.get('url', '')}".split("&preview=")[0]  # 去掉 preview 前缀尾巴
        cells = [
            str(r.get("title") or "—"),
            str(kind),
            str(search_space_key(r)),
            clean_excerpt(r.get("excerpt") or ""),
            url,
        ]
        cells = [c.replace("|", "\\|") for c in cells]  # 摘要/标题可能含 |，防表格断裂
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_tree(nodes: list[dict], show_url: bool) -> str:
    """缩进渲染树：每层两空格 + └─，可选带 pageId / URL。"""
    if not nodes:
        return "该父页下没有子页（或 parentId 不对）。"
    lines = []
    for n in nodes:
        p = n["page"]
        indent = "  " * n["depth"]
        tail = f"  [{p['id']}]"
        if show_url:
            tail += f"  {page_url(p)}"
        lines.append(f"{indent}- {p['title']}{tail}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    fp = sub.add_parser("find", help="按标题模糊找页面，拿 pageId + URL")
    fp.add_argument("title", help="标题关键词（模糊匹配）")
    fp.add_argument("--space", help="限定 space key（如 DEMO_SPACE_KEY；缺省不限）")
    fp.add_argument("--limit", type=int, default=20, help="最多返回几条（默认 20）")

    sp = sub.add_parser("search", help="按内容词全文搜索，返回 space + 高亮摘要 + pageId + URL")
    sp.add_argument("keyword", help="内容词（全文匹配，CQL text~）")
    sp.add_argument("--space", help="限定 space key（如 DEMO_SPACE_KEY；缺省不限）")
    sp.add_argument("--limit", type=int, default=20, help="最多返回几条（默认 20）")

    tp = sub.add_parser("tree", help="看父页下的子页树")
    tp.add_argument("parent_id", help="父页 pageId")
    tp.add_argument("--recursive", action="store_true", help="递归所有后代（默认只列直接子页）")
    tp.add_argument("--max-depth", type=int, default=0, help="递归最大层数（0 = 不限；需配 --recursive）")
    tp.add_argument("--show-url", action="store_true", help="每行带完整 URL")

    args = ap.parse_args()

    if args.cmd == "find":
        cql = build_find_cql(args.title, args.space)
        print(f"CQL: {cql}", file=sys.stderr)
        hits = search_pages(cql, limit=args.limit, expand="space")
        print(render_find(hits))
    elif args.cmd == "search":
        cql = build_search_cql(args.keyword, args.space)
        print(f"CQL: {cql}", file=sys.stderr)
        hits = search_content(cql, limit=args.limit)
        print(render_search(hits))
    elif args.cmd == "tree":
        if args.max_depth and not args.recursive:
            print("警告：--max-depth 需配合 --recursive 才生效，当前只列直接子页。", file=sys.stderr)
        nodes = walk_tree(args.parent_id, args.recursive, args.max_depth)
        print(render_tree(nodes, args.show_url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
