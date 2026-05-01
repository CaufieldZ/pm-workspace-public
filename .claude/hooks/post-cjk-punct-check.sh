#!/bin/bash
# PostToolUse hook: 对刚写入的中文产物扫 CJK 旁半角标点,命中打 stderr warning(不拦截)
#
# 覆盖范围:
#   - *.md (context/scene-list/inputs/deliverables/skill/rule)
#   - *.html (deliverables)
#   - *.py / *.js 当文件含中文字符串时(gen/patch 脚本)
#
# 跳过:archive/ / __pycache__/ / node_modules/ / .git/
#
# 设计:warn 不 block,stderr 输出给 Claude 看到,失败成本 0 误报成本低

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ]; then
  exit 0
fi

FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# 只检查特定扩展
case "$FILE_PATH" in
  *.md|*.html|*.py|*.js) ;;
  *) exit 0 ;;
esac

# 跳过含有 archive / __pycache__ / node_modules 的路径
if echo "$FILE_PATH" | grep -qE '(archive|__pycache__|node_modules|\.git)/'; then
  exit 0
fi

# py/js 只在含中文字符时才扫(避免纯英文源码误扫)
case "$FILE_PATH" in
  *.py|*.js)
    if ! grep -lq '[一-鿿]' "$FILE_PATH" 2>/dev/null; then
      exit 0
    fi
    ;;
esac

CHECKER="${CLAUDE_PROJECT_DIR:-$(pwd)}/scripts/check_cjk_punct.py"
[ ! -f "$CHECKER" ] && exit 0

# deliverables（非 archive）用 --strict：checker exit 2 → hook exit 2 阻断
# 适配 schema v2：projects/{产品线}/{项目}/deliverables/ 两层 + projects/{顶级}/deliverables/ 一层
IS_DELIVERABLE=0
case "$FILE_PATH" in
  */projects/*/*/deliverables/*|*/projects/*/deliverables/*)
    case "$FILE_PATH" in
      */archive/*) ;;
      *) IS_DELIVERABLE=1 ;;
    esac
    ;;
esac

if [ "$IS_DELIVERABLE" -eq 1 ]; then
  TMPOUT=$(mktemp)
  python3 "$CHECKER" "$FILE_PATH" --strict > "$TMPOUT" 2>&1
  RC=$?
  if [ "$RC" -ne 0 ]; then
    head -3 "$TMPOUT" >&2
    log_event hook cjk-punct block "$FILE_PATH"
    rm -f "$TMPOUT"
    exit 2
  fi
  log_event hook cjk-punct clean "$FILE_PATH"
  rm -f "$TMPOUT"
else
  # 用 --strict 拿 RC 做埋点判断，但 hook 不阻断（只 warn）
  STDERR=$(python3 "$CHECKER" "$FILE_PATH" --strict 2>&1 >/dev/null)
  RC=$?
  [ -n "$STDERR" ] && echo "$STDERR" >&2
  if [ "$RC" -ne 0 ]; then
    log_event hook cjk-punct warn "$FILE_PATH"
  else
    log_event hook cjk-punct clean "$FILE_PATH"
  fi
fi
exit 0
