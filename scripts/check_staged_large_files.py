#!/usr/bin/env python3
"""git staged 文件体检 — pre-commit 阻断超大文件 + project 本地源素材入库（warn / block 两级，阈值走 env var）。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import PurePosixPath

WARN_BYTES = int(os.environ.get("STAGED_FILE_WARN_BYTES", "500000"))
BLOCK_BYTES = int(os.environ.get("STAGED_FILE_BLOCK_BYTES", "2000000"))

LOCAL_ONLY_EXTS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}
PROJECT_MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mov", ".mp4"}


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args])


def staged_files() -> list[str]:
    out = git_bytes("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")
    return [p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p]


def staged_size(path: str) -> int | None:
    try:
        return int(git_bytes("cat-file", "-s", f":{path}").strip())
    except subprocess.CalledProcessError:
        return None


def is_local_project_artifact(path: str) -> bool:
    normalized = path.replace("\\", "/")
    posix = PurePosixPath(normalized)
    ext = posix.suffix.lower()

    if not normalized.startswith("projects/"):
        return False

    if ext in LOCAL_ONLY_EXTS and ("/inputs/" in normalized or "/deliverables/" in normalized):
        # moderation 词库表 xlsx = 易盾/客服交接物本体，入库（与 .gitignore 豁免同口径）
        if normalized.startswith("projects/moderation/deliverables/") and ext == ".xlsx":
            return False
        return True

    if ext in PROJECT_MEDIA_EXTS and (
        "/inputs/" in normalized
        or "/screenshots/" in normalized
        or "/deliverables/assets/" in normalized
    ):
        return True

    return False


def fmt_size(size: int) -> str:
    if size >= 1_000_000:
        return f"{size / 1_000_000:.1f} MB"
    return f"{size / 1_000:.0f} KB"


def main() -> int:
    blocked: list[tuple[str, int, str]] = []
    warnings: list[tuple[str, int]] = []

    for path in staged_files():
        size = staged_size(path)
        if size is None:
            continue
        if is_local_project_artifact(path):
            blocked.append((path, size, "project source/binary artifact should stay local"))
        elif size >= BLOCK_BYTES:
            blocked.append((path, size, f"staged file exceeds {fmt_size(BLOCK_BYTES)}"))
        elif size >= WARN_BYTES:
            warnings.append((path, size))

    if warnings:
        print("Large staged files detected (warning only):")
        for path, size in warnings:
            print(f"  - {path} ({fmt_size(size)})")
        print("")

    if not blocked:
        return 0

    print("Large or local-only staged files are blocked:", file=sys.stderr)
    for path, size, reason in blocked:
        print(f"  - {path} ({fmt_size(size)}): {reason}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Move source material to an ignored local path, or commit a lightweight md/html derivative instead.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
