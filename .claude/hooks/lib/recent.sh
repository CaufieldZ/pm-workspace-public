#!/usr/bin/env bash
# 共享：找最近 N 秒内动过的 deliverable 文件
#
# 用途：post-cjk Branch B / post-plain-language Branch B / post-prd-check 三处都做
#       「Bash 跑完 gen_/fill_/patch_ 脚本后扫最近修改的 HTML / md / drawio」
#
# 用法（无额外依赖，直接 source 本文件即可）：
#   source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/recent.sh"
#
#   # 60s 内 prd-*.md，排除 scenes/
#   RECENT=$(find_recent_deliverables 60 "prd-*.md" --not-path '*-scenes/*')
#
#   # 30s 内 *.html / *.md / *.drawio
#   RECENT=$(find_recent_deliverables 30 "*.html" "*.md" "*.drawio")
#
#   # 60s 内 *.md / *.html / *.drawio / *.mmd，包含根 deliverables/（post-plain-language 专用）
#   RECENT=$(find_recent_deliverables 60 --include-root-deliverables "*.md" "*.html" "*.drawio" "*.mmd")
#
# 参数：
#   $1                  WINDOW_SEC 秒数（必须，第一位置）
#   --not-path PATTERN  传给 find -not -path（可重复）
#   --include-root-deliverables  扫 $PROJECT_DIR/deliverables（默认只扫 projects/ + examples/）
#   其余位置参数         文件名 glob（-name 链 OR 拼接）
set +e

find_recent_deliverables() {
  local window="$1"
  shift

  local include_root=0
  local not_paths=()
  local name_globs=()

  while [ $# -gt 0 ]; do
    case "$1" in
      --include-root-deliverables) include_root=1; shift ;;
      --not-path) not_paths+=("$2"); shift 2 ;;
      *) name_globs+=("$1"); shift ;;
    esac
  done

  [ ${#name_globs[@]} -eq 0 ] && return 0

  local root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  local roots=()
  [ -d "$root/projects" ] && roots+=("$root/projects")
  [ -d "$root/examples" ] && roots+=("$root/examples")
  [ "$include_root" = "1" ] && [ -d "$root/deliverables" ] && roots+=("$root/deliverables")
  [ ${#roots[@]} -eq 0 ] && return 0

  # 参考文件：mtime 回拨 window 秒，逐文件用 bash 内建 `[ "$f" -nt "$ref" ]` 比时间。
  # 零 per-file fork——原先每文件 fork 一个 stat，85 个候选文件约 0.43s，现约 0.02s。
  # 兜底：date -v 是 BSD 语法，GNU date 走 -d；两者都失败时退化成 touch（ref 即当下）。
  local ref
  ref=$(mktemp) || return 0
  if ! touch -t "$(date -v-"${window}"S +%Y%m%d%H%M.%S 2>/dev/null)" "$ref" 2>/dev/null; then
    touch -d "-${window} seconds" "$ref" 2>/dev/null || touch "$ref"
  fi

  # 拼 find 参数：-path '*/deliverables/*' -type f -not -path '*/archive/*' [-not -path EXTRA]... \( -name g1 -o -name g2 ... \)
  local find_args=(-path '*/deliverables/*' -type f -not -path '*/archive/*')
  local p
  for p in "${not_paths[@]}"; do
    find_args+=(-not -path "$p")
  done

  # name 链
  local name_args=()
  local first=1
  for g in "${name_globs[@]}"; do
    if [ "$first" = "1" ]; then
      name_args+=(-name "$g")
      first=0
    else
      name_args+=(-o -name "$g")
    fi
  done
  find_args+=(\( "${name_args[@]}" \))

  find "${roots[@]}" "${find_args[@]}" 2>/dev/null | while read -r f; do
    [ "$f" -nt "$ref" ] && echo "$f"
  done | sort -u

  rm -f "$ref"
}
