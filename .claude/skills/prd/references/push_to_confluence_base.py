#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""
push_to_confluence_base.py — 推送 PRD docx 到 Confluence Server

用法:
    python3 push_to_confluence_base.py <docx路径> <页面标题> <space_key> [parent_page_id]

说明:
    - 凭证自动从 pm-workspace/.mcp.json 读取，不需要手动配置
    - 图片提取后作为附件上传，再用 ac:image 宏引用
    - 页面存在则更新版本，不存在则新建
    - 依赖: pip install mammoth requests

示例:
    python3 .claude/skills/prd/references/push_to_confluence_base.py \\
        projects/htx-activity-center/deliverables/prd-htx-v1.docx \\
        "HTX 活动中心 PRD v1" \\
        HTX \\
        12345678
"""

import sys, re, json, requests
from pathlib import Path

try:
    import mammoth
except ImportError:
    sys.exit("缺依赖: pip install mammoth requests")

# ── 从 .mcp.json 读取 Confluence 配置 ──────────────────────────────────────
_ROOT = Path(__file__).resolve().parents[4]  # pm-workspace 根目录
_MCP_PATH = _ROOT / ".mcp.json"
if not _MCP_PATH.exists():
    sys.exit(f"找不到 .mcp.json: {_MCP_PATH}")

_CONF = json.loads(_MCP_PATH.read_text())["mcpServers"]["confluence"]["env"]
BASE_URL = _CONF["CONF_BASE_URL"].rstrip("/")
TOKEN    = _CONF["CONF_TOKEN"]
_HEADERS = {"Authorization": f"Bearer {TOKEN}"}


# ── REST API 封装 ────────────────────────────────────────────────────────────

def _rest(method: str, path: str, **kwargs):
    url = f"{BASE_URL}/rest/api/{path.lstrip('/')}"
    headers = {**_HEADERS, **kwargs.pop("extra_headers", {})}
    r = requests.request(method, url, headers=headers, **kwargs)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        sys.exit(f"Confluence API 错误 [{r.status_code}]: {r.text[:300]}\n{e}")
    return r.json() if r.content else {}


def get_or_create_page(space_key: str, title: str, parent_id: str = None) -> tuple:
    """返回 (page_id, current_version_number)。页面不存在则新建占位页。"""
    resp = _rest("GET", "content", params={
        "spaceKey": space_key, "title": title, "expand": "version"
    })
    results = resp.get("results", [])
    if results:
        p = results[0]
        return p["id"], p["version"]["number"]

    # 新建占位页（先建后填内容，这样附件上传有 pageId）
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {"storage": {"value": "", "representation": "storage"}},
    }
    if parent_id:
        payload["ancestors"] = [{"id": str(parent_id)}]
    p = _rest("POST", "content",
              json=payload,
              extra_headers={"Content-Type": "application/json"})
    return p["id"], 1


def upload_attachment(page_id: str, filename: str, data: bytes, mime: str = "image/png"):
    """上传图片附件，已存在则更新（upsert）。"""
    base = f"{BASE_URL}/rest/api/content/{page_id}/child/attachment"
    headers = {**_HEADERS, "X-Atlassian-Token": "no-check"}

    # 查是否已有同名附件
    existing = requests.get(base, headers=_HEADERS,
                            params={"filename": filename}).json().get("results", [])
    if existing:
        att_id = existing[0]["id"]
        url = f"{base}/{att_id}/data"
    else:
        url = base

    requests.post(url, headers=headers,
                  files={"file": (filename, data, mime)}).raise_for_status()


# ── docx → Confluence storage format ────────────────────────────────────────

def convert_docx(docx_path: str, page_id: str, img_width: int = 600) -> str:
    """
    1. mammoth 把 docx 转 HTML，图片提取到内存
    2. 图片上传为页面附件
    3. <img src="..."> 替换为 <ac:image> 宏
    返回 Confluence storage format HTML 字符串
    """
    _images = {}   # filename → (bytes, mime)
    _idx = [0]

    def handle_image(image):
        with image.open() as f:
            data = f.read()
        mime = getattr(image, "content_type", None) or "image/png"
        ext  = mime.split("/")[-1].split("+")[0]   # image/svg+xml → svg
        _idx[0] += 1
        name = f"prd-img-{_idx[0]}.{ext}"
        _images[name] = (data, mime)
        return {"src": f"__ATTACH__{name}"}

    with open(docx_path, "rb") as f:
        result = mammoth.convert_to_html(
            f,
            convert_image=mammoth.images.img_element(handle_image)
        )

    if result.messages:
        for msg in result.messages:
            print(f"  ⚠ mammoth: {msg}")

    html = result.value

    # 上传附件
    for name, (data, mime) in _images.items():
        upload_attachment(page_id, name, data, mime)
        print(f"  ↑ 附件: {name} ({len(data)//1024}KB)")

    # <img src="__ATTACH__xxx"> → <ac:image> 宏
    def to_ac(m):
        src = m.group(1)
        if src.startswith("__ATTACH__"):
            fname = src[len("__ATTACH__"):]
            return f'<ac:image ac:width="{img_width}"><ri:attachment ri:filename="{fname}"/></ac:image>'
        return m.group(0)   # 外链图片保留原样

    html = re.sub(r'<img[^>]+src="([^"]+)"[^>]*/?>', to_ac, html)

    # 恢复段落缩进(mammoth 默认丢失)。
    # fill_cell_blocks 产出两级缩进:一级 "N. xxx"(Cm 0.3),二级 "  - xxx"(Cm 0.9)。
    # 映射到 HTML 的 padding-left,让 Confluence 渲染保留层次。
    def indent_p(m):
        inner = m.group(1)
        # 去掉段落内前置 <strong>/<em>/<br/> 标签,看真实文本首字符
        txt = re.sub(r'<[^>]+>', '', inner).lstrip()
        if re.match(r'^\s*-\s', txt) or inner.startswith(('  -', '\t-')):
            return f'<p style="padding-left:40px;">{inner}</p>'
        if re.match(r'^\d+\.\s', txt):
            return f'<p style="padding-left:20px;">{inner}</p>'
        return m.group(0)
    html = re.sub(r'<p>(.*?)</p>', indent_p, html, flags=re.DOTALL)

    return html


def update_page(page_id: str, title: str, body: str, current_version: int):
    payload = {
        "version": {"number": current_version + 1},
        "title": title,
        "type": "page",
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    _rest("PUT", f"content/{page_id}",
          json=payload,
          extra_headers={"Content-Type": "application/json"})


# ── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    docx_path  = sys.argv[1]
    title      = sys.argv[2]
    space_key  = sys.argv[3]
    parent_id  = sys.argv[4] if len(sys.argv) > 4 else None

    if not Path(docx_path).exists():
        sys.exit(f"文件不存在: {docx_path}")

    print(f"📄 转换: {docx_path}")
    page_id, version = get_or_create_page(space_key, title, parent_id)
    print(f"📑 页面 ID: {page_id}  当前版本: {version}")

    body = convert_docx(docx_path, page_id)

    print("📤 更新页面内容...")
    update_page(page_id, title, body, version)

    page_url = f"{BASE_URL}/pages/viewpage.action?pageId={page_id}"
    print(f"✅ 完成: {page_url}")


if __name__ == "__main__":
    main()
