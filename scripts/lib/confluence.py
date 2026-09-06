#!/usr/bin/env python3
"""Confluence REST API 共享模块。

从 .mcp.json / .mcp-disabled.json 读取凭据，提供 urllib 版 REST 封装。
upload_attachment 用 requests 做 multipart 上传（附件 upsert）。
"""
from __future__ import annotations

import json
import mimetypes
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from lib.env_refs import apply_env_file, expand_refs

_BASE_URL: str | None = None
_TOKEN: str | None = None

# REST 调用默认超时（秒）：无超时时半开连接 / LB 抽风会让整个推送无限挂起
_HTTP_TIMEOUT = 30

# 重试语义（借鉴 confluence-cli）：429 全方法可重试；503 只重放读方法
_RETRY_MAX = 4  # 1 次直连 + 3 次重试
_RETRY_BASE_DELAY = 1.0
_RETRY_MAX_DELAY = 60.0


def load_creds() -> tuple[str, str]:
    """读取 CONF_BASE_URL + CONF_TOKEN。

    查找顺序：env var（开发推荐，不依赖私有配置）→ .mcp.json → .mcp-disabled.json
    （向上查找到含配置的最近祖先）。
    """
    env_base = os.environ.get("CONF_BASE_URL", "").rstrip("/")
    env_tok = os.environ.get("CONF_TOKEN", "")
    if env_base and env_tok:
        return env_base, env_tok
    for p in Path(__file__).resolve().parents:
        for fname in (".mcp.json", ".mcp-disabled.json"):
            cand = p / fname
            if not cand.exists():
                continue
            env = (
                json.loads(cand.read_text(encoding="utf-8"))
                .get("mcpServers", {})
                .get("confluence", {})
                .get("env")
            )
            if env:
                apply_env_file(p / ".env")
                env = expand_refs(env)
            if env and env.get("CONF_BASE_URL") and env.get("CONF_TOKEN"):
                return env["CONF_BASE_URL"].rstrip("/"), env["CONF_TOKEN"]
    sys.exit("找不到 confluence 凭据（env var CONF_BASE_URL/CONF_TOKEN，或 .mcp.json / .mcp-disabled.json 的 confluence.env）")


def _ensure_creds():
    global _BASE_URL, _TOKEN
    if _BASE_URL is None:
        _BASE_URL, _TOKEN = load_creds()


def base_url() -> str:
    _ensure_creds()
    assert _BASE_URL is not None  # _ensure_creds 保证已加载（load_creds 失败 sys.exit）
    return _BASE_URL


def _should_retry(method: str, code: int) -> bool:
    """429 全方法可重试；503 只重放读方法（写可能已被后端应用，重放有重复创建风险）。"""
    if code == 429:
        return True
    if code == 503:
        return method.upper() in ("GET", "HEAD")
    return False


def _backoff_delay(attempt: int, retry_after: str | None = None) -> float:
    """指数退避（1s 起，60s 封顶，带 ±20% 抖动）。有 Retry-After 头时按服务端指示。"""
    if retry_after is not None:
        try:
            return min(max(0.0, float(retry_after)), _RETRY_MAX_DELAY)
        except ValueError:
            pass
    delay = _RETRY_BASE_DELAY * (2 ** attempt) * (0.8 + 0.4 * random.random())
    return min(delay, _RETRY_MAX_DELAY)


# 显式禁代理的 opener：Confluence 是内网资源，env 里若有 ALL_PROXY 也不该被甩去代理
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _request_with_retry(method: str, url: str, data: bytes | None,
                        headers: dict | None, timeout: int) -> tuple[int, dict, bytes]:
    """urlopen 包装：429 / 503(读) 自动重试，指数退避，重试耗尽原样 raise。返回 (status, headers, body)。"""
    attempt = 0
    while True:
        req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
        try:
            with _OPENER.open(req, timeout=timeout) as resp:
                return resp.status, dict(resp.headers.items()), resp.read()
        except urllib.error.HTTPError as e:
            if attempt < _RETRY_MAX - 1 and _should_retry(method, e.code):
                wait = _backoff_delay(attempt, e.headers.get("Retry-After") if e.headers else None)
                sys.stderr.write(
                    f"Confluence HTTP {e.code}（第 {attempt + 1} 次重试，{wait:.1f}s 后）\n"
                )
                time.sleep(wait)
                attempt += 1
                continue
            raise


