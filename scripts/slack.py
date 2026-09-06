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

# route-log: 调用埋点（scripts/lib/route_log.py）
import pathlib as _pl
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("slack"))

import json
import os
import sys
import time
import urllib.request

from lib.oauth_keychain import read_credentials, write_credentials  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Slack MCP 客户端（原 scripts/lib/slack_mcp.py，2026-05 内联以收敛 lib/ 边界）
#
# Token 管理：
#   - 首次从 Keychain（Claude Code-credentials）读取 access_token + refresh_token
#   - access_token 过期自动用 refresh_token 续期并回写 Keychain
#   - Keychain 读取失败时尝试从环境变量 SLACK_MCP_TOKEN 获取
# ─────────────────────────────────────────────────────────────────────────────

SLACK_MCP_URL = "https://mcp.slack.com/mcp"
KEYCHAIN_ACCOUNT = "plugin:slack:slack"

_token_cache = None  # (access_token, expires_at)


def _read_keychain():
    data = read_credentials()
    if not data:
        return None
    oauth_map = data.get("mcpOAuth", {})
    for key, val in oauth_map.items():
        if key.startswith("plugin:slack:slack"):
            return val
    return None


def _write_keychain(access_token, refresh_token, expires_at, scope, discovery_state):
    data = read_credentials()
    if not data:
        return False

    oauth_map = data.get("mcpOAuth", {})
    for key in list(oauth_map.keys()):
        if key.startswith("plugin:slack:slack"):
            oauth_map[key]["accessToken"] = access_token
            oauth_map[key]["refreshToken"] = refresh_token
            oauth_map[key]["expiresAt"] = expires_at
            oauth_map[key]["scope"] = scope
            oauth_map[key]["discoveryState"] = discovery_state
            break

    data["mcpOAuth"] = oauth_map
    return write_credentials(data)


def _refresh_token(refresh_token):
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": "1601185624273.8899143856786",
    }).encode()
    req = urllib.request.Request(
        "https://mcp.slack.com/oauth/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.load(resp)
        return result.get("access_token"), result.get("refresh_token"), result.get("expires_in", 43200)
    except (urllib.error.URLError, OSError):
        return None, None, None


def get_token():
    global _token_cache
    env_token = os.environ.get("SLACK_MCP_TOKEN")
    if env_token:
        return env_token

    if _token_cache:
        access_token, expires_at = _token_cache
        if time.time() + 300 < expires_at / 1000:
            return access_token

    oauth = _read_keychain()
    if not oauth:
        sys.exit("错误：无法从 Keychain 读取 Slack OAuth token，请设置 SLACK_MCP_TOKEN 环境变量")

    access_token = oauth["accessToken"]
    expires_at = oauth["expiresAt"]
    refresh_token_val = oauth.get("refreshToken")

    if time.time() + 300 < expires_at / 1000:
        _token_cache = (access_token, expires_at)
        return access_token

    if not refresh_token_val:
        sys.exit("错误：Slack token 已过期且无 refresh_token")

    new_access, new_refresh, expires_in = _refresh_token(refresh_token_val)
    if not new_access:
        sys.exit("错误：Slack token 刷新失败，请重新授权 Slack 插件")

    new_expires_at = int((time.time() + expires_in) * 1000)
    _write_keychain(
        new_access,
        new_refresh or refresh_token_val,
        new_expires_at,
        oauth.get("scope", ""),
        oauth.get("discoveryState", {}),
    )
    _token_cache = (new_access, new_expires_at)
    return new_access


def call_mcp(tool_name, arguments=None):
    token = get_token()

    init_payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "slack-cli", "version": "0.1"},
        },
    }).encode()
    init_req = urllib.request.Request(
        SLACK_MCP_URL,
        data=init_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urllib.request.urlopen(init_req, timeout=30) as resp:
            json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            global _token_cache
            _token_cache = None
            token = get_token()
            init_req.headers["Authorization"] = f"Bearer {token}"
            with urllib.request.urlopen(init_req, timeout=30) as resp:
                json.load(resp)
        else:
            raise

    call_payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {},
        },
    }).encode()
    call_req = urllib.request.Request(
        SLACK_MCP_URL,
        data=call_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    with urllib.request.urlopen(call_req, timeout=60) as resp:
        result = json.load(resp)

    if "error" in result:
        err = result["error"]
        sys.exit(f"MCP 错误：{json.dumps(err, ensure_ascii=False)}")

    content = result.get("result", {}).get("content", [])
    for c in content:
        if c.get("type") == "text":
            try:
                return json.loads(c["text"])
            except (json.JSONDecodeError, TypeError):
                return c["text"]
    return result.get("result", {})


def format_output(result):
    if isinstance(result, dict):
        return json.dumps(result, indent=2, ensure_ascii=False)
    if isinstance(result, list):
        return json.dumps(result, indent=2, ensure_ascii=False)
    return str(result)


# ─────────────────────────────────────────────────────────────────────────────
# CLI 命令
# ─────────────────────────────────────────────────────────────────────────────


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
        result = call_mcp("slack_update_canvas", params)
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
    if message == "-f" and len(args) > 3:
        with open(args[2]) as f:
            message = f.read()
        post_at = int(args[3])
    else:
        post_at = int(args[2])
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
    elif cmd in ("help", "--help", "-h"):
        print(__doc__)
    else:
        print(f"未知命令: {cmd}")
        print(f"可用: {', '.join(sorted(handlers.keys()))} / help")
        sys.exit(1)


if __name__ == "__main__":
    main()
