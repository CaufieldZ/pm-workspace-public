#!/bin/bash
# PostToolUse Bash hook: gen_prd_*.py / update_prd_*.py 跑完后自动跑 check_prd.sh
#
# 触发：Bash 命令含 gen_prd*.py / update_prd*.py / patch_prd*.py
# 检测：扫最近 60s 内动过的 PRD docx（projects/ + examples/）
#       对每个 docx 找同项目 scene-list.md，调 check_prd.sh
# 行为：check_prd 失败（exit != 0）→ hook exit 2 阻断 + stderr 报违规
# Escape：SKIP_PRD_CHECK_GATE=1 临时绕过
#
# 历史：2026-05-04 demo-private-fund 重生 PRD 时漏「讲人话」违规未被任何 hook 拦下
#       问题根因：check_prd.sh 仅 pre-wiki-push-gate 调用，本地 gen 路径裸奔

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
[ "$TOOL_NAME" != "Bash" ] && exit 0

CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# 触发：含 gen_prd / update_prd / patch_prd 的 .py 调用
if ! echo "$CMD" | grep -qE '\b(gen|update|patch)_prd[a-zA-Z0-9_-]*\.py\b'; then
  exit 0
fi

if [ "${SKIP_PRD_CHECK_GATE:-0}" = "1" ]; then
  _log_skip_gate prd-check-gate "env  ${CMD:0:120}"
  exit 0
fi
if echo "$CMD" | grep -qE '\bSKIP_PRD_CHECK_GATE=1\b'; then
  _log_skip_gate prd-check-gate "inline  ${CMD:0:120}"
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CHECKER="$PROJECT_DIR/.claude/skills/prd/scripts/check_prd.sh"
[ ! -f "$CHECKER" ] && exit 0

# 找最近 60s 内动过的 PRD docx（projects/ + examples/）
SEARCH_ROOTS=()
[ -d "$PROJECT_DIR/projects" ] && SEARCH_ROOTS+=("$PROJECT_DIR/projects")
[ -d "$PROJECT_DIR/examples" ] && SEARCH_ROOTS+=("$PROJECT_DIR/examples")
[ ${#SEARCH_ROOTS[@]} -eq 0 ] && exit 0

SIXTY_SEC_AGO=$(python3 -c "import time; print(int(time.time()) - 60)")
RECENT_DOCX=$(find "${SEARCH_ROOTS[@]}" -path '*/deliverables/*' -type f \
  -name '*prd*.docx' -not -path '*/archive/*' 2>/dev/null \
  | while read -r f; do
      MT=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null)
      [ -n "$MT" ] && [ "$MT" -gt "$SIXTY_SEC_AGO" ] && echo "$f"
    done)

# 文件名大小写：再扫一次 *PRD*.docx
RECENT_DOCX2=$(find "${SEARCH_ROOTS[@]}" -path '*/deliverables/*' -type f \
  -name '*PRD*.docx' -not -path '*/archive/*' 2>/dev/null \
  | while read -r f; do
      MT=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null)
      [ -n "$MT" ] && [ "$MT" -gt "$SIXTY_SEC_AGO" ] && echo "$f"
    done)

ALL_DOCX=$(printf '%s\n%s\n' "$RECENT_DOCX" "$RECENT_DOCX2" | sort -u | grep -v '^$')
[ -z "$ALL_DOCX" ] && exit 0

FAIL=0
FAIL_OUTPUT=""

while IFS= read -r DOCX; do
  [ -z "$DOCX" ] && continue
  PROJ_ROOT=$(dirname "$(dirname "$DOCX")")
  SCENE_LIST="$PROJ_ROOT/scene-list.md"
  if [ ! -f "$SCENE_LIST" ]; then
    echo "[prd-check-gate] 跳过 $(basename "$DOCX"): 同级 scene-list.md 不存在" >&2
    continue
  fi

  TMPOUT=$(mktemp)
  bash "$CHECKER" "$DOCX" "$SCENE_LIST" > "$TMPOUT" 2>&1
  RC=$?
  if [ "$RC" -ne 0 ]; then
    FAIL=1
    FAIL_OUTPUT="${FAIL_OUTPUT}
=== $(echo "$DOCX" | sed "s#$PROJECT_DIR/##") ===
$(cat "$TMPOUT")
"
  fi
  rm -f "$TMPOUT"
done <<< "$ALL_DOCX"

if [ "$FAIL" -eq 1 ]; then
  echo "🚫 [prd-check-gate] PRD 自检未通过（gen/update 路径自动二闸）：" >&2
  echo "$FAIL_OUTPUT" | head -60 >&2
  echo "" >&2
  echo "   修复后重跑 gen_prd_*.py / update_prd_*.py" >&2
  echo "   临时绕过：SKIP_PRD_CHECK_GATE=1 python3 ..." >&2
  log_event hook prd-check-gate block "${CMD:0:80}"
  exit 2
fi

log_event hook prd-check-gate clean "${CMD:0:80}"
exit 0
