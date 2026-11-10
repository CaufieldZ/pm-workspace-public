"""pytest 共享夹具：注入 sys.path 让 lib.* 与根脚本可 import。

被测代码布局：
  scripts/lib/*.py    → from lib.scene_match import ...
  scripts/*.py        → import check_cjk_punct（根脚本带 __main__ guard）
conftest 把 repo/scripts 加进 sys.path[0]，两种 import 都成立。
"""
import sys
from pathlib import Path

import pytest

_SCRIPTS = str(Path(__file__).resolve().parents[2] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


@pytest.fixture(autouse=True)
def _drop_inherited_git_env(monkeypatch):
    """清掉从父进程继承的 GIT_* 变量。

    pre-commit 钩子里 git 会导出 GIT_DIR / GIT_WORK_TREE 等；测试内建临时仓库时
    这些变量会把 `git commit` 指回外层工作区，临时提交失败、用例误红。
    """
    for var in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
    ):
        monkeypatch.delenv(var, raising=False)
