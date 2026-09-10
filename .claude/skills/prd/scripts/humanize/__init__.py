"""PRD 讲人话扫描两件套。

- md_scan: scan_human_voice_md / scan_prd_structural_md（md 文本输入，AST 行扫）
- patterns: 共享正则 / 替换规则 / 词集

讲人话共性铁律见 .claude/runbooks/human-voice-rules.md，PRD 形态规则见
references/prd-chapter-rules.md §三 / §三点八。check_prd_md.sh 直接调用 md_scan。
"""
from .md_scan import scan_human_voice_md, scan_prd_structural_md
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
    'scan_human_voice_md',
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
