#!/usr/bin/env python3
"""md-blockquote-gate 检查体：项目 md 新增行的引用墙检测（连排 ≥2 行 / 单行 >120 字）。

用法：
    python3 scripts/hook_check_md_blockquote.py <file>
    python3 scripts/hook_check_md_blockquote.py <file> --added-file <added-lines.txt>
参数：
    <file>            被检 md（绝对路径）
    --added-file <p>  新增行清单文件（每行一条）；缺省时自取——tracked 走
                      git diff -U0 HEAD、untracked 全文（原始内嵌行为，保留作 A/B 对拍口）
前置：无（--added-file 路径不依赖 git；缺省路径需 file 在 git 仓内）
退出码：
    0 = 恒 0（判定看 stdout：检出时首行 WALL + 明细；干净时无输出；
       异常时 traceback 进 stdout，由调用方按输出判定）

检查体从 post-checks.sh 的 pc_md_blockquote_wall 内嵌 python 逐字节搬运
（decisions/2026-09-23-pc-batch-mechanism 阶段 3：物化 + 合批，判定逻辑零重写）。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def added_lines_from_git(file_path: str, project_dir: str) -> list[str]:
    """tracked → git diff HEAD 的 added 行；untracked → 全文行。原始内嵌行为。"""
    tracked = subprocess.run(["git", "-C", project_dir, "ls-files", "--error-unmatch", file_path],
                             capture_output=True).returncode == 0
    if tracked:
        diff = subprocess.run(["git", "-C", project_dir, "diff", "-U0", "HEAD", "--", file_path],
                              capture_output=True, text=True).stdout
        return [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    with open(file_path, encoding="utf-8") as f:
        return f.read().splitlines()


def find_walls(added: list[str]) -> tuple[list[list[str]], list[str]]:
    """连排 ≥2 行引用墙 + 单行超 120 字引用。状态机与原始内嵌实现逐字节一致。"""
    walls, longs, buf = [], [], []

    def flush():
        if len(buf) >= 2:
            walls.append(buf[:])
        elif len(buf) == 1 and len(buf[0].strip()) > 120:
            longs.append(buf[0])

    for l in added:
        if l.lstrip().startswith(">"):
            buf.append(l)
        else:
            flush()
            buf.clear()
    flush()
    return walls, longs


def main() -> int:
    args = sys.argv[1:]
    added_file = None
    if "--added-file" in args:
        i = args.index("--added-file")
        added_file = args[i + 1]
        del args[i:i + 2]
    if not args:
        print("用法: python3 scripts/hook_check_md_blockquote.py <file> [--added-file <p>]", file=sys.stderr)
        return 2
    file_path = args[0]
    project_dir = args[1] if len(args) > 1 and added_file is None else ""

    if added_file is not None:
        added = Path(added_file).read_text(encoding="utf-8", errors="replace").splitlines()
    else:
        added = added_lines_from_git(file_path, project_dir)

    walls, longs = find_walls(added)
    if walls or longs:
        print("WALL")
        for w in walls[:3]:
            print(f"  连续 {len(w)} 行引用墙，首行：{w[0].strip()[:70]}")
        for l in longs[:3]:
            print(f"  超长引用行（{len(l.strip())} 字）：{l.strip()[:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
