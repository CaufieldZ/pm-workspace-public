#!/bin/bash
# PreCompact hook: 在上下文压缩前注入 session-state.md + git 动态快照
# session-state 是按需手动 checkpoint 文件，不存在时 git 快照仍兜底
set +e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
STATE_FILE="$PROJECT_DIR/.claude/session-state.md"

source "$PROJECT_DIR/.claude/hooks/lib/log.sh"
log_event hook pre-compact triggered

echo "═══ Session State 快照（PreCompact Hook 注入）═══"
echo ""

# 1. session-state.md 内容 + stale 检测
#    文件不存在 / 纯空白 → 整节跳过（用户没主动 checkpoint，没东西注入；git 快照仍会注入）
if [ -f "$STATE_FILE" ] && grep -q '[^[:space:]]' "$STATE_FILE" 2>/dev/null; then
  MTIME=$(file_mtime "$STATE_FILE")
  NOW=$(date +%s)
  AGE_MIN=$(( (NOW - MTIME) / 60 ))

  if [ "$AGE_MIN" -gt 30 ]; then
    echo "⚠️  session-state.md 已 ${AGE_MIN} 分钟未更新（stale），下方内容可能过时；请参考 git 动态快照"
    echo ""
  fi

  echo "── session-state.md（更新于 ${AGE_MIN} 分钟前）──"
  cat "$STATE_FILE"
  echo ""
fi

# 2. git 动态快照（最近 commit + 未提交变更）
cd "$PROJECT_DIR" 2>/dev/null
if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "── 最近 5 条 commit ──"
  git log --oneline -5 2>/dev/null
  echo ""

  CHANGED=$(git status -s 2>/dev/null)
  if [ -n "$CHANGED" ]; then
    echo "── 未提交变更（git status -s）──"
    echo "$CHANGED"
    echo ""
  else
    echo "── 工作树干净 ──"
    echo ""
  fi
fi

echo "═══════════════════════════════════════════════════"
echo "（以上由 pre-compact hook 自动注入。session-state.md stale 时，以 git 动态为准）"
