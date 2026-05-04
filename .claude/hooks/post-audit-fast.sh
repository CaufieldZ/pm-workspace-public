#!/bin/bash
# PostToolUse hook: deliverable Write/Edit 后跑 audit-fast 快速自检
# audit-fast 返回 0 → 静默放行；返回非 0 → exit 2 阻断后续工具调用

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ]; then
  exit 0
fi

FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

[ -z "$FILE_PATH" ] && exit 0

case "$FILE_PATH" in
  */projects/*/*/deliverables/*|*/projects/*/deliverables/*|*/examples/*/deliverables/*) ;;
  *) exit 0 ;;
esac
case "$FILE_PATH" in
  */archive/*) exit 0 ;;
esac

SCRIPT="${CLAUDE_PROJECT_DIR:-$(pwd)}/scripts/audit-fast.sh"
[ ! -f "$SCRIPT" ] && exit 0

bash "$SCRIPT" "$FILE_PATH" 2>/tmp/audit-fast-stderr.txt
RC=$?

if [ "$RC" -ne 0 ]; then
  cat /tmp/audit-fast-stderr.txt >&2
  log_event hook audit-fast block "$FILE_PATH"
  rm -f /tmp/audit-fast-stderr.txt
  exit 2
fi

log_event hook audit-fast clean "$FILE_PATH"
rm -f /tmp/audit-fast-stderr.txt
exit 0
