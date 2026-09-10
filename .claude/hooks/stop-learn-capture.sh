#!/bin/bash
# Stop hook: 从对话 transcript 提取 [LEARN] 标记 → 持锁去重追加到 LEARNED.md
# 沉淀失败（超长/格式/重复）时通过 hookSpecificOutput.additionalContext 反馈给模型，
# 让它重写合规 [LEARN]；成功静默。stop_hook_active=true 时不反馈（防 continue 循环）。
#
# 读 existing 去重 + 持锁追加写收进同一个 python 进程（fcntl.flock），
# 避免与手工整理清空 LEARNED.md 的跨进程竞态丢条。
set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LEARNED_FILE="${LEARNED_FILE:-$PROJECT_DIR/LEARNED.md}"

# 读取 stdin 获取 transcript_path + stop_hook_active（走 lib 单字段函数）
INPUT=$(cat)
TRANSCRIPT_PATH=$(hook_transcript_path)

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

# 前置短路：transcript 无 [LEARN] 标记 → 本轮无沉淀，跳过 python3（省冷启 + 整 transcript 解析）。
# python 逻辑只处理含 [LEARN] 的行，grep 预筛是其必要条件；JSONL 里 [ ] 不被 JSON 转义，能命中。
grep -q '\[LEARN\]' "$TRANSCRIPT_PATH" 2>/dev/null || exit 0

STOP_ACTIVE=$(hook_stop_active)

# 提取 [LEARN] → flock 锁内重读 existing 去重 → 追加写；统计丢弃 + 仅丢弃时反馈
python3 - "$TRANSCRIPT_PATH" "$LEARNED_FILE" "$STOP_ACTIVE" 2>/dev/null <<'PYEOF'
import sys, json, re, os, fcntl, datetime

path = sys.argv[1]
learned_file = sys.argv[2]
stop_active = (sys.argv[3] if len(sys.argv) > 3 else "").lower() in ("true", "1")
date = datetime.date.today().isoformat()

try:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except Exception:
    sys.exit(0)

candidates = []
seen_in_run = set()
dropped = {"too_long": [], "format": [], "dup_run": []}

for line in lines:
    try:
        msg = json.loads(line.strip())
    except Exception:
        continue
    # 兼容两种 schema：顶层 role 或 type='assistant' + 嵌套 message.role
    if msg.get('type') == 'assistant':
        m = msg.get('message', msg)
    elif msg.get('role') == 'assistant':
        m = msg
    else:
        continue
    content = m.get('content', '')
    if isinstance(content, list):
        text = ' '.join(
            c.get('text', '') for c in content
            if isinstance(c, dict) and c.get('type') == 'text'
        )
    else:
        text = str(content)
    # 只匹配单行 [LEARN]，避免跨段落把后续正文吞进去
    for mm in re.finditer(r'^\s*\[LEARN\]\s+(.+?)\s*$', text, re.MULTILINE):
        entry = mm.group(1).strip()
        if not entry:
            continue
        if len(entry) >= 500:
            dropped["too_long"].append(entry[:50])
            continue
        if entry.startswith('```') or entry.startswith('—') or entry.startswith('--'):
            dropped["format"].append(entry[:50])
            continue
        if entry in seen_in_run:
            dropped["dup_run"].append(entry[:50])
            continue
        seen_in_run.add(entry)
        candidates.append(entry)

# 无任何 [LEARN] 痕迹（candidates + 全部丢弃类都空）→ 静默，不打扰
has_anything = bool(candidates) or any(dropped.values())
if not has_anything:
    sys.exit(0)

# 确保文件存在（不存在则建空，header 在锁内补，防并发初始化覆盖）
if not os.path.exists(learned_file):
    open(learned_file, 'a', encoding='utf-8').close()

PATTERN = re.compile(r'^- \*\*\[\d{4}-\d{2}-\d{2}\]\*\* (.+)$')
new_entries = []
dup_existing = []
if candidates:
    with open(learned_file, 'r+', encoding='utf-8') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.seek(0, os.SEEK_END)
            if f.tell() == 0:
                f.write("# Learned Rules\n<!-- 由 stop-learn-capture hook 自动追加。定期整理合并到 runbook / SKILL.md / hook / 脚本 docstring 后清空。 -->\n")
            f.seek(0)
            existing = set()
            for ln in f:
                mm = PATTERN.match(ln.strip())
                if mm:
                    existing.add(mm.group(1).strip())
            for e in candidates:
                if e in existing:
                    dup_existing.append(e[:50])
                else:
                    new_entries.append(e)
            if new_entries:
                f.seek(0, os.SEEK_END)
                for e in new_entries:
                    f.write(f"\n- **[{date}]** {e}\n")
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

# 只在"有丢弃"且"非 continue 循环（stop_active=false）"时反馈 additionalContext；
# 成功沉淀静默（避免每个 [LEARN] turn 都多一轮 continue）
dropped["dup_existing"] = dup_existing
LABELS = {"too_long": "超长(≥500字)", "format": "格式(```/—)", "dup_run": "本turn重复", "dup_existing": "已存在"}
drop_reasons = [f"{LABELS[k]} {len(v)}" for k, v in dropped.items() if v]
drop_total = sum(len(v) for v in dropped.values())

if drop_total > 0 and not stop_active:
    prefix = f"[LEARN 沉淀] ✓ 沉淀 {len(new_entries)} 条 · " if new_entries else "[LEARN 沉淀] "
    feedback = f"{prefix}✗ 弃 {drop_total} 条（{' / '.join(drop_reasons)}）。约束：单行 · <500字 · 不以 ``` 或 — 开头。可重写合规 [LEARN] 补上"
    print(json.dumps({"hookSpecificOutput": {"additionalContext": feedback}}, ensure_ascii=False))
PYEOF

exit 0
