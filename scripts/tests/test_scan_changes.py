"""scan_changes 回归：分桶 / 规范路由 / 符号抽取 / 覆盖缺口四组纯函数 + collect_diff 的 git 取数。

锁定两件事：① 分桶口径与 pre-writeedit-guards.sh 的 required-read 归属一致
（hub/ 与 .md 必须落 out_of_scope，否则 code-review 会越界审不归它管的东西）；
② coverage_gaps 每条声明的维度都能被真样本命中 —— 恒 0 命中的检查是维护负担不是价值
（SCRIPTS_WRITING §三-K）。
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_MOD = (Path(__file__).resolve().parents[2]
        / ".claude/skills/code-review/scripts/scan_changes.py")
_spec = importlib.util.spec_from_file_location("scan_changes", _MOD)
scan_changes = importlib.util.module_from_spec(_spec)
sys.modules["scan_changes"] = scan_changes
_spec.loader.exec_module(scan_changes)

bucket_files = scan_changes.bucket_files
route_specs = scan_changes.route_specs
extract_changed_symbols = scan_changes.extract_changed_symbols
coverage_gaps = scan_changes.coverage_gaps
guess_product_skill = scan_changes.guess_product_skill
collect_diff = scan_changes.collect_diff


# ── bucket_files ──────────────────────────────────────────────

@pytest.mark.parametrize("path,expected", [
    ("scripts/dashboard.py", "root_scripts"),
    ("scripts/lib/repo.py", "root_scripts"),
    ("scripts/tests/test_dashboard.py", "root_scripts"),
    ("scripts/sync_pools.sh", "root_scripts"),
    (".claude/hooks/post-writeedit-dispatch.sh", "hooks"),
    (".claude/hooks/lib/post-checks.sh", "hooks"),
    (".claude/skills/prd/scripts/read_prd_section.py", "skill_scripts"),
    ("projects/moderation/scripts/gen_antispam_keywords.py", "project_scripts"),
    ("projects/livestream/scripts/src/crud.py", "project_scripts"),
    # 范围外：hub 走 aihub-package，md/html 归产出物 skill，根 .sh 不在四桶内
    ("hub/prototype/scripts/check_paradigm.py", "out_of_scope"),
    ("CLAUDE.md", "out_of_scope"),
    ("sync_public.sh", "out_of_scope"),
    (".claude/skills/prd/SKILL.md", "out_of_scope"),
    (".claude/skills/prd/assets/proto.js", "out_of_scope"),
])
def test_bucket_files(path, expected):
    buckets = bucket_files([path])
    assert buckets[expected] == [path]
    assert sum(len(v) for v in buckets.values()) == 1


def test_bucket_files_empty():
    assert all(v == [] for v in bucket_files([]).values())


# ── route_specs ───────────────────────────────────────────────

def test_route_specs_skill_scripts_adds_own_skill_md():
    routes = route_specs(bucket_files([".claude/skills/prd/scripts/read_prd_section.py"]))
    assert routes["skill_scripts"] == [
        "scripts/SCRIPTS_WRITING.md", ".claude/skills/prd/SKILL.md",
    ]


def test_route_specs_dedups_repeated_skill():
    routes = route_specs(bucket_files([
        ".claude/skills/prd/scripts/a.py", ".claude/skills/prd/scripts/b.py",
    ]))
    assert routes["skill_scripts"].count(".claude/skills/prd/SKILL.md") == 1


def test_route_specs_skips_out_of_scope():
    assert "out_of_scope" not in route_specs(bucket_files(["CLAUDE.md"]))


@pytest.mark.parametrize("name,expected", [
    ("build_proto_v3.py", "prototype"),
    ("gen_imap_skeleton.py", "interaction-map"),
    ("build_arch.py", "architecture-diagrams"),
    ("render_scene_list.py", "scene-list"),
    ("query_analytics.py", ""),
])
def test_guess_product_skill(name, expected):
    assert guess_product_skill(f"projects/x/scripts/{name}") == expected


# ── extract_changed_symbols ───────────────────────────────────

_DIFF = """diff --git a/scripts/lib/foo.py b/scripts/lib/foo.py
--- a/scripts/lib/foo.py
+++ b/scripts/lib/foo.py
@@ -1,8 +1,8 @@
-PATTERN_X = re.compile(r"a")
+PATTERN_X = re.compile(r"b")
-def scan_xxx(text):
+def scan_xxx(text, strict=False):
-class Helper:
+class Helper2:
-    def method_indented(self):
+    def method_indented(self, x):
diff --git a/scripts/run.sh b/scripts/run.sh
--- a/scripts/run.sh
+++ b/scripts/run.sh
-usage() {
+usage_new() {
"""


def test_extract_changed_symbols_top_level_only():
    got = extract_changed_symbols(_DIFF)
    assert ("scripts/lib/foo.py", "PATTERN_X") in got
    assert ("scripts/lib/foo.py", "scan_xxx") in got
    assert ("scripts/lib/foo.py", "Helper") in got
    assert ("scripts/run.sh", "usage") in got
    # 缩进的方法不是跨模块引用面，不该进反查
    assert all(sym != "method_indented" for _, sym in got)


def test_extract_changed_symbols_attributes_diff_header_not_a_symbol():
    # `--- a/path` 行以 - 开头，不能被当成删除的代码行
    assert extract_changed_symbols("--- a/scripts/x.py\n+++ b/scripts/x.py\n") == []


def test_extract_changed_symbols_dedups():
    diff = "+++ b/a.py\n-def f(x):\n-def f(x):\n"
    assert extract_changed_symbols(diff) == [("a.py", "f")]


def test_extract_changed_symbols_empty():
    assert extract_changed_symbols("") == []


# ── coverage_gaps（§三-K：每条维度都要有正例证明能命中）────────────

def test_gap_checker_without_test():
    gaps = coverage_gaps({"scripts/check_foo.py": "M"}, "")
    assert any("test_check_foo.py 未同改" in g for g in gaps)


def test_gap_checker_with_test_stays_silent():
    gaps = coverage_gaps({"scripts/check_foo.py": "M", "scripts/tests/test_check_foo.py": "M"}, "")
    assert not any("未同改" in g for g in gaps)


def test_gap_generator_docstring():
    gaps = coverage_gaps({"projects/x/scripts/gen_flow.py": "M"}, "")
    assert any("§三-J" in g for g in gaps)


def test_gap_lib_mypy():
    gaps = coverage_gaps({"scripts/lib/repo.py": "M"}, "")
    assert any("mypy scripts/lib/" in g for g in gaps)


@pytest.mark.parametrize("status", ["A", "D"])
def test_gap_readme_on_root_script_add_or_delete(status):
    gaps = coverage_gaps({"scripts/new_tool.py": status}, "")
    assert any("gen_scripts_readme.py" in g for g in gaps)


def test_gap_readme_silent_on_modify():
    gaps = coverage_gaps({"scripts/new_tool.py": "M"}, "")
    assert not any("gen_scripts_readme.py" in g for g in gaps)


def test_gap_readme_silent_on_nested_script():
    # scripts/lib/ 与 scripts/tests/ 不进根 README 清单
    gaps = coverage_gaps({"scripts/lib/new_mod.py": "A"}, "")
    assert not any("gen_scripts_readme.py" in g for g in gaps)


def test_gap_hooks_contract_test():
    gaps = coverage_gaps({".claude/hooks/lib/post-checks.sh": "M"}, "")
    assert any("test-hooks.sh" in g for g in gaps)


def test_gap_fail_key_positive_assertion():
    gaps = coverage_gaps({"scripts/check_foo.py": "M"}, '+    fail_keys.append("missing_intro")')
    assert any("§三-K" in g for g in gaps)


def test_gap_clean_diff():
    assert coverage_gaps({"projects/x/scripts/crud.py": "M"}, "+x = 1") == []


# ── collect_diff（I/O 层）─────────────────────────────────────

def _make_repo(path: Path) -> None:
    """在 path 建一次性 git 仓库并落一个空 initial commit（随 tmp_path 清理）。"""
    def run(*args: str) -> None:
        subprocess.run(["git", *args], cwd=path, check=True, capture_output=True)

    run("init", "-q")
    run("-c", "user.email=t@example.com", "-c", "user.name=t",
        "commit", "-q", "--allow-empty", "-m", "init")


def test_collect_diff_files_mode_returns_name_status(tmp_path):
    """指定 paths 时：状态行必须取到，且 pathspec 要真生效。

    回归锚点：选项若排在 `--` 之后，git 会把 `--name-status` 当路径spec，
    该路退化成 diff 正文，split("\\t") 解析不出条目 → 上层报「命中 0 个文件」。
    纯函数测试覆盖不到这条 I/O 路径，故单列。
    """
    _make_repo(tmp_path)
    (tmp_path / "a.sh").write_text("echo 1\n", encoding="utf-8")
    (tmp_path / "b.sh").write_text("echo 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.email=t@example.com", "-c", "user.name=t",
                    "commit", "-qm", "add"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "a.sh").write_text("echo 2\n", encoding="utf-8")

    statuses, diff, scope = collect_diff(tmp_path, False, "HEAD~1", ["a.sh"])
    assert statuses == {"a.sh": "M"}, f"name-status 未取到：{statuses}"
    assert "a.sh" in diff
    assert "b.sh" not in diff, "pathspec 未生效（b.sh 未被限定掉）"
    assert scope == "工作区改动（指定路径）"
