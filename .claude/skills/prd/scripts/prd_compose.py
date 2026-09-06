#!/usr/bin/env python3
"""PRD 组装器（split 模式 → 完整 md 字符串）。

用法：
    python3 prd_compose.py <prd.md>                 # stdout
    python3 prd_compose.py <prd.md> -o composed.md  # 写文件
    python3 prd_compose.py <prd.md> --check         # 只 check 引用完整性不输出

作用：
1. 识别 split 模式：同级目录有 `{stem}-scenes/` → split
2. 把主 md 里 5/6/7 章的场景链接 `- [5.1 A-1 · 发帖](scenes/xxx.md)` 展开为对应文件内容
3. 子文件的 `## 5.1 A-1 · 发帖` 保持 h2 层级（已是正确层级）
4. single 模式：直接透传（无子目录时等价于 cat）

push Confluence 前自动调用：`md_to_confluence.py` 检测到 split 结构会先 compose。

约定：
- 子文件引用格式固定 `- [章节号 编号 · 名](scenes_dir/filename.md)`，由 gen_prd_skeleton 生成
- 子文件不含 h1（h1 只在主 md）
- 截图相对路径：主 md 用 `./assets/`，子文件用 `../assets/`，compose 时统一为 `./assets/`
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 场景引用行正则：- [5.1 A-1 · 发帖](path/to/file.md)
_SCENE_LINK_RE = re.compile(
    r"^(\s*-\s*\[)([^\]]+)\]\(([^)]+\.md)\)\s*$"
)


def _is_split_mode(prd_path: Path) -> tuple[bool, Path]:
    """判断 split 模式 + 返回 scenes 目录路径。"""
    stem = prd_path.stem  # prd-xxx-v1
    scenes_dir = prd_path.parent / f"{stem}-scenes"
    return scenes_dir.is_dir(), scenes_dir


def _normalize_image_path(line: str) -> str:
    """子文件里的 `../assets/x.png` 改回 `./assets/x.png`（主 md 视角）。"""
    return re.sub(r"\]\(\.\./assets/", "](./assets/", line)


def compose(prd_path: Path, check_only: bool = False) -> tuple[str, list[str]]:
    """返回 (composed_md, missing_files)。

    check_only=True 时仍返回 composed_md，但 missing_files 会填上缺的子文件引用，
    调用方可判断是否完整。
    """
    if not prd_path.exists():
        raise SystemExit(f"主 PRD md 不存在：{prd_path}")

    is_split, scenes_dir = _is_split_mode(prd_path)
    main_text = prd_path.read_text(encoding="utf-8")

    if not is_split:
        # single 模式：直接透传
        return main_text, []

    missing: list[str] = []
    out_lines: list[str] = []
    for line in main_text.splitlines():
        m = _SCENE_LINK_RE.match(line)
        if not m:
            out_lines.append(line)
            continue
        _prefix, _label, rel_path = m.groups()
        scene_file = prd_path.parent / rel_path
        if not scene_file.exists():
            missing.append(rel_path)
            # 保留原链接行 + 标记
            out_lines.append(f"{line}  <!-- ⚠ 子文件缺失 -->")
            continue
        if check_only:
            # check_only：保留链接，不展开
            out_lines.append(line)
            continue
        # 展开子文件内容（保持 h2 层级）
        scene_text = scene_file.read_text(encoding="utf-8")
        # 归一化图片路径
        scene_text = "\n".join(
            _normalize_image_path(ln) for ln in scene_text.splitlines()
        )
        out_lines.append("")  # 前置空行
        out_lines.append(scene_text.rstrip())
        out_lines.append("")

    composed = "\n".join(out_lines).rstrip() + "\n"
    return composed, missing


def main() -> int:
    ap = argparse.ArgumentParser(description="组装 split 模式 PRD 为完整 md")
    ap.add_argument("prd", help="主 PRD md 路径")
    ap.add_argument("-o", "--output", default=None, help="输出路径（缺省 stdout）")
    ap.add_argument(
        "--check", action="store_true",
        help="只检查子文件引用完整性，不展开内容",
    )
    args = ap.parse_args()

    prd_path = Path(args.prd).resolve()
    composed, missing = compose(prd_path, check_only=args.check)

    if missing:
        print(f"⚠ 缺失 {len(missing)} 个子场景文件：", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        if args.check:
            return 2

    if args.output:
        Path(args.output).write_text(composed, encoding="utf-8")
        print(f"✓ 写入 {args.output}（{composed.count(chr(10))} 行）", file=sys.stderr)
    else:
        sys.stdout.write(composed)

    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
