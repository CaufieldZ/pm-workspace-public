#!/bin/bash
# PreToolUse Bash hook: 骨架/产出物生成前,强制 context.md 和 scene-list.md 版本号一致
#
# 规则来源:pm-workflow.md §批量变更与 cross-check
#   「骨架脚本生成前,先 grep 两个文件的版本号,不一致则停止并提示用户先同步」
#
# 触发:命令含 gen_imap_skeleton / gen_proto_skeleton / gen_prd_base / gen_prd_v 等
# 检测:从命令抽项目名,grep 两个文件前 30 行的 vN.M 版本号
#       不一致 → exit 2

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
[ "$TOOL_NAME" != "Bash" ] && exit 0

CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# 触发条件:命中骨架/初版生成脚本
if ! echo "$CMD" | grep -qE 'gen_(imap_skeleton|proto_skeleton|prd_(base|v[0-9])|imap_v[0-9]|proto_v[0-9])'; then
  exit 0
fi

# 抽项目路径：先试两层（产品线/项目），失败回落到一层（顶级项目）
PROJECT_NAME=$(echo "$CMD" | sed -nE 's|.*projects/([^/]+/[^/]+)/scripts/.*|\1|p' | head -1)
[ -z "$PROJECT_NAME" ] && PROJECT_NAME=$(echo "$CMD" | sed -nE 's|.*projects/([^/]+)/scripts/.*|\1|p' | head -1)
[ -z "$PROJECT_NAME" ] && exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CONTEXT_FILE="$PROJECT_DIR/projects/$PROJECT_NAME/context.md"
SCENE_FILE="$PROJECT_DIR/projects/$PROJECT_NAME/scene-list.md"

[ ! -f "$CONTEXT_FILE" ] && exit 0
[ ! -f "$SCENE_FILE" ] && exit 0

# 抽前 50 行的第一个 vN.M(允许 v1, v1.1, v12.34)
extract_version() {
  head -50 "$1" | grep -oE '\bv[0-9]+(\.[0-9]+)?' | head -1
}

CTX_V=$(extract_version "$CONTEXT_FILE")
SCN_V=$(extract_version "$SCENE_FILE")

# 任何一边没抽到不拦截(避免误报新建项目)
[ -z "$CTX_V" ] && exit 0
[ -z "$SCN_V" ] && exit 0

if [ "$CTX_V" != "$SCN_V" ]; then
  echo "" >&2
  echo "🚫 [version-sync-gate] context.md 与 scene-list.md 版本号不一致" >&2
  echo "   项目:$PROJECT_NAME" >&2
  echo "   context.md  : $CTX_V" >&2
  echo "   scene-list.md: $SCN_V" >&2
  echo "" >&2
  echo "   pm-workflow.md 强制:骨架生成前两文件版本必须一致" >&2
  echo "   → 先同步:更新 scene-list.md 头部版本号为 $CTX_V(或反之)" >&2
  echo "" >&2
  log_event gate version-sync-gate block "$PROJECT_NAME ctx=$CTX_V scene=$SCN_V"
  exit 2
fi

log_event gate version-sync-gate triggered "$PROJECT_NAME"
exit 0
