#!/usr/bin/env python3
"""PRD md 骨架生成器（scaffold）。

用法：
    python3 gen_prd_skeleton.py -p growth/activity-center -v 1
    python3 gen_prd_skeleton.py -p community/base -v 4 --mode split
    python3 gen_prd_skeleton.py -p xxx -v 1 --force       # 覆盖已存在文件

行为：
1. 读 projects/{产品线}/{项目}/scene-list.md 解析场景清单
2. 按 --mode 生成：
   single（默认，场景 ≤ 10）：
     projects/xxx/deliverables/
       ├── prd-{简称}-v{N}.md       # 12 章全在一个文件
       └── assets/                  # 空文件夹
   split（场景 > 10 或显式指定）：
     projects/xxx/deliverables/
       ├── prd-{简称}-v{N}.md              # 主骨架
       ├── prd-{简称}-v{N}-scenes/
       │   ├── front-A-1-xxx.md
       │   └── ...
       └── assets/
3. 自动填第 2.1 场景编号表 + 第 5/6/7 章（按 view 分桶）
4. 其他章节填 {{ 待填：... }} 占位符

核心路径（不传时走默认）：
- PROJECT_ROOT = `pm-workspace` 仓库根（git rev-parse 或 cwd 推断）
- SCENE_LIST = `projects/{p}/scene-list.md`
- DELIVERABLES = `projects/{p}/deliverables/`

不做的事（明确）：
- 不读 baseline 自动填内容（PM 自己填 / 对着 baseline + scene-list 填）
- 不生成截图（PM 用 prototype 产物 → prd_screenshots.py）
- 不推 Confluence（那是 D 模式）
"""
from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# 让本模块既能在 scripts/ 目录下跑，也能被 import
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
sys.path.insert(0, str(_SCRIPT_DIR.parents[3] / "scripts"))  # 接根 scripts/lib

from lib.repo import find_root  # noqa: E402
from sections_md import (
    SceneInfo,
    build_full_skeleton,
    build_scene_file,
)
from sections_md_baseline import (
    build_baseline_skeleton,
    build_delta_skeleton,
)

# ── 路径工具 ─────────────────────────────────────────────────────────────

def _project_paths(repo_root: Path, project: str) -> dict[str, Path]:
    """{p} = 'growth/activity-center' → 各种路径"""
    proj_dir = repo_root / "projects" / project
    if not proj_dir.is_dir():
        raise SystemExit(f"项目目录不存在：{proj_dir}")
    return {
        "project_dir": proj_dir,
        "scene_list": proj_dir / "scene-list.md",
        "deliverables": proj_dir / "deliverables",
        "assets": proj_dir / "deliverables" / "assets",
    }


def _project_short_name(project: str) -> str:
    """'growth/activity-center' → 'activity-center'；顶级项目保持原名"""
    return project.split("/")[-1]


def _current_quarter() -> str:
    d = datetime.date.today()
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def _delta_status_lines(paths: dict[str, Path], short_name: str, quarter: str) -> list[str]:
    """delta 启动引导：列 baseline 路径 + 该季已有版本，省手动 ls（不猜下一版本号）"""
    lines: list[str] = []
    baseline = paths["project_dir"] / f"prd-{short_name}-baseline.md"
    if baseline.exists():
        lines.append(f"→ baseline：{baseline}")
    else:
        lines.append(f"⚠ 未见 baseline（{baseline.name}）——delta 引 baseline，缺则先建 baseline")

    quarter_dir = paths["deliverables"] / quarter
    existing = sorted(p.name for p in quarter_dir.iterdir() if p.is_dir()) if quarter_dir.is_dir() else []
    if existing:
        lines.append(f"→ {quarter} 已有版本：{' / '.join(existing)}（自行定下一版，不自动 +1）")
    else:
        lines.append(f"→ {quarter} 尚无版本（本轮为该季首个 delta）")
    return lines


# ── scene-list 解析 ──────────────────────────────────────────────────────

_VIEW_HEADING_RE = re.compile(r"^\s*##\s+View\s*\d*\s*[·:·\-]?\s*(.+?)\s*$")
# ID 必须是 `字母+-数字+` 格式（A-1 / B-2 / M-1 / F-1 / G-3 等），允许后缀 `B-1a` 或多 ID `B-1/B-2`。
# 排除表头词（View / 编号）和统计行（"App 用户端" 含空格也天然不匹配）。
_ID_PAT = r"[A-Z]+-\w+(?:/[A-Z]+-\w+)?"

