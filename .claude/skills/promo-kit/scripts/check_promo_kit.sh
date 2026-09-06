#!/bin/bash
# promo-kit skill — Step B 自检（无第三方依赖，纯 bash + grep）
# 用法: bash check_promo_kit.sh <source.md>
# 按文件名后缀（-video / -grid / -copy）自动选校验集。
# FAIL（block）：合规红线 / 讲人话 / 结构完整；WARN（提示）：卖点句偏长。
set -euo pipefail

SRC="${1:-}"
if [ -z "$SRC" ] || [ ! -f "$SRC" ]; then
  echo "用法: bash check_promo_kit.sh <source.md>" >&2
  exit 2
fi

_sl_root="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
source "$_sl_root/.claude/hooks/lib/log.sh" 2>/dev/null
trap '_rc=$?; log_event skill "promo-kit" "$([ $_rc -eq 0 -o $_rc -eq 2 ] && echo completed || echo failed)" 2>/dev/null' EXIT

FAIL=0
FORM="generic"
case "$SRC" in
  *-video.md) FORM="video" ;;
  *-grid.md)  FORM="grid" ;;
  *-copy.md)  FORM="copy" ;;
esac

# 正文（去掉表格分隔行，避免 --- 干扰）；grep -v 全匹配时返回非零，|| true 兜住 set -e
BODY="$(grep -v -E '^[[:space:]]*\|?[[:space:]]*-{3,}' "$SRC" || true)"

# gate <label> <regex>：命中即打印行号 + 置 FAIL（在主 shell 内，不用 pipeline 子壳）
gate() {
  local label="$1"
  local re="$2"
  local hits
  hits="$(printf '%s\n' "$BODY" | grep -n -E "$re" || true)"
  if [ -n "$hits" ]; then
    echo "  ✗ ${label} ："
    printf '%s\n' "$hits" | sed 's/^/      /'
    FAIL=1
  else
    echo "  ✓ 通过"
  fi
}

echo "── 形态：$FORM ──"

echo "── 1 合规·承诺收益 ──"
gate "疑似承诺收益（金融宣发禁）" '稳赚|必赚|必涨|暴涨|暴富|翻倍|躺赚|包赚|保本|保收益|轻松赚|收益翻倍|抓住.*行情'

echo "── 2 合规·绝对化用语 ──"
gate "疑似绝对化用语" '最好|最强|最高|最优|最牛|最佳|最大化收益|全球第一|行业第一|唯一一(款|个)|100%|永久免费|绝对(安全|保障)|彻底根治'

echo "── 3 讲人话·内部术语泄漏 ──"
INT_HITS="$(printf '%s\n' "$BODY" | grep -n -E 'TRTC|WebRTC|[[:space:]]SDK|[[:space:]]API|[[:space:]]RTC|埋点|事件名|[A-Z]-[0-9]|[a-z]+_[a-z_]+' || true)"
if [ -n "$INT_HITS" ]; then
  echo "  ✗ 疑似内部术语 / 场景号 / 埋点名："
  printf '%s\n' "$INT_HITS" | sed 's/^/      /'
  FAIL=1
else
  echo "  ✓ 无内部术语泄漏"
fi

# ── 形态专项结构 ──
if [ "$FORM" = "video" ]; then
  echo "── 4 视频·文案列齐 ──"
  if grep -qE '中文文案|文案' "$SRC"; then
    echo "  ✓ 文案列在场"
  else
    echo "  ✗ 缺文案列（分镜表须含「中文文案」列）"; FAIL=1
  fi
  echo "── 5 视频·三段式在场 ──"
  if grep -qE '开场|钩子|痛点' "$SRC" && grep -qE 'CTA|结尾|行动' "$SRC"; then
    echo "  ✓ 开场钩子 + 结尾 CTA 在场"
  else
    echo "  ✗ 缺三段式（须有 开场/痛点钩子 与 结尾/CTA）"; FAIL=1
  fi
  echo "── 6 视频·截图列在场 ──"
  if grep -qE '截图' "$SRC"; then
    echo "  ✓ 截图列在场"
  else
    echo "  ✗ 缺截图列（官方分镜表须含「截图（中文）」等列）"; FAIL=1
  fi
fi

if [ "$FORM" = "copy" ]; then
  echo "── 4 短文案·三段齐 ──"
  if grep -qE '标题' "$SRC" && grep -qE '中段' "$SRC" && grep -qE '结尾' "$SRC"; then
    echo "  ✓ 标题 / 中段 / 结尾 三段齐"
  else
    echo "  ✗ 缺三段（标题 / 中段 / 结尾）"; FAIL=1
  fi
  echo "── 5 短文案·品牌 Tag ──"
  if grep -qE '#[A-Za-z火]' "$SRC"; then
    echo "  ✓ 品牌 Tag 在场"
  else
    echo "  ✗ 缺品牌 Tag（结尾须加 #活动标签）"; FAIL=1
  fi
fi

if [ "$FORM" = "grid" ]; then
  echo "── 4 图文·4 宫格 ──"
  ROWS="$(grep -cE '^[[:space:]]*\|[[:space:]]*[①②③④1-4]' "$SRC" || true)"
  if [ "${ROWS:-0}" -ge 4 ]; then
    echo "  ✓ 检测到 $ROWS 个宫格行（≥4）"
  else
    echo "  ✗ 宫格行不足 4（检测到 ${ROWS:-0}）"; FAIL=1
  fi
fi

# ── 卖点句偏长（WARN，不阻断；20 中文字 ≈ 66 UTF-8 字节，留余量 72）──
echo "── 卖点句长度（WARN）──"
LONG="$(printf '%s\n' "$BODY" | grep -E '^[[:space:]]*[-*✅]' | while IFS= read -r line; do
  txt="${line#*[-*✅]}"
  bytes=$(printf '%s' "$txt" | wc -c)
  [ "$bytes" -gt 72 ] && echo "    ⚠ 偏长：$(printf '%s' "$txt" | cut -c1-40)…"
done || true)"
if [ -n "$LONG" ]; then
  printf '%s\n' "$LONG"
  echo "    （建议每条卖点 ≤20 字，一句一信息）"
else
  echo "  ✓ 卖点句长度 OK"
fi

echo
if [ "$FAIL" -eq 0 ]; then
  echo "✅ 自检全绿（block 级检查通过；WARN 请自查）"
else
  echo "❌ 自检有 FAIL，按上方修"
fi
exit "$FAIL"
