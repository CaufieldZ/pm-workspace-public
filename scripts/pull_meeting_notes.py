#!/usr/bin/env python3
"""从钉钉闪记拉取会议纪要到项目 inputs/ 目录。

会议纪要 = 标题匹配 `^(纪要_)?MM-DD 内部会议[: ：]?...` 的文档。

用法:
  # 列过去一个月所有会议（默认行为）
  python3 scripts/pull_meeting_notes.py -p 项目名 --list

  # 列过去 N 天 / 自定义时间窗口
  python3 scripts/pull_meeting_notes.py -p 项目名 --list --days 14
  python3 scripts/pull_meeting_notes.py -p 项目名 --list --since 2026-04-01 --until 2026-05-06

  # 关键词过滤（标题或内容匹配）
  python3 scripts/pull_meeting_notes.py "授信" -p 项目名 --list

  # 拉最新一场会议
  python3 scripts/pull_meeting_notes.py -p 项目名 --latest

  # 拉指定一场（按 nodeId）
  python3 scripts/pull_meeting_notes.py -p 项目名 --node-id <nodeId>

  # 批量拉时间窗口内所有匹配会议
  python3 scripts/pull_meeting_notes.py -p 项目名 --download-all
  python3 scripts/pull_meeting_notes.py "授信" -p 项目名 --download-all

  # 保留转写原文（默认剥离，噪声大）
  python3 scripts/pull_meeting_notes.py -p 项目名 --latest --with-transcript

默认只保存「全文摘要 + 决策 + 行动项」部分，转写原文剥离。
直接调 dingtalk-doc MCP HTTP 接口，不需要加载 MCP server 到 Claude Code。
"""

# route-log: 调用埋点（scripts/lib/route_log.py）
import pathlib as _pl
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("pull_meeting_notes"))

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEETING_RE = re.compile(r"^(纪要_)?(\d{2})-(\d{2})\s*(?:内部会议)?[:：]?\s*(.*)$")


