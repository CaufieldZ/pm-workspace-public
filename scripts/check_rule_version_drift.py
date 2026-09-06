#!/usr/bin/env python3
"""规则版本 drift 校验 — 验产物声明的骨架版本是否落后于当前规则版本。

三层判据（机械可算边界，仿 check_baseline_fresh 三层范式）：

第一层 · 戳缺失（机械可算，黄灯）：
  产物（PRD md / IMAP / 原型 / 架构图 / scene-list HTML）无骨架版本戳
  → 早于戳机制的遗留产物。只报缺戳不强制刷新（无法判定对应哪版规则）。
  首跑会全黄（现存产物都无戳）——只汇总报数 + 抽样，不逐文件喷，等产物重生自然消解。

第二层 · 主版本落后（机械可算，红灯）：
  产物戳的 vN 整数 < workspace.json 当前 skel_version 整数
  → 按旧骨架规则生成、规则源已升级，需重生成。
  戳格式非 vN → 当无戳处理（落第一层黄灯），不进红灯。

第三层 · 不验内容逐字（机械验不了，不报）：
  产物是否真按新规则重写，drift 不验（无法机械判定措辞是否更新）。
  只验「戳声明了它属于哪版骨架」，同 baseline_fresh 第三层「只验整段漏搬不验逐字」。

扫描范围：projects/{产品线}/ 下规则生成的 md / html 产物（baseline / delta /
IMAP / 原型 / 架构图 / scene-list HTML），含 deliverables/ 与 archive/。
首轮排除：flowchart(.svg/.png) / ppt(.docx) —— 非文本产物无注入点，不扫。

用法：
    python3 scripts/check_rule_version_drift.py <产品线>
    python3 scripts/check_rule_version_drift.py livestream
    python3 scripts/check_rule_version_drift.py --rule-sources   # 输出规则源清单（post-commit 用）

退出码：恒 0（warn 级，供 hook / dashboard 调）。结构化结论走 stdout。
SKIP_RULE_VERSION_DRIFT_GATE=1 整体跳过；SKIP_DRIFT_MISSING=1 跳过第一层缺戳。
非 baseline 项目（无 prd-*-baseline.md 且无 deliverables/）→ 直接 skip。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.repo import find_root  # noqa: E402

# ── 规则源清单（决定产物骨架形态的文件，改了该 bump skel_version） ────────
# 单一真相源：post-commit hook 调 `--rule-sources` 取本清单，不另维护副本。
RULE_SOURCE_PATHS = [
    "scripts/lib/html_builder.py",
    ".claude/skills/prd/scripts/core/md_renderer.py",
    ".claude/skills/prd/scripts/sections_md.py",
    ".claude/skills/prd/scripts/split_prd.py",
    ".claude/skills/interaction-map/scripts/build_imap_skeleton.py",
    ".claude/skills/prototype/scripts/build_proto_skeleton.py",
    ".claude/skills/architecture-diagrams/scripts/build_arch_skeleton.py",
    ".claude/skills/scene-list/scripts/render_scene_list.py",
    "scripts/lib/banned_terms.py",
    "scripts/lib/ui_jargon.py",
    "scripts/lib/business_voice.py",
]
# 目录级：目录内任一文件改动都算规则源升级。
RULE_SOURCE_DIRS = [
    ".claude/skills/_shared/claude-design/",
    "scripts/lib/tech_jargon/",
]


# ── 版本戳解析 ───────────────────────────────────────────────────────────
_MD_STAMP = re.compile(r"<!-- @pm-skel v(\d+) -->")
_HTML_STAMP = re.compile(
    r'<meta\s+name=["\']x-pm-skel-version["\']\s+content=["\']v(\d+)["\']'
)
_VERSION_RE = re.compile(r"^v(\d+)$")


def _current_version(repo_root: Path) -> str | None:
    """workspace.json 当前 skel_version 的整数串（如 '1'）。未配/格式非 vN 返回 None。"""
    cfg = repo_root / ".claude" / "skills" / "_shared" / "workspace.json"
    try:
        raw = json.loads(cfg.read_text(encoding="utf-8")).get("skel_version", "")
    except (json.JSONDecodeError, OSError):
        return None
    m = _VERSION_RE.match(str(raw))
    return m.group(1) if m else None


def _parse_stamp(path: Path) -> str | None:
    """产物声明的版本整数串（如 '1'）。无戳 / 读不到 / 格式非 vN 返回 None。"""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    pat = _HTML_STAMP if path.suffix == ".html" else _MD_STAMP
    m = pat.search(text)
    return m.group(1) if m else None


def _collect_artifacts(project_dir: Path) -> list[Path]:
    """规则生成的产物：baseline md + delta md + deliverables HTML（含 archive）。"""
    out: list[Path] = []
    out += list(project_dir.glob("prd-*-baseline.md"))
    deliverables = project_dir / "deliverables"
    if deliverables.is_dir():
        out += [
            p for p in deliverables.rglob("prd-*.md")
            if "baseline" not in p.name and p.suffix == ".md"
        ]
        out += [p for p in deliverables.rglob("*.html")]
    return sorted(set(out))


# ── 主校验 ───────────────────────────────────────────────────────────────

def check(project: str, repo_root: Path) -> int:
    project_dir = repo_root / "projects" / project
    if not project_dir.is_dir():
        print(f"⚠ 项目目录不存在：{project_dir}")
        return 0

    current = _current_version(repo_root)
    if not current:
        print(f"· {project}：workspace.json 未配 skel_version（或格式非 vN），skip")
        return 0

    artifacts = _collect_artifacts(project_dir)
    if not artifacts:
        print(f"· {project}：无规则生成产物（baseline / deliverables），skip")
        return 0

    missing: list[Path] = []      # 第一层 黄灯：无戳
    stale: list[tuple[Path, str]] = []  # 第二层 红灯：落后
    ok = 0
    for p in artifacts:
        v = _parse_stamp(p)
        if v is None:
            missing.append(p)
        elif int(v) < int(current):
            stale.append((p, v))
        else:
            ok += 1

    def rel(p: Path) -> str:
        try:
            return str(p.relative_to(repo_root))
        except ValueError:
            return str(p)

    print(f"产物: {len(artifacts)} 个 · 当前规则版本: v{current}")

    # 第二层 红灯：版本落后（机械可算，必须修）
    if stale:
        print(f"\n🔴 第二层 · 版本落后（{len(stale)}）—— 按旧骨架生成、规则源已升级，需重生成：")
        for p, v in stale[:15]:
            print(f"  ❌ {rel(p)} 声明 v{v} < 当前 v{current}")
        if len(stale) > 15:
            print(f"  ... 还有 {len(stale) - 15} 个")
    else:
        print("\n🟢 第二层 · 版本落后：所有带戳产物版本 ≥ 当前")

    # 第一层 黄灯：戳缺失（首跑全黄，抽样不喷）
    if missing and not os.environ.get("SKIP_DRIFT_MISSING"):
        print(f"\n🟡 第一层 · 戳缺失（{len(missing)}）—— 早于戳机制的遗留产物，重生后消解：")
        for p in missing[:8]:
            print(f"  · {rel(p)}")
        if len(missing) > 8:
            print(f"  ... 还有 {len(missing) - 8} 个")
    elif not missing:
        print("🟢 第一层 · 戳缺失：所有产物均带骨架版本戳")

    if ok:
        print(f"\n🟢 {ok} 个产物版本达标")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="规则版本 drift 校验")
    ap.add_argument("project", nargs="?", help="项目 / 产品线路径片段，如 livestream")
    ap.add_argument("--rule-sources", action="store_true",
                    help="输出规则源清单（文件 + 目录），供 post-commit hook 取用")
    args = ap.parse_args()

    if args.rule_sources:
        for p in RULE_SOURCE_PATHS + RULE_SOURCE_DIRS:
            print(p)
        return 0

    if not args.project:
        ap.error("the following argument is required: project")
    return check(args.project, find_root())


if __name__ == "__main__":
    sys.exit(main())
