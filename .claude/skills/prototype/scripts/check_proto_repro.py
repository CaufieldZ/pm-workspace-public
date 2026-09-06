#!/usr/bin/env python3
"""原型可复现性检查：已交付产物能否从当前 src/ 原样重建。

共享场景库（`projects/{产品线}/scripts/src/registry.py`）让多个 delta 版本复用同一份
场景实现 —— 复用是要的，代价是改共享层会静默改掉其他版本的产物。本检查把「潜伏的
污染」翻出来：逐个 build_proto_v*.py 重建到临时目录，与 deliverables/ 下已交付的
HTML 逐字节比对，不一致即报。

每个 build 脚本跑在独立子进程里（`src.build._PROJECT` 改道 tmp），不碰已交付产物。

封版豁免：`.proto-lock.json` 带 `frozen=true` 的版本跳过比对（已决策不重建，
见 .claude/decisions/implemented/2026-08-25-proto-drift-frozen.md）。

用法：
    python3 .claude/skills/prototype/scripts/check_proto_repro.py             # 全部产线
    python3 .claude/skills/prototype/scripts/check_proto_repro.py livestream  # 指定产线
    python3 .claude/skills/prototype/scripts/check_proto_repro.py --strict    # 漂移则 exit 2

退出码：
    0 — 无漂移 / 有漂移但未传 --strict（warn）
    2 — 传 --strict 且有漂移
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from lib.repo import find_root  # noqa: E402

# 子进程模板：把产物出口改道 tmp 后按原样跑 build 脚本。
# sys.argv[0] 必须指向真实 build 脚本 —— 产物头部注释会嵌入源脚本名，
# 不改 argv 会让每个文件都因为那一行注释假阳。
_RUNNER = """\
import sys, runpy
sys.path.insert(0, {scripts_dir!r})
import src.build as B
B._PROJECT = {tmp!r}
sys.argv = [{script!r}]
runpy.run_path({script!r}, run_name='__main__')
"""


def find_shared_lib_projects(repo_root: Path) -> list[Path]:
    """有共享场景库的产线目录（存在 scripts/src/registry.py）。"""
    return sorted(
        p.parents[2]
        for p in (repo_root / "projects").rglob("scripts/src/registry.py")
        if "archive" not in p.parts
    )


def rebuild_to_tmp(project_dir: Path, tmp: Path) -> list[str]:
    """跑该产线全部 build_proto_v*.py，产物落 tmp。返回失败脚本的报错摘要。"""
    scripts_dir = project_dir / "scripts"
    errors = []
    for script in sorted(scripts_dir.glob("build_proto_v*.py")):
        code = _RUNNER.format(scripts_dir=str(scripts_dir), tmp=str(tmp), script=str(script))
        r = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, cwd=str(scripts_dir)
        )
        if r.returncode != 0:
            tail = (r.stderr or "").strip().splitlines()
            errors.append(f"{script.name} 重建失败：{tail[-1] if tail else '未知错误'}")
    return errors


def frozen_versions(project_dir: Path) -> set[str]:
    """该产线已封版的版本目录名（.proto-lock.json frozen=true）。"""
    frozen = set()
    for lock in (project_dir / "deliverables").rglob(".proto-lock.json"):
        try:
            data = json.loads(lock.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("frozen"):
            frozen.add(lock.parent.name)
    return frozen


def compare(tmp: Path, project_dir: Path) -> tuple[list[str], list[str], list[str]]:
    """比对 tmp 重建产物与已交付产物，返回 (漂移明细, 一致文件名, 豁免版本)。"""
    frozen = frozen_versions(project_dir)
    drift: list[str] = []
    same: list[str] = []
    exempt: list[str] = []
    for built in sorted((tmp / "deliverables").rglob("proto-*.html")):
        rel = built.relative_to(tmp)
        if rel.parts[2] in frozen:
            exempt.append(rel.parts[2])
            continue
        real = project_dir / rel
        if not real.is_file():
            archived = project_dir / "deliverables" / "archive" / real.relative_to(project_dir / "deliverables")
            if archived.is_file():
                exempt.append(f"{rel.parts[2]}（已归档）")
                continue
            drift.append(f"{rel} —— 重建出来了但 deliverables/ 下没有（漏提交？）")
            continue
        a = real.read_text(encoding="utf-8", errors="replace").splitlines()
        b = built.read_text(encoding="utf-8", errors="replace").splitlines()
        if a == b:
            same.append(real.name)
        else:
            delta = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
            drift.append(f"{rel} —— 重建与已交付差 {delta} 行")
    return drift, same, exempt


def check(project_dir: Path) -> tuple[list[str], list[str], list[str]]:
    """重建 + 比对，返回 (漂移明细, 一致文件名, 封版豁免版本)。"""
    with tempfile.TemporaryDirectory(prefix="proto-repro-") as td:
        tmp = Path(td)
        errors = rebuild_to_tmp(project_dir, tmp)
        if errors:
            return errors, [], []
        return compare(tmp, project_dir)


def main() -> int:
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0
    strict = "--strict" in args
    wanted = [a for a in args if not a.startswith("-")]

    repo_root = find_root()
    projects = find_shared_lib_projects(repo_root)
    if wanted:
        projects = [p for p in projects if p.name in wanted]
    if not projects:
        print("· 无共享场景库产线（projects/**/scripts/src/registry.py），skip")
        return 0

    any_drift = False
    for pd in projects:
        drift, same, exempt = check(pd)
        print(f"\n── {pd.relative_to(repo_root)} ──")
        if not drift and not exempt:
            print(f"  🟢 {len(same)} 个已交付原型均可从当前 src/ 原样重建")
            continue
        if exempt:
            print(f"  ⊘ {len(set(exempt))} 个版本豁免（.proto-lock.json frozen=true 封版 / deliverables/archive/ 整包归档）")
        if not drift:
            continue
        any_drift = True
        print(f"  🟡 {len(drift)} 个产物漂移（{len(same)} 个一致）—— "
              "改共享 src/ 影响了这些版本，重建前先确认是否有意：")
        for d in drift:
            print(f"    · {d}")

    return 2 if (any_drift and strict) else 0


if __name__ == "__main__":
    sys.exit(main())
