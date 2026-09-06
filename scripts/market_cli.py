#!/usr/bin/env python3
"""Platform C 现货公开行情查询（api.example.com 公开 REST，免鉴权）——快速查币价 / K线 / 盘口 / 成交 / 币对清单。

用法：
    python3 scripts/market_cli.py ticker btc eth             # 实时行情；裸 base 自动补 usdt
    python3 scripts/market_cli.py tickers --top 10           # 全市场 24h 成交额榜（-q 换计价币，-q all 全量）
    python3 scripts/market_cli.py kline btc -p 1day -n 30    # K线（period: 1min/5min/15min/30min/60min/4hour/1day/1mon/1week）
    python3 scripts/market_cli.py depth btc -n 10            # 盘口买卖档
    python3 scripts/market_cli.py trades btc -n 20           # 最近逐笔成交
    python3 scripts/market_cli.py symbols -q usdt pepe            # 现货在线币对（-q 计价币 / 子串过滤）
    python3 scripts/market_cli.py symbols -t swap --cat tradfi    # 合约清单（-t swap/coin/delivery/all；--cat 按标签过滤）
全局：--json 输出原始 JSON；--host api.example.com 换网关（主备自动切换）。

symbol 写法：BTC / BTC-USDT / BTC/USDT / btcusdt 均可；非 usdt 计价的裸 base 请写全（如 ethbtc）。

退出码：0 成功；1 网络 / 币对不存在等错误（原因写 stderr）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

import requests

HOSTS = ["api.example.com", "api.example.com"]  # 现货主 / 备网关，均免鉴权
HBDM_HOSTS = ["api.hbdm.com"]  # 合约网关（U 本位 / 币本位永续 + 币本位交割）
TIMEOUT = 10
DEFAULT_QUOTE = "usdt"
# 裸 base 补 usdt 前先认已带计价后缀；Platform C 现货实际计价币全集见 symbols 子命令输出
QUOTE_SUFFIXES = ("usdt", "usdc", "btc", "eth", "ht", "husd", "dai", "eur")


# ── 纯函数（格式化 / 归一化，pytest 直测，无网络）──────────────────────────
def norm_symbol(raw: str) -> str:
    """归一化币对：'BTC' -> 'btcusdt'；'BTC-USDT' / 'BTC/USDT' / 'btcusdt' -> 'btcusdt'；'ETH/BTC' -> 'ethbtc'。"""
    s = raw.strip().lower()
    for sep in ("/", "-", "_", " "):
        s = s.replace(sep, "")
    if not any(s.endswith(q) and len(s) > len(q) for q in QUOTE_SUFFIXES):
        s += DEFAULT_QUOTE
    return s


def fmt_price(x: float) -> str:
    """价格按量级自适应小数位：77717.14 -> '77,717.14'；0.00001234 -> '0.00001234'。"""
    if x == 0:
        return "0"
    a = abs(x)
    if a >= 100:
        return f"{x:,.2f}"
    if a >= 1:
        return f"{x:,.4f}".rstrip("0").rstrip(".")
    return f"{x:.10f}".rstrip("0").rstrip(".")


def fmt_qty(x: float) -> str:
    """量 / 额缩写：283268741.5 -> '283.27M'；3783.0958 -> '3.78K'；950 -> '950'。"""
    a = abs(x)
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div:
            return f"{x / div:,.2f}{suf}"
    return f"{x:,.4f}".rstrip("0").rstrip(".")


def pct(open_: float, close: float) -> str:
    """24h 涨跌幅：100 -> 110 得 '+10.00%'；open 为 0 返回 '-'。"""
    if not open_:
        return "-"
    return f"{(close - open_) / open_ * 100:+.2f}%"


def ts_str(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def render_ticker(sym: str, t: dict) -> str:
    """detail/merged 的 tick -> 单行行情。amount=base 量，vol=计价币成交额。"""
    bid = t.get("bid") or [0, 0]
    ask = t.get("ask") or [0, 0]
    return (
        f"{sym.upper():<14} {fmt_price(t['close']):>14}  24h {pct(t['open'], t['close']):>8}"
        f"  高 {fmt_price(t['high'])}  低 {fmt_price(t['low'])}"
        f"  额 {fmt_qty(t['vol'])}  量 {fmt_qty(t['amount'])}"
        f"  买一 {fmt_price(bid[0])} / 卖一 {fmt_price(ask[0])}"
    )


def render_tickers(rows: list[dict], quote: str, top: int) -> list[str]:
    """/market/tickers -> 按计价币过滤、24h 成交额（vol）降序取前 N。"""
    sel = [r for r in rows if not quote or quote == "all" or r["symbol"].endswith(quote)]
    sel.sort(key=lambda r: r.get("vol", 0), reverse=True)
    out = [
        f"共 {len(sel)} 个币对（quote={quote}），按 24h 成交额取前 {min(top, len(sel))}：",
        f"{'SYMBOL':<16}{'现价':>14}  {'24h':>8}  {'成交额':>12}  {'成交量':>14}  {'笔数':>8}",
    ]
    for r in sel[:top]:
        out.append(
            f"{r['symbol'].upper():<16}{fmt_price(r['close']):>14}  {pct(r['open'], r['close']):>8}"
            f"  {fmt_qty(r['vol']):>12}  {fmt_qty(r['amount']):>14}  {r.get('count', 0):>8}"
        )
    return out


def render_kline(rows: list[dict]) -> list[str]:
    """kline 对象数组（字段名序 open/close/low/high，展示按开高低收）-> 行列表。id 为秒级时间。"""
    out = [f"{'时间':<17}{'开':>13}{'高':>13}{'低':>13}{'收':>13}  {'涨跌':>8}  {'量(base)':>12}  {'额(计价)':>12}"]
    for k in rows:
        ts = datetime.fromtimestamp(k["id"]).strftime("%Y-%m-%d %H:%M")
        out.append(
            f"{ts:<17}{fmt_price(k['open']):>13}{fmt_price(k['high']):>13}{fmt_price(k['low']):>13}{fmt_price(k['close']):>13}"
            f"  {pct(k['open'], k['close']):>8}  {fmt_qty(k['amount']):>12}  {fmt_qty(k['vol']):>12}"
        )
    return out


def render_depth(tick: dict, n: int) -> list[str]:
    """盘口：asks 升序 / bids 降序，各取前 n 档，卖档倒排让最优价贴近中间。"""
    asks = tick.get("asks", [])[:n]
    bids = tick.get("bids", [])[:n]
    out = [f"{'档':<3}{'价格':>15}{'数量':>15}"]
    for p, a in reversed(asks):
        out.append(f"{'卖':<3}{fmt_price(p):>15}{fmt_qty(a):>15}")
    out.append("─" * 35)
    for p, a in bids:
        out.append(f"{'买':<3}{fmt_price(p):>15}{fmt_qty(a):>15}")
    return out


def flatten_trades(batches: list[dict]) -> list[dict]:
    """history/trade 的批次结构拍平成单笔列表，按时间正序（最新在末行）。"""
    flat = [t for b in batches for t in b.get("data", [])]
    flat.reverse()
    return flat


def render_trades(rows: list[dict]) -> list[str]:
    out = []
    for t in rows:
        side = "买" if t["direction"] == "buy" else "卖"
        out.append(
            f"{datetime.fromtimestamp(t['ts'] / 1000).strftime('%H:%M:%S')}  {side}"
            f"  {fmt_price(t['price']):>14}  {fmt_qty(t['amount']):>14}"
        )
    return out


def render_symbols(rows: list[dict], quote: str, pattern: str, cat: str = "") -> list[str]:
    """/v1/common/symbols -> 只留 online，按计价币 / 子串 / tags（--cat）过滤，一币对一行（可 grep）。"""
    sel = [r for r in rows if r.get("state") == "online"]
    if quote and quote != "all":
        sel = [r for r in sel if r.get("quote-currency") == quote]
    if pattern:
        p = pattern.lower()
        sel = [r for r in sel if p in r["symbol"]]
    if cat:
        c = cat.lower()
        sel = [r for r in sel if c in (r.get("tags") or "").lower()]
    head = f"在线 {len(sel)} 个币对"
    if quote and quote != "all":
        head += f"（quote={quote}）"
    if pattern:
        head += f"（含 '{pattern}'）"
    if cat:
        head += f"（cat={cat}）"
    return [head] + [r["symbol"] for r in sel]


def fmt_labels(labels: list | None, tradfi: list | None) -> str:
    """合约标签拼展示串：(['tradfi','common'], ['Stocks']) -> '[tradfi·common·Stocks]'；空则 ''。"""
    all_ = list(labels or []) + list(tradfi or [])
    return f"[{'·'.join(all_)}]" if all_ else ""


def render_contracts(rows: list[dict], market: str, pattern: str = "", cat: str = "") -> list[str]:
    """合约清单：contract_status==1 在线；pattern 匹配 code；cat 匹配标签（tradfi/stocks/hot/…，子串不区分大小写）。"""
    sel = [r for r in rows if r.get("contract_status", 1) == 1]
    if pattern:
        p = pattern.lower()
        sel = [r for r in sel if p in r["contract_code"].lower()]
    if cat:
        c = cat.lower()
        sel = [r for r in sel if c in fmt_labels(r.get("labels"), r.get("tradfi_labels")).lower()]
    head = f"在线 {len(sel)} 个{market}合约"
    if pattern:
        head += f"（含 '{pattern}'）"
    if cat:
        head += f"（cat={cat}）"
    return [head] + [f"{r['contract_code']:<18}{fmt_labels(r.get('labels'), r.get('tradfi_labels'))}" for r in sel]


# ── 网络层 ────────────────────────────────────────────────────────────────
def api_get(path: str, params: dict[str, str] | None = None, host: str = "", hosts: list[str] | None = None) -> dict:
    """GET 公开接口；主网关失败自动切备；status != ok 抛 RuntimeError。"""
    last_err = ""
    for h in [host] if host else (hosts or HOSTS):
        try:
            r = requests.get(f"https://{h}{path}", params=params, timeout=TIMEOUT)
            data = r.json()
        except (requests.RequestException, ValueError) as e:
            last_err = f"{h}: {e}"
            continue
        if data.get("status") != "ok":
            raise RuntimeError(
                f"接口报错 {data.get('err-code') or data.get('status')}: {data.get('err-msg', '')}"
                f"（{path} {params or ''}）".strip()
            )
        return data
    raise RuntimeError(f"网关均不可达（{last_err}）；--host 换网关或检查代理")


# ── CLI ───────────────────────────────────────────────────────────────────
def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="输出原始 JSON")
    common.add_argument("--host", default="", help=f"网关域名（默认 {HOSTS[0]}，失败切 {HOSTS[1]}）")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ticker", parents=[common], help="单/多币对实时行情")
    p.add_argument("symbols", nargs="+", help="BTC / BTC-USDT / btcusdt；裸 base 自动补 usdt")
    p = sub.add_parser("tickers", parents=[common], help="全市场 24h 成交额榜")
    p.add_argument("-q", "--quote", default=DEFAULT_QUOTE, help="计价币后缀（usdt/btc/.../all）")
    p.add_argument("--top", type=int, default=15, help="取前 N（默认 15）")

    p = sub.add_parser("kline", parents=[common], help="K线")
    p.add_argument("symbol")
    p.add_argument("-p", "--period", default="1day", help="1min/5min/15min/30min/60min/4hour/1day/1mon/1week")
    p.add_argument("-n", "--size", type=int, default=30, help="根数（默认 30，上限 2000）")

    p = sub.add_parser("depth", parents=[common], help="盘口")
    p.add_argument("symbol")
    p.add_argument("-n", "--levels", type=int, default=10, help="买卖各取前 N 档（默认 10）")

    p = sub.add_parser("trades", parents=[common], help="最近成交")
    p.add_argument("symbol")
    p.add_argument("-n", "--size", type=int, default=20, help="条数（默认 20）")

    p = sub.add_parser("symbols", parents=[common], help="在线币对清单（现货 / 合约）")
    p.add_argument("-q", "--quote", default="", help="计价币（现货用：usdt/btc/...，默认全部）")
    p.add_argument(
        "-t", "--type", default="spot", choices=["spot", "swap", "coin", "delivery", "all"],
        help="市场：spot 现货 / swap U本位永续 / coin 币本位永续 / delivery 币本位交割 / all 现货+U永续",
    )
    p.add_argument("--cat", default="", help="标签过滤：合约 tradfi/stocks/indices/metals/hot/new，现货 tags（st/zerofee/...）")
    p.add_argument("pattern", nargs="?", default="", help="子串过滤（如 pepe）")

    args = ap.parse_args()
    sym = norm_symbol(args.symbol) if getattr(args, "symbol", "") else ""

    try:
        if args.cmd == "ticker":
            syms = [norm_symbol(raw) for raw in args.symbols]
            d = {s: api_get("/market/detail/merged", {"symbol": s}, args.host)["tick"] for s in syms}
            out = [render_ticker(s, t) for s, t in d.items()]
        elif args.cmd == "tickers":
            d = api_get("/market/tickers", host=args.host)
            out = render_tickers(d["data"], args.quote, args.top) if not args.json else None
        elif args.cmd == "kline":
            d = api_get("/market/history/kline", {"symbol": sym, "period": args.period, "size": args.size}, args.host)
            out = render_kline(d["data"]) if not args.json else None
        elif args.cmd == "depth":
            d = api_get("/market/depth", {"symbol": sym, "type": "step0"}, args.host)
            out = render_depth(d["tick"], args.levels) if not args.json else None
        elif args.cmd == "trades":
            d = api_get("/market/history/trade", {"symbol": sym, "size": args.size}, args.host)
            out = render_trades(flatten_trades(d["data"])[-args.size :]) if not args.json else None
        else:  # symbols
            if args.type == "spot":
                d = api_get("/v1/common/symbols", host=args.host)
                out = render_symbols(d["data"], args.quote, args.pattern, args.cat) if not args.json else None
            elif args.type == "swap":
                d = api_get("/linear-swap-api/v1/swap_contract_info", host=args.host, hosts=HBDM_HOSTS)
                out = render_contracts(d["data"], "U本位永续", args.pattern, args.cat) if not args.json else None
            elif args.type == "coin":
                d = api_get("/swap-api/v1/swap_contract_info", host=args.host, hosts=HBDM_HOSTS)
                out = render_contracts(d["data"], "币本位永续", args.pattern, args.cat) if not args.json else None
            elif args.type == "delivery":
                d = api_get("/api/v1/contract_contract_info", host=args.host, hosts=HBDM_HOSTS)
                # 交割合约 code 形如 BTC260828，labels 槽放周次（this_week/next_week/...）复用同一渲染
                rows = [{"contract_code": r["contract_code"], "labels": [r["contract_type"]]} for r in d["data"]]
                out = render_contracts(rows, "币本位交割", args.pattern, args.cat) if not args.json else None
            else:  # all：现货 + U 本位永续分节
                spot_d = api_get("/v1/common/symbols", host=args.host)
                swap_d = api_get("/linear-swap-api/v1/swap_contract_info", host=args.host, hosts=HBDM_HOSTS)
                d = {"spot": spot_d, "swap": swap_d}
                out = (
                    ["== 现货 =="] + render_symbols(spot_d["data"], args.quote, args.pattern, args.cat)
                    + ["", "== U本位永续 =="] + render_contracts(swap_d["data"], "U本位永续", args.pattern, args.cat)
                )
    except RuntimeError as e:
        print(f"[market_cli] {e}", file=sys.stderr)
        return 1

    try:
        print(json.dumps(d, ensure_ascii=False, indent=2) if args.json else "\n".join(out))
    except BrokenPipeError:
        # 管道下游提前关闭（| head / | wc）属正常用法：静默退出，dup2 防 interpreter 退出时二次报错
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    return 0


if __name__ == "__main__":
    sys.exit(main())
