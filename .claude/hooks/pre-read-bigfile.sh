#!/bin/bash
# PreToolUse Read hook: 阻断 > 500 行文件的全量 Read（必须用 offset/limit）
#
# 触发：Read 普通文本文件且文件 > 500 行
# 行为：tool_input 未带 offset / limit → exit 2 阻断,stderr 给修法
# Escape：SKIP_READ_BIGFILE_GATE=1（Read 不经 Bash 管道,只 env 生效）
#
# CLAUDE.md 规则:"> 500 行禁全量 Read,走 wc -l + Grep + offset/limit"

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"

INPUT=$(cat)
hook_parse_read

[ "$HOOK_TOOL_NAME" = "Read" ] || exit 0

FILE_PATH="$HOOK_FILE_PATH"
[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# 非文本类:图片 / PDF / notebook 走 Read 自身机制,跳过
case "$FILE_PATH" in
  *.png|*.jpg|*.jpeg|*.gif|*.webp|*.svg|*.pdf|*.ipynb) exit 0 ;;
esac

# hook 自身文件 / settings 排除（运维排查时需全量读）
case "$FILE_PATH" in
  */.claude/hooks/*) exit 0 ;;
  */.claude/settings.json|*/.claude/settings.local.json) exit 0 ;;
esac

# 已带 offset 或 limit → 放行(模型已知分页)。paging 标志由 hook_parse_read 一并解析，省一次 jq。
[ "$HOOK_HAS_PAGING" = "1" ] && exit 0

check_skip_env "read-bigfile" "SKIP_READ_BIGFILE_GATE" "$FILE_PATH"

LINE_COUNT=$(wc -l < "$FILE_PATH" 2>/dev/null)
LINE_COUNT="${LINE_COUNT//[[:space:]]/}"   # 去 BSD wc 前导空格（参数展开，省 tr fork）
[ -z "$LINE_COUNT" ] && exit 0

# 快速放行：≤ 500 行直接过。500 = thresholds.yaml large_file_lines 的保守下界，与下方
# fallback 同源（调整 yaml 阈值时同步这两处 500）。绝大多数文件命中此分支，省每次 awk 解析 yaml。
[ "$LINE_COUNT" -le 500 ] && exit 0

# 仅 > 500 行才精确读阈值（yaml 真相源，可能被调高于 500）。awk 失败 fallback 500。
THRESHOLD=$(awk '/^risky_op:/{f=1; next} f && /^[a-z]/{exit} f && /large_file_lines:/{gsub(/[^0-9]/,"",$2); print $2; exit}' "${CLAUDE_PROJECT_DIR:-$(pwd)}/scripts/lib/thresholds.yaml" 2>/dev/null)
[ -z "$THRESHOLD" ] && THRESHOLD=500

if [ "$LINE_COUNT" -gt "$THRESHOLD" ]; then
  REL_PATH="${FILE_PATH#${CLAUDE_PROJECT_DIR:-$(pwd)}/}"
  cat >&2 <<EOF
🚫 [read-bigfile] $REL_PATH 共 $LINE_COUNT 行(> $THRESHOLD)
   → 修法(任一):
     1. Grep -n '关键词' 此文件     # 先定位行号
     2. Read 加 offset=N limit=M    # 按行号范围分页
     3. baseline / PRD md → python3 .claude/skills/prd/scripts/read_prd_section.py --toc / -s
   理由:全量 Read 大文件吃 token 预算 / 触发 compact 丢状态
   Escape: SKIP_READ_BIGFILE_GATE=1(env 设置后重试)
EOF
  log_event hook read-bigfile block "$REL_PATH ($LINE_COUNT lines)"
  exit 2
fi

exit 0
