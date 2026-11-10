#!/usr/bin/env python3
"""推送 Markdown 到 Confluence 页面（markdown-it 渲染原生 storage，缺 markdown-it-py 时降级 markdown 宏）。

前置凭证（任一即可，--help 本身不需要）：
  - env var：CONF_BASE_URL + CONF_TOKEN
  - 仓库根 .mcp.json / .mcp-disabled.json 的 mcpServers.confluence.env（REST 直调，无需 MCP server 存活）

Usage:
    python3 scripts/md_to_confluence.py <md_path> --parent-id <id> [--title <title>] [--space <key>] [--update-id <id>]
    可选：--minor（附件更新不通知 watcher）/ --label（覆盖自动标签，缺省按路径打 pm-{产品线}）

Examples:
    # 在父页下新建子页
    python3 scripts/md_to_confluence.py projects/foo/deliverables/prd-foo-v1.md --parent-id 151429067

    # 覆盖已有页（跳过新建，按 pageId update）
    python3 scripts/md_to_confluence.py projects/foo/deliverables/prd-foo-v1.md --update-id 164481003

产物：Confluence 页面本体（本地 md 不动，只裁推送版：剥离内部章 + 文档头元信息）。
退出码：1 = md 不存在 / 参数互斥 / 同名冲突等（消息见 stderr）。

PRD md 路径自动适配：
    1. 扫 md 里 `![alt](./assets/...)` 本地图片 → 上传为 Confluence attachment
    2. 图片在 storage 里渲染为 <ac:image><ri:attachment ri:filename="X"/></ac:image> 真原生引用
       （Confluence markdown 宏内嵌 `![](filename)` 不会自动找 attachment，会图片裂）

首推前查同名（LEARNED 2026-05-12）：
    --parent-id 模式首推时，Confluence create 同名冲突会返回 HTTP 400。
    PM 先用 `--title` 显式改名或先用 search_pages 查空间下同名页（lib.confluence_rest.search_pages）.

推送前 md 内容自检：

- 字段块软换行：promo / launch 产物里 ≥2 行连续的「标签：值」且中间无空行 → 阻断
  （CommonMark 会把它们并成一段，wiki 上只剩空格）。修法：补空行或改成列表项；
  确认要这样推加 `--allow-soft-breaks`。侦测器：`check_soft_line_breaks`。

以下渲染会炸的：
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
import sys
from datetime import datetime
from pathlib import Path

from lib.confluence_md import (
    _is_sep_line,
    _is_table_row,
    _png_dims,
    _table_cells,
    extract_title,
    render_md_full,
    render_raw_html,
)
from lib.confluence_rest import (
    add_label,
    base_url,
    create_page,
    search_pages,
    set_content_property,
    update_page,
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
    delta 协作头（PRD 版本 / 拟制人 / 内部项目系统 / 团队 / 设计稿）是表格，故留在 wiki 上给同事看；
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


# ── 推送前体检：表格块内空行导致断表 ───────────────────────────────────
# md 表格中途留空行 → 空行后的 `|` 行不再是表格，被渲染成字面段落推上 wiki，
# 只有推完肉眼验收才发现。此处在渲染前扫出来提醒。
# 表格行 / 分隔行的判定口径见 `lib.confluence_md`（宽松解析器那组）。


def broken_tables(md: str) -> list[int]:
    """扫断表，回孤儿行行号（1-based，升序）。

    以「表头 + 分隔行」为表区起点，表区可跨过空行继续；空行后落回表格行即断表。
    空行后是另一张表的表头（其后紧跟分隔行）属合法双表，表区到此结束。
    围栏代码块内的 `|` 行不算表格。
    """
    lines = md.split("\n")
    broken: list[int] = []

    fence = [False] * len(lines)
    in_fence = False
    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            fence[idx] = True
            in_fence = not in_fence
        else:
            fence[idx] = in_fence

    i = 0
    while i < len(lines):
        # 表区起点 = 表格行 + 紧邻分隔行
        if (fence[i] or not _is_table_row(lines[i])
                or not (i + 1 < len(lines) and not fence[i + 1] and _is_sep_line(lines[i + 1]))):
            i += 1
            continue
        i += 2
        while i < len(lines) and not fence[i]:
            if _is_table_row(lines[i]):
                i += 1
                continue
            if lines[i].strip():
                break  # 表体遇正文 → 表区结束
            k = i
            while k < len(lines) and not lines[k].strip() and not fence[k]:
                k += 1
            if k >= len(lines) or fence[k] or not _is_table_row(lines[k]):
                break  # 空行后不是表格 → 表区结束
            if k + 1 < len(lines) and not fence[k + 1] and _is_sep_line(lines[k + 1]):
                break  # 空行后是另一张表的表头 → 合法双表
            broken.append(k + 1)
            i = k
    return broken


def warn_broken_tables(md: str, md_path: Path) -> None:
    """断表提醒（不阻断推送，仅指向行号）。"""
    rows = broken_tables(md)
    if not rows:
        return
    print(
        f"\n⚠️  {md_path.name} 检出 {len(rows)} 处断表 —— 表格块内有空行，"
        f"空行后的行会渲染成字面段落：",
        file=sys.stderr,
    )
    for ln in rows[:10]:
        print(f"      L{ln}", file=sys.stderr)
    if len(rows) > 10:
        print(f"      …另 {len(rows) - 10} 处", file=sys.stderr)
    print("    建议删掉表格内的空行后重推；坚持推送的话，这几处请推完肉眼验收。\n", file=sys.stderr)


# ── 软换行陷阱：连续行在 Markdown 里会并成一段 ────────────────────
# CommonMark 把「中间没有空行的连续行」当同一段的软换行，推上去只剩一个空格。
# 骨架里的「主标题：/副标题：」这类逐行字段最常踩：本地看着一行一条，wiki 上并成一句。
# 判据：整段每行都短（<46 字符）且段内含至少一条「标签：」行 → 字段块，阻断；
#       其余短行段只提示，正文硬折行（长行）不提示。
_OL_RE = re.compile(r"^\s*\d+[.)]\s")
_FIELD_RE = re.compile(r"^\s*[^：:|]{1,12}[：:]")
_STRUCT_PREFIX = ("-", "*", "|", "#", ">", "`", "+", "<", "!", "{", "[", "(", '"', "'")


def soft_break_runs(md: str):
    """返回 [(起始行号, [行...]), ...]：会被并成一段的短行块。"""
    lines = md.split("\n")
    runs, cur = [], []
    fence = front = False

    def flush():
        if len(cur) >= 2:
            runs.append((start, list(cur)))

    start = 1
    for i, line in enumerate(lines, 1):
        st = line.strip()
        if st.startswith("```"):
            fence = not fence
            flush(); cur = []
            continue
        if fence:
            continue
        if i == 1 and st == "---":
            front = True
            continue
        if front:
            if st == "---":
                front = False
            continue
        is_prose = bool(st) and not st.startswith(_STRUCT_PREFIX) \
            and not st.startswith("---") and not _OL_RE.match(st)
        if is_prose and len(st) < 46:
            if not cur:
                start = i
            cur.append(st)
        else:
            flush(); cur = []
    flush()
    return runs


def check_soft_line_breaks(md: str, md_path: Path, allow: bool = False) -> int:
    """推前扫软换行陷阱。返回阻断数（字段块数）；allow=True 时只提示。"""
    runs = soft_break_runs(md)
    # 只有 promo-kit 产物（launch-* / promo-*）才按字段块阻断：那套骨架要求逐行写字段。
    # 其余文档里的「标签：」行多为提纲或语料，阻断会误伤正常推送。
    is_promo = bool(re.match(r"(launch|promo)-.*\.md$", md_path.name))
    field_runs = [(ln, lines) for ln, lines in runs
                  if is_promo and any(_FIELD_RE.match(x) for x in lines)]
    if not runs:
        return 0
    # 2 行短段多半是正常的两行句，只对 ≥3 行提示，避免正文折行刷屏
    runs = [r for r in runs if len(r[1]) >= 3]
    if field_runs:
        print(f"\n🚫 {md_path.name} 检出 {len(field_runs)} 处字段块会被并成一段：",
              file=sys.stderr)
        for ln, lines in field_runs[:6]:
            print(f"      L{ln}-{ln + len(lines) - 1}  {lines[0][:28]}", file=sys.stderr)
        if len(field_runs) > 6:
            print(f"      …另 {len(field_runs) - 6} 处", file=sys.stderr)
        print("    Markdown 连续行之间没有空行会并成同一段，wiki 上只剩空格。", file=sys.stderr)
        print("    修法：字段之间补空行，或改成列表项（每行前加「- 」）。", file=sys.stderr)
        if not allow:
            print("    确认要这样推：加 --allow-soft-breaks\n", file=sys.stderr)
            return len(field_runs)
        print("    （--allow-soft-breaks 已指定，继续推送）\n", file=sys.stderr)
    else:
        print(f"\n⚠️  {md_path.name} 有 {len(runs)} 处连续短行可能并成一段，"
              f"请推完肉眼验收。\n", file=sys.stderr)
    return 0


# ── PRD md 本地图片提取 ─────────────────────

# 相对路径图：可选 ./ 或 ../ 前缀 + 非 / 开头（排除绝对路径）。
# confluence.py get --mode pandoc 回流吐裸 assets/x.png（无 ./），生成器吐 ./assets/x.png，两者都收；
# 绝对路径 / 外链由 extract_local_images 的 startswith 兜底再过滤一次。
_IMG_RE = re.compile(r"!\[([^\]]*)\]\(((?:\.{1,2}/)?[^)/][^)]*)\)")
# HTML <img src="...">（生成器吐 HTML table 左列图 + fetch 回流的裸相对路径）
_HTML_IMG_RE = re.compile(r'(<img\s+[^>]*?src=")((?:\.{1,2}/)?[^"/][^"]*)(")')


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
        from lib.confluence_rest import upload_attachment
    except ImportError as e:
        sys.exit(f"图片上传依赖 lib.confluence_rest.upload_attachment：{e}")

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


# ── 埋点表 rowspan 合并（--merge-tracking）────────────────────────────────
_TRACKING_EVENT_COLS = {0, 1, 2, 8}  # 事件级列：所属页面 / 事件中文名 / 事件英文名 / 应埋点平台


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
        if _is_table_row(lines[i]) and _is_tracking_header(_table_cells(lines[i])):
            start = i
            i += 1
            while i < len(lines) and _is_table_row(lines[i]):
                i += 1
            block = lines[start:i]
            rows = [_table_cells(ln) for ln in block if not _is_sep_line(ln)]
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
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("md_path", help="要推送的 md 文件路径")
    p.add_argument("--parent-id", help="父页 pageId（新建子页用；与 --update-id 互斥）")
    p.add_argument("--update-id", help="已有页 pageId，覆盖更新（跳过新建）")
    p.add_argument("--space", default="DEMO_SPACE_KEY", help="space key（默认 DEMO_SPACE_KEY）")
    p.add_argument("--title", help="覆盖页面标题（默认取 md 首个 H1）")
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
    p.add_argument("--no-merge-tracking", dest="merge_tracking", action="store_false",
                   help="关闭埋点表 rowspan 合并（恢复平铺 md 表格）")
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
    p.add_argument(
        "--allow-soft-breaks",
        action="store_true",
        help="跳过字段块软换行阻断（连续行会被 wiki 并成一段）",
    )
    args = p.parse_args()

    md_path = Path(args.md_path)
    if not md_path.exists():
        sys.exit(f"md 文件不存在：{md_path}")

    exclude_sections = DEFAULT_EXCLUDE_SECTIONS + (args.exclude_section or [])
    strip_preamble = not args.keep_preamble

    md, base_dir = md_path.read_text(encoding="utf-8"), md_path.parent
    md = strip_for_confluence(md, exclude_sections, strip_preamble)
    warn_broken_tables(md, md_path)
    if check_soft_line_breaks(md, md_path, allow=args.allow_soft_breaks):
        sys.exit(1)
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
