"""check_static_chapter 章节边界单元测试。

锁四种章节边界形态：`#` 非静态章整章跳过（含其下的 `##`）；半静态章（埋点 / 非功能性需求）
只免「技术实现」「UI 视觉」，流水 / 思考过程照查；`##` 非静态节只跳本节；模块章里的真泄漏照报。
"""

from pathlib import Path

import check_static_chapter as csc


def _hits(tmp_path: Path, text: str) -> list[tuple[int, str, str, str, str]]:
    p = tmp_path / "sample.md"
    p.write_text(text, encoding="utf-8")
    return csc.check_file(p)


def _cats(hits: list[tuple[int, str, str, str, str]]) -> list[str]:
    return [h[2] for h in hits]


# ── 1. `#` 非静态章：整章跳过，底下的 `##` 跟着跳过 ──────────────────────────

def test_h1_dynamic_chapter_skips_whole_chapter(tmp_path):
    hits = _hits(tmp_path, """# 示例直播 · Baseline PRD

# 1. 直播间模块

## 1.1 展示
- 状态按 Apollo 配置的频道状态更新

# 15. 变更记录

## 15.1 明细
| 2026-09-03 | 推卡币对来源改 Apollo 白名单 |

## 15.2 其他
- 下线走 binlog 同步的旧链路
""")
    # 模块章的真泄漏照报，变更记录章（含其下两个 `##`）一条都不报
    assert len(hits) == 1, f"变更记录章未被整章跳过：{hits}"
    assert hits[0][0] == 6


def test_new_h1_resets_both_levels(tmp_path):
    """H1 非静态章之后遇到新 H1，两级状态都重置，后续行恢复扫描。"""
    hits = _hits(tmp_path, """# 15. 变更记录
| 2026-08-01 | 改 Apollo 白名单 |

# 6. 直播间模块

## 6.0 模块规则
- 状态按 Apollo 配置的频道状态更新
""")
    assert _cats(hits) == ["技术实现"]
    assert hits[0][0] == 7


# ── 2. 半静态章：只免「技术实现」「UI 视觉」 ────────────────────────────────

def test_partial_static_tracking_chapter(tmp_path):
    """埋点章不报 translate（UI 视觉），但「（v2.1 新增）」照报（流水标注）。"""
    hits = _hits(tmp_path, """# 12. 埋点契约

## 12.1 业务事件清单
| 直播间 APP | 消息操作 | `APP_LIVE_msg_action` | del / copy / translate | APP |
| 打赏入口（v2.1 新增） | 动作类型 | `APP_LIVE_tip` | 点击 | APP |
""")
    assert _cats(hits) == ["流水标注"]


def test_partial_static_nonfunctional_chapter(tmp_path):
    """非功能性需求章免技术实现 / UI 视觉，但不免思考过程。"""
    hits = _hits(tmp_path, """# 14. 非功能性需求

## 14.1 性能
- 首屏渲染 ≤ 300ms，缓存走 Redis
- 起初考虑放宽到 500ms
""")
    assert _cats(hits) == ["思考过程"]


# ── 3. `##` 非静态节：只跳本节 ──────────────────────────────────────────────

def test_h2_dynamic_section_skips_only_itself(tmp_path):
    hits = _hits(tmp_path, """# 1. 直播间模块

## 1.1 展示
- 推卡币对来源读 Redis 白名单

## 方案决策
- 推卡币对来源改用 Apollo 白名单

## 1.2 交互
- 下发走 Kafka 消息
""")
    assert len(hits) == 2, f"`## 方案决策` 未只跳本节：{hits}"
    assert all("方案决策" not in h[3] for h in hits)
    assert [h[0] for h in hits] == [4, 10]


# ── 4. lint-allow 在 `#` / `##` 处都清空 ────────────────────────────────────

def test_lint_allow_cleared_at_h1(tmp_path):
    hits = _hits(tmp_path, """# 1. 直播间模块
<!-- lint-allow: Apollo -->
- 推卡币对来源读 Apollo 白名单

# 2. 连麦模块
- 推卡币对来源读 Apollo 白名单
""")
    assert len(hits) == 1, f"章节豁免未在 H1 处清空：{hits}"
    assert hits[0][0] == 6
