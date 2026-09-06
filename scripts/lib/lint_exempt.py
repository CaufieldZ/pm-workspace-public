"""行文类 lint 的产物豁免判定（规则数据见同目录 lint_exempt.txt）。

规则表是 bash / Python 双侧共读的单一真相源：Python 走本模块，
bash 走 .claude/hooks/lib/guards.sh 的 is_plain_language_exempt。

调用方：
- scripts/check_plain_language.py
- .claude/hooks/lib/guards.sh（经 --check-exempt CLI）

CLI（供 bash 调用，退出码即判定）：
    python3 scripts/lib/lint_exempt.py --check-exempt <path>   # 0=豁免 1=不豁免
"""
from __future__ import annotations

import sys
from fnmatch import fnmatchcase
from pathlib import Path

_RULES_PATH = Path(__file__).parent / "lint_exempt.txt"


def _load() -> tuple[list[str], list[str]]:
    """解析规则表 → (basename glob 列表, pathseg 名列表)。"""
    basenames: list[str] = []
    pathsegs: list[str] = []
    for raw in _RULES_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        kind, _, pattern = line.partition(":")
        if kind == "basename":
            basenames.append(pattern)
        elif kind == "pathseg":
            pathsegs.append(pattern)
    return basenames, pathsegs


EXEMPT_BASENAME, EXEMPT_PATHSEGMENT = _load()


def is_lint_exempt(path: Path) -> bool:
    """产物自身是内部文档（audit / fix-plan / imap / interaction）→ 不跑行文 lint。"""
    # fnmatchcase 而非 fnmatch：后者在大小写不敏感文件系统上会归一化，与 bash case 分叉
    if any(fnmatchcase(path.name, pat) for pat in EXEMPT_BASENAME):
        return True
    return any(seg in path.parts for seg in EXEMPT_PATHSEGMENT)


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--check-exempt":
        return 0 if is_lint_exempt(Path(args[1])) else 1
    sys.stderr.write(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
