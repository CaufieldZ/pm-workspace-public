#!/usr/bin/env bash
# toggle-firecrawl.sh — 切换 firecrawl MCP 启用/禁用
# 用法: ./scripts/toggle-firecrawl.sh [on|off|status]
#
# 机制:在 .mcp.json 和 .mcp-disabled.json 之间搬运 firecrawl 节点。
#       Claude Code 只扫描 .mcp.json,所以移除节点可彻底省下 schema token。
# 改完需重启 Claude Code 才生效。

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MCP="$ROOT/.mcp.json"
DISABLED="$ROOT/.mcp-disabled.json"
ACTION="${1:-status}"

case "$ACTION" in
  on)
    python3 << PYEOF
import json, os
mcp_path = "$MCP"
dis_path = "$DISABLED"
with open(mcp_path) as f: mcp = json.load(f)
if 'firecrawl' in mcp.get('mcpServers', {}):
    print('firecrawl 已在 .mcp.json,无需启用')
else:
    if not os.path.exists(dis_path):
        raise SystemExit('错: .mcp-disabled.json 不存在,无法恢复 firecrawl')
    with open(dis_path) as f: dis = json.load(f)
    node = dis.get('mcpServers', {}).pop('firecrawl', None)
    if not node:
        raise SystemExit('错: .mcp-disabled.json 里没有 firecrawl 节点')
    mcp['mcpServers']['firecrawl'] = node
    with open(mcp_path, 'w') as f: json.dump(mcp, f, indent=2, ensure_ascii=False)
    with open(dis_path, 'w') as f: json.dump(dis, f, indent=2, ensure_ascii=False)
    print('firecrawl 已启用(已从 .mcp-disabled.json 恢复到 .mcp.json)')
PYEOF
    echo "→ 请重启 Claude Code 生效"
    ;;
  off)
    python3 << PYEOF
import json, os
mcp_path = "$MCP"
dis_path = "$DISABLED"
with open(mcp_path) as f: mcp = json.load(f)
node = mcp.get('mcpServers', {}).pop('firecrawl', None)
if not node:
    print('firecrawl 不在 .mcp.json,无需禁用')
else:
    dis = {'mcpServers': {}}
    if os.path.exists(dis_path):
        with open(dis_path) as f: dis = json.load(f)
    dis.setdefault('mcpServers', {})['firecrawl'] = node
    with open(mcp_path, 'w') as f: json.dump(mcp, f, indent=2, ensure_ascii=False)
    with open(dis_path, 'w') as f: json.dump(dis, f, indent=2, ensure_ascii=False)
    print('firecrawl 已禁用(节点已挪到 .mcp-disabled.json)')
PYEOF
    echo "→ 请重启 Claude Code 生效"
    ;;
  status|*)
    python3 << PYEOF
import json, os
with open("$MCP") as f: mcp = json.load(f)
active = list(mcp.get('mcpServers', {}).keys())
disabled = []
if os.path.exists("$DISABLED"):
    with open("$DISABLED") as f: dis = json.load(f)
    disabled = list(dis.get('mcpServers', {}).keys())
print(f'启用中: {active}')
print(f'已禁用: {disabled}')
PYEOF
    ;;
esac
