"""hook_py_batch（Write|Edit 检查器合批运行器）等价性与崩溃语义测试。

等价性判据（decisions 纪律「集合守恒 / 逐字节」）：对同一 argv，
「子进程直跑（今天 bash 的方式）」与「批量帧」的 (退出码, stdout+stderr 合并输出)
必须逐字节相等。跑的是同一份代码对象，任何差异都是批量层的 bug。
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
RUNNER = REPO / "scripts" / "hook_py_batch.py"
sys.path.insert(0, str(REPO / "scripts" / "tests"))

from test_perf import REPO as _R  # noqa: E402  复用仓库根（同目录 conftest 已注入 sys.path）


def run_direct(argv: list[str]) -> tuple[int, str]:
    """A 侧：今天 bash 的方式——独立子进程按原始 argv 直跑，合并捕获。"""
    r = subprocess.run([sys.executable, *argv], capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout + r.stderr


def run_batch(slots: list[tuple[str, list[str]]], out_dir: Path) -> int:
    """B 侧：spool → 批量运行器。返回 runner 退出码。"""
    spool = "".join(f"{s}\n{len(a)}\n" + "".join(f"{x}\n" for x in a) for s, a in slots)
    r = subprocess.run(
        [sys.executable, str(RUNNER), str(out_dir)],
        input=spool, capture_output=True, text=True, timeout=60,
    )
    return r.returncode


def _read(out_dir: Path, slot: str, suffix: str) -> str:
    return (out_dir / f"{slot}.{suffix}").read_text(encoding="utf-8")


# ── 真实 checker 的 A/B 逐字节对拍 ──────────────────────────────────────

LEARNED = str(REPO / "scripts" / "check_learned_rules.py")
PLAIN = str(REPO / "scripts" / "check_plain_language.py")

AB_CASES = [
    # (slot, checker, argv 尾参, fixture 内容)——干净 / 触发判定路径的对抗文本各一
    ("learned", LEARNED, [], "# 备忘\n\n用户完成签到后获得奖励。\n"),
    ("learned", LEARNED, [], "# 备忘\n\n参见决策 7，[LEARN] 占位 [待补充]。\n"),
    ("plain", PLAIN, ["--strict"], "# 备忘\n\n用户完成签到后获得奖励。\n"),
    ("plain", PLAIN, ["--strict"], "# 备忘\n\n本方案 A-1 落地后参见决策 7。[待补充]\n"),
    ("plain", PLAIN, ["--strict", "--added-only"], "# 备忘\n\n本方案 A-1 落地后参见决策 7。[待补充]\n"),
]


@pytest.mark.parametrize("slot,checker,tail,content", AB_CASES)
def test_ab_byte_equal_real_checkers(tmp_path, slot, checker, tail, content):
    f = tmp_path / f"{slot}.md"
    f.write_text(content, encoding="utf-8")
    argv = [checker, str(f), *tail]
    rc_a, out_a = run_direct(argv)
    out_dir = tmp_path / "batch"
    assert run_batch([(slot, argv)], out_dir) == 0
    rc_b = int(_read(out_dir, slot, "rc"))
    out_b = _read(out_dir, slot, "all")
    assert rc_b == rc_a, f"rc 不等: 直跑 {rc_a} vs 批量 {rc_b}"
    assert out_b == out_a, f"合并输出不等:\n--直跑--\n{out_a!r}\n--批量--\n{out_b!r}"


# ── PRD 内容门的 A/B 对拍（argv 带 --added-file 双参形态）────────────────

PRD_CONTENT = str(REPO / "scripts" / "hook_check_prd_content.py")

PRD_AB_CASES = [
    # (slot, md 内容, 新增行清单)——干净 / 触发判定路径各一
    ("prd_clean", "# 1. 背景\n\n- 用户点分享出面板\n", "- 用户点分享出面板\n"),
    ("prd_hit", "# 1. 背景\n\n- 鼠标 hover 时展示浮层\n", "- 鼠标 hover 时展示浮层\n"),
]


@pytest.mark.parametrize("slot,content,added", PRD_AB_CASES)
def test_ab_byte_equal_prd_content_checker(tmp_path, slot, content, added):
    f = tmp_path / "prd-demo-v1.md"
    f.write_text(content, encoding="utf-8")
    added_file = tmp_path / "added.txt"
    added_file.write_text(added, encoding="utf-8")
    argv = [PRD_CONTENT, str(f), "--added-file", str(added_file)]
    rc_a, out_a = run_direct(argv)
    out_dir = tmp_path / "batch"
    assert run_batch([(slot, argv)], out_dir) == 0
    rc_b = int(_read(out_dir, slot, "rc"))
    out_b = _read(out_dir, slot, "all")
    assert rc_b == rc_a, f"rc 不等: 直跑 {rc_a} vs 批量 {rc_b}"
    assert out_b == out_a, f"合并输出不等:\n--直跑--\n{out_a!r}\n--批量--\n{out_b!r}"


# ── 产线三查的 A/B 对拍（argv 形态 = [checker, 产品线]）──────────────────

LINE_CHECKERS = [
    ("line_bf", str(REPO / "scripts" / "check_baseline_fresh.py"), ["livestream"]),
    ("line_dc", str(REPO / "scripts" / "check_delta_conflict.py"), ["livestream"]),
    ("line_rvd", str(REPO / "scripts" / "check_rule_version_drift.py"), ["livestream"]),
]


@pytest.mark.parametrize("slot,checker,tail", LINE_CHECKERS)
def test_ab_byte_equal_line_checkers(tmp_path, slot, checker, tail):
    """产线三查只读扫描真实 livestream 产品线，直跑 vs 批量逐字节相等。"""
    argv = [checker, *tail]
    rc_a, out_a = run_direct(argv)
    out_dir = tmp_path / "batch"
    assert run_batch([(slot, argv)], out_dir) == 0
    assert int(_read(out_dir, slot, "rc")) == rc_a
    assert _read(out_dir, slot, "all") == out_a, f"{slot} 输出不等:\n{out_a!r}\nvs\n{_read(out_dir, slot, 'all')!r}"


# ── 崩溃 / 退出码语义 ──────────────────────────────────────────────────

def test_systemexit_code_and_main_return(tmp_path):
    """sys.exit(2) 与 main() 返回 None→0、返回 int 原样透传。"""
    mk = tmp_path / "mk.py"
    mk.write_text(
        'import sys\ndef main():\n    if sys.argv[1] == "a":\n        sys.exit(2)\n'
        '    if sys.argv[1] == "b":\n        return None\n    return 3\n'
        'if __name__ == "__main__":\n    sys.exit(main())\n', encoding="utf-8")
    out_dir = tmp_path / "o"
    assert run_batch([("s1", [str(mk), "a"]), ("s2", [str(mk), "b"]), ("s3", [str(mk), "c"])], out_dir) == 0
    assert int(_read(out_dir, "s1", "rc")) == 2
    assert int(_read(out_dir, "s2", "rc")) == 0
    assert int(_read(out_dir, "s3", "rc")) == 3


def test_uncaught_exception_rc1_with_traceback(tmp_path):
    """未捕获异常 → rc=1 + traceback 进合并输出（等价今天进程崩溃后 bash 拿到的输出面）。"""
    boom = tmp_path / "boom.py"
    boom.write_text("def main():\n    raise ValueError('boom-标记串')\n\nif __name__ == '__main__':\n    raise SystemExit(main())\n", encoding="utf-8")
    out_dir = tmp_path / "o"
    assert run_batch([("x", [str(boom)])], out_dir) == 0
    assert int(_read(out_dir, "x", "rc")) == 1
    assert "ValueError" in _read(out_dir, "x", "all") and "boom-标记串" in _read(out_dir, "x", "all")


def test_slot_isolation(tmp_path):
    """一槽崩溃不连坐：后继槽照常跑完。"""
    boom = tmp_path / "boom.py"
    boom.write_text("def main():\n    raise RuntimeError('x')\n", encoding="utf-8")
    ok = tmp_path / "ok.py"
    ok.write_text("def main():\n    print('ok-输出')\n    return 0\n", encoding="utf-8")
    out_dir = tmp_path / "o"
    assert run_batch([("bad", [str(boom)]), ("good", [str(ok)])], out_dir) == 0
    assert int(_read(out_dir, "bad", "rc")) == 1
    assert int(_read(out_dir, "good", "rc")) == 0
    assert _read(out_dir, "good", "all") == "ok-输出\n"


# ── spool 解析（人为破坏面：截断 / 非法槽名 / 非法 argc）────────────────

def test_parse_spool_rejects_broken():
    from hook_py_batch import parse_spool
    assert parse_spool("a\n1\nx\n") == [("a", ["x"])]
    assert parse_spool("a\n0\n") == [("a", [])]
    with pytest.raises(ValueError):
        parse_spool("a\n2\nx\n")          # argc 越界（截断）
    with pytest.raises(ValueError):
        parse_spool("a-b\n1\nx\n")        # 非法槽名
    with pytest.raises(ValueError):
        parse_spool("a\nn\nx\n")          # argc 非数字
    assert parse_spool("") == []          # 空槽清单 = 零槽批次，合法（_pc_flush 上游已挡空跑）


# ── bash 侧 _pc_flush 协议（lib/pybatch.sh）────────────────────────────

def test_pc_flush_fills_defaults_on_runner_failure(tmp_path):
    """runner 起不来（PROJECT_DIR 指向不存在的 scripts）→ 全槽 rc=1 + 空 all 文件。"""
    script = (
        'source "' + str(REPO / ".claude/hooks/lib/pybatch.sh") + '"\n'
        'PROJECT_DIR="' + str(tmp_path) + '"\n'  # tmp_path/scripts/hook_py_batch.py 不存在
        '_pc_enqueue t1 "' + LEARNED + '" /dev/null\n'
        '_pc_enqueue t2 "' + LEARNED + '" /dev/null\n'
        '_pc_flush\n'
        'printf "rc=%s|%s all_bytes=%s|%s\\n" "$_PC_RC_t1" "$_PC_RC_t2" '
        '"$(wc -c < "$_PC_ALL_t1" | tr -d \\ )" "$(wc -c < "$_PC_ALL_t2" | tr -d \\ )"\n'
    )
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0
    assert "rc=1|1" in r.stdout, r.stdout
    assert "all_bytes=0|0" in r.stdout, r.stdout


def test_pc_flush_roundtrip_real_checker(tmp_path):
    """bash 排队 → flush → 读回变量，与 A 侧直跑一致（覆盖 bash↔python 协议两端）。"""
    f = tmp_path / "f.md"
    f.write_text("# 备忘\n\n用户完成签到后获得奖励。\n", encoding="utf-8")
    script = (
        'source "' + str(REPO / ".claude/hooks/lib/pybatch.sh") + '"\n'
        'PROJECT_DIR="' + str(REPO) + '"\n'
        '_pc_enqueue learned "' + LEARNED + '" "' + str(f) + '"\n'
        '_pc_flush\n'
        'printf "rc=%s dur=%s out=" "$_PC_RC_learned" "$_PC_DUR_MS_learned"\n'
        'cat "$_PC_ALL_learned"\n'
    )
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=60)
    rc_a, out_a = run_direct([LEARNED, str(f)])
    assert r.returncode == 0
    assert f"rc={rc_a} " in r.stdout
    assert r.stdout.split("out=", 1)[1] == out_a
