#!/usr/bin/env python3
"""项目生成脚本 docstring 自证充分性检查（轻量 lint）。

projects/**/scripts/ 下的 gen_*/build_* 生成脚本，头部 docstring/注释应让「换 session 后
第一次看到它的人」定位得到：怎么跑 / 产物落哪 / 改哪重生。只回显文件名的退化 docstring
会让人抓瞎——配合产物内 provenance 注释（HTML 顶 <!-- 源脚本 -->），双向都能找到源。

用法：
    python3 scripts/check_generator_docstring.py <file>... [--strict]
    python3 scripts/check_generator_docstring.py --scan [--strict]   # 扫全仓项目生成脚本

退出码：
    0 — clean / warn（未传 --strict）
    2 — 传 --strict 且有退化 docstring
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# 头部含任一「定位线索」即算充分：怎么跑 / 产物落哪 / 改哪 / 任意路径锚点
_ORIENT_RE = re.compile(
    r"运行|用法|usage|python3|node\s|跑本?脚本|重跑|重生"        # 怎么跑
    r"|产物|输出|写出|落[在到]|output|deliverables"              # 产物落哪
    r"|改源|改这里|改场景|src/|scenes|source"                    # 改哪
    r"|projects/|\.claude/|\.html|\.drawio|\.svg|\.docx",        # 路径锚点
    re.IGNORECASE,
)

# 生成脚本文件名前缀（projects/**/scripts/ 下的产物生成器）
_GEN_NAME_RE = re.compile(r"^(gen|build)[_-].+\.(py|js|mjs|cjs)$")


def extract_header(text: str, ext: str) -> str:
    """取脚本顶部 docstring / 注释块文本（去 shebang）。"""
    lines = text.splitlines()
    if lines and lines[0].startswith("#!"):
        lines = lines[1:]
    joined = "\n".join(lines)
    if ext == ".py":
        m = re.match(r'\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', joined, re.DOTALL)
        if m:
            return m.group(1)
        out = []  # 无 docstring → 取开头连续 # 注释块
        for line in lines:
            s = line.strip()
            if s.startswith("#"):
                out.append(s.lstrip("#").strip())
            elif s == "":
                continue
            else:
                break
        return "\n".join(out)
    m = re.match(r"\s*/\*(.*?)\*/", joined, re.DOTALL)  # .js: /* */ 块
    if m:
        return m.group(1)
    out = []  # 无块注释 → 取开头连续 // 注释
    for line in lines:
        s = line.strip()
        if s.startswith("//"):
            out.append(s.lstrip("/").strip())
        elif s == "":
            continue
        else:
            break
    return "\n".join(out)


def check_header(filename: str, header: str) -> list[str]:
    """返回问题描述列表（空 = 充分）。只拦「退化 docstring」，不苛求三要素齐全。"""
    if not header.strip():
        return ["无头部 docstring/注释：补「做什么 + 怎么跑 + 产物落哪 + 改哪重生」"]
    stem = filename.rsplit(".", 1)[0]
    # 剔除「只回显文件名」「纯星号装饰」的行，看剩多少实质内容
    substance = "\n".join(
        ln for ln in header.splitlines()
        if ln.strip().strip("*").strip() and stem not in ln
    ).strip()
    if len(substance) < 40 and not _ORIENT_RE.search(header):
        return ["头部近乎只回显文件名：换 session 的人无法定位，补「怎么跑 / 产物落哪 / 改哪重生」"]
    return []


def check_file(path: Path) -> list[str]:
    """读文件 → check_header。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    return check_header(path.name, extract_header(text, path.suffix))


def _scan_targets(root: Path) -> list[Path]:
    """扫 projects/**/scripts/ 下 gen_*/build_* 生成脚本（排除 archive / _ 草稿）。"""
    out = []
    for p in (root / "projects").rglob("scripts/*"):
        if not p.is_file():
            continue
        if "/archive/" in str(p) or p.name.startswith("_"):
            continue
        if _GEN_NAME_RE.match(p.name):
            out.append(p)
    return sorted(out)


def main() -> int:
    args = sys.argv[1:]
    strict = "--strict" in args
    scan = "--scan" in args
    root = Path(__file__).resolve().parents[1]
    if scan:
        files = _scan_targets(root)
    else:
        files = [Path(a) for a in args if not a.startswith("-")]

    total_hits = 0
    for f in files:
        if not f.is_file():
            continue
        issues = check_file(f)
        if issues:
            total_hits += 1
            rel = f.relative_to(root) if f.is_relative_to(root) else f
            print(f"⚠️  {rel}", file=sys.stderr)
            for it in issues:
                print(f"     {it}", file=sys.stderr)

    if total_hits:
        print(f"\n{total_hits} 个生成脚本 docstring 退化（换 session 定位难）。", file=sys.stderr)
    return 2 if (strict and total_hits) else 0


if __name__ == "__main__":
    sys.exit(main())
