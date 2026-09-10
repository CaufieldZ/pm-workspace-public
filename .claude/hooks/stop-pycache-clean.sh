#!/bin/bash
# Stop hook: 每次 session 结束后清理工区代码目录产生的 __pycache__
# 范围：prune 掉 .venv / node_modules / .git（依赖环境字节码 import 会重生成，清了纯浪费 IO）
# 实现：单条 find + -prune + -exec rm -rf {} + 批量删，零 per-dir fork（HOOK_WRITING §三 K）
# housekeeping 不 emit log_event（不进 dashboard 诊断表，对齐 stop-dashboard-refresh.sh）
# 跳过：SKIP_PYCACHE_CLEAN=1
set +e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

[ "${SKIP_PYCACHE_CLEAN:-0}" = "1" ] && exit 0
[ ! -d "$PROJECT_DIR" ] && exit 0

# 后台清理（不阻塞 Stop 返回）：先 prune 大目录，再删剩下的 __pycache__
(
  find "$PROJECT_DIR" \
    \( -name .venv -o -name node_modules -o -name .git \) -prune -o \
    -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
) &
exit 0
