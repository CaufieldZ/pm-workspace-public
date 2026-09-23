#!/bin/bash
# promo-kit skill — Step B 自检（完整用法见 usage() / -h）
set -euo pipefail

usage() {
  cat <<'EOF'
promo-kit Step B 自检：上线宣发四形态（launch-*-video/-grid/-poster/-copy.md）的结构 / 讲人话 / 合规红线机械检查。
无第三方依赖，纯 bash + grep；按文件名后缀（-video / -grid / -poster / -copy）自动选校验集。

用法:
  bash .claude/skills/promo-kit/scripts/check_promo_kit.sh <source.md>   # Step B 自检
  bash .claude/skills/promo-kit/scripts/check_promo_kit.sh -h           # 本帮助

参数:
  <source.md>  宣发稿路径；文件名后缀决定形态专项检查，无匹配后缀按 generic 只跑通用项

检查项: FAIL（阻断）：合规红线（承诺收益 / 绝对化用语）/ 讲人话（内部术语 / 场景号 / 埋点名泄漏）/
形态结构（视频三段式 + 文案列 / 短文案三段 + 品牌 Tag / 4 宫格行数 / 海报张数 + 主副标题 + 支持项）/
海报主副标题字数（汉字，不含标点）/ 海报锚位卡（≥3 条，关系取值在闭集内、非顺承、证据与专属理由均具名非空）/
视觉规格块（-poster 与 -grid：画幅 / 安全区 / 文字落位 / 底图来源与遮挡四字段齐、未留占位，画幅取自闭集）；
WARN（提示）：卖点句 > 20 字 / 海报支持项 > 4 条 / -video 缺画幅与安全区。

字数是体检项不是写作目标：先写清楚再收短，别先定长度往格子里塞（塞出来的是凑字句）。
卖点句长度只扫卖点区，「出图说明」等内部段不扫。

前置: 无（纯文本扫描，--help 亦不需要）。

退出码:
  0 = 全绿（WARN 请自查）
  1 = 有 FAIL 项
  2 = 缺参数或文件不存在
EOF
}

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
esac

SRC="${1:-}"
if [ -z "$SRC" ] || [ ! -f "$SRC" ]; then
  usage >&2
  exit 2
fi

_sl_root="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
source "$_sl_root/.claude/hooks/lib/log.sh" 2>/dev/null
trap '_rc=$?; log_event skill "promo-kit" "$([ $_rc -eq 0 -o $_rc -eq 2 ] && echo completed || echo failed)" 2>/dev/null' EXIT

FAIL=0
FORM="generic"
case "$SRC" in
  *-video.md)  FORM="video" ;;
  *-grid.md)   FORM="grid" ;;
  *-poster.md) FORM="poster" ;;
  *-copy.md)   FORM="copy" ;;
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
# 只扫对外可见部分：内部段（锚位卡 / 出图说明）本就该出现「埋点名」「PRD 模块」「场景号 A-1」
# 这类内部指称——锚位卡的证据槽还明确要求具名到这些。扫进去会与证据槽自相矛盾。
# 两道去法并用：按「（内部）/出图说明」标题截断，再显式剔除锚位行——后者不依赖标题标记，
# 产物漏写「（内部，不入画）」时证据槽仍不会被自己的禁词表拦。
TERM_BODY="$(printf '%s\n' "$BODY" | sed -E '/(内部|出图说明)/,$d' \
  | grep -vE '^[-*[:space:]]*锚位[[:space:]]*[：:]' || true)"
INT_HITS="$(printf '%s\n' "$TERM_BODY" | grep -n -E 'TRTC|WebRTC|[[:space:]]SDK|[[:space:]]API|[[:space:]]RTC|埋点|事件名|[A-Z]-[0-9]|[a-z]+_[a-z_]+' || true)"
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

