"""check_baseline_fresh 回归：parse_changelog / parse_module_freshness / parse_delta_pillar_entities。

防 6814a2c 类静默漏判——delta 收集 glob 漏递归曾让 community/livestream 整线假绿。
这里锁定三个纯解析函数的契约，漂移即报。
"""
from datetime import date
from pathlib import Path

from check_baseline_fresh import (
    delta_in_flight,
    delta_is_live,
    parse_changelog,
    parse_delta_pillar_entities,
    parse_module_freshness,
)

CHANGELOG = """# 变更记录

| 日期 | 模块 | delta PRD | 状态 |
|------|------|-----------|------|
| 2026-06 | 连麦 | delta-prd-ll-v1.md | 已上线 |
| 2026-05 | 社区 | delta-prd-community-v2.md | 待合并 |
"""


def test_parse_changelog():
    # key 是从 delta 列抠出的 prd-xxx.md（_DELTA_FILE），不是 delta-prd- 前缀
    assert parse_changelog(CHANGELOG) == {
        "prd-ll-v1.md": "已上线",
        "prd-community-v2.md": "待合并",
    }


def test_parse_changelog_only_within_section():
    # 变更记录章之外的表格行不收（防误收概述章里的表格）
    text = """# 概述
| 2026-06 | 连麦 | prd-x.md | 已上线 |

# 变更记录
| 2026-06 | 连麦 | prd-y.md | 待合并 |
"""
    assert parse_changelog(text) == {"prd-y.md": "待合并"}


def test_parse_changelog_same_name_conflict_not_swallowed():
    # 同文件名多行且状态不一致：不静默覆盖（否则「已合并」掩盖「已登记」→ stale 漏报），标冲突态
    text = """# 变更记录
| 2026-04 | A | prd-x-2.1.md | 已合并 |
| 2026-07 | B | prd-x-2.1.md | 已登记 |
"""
    status = parse_changelog(text)["prd-x-2.1.md"]
    assert status != "已合并"
    assert status.startswith("状态冲突")


def test_parse_changelog_same_name_same_status_idempotent():
    # 同名同状态：不误标冲突
    text = """# 变更记录
| 2026-04 | A | prd-x-2.1.md | 已合并 |
| 2026-07 | B | prd-x-2.1.md | 已合并 |
"""
    assert parse_changelog(text) == {"prd-x-2.1.md": "已合并"}


MODULES = """# 1. 连麦模块
最后核对线上：2026-06-01

# 2. 社区模块
状态：未上线

# 3. 红人模块
"""


def test_parse_module_freshness():
    result = parse_module_freshness(MODULES)
    by_title = {t: (d, raw) for t, d, raw in result}
    # 连麦模块有核对日期
    assert by_title["连麦模块"] == (date(2026, 6, 1), "2026-06-01")
    # 社区模块标「未上线」→ 跳过（不该核对线上）
    assert "社区模块" not in by_title
    # 红人模块无核对日期 → None 占位（防静默漏报）
    assert by_title["红人模块"] == (None, "")


DELTA = """# 3. 业务对象增量
## 3.1 订阅关系（社区只读）
## 3.2 打赏记录

# 4. 状态机增量
## 4.1 订阅状态机

# 5. 全局规则增量
- 自由 bullet（不收）
"""


def test_parse_delta_pillar_entities():
    result = parse_delta_pillar_entities(DELTA)
    assert result["业务对象"] == ["订阅关系", "打赏记录"]
    assert result["状态机"] == ["订阅状态机"]


def test_delta_is_live():
    assert delta_is_live("状态：已上线") is True
    assert delta_is_live("**状态**：已上线（2026-07-XX）") is True
    assert delta_is_live("状态：待合并") is False
    assert delta_is_live("无状态行") is False


def test_delta_in_flight_excludes_merged_and_archived():
    # 第四层作用域：已合并 / 已归档的历史 delta 不该再被要求补火效链接
    archive = Path("p/deliverables/archive")
    merged = Path("p/deliverables/2026Q3/2.2/prd-x-2.2.md")
    archived = Path("p/deliverables/archive/2026Q3/2.2/prd-x-2.2-tracking.md")
    live = Path("p/deliverables/2026Q3/2.4/prd-x-2.4.md")
    changelog = {"prd-x-2.2.md": "已合并"}

    assert not delta_in_flight(merged, changelog, archive), "changelog 标已合并 → 不在途"
    assert not delta_in_flight(archived, changelog, archive), "落 archive/ → 不在途"
    assert delta_in_flight(live, changelog, archive)


def test_delta_in_flight_keeps_registered_but_unmerged():
    # changelog 有行但状态未推进到「已合并」→ 仍在途，火效链接照样该补
    archive = Path("p/deliverables/archive")
    dp = Path("p/deliverables/2026Q3/2.3/prd-x-2.3.md")
    assert delta_in_flight(dp, {"prd-x-2.3.md": "待合并"}, archive)
