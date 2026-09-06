#!/usr/bin/env bash
# PreToolUse Agent hook: Agent tool 调用 → 记录 sub-agent 调度（type=agent）
#
# 跟踪 Explore / general-purpose 通用 agent 派发频次、最近命中。
#
# 不拦截，纯记录。tool_name 兼容 "Agent"（现名）与 "Task"（旧名，回滚/旧版 CLI）
# dashboard.py render_agents() 消费此数据。

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"

INPUT=$(cat)
hook_parse_task

case "$HOOK_TOOL_NAME" in
  Agent|Task) ;;
  *) exit 0 ;;
esac

SUBAGENT="${HOOK_SUBAGENT_TYPE:-general-purpose}"

log_event agent "$SUBAGENT" triggered "$HOOK_DESCRIPTION"
exit 0
