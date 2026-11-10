"""prd_fail_keys / prd_warn_keys 逐维命中测试。

「维度名写错 / 扫描器不再返回该键」会退化成静默漏检（hits 恒空 → 该维永远绿）。
这里给每个 FAIL 维度各配一条违规样本，锁住「每个维度都真的会响」，
并锁住写法类内容（长句 / 分号 / 用词）不被判成硬错。
"""

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SCRIPTS.parent / ".claude/skills/prd/scripts"))

from humanize.md_scan import scan_prd_structural_md  # noqa: E402
from humanize.patterns import prd_fail_keys, prd_warn_keys  # noqa: E402


def _hits(key: str, md: str) -> list:
    return scan_prd_structural_md(md).get(key, [])


_ALL = dict(skeleton=False, profile="delta")


def test_fail_keys_full_set():
    keys = [k for k, _ in prd_fail_keys(**_ALL)]
    assert len(keys) == 7, keys


def test_fail_keys_narrow_by_condition():
    """开关关掉时对应维度不入列（baseline / skeleton 各自的豁免集）。"""
    narrow = [k for k, _ in prd_fail_keys(skeleton=True, profile="baseline")]
    gated = ("placeholders", "blockquote_hits", "server_platform_tracking")
    for k in gated:
        assert k not in narrow, k
    full = [k for k, _ in prd_fail_keys(**_ALL)]
    for k in gated:
        assert k in full, k


def test_warn_keys_only_skeleton_placeholders():
    assert prd_warn_keys(skeleton=False) == []
    assert [k for k, _ in prd_warn_keys(skeleton=True)] == ["placeholders"]


_CASES = {
    "diagram_code_hits": "```mermaid\ngraph TD\n  A --> B\n```",
    "horizontal_rule_hits": "- 上一句\n\n---\n\n- 下一句",
    "broken_image_alt": "![](./assets/flow.png)",
    "tracking_header_hits": (
        "| 页面 | 事件英文名 | 属性 | 平台 |\n| :--- | :--- | :--- | :--- |\n"
        "| 直播间 | `app_live_card_close` | 卡片类型 | APP |\n"
    ),
    "placeholders": "- 阈值填 TODO",
    "blockquote_hits": "> 静态章。只描述当前态。",
    "server_platform_tracking": (
        "| 所属页面 | 事件中文名 | 事件英文名 | 属性中文名 | 属性英文名 | 数据类型 | 是否必填 | 数据值示例 | 应埋点平台 | 触发机制 |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        "| 分享面板 | 分享点击 | `app_share_click` | 渠道 | channel | STRING | 是 | x | 服务端 | 点击后 |\n"
    ),
}


def test_every_fail_key_has_a_hitting_sample():
    for key, _label in prd_fail_keys(**_ALL):
        assert key in _CASES, f"FAIL 维度 {key} 没有违规样本"
        assert _hits(key, _CASES[key]), f"{key} 的样本没命中：{_CASES[key]!r}"


def test_samples_are_targeted():
    """每条样本只打中它自己那一维——样本顺带打中别的维，会掩盖那一维的漏检。"""
    all_keys = [k for k, _ in prd_fail_keys(**_ALL)]
    for key, md in _CASES.items():
        fired = {k for k in all_keys if _hits(k, md)}
        assert fired == {key}, f"{key} 的样本连带命中 {sorted(fired - {key})}"


def test_standard_tracking_header_passes():
    md = (
        "| 所属页面 | 事件中文名 | 事件英文名 | 属性中文名 | 属性英文名 | 数据类型 | 是否必填 | 数据值示例 | 应埋点平台 | 触发机制 |\n"
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        "| 直播间 | 策略卡关闭 | `app_live_card_close` | 卡片类型 | card_type | STRING | 是 | market | APP | 点关闭后 |\n"
    )
    assert _hits("tracking_header_hits", md) == []


def test_writing_style_is_not_judged():
    """写法交给作者：行内句号、分号串、英文 UI 词、长句、章节锚点都不算硬错。"""
    md = (
        "# 2. 本轮需求\n\n"
        "- **现状**：入口在持仓行。用户要点两下。分享出的是海报。\n"
        "- 默认自动通过；运营可驳回；通过前校验冲突，口径见 §5.1，A-1 走海报\n"
        "- 鼠标 hover 时展示 tooltip，打赏入口（v2.1 新增）\n"
        "- 平仓盈利顶飘的触发要覆盖主动平仓、止盈止损触发、部分平仓三种情况，"
        "并且每一笔都要显示本次已实现盈亏与收益率两个数字，以及对应的晒单入口\n"
    )
    out = scan_prd_structural_md(md)
    fired = [k for k, _ in prd_fail_keys(**_ALL) if out.get(k)]
    assert fired == [], fired
