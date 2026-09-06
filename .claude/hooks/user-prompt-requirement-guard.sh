#!/bin/bash
# UserPromptSubmit hook: 检测模糊需求动词（无量化目标）时注入 PM-Gate 提醒
#
# 触发：用户 prompt 同时满足以下条件——
#   1. 含 PRD / 需求 / 场景清单 / 写需求 / scene-list 等产出物关键词
#   2. 含 优化 / 提升 / 改善 / 增加 / 降低 / 完善 / 增强 / 调整 等量化动词
#   3. 不含任何数字（无量化目标）
# 输出：stdout JSON {systemMessage}（注入 Claude context 的工作提示，用户不可见）
#   systemMessage 是唯一合法通道：不阻断、不 exit 2、stderr 在 exit 0 时被丢弃。
# Escape：无 SKIP 机制（提醒非阻断，无需跳过）

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/dedup.sh"

INPUT=$(cat)
hook_parse_all

# 提取用户 prompt（UserPromptSubmit 的 stdin JSON 含 prompt 字段）
PROMPT=$(printf '%s' "$INPUT" | jq -r '.prompt // ""' 2>/dev/null)
[ -z "$PROMPT" ] && exit 0

# ── 条件 1：含产出物关键词 ───────────────────────────────────────────
echo "$PROMPT" | grep -qE 'PRD|需求文档|写需求|需求|场景清单|scene.list' || exit 0

# ── 条件 2：含量化动词 ───────────────────────────────────────────────
echo "$PROMPT" | grep -qE '优化|提升|改善|增加|降低|完善|增强|调整|减少|提高|加速|缩短' || exit 0

# ── 条件 3：不含数字（无量化目标）───────────────────────────────────
# 含数字 → 用户已给量化目标，不提醒
echo "$PROMPT" | grep -qE '[0-9]' && exit 0

# 节流：10 分钟内只提醒一次（连续写需求时段不被反复打扰；命中即消耗配额，SKIP 无）
_dedup_if_fresh pm-gate-reminder 600 "global" && exit 0

MSG="[pm-gate-reminder] 检测到需求动词但缺乏量化目标——产出物目标/成功标准章节需要具体数字，否则 Viability 无法验证。正确写法示例：❌「提升主播留存率」✅「主播次日留存从 42% → 55%（Q3 目标，基于历史基线）」。PM-GATE Viability 检查项：核心指标 + 具体数字 + 判断成功的边界值。跳过条件：baseline 已含结论 / 改 ≤1 场景 / 方案型项目。"

# stdout 只输出 systemMessage JSON（注入 Claude context，不给用户显示，不阻断）
jq -nc --arg msg "$MSG" '{systemMessage: $msg}'

log_event hook pm-gate-reminder triggered "prompt_len=${#PROMPT}"

exit 0
