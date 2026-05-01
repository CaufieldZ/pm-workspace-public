#!/usr/bin/env python3
"""命令行 alias —— Layer 2 重构后实现搬到 confluence_push.py。

老命令仍然可用（保持 .confluence.json 配置 + pre-wiki-push-gate hook 命中）：
    python3 .claude/skills/prd/scripts/push_to_confluence_base.py <docx>

新脚本可直接调 confluence_push.py（推荐）：
    python3 .claude/skills/prd/scripts/confluence_push.py <docx>
"""
from confluence_push import main

if __name__ == "__main__":
    main()
