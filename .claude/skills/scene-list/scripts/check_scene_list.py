#!/usr/bin/env python3
"""scene-list.md 结构自检（pipeline 源头护栏 · 默认 warn 不阻断）。

scene-list 是整条 pipeline 的编号源头，编号错会污染 IMAP / 原型 / PRD 全下游。
但 scene-list 格式按项目形态分流（叙事型 / 规则系统型 / 主题索引），故只查 **schema
无关** 的安全项，避免误伤：

  1. 重复场景编号（同编号在场景表第一列出现 ≥ 2 次）—— error，真 bug
  2. 优先级值合法（仅当该表含 P 列）—— warn
  3. 设备标识非空（仅当该表含设备列）—— warn

只解析「表头含『编号』」的场景表，自动跳过 View 划分 / 统计 等其它表。

用法：
    python3 scripts/check_scene_list.py <scene-list.md>... [--strict]
退出码：0 clean/warn（未传 --strict）· 2 传 --strict 且有 error
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_PRIORITY_OK = re.compile(r"^P\d")
_PRIORITY_EXEMPT = {"后续", "—", "-", ""}
_SEP_CHARS = set("|-: ")


def _cells(line: str) -> list[str]:
    """拆 markdown 表格行 → cell 列表（去首尾 | 与空白）。"""
    s = line.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") else s
    return [c.strip() for c in s.split("|")]


def _is_sep_row(line: str) -> bool:
    """表头分隔行 |---|:--|。"""
    return bool(line.strip()) and set(line.strip()) <= _SEP_CHARS


def check_text(text: str) -> list[tuple[str, str]]:
    """返回 [(level, message), ...]，level ∈ {error, warn}。"""
    findings: list[tuple[str, str]] = []
    lines = text.splitlines()
    seen: dict[str, int] = {}  # 编号 → 首次出现行号
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        if not (line.lstrip().startswith("|") and "编号" in line):
            i += 1
            continue
        header = _cells(line)
        id_col = next((k for k, h in enumerate(header) if "编号" in h), None)
        if id_col is None:
            i += 1
            continue
        dev_col = next((k for k, h in enumerate(header) if "设备" in h), None)
        p_col = next((k for k, h in enumerate(header) if h == "P" or "优先级" in h), None)
        # 读该表数据行（直到非表格行）
        j = i + 1
        while j < n and lines[j].lstrip().startswith("|"):
            row = lines[j]
            if _is_sep_row(row):
                j += 1
                continue
            cells = _cells(row)
            if id_col >= len(cells):
                j += 1
                continue
            sid = cells[id_col]
            if not sid or "编号" in sid:  # 空格或重复表头
                j += 1
                continue
            if sid in seen:
                findings.append(("error", f"L{j + 1}: 重复场景编号「{sid}」（首现于 L{seen[sid]}）"))
            else:
                seen[sid] = j + 1
            if p_col is not None and p_col < len(cells):
                pv = cells[p_col]
                if not _PRIORITY_OK.match(pv) and pv not in _PRIORITY_EXEMPT:
                    findings.append(("warn", f"L{j + 1}: 编号「{sid}」优先级「{pv}」非法（应 P0/P1/P2/后续/—）"))
            if dev_col is not None and dev_col < len(cells):
                if not cells[dev_col]:
                    findings.append(("warn", f"L{j + 1}: 编号「{sid}」设备列为空（应标 📱phone / 🖥web）"))
            j += 1
        i = j
    return findings


def check_file(path: Path) -> list[tuple[str, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return check_text(text)


def main() -> int:
    args = sys.argv[1:]
    strict = "--strict" in args
    files = [Path(a) for a in args if not a.startswith("-")]
    if not files:
        print("用法: check_scene_list.py <scene-list.md>... [--strict]", file=sys.stderr)
        return 1
    total_err = 0
    for fp in files:
        if not fp.exists():
            # 传错路径静默当 clean 会漏拦全部 error（管道源头护栏失效），必须报出来
            print(f"✗ 文件不存在: {fp}", file=sys.stderr)
            total_err += 1
            continue
        findings = check_file(fp)
        if not findings:
            continue
        errs = [m for lv, m in findings if lv == "error"]
        warns = [m for lv, m in findings if lv == "warn"]
        total_err += len(errs)
        print(f"\n{fp} — error {len(errs)} / warn {len(warns)}", file=sys.stderr)
        for m in errs:
            print(f"  ❌ {m}", file=sys.stderr)
        for m in warns[:20]:
            print(f"  ⚠️  {m}", file=sys.stderr)
        if len(warns) > 20:
            print(f"  ... （共 {len(warns)} 条 warn，仅显示前 20）", file=sys.stderr)
    if total_err:
        print("\n→ 编号错会污染下游 IMAP / 原型 / PRD，修后重试。临时绕过：SKIP_SCENE_LIST_GATE=1", file=sys.stderr)
    return 2 if (strict and total_err) else 0


if __name__ == "__main__":
    sys.exit(main())
