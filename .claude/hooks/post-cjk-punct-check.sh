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

python3 "$CHECKER" "$FILE_PATH"
exit 0
