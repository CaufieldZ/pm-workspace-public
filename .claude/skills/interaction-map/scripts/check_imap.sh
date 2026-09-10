#!/usr/bin/env bash
set -euo pipefail
# IMAP 综合自检 — 薄 wrapper，逻辑见 ../../_shared/check_voice_html.sh
usage() {
  cat <<'EOF'
check_imap.sh — IMAP 交互大图产物综合自检（结构 + 文案讲人话 + ann-card 四禁）

用法:
    bash .claude/skills/interaction-map/scripts/check_imap.sh <file>.html [<scene-list.md>]

参数:
    <file>.html      IMAP 产物 HTML 路径（必填）
    <scene-list.md>  对照场景清单（可省略：从 HTML 路径自动推断同项目 scene-list.md）

前置: 无
退出码:
    0 = 通过（含 warn 也算过）
    1 = FAIL（结构 / 编号 / 组件 / 文案 / ann-card 四禁违规，明细见输出）
    2 = 参数错误（缺路径 / 文件不存在）

示例:
    bash .claude/skills/interaction-map/scripts/check_imap.sh <file>.html
    bash .claude/skills/interaction-map/scripts/check_imap.sh <file>.html <scene-list.md>
EOF
}
case "${1:-}" in
  -h|--help) usage; exit 0 ;;
esac
exec bash "$(dirname "$0")/../../_shared/check_voice_html.sh" imap "$@"
