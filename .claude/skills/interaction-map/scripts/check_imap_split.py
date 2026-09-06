#!/usr/bin/env python3
"""interaction-map src/scenes 分场景拆分门

规则源：.claude/skills/interaction-map/SKILL.md §硬规则「src/scenes 分场景拆分（强制）」
  每个 IMAP 必须把 scene_fns 拆为 scripts/src/scenes/{scene_id}.py 一文件一主场景，
  由 build_imap_v{N}.py orchestrator import 收口。禁止把 scene_fns 内联在 orchestrator
  单文件里。generate() 对 scene_fns 如何组装是 agnostic 的，所以拆分只能在 imap-*.html
  产出层兜底校验：找不到任何 src/scenes/*.py 即视为未拆（内联）→ FAIL。

用法：
    python3 .claude/skills/interaction-map/scripts/check_imap_split.py <imap.html>...
    [--strict]  # hook 用，命中 exit 2 阻断；否则 exit 1

退出码：
    0 — 找到 src/scenes/*.py（已拆分）
    1 — 未拆分但未传 --strict
    2 — 传 --strict 且未拆分
"""
import argparse
import sys
from pathlib import Path

# 从 imap-*.html 向上找 build 脚本目录的最大层数
# 覆盖两种落点：① delta 包同级 deliverables/{季度}/{版本}/scripts/
#              ② 项目根 projects/{项目}/scripts/
_MAX_UP = 6


def _has_scene_files(scenes_dir: Path) -> bool:
    """src/scenes 目录里有 ≥1 个真实场景 .py（排除 __init__.py）"""
    if not scenes_dir.is_dir():
        return False
    return any(p.name != "__init__.py" for p in scenes_dir.glob("*.py"))


def find_split(html_path: Path):
    """从 html 路径向上收集候选 scripts 目录，命中 src/scenes/*.py 返回该目录。

    返回 (found_dir | None, checked_dirs)。
    """
    checked = []
    base = html_path.parent
    for _ in range(_MAX_UP + 1):
        for scenes in (base / "scripts" / "src" / "scenes", base / "src" / "scenes"):
            checked.append(scenes)
            if _has_scene_files(scenes):
                return scenes, checked
        if base.parent == base:  # 到达文件系统根
            break
        base = base.parent
    return None, checked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    violations = 0
    for f in args.files:
        html_path = Path(f).resolve()
        if html_path.suffix.lower() != ".html":
            continue
        found, checked = find_split(html_path)
        if found:
            continue
        violations += 1
        print(f"\n{html_path} — 未找到 src/scenes 分场景拆分", file=sys.stderr)
        print("  已查候选目录：", file=sys.stderr)
        for d in checked:
            print(f"    - {d}", file=sys.stderr)

    if violations:
        print("", file=sys.stderr)
        print("❌ IMAP scene_fns 未拆分到 src/scenes/。", file=sys.stderr)
        print("   规则：每个 IMAP 必须拆 scripts/src/scenes/{scene_id}.py", file=sys.stderr)
        print("   一文件一主场景（≤300 行），由 build_imap_v{N}.py import 收口，禁内联。", file=sys.stderr)
        print("   拆分结构见 .claude/runbooks/html-build-split.md §二。", file=sys.stderr)
        print("   临时绕过：SKIP_IMAP_SPLIT_GATE=1", file=sys.stderr)

    if violations == 0:
        sys.exit(0)
    sys.exit(2 if args.strict else 1)


if __name__ == "__main__":
    main()
