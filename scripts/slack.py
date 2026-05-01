#!/usr/bin/env python3
"""Slack CLI —— 调用 Slack MCP，不加载 MCP server 到 Claude Code。

用法:
  # 发送消息
  python3 scripts/slack.py send <channel_id> <message>
  python3 scripts/slack.py send <channel_id> -f file.md      # 从文件读消息
  python3 scripts/slack.py send <channel_id> --thread <ts>    # 回复到线程

  # 读取消息
  python3 scripts/slack.py read <channel_id> [--limit 20] [--oldest ts] [--latest ts]

  # 读取线程
  python3 scripts/slack.py thread <channel_id> <message_ts> [--limit 20]

  # 搜索
  python3 scripts/slack.py search channels <query>
  python3 scripts/slack.py search users <query>
  python3 scripts/slack.py search messages <query> [--public-only]

  # Canvas
  python3 scripts/slack.py canvas create <title> <file.md>   # 从文件读 markdown 内容
  python3 scripts/slack.py canvas read <canvas_id>
  python3 scripts/slack.py canvas update <canvas_id> <action> <content> [--section id]

  # 草稿
  python3 scripts/slack.py draft <channel_id> <message>

  # 定时消息
  python3 scripts/slack.py schedule <channel_id> <message> <unix_timestamp>

  # 读取用户信息
  python3 scripts/slack.py user [user_id]

Channel ID 也可以是 user_id（用于发 DM）。

环境变量:
  SLACK_MCP_TOKEN — 手动指定 token（跳过 Keychain 读取）
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.slack_mcp import call_mcp, format_output


def cmd_send(args):
    channel_id = args[0]
    if args[1] == "-f":
        with open(args[2]) as f:
            message = f.read()
    else:
        message = args[1]
    params = {"channel_id": channel_id, "message": message}
    for i, a in enumerate(args):
        if a == "--thread" and i + 1 < len(args):
            params["thread_ts"] = args[i + 1]
            break
    result = call_mcp("slack_send_message", params)
    print(format_output(result))


def cmd_read(args):
    channel_id = args[0]
    params = {"channel_id": channel_id}
    i = 1
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            params["limit"] = int(args[i + 1])
            i += 2
        elif args[i] == "--oldest" and i + 1 < len(args):
            params["oldest"] = args[i + 1]
            i += 2
        elif args[i] == "--latest" and i + 1 < len(args):
            params["latest"] = args[i + 1]
            i += 2
        elif args[i] == "--concise":
            params["response_format"] = "concise"
            i += 1
        else:
            i += 1
    result = call_mcp("slack_read_channel", params)
    print(format_output(result))


def cmd_thread(args):
    channel_id = args[0]
    message_ts = args[1]
    params = {"channel_id": channel_id, "message_ts": message_ts}
    i = 2
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            params["limit"] = int(args[i + 1])
            i += 2
        else:
            i += 1
    result = call_mcp("slack_read_thread", params)
    print(format_output(result))


def cmd_search(args):
    sub = args[0]
    query = args[1] if len(args) > 1 else ""

    if sub == "channels":
        result = call_mcp("slack_search_channels", {"query": query})
        print(format_output(result))

    elif sub == "users":
        result = call_mcp("slack_search_users", {"query": query})
        print(format_output(result))

    elif sub == "messages":
        params = {"query": query}
        for i, a in enumerate(args):
            if a == "--public-only":
                pass  # 用 slack_search_public
        if "--public-only" in args:
            result = call_mcp("slack_search_public", params)
        else:
            result = call_mcp("slack_search_public_and_private", params)
        print(format_output(result))

    elif sub == "all":
        params = {"query": query}
        result = call_mcp("slack_search_public_and_private", params)
        print(format_output(result))

    else:
        sys.exit(f"未知搜索类型: {sub}，可选: channels / users / messages / all")


def cmd_canvas(args):
    action = args[0]

    if action == "create":
        title = args[1]
        with open(args[2]) as f:
            content = f.read()
        result = call_mcp("slack_create_canvas", {"title": title, "content": content})
        print(format_output(result))

    elif action == "read":
        canvas_id = args[1]
        result = call_mcp("slack_read_canvas", {"canvas_id": canvas_id})
        print(format_output(result))

    elif action == "update":
        canvas_id = args[1]
        update_action = args[2]
        content = args[3]
        if content == "-f" and len(args) > 4:
            with open(args[4]) as f:
                content = f.read()
        params = {"canvas_id": canvas_id, "action": update_action, "content": content}
        for i, a in enumerate(args):
            if a == "--section" and i + 1 < len(args):
                params["section_id"] = args[i + 1]
                break
        result = call_mcp("slack_update_canvas", **params)
        print(format_output(result))

    else:
        sys.exit(f"未知 canvas 操作: {action}，可选: create / read / update")


def cmd_draft(args):
    channel_id = args[0]
    message = args[1]
    if message == "-f" and len(args) > 2:
        with open(args[2]) as f:
            message = f.read()
    params = {"channel_id": channel_id, "message": message}
    for i, a in enumerate(args):
        if a == "--thread" and i + 1 < len(args):
            params["thread_ts"] = args[i + 1]
            break
    result = call_mcp("slack_send_message_draft", params)
    print(format_output(result))


def cmd_schedule(args):
    channel_id = args[0]
    message = args[1]
    post_at = int(args[2])
    if message == "-f" and len(args) > 3:
        with open(args[3]) as f:
            message = f.read()
    params = {"channel_id": channel_id, "message": message, "post_at": post_at}
    result = call_mcp("slack_schedule_message", params)
    print(format_output(result))


def cmd_user(args):
    params = {}
    if args and args[0] not in ("--concise",):
        params["user_id"] = args[0]
    result = call_mcp("slack_read_user_profile", params)
    print(format_output(result))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    rest = sys.argv[2:]

    handlers = {
        "send": cmd_send,
        "read": cmd_read,
        "thread": cmd_thread,
        "search": cmd_search,
        "canvas": cmd_canvas,
        "draft": cmd_draft,
        "schedule": cmd_schedule,
        "user": cmd_user,
    }

    if cmd in handlers:
        if not rest and cmd not in ("user",):
            sys.exit(f"用法: python3 scripts/slack.py {cmd} <参数...>")
        handlers[cmd](rest)
    elif cmd == "help":
        print(__doc__)
    else:
        print(f"未知命令: {cmd}")
        print(f"可用: {', '.join(sorted(handlers.keys()))} / help")
        sys.exit(1)


if __name__ == "__main__":
    main()