# 6 列（编号 / 场景 / 模块 / 端 / 优先级 / 说明）
_SCENE_ROW_RE_6 = re.compile(
    rf"^\s*\|\s*({_ID_PAT})\s*\|\s*([^|]+?)\s*\|"
    r"\s*([^|]*?)\s*\|"
    r"\s*([^|]*?)\s*\|"
    r"\s*([^|]*?)\s*\|"
    r"\s*([^|]*?)\s*\|"
    r"\s*$"
)
# 5 列（编号 / 场景 / 模块 / 优先级 / 说明）—— 端放在 `## View N · ...` 标题里
_SCENE_ROW_RE_5 = re.compile(
    rf"^\s*\|\s*({_ID_PAT})\s*\|\s*([^|]+?)\s*\|"
    r"\s*([^|]*?)\s*\|"
    r"\s*([^|]*?)\s*\|"
    r"\s*([^|]*?)\s*\|"
    r"\s*$"
)

# 历史日期注释剥离：scene-list 说明列常带 `（YYYY-MM-DD ...）` 变更注释，不该进 PRD 2.1 表
_DATE_NOTE_RE = re.compile(r"[（(]\s*\d{4}-\d{2}-\d{2}[^）)]*[）)]")


def _match_scene_row(line: str):
    """6 列 → 5 列依次试。返回 (id, name, module, device, priority, note) 或 None。

    device = scene-list「端」列（如 📱 / 📱web / web）；5 列表无「端」列时为空串。
    """
    m = _SCENE_ROW_RE_6.match(line)
    if m:
        scene_id, name, module, device, priority, note = m.groups()
        return scene_id, name, module, device, priority, note
    m = _SCENE_ROW_RE_5.match(line)
    if m:
        scene_id, name, module, priority, note = m.groups()
        return scene_id, name, module, "", priority, note
    return None


def _classify_view(view_text: str) -> str:
    """从 `## View N · XXX` 的 XXX 判断前台 / 后台 / 跨端（heading 兜底信号）"""
    t = view_text.lower()
    if any(k in t for k in ("用户端", "前台", "app", "ios", "android", "h5", "web 用户")):
        return "前台"
    if any(k in t for k in (
        "mgt", "后台", "管理端", "cms", "运营端", "管理后台",
        "运营配置", "运营后台", "后端配置", "配置后台",
    )):
        return "后台"
    return "跨端"


# 用户端设备标记（scene-list「端」列命中 → 该场景面向用户 = 前台）
_FRONT_DEVICE_KW = ("📱", "web", "app", "ios", "android", "h5", "pc")


def _classify_scene(scene_id: str, device: str, heading_view: str) -> str:
    """按场景优先分类前台 / 后台 / 跨端。

    信号优先级（编号约定 SSOT 见 CLAUDE.md「场景编号」）：
      1. 编号前缀 M（M-N 后台）→ 后台
      2. 编号前缀 D / E（D-N 数据流 / E-N 异常，天然跨系统）→ 跨端
      3. 「端」列有用户端设备标记 → 前台（除非 heading 明确判后台）
      4. 回落 heading 兜底分类（_classify_view）

    历史坑：只靠 heading 关键词判类，真实 View 标题（「社区 Feed 首页」）不含关键词 →
    全部前台场景默认落「跨端」章、「前台」章恒空。用编号前缀 + 端列纠正。
    """
    prefix = scene_id.split("-")[0].upper()
    if prefix == "M":
        return "后台"
    if prefix in ("D", "E"):
        return "跨端"
    dev = device.lower()
    if any(k in dev for k in _FRONT_DEVICE_KW):
        return "后台" if heading_view == "后台" else "前台"
    return heading_view


