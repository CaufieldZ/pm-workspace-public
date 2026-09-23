#!/bin/bash
# PostToolUse Bash hook: 调度 cjk / plain-language / prd-check / ui-annotation / proto-audit / prototype-split / imap-split / proto-drift 八个 Bash 路径 sub-checker
#
# 设计：每个 sub-checker 自检 trigger pattern，串行跑，首个 fail 直接 stderr + exit 2 阻断

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/recent.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/notes.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/checkers.sh"

INPUT=$(cat)
hook_parse_all
require_bash

CMD="$HOOK_COMMAND"

# 8 个 sub-checker 串联（每个内部自判 trigger pattern；首个 fail 直接 exit 2）
check_cjk_for_bash_recent "$CMD"
check_plain_language_for_bash_recent "$CMD"
check_prd_for_bash_recent "$CMD"
check_ui_annotation_for_bash_recent "$CMD"
check_proto_audit_for_bash "$CMD"
check_prototype_split_for_bash "$CMD"
check_imap_split_for_bash "$CMD"
check_proto_drift_for_bash "$CMD"

# warn 类说明汇总送达模型（任一 sub-checker _check_block 时已 exit 2，走不到这里）
note_emit "PostToolUse"
exit 0