def api_request(method: str, path: str, body: dict | None = None, headers: dict | None = None) -> dict:
    """带 auth 的 REST 请求。path 为完整路径（如 /rest/api/content）。
    headers 透传额外请求头（如 Accept），向后兼容（默认 None 不加）。"""
    _ensure_creds()
    url = f"{_BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req_headers = {"Authorization": f"Bearer {_TOKEN}", "Content-Type": "application/json"}
    for k, v in (headers or {}).items():
        req_headers[k] = v
    try:
        _, _, raw = _request_with_retry(method, url, data, req_headers, _HTTP_TIMEOUT)
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # 200 但非 JSON：登录跳转 / WAF 拦截 / 维护页。裸 JSONDecodeError 不带任何
            # 上下文，调用方无从判断，转成带响应片段的 URLError。
            snippet = raw[:300].decode("utf-8", errors="replace")
            raise urllib.error.URLError(
                f"Confluence 返回非 JSON（{url}）：{snippet!r}\n"
                "  多半是 token 失效跳登录页 / 反向代理拦截，检查 CONF_TOKEN"
            ) from None
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.stderr.write(
                "Confluence 认证失败（401）：CONF_TOKEN 失效或无权访问\n"
                "  检查 env CONF_BASE_URL/CONF_TOKEN 或 .mcp.json / .mcp-disabled.json 的 confluence.env，"
                "必要时重新生成 token\n"
            )
            raise
        # decode 不带 errors 时非 UTF-8 错误页会抛 UnicodeDecodeError，把原始 HTTP 状态码吃掉
        sys.stderr.write(f"Confluence HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:500]}\n")
        raise
    except urllib.error.URLError as e:
        sys.stderr.write(f"Confluence 请求失败 ({e})\n")
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


def search_pages(cql: str, limit: int = 10, expand: str | None = None) -> list:
    _ensure_creds()
    encoded = urllib.parse.quote(cql)
    path = f"/rest/api/content/search?cql={encoded}&limit={limit}"
    if expand:
        path += f"&expand={urllib.parse.quote(expand)}"
    data = api_request("GET", path)
    return data.get("results", [])


def add_label(page_id: str, name: str) -> None:
    """给页面打全局标签（重复打幂等，已存在时 Confluence 原样返回不报错）。

    检索走 CQL：space=KEY AND label="pm-community"。
    """
    api_request("POST", f"/rest/api/content/{page_id}/label",
                [{"prefix": "global", "name": name}])


def set_content_property(page_id: str, key: str, value) -> None:
    """在页面上挂结构化元数据（upsert：已存在则带 property 乐观锁版本号 PUT 覆盖）。

    与正文 magic 行（> Confluence v2 | pageId: xxx）互补：property 机器可查
    （GET /rest/api/content/{id}/property/{key}），无需解析正文。
    探测用 request_raw：404（不存在）/ 200 是预期分支，不走 api_request 的 stderr 诊断打印。
    PUT 的 version 必须是 {"number": current+1}（对象非整数，缺 +1 报 409）。
    """
    status, _, raw = request_raw("GET", f"/rest/api/content/{page_id}/property/{key}")
    body: dict = {"key": key, "value": value}
    if status == 200:
        try:
            cur_ver = json.loads(raw).get("version", {}).get("number", 0)
        except json.JSONDecodeError:
            cur_ver = 0
        body["version"] = {"number": cur_ver + 1}
        api_request("PUT", f"/rest/api/content/{page_id}/property/{key}", body)
    else:
        api_request("POST", f"/rest/api/content/{page_id}/property", body)


_SESSION: requests.Session | None = None


