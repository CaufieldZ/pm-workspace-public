#!/bin/bash
# Stop hook: 从对话 transcript 提取 [LEARN] 标记 → 追加到 LEARNED.md

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LEARNED_FILE="$PROJECT_DIR/LEARNED.md"

# 读取 stdin 获取 transcript_path
INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('transcript_path', ''))
except:
    print('')
" 2>/dev/null)

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

# 从 transcript 末尾 50 条消息中提取 [LEARN] 标记
ENTRIES=$(python3 - "$TRANSCRIPT_PATH" 2>/dev/null <<'PYEOF'
import sys, json, re

path = sys.argv[1]
lines = []

try:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except:
    sys.exit(0)

# 只看最近 50 条
recent = lines[-50:]
entries = []

for line in recent:
    try:
        msg = json.loads(line.strip())
    except:
        continue
    if msg.get('role') != 'assistant':
        continue
    content = msg.get('content', '')
    if isinstance(content, list):
        text = ' '.join(
            c.get('text', '') for c in content
            if isinstance(c, dict) and c.get('type') == 'text'
        )
    else:
        text = str(content)
    for m in re.finditer(r'\[LEARN\]\s*(.+?)(?=\n\[LEARN\]|\Z)', text, re.DOTALL):
        entry = m.group(1).strip()
        if entry and len(entry) < 500:
            entries.append(entry)

for e in entries:
    print(e)
PYEOF
)

if [ -z "$ENTRIES" ]; then
  exit 0
fi

# 初始化 LEARNED.md（如不存在）
if [ ! -f "$LEARNED_FILE" ]; then
  printf "# Learned Rules\n<!-- 由 stop-learn-capture hook 自动追加。定期整理合并到 soul.md 后清空。 -->\n" > "$LEARNED_FILE"
fi

DATE=$(date '+%Y-%m-%d')
COUNT=0

while IFS= read -r entry; do
  if [ -n "$entry" ]; then
    printf "\n- **[%s]** %s\n" "$DATE" "$entry" >> "$LEARNED_FILE"
    COUNT=$((COUNT + 1))
  fi
done <<< "$ENTRIES"

if [ "$COUNT" -gt 0 ]; then
  echo "[learn-capture] $COUNT 条规则已写入 LEARNED.md" >&2
fi

exit 0
