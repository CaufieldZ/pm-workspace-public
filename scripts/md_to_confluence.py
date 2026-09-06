#!/usr/bin/env python3
"""Push a Markdown file to Confluence as a child page, wrapped in the Markdown macro.

Reads Confluence creds from .mcp.json or .mcp-disabled.json (toggle-mcp.sh
parks the env block in the latter when the server is disabled — REST calls
still work since no live MCP server is needed).

Usage:
    python3 scripts/md_to_confluence.py <md_path> --parent-id <id> [--title <title>] [--space <key>] [--update-id <id>]
    可选：--minor（附件更新不通知 watcher）/ --label（覆盖自动标签，缺省按路径打 pm-{产品线}）

Examples:
    # Create new child page under parent
    python3 scripts/md_to_confluence.py projects/foo/deliverables/prd-foo-v1.md --parent-id 151429067

    # Overwrite an existing page by ID
    python3 scripts/md_to_confluence.py projects/foo/deliverables/prd-foo-v1.md --update-id 164481003

PRD md 路径自动适配：
    1. 检测 split 模式（{stem}-scenes/ 子目录存在）→ 调 prd_compose.py 拼接成完整 md 再推
    2. 扫 md 里 `![alt](./assets/...)` 本地图片 → 上传为 Confluence attachment
    3. 图片在 storage 里渲染为 <ac:image><ri:attachment ri:filename="X"/></ac:image> 真原生引用
       （Confluence markdown 宏内嵌 `![](filename)` 不会自动找 attachment，会图片裂）

split-children-by-chapter 模式：
    - 新建：--parent-id PARENT_SPACE_ID（在某 space 下新建父页 + N 子页）
    - 更新：--update-id PARENT_PAGE_ID（已存在的父页，自动取 children 按章节标题匹配 update）

首推前查同名（LEARNED 2026-05-12）：
    --parent-id 模式首推时，Confluence create 同名冲突会返回 HTTP 400。
    PM 先用 `--title` 显式改名或先用 search_pages 查空间下同名页（lib.confluence.search_pages）.

推送前 md 内容自检（渲染会炸的）：
    - 嵌套任务列表：Confluence ac:task-body 不允许嵌 ul，改「标签 → 子项」平铺 checkbox；
      推前 grep 野生 `</content>` / `</ac:` 标签残留，可跑 render_md_full 校验 task-body 开合平衡。
    - HTML table 的 th 含 `&` 必须写 `&amp;`，否则渲染后 Confluence XHTML 解析 400
      （骨架模板已写，手写场景块 table 时易漏）。
"""

from __future__ import annotations

import pathlib as _pl

# route-log: 调用埋点（scripts/lib/route_log.py）
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("md_to_confluence"))
import argparse
import mimetypes
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from lib.confluence import (
    add_label,
    base_url,
    create_page,
    list_child_pages,
    search_pages,
    set_content_property,
    update_page,
)
from lib.confluence_md import (
    _png_dims,
    extract_title,
    render_md_full,
    render_raw_html,
)

ROOT = Path(__file__).resolve().parent.parent

# ── 推送前剥离内部内容（不上 wiki 的 plumbing）─────────────────────────
# 支持顶级（# 标题）和二级（## 标题）关键词剥离。
# 格式：纯字符串 = 匹配任意级别；"##关键词" 前缀 = 只匹配二级标题。
DEFAULT_EXCLUDE_SECTIONS = [
    "反向合并指引",    # delta §9 内部 checklist
    "决策记录",        # 决策章（delta §6）论证留本地，不上 wiki
    "排期 / 上线节奏",  # delta §8
    "里程碑与排期",    # 普通 12 章 PRD §11
]


def _is_top_heading(line: str) -> bool:
    return bool(re.match(r"^#\s+\S", line))


def _heading_level(line: str) -> int:
    """返回标题级别（1=H1, 2=H2, …），非标题返回 0。"""
    m = re.match(r"^(#{1,6})\s+\S", line)
    return len(m.group(1)) if m else 0


def _preamble_all_meta(lines: list[str]) -> bool:
    """文档头块（H1 与首章之间）是否全是元信息行（- 项 / > 引用 / --- / 空行）。
    含真正散文段落则返回 False，避免误删其他文档的引言。

    PRD 侧承重约定（勿"优化"成连表格一起剥）：表格行以 `|` 开头 → 返回 False → 整块保留。
    delta 协作头（PRD 版本 / 拟制人 / 火效 / 团队 / 设计稿）是表格，故留在 wiki 上给同事看；
    内部机制说明（baseline 的「承重不变量」等）是 bullet，照旧剥掉。即：表 = 对外协作信息，
    bullet = 内部机制。"""
    for line in lines:
        s = line.strip()
        if not s or s == "---" or s.startswith(("-", ">")):
            continue
        return False
    return True


