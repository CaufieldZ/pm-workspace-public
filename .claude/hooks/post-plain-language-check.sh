#!/bin/bash
# PostToolUse hook: 通用「讲人话」自检（deliverables/ 产出物兜底）
#
# 规则源：scripts/check_plain_language.py
#         覆盖：内部文件名 / 决策 N / 第 N 章节条 / PART 骨架锚点 / [待补充] / FIXME / TODO
#         详见 .claude/rules/pm-workflow.md「人读产出物讲人话」
#
# 两条路径：
#   A. Write/Edit 落 deliverables/**/*.{md,html} → 直接扫文件
#   B. Bash 跑 gen_*/fill_*.py 或 .sh → 扫 60s 内修改的 deliverables md/html
#
# 豁免：
#   - deliverables/audit-*.md（workspace-audit 产出，PM 自用）
#   - deliverables/**/*prd*.docx（走 post-prd-check.sh）
#   - deliverables/**/imap-*.html / *-interaction-*.html（走 check_imap.sh）
#   - 非 deliverables/ 路径（内部文档本就要引锚点）
#
# 行为：strict 命中 → exit 2 阻断 + stderr 报违规行号；其他 → exit 0
# Escape：SKIP_PLAIN_LANGUAGE_GATE=1

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CHECKER="$PROJECT_DIR/scripts/check_plain_language.py"
[ ! -f "$CHECKER" ] && exit 0

# ── Branch A: Write / Edit ─────────────────────────────────────────

if [ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ]; then
  FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

  [ -z "$FILE_PATH" ] && exit 0
  [ ! -f "$FILE_PATH" ] && exit 0

  # 只检 md / html
  case "$FILE_PATH" in
    *.md|*.html) ;;
    *) exit 0 ;;
  esac

  # 必须在 deliverables/ 下
  echo "$FILE_PATH" | grep -qE '/deliverables/' || exit 0

  # 豁免：audit-*.md / fix-plan-*.md / /audits/ 目录 / imap / interaction
  # （checker 也会二次校验，hook 先短路减少 subprocess）
  BASENAME=$(basename "$FILE_PATH")
  case "$BASENAME" in
    audit-*.md|fix-plan-*.md) exit 0 ;;
    imap-*.html|imap.html) exit 0 ;;
    *interaction*.html) exit 0 ;;
  esac
  echo "$FILE_PATH" | grep -q '/audits/' && exit 0

  if [ "${SKIP_PLAIN_LANGUAGE_GATE:-0}" = "1" ]; then
    _log_skip_gate plain-language-gate "env  ${FILE_PATH:0:120}"
    exit 0
  fi

  TMPOUT=$(mktemp)
  python3 "$CHECKER" "$FILE_PATH" --strict > "$TMPOUT" 2>&1
  RC=$?

  if [ "$RC" -eq 2 ]; then
    echo "🚫 [plain-language-gate] 讲人话自检未通过：$(echo "$FILE_PATH" | sed "s#$PROJECT_DIR/##")" >&2
    cat "$TMPOUT" >&2
    log_event hook plain-language-gate block "$FILE_PATH"
    rm -f "$TMPOUT"
    exit 2
  fi
  rm -f "$TMPOUT"
  log_event hook plain-language-gate clean "$FILE_PATH"
  exit 0
fi

# ── Branch B: Bash（扫 60s 内修改的 deliverables 文件）────────────

if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# 触发：含 gen_/fill_ 脚本（push/sync 不触发，不改本地文件）
if ! echo "$CMD" | grep -qE '\b(gen|fill)_[a-zA-Z0-9_-]+\.(py|sh)\b'; then
  exit 0
fi

if [ "${SKIP_PLAIN_LANGUAGE_GATE:-0}" = "1" ]; then
  _log_skip_gate plain-language-gate "env  ${CMD:0:120}"
  exit 0
fi
if echo "$CMD" | grep -qE '\bSKIP_PLAIN_LANGUAGE_GATE=1\b'; then
  _log_skip_gate plain-language-gate "inline  ${CMD:0:120}"
  exit 0
fi

SEARCH_ROOTS=()
[ -d "$PROJECT_DIR/projects" ] && SEARCH_ROOTS+=("$PROJECT_DIR/projects")
[ -d "$PROJECT_DIR/examples" ] && SEARCH_ROOTS+=("$PROJECT_DIR/examples")
[ -d "$PROJECT_DIR/deliverables" ] && SEARCH_ROOTS+=("$PROJECT_DIR/deliverables")
[ ${#SEARCH_ROOTS[@]} -eq 0 ] && exit 0

SIXTY_SEC_AGO=$(python3 -c "import time; print(int(time.time()) - 60)")

RECENT=$(find "${SEARCH_ROOTS[@]}" -path '*/deliverables/*' -type f \
  \( -name '*.md' -o -name '*.html' \) -not -path '*/archive/*' 2>/dev/null \
  | while read -r f; do
      MT=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null)
      [ -n "$MT" ] && [ "$MT" -gt "$SIXTY_SEC_AGO" ] && echo "$f"
    done)

[ -z "$RECENT" ] && exit 0

FAIL=0
FAIL_OUTPUT=""

while IFS= read -r FILE; do
  [ -z "$FILE" ] && continue

  BASENAME=$(basename "$FILE")
  case "$BASENAME" in
    audit-*.md|fix-plan-*.md) continue ;;
    imap-*.html|imap.html) continue ;;
    *interaction*.html) continue ;;
  esac
  echo "$FILE" | grep -q '/audits/' && continue

  TMPOUT=$(mktemp)
  python3 "$CHECKER" "$FILE" --strict > "$TMPOUT" 2>&1
  RC=$?

  if [ "$RC" -eq 2 ]; then
    FAIL=1
    FAIL_OUTPUT="${FAIL_OUTPUT}
=== $(echo "$FILE" | sed "s#$PROJECT_DIR/##") ===
$(cat "$TMPOUT")
"
  fi
  rm -f "$TMPOUT"
done <<< "$RECENT"

if [ "$FAIL" -eq 1 ]; then
  echo "🚫 [plain-language-gate] 讲人话自检未通过（gen/fill 路径自动二闸）：" >&2
  echo "$FAIL_OUTPUT" | head -80 >&2
  echo "" >&2
  echo "   修法：把内部锚点（文件名 / 决策 N / 第 N 章 / PART / 占位）改成业务白话。" >&2
  echo "   临时绕过：SKIP_PLAIN_LANGUAGE_GATE=1 python3 ..." >&2
  log_event hook plain-language-gate block "${CMD:0:80}"
  exit 2
fi

log_event hook plain-language-gate clean "${CMD:0:80}"
exit 0
