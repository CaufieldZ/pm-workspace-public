#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""从 Figma 拉取文件/节点/截图。

用法:
  python3 scripts/fetch_figma.py <url>                        # 打印文件结构摘要
  python3 scripts/fetch_figma.py <url> --nodes                # 打印指定节点详情
  python3 scripts/fetch_figma.py <url> --image                # 下载节点截图到 stdout（PNG）
  python3 scripts/fetch_figma.py <url> --image -o out.png     # 下载节点截图到文件
  python3 scripts/fetch_figma.py <url> --image -p 项目名      # 截图存到 projects/{项目}/screenshots/
  python3 scripts/fetch_figma.py <url> --tree                 # 打印完整节点树（用于找 node-id）
  python3 scripts/fetch_figma.py <url> --search "关键词"      # 按名称搜索节点

直调 Figma REST API，不需要加载 MCP server（省 ~15K token）。

Figma URL 格式:
  https://www.figma.com/design/{file_key}/{title}?node-id={node_id}
  https://www.figma.com/file/{file_key}/...
  https://www.figma.com/board/{file_key}/...

凭证读取优先级:
  1. 环境变量 FIGMA_PAT
  2. .mcp-disabled.json → mcpServers.figma.env.FIGMA_PAT
  3. .mcp.json → mcpServers.figma.env.FIGMA_PAT
