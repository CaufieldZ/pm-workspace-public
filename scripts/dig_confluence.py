#!/usr/bin/env python3
"""考古：按 feature 关键词批量拉一组历史迭代文档，聚成一份按时间正序的语料 md。

一个 feature 常被多篇独立的历史迭代文档（≈ 工区的 delta）反复改过，最终成为线上真相。
本脚本按关键词在指定 space（可选限定父页子树）圈出所有相关文档，逐页转 md，
按「标题版本号优先、创建时间兜底」正序拼成一份语料，供后续 agent 重建
「现状真相 + 演进时间线」。也可 --page-id 单页考古：拉当前正文 + 逐版本元数据时间线
（谁/何时改的；Platform C 实例历史版本正文拉不到，只能给元数据）。

用法：
    python3 scripts/dig_confluence.py "<feature 关键词>" [--space <KEY>] [--parent-id <ID>] [--limit N] [-p <项目>] [--out-dir DIR] [--images]
    python3 scripts/dig_confluence.py --page-id <ID> [-p <项目>] [--out-dir DIR] [--images]

示例：
    python3 scripts/dig_confluence.py "红包雨" --limit 5
    python3 scripts/dig_confluence.py "邀请返佣" --parent-id 151429067 -p growth
    python3 scripts/dig_confluence.py --page-id 151429067
"""

from __future__ import annotations

import pathlib as _pl

# route-log: 调用埋点（scripts/lib/route_log.py）
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("dig_confluence"))

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_confluence import _safe_filename, page_to_md_block, save_images_to_dir  # noqa: E402
from lib.confluence import api_request, base_url, fetch_attachments, get_page, search_pages  # noqa: E402
from lib.confluence_storage import extract_referenced_images  # noqa: E402


def build_cql(keyword: str | None, space: str, parent_id: str | None = None, in_title: bool = False) -> str:
    """拼 CQL：space + 可选关键词（title 或全文）+ 可选父页子树。

    按 created desc 排：limit 截断时保住**最新**的 N 篇（考古现状真相在最新文档），
    本地 sort_pages 再把它们正序渲染成演进时间线。
    in_title=True 走标题匹配（泛 feature 词下远比全文精准，噪声少）。
    keyword 为空时纯按 parent_id 拉整棵子树（父页考古，不做关键词过滤）。
    """
    parts = [f'space="{space}"', "type=page"]
    if keyword:
        safe_kw = keyword.replace('"', '\\"')
        field = "title" if in_title else "text"
        parts.append(f'{field} ~ "{safe_kw}"')
    if parent_id:
        parts.append(f"ancestor={parent_id}")
    return " AND ".join(parts) + " order by created desc"


_VER_RE = re.compile(r"[vV](\d+(?:\.\d+)*)")
_DATE_RE = re.compile(r"(\d{4})[-/.](\d{1,2})(?:[-/.](\d{1,2}))?")
_QUARTER_RE = re.compile(r"(\d{4})?\s*[qQ]([1-4])")


def title_version_key(title: str) -> tuple | None:
    """从标题抽一个可比的版本键；抽不到返回 None。

    命中优先级：日期（YYYY-MM[-DD]）> 季度（[YYYY]Qn）> vN[.n]。
    返回可比 tuple，供有命名规律的迭代之间正序排列；无规律的交给创建时间兜底。
    """
    m = _DATE_RE.search(title)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        return (0, y, mo, d)
    m = _QUARTER_RE.search(title)
    if m:
        y = int(m.group(1)) if m.group(1) else 0
        return (1, y, int(m.group(2)))
    m = _VER_RE.search(title)
    if m:
        nums = tuple(int(x) for x in m.group(1).split("."))
        return (2,) + nums
    return None


def sort_pages(items: list[dict]) -> list[dict]:
    """按「创建时间为全局主键、标题版本号为同段 tie-break」正序排。

    items: [{"page": {...}, "created": iso, "updated": iso}, ...]
    创建时间保证全局单调；同时刻/相近文档再按标题版本键细分。
    """
    def key(item):
        vk = title_version_key(item["page"]["title"])
        return (item["created"], vk if vk is not None else ())

    return sorted(items, key=key)


SOP_BLOCK = """## 这份语料怎么用（下一步 SOP）

1. 综合：把本语料喂 general-purpose agent，重建两段——「现状真相」（各功能最终态）+「演进时间线」（谁改了什么、带 pageId）。语料 > 1 万行时按时间正序分段并行派，agent prompt 禁读写 session-state。
2. 反哺 baseline：**先做 gap 全量比对**（考古全部功能 vs baseline 逐项、标在线性），别只做「深度补强」就收工。完整四铁律见 `.claude/runbooks/confluence-archaeology.md`。
"""