def strip_for_confluence(
    md: str, exclude_sections: list[str], strip_preamble: bool = True
) -> str:
    """推送前剥离不上 wiki 的内部内容：
    - exclude_sections：标题含任一关键词 → 整章删（到下一同级或更高级标题前）。
      关键词格式：纯字符串匹配任意级别标题；"##前缀" 格式（如 "##本轮需求索引"）
      只匹配 H2 标题，其余级别忽略。
    - strip_preamble：H1 标题与首章之间的元信息块 → 删（全为 bullet/引用/空行时才删）
    """
    lines = md.split("\n")
    tops = [i for i, line in enumerate(lines) if _is_top_heading(line)]
    if not tops:
        return md
    drop = [False] * len(lines)

    if strip_preamble and len(tops) >= 2 and _preamble_all_meta(lines[tops[0] + 1 : tops[1]]):
        for i in range(tops[0] + 1, tops[1]):
            drop[i] = True

    # 拆分关键词：带 "##" 前缀的只匹配 H2，其余匹配任意级别
    kw_any   = [kw for kw in exclude_sections if not kw.startswith("##")]
    kw_h2    = [kw[2:] for kw in exclude_sections if kw.startswith("##")]

    # 扫描所有标题行（不限顶级），按级别确定章节范围
    all_headings = [(i, _heading_level(lines[i])) for i in range(len(lines))
                    if _heading_level(lines[i]) > 0]

    for hi, (start, lvl) in enumerate(all_headings):
        if start == tops[0]:
            continue  # H1 文档标题本身保留
        line = lines[start]
        matched = (any(kw in line for kw in kw_any) or
                   (lvl == 2 and any(kw in line for kw in kw_h2)))
        if not matched:
            continue
        # 找到下一个同级或更高级的标题作为结束边界
        end = len(lines)
        for _, (nxt_i, nxt_lvl) in enumerate(all_headings[hi + 1:]):
            if nxt_lvl <= lvl:
                end = nxt_i
                break
        for i in range(start, end):
            drop[i] = True

    out = "\n".join(line for i, line in enumerate(lines) if not drop[i])
    return re.sub(r"\n{3,}", "\n\n", out)


# ── PRD md 自适配：split 模式 compose + 本地图片提取 ─────────────────────

# 相对路径图：可选 ./ 或 ../ 前缀 + 非 / 开头（排除绝对路径）。
# fetch_confluence.py pandoc 回流吐裸 assets/x.png（无 ./），生成器吐 ./assets/x.png，两者都收；
# 绝对路径 / 外链由 extract_local_images 的 startswith 兜底再过滤一次。
_IMG_RE = re.compile(r"!\[([^\]]*)\]\(((?:\.{1,2}/)?[^)/][^)]*)\)")
# HTML <img src="...">（生成器吐 HTML table 左列图 + fetch 回流的裸相对路径）
_HTML_IMG_RE = re.compile(r'(<img\s+[^>]*?src=")((?:\.{1,2}/)?[^"/][^"]*)(")')


def maybe_compose_split(md_path: Path) -> tuple[str, Path]:
    """如果同级有 {stem}-scenes/ 目录则调 prd_compose 拼接，否则原文返回。

    返回 (md_text, base_dir) —— base_dir 是图片相对路径的解析根。
    """
    scenes_dir = md_path.parent / f"{md_path.stem}-scenes"
    if not scenes_dir.is_dir():
        return md_path.read_text(encoding="utf-8"), md_path.parent

    # 找 prd_compose.py
    compose_py = (
        Path(__file__).resolve().parent.parent
        / ".claude/skills/prd/scripts/prd_compose.py"
    )
    if not compose_py.exists():
        sys.exit(f"split 模式但找不到 prd_compose.py：{compose_py}")
    print(f"  → split 模式，拼接 {scenes_dir.name}/ ...", file=sys.stderr)
    out = subprocess.run(
        ["python3", str(compose_py), str(md_path)],
        capture_output=True, text=True, check=True,
    )
    return out.stdout, md_path.parent


