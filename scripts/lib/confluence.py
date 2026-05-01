#!/usr/bin/env python3
"""Confluence REST API 共享模块。

从 .mcp.json / .mcp-disabled.json 读取凭据，提供 urllib 版 REST 封装。
push_to_confluence_base.py 的 multipart upload 仍用 requests，本模块只覆盖 JSON API。
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_BASE_URL: str | None = None
_TOKEN: str | None = None


def load_creds() -> tuple[str, str]:
    """从 .mcp.json / .mcp-disabled.json 读取 CONF_BASE_URL + CONF_TOKEN。

    向上查找到 pm-workspace 根目录（含 .mcp.json 的最近祖先）。
    """
    for p in Path(__file__).resolve().parents:
        for fname in (".mcp.json", ".mcp-disabled.json"):
            cand = p / fname
            if not cand.exists():
                continue
            env = (
                json.loads(cand.read_text())
                .get("mcpServers", {})
                .get("confluence", {})
                .get("env")
            )
            if env and env.get("CONF_BASE_URL") and env.get("CONF_TOKEN"):
                return env["CONF_BASE_URL"].rstrip("/"), env["CONF_TOKEN"]
    sys.exit("找不到 confluence 凭据（.mcp.json 和 .mcp-disabled.json 都没有 env）")


def _ensure_creds():
    global _BASE_URL, _TOKEN
    if _BASE_URL is None:
        _BASE_URL, _TOKEN = load_creds()


def base_url() -> str:
    _ensure_creds()
    return _BASE_URL


def api_request(method: str, path: str, body: dict | None = None) -> dict:
    """带 auth 的 REST 请求。path 为完整路径（如 /rest/api/content）。"""
    _ensure_creds()
    url = f"{_BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {_TOKEN}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"Confluence HTTP {e.code}: {e.read().decode()[:500]}\n")
        raise


def get_page(page_id: str, expand: str = "version,space") -> dict:
    return api_request("GET", f"/rest/api/content/{page_id}?expand={expand}")


def create_page(
    space: str, title: str, body: str, parent_id: str | None = None
) -> dict:
    payload: dict = {
        "type": "page",
        "title": title,
        "space": {"key": space},
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    if parent_id:
        payload["ancestors"] = [{"id": str(parent_id)}]
    return api_request("POST", "/rest/api/content", payload)


def update_page(page_id: str, title: str | None, body: str) -> dict:
    current = get_page(page_id)
    payload = {
        "type": "page",
        "title": title or current["title"],
        "space": {"key": current["space"]["key"]},
        "version": {"number": current["version"]["number"] + 1},
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    return api_request("PUT", f"/rest/api/content/{page_id}", payload)


def search_pages(cql: str, limit: int = 10) -> list:
    _ensure_creds()
    encoded = urllib.parse.quote(cql)
    data = api_request(
        "GET",
        f"/rest/api/content/search?cql={encoded}&limit={limit}&orderby=created+desc",
    )
    return data.get("results", [])