def render_corpus(keyword: str | None, space: str, parent_id: str | None, items: list[dict], with_images: bool) -> str:
    """把已排序的 items 渲染成一份考古语料 md（顶部时间轴索引 + 各篇正文）。"""
    base = base_url()
    lines = [
        f"# 考古语料：{keyword or f'父页 {parent_id} 子树'}",
        "",
        f"> space=`{space}`"
        + (f" · ancestor=`{parent_id}`" if parent_id else "")
        + f" · 命中 {len(items)} 篇 · 按时间正序（创建时间为主，标题版本号细分）",
        "",
        SOP_BLOCK,
        "## 命中清单（时间轴）",
        "",
        "| # | 文档 | 创建 | 最后更新 | 最后修改 | pageId |",
        "|---|------|------|----------|----------|--------|",
    ]
    for i, item in enumerate(items, 1):
        p = item["page"]
        webui = p.get("_links", {}).get("webui")
        url = f"{base}{webui}" if webui else ""
        title_cell = f"[{p['title']}]({url})" if url else p["title"]
        lines.append(
            f"| {i} | {title_cell} | {item['created'][:10]} | {item['updated'][:10]} | {item['author']} | {p['id']} |"
        )
    lines += ["", "---", ""]

    for i, item in enumerate(items, 1):
        p = item["page"]
        src = (
            f"> 文档 #{i} · pageId {p['id']} · "
            f"创建 {item['created'][:10]} · 最后更新 {item['updated'][:10]}"
            + (f" · 最后修改 {item['author']}" if item["author"] != "—" else "")
        )
        block = page_to_md_block(
            p,
            heading_offset=1,
            img_mapping=item.get("img_mapping") if with_images else None,
            img_rel_dir="assets" if with_images else None,
        )
        lines += [src, "", block, "", "---", ""]

    return "\n".join(lines)


# ── 单页考古：当前正文 + 逐版本元数据时间线 ─────────────────────────────────
# Platform C 实例限制：历史版本正文拉不到（status=historical&version=N 的 body.storage
# 恒空，experimental 端点同），版本考古只能给元数据（谁 / 何时 / minorEdit）。


def fetch_page_versions(page_id: str) -> tuple[dict, list[dict]]:
    """拉当前页（含正文）+ 逐版本元数据（experimental /version/{n}，轻量）。

    返回 (page, timeline)，timeline 新 → 旧 [{number, by, when, minor}, ...]。
    """
    page = get_page(page_id, expand="body.storage,version,history,space")
    latest = page["version"]["number"]
    timeline = []
    for v in range(latest, 0, -1):
        meta = api_request("GET", f"/rest/experimental/content/{page_id}/version/{v}")
        timeline.append({
            "number": meta.get("number", v),
            "by": meta.get("by", {}).get("displayName", "—"),
            "when": (meta.get("when") or "")[:19].replace("T", " "),
            "minor": meta.get("minorEdit", False),
        })
        print(f"  → v{v}/{latest}", file=sys.stderr, end="\r")
    print(file=sys.stderr)
    return page, timeline