def extract_local_images(md: str, base_dir: Path) -> list[tuple[str, Path]]:
    """扫 md 里本地图片引用，返回 [(原始路径, 实际文件 Path), ...]，按出现顺序去重。

    跳过 http/https/data: 等外链。
    """
    seen: set[str] = set()
    found: list[tuple[str, Path]] = []
    # ![]() markdown 图（group 2）+ <img src> HTML 图（group 2）统一收集，按出现顺序去重
    rels = [m.group(2) for m in _IMG_RE.finditer(md)]
    rels += [m.group(2) for m in _HTML_IMG_RE.finditer(md)]
    for rel in rels:
        if rel.startswith(("http://", "https://", "data:", "/")):
            continue
        if rel in seen:
            continue
        seen.add(rel)
        # 解析相对路径（用 resolve() 让 Path 正确处理 ../ 上层级语义）
        full = (base_dir / rel).resolve()
        if full.exists():
            found.append((rel, full.resolve()))
        else:
            print(f"  ⚠ 图片不存在：{rel}（解析为 {full}）", file=sys.stderr)
    return found


def rewrite_image_paths(md: str, mapping: dict[str, str]) -> str:
    """把 md 里的本地图片路径改成 attachment filename（![]() 与 <img src> 两种形式）。

    mapping: {原始相对路径: 上传后的 filename}
    """
    def _sub_md(m: re.Match) -> str:
        alt, rel = m.group(1), m.group(2)
        if rel in mapping:
            return f"![{alt}]({mapping[rel]})"
        return m.group(0)

    def _sub_html(m: re.Match) -> str:
        pre, rel, post = m.group(1), m.group(2), m.group(3)
        if rel in mapping:
            return f"{pre}{mapping[rel]}{post}"
        return m.group(0)

    md = _IMG_RE.sub(_sub_md, md)
    return _HTML_IMG_RE.sub(_sub_html, md)


def upload_local_images(page_id: str, images: list[tuple[str, Path]],
                        minor_edit: bool = False) -> dict[str, str]:
    """上传所有本地图片为 page 的 attachment，返回 {原始路径: filename} 映射。

    Lazy import upload_attachment（依赖 requests，仅有图时才 import）。
    """
    if not images:
        return {}
    try:
        from lib.confluence import upload_attachment
    except ImportError as e:
        sys.exit(f"图片上传依赖 lib.confluence.upload_attachment：{e}")

    mapping: dict[str, str] = {}
    name_taken: set[str] = set()
    for rel, full in images:
        # filename 用原文件名（多个相对路径指向同名时加数字后缀避免冲突）
        base_name = full.name
        name = base_name
        n = 1
        while name in name_taken:
            stem, dot, ext = base_name.rpartition(".")
            name = f"{stem}-{n}.{ext}" if dot else f"{base_name}-{n}"
            n += 1
        name_taken.add(name)
        mime = mimetypes.guess_type(full.name)[0] or "image/png"
        data = full.read_bytes()
        upload_attachment(page_id, name, data, mime, minor_edit=minor_edit)
        print(f"  ↑ 附件: {name} ({len(data)//1024}KB)", file=sys.stderr)
        mapping[rel] = name
    return mapping


def _img_dims(local_images: list[tuple[str, Path]], mapping: dict[str, str]) -> dict[str, tuple[int, int]]:
    """{filename: (w, h)} PNG 实际尺寸，供 render_md_full 智能宽度路由。"""
    dims: dict[str, tuple[int, int]] = {}
    for rel, full in local_images:
        fname = mapping.get(rel)
        if fname:
            d = _png_dims(full)
            if d:
                dims[fname] = d
    return dims


# ── 推送后处理：标签 + 来源 property（wiki 侧反查本地文件）─────────────────

PROP_KEY = "pm-workspace"


def _infer_labels(md_path: Path, explicit: list[str]) -> list[str]:
    """显式 --label 优先；否则从路径 projects/{产品线}/ 推断 pm-{产品线}。"""
    if explicit:
        return explicit
    parts = md_path.resolve().parts
    if "projects" in parts:
        i = parts.index("projects")
        if i + 1 < len(parts):
            return [f"pm-{parts[i + 1]}"]
    return []


