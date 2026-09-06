"""性能回归：PreToolUse hook 延迟 + 大文件压力（补 test-hooks.sh 的 huge transcript 盲区）。

为什么单独一层：
- test-hooks.sh 用 $SECONDS 整秒分辨率，亚秒 hook 全落 0ms，测不出性能回归。
- 这里用 time.perf_counter() 亚秒精确，建基线 + 阈值断言。

阈值收紧到基线 ×5-8（留 CI 慢机器余量）；校准重跑 `pytest test_perf.py --durations=10`。
"""
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HOOKS = REPO / ".claude" / "hooks"

# 阈值（ms）· 基线 @ 2026-06-21（macOS 本地）：pre-bash 130 / pre-read 40 / dispatcher 250 / checker 大文件 70
PRETOOLUSE_BUDGET_MS = 600    # pre-bash-guard / pre-read-bigfile 单次（基线 ×~5）
DISPATCHER_BUDGET_MS = 2000   # post-writeedit 全链路 14 pc_*（基线 ×8，留 dedup cache miss 余量）
CHECKER_LARGEFILE_MS = 1000   # 单 checker 处理 5000 行（基线 ×14，大文件波动大留余量）


def _run_hook(hook_rel: str, payload: str, timeout: float = 15):
    """跑一个 hook（CLAUDE_HOOK_TEST=1 隔离埋点），返回 (耗时 ms, exit code)。"""
    env = {**os.environ, "CLAUDE_HOOK_TEST": "1"}
    t0 = time.perf_counter()
    r = subprocess.run(
        ["bash", str(HOOKS / hook_rel)],
        input=payload, capture_output=True, text=True, timeout=timeout, env=env,
    )
    return (time.perf_counter() - t0) * 1000, r.returncode


def test_pre_bash_guard_latency():
    payload = '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'
    dt, rc = _run_hook("pre-bash-guard.sh", payload)
    assert rc == 0, f"放行命令应 exit 0，实际 {rc}"
    assert dt < PRETOOLUSE_BUDGET_MS, f"pre-bash-guard {dt:.0f}ms > {PRETOOLUSE_BUDGET_MS}ms"


def test_pre_read_bigfile_latency(tmp_path):
    f = tmp_path / "small.txt"
    f.write_text("hi\n", encoding="utf-8")
    payload = '{"tool_name":"Read","tool_input":{"file_path":"%s"}}' % f
    dt, rc = _run_hook("pre-read-bigfile.sh", payload)
    assert rc == 0
    assert dt < PRETOOLUSE_BUDGET_MS, f"pre-read-bigfile {dt:.0f}ms > budget"


def test_dispatcher_latency(tmp_path):
    # 正常 prd → dispatcher 跑全链路 14 pc_*，不 block，耗时 < 预算
    d = tmp_path / "proj" / "deliverables"
    d.mkdir(parents=True)
    f = d / "prd-perf.md"
    f.write_text("# t\n\n用户完成签到后获得奖励。\n", encoding="utf-8")
    payload = '{"tool_name":"Edit","tool_input":{"file_path":"%s"}}' % f
    dt, _rc = _run_hook("post-writeedit-dispatch.sh", payload, timeout=30)
    assert dt < DISPATCHER_BUDGET_MS, f"dispatcher 全链路 {dt:.0f}ms > {DISPATCHER_BUDGET_MS}ms"


def test_checker_large_file(tmp_path):
    """大文件压力（补 huge 盲区）：check_static_chapter.check_file 处理 5000 行 < 阈值。"""
    from check_static_chapter import check_file
    big = tmp_path / "big.md"
    big.write_text("# t\n\n## 1. 现状\n" + "用户完成签到后获得奖励。\n" * 5000, encoding="utf-8")
    t0 = time.perf_counter()
    check_file(big)
    dt = (time.perf_counter() - t0) * 1000
    assert dt < CHECKER_LARGEFILE_MS, f"check_static_chapter 大文件 {dt:.0f}ms > {CHECKER_LARGEFILE_MS}ms"


def test_analyze_gate_funnel_runs():
    """层 C：analyze 能跑 + 慢闸段标题在（dispatcher dur_ms 已埋点，数据随运行累积）。"""
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts/analyze_gate_funnel.py"), "--days", "7"],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, f"analyze 应 exit 0，实际 {r.returncode}\n{r.stderr}"
    assert "慢闸" in r.stdout, "analyze 输出应含慢闸段"