if [ "$FORM" = "poster" ]; then
  echo "── 4 海报·4 张齐 ──"
  ROWS="$(grep -cE '^#{1,4}[[:space:]]*海报[[:space:]]*[1-4][[:space:]]*[·：:]|^\*\*海报[[:space:]]*[1-4][[:space:]]*[·：:]' "$SRC" || true)"
  if [ "${ROWS:-0}" -ge 4 ]; then
    echo "  ✓ 检测到 $ROWS 张海报（≥4）"
  else
    echo "  ✗ 海报张数不足 4（检测到 ${ROWS:-0}）"; FAIL=1
  fi
  echo "── 5 海报·主副标题齐 ──"
  MAIN="$(grep -cE '^[-*[:space:]]*主标题[[:space:]]*[：:]' "$SRC" || true)"
  SUB="$(grep -cE '^[-*[:space:]]*副标题[[:space:]]*[：:]' "$SRC" || true)"
  if [ "${MAIN:-0}" -ge 4 ] && [ "${SUB:-0}" -ge 4 ]; then
    echo "  ✓ 主标题 ${MAIN} / 副标题 ${SUB}"
  else
    echo "  ✗ 主标题或副标题不足 4 条（主 ${MAIN:-0} / 副 ${SUB:-0}）"; FAIL=1
  fi
  echo "── 6 海报·总览支持项 ──"
  SUP_LINE="$(grep -E '^[-*[:space:]]*支持[[:space:]]*[：:]' "$SRC" | head -1 || true)"
  if [ -n "$SUP_LINE" ]; then
    echo "  ✓ 总览「支持：」在场"
    ITEMS="$(printf '%s' "$SUP_LINE" | grep -o '、' | wc -l | tr -d ' ' || true)"
    if [ "${ITEMS:-0}" -gt 3 ]; then
      echo "    ⚠ 支持项超过 4 条（行内 ${ITEMS} 个顿号）—— 应为 3 项，与三张分述主题对应"
    fi
  else
    echo "  ✗ 缺总览「支持：」行"; FAIL=1
  fi

  # 字数口径：数汉字，不含标点 / 空格 / 分隔符「｜」（与硬规则 3 一致）
  _cjk() { printf '%s' "$1" | sed -E 's/^[-*[:space:]]*(主|副)标题[[:space:]]*[：:][[:space:]]*//' | grep -o '[一-龥]' | wc -l | tr -d ' '; }
  echo "── 7 海报·主副标题字数（汉字，不含标点）──"
  LENBAD=0
  while IFS= read -r l; do
    [ -z "$l" ] && continue
    n="$(_cjk "$l")"
    if [ "${n:-0}" -gt 14 ]; then
      echo "    ✗ 主标题 ${n} 字（上限 14）：$(printf '%s' "$l" | cut -c1-34)"; LENBAD=1
    fi
  done < <(grep -E '^[-*[:space:]]*主标题[[:space:]]*[：:]' "$SRC" || true)
  while IFS= read -r l; do
    [ -z "$l" ] && continue
    n="$(_cjk "$l")"
    if [ "${n:-0}" -gt 16 ]; then
      echo "    ✗ 副标题 ${n} 字（上限 16）：$(printf '%s' "$l" | cut -c1-34)"; LENBAD=1
    fi
  done < <(grep -E '^[-*[:space:]]*副标题[[:space:]]*[：:]' "$SRC" || true)
  if [ "$LENBAD" -eq 0 ]; then echo "  ✓ 主副标题字数在限内"; else FAIL=1; fi

  echo "── 8 海报·锚位卡（三张分述主标题）──"
  ANCHORS="$(grep -E '^[-*[:space:]]*锚位[[:space:]]*[：:]' "$SRC" || true)"
  N_ANCHOR="$(printf '%s\n' "$ANCHORS" | grep -c '锚位' || true)"
  if [ "${N_ANCHOR:-0}" -ge 3 ]; then
    echo "  ✓ 锚位卡 ${N_ANCHOR} 条（≥3）"
    # 注意：bash 3.2（macOS 系统 bash）无法解析含多字节字符的 case 模式，闭集判定一律走 grep。
    REL_BAD="$(printf '%s\n' "$ANCHORS" | while IFS= read -r l; do
      [ -z "$l" ] && continue
      # 取行内【第一个】「关系=…」的值，不按字段位置取：
      #   - 锚位名里引了整句主标题（含「｜」）时，按字段位置取会取到句子碎片 → 假 FAIL
      #   - 专属理由里再提到「关系=」时，整行贪婪匹配会取到最后一个 → 同样假 FAIL
      r="$(printf '%s' "$l" | grep -oE '关系[[:space:]]*[=＝][[:space:]]*[^｜|]+' | head -1 \
           | sed -E 's/^关系[[:space:]]*[=＝][[:space:]]*//' | tr -d '[:space:]')"
      if printf '%s' "$r" | grep -qE '^(分工|位移|对照|并列|在场|落点)$'; then
        :
      elif printf '%s' "$r" | grep -q '顺承'; then
        echo "      ✗ 自认顺承（顺承是降档，这句必须重写）：$(printf '%s' "$l" | cut -c1-34)"
      else
        echo "      ✗ 关系取值不在闭集（分工/位移/对照/并列/在场/落点）：$(printf '%s' "$l" | cut -c1-34)"
      fi
      if ! printf '%s' "$l" | grep -qE '专属理由[[:space:]]*[=＝][[:space:]]*[^[:space:]]'; then
        echo "      ✗ 缺「专属理由=…」（写不出就说明这是通用句）：$(printf '%s' "$l" | cut -c1-34)"
      fi
      # 证据槽：只校验「专属理由非空」时空口理由能过闸；要求具名出处，且自认不合格的一律拦。
      if ! printf '%s' "$l" | grep -qE '证据[[:space:]]*[=＝][[:space:]]*[^[:space:]]'; then
        echo "      ✗ 缺「证据=…」（须具名出处：PRD 模块 / 功能规格 / 埋点名 / 客诉原话 / 已核口径）：$(printf '%s' "$l" | cut -c1-34)"
      elif printf '%s' "$l" | grep -qE '证据[[:space:]]*[=＝][[:space:]]*(待补证|禁止|无依据|无出处|不明)'; then
        echo "      ✗ 证据自认不合格（最终稿只能用具名且已确认的出处）：$(printf '%s' "$l" | cut -c1-34)"
      fi
    done || true)"
    if [ -n "$REL_BAD" ]; then printf '%s\n' "$REL_BAD"; FAIL=1; fi
  else
    echo "  ✗ 锚位卡不足 3 条（检测到 ${N_ANCHOR:-0}）—— 三张分述主标题各需一条，格式：锚位：关系=分工 ｜ 证据=出处 ｜ 专属理由=…"; FAIL=1
  fi
