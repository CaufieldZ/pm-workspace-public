#!/usr/bin/env python3
"""PRD 截图 framework · 复活自 git show 36e1b5b^:.claude/skills/prd/scripts/screenshots.py

提供：
- IMAP 模式截图（按 .st h2 找最近 .flow，element screenshot + 透明底 + DPI 144）
- 原型模式截图（骨架原型 build_proto_skeleton 生成的：遍历 view × page，
  switchGlobalView + goPage 逐页 element screenshot）
- 通用 helpers（项目原型脚本可 import 复用）：launch_page / hide_imap_annotations /
  dismiss_all_overlays / fix_dpi
- freshness 断言（核心解药，防漏重拍）：assert_screenshots_fresh
- 截图源探测（prototype-first → IMAP fallback）：discover_source_html

不提供：
- 手写原型截图（非骨架结构：selector / 交互态 / overlay 项目专属，留项目脚本自管，
  但项目脚本应 import 本模块的 helpers，不要从零起步）
- 骨架原型的抽屉 / 模态 / dropdown 等附加交互态（只覆盖 view × page 导航主干，
  附加态需要时走 --scenes 白名单 + per-project）
- docx 回填（v2 起 PRD 是 md，截图直接 ./assets/ 引用，Confluence 推送时自动上传）

用法：
    # IMAP 模式全截（discover）
    python3 screenshot_for_prd.py --imap <imap.html> -o <assets_dir>

    # IMAP 模式白名单
    python3 screenshot_for_prd.py --imap <imap.html> -o <assets_dir> \\
        --scenes "scene-A-1.png=A-1 · 完整全貌,scene-B-flow.png=B · 连麦全流程"

    # 原型模式全截（骨架原型，按 view × page discover）
    python3 screenshot_for_prd.py --proto <proto.html> -o <assets_dir>

    # 原型模式白名单（keyword 匹配 'view_id/page_id' 或 view_id 或 page_id）
    python3 screenshot_for_prd.py --proto <proto.html> -o <assets_dir> \\
        --scenes "proto-h5-center.png=h5/center"

    # freshness 断言（check_prd_md.sh 调用）
    python3 screenshot_for_prd.py --assert-fresh --source <html> --assets <assets_dir>

项目脚本 import 示例：
    sys.path.insert(0, "<repo>/.claude/skills/prd/scripts")
    from screenshot_for_prd import shoot_from_imap, assert_screenshots_fresh
    shoot_from_imap(imap_html=..., out_dir=..., scenes=[(fname, kw), ...])
"""
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from core.images import fix_dpi, round_phone_corners  # noqa: E402

DEFAULT_VIEWPORT = (2600, 900)
DEFAULT_DPI = 144

HIDE_AND_TRANSPARENT_CSS = """
  /* 隐藏所有非设备层 */
  .anno, .anno-n,
  .ann-card, .ann-tag,
  .flow-note,
  .st,
  .side-nav, header.hd, .progress-bar { display: none !important; }
  /* IMAP 排版用的空 spacer DIV（.flow 直接子级、无内容）—— 比如 phone 和 .ann-card
     之间的 `<div style="width:32px"></div>` —— 在截图模式下成为 phantom 右留白，
     精确打击不误伤设备壳 */
  .flow > div:empty { display: none !important; }
  /* body / 容器透明，让 omit_background 生效 + phone 圆角四角透明 */
  html, body { background: transparent !important; }
  .cv, .fade-section, .flow, .flow-col { background: transparent !important; }
  /* .flow 宽度收缩到子元素总宽，避免右边大片留白被截进图 */
  .flow {
    width: fit-content !important;
    max-width: none !important;
    overflow: visible !important;
    padding: 12px !important;
    gap: 24px !important;
  }
"""


# ── 通用 helpers ─────────────────────────────────────────────────────────

def launch_page(html_path, viewport=DEFAULT_VIEWPORT, device_scale_factor=2):
    """playwright launch + new_context + new_page + goto + wait_for_load_state boilerplate。

    caller 负责 browser.close() 和 pw.stop()。推荐用 try/finally 包围。

    Returns: (pw, browser, ctx, page)
    """
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport={"width": viewport[0], "height": viewport[1]},
        device_scale_factor=device_scale_factor,
    )
    page = ctx.new_page()
    page.goto(Path(html_path).as_uri())
    page.wait_for_load_state("networkidle")
    return pw, browser, ctx, page


