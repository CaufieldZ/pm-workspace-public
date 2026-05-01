#!/bin/bash
# PreToolUse hook: 高风险操作前检查 session-state.md 是否近期更新
# 命中风险模式 + 状态文件超 3 分钟未更新 → stderr 打印警告(不拦截)
#
# 风险模式:
#   - Bash 命令含 playwright / chromium / browser.*launch / screenshot.*full_page
#   - Bash 命令含 render_.*\.py 且涉及截图验证
#   - Write/Edit 目标已存在且 > 500 行(可能是大 HTML 产出物)
#
# 设计:warn 不 block,误拦比漏报代价更低

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

STATE_FILE="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/session-state.md"
STALE_SECONDS=600  # 10 分钟

# 读 hook 输入(JSON via stdin)
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

is_risky=0
risky_reason=""

case "$TOOL_NAME" in
  Bash)
    CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)
    if echo "$CMD" | grep -qE 'playwright|chromium|browser\.(launch|new_page)|screenshot.*full_page|page\.goto'; then
      is_risky=1
      risky_reason="Playwright/浏览器渲染"
    elif echo "$CMD" | grep -qE 'python3.*render_.*\.py|node.*gen_.*\.js.*[0-9]{3}'; then
      is_risky=1
      risky_reason="大文件渲染脚本"
    fi
    ;;
  Write|Edit)
    FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)
    if [ -f "$FILE_PATH" ]; then
      LINE_COUNT=$(wc -l < "$FILE_PATH" 2>/dev/null || echo 0)
      if [ "$LINE_COUNT" -gt 500 ] && echo "$FILE_PATH" | grep -qE '\.(html|md|py|js)$'; then
        is_risky=1
        risky_reason="编辑大文件($LINE_COUNT 行)"
      fi
    fi
    ;;
esac

[ "$is_risky" -eq 0 ] && exit 0

# 检查 session-state.md 更新时效
if [ ! -f "$STATE_FILE" ]; then
  echo "⚠️  高风险操作($risky_reason)前 session-state.md 不存在" >&2
  echo "   建议先 Write .claude/session-state.md 保存当前进度(防 session 假死丢状态)" >&2
  exit 0
fi

# macOS stat -f %m,Linux stat -c %Y
MTIME=$(stat -f %m "$STATE_FILE" 2>/dev/null || stat -c %Y "$STATE_FILE" 2>/dev/null)
NOW=$(date +%s)
AGE=$((NOW - MTIME))

if [ "$AGE" -gt "$STALE_SECONDS" ]; then
  MINS=$((AGE / 60))
  echo "⚠️  高风险操作($risky_reason)前 session-state.md 已 ${MINS} 分钟未更新" >&2
  echo "   建议先 Write .claude/session-state.md 保存当前进度" >&2
  echo "   理由:Playwright/大文件操作一旦 tool output 超 50K 或 API 挂住,无 compact 触发,状态会丢" >&2
  log_event hook risky-op warn "$risky_reason"
else
  log_event hook risky-op triggered "$risky_reason"
fi

exit 0
