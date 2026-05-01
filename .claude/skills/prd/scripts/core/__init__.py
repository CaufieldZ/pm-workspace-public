"""PRD skill 底层职责模块 —— 给 gen_prd_base / update_prd_base / sections 共用，
也给 ops-handbook 等下游 skill 直接 import 复用美学栈。

直接 import 子模块即可：
    from core.styles import C, FONT, para_run, cell_text
    from core.headings import h1, h2, h3, chapter_story
    from core.tables import scene_table, fill_cell_blocks, set_cell_blocks
    from core.images import fix_dpi, replace_cell_image
    from core.normalize import normalize_punctuation, normalize_fonts, ensure_theme
    from core.patch import insert_paragraph_before, insert_scene_blocks, replace_para_text

或通过聚合入口（向后兼容）：
    from gen_prd_base import *      # 所有 core/* + sections + document API
    from update_prd_base import *   # core/patch + core/normalize + humanize + screenshots
"""
