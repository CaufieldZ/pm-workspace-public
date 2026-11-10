"""PRD 自检扫描。

- md_scan: scan_prd_structural_md（md 文本输入，只查会把文档弄坏的硬错）
- patterns: 维度清单 prd_fail_keys / 共享正则 / 词集

check_prd_md.sh 与 scripts/hook_check_prd_content.py 直接调用 md_scan。
"""
from .md_scan import scan_prd_structural_md
from .patterns import (
    PRD_CHANGELOG_BODY_HISTORY,
    PRD_CHANGELOG_ITERATION_WORDS,
    PRD_CHANGELOG_LANE_HISTORY,
    PRD_CHANGELOG_PATTERNS,
    PRD_JARGON_REPLACEMENTS,
    PRD_KILL_BULLET_KEYWORDS,
    PRD_TRAILING_JUNK_PATTERNS,
    PRD_UI_STRIP_PATTERNS,
)

__all__ = [
    'scan_prd_structural_md',
    'PRD_CHANGELOG_PATTERNS',
    'PRD_CHANGELOG_BODY_HISTORY',
    'PRD_CHANGELOG_ITERATION_WORDS',
    'PRD_CHANGELOG_LANE_HISTORY',
    'PRD_JARGON_REPLACEMENTS',
    'PRD_KILL_BULLET_KEYWORDS',
    'PRD_TRAILING_JUNK_PATTERNS',
    'PRD_UI_STRIP_PATTERNS',
]
