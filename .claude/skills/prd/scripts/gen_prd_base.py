#!/usr/bin/env python3
"""聚合入口（向后兼容壳）—— Layer 2 重构后退化为 re-export，所有 API 实现在
core/* + sections.py + document.py + humanize/。

老脚本零改动继续跑：
    from gen_prd_base import *
    # 拿到 C / FONT / para_run / h1/h2/h3 / scene_table / make_table / save_prd / 等

核心位置：
- core.styles    → C / FONT / para_run / para_run_md / cell_text / set_cell_bg / set_cell_border
- core.headings  → h1/h2/h3 / chapter_story / pullquote / metric_run / add_p / bullet
- core.tables    → make_table / scene_table / fill_cell_blocks
- document       → init_doc / cover_page / get_author / save_prd

下游脚本可直接 import 子模块（推荐）：
    from core.styles import C, para_run
    from core.headings import h1, h2
    from document import save_prd
"""
# ── 保留原 gen_prd_base.py 的全部 docx / 标准库 import，让 from gen_prd_base import *
#    继续拿到 Document / Pt / Cm / qn 等 docx 类型 + json/os/pathlib/re 标准库 ──
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json, os, pathlib, re  # noqa: F401

# ── re-export 实现（全部来自拆分后的 core/ + document） ───────────────────
from core.styles import (
    C, FONT,
    set_cell_bg, set_cell_border,
    para_run, para_run_md,
    cell_text,
)
from core.headings import (
    add_p, bullet,
    h1, h2, h3,
    chapter_story, pullquote, metric_run,
)
from core.tables import (
    make_table, scene_table, fill_cell_blocks,
)
from document import (
    init_doc, cover_page, get_author, save_prd,
)