def parse_scene_list(scene_list_path: Path) -> list[dict]:
    """返回 [{'id', 'name', 'view', 'priority', 'note'}, ...]。

    不存在返回空列表，调用方自行兜底。
    跳过含 ⚠ / 已迁移 / 已弃 字样的行（按约定不再是活跃场景）。
    """
    if not scene_list_path.exists():
        return []
    text = scene_list_path.read_text(encoding="utf-8")
    current_view = "跨端"
    scenes: list[dict] = []
    seen_ids: set[str] = set()
    for line in text.splitlines():
        m = _VIEW_HEADING_RE.match(line)
        if m:
            current_view = _classify_view(m.group(1))
            continue
        row = _match_scene_row(line)
        if not row:
            # 表格行首列像场景 ID 却没匹配上（列数非 5/6）→ 显式警告，不静默丢行
            _first_cell = re.match(r"^\s*\|\s*([^|]+?)\s*\|", line)
            if _first_cell and re.fullmatch(_ID_PAT, _first_cell.group(1).strip()):
                print(f"⚠ 跳过无法解析的场景表行（列数非 5/6）: {line.strip()[:80]}", file=sys.stderr)
            continue
        scene_id, name, module, device, priority, note = row
        if scene_id.strip().lower() in ("编号",):  # 跳过表头
            continue
        # 跳过禁用 / 已迁移
        if any(flag in (name + note) for flag in ("⚠ 已迁移", "已弃", "已废弃")):
            continue
        # 去重（子场景 B-1a/b/c 只取第一个代表）
        base_id = scene_id.split("/")[0]
        if base_id in seen_ids:
            continue
        seen_ids.add(base_id)
        clean_note = _DATE_NOTE_RE.sub("", note).strip()
        scenes.append({
            "id": base_id,
            "name": name.strip(),
            "view": _classify_scene(base_id, device, current_view),
            "module": module.strip(),
            "priority": priority.strip() or "—",  # 空优先级兜 —，与 check_scene_list._PRIORITY_EXEMPT 对齐（不虚报 P0）
            "note": clean_note,
        })
    return scenes


# ── scene-list 合规预检（scaffold 前拦截） ──────────────────────────────
# 骨架脚本会把场景名扩散到 N 个子场景文件 + 2.1 表 + image alt，
# 源头不清洁就生成会导致污染扩散，PM 要逐文件返工。
# 拦截两类硬错：
#   1. 场景名含半角括号包 CJK（check_cjk_punct.py --strict 会报错）
#   2. 场景名裸引用其他场景编号（如「与 C-3 同款」/「同 B-2」），check_prd_md.sh
#      的 bare_scene_codes checker 会报 FAIL

_HALF_PAREN_CJK_RE = re.compile(r"[一-鿿][(][^)]*[)]|[(][^()]*[一-鿿][^()]*[)]")
# 裸引用：场景名里出现「X-N」但不是场景自身的编号（自身在单独的 id 列，不会出现在 name 里）
_OTHER_SCENE_REF_RE = re.compile(r"(?:与|同|见|如|类似|参考|对标|同款)\s*[A-Z]+-\w+")


def precheck_scene_list(scenes_raw: list[dict]) -> list[str]:
    """扫场景名三类硬错，返回问题描述列表（空 = 通过）。"""
    issues: list[str] = []
    for s in scenes_raw:
        name = s.get("name", "")
        sid = s.get("id", "")
        if _HALF_PAREN_CJK_RE.search(name):
            issues.append(
                f"  ❌ 场景 {sid} 名含半角括号包 CJK：{name!r}\n"
                f"     → 改全角括号 `（）`（check_cjk_punct.py strict 会报错 + 会扩散到所有子场景文件）"
            )
        m = _OTHER_SCENE_REF_RE.search(name)
        if m:
            issues.append(
                f"  ❌ 场景 {sid} 名含裸场景引用：{name!r}\n"
                f"     → 改白话描述（check_prd_md.sh 的 bare_scene_codes 会报 FAIL）"
            )
    return issues


# ── 模式判定 ─────────────────────────────────────────────────────────────

_SCENE_COUNT_THRESHOLD = 10  # 阈值登记: thresholds.yaml §E prd_checks.scene_split_count


def _decide_mode(scenes: list[dict], user_mode: Optional[str]) -> str:
    if user_mode in ("single", "split"):
        return user_mode
    if user_mode is not None:
        raise SystemExit(f"--mode 只接受 single / split，传入：{user_mode}")
    # 自动：场景数 > 10 → split
    return "split" if len(scenes) > _SCENE_COUNT_THRESHOLD else "single"


# ── 文件写入 ─────────────────────────────────────────────────────────────

