"""HTML 产出物基础结构检查 - FILL 占位 / HTML 闭合 / 字体 CJK 优先顺序。

跨脚本共享，迁移自：
- scripts/check_html.sh:25-44, :29-35（FILL / 闭合 / 字体）
- scripts/audit-fast.sh:106-125（FILL / 字体）

规则源：
- CLAUDE.md §修改入口防误操「已脚本化产出物只改源」
- .claude/runbooks/html-pipeline.md「fill 视觉铁律」
- _shared/claude-design/tokens.css「字体栈 CJK 优先 SSOT」
"""
from __future__ import annotations

import re

FILL_MARKERS = ('FILL_START:', 'FILL_END:', '待填充')


def check_fill_placeholders(text: str) -> list[tuple[str, int]]:
    """返回 [(marker, count), ...]，count > 0 即占位残留。"""
    hits: list[tuple[str, int]] = []
    for kw in FILL_MARKERS:
        n = text.count(kw)
        if n > 0:
            hits.append((kw, n))
    return hits


def check_html_closed(text: str) -> bool:
    """`</html>` 出现即认为闭合。"""
    return '</html>' in text


# CJK 优先违例：英文字体在 Noto Sans/Serif SC / system-ui 之前
# 命中即视为违反 CJK 优先（fallback 应放后面）
# 字体名兼容单引号 / 双引号 / 裸字
_Q = r"['\"]?"
_FONT_PRIORITY_BAD = [
    (re.compile(rf"font-family\s*:[^;{{}}]*{_Q}DM Sans{_Q}[^;{{}}]*{_Q}Noto Sans SC{_Q}"),
     "DM Sans 在 Noto Sans SC 前面"),
    (re.compile(rf"font-family\s*:[^;{{}}]*{_Q}Inter{_Q}[^;{{}}]*{_Q}Noto Sans SC{_Q}"),
     "Inter 在 Noto Sans SC 前面"),
    (re.compile(rf"font-family\s*:[^;{{}}]*{_Q}Source Serif 4{_Q}[^;{{}}]*{_Q}Noto Serif SC{_Q}"),
     "Source Serif 4 在 Noto Serif SC 前面"),
    (re.compile(rf"font-family\s*:[^;{{}}]*-apple-system[^;{{}}]*{_Q}Noto Sans SC{_Q}"),
     "-apple-system 在 Noto Sans SC 前面"),
    (re.compile(rf"font-family\s*:[^;{{}}]*{_Q}Plus Jakarta Sans{_Q}[^;{{}}]*{_Q}Noto Sans SC{_Q}"),
     "Plus Jakarta Sans 在 Noto Sans SC 前面"),
    (re.compile(rf"font-family\s*:[^;{{}}]*{_Q}Poppins{_Q}[^;{{}}]*{_Q}Noto Sans SC{_Q}"),
     "Poppins 在 Noto Sans SC 前面"),
]


def check_font_cjk_priority(text: str) -> list[str]:
    """返回违反 CJK 优先规则的描述清单（空 = 全过）。"""
    bad = []
    for pat, desc in _FONT_PRIORITY_BAD:
        if pat.search(text):
            bad.append(desc)
    return bad


def check_line_count(text: str, min_lines: int = 500) -> tuple[int, bool]:
    """返回 (行数, 是否合规)。"""
    n = text.count('\n') + 1
    return n, n >= min_lines
