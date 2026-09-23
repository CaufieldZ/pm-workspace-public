#!/usr/bin/env bash
# 共享：warn 类说明的累加器 + 送达模型的发射器
#
# 为什么需要这层：hook 在 exit 0 时，写到 stderr 的内容**不进模型 context** ——
# 只进 transcript 的 hook_success 记录（供界面展示）与 debug log。warn 类门既想提示模型、
# 又不想阻断，唯一可用的通道是 hookSpecificOutput.additionalContext。
# block 类走 exit 2，那条路上 stderr 本就可达模型，不要再叠一份（调用方负责跳过）。
#
# 用法（hook 入口脚本里）：
#   source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/notes.sh"
#   note_add "一句事实陈述"          # 任意 warn 分支里累加，可多次
#   note_emit "PostToolUse"          # 或 "PreToolUse"；无内容时不输出任何东西
#
# 多个 exit 分支的脚本（Pre 侧 guard 会在子函数里直接 exit 2）用 trap 兜住：
#   trap 'rc=$?; [ "$rc" = "0" ] && note_emit "PreToolUse"' EXIT
#
# ⚠️ 措辞必须是事实陈述，不能写成祈使的系统指令 —— 祈使句会触发模型的 prompt-injection
#    防御，症状是提醒被反弹给用户而非被吸收（工区已有先例，见 user-prompt-warn.sh 文件头）。
set +e

_NOTES=""

note_add() {
  [ -n "$1" ] && _NOTES="${_NOTES}$1"$'\n'
}

# 有内容则往 stdout 打一行 JSON。additionalContext 必须嵌在 hookSpecificOutput 内且
# hookEventName 正确——放顶层会被静默忽略（发了等于没发）。
# stdout 必须只有这一行：多余输出会让整条校验失败被丢弃。
note_emit() {
  [ -z "$_NOTES" ] && return 0
  jq -nc --arg ctx "$_NOTES" --arg ev "${1:-PostToolUse}" \
    '{hookSpecificOutput: {hookEventName: $ev, additionalContext: $ctx}}'
}