def _post_push(page_ids: list[str], labels: list[str], md_path: Path) -> None:
    """推送成功后：打标签（CQL label= 可检索）+ 写来源 property。失败只 warn 不阻断推送。"""
    src = md_path.resolve()
    try:
        source = str(src.relative_to(ROOT))
    except ValueError:
        source = str(src)
    meta = {"source": source, "pushed_at": datetime.now().isoformat(timespec="seconds")}
    for pid in page_ids:
        for lb in labels:
            try:
                add_label(pid, lb)
            except Exception as e:
                print(f"  ⚠ 打标签 {lb} 失败（不影响推送）：{e}", file=sys.stderr)
        try:
            set_content_property(pid, PROP_KEY, meta)
        except Exception as e:
            print(f"  ⚠ 写来源 property 失败（不影响推送）：{e}", file=sys.stderr)
    if labels:
        print(f"  → 标签：{', '.join(labels)}", file=sys.stderr)


# ── 父页 + N 章节子页推送（split-children-by-chapter）─────────────────────

_PARENT_CHAPTER_HEAD_RE = re.compile(r"^#\s+\*{0,2}([4-7])\.\s+(.+?)\*{0,2}\s*$")
_PARENT_SCENE_LINK_RE = re.compile(r"^- \[([^\]]+)\]\(([^)]+\.md)\)\s*$")


def parse_chapter_blocks_for_split(md: str) -> list[dict]:
    """解析主 md 的 §4-7 章节。每章返回：
    chapter / title (heading 白话部分) / heading_idx /
    scene_links: [(anchor_text, link_path), ...]
    """
    lines = md.splitlines()
    chapters: list[dict] = []
    current: dict | None = None
    for i, line in enumerate(lines):
        m_ch = _PARENT_CHAPTER_HEAD_RE.match(line)
        if m_ch:
            if current is not None:
                chapters.append(current)
            current = {
                "chapter": int(m_ch.group(1)),
                "title": m_ch.group(2).strip(),
                "heading_idx": i,
                "scene_links": [],
            }
            continue
        # 下一个 # heading（非 §4-7）关闭当前章
        if line.startswith("# ") and current is not None and not m_ch:
            chapters.append(current)
            current = None
            continue
        if current is not None:
            m_link = _PARENT_SCENE_LINK_RE.match(line)
            if m_link:
                current["scene_links"].append(
                    (m_link.group(1).strip(), m_link.group(2).strip())
                )
    if current is not None:
        chapters.append(current)
    return [c for c in chapters if c["scene_links"]]


def gen_child_md(chapter: dict, scenes_dir: Path) -> str:
    """生成子页 md：# 章节标题 + 章节简介（来自主 md 已剥）+ 场景文件内容串接。

    简介由调用方传入（这里只串接 scene 文件）；child_md 起头是 chapter title。
    """
    parts = [f"# {chapter['title']}\n"]
    for _, link_path in chapter["scene_links"]:
        # link_path 是相对主 md 的路径，如 'prd-xxx-scenes/audience-A-1-...md'
        # scenes_dir 已是 scenes/ 目录绝对路径，取 basename
        scene_file = scenes_dir / Path(link_path).name
        if not scene_file.exists():
            print(f"  ⚠ 场景文件不存在：{scene_file}", file=sys.stderr)
            continue
        parts.append(scene_file.read_text(encoding="utf-8").rstrip() + "\n")
    return "\n".join(parts)


def rewrite_scene_links_to_confluence(
    md: str, chapter_to_pageid: dict[int, str]
) -> str:
    """主 md §4-7 章下的 - [N.x · 名](xxx.md) 引用 link 改写为对应章节子页 URL。"""
    lines = md.splitlines()
    out: list[str] = []
    current_chapter = 0
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
        if current_chapter in chapter_to_pageid:
            m_link = _PARENT_SCENE_LINK_RE.match(line)
            if m_link:
                anchor = m_link.group(1).strip()
                page_id = chapter_to_pageid[current_chapter]
                url = f"{base_url()}/pages/viewpage.action?pageId={page_id}"
                out.append(f"- [{anchor}]({url})")
                continue
        out.append(line)
    return "\n".join(out) + "\n"


def _precheck_duplicate_title(space: str, title: str) -> None:
    """首推前查 space 下是否已有同 title 页；有则 friendly exit 提示 PM 三选一。

    避免 create_page POST 遇 HTTP 400「A page already exists with this title」崩溃。
    """
    try:
        results = search_pages(
            f'space = "{space}" AND title = "{title}" AND type = "page"',
            limit=5,
        )
    except OSError:
        # 预检失败不阻断推送（网络问题 / 权限问题），由 create_page 的 400 兜底
        return
    if not results:
        return
    base = base_url()
    lines = [
        f"\n⚠️  space={space} 下已存在同 title 页：「{title}」",
        "直接 create 会 HTTP 400。三选一：",
        "",
        "  1. 新建新版页：加 --title 改名，如 --title \"{title}（2026-05-12）\"",
        "  2. 覆盖历史页：改用 --update-id <历史 pageId> 覆盖推",
        "  3. 先归档历史页：去 wiki 改名 / 加「- 历史版本」后缀，再跑原命令",
        "",
        "  已命中的历史页：",
    ]
    for r in results[:5]:
        pid = r.get("id", "?")
        rtitle = r.get("title", "?")
        lines.append(f"    [{pid}] {rtitle}")
        lines.append(f"      {base}/pages/viewpage.action?pageId={pid}")
    sys.exit("\n".join(lines))


