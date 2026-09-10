"""check_code_review_gate 谓词回归：infra / total 两维度边界 + 范围排除。

锁三件事：① infra 下限 30 与总 churn 下限 300 的边界行为（阈值调整时这里先红，
提醒同步 thresholds.yaml 的标定注释）；② hub/ 与非代码文件不进谓词（越界 =
误拦不属于 code-review skill 的提交）；③ numstat 异常行（`-` 占位）不炸不计数。
"""
import importlib.util
import sys
from pathlib import Path

import pytest

_MOD = Path(__file__).resolve().parents[2] / "scripts/check_code_review_gate.py"
_spec = importlib.util.spec_from_file_location("check_code_review_gate", _MOD)
gate = importlib.util.module_from_spec(_spec)
sys.modules["check_code_review_gate"] = gate
_spec.loader.exec_module(gate)

is_significant = gate.is_significant
INFRA, TOTAL = gate.INFRA_LINES, gate.TOTAL_LINES  # 边界用例跟随 yaml，改阈值不用改测试


# ── infra 桶 ──────────────────────────────────────────────

@pytest.mark.parametrize("path", [
    "scripts/lib/repo.py",
    ".claude/hooks/lib/post-checks.sh",
    ".claude/hooks/pre-writeedit-guard.sh",
    ".githooks/pre-commit",
])
def test_infra_at_threshold_triggers(path):
    hit, reasons = is_significant([(str(INFRA), "0", path)])
    assert hit and any("infra" in r for r in reasons)


def test_infra_below_threshold_not_triggered():
    assert is_significant([(str(INFRA - 1), "0", "scripts/lib/repo.py")])[0] is False


def test_infra_churn_aggregates_across_files():
    # 单文件都不够，lib + hooks + githooks 合计过线才触发
    rows = [(str(INFRA // 3), "0", "scripts/lib/a.py"),
            (str(INFRA // 3), "0", ".claude/hooks/b.sh"),
            (str(INFRA - 2 * (INFRA // 3)), "0", ".githooks/c")]
    assert is_significant(rows)[0] is True


def test_infra_aggregate_just_below_not_triggered():
    rows = [(str(INFRA // 2), "0", "scripts/lib/a.py"),
            (str(INFRA // 2 - 1), "0", ".claude/hooks/b.sh")]
    assert is_significant(rows)[0] is False


def test_infra_added_plus_deleted_counts():
    # churn = added + deleted，不是只算 added
    assert is_significant([(str(INFRA // 2), str(INFRA // 2), "scripts/lib/a.py")])[0] is True


# ── 总 churn ───────────────────────────────────────────────

def test_total_at_threshold_triggers():
    hit, reasons = is_significant([(str(TOTAL), "0", "projects/x/scripts/gen.py")])
    assert hit and any("总 churn" in r for r in reasons)


def test_total_below_threshold_not_triggered():
    assert is_significant([(str(TOTAL - 1), "0", "projects/x/scripts/gen.py")])[0] is False


def test_total_aggregates_across_buckets():
    rows = [(str(TOTAL // 3), "0", "scripts/a.py"),
            (str(TOTAL // 3), "0", ".claude/skills/prd/scripts/b.py"),
            (str(TOTAL - 2 * (TOTAL // 3)), "0", "projects/x/scripts/c.py")]
    assert is_significant(rows)[0] is True


def test_new_file_counts_full_lines():
    # 新文件 numstat 全量进 churn（added=文件行数）
    assert is_significant([(str(TOTAL), "0", "scripts/new_tool.py")])[0] is True


# ── 排除面 ─────────────────────────────────────────────────

@pytest.mark.parametrize("path", [
    "hub/prototype/scripts/check_paradigm.py",   # 分发包走自己管线
    "CLAUDE.md",
    ".claude/hooks/README.md",                    # 生成产物，非 py/sh
    "scripts/lib/thresholds.yaml",                # 配置非代码
    "projects/x/inputs/spec.png",
    "sync_public.sh",                             # 根 sh 不在审范围四桶
])
def test_out_of_scope_and_non_code_never_trigger(path):
    assert is_significant([("99999", "99999", path)])[0] is False


def test_binary_and_rename_dash_rows_skipped():
    # numstat 对二进制 / 无行数统计输出 `-	-	path`，跳过不炸
    assert is_significant([("-", "-", "scripts/lib/a.py")])[0] is False


def test_malformed_line_never_reaches_predicate():
    # 解析层只喂三段行；谓词拿到二元组也不该把 - 当数字加
    assert is_significant([]) == (False, [])


def test_both_reasons_reported():
    rows = [(str(TOTAL), "0", "scripts/lib/a.py")]  # 同时超 infra 和 total
    _, reasons = is_significant(rows)
    assert len(reasons) == 2
