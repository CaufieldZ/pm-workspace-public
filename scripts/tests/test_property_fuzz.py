"""核心解析器属性测试（hypothesis fuzz）。

服务 §K「checker 维度必须自证能命中」：正则/解析器类 checker 的退化（死模式 /
\b 边界失效 / 豁免漏收）靠手写用例难穷举，属性测试喂任意输入断言不变量：
  1. 任意输入不崩溃
  2. 返回结构契约（类型 / 键全集）不破
  3. GFM 表格行的拆解不变量

被测代码在 skill 目录，手动注入 sys.path（conftest 只覆盖 scripts/）。
"""
import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

_ROOT = Path(__file__).resolve().parents[2]

# ── scene-list 解析器（.claude/skills/scene-list/scripts/）──
_SCENE_SCRIPTS = _ROOT / ".claude" / "skills" / "scene-list" / "scripts"
if str(_SCENE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCENE_SCRIPTS))
import check_scene_list as csl

# ── PRD 扫描器（.claude/skills/prd/scripts/humanize/，相对 import 需包上下文）──
_PRD_HUMANIZE = _ROOT / ".claude" / "skills" / "prd" / "scripts"
if str(_PRD_HUMANIZE) not in sys.path:
    sys.path.insert(0, str(_PRD_HUMANIZE))
# ── CJK 标点（根 scripts/，conftest 已注入）──
import check_cjk_punct as cjk
from humanize import md_scan

# ═══════════ 1. check_scene_list ═══════════

@given(st.text(max_size=4000))
def test_scene_list_check_text_never_crashes(text):
    """任意文本（含全 unicode）→ 不崩溃 + 返回 (level, message) 二元组列表。"""
    out = csl.check_text(text)
    assert isinstance(out, list)
    for item in out:
        assert isinstance(item, tuple) and len(item) == 2
        assert isinstance(item[0], str) and isinstance(item[1], str)


@given(st.text(alphabet="| -:abcdefgABCDEFG0123456789", max_size=300))
def test_scene_list_cells_invariant(line):
    """GFM 表格行（首尾 |）→ cell 数 = split 段数 - 2（首尾空段剥净）。"""
    if line.count("|") >= 2 and line.lstrip().startswith("|") and line.rstrip().endswith("|"):
        cells = csl._cells(line)
        segments = line.split("|")
        assert len(cells) == len(segments) - 2
        assert all(c == c.strip() for c in cells)  # 去空白


@given(st.text(alphabet="|-: ", max_size=100))
def test_scene_list_sep_row_never_crashes(line):
    """分隔行判定不崩溃（| - : 空格组合）。"""
    assert isinstance(csl._is_sep_row(line), bool)


# ═══════════ 2. md_scan（PRD 扫描器）═══════════

# 两个扫描函数的返回键全集（check_prd_md.sh fail_keys 依赖，缺键即静默漏检）
_HUMAN_VOICE_KEYS = [
    "date_tag_hits", "snake_field_hits", "css_impl_hits", "zombie_heading_hits",
    "v_tag_heading_hits", "tech_field_hits", "pm_overreach_hits",
    "visual_overreach_hits", "semicolon_abuse_hits", "long_sentence_hits",
    "bullet_runon_hits", "scene_prose_runon_hits",
]
_STRUCTURAL_KEYS = [
    "circle_nums", "placeholders", "decision_nums", "section_anchors",
    "route_urls", "cjk_half_punct", "bare_scene_codes", "broken_image_alt",
    "iteration_traces", "nested_subscenes", "branch_prose_hits",
    "horizontal_rule_hits", "blockquote_hits",
]


@given(st.text(max_size=6000))
def test_md_scan_human_voice_never_crashes(text):
    """任意 md → 不崩溃 + 返回 dict 含 human_voice 全部键（fail_keys 依赖）。"""
    out = md_scan.scan_human_voice_md(text)
    assert isinstance(out, dict)
    for key in _HUMAN_VOICE_KEYS:
        assert key in out, f"scan_human_voice_md 缺键 {key}"
        assert isinstance(out[key], list)


@given(st.text(max_size=6000))
def test_md_scan_structural_never_crashes(text):
    """任意 md → 结构性扫描不崩溃 + 返回 dict 含 structural 全部键。"""
    out = md_scan.scan_prd_structural_md(text)
    assert isinstance(out, dict)
    for key in _STRUCTURAL_KEYS:
        assert key in out, f"scan_prd_structural_md 缺键 {key}"
        assert isinstance(out[key], list)


# ═══════════ 3. check_cjk_punct ═══════════

@given(st.text(max_size=4000))
def test_cjk_check_text_never_crashes(text):
    """任意文本 → 不崩溃 + 返回 4 元组 (行号, 级别, 原因, 原文) 列表。"""
    out = cjk.check_text(text)
    assert isinstance(out, list)
    for item in out:
        assert isinstance(item, tuple) and len(item) == 4


@given(st.text(alphabet="中文测试,.;:!?（）() 0123456789abc", max_size=800))
def test_cjk_check_text_cjk_alphabet_never_crashes(text):
    """CJK + 半角/全角标点混合（核心判定路径）→ 不崩溃 + 行号合法。"""
    for lineno, level, reason, _raw in cjk.check_text(text):
        assert isinstance(lineno, int) and lineno >= 1
        assert level in ("strict", "warn")
        assert isinstance(reason, str)
