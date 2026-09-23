"""hook_check_md_blockquote（blockquote 物化）与 _pc_git_added_lines（共享 diff）等价测试。

等价性判据：原内嵌 python 的 added 抽取（`l[1:]` 管线）与 bash 共享 helper
（`grep '^+' | grep -v '^+++' | sed` 管线）在四种 git 状态下输出逐字节相等；
物化后的墙检测状态机覆盖 连排墙 / 单行超长 / 干净 三态。
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HOOKED = REPO / "scripts" / "hook_check_md_blockquote.py"
sys.path.insert(0, str(REPO / "scripts"))

from hook_check_md_blockquote import find_walls  # noqa: E402


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, timeout=30)


def _bash_added_file(repo: Path, file: Path) -> str:
    """bash 共享 helper（post-checks.sh _pc_git_added_lines 的管线本体）输出内容。"""
    script = (
        'ADDED=$(mktemp)\n'
        'if git -C "$1" ls-files --error-unmatch "$2" >/dev/null 2>&1; then\n'
        '  git -C "$1" diff -U0 HEAD -- "$2" 2>/dev/null | grep \'^+\' | grep -v \'^+++\' | sed \'s/^+//\' > "$ADDED"\n'
        'else\n'
        '  cp "$2" "$ADDED"\n'
        'fi\n'
        'cat "$ADDED"; rm -f "$ADDED"\n'
    )
    r = subprocess.run(["bash", "-c", script, "bash", str(repo), str(file)],
                       capture_output=True, text=True, timeout=30)
    return r.stdout


def _py_added(repo: Path, file: Path) -> str:
    """原内嵌 python 的 added 抽取（hook_check_md_blockquote.added_lines_from_git）。"""
    from hook_check_md_blockquote import added_lines_from_git
    return "".join(f"{l}\n" for l in added_lines_from_git(str(file), str(repo)))


def _mk_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    return repo


def test_added_extraction_equivalence_across_git_states(tmp_path):
    """四种 git 状态：tracked 有 diff / tracked 无 diff / untracked / 全新增逐行对拍。"""
    repo = _mk_repo(tmp_path)
    # tracked 有 diff：HEAD 一行，工作区两行
    f1 = repo / "notes.md"
    f1.write_text("旧内容\n", encoding="utf-8")
    _git(repo, "add", "notes.md")
    _git(repo, "commit", "-q", "-m", "base")
    f1.write_text("旧内容\n新增引用行\n", encoding="utf-8")
    assert _bash_added_file(repo, f1) == _py_added(repo, f1) == "新增引用行\n"
    # tracked 无 diff：输出为空
    _git(repo, "add", "notes.md")
    _git(repo, "commit", "-q", "-m", "sync")
    assert _bash_added_file(repo, f1) == _py_added(repo, f1) == ""
    # untracked：全文
    f2 = repo / "new.md"
    f2.write_text("> 第一行\n普通行\n> 第二行\n", encoding="utf-8")
    assert _bash_added_file(repo, f2) == _py_added(repo, f2) == "> 第一行\n普通行\n> 第二行\n"
    # 全新增（tracked 但 HEAD 无该文件内容 = 首次 add 后未 commit）
    _git(repo, "add", "new.md")
    assert _bash_added_file(repo, f2) == _py_added(repo, f2)


def test_find_walls_three_states():
    """物化状态机：连排墙 / 单行超长 / 干净（与原内嵌逻辑同构三态）。"""
    walls, longs = find_walls(["> a", "> b", "正文"])
    assert len(walls) == 1 and walls[0] == ["> a", "> b"] and not longs
    walls, longs = find_walls(["正文", "> " + "长" * 121, "正文"])
    assert not walls and len(longs) == 1
    walls, longs = find_walls(["正文", "> 单行短引用", "正文"])
    assert not walls and not longs


def test_cli_stdout_contract(tmp_path):
    """CLI 形态：检出打 WALL 首行 + 明细；干净零输出（bash 侧靠这两个形态判定）。"""
    f = tmp_path / "n.md"
    f.write_text("x\n", encoding="utf-8")
    added = tmp_path / "added.txt"
    added.write_text("> a\n> b\n", encoding="utf-8")
    r1 = subprocess.run([sys.executable, str(HOOKED), str(f), "--added-file", str(added)],
                        capture_output=True, text=True, timeout=30)
    assert r1.returncode == 0 and r1.stdout.splitlines()[0] == "WALL"
    added.write_text("普通\n", encoding="utf-8")
    r2 = subprocess.run([sys.executable, str(HOOKED), str(f), "--added-file", str(added)],
                        capture_output=True, text=True, timeout=30)
    assert r2.returncode == 0 and r2.stdout == ""
