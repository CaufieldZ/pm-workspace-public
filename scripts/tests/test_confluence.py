"""lib.confluence 测试：重试语义矩阵 / 退避 / mock opener 重试冒烟 / 401 提示 / 禁代理 / 单次批量拉取硬顶。"""

import urllib.error

import pytest
from lib.confluence import (
    BATCH_PULL_CAP,
    _OPENER,
    _RETRY_MAX,
    _backoff_delay,
    _requests_session,
    _should_retry,
    api_request,
    fetch_attachments,
    fetch_children,
    search_pages,
)


@pytest.mark.parametrize("method,code,expected", [
    ("POST", 429, True),
    ("GET", 429, True),
    ("PUT", 429, True),
    ("GET", 503, True),
    ("HEAD", 503, True),
    ("POST", 503, False),
    ("PUT", 503, False),
    ("DELETE", 503, False),
    ("GET", 404, False),
    ("GET", 401, False),
    ("GET", 500, False),
])
def test_should_retry_matrix(method, code, expected):
    assert _should_retry(method, code) is expected


def test_backoff_delay_caps_at_max():
    for attempt in range(0, 10):
        assert _backoff_delay(attempt) <= 60.0


def test_backoff_delay_grows_with_attempt():
    assert _backoff_delay(3) > _backoff_delay(0)


def test_backoff_delay_retry_after_preferred():
    assert _backoff_delay(0, retry_after="5") == pytest.approx(5.0, abs=0.01)


def test_backoff_delay_invalid_retry_after_falls_back():
    assert _backoff_delay(0, retry_after="garbage") > 0


@pytest.fixture
def fake_creds(monkeypatch):
    monkeypatch.setattr("lib.confluence._BASE_URL", "https://wiki.example.com")
    monkeypatch.setattr("lib.confluence._TOKEN", "test-token")


def _raising_opener(codes, response=b'{"ok": true}'):
    """返回一个 opener 替身：依次抛 codes 里的状态码，最后返回 response。"""
    calls = {"n": 0}

    class FakeResp:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return response

    def fake(req, timeout):
        calls["n"] += 1
        if calls["n"] <= len(codes):
            raise urllib.error.HTTPError(req.full_url, codes[calls["n"] - 1], "Err", {}, None)
        return FakeResp()

    class FakeOpener:
        def open(self, req, timeout=None):
            return fake(req, timeout)

    return FakeOpener(), calls


def test_retries_two_429_then_succeeds(monkeypatch, fake_creds):
    opener, calls = _raising_opener([429, 429])
    monkeypatch.setattr("lib.confluence._OPENER", opener)
    monkeypatch.setattr("lib.confluence.time.sleep", lambda s: None)
    assert api_request("GET", "/rest/api/content/1") == {"ok": True}
    assert calls["n"] == 3


def test_503_read_retries(monkeypatch, fake_creds):
    opener, calls = _raising_opener([503])
    monkeypatch.setattr("lib.confluence._OPENER", opener)
    monkeypatch.setattr("lib.confluence.time.sleep", lambda s: None)
    assert api_request("GET", "/rest/api/content/1") == {"ok": True}
    assert calls["n"] == 2


def test_503_write_not_retried(monkeypatch, fake_creds):
    opener, calls = _raising_opener([503])
    monkeypatch.setattr("lib.confluence._OPENER", opener)
    monkeypatch.setattr("lib.confluence.time.sleep", lambda s: None)
    with pytest.raises(urllib.error.HTTPError) as exc:
        api_request("POST", "/rest/api/content", {"type": "page"})
    assert exc.value.code == 503
    assert calls["n"] == 1


def test_retries_exhausted_raises(monkeypatch, fake_creds, capsys):
    opener, calls = _raising_opener([429, 429, 429, 429, 429])
    monkeypatch.setattr("lib.confluence._OPENER", opener)
    monkeypatch.setattr("lib.confluence.time.sleep", lambda s: None)
    with pytest.raises(urllib.error.HTTPError):
        api_request("GET", "/rest/api/content/1")
    assert calls["n"] == _RETRY_MAX
    assert "重试" in capsys.readouterr().err


def test_401_hint_written(monkeypatch, fake_creds, capsys):
    def fake(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, None)

    class FakeOpener:
        def open(self, req, timeout=None):
            return fake(req, timeout)

    monkeypatch.setattr("lib.confluence._OPENER", FakeOpener())
    with pytest.raises(urllib.error.HTTPError):
        api_request("GET", "/rest/api/content/1")
    err = capsys.readouterr().err
    assert "401" in err
    assert "CONF_TOKEN" in err


