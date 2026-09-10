"""check_hub_fresh 回归：三层判据的纯函数契约。

锁定：① zip 新鲜度按 mtime 判且忽略缓存文件；② Tool 比版本号 / Agent 比部署日期；
③ 登记表缺失或坏 JSON 时降级为空表（不炸、不误报）。
"""
import json
import os

import pytest
from check_hub_fresh import (
    check,
    deploy_drift,
    load_deployed,
    parse_tool_version,
    report,
    stale_files,
)


@pytest.mark.parametrize("text,expected", [
    ('"""tool\nversion: 1.3.1\n"""', "1.3.1"),
    ('"""tool\n  version: 0.1.0  \n"""', "0.1.0"),
    ('"""tool\nversion: v1.3\n"""', None),
    ("no version here", None),
])
def test_parse_tool_version(text, expected):
    assert parse_tool_version(text) == expected


def _touch(path, mtime):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    os.utime(path, (mtime, mtime))


def test_stale_files_detects_newer_source(tmp_path):
    pkg = tmp_path / "prd"
    zip_path = tmp_path / "zips" / "prd.zip"
    _touch(zip_path, 1000)
    _touch(pkg / "SKILL.md", 2000)      # 比 zip 新 → 该重打
    _touch(pkg / "SETUP.md", 500)       # 比 zip 旧 → 不算
    assert [p.name for p in stale_files(pkg, zip_path)] == ["SKILL.md"]


def test_stale_files_ignores_cache_and_missing_zip(tmp_path):
    pkg = tmp_path / "prd"
    zip_path = tmp_path / "zips" / "prd.zip"
    _touch(zip_path, 1000)
    _touch(pkg / "scripts" / "__pycache__" / "a.pyc", 9999)
    _touch(pkg / ".DS_Store", 9999)
    assert stale_files(pkg, zip_path) == []
    # zip 不存在时不报 stale（缺 zip 是第二层黄灯的事，不是第一层红灯）
    assert stale_files(pkg, tmp_path / "zips" / "nope.zip") == []


def test_load_deployed_degrades(tmp_path):
    assert load_deployed(tmp_path / "missing.json") == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert load_deployed(bad) == {}
    good = tmp_path / "good.json"
    good.write_text(json.dumps({"packages": {"prd": {"version": "1.0.0"}}}), encoding="utf-8")
    assert load_deployed(good) == {"prd": {"version": "1.0.0"}}


def test_deploy_drift_tool_version_mismatch(tmp_path):
    pkg = tmp_path / "sensors-cli"
    pkg.mkdir()
    (pkg / "aihub_tool.py").write_text('"""t\nversion: 1.3.1\n"""', encoding="utf-8")
    assert deploy_drift(pkg, {"version": "1.3.1"}) is None
    assert deploy_drift(pkg, {"version": "v1.3.1"}) is None   # 登记带 v 前缀也算一致
    assert "1.1.0" in deploy_drift(pkg, {"version": "1.1.0", "deployed_at": "2026-07-01"})
    assert deploy_drift(pkg, None) is None


def test_deploy_drift_agent_changed_after_deploy(tmp_path):
    pkg = tmp_path / "promo-agent"
    pkg.mkdir()
    (pkg / "agent-model.json").write_text("{}", encoding="utf-8")
    sp = pkg / "system-prompt.md"
    sp.write_text("x", encoding="utf-8")
    os.utime(sp, (1_800_000_000, 1_800_000_000))  # 2027-01-15 前后，晚于下面登记日
    assert "重贴 OWUI" in deploy_drift(pkg, {"deployed_at": "2020-01-01"})
    assert deploy_drift(pkg, {"deployed_at": "2099-01-01"}) is None
    assert deploy_drift(pkg, {}) is None           # 无 deployed_at → 不判断


def test_check_exempt_package_skips_zip_layers(tmp_path):
    hub = tmp_path / "hub"
    (hub / "zips").mkdir(parents=True)
    # 豁免名单里的 agent 包：无 zip 不该报黄灯
    agent = hub / "promo-agent"
    agent.mkdir()
    (agent / "agent-model.json").write_text("{}", encoding="utf-8")
    (agent / "system-prompt.md").write_text("x", encoding="utf-8")
    result = check(hub)
    assert [y for y in result["yellow"] if y["kind"] == "zip-missing"] == []
    assert result["unregistered"] == ["promo-agent"]


def test_empty_registry_reports_unusable_not_green(tmp_path, capsys):
    # 登记表空 → 「无漂移」恒真；报绿等于谎称已核对，必须显式说结论不可用
    hub = tmp_path / "hub"
    (hub / "zips").mkdir(parents=True)
    agent = hub / "promo-agent"
    agent.mkdir()
    (agent / "agent-model.json").write_text("{}", encoding="utf-8")
    (agent / "system-prompt.md").write_text("x", encoding="utf-8")
    result = check(hub)
    assert result["registered"] == []
    report(result)
    out = capsys.readouterr().out
    assert "第三层" in out and "结论不可用" in out
    assert "🟢 第三层" not in out


def test_check_flags_missing_zip_for_non_exempt(tmp_path):
    hub = tmp_path / "hub"
    (hub / "zips").mkdir(parents=True)
    pkg = hub / "brand-new-skill"
    pkg.mkdir()
    (pkg / "SKILL.md").write_text("x", encoding="utf-8")
    result = check(hub)
    assert [y["pkg"] for y in result["yellow"] if y["kind"] == "zip-missing"] == ["brand-new-skill"]
    assert result["red"] == []
