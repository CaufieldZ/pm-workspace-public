#!/usr/bin/env bash
# 共享：工具门 / 路径门 / SKIP 环境变量门
#
# 用法（前提是已 source lib/input.sh + 已 hook_parse_all）：
#   source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"
#
#   require_bash                           # 非 Bash 工具早退 exit 0
#   require_write_or_edit                  # 非 Write/Edit 早退 exit 0
#   is_deliverable_path "$HOOK_FILE_PATH" || exit 0
#   is_excluded_path "$HOOK_FILE_PATH" && exit 0
#   check_skip_env "<gate-name>" "<env-var-name>" "${HOOK_COMMAND:0:120}"
#
# 设计：
# - require_* 直接 exit 0（不返回），调用方少写一行
# - is_*_path 返回码（0 = 是，1 = 否），调用方按需 && / ||
# - check_skip_env 命中 skip 则 _log_skip_gate + exit 0；不命中返回，调用方继续
set +e

require_bash() {
  [ "${HOOK_TOOL_NAME:-}" = "Bash" ] || exit 0
}

require_write_or_edit() {
  case "${HOOK_TOOL_NAME:-}" in
    Write|Edit) return 0 ;;
    *) exit 0 ;;
  esac
}

# 是否 deliverable 路径（projects/ 两层或一层 + examples/）
# 注：本函数 *不* 排除 archive/ — 调用方按需用 is_excluded_path
is_deliverable_path() {
  local p="$1"
  case "$p" in
    */projects/*/*/deliverables/*|*/projects/*/deliverables/*|*/examples/*/deliverables/*) return 0 ;;
    *) return 1 ;;
  esac
}

# 通用排除：archive / __pycache__ / node_modules / .git
is_excluded_path() {
  case "$1" in
    */archive/*|*/__pycache__/*|*/node_modules/*|*/.git/*) return 0 ;;
    *) return 1 ;;
  esac
}

# 讲人话豁免：产物自身是内部文档（audit / fix-plan / imap / interaction）→ 不跑 plain-language。
# 规则表 scripts/lib/lint_exempt.txt 是 bash + Python 双侧单一真相源（Python 侧
# lib/lint_exempt.py），加 / 改豁免只动那张表。Write 路径（post-checks
# pc_plain_language / pc_bullet_density）与 Bash-rebuild 路径（checkers
# check_plain_language_for_bash_recent）共用本函数。
#
# 解析全走 bash 内建（read / case / 参数展开），零 fork；每进程只读一次（§三 K）。
_LINT_EXEMPT_LOADED=""
_LINT_EXEMPT_BASENAME=()
_LINT_EXEMPT_PATHSEG=()

_load_lint_exempt() {
  [ -n "$_LINT_EXEMPT_LOADED" ] && return 0
  _LINT_EXEMPT_LOADED=1
  local rules="${CLAUDE_PROJECT_DIR:-$PWD}/scripts/lib/lint_exempt.txt"
  [ ! -f "$rules" ] && return 0
  local line kind pattern
  # 末行无换行也要收（|| [ -n "$line" ]）
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [ -z "$line" ] && continue
    case "$line" in \#*) continue ;; esac
    kind="${line%%:*}"
    pattern="${line#*:}"
    case "$kind" in
      basename) _LINT_EXEMPT_BASENAME+=("$pattern") ;;
      pathseg)  _LINT_EXEMPT_PATHSEG+=("$pattern") ;;
    esac
  done < "$rules"
}

is_plain_language_exempt() {
  _load_lint_exempt
  local name="${1##*/}" pat
  # ${arr[@]+...} 是 bash 3.2 下空数组 + set -u 的安全展开式
  for pat in ${_LINT_EXEMPT_BASENAME[@]+"${_LINT_EXEMPT_BASENAME[@]}"}; do
    [[ "$name" == $pat ]] && return 0   # pat 不加引号才按 glob 匹配
  done
  for pat in ${_LINT_EXEMPT_PATHSEG[@]+"${_LINT_EXEMPT_PATHSEG[@]}"}; do
    case "/$1/" in */"$pat"/*) return 0 ;; esac
  done
  return 1
}

# SKIP 环境变量门
# 用法：check_skip_env GATE_NAME ENV_VAR_NAME [DETAIL_PREFIX]
#   GATE_NAME      调 _log_skip_gate 用（gate 字符串名，dashboard 分组键）
#   ENV_VAR_NAME   要检查的 env 变量名（如 SKIP_DELIVERABLE_GATE）
#   DETAIL_PREFIX  可选，截断到 120 字符
#
# 行为：
#   - 命中 env=1 或命令行 inline `<VAR>=1` → _log_skip_gate + exit 0
#   - 不命中 → 静默 return
check_skip_env() {
  local gate="$1"
  local var="$2"
  local detail="${3:-}"
  local val
  eval "val=\${${var}:-0}"
  if [ "$val" = "1" ]; then
    _log_skip_gate "$gate" "env  ${detail:0:120}"
    exit 0
  fi
  if [ -n "${HOOK_COMMAND:-}" ] && echo "$HOOK_COMMAND" | grep -qE "\b${var}=1\b"; then
    _log_skip_gate "$gate" "inline  ${HOOK_COMMAND:0:120}"
    exit 0
  fi
}
