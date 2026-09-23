#!/bin/bash
# Stop hook: 每次 session 结束后清理 Python 工具链缓存（__pycache__ / .pytest_cache / .hypothesis）
# 范围：prune 掉 .venv / node_modules / .git（依赖环境字节码 / 测试缓存会重生成，清了纯浪费 IO）
# 实现：单条 find + -prune + -exec rm -rf {} + 批量删，零 per-dir fork（HOOK_WRITING §三 K）
# housekeeping 不 emit log_event（不进 dashboard 诊断表，对齐 stop-dashboard-refresh.sh）
# 跳过：SKIP_PYCACHE_CLEAN=1
set +e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

[ "${SKIP_PYCACHE_CLEAN:-0}" = "1" ] && exit 0
[ ! -d "$PROJECT_DIR" ] && exit 0

# 后台清理（不阻塞 Stop 返回）：先 prune 大目录，再删剩下的缓存目录
# 重定向必须挂在子 shell 上：子进程自己不重定向就会继承并持有本 hook 的 stdout 管道，
# 宿主读不到 EOF 会一直等到清理跑完，后台等于没后台（实测 0.11~0.35s vs 重定向后 ~0.02s）。
# 对照 stop-dashboard-refresh.sh —— 它两条输出流都进了 /dev/null，所以只要 ~12ms。
(
  find "$PROJECT_DIR" \
    \( -name .venv -o -name node_modules -o -name .git \) -prune -o \
    -type d \( -name __pycache__ -o -name .pytest_cache -o -name .hypothesis \) \
    -prune -exec rm -rf {} +
) > /dev/null 2>&1 &
exit 0
