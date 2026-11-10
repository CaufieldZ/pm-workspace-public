"""hook_check_prd_content（PRD 写入时内容门）单元测试。

锁四件事：只报本次新增行（存量旧账不卡）；骨架占位符不拦；别的门已管的维度（水平线）
不重复报；baseline 豁免的维度只在 delta 下报。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import hook_check_prd_content as hc  # noqa: E402


def _run(f: Path, added: list[str]) -> list[str]:
    """按 hook 的调用形态跑一遍，返回命中的明细行。"""
    keys = hc.key_list(str(f))
    hits = hc.scan_added_hits(str(f), added, keys)
    return [h for key, _label in keys for h in hits.get(key, [])]


def _md(tmp_path: Path, text: str, name: str = "prd-demo-v1.md", sub: str = "") -> Path:
    d = tmp_path / sub if sub else tmp_path
    d.mkdir(parents=True, exist_ok=True)
    f = d / name
    f.write_text(text, encoding="utf-8")
    return f


# ── 1. 只报新增行 ──────────────────────────────────────────────────────────

def test_only_added_lines_are_reported(tmp_path):
    text = "# 1. 背景\n\n> 旧账导读\n\n> 新增导读\n"
    f = _md(tmp_path, text)
    # 只把第二段当作本次新增
    hits = _run(f, ["> 新增导读"])
    assert len(hits) == 1, hits
    assert "新增导读" in hits[0]


def test_whole_file_added_reports_everything(tmp_path):
    text = "# 1. 背景\n\n> 导读一\n\n```mermaid\ngraph TD\n```\n"
    f = _md(tmp_path, text)
    assert len(_run(f, text.splitlines())) == 2


# ── 2. 骨架占位符不拦 ──────────────────────────────────────────────────────

def test_draft_placeholders_not_blocked(tmp_path):
    text = "# 1. 背景\n\n- 阈值填 TODO\n- 文案待填充\n"
    f = _md(tmp_path, text, name="prd-demo-v1.md")
    assert _run(f, text.splitlines()) == []


# ── 3. 别的门已管的维度不重复报 ────────────────────────────────────────────

def test_other_gate_keys_not_reported(tmp_path):
    text = "# 1. 背景\n\n- 上一段\n\n---\n\n- 下一段\n"
    f = _md(tmp_path, text)
    assert _run(f, text.splitlines()) == []


# ── 4. baseline 豁免维度 ───────────────────────────────────────────

def test_baseline_profile_skips_delta_only_keys(tmp_path):
    text = (
        "# 1. 背景\n\n> 导读墙\n\n"
        "| 所属页面 | 事件中文名 | 事件英文名 | 属性中文名 | 属性英文名 | 数据类型 | 是否必填 | 数据值示例 | 应埋点平台 | 触发机制 |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        "| 页 | 事件 | `a` | 属性 | p | STRING | 是 | x | 服务端 | 点击后 |\n"
    )
    delta = _md(tmp_path, text, name="prd-demo-v1.md")
    assert len(_run(delta, text.splitlines())) == 2, _run(delta, text.splitlines())

    base = _md(tmp_path, text, name="prd-demo-baseline.md")
    assert _run(base, text.splitlines()) == []
