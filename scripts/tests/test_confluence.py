"""lib.confluence 重试语义测试：_should_retry 矩阵 / 退避 / mock opener 重试冒烟 / 401 提示 / 禁代理。"""

import urllib.error

import pytest
from lib.confluence import (
    _OPENER,
    _RETRY_MAX,
    _backoff_delay,
    _requests_session,
    _should_retry,
    api_request,
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
