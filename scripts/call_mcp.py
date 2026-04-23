#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""通用 MCP 调用脚本——HTTP 和 stdio 均支持，不需要在 Claude Code 里加载 server。

用法:
  python3 scripts/call_mcp.py list <server>                          # 列出所有工具
  python3 scripts/call_mcp.py call <server> <tool> '{"key":"val"}'   # 调用工具
  python3 scripts/call_mcp.py call <server> <tool> key=val key2=val2 # 简写形式
  python3 scripts/call_mcp.py servers                                # 列出所有已配置的 server

server 名从 .mcp.json / .mcp-disabled.json / ~/.claude.json 自动读取，
MCP 关掉也能调。
"""

import json, os, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_JSON = os.path.join(ROOT, ".mcp.json")
DISABLED_JSON = os.path.join(ROOT, ".mcp-disabled.json")
CLAUDE_JSON = os.path.expanduser("~/.claude.json")

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

def http_call(url, method, params=None):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {},
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.load(resp)
    if "error" in result:
        sys.exit(f"MCP 错误：{json.dumps(result['error'], ensure_ascii=False)}")
    return result.get("result", {})


def http_init(url):
    http_call(url, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "call-mcp", "version": "0.1"},
    })


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


def cmd_list(server_name):
    cfg = get_server(server_name)
    transport = cfg.get("_transport", "stdio")

    if transport in ("http", "sse"):
        http_init(cfg["url"])
        result = http_call(cfg["url"], "tools/list")
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
    transport = cfg.get("_transport", "stdio")
    arguments = parse_args_to_json(extra_args)

    if transport in ("http", "sse"):
        http_init(cfg["url"])
        result = http_call(cfg["url"], "tools/call", {"name": tool_name, "arguments": arguments})
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
