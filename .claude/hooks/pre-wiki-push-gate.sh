#!/bin/bash
# PreToolUse Bash hook: Confluence push 前强制跑自检
#
# 规则来源:soul.md 2026-04-28
#   「推共享 wiki / 公共 PR 等高风险动作前必须二闸:先跑自检脚本」
#
# 触发:Bash 命令含 push_to_confluence_base.py 或 md_to_confluence.py
# 行为:
#   - push_to_confluence_base.py(推 docx)→ 同步跑 check_prd.sh,失败 exit 2
#   - md_to_confluence.py(推 md)→ stderr warn 提醒人工扫(无专属 check)
# Escape hatch:SKIP_WIKI_PUSH_GATE=1 临时绕过

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
[ "$TOOL_NAME" != "Bash" ] && exit 0

CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

if [ "${SKIP_WIKI_PUSH_GATE:-0}" = "1" ]; then
  _log_skip_gate wiki-push-gate "env  ${CMD:0:120}"
  exit 0
fi
# 也认命令行 inline env 前缀：SKIP_WIKI_PUSH_GATE=1 python3 ...（Claude Code hook 进程不继承 Bash inline env）
if echo "$CMD" | grep -qE '\bSKIP_WIKI_PUSH_GATE=1\b'; then
  _log_skip_gate wiki-push-gate "inline  ${CMD:0:120}"
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# === 路径 1:push_to_confluence_base.py 推 docx ===
if echo "$CMD" | grep -q 'push_to_confluence_base\.py'; then
  # 抽第一个 .docx 路径（去掉首尾的引号 — 命令行 "path" 包裹时 grep 会带进来）
  DOCX=$(echo "$CMD" | grep -oE '[^ ]+\.docx' | head -1 | sed -E 's/^["'"'"']//; s/["'"'"']$//')
  if [ -z "$DOCX" ]; then
    exit 0  # 抽不到不拦
  fi

  # 解析 docx 所属项目
  # 抽项目路径：先试两层（产品线/项目），失败回落到一层（顶级项目）
  PROJ_NAME=$(echo "$DOCX" | sed -nE 's|.*projects/([^/]+/[^/]+)/deliverables/.*|\1|p')
  [ -z "$PROJ_NAME" ] && PROJ_NAME=$(echo "$DOCX" | sed -nE 's|.*projects/([^/]+)/deliverables/.*|\1|p')
  if [ -z "$PROJ_NAME" ]; then
    exit 0
  fi

  SCENE_LIST="$PROJECT_DIR/projects/$PROJ_NAME/scene-list.md"
  CHECK_SCRIPT="$PROJECT_DIR/.claude/skills/prd/scripts/check_prd.sh"

  if [ ! -f "$SCENE_LIST" ] || [ ! -f "$CHECK_SCRIPT" ]; then
    exit 0  # 缺依赖文件不拦
  fi

  # 同步跑 check_prd
  TMPOUT=$(mktemp)
  bash "$CHECK_SCRIPT" "$DOCX" "$SCENE_LIST" > "$TMPOUT" 2>&1
  RC=$?

  if [ "$RC" -ne 0 ]; then
    echo "" >&2
    echo "🚫 [wiki-push-gate] PRD 自检未通过,拒绝推 Confluence" >&2
    echo "   docx: $DOCX" >&2
    echo "" >&2
    echo "   ── check_prd 输出(末尾 30 行)──" >&2
    tail -30 "$TMPOUT" >&2
    echo "" >&2
    echo "   → 修复后重试,或 export SKIP_WIKI_PUSH_GATE=1 强推" >&2
    log_event gate wiki-push-gate block "$DOCX"
    rm -f "$TMPOUT"
    exit 2
  fi
  log_event gate wiki-push-gate triggered "$DOCX"
  rm -f "$TMPOUT"
  exit 0
fi

# === 路径 2:md_to_confluence.py 推 md ===
if echo "$CMD" | grep -q 'md_to_confluence\.py'; then
  echo "" >&2
  echo "ℹ️  [wiki-push-gate] 推 md 到 Confluence 前请确认:" >&2
  echo "   ① 文件已肉眼扫:无圈数字 ①②③ / 无段首裸编号 / 无 ChatGPT 味结构化堆砌" >&2
  echo "   ② 业务白话:讲人话产物正文禁裸 A-1/B-2/决策 N(锚点除外)" >&2
  echo "   ③ 半角标点:CJK 旁无 :,;()" >&2
  echo "   如已自检通过,放行" >&2
  echo "" >&2
  log_event gate wiki-push-gate warn "md_to_confluence"
  exit 0  # warn 不阻断(md 没专属 check)
fi

exit 0
