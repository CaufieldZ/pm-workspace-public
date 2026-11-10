"""md_to_confluence 软换行陷阱侦测单测。

CommonMark 把「中间没有空行的连续行」当同一段的软换行，推上 wiki 只剩一个空格。
promo-kit 骨架里的「主标题：/副标题：」逐行字段最常踩。

  阻断  — launch-* / promo-* 产物里 ≥2 行连续的「标签：值」且中间无空行
  放行  — 字段间有空行 / 长行正文硬折行 / 列表 / 表格 / 代码围栏 / 无字段的短行段
  收窄  — 非 promo 产物不阻断（语料与提纲里的「标签：」行不是这个坑）
  跳过  — 无代码围栏的 JSON 块
  逃生口 — allow=True 只提示不阻断
"""
from pathlib import Path

import md_to_confluence as m


def _blocked(text: str, name: str = "launch-x.md") -> int:
    return m.check_soft_line_breaks(text, Path(name), allow=False)


# ── 真阳性 ────────────────────────────────────────────
def test_field_block_without_blank_lines_blocks():
    assert _blocked("## 一\n\n主标题：甲\n副标题：乙\n支持：丙\n") == 1


def test_soft_break_runs_reports_line_numbers():
    assert m.soft_break_runs("## 一\n\n甲：一\n乙：二\n") == [(3, ["甲：一", "乙：二"])]


# ── 真阴性 ────────────────────────────────────────────
def test_field_block_with_blank_lines_passes():
    assert _blocked("## 一\n\n主标题：甲\n\n副标题：乙\n") == 0


def test_long_wrapped_prose_passes():
    line = "这是一段按八十字符硬折行的正文，第一行停在句中，第二行接着说下去，两行都超过四十六个字符。"
    assert _blocked(f"## 一\n\n{line}\n{line}\n") == 0


def test_list_row_fence_pass():
    assert _blocked("## 一\n\n- 主标题：甲\n- 副标题：乙\n") == 0
    assert _blocked("| 主标题：甲 | 说明 |\n| --- | --- |\n") == 0
    assert _blocked("```\n主标题：甲\n副标题：乙\n```\n") == 0


# ── 收窄边界 ──────────────────────────────────────────
def test_non_promo_file_never_blocks():
    md = "## 一\n\n主标题：甲\n副标题：乙\n"
    assert _blocked(md, name="prd-foo.md") == 0
    assert _blocked(md, name="dig-直播.md") == 0


def test_unfenced_json_not_field_block():
    assert _blocked('## 一\n\n{\n"uid": "1",\n"message": "换绑"\n') == 0


def test_allow_flag_only_warns():
    md = "## 一\n\n主标题：甲\n副标题：乙\n"
    assert m.check_soft_line_breaks(md, Path("launch-x.md"), allow=True) == 0
