#!/usr/bin/env bash
# publish.sh — 把 deliverables 下的 HTML 发布到 ~/pm-deliverables (Vercel)
#
# 用法:
#   bash scripts/publish.sh <文件路径> [更多文件...]     # 发布
#   bash scripts/publish.sh --list                       # 列出所有已发布
#   bash scripts/publish.sh --unpublish <仓库内路径>     # 下线
#
# 映射: projects/{项目}/deliverables/{文件} → ~/pm-deliverables/{项目}/{文件}
# URL:  https://pm-deliverables.vercel.app/{项目}/{文件}

set -euo pipefail

# route-log: 调用埋点
{ . "${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}/.claude/hooks/lib/log.sh" 2>/dev/null && log_event route "publish" triggered; } 2>/dev/null || true

DELIVERABLES_REPO="${DELIVERABLES_REPO:-$HOME/pm-deliverables}"
VERCEL_DOMAIN="${VERCEL_DOMAIN:-pm-deliverables.vercel.app}"

# 排除的非产出物文件 (仓库基础设施)
EXCLUDE_FILES=(index.html README.md vercel.json .gitignore)

usage() {
  cat >&2 <<EOF
用法:
  bash scripts/publish.sh <文件路径> [更多文件...]     发布产出物
  bash scripts/publish.sh --list                       列出所有已发布
  bash scripts/publish.sh --unpublish <仓库内路径>     下线某个产出物

示例:
  bash scripts/publish.sh projects/liquidity/deliverables/ppt-lt-leadership-v1.html
  bash scripts/publish.sh --list
  bash scripts/publish.sh --unpublish liquidity/ppt-lt-leadership-v1.html
EOF
  exit 1
}

