"""changelog_residue 回归：5 类「描述当前态」修订痕迹 PATTERN + heading 旁路。

防类 2 静默漏判：这些 PATTERN 是真相源静态章 lint 的核心，漂移会让带修订痕迹的
baseline 假绿通过。
"""
import pytest
from lib.changelog_residue import scan_residue


@pytest.mark.parametrize("text,cat", [
    # revision：修订痕迹 / 日期标注 / 变更词
    ("（2024-01-15 修订）", "revision"),
    ("(from v1)", "revision"),
    ("（变更：字段调整）", "revision"),
    ("反转说明：", "revision"),
    ("砍掉：", "revision"),
    # version_tag：版本号 + 动作词流水账
    ("（V1.0 变更：重构）", "version_tag"),
    ("V2.0 新增 连麦", "version_tag"),
    # decision_ref：决策号引用
    ("决策 #1", "decision_ref"),
    ("决策 1 · v2.0", "decision_ref"),
    ("反转决策 3", "decision_ref"),
    # migration：from-to 迁移叙事
    ("由旧方案替代", "migration"),
    ("改为新逻辑", "migration"),
    ("不再使用旧字段", "migration"),
    ("从旧版迁移到新版", "migration"),
])
def test_hit(text, cat):
    cats = {c for c, _ in scan_residue(text)}
    assert cat in cats, f"期望命中 {cat}，实际命中 {cats}"


def test_zombie_only_in_heading():
    # zombie_heading（已废弃 / 砍掉）仅 is_heading=True 触发
    assert scan_residue("## 已废弃字段", is_heading=False) == []
    hits = scan_residue("## 已废弃字段", is_heading=True)
    assert any(c == "zombie_heading" for c, _ in hits)


def test_clean_text_no_hit():
    # 纯当前态描述，无任何修订痕迹
    assert scan_residue("这是正常的业务描述，描述当前态。") == []


def test_returns_match_string():
    # 返回结构含命中原文（调用方按需展示）
    hits = scan_residue("决策 #1")
    assert hits == [("decision_ref", "决策 #1")]
