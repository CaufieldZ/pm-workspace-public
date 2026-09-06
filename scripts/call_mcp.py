#!/usr/bin/env python3
"""通用 MCP 调用脚本——HTTP 和 stdio 均支持，不需要在 Claude Code 里加载 server。

用法:
  python3 scripts/call_mcp.py list <server>                          # 列出所有工具
  python3 scripts/call_mcp.py call <server> <tool> '{"key":"val"}'   # 调用工具
  python3 scripts/call_mcp.py call <server> <tool> key=val key2=val2 # 简写形式
  python3 scripts/call_mcp.py servers                                # 列出所有已配置的 server

server 名从 .mcp.json / .mcp-disabled.json / ~/.claude.json 自动读取，
MCP 关掉也能调。配置里的凭据值用 ${VAR} 引用 .env（见 lib/env_refs.py）。
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from lib.env_refs import apply_env_file, expand_refs  # noqa: E402
from lib.oauth_keychain import read_credentials, write_credentials  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_JSON = os.path.join(ROOT, ".mcp.json")
DISABLED_JSON = os.path.join(ROOT, ".mcp-disabled.json")
CLAUDE_JSON = os.path.expanduser("~/.claude.json")
KEYCHAIN_SERVICE = "Claude Code-credentials"

apply_env_file(os.path.join(ROOT, ".env"))

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

    return expand_refs(servers)


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
    data = read_credentials()
    if not data:
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
    except (urllib.error.URLError, OSError):
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

    write_credentials(keychain_data)
    _oauth_cache[server_name] = (new_access, new_expires_at)
    return new_access, new_refresh, new_expires_at


_FAILOVER_HINTS = ("rate limit", "-429", "-401", "api key not found", "quota", "1302")


def _should_failover(code, result):
    if code in (401, 403, 429):
        return True
    err = (result or {}).get("error") or {}
    blob = f"{err.get('code','')} {err.get('message','')}".lower()
    res = (result or {}).get("result") or {}
    if res.get("isError"):
        for c in res.get("content", []):
            blob += " " + str(c.get("text", "")).lower()
    return any(h in blob for h in _FAILOVER_HINTS)


def _http_once(url, method, params, auth, session_id):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if auth:
        headers["Authorization"] = auth
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params or {},
    }).encode()
    req = urllib.request.Request(url, data=payload, headers=headers)
    code, body, resp_headers = 0, "", {}
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            code = resp.status
            body = resp.read().decode("utf-8")
            resp_headers = dict(resp.headers)
    except urllib.error.HTTPError as e:
        code = e.code
        body = e.read().decode("utf-8", "replace")
        resp_headers = dict(e.headers)
    except (urllib.error.URLError, OSError) as e:
        # 纯网络失败（timeout / connection refused / DNS）：code=0，交上层统一退出，
        # 不再抛 traceback。
        return 0, f"网络错误：{e}", {}, session_id
    ctype = resp_headers.get("Content-Type", "")
    if "text/event-stream" in ctype:
        result = _parse_sse(body)
    else:
        # 错误响应体常是 HTML（网关 502 / 登录跳转），json.loads 会抛 traceback 绕过
        # http_call 的友好退出。解析失败留空 result，交由上层按 code>=400 统一报错。
        try:
            result = json.loads(body) if body.strip() else {}
        except json.JSONDecodeError:
            result = {}
    new_sid = resp_headers.get("Mcp-Session-Id") or resp_headers.get("mcp-session-id")
    return code, body, result, new_sid


def _exit_unavailable(msg, fallback_hint=None):
    """server 不可用时统一退出：先打错误，再（若配了）打 fallback 建议。"""
    if fallback_hint:
        msg = f"{msg}\n[server 不可用] 建议改用：{fallback_hint}"
    sys.exit(msg)


def http_call(url, method, params=None, auth_header=None, fallback_auths=None,
              session_id=None, fallback_hint=None):
    """Make one JSON-RPC call. On the first call (no session_id), tries each
    auth in turn until one is not rate-limited / auth-failed. Returns
    (result_dict, working_auth, session_id) so callers can reuse the bound
    session + key for follow-up requests."""
    auths = [auth_header] + list(fallback_auths or []) if session_id is None else [auth_header]
    last_code, last_body, last_result = 0, "", {}
    for i, auth in enumerate(auths):
        code, body, result, new_sid = _http_once(url, method, params, auth, session_id)
        last_code, last_body, last_result = code, body, result
        if _should_failover(code, result) and i < len(auths) - 1:
            print(f"主 key 不可用（{code}），降级到备用 key 重试…", file=sys.stderr)
            continue
        if code == 0:  # 网络失败（timeout / connection refused / DNS）
            _exit_unavailable(f"MCP 网络不可达：{body[:200]}", fallback_hint)
        if code >= 400 and "error" not in result:
            _exit_unavailable(f"MCP HTTP {code}：{body[:200]}", fallback_hint)
        if "error" in result:
            _exit_unavailable(
                f"MCP 错误：{json.dumps(result['error'], ensure_ascii=False)}", fallback_hint)
        return result.get("result", {}), auth, (new_sid or session_id)
    if last_code == 0:
        _exit_unavailable(f"MCP 网络不可达：{last_body[:200]}", fallback_hint)
    if "error" in last_result:
        _exit_unavailable(
            f"MCP 错误：{json.dumps(last_result['error'], ensure_ascii=False)}", fallback_hint)
    _exit_unavailable(f"MCP HTTP {last_code}：{last_body[:200]}", fallback_hint)


def _parse_sse(body):
    """Extract the last JSON-RPC message from an SSE response stream."""
    last = {}
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            data = line[len("data:"):].strip()
            if data and data != "[DONE]":
                try:
                    last = json.loads(data)
                except json.JSONDecodeError:
                    pass
    return last


def http_init(url, auth_header=None, fallback_auths=None, fallback_hint=None):
    """Returns (working_auth, session_id) to reuse on follow-up calls."""
    _, auth, sid = http_call(url, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "call-mcp", "version": "0.1"},
    }, auth_header=auth_header, fallback_auths=fallback_auths, fallback_hint=fallback_hint)
    return auth, sid


# ── stdio transport ─────────────────────────────────────────────

class MCPProtocolError(Exception):
    """stdio MCP 返回 JSON-RPC error 或进程意外退出时抛出，携带原始 error dict，
    供上层决定是降级备用 key 还是直接退出。"""
    def __init__(self, error):
        self.error = error
        super().__init__(json.dumps(error, ensure_ascii=False))


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
                raise MCPProtocolError({"message": "stdio MCP 进程意外退出"})
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in msg:
                if "error" in msg:
                    raise MCPProtocolError(msg["error"])
                return msg.get("result", {})

    def call(self, method, params=None):
        return self._send(method, params or {})

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except (subprocess.SubprocessError, OSError):
            self.proc.kill()


def _env_candidates(base_env, fallback_env):
    """构造待轮试的 env 列表：首项是 base env；`_fallback_env` 里每个备份值追加一个
    仅替换该 env var 的变体。`_fallback_env` 形如 {ENV_VAR: [backup1, backup2]}。"""
    if not fallback_env:
        return [base_env]
    candidates = [base_env]
    for var, backups in fallback_env.items():
        for bk in backups:
            new_env = dict(base_env)
            new_env[var] = bk
            candidates.append(new_env)
    return candidates


def _stdio_error_is_key_failure(error):
    """stdio MCP error 是否像是 key/认证失败（值得换备用 key 重试），复用 http 的
    failover 关键词表。"""
    blob = json.dumps(error, ensure_ascii=False).lower()
    return any(h in blob for h in _FAILOVER_HINTS)


def _stdio_invoke(cfg, method, params=None):
    """跑一次 stdio MCP 调用，主 key 失败时按 `_fallback_env` 降级重试，行为对齐 http
    分支的 failover。所有候选都失败或非 key 错误则 sys.exit（与原行为一致）。"""
    command = cfg["command"]
    args = cfg.get("args", [])
    fallback_hint = cfg.get("_fallback_hint")
    candidates = _env_candidates(cfg.get("env", {}), cfg.get("_fallback_env", {}))
    for i, env in enumerate(candidates):
        mcp = None
        try:
            mcp = StdioMCP(command, args, env)
            return mcp.call(method, params or {})
        except MCPProtocolError as e:
            if i < len(candidates) - 1 and _stdio_error_is_key_failure(e.error):
                print("stdio MCP 主 key 不可用，降级到备用 key 重试…", file=sys.stderr)
                continue
            _exit_unavailable(
                f"MCP 错误：{json.dumps(e.error, ensure_ascii=False)}", fallback_hint)
        finally:
            if mcp is not None:
                mcp.close()


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
    headers = cfg.get("headers") or {}
    return headers.get("Authorization")


def _get_fallback_auths(cfg):
    fb = cfg.get("_fallback_auth") or []
    return [fb] if isinstance(fb, str) else list(fb)


def cmd_list(server_name):
    cfg = get_server(server_name)
    cfg["_name"] = server_name
    transport = cfg.get("_transport", "stdio")
    auth = _get_auth_header(cfg)
    fallbacks = _get_fallback_auths(cfg)
    hint = cfg.get("_fallback_hint")

    if transport in ("http", "sse"):
        auth, sid = http_init(cfg["url"], auth_header=auth, fallback_auths=fallbacks,
                              fallback_hint=hint)
        result, _, _ = http_call(cfg["url"], "tools/list", auth_header=auth, session_id=sid,
                                 fallback_hint=hint)
    else:
        result = _stdio_invoke(cfg, "tools/list")

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
    fallbacks = _get_fallback_auths(cfg)
    hint = cfg.get("_fallback_hint")

    if transport in ("http", "sse"):
        auth, sid = http_init(cfg["url"], auth_header=auth, fallback_auths=fallbacks,
                              fallback_hint=hint)
        result, _, _ = http_call(cfg["url"], "tools/call", {"name": tool_name, "arguments": arguments}, auth_header=auth, session_id=sid, fallback_hint=hint)
    else:
        result = _stdio_invoke(cfg, "tools/call", {"name": tool_name, "arguments": arguments})

    print(format_result(result))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd in ("--help", "-h", "help"):
        print("用法: call_mcp.py servers | list <server> | call <server> <tool> [k=v...]")
        sys.exit(0)

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
