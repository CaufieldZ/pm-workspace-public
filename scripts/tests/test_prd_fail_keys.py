"""prd_fail_keys / prd_warn_keys 逐维命中测试。

清单搬进 patterns.py 后，「维度名写错 / 扫描器不再返回该键」会退化成静默漏检
（hits 恒空 → 该维永远绿）。这里给每个 FAIL 维度各配一条违规样本 + 一条干净样本，
锁住「19 个 FAIL 维度都真的会响」。
"""

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SCRIPTS.parent / ".claude/skills/prd/scripts"))

from humanize.md_scan import scan_human_voice_md, scan_prd_structural_md  # noqa: E402
from humanize.patterns import prd_fail_keys, prd_warn_keys  # noqa: E402


def _scan(md: str) -> dict:
    return {**scan_human_voice_md(md), **scan_prd_structural_md(md)}


def _hits(key: str, md: str) -> list:
    return _scan(md).get(key, [])


# ── 条件开关：19 个 FAIL 维度只在全开时齐全 ─────────────────────────────────

def test_fail_keys_full_set_is_nineteen():
    keys = prd_fail_keys(split=True, skeleton=False, profile="delta", scene_prose=True)
    assert len(keys) == 19, [k for k, _ in keys]


def test_fail_keys_narrow_by_condition():
    """开关关掉时对应维度不入列（baseline / skeleton / split 各自的豁免集）。"""
    base = prd_fail_keys(split=False, skeleton=True, profile="baseline", scene_prose=False)
    names = [k for k, _ in base]
    for k in ("section_anchors", "bare_scene_codes", "placeholders",
              "blockquote_hits", "server_platform_tracking", "scene_prose_runon_hits"):
        assert k not in names, k
    full = [k for k, _ in prd_fail_keys(split=True, skeleton=False, profile="delta", scene_prose=True)]
    for k in ("section_anchors", "bare_scene_codes", "placeholders",
              "blockquote_hits", "server_platform_tracking", "scene_prose_runon_hits"):
        assert k in full, k


def test_warn_keys_skeleton_adds_placeholders():
    assert "placeholders" not in [k for k, _ in prd_warn_keys(skeleton=False)]
    assert "placeholders" in [k for k, _ in prd_warn_keys(skeleton=True)]


# ── 逐个 FAIL 维度：一条违规样本必须命中 ────────────────────────────────────

_CASES = {
    "date_tag_hits": "- 场景 X（2026-04-22 新增）",
    "zombie_heading_hits": "### 砍掉：旧版入口",
    "v_tag_heading_hits": "## 3.1 (V2.0 新增)",
    "tech_field_hits": "- **触发**：用户点分享",
    "circle_nums": "- 支持 ① 现货 ② 合约",
    "decision_nums": "- 按决策 3 的口径，展示战绩",
    "route_urls": "- 点入口进 /user/profile 页",
    "pm_overreach_hits": "- 鼠标 hover 时展示浮层",
    "visual_overreach_hits": "- 按钮用蓝色按钮，圆角 8px",
    "iteration_traces": "## 1.4 核心变更\n\n- 覆盖条目：上一稿的入口方案",
    "broken_image_alt": "![](./assets/flow.png)",
    "nested_subscenes": "##### 5.1.1.1 二级嵌套",
    "horizontal_rule_hits": "- 上一句\n\n---\n\n- 下一句",
    "scene_prose_runon_hits": (
        "# 2. 本轮需求\n\n"
        "## 2.1 T-1 · 分享入口\n\n"
        "- **现状**：入口在持仓行。用户要点两下。分享出的是海报。\n"
    ),
    "section_anchors": "- 展示口径见 §5.1",
    "bare_scene_codes": "- A-1 走海报，B-2 走卡片",
    "placeholders": "- 阈值填 TODO",
    "blockquote_hits": "> 静态章。只描述当前态。",
    "server_platform_tracking": (
        "| 事件英文名 | 应埋点平台 |\n| :--- | :--- |\n"
        "| `app_share_click` | 服务端 |\n"
    ),
}


def test_every_fail_key_has_a_hitting_sample():
    covered = set(_CASES)
    for key, _label in prd_fail_keys(split=True, skeleton=False, profile="delta", scene_prose=True):
        assert key in covered, f"FAIL 维度 {key} 没有违规样本"
        assert _hits(key, _CASES[key]), f"{key} 的样本没命中：{_CASES[key]!r}"


def test_date_tag_covers_inline_version_tag():
    """「（v2.1 新增）」这类行内版本标签也要命中，且不误伤括号列表里的版本号。"""
    assert _hits("date_tag_hits", "- 打赏入口（v2.1 新增）")
    assert _hits("date_tag_hits", "- 打赏入口（v3 更新）")
    assert _hits("date_tag_hits", "- 打赏入口（v2.1新增）")
    # 括号列表里顺带出现「1.4 核心变更」不是版本标签
    assert not _hits("date_tag_hits", "- 章节含（1.1 现状 / 1.4 核心变更）")
    # 长括号里顺带出现「覆盖」也不是
    assert not _hits("date_tag_hits", "- 见（v1.0.0，纯文档包，覆盖全链路）")


def test_samples_are_targeted():
    """每条样本只打中它自己那一维——样本要是顺带打中别的维，会掩盖那一维的漏检。"""
    all_keys = [k for k, _ in prd_fail_keys(split=True, skeleton=False, profile="delta", scene_prose=True)]
    for key, md in _CASES.items():
        fired = {k for k in all_keys if _hits(k, md)}
        assert fired == {key}, f"{key} 的样本连带命中 {sorted(fired - {key})}"
