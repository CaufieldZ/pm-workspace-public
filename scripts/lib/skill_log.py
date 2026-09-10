"""Skill 完成/失败埋点 - 写入 .claude/logs/usage.jsonl。

被 SKILL.md frontmatter scripts 字段里的 Python gen 脚本调用。
dashboard.py 按 type=skill + action=completed/failed 聚合「Skill 完成率」。

调用方尾部模板（main 成功后）：
    from lib.skill_log import emit
    emit("skill-name", True)   # 或 False 表示失败
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


def emit(name: str, success: bool = True, reason: str = None) -> None:
    try:
        root = _find_root()
        log_dir = root / ".claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        tz = datetime.timezone(datetime.timedelta(hours=8))
        ts = datetime.datetime.now(tz).isoformat(timespec="seconds")
        event = {
            "ts": ts,
            "type": "skill",
            "name": name,
            "action": "completed" if success else "failed",
        }
        if reason:
            event["detail"] = reason
        sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
        if sid:
            event["session_id"] = sid
        with (log_dir / "usage.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except (OSError, PermissionError) as e:
        if os.environ.get("PM_DEBUG_LOG"):
            import sys as _sys
            print(f"[skill_log] log_skill({name}) failed: {e}", file=_sys.stderr)
