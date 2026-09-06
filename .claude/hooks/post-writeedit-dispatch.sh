#!/bin/bash
# PostToolUse Write|Edit 统一 dispatcher
#
# 一次 parse → 顺序跑 checker 子函数（lib/post-checks.sh）。
# checker 互不依赖（全只读检查同一文件）：block 类不即时 exit，而是累积 _PC_BLOCKED，
# 跑完全部再统一 exit 2 —— 一次拿全所有违规（优于「continueOnBlock 半路截断」）。
#
# 子函数 / gate 名 / SKIP env 见 lib/post-checks.sh。
# 加 / 删 checker：改 lib/post-checks.sh + 下方调用序列。
set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/runner.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/dedup.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/post-checks.sh"

INPUT=$(cat)
hook_parse_all
require_write_or_edit

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# 产品线名（baseline_fresh / rule_version_drift 检查整产品线树，dedup key 用它）
# bash 参数展开抽段（零 fork，替 sed -nE）：/projects/ 后第一段，要求其后还有路径（严格等价 sed 的 ([^/]+)/.*）
case "$HOOK_FILE_PATH" in
  */projects/*/*) _pl_tail="${HOOK_FILE_PATH#*/projects/}"; DEDUP_PL="${_pl_tail%%/*}" ;;
  *) DEDUP_PL="" ;;
esac

# 顺序与原 settings.json PostToolUse Write|Edit 链一致
# warn 类 5 个（static_chapter / prd_cross_check / baseline_fresh / delta_conflict / rule_version_drift）
# 不阻断，加 dedup 节流：同 key 60s 内只跑第一次，降密集 Edit 时发热
# block 类（pc_scene_list 等）禁节流：节流窗口内第二处违规会漏拦
pc_cjk_punct
pc_plain_language
pc_md_blockquote_wall
pc_bullet_density
_dedup_if_fresh context-static-lint 60 "$HOOK_FILE_PATH" || pc_static_chapter
pc_scene_list
pc_audit_fast
pc_pm_visual
pc_prototype_audit
pc_prototype_source
pc_prototype_split
pc_imap_split
pc_ui_annotation
_dedup_if_fresh prd-cross-check-gate 60 "$HOOK_FILE_PATH" || pc_prd_cross_check
pc_script_syntax
_dedup_if_fresh baseline-fresh-gate 60 "$DEDUP_PL" || pc_baseline_fresh
_dedup_if_fresh delta-conflict-gate 60 "$DEDUP_PL" || pc_delta_conflict
_dedup_if_fresh rule-version-drift-gate 60 "$DEDUP_PL" || pc_rule_version_drift
pc_test_reminder

[ "$_PC_BLOCKED" = "1" ] && exit 2
exit 0
