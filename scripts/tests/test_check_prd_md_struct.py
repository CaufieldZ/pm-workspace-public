"""check_prd_md.sh「1.7 文档结构」维单测：章节完整性 + 渲染卫生。

锁住两类「写坏但内容扫描全绿」的坏法各自的判据与边界：
  渲染卫生 — 标题前缺空行 / <td> 内空行（代码块内的标题样行不算）
  完整性   — 章节数减少 = 问题；章节数不变但行数缩水逾两成 = 提醒；无上一版则不比
"""
import sys
from pathlib import Path

import pytest

_HUMANIZE = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "prd" / "scripts"
if str(_HUMANIZE) not in sys.path:
    sys.path.insert(0, str(_HUMANIZE))

from humanize import prd_struct_scan as s  # noqa: E402


def prev_of(lines):
    """造上一版文本：N 个章节 + M 行正文。"""
    return "# 1. 甲\n" + "正文\n" * lines + "\n# 2. 乙\n正文\n"


# ── 渲染卫生：标题前缺空行 ──────────────────────────────
def test_heading_after_html_block_hits():
    """标题紧贴 HTML 块 → 报（会被吞进块内，不再当标题渲染）。"""
    text = "<!-- 注释 -->\n# 1. 甲\n"
    hits = s.scan_hygiene(text)
    assert len(hits) == 1 and 'L2' in hits[0]


def test_heading_with_blank_line_clean():
    """标题前有空行 → 不报。"""
    assert s.scan_hygiene("<!-- 注释 -->\n\n# 1. 甲\n") == []


def test_heading_inside_fence_skipped():
    """代码块里的标题样行不算（模板 / 示例常带 # 行）。"""
    text = "```\n<div>\n# 不是标题\n```\n"
    assert s.scan_hygiene(text) == []


def test_first_line_heading_clean():
    """文件首行就是标题 → 不报（无前一行可比）。"""
    assert s.scan_hygiene("# 1. 甲\n") == []


# ── 渲染卫生：<td> 内空行 ───────────────────────────────
def test_blank_inside_td_hits():
    """单元格内空行 → 报（Confluence 截断 HTML 块，表格花屏）。"""
    text = "<table>\n<tr>\n<td>\n规则甲\n\n规则乙\n</td>\n</tr>\n</table>\n"
    hits = s.scan_hygiene(text)
    assert len(hits) == 1 and 'L5' in hits[0]


def test_blank_outside_td_clean():
    """单元格外的空行不报。"""
    text = "<table>\n<tr>\n<td>规则甲</td>\n</tr>\n</table>\n\n正文\n"
    assert s.scan_hygiene(text) == []


# ── 完整性：与上一版比对 ────────────────────────────────
def test_chapter_loss_is_problem():
    """章节数减少 → 报（文档可能被脚本写残）。"""
    problems, _warns = s.compare_prev("# 1. 甲\n正文\n", prev_of(5))
    assert problems and '章节数 1 少于上一版的 2' in problems[0]


def test_line_shrink_over_twenty_pct_warns():
    """章节数不变但行数缩水逾两成 → 提醒（不阻断）。"""
    now = "# 1. 甲\n" * 1 + "# 2. 乙\n"
    problems, warns = s.compare_prev(now, prev_of(50))
    assert problems == [] and warns and '缩水逾两成' in warns[0]


def test_line_shrink_under_twenty_pct_silent():
    """缩水不足两成 → 不报（正常删改）。"""
    prev = "# 1. 甲\n" + "正文\n" * 10 + "# 2. 乙\n"
    now = "# 1. 甲\n" + "正文\n" * 8 + "# 2. 乙\n"
    assert s.compare_prev(now, prev) == ([], [])


def test_no_prev_skips_completeness():
    """没有上一版（新文件 / 不在仓库内）→ 只查渲染卫生。"""
    problems, warns = s.scan_structure("# 1. 甲\n正文\n", None)
    assert (problems, warns) == ([], [])


def test_previous_version_none_outside_repo(tmp_path):
    """文件不在仓库内 → 取不到上一版，返回 None（不抛）。"""
    f = tmp_path / "prd.md"
    f.write_text("# 1. 甲\n", encoding="utf-8")
    assert s.previous_version("/nonexistent/repo", f) is None


def test_previous_version_none_for_untracked(tmp_path):
    """在仓库内但未被 git 跟踪 → 返回 None（不抛）。"""
    repo = Path(__file__).resolve().parents[2]
    f = tmp_path / "prd.md"
    f.write_text("# 1. 甲\n", encoding="utf-8")
    assert s.previous_version(repo, f) is None


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
