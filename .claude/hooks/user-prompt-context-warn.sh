#!/bin/bash
# UserPromptSubmit hook: context 缓存读取超阈值时提醒 /compact
#
# 触发：每次用户发消息前
# 数据源：transcript JSONL 最后一条 assistant message 的 message.usage.cache_read_input_tokens
#         （= 下一轮预计 cache hit 的 token 数，最贴近"缓存读取"心智模型）
# 阈值：350000（用户设定，约 1M context 的 35%）
# 输出：stdout JSON `{systemMessage}`（给用户的警告，不注入 Claude context、不阻断）。
#   禁 stderr：UserPromptSubmit 在 exit 0 时 stderr 被静默丢弃，警告到不了用户。
#   禁 stdout 纯文本：会被当 additionalContext 注入 context。只有 systemMessage 字段两不沾。

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"

INPUT=$(cat)
hook_parse_all

[ -f "$HOOK_TRANSCRIPT" ] || exit 0

THRESHOLD=350000

TOKENS=$(python3 <<PY 2>/dev/null
import json
path = r"""$HOOK_TRANSCRIPT"""
try:
    with open(path) as f:
        lines = f.readlines()
except Exception:
    raise SystemExit(0)
for line in reversed(lines):
    try:
        d = json.loads(line)
    except Exception:
        continue
    u = (d.get("message") or {}).get("usage") or {}
    cr = u.get("cache_read_input_tokens", 0) or 0
    if cr > 0:
        print(cr)
        break
PY
)

[ -z "$TOKENS" ] && exit 0
[ "$TOKENS" -lt "$THRESHOLD" ] && exit 0

PCT=$(( TOKENS * 100 / 1000000 ))
TOKENS_K=$(( TOKENS / 1000 ))
MSG="⚠️  context 缓存读取 ${TOKENS_K}K token（~${PCT}% of 1M），建议 /compact 一次（手动 compact 质量优于自动）"
# stdout 必须只有这行 JSON（systemMessage = 用户可见警告，不进 context、不阻断）
jq -nc --arg msg "$MSG" '{systemMessage: $msg}'

log_event hook context-warn triggered "cache_read=${TOKENS}"

exit 0