def _get_chapter_children(parent_id: str, chapters: list[dict]) -> dict[int, str]:
    """从已存在的父页拿 children，按 child.title == chapter.title 匹配。

    返回 {chapter_num: child_page_id}。匹配不到的 chapter 报错。
    """
    children = list_child_pages(parent_id)
    title_to_id = {c["title"]: c["id"] for c in children}
    chapter_to_pageid: dict[int, str] = {}
    missing: list[str] = []
    for ch in chapters:
        page_id = title_to_id.get(ch["title"])
        if page_id is None:
            missing.append(f"§{ch['chapter']} {ch['title']}")
            continue
        chapter_to_pageid[ch["chapter"]] = page_id
    if missing:
        sys.exit(
            f"父页 {parent_id} 下找不到匹配 children：\n  " + "\n  ".join(missing)
            + f"\n  现有 children: {list(title_to_id.keys())}"
        )
    return chapter_to_pageid


def push_split_children_by_chapter(
    md_path: Path,
    parent_id: str | None,
    update_id: str | None,
    space: str,
    title_override: str | None,
    exclude_sections: list[str] | None = None,
    strip_preamble: bool = True,
    minor_edit: bool = False,
) -> list[str]:
    """父页 + 各章节子页推送。

    新建模式：传 parent_id（在 space 下新建父页 + N 子页）
    更新模式：传 update_id（已存在父页，按 children title 匹配章节 update）
    """
    scenes_dir = md_path.parent / f"{md_path.stem}-scenes"
    if not scenes_dir.is_dir():
        sys.exit(
            f"--split-children-by-chapter 需要 split 后的 PRD（{scenes_dir} 不存在）；"
            f"先跑 split_prd.py"
        )

    main_md = md_path.read_text(encoding="utf-8")
    main_md = strip_for_confluence(main_md, exclude_sections or [], strip_preamble)
    chapters = parse_chapter_blocks_for_split(main_md)
    if not chapters:
        sys.exit("未在主 md 找到 §4-7 章节及其场景引用列表")
    print(
        f"  → 发现 {len(chapters)} 章可拆为子页：{[c['chapter'] for c in chapters]}",
        file=sys.stderr,
    )

    parent_title = title_override or extract_title(main_md)
    is_update = update_id is not None

    # 1. 父页：新建走 create + 后续 update / 更新模式直接拿现有 page id
    if is_update:
        parent_page_id = update_id
        chapter_to_pageid = _get_chapter_children(parent_page_id, chapters)
        print(f"  → 更新模式：父页 {parent_page_id}，子页映射：", file=sys.stderr)
        for ch in chapters:
            print(
                f"    §{ch['chapter']} → {chapter_to_pageid[ch['chapter']]}",
                file=sys.stderr,
            )
    else:
        _precheck_duplicate_title(space, parent_title)
        parent_page = create_page(
            space, parent_title, render_md_full(main_md), parent_id
        )
        parent_page_id = parent_page["id"]
        print(f"  ↑ 父页（新建）：{parent_title} → pageId={parent_page_id}", file=sys.stderr)
        chapter_to_pageid = {}

    # 2. 子页：按章节
    for ch in chapters:
        child_title = ch["title"]
        child_md = gen_child_md(ch, scenes_dir)
        child_imgs = extract_local_images(child_md, scenes_dir)

        if is_update:
            child_page_id = chapter_to_pageid[ch["chapter"]]
        else:
            child_page = create_page(
                space, child_title, render_md_full(child_md), parent_page_id
            )
            child_page_id = child_page["id"]
            chapter_to_pageid[ch["chapter"]] = child_page_id

        # 上传图片，得到 attachment names → 走 render_md_full 终轮渲染
        mapping = upload_local_images(child_page_id, child_imgs, minor_edit=minor_edit) if child_imgs else {}
        attachment_names = set(mapping.values())
        if attachment_names:
            child_md_final = rewrite_image_paths(child_md, mapping)
            body = render_md_full(child_md_final, attachment_names)
        else:
            body = render_md_full(child_md)

        update_page(child_page_id, child_title, body)
        action = "↻ 更新" if is_update else "↑ 新建"
        print(
            f"  {action} 子页 §{ch['chapter']}：{child_title} → pageId={child_page_id} "
            f"({len(ch['scene_links'])} 场景 / {len(attachment_names)} 图)",
            file=sys.stderr,
        )

    # 3. 父页 update：图片 + 场景 link 改写为子页 URL
    parent_imgs = extract_local_images(main_md, md_path.parent)
    parent_mapping = upload_local_images(parent_page_id, parent_imgs, minor_edit=minor_edit) if parent_imgs else {}
    parent_attachment_names = set(parent_mapping.values())

    rewritten = main_md
    if parent_mapping:
        rewritten = rewrite_image_paths(rewritten, parent_mapping)
    rewritten = rewrite_scene_links_to_confluence(rewritten, chapter_to_pageid)

    body = render_md_full(rewritten, parent_attachment_names)
    update_page(parent_page_id, parent_title, body)
    print("  → 父页 update 完成（场景 link 改写为子页 URL）", file=sys.stderr)

    print(f"\n✓ 推送完成：1 父页 + {len(chapters)} 子页（{'update' if is_update else '新建'} 模式）")
    print(f"  父页：{base_url()}/pages/viewpage.action?pageId={parent_page_id}")
    return [parent_page_id] + list(chapter_to_pageid.values())


