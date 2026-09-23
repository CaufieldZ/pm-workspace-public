"""md_scan.label_li_runs 单测：场景块平铺标签前缀的形态识别。

这条 WARN 的形态识别必须覆盖存量真实写法，否则静默零命中（看着在跑其实没查）：
  认 — `标签：` / `<strong>标签</strong>：` / `标签 · ` 三种平铺前缀，连续 ≥ 3 条同标签报一处
  不认 — 组头式（标签后换行跟嵌套列表）是正确形态，一条都不该报；连排 < 3 条放过
"""
import sys
from pathlib import Path

import pytest

_HUMANIZE = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "prd" / "scripts"
if str(_HUMANIZE) not in sys.path:
    sys.path.insert(0, str(_HUMANIZE))

from humanize import md_scan as s  # noqa: E402


def runs_of(md):
    """取 label_li_runs 命中列表。"""
    return s.scan_prd_structural_md(md)["label_li_runs"]


def flat(n, sep="：", label="显示逻辑", bold=False):
    """造 n 条连排的平铺标签 li。"""
    head = "<strong>%s</strong>" % label if bold else label
    return "".join("        <li>%s%s规则 %d</li>\n" % (head, sep, i) for i in range(1, n + 1))


# ── 真阳性：三种平铺前缀 ────────────────────────────────
def test_plain_colon_run_hits():
    """`显示逻辑：` 连排 3 条 → 报一处。"""
    hits = runs_of(flat(3))
    assert len(hits) == 1 and '连续 3 个「显示逻辑」' in hits[0]


def test_bold_colon_run_hits():
    """`<strong>显示逻辑</strong>：` 连排 3 条 → 同样要报（只认裸标签会静默漏检）。"""
    assert len(runs_of(flat(3, bold=True))) == 1


def test_middot_run_hits():
    """`显示逻辑 · ` 连排 3 条 → 同样要报。"""
    assert len(runs_of(flat(3, sep=" · "))) == 1


def test_longer_run_reports_actual_length():
    """连排 5 条 → 报 5。"""
    assert '连续 5 个' in runs_of(flat(5))[0]


# ── 真阴性 ──────────────────────────────────────────────
def test_grouped_form_never_hits():
    """组头式（标签后换行跟嵌套 ul）是目标形态 → 一条都不报。"""
    md = "".join(
        "        <li><strong>%s</strong>\n          <ul>\n            <li>规则</li>\n          </ul>\n        </li>\n" % lb
        for lb in ("显示逻辑", "显示要素", "交互", "显示逻辑", "显示要素", "交互")
    )
    assert runs_of(md) == []


def test_two_consecutive_below_threshold():
    """连排 2 条 < 阈值 3 → 不报（存量里两条并列常见，报则噪音）。"""
    assert runs_of(flat(2)) == []


def test_label_switch_resets_run():
    """换标签即重置：3 条显示逻辑 + 3 条交互 = 两处，不是一处 6 连。"""
    hits = runs_of(flat(3) + flat(3, label="交互"))
    assert len(hits) == 2 and '「显示逻辑」' in hits[0] and '「交互」' in hits[1]


def test_plain_numbered_list_never_hits():
    """无标签的普通 li 不报。"""
    assert runs_of("".join("        <li>第 %d 步</li>\n" % i for i in range(4))) == []


def test_fenced_code_skipped():
    """代码块里的同形行不算。"""
    md = "```html\n" + flat(4) + "```\n"
    assert runs_of(md) == []


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
