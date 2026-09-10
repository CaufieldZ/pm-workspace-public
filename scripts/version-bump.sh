#!/bin/bash
# version-bump.sh — 版本升级：归档旧版 → 按新版本号重命名 → 更新文件内版本号
set -euo pipefail

usage() {
  cat <<'EOF'
版本升级：把 projects/<项目名>/deliverables/ 顶层带版本号的产物归档旧版、重命名为下一版本并更新文件内版本号（执行前交互确认）。
用法：
    bash scripts/version-bump.sh <项目名>
参数：
    <项目名>    projects/ 下的项目目录名（英文短名）
示例：
    bash scripts/version-bump.sh <项目名>
前置：在 git 仓库内运行；<项目名> 需含 deliverables/ 目录，仅扫描其顶层 .html/.md/.docx（--help 不需要）
退出码：
    0 = 成功 / 无可升版本产物 / 确认阶段输入非 y 主动中止
    1 = deliverables/ 不存在等错误
EOF
}
case "${1:-}" in
  -h|--help) usage; exit 0 ;;
esac

PROJECT="${1:?Usage: bash scripts/version-bump.sh <project-name>}"
ROOT="$(git rev-parse --show-toplevel)"
PROJECT_DIR="$ROOT/projects/$PROJECT"
DELIV_DIR="$PROJECT_DIR/deliverables"
ARCHIVE_DIR="$DELIV_DIR/archive"

[ -d "$DELIV_DIR" ] || { echo "ERR: deliverables/ not found: $DELIV_DIR"; exit 1; }
mkdir -p "$ARCHIVE_DIR"

echo "=========================================="
echo "  Version Bump — $PROJECT"
echo "=========================================="
echo ""

# ─── Discover deliverables and their current versions ───

echo "--- Current Deliverables ---"
BUMP_LIST=""
for f in "$DELIV_DIR"/*; do
  [ -f "$f" ] || continue
  filename=$(basename "$f")
  ext="${filename##*.}"
  case "$ext" in
    html|docx|md) ;;
    *) continue ;;
  esac

  # Extract version: [Vv]{major}.{minor} or [Vv]{number} (preserve case)
  # 前缀支持 _ 与 - 两种（老 _v1 命名 + 现行 {prefix}-{project}-v{N} 连字符规范）
  if echo "$filename" | grep -qoE '[_\-][Vv][0-9]+\.[0-9]+\.'; then
    CUR_VER=$(echo "$filename" | grep -oE '[Vv][0-9]+\.[0-9]+' | tail -1)
    V_PREFIX="${CUR_VER:0:1}"
    MAJOR=$(echo "$CUR_VER" | sed -E 's/[Vv]([0-9]+)\.([0-9]+)/\1/')
    MINOR=$(echo "$CUR_VER" | sed -E 's/[Vv]([0-9]+)\.([0-9]+)/\2/')
    NEW_MINOR=$((MINOR + 1))
    NEW_VER="${V_PREFIX}${MAJOR}.${NEW_MINOR}"
  elif echo "$filename" | grep -qoE '[_\-][Vv][0-9]+\.'; then
    CUR_VER=$(echo "$filename" | grep -oE '[Vv][0-9]+' | tail -1)
    V_PREFIX="${CUR_VER:0:1}"
    CUR_NUM=$(echo "$CUR_VER" | sed -E 's/[Vv]//')
    NEW_NUM=$((CUR_NUM + 1))
    NEW_VER="${V_PREFIX}${NEW_NUM}"
  else
    echo "  SKIP  $filename  (no version in filename)"
    continue
  fi

  NEW_FILENAME=$(echo "$filename" | sed "s/${CUR_VER}/${NEW_VER}/")
  printf "  %-50s  %s → %s\n" "$filename" "$CUR_VER" "$NEW_VER"
  BUMP_LIST="${BUMP_LIST:+$BUMP_LIST|}$filename|$CUR_VER|$NEW_VER|$NEW_FILENAME|$ext"
done

if [ -z "$BUMP_LIST" ]; then
  echo "  No versionable deliverables found."
  exit 0
fi

echo ""
echo "Proceed? [y/N] "
read -r CONFIRM
[ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ] || { echo "Aborted."; exit 0; }

echo ""
echo "--- Executing ---"

# ─── Process each file ───
# BUMP_LIST 每项 5 字段（filename|cur_ver|new_ver|new_filename|ext）以 | 连接：
# tr 展开成行 → paste 5 列（原 6 列会把下一项首字段吞进当前行，字段错位：filename 变版本号）

echo "$BUMP_LIST" | tr '|' '\n' | paste -d'|' - - - - - | while IFS='|' read -r filename cur_ver new_ver new_filename ext; do
  [ -z "$filename" ] && continue

  OLD_PATH="$DELIV_DIR/$filename"
  NEW_PATH="$DELIV_DIR/$new_filename"
  ARCHIVE_PATH="$ARCHIVE_DIR/$filename"

  # 1. Archive old version
  cp "$OLD_PATH" "$ARCHIVE_PATH"
  echo "  ARCHIVE  $filename → archive/"

  # 2. Rename to new version
  mv "$OLD_PATH" "$NEW_PATH"
  echo "  RENAME   $filename → $new_filename"

  # 3. Update internal version numbers (HTML title/header, docx not supported here)
  case "$ext" in
    html)
      # Replace version in <title> and <h1> tags
      sed -i.bak "s/${cur_ver}/${new_ver}/g" "$NEW_PATH" 2>/dev/null || true
      rm -f "$NEW_PATH.bak" 2>/dev/null || true
      REPLACED=$(grep -c "${new_ver}" "$NEW_PATH" 2>/dev/null || echo 0)
      echo "  INTERNAL $new_filename ($REPLACED occurrences of $new_ver)"
      ;;
    md)
      sed -i.bak "s/${cur_ver}/${new_ver}/g" "$NEW_PATH" 2>/dev/null || true
      rm -f "$NEW_PATH.bak" 2>/dev/null || true
      echo "  INTERNAL $new_filename (sed replace)"
      ;;
    docx)
      echo "  INTERNAL $new_filename (docx: manual update needed for internal version)"
      ;;
  esac

  echo ""
done

echo ""
echo "=========================================="
echo "  Version bump complete."
echo "  Archive: $ARCHIVE_DIR"
echo "  Remember: run impact-check.sh after bump"
echo "=========================================="