# ── 埋点表 rowspan 合并（--merge-tracking）────────────────────────────────
_TRACKING_EVENT_COLS = {0, 1, 2, 8}  # 事件级列：所属页面 / 事件中文名 / 事件英文名 / 应埋点平台


def _table_cells(line: str) -> list[str]:
    """md 表格行 → cell 列表（去首尾 | + 去反引号）。"""
    return [c.strip().strip("`") for c in line.strip().strip("|").split("|")]


def _is_tracking_header(cells: list[str]) -> bool:
    """10 列埋点表头签名：所属页面 + 事件英文名。"""
    return len(cells) >= 3 and cells[0] == "所属页面" and cells[2] == "事件英文名"


def _build_tracking_html_table(rows: list[list[str]]) -> str:
    """埋点表行 → <table class="wrapped"> storage；事件级列按连续同事件段 rowspan。

    rows[0] = 表头；rows[1:] = 数据行。事件英文名列（col 2）包 <code> 提升可读性。
    """
    head_cells = rows[0]
    thead = "<tr>" + "".join(f"<th>{c}</th>" for c in head_cells) + "</tr>"
    body: list[str] = []
    i = 1
    n = len(rows)
    while i < n:
        j = i
        while j < n and (rows[j][2] if len(rows[j]) > 2 else "") == (rows[i][2] if len(rows[i]) > 2 else ""):  # 同事件连续段
            j += 1
        span = j - i
        for k in range(i, j):
            tds = []
            for ci in range(len(head_cells)):
                cell = rows[k][ci] if ci < len(rows[k]) else ""
                if ci in _TRACKING_EVENT_COLS and k != i:
                    continue  # 续行省略事件级列
                attr = f' rowspan="{span}"' if (ci in _TRACKING_EVENT_COLS and k == i and span > 1) else ""
                inner = f"<code>{cell}</code>" if ci == 2 else cell
                tds.append(f"<td{attr}>{inner}</td>")
            body.append(f"<tr>{''.join(tds)}</tr>")
        i = j
    return f'<table class="wrapped"><thead>{thead}</thead><tbody>{"".join(body)}</tbody></table>'


def merge_tracking_tables(md: str) -> tuple[str, int]:
    """md 里所有 10 列埋点表 → rowspan HTML table（供 pandoc 直通渲染）。

    保留原表顺序与原行序，事件级列按连续相同事件段纵向合并。返回 (新 md, 替换表数)。
    """
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    replaced = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("|") and _is_tracking_header(_table_cells(s)):
            start = i
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                i += 1
            block = lines[start:i]
            rows = [
                _table_cells(ln)
                for ln in block
                if not all(set(c) <= set(": -") for c in _table_cells(ln))
            ]
            if len(rows) >= 2 and len(rows[0]) >= 10:
                out.append(_build_tracking_html_table([r[:10] for r in rows]))
                replaced += 1
            else:
                out.extend(block)
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out), replaced