[[ $# -eq 0 ]] && usage

if [[ ! -d "$DELIVERABLES_REPO/.git" ]]; then
  echo "✗ 未找到 $DELIVERABLES_REPO 或它不是 git 仓库" >&2
  echo "  先跑: bash scripts/init-deliverables-repo.sh" >&2
  exit 1
fi

# --- 判断是否 exclude file ---
is_excluded() {
  local name="$1"
  for ex in "${EXCLUDE_FILES[@]}"; do
    [[ "$name" == "$ex" ]] && return 0
  done
  return 1
}

# ============== 子命令: --list ==============
if [[ "$1" == "--list" ]]; then
  cd "$DELIVERABLES_REPO"
  echo "已发布产出物 · $DELIVERABLES_REPO"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # 找所有 html, 按目录分组
  files=$(find . -type f -name '*.html' \
    -not -path './.git/*' \
    -not -path './node_modules/*' \
    | sed 's|^\./||' \
    | sort)

  [[ -z "$files" ]] && { echo "  (空)"; exit 0; }

  current_group=""
  count=0
  while IFS= read -r f; do
    base=$(basename "$f")
    is_excluded "$base" && continue

    group=$(dirname "$f")
    [[ "$group" == "." ]] && group="(根目录)"

    if [[ "$group" != "$current_group" ]]; then
      [[ -n "$current_group" ]] && echo ""
      echo "▸ $group"
      current_group="$group"
    fi

    # 最后修改时间 (macOS)
    mtime=$(stat -f '%Sm' -t '%Y-%m-%d %H:%M' "$f" 2>/dev/null \
            || stat -c '%y' "$f" 2>/dev/null | cut -d'.' -f1)
    url_path=$(python3 -c "import urllib.parse,sys;print('/'.join(urllib.parse.quote(p) for p in sys.argv[1].split('/')))" "$f")
    echo "  $base"
    echo "    https://$VERCEL_DOMAIN/$url_path"
    echo "    更新于 $mtime"
    count=$((count + 1))
  done <<< "$files"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "共 $count 个已发布"
  exit 0
fi

# ============== 子命令: --unpublish ==============
if [[ "$1" == "--unpublish" ]]; then
  if [[ $# -lt 2 ]]; then
    echo "✗ --unpublish 需要指定仓库内路径" >&2
    echo "  示例: bash scripts/publish.sh --unpublish liquidity/xxx.html" >&2
    echo "  先跑 --list 看路径" >&2
    exit 1
  fi

  target="$2"
  # 去掉可能的 URL 前缀和绝对路径前缀
  target="${target#https://$VERCEL_DOMAIN/}"
  target="${target#$DELIVERABLES_REPO/}"
  target="${target#/}"

  full="$DELIVERABLES_REPO/$target"
  if [[ ! -f "$full" ]]; then
    echo "✗ 不存在: $target (在 $DELIVERABLES_REPO)" >&2
    echo "  先跑 --list 看现在有啥" >&2
    exit 1
  fi

  base=$(basename "$target")
  if is_excluded "$base"; then
    echo "✗ $base 是仓库基础设施文件，禁止下线" >&2
    exit 1
  fi

  echo "即将下线:"
  echo "  $target"
  echo "  URL: https://$VERCEL_DOMAIN/$target"
  read -r -p "确认? [y/N] " ans
  if [[ ! "$ans" =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
  fi

  cd "$DELIVERABLES_REPO"
  git rm --quiet "$target"
  # 如果目录空了，顺手清掉
  dir=$(dirname "$target")
  if [[ "$dir" != "." && -d "$dir" && -z "$(ls -A "$dir")" ]]; then
    rmdir "$dir" 2>/dev/null || true
  fi
  git commit -m "unpublish: $target" >/dev/null
  git push --quiet
  echo "✓ 已下线并推送到 GitHub (Vercel 会在 30s 内生效)"
  exit 0
fi

# ============== 默认: 发布 ==============
published_urls=()

for src in "$@"; do
  if [[ ! -f "$src" ]]; then
    echo "✗ 文件不存在: $src" >&2
    exit 1
  fi

  # 路径映射规则
  #   projects/xx/deliverables/yy.html       → xx/yy.html
  #   projects/xx/yy/deliverables/zz.html    → xx/yy/zz.html
  #   其他 (_demos/xx/yy.html 之类)          → 去掉开头的 _ 保留结构
  if [[ "$src" =~ ^projects/.+/deliverables/.+ ]]; then
    rel=$(echo "$src" | sed -E 's|^projects/||; s|/deliverables/|/|')
  else
    rel=$(echo "$src" | sed -E 's|^_||')
  fi

  # .md → .html (用 md_to_html.py 转换带 "Copy for LLM" 按钮的 HTML)
  if [[ "$src" == *.md ]]; then
    rel="${rel%.md}.html"
    dst="$DELIVERABLES_REPO/$rel"
    mkdir -p "$(dirname "$dst")"
    python3 "$(dirname "$0")/lib/md_to_html.py" "$src" "$dst" >/dev/null
    echo "✓ Rendered: $src → $rel (带 Copy for LLM 按钮)"
  else
    dst="$DELIVERABLES_REPO/$rel"
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    echo "✓ Copied: $src → $rel"
  fi

  url_path=$(python3 -c "import urllib.parse, sys; print('/'.join(urllib.parse.quote(p) for p in sys.argv[1].split('/')))" "$rel")
  published_urls+=("https://$VERCEL_DOMAIN/$url_path")
done

# commit & push
cd "$DELIVERABLES_REPO"
if [[ -z "$(git status --porcelain)" ]]; then
  echo "⚠ 无变更，跳过 commit"
else
  git add -A
  nfile=$(git diff --cached --name-only | wc -l | tr -d ' ')
  msg="publish: $(date +%Y-%m-%d\ %H:%M) (${nfile}文件)"
  git commit -m "$msg" >/dev/null
  git push --quiet
  echo "✓ Pushed to GitHub (Vercel 会自动部署，通常 30 秒内生效)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for url in "${published_urls[@]}"; do
  echo "  $url"
done
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v pbcopy >/dev/null 2>&1; then
  printf '%s\n' "${published_urls[@]}" | pbcopy
  echo "  (URL 已复制到剪贴板)"
elif command -v clip.exe >/dev/null 2>&1; then
  printf '%s\n' "${published_urls[@]}" | clip.exe
  echo "  (URL 已复制到剪贴板)"
elif command -v xclip >/dev/null 2>&1; then
  printf '%s\n' "${published_urls[@]}" | xclip -selection clipboard
  echo "  (URL 已复制到剪贴板)"
fi
