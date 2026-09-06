"""PRD skill 底层职责模块（md 形态精简后）。

留下两类：
- md_renderer: md 字符串原语（h1/h2/table/list/image…），新 md 路径用
- images: 截图圆角 / DPI 修正，docx 时代遗留路径（v2 md 化后主路径走 screenshot_for_prd.py）

直接 import 子模块即可：
    from core.md_renderer import MdWriter, scene_block_card  # scene_5section_card 已 deprecated
    from core.images import fix_dpi, replace_cell_image, round_phone_corners
"""
