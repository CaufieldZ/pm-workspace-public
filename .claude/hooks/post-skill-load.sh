#!/usr/bin/env bash
# PostToolUse hook: 监听 Read .claude/skills/{name}/SKILL.md → 记录 skill 触发
#
# Skill 触发的可观测信号：模型读了对应 SKILL.md
# 不拦截，纯记录。写入 .claude/logs/usage.jsonl
#
# ⚠️ 不可删：是 dashboard half-life signal 唯一数据源 + jsonl 里唯一项目↔Skill 关联

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"

INPUT=$(cat)

# 绝大多数 Read 不是 guide 文件：raw input 不含任一字样 → case 早退（零 fork），
# 省掉 hook_parse_all 的 jq + 下方 sed。含字样的才走精确解析。
case "$INPUT" in
  *SKILL.md*|*info-ownership.md*|*SCRIPTS_WRITING.md*|*HOOK_WRITING.md*|*runbooks*|*quickref*|*AUTHORING-RULES.md*|*AI中台-规范及帮助文档*) ;;
  *) exit 0 ;;
esac

hook_parse_all

[ "$HOOK_TOOL_NAME" != "Read" ] && exit 0

FILE_PATH="$HOOK_FILE_PATH"
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# guide-read 埋点（跨 session 持久）：skill-load-gate / required-read-gate 的 6h fallback 查这条，
# 解决「上轮读过 guide，compact / 换 session 后 transcript 清零，再编辑同一产物又被拦」的失忆误报。
# 覆盖 pre-writeedit-guards 强制必读的 guide 全集；detail 存相对路径供 endswith 精确匹配。
case "$FILE_PATH" in
  */.claude/skills/*/SKILL.md|*/.claude/runbooks/info-ownership.md|*/.claude/runbooks/*.md|*/scripts/SCRIPTS_WRITING.md|*/.claude/hooks/HOOK_WRITING.md|*/.claude/hooks/HOOK_WRITING-quickref.md|*/.claude/skills/*/references/*-quickref.md|*/hub/AUTHORING-RULES.md|*/hub/AI中台-规范及帮助文档/*.md)
    log_event guide guide-read read "${FILE_PATH#$ROOT/}"
    ;;
esac

# 以下仅 SKILL.md 维持原 skill-triggered 埋点（dashboard half-life 唯一数据源，不可动）
SKILL_NAME=$(echo "$FILE_PATH" | sed -nE 's|.*/\.claude/skills/([^/]+)/SKILL\.md$|\1|p')
[ -z "$SKILL_NAME" ] && exit 0

# 尝试反推当前项目（SKILL.md 路径里没项目信息）
# fallback 链：① git 未提交变更里第一个 projects/{X}/{Y} 路径（最准，跟当前作业一致）
#              ② session-state.md 「项目: xxx」字段（用户主动 checkpoint 才有）
#              ③ 空字符串（log_event 容忍）
PROJECT=""

if command -v git >/dev/null 2>&1 && [ -d "$ROOT/.git" ]; then
  PROJECT=$(cd "$ROOT" && git status --porcelain 2>/dev/null \
    | awk '{print $NF}' \
    | grep -oE 'projects/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+' \
    | head -1 \
    | sed 's|projects/||')
fi

if [ -z "$PROJECT" ]; then
  STATE_FILE="$ROOT/.claude/session-state.md"
  if [ -f "$STATE_FILE" ]; then
    PROJECT=$(grep -oE '项目[:：][[:space:]]*[a-zA-Z0-9_/-]+' "$STATE_FILE" 2>/dev/null | head -1 | sed -E 's/项目[:：][[:space:]]*//')
  fi
fi

log_event skill "$SKILL_NAME" triggered "$PROJECT"
exit 0
