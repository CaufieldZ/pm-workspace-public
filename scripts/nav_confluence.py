#!/usr/bin/env python3
"""Confluence 页面导航：不知道 pageId/URL 时按标题定位页面、按父页看子页树。

dig_confluence 靠 CQL 拉正文语料；本脚本只做「定位 + 结构导航」，不拉 body，
输出 pageId / URL 供后续 fetch_confluence / dig_confluence / md_to_confluence 用。

用法：
    # 按标题找页面（拿 pageId + URL）
    python3 scripts/nav_confluence.py find "直播竞品" [--space jituankejizhongxin] [--limit 20]

    # 看父页下的子页树（默认只列直接子页；--recursive 递归）
    python3 scripts/nav_confluence.py tree <parentId> [--recursive] [--max-depth N] [--show-url]

示例：
    python3 scripts/nav_confluence.py find "红包雨" --space jituankejizhongxin
    python3 scripts/nav_confluence.py tree 151429067 --recursive --max-depth 3
"""
from __future__ import annotations

import pathlib as _pl

# route-log: 调用埋点（scripts/lib/route_log.py）
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("nav_confluence"))

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.confluence import base_url, list_child_pages, search_pages  # noqa: E402


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
    ap = argparse.ArgumentParser(description="Confluence 页面导航：按标题定位 / 看子页树")
    sub = ap.add_subparsers(dest="cmd", required=True)

    fp = sub.add_parser("find", help="按标题模糊找页面，拿 pageId + URL")
    fp.add_argument("title", help="标题关键词（模糊匹配）")
    fp.add_argument("--space", help="限定 space key（如 jituankejizhongxin；缺省不限）")
    fp.add_argument("--limit", type=int, default=20, help="最多返回几条（默认 20）")

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
    elif args.cmd == "tree":
        if args.max_depth and not args.recursive:
            print("警告：--max-depth 需配合 --recursive 才生效，当前只列直接子页。", file=sys.stderr)
        nodes = walk_tree(args.parent_id, args.recursive, args.max_depth)
        print(render_tree(nodes, args.show_url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
