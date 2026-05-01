#!/bin/bash
# PreToolUse: 外网下载命令自动检查代理
# 命中高风险命令且未设代理 → exit 2 阻断
# 已设代理 / 国内源 / 不匹配 / 显式跳过 → exit 0

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
[ "$TOOL_NAME" = "Bash" ] || exit 0

CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)
[ -n "$CMD" ] || exit 0

# 快速放过：不含高风险关键字直接走
echo "$CMD" | grep -qE '(pip|pip3|npm|pnpm|yarn|brew|curl|wget|go\s|cargo|bun|composer)\s+(install|i\s|add|get|build|update|fetch|clone)' && echo "$CMD" | grep -qE 'https?://|pypi|npmjs|crates\.io|rubygems|proxy\.golang|packagist' || exit 0

# 已设代理 → 放
echo "$CMD" | grep -qiE '(ALL_PROXY|HTTPS?_PROXY|all_proxy|https?_proxy)=' && exit 0

# 国内镜像 → 放
echo "$CMD" | grep -qE '(pypi\.tuna\.tsinghua|npmmirror|mirrors\.(aliyun|tencent|ustc|163)|registry\.npm\.taobao|goproxy\.cn|\.cn[/:])' && exit 0

# 显式跳过 → 放
echo "$CMD" | grep -q 'SKIP_PROXY_CHECK=1' && exit 0

# 命中
echo "" >&2
echo "[proxy-gate] 外网下载命令未设代理" >&2
echo "   $CMD" >&2
echo "   请改为: ALL_PROXY=http://127.0.0.1:7897 $CMD" >&2
echo "   国内源或确认不需代理: SKIP_PROXY_CHECK=1 $CMD" >&2
echo "" >&2
log_event gate proxy-check block "${CMD:0:120}"
exit 2
