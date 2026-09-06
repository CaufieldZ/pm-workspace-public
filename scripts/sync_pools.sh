#!/bin/bash
# 一键刷新两个需求池 md（增长 + 体验专项）
# 单条反写仍走 sync_growth_demand_pool.py / sync_ux_demand_pool.py writeback 子命令
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

{ . "$REPO_ROOT/.claude/hooks/lib/log.sh" 2>/dev/null && log_event route "sync_pools" triggered; } 2>/dev/null || true

echo "═══ 1/2 · 增长需求池 ═══"
python3 scripts/sync_growth_demand_pool.py pull

echo ""
echo "═══ 2/2 · 体验专项需求池 ═══"
python3 scripts/sync_ux_demand_pool.py pull

echo ""
echo "✅ 两个池子已刷新："
echo "   - references/growth-demand-pool.md"
echo "   - references/ux-demand-pool.md"