def main():
    p = argparse.ArgumentParser()
    p.add_argument("md_path")
    p.add_argument("--parent-id", help="parent page id (for create)")
    p.add_argument("--update-id", help="existing page id to overwrite (skips create)")
    p.add_argument("--space", default="jituankejizhongxin")
    p.add_argument("--title", help="override page title (default: first H1 of md)")
    p.add_argument(
        "--split-children-by-chapter",
        action="store_true",
        help=(
            "分章节推为父页 + N 子页（按 §4-7 各章拆）。需要先跑 split_prd.py。"
            "父页含 §1-3 + §8-12 全文 + §4-7 章节链接到子页；子页含该章全部场景内容"
        ),
    )
    p.add_argument(
        "--no-split",
        action="store_true",
        help=(
            "强制单页推送（即便检测到 -scenes/ split 目录）。用于场景少 / 不想拆子页 / 历史页面已经是单页结构"
        ),
    )
    p.add_argument(
        "--raw-html",
        action="store_true",
        help=(
            "HTML 为主的文档（裸 <table> 富文本，多为 Confluence pandoc 抓回的）走 pandoc md→html "
            "原样推 storage，不进 markdown 宏（宏会把表格转义成字面源码）。不支持本地图片附件。"
        ),
    )
    p.add_argument(
        "--merge-tracking",
        action="store_true",
        default=True,
        help=(
            "10 列埋点表 → rowspan HTML（事件级列同事件纵向合并）走 pandoc 直通，默认开启。"
            "md 表格不支持 rowspan，开启后埋点表在 wiki 上事件名 / 所属页面等列合并显示。"
            "用 --no-merge-tracking 关闭。"
        ),
    )
    p.add_argument("--no-merge-tracking", dest="merge_tracking", action="store_false")
    p.add_argument(
        "--exclude-section",
        action="append",
        metavar="标题关键词",
        help="推送时排除标题含该关键词的顶级章节（可多次）。默认已排除「反向合并指引 / 决策记录 / 排期」章",
    )
    p.add_argument(
        "--keep-preamble",
        action="store_true",
        help="保留文档头元信息块（默认剥离 H1 与首章之间的 baseline / 状态 / 来源等内部元信息）",
    )
    p.add_argument(
        "--minor",
        action="store_true",
        help="附件更新标 minor edit（不通知 watcher）。注：页面 update 本身实例不支持 minorEdit（实测忽略），无法抑制",
    )
    p.add_argument(
        "--label",
        action="append",
        metavar="标签名",
        help="推送后打标签（可多次；CQL label=\"...\" 可检索）。缺省从路径自动推断 pm-{产品线}",
    )
    args = p.parse_args()

    md_path = Path(args.md_path)
    if not md_path.exists():
        sys.exit(f"md 文件不存在：{md_path}")

    exclude_sections = DEFAULT_EXCLUDE_SECTIONS + (args.exclude_section or [])
    strip_preamble = not args.keep_preamble

    # 父页 + N 子页模式（split-children-by-chapter）
    if args.split_children_by_chapter:
        if not (args.parent_id or args.update_id):
            sys.exit("--split-children-by-chapter 需要 --parent-id（新建）或 --update-id（更新）")
        if args.parent_id and args.update_id:
            sys.exit("--parent-id（新建）与 --update-id（更新）互斥，只能传一个")
        page_ids = push_split_children_by_chapter(
            md_path, args.parent_id, args.update_id, args.space, args.title,
            exclude_sections, strip_preamble, minor_edit=args.minor,
        )
        _post_push(page_ids, _infer_labels(md_path, args.label), md_path)
        return

    # split 检测门：scenes/ 存在但既没选 split-children 也没选 no-split → 强制 PM 选
    scenes_dir = md_path.parent / f"{md_path.stem}-scenes"
    if scenes_dir.is_dir() and not args.no_split:
        sys.exit(
            f"\n⚠️  检测到 split 目录：{scenes_dir.name}/\n"
            f"必须显式选择推送方式（防止误把子页结构推成单页）：\n"
            f"  方式 A：1 父页 + N 子页（推荐，按章节拆）\n"
            f"    python3 scripts/md_to_confluence.py {md_path} \\\n"
            f"      --split-children-by-chapter --update-id <PARENT_PAGE_ID>\n"
            f"  方式 B：单页（compose 全 md 推一页）\n"
            f"    python3 scripts/md_to_confluence.py {md_path} \\\n"
            f"      --no-split --update-id <PAGE_ID>\n"
        )

    # 单页模式（含 split 自动 compose）
    md, base_dir = maybe_compose_split(md_path)
    md = strip_for_confluence(md, exclude_sections, strip_preamble)
    title = args.title or extract_title(md)

    # merge-tracking：10 列埋点表 → rowspan HTML（rowspan 不能进 markdown 宏，仅在实际
    # 合并到 ≥1 张表时才隐含 raw-html 走 pandoc 直通；无埋点表的 md 保持原渲染路径，
    # ::: 面板等 markdown-it 扩展才不会被 pandoc 输出成字面量）
    if args.merge_tracking:
        md, n_merged = merge_tracking_tables(md)
        if n_merged:
            print(f"  → 合并 {n_merged} 张埋点表为 rowspan HTML（走 pandoc 直通）", file=sys.stderr)
            args.raw_html = True

    # raw-html 模式：HTML 为主文档原样推 storage（裸 <table> 不进 markdown 宏）
    if args.raw_html:
        local_images = extract_local_images(md, base_dir)
        if local_images:
            print(f"  → 检测到 {len(local_images)} 张本地图片，将上传为附件", file=sys.stderr)
        if args.update_id:
            # 页已存在：附件先上 → 正文一轮推终态（不产生无图中间版本）
            mapping = upload_local_images(args.update_id, local_images, minor_edit=args.minor)
            if mapping:
                body = render_md_full(rewrite_image_paths(md, mapping),
                                      set(mapping.values()),
                                      attachment_dims=_img_dims(local_images, mapping))
            else:
                body = render_raw_html(md)
            res = update_page(args.update_id, title, body)
        else:
            if not args.parent_id:
                sys.exit("need --parent-id for create, or --update-id to overwrite")
            _precheck_duplicate_title(args.space, title)
            res = create_page(args.space, title, render_raw_html(md), args.parent_id)
            # create 场景必须先建页才能传附件 → 补图轮（终态）
            if local_images:
                mapping = upload_local_images(res["id"], local_images, minor_edit=args.minor)
                if mapping:
                    body = render_md_full(rewrite_image_paths(md, mapping),
                                          set(mapping.values()),
                                          attachment_dims=_img_dims(local_images, mapping))
                    update_page(res["id"], title, body)
                    print(f"  → 图片转 ac:image storage 引用并 update 完成（{len(mapping)} 张）", file=sys.stderr)
        page_id = res["id"]
        _post_push([page_id], _infer_labels(md_path, args.label), md_path)
        print(f"✓ {title}")
        print(f"  {base_url()}/pages/viewpage.action?pageId={page_id}")
        return

    local_images = extract_local_images(md, base_dir)
    if local_images:
        print(f"  → 检测到 {len(local_images)} 张本地图片，将上传为附件", file=sys.stderr)

    if args.update_id:
        # 页已存在：附件先上 → 正文一轮推终态（不产生无图中间版本）
        mapping = upload_local_images(args.update_id, local_images, minor_edit=args.minor)
        if mapping:
            md = rewrite_image_paths(md, mapping)
            body = render_md_full(md, set(mapping.values()),
                                  attachment_dims=_img_dims(local_images, mapping))
        else:
            body = render_md_full(md)
        res = update_page(args.update_id, title, body)
    else:
        if not args.parent_id:
            sys.exit("need --parent-id for create, or --update-id to overwrite")
        # 首推同名预检：space 下已有同 title 页会让 POST 返 HTTP 400 崩，提前提示
        _precheck_duplicate_title(args.space, title)
        res = create_page(args.space, title, render_md_full(md), args.parent_id)
        # create 场景必须先建页才能传附件 → 补图轮（终态）
        if local_images:
            mapping = upload_local_images(res["id"], local_images, minor_edit=args.minor)
            if mapping:
                md_rewritten = rewrite_image_paths(md, mapping)
                body = render_md_full(md_rewritten, set(mapping.values()),
                                      attachment_dims=_img_dims(local_images, mapping))
                update_page(res["id"], title, body)
                print(
                    f"  → 图片转 ac:image storage 引用并 update 完成（{len(mapping)} 张）",
                    file=sys.stderr,
                )
    page_id = res["id"]

    _post_push([page_id], _infer_labels(md_path, args.label), md_path)
    print(f"✓ {title}")
    print(f"  {base_url()}/pages/viewpage.action?pageId={page_id}")


if __name__ == "__main__":
    main()