def render_page_corpus(page: dict, timeline: list[dict], img_mapping=None) -> str:
    """单页考古语料：版本时间线（新 → 旧）+ 当前正文。"""
    lines = [
        f"# 考古语料（单页）：{page['title']}",
        "",
        f"> pageId={page['id']} · 当前 v{page['version']['number']} · "
        f"创建 {(page.get('history', {}).get('createdDate') or '')[:10]} · "
        f"共 {len(timeline)} 版（历史版本正文实例拉不到，时间线为元数据）",
        "",
        SOP_BLOCK,
        "## 版本时间线（新 → 旧）",
        "",
        "| 版本 | 修改人 | 时间 | minor |",
        "|------|--------|------|-------|",
    ]
    for t in timeline:
        lines.append(f"| v{t['number']} | {t['by']} | {t['when']} | {'是' if t['minor'] else '—'} |")
    lines += ["", "---", ""]
    lines.append(page_to_md_block(page, img_mapping=img_mapping, img_rel_dir="assets" if img_mapping else None))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Confluence 考古：批量拉迭代文档聚成时间线语料 / 单页版本考古")
    ap.add_argument("keyword", nargs="?", help="feature 关键词（全文匹配）；省略则纯按 --parent-id 拉整棵子树")
    ap.add_argument("--space", default="jituankejizhongxin", help="Confluence space key（默认 jituankejizhongxin）")
    ap.add_argument("--parent-id", help="限定在某父页子树下（CQL ancestor 子句）；无 keyword 时必填")
    ap.add_argument("--page-id", help="单页考古模式：当前正文 + 逐版本元数据时间线（与 keyword / --parent-id 互斥）")
    ap.add_argument("--limit", type=int, default=25, help="最多拉几篇（默认 25，取最新 N 篇）")
    ap.add_argument("--title", action="store_true", help="按标题匹配（泛 feature 词强烈建议，噪声远少于全文）")
    ap.add_argument("--project", "-p", help="项目名（语料落 projects/{项目}/inputs/docs/）")
    ap.add_argument("--out-dir", help="通用输出目录（与 -p 互斥）")
    ap.add_argument("--images", action="store_true", help="下载正文图片到 assets/（默认纯文字省 token；只下 storage 实际引用的）")
    args = ap.parse_args()

    if args.project and args.out_dir:
        sys.exit("错误：-p / --project 与 --out-dir 互斥")
    if args.page_id:
        if args.keyword or args.parent_id:
            sys.exit("错误：--page-id 单页模式与 keyword / --parent-id 互斥")
    elif not args.keyword and not args.parent_id:
        sys.exit("错误：keyword 与 --parent-id 至少给一个（单页考古用 --page-id）")

    def _resolve_out_dir():
        if args.project:
            out = ROOT / "projects" / args.project / "inputs" / "docs"
        elif args.out_dir:
            out = Path(args.out_dir)
        else:
            out = Path.cwd()
        out.mkdir(parents=True, exist_ok=True)
        return out

    # ── 单页考古模式 ──
    if args.page_id:
        out_dir = _resolve_out_dir()
        page, timeline = fetch_page_versions(args.page_id)
        img_mapping = None
        if args.images:
            refs = extract_referenced_images(page["body"]["storage"]["value"])
            if refs:
                atts = fetch_attachments(args.page_id, download=True, filter_names=refs)
                img_mapping = save_images_to_dir(atts, out_dir / "assets") or None
        out_path = out_dir / f"dig-page-{args.page_id}.md"
        out_path.write_text(render_page_corpus(page, timeline, img_mapping), encoding="utf-8")
        print(f"语料已写入 {out_path}（{len(timeline)} 版时间线 + 当前正文）")
        return

    cql = build_cql(args.keyword, args.space, args.parent_id, in_title=args.title)
    print(f"CQL: {cql}", file=sys.stderr)
    hits = search_pages(cql, limit=args.limit, expand="body.storage,version,history,space")

    if not hits:
        if not args.keyword:
            sys.exit(f"命中 0 篇。确认 --parent-id={args.parent_id} 下有子页、--space {args.space} 是否正确。")
        hint = "" if args.title else "泛词试试 --title 走标题匹配（噪声少）；或"
        sys.exit(f"命中 0 篇。{hint}放宽关键词，或确认 --space {args.space} / --parent-id 是否正确。")
    if len(hits) >= args.limit:
        extra = "" if args.title else " 或加 --title 走标题匹配收窄噪声"
        print(
            f"警告：命中 ≥ {args.limit} 篇，当前只取最新 {args.limit} 篇（更早的被切）。"
            f"加大 --limit 可拉更多{extra}。",
            file=sys.stderr,
        )

    # search 的 expand 直接带回正文 + 创建/更新时间/最后修改人，省掉逐页 get_page 的 N+1 请求
    items = [
        {
            "page": h,
            "created": h.get("history", {}).get("createdDate") or "9999",
            "updated": h.get("version", {}).get("when") or "9999",
            "author": h.get("version", {}).get("by", {}).get("displayName", "—"),
        }
        for h in hits
    ]
    items = sort_pages(items)

    slug = (_safe_filename(args.keyword)[:40] if args.keyword else f"parent-{args.parent_id}") or "dig"
    out_dir = _resolve_out_dir()
    if args.images:
        img_dir = out_dir / "assets"
        for item in items:
            # 只下 storage 实际引用的图（attachment 仓库含历史版本 + 未引用图，全集是垃圾流量）
            refs = extract_referenced_images(item["page"]["body"]["storage"]["value"])
            if not refs:
                item["img_mapping"] = {}
                continue
            atts = fetch_attachments(item["page"]["id"], download=True, filter_names=refs)
            item["img_mapping"] = save_images_to_dir(atts, img_dir) if atts else {}

    out_path = out_dir / f"dig-{slug}.md"
    out_path.write_text(
        render_corpus(args.keyword, args.space, args.parent_id, items, args.images),
        encoding="utf-8",
    )
    print(f"语料已写入 {out_path}（{len(items)} 篇）")
    print("下一步：喂 general-purpose agent 重建「现状真相 + 演进时间线」。")
    print("反哺 baseline 前先读 .claude/runbooks/confluence-archaeology.md（先 gap 全量比对，别只做深度补强）。")


if __name__ == "__main__":
    main()