"""

import argparse, json, os, re, sys, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_BASE = "https://api.figma.com/v1"


# ── 凭证 ──────────────────────────────────────────────────────

def load_pat():
    pat = os.environ.get("FIGMA_PAT")
    if pat:
        return pat
    for src in [ROOT / ".mcp-disabled.json", ROOT / ".mcp.json"]:
        if src.exists():
            cfg = json.loads(src.read_text())
            env = cfg.get("mcpServers", {}).get("figma", {}).get("env", {})
            if "FIGMA_PAT" in env:
                return env["FIGMA_PAT"]
    sys.exit(
        "错误：找不到 Figma PAT。\n"
        "三种配法任选一种：\n"
        "  1. export FIGMA_PAT=figd_xxx\n"
        "  2. .mcp-disabled.json → mcpServers.figma.env.FIGMA_PAT\n"
        "  3. .mcp.json → mcpServers.figma.env.FIGMA_PAT\n\n"
        "生成 PAT：Figma → Settings → Account → Personal access tokens"
    )


# ── URL 解析 ──────────────────────────────────────────────────

def parse_figma_url(url):
    """从 Figma URL 提取 file_key 和 node_id（可选）。"""
    m = re.search(r'figma\.com/(?:file|design|board|proto)/([A-Za-z0-9]+)', url)
    if not m:
        sys.exit(f"错误：无法识别 Figma URL: {url}")
    file_key = m.group(1)
    node_id = None
    qs = urllib.parse.urlparse(url).query
    params = urllib.parse.parse_qs(qs)
    if "node-id" in params:
        node_id = params["node-id"][0].replace("-", ":")
    return file_key, node_id


# ── API 调用 ──────────────────────────────────────────────────

def api_get(pat, path, params=None):
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"X-Figma-Token": pat})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 403:
            sys.exit("错误：Figma PAT 无权限或已过期，请重新生成")
        if e.code == 404:
            sys.exit("错误：文件不存在或无访问权限")
        raise


def download_bytes(url):
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


# ── 核心功能 ──────────────────────────────────────────────────

def get_file_summary(pat, file_key):
    """文件元信息 + 顶层页面/Frame 列表。"""
    data = api_get(pat, f"/files/{file_key}", {"depth": "2"})
    summary = {
        "name": data.get("name"),
        "lastModified": data.get("lastModified"),
        "version": data.get("version"),
        "pages": [],
    }
    doc = data.get("document", {})
    for page in doc.get("children", []):
        frames = []
        for child in page.get("children", []):
            frames.append({
                "id": child["id"],
                "name": child["name"],
                "type": child["type"],
            })
        summary["pages"].append({
            "id": page["id"],
            "name": page["name"],
            "frames": frames,
        })
    return summary


def get_nodes(pat, file_key, node_ids):
    """获取指定节点的完整属性。"""
    ids = ",".join(node_ids) if isinstance(node_ids, list) else node_ids
    data = api_get(pat, f"/files/{file_key}/nodes", {"ids": ids})
    return data.get("nodes", {})


def get_image_url(pat, file_key, node_id, fmt="png", scale=2):
    """获取节点渲染图的下载 URL。"""
    data = api_get(pat, f"/images/{file_key}", {
        "ids": node_id,
        "format": fmt,
        "scale": str(scale),
    })
    images = data.get("images", {})
    url = images.get(node_id)
    if not url:
        sys.exit(f"错误：无法渲染节点 {node_id}，可能是空 Frame 或不可见节点")
    return url


def walk_tree(node, depth=0, max_depth=None):
    """递归遍历节点树，返回 (depth, id, type, name) 列表。"""
    if max_depth is not None and depth > max_depth:
        return []
    result = [(depth, node.get("id", ""), node.get("type", ""), node.get("name", ""))]
    for child in node.get("children", []):
        result.extend(walk_tree(child, depth + 1, max_depth))
    return result


def search_nodes(node, keyword):
    """按名称搜索节点，返回匹配列表。"""
    results = []
    name = node.get("name", "")
    if keyword.lower() in name.lower():
        results.append({
            "id": node.get("id"),
            "name": name,
            "type": node.get("type"),
        })
    for child in node.get("children", []):
        results.extend(search_nodes(child, keyword))
    return results


# ── CLI ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Figma REST API 轻量客户端")
    parser.add_argument("url", help="Figma 文件/节点 URL")
    parser.add_argument("--nodes", action="store_true", help="获取 URL 中 node-id 的详细属性")
    parser.add_argument("--image", action="store_true", help="下载节点截图（PNG）")
    parser.add_argument("--tree", action="store_true", help="打印完整节点树")
    parser.add_argument("--search", metavar="关键词", help="按名称搜索节点")
    parser.add_argument("--depth", type=int, default=None, help="--tree 的最大深度")
    parser.add_argument("--scale", type=int, default=2, help="截图缩放倍数（默认 2x）")
    parser.add_argument("--format", choices=["png", "svg", "pdf"], default="png", help="截图格式")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("-p", "--project", help="项目名，截图存到 projects/{项目}/screenshots/")
    args = parser.parse_args()

    pat = load_pat()
    file_key, node_id = parse_figma_url(args.url)

    if args.image:
        if not node_id:
            sys.exit("错误：截图需要 URL 中包含 node-id 参数")
        img_url = get_image_url(pat, file_key, node_id, args.format, args.scale)
        img_bytes = download_bytes(img_url)
        if args.project:
            out_dir = ROOT / "projects" / args.project / "screenshots"
            out_dir.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r'[^\w\-]', '_', node_id)
            out_path = out_dir / f"figma-{safe_name}.{args.format}"
            out_path.write_bytes(img_bytes)
            print(f"已保存: {out_path}", file=sys.stderr)
        elif args.output:
            Path(args.output).write_bytes(img_bytes)
            print(f"已保存: {args.output}", file=sys.stderr)
        else:
            sys.stdout.buffer.write(img_bytes)
        return

    if args.search:
        data = api_get(pat, f"/files/{file_key}")
        doc = data.get("document", {})
        results = search_nodes(doc, args.search)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if args.tree:
        depth_param = {"depth": str(args.depth)} if args.depth else {}
        data = api_get(pat, f"/files/{file_key}", depth_param)
        doc = data.get("document", {})
        for d, nid, ntype, name in walk_tree(doc, max_depth=args.depth):
            indent = "  " * d
            print(f"{indent}{ntype} [{nid}] {name}")
        return

    if args.nodes:
        if not node_id:
            sys.exit("错误：--nodes 需要 URL 中包含 node-id 参数")
        nodes = get_nodes(pat, file_key, node_id)
        print(json.dumps(nodes, ensure_ascii=False, indent=2))
        return

    summary = get_file_summary(pat, file_key)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
