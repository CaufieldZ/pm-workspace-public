#!/usr/bin/env bash
# 外网下载降级 wrapper：直连失败且非国内域名时自动加代理重试一次。
# 本脚本自身无参数，--help 透传给内层命令。
#
# 用法（命令直接接在后面，不传 shell 串，不支持管道/重定向）：
#   bash scripts/net_retry.sh curl -L https://example.com/x.tgz -o x.tgz
#   bash scripts/net_retry.sh pip3 install foo
#   bash scripts/net_retry.sh git clone https://github.com/owner/repo
#
# 策略单一事实源 = .claude/runbooks/proxy-fallback.md：
#   直连失败（connection refused / timeout / reset / 无法解析）+ 非国内域名 → 按
#   scripts/lib/proxy.py 判定重试（判定到可用代理才加代理重试一次，判直连则不加）；
#   国内域名/镜像不重试。含管道/重定向的命令 wrapper 不适用，按 runbook 手动加 ALL_PROXY。
set +e

[ "$#" -ge 1 ] || { echo "用法: net_retry.sh <command> [args...]" >&2; exit 2; }

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export CLAUDE_PROJECT_DIR="$ROOT"  # log.sh 优先按此解析 workspace root，避免 BASH_SOURCE 推断走偏
[ -f "$ROOT/.claude/hooks/lib/log.sh" ] && source "$ROOT/.claude/hooks/lib/log.sh"
type log_event >/dev/null 2>&1 || log_event() { :; }  # source 失败兜底为 no-op

# 失败关键词（命中才认为是网络问题，值得加代理重试）
NET_FAIL_RE='[Cc]onnection refused|[Tt]imed? ?out|[Cc]onnection reset|[Cc]ould not resolve|[Cc]ouldn.t resolve|[Cc]onnection closed|[Nn]etwork is unreachable|[Ff]ailed to connect'
# 国内域名/镜像（命中则不走代理，对齐 pre-proxy-check.sh 的国内源排除表）
CN_RE='pypi\.tuna\.tsinghua|npmmirror|mirrors\.(aliyun|tencent|ustc|163)|registry\.npm\.taobao|goproxy\.cn|\.cn([/:]|$|[[:space:]])'

CMD_STR="$*"

# ── 第一次：直连（stderr 落临时文件再回显，避免异步 tee 漏读）──
ERRFILE="$(mktemp)"
# PROXY_ERRFILE 在判定腿才建（`${PROXY_ERRFILE:-}` 兜住 trap 早于赋值触发的场景），一并清
trap 'rm -f "$ERRFILE" "${PROXY_ERRFILE:-}"' EXIT
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

# ── 第二次：判定到可用代理才加代理重试（候选端口与验活规则都在 scripts/lib/proxy.py）──
# stderr 单独收着：空结论有两种来源——「判直连」（正常）与「判定源自己炸了」（异常），
# 吞掉 stderr 会让后者伪装成前者，排查方向被带偏。
PROXY_ERRFILE="$(mktemp)"
PROXY_PREFIX="$(python3 "$ROOT/scripts/lib/proxy.py" --prefix 2>"$PROXY_ERRFILE")"
if [ -z "$PROXY_PREFIX" ]; then
  echo "[net_retry] 未判定到可用代理（国外直连失败为真实失败 / 代理未启动），不重试代理" >&2
  if [ -s "$PROXY_ERRFILE" ]; then
    echo "[net_retry] 判定源自身报错（上面的结论未必是真判直连，先修这个）：" >&2
    head -5 "$PROXY_ERRFILE" >&2
  fi
  log_event gate net-retry proxy-skip-direct "${CMD_STR:0:120}"
  exit $rc
fi
rm -f "$PROXY_ERRFILE"
# PROXY_PREFIX 是 `export A=… B=…;` 一行，eval 进本进程后子进程直接继承
eval "$PROXY_PREFIX"
echo "[net_retry] 判定到代理，加代理重试：ALL_PROXY=${ALL_PROXY}" >&2
log_event gate net-retry proxy-retry "${CMD_STR:0:120}"
"$@"
exit $?
