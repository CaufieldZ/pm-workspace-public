"""pytest 共享夹具：注入 sys.path 让 lib.* 与根脚本可 import。

被测代码布局：
  scripts/lib/*.py    → from lib.scene_match import ...
  scripts/*.py        → import check_cjk_punct（根脚本带 __main__ guard）
conftest 把 repo/scripts 加进 sys.path[0]，两种 import 都成立。
"""
import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parents[2] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