def hide_imap_annotations(page):
    """IMAP 模式注入 CSS：隐藏标注层 + 透明背景 + .flow 自适应宽度 + 强制展开 fade-section。"""
    page.add_style_tag(content=HIDE_AND_TRANSPARENT_CSS)
    page.evaluate(
        "document.querySelectorAll('.fade-section').forEach(el => el.classList.add('visible'));"
    )
    page.wait_for_timeout(400)


def dismiss_all_overlays(page, extra_ids=None):
    """通用 overlay dismiss（原型截图模式调用，截图前预处理）。

    Args:
        page: playwright Page
        extra_ids: 项目特定 overlay element id 列表（如 ['drawerOverlay', 'taskSheet']）

    总是做的：
    - 移除所有 .modal-bg / .overlay / .drawer-overlay 的 .show class + display=none
    - 对 extra_ids 里的每个 id 同上

    Examples:
        # 通用兜底
        dismiss_all_overlays(page)

        # 项目特定（activity-center）
        dismiss_all_overlays(page, extra_ids=[
            'drawerOverlay', 'drawerPanel', 'appDrawerMask', 'appDrawerPanel',
            'myRewardsOverlay', 'myRewardsPanel', 'taskSheetOverlay', 'taskSheet',
            'tabModal', 'bnModal', 'navDropdown',
        ])
    """
    extra_ids = extra_ids or []
    page.evaluate(
        """(extraIds) => {
            document.querySelectorAll('.modal-bg, .overlay, .drawer-overlay').forEach(el => {
                el.classList.remove('show');
                el.style.display = 'none';
            });
            extraIds.forEach(id => {
                const el = document.getElementById(id);
                if (el) { el.classList.remove('show'); el.style.display = 'none'; }
            });
        }""",
        extra_ids,
    )
    page.wait_for_timeout(200)


def shoot_phone_full(page, container_selector='.app-mock', page_selector='.p-page.show') -> bytes:
    """Phone 端全高截图：撑高容器至内容 scrollHeight 再截，截完还原。

    解决内容超出 viewport 高度时被截断的问题（内联卡、长列表等）。

    Args:
        page: playwright Page
        container_selector: 手机壳容器选择器，默认 .app-mock
        page_selector: 当前展示页的选择器，用于读 scrollHeight，默认 .p-page.show

    Returns:
        bytes: PNG 截图数据

    Examples:
        data = shoot_phone_full(page)
        data = shoot_phone_full(page, container_selector='.phone-frame', page_selector='.view.active')
    """
    page.evaluate(
        f"""() => {{
            const container = document.querySelector('{container_selector}');
            if (!container) return;
            const inner = container.querySelector('{page_selector}');
            if (inner) container.style.height = inner.scrollHeight + 'px';
        }}"""
    )
    page.wait_for_timeout(80)
    data = page.locator(container_selector).first.screenshot()
    page.evaluate(
        f"""() => {{
            const container = document.querySelector('{container_selector}');
            if (container) container.style.height = '';
        }}"""
    )
    return data


# ── IMAP 模式截图 ────────────────────────────────────────────────────────

MANIFEST_FILENAME = ".freshness.json"
MANIFEST_SCHEMA = 1

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_WS_RE = re.compile(r"\s+")
_INTER_TAG_WS_RE = re.compile(r">\s+<")


def _normalize_html_for_hash(html: str) -> str:
    """Normalize HTML 给 hash 用，让语义无关变更不触发 stale：
    - 去 HTML 注释
    - 连续空白合并为单空格（含跨行）
    - 标签之间的纯空白删除（IDE 缩进 / 换行）—— 用于忽略 Prettier reformat
    - 整体 strip

    保留：所有标签 / 属性 / 文本节点内空白（如 'hello world' 的中间空格）。
    任何会影响 .flow 渲染的实质改动都该触发 stale。
    """
    if not html:
        return ""
    cleaned = _HTML_COMMENT_RE.sub("", html)
    cleaned = _WS_RE.sub(" ", cleaned)
    cleaned = _INTER_TAG_WS_RE.sub("><", cleaned)
    return cleaned.strip()


def _hash_flow_html(html: str) -> str:
    """sha256(normalize(html))，输出 'sha256:<hex>'。"""
    norm = _normalize_html_for_hash(html)
    return "sha256:" + hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _manifest_path(assets_dir):
    return Path(assets_dir) / MANIFEST_FILENAME