def _safe_write(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(
            f"文件已存在：{path}\n"
            f"确认要覆盖请加 --force；或先归档现有文件到 archive/"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  ✓ 写入 {path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path}")


def _write_single(
    deliverables: Path,
    short_name: str,
    version: str,
    info: dict,
    force: bool,
) -> Path:
    prd_path = deliverables / f"prd-{short_name}-v{version}.md"
    content = build_full_skeleton(info)
    _safe_write(prd_path, content, force)
    (deliverables / "assets").mkdir(parents=True, exist_ok=True)
    print("  ✓ 创建 assets/ 空目录")
    return prd_path


def _write_baseline(
    project_dir: Path,
    short_name: str,
    info: dict,
    force: bool,
) -> Path:
    """baseline 落产品线根（与 scene-list 同级），单文件，living，无版本号。

    只在迁移 / 首建时 scaffold 一次。此后反向合并是手动 Edit，绝不重跑（--force 会 clobber）。
    """
    prd_path = project_dir / f"prd-{short_name}-baseline.md"
    content = build_baseline_skeleton(info)
    _safe_write(prd_path, content, force)
    (project_dir / "deliverables" / "assets").mkdir(parents=True, exist_ok=True)
    return prd_path


def _write_delta(
    deliverables: Path,
    short_name: str,
    version: str,
    info: dict,
    force: bool,
    quarter: str | None = None,
) -> Path:
    """delta 落 deliverables/{季度}/{版本}/，整包装 delta + imap + proto + assets，上线后整季度归 archive/。

    quarter 缺省时落 deliverables 根（兼容无季度划分的产品线）。
    """
    out_dir = deliverables / quarter / version if quarter else deliverables
    prd_path = out_dir / f"prd-{short_name}-{version}.md"
    content = build_delta_skeleton(info)
    _safe_write(prd_path, content, force)
    (out_dir / "assets").mkdir(parents=True, exist_ok=True)
    return prd_path


def _scan_stale_scene_files(
    scenes_dir: Path, expected_filenames: set[str]
) -> tuple[list[Path], list[Path]]:
    """扫 scenes_dir 下当前存在的 .md 文件 + 嵌套子目录，返回 (stale_md, stale_subdirs)。

    stale_md = scenes_dir/*.md 里不在 expected_filenames 集合的
    stale_subdirs = scenes_dir 下不应存在的任何子目录（骨架不生成嵌套）
    """
    if not scenes_dir.is_dir():
        return [], []
    stale_md: list[Path] = []
    stale_subdirs: list[Path] = []
    for p in sorted(scenes_dir.iterdir()):
        if p.is_file() and p.suffix == ".md":
            if p.name not in expected_filenames:
                stale_md.append(p)
        elif p.is_dir():
            # 骨架目录下不该出现子目录（如误 mv 嵌套的 prd-base-v4-scenes/）
            stale_subdirs.append(p)
    return stale_md, stale_subdirs


def _write_split(
    deliverables: Path,
    short_name: str,
    version: str,
    info: dict,
    scenes: list[SceneInfo],
    force: bool,
    clean_stale: bool = False,
) -> Path:
    prd_path = deliverables / f"prd-{short_name}-v{version}.md"
    scenes_dir = deliverables / f"prd-{short_name}-v{version}-scenes"
    scenes_dir_name = scenes_dir.name

    # 按 view 分桶分配章节编号（5.x / 6.x / 7.x）
    chapter_map = {"前台": 5, "后台": 6, "跨端": 7}
    view_counters = {5: 0, 6: 0, 7: 0}
    expected_filenames: set[str] = set()
    scene_labels: list[tuple[SceneInfo, str]] = []
    for scene in scenes:
        view_key = "前台" if scene.view_prefix == "front" else (
            "后台" if scene.view_prefix == "back" else "跨端"
        )
        chapter = chapter_map[view_key]
        view_counters[chapter] += 1
        label = f"{chapter}.{view_counters[chapter]}"
        expected_filenames.add(scene.scene_filename())
        scene_labels.append((scene, label))

    # Stale 扫描（scene-list 删场景 / 改 view 前缀 / 误嵌套会留 stale，不清掉 check_prd_md 会抓）
    stale_md, stale_subdirs = _scan_stale_scene_files(scenes_dir, expected_filenames)
    if stale_md or stale_subdirs:
        print(f"\n⚠ 检测到 {len(stale_md)} 个过时场景文件 + {len(stale_subdirs)} 个误嵌套目录（不在本次生成清单里）：")
        for p in stale_md:
            rel = p.relative_to(Path.cwd()) if p.is_relative_to(Path.cwd()) else p
            print(f"  - {rel}")
        for p in stale_subdirs:
            rel = p.relative_to(Path.cwd()) if p.is_relative_to(Path.cwd()) else p
            print(f"  - {rel}/ （嵌套子目录，骨架不应有）")
        if clean_stale:
            print("\n→ --clean-stale 已指定，删除 stale：")
            for p in stale_md:
                p.unlink()
                print(f"  ✗ 删除 {p.name}")
            for p in stale_subdirs:
                import shutil
                shutil.rmtree(p)
                print(f"  ✗ 删除目录 {p.name}/")
        else:
            print("\n  加 --clean-stale 可自动删除；或手动 rm 后重跑")
            print("  （不删会导致 check_prd_md.sh 抓到消失场景的裸引用 / 编号不一致）\n")

    # 主骨架
    main_content = build_full_skeleton(info, scenes_dir_name=scenes_dir_name)
    _safe_write(prd_path, main_content, force)

    # 子场景文件
    scenes_dir.mkdir(parents=True, exist_ok=True)
    for scene, label in scene_labels:
        scene_file = scenes_dir / scene.scene_filename()
        scene_content = build_scene_file(scene, chapter_label=label)
        _safe_write(scene_file, scene_content, force)

    (deliverables / "assets").mkdir(parents=True, exist_ok=True)
    print("  ✓ 创建 assets/ 空目录")
    return prd_path


# ── CLI ──────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="生成 PRD md 空骨架")
    ap.add_argument(
        "-p", "--project", required=True,
        help="项目路径片段，如 growth/activity-center / community/base / 顶级项目名",
    )
    ap.add_argument(
        "-v", "--version", required=True,
        help="版本号，如 1 / 1.0 / 5.3",
    )
    ap.add_argument(
        "--mode", choices=["single", "split"], default=None,
        help="骨架模式：single（单 md）/ split（主 + scenes/）。缺省按场景数自动判断",
    )
    ap.add_argument(
        "--profile", choices=["baseline", "delta"], default=None,
        help="文档集模型：baseline（产品线根 living 真相源，按模块树）/ delta（deliverables 单轮迭代，档位见 --tier）。"
             "缺省 = 普通 12 章 PRD。baseline 时 -p 接产品线（如 livestream）",
    )
    ap.add_argument(
        "--quarter", default=None,
        help="delta 季度标识（如 2026Q3），落 deliverables/{季度}/{版本}/，按季度 KPI 聚集。缺省用当前季",
    )
    ap.add_argument(
        "--tier", choices=["patch", "feature", "bundle"], default="feature",
        help="delta 迭代档位（仅 --profile delta 生效）：patch（补丁包，散修复+小调，无新对象/状态机，版本号三段）"
             " / feature（内聚特性，单一能力有新对象/状态机，默认）/ bundle（集合体，N 个松耦合需求跨模块/团队）。"
             "patch / bundle 自动出 §2.0 本轮需求索引表 + 按单轴分组",
    )
    ap.add_argument(
        "--author", default=None,
        help="作者，缺省读 git config user.name",
    )
    ap.add_argument(
        "--baseline", default="无线上基线（新项目）",
        help="1.3 章线上基线描述",
    )
    ap.add_argument(
        "--project-name", default=None,
        help="项目中文名（出现在 h1）。缺省用项目路径末段",
    )
    ap.add_argument(
        "--force", action="store_true",
        help="覆盖已存在文件（慎用，建议先归档）",
    )
    ap.add_argument(
        "--clean-stale", action="store_true",
        help="split 模式下自动删除 scenes 目录里不再期望的 stale 场景 md + 误嵌套子目录（scene-list 删场景 / 改 view 前缀后用）",
    )
    args = ap.parse_args()

    repo_root = find_root()
    paths = _project_paths(repo_root, args.project)

    # 解析场景清单
    scenes_raw = parse_scene_list(paths["scene_list"])
    if not scenes_raw:
        print(
            f"⚠ 未找到场景清单 / 场景为空：{paths['scene_list']}\n"
            f"  将生成纯占位符骨架，第 2.1 表需要 PM 手填"
        )

    # scene-list 合规预检 —— 源头不清洁就生成会污染 N 个子场景文件
    precheck_issues = precheck_scene_list(scenes_raw)
    if precheck_issues:
        print(f"\n🚫 scene-list.md 预检未通过（{len(precheck_issues)} 处问题）：\n")
        for issue in precheck_issues:
            print(issue)
        print(
            f"\n  scene-list.md 源：{paths['scene_list'].relative_to(repo_root) if paths['scene_list'].is_relative_to(repo_root) else paths['scene_list']}"
        )
        print(
            "  修复后重跑 gen_prd_skeleton.py\n"
            "  临时绕过（不推荐）：SKIP_SCENE_LIST_PRECHECK=1 python3 gen_prd_skeleton.py ..."
        )
        import os as _os
        if not _os.environ.get("SKIP_SCENE_LIST_PRECHECK"):
            return 2

    mode = _decide_mode(scenes_raw, args.mode)

    # 作者
    author = args.author
    if not author:
        try:
            author = subprocess.check_output(
                ["git", "config", "user.name"], stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            author = ""
    author = author or "待填"

    short_name = _project_short_name(args.project)
    project_display_name = args.project_name or short_name.replace("-", " ")

    info = {
        "project_name": project_display_name,
        "version": args.version,
        "author": author,
        "baseline": args.baseline,
        "scenes": scenes_raw,
        "mode": mode,
        "tier": args.tier,
    }

    print(f"→ 项目：{args.project}")
    print(f"→ 场景数：{len(scenes_raw)}")

    # profile 分流（文档集模型）：baseline / delta 各走专属生成器
    if args.profile == "baseline":
        print("→ profile：baseline（产品线根 living 真相源，模块树组织）")
        print()
        prd_path = _write_baseline(paths["project_dir"], short_name, info, args.force)
        print(f"  ✓ 写入 {prd_path.relative_to(repo_root)}")
        print()
        print("下一步：")
        print("  1. baseline 是 living 单文件，迁移时填一次，此后反向合并手动 Edit（勿 --force 重跑）")
        print("  2. 各模块章头补「最后核对线上: 日期 / 人」")
        print(f"  3. 分段读：read_prd_section.py {prd_path.relative_to(repo_root)} --toc")
        return 0

    if args.profile == "delta":
        quarter = args.quarter or _current_quarter()
        tier_label = {"patch": "补丁包", "feature": "内聚特性", "bundle": "集合体"}[args.tier]
        print(f"→ profile：delta（单轮迭代，引 baseline）· 档位：{tier_label} · 季度：{quarter}")
        for line in _delta_status_lines(paths, short_name, quarter):
            print(line)
        # 软提示：版本号三段通常是补丁包，档位没显式切到 patch 时点一句
        if args.version.count(".") >= 2 and args.tier != "patch":
            print(f"  ⚠ 版本号「{args.version}」是三段，通常对应补丁包（patch）——确认档位是否该用 --tier patch")
        print()
        prd_path = _write_delta(paths["deliverables"], short_name, args.version, info, args.force, quarter)
        print(f"  ✓ 写入 {prd_path.relative_to(repo_root)}")
        print()
        print("下一步：")
        print("  1. 填本轮 N 需求 + WHY，术语 / 模块树引 baseline 不重复")
        if args.tier in ("patch", "bundle"):
            print("  2. 先填 §2.0 本轮需求索引：定一条分组轴 → 把需求拆成 ## 组 X · 组名")
            print("  3. 上线后按承重不变量：先写 baseline changelog 行（已登记）→ 反向合并 → 状态推进「已合并」")
        else:
            print("  2. 上线后按承重不变量：先写 baseline changelog 行（已登记）→ 反向合并 → 状态推进「已合并」")
        return 0

    print(f"→ 模式：{mode}{' （场景超阈值自动拆分）' if mode == 'split' and args.mode is None else ''}")
    print(f"→ 输出目录：{paths['deliverables'].relative_to(repo_root)}")
    print()

    if mode == "single":
        prd_path = _write_single(
            paths["deliverables"], short_name, args.version, info, args.force
        )
    else:
        scene_infos = [SceneInfo.from_dict(s) for s in scenes_raw]
        prd_path = _write_split(
            paths["deliverables"], short_name, args.version, info, scene_infos,
            args.force, clean_stale=args.clean_stale,
        )

    print()
    print("下一步：")
    print(f"  1. VS Code 打开 {prd_path.relative_to(repo_root)}")
    print("  2. 搜 `{{ 待填` 定位所有占位符，按 references/prd-chapter-rules.md 填充")
    if mode == "split":
        print(f"  3. 场景细节写在 {prd_path.stem}-scenes/ 各子文件里")
    print(f"  4. 截图放 {paths['assets'].relative_to(repo_root)}/，md 用相对路径 `./assets/xxx.png`")
    print(f"  5. 完成后跑 check_prd_md.sh {prd_path.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
