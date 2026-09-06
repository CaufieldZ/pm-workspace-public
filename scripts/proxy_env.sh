#!/usr/bin/env bash
# 代理模式判定（单一实现；策略源 = .claude/runbooks/proxy-fallback.md）
#
# 判定链（按优先级）：
#   FORCE_PROXY=1 / FORCE_DIRECT=1 → 强制指定，跳过探针
#   已有 ALL_PROXY / HTTPS_PROXY / HTTP_PROXY 环境变量 → 尊重显式意图（mode=explicit）
#   缓存命中（TTL 600s）→ 直连探针（google generate_204，http→https）
#   直连通 = 免墙环境，direct（不走 7897）；直连不通则探 7897 过代理访问同端点 → 通 = proxy
#   全不通 = direct + stderr 提示
#
# 用法：
#   source scripts/proxy_env.sh         # 设 PROXY_MODE；proxy 模式 export ALL_PROXY/HTTP(S)_PROXY
#   bash scripts/proxy_env.sh --print   # 打印 mode=… / proxy=…（Python 消费）
#
# 探针需要出网：Bash 沙箱内会全不通 → 误判 direct（按 proxy-fallback.md 关沙箱再跑）。
# 探针端点选 google generate_204（免墙环境代表）：判定语义是「被墙资源直连可不可达」，
# 不是「任意出网」——gstatic / cloudflare 国内大量直连可达，探针通≠被墙资源通。

PROXY_URL="${PROXY_URL:-http://127.0.0.1:7897}"
PM_PROXY_CACHE="${TMPDIR:-/tmp}/pm-proxy-mode-${UID:-0}"
PM_PROXY_TTL=600
PROXY_MODE=""

_probe_direct() {
  curl -s --max-time 2 -o /dev/null http://www.google.com/generate_204 2>/dev/null \
    || curl -s --max-time 2 -o /dev/null https://www.google.com/generate_204 2>/dev/null
}

_probe_proxy() {
  curl -s --max-time 2 -x "$PROXY_URL" -o /dev/null https://www.google.com/generate_204 2>/dev/null
}

_cache_read() {
  local _mtime _now
  [ -f "$PM_PROXY_CACHE" ] || return 1
  _mtime=$(stat -f %m "$PM_PROXY_CACHE" 2>/dev/null) || return 1
  _now=$(date +%s)
  [ $((_now - _mtime)) -lt "$PM_PROXY_TTL" ] || return 1
  PROXY_MODE=$(sed -n '1p' "$PM_PROXY_CACHE" 2>/dev/null)
  case "$PROXY_MODE" in
    proxy|direct) return 0 ;;
    *) return 1 ;;
  esac
}

_cache_write() {
  printf '%s\n' "$PROXY_MODE" > "$PM_PROXY_CACHE" 2>/dev/null
}

_decide() {
  if [ "${FORCE_PROXY:-0}" = "1" ]; then PROXY_MODE=proxy; return; fi
  if [ "${FORCE_DIRECT:-0}" = "1" ]; then PROXY_MODE=direct; return; fi
  if [ -n "${ALL_PROXY:-}${HTTPS_PROXY:-}${HTTP_PROXY:-}${all_proxy:-}${https_proxy:-}${http_proxy:-}" ]; then
    PROXY_MODE=explicit
    return
  fi
  if _cache_read; then return; fi
  if _probe_direct; then
    PROXY_MODE=direct
  elif _probe_proxy; then
    PROXY_MODE=proxy
  else
    PROXY_MODE=direct
    echo "[proxy_env] 直连与 $PROXY_URL 探针均不通（网络异常 / Bash 沙箱 / Clash 未启动），暂判 direct" >&2
  fi
  _cache_write
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  # 执行模式：只支持 --print
  [ "${1:-}" = "--print" ] || { echo "用法: bash $0 --print" >&2; exit 2; }
  _decide
  printf 'mode=%s\nproxy=%s\n' "$PROXY_MODE" "$PROXY_URL"
else
  # source 模式：忽略调用方位置参数，直接判定
  _decide
  if [ "$PROXY_MODE" = "proxy" ]; then
    export ALL_PROXY="$PROXY_URL" HTTP_PROXY="$PROXY_URL" HTTPS_PROXY="$PROXY_URL"
  fi
fi
