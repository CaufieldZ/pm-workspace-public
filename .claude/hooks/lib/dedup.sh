#!/usr/bin/env bash
# 共享：warn 类 checker 去重节流（连续 Edit 同 key 在 TTL 内只跑一次）
#
# 背景：post-writeedit-dispatch.sh 的 4 个 warn checker（static_chapter /
# prd_cross_check / baseline_fresh / rule_version_drift）不阻断却每次 Edit
# 同步跑，密集写产物时持续发热。dedup 让同 key 在 TTL 秒内只跑第一次。
#
# 用法（dispatcher 包裹 checker 调用，须在 log.sh 之后 source）：
#   source lib/dedup.sh
#   _dedup_if_fresh context-static-lint 60 "$FILE_PATH" || pc_static_chapter
#   ↑ fresh（TTL 内跑过）返回 0 → || 短路 → skip checker
#     stale（该跑了）   返回 1 → || 执行 → run checker
#
# key 维度由调用方定：
#   - 检查具体文件（static_chapter / prd_cross_check）→ key = 文件路径
#   - 检查产品线树（baseline_fresh / rule_version_drift）→ key = 产品线名
#
# cache：$TMPDIR/pmws_dedup/<gate>.<sha1(key)[:16]>，mtime = 上次跑时刻
# TTL 内 → emit dedupe-skip（action 不在 dashboard 5 列，不污染聚合；usage.jsonl 留痕）
set +e

_DEDUP_DIR="${TMPDIR:-/tmp}/pmws_dedup"

# _dedup_if_fresh GATE_NAME TTL_SECS KEY
# 返回 0 = fresh（跳过 checker）；返回 1 = stale（该跑 checker）
# 调用方： _dedup_if_fresh GATE TTL KEY || pc_xxx
_dedup_if_fresh() {
  local gate="$1" ttl="$2" key="$3"
  [ -z "$key" ] && return 1            # 无 key 无法去重，放行跑
  [ -z "$ttl" ] && return 1

  mkdir -p "$_DEDUP_DIR" 2>/dev/null || return 1
  local hash cache
  hash=$(printf '%s' "$key" | shasum 2>/dev/null | cut -c1-16)
  [ -z "$hash" ] && return 1
  cache="$_DEDUP_DIR/$gate.$hash"

  if [ -f "$cache" ]; then
    local mtime now age
    mtime=$(file_mtime "$cache")
    now=$(date +%s)
    if [ -n "$mtime" ]; then
      age=$((now - mtime))
      if [ "$age" -lt "$ttl" ]; then
        log_event hook "$gate" dedupe-skip "$key ($((ttl - age))s left)"
        return 0   # fresh → skip
      fi
    fi
  fi
  # stale 或无 cache → 标记此刻，放行跑（返回 1 触发 || 右侧 checker）
  touch "$cache"
  return 1
}
