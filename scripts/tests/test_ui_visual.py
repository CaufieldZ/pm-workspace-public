"""ui_visual 回归：11 类 UI 视觉 PATTERN + 章节豁免（性能契约保留）。

防类 1 误拦：#128 / #1024 这类编号不能被当 hex 假阳；
防类 2 漏判：非功能性 / 性能 / 兼容性章节里的 300ms / 1280px 是契约，整段豁免。
"""
import pytest
from lib.ui_visual import _is_exempt_h2, scan_ui_visual


@pytest.mark.parametrize("text,cat", [
    ("宽度 100px", "px"),
    ("字号 14pt", "pt"),
    ("背景色 #ffffff", "hex"),
    ("颜色 #f0a", "hex"),             # 3 位含字母 → 命中
    ("透明度 opacity:0.5", "opacity"),
    ("font-family: sans", "font"),
    ("border-radius: 4px", "css_prop"),
    ("动画 300ms", "ms"),
    ("linear-gradient(red,blue)", "gradient"),
    ('<div class="x">', "html_attr"),
])
def test_hit(text, cat):
    cats = {c for c, _ in scan_ui_visual(text)}
    assert cat in cats, f"期望命中 {cat}，实际 {cats}"


def test_3digit_hex_without_letter_not_matched():
    # #128 / #1024 这类纯数字编号不能假阳为 hex（3 位必须含字母）
    cats = {c for c, _ in scan_ui_visual("see issue #128")}
    assert "hex" not in cats


@pytest.mark.parametrize("h2", ["非功能性需求", "性能指标", "兼容性矩阵", "兼容矩阵"])
def test_exempt_h2_keywords(h2):
    assert _is_exempt_h2(h2) is True


@pytest.mark.parametrize("h2", ["交互流程", "业务规则", ""])
def test_non_exempt_h2(h2):
    assert _is_exempt_h2(h2) is False


def test_exempt_h2_skips_entire_scan():
    # 命中豁免章节 → 整段不扫（性能契约保留）
    assert scan_ui_visual("300ms / 1280px", exempt_h2="非功能性需求") == []


def test_normal_h2_still_scans():
    # 非豁免章节 → 正常扫
    assert scan_ui_visual("100px", exempt_h2="交互流程") != []
