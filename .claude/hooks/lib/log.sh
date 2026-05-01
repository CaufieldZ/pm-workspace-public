#!/usr/bin/env bash
# 共享日志函数：被所有 hook source，统一埋点到 .claude/logs/usage.jsonl
#
# 用法：
#   source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
#   log_event TYPE NAME ACTION [DETAIL] [HITS]
#
# TYPE   : hook | skill | gate
# NAME   : cjk-punct / prd / wiki-push-gate 等
# ACTION : triggered | warn | block | clean | skip
# DETAIL : 可选，文件路径或命令摘要（≤ 200 char）
# HITS   : 可选，命中计数（如 CJK 命中 3 处半角标点）
#
# 输出格式（JSONL）：
#   {"ts":"2026-05-01T03:15:22+08:00","type":"hook","name":"cjk-punct","action":"warn",
#    "detail":"projects/community/scene-list.md","hits":3}
#
# 设计：静默失败（埋点不应阻塞业务逻辑）；原子 append（< 4KB 单行写 POSIX 保证原子）

log_event() {
  local type="$1"
  local name="$2"
  local action="$3"
  local detail="${4:-}"
  local hits="${5:-}"

  [ -z "$type" ] || [ -z "$name" ] || [ -z "$action" ] && return 0

  local log_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/logs"
  mkdir -p "$log_dir" 2>/dev/null || return 0

  # 截断 detail（避免单条 event 过大）
  if [ ${#detail} -gt 200 ]; then
    detail="${detail:0:197}..."
  fi

  python3 - "$type" "$name" "$action" "$detail" "$hits" "$log_dir/usage.jsonl" 2>/dev/null <<'PYEOF'
import sys, json, datetime
type_, name, action, detail, hits, log_path = sys.argv[1:7]
tz = datetime.timezone(datetime.timedelta(hours=8))
ts = datetime.datetime.now(tz).isoformat(timespec='seconds')
event = {"ts": ts, "type": type_, "name": name, "action": action}
if detail:
    event["detail"] = detail
if hits:
    try:
        event["hits"] = int(hits)
    except ValueError:
        event["hits"] = hits
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(event, ensure_ascii=False) + "\n")
PYEOF
  return 0
}

# 兼容函数：原 3 个 gate hook 调用的 _log_skip 升级到新埋点，同时写老 skip-gates.log
# 老调用：_log_skip "env  $COMMAND"   （gate 名从脚本名推断）
# 新调用支持指定 gate 名：_log_skip_gate GATE_NAME "detail"
_log_skip_gate() {
  local gate_name="$1"
  local detail="$2"
  log_event gate "$gate_name" skip "$detail"
  local log_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/logs"
  mkdir -p "$log_dir" 2>/dev/null || return 0
  echo "$(date '+%Y-%m-%d %H:%M:%S')  $gate_name  $detail" >> "$log_dir/skip-gates.log"
}