def _load_manifest(assets_dir):
    """读 .freshness.json；不存在 / 损坏 / schema 不匹配 → None（触发降级）。"""
    p = _manifest_path(assets_dir)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("schema") != MANIFEST_SCHEMA:
        return None
    if not isinstance(data.get("entries"), dict):
        return None
    return data


def _save_manifest(assets_dir, entries):
    """落 .freshness.json，按 filename 排序保证 diff 稳定。"""
    p = _manifest_path(assets_dir)
    data = {
        "schema": MANIFEST_SCHEMA,
        "entries": {k: entries[k] for k in sorted(entries)},
    }
    p.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return p


_DIV_TAG_RE = re.compile(r"<(/?)div\b[^>]*>", re.IGNORECASE)


def _extract_balanced_div(text, start_idx):
    """从 text[start_idx]（必须是 <div ...> 起点）抽 outerHTML（含匹配 </div>）。

    计数法处理嵌套 div；None 表示 markup 不闭合。
    """
    depth = 0
    pos = start_idx
    while True:
        m = _DIV_TAG_RE.search(text, pos)
        if not m:
            return None
        if m.group(1) == "":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return text[start_idx: m.end()]
        pos = m.end()


def _find_flow_for_h2(source_html_text, h2_keyword):
    """按 h2 文本（含 keyword）定位 .st，回紧邻下一个 .flow 的 outerHTML。

    扫所有 .st 段（section|div class=st），h2 文本包含 keyword 即命中；
    从 .st 结束位置向后找首个 <div class=...flow...>，中间只允许空白，
    用 balanced div 抽 outerHTML。

    与 _FLOW_INDEX_JS 的「文档顺序最近 .flow」一致——IMAP 中 .st / .flow 兄弟同层。
    若 markup 重构破坏紧邻约定 → None → freshness 报「源结构变化」。
    """
    st_iter = re.finditer(
        r'<(?P<tag>section|div)[^>]*\bclass="[^"]*\bst\b[^"]*"[^>]*>(?P<body>.*?)</(?P=tag)>',
        source_html_text,
        re.DOTALL,
    )
    for m in st_iter:
        body = m.group("body")
        h2_match = re.search(r"<h2[^>]*>(.+?)</h2>", body, re.DOTALL)
        if not h2_match:
            continue
        h2_text = re.sub(r"<[^>]+>", "", h2_match.group(1)).strip()
        if h2_keyword not in h2_text:
            continue
        tail_start = m.end()
        flow_open = re.search(
            r'<div[^>]*\bclass="[^"]*\bflow\b[^"]*"[^>]*>',
            source_html_text[tail_start:],
        )
        if not flow_open:
            return None
        flow_start_abs = tail_start + flow_open.start()
        between = source_html_text[tail_start: flow_start_abs]
        if between.strip():
            return None
        return _extract_balanced_div(source_html_text, flow_start_abs)
    return None


_SCENE_CODE_RE = re.compile(r'^([A-Z](?:-[\w/]+)?)\s*[·•]')


def _find_page_div(source_html_text, page_id):
    """按 id="page-{page_id}" 定位 .p-page div，回 outerHTML。骨架原型专用（freshness hash）。

    与 _find_flow_for_h2 同源：从源 HTML 文本（非浏览器 DOM）抽子树，避免 markup 规范化
    导致生成端 / 检查端 hash 不一致。None = 该页在源 HTML 中找不到（结构变化）。
    """
    m = re.search(
        r'<div[^>]*\bid="page-' + re.escape(page_id) + r'"[^>]*>',
        source_html_text,
    )
    if not m:
        return None
    return _extract_balanced_div(source_html_text, m.start())


def _extract_scene_id(h2_text):
    """从 h2 文本头部抽 scene_id（如 'A-1' from 'A-1 · ...'）；不匹配返 None。"""
    m = _SCENE_CODE_RE.match(h2_text.strip())
    return m.group(1) if m else None


def discover_scenes_from_imap(imap_html):
    """从 IMAP HTML 抽场景列表（按 .st h2 文本）。

    h2 文本格式 "A-1 · 直播间完整全貌" / "B · 连麦全流程" / "D-0d/f/e"，
    抽编号头部当 scene_code。

    Returns: [(scene_code, h2_full_text), ...]
    """
    text = Path(imap_html).read_text(encoding="utf-8")
    h2_re = re.compile(
        r'<section[^>]*class="[^"]*\bst\b[^"]*"[^>]*>.*?<h2[^>]*>(.+?)</h2>',
        re.DOTALL,
    )
    matches = h2_re.findall(text)
    if not matches:
        matches = re.findall(r'<h2[^>]*>(.+?)</h2>', text)

    results = []
    for raw in matches:
        clean = re.sub(r'<[^>]+>', '', raw).strip()
        code = _extract_scene_id(clean)
        if code:
            results.append((code, clean))
    return results


