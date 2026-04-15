#!/usr/bin/env bash
# 推送会议纪要到 Slack channel
# 用法: slack-push.sh <channel> <markdown-file> [format]
#   channel: Slack channel 名称 (不带 #) 或 channel ID
#   markdown-file: 会议纪要 markdown 文件路径
#   format: full (全文) | summary (摘要+action items, 默认)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "错误: 未找到 .env 文件" >&2
  exit 1
fi

source "$ENV_FILE"

if [[ -z "${SLACK_BOT_TOKEN:-}" ]]; then
  echo "错误: SLACK_BOT_TOKEN 未设置" >&2
  exit 1
fi

CHANNEL="${1:?用法: slack-push.sh <channel> <file> [full|summary]}"
FILE="${2:?用法: slack-push.sh <channel> <file> [full|summary]}"
FORMAT="${3:-summary}"

if [[ ! -f "$FILE" ]]; then
  echo "错误: 文件不存在: $FILE" >&2
  exit 1
fi

CONTENT=$(cat "$FILE")
FILENAME=$(basename "$FILE")

# 提取标题 (第一个 # 开头的行)
TITLE=$(grep -m1 '^#' "$FILE" | sed 's/^#\+ *//' || echo "$FILENAME")

if [[ "$FORMAT" == "summary" ]]; then
  # 提取摘要: 关键决策 + Action Items 部分
  SUMMARY=""

  # 提取 "关键决策" 或 "决策" 部分
  DECISIONS=$(awk '/^##.*决策/,/^##[^#]/' "$FILE" | head -20)
  if [[ -n "$DECISIONS" ]]; then
    SUMMARY+="$DECISIONS"$'\n\n'
  fi

  # 提取 "Action Items" 或 "待办" 或 "行动项" 部分
  ACTIONS=$(awk '/^##.*(Action|待办|行动项|TODO)/,/^##[^#]/' "$FILE" | head -30)
  if [[ -n "$ACTIONS" ]]; then
    SUMMARY+="$ACTIONS"
  fi

  # 如果都没提取到, fallback 到全文前 40 行
  if [[ -z "$SUMMARY" ]]; then
    SUMMARY=$(head -40 "$FILE")
    SUMMARY+=$'\n\n_(截断，完整内容见原文)_'
  fi

  POST_TEXT="$SUMMARY"
else
  POST_TEXT="$CONTENT"
fi

# 构建 Slack Block Kit payload
ESCAPED_TITLE=$(echo "$TITLE" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")
ESCAPED_TEXT=$(echo "$POST_TEXT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")

PAYLOAD=$(cat <<ENDJSON
{
  "channel": "$CHANNEL",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": $(echo "$TITLE" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": $(echo "$POST_TEXT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")
      }
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "📎 来源: \`$FILENAME\` | 格式: $FORMAT"
        }
      ]
    }
  ]
}
ENDJSON
)

# 发送
RESPONSE=$(curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

OK=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('ok', False))")

if [[ "$OK" == "True" ]]; then
  TS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('ts',''))")
  echo "✅ 已推送到 #$CHANNEL (ts: $TS)"
else
  ERROR=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('error','unknown'))")
  echo "❌ 推送失败: $ERROR" >&2
  echo "$RESPONSE" >&2
  exit 1
fi
