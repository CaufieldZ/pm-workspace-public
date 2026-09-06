#!/bin/bash
# PreToolUse Agent hook: sub-agent prompt 必须显式禁读写 session-state.md
#
# 触发：Agent 工具调用 sub-agent 时（tool_name 兼容 "Agent" 现名 / "Task" 旧名）
# 行为：prompt 未含 session[-_]state 关键词 → exit 2 阻断,stderr 给修法
# Escape：SKIP_TASK_PROMPT_SCRUB_GATE=1（Agent 不经 Bash 管道,只 env 生效）
#
# CLAUDE.md 规则:"sub-agent prompt 必须显式禁读写 session-state.md"

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"

INPUT=$(cat)
hook_parse_task

case "$HOOK_TOOL_NAME" in
  Agent|Task) ;;
  *) exit 0 ;;
esac

PROMPT="$HOOK_PROMPT"
[ -z "$PROMPT" ] && exit 0

# 短 prompt(< 100 char)一般是简单查询,跳过免烦扰
[ ${#PROMPT} -lt 100 ] && exit 0

check_skip_env "task-prompt-scrub" "SKIP_TASK_PROMPT_SCRUB_GATE" "${PROMPT:0:80}"

# 命中关键词 → 放行
if echo "$PROMPT" | grep -qiE 'session[-_]state'; then
  log_event hook task-prompt-scrub clean "${PROMPT:0:80}"
  exit 0
fi

cat >&2 <<EOF
🚫 [task-prompt-scrub] sub-agent prompt 未显式禁读写 session-state.md
   CLAUDE.md 规则:sub-agent prompt 必须显式禁读写 .claude/session-state.md
   → 修法:prompt 末尾追加(任一句式即可,只要含 session-state):
     "禁读写 .claude/session-state.md(主线 checkpoint,sub-agent 不应触碰)"
     "Do not read or write .claude/session-state.md."
   理由:sub-agent 误写会覆盖主线进度,session 假死时无法恢复
   Escape: SKIP_TASK_PROMPT_SCRUB_GATE=1(env 设置后重试)
EOF
log_event hook task-prompt-scrub block "${PROMPT:0:120}"
exit 2
