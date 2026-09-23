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

import pytest

REPO = Path(__file__).resolve().parents[2]
HOOKS = REPO / ".claude" / "hooks"

# 阈值（ms）· 基线 @ 2026-06-21（macOS 本地）：pre-bash 130 / pre-read 40 / dispatcher 250 / checker 大文件 70
# 复测 @ 2026-09-13：pre-bash 15 / pre-read 18 / dispatcher 935（处置见 decisions/2026-09-13-hotpath-fixed-cost.md）。
# 复测 @ 2026-09-23（合批轮后，沙箱四路径三轮中位）：delta ~744 / baseline ~467 / scene-list ~401
# / notes ~309（before ~1100/580/490/370）；机制与 go/no-go 见 decisions/2026-09-23-pc-batch-mechanism.md。
# 预算线不动——它的作用是「撞线即红」，不是追平最新实测。
PRETOOLUSE_BUDGET_MS = 600    # pre-bash-guard / pre-read-bigfile 单次（基线 ×~5）
DISPATCHER_BUDGET_MS = 2000   # post-writeedit 全链路 14 pc_*（基线 ×8，留 dedup cache miss 余量）
CHECKER_LARGEFILE_MS = 1000   # 单 checker 处理 5000 行（基线 ×14，大文件波动大留余量）


def _run_hook(hook_rel: str, payload: str, timeout: float = 15, extra_env: dict | None = None):
    """跑一个 hook（CLAUDE_HOOK_TEST=1 隔离埋点），返回 (耗时 ms, exit code)。

    extra_env 可注入 CLAUDE_PROJECT_DIR / TMPDIR（沙箱工区 / dedup 缓存隔离）。
    """
    env = {**os.environ, "CLAUDE_HOOK_TEST": "1", **(extra_env or {})}
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


# ── 四路径锚定（沙箱工区）─────────────────────────────────────────────
# 背景：上面 tmp_path 路径不含 /projects/，产线三查 / audit-fast / cross-check 全静默
# skip，测不到写盘路径真实成本（决策文档实测 delta PRD 937 / baseline 675 /
# scene-list 445ms）。此处建一次性沙箱工区（.claude / scripts 软链真仓，projects/
# 自造 liveline），让这些分支真实触发。TMPDIR 指向一次性目录隔离 dedup 缓存与
# warn-hash 抑制（手法同 test-hooks.sh 的 run_post_json），保证 TTL 门必跑。
# 预算断言沿用 DISPATCHER_BUDGET_MS；各路径耗时印进 pytest 输出作 before/after 对照。


def _mk_ws_sandbox(tmp_path):
    """一次性沙箱工区：软链 .claude + scripts，自造产品线 liveline 四类 fixture。"""
    sbx = tmp_path / "ws"
    pl = sbx / "projects" / "liveline"
    (pl / "deliverables" / "2026Q3" / "2.3").mkdir(parents=True)
    sbx.joinpath(".claude").symlink_to(REPO / ".claude")
    sbx.joinpath("scripts").symlink_to(REPO / "scripts")
    # baseline：带 changelog 章的极简真相源（产线三查的入口条件是产品线根有 prd-*-baseline.md）
    (pl / "prd-liveline-baseline.md").write_text(
        "# Live Line PRD Baseline\n\n## 1. 现状\n\n用户完成签到后获得奖励。\n\n## 9. 版本历史\n\n| 日期 | 版本 | 状态 |\n| --- | --- | --- |\n",
        encoding="utf-8")
    # scene-list：编号唯一的最小表（scene-list-gate 只拦重复编号）
    (pl / "scene-list.md").write_text(
        "# 场景清单\n\n| 编号 | 场景 | 描述 |\n| --- | --- | --- |\n| A-1 | 签到 | 用户完成签到后获得奖励 |\n| B-1 | 领奖 | 用户在奖品中心领取奖励 |\n",
        encoding="utf-8")
    # delta PRD：deliverables/{季度}/{版本}/prd-{产品线}-{版本}.md 标准落点。
    # 正文须引用 scene-list 全部编号（audit-fast 全覆盖校验：scene-list ⊆ 产物）
    (pl / "deliverables" / "2026Q3" / "2.3" / "prd-liveline-2.3.md").write_text(
        "# Live Line 2.3 PRD\n\n## 1. 目标\n\n用户完成签到后获得奖励。\n\n## 4. 需求详述\n\n### 4.1 签到（A-1）\n\n用户完成签到后获得奖励。\n\n### 4.2 领奖（B-1）\n\n用户在奖品中心领取奖励。\n",
        encoding="utf-8")
    # 通用项目 md（非 baseline / scene-list / deliverables：只走 cjk + learned + 引用墙 + 挤话）
    (pl / "notes.md").write_text("# 备忘\n\n用户完成签到后获得奖励。\n", encoding="utf-8")
    tmpdir = tmp_path / "tmpdir-isolated"
    tmpdir.mkdir()
    env = {"CLAUDE_PROJECT_DIR": str(sbx), "TMPDIR": str(tmpdir)}
    return sbx, env


@pytest.mark.parametrize("rel", [
    "projects/liveline/deliverables/2026Q3/2.3/prd-liveline-2.3.md",  # delta PRD
    "projects/liveline/prd-liveline-baseline.md",                      # baseline
    "projects/liveline/scene-list.md",                                 # scene-list
    "projects/liveline/notes.md",                                      # 通用项目 md
])
def test_dispatcher_latency_paths(tmp_path, rel):
    sbx, env = _mk_ws_sandbox(tmp_path)
    payload = '{"tool_name":"Edit","tool_input":{"file_path":"%s"}}' % (sbx / rel)
    dt, rc = _run_hook("post-writeedit-dispatch.sh", payload, timeout=30, extra_env=env)
    assert rc == 0, f"{rel} 干净 fixture 应放行（exit 0），实际 {rc}"
    assert dt < DISPATCHER_BUDGET_MS, f"{rel} {dt:.0f}ms > {DISPATCHER_BUDGET_MS}ms"
    print(f"\n[perf-path] {rel}: {dt:.0f}ms")  # noqa: T201  before/after 对照锚点


def test_checker_large_file(tmp_path):
    """大文件压力（补 huge 盲区）：check_static_chapter.check_file 处理 5000 行 < 阈值。"""
    from check_static_chapter import check_file
    big = tmp_path / "big.md"
    big.write_text("# t\n\n## 1. 现状\n" + "用户完成签到后获得奖励。\n" * 5000, encoding="utf-8")
    t0 = time.perf_counter()
    check_file(big)
    dt = (time.perf_counter() - t0) * 1000
    assert dt < CHECKER_LARGEFILE_MS, f"check_static_chapter 大文件 {dt:.0f}ms > {CHECKER_LARGEFILE_MS}ms"


def test_telemetry_funnel_runs():
    """层 C：analyze 能跑 + 慢闸段标题在（dispatcher dur_ms 已埋点，数据随运行累积）。"""
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts/telemetry.py"), "funnel", "--days", "7"],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, f"analyze 应 exit 0，实际 {r.returncode}\n{r.stderr}"
    assert "慢闸" in r.stdout, "analyze 输出应含慢闸段"
