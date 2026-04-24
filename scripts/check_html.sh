#!/bin/bash
# 通用 HTML 产出物自检脚本（交互大图 / 原型 通用）
# 用法: bash scripts/check_html.sh <html文件路径> <scene-list.md路径> [imap|proto]
set -euo pipefail

FILE="${1:?用法: bash scripts/check_html.sh <html> <scene-list> [imap|proto]}"
SCENE_LIST="${2:?缺少 scene-list.md 路径}"
TYPE="${3:-imap}"

echo "=========================================="
echo "  HTML 自检: $(basename "$FILE") [$TYPE]"
echo "=========================================="
FAIL=0

# --- 1. 基础结构 ---
echo ""
echo "--- 基础结构 ---"
LINES=$(wc -l < "$FILE")
echo "总行数: $LINES"
[ "$LINES" -lt 500 ] && echo "❌ 行数异常（< 500）" && FAIL=1

grep -q '</html>' "$FILE" && echo "✅ HTML 已闭合" || { echo "❌ HTML 未闭合"; FAIL=1; }

# --- 1.5 字体顺序检查 ---
echo ""
echo "--- 字体顺序检查 ---"
if grep -q "font-family:.*'DM Sans'.*'Noto Sans SC'" "$FILE" 2>/dev/null; then
  echo "❌ 字体顺序错误：DM Sans 在 Noto Sans SC 前面（应 CJK 优先）"
  FAIL=1
else
  echo "✅ 字体顺序正确（或未使用此字体组合）"
fi

# --- 2. 占位符残留 ---
echo ""
echo "--- 占位符检查 ---"
for kw in "待填充" "FILL_START:" "FILL_END:"; do
  COUNT=$(grep -c "$kw" "$FILE" 2>/dev/null || true)
  [ "$COUNT" -gt 0 ] && echo "❌ 残留「$kw」共 $COUNT 处" && FAIL=1
done
[ "$FAIL" -eq 0 ] && echo "✅ 无占位符残留"

# --- 3. 场景编号对照 ---
echo ""
echo "--- 场景编号对照 (vs scene-list.md) ---"
SCENE_IDS=$(grep -oE '\b[A-Z](-[0-9]+)?\b' "$SCENE_LIST" 2>/dev/null | sort -u | grep -v '^[A-Z]$' || true)
# 备用：从表格中提取场景编号（兼容 macOS，无需 -P）
if [ -z "$SCENE_IDS" ]; then
  SCENE_IDS=$(sed -n 's/^|[[:space:]]*\([A-Z]-\{0,1\}[0-9]*\)[[:space:]].*/\1/p' "$SCENE_LIST" 2>/dev/null | sort -u)
fi
if [ -z "$SCENE_IDS" ]; then
  echo "⚠️ 无法从 scene-list.md 提取编号，跳过"
else
  MISSING=""
  for sid in $SCENE_IDS; do
    grep -qi "scene.*${sid}\|id.*${sid}\|${sid}[：:. ]" "$FILE" || MISSING="$MISSING $sid"
  done
  [ -z "$MISSING" ] && echo "✅ 全部编号已覆盖" || { echo "❌ 缺失编号:$MISSING"; FAIL=1; }
fi

# --- 4. JS 交互 ---
echo ""
echo "--- JS 交互检查 ---"
EVENTS=$(grep -c 'addEventListener\|onclick\|onchange\|onClick' "$FILE" 2>/dev/null || true)
echo "事件绑定数: $EVENTS"
[ "$EVENTS" -eq 0 ] && echo "❌ 无任何交互事件" && FAIL=1

# onclick 引用的函数是否存在
echo ""
echo "--- 函数引用检查 ---"
ONCLICK_FNS=$(grep -oE 'onclick="([^"(]+)' "$FILE" 2>/dev/null | sed 's/onclick="//g' | sort -u || true)
for fn in $ONCLICK_FNS; do
  grep -q "function $fn\|const $fn\|$fn =" "$FILE" || echo "❌ onclick 引用了不存在的函数: $fn"
done

# --- 5. 导航-页面匹配 ---
echo ""
echo "--- 导航-页面匹配 ---"
NAV=$(grep -c 'nav-item\|goPage\|switchView\|switchTab\|gnav' "$FILE" 2>/dev/null || true)
PAGE=$(grep -c 'class="page"\|class="view"\|id="part\|id="page-\|id="view-' "$FILE" 2>/dev/null || true)
echo "导航项: $NAV / 页面区: $PAGE"

# --- 6. 弹窗关闭检查 ---
echo ""
echo "--- 弹窗关闭检查 ---"
MODAL=$(grep -c 'class="modal\|class=.modal' "$FILE" 2>/dev/null || true)
CLOSE=$(grep -c 'closeModal\|hideModal\|close-btn\|✕\|display.*none' "$FILE" 2>/dev/null || true)
echo "弹窗数: $MODAL / 关闭逻辑: $CLOSE"
[ "$MODAL" -gt 0 ] && [ "$CLOSE" -eq 0 ] && echo "❌ 有弹窗但无关闭机制" && FAIL=1

