"""Keychain 凭据 JSON 读写（security 命令包装）。

调用方：
- scripts/slack.py（Slack MCP OAuth：plugin:slack 前缀过滤 + Slack 端点刷新）
- scripts/call_mcp.py（MCP server OAuth：按 server_name 匹配 + 配置化刷新）

只做「读原始 JSON / 整包写回」，OAuth 条目过滤与刷新逻辑留在调用方（两端匹配键规则不同）。
写回是 delete + add 整包替换（与 Claude Code 插件同一 Keychain 条目，别改条目名）。
"""

from __future__ import annotations

import json
import subprocess

KEYCHAIN_SERVICE = "Claude Code-credentials"


def read_credentials() -> dict | None:
    """读 Keychain 中的凭据 JSON；条目不存在 / 解析失败返回 None。"""
    try:
        raw = subprocess.check_output(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except subprocess.CalledProcessError:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def write_credentials(data: dict) -> bool:
    """整包写回 Keychain（delete + add -U）。add 失败时回写旧值兜底，失败返回 False。"""
    payload = json.dumps(data, separators=(",", ":"))
    # 先读旧值：delete 成功而 add 失败（Keychain 锁定 / 授权弹窗被拒）时原样回写，
    # 防 MCP OAuth 凭据整包不可恢复丢失（读不到则尽力而为，仍走原流程）
    old = subprocess.run(
        ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
        capture_output=True, text=True,
    )
    old_payload = old.stdout.strip() if old.returncode == 0 else None
    subprocess.run(
        ["security", "delete-generic-password", "-s", KEYCHAIN_SERVICE],
        capture_output=True,
    )
    result = subprocess.run(
        ["security", "add-generic-password", "-s", KEYCHAIN_SERVICE,
         "-a", "Claude Key", "-w", payload, "-U"],
        capture_output=True,
    )
    if result.returncode != 0 and old_payload:
        subprocess.run(
            ["security", "add-generic-password", "-s", KEYCHAIN_SERVICE,
             "-a", "Claude Key", "-w", old_payload, "-U"],
            capture_output=True,
        )
    return result.returncode == 0
