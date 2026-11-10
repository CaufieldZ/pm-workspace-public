"""projects/moderation/scripts/jev_client 测试：低质量判定解析 / 共享 state / 回退 / 致命错误。"""

import sys
from pathlib import Path

import pytest

MOD = str(Path(__file__).resolve().parents[2] / "projects/moderation/scripts")
if MOD not in sys.path:
    sys.path.insert(0, MOD)

import jev_client  # noqa: E402


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.text = str(payload)

    def json(self):
        return self._payload


def full_answers(prefix="", divert=0.9, value=2.0):
    out = {f"{prefix}{h}": {"type": "noul", "noul": 0.05} for h in jev_client.HARMS}
    out[f"{prefix}divert"] = {"type": "noul", "noul": divert}
    out[f"{prefix}value"] = {"type": "score", "score": value, "confidence": 0.8,
                             "probabilities": {"0": 0, "1": 0, "2": 1, "3": 0}}
    return out


def payload(answers):
    return {"answers": answers, "usage": {"input_tokens": 100}, "model": "jev-1.14.0"}


@pytest.fixture(autouse=True)
def key(monkeypatch):
    monkeypatch.setenv("JEV_API_KEY", "test")
    monkeypatch.setattr(jev_client.time, "sleep", lambda s: None)


def test_judge_one_parses_harm_and_value(monkeypatch):
    monkeypatch.setattr(jev_client.requests, "post",
                        lambda *a, **k: FakeResponse(payload(full_answers())))
    rec = jev_client.judge_one({"text": "加我微信", "scene": "IM"})
    assert rec["harm"]["divert"] == 0.9
    assert rec["harm_max"] == 0.9
    assert rec["value"] == 2.0


def test_item_view_splits_title_and_body():
    view = jev_client.item_view({"text": "公🀄浩：XX__&__正文", "scene": "COMMUNITY"})
    assert view == {"scene": "社区帖子", "title": "公🀄浩：XX", "body": "正文"}
    assert "title" not in jev_client.item_view({"text": "只有正文", "scene": "IM"})


def test_judge_shared_splits_usage_and_falls_back(monkeypatch):
    calls = []

    def fake_post(url, json, **kwargs):
        calls.append(json)
        if "items" in json["state"]:
            # 第二条缺项 → 应逐条回退
            return FakeResponse(payload(full_answers("0_", divert=0.1)))
        return FakeResponse(payload(full_answers(divert=0.95)))

    monkeypatch.setattr(jev_client.requests, "post", fake_post)
    items = [{"text": "a", "scene": "IM"}, {"text": "b", "scene": "IM"}]
    recs = jev_client.judge_shared(items)
    assert recs[0]["harm"]["divert"] == 0.1
    assert recs[0]["usage"]["input_tokens"] == 50
    assert recs[1]["harm"]["divert"] == 0.95
    assert len(calls) == 2
    assert "rubric" in calls[0]["state"]


def test_fatal_status_raises_without_retry(monkeypatch):
    calls = []

    def fake_post(*a, **k):
        calls.append(1)
        return FakeResponse({"error": "bad key"}, status=401)

    monkeypatch.setattr(jev_client.requests, "post", fake_post)
    with pytest.raises(jev_client.JevFatal):
        jev_client.judge_one({"text": "x", "scene": "IM"})
    assert len(calls) == 1


def test_transient_failure_becomes_error_record(monkeypatch):
    monkeypatch.setattr(jev_client.requests, "post",
                        lambda *a, **k: FakeResponse({}, status=503))
    rec = jev_client.judge_one({"text": "x", "scene": "IM"}, retries=2)
    assert "error" in rec


def test_iter_judge_stops_after_error_streak(monkeypatch):
    monkeypatch.setattr(jev_client.requests, "post",
                        lambda *a, **k: FakeResponse({}, status=503))
    items = [{"text": str(i), "scene": "IM"} for i in range(10)]
    with pytest.raises(jev_client.JevUnavailable):
        list(jev_client.iter_judge(items, workers=2, retries=1, max_consecutive_errors=3))


def test_normalize_and_hash_ignore_html_and_case():
    assert jev_client.normalize("<p>加 我</p>  ") == "加 我"
    assert jev_client.text_hash("ABC") == jev_client.text_hash("<b>abc</b>")
