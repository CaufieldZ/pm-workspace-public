#!/usr/bin/env python3
"""命令行 alias —— Layer 2 重构后实现搬到 screenshots.py。

老命令仍然可用（保持 CLAUDE.md 快捷路由表的命令字面量）：
    python3 .claude/skills/prd/scripts/prd_screenshots.py --project XXX

新脚本可直接调 screenshots.py（推荐）：
    python3 .claude/skills/prd/scripts/screenshots.py --project XXX
"""
from screenshots import main

if __name__ == "__main__":
    main()