_FLOW_INDEX_JS = """() => {
    const flows = Array.from(document.querySelectorAll('.flow'));
    const sts = Array.from(document.querySelectorAll('.st'));
    const result = [];
    for (const st of sts) {
        const h2 = st.querySelector('h2');
        const title = h2 ? h2.textContent.trim() : '';
        let nearest = -1, bestDist = Infinity;
        for (let i = 0; i < flows.length; i++) {
            const cmp = st.compareDocumentPosition(flows[i]);
            if (cmp & Node.DOCUMENT_POSITION_FOLLOWING) {
                const stRect = st.getBoundingClientRect();
                const flowRect = flows[i].getBoundingClientRect();
                const dist = flowRect.top - stRect.top;
                if (dist >= 0 && dist < bestDist) {
                    bestDist = dist;
                    nearest = i;
                }
            }
        }
        if (nearest >= 0) result.push({title, flowIndex: nearest});
    }
    return result;
}"""


def shoot_from_imap(imap_html, out_dir, scenes=None,
                    viewport=DEFAULT_VIEWPORT, dpi=DEFAULT_DPI,
                    round_phone=False):
    """IMAP 模式截图：按 h2 keyword 找最近 .flow 元素，element screenshot omit_background。

    Args:
        imap_html: IMAP HTML 文件路径
        out_dir: 输出目录
        scenes: [(filename, h2_keyword), ...]，None 则 discover 全截
        viewport: (width, height) 初始 viewport，加载后会撑到完整页高
        dpi: DPI 元数据值（默认 144，避免 docx / Confluence 渲染虚化）
        round_phone: True 则对截图调 round_phone_corners 加圆角蒙版（CSS border-radius 已生效时不必）

    Returns: dict {filename: png_path}
    """
    imap_html = Path(imap_html)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not imap_html.exists():
        raise SystemExit(f"❌ IMAP HTML 不存在：{imap_html}")

    if scenes is None:
        discovered = discover_scenes_from_imap(imap_html)
        scenes = [(f"scene-{code}.png", h2) for code, h2 in discovered]
        if not scenes:
            raise SystemExit(f"❌ 未能从 {imap_html.name} 抽出任何 .st h2")
        print(f"→ discover {len(scenes)} 个场景（无 --scenes 白名单）")

    pw, browser, _ctx, page = launch_page(imap_html, viewport=viewport)
    try:
        hide_imap_annotations(page)

        full_height = page.evaluate("() => document.documentElement.scrollHeight")
        print(f"Full page height: {full_height}px")
        page.set_viewport_size({"width": viewport[0], "height": full_height})
        page.wait_for_timeout(600)

        flow_index_map = page.evaluate(_FLOW_INDEX_JS)
        print(f"{len(flow_index_map)} st→flow 映射")

        # 读源 HTML 文本一次，给 manifest hash 用（与 freshness 检查端同源）
        source_text = imap_html.read_text(encoding="utf-8")

        captured = {}
        missing = []
        manifest_entries = {}
        for fname, keyword in scenes:
            entry = next((e for e in flow_index_map if keyword in e["title"]), None)
            if not entry:
                missing.append((fname, keyword))
                print(f"[MISS] {fname} ← '{keyword}' 未匹配")
                continue

            flow_locator = page.locator(".flow").nth(entry["flowIndex"])
            flow_locator.scroll_into_view_if_needed()
            page.wait_for_timeout(200)

            out_path = out_dir / fname
            flow_locator.screenshot(path=str(out_path), omit_background=True)
            fix_dpi(str(out_path), dpi=dpi)
            if round_phone:
                round_phone_corners(str(out_path))

            # hash 走源 HTML 文本（不用 Playwright DOM）：浏览器会规范化 markup
            # （属性顺序 / 引号 / 自闭合标签），导致生成端 hash 与检查端 Python 解析 hash 不一致
            flow_html_for_hash = _find_flow_for_h2(source_text, keyword)
            if flow_html_for_hash is None:
                print(f"  ⚠ {fname} hash 跳过：源 HTML 中按 h2 keyword 未定位 .flow")
            else:
                manifest_entries[fname] = {
                    "scene_id": _extract_scene_id(entry["title"]) or "",
                    "h2_keyword": entry["title"],
                    "source_html": imap_html.name,
                    "flow_html_hash": _hash_flow_html(flow_html_for_hash),
                    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                }

            kb = os.path.getsize(out_path) / 1024
            print(f"[OK] {fname} ({kb:.0f} KB) ← {entry['title'][:50]}")
            captured[fname] = out_path

        if missing:
            print(f"\n⚠ {len(missing)} 张未匹配：{missing}")
        print(f"\n✓ {len(captured)} 张落到 {out_dir}/")

        if manifest_entries:
            existing = _load_manifest(out_dir)
            merged = dict(existing["entries"]) if existing else {}
            merged.update(manifest_entries)
            mp = _save_manifest(out_dir, merged)
            print(f"  manifest: {mp.name} ({len(manifest_entries)} 条更新 / 共 {len(merged)} 条)")

        return captured
    finally:
        browser.close()
        pw.stop()


