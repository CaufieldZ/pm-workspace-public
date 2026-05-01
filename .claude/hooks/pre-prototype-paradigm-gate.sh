#!/bin/bash
# PreToolUse hook: Bash 命中 gen_proto_skeleton / generate_skeleton 时强制范式门
#
# 拦下「跳过 Step 0 直接裸跑 generate_skeleton」的偷懒（v1 翻车的根因）
# 检测条件：
#   1. Bash 命令含 gen_proto_skeleton 或 generate_skeleton(
#   2. 命令含项目名（projects/{xxx}/）
#   3. 检查 projects/{xxx}/inputs/scene-anchors.md 或 .claude/session-state.md 是否含「范式」字眼
#   4. 都没 → exit 2 阻断 + stderr 提示先跑 check_paradigm.py

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

[ "$TOOL_NAME" != "Bash" ] && exit 0

CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# 触发条件：调骨架生成的三种形式
#   1) python3 .../gen_proto_v{N}.py（项目级骨架脚本）
#   2) import gen_proto_skeleton（脚本内或 -c）
#   3) generate_skeleton(...)（直接调函数）
if ! echo "$CMD" | grep -qE 'gen_proto_v[0-9]+\.py|gen_proto_skeleton|generate_skeleton\('; then
  exit 0
fi

# 抽出项目名（projects/{xxx}/）
PROJECT=$(echo "$CMD" | grep -oE 'projects/[a-zA-Z0-9_-]+' | head -1 | sed 's|projects/||')

if [ -z "$PROJECT" ]; then
  # 没找到项目名 → 软提示但放行
  echo "⚠️  pre-prototype-paradigm-gate: 命中 generate_skeleton 但未识别项目名，跳过范式门检测" >&2
  exit 0
fi

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
PROJ_DIR="$ROOT/projects/$PROJECT"
ANCHORS="$PROJ_DIR/inputs/scene-anchors.md"
SESSION="$ROOT/.claude/session-state.md"

# 范式门跳过条件（任一满足即放行）：
#   1) scene-anchors.md 含「范式」字眼（新项目走完 Step 0 后写入）
#   2) session-state.md 含「范式: ...」（元工具会写）
#   3) deliverables/ 已存在 proto-*.html（迭代场景，范式已锁定）
HAS_PARADIGM=0
if [ -f "$ANCHORS" ] && grep -q "范式" "$ANCHORS" 2>/dev/null; then
  HAS_PARADIGM=1
fi
if [ -f "$SESSION" ] && grep -qE "范式[:：]" "$SESSION" 2>/dev/null; then
  HAS_PARADIGM=1
fi
if ls "$PROJ_DIR/deliverables/proto-"*.html >/dev/null 2>&1; then
  HAS_PARADIGM=1
fi

if [ "$HAS_PARADIGM" -eq 0 ]; then
  printf '═══ pre-prototype-paradigm-gate fail ═══\n\n' >&2
  printf '❌ 检测到 generate_skeleton / gen_proto_skeleton 调用，但项目 [%s] 未跑 Step 0 范式门\n\n' "$PROJECT" >&2
  printf '→ 先跑：python3 .claude/skills/prototype/scripts/check_paradigm.py %s\n' "$PROJECT" >&2
  printf '→ 推断结果记到 projects/%s/inputs/scene-anchors.md（含「范式: xxx」一行）\n' "$PROJECT" >&2
  printf '→ 或更新 .claude/session-state.md 含「范式: xxx」\n' >&2
  printf '→ 用户口头确认范式后才允许跑 generate_skeleton\n\n' >&2
  printf '（v1 翻车根因：跳过范式门默认 view-page，推倒重来。本 hook 防同款）\n' >&2
  log_event gate prototype-paradigm-gate block "$PROJECT"
  exit 2
fi

log_event gate prototype-paradigm-gate triggered "$PROJECT"
exit 0
