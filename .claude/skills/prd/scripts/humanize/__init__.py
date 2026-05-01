"""PRD 讲人话三合一：扫描（scan）+ 自动修复（fix）+ CLI。

PRD docx 是产品 / 业务 / 项目经理读的文档，必须讲人话。三类违规：

1. **流水账 / 版本痕迹（FAIL 阻断）**：(YYYY-MM-DD) / (from vN) / (变更) / (新增) /
   反转说明：/ 砍掉： —— PRD 描述当前状态，不写讨论流水。
2. **代码字段 snake_case（WARN）**：card_type / is_same_symbol / xxx_id / has_xxx ——
   PRD 给 PM 读，正文应改白话。**例外（豁免）**：表头含「ID/字段/事件/参数/枚举/指标/
   触发/层级/路由」的字段表，或 H2 标题含「枚举值/字段/埋点/事件/参数/对照/归因」的章节。
3. **CSS 实现细节（WARN）**：rgba/hex/px/font-size —— PRD 描述 What 不描述 How。

bspec / pspec / test-cases 不受此约束（研发/QA/设计师消费，允许字段名 + 像素 + 编号）。

使用：

    # 修复（gen / update 时）
    from humanize import humanize_prd_voice, humanize_doc
    humanize_prd_voice(doc, extra_jargon=PROJECT_JARGON)

    # 扫描（check_prd.sh / push gate 共享调用）
    from humanize import scan_human_voice, report_violations
    result = scan_human_voice(doc)
    fail = report_violations(result)

    # CLI
    python3 -m humanize <docx>
    # exit 1 if date_tag_hits non-empty (FAIL)，else 0（WARN 不阻断）

包结构：
- patterns: 所有 regex / 常量
- scan: scan_human_voice（read 端）
- report: report_violations（CLI 报告）
- scene_codes: humanize_doc / _humanize_text（PM 内部场景编号清理）
- fix: humanize_prd_voice（write 端，gen / update 时调用）
"""
from .patterns import (
    CIRCLE_NUMS,
    PRD_CHANGELOG_PATTERNS,
    PRD_CHANGELOG_BODY_HISTORY,
    PRD_CHANGELOG_ITERATION_WORDS,
    PRD_CHANGELOG_LANE_HISTORY,
    PRD_JARGON_REPLACEMENTS,
    PRD_KILL_BULLET_KEYWORDS,
    PRD_TRAILING_JUNK_PATTERNS,
    PRD_UI_STRIP_PATTERNS,
)
from .scan import scan_human_voice
from .structural import scan_prd_structural, report_structural_violations
from .report import report_violations
from .scene_codes import humanize_doc
from .fix import humanize_prd_voice

__all__ = [
    'scan_human_voice',
    'scan_prd_structural',
    'report_violations',
    'report_structural_violations',
    'humanize_doc',
    'humanize_prd_voice',
    'CIRCLE_NUMS',
    'PRD_CHANGELOG_PATTERNS',
    'PRD_CHANGELOG_BODY_HISTORY',
    'PRD_CHANGELOG_ITERATION_WORDS',
    'PRD_CHANGELOG_LANE_HISTORY',
    'PRD_JARGON_REPLACEMENTS',
    'PRD_KILL_BULLET_KEYWORDS',
    'PRD_TRAILING_JUNK_PATTERNS',
    'PRD_UI_STRIP_PATTERNS',
]
