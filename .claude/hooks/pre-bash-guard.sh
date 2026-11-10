#!/bin/bash
# PreToolUse: Bash 命令前置守卫（多规则聚合 · 5 hook 合并入口）
#
# 本文件内联规则：
#   A：外网下载的代理判定与注入 → 已迁至 pre-proxy-check.sh（本文件只留文末指针，不重复判）
#   B：git push/remote 用 HTTPS → 阻断（CLAUDE.md「push 用 SSH」）
#
# lib/bash-guards.sh 子函数（原独立 hook 合并，gate 名不变）：
#   risky-op / git-safety / prototype-paradigm-gate
#
# 任一命中 exit 2；跳过：git-safety 支持 SKIP_GIT_SAFETY_GATE=1、prototype-paradigm 支持
# SKIP_PROTOTYPE_PARADIGM_GATE=1（均 env / 命令行前缀双通道）；risky-op 无逃生门（按 block 消息修法走，防绕过安全网）
set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/strip.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/bash-guards.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/notes.sh"

# warn 类说明汇总送达模型（exit 0 时 stderr 模型看不到，见 lib/notes.sh 文件头）。
# 本脚本有多条 exit 0 早退、且 guard 子函数里会直接 exit 2，故用 EXIT trap 兜住所有出口：
# 只在退出码为 0 时发射 —— exit 2（阻断）那条路上 stderr 本就可达模型，不重复注入。
trap 'rc=$?; [ "$rc" = "0" ] && note_emit "PreToolUse"' EXIT

hook_read_input
hook_parse_all
require_bash

CMD="$HOOK_COMMAND"
[ -n "$CMD" ] || exit 0

CMD_STRIPPED=$(strip_command_literals "$CMD")

# === 合并的 3 个 guard（各自判 trigger / SKIP；命中违规直接 exit 2）===
# 放在内联规则前：内联 proxy 规则在「非下载命令」时会 exit 0，会挡掉后续 guard
guard_risky_op "$CMD" "$CMD_STRIPPED"
guard_git_safety "$CMD" "$CMD_STRIPPED"
guard_prototype_paradigm "$CMD" "$CMD_STRIPPED"

# === 规则 B：git push / git remote (add|set-url) 用 HTTPS 拦截 ===
# case 粗筛：不含 github.com 的命令直接跳过（绝大多数），省 SKIP grep + pattern grep。
# 注：用原始 $CMD 而非 $CMD_STRIPPED——strip_command_literals 会把引号内 URL 整体抹成 ""，
#     导致 git remote add origin "https://github.com/..." 里的 URL 消失，gate 静默 fail-open。
case "$CMD" in
  *github.com*)
    if [ "${SKIP_GIT_HTTPS_GATE:-0}" != "1" ] && [[ "$CMD" != *SKIP_GIT_HTTPS_GATE=1* ]]; then
      # 逐段判：动词看 stripped 段（剥引号字面量，echo "...git remote add..." 不误拦），
      # URL 看原始段（git remote add origin "https://..." 引号内的 URL 仍要拦）。
      # 整行 `.*` 会跨命令误判（git push origin dev && curl https://github.com/... 被当成 push over https），故拆两判。
      while IFS= read -r _seg || [ -n "$_seg" ]; do
        _seg_stripped=$(strip_command_literals "$_seg")
        printf '%s' "$_seg_stripped" | grep -qE '\bgit([[:space:]]+[^[:space:]]+)*[[:space:]]+(push|remote[[:space:]]+(add|set-url))([[:space:]]|$)' || continue
        printf '%s' "$_seg" | grep -q 'https://github\.com' || continue
        echo "" >&2
        echo "🚫 [git-https-gate] git push/remote 应用 SSH，不用 HTTPS" >&2
        echo "   $CMD" >&2
        echo "   改成: 当前仓库的 SSH URL（git remote -v 查，形如 git@github.com:<owner>/<repo>.git）" >&2
        echo "   显式跳过: SKIP_GIT_HTTPS_GATE=1 $CMD" >&2
        log_event gate git-https-gate block "${CMD:0:120}"
        exit 2
      done <<EOF
$(split_command_segments "$CMD")
EOF
    fi
    ;;
esac

# === 外网下载的代理处理已迁至 pre-proxy-check.sh ===
# 那条命令的判定与注入由独立 hook 负责（命中即把代理挂上，不再只发提醒）。
# 本文件不再参与 proxy-check——两处同时判会让同一条命令被处理两次。

exit 0