# ── 原型模式截图（build_proto_skeleton 生成的骨架原型）────────────────────

PROTO_VIEWPORT = (1440, 1024)

# 截图前隐藏原型外壳（顶部 view 切换 chrome）：.gnav 固定定位会盖进 web-front 整屏截图；
# 同步清掉 .gnav-view-wrap 给 gnav 让位的 padding-top，避免顶部留白
PROTO_HIDE_CHROME_CSS = """
  .gnav { display: none !important; }
  .gnav-view-wrap { padding-top: 0 !important; }
"""

_PROTO_DISCOVER_JS = """() => {
    const tabs = Array.from(document.querySelectorAll('.gnav-tab'));
    const sections = Array.from(document.querySelectorAll('.gnav-view-section'));
    const result = [];
    sections.forEach((sec, vi) => {
        const viewId = sec.id || ('view' + vi);
        const tab = tabs[vi];
        const viewName = tab ? tab.textContent.trim() : viewId;
        const hasAppMock = !!sec.querySelector('.app-mock');
        sec.querySelectorAll('.p-page').forEach(p => {
            const pageId = (p.id || '').replace(/^page-/, '');
            if (pageId) result.push({viewIdx: vi, viewId, viewName, hasAppMock, pageId});
        });
    });
    return result;
}"""


