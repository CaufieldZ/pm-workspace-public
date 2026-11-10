"""delta 骨架回归：三种档位生成的骨架必须过自己的自检。

骨架（sections_md_baseline.build_delta_skeleton）和检查器（humanize）是两处独立代码：
埋点表头、引用块、mermaid 等任何一边改了，新骨架一生成就过不了 check_prd_md，
这里把两边锁在一起。
"""
import sys
from pathlib import Path

import pytest

_PRD_SCRIPTS = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "prd" / "scripts"
sys.path.insert(0, str(_PRD_SCRIPTS))

import gen_prd_skeleton as g  # noqa: E402
from humanize.md_scan import TRACKING_HEADER, scan_prd_structural_md  # noqa: E402
from humanize.patterns import prd_fail_keys  # noqa: E402
from sections_md_baseline import build_delta_skeleton  # noqa: E402

_INFO = {
    "project_name": "demo",
    "version": "1.0",
    "author": "pm",
    "baseline": "b",
    "scenes": [{"id": "A-1", "name": "发帖", "view": "前台", "module": "社区",
                "priority": "P0", "note": ""}],
}


@pytest.mark.parametrize("tier", ["patch", "feature", "bundle"])
def test_delta_skeleton_passes_own_checks(tier):
    md = build_delta_skeleton({**_INFO, "tier": tier})
    hits = scan_prd_structural_md(md)
    fired = {k: hits[k] for k, _ in prd_fail_keys(skeleton=True, profile="delta") if hits.get(k)}
    assert fired == {}, fired


def test_delta_skeleton_tracking_header_is_fixed():
    md = build_delta_skeleton({**_INFO, "tier": "feature"})
    expected = "| " + " | ".join(TRACKING_HEADER) + " |"
    assert expected in md


def test_precheck_only_blocks_half_width_paren():
    assert g.precheck_scene_list([{"id": "C-4", "name": "晒单卡（与 C-3 同款）"}]) == []
    assert g.precheck_scene_list([{"id": "C-4", "name": "晒单卡(新)"}])
