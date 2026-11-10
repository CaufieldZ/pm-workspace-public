"""projects/moderation/scripts 语料管线测试：corpus 去重计数 / library 匹配语义 / label_corpus 续跑合并。"""

import json
import sys
from pathlib import Path

import openpyxl
import pytest

MOD = str(Path(__file__).resolve().parents[2] / "projects/moderation/scripts")
if MOD not in sys.path:
    sys.path.insert(0, MOD)

import corpus  # noqa: E402
import label_corpus  # noqa: E402
import library  # noqa: E402

EXPORT_HEADER = ["文本内容", "产品名称", "业务名称", "TaskId", "操作类型", "审核轮数", "数据标识",
                 "机审结果状态", "机审命中类型-一级标签", "命中内容", "自定义策略"]


def write_export(path, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(EXPORT_HEADER)
    for text, scene, status, hits, strategy in rows:
        ws.append([text, "p", "普通文本", "t", "平台机器检测", "0", f"{scene}-1-X", status,
                   "广告" if status != "通过" else "正常", hits, strategy])
    wb.save(path)


def test_corpus_counts_repeats_and_excludes_customer(tmp_path):
    path = tmp_path / "e.xlsx"
    write_export(path, [
        ("<p>加我 微信</p>", "IM", "不通过", "微信", "关键词名单"),
        ("加我  微信", "IM", "通过", "", ""),
        ("您好，客服在线", "CUSTOMER", "通过", "", ""),
        ("BTC 看涨", "COMMUNITY", "通过", "", ""),
    ])
    data = corpus.load([path])
    by_text = {corpus.normalize(it["text"]): it for it in data}
    item = by_text["加我 微信"]
    assert item["count"] == 2
    assert item["blocked"] and item["keyword_hit"]
    assert item["hits"] == ["微信"]
    assert "您好，客服在线" not in by_text
    assert data[0]["count"] == 2


def write_library(path, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["关键词导出：x"])
    ws.append(["关键词", "关键词类型", "作用范围", "垃圾类型", "状态", "近7天命中次数", "更新时间",
               "最新操作人", "失效时间", "备注", "返回结果", "匹配方式"])
    for word, typ, match, status, updated in rows:
        ws.append([word, typ, "普通文本", "广告", status, 0, updated, "x", "永久有效", "", "不通过", match])
    wb.save(path)


def test_library_match_semantics(tmp_path):
    path = tmp_path / "lib.xlsx"
    write_library(path, [
        ("加微", "普通词", "默认匹配", "已生效", "2026-08-01"),
        ("tt", "普通词", "精确匹配", "已生效", "2026-08-01"),
        ("(波场+垃圾)", "普通组合词", "默认匹配", "已生效", "2026-08-01"),
        ("停用词", "普通词", "默认匹配", "已失效", "2026-08-01"),
        ("新词", "普通词", "默认匹配", "已生效", "2026-11-03"),
    ])
    lib = library.load(path)
    assert lib.covers("请加微好友")
    assert not lib.covers("twitter 上看到")
    assert lib.covers("TT")
    assert lib.covers("波场真是垃圾")
    assert not lib.covers("停用词")
    assert lib.covers("新词", active=lambda e: e["updated"] >= "2026-11-01")
    assert not lib.covers("加微", active=lambda e: e["updated"] >= "2026-11-01")
    assert lib.contains_any("快来加微领取") == "加微"


def test_load_labels_prefers_stage_two(tmp_path):
    path = tmp_path / "q.jsonl"
    rows = [
        {"hash": "a", "stage": 1, "harm_max": 0.6, "model": "m"},
        {"hash": "a", "stage": 2, "harm_max": 0.9, "model": "m"},
        {"hash": "b", "stage": 1, "harm_max": 0.1, "model": "m"},
        {"hash": "c", "stage": 1, "error": "x"},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    labels = label_corpus.load_labels(path)
    assert labels["a"]["stage"] == 2 and labels["a"]["harm_max"] == 0.9
    assert set(labels) == {"a", "b"}
    done = label_corpus.load_done(path, "m")
    assert set(done[1]) == {"a", "b"} and done[2] == {"a"}


def test_load_done_rejects_model_change(tmp_path):
    path = tmp_path / "q.jsonl"
    path.write_text(json.dumps({"hash": "a", "stage": 1, "harm_max": 0.1, "model": "old"}) + "\n")
    with pytest.raises(SystemExit):
        label_corpus.load_done(path, "new")
