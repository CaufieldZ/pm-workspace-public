#!/bin/bash
# Stop hook: 每次 session 结束后刷新 workspace-dashboard.md
# 鲜度阈值：6 小时（避免频繁 session 都跑 dashboard）
# 跳过：SKIP_DASHBOARD_REFRESH=1
set +e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
DASHBOARD="$PROJECT_DIR/.claude/workspace-dashboard.md"
DASH_SCRIPT="$PROJECT_DIR/scripts/dashboard.py"

source "$PROJECT_DIR/.claude/hooks/lib/log.sh"

[ "${SKIP_DASHBOARD_REFRESH:-0}" = "1" ] && exit 0
[ ! -f "$DASH_SCRIPT" ] && exit 0

# 鲜度检查：dashboard 修改时间距今 < 6h 则跳过
if [ -f "$DASHBOARD" ]; then
  MT=$(file_mtime "$DASHBOARD")
  NOW=$(date +%s)
  AGE=$((NOW - MT))
  [ "$AGE" -lt 21600 ] && exit 0  # 6h = 21600s
fi

# 后台刷新（不阻塞 Stop 返回）
(python3 "$DASH_SCRIPT" > /dev/null 2>&1) &
exit 0
