#!/usr/bin/env python3
"""并行 delta 冲突检测（在途 delta 间的反向合并目标重叠提示）。

check_baseline_fresh.py 只验「单个 delta vs baseline」。本脚本补「delta vs delta」：
同一产品线下多个在途 delta（changelog 状态 ≠「已合并」）若触及同一 baseline 目标
（场景编号 / 支柱章），反向合并时存在顺序依赖与潜在矛盾——机械检测目标重叠，报黄灯
「人工核对」，不判定真矛盾（§9 合并动作是自由文本，无 ADDED/MODIFIED/REMOVED 语义）。

用法：
    python3 scripts/check_delta_conflict.py livestream

退出码：恒 0（warn 级，供 hook / dashboard 调）。结构化结论走 stdout。
非 baseline 项目 / 在途 delta < 2 → skip。SKIP_DELTA_CONFLICT=1 整体跳过。
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_baseline_fresh import _find_baseline, parse_changelog  # noqa: E402
from lib.repo import find_root  # noqa: E402
from lib.scene_match import extract_referenced_ids  # noqa: E402

# 无编号支柱 / 特殊章关键词（业务对象 / 状态机 / 全局规则 / 埋点 / 术语）
_PILLAR_KW = ("埋点契约", "术语", "业务对象", "状态机", "全局规则")
# 行内反向合并语境（§2.0 索引表 / 正文「反向合并目标：…」段）
_MERGE_CTX = ("反向合并", "目标章", "基线目标")
# §9 反向合并指引章标题（章内每行都算合并语境，覆盖表 data 行不含 context 词的情况）
_MERGE_SECTION = re.compile(r"^#{1,4}\s+\d*\.?\s*反向合并指引")
_H1 = re.compile(r"^#{1,4}\s")


def extract_targets(delta_text: str) -> tuple[set[str], set[str]]:
    """抽该 delta 触及的 (场景编号集, 支柱章集)。

    场景编号复用 scene_match.extract_referenced_ids（A-2 / B-6 / D-5，连字符形态，噪音低）；
    支柱章名在 §9 反向合并章内（含表 data 行）或行内反向合并语境命中，正文偶提不收。
    """
    scenes = set(extract_referenced_ids(delta_text))

    pillars: set[str] = set()
    in_merge_section = False
    for line in delta_text.splitlines():
        if _MERGE_SECTION.match(line):
            in_merge_section = True
            continue
        if in_merge_section and _H1.match(line):
            in_merge_section = False
        ctx = in_merge_section or any(c in line for c in _MERGE_CTX)
        if not ctx:
            continue
        for kw in _PILLAR_KW:
            if kw in line:
                pillars.add(kw)
    return scenes, pillars


def find_overlaps(
    targets: dict[str, tuple[set[str], set[str]]],
) -> list[tuple[str, str, list[str]]]:
    """两两求场景编号 + 支柱章交集，返回 [(a, b, [共同项...]), ...]。

    同一版本的分端文档（`2026Q3/2.3#app` 与 `2026Q3/2.3#main`）属同一个 delta 包、
    一起反向合并，不是并行冲突 —— 按 `#` 前的版本键判同源，跳过。
    """
    out: list[tuple[str, str, list[str]]] = []
    for a, b in combinations(sorted(targets), 2):
        if a.split("#", 1)[0] == b.split("#", 1)[0]:
            continue
        sc_a, pl_a = targets[a]
        sc_b, pl_b = targets[b]
        shared = sorted(sc_a & sc_b) + sorted(pl_a & pl_b)
        if shared:
            out.append((a, b, shared))
    return out


def _short(delta_path: Path) -> str:
    """delta 短名：版本目录（如 2.1.1）优先，否则文件名去 prd- 前缀。"""
    parent = delta_path.parent.name
    if re.fullmatch(r"[0-9][\w.]*", parent):
        return parent
    return delta_path.stem.replace("prd-", "")


def _variant(delta_path: Path) -> str:
    """delta 文件名里版本号之后的区分段（`prd-livestream-2.3-web` → `web`）；无则 `main`。"""
    m = re.match(r"^prd-.+?-\d[\w.]*(?:-(.+))?$", delta_path.stem)
    return m.group(1) if m and m.group(1) else "main"


def _unique_shorts(paths: list[Path]) -> dict[Path, str]:
    """给每个 delta 路径分配唯一显示名。

    短名不撞时直接用 `_short`；撞键的走两级消歧：先加季度目录前缀（跨季度同名版本
    目录，如两个季度都有 `2.1/`），仍撞的再加文件名区分段（同一版本目录下多份 delta，
    如 `2.3/` 下的主体 + `-app` + `-web` + `-web-tracking`）。任一级漏掉都会让 dict
    折叠、某个 delta 被静默丢弃、并行冲突漏检。
    """
    shorts = [_short(p) for p in paths]
    collided = {s for s in shorts if shorts.count(s) > 1}
    out: dict[Path, str] = {}
    for p, s in zip(paths, shorts, strict=True):
        out[p] = f"{p.parent.parent.name}/{s}" if s in collided else s

    names = list(out.values())
    still = {n for n in names if names.count(n) > 1}
    for p, n in list(out.items()):
        if n in still:
            out[p] = f"{n}#{_variant(p)}"
    return out


def _in_flight_deltas(project_dir: Path, changelog: dict[str, str]) -> list[Path]:
    """在途 delta：deliverables/ 下（不含 archive），changelog 状态 ≠「已合并」。"""
    deliverables = project_dir / "deliverables"
    if not deliverables.is_dir():
        return []
    archive = deliverables / "archive"
    return [
        p for p in deliverables.rglob("prd-*.md")
        if "baseline" not in p.name
        and archive not in p.parents
        and changelog.get(p.name) != "已合并"
    ]


def check(project: str, repo_root: Path) -> int:
    project_dir = repo_root / "projects" / project
    if not project_dir.is_dir():
        print(f"⚠ 项目目录不存在：{project_dir}")
        return 0

    baseline = _find_baseline(project_dir)
    if baseline is None:
        print(f"· {project}：非 baseline 项目（无 prd-*-baseline.md），skip")
        return 0

    changelog = parse_changelog(baseline.read_text(encoding="utf-8"))
    in_flight = sorted(_in_flight_deltas(project_dir, changelog))

    if len(in_flight) < 2:
        print(f"· {project}：在途 delta {len(in_flight)} 个（< 2），无并行冲突可查，skip")
        return 0

    names = _unique_shorts(in_flight)
    targets = {
        names[p]: extract_targets(p.read_text(encoding="utf-8", errors="replace"))
        for p in in_flight
    }
    # 显示名撞键会让 dict 静默折叠、delta 被丢弃 —— 宁可炸也不给漏检的结论
    if len(targets) != len(in_flight):
        dupes = sorted({n for n in names.values() if list(names.values()).count(n) > 1})
        raise AssertionError(
            f"显示名不唯一，{len(in_flight)} 个 delta 折叠成 {len(targets)} 个键："
            f"{dupes} —— _unique_shorts 消歧不足，冲突检测结论不可信"
        )

    print(f"baseline: {baseline.relative_to(repo_root)}")
    print(f"在途 delta: {len(in_flight)} 个")
    for name, (sc, pl) in targets.items():
        print(f"  · {name}：场景 {len(sc)} 个 / 支柱章 {len(pl)} 个")

    overlaps = find_overlaps(targets)
    if overlaps:
        print(f"\n🟡 并行 delta 目标重叠（{len(overlaps)} 组）—— 反向合并前核对合并顺序与是否矛盾：")
        for a, b, shared in overlaps:
            print(f"  🟡 {a} ∩ {b} 共同触及：{', '.join(shared)}")
    else:
        print(f"\n🟢 {len(in_flight)} 个在途 delta 目标互不重叠")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="并行 delta 冲突检测")
    ap.add_argument("project", help="项目 / 产品线路径片段，如 livestream")
    args = ap.parse_args()
    if os.environ.get("SKIP_DELTA_CONFLICT"):
        print("· SKIP_DELTA_CONFLICT 已设，跳过")
        return 0
    return check(args.project, find_root())


if __name__ == "__main__":
    sys.exit(main())
