#!/bin/bash
# PostToolUse hook: prototype HTML（proto-*.html）Write/Edit 后跑 audit_against_baseline.py
# 检查 E1-E6 视觉铁律 + 标杆组件计数 + 反 AI slop 六禁 + 字重三级
# fail → exit 2 阻断 + stderr 输出失败项；过 → 静默放行
#
# 与 post-audit-fast.sh 互补：audit-fast 通用规则，本 hook 是 prototype 专项

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ]; then
  exit 0
fi

FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

[ -z "$FILE_PATH" ] && exit 0

# 只处理 prototype HTML 产出物
case "$FILE_PATH" in
  */deliverables/proto-*.html) ;;
  *) exit 0 ;;
esac
case "$FILE_PATH" in
  */archive/*) exit 0 ;;
esac

SCRIPT="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/skills/prototype/scripts/audit_against_baseline.py"
[ ! -f "$SCRIPT" ] && exit 0

STDERR=/tmp/proto-audit-stderr.$$.txt
python3 "$SCRIPT" "$FILE_PATH" >"$STDERR" 2>&1
RC=$?

if [ "$RC" -ne 0 ]; then
  echo "═══ prototype audit fail (post-prototype-audit.sh) ═══" >&2
  cat "$STDERR" >&2
  echo "" >&2
  echo "→ 修复方案：见 .claude/skills/prototype/references/prototype-components.md § E（Fill 视觉铁律 E1-E6）" >&2
  log_event hook prototype-audit block "$FILE_PATH"
  rm -f "$STDERR"
  exit 2
fi

log_event hook prototype-audit clean "$FILE_PATH"
rm -f "$STDERR"
exit 0
