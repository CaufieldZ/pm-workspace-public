"""gen_prd_skeleton 场景 view 分类回归（前台 / 后台 / 跨端）。

锁回归：分类不能只看 `## View N` 标题关键词——真实标题（「社区 Feed 首页」）不含关键词，
会让所有前台场景默认落「跨端」、「前台」章恒空。用编号前缀（M=后台 / D·E=跨端，见
CLAUDE.md 编号约定）+「端」列设备标记纠正，并保留标题兜底。
"""
import sys
from pathlib import Path

_PRD_SCRIPTS = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "prd" / "scripts"
sys.path.insert(0, str(_PRD_SCRIPTS))

import gen_prd_skeleton as g  # noqa: E402


def _views(md: str, tmp_path) -> dict:
    f = tmp_path / "scene-list.md"
    f.write_text(md, encoding="utf-8")
    return {s["id"]: s["view"] for s in g.parse_scene_list(f)}


def test_view_by_prefix_and_device(tmp_path):
    md = """## View 1 · 社区 Feed 首页
| 编号 | 场景 | 模块 | 端 | 优先级 | 说明 |
|------|------|------|----|--------|------|
| A-1 | 帖子流 | Feed | 📱web | P0 | x |
| M-1 | 后台配置 | 运营 | 🖥 | P0 | y |
| D-1 | 数据同步 | 流 | | P0 | z |
"""
    v = _views(md, tmp_path)
    assert v["A-1"] == "前台"   # 用户端设备 → 前台（曾误判跨端）
    assert v["M-1"] == "后台"   # M-N 编号约定
    assert v["D-1"] == "跨端"   # D-N 数据流天然跨系统


def test_front_default_not_swallowed_by_cross(tmp_path):
    # 无「端」列（5 列表）+ 标题无关键词 → 回落标题兜底（跨端），不崩
    md = """## View 1 · 发布器
| 编号 | 场景 | 模块 | 优先级 | 说明 |
|------|------|------|--------|------|
| B-1 | 发帖 | 发布 | P0 | x |
"""
    v = _views(md, tmp_path)
    assert v["B-1"] in ("前台", "跨端")  # 至少不因 5 列解析失败丢场景


def test_backend_heading_still_wins(tmp_path):
    # 标题含后台关键词 + 用户端设备：heading 判后台优先（避免管理端 web 误判前台）
    md = """## View 9 · 运营后台配置
| 编号 | 场景 | 模块 | 端 | 优先级 | 说明 |
|------|------|------|----|--------|------|
| F-1 | 配置项 | 运营 | web | P0 | x |
"""
    v = _views(md, tmp_path)
    assert v["F-1"] == "后台"
