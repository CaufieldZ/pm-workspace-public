#!/usr/bin/env python3
"""聚合入口（向后兼容壳）—— Layer 2 重构后退化为 re-export，所有 API 实现在
core/* + humanize/ + screenshots.py。

老脚本零改动继续跑：
    from update_prd_base import *
    # 拿到 normalize_* / insert_* / replace_* / set_cell_* / humanize_* / 等

核心位置：
- core.normalize → normalize_punctuation / normalize_fonts / ensure_theme
- core.headings  → insert_heading_before / normalize_headings
- core.tables    → set_cell_text / set_cell_blocks / cell_paragraphs_to_blocks /
                   fix_scene_cell_numbering
- core.images    → fix_dpi / replace_cell_image / replace_cell_image_keep_title
- core.patch     → insert_paragraph_before / insert_description_after /
                   insert_scene_blocks / remove_table / replace_para_text /
                   search_replace_para
- humanize       → humanize_doc / humanize_prd_voice + PRD_*_PATTERNS / CIRCLE_NUMS
- screenshots    → assert_screenshots_fresh

下游脚本可直接 import 子模块（推荐）：
    from core.patch import insert_scene_blocks
    from core.images import replace_cell_image
    from humanize import humanize_prd_voice
"""
# 保留原 docx / 标准库 import 兼容 from update_prd_base import *
from docx.shared import Cm, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re

# ── re-export 实现（全部来自拆分后的 core/ + humanize/ + screenshots/）──
from core.normalize import (
    normalize_punctuation, normalize_fonts, ensure_theme,
)
from core.headings import (
    insert_heading_before, normalize_headings,
)
from core.tables import (
    set_cell_text, set_cell_blocks,
    cell_paragraphs_to_blocks, fix_scene_cell_numbering,
)
from core.images import (
    fix_dpi, replace_cell_image, replace_cell_image_keep_title,
)
from core.patch import (
    insert_paragraph_before, insert_description_after,
    insert_scene_blocks, remove_table,
    replace_para_text, search_replace_para,
)
from humanize import (
    humanize_doc, humanize_prd_voice,
    CIRCLE_NUMS,
    PRD_CHANGELOG_PATTERNS, PRD_JARGON_REPLACEMENTS,
    PRD_KILL_BULLET_KEYWORDS, PRD_TRAILING_JUNK_PATTERNS,
    PRD_UI_STRIP_PATTERNS,
)
from screenshots import (
    assert_screenshots_fresh,
)