fi

# ── 视觉规格块（-poster / -grid 强制 · -video 只查画幅与安全区，WARN）──
# 字段值必须真填：留着 {占位} 或写「待定 / TBD」等同没填，与证据槽「写待补证即自认不合格」同一把尺。
# 「按品牌规范，待设计侧确认」是合法值——那是一个看得见的待办，不是空话（promo-visual-spec.md §七）。
VIS_BAD=0
vis_check() {   # vis_check <字段名> [该行还必须命中的正则] [缺失时的补充说明]
  local label="$1" extra="${2:-}" extra_msg="${3:-}" line val
  line="$(grep -E "^[-*[:space:]]*${label}[[:space:]]*[：:]" "$SRC" | head -1 || true)"
  if [ -z "$line" ]; then
    echo "    ✗ 缺「${label}：」字段（骨架见 promo-kit-templates.md 的「视觉规格」块）"; VIS_BAD=1; return
  fi
  val="$(printf '%s' "$line" | sed -E "s/^[-*[:space:]]*${label}[[:space:]]*[：:][[:space:]]*//")"
  if [ -z "$val" ]; then
    echo "    ✗ 「${label}」为空"; VIS_BAD=1; return
  fi
  if printf '%s' "$line" | grep -q '[{}]'; then
    echo "    ✗ 「${label}」还留着 {占位} 未填实：$(printf '%s' "$val" | cut -c1-40)"; VIS_BAD=1; return
  fi
  if printf '%s' "$val" | grep -qE '^(待定|TBD|tbd|待补|待确认|暂无|—|-)$'; then
    echo "    ✗ 「${label}」写成「${val}」等同没填"; VIS_BAD=1; return
  fi
  if [ -n "$extra" ] && ! printf '%s' "$line" | grep -qEi "$extra"; then
    echo "    ✗ 「${label}」${extra_msg}"; VIS_BAD=1; return
  fi
  echo "    ✓ ${label}"
}

echo "── 视觉规格块 ──"
# 画幅闭集：宽高均为 16 的倍数才被 image_gen 收，自拟的 1080x1920 会在真花钱之前被拒。
# 光写「见 promo-visual-spec.md」绑不住取值（实测 4 次里 3 次自拟了非法尺寸），闭集在这里机械校验。
VIS_SIZES='1536[x×]1536|1280[x×]1600|1152[x×]2048|2048[x×]1152|1536[x×]2048'

if [ "$FORM" = "poster" ] || [ "$FORM" = "grid" ]; then
  vis_check "画幅" "$VIS_SIZES" \
    "没取画幅表里的标准尺寸（1536x1536 / 1280x1600 / 1152x2048 / 2048x1152 / 1536x2048）——自拟尺寸宽高多半不是 16 的倍数，image_gen 会拒"
  vis_check "安全区"
  vis_check "文字落位"
  vis_check "底图来源" '遮挡[[:space:]]*[：:][[:space:]]*[^[:space:]]' \
    "行内缺「遮挡：…」——敏感区（金额 / 昵称 / UID / 技术状态文字）要点名，确实没有就写「遮挡：无」"
  if [ "$VIS_BAD" -ne 0 ]; then FAIL=1; fi
elif [ "$FORM" = "video" ]; then
  # 视频的视觉信息主要落在分镜表的截图列，这里只提示不阻断
  for f in 画幅 安全区; do
    if grep -qE "^[-*[:space:]]*${f}[[:space:]]*[：:][[:space:]]*[^[:space:]]" "$SRC"; then
      echo "    ✓ ${f}"
    else
      echo "    ⚠ 缺「${f}：」（建议补视觉规格块，见 promo-visual-spec.md §一 / §二）"
    fi
  done
else
  echo "  — 本形态不查（视觉规格块适用 -poster / -grid / -video）"
fi

# ── 卖点句偏长（WARN，不阻断；20 中文字 ≈ 66 UTF-8 字节，留余量 72）──
# 只扫卖点句所在区，砍掉「出图说明」这类内部段——内部段按骨架要求写四张关系/配图来源/数字口径，
# 本就长于 20 字，扫进去是误报（会把产出逼去拆碎内部说明）。
SCAN_BODY="$(printf '%s\n' "$BODY" | sed -E '/(内部|出图说明)/,$d')"
echo "── 卖点句长度（WARN）──"
LONG="$(printf '%s\n' "$SCAN_BODY" | grep -E '^[[:space:]]*[-*✅]' | while IFS= read -r line; do
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
