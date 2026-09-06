#!/usr/bin/env python3
"""决策记录（.claude/decisions/）格式校验：生命周期目录一致、必需章节、alternatives 实质非空。

用法：
    python3 scripts/check_decisions.py [path...] [--strict]

    不传 path 时默认扫 <repo>/.claude/decisions/ 下全部 *.md（根 README.md 豁免）。

退出码：
    0 — clean / warn（未传 --strict）
    2 — 传 --strict 且有违规（hook / CI 用）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from lib.repo import find_root

TITLE_RE = re.compile(r"^# Decision: \S.*$")
STATUS_RE = re.compile(r"^Status:\s*(proposed|implemented|rejected)(?:\s*—\s*\S.*)?$")
FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
PLACEHOLDER = "alternatives-not-recorded"
STATUS_SCAN_WINDOW = 5  # Status 行必须在头几行内（头两行固定 + 容错空行）

# 各生命周期必需章节；元组 = 至少其一（rejected 的 Proposal/Decision）
REQUIRED_SECTIONS: dict[str, tuple[object, ...]] = {
    "proposed": ("Problem", "Proposal", "Alternatives considered"),
    "implemented": ("Problem", "Decision", "Alternatives considered", "Consequences"),
    "rejected": ("Problem", ("Proposal", "Decision"), "Alternatives considered"),
}
# implemented 禁 spec-speak：提案期章节名不得出现在已生效 note
SPEC_SPEAK_BANNED = ("Proposal", "Acceptance criteria")


def parse_sections(text: str) -> dict[str, tuple[int, str]]:
    """解析 `## ` 章节标题 → {章节名: (标题行号, 章节正文)}。"""
    sections: dict[str, tuple[int, str]] = {}
    current: str | None = None
    buf: list[str] = []
    start = 0
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            if current is not None:
                sections[current] = (start, "\n".join(buf))
            current = m.group(1)
            buf = []
            start = i
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = (start, "\n".join(buf))
    return sections


def check_filename(name: str) -> str | None:
    """文件名须为 yyyy-mm-dd-slug.md（slug 限 ASCII kebab）；返回错误消息或 None。"""
    if not FILENAME_RE.match(name):
        return f"文件名 `{name}` 不符 yyyy-mm-dd-slug.md（slug 限小写 ASCII kebab）"
    return None


def check_text(text: str, lifecycle: str) -> list[tuple[int, str, str]]:
    """校验单篇 note 正文，返回 [(行号, code, 消息), ...]；文件级问题行号记 1。"""
    hits: list[tuple[int, str, str]] = []
    lines = text.splitlines()

    if not lines or not TITLE_RE.match(lines[0]):
        hits.append((1, "title", "首行必须是 `# Decision: <标题>`"))

    window = lines[:STATUS_SCAN_WINDOW]
    status_idx = next((i for i, ln in enumerate(window) if ln.startswith("Status:")), None)
    if status_idx is None:
        hits.append((1, "status-missing", f"头 {STATUS_SCAN_WINDOW} 行内缺 `Status:` 行"))
    else:
        line_no = status_idx + 1
        raw = window[status_idx]
        m = STATUS_RE.match(raw)
        if not m:
            hits.append((line_no, "status-value", "Status 行格式错（应为 `Status: proposed|implemented|rejected`）"))
        else:
            value = m.group(1)
            if value != lifecycle:
                hits.append((line_no, "status-value", f"Status={value} 与所在目录 {lifecycle}/ 不一致"))
            has_reason = "—" in raw
            if value == "rejected" and not has_reason:
                hits.append((line_no, "status-reason", "rejected 必须带一行否决理由（Status: rejected — …）"))
            if value != "rejected" and has_reason:
                hits.append((line_no, "status-value", "只有 rejected 允许在 Status 行带理由"))

    sections = parse_sections(text)
    for req in REQUIRED_SECTIONS[lifecycle]:
        names = req if isinstance(req, tuple) else (req,)
        if not any(n in sections for n in names):
            hits.append((1, "section-missing", f"缺必需章节 `## {names[0]}`"))

    alt = sections.get("Alternatives considered")
    if alt is not None and not alt[1].strip() and PLACEHOLDER not in alt[1]:
        hits.append(
            (alt[0], "alternatives-empty",
             "`## Alternatives considered` 空节：写实质备选，或考古不出时放 `<!-- alternatives-not-recorded -->`")
        )

    if lifecycle == "implemented":
        for banned in SPEC_SPEAK_BANNED:
            if banned in sections:
                hits.append(
                    (sections[banned][0], "spec-speak",
                     f"implemented note 禁 spec-speak 章节 `## {banned}`（改写为现在时事实）")
                )
    return hits


def check_path(path: Path, decisions_root: Path) -> list[tuple[int, str, str]]:
    """校验单个文件：目录归属 + 文件名 + 正文。根 README.md 豁免。"""
    try:
        rel = path.relative_to(decisions_root)
    except ValueError:
        rel = Path(path.name)
    if len(rel.parts) == 1 and rel.name == "README.md":
        return []
    lifecycle = rel.parts[0] if len(rel.parts) > 1 else ""
    if lifecycle not in REQUIRED_SECTIONS:
        return [(1, "dir", f"须落在 proposed/ | implemented/ | rejected/ 之下（当前：{rel.as_posix()}）")]

    hits: list[tuple[int, str, str]] = []
    name_err = check_filename(path.name)
    if name_err:
        hits.append((1, "name", name_err))
    text = path.read_text(encoding="utf-8", errors="replace")
    hits.extend(check_text(text, lifecycle))
    return hits


def main() -> int:
    args = sys.argv[1:]
    strict = "--strict" in args
    targets = [Path(a) for a in args if not a.startswith("-")]

    decisions_root = find_root() / ".claude" / "decisions"
    files: list[Path] = []
    if targets:
        for t in targets:
            files.extend(t.rglob("*.md") if t.is_dir() else [t])
    else:
        files = sorted(decisions_root.rglob("*.md"))

    all_hits: list[str] = []
    for f in files:
        # 显式传入且不在 decisions 树下的文件按「祖父目录 = 树根」兜底（树深固定一层）
        root = decisions_root if f.is_relative_to(decisions_root) else f.parent.parent
        for line_no, code, msg in check_path(f, root):
            all_hits.append(f"{f}:{line_no}: [{code}] {msg}")

    for h in all_hits:
        print(h, file=sys.stderr)
    print(f"[check_decisions] {len(files)} 篇，{len(all_hits)} 违规", file=sys.stderr)
    return 2 if (strict and all_hits) else 0


if __name__ == "__main__":
    sys.exit(main())
