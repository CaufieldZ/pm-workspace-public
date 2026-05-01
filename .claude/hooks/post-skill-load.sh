#!/usr/bin/env bash
# PostToolUse hook: 监听 Read .claude/skills/{name}/SKILL.md → 记录 skill 触发
#
# Skill 触发的可观测信号：模型读了对应 SKILL.md
# 不拦截，纯记录。写入 .claude/logs/usage.jsonl

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

[ "$TOOL_NAME" != "Read" ] && exit 0

FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# 匹配 .claude/skills/{name}/SKILL.md
SKILL_NAME=$(echo "$FILE_PATH" | sed -nE 's|.*/\.claude/skills/([^/]+)/SKILL\.md$|\1|p')
[ -z "$SKILL_NAME" ] && exit 0

# 尝试从 cwd 或 FILE_PATH 推断当前项目（cwd 不一定是 root，用 FILE_PATH 更稳）
# 但 SKILL.md 路径里没有项目信息，用 session-state.md 的项目字段反推
PROJECT=""
STATE_FILE="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/session-state.md"
if [ -f "$STATE_FILE" ]; then
  PROJECT=$(grep -oE '项目[:：][[:space:]]*[a-zA-Z0-9_/-]+' "$STATE_FILE" 2>/dev/null | head -1 | sed -E 's/项目[:：][[:space:]]*//')
fi

log_event skill "$SKILL_NAME" triggered "$PROJECT"
exit 0
