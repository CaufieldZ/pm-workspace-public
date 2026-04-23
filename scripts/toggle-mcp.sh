#!/usr/bin/env bash
# toggle-mcp.sh — 按需启用/禁用 MCP server，省上下文 token
# 用法:
#   ./scripts/toggle-mcp.sh status              # 查看所有 server 状态
#   ./scripts/toggle-mcp.sh on  figma sensors    # 启用指定 server
#   ./scripts/toggle-mcp.sh off figma dingtalk-a1 dingtalk-doc  # 禁用指定 server
#   ./scripts/toggle-mcp.sh only sensors confluence  # 只保留这些，其余全禁用
#
# 机制：stdio server 在 .mcp.json / .mcp-disabled.json 间搬运；
#       HTTP server 在 ~/.claude.json 项目级 mcpServers 与 .mcp-disabled.json 间搬运。
# 改完需重启 Claude Code 生效。

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ACTION="${1:-status}"
shift 2>/dev/null || true

python3 - "$ROOT" "$ACTION" "$@" << 'PYEOF'
import json, sys, os, copy

root = sys.argv[1]
action = sys.argv[2]
targets = sys.argv[3:]

MCP = os.path.join(root, ".mcp.json")
DISABLED = os.path.join(root, ".mcp-disabled.json")
CLAUDE_JSON = os.path.expanduser("~/.claude.json")
PROJECT_KEY = root

def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def get_claude_json_servers():
    d = load_json(CLAUDE_JSON)
    return d.get("projects", {}).get(PROJECT_KEY, {}).get("mcpServers", {})

def set_claude_json_servers(servers):
    d = load_json(CLAUDE_JSON)
    d.setdefault("projects", {}).setdefault(PROJECT_KEY, {})["mcpServers"] = servers
    save_json(CLAUDE_JSON, d)

mcp = load_json(MCP)
mcp.setdefault("mcpServers", {})
disabled = load_json(DISABLED)
disabled.setdefault("mcpServers", {})
http_servers = get_claude_json_servers()

TOKEN_ESTIMATE = {
    "figma": "~15K",
    "dingtalk-doc": "~12K",
    "dingtalk-a1": "~1K",
    "sensors": "~6K",
    "confluence": "~3K",
    "firecrawl": "~6K",
}

def all_active():
    return {**{k: "stdio" for k in mcp["mcpServers"]},
            **{k: http_servers[k].get("type", "http") for k in http_servers}}

def all_disabled():
    result = {}
    for k, v in disabled["mcpServers"].items():
        src = v.pop("__source", "stdio") if "__source" in v else "stdio"
        result[k] = src
        v["__source"] = src  # put back
    return result

def enable(name):
    if name in mcp["mcpServers"] or name in http_servers:
        print(f"  {name}: 已启用，跳过")
        return
    node = disabled["mcpServers"].pop(name, None)
    if not node:
        print(f"  {name}: 未找到（既不在启用列表也不在禁用列表）")
        return
    source = node.pop("__source", "stdio")
    if source == "stdio":
        mcp["mcpServers"][name] = node
    else:
        http_servers[name] = node
    print(f"  {name}: 已启用 ({source})")

def disable(name):
    node = None
    source = "stdio"
    if name in mcp["mcpServers"]:
        node = mcp["mcpServers"].pop(name)
        source = "stdio"
    elif name in http_servers:
        node = http_servers.pop(name)
        source = http_servers.get(name, {}).get("type", "http")
        if name in http_servers:
            del http_servers[name]
        source = node.get("type", "http")
    if not node:
        print(f"  {name}: 未启用，跳过")
        return
    node["__source"] = source
    disabled["mcpServers"][name] = node
    print(f"  {name}: 已禁用（省 {TOKEN_ESTIMATE.get(name, '?')} token）")

if action == "status":
    active = all_active()
    dis = all_disabled()
    total_active = 0
    print("启用中:")
    for k, t in sorted(active.items()):
        est = TOKEN_ESTIMATE.get(k, "?")
        print(f"  ✓ {k:<20} ({t:<6}) {est} token")
        total_active += 1
    print(f"\n禁用中:")
    for k, t in sorted(dis.items()):
        est = TOKEN_ESTIMATE.get(k, "?")
        print(f"  ✗ {k:<20} ({t:<6}) {est} token")
    if not dis:
        print("  (无)")
    print(f"\n共 {total_active} 个启用，{len(dis)} 个禁用")

elif action == "on":
    if not targets:
        print("用法: toggle-mcp.sh on <server1> [server2] ...")
        sys.exit(1)
    for t in targets:
        enable(t)
    save_json(MCP, mcp)
    save_json(DISABLED, disabled)
    set_claude_json_servers(http_servers)
    print("\n→ 重启 Claude Code 生效")

elif action == "off":
    if not targets:
        print("用法: toggle-mcp.sh off <server1> [server2] ...")
        sys.exit(1)
    for t in targets:
        disable(t)
    save_json(MCP, mcp)
    save_json(DISABLED, disabled)
    set_claude_json_servers(http_servers)
    print("\n→ 重启 Claude Code 生效")

elif action == "only":
    if not targets:
        print("用法: toggle-mcp.sh only <server1> [server2] ...  (只保留指定的)")
        sys.exit(1)
    keep = set(targets)
    active = all_active()
    to_disable = [k for k in active if k not in keep]
    to_enable = [k for k in keep if k not in active]
    for t in to_disable:
        disable(t)
    for t in to_enable:
        enable(t)
    save_json(MCP, mcp)
    save_json(DISABLED, disabled)
    set_claude_json_servers(http_servers)
    print("\n→ 重启 Claude Code 生效")

else:
    print(f"未知操作: {action}")
    print("用法: toggle-mcp.sh [status|on|off|only] [server ...]")
    sys.exit(1)
PYEOF
