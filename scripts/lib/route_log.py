"""快捷路由脚本调用埋点 - 写入 .claude/logs/usage.jsonl。

被 CLAUDE.md「快捷路由」表里的 Python 脚本调用。dashboard.py
按 type=route 聚合「快捷路由热度」section，14 天零调用 = 死路由。

调用方头部 4 行模板（含注释 1 行）：

    # route-log: scripts/lib/route_log.py
    import sys as _s, pathlib as _pl
    _r = next((p for p in _pl.Path(__file__).resolve().parents if (p/".claude").is_dir()), None)
    _r and (_s.path.insert(0, str(_r/"scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("XXX"))

设计：静默失败（埋点不能阻塞业务）、原子 append（< 4KB 单行写 POSIX 保证原子）。
"""

import datetime
import json
import os
from pathlib import Path


def _find_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / ".claude").is_dir():
            return p
    return here.parent


def emit(name: str, detail: str = "") -> None:
    try:
        root = _find_root()
        log_dir = root / ".claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        tz = datetime.timezone(datetime.timedelta(hours=8))
        ts = datetime.datetime.now(tz).isoformat(timespec="seconds")
        event = {"ts": ts, "type": "route", "name": name, "action": "triggered"}
        if detail:
            event["detail"] = detail[:200]
        sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
        if sid:
            event["session_id"] = sid
        with (log_dir / "usage.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except (OSError, PermissionError) as e:
        if os.environ.get("PM_DEBUG_LOG"):
            import sys as _sys
            print(f"[route_log] emit({name}) failed: {e}", file=_sys.stderr)
