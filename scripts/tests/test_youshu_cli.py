"""youshu_cli 新子命令纯函数测试：es 服务端搜索 payload / 结果提取 / 渲染 / flush-cache payload。"""

from types import SimpleNamespace

from youshu_cli import cmd_flush_cache, es_search_reports, print_es_results


def _fake_api(responses):
    """返回一个 api_request 替身：按调用顺序返回预置响应。"""
    calls = []

    def fake(base_url, method, path, payload=None, params=None):
        calls.append({"method": method, "path": path, "payload": payload, "params": params})
        return responses.pop(0)

    return fake, calls


# ── es_search_reports ──────────────────────────────────────────

def test_es_search_payload_required_fields(monkeypatch):
    fake, calls = _fake_api([{"result": []}])
    monkeypatch.setattr("youshu_cli.api_request", fake)
    assert es_search_reports("https://bi.example.com", "tok", 2, "合约") == []
    assert calls[0]["method"] == "POST"
    assert calls[0]["path"] == "/api/dash/es/searchReport"
    assert calls[0]["payload"] == {"token": "tok", "projectId": 2, "reportKeyword": "合约"}


def test_es_search_payload_optional_keywords(monkeypatch):
    fake, calls = _fake_api([{"result": []}])
    monkeypatch.setattr("youshu_cli.api_request", fake)
    es_search_reports("https://bi.example.com", "tok", 2, "收益", measure="利润", dimension="地区")
    assert calls[0]["payload"]["measureKeyword"] == "利润"
    assert calls[0]["payload"]["dimensionKeyword"] == "地区"


def test_es_search_extracts_result_list(monkeypatch):
    hits = [{"reportId": 134, "reportName": "超市"}]
    fake, _ = _fake_api([{"result": hits}])
    monkeypatch.setattr("youshu_cli.api_request", fake)
    assert es_search_reports("https://bi.example.com", "tok", 2, "超市") == hits


def test_es_search_empty_result_dict(monkeypatch):
    # api_request 的 `result.get("result") or result` 怪癖：空列表时返回整个 dict
    fake, _ = _fake_api([{"result": []}])
    monkeypatch.setattr("youshu_cli.api_request", fake)
    assert es_search_reports("https://bi.example.com", "tok", 2, "无") == []


# ── print_es_results ───────────────────────────────────────────

def test_print_es_results_empty(capsys):
    print_es_results([], "无")
    assert "命中 0 个报告" in capsys.readouterr().out


def test_print_es_results_table(capsys):
    hits = [{
        "reportId": 134,
        "reportName": "超市分析",
        "componentHighlights": [
            {"componentTitle": "利润(按地区划分)", "matchMeasures": ["利润"]},
        ],
    }]
    print_es_results(hits, "超市")
    out = capsys.readouterr().out
    assert "超市分析" in out
    assert "134" in out
    assert "利润(按地区划分)" in out


def test_print_es_results_no_highlights(capsys):
    print_es_results([{"reportId": 1, "reportName": "A", "componentHighlights": []}], "A")
    out = capsys.readouterr().out
    assert "A" in out
    assert "download <URL>" in out


# ── cmd_flush_cache ────────────────────────────────────────────

def test_flush_cache_payload_required(monkeypatch):
    fake, calls = _fake_api([{"code": 200}])
    monkeypatch.setattr("youshu_cli.api_request", fake)
    monkeypatch.setattr("youshu_cli.get_token", lambda args: "tok")
    monkeypatch.setattr("youshu_cli.resolve_config", lambda args: ("https://bi.example.com", "", 2))
    args = SimpleNamespace(data_connection_id=700310511, table="bigviz_user", database=None)
    cmd_flush_cache(args)
    assert calls[0]["path"] == "/api/dash/cacheTask/flushByTable"
    assert calls[0]["payload"] == {"token": "tok", "dataConnectionId": 700310511,
                                   "tableName": "bigviz_user"}
    assert "database" not in calls[0]["payload"]


def test_flush_cache_payload_with_database(monkeypatch, capsys):
    fake, calls = _fake_api([{"code": 200, "result": 20}])
    monkeypatch.setattr("youshu_cli.api_request", fake)
    monkeypatch.setattr("youshu_cli.get_token", lambda args: "tok")
    monkeypatch.setattr("youshu_cli.resolve_config", lambda args: ("https://bi.example.com", "", 2))
    args = SimpleNamespace(data_connection_id=1, table="t", database="dev")
    cmd_flush_cache(args)
    assert calls[0]["payload"]["database"] == "dev"
    assert "缓存刷新完成" in capsys.readouterr().out
