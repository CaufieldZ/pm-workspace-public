#!/usr/bin/env bash
# 外网下载降级 wrapper：直连失败且非国内域名时自动加代理重试一次。
#
# 用法（命令直接接在后面，不传 shell 串，不支持管道/重定向）：
#   bash scripts/net_retry.sh curl -L https://example.com/x.tgz -o x.tgz
#   bash scripts/net_retry.sh pip3 install foo
#   bash scripts/net_retry.sh git clone https://github.com/owner/repo
#
# 策略单一事实源 = .claude/runbooks/proxy-fallback.md：
#   直连失败（connection refused / timeout / reset / 无法解析）+ 非国内域名 → 按
#   scripts/proxy_env.sh 判定重试（proxy 模式加 ALL_PROXY 一次，direct 模式不重试）；
#   国内域名/镜像不重试。含管道/重定向的命令 wrapper 不适用，按 runbook 手动加 ALL_PROXY。
set +e

[ "$#" -ge 1 ] || { echo "用法: net_retry.sh <command> [args...]" >&2; exit 2; }

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export CLAUDE_PROJECT_DIR="$ROOT"  # log.sh 优先按此解析 workspace root，避免 BASH_SOURCE 推断走偏
[ -f "$ROOT/.claude/hooks/lib/log.sh" ] && source "$ROOT/.claude/hooks/lib/log.sh"
type log_event >/dev/null 2>&1 || log_event() { :; }  # source 失败兜底为 no-op

# 失败关键词（命中才认为是网络问题，值得加代理重试）
NET_FAIL_RE='[Cc]onnection refused|[Tt]imed? ?out|[Cc]onnection reset|[Cc]ould not resolve|[Cc]ouldn.t resolve|[Cc]onnection closed|[Nn]etwork is unreachable|[Ff]ailed to connect'
# 国内域名/镜像（命中则不走代理，对齐 pre-bash-guard.sh 规则 A）
CN_RE='pypi\.tuna\.tsinghua|npmmirror|mirrors\.(aliyun|tencent|ustc|163)|registry\.npm\.taobao|goproxy\.cn|\.cn([/:]|$|[[:space:]])'
PROXY="${ALL_PROXY:-http://127.0.0.1:7897}"

CMD_STR="$*"

# ── 第一次：直连（stderr 落临时文件再回显，避免异步 tee 漏读）──
ERRFILE="$(mktemp)"
trap 'rm -f "$ERRFILE"' EXIT
"$@" 2>"$ERRFILE"
rc=$?
cat "$ERRFILE" >&2
ERR_TEXT="$(cat "$ERRFILE")"
if [ $rc -eq 0 ]; then
  log_event gate net-retry direct "${CMD_STR:0:120}"
  exit 0
fi

# 非网络类失败（如参数错、404）→ 不重试，透传
if ! echo "$ERR_TEXT" | grep -qE "$NET_FAIL_RE"; then
  log_event gate net-retry direct-fail "${CMD_STR:0:120}"
  exit $rc
fi

# 国内域名 → 不加代理，透传失败
if echo "$CMD_STR" | grep -qE "$CN_RE"; then
  echo "[net_retry] 国内域名直连失败，不走代理（按 proxy-fallback.md）" >&2
  log_event gate net-retry proxy-skip-cn "${CMD_STR:0:120}"
  exit $rc
fi

# ── 第二次：按动态判定决定是否走代理（proxy_env.sh：proxy 模式已 export 代理变量）──
source "$ROOT/scripts/proxy_env.sh"
MODE="${PROXY_MODE:-direct}"
if [ "$MODE" = "direct" ]; then
  echo "[net_retry] 代理判定 direct（国外直连失败为真实失败 / 7897 不在线），不重试代理" >&2
  log_event gate net-retry proxy-skip-direct "${CMD_STR:0:120}"
  exit $rc
fi
echo "[net_retry] 代理判定 $MODE，加代理重试：ALL_PROXY=${ALL_PROXY:-$PROXY}" >&2
log_event gate net-retry proxy-retry "${CMD_STR:0:120}"
ALL_PROXY="${ALL_PROXY:-$PROXY}" HTTPS_PROXY="${HTTPS_PROXY:-$PROXY}" HTTP_PROXY="${HTTP_PROXY:-$PROXY}" "$@"
exit $?