def shoot_from_proto(proto_html, out_dir, scenes=None,
                     viewport=PROTO_VIEWPORT, dpi=DEFAULT_DPI):
    """骨架原型模式截图：遍历 view × page，switchGlobalView + goPage 逐页 element screenshot。

    依赖 build_proto_skeleton 约定：.gnav-view-section[id] = view（switchGlobalView 切，
    .gnav-active 标记），.p-page#page-{id} = 页面（goPage 切，.show 标记），截图目标取激活
    view 内 .app-mock（phone 设备）或 section 本身（web-front）。手写原型（无此结构）→
    报错引导走 per-project 脚本。只覆盖 view × page 导航主干，抽屉 / 模态等附加态不遍历。

    Args:
        proto_html: 原型 HTML 文件路径
        out_dir: 输出目录
        scenes: [(filename, keyword), ...] 白名单，keyword 匹配 'view_id/page_id' / view_id /
                page_id；None 则 discover 全截
        viewport: (width, height) 初始 viewport
        dpi: DPI 元数据值（默认 144）

    Returns: dict {filename: png_path}
    """
    proto_html = Path(proto_html).resolve()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not proto_html.exists():
        raise SystemExit(f"❌ 原型 HTML 不存在：{proto_html}")

    source_text = proto_html.read_text(encoding="utf-8")

    pw, browser, _ctx, page = launch_page(proto_html, viewport=viewport)
    try:
        pages_meta = page.evaluate(_PROTO_DISCOVER_JS)
        if not pages_meta:
            raise SystemExit(
                f"❌ {proto_html.name} 非骨架原型结构（无 .gnav-view-section / .p-page）。\n"
                f"   手写原型状态到达逻辑项目专属，无法通用截图，请走 per-project 脚本：\n"
                f"   参考 projects/growth/archive/activity-center/scripts/screenshot_for_prd.py\n"
                f"   （import 本模块 launch_page / dismiss_all_overlays / fix_dpi，不从零起步）"
            )
        n_views = len({m["viewId"] for m in pages_meta})
        print(f"→ discover {len(pages_meta)} 个页面（{n_views} 个 view）")

        page.add_style_tag(content=PROTO_HIDE_CHROME_CSS)

        captured = {}
        manifest_entries = {}
        for meta in pages_meta:
            vid, pid = meta["viewId"], meta["pageId"]
            if scenes is not None:
                match = next((f for f, kw in scenes
                              if kw in (f"{vid}/{pid}", vid, pid)), None)
                if not match:
                    continue
                fname = match
            else:
                fname = f"proto-{vid}-{pid}.png"

            # 导航到该 view × page（switchGlobalView 切 view，goPage 切页）
            page.evaluate(f"switchGlobalView({meta['viewIdx']}); goPage({pid!r});")
            page.wait_for_timeout(300)
            dismiss_all_overlays(page)

            # 截图目标：激活 section 内 .app-mock（phone）或 .p-page.show（web-front）
            # web-front 不用整个 section（section 有 min-height:100vh 会带出大片留白）
            sec = page.locator(".gnav-view-section.gnav-active")
            target = sec.locator(".app-mock")
            if target.count() == 0:
                active_page = sec.locator(".p-page.show")
                target = active_page if active_page.count() > 0 else sec
            target.first.scroll_into_view_if_needed()
            page.wait_for_timeout(150)

            out_path = out_dir / fname
            target.first.screenshot(path=str(out_path))
            fix_dpi(str(out_path), dpi=dpi)

            # hash 走源 HTML 文本（不用 Playwright DOM，避免 markup 规范化致 hash 不一致）
            page_html_for_hash = _find_page_div(source_text, pid)
            if page_html_for_hash is None:
                print(f"  ⚠ {fname} hash 跳过：源 HTML 中未定位 #page-{pid}")
            else:
                manifest_entries[fname] = {
                    "view_id": vid,
                    "page_id": pid,
                    "source_html": proto_html.name,
                    "page_html_hash": _hash_flow_html(page_html_for_hash),
                    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                }

            kb = os.path.getsize(out_path) / 1024
            print(f"[OK] {fname} ({kb:.0f} KB) ← {meta['viewName']} / {pid}")
            captured[fname] = out_path

        print(f"\n✓ {len(captured)} 张落到 {out_dir}/")

        if manifest_entries:
            existing = _load_manifest(out_dir)
            merged = dict(existing["entries"]) if existing else {}
            merged.update(manifest_entries)
            mp = _save_manifest(out_dir, merged)
            print(f"  manifest: {mp.name} ({len(manifest_entries)} 条更新 / 共 {len(merged)} 条)")

        return captured
    finally:
        browser.close()
        pw.stop()


# ── freshness 断言（核心解药）────────────────────────────────────────────

def _collect_pngs(assets_dir, excluded_patterns):
    pngs = []
    for p in assets_dir.rglob('*.png'):
        rel = str(p.relative_to(assets_dir))
        if any(pat in rel for pat in excluded_patterns):
            continue
        pngs.append(p)
    return pngs


def _assert_fresh_by_mtime(source_html, assets_dir, pngs):
    """降级路径：mtime 比对（manifest 缺失 / 单 PNG 无 entry 时用）。

    保持原 v1 行为：源 mtime > PNG mtime → stale。
    返回 stale 列表 [(png_path, reason_str)]，不直接抛错。
    """
    src_t = source_html.stat().st_mtime
    stale = []
    for p in pngs:
        if p.stat().st_mtime < src_t:
            delta_h = (src_t - p.stat().st_mtime) / 3600
            stale.append((p, f"mtime 旧 {delta_h:.1f}h（无 manifest entry，降级判定）"))
    return stale


