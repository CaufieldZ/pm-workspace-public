#!/usr/bin/env python3
"""通用 MCP 调用脚本——HTTP 和 stdio 均支持，不需要在 Claude Code 里加载 server。

用法:
  python3 scripts/call_mcp.py list <server>                          # 列出所有工具
  python3 scripts/call_mcp.py call <server> <tool> '{"key":"val"}'   # 调用工具
  python3 scripts/call_mcp.py call <server> <tool> key=val key2=val2 # 简写形式
  python3 scripts/call_mcp.py servers                                # 列出所有已配置的 server

server 名从 .mcp.json / .mcp-disabled.json / ~/.claude.json 自动读取，
MCP 关掉也能调。
"""

import json, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_JSON = os.path.join(ROOT, ".mcp.json")
DISABLED_JSON = os.path.join(ROOT, ".mcp-disabled.json")
CLAUDE_JSON = os.path.expanduser("~/.claude.json")
KEYCHAIN_SERVICE = "Claude Code-credentials"

_oauth_cache = {}  # {server_name: (access_token, expires_at)}

# ── config loading ──────────────────────────────────────────────

def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def all_servers():
    """Return {name: config_dict} for every known MCP server."""
    servers = {}

    for src in (MCP_JSON, DISABLED_JSON):
        d = load_json(src)
        for k, v in d.get("mcpServers", {}).items():
            if k not in servers:
                cfg = dict(v)
                source = cfg.pop("__source", None)
                if "url" in cfg or source in ("http", "sse"):
                    cfg["_transport"] = cfg.get("type", source or "http")
                elif "command" in cfg:
                    cfg["_transport"] = "stdio"
                servers[k] = cfg

    d = load_json(CLAUDE_JSON)
    for k, v in d.get("projects", {}).get(ROOT, {}).get("mcpServers", {}).items():
        if k not in servers:
            cfg = dict(v)
            cfg.pop("__source", None)
            cfg["_transport"] = cfg.get("type", "http")
            servers[k] = cfg

    return servers


def get_server(name):
    servers = all_servers()
    if name not in servers:
        print(f"错误：找不到 server「{name}」", file=sys.stderr)
        print(f"可用: {', '.join(sorted(servers.keys()))}", file=sys.stderr)
        sys.exit(1)
    return servers[name]


# ── HTTP transport ──────────────────────────────────────────────

def _get_oauth_token(server_name, oauth_cfg):
    """Get OAuth access token from Keychain for an MCP server.
    Returns (token, None) or exits on failure.
    """
    global _oauth_cache
    now = time.time()

    if server_name in _oauth_cache:
        token, expires_at = _oauth_cache[server_name]
        if expires_at is None or now + 300 < expires_at / 1000:
            return token

    key = oauth_cfg.get("keychainKey", server_name)
    try:
        raw = subprocess.check_output(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        data = json.loads(raw)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        sys.exit(f"错误：无法从 Keychain 读取 {server_name} OAuth token")

    oauth_map = data.get("mcpOAuth", {})
    for k, v in oauth_map.items():
        if key in k or k.startswith(f"plugin:{key}") or k == key:
            token = v["accessToken"]
            expires_at = v.get("expiresAt", 0)
            if now + 300 < expires_at / 1000:
                _oauth_cache[server_name] = (token, expires_at)
                return token
            # Token expired, try refresh
            refresh_token = v.get("refreshToken")
            if refresh_token:
                new_token, new_refresh, new_expires_at = _refresh_oauth(
                    server_name, oauth_cfg, refresh_token, v, data
                )
                if new_token:
                    return new_token
            sys.exit(f"错误：{server_name} OAuth token 已过期且刷新失败")

    sys.exit(f"错误：Keychain 中未找到 {server_name} 的 OAuth token")


def _refresh_oauth(server_name, oauth_cfg, refresh_token, oauth_entry, keychain_data):
    """Refresh OAuth token and write back to Keychain."""
    url = oauth_cfg.get("tokenUrl", "https://mcp.slack.com/oauth/token")
    client_id = oauth_cfg.get("clientId", "")
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.load(resp)
    except Exception:
        return None, None, None

    new_access = result.get("access_token")
    new_refresh = result.get("refresh_token", refresh_token)
    expires_in = result.get("expires_in", 43200)
    if not new_access:
        return None, None, None

    new_expires_at = int((time.time() + expires_in) * 1000)
    oauth_entry["accessToken"] = new_access
    oauth_entry["refreshToken"] = new_refresh
    oauth_entry["expiresAt"] = new_expires_at

    oauth_map = keychain_data.get("mcpOAuth", {})
    for k in oauth_map:
        if k == oauth_entry.get("serverName") or server_name in k:
            oauth_map[k] = oauth_entry
            break
    keychain_data["mcpOAuth"] = oauth_map

    payload = json.dumps(keychain_data, separators=(",", ":"))
    subprocess.run(
        ["security", "delete-generic-password", "-s", KEYCHAIN_SERVICE],
        capture_output=True,
    )
    subprocess.run(
        ["security", "add-generic-password", "-s", KEYCHAIN_SERVICE,
         "-a", "Claude Key", "-w", payload, "-U"],
        capture_output=True,
    )
    _oauth_cache[server_name] = (new_access, new_expires_at)
    return new_access, new_refresh, new_expires_at


def http_call(url, method, params=None, auth_header=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if auth_header:
        headers["Authorization"] = auth_header
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {},
    }).encode()
    req = urllib.request.Request(url, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.load(resp)
    if "error" in result:
        sys.exit(f"MCP 错误：{json.dumps(result['error'], ensure_ascii=False)}")
    return result.get("result", {})


def http_init(url, auth_header=None):
    http_call(url, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "call-mcp", "version": "0.1"},
    }, auth_header=auth_header)


