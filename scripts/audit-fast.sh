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

# ── 0. in-file audit-skip 注释全量豁免 ──
# 产物头部含 <!-- audit-skip --> 则跳过所有检查
# 适用：独立工具规格文档、方案型交付物等不走标准 pipeline 的产物
if head -10 "$FILE" | grep -q 'audit-skip'; then
  exit 0
fi

# 提取项目名
PROJECT=$(echo "$FILE" | sed -E 's|.*/projects/([^/]+)/deliverables/.*|\1|')
SCENE_LIST="$ROOT/projects/$PROJECT/scene-list.md"
BASENAME=$(basename "$FILE")

FAIL=""

# ── 0. standalone 产物跳过场景编号检查 ──
# standalone skill (mrd-review / competitor-analysis 等) 不在 pipeline 上,
# 产物本就不应该带 scene-list 编号 (例: 评审 MRD 时产品场景还没定)
STANDALONE_PREFIXES=""
for f in "$ROOT"/.claude/skills/*/SKILL.md; do
  type_val=$(sed -n 's/^type: *//p' "$f" 2>/dev/null | head -1 | tr -d ' ')
  [ "$type_val" != "standalone" ] && continue
  pfx=$(sed -n 's/^output_prefix: *//p' "$f" 2>/dev/null | head -1 | tr -d ' ')
  [ -z "$pfx" ] && continue
  [ "$pfx" = "none" ] && continue
  STANDALONE_PREFIXES="$STANDALONE_PREFIXES|$pfx"
done
STANDALONE_PREFIXES="${STANDALONE_PREFIXES#|}"

SKIP_SCENE_CHECK=0
if [ -n "$STANDALONE_PREFIXES" ] && echo "$BASENAME" | grep -qE "^($STANDALONE_PREFIXES)"; then
  SKIP_SCENE_CHECK=1
fi

# ── 0b. 方案型项目跳过 scene code 严格匹配 ──
# 方案型项目 (跨系统 / 资金流转 / 多团队共建 / 纯后端无 UI) 不走标准 pipeline,
# scene-list.md 作为主题索引使用, 不做场景编号强绑定.
# 识别方式: scene-list.md 头部含 `项目类型: 方案型`
if [ -f "$SCENE_LIST" ]; then
  if head -20 "$SCENE_LIST" | grep -qE '项目类型.{0,10}方案型'; then
    SKIP_SCENE_CHECK=1
  fi
fi

# ── 0c. partial delta → 子集校验模式 ──
# baseline 线 partial delta 只动本轮场景, 不应要求覆盖整张 scene-list.
# 改用 subset 校验: delta 引用的编号必须 ⊆ scene-list (抓引用不存在的编号),
# 替掉「整张 scene-list 关严格匹配」的粗粒度跳过.
# 标记: scene-list.md 头部含 `audit-fast: 跳过 scene code 严格匹配`
PARTIAL_DELTA=0
if [ -f "$SCENE_LIST" ]; then
  if head -20 "$SCENE_LIST" | grep -qE 'audit-fast.{0,20}跳过.*scene code'; then
    PARTIAL_DELTA=1
  fi
fi

# ── 1. 场景编号一致性 ──
if [ -f "$SCENE_LIST" ] && [ "$SKIP_SCENE_CHECK" = "0" ]; then
  # 委托 Python（共享 lib.scene_match 严格匹配，避免单字符 ID 假阳）
  # PARTIAL_DELTA=1 → subset 校验（引用 ⊆ scene-list）；否则 full coverage（scene-list ⊆ 产物）
  MISSING=$(python3 - "$FILE" "$SCENE_LIST" "$PARTIAL_DELTA" 2>/dev/null <<'PY'
import sys, pathlib
# audit-fast.sh 调 python 时 __file__ 不准，向上找项目根定位 lib
cur = pathlib.Path(sys.argv[1]).resolve()
while cur.parent != cur:
    if (cur / 'scripts' / 'lib' / 'scene_match.py').exists():
        sys.path.insert(0, str(cur / 'scripts'))
        break
    cur = cur.parent
try:
    from lib.scene_match import (extract_scene_ids, find_missing_ids,
                                 extract_referenced_ids, find_undefined_ids)
except ImportError:
    sys.exit(0)
text = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
ids = extract_scene_ids(sys.argv[2])
if not ids:
    sys.exit(0)
if sys.argv[3] == '1':
    undefined = find_undefined_ids(extract_referenced_ids(text), ids)
    if undefined:
        print('UNDEFINED:' + ' '.join(undefined))
else:
    missing = find_missing_ids(ids, text)
    if missing:
        print(' '.join(missing))
PY
  )
  if [ -n "$MISSING" ]; then
    case "$MISSING" in
      UNDEFINED:*) FAIL="场景编号未定义(不在 scene-list):${MISSING#UNDEFINED:} (vs $SCENE_LIST)" ;;
      *)           FAIL="场景编号缺失:$MISSING (vs $SCENE_LIST)" ;;
    esac
  fi
fi

# ── 2. 命名前缀规范 ──
# 动态读取所有 SKILL.md 的 output_prefix（排除 none）
VALID_PREFIXES=""
for f in "$ROOT"/.claude/skills/*/SKILL.md; do
  pfx=$(sed -n 's/^output_prefix: *//p' "$f" 2>/dev/null)
  [ -z "$pfx" ] && continue
  [ "$pfx" = "none" ] && continue
  # 单 skill 多前缀：frontmatter 用「A- / B-」或「A-, B-」分隔，拆成正则交替
  pfx=$(echo "$pfx" | tr ',/' '  ' | tr -s ' ')
  for p in $pfx; do
    VALID_PREFIXES="$VALID_PREFIXES|$p"
  done
done
VALID_PREFIXES="${VALID_PREFIXES#|}"
# prd skill「交付前冷读」工序产物（cold_read.py 生成的盲点清单），非顶层 skill 输出但是合法交付物
VALID_PREFIXES="$VALID_PREFIXES|cold-read-"
# PRD 衍生对接 handoff（给开发 / 数据组的专项抽取文档，非 skill 输出但是合法交付物）
VALID_PREFIXES="$VALID_PREFIXES|handoff-"

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
# 加 class= 边界 + 词边界，避免误伤 class="ann-tag warn new-feature"
case "$BASENAME" in
  imap-*|*交互大图*)
    BAD=$(grep -cE 'class="[^"]*\bann-tag-(new|chg|del)\b' "$FILE" 2>/dev/null || true)
    if [ "$BAD" -gt 0 ]; then
      FAIL="${FAIL:+$FAIL; }IMAP 差量标签残留 ann-tag-(new|chg|del) ×${BAD}"
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