def assert_screenshots_fresh(source_html, assets_dir,
                             excluded_patterns=('archive', 'deprecated')):
    """断言截图与源 HTML 一致。

    判定逻辑（v2，hash-based）：
    1. 读 deliverables/assets/.freshness.json
       - 无 → 全量降级 mtime
       - 有 → 走 hash 路径，每张 PNG：
         * 有 entry → 在源 HTML 中按 h2_keyword 重定位 .flow，重算 hash 比对
         * 无 entry → 单 PNG 降级 mtime（兼容未迁移截图，如 *-web 变体）
    2. stale 非空 → AssertionError，按原因分类列出

    优势 vs v1（纯 mtime）：改源 HTML 中无关 CSS / 注释 / 别的 .flow → 不误报；
    只有截图对应的 .flow 子树真改了才标 stale。

    Args:
        source_html: 截图来源 HTML（原型 / IMAP），用于 hash 重算 + mtime 兜底
        assets_dir: 截图目录（同目录有 .freshness.json）
        excluded_patterns: 相对路径含这些子串的 PNG 跳过

    边界（静默 return）：source 不存在 / assets_dir 不存在 / 无 PNG
    """
    source_html = Path(source_html)
    assets_dir = Path(assets_dir)

    if not source_html.exists():
        return
    if not assets_dir.exists():
        return

    pngs = _collect_pngs(assets_dir, excluded_patterns)
    if not pngs:
        return

    manifest = _load_manifest(assets_dir)

    if manifest is None:
        # 全量降级
        stale = _assert_fresh_by_mtime(source_html, assets_dir, pngs)
        if not stale:
            return
        _raise_stale(source_html, assets_dir, stale, len(pngs),
                     note="无 .freshness.json，全量降级 mtime 判定")
        return

    # Hash 路径
    entries = manifest["entries"]
    # 全局 source_text：传入 source_html 的缓存（多端原型时部分 entry 会用自己的 source）
    _source_text_cache: dict = {}

    def _get_source_text(html_path: Path) -> str:
        key = str(html_path)
        if key not in _source_text_cache:
            _source_text_cache[key] = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
        return _source_text_cache[key]

    stale = []
    no_entry_pngs = []

    for p in pngs:
        name = p.name
        entry = entries.get(name)
        if not entry:
            no_entry_pngs.append(p)
            continue

        # 多端原型：entry 记了自己的 source_html（如 app.html vs web.html），优先用 entry 的
        entry_source_name = entry.get("source_html")
        if entry_source_name:
            entry_source = source_html.parent / entry_source_name
        else:
            entry_source = source_html
        cur_text = _get_source_text(entry_source)

        # proto entry（骨架原型）：按 page_id 重定位 .p-page 子树重算 hash
        if entry.get("page_id"):
            page_id = entry["page_id"]
            page_html = _find_page_div(cur_text, page_id)
            if page_html is None:
                stale.append((p, f"源结构变化：原型页 #page-{page_id} 找不到"))
                continue
            if _hash_flow_html(page_html) != entry.get("page_html_hash"):
                stale.append((p, ".p-page 内容变化（hash 不一致）"))
            continue

        # IMAP entry：按 h2_keyword 重定位 .flow
        keyword = entry.get("h2_keyword", "")
        flow_html = _find_flow_for_h2(cur_text, keyword) if keyword else None
        if flow_html is None:
            stale.append((p, f"源结构变化：h2「{keyword}」找不到或紧邻 .flow 缺失"))
            continue

        current_hash = _hash_flow_html(flow_html)
        if current_hash != entry.get("flow_html_hash"):
            stale.append((p, ".flow 内容变化（hash 不一致）"))

    # 单 PNG 降级 mtime
    if no_entry_pngs:
        stale.extend(_assert_fresh_by_mtime(source_html, assets_dir, no_entry_pngs))

    # 反向扫：manifest 有但文件已删 → warning（不阻断）
    existing_names = {p.name for p in pngs}
    orphan = [name for name in entries if name not in existing_names]
    if orphan:
        print(f"⚠ manifest 有 {len(orphan)} 条但 PNG 缺失（孤立 entry）：{orphan[:5]}")

    if not stale:
        return
    _raise_stale(source_html, assets_dir, stale, len(pngs))


def _raise_stale(source_html, assets_dir, stale, total, note=None):
    msg = [
        '\n❌ [assert_screenshots_fresh] 截图与源 HTML 不一致：',
        f'   源 HTML: {source_html.name}',
        f'   stale ({len(stale)}/{total} 张):',
    ]
    if note:
        msg.append(f'   备注: {note}')
    for p, reason in stale[:10]:
        msg.append(f'     - {p.relative_to(assets_dir)} : {reason}')
    if len(stale) > 10:
        msg.append(f'     ... 共 {len(stale)} 张')
    msg.append('   修复：跑 projects/{项目}/scripts/screenshot_for_prd*.py 或 framework CLI 重拍')
    raise AssertionError('\n'.join(msg))


