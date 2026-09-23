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
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/notes.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/pybatch.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/post-checks.sh"

INPUT=$(cat)
hook_parse_all
require_write_or_edit

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# 产品线名（baseline_fresh / rule_version_drift 检查整产品线树，dedup key 用它）
# campaign 嵌套取全段（growth/queen）、单段项目取首段——口径见 post-checks.sh
# _pc_product_line_of（对齐 dashboard / audit-fast，修嵌套项目产线三查静默 skip）
DEDUP_PL=$(_pc_product_line_of "$HOOK_FILE_PATH")

# 顺序与原 settings.json PostToolUse Write|Edit 链一致
# warn 类 5 个（static_chapter / prd_cross_check / baseline_fresh / delta_conflict / rule_version_drift）
# 不阻断，加 dedup 节流：同 key TTL 内只跑第一次，降密集 Edit 时发热
# block 类（pc_scene_list 等）禁节流：节流窗口内第二处违规会漏拦
#
# 三个产品线级门（baseline_fresh / delta_conflict / rule_version_drift）单独用长 TTL：
# 它们各要扫一遍整条产线，每项约 90ms；而 60s 窗口在一轮编辑里会被反复越过——
# 实测「一轮 5 分钟、同一 delta 编辑 5 次」时三项合计 2.1s，几乎全是重复扫描。
# 取 10 分钟覆盖一轮，让一轮内最多各跑一次。副作用：改坏产线结构后最迟 10 分钟内的
# 下一次编辑会看到提醒（原为 60s）——三者都只提示「有账没还」，不阻断，延迟可接受。
LINE_CHECK_TTL=600
pc_cjk_punct
pc_plain_language
pc_md_blockquote_wall
pc_bullet_density
pc_prd_content
# 合批冲刷点（不变量 2：已迁移成员最后一个的原位置之后；不变量 1：在 cjk 之后，
# 共享 git diff 在 flush 惰性取补空格后的定型状态）。迁移新成员入批时把 _pc_flush
# 与对应 _pcr_* report 挪到该成员原调用位之后，report 顺序 = 原调用顺序。
_pc_flush
_pcr_plain_language
_pcr_md_blockquote_wall
_pcr_bullet_density
_pcr_prd_content
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
_dedup_if_fresh baseline-fresh-gate "$LINE_CHECK_TTL" "$DEDUP_PL" || pc_baseline_fresh
_dedup_if_fresh delta-conflict-gate "$LINE_CHECK_TTL" "$DEDUP_PL" || pc_delta_conflict
_dedup_if_fresh rule-version-drift-gate "$LINE_CHECK_TTL" "$DEDUP_PL" || pc_rule_version_drift
# 产线三查批的冲刷点（第二 flush：三查在调用链尾部，与前面的 md 批分批跑，
# 保持各 gate 输出在其原调用位附近——stderr 全局顺序不变量 2）
_pc_flush
_pcr_baseline_fresh
_pcr_delta_conflict
_pcr_rule_version_drift
pc_test_reminder

# block 类走 exit 2 —— 那条路上 stderr 本来就到得了模型，不必再重复注入 warn 说明
_pc_cleanup
[ "$_PC_BLOCKED" = "1" ] && exit 2

# warn 类说明走 additionalContext 送达模型：exit 0 时 stderr 模型看不到（见 post-checks.sh 文件头）。
# additionalContext 必须嵌在 hookSpecificOutput 内且 hookEventName 正确，放顶层会被静默忽略。
# stdout 必须只有这一行 JSON——多余输出会让整条校验失败被丢。
_pc_cleanup
note_emit "PostToolUse"
exit 0
