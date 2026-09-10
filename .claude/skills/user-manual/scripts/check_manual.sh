#!/bin/bash
# user-manual skill — Step B 自检：build 冒烟 + 讲人话 + CJK 标点（完整用法见 usage() / -h）
set -euo pipefail

usage() {
  cat <<'EOF'
user-manual Step B 自检：手册 / 营销稿 md 交付前三连检查。

用法:
  bash .claude/skills/user-manual/scripts/check_manual.sh <source.md>   # Step B 自检
  bash .claude/skills/user-manual/scripts/check_manual.sh -h           # 本帮助

参数:
  <source.md>  源 md 路径（user-manual-*.md / promo-*.md）

检查项: 1) build_manual.py 全流程（缺图严格校验 + pandoc 转 docx）；
2) check_plain_language.py --strict（内部锚点 / 决策号 / 翻译腔）；3) check_cjk_punct.py --strict。
2 / 3 项脚本不在则跳过对应节（warn 提示）。

前置: pandoc 已装（build 步需要）；--help 不需要。

退出码:
  0 = 全绿
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

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL=0

echo "── 1/3 build（缺图严格校验 + pandoc 转 docx）──"
if python3 "$SKILL_DIR/scripts/build_manual.py" "$SRC"; then
  echo "  ✓ build 通过（零缺图）"
else
  echo "  ✗ build 失败（看上方缺图 / pandoc 报错）"
  FAIL=1
fi

echo "── 2/3 讲人话 ──"
if [ -f "$ROOT/scripts/check_plain_language.py" ]; then
  if python3 "$ROOT/scripts/check_plain_language.py" "$SRC" --strict; then
    echo "  ✓ 讲人话通过"
  else
    echo "  ✗ 讲人话违规（内部锚点 / 决策号 / 翻译腔）"
    FAIL=1
  fi
else
  echo "  ⚠ 跳过（check_plain_language.py 不在）"
fi

echo "── 3/3 CJK 标点 ──"
if [ -f "$ROOT/scripts/check_cjk_punct.py" ]; then
  if python3 "$ROOT/scripts/check_cjk_punct.py" "$SRC" --strict; then
    echo "  ✓ CJK 标点通过"
  else
    echo "  ✗ CJK 标点违规（修：python3 scripts/check_cjk_punct.py --fix \"$SRC\"）"
    FAIL=1
  fi
else
  echo "  ⚠ 跳过（check_cjk_punct.py 不在）"
fi

echo
if [ "$FAIL" -eq 0 ]; then
  echo "✅ 自检全绿"
else
  echo "❌ 自检有 FAIL，按上方修"
fi
exit "$FAIL"
