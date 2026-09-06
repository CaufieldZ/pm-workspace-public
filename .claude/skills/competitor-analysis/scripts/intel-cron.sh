#!/usr/bin/env bash
# intel-cron.sh — crontab 入口，定时采集竞品公告 & 媒体内容
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
cd "$WORKSPACE_ROOT"
LOG_DIR="references/competitors/_logs"
mkdir -p "$LOG_DIR"
python3 .claude/skills/competitor-analysis/scripts/scheduled-scrape.py --all \
  2>&1 | tee "$LOG_DIR/scrape-$(date +%Y%m%d).log"