# ── stdio transport ─────────────────────────────────────────────

class StdioMCP:
    def __init__(self, command, args, env=None):
        full_env = dict(os.environ)
        if env:
            full_env.update(env)
        self.proc = subprocess.Popen(
            [command] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=full_env,
        )
        self._id = 0
        self._init()

    def _init(self):
        self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "call-mcp", "version": "0.1"},
        })
        self._send("notifications/initialized", None, notify=True)

    def _send(self, method, params, notify=False):
        self._id += 1
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            msg["id"] = self._id
        line = json.dumps(msg) + "\n"
        self.proc.stdin.write(line.encode())
        self.proc.stdin.flush()
        if notify:
            return None
        return self._read()

    def _read(self):
        while True:
            line = self.proc.stdout.readline()
            if not line:
                sys.exit("错误：stdio MCP 进程意外退出")
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in msg:
                if "error" in msg:
                    sys.exit(f"MCP 错误：{json.dumps(msg['error'], ensure_ascii=False)}")
                return msg.get("result", {})

    def call(self, method, params=None):
        return self._send(method, params or {})

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


# ── tool result formatting ──────────────────────────────────────

def format_result(result):
    structured = result.get("structuredContent")
    if structured:
        return json.dumps(structured, indent=2, ensure_ascii=False)
    content = result.get("content", [])
    parts = []
    for c in content:
        if c.get("type") == "text":
            try:
                parsed = json.loads(c["text"])
                parts.append(json.dumps(parsed, indent=2, ensure_ascii=False))
            except (json.JSONDecodeError, TypeError):
                parts.append(c["text"])
    return "\n".join(parts) if parts else json.dumps(result, indent=2, ensure_ascii=False)


# ── CLI ─────────────────────────────────────────────────────────

def parse_args_to_json(args):
    if not args:
        return {}
    if len(args) == 1:
        try:
            return json.loads(args[0])
        except json.JSONDecodeError:
            pass
    result = {}
    for a in args:
        if "=" in a:
            k, v = a.split("=", 1)
            try:
                v = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                pass
            result[k] = v
        else:
            try:
                return json.loads(a)
            except json.JSONDecodeError:
                sys.exit(f"错误：无法解析参数「{a}」，用 key=value 或 JSON 格式")
    return result


def cmd_servers():
    for name, cfg in sorted(all_servers().items()):
        transport = cfg.get("_transport", "?")
        url = cfg.get("url", cfg.get("command", ""))
        if isinstance(url, str) and len(url) > 60:
            url = url[:57] + "..."
        print(f"  {name:<20} {transport:<6} {url}")


def _get_auth_header(cfg):
    oauth = cfg.get("oauth")
    if oauth:
        token = _get_oauth_token(cfg.get("_name", ""), oauth)
        return f"Bearer {token}"
    return None


def cmd_list(server_name):
    cfg = get_server(server_name)
    cfg["_name"] = server_name
    transport = cfg.get("_transport", "stdio")
    auth = _get_auth_header(cfg)

    if transport in ("http", "sse"):
        http_init(cfg["url"], auth_header=auth)
        result = http_call(cfg["url"], "tools/list", auth_header=auth)
    else:
        mcp = StdioMCP(cfg["command"], cfg.get("args", []), cfg.get("env"))
        try:
            result = mcp.call("tools/list")
        finally:
            mcp.close()

    tools = result.get("tools", [])
    for t in tools:
        desc = (t.get("description") or "")[:60].replace("\n", " ")
        print(f"  {t['name']:<40} {desc}")
    print(f"\n共 {len(tools)} 个工具")


def cmd_call(server_name, tool_name, extra_args):
    cfg = get_server(server_name)
    cfg["_name"] = server_name
    transport = cfg.get("_transport", "stdio")
    arguments = parse_args_to_json(extra_args)
    auth = _get_auth_header(cfg)

    if transport in ("http", "sse"):
        http_init(cfg["url"], auth_header=auth)
        result = http_call(cfg["url"], "tools/call", {"name": tool_name, "arguments": arguments}, auth_header=auth)
    else:
        mcp = StdioMCP(cfg["command"], cfg.get("args", []), cfg.get("env"))
        try:
            result = mcp.call("tools/call", {"name": tool_name, "arguments": arguments})
        finally:
            mcp.close()

    print(format_result(result))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "servers":
        cmd_servers()
    elif cmd == "list":
        if len(sys.argv) < 3:
            sys.exit("用法: call_mcp.py list <server>")
        cmd_list(sys.argv[2])
    elif cmd == "call":
        if len(sys.argv) < 4:
            sys.exit("用法: call_mcp.py call <server> <tool> [args...]")
        cmd_call(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        print(f"未知命令: {cmd}")
        print("可用: servers | list <server> | call <server> <tool> [args]")
        sys.exit(1)


if __name__ == "__main__":
    main()
