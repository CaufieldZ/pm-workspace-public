#!/usr/bin/env python3
"""Slack MCP 客户端 —— 从 Keychain 读取 OAuth token，调用 Slack MCP HTTP 服务。

用法：
  from scripts.lib.slack_mcp import SlackMCP
  client = SlackMCP()
  result = client.call("slack_send_message", {"channel_id": "C...", "message": "hi"})

Token 管理：
  - 首次从 Keychain（Claude Code-credentials）读取 access_token + refresh_token
  - access_token 过期自动用 refresh_token 续期并回写 Keychain
  - Keychain 读取失败时尝试从环境变量 SLACK_MCP_TOKEN 获取
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

SLACK_MCP_URL = "https://mcp.slack.com/mcp"
KEYCHAIN_SERVICE = "Claude Code-credentials"
KEYCHAIN_ACCOUNT = "plugin:slack:slack"

_token_cache = None  # (access_token, expires_at)


def _read_keychain():
    """从 Keychain 读取 Claude Code 的 OAuth token JSON，提取 Slack 部分。"""
    try:
        raw = subprocess.check_output(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except subprocess.CalledProcessError:
        return None
    try:
        data = json.loads(raw)
        oauth_map = data.get("mcpOAuth", {})
        for key, val in oauth_map.items():
            if key.startswith("plugin:slack:slack"):
                return val
        return None
    except json.JSONDecodeError:
        return None


def _write_keychain(access_token, refresh_token, expires_at, scope, discovery_state):
    """回写更新后的 token 到 Keychain（保留其他 MCP 的 token 不动）。"""
    try:
        raw = subprocess.check_output(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        data = json.loads(raw)
    except subprocess.CalledProcessError:
        return False
    except json.JSONDecodeError:
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
    payload = json.dumps(data, separators=(",", ":"))
    result = subprocess.run(
        ["security", "delete-generic-password", "-s", KEYCHAIN_SERVICE],
        capture_output=True,
    )
    result = subprocess.run(
        ["security", "add-generic-password", "-s", KEYCHAIN_SERVICE,
         "-a", "Claude Key", "-w", payload, "-U"],
        capture_output=True,
    )
    return result.returncode == 0


def _refresh_token(refresh_token):
    """用 refresh_token 换新 access_token（OAuth 2.0 token refresh 标准流程）。"""
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": "1601185624273.8899143856786",
    }).encode()
    # Slack OAuth token refresh 端点（通过 MCP gateway）
    req = urllib.request.Request(
        "https://mcp.slack.com/oauth/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.load(resp)
        return result.get("access_token"), result.get("refresh_token"), result.get("expires_in", 43200)
    except Exception:
        return None, None, None


def get_token():
    """获取有效的 Slack OAuth access_token，过期则自动刷新。"""
    global _token_cache
    env_token = os.environ.get("SLACK_MCP_TOKEN")
    if env_token:
        return env_token

    # 优先用缓存
    if _token_cache:
        access_token, expires_at = _token_cache
        if time.time() + 300 < expires_at / 1000:  # 留 5 分钟余量
            return access_token

    oauth = _read_keychain()
    if not oauth:
        sys.exit("错误：无法从 Keychain 读取 Slack OAuth token，请设置 SLACK_MCP_TOKEN 环境变量")

    access_token = oauth["accessToken"]
    expires_at = oauth["expiresAt"]
    refresh_token_val = oauth.get("refreshToken")

    # 没过期直接返回
    if time.time() + 300 < expires_at / 1000:
        _token_cache = (access_token, expires_at)
        return access_token

    # 过期了，用 refresh_token 续期
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
    """调用 Slack MCP 服务器的指定工具。

    参数：
      tool_name: 工具名（如 slack_send_message）
      arguments: 参数字典

    返回：
      MCP 响应 result（已解析 JSON 或原始文本）
    """
    token = get_token()
    seen_error = False

    # 先 initialize（每个 connection 需要）
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
            # Token 可能过期（缓存不准），清除缓存重试
            global _token_cache
            _token_cache = None
            token = get_token()
            init_req.headers["Authorization"] = f"Bearer {token}"
            with urllib.request.urlopen(init_req, timeout=30) as resp:
                json.load(resp)
        else:
            raise

    # Call tool
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
    """格式化输出 MCP 结果。"""
    if isinstance(result, dict):
        return json.dumps(result, indent=2, ensure_ascii=False)
    if isinstance(result, list):
        return json.dumps(result, indent=2, ensure_ascii=False)
    return str(result)
