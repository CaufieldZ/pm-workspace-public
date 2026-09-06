#!/usr/bin/env bash
set -euo pipefail
# IMAP 综合自检 — 薄 wrapper，逻辑见 ../../_shared/check_voice_html.sh
# 用法: bash check_imap.sh <imap.html> [<scene-list.md>]
exec bash "$(dirname "$0")/../../_shared/check_voice_html.sh" imap "$@"
