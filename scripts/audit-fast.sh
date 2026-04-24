#!/bin/bash
# audit-fast.sh — PostToolUse 快速自检（< 1s）
# 用法: bash scripts/audit-fast.sh <deliverable 绝对路径>
# exit 0 = 通过（静默），exit 1 = 违规（stderr 一行说明）
set -uo pipefail

FILE="${1:?用法: bash scripts/audit-fast.sh <deliverable>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ── 0. 路径过滤：只检查 projects/*/deliverables/* ──
case "$FILE" in
  */projects/*/deliverables/*) ;;
  *) exit 0 ;;
esac
# 跳过 archive/
case "$FILE" in
  */archive/*) exit 0 ;;
esac
[ -f "$FILE" ] || exit 0

# 提取项目名
PROJECT=$(echo "$FILE" | sed -E 's|.*/projects/([^/]+)/deliverables/.*|\1|')
SCENE_LIST="$ROOT/projects/$PROJECT/scene-list.md"
BASENAME=$(basename "$FILE")

FAIL=""

# ── 1. 场景编号一致性 ──
if [ -f "$SCENE_LIST" ]; then
  # 从 scene-list 表格第一列提取主场景编号（A/B/M/D/E/F/G 等，含连字号子编号）
  # 提取编号，复合编号（B-1a/b/c）只取第一个变体（B-1a）
  SCENE_IDS=$(grep -E '^\|' "$SCENE_LIST" \
    | grep -vE '^\| *编号|^\| *---' \
    | sed -E 's/^\| *([^ |]+).*/\1/' \
    | sed -E 's|/.*||' \
    | grep -E '^[A-Z]' \
    | grep -vE '本项目场景|动作|目标' \
    | sort -u || true)

  if [ -n "$SCENE_IDS" ]; then
    MISSING=""
    for sid in $SCENE_IDS; do
      # 在 HTML/docx(zip 不查)/md 里找编号引用
      if ! grep -qi "${sid}[^a-zA-Z0-9]\\|${sid}\$" "$FILE" 2>/dev/null; then
        MISSING="$MISSING $sid"
      fi
    done
    if [ -n "$MISSING" ]; then
      FAIL="场景编号缺失:${MISSING} (vs $SCENE_LIST)"
    fi
  fi
fi

# ── 2. 命名前缀规范 ──
# 动态读取所有 SKILL.md 的 output_prefix（排除 none）
VALID_PREFIXES=""
for f in "$ROOT"/.claude/skills/*/SKILL.md; do
  pfx=$(sed -n 's/^output_prefix: *//p' "$f" 2>/dev/null)
  [ -z "$pfx" ] && continue
  [ "$pfx" = "none" ] && continue
  VALID_PREFIXES="$VALID_PREFIXES|$pfx"
done
VALID_PREFIXES="${VALID_PREFIXES#|}"

if [ -n "$VALID_PREFIXES" ]; then
  # 文件名如果以某个已知前缀开头就合法
  if ! echo "$BASENAME" | grep -qE "^($VALID_PREFIXES)"; then
    # 也可能是中文开头的 deliverable（如「活动中心_交互大图_v4.9.html」），只要含已知 skill 关键字也行
    # 仅对英文文件名严格校验前缀
    if echo "$BASENAME" | grep -qE '^[a-zA-Z]'; then
      FAIL="${FAIL:+$FAIL; }命名前缀不规范: '$BASENAME' 不匹配任何 skill output_prefix ($VALID_PREFIXES)"
    fi
  fi
fi

# ── 3. FILL 占位残留 ──
case "$BASENAME" in
  *.html|*.md)
    for kw in "FILL_START:" "FILL_END:" "待填充"; do
      COUNT=$(grep -c "$kw" "$FILE" 2>/dev/null || true)
      if [ "$COUNT" -gt 0 ]; then
        FAIL="${FAIL:+$FAIL; }占位符残留 ${kw} x${COUNT}"
      fi
    done
    ;;
esac

# ── 4. CJK 字体顺序 ──
case "$BASENAME" in
  *.html)
    if grep -q "font-family:.*'DM Sans'.*'Noto Sans SC'" "$FILE" 2>/dev/null || \
       grep -q "font-family:.*'Inter'.*'Noto Sans SC'" "$FILE" 2>/dev/null; then
      FAIL="${FAIL:+$FAIL; }字体顺序违规: 英文字体排在 CJK 前"
    fi
    ;;
esac

# ── 5. 差量标签残留（IMAP 专项） ──
case "$BASENAME" in
  imap-*|*交互大图*)
    BAD=$(grep -cE 'ann-tag.*(new|chg|del)' "$FILE" 2>/dev/null || true)
    if [ "$BAD" -gt 0 ]; then
      FAIL="${FAIL:+$FAIL; }IMAP 差量标签残留 ann-tag.(new|chg|del) ×$BAD"
    fi
    ;;
esac

# ── 6. 逐 Scene 组件计数（IMAP HTML） ──
case "$BASENAME" in
  imap-*.html|*交互大图*.html|*IMAP*.html)
    SCENE_IDS_HTML=$(grep -oE 'id="scene-[^"]*"' "$FILE" 2>/dev/null | grep -oE 'scene-[^"]*' | sed 's/^scene-//' || true)
    if [ -n "$SCENE_IDS_HTML" ]; then
      for sid in $SCENE_IDS_HTML; do
        BLOCK=$(sed -n "/id=\"scene-${sid}\"/,/id=\"scene-[^\"]*\"/p" "$FILE" | sed '$d')
        [ -z "$BLOCK" ] && BLOCK=$(sed -n "/id=\"scene-${sid}\"/,\$p" "$FILE")
        s_aw=$(echo "$BLOCK" | grep -c 'class="aw"' || true)
        s_anno=$(echo "$BLOCK" | grep -c 'class="anno ' || true)
        s_tag=$(echo "$BLOCK" | grep -c 'class="ann-tag' || true)
        s_note=$(echo "$BLOCK" | grep -c 'class="flow-note"' || true)
        MISS=""
        [ "$s_aw" -eq 0 ] && MISS="${MISS}.aw "
        [ "$s_anno" -eq 0 ] && MISS="${MISS}.anno "
        [ "$s_tag" -eq 0 ] && MISS="${MISS}.ann-tag "
        [ "$s_note" -eq 0 ] && MISS="${MISS}.flow-note "
        [ -n "$MISS" ] && FAIL="${FAIL:+$FAIL; }Scene $sid 缺组件: $MISS"
      done
    fi
    ;;
esac

# ── 输出 ──
if [ -n "$FAIL" ]; then
  echo "❌ audit-fast: $FAIL" >&2
  exit 1
fi
exit 0
