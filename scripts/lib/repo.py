"""pm-workspace 仓库根定位。

调用方：check_baseline_fresh.py / check_rule_version_drift.py
"""
import subprocess
from pathlib import Path


def find_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
        )
        return Path(out.decode().strip())
    except Exception:
        pass
    cur = Path.cwd()
    for p in [cur, *cur.parents]:
        if (p / ".claude").is_dir() and (p / "projects").is_dir():
            return p
    raise SystemExit("无法定位 pm-workspace 根目录")
