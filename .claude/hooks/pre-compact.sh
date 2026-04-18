#!/bin/bash
# PreCompact hook: 在上下文压缩前注入 session-state.md 内容
# 确保 compact 后 Claude 仍然知道当前项目/Skill/Step/已填 Scene/待办

STATE_FILE="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/session-state.md"

if [ -s "$STATE_FILE" ]; then
  echo "═══ Session State 快照（PreCompact Hook 注入）═══"
  echo ""
  cat "$STATE_FILE"
  echo ""
  echo "═══════════════════════════════════════════════════"
  echo "（以上内容由 pre-compact hook 自动注入，用于 compact 后恢复进度）"
fi
