"""market_cli 纯函数测试（归一化 / 格式化 / 渲染，无网络）。"""
import pytest
from market_cli import (
    flatten_trades,
    fmt_labels,
    fmt_price,
    fmt_qty,
    norm_symbol,
    pct,
    render_contracts,
    render_depth,
    render_kline,
    render_symbols,
    render_tickers,
)

KLINE_ROW = {
    "id": 1787241600,
    "open": 72448.78,
    "close": 77706.88,
    "low": 72198.91,
    "high": 79488.68,
    "amount": 2995.598,
    "vol": 2.266442422423582e8,
    "count": 43331,
}


@pytest.mark.parametrize(
    "raw, want",
    [
        ("BTC", "btcusdt"),
        ("BTC-USDT", "btcusdt"),
        ("BTC/USDT", "btcusdt"),
        ("btcusdt", "btcusdt"),
        ("ETH/BTC", "ethbtc"),
        ("ethbtc", "ethbtc"),
        ("pepe", "pepeusdt"),
        # 长裸 base（无计价后缀）也要补 usdt，不能按长度截断
        ("1MBABYDOGE", "1mbabydogeusdt"),
        ("HT/USDT", "htusdt"),
    ],
)
def test_norm_symbol(raw, want):
    assert norm_symbol(raw) == want


@pytest.mark.parametrize(
    "x, want",
    [
        (77717.14, "77,717.14"),
        (123.456, "123.46"),
        (77.1, "77.1"),
        (0.5, "0.5"),
        (0.00001234, "0.00001234"),
        (0, "0"),
    ],
)
def test_fmt_price(x, want):
    assert fmt_price(x) == want


@pytest.mark.parametrize(
    "x, want",
    [
        (1.5e9, "1.50B"),
        (1.5e12, "1.50T"),
        (283268741.5, "283.27M"),
        (3783.0958, "3.78K"),
        (950.0, "950"),
    ],
)
def test_fmt_qty(x, want):
    assert fmt_qty(x) == want


def test_pct():
    assert pct(100, 110) == "+10.00%"
    assert pct(100, 90) == "-10.00%"
    assert pct(0, 5) == "-"


def test_render_kline_maps_fields():
    line = render_kline([KLINE_ROW])[1]
    # 展示按 开高低收，字段名序是 open/close/low/high，混淆会在这暴露
    assert "72,448.78" in line and "79,488.68" in line
    assert "72,198.91" in line and "77,706.88" in line
    assert "+7.26%" in line
    assert "226.64M" in line


def test_render_depth_orders_asks_desc_bids_desc():
    # API 真实形态：asks 价格升序、bids 降序
    tick = {"asks": [[99.0, 2.0], [100.0, 1.0]], "bids": [[98.5, 3.0], [98.0, 4.0]]}
    lines = render_depth(tick, 10)
    sep = lines.index("─" * 35)
    asks = [ln for ln in lines[:sep] if ln.startswith("卖")]
    # 卖档倒排：最优卖价（最低 99）贴近买卖分界
    assert asks[0].split() == ["卖", "100.00", "1"]
    assert asks[-1].split() == ["卖", "99", "2"]
    assert lines[sep + 1].split() == ["买", "98.5", "3"]


def test_render_tickers_filters_and_sorts():
    rows = [
        {"symbol": "aausdt", "open": 2, "close": 2, "vol": 100, "amount": 10, "count": 1},
        {"symbol": "bbusdt", "open": 1, "close": 2, "vol": 900, "amount": 10, "count": 2},
        {"symbol": "aabtc", "open": 1, "close": 2, "vol": 9999, "amount": 10, "count": 3},
    ]
    lines = render_tickers(rows, "usdt", 5)
    assert "共 2 个币对" in lines[0]
    assert lines[2].startswith("BBUSDT")  # vol 降序
    assert not any(ln.startswith("AABTC") for ln in lines)


def test_flatten_trades_chronological():
    batches = [
        {"ts": 2, "data": [{"trade-id": 3, "ts": 2}, {"trade-id": 2, "ts": 2}]},
        {"ts": 1, "data": [{"trade-id": 1, "ts": 1}]},
    ]
    # 拍平 + 时间正序：批次新→旧反转后，逐笔旧→新（最新在末行）
    assert [t["trade-id"] for t in flatten_trades(batches)] == [1, 2, 3]


@pytest.mark.parametrize(
    "labels, tradfi, want",
    [
        (["tradfi", "common"], ["Stocks"], "[tradfi·common·Stocks]"),
        (["hot", "common"], None, "[hot·common]"),
        ([], [], ""),
        (None, ["Metals"], "[Metals]"),
    ],
)
def test_fmt_labels(labels, tradfi, want):
    assert fmt_labels(labels, tradfi) == want


CONTRACTS = [
    {"contract_code": "BTC-USDT", "contract_status": 1, "labels": ["hot", "common"]},
    {"contract_code": "XAU-USDT", "contract_status": 1, "labels": ["tradfi", "common"], "tradfi_labels": ["Stocks"]},
    {"contract_code": "TQQQ-USDT", "contract_status": 1, "labels": ["tradfi"], "tradfi_labels": ["Stocks", "Indices"]},
    {"contract_code": "DEAD-USDT", "contract_status": 3, "labels": ["common"]},  # 非在线，应被滤掉
    {"contract_code": "BTC260828", "labels": ["this_week"]},  # 交割周次占 labels 槽，无 status 字段视为在线
]


def test_render_contracts_status_pattern_cat():
    all_online = render_contracts(CONTRACTS, "U本位永续")
    assert all_online[0] == "在线 4 个U本位永续合约"
    assert not any("DEAD-USDT" in ln for ln in all_online)
    assert f"{'BTC260828':<18}[this_week]" in all_online

    by_code = render_contracts(CONTRACTS, "U本位永续", pattern="xau")
    assert by_code[1:] == [f"{'XAU-USDT':<18}[tradfi·common·Stocks]"]

    tradfi = render_contracts(CONTRACTS, "U本位永续", cat="tradfi")
    assert tradfi[0] == "在线 2 个U本位永续合约（cat=tradfi）"
    # cat 子串匹配也覆盖 tradfi_labels 二级细分
    indices = render_contracts(CONTRACTS, "U本位永续", cat="indices")
    assert indices[1].startswith("TQQQ-USDT")


def test_render_symbols_online_only_and_filters():
    rows = [
        {"symbol": "pepeusdt", "state": "online", "quote-currency": "usdt", "base-currency": "pepe"},
        {"symbol": "manabtc", "state": "offline", "quote-currency": "btc", "base-currency": "mana"},
        {"symbol": "pepebtc", "state": "online", "quote-currency": "btc", "base-currency": "pepe", "tags": "st,zerofee"},
    ]
    lines = render_symbols(rows, "usdt", "")
    assert lines == ["在线 1 个币对（quote=usdt）", "pepeusdt"]
    assert render_symbols(rows, "", "pepe") == ["在线 2 个币对（含 'pepe'）", "pepeusdt", "pepebtc"]
    assert render_symbols(rows, "", "", cat="st") == ["在线 1 个币对（cat=st）", "pepebtc"]
