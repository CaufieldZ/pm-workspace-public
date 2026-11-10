#!/usr/bin/env python3
"""prd-content-gate 检查体：PRD 写入时新增行的硬错检测。

完整的 check_prd_md.sh 只在交付时跑；本检查体补「写入时」这一段：跑 md_scan 的硬错维度
（Confluence 渲染不了的写法 / 埋点表），只报本次新增行，存量不卡。

用法：
    python3 scripts/hook_check_prd_content.py <file> --added-file <added-lines.txt>
    python3 scripts/hook_check_prd_content.py <file> <project_dir>   # 自取 diff
参数：
    <file>           被检 PRD md（绝对路径）
    --added-file <p> 新增行清单文件（每行一条）；缺省时自取——tracked 走
                     git diff -U0 HEAD、untracked 全文
前置：无（--added-file 路径不依赖 git；缺省路径需 file 在 git 仓内）
退出码：
    0 = 恒 0（判定看 stdout：命中时首行 HITS + 明细；干净时无输出；
       异常时 traceback 进 stdout，由调用方按输出判定）

维度取 humanize/patterns.py 的 prd_fail_keys(skeleton=True)——骨架阶段的占位符降 WARN，
写入时不拦。水平线归 cjk-punct 管，这里不重复报。

进合批：top-level 不读 argv / 不 print / 不 exit，判定全在 main()（见 lib/pybatch.sh 不变量）。
"""
import re
import subprocess
import sys
from pathlib import Path

# 别的门已经管的维度，本检查体不重复报（避免一处违规两份措辞不同的拦截）
OTHER_GATE_KEYS = frozenset({"horizontal_rule_hits"})

_HIT_LINENO_RE = re.compile(r"^L(\d+)\b")


def _humanize_path() -> Path:
    """humanize 包所在目录（.claude/skills/prd/scripts）。"""
    return Path(__file__).resolve().parent.parent / ".claude" / "skills" / "prd" / "scripts"


def key_list(file_path: str, project_dir: str = "") -> list[tuple[str, str]]:
    """取本次要查的 (维度键, 标签) 清单。

    profile 按文件名判（prd-*-baseline.md = baseline）。
    """
    sys.path.insert(0, str(_humanize_path()))
    from humanize.patterns import prd_fail_keys  # noqa: E402

    name = Path(file_path).name
    is_baseline = name.startswith("prd-") and name.endswith("-baseline.md")
    keys = prd_fail_keys(
        skeleton=True,
        profile="baseline" if is_baseline else "delta",
    )
    return [(k, label) for k, label in keys if k not in OTHER_GATE_KEYS]


def added_lines_from_git(file_path: str, project_dir: str) -> list[str]:
    """tracked → git diff -U0 HEAD 的 added 行；untracked → 全文行。"""
    tracked = subprocess.run(
        ["git", "-C", project_dir, "ls-files", "--error-unmatch", file_path],
        capture_output=True,
    ).returncode == 0
    if tracked:
        diff = subprocess.run(
            ["git", "-C", project_dir, "diff", "-U0", "HEAD", "--", file_path],
            capture_output=True, text=True,
        ).stdout
        return [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    with open(file_path, encoding="utf-8") as f:
        return f.read().splitlines()


def scan_added_hits(file_path: str, added: list[str], keys: list[tuple[str, str]]) -> dict[str, list[str]]:
    """跑 md_scan，只留行号落在本次新增行里的命中。"""
    sys.path.insert(0, str(_humanize_path()))
    from humanize.md_scan import scan_prd_structural_md  # noqa: E402

    text = Path(file_path).read_text(encoding="utf-8")
    merged = scan_prd_structural_md(text)

    added_set = set(added)
    text_lines = text.splitlines()
    out: dict[str, list[str]] = {}
    for key, _label in keys:
        kept = []
        for hit in merged.get(key, []):
            m = _HIT_LINENO_RE.match(hit)
            if not m:
                continue
            no = int(m.group(1))
            if 1 <= no <= len(text_lines) and text_lines[no - 1] in added_set:
                kept.append(hit)
        if kept:
            out[key] = kept
    return out


def main() -> int:
    argv = list(sys.argv[1:])
    added_file = None
    if "--added-file" in argv:
        i = argv.index("--added-file")
        added_file = argv[i + 1] if i + 1 < len(argv) else None
        del argv[i:i + 2]
    if not argv:
        print("用法: python3 scripts/hook_check_prd_content.py <file> [--added-file <p>]", file=sys.stderr)
        return 2

    file_path = argv[0]
    project_dir = argv[1] if len(argv) > 1 and added_file is None else ""

    if added_file is not None:
        added = Path(added_file).read_text(encoding="utf-8", errors="replace").splitlines()
    else:
        added = added_lines_from_git(file_path, project_dir)

    keys = key_list(file_path, project_dir)
    hits = scan_added_hits(file_path, added, keys)
    if hits:
        print("HITS")
        for key, label in keys:
            for hit in hits.get(key, []):
                print(f"  [{label}] {hit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
