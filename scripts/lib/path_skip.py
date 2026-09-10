"""产物 lint 的跳过规则（二进制 / 资源后缀 + 非内容目录段）。

调用方：check_cjk_punct.py / check_plain_language.py
"""
from pathlib import Path

SKIP_FILE_SUFFIXES = {".docx", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip",
                      ".pyc", ".woff", ".woff2", ".ttf", ".ico", ".svg"}
SKIP_DIR_NAMES = {"__pycache__", "node_modules", ".git", "archive", ".public",
                  "_site", "lib", "dist", "build"}


def is_skipped(path: Path) -> bool:
    """二进制 / 资源后缀，或路径含非内容目录段 → 跳过 lint。"""
    if path.suffix.lower() in SKIP_FILE_SUFFIXES:
        return True
    return any(part in SKIP_DIR_NAMES for part in path.parts)
