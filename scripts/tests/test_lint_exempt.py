"""行文 lint 豁免规则（lib/lint_exempt）+ bash 侧同源判定的一致性测试。

核心资产是 test_bash_python_agree：规则表是 bash / Python 双侧共读的单一真相源，
任一侧解析走样（glob 语义 / 路径段匹配）都会让 gate 时灵时不灵，这里逐条对拍锁死。
"""
import shutil
import subprocess
from pathlib import Path

import pytest
from lib.lint_exempt import is_lint_exempt

_REPO = Path(__file__).resolve().parents[2]

# (路径, 期望豁免)——正 / 负 / 边界三类混排
CASES = [
    # 内部审计文档
    ("x/audit-2026Q3.md", True),
    ("x/fix-plan-community.md", True),
    ("projects/x/audits/deep-dive.md", True),
    # IMAP / 交互大图（四种命名形态都得覆盖）
    ("imap.html", True),
    ("imap-proj-community-v6.html", True),
    ("deliverables/community-imap.html", True),
    ("interaction-flow.html", True),
    ("x-interaction.html", True),
    ("foo-interaction-bar.html", True),
    # 该扫的产物
    ("projects/community/prd-community-baseline.md", False),
    ("projects/community/scene-list.md", False),
    ("deliverables/proto-queen-v2.html", False),
    ("deliverables/reports/weekly-2026W30.md", False),
    # 边界：像但不是
    ("notaudit-x.md", False),          # audit- 必须在词首
    ("my-imap-notes.md", False),       # imap glob 只认 .html
    ("x/audit/deep.md", False),        # 目录段是 audits 不是 audit
    ("IMAP.HTML", False),              # glob 大小写敏感，与 bash case 对齐
]


@pytest.mark.parametrize("rel,expected", CASES)
def test_is_lint_exempt(rel, expected):
    assert is_lint_exempt(Path(rel)) is expected


@pytest.mark.skipif(shutil.which("bash") is None, reason="无 bash")
@pytest.mark.parametrize("rel,expected", CASES)
def test_bash_python_agree(rel, expected):
    """bash 侧 is_plain_language_exempt 必须与 Python 侧逐条同结论。"""
    script = (
        f'source "{_REPO}/.claude/hooks/lib/guards.sh"; '
        f'is_plain_language_exempt "{rel}"'
    )
    rc = subprocess.run(
        ["bash", "-c", script],
        env={"CLAUDE_PROJECT_DIR": str(_REPO), "PATH": "/usr/bin:/bin"},
        capture_output=True,
    ).returncode
    assert (rc == 0) is expected, f"bash 侧判定与预期不符：{rel}"


def test_rules_file_parsed():
    """规则表非空且两类规则都解析到（防路径写错静默退化成全不豁免）。"""
    from lib.lint_exempt import EXEMPT_BASENAME, EXEMPT_PATHSEGMENT
    assert EXEMPT_BASENAME and EXEMPT_PATHSEGMENT


def test_cli_exit_codes():
    cli = _REPO / "scripts/lib/lint_exempt.py"
    assert subprocess.run(["python3", cli, "--check-exempt", "audit-x.md"]).returncode == 0
    assert subprocess.run(["python3", cli, "--check-exempt", "prd-x.md"]).returncode == 1
