"""check_fork_drift 回归：漂移方向判定的纯函数契约。

锁定：① 内容相同短路（不看时间）；② content_age 取 min 抗「首次入库日」失真；
③ 缺文件报登记表不符而非静默跳过。
"""
import os

import pytest
from check_fork_drift import FORK_GROUPS, compare, content_age, fs_mtime


def _write(path, text, mtime=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))


def test_same_content_short_circuits(tmp_path):
    _write(tmp_path / "src.py", "x = 1", mtime=1000)
    _write(tmp_path / "copy.py", "x = 1", mtime=9000)   # 时间差很大，但内容相同
    assert compare(tmp_path, "src.py", "copy.py")["status"] == "same"


def test_src_ahead_flags_backport_candidate(tmp_path):
    _write(tmp_path / "src.py", "x = 2", mtime=2_000_000_000)
    _write(tmp_path / "copy.py", "x = 1", mtime=1_000_000_000)
    r = compare(tmp_path, "src.py", "copy.py")
    assert r["status"] == "src-ahead"
    assert r["src_date"] > r["copy_date"]


def test_copy_ahead_is_separate_bucket(tmp_path):
    _write(tmp_path / "src.py", "x = 1", mtime=1_000_000_000)
    _write(tmp_path / "copy.py", "x = 2", mtime=2_000_000_000)
    assert compare(tmp_path, "src.py", "copy.py")["status"] == "copy-ahead"


@pytest.mark.parametrize("missing,expected", [("src.py", "src-missing"), ("copy.py", "copy-missing")])
def test_missing_file_reports_registry_mismatch(tmp_path, missing, expected):
    for name in ("src.py", "copy.py"):
        if name != missing:
            _write(tmp_path / name, "x = 1")
    assert compare(tmp_path, "src.py", "copy.py")["status"] == expected


def test_content_age_takes_min_of_signals(tmp_path):
    # 非 git 仓库 → git_mtime 返回 None，降级纯 mtime；min 逻辑仍成立
    p = tmp_path / "a.py"
    _write(p, "x", mtime=1_000_000_000)
    assert content_age(tmp_path, "a.py") == fs_mtime(p)


def test_registry_paths_are_relative_and_nonempty():
    # 登记表写绝对路径会在别的 clone 里失效
    for name, (src, copies) in FORK_GROUPS.items():
        assert not src.startswith("/"), name
        assert copies, f"{name} 无副本，不该登记"
        for c in copies:
            assert not c.startswith("/"), f"{name}:{c}"
            assert c != src, f"{name} 副本与源头同路径"
