#!/usr/bin/env bash
# Pre-commit warning hook（非阻断）：archive 体积 / 旧版本脚本累积两类。
# 由 .githooks/pre-commit 显式调用。

WORKSPACE=$(git rev-parse --show-toplevel)
cd "$WORKSPACE" || exit 0

WARN_COUNT=0

# 1. Archive 体积：单项目 archive > 50M
while IFS= read -r dir; do
  [ -d "$dir" ] || continue
  size_mb=$(du -sm "$dir" 2>/dev/null | awk '{print $1}')
  [ -z "$size_mb" ] && continue
  if [ "$size_mb" -gt 50 ]; then
    echo "⚠️  $dir 体积 ${size_mb}M (> 50M) — 考虑迁出本地或换 OSS"
    WARN_COUNT=$((WARN_COUNT+1))
  fi
done < <(find projects -type d -name "archive" 2>/dev/null)

# 2. 版本号脚本累积：同基名 gen_*/fill_*/patch_*_v[0-9]+ > 5 个
while IFS= read -r project_scripts; do
  [ -d "$project_scripts" ] || continue
  # 按基名分组（去掉 _v\d+ 后缀），统计每个基名出现次数
  basenames=$(ls "$project_scripts" 2>/dev/null | grep -E '_v[0-9]+\.(py|js)$' | sed -E 's/_v[0-9]+\.(py|js)$//' | sort | uniq -c | awk '$1 > 5 {print $2, $1}')
  if [ -n "$basenames" ]; then
    while IFS= read -r line; do
      base=$(echo "$line" | awk '{print $1}')
      n=$(echo "$line" | awk '{print $2}')
      echo "⚠️  $project_scripts/${base}_v*.py|.js 累计 $n 个版本 — 考虑归档 archive_scripts/"
      WARN_COUNT=$((WARN_COUNT+1))
    done <<< "$basenames"
  fi
done < <(find projects -type d -name "scripts" 2>/dev/null)

# 仅输出 warning，不阻断 commit
if [ "$WARN_COUNT" -gt 0 ]; then
  echo ""
  echo "🟡 housekeeping warnings: $WARN_COUNT 处（不阻断，可后续清理）"
fi

exit 0