def discover_source_html(deliverables_dir):
    """找截图源 HTML：合并 prototype + IMAP 候选，取 mtime 最新的。

    candidates: *原型*.html / proto-*.html / prototype-*.html / *交互大图*.html / imap-*.html

    设计：取最新 mtime 而非 prototype-first，避免「项目同时有 prototype 和 IMAP，
    但实际只从其中一个截图」时挑错源。任一源 HTML 更新 → PNG 被认定 stale，保守安全。
    archive / deprecated 子串路径排除。

    Returns: Path | None
    """
    deliverables_dir = Path(deliverables_dir)
    if not deliverables_dir.exists():
        return None

    patterns = ('*原型*.html', 'proto-*.html', 'prototype-*.html',
                '*交互大图*.html', 'imap-*.html')
    candidates = []
    for pat in patterns:
        candidates.extend(deliverables_dir.glob(pat))
    candidates = [c for c in candidates
                  if 'archive' not in str(c) and 'deprecated' not in str(c)]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PRD 截图 framework（IMAP 模式 + 原型模式 + freshness 断言）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--imap", help="IMAP HTML 路径（IMAP 截图模式）")
    parser.add_argument("--proto", help="原型 HTML 路径（骨架原型截图模式，与 --imap 互斥）")
    parser.add_argument("-o", "--out", help="输出目录（截图模式；省略则配合 -p 推导 projects/{线}/{项目}/deliverables/assets/prd/）")
    parser.add_argument("-p", "--project", help="项目名（短名 kebab-case，如 leaderboard）；用于推导 -o 默认值")
    parser.add_argument(
        "--scenes",
        help="白名单，格式 'fname1.png=kw1,fname2.png=kw2'，省略则 discover 全截",
    )
    parser.add_argument("--round-phone", action="store_true",
                        help="对截图调 round_phone_corners 加圆角（默认 off）")
    parser.add_argument("--assert-fresh", action="store_true",
                        help="只跑 freshness 断言，不截图")
    parser.add_argument("--source", help="freshness 断言：源 HTML 路径")
    parser.add_argument("--assets", help="freshness 断言：截图目录")
    args = parser.parse_args()

    if args.assert_fresh:
        if not args.source or not args.assets:
            sys.exit("❌ --assert-fresh 需要 --source 和 --assets")
        assert_screenshots_fresh(args.source, args.assets)
        print(f"✓ 截图 fresh（vs {Path(args.source).name}）")
        return

    if args.project and not args.out:
        repo = Path(__file__).resolve().parents[4]
        cands = list((repo / "projects").glob(f"*/{args.project}"))
        direct = repo / "projects" / args.project
        if direct.is_dir():
            cands.append(direct)
        if len(cands) == 1:
            args.out = str(cands[0] / "deliverables" / "assets" / "prd")
        elif len(cands) > 1:
            sys.exit(f"❌ -p {args.project} 匹配多个：{[str(c) for c in cands]}；请显式传 -o")
        else:
            sys.exit(f"❌ -p {args.project} 找不到对应项目目录；请显式传 -o")

    if args.imap and args.proto:
        sys.exit("❌ --imap 与 --proto 互斥，二选一")
    if not (args.imap or args.proto) or not args.out:
        sys.exit("❌ 截图模式需要 --imap 或 --proto，外加 -o（或 -p 推导）；freshness 模式用 --assert-fresh")

    scenes = None
    if args.scenes:
        scenes = []
        for pair in args.scenes.split(","):
            if "=" not in pair:
                sys.exit(f"❌ --scenes 格式错误：{pair}（应为 fname=keyword）")
            fname, keyword = pair.split("=", 1)
            scenes.append((fname.strip(), keyword.strip()))

    if args.proto:
        # 项目有专属截图脚本时拒绝通用 --proto，避免 shot_setup / registry 被跳过
        proto_path = Path(args.proto).resolve()
        project_script = proto_path.parents[3] / "scripts" / "screenshot_proto.py"
        if project_script.exists():
            sys.exit(
                f"❌ [screenshot-route-gate] 该项目有专属截图脚本，禁用通用 --proto 模式：\n"
                f"   项目脚本：{project_script}\n"
                f"   原因：通用模式不读 registry.shot_setup，含多场景页面会截到错误默认态\n"
                f"   修复：cd {project_script.parent.parent} && python3 scripts/screenshot_proto.py"
            )
        shoot_from_proto(args.proto, args.out, scenes=scenes)
    else:
        shoot_from_imap(args.imap, args.out, scenes=scenes, round_phone=args.round_phone)


if __name__ == "__main__":
    main()
