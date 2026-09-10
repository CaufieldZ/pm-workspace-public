#!/bin/bash
# PreToolUse Read hook: 图片 Read 前多图限制预检（> 2000px / > 5MB 先压缩）
#
# 触发：Read 图片文件 且 ANTHROPIC_BASE_URL 含 aihub 网关特征（Bedrock 类内部网关）
# 行为：任意维度 > 2000px 或文件 > 5MB → exit 2 阻断，提示先跑 compress_image.py
# 放行：非 Bedrock 网关（中转站支持大图）/ 图片已满足限制 / PIL 无法读取（按满足处理）
# Escape：SKIP_READ_IMAGE_CHECK_GATE=1（Read 不经 Bash 管道，只 env 生效）
#
# 网关特征只写 aihub 子串，不写完整内部域名：
# .claude/hooks/ 会被 sync_public.sh 同步进 public repo，其 §3 通杀 sed 会替换
# 品牌词 / 内部域名（关键词清单见该脚本，此处不字面枚举防自指泄漏）；aihub 不在通杀清单，匹配仍精确。
# CLAUDE.md 规则: "Read 图片前预检:任意维度 > 2000px 或文件 > 5MB 先跑 compress_image.py 再 Read"

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"

INPUT=$(cat)
hook_parse_read

[ "$HOOK_TOOL_NAME" = "Read" ] || exit 0

FILE_PATH="$HOOK_FILE_PATH"
[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# 只处理图片后缀
case "${FILE_PATH##*.}" in
  png|jpg|jpeg|gif|webp|bmp|tif|tiff|heic) ;;
  *) exit 0 ;;
esac

# Bedrock 网关判定：baseurl 含 aihub 网关特征（完整域名不进 git）
case "${ANTHROPIC_BASE_URL:-}" in
  *aihub*) ;;
  *) exit 0 ;;
esac

check_skip_env "read-image-check" "SKIP_READ_IMAGE_CHECK_GATE" "$FILE_PATH"

# ── 1. 大小 / 尺寸预检（满足限制 → 放行）───────────────────────────────
FILE_SIZE=$(wc -c < "$FILE_PATH" 2>/dev/null | tr -d ' ')
MAX_BYTES=$((5 * 1024 * 1024))
SIZE_OVER=0; DIM_OVER=0; W="?"; H="?"

if [ -n "$FILE_SIZE" ] && [ "$FILE_SIZE" -gt "$MAX_BYTES" ]; then
  SIZE_OVER=1
else
  # PIL 查尺寸（lazy 加载）。输出 "1 W H"=超限 / "0 W H"=满足 / "ERR"=读取失败
  IMG_INFO=$(python3 - "$FILE_PATH" <<'PY' 2>/dev/null
import sys
from pathlib import Path
from PIL import Image
p = Path(sys.argv[1])
try:
    with Image.open(p) as im:
        w, h = im.size
except Exception:
    print("ERR")
else:
    print(f"{1 if (w > 2000 or h > 2000) else 0} {w} {h}")
PY
)
  if [ -n "$IMG_INFO" ] && [ "${IMG_INFO%% *}" = "1" ]; then
    DIM_OVER=1
    read -r _ W H <<< "$IMG_INFO"
  fi
fi

[ "$SIZE_OVER" = "0" ] && [ "$DIM_OVER" = "0" ] && exit 0

REL_PATH="${FILE_PATH#${CLAUDE_PROJECT_DIR:-$(pwd)}/}"
SIZE_MB=$(awk -v s="$FILE_SIZE" 'BEGIN { printf "%.1f", s / 1024 / 1024 }')
DIM_MSG=""
[ "$DIM_OVER" = "1" ] && DIM_MSG="尺寸 ${W}×${H}px"
[ "$SIZE_OVER" = "1" ] && DIM_MSG="$DIM_MSG${DIM_MSG:+ · }文件 $SIZE_MB MB"
[ -z "$DIM_MSG" ] && DIM_MSG="未知"

cat >&2 <<EOF
🚫 [read-image-check] 图片超出当前网关多图限制（任意维度 > 2000px 或 > 5MB）
   文件: ${REL_PATH}（${DIM_MSG}）
   原因: 当前网关为内部 Bedrock 网关，超限图直接 Read 会报错

   → 修法 1: python3 scripts/compress_image.py "${REL_PATH}"
       压缩后输出同目录 {文件名}-compressed.{后缀}，Read 压缩版
   → 修法 2: 多张批量: python3 scripts/compress_image.py a.png b.png c.png
   → 真不适用 → SKIP_READ_IMAGE_CHECK_GATE=1（仅确知网关接受大图时）
EOF
log_event gate read-image-check block "${REL_PATH} (${DIM_MSG})"
exit 2
