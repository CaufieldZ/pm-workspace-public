"""check_proto_repro 回归：产线发现 + 字节比对契约。

锁定两件事：① 只把有共享场景库（scripts/src/registry.py）的产线纳入、archive 排除；
② 比对是逐字节的，一行不同就得报出来 —— 检查器不能恒绿（空绿灯比没有检查更危险）。
"""
import importlib.util
import sys
from pathlib import Path

import pytest

_MOD = (Path(__file__).resolve().parents[2]
        / ".claude/skills/prototype/scripts/check_proto_repro.py")
_spec = importlib.util.spec_from_file_location("check_proto_repro", _MOD)
check_proto_repro = importlib.util.module_from_spec(_spec)
sys.modules["check_proto_repro"] = check_proto_repro
_spec.loader.exec_module(check_proto_repro)

compare = check_proto_repro.compare
find_shared_lib_projects = check_proto_repro.find_shared_lib_projects


def _mk(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_find_shared_lib_projects_picks_registry_owners(tmp_path):
    _mk(tmp_path / "projects/livestream/scripts/src/registry.py", "SCENES = {}")
    _mk(tmp_path / "projects/community/scene-list.md", "x")          # 无共享库 → 不收
    found = find_shared_lib_projects(tmp_path)
    assert [p.name for p in found] == ["livestream"]


def test_find_shared_lib_projects_excludes_archive(tmp_path):
    _mk(tmp_path / "projects/x/archive/2026Q2/scripts/src/registry.py", "SCENES = {}")
    assert find_shared_lib_projects(tmp_path) == []


def test_compare_flags_single_line_drift(tmp_path):
    proj, tmp = tmp_path / "proj", tmp_path / "tmp"
    rel = "deliverables/2026Q3/2.4/proto-x-2.4-app.html"
    _mk(proj / rel, "<html>\n<body>A</body>\n</html>\n")
    _mk(tmp / rel, "<html>\n<body>B</body>\n</html>\n")
    drift, same, exempt = compare(tmp, proj)
    assert same == [] and exempt == []
    assert len(drift) == 1 and "差 1 行" in drift[0]


def test_compare_green_when_identical(tmp_path):
    proj, tmp = tmp_path / "proj", tmp_path / "tmp"
    rel = "deliverables/2026Q3/2.4/proto-x-2.4-app.html"
    body = "<html>\n<body>A</body>\n</html>\n"
    _mk(proj / rel, body)
    _mk(tmp / rel, body)
    drift, same, exempt = compare(tmp, proj)
    assert drift == [] and exempt == [] and same == ["proto-x-2.4-app.html"]


def test_compare_flags_built_but_undelivered(tmp_path):
    # 重建出来了但 deliverables/ 下没有 → 漏提交，不能算一致
    proj, tmp = tmp_path / "proj", tmp_path / "tmp"
    _mk(tmp / "deliverables/2026Q3/2.6/proto-x-2.6-app.html", "<html></html>\n")
    proj.mkdir(parents=True, exist_ok=True)
    drift, same, exempt = compare(tmp, proj)
    assert same == [] and exempt == [] and len(drift) == 1 and "漏提交" in drift[0]


@pytest.mark.parametrize("extra", [1, 5])
def test_compare_counts_length_difference(tmp_path, extra):
    proj, tmp = tmp_path / "proj", tmp_path / "tmp"
    rel = "deliverables/2026Q3/2.4/proto-x-2.4-web.html"
    _mk(proj / rel, "L\n" * 10)
    _mk(tmp / rel, "L\n" * (10 + extra))
    drift, _, _ = compare(tmp, proj)
    assert f"差 {extra} 行" in drift[0]


def test_compare_skips_frozen_version(tmp_path):
    # 封版版本（.proto-lock.json frozen=true）：内容不一致也不算漂移，进豁免清单
    proj, tmp = tmp_path / "proj", tmp_path / "tmp"
    rel = "deliverables/2026Q3/2.3/proto-x-2.3-app.html"
    _mk(proj / rel, "<html>A</html>\n")
    _mk(tmp / rel, "<html>B</html>\n")
    _mk(proj / "deliverables/2026Q3/2.3/.proto-lock.json",
        '{"version": "2.3", "frozen": true, "inputs": {}}')
    drift, same, exempt = compare(tmp, proj)
    assert drift == [] and same == [] and exempt == ["2.3"]
