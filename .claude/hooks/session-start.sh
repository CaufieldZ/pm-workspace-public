#!/bin/bash
# SessionStart hook: 新 session / resume / compact 后，把项目视图 / resume 成本行 / session-state.md 注入新 conversation
#
# Matcher：startup|resume|compact
#   - compact：/compact 后状态恢复（与 PreCompact 互补，PreCompact 在 compact 之前）
#   - startup / resume：注入项目视图，免去每次切项目 ls 一次的开销
#   - 不加 clear：用户 /clear 主动重置，不应自动注入
#
# 输出策略：plain stdout → Claude Code 自动当 additionalContext 注入
#   - 总长度截 9500 字符（10K cap 内，文档说 24K 但保守取一半）
#   - 措辞用陈述句不用祈使句（避免 prompt-injection-defense 误判）
#
# 注入分层：
#   - resume 成本行（闲置时长 · context tok · re-cache ≈ $）：仅 resume 且 stdin 字段齐全
#   - 项目视图（dashboard 「## 项目视图」节，~600 字符）：startup/resume/compact 都注入，省 ls
#   - session-state.md：按需手动 checkpoint 桥梁文件（用户主动 Write 才存在）
#       - 文件存在且非 stale → 注入头部 + stale > 30min warn
#       - 文件存在但 > 72h → rm + echo「auto-cleared」（避免周末隔月残留）
#       - 文件不存在 → 整节不注入（零噪音）
#   - 不注入 dashboard 的 Skill/Agent/路由热度（PM review 工具，每 session 1.8k 纯浪费）

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
STATE="$PROJECT_DIR/.claude/session-state.md"
DASHBOARD="$PROJECT_DIR/.claude/workspace-dashboard.md"

# stdin：SessionStart 事件 JSON（source=startup|resume|compact|clear|fork）。
# tty 守卫：手工裸跑（无管道输入）不卡死，INPUT 留空即全跳过
if [ ! -t 0 ]; then INPUT=$(cat); else INPUT=""; fi

OUT=$(mktemp)
trap "rm -f $OUT" EXIT

# ── resume 成本（量化「切 session vs resume」决策）──────────────────
# 2.1.251+ 起 resume 事件的 stdin 携带 seconds_since_last_response /
# context_tokens / estimated_cache_write_usd。仅 source=resume 且字段齐全时
# 输出一行；startup / compact / 老版本缺字段 / 裸跑 → 零输出零行为变化
if [ -n "$INPUT" ]; then
  RESUME_COST=$(printf '%s' "$INPUT" | jq -r '
    select(.source == "resume") |
    select(has("seconds_since_last_response") and has("estimated_cache_write_usd")) |
    "── resume 成本（session 已闲置 \((.seconds_since_last_response/3600)|floor)h · context \(.context_tokens // "?") tok · re-cache ≈ $\(.estimated_cache_write_usd)）──"' 2>/dev/null)
  if [ -n "$RESUME_COST" ]; then
    echo "$RESUME_COST" >> "$OUT"
    echo "" >> "$OUT"
  fi
fi

# ── workspace-dashboard.md 「## 项目视图」节（Stop hook 每 6h 刷新）─────
# 注入项目清单 + 最近活动 + 阻塞，免去每次切项目 ls。需要 Skill/Agent/路由热度 → 手动 Read 全文。
if [ -s "$DASHBOARD" ]; then
  echo "── 项目视图（workspace-dashboard.md · Stop hook 6h 刷新）──" >> "$OUT"
  awk '/^## 项目视图/{f=1} /^## Skill 使用/{f=0} f' "$DASHBOARD" >> "$OUT"
  echo "" >> "$OUT"
fi

# ── session-state.md（按需手动 checkpoint 桥梁）─────────────────────
# 定位：跨 session / 手动 compact 时的桥梁文件，用户主动 Write 才生效
# 72h 未更新 → 视为过期任务，rm 文件 + echo 提示（避免周末隔月残留误导新 session）
# 文件不存在/纯空白/被清理 → 整节不注入（不打标题、不报警告，零噪音）
# 「实质内容」判定：grep 到至少一个非空白字符，避免 1 byte 换行符这种 placeholder 触发注入
state_has_content() {
  [ -f "$STATE" ] && grep -q '[^[:space:]]' "$STATE" 2>/dev/null
}

# MTIME / AGE_MIN 前置算一次，if / elif 两个分支共用（原 elif 分支重算）
MTIME=$(file_mtime "$STATE")
NOW=$(date +%s)
AGE_MIN=""
[ -n "$MTIME" ] && AGE_MIN=$(( (NOW - MTIME) / 60 ))

STATE_CLEARED_AGE=""
if state_has_content && [ -n "$AGE_MIN" ]; then
  AGE_HOUR=$(( AGE_MIN / 60 ))
  if [ "$AGE_HOUR" -ge 72 ]; then
    rm -f "$STATE"
    STATE_CLEARED_AGE="$AGE_HOUR"
  fi
fi

if [ -n "$STATE_CLEARED_AGE" ]; then
  echo "── session-state.md auto-cleared（${STATE_CLEARED_AGE}h 未更新，已超 72h 阈值）──" >> "$OUT"
  echo "" >> "$OUT"
elif state_has_content; then
  # 文件存在时 AGE_MIN 已算；mtime 取不到则按 0 分钟前处理（对齐原 elif 分支语义）
  [ -z "$AGE_MIN" ] && AGE_MIN=0
  echo "── session-state.md（主线任务状态 · 更新于 ${AGE_MIN} 分钟前 · PreCompact hook 也会注入到 compact summary 输入）──" >> "$OUT"
  if [ "$AGE_MIN" -gt 30 ]; then
    echo "⚠️  已 ${AGE_MIN} 分钟未更新（可能 stale，按 git log + working tree 实际动态判断）" >> "$OUT"
    echo "" >> "$OUT"
  fi
  head -100 "$STATE" >> "$OUT"
  echo "" >> "$OUT"
fi

echo "" >> "$OUT"
echo "── 注入结束（10K 字符上限内，超过部分自动截断）──" >> "$OUT"

# 截 9500 字符注入 stdout
head -c 9500 "$OUT"

log_event hook session-start triggered

exit 0
