"""check_delta_conflict 回归：extract_targets / find_overlaps 纯函数契约。

锁定两件事：① 场景编号 + §9 支柱章（含表 data 行）都被抽到；② 两两重叠正确求交。
"""
from pathlib import Path

import pytest
from check_delta_conflict import _unique_shorts, extract_targets, find_overlaps


def test_unique_shorts_collision_disambiguated():
    # 跨季度同名版本目录（两个 2.1/）：短名会撞 → 加季度前缀区分，不折叠丢 delta
    ps = [
        Path("p/deliverables/2026Q3/2.1/prd-x-2.1.md"),
        Path("p/deliverables/2026Q2/2.1/prd-x-2.1.md"),
    ]
    names = _unique_shorts(ps)
    assert len(set(names.values())) == 2
    assert names[ps[0]] == "2026Q3/2.1"
    assert names[ps[1]] == "2026Q2/2.1"


def test_unique_shorts_no_collision_keeps_short():
    # 不撞时保持简洁短名，不加前缀
    ps = [
        Path("p/deliverables/2026Q3/2.1/prd-x-2.1.md"),
        Path("p/deliverables/2026Q3/2.2/prd-x-2.2.md"),
    ]
    assert set(_unique_shorts(ps).values()) == {"2.1", "2.2"}


def test_unique_shorts_same_dir_multifile_disambiguated():
    # 同一版本目录下多份 delta（主体 + 分端 + 埋点）：季度前缀救不了，须加文件名区分段
    ps = [
        Path("p/deliverables/2026Q3/2.3/prd-x-2.3.md"),
        Path("p/deliverables/2026Q3/2.3/prd-x-2.3-app.md"),
        Path("p/deliverables/2026Q3/2.3/prd-x-2.3-web.md"),
        Path("p/deliverables/2026Q3/2.3/prd-x-2.3-web-tracking.md"),
    ]
    names = _unique_shorts(ps)
    assert len(set(names.values())) == 4, "四份 delta 折叠成同一键会被静默丢弃"
    assert names[ps[0]] == "2026Q3/2.3#main"
    assert names[ps[3]] == "2026Q3/2.3#web-tracking"


def test_find_overlaps_skips_same_version_sibling_docs():
    # 同版本分端文档属同一 delta 包、一起反向合并，不是并行冲突
    targets = {
        "2.3#main": ({"B-1"}, {"状态机"}),
        "2.3#web": ({"B-1"}, {"状态机"}),
        "2.4": ({"B-1"}, set()),
    }
    pairs = {(a, b) for a, b, _ in find_overlaps(targets)}
    assert ("2.3#main", "2.3#web") not in pairs
    assert ("2.3#main", "2.4") in pairs and ("2.3#web", "2.4") in pairs


DELTA_A = """# Delta · 2.1.1
# 9. 反向合并指引（上线后执行）

| baseline 目标章 | 合并动作 |
| --- | --- |
| 开播与主播管理模块（A-2 / A-3） | 默认开始时间改为当前 + 5 分钟 |
| 直播间模块（B-6 直播中实时管理） | 放开画面源 |
| 埋点契约章 | 并入 §7 消息事件 |
"""

DELTA_B = """# Delta · 2.2
**反向合并目标**：baseline 直播间模块「B-6 实时管理」+ 埋点契约章
连麦入口（反向合并目标：B-1 直播间全貌）
正文随口提一句 D-9 但不在合并语境，应不收支柱
"""


def test_extract_scene_ids():
    scenes, _ = extract_targets(DELTA_A)
    assert scenes == {"A-2", "A-3", "B-6"}


def test_extract_pillar_in_section_table_row():
    # §9 章内表 data 行的「埋点契约」即便不含「反向合并」字样也要抓到
    _, pillars = extract_targets(DELTA_A)
    assert "埋点契约" in pillars


def test_extract_pillar_inline_context():
    # 行内「反向合并目标」语境里的支柱章命中
    _, pillars = extract_targets(DELTA_B)
    assert "埋点契约" in pillars


def test_find_overlaps_intersect():
    targets = {
        "2.1.1": extract_targets(DELTA_A),
        "2.2": extract_targets(DELTA_B),
    }
    overlaps = find_overlaps(targets)
    assert len(overlaps) == 1
    a, b, shared = overlaps[0]
    assert (a, b) == ("2.1.1", "2.2")
    assert "B-6" in shared and "埋点契约" in shared


def test_find_overlaps_none_when_disjoint():
    targets = {
        "x": ({"A-1"}, set()),
        "y": ({"Z-9"}, {"术语"}),
    }
    assert find_overlaps(targets) == []


@pytest.mark.parametrize("text", ["", "无任何编号的纯文本", "# 标题\n正文"])
def test_extract_targets_empty(text):
    scenes, pillars = extract_targets(text)
    assert scenes == set() and pillars == set()
