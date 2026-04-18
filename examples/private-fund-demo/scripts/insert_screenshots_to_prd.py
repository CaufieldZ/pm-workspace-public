"""将截图插入 PRD docx 左列，修正 DPI 防模糊"""
import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/prd/references'))
from update_prd_base import *
from docx import Document
from docx.shared import Cm

DOCX = os.path.join(os.path.dirname(__file__), '../deliverables/prd-private-fund-v1.docx')
SHOTS_DIR = os.path.join(os.path.dirname(__file__), '../screenshots/prd')

# scene_id -> (screenshot filename, width_cm)
# phone 截图 5cm，web 截图 7cm
SCENE_SHOTS = [
    ("A-1", "a1.png", 5.0),
    ("A-2", "a2.png", 5.0),
    ("B-1", "b1.png", 5.0),
    ("B-2", "b2.png", 5.0),
    ("C-1", "c1.png", 7.0),
]

doc = Document(DOCX)

# fix DPI for all screenshots
for _, fname, _ in SCENE_SHOTS:
    path = os.path.join(SHOTS_DIR, fname)
    fix_dpi(path)
    print(f"  DPI fixed: {fname}")

# 找到 scene 对应的两列表格并插入截图
# scene_table 每个场景生成一张表，左列第一行 cell[0] 放截图
scene_idx = {sid: i for i, (sid, _, _) in enumerate(SCENE_SHOTS)}

# 遍历 doc tables，找包含场景标题的表格
inserted = set()
for table in doc.tables:
    if not table.rows:
        continue
    cell0 = table.rows[0].cells[0]
    text = cell0.text.strip()
    for scene_id, fname, width_cm in SCENE_SHOTS:
        if scene_id in text and scene_id not in inserted:
            img_path = os.path.join(SHOTS_DIR, fname)
            replace_cell_image(cell0, img_path, width_cm=width_cm)
            print(f"  inserted: {scene_id} ← {fname}")
            inserted.add(scene_id)
            break

doc.save(DOCX)
print(f"\nAll done. Inserted {len(inserted)}/5 screenshots → {DOCX}")
