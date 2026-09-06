#!/usr/bin/env python3
"""hx-cli 调用封装（被 hx_task_progress / hx_panel / sync_hx_status import）。

职责：
- 按平台选二进制（macos universal / linux amd64），从 __file__ 上溯 skill 目录，不硬编码路径。
- 跑命令 → 解析单行 JSON stdout → 按 troubleshooting.md 错误码抛类型化异常。
- auth bootstrap 助手：status 判 logged_in，未登录 / session 过期给可执行的 GA 提示。

只读封装。写操作（work create/transition/update-progress、repo flow tag/mr/merge）不在此抽象，
按 SKILL.md 后果确认协议逐步人工确认，脚本化会架空确认。

public API：
    run(cmd_args, token=None) -> dict          # 跑一条命令，返回 data；失败抛 HxError 子类
    ensure_auth(token=None) -> dict             # status 检查，返回 status data；未登录抛 HxAuthError
    WEB_BASE                                    # https://INTERNAL_URL_REDACTED
    work_link(work_id) -> str                   # 工作项详情用户链接
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

WEB_BASE = "https://INTERNAL_URL_REDACTED"


# ── 异常类型（对齐 troubleshooting.md 错误码）─────────────────────────────

class HxError(Exception):
    """hx-cli 调用失败基类。"""

    def __init__(self, code: str, msg: str, cmd: str = ""):
        self.code = code
        self.msg = msg
        self.cmd = cmd
        super().__init__(f"[{code}] {msg}" + (f"（cmd={cmd}）" if cmd else ""))


class HxAuthError(HxError):
    """not_logged_in / unauthorized / session_expired —— 需要用户补 token 或 GA 码。

    hint 给可直接照做的下一步。
    """

    def __init__(self, code: str, msg: str, cmd: str = "", hint: str = ""):
        super().__init__(code, msg, cmd)
        self.hint = hint


# ── 二进制定位 ────────────────────────────────────────────────────────────

def _skill_dir() -> Path:
    """scripts/ 的父目录 = skill 根（二进制与 SKILL.md 所在处）。"""
    return Path(__file__).resolve().parent.parent


def _binary() -> Path:
    sysname = platform.system()
    if sysname == "Darwin":
        name = "hx-cli-macos"
    elif sysname == "Linux":
        name = "hx-cli-linux"
    else:
        raise HxError("platform_error", f"不支持的平台 {sysname}（仅 macOS / Linux amd64）")
    binpath = _skill_dir() / name
    if not binpath.exists():
        raise HxError("binary_missing", f"未找到二进制 {binpath}（skill 是否完整解压？）")
    return binpath


# ── 命令执行 ──────────────────────────────────────────────────────────────

def _auth_hint(code: str, msg: str) -> str:
    if code == "not_logged_in":
        return "设置环境变量 AIHUB_TOKEN（或 source .env），或对单次命令传 --token。"
    if "40104" in msg or "未绑定 GA" in msg:
        return "先跑 `auth ga bindreq` 拿二维码/密钥绑定，再 `auth ga bindconfirm --ga-code <6位码>`。"
    if code == "session_expired" or "40102" in msg or "Session 已过期" in msg:
        return "打开 TOTP APP，用当前 6 位 GA 码跑 `auth login --ga-code <code>`（session 30min）。"
    if code == "unauthorized":
        return "AIHUB token 可能失效/无权限，去 AIHUB 平台刷新 token 后重试。"
    return ""


def run(cmd_args: list[str], token: str | None = None) -> dict:
    """跑一条 hx-cli 命令，返回解析后的 data 字段（dict）。

    cmd_args: 不含二进制名，如 ["work", "get", "402040"]。
    token: 覆盖 AIHUB_TOKEN，仅本次生效。
    失败按错误码抛 HxAuthError（认证类）或 HxError（其余）。
    """
    argv = [str(_binary())]
    if token:
        argv += ["--token", token]
    argv += cmd_args
    cmd_str = " ".join(cmd_args)

    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired as exc:
        raise HxError("network_error", "hx-cli 调用超时（60s）", cmd_str) from exc

    out = proc.stdout.strip()
    if not out:
        raise HxError(
            "empty_output",
            f"hx-cli 无 stdout（exit={proc.returncode}）；stderr 末尾：{proc.stderr.strip()[-300:]}",
            cmd_str,
        )
    try:
        payload = json.loads(out.splitlines()[-1])
    except json.JSONDecodeError as exc:
        raise HxError("decode_error", f"stdout 非 JSON：{out[:300]}", cmd_str) from exc

    if payload.get("status") == "ok":
        return payload.get("data") or {}

    code = payload.get("code", "api_error")
    msg = payload.get("msg", "未知错误")
    if code in ("not_logged_in", "unauthorized", "session_expired") or "40102" in msg or "40104" in msg:
        raise HxAuthError(code, msg, cmd_str, hint=_auth_hint(code, msg))
    raise HxError(code, msg, cmd_str)


def ensure_auth(token: str | None = None) -> dict:
    """跑 status，确认已登录。未登录抛 HxAuthError（带 hint）。返回 status data。"""
    data = run(["status"], token=token)
    if not data.get("logged_in"):
        raise HxAuthError(
            "not_logged_in",
            "AIHUB token 不存在或未登录",
            "status",
            hint=_auth_hint("not_logged_in", ""),
        )
    return data


# ── 用户链接 ──────────────────────────────────────────────────────────────

def work_link(work_id: str | int) -> str:
    """工作项详情用户可点击链接（裸 /<work_id>，前端复制任务链接格式）。"""
    return f"{WEB_BASE}{work_id}"


if __name__ == "__main__":
    # 自测：跑 status，打印认证态。
    try:
        d = run(sys.argv[1:] or ["status"])
        print(json.dumps(d, ensure_ascii=False, indent=2))
    except HxAuthError as e:
        print(f"认证失败：{e}\n下一步：{e.hint}", file=sys.stderr)
        sys.exit(2)
    except HxError as e:
        print(f"调用失败：{e}", file=sys.stderr)
        sys.exit(1)
