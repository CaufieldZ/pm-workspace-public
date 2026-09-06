#!/usr/bin/env bash
# 共享：跑外部 checker + 自动 tempfile + 失败时 stderr 输出
#
# 用途：post-audit-fast / post-prototype-audit / post-pm-visual-overreach 等都做
#       「跑 checker → mktemp 收集输出 → 失败时 cat/head/tail 到 stderr → cleanup」
#       原本 5 处 tempfile 风格不一（/tmp 固定名 / $$ PID / mktemp），统一成 lib
#
# 用法：
#   source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/runner.sh"
#
#   # 简单模式：失败 cat 全输出 + log_event block + exit 2；成功 log_event clean + return
#   run_checker_block GATE_NAME DETAIL bash /path/to/check.sh "$FILE"
#
#   # 自定义失败处理（如要 head -30 而非 cat 全部，加额外提示）：
#   run_checker_capture bash /path/to/check.sh "$FILE"  # 设 RC + TMPOUT 变量
#   if [ "$RC" -ne 0 ]; then
#     head -30 "$TMPOUT" >&2
#     log_event hook X block "$FILE"
#     exit 2
#   fi
#
# 设计：
# - 每次调 run_checker_capture 创建 mktemp，自动注册到 _HOOK_TMPS 数组
# - shell 退出（包括 exit 2）时 trap 统一清理
# - run_checker_block 是 high-level wrapper，常见场景一行搞定
set +e

_HOOK_TMPS=()
_hook_cleanup_tmps() { rm -f "${_HOOK_TMPS[@]}" 2>/dev/null; }

# 低阶：跑 checker，输出捕获到 mktemp 文件
# 设置：TMPOUT（路径）+ RC（退出码）+ DUR_MS（耗时毫秒）
# 调用方按需自定义失败处理逻辑
# 计时用 bash 内建 $SECONDS（零子进程，bash 3.2 无 EPOCHREALTIME / BSD date 无 %N）：
#   整秒分辨率，只为定位「多秒慢闸」——亚秒 checker 落 0ms 不关心，正是想要的过滤
run_checker_capture() {
  TMPOUT=$(mktemp -t hook.XXXXXX)
  _HOOK_TMPS+=("$TMPOUT")
  trap _hook_cleanup_tmps EXIT
  local _t0=$SECONDS
  "$@" > "$TMPOUT" 2>&1
  RC=$?
  DUR_MS=$(( (SECONDS - _t0) * 1000 ))
  return 0
}

# 高阶：跑 checker，失败 cat 全输出 + log_event block + exit 2；成功 log_event clean + return 0
# 用法：run_checker_block GATE_NAME DETAIL CMD ARGS...
run_checker_block() {
  local gate="$1"; shift
  local detail="$1"; shift
  run_checker_capture "$@"
  if [ "$RC" -ne 0 ]; then
    cat "$TMPOUT" >&2
    log_event hook "$gate" block "$detail" "" "$DUR_MS"
    exit 2
  fi
  log_event hook "$gate" clean "$detail" "" "$DUR_MS"
  return 0
}
