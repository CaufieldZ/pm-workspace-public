#!/usr/bin/env bash
# 治理变更 ↔ decision note 配对守卫（.githooks/pre-commit 调用）。
#
# CLAUDE.md 与 .claude/decisions/README.md 都写着「治理类非平凡变更同轮必须写或更新
# 一篇 decision note」，此前纯靠自觉。本脚本把它机械化：治理层文件进了 staged，
# 同一 commit 里就得有 .claude/decisions/ 的变更。
#
# 治理面不含 .claude/skills/*/SKILL.md —— 那里的改动多是产物模板微调，纳进来会天天
# 被拦、养出 --no-verify 习惯，比漏网更糟。
#
# 自己读 staged 而不吃调用方的变量：插在 pre-commit 哪一行都不会因为变量还没赋值
# 而静默失效。
set -euo pipefail

GOV_RE='^CLAUDE\.md$|^\.claude/runbooks/|^\.claude/hooks/|^\.githooks/|^\.claude/settings\.json$|^scripts/lib/thresholds\.yaml$'

staged=$(git diff --cached --name-only --diff-filter=ACMR)
gov_changed=$(echo "$staged" | grep -E "$GOV_RE" || true)
note_changed=$(echo "$staged" | grep -E '^\.claude/decisions/' || true)

[ -z "$gov_changed" ] && exit 0
[ -n "$note_changed" ] && exit 0

if [ "${SKIP_DECISION_PAIR_GATE:-0}" = "1" ]; then
  echo "⚠️  [decision-pair-gate] 治理变更未带 decision note，SKIP 豁免放行（请确属纯机械编辑）"
  exit 0
fi

echo "🚫 [decision-pair-gate] 治理层文件变更，但本次 commit 没有 .claude/decisions/ 变更"
echo "   命中："
echo "$gov_changed" | sed 's/^/     /'
echo ""
echo "   → 修法 1: 新写一篇 .claude/decisions/implemented/$(date +%F)-<slug>.md 并 git add"
echo "             （骨架 Problem / Decision / Alternatives considered / Consequences，"
echo "               格式见 .claude/decisions/README.md，check_decisions.py 会校验）"
echo "   → 修法 2: 已有 note 拥有这个决策 → 更新那一篇，别开重复篇"
echo "   → 真不适用（纯排版 / 错别字 / 生成产物回写）→ SKIP_DECISION_PAIR_GATE=1 git commit ..."
exit 1
