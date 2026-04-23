#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""从钉钉闪记拉取会议纪要到项目 inputs/ 目录。

用法:
  python3 scripts/pull_meeting_notes.py "关键词" --project 项目名
  python3 scripts/pull_meeting_notes.py "关键词" --project 项目名 --list        # 只列出匹配的文档，不下载
  python3 scripts/pull_meeting_notes.py --latest --project 项目名               # 拉最新一条
  python3 scripts/pull_meeting_notes.py "关键词" -p 项目名 --with-transcript    # 保留转写原文（默认剥离）

默认只保存「全文摘要 + 决策 + 行动项」部分，转写原文剥离（噪声大、吃 token）。
如需转写（回查歧义、确认争论过程），加 --with-transcript。

直接调 dingtalk-doc MCP HTTP 接口，不需要加载 MCP server 到 Claude Code。
"""

import argparse, json, os, re, sys, urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_mcp_url():
    claude_json = os.path.expanduser("~/.claude.json")
    with open(claude_json) as f:
        d = json.load(f)
    servers = d.get("projects", {}).get(ROOT, {}).get("mcpServers", {})
    dd = servers.get("dingtalk-doc")
    if not dd:
        disabled = os.path.join(ROOT, ".mcp-disabled.json")
        if os.path.exists(disabled):
            with open(disabled) as f:
                dis = json.load(f)
            dd = dis.get("mcpServers", {}).get("dingtalk-doc")
    if not dd:
        sys.exit("错误：找不到 dingtalk-doc MCP 配置（~/.claude.json 和 .mcp-disabled.json 都没有）")
    return dd["url"]


def mcp_call(url, method_name, arguments):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": method_name, "arguments": arguments},
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.load(resp)
    if "error" in result:
        sys.exit(f"MCP 错误：{result['error']}")
    content = result.get("result", {}).get("structuredContent") or json.loads(
        result["result"]["content"][0]["text"]
    )
    return content


def mcp_init(url):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pull-meeting-notes", "version": "0.1"},
        },
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        json.load(resp)


def search_docs(url, keyword, page_size=30):
    args = {"pageSize": page_size}
    if keyword:
        args["keyword"] = keyword
    return mcp_call(url, "search_documents", args)


def get_content(url, node_id):
    return mcp_call(url, "get_document_content", {"nodeId": node_id})


def strip_transcript(markdown):
    parts = re.split(r"\n#+\s*转写原文\s*\n", markdown, maxsplit=1)
    return parts[0].rstrip() + "\n"


def save_note(markdown, title, project_dir):
    date_match = re.search(r"(\d{2})-(\d{2})", title)
    if date_match:
        month, day = date_match.groups()
        date_str = f"{datetime.now().year}-{month}-{day}"
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    safe_title = re.sub(r'[/:*?"<>|]', "-", title).strip()
    filename = f"meeting-{date_str}-{safe_title}.md"

    inputs_dir = os.path.join(project_dir, "inputs")
    os.makedirs(inputs_dir, exist_ok=True)
    path = os.path.join(inputs_dir, filename)

    with open(path, "w") as f:
        f.write(markdown)

    return path


def main():
    parser = argparse.ArgumentParser(description="从钉钉闪记拉取会议纪要")
    parser.add_argument("keyword", nargs="?", default="", help="搜索关键词")
    parser.add_argument("--project", "-p", required=True, help="项目名（projects/ 下的目录名）")
    parser.add_argument("--list", "-l", action="store_true", help="只列出匹配文档，不下载")
    parser.add_argument("--latest", action="store_true", help="拉最新一条（忽略 keyword）")
    parser.add_argument("--with-transcript", action="store_true", help="保留转写原文（默认只存摘要）")
    args = parser.parse_args()

    project_dir = os.path.join(ROOT, "projects", args.project)
    if not os.path.isdir(project_dir):
        sys.exit(f"错误：项目目录不存在 {project_dir}")

    url = get_mcp_url()
    mcp_init(url)

    keyword = "" if args.latest else args.keyword
    result = search_docs(url, keyword, page_size=1 if args.latest else 30)
    docs = result.get("documents", [])

    if not docs:
        print("未找到匹配的文档")
        return

    if args.list:
        for i, doc in enumerate(docs):
            ts = doc.get("createTime", 0)
            dt = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M") if ts else "?"
            name = doc.get("name") or doc.get("title") or "(untitled)"
            print(f"  {i + 1}. [{dt}] {name}")
            print(f"     nodeId: {doc.get('nodeId', '?')}")
        return

    docs = [d for d in docs if d.get("name") or d.get("title")]
    if not docs:
        print("未找到有效文档")
        return
    doc = docs[0]
    doc_name = doc.get("name") or doc.get("title")
    print(f"拉取: {doc_name}")
    content = get_content(url, doc["nodeId"])
    markdown = content.get("markdown", "")
    if not markdown:
        sys.exit("错误：文档内容为空")

    raw_len = len(markdown)
    if not args.with_transcript:
        markdown = strip_transcript(markdown)

    path = save_note(markdown, doc_name, project_dir)
    print(f"已保存: {path}")
    if args.with_transcript:
        print(f"字数: {raw_len}（含转写）")
    else:
        print(f"字数: {len(markdown)}（已剥离转写，原文 {raw_len}；加 --with-transcript 保留）")


if __name__ == "__main__":
    main()