def get_mcp_url():
    claude_json = os.path.expanduser("~/.claude.json")
    try:
        with open(claude_json) as f:
            d = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"错误：读取 {claude_json} 失败 ({e})")
    servers = d.get("projects", {}).get(ROOT, {}).get("mcpServers", {})
    dd = servers.get("dingtalk-doc")
    if not dd:
        disabled = os.path.join(ROOT, ".mcp-disabled.json")
        if os.path.exists(disabled):
            try:
                with open(disabled) as f:
                    dis = json.load(f)
            except (OSError, json.JSONDecodeError):
                dis = {}
            dd = dis.get("mcpServers", {}).get("dingtalk-doc")
    if not dd:
        sys.exit("错误：找不到 dingtalk-doc MCP 配置")
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
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.load(resp)
    except urllib.error.URLError as e:
        sys.exit(f"错误：MCP 调用失败 ({e})\n  检查钉钉 MCP 服务是否可用")
    if "error" in result:
        sys.exit(f"MCP 错误：{result['error']}")
    structured = result.get("result", {}).get("structuredContent")
    if structured:
        return structured
    # 回退解析 content[0].text：MCP 可能返回空 content / 缺字段，逐层守卫，不让裸 IndexError 冒出
    try:
        return json.loads(result["result"]["content"][0]["text"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
        sys.exit(f"错误：MCP 返回结构异常，无法解析内容（{e}）\n  原始返回：{str(result)[:300]}")


def mcp_init(url):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pull-meeting-notes", "version": "0.2"},
        },
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            json.load(resp)
    except urllib.error.URLError as e:
        sys.exit(f"错误：MCP 初始化失败 ({e})\n  检查钉钉 MCP 服务是否可用")


def search_window(url, since_ms, until_ms, keyword="", max_pages=20):
    """分页拉取时间窗口内所有文档（最多 max_pages * 30 条）。"""
    docs = []
    page_token = None
    for _ in range(max_pages):
        args = {"pageSize": 30}
        if since_ms is not None:
            args["createdTimeFrom"] = since_ms
        if until_ms is not None:
            args["createdTimeTo"] = until_ms
        if keyword:
            args["keyword"] = keyword
        if page_token:
            args["pageToken"] = page_token
        result = mcp_call(url, "search_documents", args)
        page_docs = result.get("documents", [])
        docs.extend(page_docs)
        page_token = result.get("nextPageToken")
        if not page_token or not page_docs:
            break
    return docs


def filter_meeting_notes(docs):
    """匹配会议纪要 pattern + 去重（同 MM-DD + topic，优先「纪要_」前缀版）。"""
    by_key = {}
    for d in docs:
        name = d.get("name") or d.get("title") or ""
        m = MEETING_RE.match(name)
        if not m:
            continue
        _, mm, dd, topic = m.groups()
        key = (mm, dd, topic.strip())
        prev = by_key.get(key)
        if prev is None:
            by_key[key] = d
            continue
        prev_has = (prev.get("name") or "").startswith("纪要_")
        curr_has = name.startswith("纪要_")
        if curr_has and not prev_has:
            by_key[key] = d
        elif curr_has == prev_has and d.get("createTime", 0) > prev.get("createTime", 0):
            by_key[key] = d
    out = list(by_key.values())
    out.sort(key=lambda x: x.get("createTime", 0), reverse=True)
    return out


def get_content(url, node_id):
    return mcp_call(url, "get_document_content", {"nodeId": node_id})


def strip_transcript(markdown):
    parts = re.split(r"\n#+\s*转写原文\s*\n", markdown, maxsplit=1)
    return parts[0].rstrip() + "\n"


def slugify_topic(topic):
    """把 topic 截短做文件名后缀（同日多场会议时使用）。"""
    s = re.sub(r'[/:*?"<>|\s]', "", topic)
    return s[:20]


def save_note(markdown, doc_name, project_dir, force_slug=False):
    """文件名 meeting-YYYY-MM-DD.md，同日撞名加 topic slug 后缀。"""
    m = MEETING_RE.match(doc_name)
    if m:
        _, mm, dd, topic = m.groups()
        date_str = f"{datetime.now().year}-{mm}-{dd}"
        slug = slugify_topic(topic)
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        slug = ""

    inputs_dir = os.path.join(project_dir, "inputs", "meetings")
    os.makedirs(inputs_dir, exist_ok=True)

    base = f"meeting-{date_str}.md"
    path = os.path.join(inputs_dir, base)
    if os.path.exists(path) or force_slug:
        if slug:
            path = os.path.join(inputs_dir, f"meeting-{date_str}-{slug}.md")
        else:
            path = os.path.join(inputs_dir, f"meeting-{date_str}-2.md")

    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    return path


def fetch_and_save(url, doc, project_dir, with_transcript=False, force_slug=False):
    name = doc.get("name") or doc.get("title")
    content = get_content(url, doc["nodeId"])
    markdown = content.get("markdown", "")
    if not markdown:
        return None, 0
    raw_len = len(markdown)
    if not with_transcript:
        markdown = strip_transcript(markdown)
    path = save_note(markdown, name, project_dir, force_slug=force_slug)
    return path, raw_len


def parse_date(s):
    return int(datetime.strptime(s, "%Y-%m-%d").timestamp() * 1000)


def main():
    parser = argparse.ArgumentParser(description="从钉钉闪记拉取会议纪要")
    parser.add_argument("keyword", nargs="?", default="", help="关键词过滤（标题/内容）")
    parser.add_argument("--project", "-p", required=True, help="项目名（projects/ 下目录）")
    parser.add_argument("--list", "-l", action="store_true", help="列出匹配会议，不下载")
    parser.add_argument("--latest", action="store_true", help="拉最新一场会议")
    parser.add_argument("--node-id", help="按 nodeId 拉指定一场会议")
    parser.add_argument("--download-all", action="store_true", help="批量下载窗口内所有匹配会议")
    parser.add_argument("--days", type=int, default=30, help="时间窗口（默认过去 30 天）")
    parser.add_argument("--since", help="起始日期 YYYY-MM-DD（覆盖 --days）")
    parser.add_argument("--until", help="截止日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--with-transcript", action="store_true", help="保留转写原文")
    args = parser.parse_args()

    project_dir = os.path.join(ROOT, "projects", args.project)
    if not os.path.isdir(project_dir):
        sys.exit(f"错误：项目目录不存在 {project_dir}")

    url = get_mcp_url()
    mcp_init(url)

    # node-id 直接拉
    if args.node_id:
        meta = mcp_call(url, "get_document_info", {"nodeId": args.node_id})
        doc = {"nodeId": args.node_id, "name": meta.get("name") or meta.get("title", "")}
        path, raw_len = fetch_and_save(url, doc, project_dir, args.with_transcript)
        print(f"已保存: {path}（原文 {raw_len} 字）")
        return

    # 时间窗口
    # --until 含当天：parse_date 取零点，截止补到 23:59:59，否则当天白天创建的纪要被排除
    until_ms = parse_date(args.until) + 86_399_000 if args.until else int(datetime.now().timestamp() * 1000)
    if args.since:
        since_ms = parse_date(args.since)
    else:
        since_ms = int((datetime.now() - timedelta(days=args.days)).timestamp() * 1000)

    docs = search_window(url, since_ms, until_ms, args.keyword)
    meetings = filter_meeting_notes(docs)

    if not meetings:
        print("未找到匹配会议")
        return

    if args.latest:
        doc = meetings[0]
        path, raw_len = fetch_and_save(url, doc, project_dir, args.with_transcript)
        print(f"拉取: {doc.get('name')}")
        print(f"已保存: {path}（原文 {raw_len} 字）")
        return

    if args.list or not args.download_all:
        print(f"窗口内会议纪要 {len(meetings)} 场：")
        for i, d in enumerate(meetings, 1):
            ts = d.get("createTime", 0)
            dt = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M")
            print(f"  {i:2}. [{dt}] {d.get('name') or d.get('title')}")
            print(f"       nodeId: {d.get('nodeId')}")
        if not args.list:
            print("\n（加 --download-all 批量下载，或 --node-id <id> 拉指定一场）")
        return

    # download-all
    saved, skipped = [], []
    for d in meetings:
        name = d.get("name") or d.get("title", "")
        # 同日多场触发 slug 后缀
        _cur_m = MEETING_RE.match(name)
        _cur_day = _cur_m.groups()[1:3] if _cur_m else None
        same_day = sum(
            1 for x in meetings
            if (_xm := MEETING_RE.match(x.get("name") or x.get("title") or ""))
            and _xm.groups()[1:3] == _cur_day
        ) if _cur_day else 1
        force_slug = same_day > 1
        path, raw_len = fetch_and_save(url, d, project_dir, args.with_transcript, force_slug)
        if path:
            saved.append((path, name, raw_len))
            print(f"  ✓ {os.path.basename(path)}  ({name})")
        else:
            skipped.append(name)
    print(f"\n下载完成：{len(saved)} 场，跳过 {len(skipped)} 场")


if __name__ == "__main__":
    main()