# ── 禁代理（内网直连） ─────────────────────────────────────────

def test_opener_disables_proxy():
    """_OPENER 不含 ProxyHandler：env 里的 ALL_PROXY 不作用于 Confluence（内网直连）。

    build_opener(ProxyHandler({})) 的 skip 语义：传入的 ProxyHandler 类触发默认
    ProxyHandler 被跳过，最终 opener 无任何代理处理链。
    """
    assert not any(isinstance(h, urllib.request.ProxyHandler) for h in _OPENER.handlers)


def test_requests_session_no_proxy_env_and_retry():
    """requests 路径 trust_env=False（不读环境代理），且带 429/503 重试。"""
    s = _requests_session()
    assert s.trust_env is False
    assert s.get_adapter("https://").max_retries.total == 3


# ── 单次批量拉取硬顶（安全限制） ─────────────────────────────────

def test_search_pages_clamps_over_cap(monkeypatch, fake_creds, capsys):
    """limit 超 BATCH_PULL_CAP：请求截断为 limit=cap + stderr 告警。"""
    seen = {}

    def fake_api_request(method, path, body=None, headers=None):
        seen["path"] = path
        return {"results": []}

    monkeypatch.setattr("lib.confluence.api_request", fake_api_request)
    search_pages("cql", limit=BATCH_PULL_CAP + 10)
    assert f"limit={BATCH_PULL_CAP}" in seen["path"]
    assert "上限" in capsys.readouterr().err


def test_search_pages_under_cap_passthrough(monkeypatch, fake_creds, capsys):
    seen = {}

    def fake_api_request(method, path, body=None, headers=None):
        seen["path"] = path
        return {"results": []}

    monkeypatch.setattr("lib.confluence.api_request", fake_api_request)
    search_pages("cql", limit=10)
    assert "limit=10" in seen["path"]
    assert capsys.readouterr().err == ""


def test_fetch_children_truncates_at_cap(monkeypatch, fake_creds, capsys):
    """单页响应即满 50 个：累计达 cap 截断为 50 + 告警，不再翻页。"""
    calls = {"n": 0}

    def fake_api_get(path, headers=None):
        calls["n"] += 1
        return {"results": [{"id": str(i)} for i in range(50)]}

    monkeypatch.setattr("lib.confluence.api_get", fake_api_get)
    children = fetch_children("123")
    assert len(children) == BATCH_PULL_CAP
    assert calls["n"] == 1  # 第一页 50 个即触顶，不再翻页
    assert "上限" in capsys.readouterr().err


def test_fetch_children_under_cap_no_warn(monkeypatch, fake_creds, capsys):
    monkeypatch.setattr(
        "lib.confluence.api_get",
        lambda path, headers=None: {"results": [{"id": "1"}, {"id": "2"}]},
    )
    assert len(fetch_children("123")) == 2
    assert capsys.readouterr().err == ""


def test_fetch_attachments_download_truncates_at_cap(monkeypatch, fake_creds, capsys):
    """download=True 候选 60 张：只下前 cap 张并告警截断。"""
    calls = {"n": 0}

    def fake_api_get(path, headers=None):
        calls["n"] += 1
        return {"results": [
            {"title": f"img{i}.png", "_links": {"download": f"/dl/img{i}.png"}}
            for i in range(60)
        ]}

    monkeypatch.setattr("lib.confluence.api_get", fake_api_get)
    monkeypatch.setattr("lib.confluence.download_bytes", lambda path, timeout=60: b"x")
    mapping = fetch_attachments("123", download=True)
    assert len(mapping) == BATCH_PULL_CAP
    assert calls["n"] == 1  # 触顶即返回，不翻页
    assert "上限" in capsys.readouterr().err


def test_fetch_attachments_listing_not_capped(monkeypatch, fake_creds, capsys):
    """download=False 纯列清单（不下内容）不受硬顶。"""
    calls = {"n": 0}

    def fake_api_get(path, headers=None):
        calls["n"] += 1
        if calls["n"] > 1:
            return {"results": []}
        return {"results": [
            {"title": f"img{i}.png", "_links": {"download": f"/dl/img{i}.png"}}
            for i in range(60)
        ]}

    monkeypatch.setattr("lib.confluence.api_get", fake_api_get)
    mapping = fetch_attachments("123", download=False)
    assert len(mapping) == 60
    assert capsys.readouterr().err == ""