def _requests_session() -> requests.Session:
    """进程内共享 session：429/503 自动重试。附件 upsert 幂等，写路径也重试（allowed_methods=None）。

    trust_env=False：内网直连，不读环境代理变量（.env 注入的 ALL_PROXY 不作用于 Confluence）。
    模块级缓存：一次推 N 张图不再每张新建 session。
    """
    global _SESSION
    if _SESSION is None:
        session = requests.Session()
        session.trust_env = False
        retry = Retry(total=3, status_forcelist=(429, 503), allowed_methods=None, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        _SESSION = session
    return _SESSION


def upload_attachment(page_id: str, filename: str, data: bytes, mime: str = "image/png",
                      minor_edit: bool = False):
    """上传图片附件到 Confluence 页面，已存在则更新（upsert）。

    minor_edit=True 时 multipart 带 minorEdit 字段，附件更新不通知 watcher。
    """
    _ensure_creds()
    assert _BASE_URL is not None and _TOKEN is not None  # _ensure_creds 保证已加载
    _headers = {"Authorization": f"Bearer {_TOKEN}"}
    att_base = f"{_BASE_URL}/rest/api/content/{page_id}/child/attachment"
    headers = {**_headers, "X-Atlassian-Token": "no-check"}

    resp = _requests_session().get(att_base, headers=_headers,
                                   params={"filename": filename}, timeout=_HTTP_TIMEOUT)
    resp.raise_for_status()  # 错误页（HTML 登录跳转 / 500）先炸出状态，不让 .json() 吞成空
    existing = resp.json().get("results", [])
    if existing:
        att_id = existing[0]["id"]
        url = f"{att_base}/{att_id}/data"
    else:
        url = att_base

    files = {"file": (filename, data, mime)}
    if minor_edit:
        files["minorEdit"] = (None, "true")
    _requests_session().post(url, headers=headers,
                             files=files,
                             timeout=_HTTP_TIMEOUT).raise_for_status()


def request_raw(method: str, path: str, body: bytes | None = None,
                headers: dict | None = None) -> tuple[int, dict, bytes]:
    """透传原始请求，返回 (HTTP status, 响应头, raw bytes)。非 JSON / 错误响应不炸。

    与 api_request 的区别：不解析 JSON、HTTPError 也原样返回（状态码+响应体），
    供 confluence_api.py 透传命令使用。path 为相对路径时拼 base_url；
    已是完整 URL（同源校验过的绝对地址）则直接用，不再拼接。
    """
    _ensure_creds()
    url = path if path.startswith(("http://", "https://")) else f"{_BASE_URL}{path}"
    req_headers = {"Authorization": f"Bearer {_TOKEN}"}
    for k, v in (headers or {}).items():
        req_headers[k] = v
    try:
        return _request_with_retry(method, url, body, req_headers, _HTTP_TIMEOUT)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers.items()), e.read()


def api_get(path: str, headers: dict | None = None) -> dict:
    """GET JSON 请求，默认带 Accept: application/json（fetch_confluence 行为）。"""
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    return api_request("GET", path, headers=h)


def download_bytes(path: str, timeout: int = 60) -> bytes:
    """下载附件二进制（urlopen 返回 raw bytes）。失败 raise URLError。"""
    _ensure_creds()
    url = f"{_BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {_TOKEN}"})
    try:
        with _OPENER.open(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.URLError as e:
        sys.stderr.write(f"Confluence download 失败 ({e})\n")
        raise


def fetch_attachments(page_id: str, download: bool = False, filter_names: set | None = None) -> dict:
    """获取页面附件列表（分页 LIMIT=50，用 len(results)<LIMIT 终止，不依赖 totalCount）。

    返回 {filename: {dl_path, mime, bytes?}}。filter_names 非空时只处理集合内名字
    （Confluence attachment 仓库含历史版本 + 未引用图，传 storage 实际引用集合避免下垃圾图）。
    """
    LIMIT = 50
    mapping: dict = {}
    start = 0
    while True:
        data = api_get(f"/rest/api/content/{page_id}/child/attachment?start={start}&limit={LIMIT}")
        results = data.get("results", [])
        for att in results:
            fname = att["title"]
            if not re.search(r"\.(png|jpg|jpeg|gif|svg|webp)$", fname, re.I):
                continue
            if filter_names is not None and fname not in filter_names:
                continue
            dl_path = att["_links"]["download"]
            mime = mimetypes.guess_type(fname)[0] or "image/png"
            entry: dict = {"dl_path": dl_path, "mime": mime}
            if download:
                entry["bytes"] = download_bytes(dl_path)
                print(f"  图片: {fname} ({len(entry['bytes']) // 1024}KB)", file=sys.stderr)
            mapping[fname] = entry
        if len(results) < LIMIT:
            break
        start += LIMIT
    return mapping


def list_child_pages(parent_id: str, limit: int = 100) -> list:
    """轻量列直接子页（只拿 title + _links，不拉 body）。树导航专用。

    fetch_children 强制 expand=body.storage 用于回流正文，树形导航不需要正文，
    拉 body 在大子树下浪费大量带宽 / token。分页 len<limit 终止。
    """
    children = []
    start = 0
    while True:
        res = api_get(
            f"/rest/api/content/{parent_id}/child/page?limit={limit}&start={start}"
        )
        results = res.get("results", [])
        children.extend(results)
        if len(results) < limit:
            break
        start += limit
    return children


def fetch_children(parent_id: str, limit: int = 50) -> list:
    """拿父页所有直接子页（按 wiki position 排序，含 body.storage, version）。

    返回 [{id, title, version, body.storage.value, ...}, ...]。分页 len<limit 终止。
    """
    children = []
    start = 0
    while True:
        res = api_get(
            f"/rest/api/content/{parent_id}/child/page"
            f"?expand=body.storage,version&limit={limit}&start={start}"
        )
        results = res.get("results", [])
        children.extend(results)
        if len(results) < limit:
            break
        start += limit
    return children
