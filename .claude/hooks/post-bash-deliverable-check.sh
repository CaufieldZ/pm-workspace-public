#!/bin/bash
# PostToolUse Bash hook: 调度 cjk / plain-language / prd-check / ui-annotation / proto-audit / proto-drift 六个 Bash 路径 sub-checker
#
# 设计：每个 sub-checker 自检 trigger pattern，串行跑，首个 fail 直接 stderr + exit 2 阻断

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/recent.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/checkers.sh"

INPUT=$(cat)
hook_parse_all
require_bash

CMD="$HOOK_COMMAND"

# 6 个 sub-checker 串联（每个内部自判 trigger pattern；首个 fail 直接 exit 2）
check_cjk_for_bash_recent "$CMD"
check_plain_language_for_bash_recent "$CMD"
check_prd_for_bash_recent "$CMD"
check_ui_annotation_for_bash_recent "$CMD"
check_proto_audit_for_bash "$CMD"
check_proto_drift_for_bash "$CMD"

exit 0