# --- 7. 类型专属检查 ---
if [ "$TYPE" = "imap" ]; then
  echo ""
  echo "--- 交互大图专属 ---"
  grep -q 'side-nav\|flow' "$FILE" && echo "✅ 有侧导航/流程结构" || echo "⚠️ 缺侧导航"
  grep -q 'scroll\|updateNav\|IntersectionObserver' "$FILE" && echo "✅ 有滚动交互" || echo "⚠️ 无滚动交互"

  # --- 组件完整性检查 ---
  echo ""
  echo "--- 组件完整性检查 ---"
  SCENE_COUNT=$(grep -c 'id="scene-' "$FILE" 2>/dev/null || true)
  echo "Scene 数: $SCENE_COUNT"

  AW_COUNT=$(grep -c 'class="aw"' "$FILE" 2>/dev/null || true)
  ANNO_COUNT=$(grep -c 'class="anno ' "$FILE" 2>/dev/null || true)
  CARD_TITLE_COUNT=$(grep -c 'class="card-title"' "$FILE" 2>/dev/null || true)
  ANN_ITEM_COUNT=$(grep -c 'class="ann-item"' "$FILE" 2>/dev/null || true)
  ANN_TAG_COUNT=$(grep -c 'class="ann-tag' "$FILE" 2>/dev/null || true)
  FLOW_NOTE_COUNT=$(grep -c 'class="flow-note"' "$FILE" 2>/dev/null || true)
  INFO_BOX_COUNT=$(grep -c 'class="info-box' "$FILE" 2>/dev/null || true)

  echo "箭头 .aw: $AW_COUNT | 标注框 .anno: $ANNO_COUNT | 卡片标题: $CARD_TITLE_COUNT"
  echo "注释条目 .ann-item: $ANN_ITEM_COUNT | 优先级标签 .ann-tag: $ANN_TAG_COUNT"
  echo "屏幕说明 .flow-note: $FLOW_NOTE_COUNT | 信息框 .info-box: $INFO_BOX_COUNT"

  if [ "$SCENE_COUNT" -gt 0 ]; then
    [ "$AW_COUNT" -eq 0 ] && echo "❌ 无任何箭头(.aw)，屏幕间缺流向" && FAIL=1
    [ "$ANNO_COUNT" -eq 0 ] && echo "❌ 无任何标注框(.anno)，注释无法对应屏幕区域" && FAIL=1
    [ "$ANN_TAG_COUNT" -eq 0 ] && echo "❌ 无任何优先级标签(.ann-tag)" && FAIL=1
    [ "$FLOW_NOTE_COUNT" -eq 0 ] && echo "❌ 无任何屏幕说明(.flow-note)" && FAIL=1
    [ "$INFO_BOX_COUNT" -eq 0 ] && echo "⚠️ 无信息框(.info-box)，建议至少 1 个"

    # 比例检查
    MIN_AW=$((SCENE_COUNT - 1))
    [ "$MIN_AW" -gt 0 ] && [ "$AW_COUNT" -lt "$MIN_AW" ] && echo "⚠️ 箭头数($AW_COUNT) < Scene-1($MIN_AW)，可能遗漏"

    # --- 逐 Scene 组件完整性检查 ---
    echo ""
    echo "--- 逐 Scene 组件检查 ---"
    SCENE_IDS_HTML=$(grep -oE 'id="scene-[^"]*"' "$FILE" 2>/dev/null | grep -oE 'scene-[^"]*' | sed 's/^scene-//' || true)
    if [ -n "$SCENE_IDS_HTML" ]; then
      PER_SCENE_FAIL=0
      for sid in $SCENE_IDS_HTML; do
        # 提取 scene 块（从 id="scene-X" 到下一个 id="scene-" 或文件末尾）
        BLOCK=$(sed -n "/id=\"scene-${sid}\"/,/id=\"scene-[^\"]*\"/p" "$FILE" | sed '$d')
        [ -z "$BLOCK" ] && BLOCK=$(sed -n "/id=\"scene-${sid}\"/,\$p" "$FILE")

        s_aw=$(echo "$BLOCK" | grep -c 'class="aw"' || true)
        s_anno=$(echo "$BLOCK" | grep -c 'class="anno ' || true)
        s_tag=$(echo "$BLOCK" | grep -c 'class="ann-tag' || true)
        s_note=$(echo "$BLOCK" | grep -c 'class="flow-note"' || true)

        MISSING_COMPS=""
        [ "$s_aw" -eq 0 ] && MISSING_COMPS="${MISSING_COMPS}.aw "
        [ "$s_anno" -eq 0 ] && MISSING_COMPS="${MISSING_COMPS}.anno "
        [ "$s_tag" -eq 0 ] && MISSING_COMPS="${MISSING_COMPS}.ann-tag "
        [ "$s_note" -eq 0 ] && MISSING_COMPS="${MISSING_COMPS}.flow-note "

        if [ -n "$MISSING_COMPS" ]; then
          echo "  ❌ Scene $sid missing: $MISSING_COMPS"
          PER_SCENE_FAIL=1
          FAIL=1
        fi
      done
      [ "$PER_SCENE_FAIL" -eq 0 ] && echo "  ✅ 所有 Scene 组件完整"
    else
      echo "  ⚠️ 未找到 id=\"scene-*\" 标记，跳过逐 Scene 检查"
    fi
  fi
fi

if [ "$TYPE" = "proto" ]; then
  echo ""
  echo "--- 原型专属 ---"
  echo "数据数组:"
  grep -oP 'const \w+ = \[' "$FILE" 2>/dev/null | sed 's/const //;s/ = \[//' | while read arr; do
    echo "  $arr"
  done
fi

# --- 结果 ---
echo ""
echo "=========================================="
[ "$FAIL" -eq 0 ] && echo "✅ 自检通过" || echo "❌ 自检未通过（见上方错误）"
echo "=========================================="
exit $FAIL
