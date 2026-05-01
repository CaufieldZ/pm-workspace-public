#!/bin/bash
# PreToolUse Write/Edit hook: 已脚本化的 HTML deliverable 禁止直接 Write/Edit
#
# 规则来源:pm-workflow.md §大文件生成与文档同步
#   「一旦产出物已有 gen 脚本,HTML 即为只读产物:禁止直接 Edit/Write 生成出来的 HTML」
#
# 触发:Write/Edit 命中 projects/{X}/deliverables/*.html
# 检测:同项目 projects/{X}/scripts/ 下存在 gen_*.py / gen_*.js / fill_*.py / patch_*.py
# 命中 → exit 2 阻断
# Escape hatch:环境变量 SKIP_DELIVERABLE_GATE=1 临时绕过(适用真正小幅文案修改)

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ]; then
  exit 0
fi

FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)
[ -z "$FILE_PATH" ] && exit 0

if [ "${SKIP_DELIVERABLE_GATE:-0}" = "1" ]; then
  _log_skip_gate deliverable-source-gate "$FILE_PATH"
  exit 0
fi

# 仅管 projects/{产品线}/{项目}/deliverables/*.html 或 projects/{顶级}/deliverables/*.html
case "$FILE_PATH" in
  *projects/*/*/deliverables/*.html|*projects/*/deliverables/*.html)
    case "$FILE_PATH" in
      *archive/*) exit 0 ;;
    esac
    ;;
  *) exit 0 ;;
esac

# 抽项目路径：先试两层（产品线/项目），失败回落到一层（顶级项目）
PROJECT_PATH=$(echo "$FILE_PATH" | sed -nE 's|.*projects/([^/]+/[^/]+)/deliverables/.*|\1|p')
[ -z "$PROJECT_PATH" ] && PROJECT_PATH=$(echo "$FILE_PATH" | sed -nE 's|.*projects/([^/]+)/deliverables/.*|\1|p')
[ -z "$PROJECT_PATH" ] && exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SCRIPTS_DIR="$PROJECT_DIR/projects/$PROJECT_PATH/scripts"
PROJECT_NAME="$PROJECT_PATH"
[ ! -d "$SCRIPTS_DIR" ] && exit 0

# 找 gen / fill / patch 脚本(deliverable 生成或局部修补)
EXISTING=$(find "$SCRIPTS_DIR" -maxdepth 1 -type f \
  \( -name 'gen_*.py' -o -name 'gen_*.js' \
     -o -name 'fill_*.py' -o -name 'fill_*.js' \
     -o -name 'patch_*.py' -o -name 'patch_*.js' \) \
  2>/dev/null | head -5)

[ -z "$EXISTING" ] && exit 0

# 进一步判:脚本目标产物是否匹配当前文件?
# 从脚本名 gen_X_v* / fill_X_* / patch_X_* 提 X,跟目标文件名做匹配:
#   - imap → imap-*.html / imap_*.html
#   - proto → proto-*.html
#   - flow → flow-*.html
#   - prd → 含 PRD / prd-
#   - arch / ppt / handbook 等同理
# 不匹配则放行(避免「项目有任何脚本就拦」过粗)
FILE_BASE=$(basename "$FILE_PATH")
MATCH_SCRIPT=""
for script in $EXISTING; do
  base=$(basename "$script")
  # gen_imap_v6.py → imap;fill_proto_v1.py → proto
  TYPE=$(echo "$base" | sed -nE 's/^(gen|fill|patch)_([a-zA-Z]+)_.*/\2/p')
  [ -z "$TYPE" ] && continue
  case "$FILE_BASE" in
    *"-${TYPE}-"*|*"_${TYPE}_"*|"${TYPE}-"*|"${TYPE}_"*)
      MATCH_SCRIPT="$script"
      break
      ;;
  esac
done

[ -z "$MATCH_SCRIPT" ] && exit 0  # 项目有脚本但没一个目标匹配当前文件,放行

echo "" >&2
echo "🚫 [deliverable-source-gate] 禁止直接 Write/Edit 已脚本化的 HTML 产出物" >&2
echo "   文件:$FILE_BASE" >&2
echo "   匹配脚本:$(basename "$MATCH_SCRIPT")" >&2
echo "" >&2
echo "   → 改源(pages/*.js / fill_*.py / scenes_*.py / patch_*.py),再重生 HTML" >&2
echo "   → 真要小幅文案修改且不重生:export SKIP_DELIVERABLE_GATE=1 后重试" >&2
echo "" >&2
log_event gate deliverable-source-gate block "$FILE_BASE"
exit 2
