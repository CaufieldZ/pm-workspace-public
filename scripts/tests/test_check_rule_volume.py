"""check_rule_volume 回归：四条红灯各自可命中，棘轮不误报。

锁定：① 超上限 / 文件不存在 / 上限非法 / 未登记 四类都有正例点亮；
② 恰好等于上限不算超（护栏是「不得超过」不是「必须留余量」）；
③ tokens = bytes/2 的 audit §5.1 口径。
"""
import pytest
from check_rule_volume import check_budgets, has_red, tokens_of


@pytest.mark.parametrize("nbytes,expected", [(0, 0), (1, 0), (2, 1), (9999, 4999)])
def test_tokens_is_half_bytes(nbytes, expected):
    assert tokens_of(nbytes) == expected


def run(budgets, sizes, present=frozenset()):
    return check_budgets(budgets, sizes, set(present))


# ─── 红灯一：超上限 ───

def test_over_ceiling_flagged():
    r = run({"a.md": 100}, {"a.md": 300})       # 300 bytes → 150t > 100
    assert r["over"] == [("a.md", 150, 100)]
    assert has_red(r)


def test_exactly_at_ceiling_is_ok():
    r = run({"a.md": 150}, {"a.md": 300})
    assert r["over"] == [] and not has_red(r)


# ─── 红灯二：登记了但文件没了 ───

def test_missing_budgeted_file_flagged():
    r = run({"gone.md": 100}, {"gone.md": None})
    assert r["missing"] == ["gone.md"]
    assert has_red(r)
    assert r["rows"] == []          # 不存在的文件不进报表


# ─── 红灯三：上限值非法 ───

@pytest.mark.parametrize("bad", [0, -5, "1000", 1.5, None, True])
def test_invalid_ceiling_flagged(bad):
    r = run({"a.md": bad}, {"a.md": 100})
    assert [p for p, _ in r["invalid"]] == ["a.md"]
    assert has_red(r)


# ─── 红灯四：未登记（预算面被绕开）───

def test_unregistered_runbook_flagged():
    r = run({"a.md": 100}, {"a.md": 100},
            present={"a.md", ".claude/runbooks/newcomer.md"})
    assert r["unregistered"] == [".claude/runbooks/newcomer.md"]
    assert has_red(r)


def test_all_registered_is_clean():
    budgets = {"a.md": 100, ".claude/runbooks/b.md": 100}
    r = run(budgets, {"a.md": 100, ".claude/runbooks/b.md": 100},
            present={".claude/runbooks/b.md"})
    assert not has_red(r)
    assert len(r["rows"]) == 2
