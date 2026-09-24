"""把 screenshots/prd/*.png 插入 PRD docx 的 scene 表格。

通用脚本 .claude/skills/prd/scripts/screenshots.py 的 --project 参数硬编码到 projects/ 下，
本 demo 在 examples/ 下，所以单独包一个调用 insert_into_docx() 的 thin wrapper。
"""
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
_ROOT = _DIR.parents[2]
sys.path.insert(0, str(_ROOT / ".claude/skills/prd/scripts"))

from screenshots import insert_into_docx  # noqa: E402

PROJ = _DIR.parent
DOCX = PROJ / "deliverables/prd-private-fund-v1.docx"
SHOT_DIR = PROJ / "screenshots/prd"

def _stem_to_scene_id(stem: str) -> str:
    """a1 → A-1，c1 → C-1（截图文件名省略连字符，PRD 表格用 A-1 形式）。"""
    return f"{stem[0].upper()}-{stem[1:]}"


shots = {_stem_to_scene_id(p.stem): p for p in sorted(SHOT_DIR.glob("*.png"))}
print(f"加载截图 {len(shots)} 张")
inserted = insert_into_docx(DOCX, shots)
print(f"插入 {len(inserted)}/{len(shots)} 个场景")
