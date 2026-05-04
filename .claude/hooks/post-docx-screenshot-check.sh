#!/bin/bash
# PostToolUse Bash hook: 检测 docx 文字改完是否漏刷截图
#
# 触发条件：Bash 跑了 update_*.py / patch_proto_*.py / patch_imap_*.py 后
# 检测逻辑：扫 cwd 下所有 projects/*/，对每个项目：
#   - 找最新 prototype html 的 mtime（A）
#   - 找 screenshots/ 下最旧 png 的 mtime（B）
#   - 找 deliverables/ 下最新 docx 的 mtime（C）
#   - 如果 A > B（原型比某些截图新）且 C > B（docx 改过但某些截图还是旧的）→ FAIL
#
# 严格度（plan toasty-prancing-leaf 任务 3B 升级,2026-05-01）：
#   - docx 实际改过(A > B 且 C > B)→ exit 2 阻断
#     与 post-cjk-punct-check.sh 同模式：deliverables 命中用 strict
#   - 仅 A > B 但 docx 未改 → stderr warn 不阻断
# Escape hatch：SKIP_DOCX_SHOT_GATE=1 临时绕过(改文字 + 推 wiki 不打算重拍时用)
#
# 历史：连续两次踩坑（PRD/SOP docx 改完忘重拍截图）→ 加此 hook 兜底（2026-04-28）
#       2026-05-01 升级 strict 阻断（plan toasty-prancing-leaf 任务 3B）

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
[ "$TOOL_NAME" != "Bash" ] && exit 0

COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# 只对跑 update_*.py / patch_proto_*.py / patch_imap_*.py 触发
case "$COMMAND" in
  *update_prd*|*update_sop*|*patch_proto*|*patch_imap*) ;;
  *) exit 0 ;;
esac

if [ "${SKIP_DOCX_SHOT_GATE:-0}" = "1" ]; then
  _log_skip_gate docx-shot-gate "env  ${COMMAND:0:120}"
  exit 0
fi
# 也认命令行 inline env 前缀:SKIP_DOCX_SHOT_GATE=1 python3 ...
if echo "$COMMAND" | grep -qE '\bSKIP_DOCX_SHOT_GATE=1\b'; then
  _log_skip_gate docx-shot-gate "inline  ${COMMAND:0:120}"
  exit 0
fi

# 跨平台 stat（macOS / Linux）
mtime() {
  stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null
}

WARN=""
FAIL=""

# Schema v2 项目路径可能是 projects/{产品线}/{项目}/ 或 projects/{顶级}/
# 用 deliverables/ 作为项目根锚点，一次性收齐两种布局；examples/{demo}/ 同步纳入
SEARCH_ROOTS=()
[ -d "$CLAUDE_PROJECT_DIR/projects" ] && SEARCH_ROOTS+=("$CLAUDE_PROJECT_DIR/projects")
[ -d "$CLAUDE_PROJECT_DIR/examples" ] && SEARCH_ROOTS+=("$CLAUDE_PROJECT_DIR/examples")
if [ ${#SEARCH_ROOTS[@]} -eq 0 ]; then
  PROJECT_DIRS=""
else
  PROJECT_DIRS=$(find "${SEARCH_ROOTS[@]}" -maxdepth 3 -type d -name deliverables 2>/dev/null \
    | sed -E 's#/deliverables$##')
fi

for project_dir in $PROJECT_DIRS; do
  [ -d "$project_dir" ] || continue
  proj=${project_dir#"$CLAUDE_PROJECT_DIR/"}

  # 跳过 archive
  proto_dir="$project_dir/deliverables"
  shots_dir="$project_dir/screenshots"
  [ -d "$proto_dir" ] || continue
  [ -d "$shots_dir" ] || continue

  # 找最新 prototype html mtime（排除 archive/）
  # 命名两派都认：旧派 `*可交互原型*.html`，Schema v2 派 `proto-*.html`
  proto_t=$(find "$proto_dir" -maxdepth 1 -type f \
    \( -name '*可交互原型*.html' -o -name 'proto-*.html' \) 2>/dev/null \
    | while read -r f; do mtime "$f"; done | sort -n | tail -1)
  [ -z "$proto_t" ] && continue

  # 找最旧 screenshots png mtime（跳过废弃的版本化子目录如 prd_v47/、archive/）
  shot_t=$(find "$shots_dir" -name '*.png' -type f 2>/dev/null \
    | grep -Ev '/(.*_v[0-9]+|archive|deprecated|old)/' \
    | while read -r f; do mtime "$f"; done | sort -n | head -1)
  [ -z "$shot_t" ] && continue

  # 找最新 docx mtime（排除 archive/）
  docx_t=$(find "$proto_dir" -maxdepth 1 -name '*.docx' -type f 2>/dev/null \
    | while read -r f; do mtime "$f"; done | sort -n | tail -1)

  # 截图过期判定：原型比最旧截图新（说明至少有 1 张截图未跟版）
  if [ "$proto_t" -gt "$shot_t" ]; then
    DELTA=$(( proto_t - shot_t ))
    HOURS=$(( DELTA / 3600 ))
    # 加 docx 修改信号增强判断：如果 docx 也是新的，几乎肯定漏更 → FAIL
    if [ -n "$docx_t" ] && [ "$docx_t" -gt "$shot_t" ]; then
      FAIL="$FAIL
  ❌ $proj: 原型已改 + docx 已改但 screenshots/ 下存在较旧截图(原型新于最旧截图 ${HOURS}h),极可能漏更新内嵌截图"
    else
      WARN="$WARN
  · $proj: 原型新于部分截图(${HOURS}h),但 docx 暂未改 — 暂不影响交付物"
    fi
  fi
done

if [ -n "$WARN" ]; then
  echo "[docx-screenshot-check] 检查到截图可能未跟版(warn):" >&2
  echo "$WARN" >&2
  echo "" >&2
  log_event hook docx-shot-gate warn "${COMMAND:0:80}"
fi

if [ -n "$FAIL" ]; then
  echo "" >&2
  echo "🚫 [docx-screenshot-check] 截图过期(strict 阻断):" >&2
  echo "$FAIL" >&2
  echo "" >&2
  echo "   修复:跑 screenshot_*.py 重拍 + insert_*.py 回填到 docx" >&2
  echo "   或在 update_*.py 末尾调 save_prd(doc, path, screenshots_fresh=True, prototype_html=..., shot_dir=...)" >&2
  echo "   临时绕过:SKIP_DOCX_SHOT_GATE=1 python3 ...(改文字不打算重拍时用)" >&2
  log_event hook docx-shot-gate block "${COMMAND:0:80}"
  exit 2
fi

if [ -z "$WARN" ] && [ -z "$FAIL" ]; then
  log_event hook docx-shot-gate clean "${COMMAND:0:80}"
fi

exit 0
