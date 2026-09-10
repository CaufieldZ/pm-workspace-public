#!/bin/bash
# PreToolUse Write|Edit 统一 guard dispatcher（原 4 个独立 pre-*.sh 合并入口）
#
# 一次 parse → 顺序跑 4 个 guard 子函数（lib/pre-writeedit-guards.sh）。
# Pre 侧 = 硬 block：任一 guard return 2 → 立即 exit 2（拦住就停，不聚合）。
#
# 子函数 / gate 名 / SKIP env 见 lib/pre-writeedit-guards.sh（与原 4 hook 逐字一致）。
set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/pre-writeedit-guards.sh"

INPUT=$(cat)
hook_parse_all
require_write_or_edit

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# 顺序与原 settings.json PreToolUse Write|Edit 链一致；任一命中即停
pg_scripts_first        || exit 2
pg_deliverable_source   || exit 2
pg_deliverable_img_path || exit 2
pg_skill_load           || exit 2

exit 0
