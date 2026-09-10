"""confluence_api 透传原语测试：endpoint 规范化 / -f 解析 / body 组装 / 迷你 jq / 输出渲染。"""

import json

import pytest
from confluence_api import build_body, evaluate_jq, normalize_endpoint, parse_kv_args, render_output

# ── normalize_endpoint ──────────────────────────────────────────

def test_endpoint_relative_joins_base():
    assert normalize_endpoint("/rest/api/content/1", "https://wiki.example.com") \
        == "https://wiki.example.com/rest/api/content/1"


def test_endpoint_absolute_same_origin_passthrough():
    assert normalize_endpoint("https://wiki.example.com/rest/api/user/current",
                              "https://wiki.example.com") \
        == "https://wiki.example.com/rest/api/user/current"


def test_endpoint_absolute_cross_origin_rejected():
    with pytest.raises(ValueError):
        normalize_endpoint("https://evil.com/rest/api/content", "https://wiki.example.com")


def test_endpoint_bare_word_rejected():
    with pytest.raises(ValueError):
        normalize_endpoint("content/1", "https://wiki.example.com")


# ── parse_kv_args ───────────────────────────────────────────────

def test_parse_kv_args_scalar_and_json_literals():
    assert parse_kv_args(["a=1", "b=true", "c=hello"]) == {"a": 1, "b": True, "c": "hello"}


def test_parse_kv_args_dotted_keys_expand():
    # Confluence REST 嵌套载荷（space.key / body.storage.value）走 dotted key 展开
    assert parse_kv_args(["space.key=Platform C", "body=1"]) \
        == {"space": {"key": "Platform C"}, "body": 1}
    assert parse_kv_args(["body.storage.value=hi"]) \
        == {"body": {"storage": {"value": "hi"}}}


def test_parse_kv_args_missing_equals_rejected():
    with pytest.raises(ValueError):
        parse_kv_args(["naked"])


# ── build_body ──────────────────────────────────────────────────

def test_build_body_input_file_wins(tmp_path):
    f = tmp_path / "body.json"
    f.write_text('{"title": "x"}', encoding="utf-8")
    assert build_body(str(f), ["a=1"]) == b'{"title": "x"}'


def test_build_body_fields_only():
    assert build_body(None, ["a=1"]) == b'{"a": 1}'


def test_build_body_none_without_sources():
    assert build_body(None, []) is None


# ── request_raw 拼接语义 ─────────────────────────────────────────

def test_request_raw_absolute_url_not_double_joined(monkeypatch):
    """normalize_endpoint 已拼好绝对 URL → request_raw 不得再拼 base（曾双拼导致 Errno 8）。"""
    import lib.confluence as lc
    seen = {}

    class FakeResp:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"ok"

    class FakeOpener:
        def open(self, req, timeout=None):
            seen["url"] = req.full_url
            return FakeResp()

    monkeypatch.setattr(lc, "_BASE_URL", "https://wiki.example.com")
    monkeypatch.setattr(lc, "_TOKEN", "t")
    monkeypatch.setattr(lc, "_OPENER", FakeOpener())

    from lib.confluence import request_raw
    status, _, raw = request_raw("GET", "https://wiki.example.com/rest/api/user/current", None, {})
    assert status == 200
    assert seen["url"] == "https://wiki.example.com/rest/api/user/current"


# ── evaluate_jq ─────────────────────────────────────────────────

DATA = {
    "results": [
        {"id": "1001", "title": "A", "tags": ["x", "y"]},
        {"id": "1002", "title": "B", "tags": []},
    ],
    "total": 2,
}


def test_jq_dot_path():
    assert evaluate_jq(".total", DATA) == 2
    assert evaluate_jq(".results[0].id", DATA) == "1001"


def test_jq_expand_list():
    assert evaluate_jq(".results[].id", DATA) == ["1001", "1002"]


def test_jq_pipe_length():
    assert evaluate_jq(".results | length", DATA) == 2


def test_jq_missing_key_raises():
    with pytest.raises(KeyError):
        evaluate_jq(".nope", DATA)


def test_jq_invalid_expr_raises():
    with pytest.raises(ValueError):
        evaluate_jq("results[0]", DATA)
    with pytest.raises(ValueError):
        evaluate_jq(".results | sum", DATA)


def test_jq_expand_on_scalar_raises():
    with pytest.raises(ValueError):
        evaluate_jq(".total[]", DATA)


# ── render_output ───────────────────────────────────────────────

def test_render_pretty_json(capsys):
    assert render_output(b'{"a": 1}', None, False) == 0
    assert json.loads(capsys.readouterr().out) == {"a": 1}


def test_render_raw_text(capsys):
    assert render_output(b"hello", None, False) == 0
    assert capsys.readouterr().out == "hello"


def test_render_jq_scalar(capsys):
    assert render_output(b'{"total": 2}', ".total", False) == 0
    assert capsys.readouterr().out.strip() == "2"


def test_render_jq_list_expands_lines(capsys):
    assert render_output(json.dumps(DATA).encode(), ".results[].id", False) == 0
    assert capsys.readouterr().out.splitlines() == ["1001", "1002"]


def test_render_jq_failure_exit2(capsys):
    assert render_output(b'{"a": 1}', ".missing", False) == 2
    assert "求值失败" in capsys.readouterr().err


def test_render_jq_non_json_exit2(capsys):
    assert render_output(b"<html>login</html>", ".a", False) == 2
    assert "不是 JSON" in capsys.readouterr().err
