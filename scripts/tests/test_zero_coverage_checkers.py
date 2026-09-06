"""零覆盖 hook 检查器补测（覆盖率报告 0% 的 4 个 gate 相关 checker）。

覆盖：
- check_learned_rules（learned-rules-gate：scene-list 一级分组）
- check_rule_version_drift（rule-version-drift-gate：产物骨架版本戳）
- check_ui_annotation（ui-annotation-gate block：渲染屏内注解）
- check_staged_large_files（pre-commit：大文件 staged 拦截）
"""
import json

import check_learned_rules as clr
import check_rule_version_drift as crvd
import check_staged_large_files as cslf
import check_ui_annotation as cua

# ═══════════ check_learned_rules ═══════════

def test_learned_scene_list_view_heading_ok(tmp_path):
    p = tmp_path / "scene-list.md"
    p.write_text("## View 1 · 发帖\n| A-1 | 发帖 |\n", encoding="utf-8")
    assert clr.check_scene_list(p) == []


def test_learned_scene_list_aux_prefix_exempt(tmp_path):
    p = tmp_path / "scene-list.md"
    for aux in ("附录", "跨端", "备注", "术语", "变更记录"):
        p.write_text(f"## {aux}\n", encoding="utf-8")
        assert clr.check_scene_list(p) == [], f"辅助段 ## {aux} 应豁免"


def test_learned_scene_list_bad_heading_flagged(tmp_path):
    p = tmp_path / "scene-list.md"
    p.write_text("## 1. 顶部入口\n", encoding="utf-8")
    errs = clr.check_scene_list(p)
    assert len(errs) == 1
    assert "L1" in errs[0]


def test_learned_scene_list_code_fence_exempt(tmp_path):
    p = tmp_path / "scene-list.md"
    p.write_text("```\n## 随便写\n```\n", encoding="utf-8")
    assert clr.check_scene_list(p) == []


def test_learned_scene_list_missing_file(tmp_path):
    assert clr.check_scene_list(tmp_path / "nope.md") == []


# ═══════════ check_rule_version_drift ═══════════

def test_drift_parse_stamp():
    assert crvd._parse_stamp(__import__("pathlib").Path("x")) is None  # 文件不存在


def test_drift_parse_stamp_with_stamp(tmp_path):
    p = tmp_path / "prd-x.md"
    p.write_text("<!-- @pm-skel v5 -->\n# x\n", encoding="utf-8")
    assert crvd._parse_stamp(p) == "5"


def test_drift_parse_stamp_html(tmp_path):
    p = tmp_path / "proto-x.html"
    p.write_text('<meta name="x-pm-skel-version" content="v6">', encoding="utf-8")
    assert crvd._parse_stamp(p) == "6"


def test_drift_current_version(tmp_path):
    cfg = tmp_path / ".claude" / "skills" / "_shared" / "workspace.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"skel_version": "v7"}), encoding="utf-8")
    assert crvd._current_version(tmp_path) == "7"


def test_drift_collect_artifacts(tmp_path):
    proj = tmp_path / "projects" / "demo"
    (proj / "deliverables" / "2026Q3" / "1.0").mkdir(parents=True)
    (proj / "prd-demo-baseline.md").write_text("x", encoding="utf-8")
    (proj / "deliverables" / "2026Q3" / "1.0" / "prd-demo-1.0.md").write_text("x", encoding="utf-8")
    (proj / "deliverables" / "2026Q3" / "1.0" / "proto-demo-1.0.html").write_text("x", encoding="utf-8")
    arts = crvd._collect_artifacts(proj)
    assert len(arts) == 3
    assert any(p.name == "prd-demo-baseline.md" for p in arts)
    assert any(p.suffix == ".html" for p in arts)


def test_drift_check_red_flag_on_stale(tmp_path, capsys):
    cfg = tmp_path / ".claude" / "skills" / "_shared" / "workspace.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"skel_version": "v6"}), encoding="utf-8")
    proj = tmp_path / "projects" / "demo"
    (proj / "deliverables").mkdir(parents=True)
    (proj / "deliverables" / "prd-demo-1.0.md").write_text(
        "<!-- @pm-skel v5 -->\n# x\n", encoding="utf-8")
    rc = crvd.check("demo", tmp_path)
    out = capsys.readouterr().out
    assert rc == 0
    assert "🔴" in out and "v5 < 当前 v6" in out


# ═══════════ check_ui_annotation ═══════════

def test_ui_annotation_kind():
    assert cua._kind_for(__import__("pathlib").Path("proto-x.html")) == "proto"
    assert cua._kind_for(__import__("pathlib").Path("imap-x.html")) == "imap"
    assert cua._kind_for(__import__("pathlib").Path("prd-x.md")) is None


def test_ui_annotation_clean_html(tmp_path):
    p = tmp_path / "proto-clean.html"
    p.write_text('<div class="p-card">真实文案</div>', encoding="utf-8")
    kind, findings = cua.check_file(p)
    assert kind == "proto"
    assert findings == []


def test_ui_annotation_prefix_flagged(tmp_path):
    p = tmp_path / "proto-dirty.html"
    # 只扫 .app-mock / .web-front / .layout 渲染壳内
    p.write_text('<div class="app-mock"><div> 注：这里需要后端返回</div></div>', encoding="utf-8")
    kind, findings = cua.check_file(p)
    assert kind == "proto"
    # findings = [(loc, text, hits)]，hits 内才是 (category, match)
    assert any(any(cat == "annotation_prefix" for cat, _ in hits) for _, _, hits in findings)


def test_ui_annotation_paren_flagged(tmp_path):
    p = tmp_path / "imap-dirty.html"
    p.write_text('<div class="phone">策略卡（示例数据）</div>', encoding="utf-8")
    kind, findings = cua.check_file(p)
    assert kind == "imap"
    assert any(any(cat == "annotation_paren" for cat, _ in hits) for _, _, hits in findings)


def test_ui_annotation_non_mockup_skipped(tmp_path):
    p = tmp_path / "proto-x.html"
    p.write_text('<div class="ann-card">注：旁注区合法</div>', encoding="utf-8")
    kind, findings = cua.check_file(p)
    assert kind == "proto"
    assert findings == []  # ann-card 旁注区不扫


# ═══════════ check_staged_large_files ═══════════

def test_staged_local_project_artifact():
    assert cslf.is_local_project_artifact("projects/x/inputs/docs/a.docx") is True
    assert cslf.is_local_project_artifact("projects/x/deliverables/b.pdf") is True
    assert cslf.is_local_project_artifact("projects/x/deliverables/assets/shot.png") is True
    assert cslf.is_local_project_artifact("projects/x/deliverables/shot.png") is False  # 非 assets/ 子目录
    assert cslf.is_local_project_artifact("scripts/x.docx") is False  # 非 projects/
    assert cslf.is_local_project_artifact("projects/x/inputs/docs/a.txt") is False  # 非豁免 ext
    assert cslf.is_local_project_artifact("projects/moderation/deliverables/客服导入-C1.xlsx") is False  # 词库表豁免
    assert cslf.is_local_project_artifact("projects/moderation/deliverables/a.xls") is True  # 豁免仅 xlsx
    assert cslf.is_local_project_artifact("projects/moderation/inputs/a.xlsx") is True  # 豁免仅 deliverables/


def test_staged_fmt_size():
    assert cslf.fmt_size(1_500_000) == "1.5 MB"
    assert cslf.fmt_size(500_000) == "500 KB"
    assert cslf.fmt_size(2_000_000) == "2.0 MB"
