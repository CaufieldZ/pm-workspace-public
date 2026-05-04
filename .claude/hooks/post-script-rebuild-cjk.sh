#!/bin/bash
# PostToolUse Bash hook: gen/fill/patch/update 脚本跑完后,扫最近 30s 内动过的 deliverables
# 用 check_cjk_punct.py --strict 检查 CJK 旁半角标点
# 命中 → exit 2 阻断 + stderr 报违规
#
# 解决问题:Write/Edit hook 只覆盖手写场景,脚本重生 HTML 时 CJK 检查会漏
# 例如 fstring 拼接 f"前一句:后一句" 在源码看是变量+冒号,产物才暴露

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
[ "$TOOL_NAME" != "Bash" ] && exit 0

CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# 触发:命令含 gen_/fill_/patch_/update_ 开头的脚本调用
if ! echo "$CMD" | grep -qE '\b(gen|fill|patch|update)_[a-zA-Z0-9_-]+\.(py|js)\b'; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CHECKER="$PROJECT_DIR/scripts/check_cjk_punct.py"
[ ! -f "$CHECKER" ] && exit 0

# 找最近 30s 内修改过的 deliverables（HTML / md）— 覆盖 projects/ + examples/
SEARCH_ROOTS=()
[ -d "$PROJECT_DIR/projects" ] && SEARCH_ROOTS+=("$PROJECT_DIR/projects")
[ -d "$PROJECT_DIR/examples" ] && SEARCH_ROOTS+=("$PROJECT_DIR/examples")
[ ${#SEARCH_ROOTS[@]} -eq 0 ] && exit 0

RECENT=$(find "${SEARCH_ROOTS[@]}" -path '*/deliverables/*' -type f \
  \( -name '*.html' -o -name '*.md' \) \
  -not -path '*/archive/*' \
  -mtime -30s 2>/dev/null)

# macOS find 不支持 -mtime -30s,改用 stat 自滤
if [ -z "$RECENT" ]; then
  THIRTY_SEC_AGO=$(python3 -c "import time; print(int(time.time()) - 30)")
  RECENT=$(find "${SEARCH_ROOTS[@]}" -path '*/deliverables/*' -type f \
    \( -name '*.html' -o -name '*.md' \) \
    -not -path '*/archive/*' 2>/dev/null \
    | while read -r f; do
        MT=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null)
        [ -n "$MT" ] && [ "$MT" -gt "$THIRTY_SEC_AGO" ] && echo "$f"
      done)
fi

[ -z "$RECENT" ] && exit 0

# 跑 strict 检查
TMPOUT=$(mktemp)
echo "$RECENT" | xargs python3 "$CHECKER" --strict > "$TMPOUT" 2>&1
RC=$?

if [ "$RC" -ne 0 ]; then
  echo "[script-rebuild-cjk] 脚本重生的 deliverable 含 CJK 旁半角标点：" >&2
  head -30 "$TMPOUT" >&2
  echo "" >&2
  echo "  → 改源脚本中的字符串,重新生成" >&2
  log_event hook script-rebuild-cjk block "$(echo "$RECENT" | head -1)"
  rm -f "$TMPOUT"
  exit 2
fi

# RC == 0 但仍有 warn 级违规（中英文间漏空格 / 全角标点旁多余空格 等）→ 提示不阻断
# pm-workflow.md「warn: stderr 提示不阻断」契约要求脚本生成路径同样可见
if grep -q '⚠️' "$TMPOUT" 2>/dev/null; then
  echo "[script-rebuild-cjk] 脚本重生的 deliverable 含 CJK 排版 warn（不阻断，建议改源脚本字符串）：" >&2
  head -30 "$TMPOUT" >&2
  echo "" >&2
  log_event hook script-rebuild-cjk warn "$(echo "$RECENT" | head -1)"
  rm -f "$TMPOUT"
  exit 0
fi

log_event hook script-rebuild-cjk clean "$(echo "$RECENT" | head -1)"
rm -f "$TMPOUT"
exit 0
