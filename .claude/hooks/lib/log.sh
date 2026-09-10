#!/usr/bin/env bash
# 共享日志函数：被所有 hook source，统一埋点到 .claude/logs/usage.jsonl
#
# 用法：
#   source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
#   log_event TYPE NAME ACTION [DETAIL] [HITS] [DUR_MS] [HITS_WORDS]
#
# TYPE   : hook | gate | skill | route | agent
#   hook  : 通用检查器（cjk-punct / context-static-lint / risky-op...）
#   gate  : 强阻断闸（git-safety / prototype-paradigm-gate...）
#   skill : SKILL.md frontmatter 脚本完成态（lib/skill_log.py emit）
#   route : CLAUDE.md 快捷路由表脚本调用（lib/route_log.py emit）
#   agent : Task tool sub-agent 调度（pre-agent-log.sh emit）
# NAME   : cjk-punct / prd 等（dashboard 按 name 聚合）
# ACTION : triggered | warn | block | clean | skip | completed | failed
# DETAIL : 可选，文件路径或命令摘要（≤ 200 char）
# HITS   : 可选，命中计数（如 CJK 命中 3 处半角标点）
# DUR_MS : 可选，checker / 脚本耗时毫秒（runner.sh 计时后传，定位慢闸）
# HITS_WORDS : 可选，命中词明细 JSON 数组串（如 '["赋能","闭环"]'），去重限 50、整 ≤200 char；
#              词表防腐化用（analyze_term_hits 反查死词 / 漏收）。第 5 位 HITS 计数语义不动
#
# session_id：不走参数，log_event 自动读 $CLAUDE_CODE_SESSION_ID env（Claude Code
#   给整个进程树暴露，bash / python 子进程都继承同一值）→ 事件流串成会话主键
#
# 输出格式（JSONL）：
#   {"ts":"2026-05-01T03:15:22+08:00","type":"hook","name":"cjk-punct","action":"warn",
#    "detail":"projects/community/scene-list.md","hits":3,
#    "session_id":"341b60a1-...","dur_ms":42,"hits_words":["赋能","闭环"]}
#
# 设计：静默失败（埋点不应阻塞业务逻辑）；原子 append（< 4KB 单行写 POSIX 保证原子）
set +e

log_event() {
  local type="$1"
  local name="$2"
  local action="$3"
  local detail="${4:-}"
  local hits="${5:-}"
  local dur_ms="${6:-}"
  local hits_words="${7:-}"
  local sid="${CLAUDE_CODE_SESSION_ID:-}"

  # 测试态短路：test-hooks.sh export CLAUDE_HOOK_TEST=1，回归跑不污染 usage.jsonl
  [ -n "${CLAUDE_HOOK_TEST:-}" ] && return 0

  [ -z "$type" ] || [ -z "$name" ] || [ -z "$action" ] && return 0

  local log_dir="$(_hook_root)/.claude/logs"
  # SIGPIPE 竞态防御：head/管道截断中断脚本后，trap 里 $(...) 命令替换可能捕获
  # echo 残留（含换行 / ANSI 转义），污染 log_dir → mkdir 会创建怪目录树。校验后跳过。
  case "$log_dir" in
    *$'\n'*|*$'\e'*) return 0 ;;
  esac
  case "$log_dir" in
    */.claude/logs) ;;
    *) return 0 ;;
  esac
  mkdir -p "$log_dir" 2>/dev/null || return 0

  # 截断 detail（避免单条 event 过大）
  if [ ${#detail} -gt 200 ]; then
    detail="${detail:0:197}..."
  fi

  # jq 构造单行 JSON（启动 ~1ms，远低于 python3 冷启动 ~30ms；settings.json 已 allow jq）。
  # hits / dur_ms 能转 int 走 number，否则保留字符串（复刻原 try/except）；
  # hits_words 是已 dump 的 JSON 数组串，--argjson 解析后去重 + 限 50（解析失败则整条不带该字段）。
  local ts
  ts=$(date '+%Y-%m-%dT%H:%M:%S+08:00')
  jq -cn \
    --arg ts "$ts" --arg type "$type" --arg name "$name" --arg action "$action" \
    --arg detail "$detail" --arg hits "$hits" --arg dur_ms "$dur_ms" \
    --arg hits_words "$hits_words" --arg sid "$sid" '
    {ts: $ts, type: $type, name: $name, action: $action}
    + (if $detail != "" then {detail: $detail} else {} end)
    + (if $hits != "" then {hits: ($hits | (tonumber? // .))} else {} end)
    + (if $dur_ms != "" then ((($dur_ms | tonumber?) ) as $d | if $d != null then {dur_ms: $d} else {} end) else {} end)
    + (if $hits_words != "" then
         (($hits_words | fromjson?) as $w
          | if ($w | type) == "array"
            then {hits_words: ([$w[] | select(type == "string" and . != "")] | unique | .[0:50])}
            else {} end)
       else {} end)
    + (if $sid != "" then {session_id: $sid} else {} end)
  ' >> "$log_dir/usage.jsonl" 2>/dev/null
  return 0
}

# 文件 mtime（秒级 epoch）。跨平台：BSD stat -f %m / GNU stat -c %Y。失败 echo 空。
file_mtime() {
  stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null
}

# workspace root 解析：CLAUDE_PROJECT_DIR > 脚本自身路径推断 > pwd 兜底。
# 不用 pwd 作首选 fallback：cwd 在子项目目录（如 projects/community/leaderboard/）时会写错地方。
# BASH_SOURCE[0] 在函数体内指定义文件（log.sh）路径，被 log_event / _log_skip_gate 共用。
_hook_root() {
  if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    printf '%s' "$CLAUDE_PROJECT_DIR"
  else
    local r
    r="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." 2>/dev/null && pwd)"
    [ -z "$r" ] && r="$(pwd)"
    printf '%s' "$r"
  fi
}

# 记录 gate 跳过：写 usage.jsonl（skip action）+ 老 skip-gates.log
# 用法：_log_skip_gate GATE_NAME "detail"
_log_skip_gate() {
  local gate_name="$1"
  local detail="$2"
  [ -n "${CLAUDE_HOOK_TEST:-}" ] && return 0
  log_event gate "$gate_name" skip "$detail"
  local log_dir="$(_hook_root)/.claude/logs"
  case "$log_dir" in
    *$'\n'*|*$'\e'*) return 0 ;;
  esac
  case "$log_dir" in
    */.claude/logs) ;;
    *) return 0 ;;
  esac
  mkdir -p "$log_dir" 2>/dev/null || return 0
  echo "$(date '+%Y-%m-%d %H:%M:%S')  $gate_name  $detail" >> "$log_dir/skip-gates.log"
}
