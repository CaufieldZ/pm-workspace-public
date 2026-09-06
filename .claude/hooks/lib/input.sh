#!/usr/bin/env bash
# 共享 hook 入参解析：被所有读 stdin JSON 的 hook source，避免每个 hook 各启 python3 解析
#
# 用法（推荐一次性解析）：
#   source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
#   INPUT=$(cat); hook_parse_all
#   # 之后用 $HOOK_TOOL_NAME / $HOOK_FILE_PATH / $HOOK_COMMAND / $HOOK_TRANSCRIPT
#
# 单字段解析（调用方已 INPUT=$(cat)）：
#   TOOL_NAME=$(hook_tool_name)
#   FILE_PATH=$(hook_file_path)
#   CMD=$(hook_command)
#   TRANS=$(hook_transcript_path)
#
# 设计：
# - 用 jq 解析（启动 ~1ms，远低于 python3 冷启动 ~30ms；settings.json 已 allow jq）
# - 解析失败返回空串（不阻塞 hook，调用方按空判断）
# - hook_parse_all 用 jq @sh（single-quote escape）防 JSON 内容里的 ' " ` $() 注入 eval
# - 所有函数都假定 $INPUT 已设置（调用方 cat 一次）
set +e

hook_tool_name() {
  printf '%s' "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null
}

hook_file_path() {
  printf '%s' "$INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null
}

hook_command() {
  printf '%s' "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null
}

hook_transcript_path() {
  printf '%s' "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null
}

hook_stop_active() {
  printf '%s' "$INPUT" | jq -r 'if .stop_hook_active then "true" else "false" end' 2>/dev/null
}

# 一次性解析：把 4 个字段 eval 进当前 shell（HOOK_TOOL_NAME / HOOK_FILE_PATH / HOOK_COMMAND / HOOK_TRANSCRIPT）
# jq @sh 输出 bash-safe 的 single-quote-escaped 赋值语句，避免 JSON 内容里的 ' " ` $ 等被 shell 解释。
# 解析失败（jq 吞错 → eval 空串）时，4 个变量保持下方预置的空值，与原 python except 分支一致。
hook_parse_all() {
  HOOK_TOOL_NAME=""; HOOK_FILE_PATH=""; HOOK_COMMAND=""; HOOK_TRANSCRIPT=""
  if command -v jq >/dev/null 2>&1; then
    eval "$(printf '%s' "$INPUT" | jq -r '
      "HOOK_TOOL_NAME=" + (.tool_name // "" | @sh),
      "HOOK_FILE_PATH=" + (.tool_input.file_path // "" | @sh),
      "HOOK_COMMAND=" + (.tool_input.command // "" | @sh),
      "HOOK_TRANSCRIPT=" + (.transcript_path // "" | @sh)' 2>/dev/null)"
  else
    # jq 缺失兜底：不 fallback 会让 $HOOK_COMMAND 恒空 → 所有 PreToolUse 安全门（force-push /
    # reset --hard 等）静默 fail-open。用 python3（本仓强依赖）+ shlex.quote 输出 shell-safe 赋值。
    eval "$(HOOK_JSON="$INPUT" python3 - <<'PY'
import json, os, shlex
try:
    d = json.loads(os.environ.get("HOOK_JSON") or "{}")
    if not isinstance(d, dict):
        d = {}
except Exception:
    d = {}
ti = d.get("tool_input")
ti = ti if isinstance(ti, dict) else {}
for var, val in (
    ("HOOK_TOOL_NAME", d.get("tool_name")),
    ("HOOK_FILE_PATH", ti.get("file_path")),
    ("HOOK_COMMAND", ti.get("command")),
    ("HOOK_TRANSCRIPT", d.get("transcript_path")),
):
    print(f"{var}={shlex.quote(str(val) if val is not None else '')}")
PY
)"
  fi
}

# Read 专用一次性解析：tool_name + file_path + has_paging（offset/limit 任一存在 → 1）一次 jq 出。
# pre-read-bigfile 原本 hook_parse_all 后还要单独 jq 取 paging，合并省一次 jq fork。
# HOOK_HAS_PAGING 是固定 0/1 不经 @sh；其余仍 @sh 防注入。jq 失败保持预置值。
hook_parse_read() {
  HOOK_TOOL_NAME=""; HOOK_FILE_PATH=""; HOOK_HAS_PAGING=0
  if command -v jq >/dev/null 2>&1; then
    eval "$(printf '%s' "$INPUT" | jq -r '
      "HOOK_TOOL_NAME=" + (.tool_name // "" | @sh),
      "HOOK_FILE_PATH=" + (.tool_input.file_path // "" | @sh),
      "HOOK_HAS_PAGING=" + (if (.tool_input | (has("offset") or has("limit"))) then "1" else "0" end)' 2>/dev/null)"
  else
    # jq 缺失兜底（与 hook_parse_all 同因）：不 fallback 会让 Read 门（大文件 / 图片预检）静默 fail-open
    eval "$(HOOK_JSON="$INPUT" python3 - <<'PY'
import json, os, shlex
try:
    d = json.loads(os.environ.get("HOOK_JSON") or "{}")
    if not isinstance(d, dict):
        d = {}
except Exception:
    d = {}
ti = d.get("tool_input")
ti = ti if isinstance(ti, dict) else {}
print(f"HOOK_TOOL_NAME={shlex.quote(str(d.get('tool_name') or ''))}")
print(f"HOOK_FILE_PATH={shlex.quote(str(ti.get('file_path') or ''))}")
print(f"HOOK_HAS_PAGING={1 if ('offset' in ti or 'limit' in ti) else 0}")
PY
)"
  fi
}

# Task 专用一次性解析：tool_name + subagent_type + description + prompt 一次 jq 出。
# pre-agent-log / pre-task-prompt-scrub 原本各自 fork python3 取 subagent 字段（§三 E 反模式），
# 合并成单次 jq；jq 缺失时 python3 fallback 语义与 hook_parse_all 对齐（防安全门 fail-open）。
hook_parse_task() {
  HOOK_TOOL_NAME=""; HOOK_SUBAGENT_TYPE=""; HOOK_DESCRIPTION=""; HOOK_PROMPT=""
  if command -v jq >/dev/null 2>&1; then
    eval "$(printf '%s' "$INPUT" | jq -r '
      "HOOK_TOOL_NAME=" + (.tool_name // "" | @sh),
      "HOOK_SUBAGENT_TYPE=" + (.tool_input.subagent_type // "" | @sh),
      "HOOK_DESCRIPTION=" + (.tool_input.description // "" | @sh),
      "HOOK_PROMPT=" + (.tool_input.prompt // "" | @sh)' 2>/dev/null)"
  else
    eval "$(HOOK_JSON="$INPUT" python3 - <<'PY'
import json, os, shlex
try:
    d = json.loads(os.environ.get("HOOK_JSON") or "{}")
    if not isinstance(d, dict):
        d = {}
except Exception:
    d = {}
ti = d.get("tool_input")
ti = ti if isinstance(ti, dict) else {}
for var, val in (
    ("HOOK_TOOL_NAME", d.get("tool_name")),
    ("HOOK_SUBAGENT_TYPE", ti.get("subagent_type")),
    ("HOOK_DESCRIPTION", ti.get("description")),
    ("HOOK_PROMPT", ti.get("prompt")),
):
    print(f"{var}={shlex.quote(str(val) if val is not None else '')}")
PY
)"
  fi
}
