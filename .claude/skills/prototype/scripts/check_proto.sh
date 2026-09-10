#!/usr/bin/env bash
set -euo pipefail
# prototype 综合自检 — 薄 wrapper，逻辑见 ../../_shared/check_voice_html.sh
# 用法: bash check_proto.sh <prototype.html> [<scene-list.md>]
exec bash "$(dirname "$0")/../../_shared/check_voice_html.sh" proto "$@"
