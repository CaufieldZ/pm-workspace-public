#!/usr/bin/env python3
"""用站点自己的账单核对峰谷判定 —— 指定日期的实际成交价 vs「交易所日历」规则。

用法：
    python3 scripts/reconcile_peak.py --provider <名>                     # 看今天
    python3 scripts/reconcile_peak.py --provider <名> --date 2026-10-01   # 看指定日
    python3 scripts/reconcile_peak.py --provider <名> --date 2026-10-01 --days 7 --strict

判读口径：从站点流水里按条反推「成交输入价」，按小时聚合。同一模型同一档的成交价只有两档
    ——低谷价与它的 ×2 高峰价，所以用当日低谷时段的价当基准，高峰窗的价除以基准即 1 或 2。
    成交价来自账单本身（`quota` ÷ 加权 token），与 hook 用的价目表无关：这正是它作为
    独立裁判的意义——hook 的价目 / 峰谷规则改了，本脚本不受影响。

场景与判别力：每个日期会标出该日**能验什么** —— 只有「按周几规则本来该收 ×2、实际却该是低谷」
    的日子（放假日落在工作日）才验得出节假日豁免；两历同结果的日子跑一万次也验不出口径。
    归一化后：高峰日的高峰窗应为 ×2、低谷日全天应为 ×1。

不一致时的诊断会点名被证伪的假设：补班周末出现 ×2 = 站点按「国务院日历」判（要纳补班日历）；
放假日落在工作日出现 ×2 = 站点不豁免该日（整段都不豁免 → 改 holidays_mode，只有调休连休不豁免
     → 站点只认《放假办法》的法定日）。笼统说「不一致」等于没说，所以分开报。

产物：无（只打印判读表）。

前置：`.claude/hooks/cost-config.json` 的 `providers.<名>`（含凭据引用）+ 根目录 .env。
    `--help` 本身不需要网络与凭据。

退出码：0 判读完成且（`--strict` 下）每日都验成了 / 2 取数失败；`--strict` 下规则与账单不一致，
    **或该日判据不足没能下结论**（「没验成」不等于「验过了」——否则一条什么都没验到的命令
    会绿着退出，看起来像通过）
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from relay_balance import DEFAULT_QUOTA_PER_UNIT, load_provider  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SH = datetime.timezone(datetime.timedelta(hours=8))
PEAK_HOURS = set(range(9, 12)) | set(range(14, 18))
PAGE_SIZE = 100
MAX_PAGES = 200


def holiday_dates(cfg: dict) -> set[str]:
    """配置指向的节假日表里的放假日；没声明 / 读不到 → 空集（调用方按「未覆盖」处理）。"""
    peak = cfg.get("peak") or {}
    name = peak.get("holidays_file") or ""
    if not name or str(peak.get("holidays_mode") or "") == "ignore":
        return set()
    path = Path(os.environ.get("PMWS_COST_CONFIG") or
                ROOT / ".claude" / "hooks" / "cost-config.json")
    p = Path(name) if os.path.isabs(name) else path.parent / name
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return set()
    out: set[str] = set()
    for days in (doc.get("off_days") or {}).values():
        out.update(str(d) for d in days)
    return out


def discriminating_power(day: datetime.date, want: bool) -> str:
    """该日能不能验出入口径 —— 两历同结果的日子跑一万次也验不出东西。"""
    if want:
        return "基线：高峰窗该收 ×2"
    if day.weekday() >= 5:
        return "周末豁免（两历同休；若该日是调休补班日，更能验「交易所 vs 国务院」日历）"
    return "节假日豁免（按周几规则本来该收 ×2）"


def mismatch_hint(day: datetime.date, want: bool, mult: float) -> str:
    """不一致时点名被证伪的假设 —— 不同场景的修法完全不同，笼统说「不一致」等于没说。"""
    if want:
        return (f"规则说该日 ×{mult:g}、账单说没 ×{mult:g} —— 站点可能把该日当成放假日，"
                "或把高峰整个关掉了（看一眼 /api/pricing 的 peak_active）")
    if day.weekday() >= 5:
        return (f"规则说周末全天低谷、账单说高峰窗 ×{mult:g} —— 若该日是调休补班日，说明站点按"
                "「国务院日历」判而非「交易所日历」；这一条节假日表修不了，得另配工作日历")
    return (f"规则说全天低谷、账单说高峰窗 ×{mult:g} —— 站点不豁免该放假日。两种可能："
            "①整段连休都不豁免 → 把 peak.holidays_mode 改成 \"ignore\"；"
            "②只有调休凑出来的那几天不豁免 → 站点只认《放假办法》的法定日，口径要收窄。"
            "本表只存放假日、不区分法定日与调休连休，这两种得人工比对区分")


def expected_peak(day: datetime.date, holidays: set[str]) -> bool:
    """规则判定该日是否为高峰日：周一~周五且不在放假日表（周末一律低谷）。"""
    return day.weekday() < 5 and day.isoformat() not in holidays


def channel_prefixes(cfg: dict, provider: str) -> list[str]:
    """该 provider 名下各通道价目表覆盖的模型前缀 —— 对账范围收敛到规则真正管的模型。

    不收这个范围会把按张计价的图像类模型算进来（它们的 quota 与 token 不成比例，
    反推出的「成交价」是假象）。
    """
    out: set[str] = set()
    for ch in (cfg.get("channels") or []):
        if not isinstance(ch, dict) or str(ch.get("provider") or "") != provider:
            continue
        out.update(str(p) for p in (ch.get("rates_off_peak") or {}))
        out.update(str(p) for p in (ch.get("models") or []))
    return sorted(out)


def realized_price(entry: dict, per_unit: float = DEFAULT_QUOTA_PER_UNIT) -> float | None:
    """从一条流水反推成交输入价 ¥/1M。

    按该条自带的倍率加权 token（输出 / 缓存读 / 缓存写都折回输入价的当量），
    再除 quota。token 为 0 或非按 token 计价（model_ratio ≤ 0）→ None。

    `per_unit` 是配额单位（quota ÷ per_unit = ¥），走 provider 配置的 `quota_per_unit`
    ——与 relay_balance.py 同一口径，不在这里写死第二份。
    """
    try:
        other = json.loads(entry.get("other") or "{}")
    except Exception:
        return None
    mr = other.get("model_ratio")
    if not isinstance(mr, (int, float)) or mr <= 0:
        return None
    tokens = (int(entry.get("prompt_tokens") or 0)
              + int(entry.get("completion_tokens") or 0) * (other.get("completion_ratio") or 1)
              + int(other.get("cache_tokens") or 0) * (other.get("cache_ratio") or 0)
              + int(other.get("cache_creation_tokens") or 0) * (other.get("cache_creation_ratio") or 0))
    quota = int(entry.get("quota") or 0)
    if tokens <= 0 or quota <= 0 or per_unit <= 0:
        return None
    return quota / float(per_unit) / (tokens / 1e6)


def fetch_day(prov: dict, day: datetime.date, timeout: float) -> list[dict]:
    """取某日（Asia/Shanghai 00:00 ~ 次日 00:00）的全部流水。"""
    base = str(prov.get("base_url") or "").rstrip("/")
    start = int(datetime.datetime(day.year, day.month, day.day, tzinfo=SH).timestamp())
    end = start + 86400
    out: list[dict] = []
    seen: set = set()
    for page in range(MAX_PAGES):
        qs = urllib.parse.urlencode({"p": page, "page_size": PAGE_SIZE, "type": 0,
                                     "start_timestamp": start, "end_timestamp": end})
        req = urllib.request.Request(base + "/api/log/self?" + qs, headers={
            "User-Agent": "pm-workspace/1.0", "Accept": "application/json",
            "Authorization": f"Bearer {prov['token']}", "New-Api-User": str(prov["uid"])})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            doc = json.loads(resp.read().decode("utf-8", errors="replace"))
        data = doc.get("data") or {}
        items = data.get("items") if isinstance(data, dict) else data
        if not items:
            break
        for it in items:
            if it.get("id") in seen:
                continue
            seen.add(it.get("id"))
            out.append(it)
        if len(items) < PAGE_SIZE:
            break
    else:
        # 触顶必须出声：残缺样本照样能跑出「结论」，静默截断正是「分页不全 → 反向结论」
        # 那类错误的成因（本项目在站点账单上踩过一次）。
        print(f"reconcile_peak: {day} 流水超过 {MAX_PAGES} 页，仅取前 "
              f"{MAX_PAGES * PAGE_SIZE} 条——判读基于残缺样本，可能不完整", file=sys.stderr)
    return out


def summarize(entries: list[dict], prefixes: list[str], per_unit: float = DEFAULT_QUOTA_PER_UNIT) -> dict:
    """按小时聚合成交价 → {小时: {价: 条数}}，只留有可反推成交价的条目。"""
    per_hour: dict[int, collections.Counter] = collections.defaultdict(collections.Counter)
    for e in entries:
        model = str(e.get("model_name") or "")
        if prefixes and not any(model.startswith(p) for p in prefixes):
            continue
        price = realized_price(e, per_unit)
        if price is None:
            continue
        ts = e.get("created_at")
        if not ts:
            continue
        hour = datetime.datetime.fromtimestamp(int(ts), SH).hour
        per_hour[hour][round(price, 3)] += 1
    return per_hour


def judge(per_hour: dict, mult: float) -> tuple[str, list[str]]:
    """→ (verdict, 明细行)。基准取「当日非高峰窗里最常见的成交价」，再看高峰窗是否 ×mult。

    分不出档的小时（既非基准价、也非基准价的 ×mult）不计入判据——它们是别的计价形态
    （按张计费 / 别的档位），拿它们下结论会把「有个别条目看不懂」说成「站点没在收高峰价」。
    """
    off = collections.Counter()
    for hour, hist in per_hour.items():
        if hour not in PEAK_HOURS:
            off += hist
    if not off:
        return "nodecision", []
    base = off.most_common(1)[0][0]
    peak_vals: list[int] = []
    lines = []
    for hour in sorted(per_hour):
        hist = per_hour[hour]
        price = hist.most_common(1)[0][0]
        ratio = price / base if base else 0
        if abs(ratio - 1) < 0.05:
            tag, cls = "低谷", 1
        elif abs(ratio - mult) < 0.1 * mult:
            tag, cls = f"高峰 ×{mult:g}", 2
        else:
            tag, cls = f"其他（×{ratio:.2f}，不在本规则内）", 0
        lines.append(f"  {hour:02d} 时 {sum(hist.values()):>6} 条   ¥{price:.4f}/1M"
                     f"  基准价 ×{ratio:<5.2f} {tag}")
        if hour in PEAK_HOURS and cls:
            peak_vals.append(cls)
    if not peak_vals:
        return "nodecision", lines
    if all(v == 2 for v in peak_vals):
        return "peak", lines
    if all(v == 1 for v in peak_vals):
        return "valley", lines
    return "mixed", lines


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  python3 scripts/reconcile_peak.py --provider <名>\n"
               "  python3 scripts/reconcile_peak.py --provider <名> --date YYYY-MM-DD --days 7\n"
               "  python3 scripts/reconcile_peak.py --provider <名> --date YYYY-MM-DD --strict\n")
    ap.add_argument("--provider", required=True,
                    help="cost-config.json 里 providers 下的条目名（余额 / 流水的取数凭据）")
    ap.add_argument("--date", default=str(datetime.datetime.now(SH).date()),
                    help="起始日期 YYYY-MM-DD（默认今天，按 Asia/Shanghai）")
    ap.add_argument("--days", type=int, default=1, help="从起始日期起连续看几天（默认 1，国庆这类连休填 7）")
    ap.add_argument("--timeout", type=float,
                    default=float(os.environ.get("RELAY_HTTP_TIMEOUT") or 20),
                    help="单次请求超时秒（默认 RELAY_HTTP_TIMEOUT 或 20）")
    ap.add_argument("--strict", action="store_true",
                    help="验证模式：规则与账单不一致、或该日判据不足没能下结论时退出 2"
                         "（「没验成」也判失败，避免空跑看起来像通过）")
    args = ap.parse_args()

    try:
        start = datetime.date.fromisoformat(args.date)
    except ValueError as e:
        print(f"reconcile_peak: --date 认不出：{e}", file=sys.stderr)
        return 2
    if args.days < 1:
        print("reconcile_peak: --days 必须 ≥ 1", file=sys.stderr)
        return 2

    try:
        prov, cfg = load_provider(args.provider)
    except ValueError as e:
        print(f"reconcile_peak: {e}", file=sys.stderr)
        return 2
    holidays = holiday_dates(cfg)
    covered = bool(holidays)
    prefixes = channel_prefixes(cfg, args.provider)
    if not prefixes:
        print(f"reconcile_peak: 配置里 providers.{args.provider} 名下没有通道价目表，"
              "对账不筛模型（图像等按张计价的条目会混进判读）", file=sys.stderr)
    try:
        mult = float((cfg.get("peak") or {}).get("multiplier") or 2)
    except Exception:
        mult = 2.0
    per_unit = float(prov.get("quota_per_unit") or DEFAULT_QUOTA_PER_UNIT)

    mismatch = inconclusive = False
    for i in range(args.days):
        day = start + datetime.timedelta(days=i)
        try:
            entries = fetch_day(prov, day, args.timeout)
        except Exception as e:
            print(f"reconcile_peak: 取 {day} 流水失败：{str(e)[:160]}", file=sys.stderr)
            return 2
        want = expected_peak(day, holidays)
        rule = "高峰日（周一~周五、非放假日）" if want else (
            "低谷日（周末）" if day.weekday() >= 5 else "低谷日（放假日）")
        if not covered:
            rule += "〔未读到节假日表，放假日无法识别〕"
        print(f"\n══ {day} {day.strftime('%a')} · 规则判定：{rule}")
        print(f"   该日能验：{discriminating_power(day, want)}")
        per_hour = summarize(entries, prefixes, per_unit)
        if not per_hour:
            print(f"  该日无可对账的流水（{len(entries)} 条记录，筛后 0 条）—— 没验成")
            inconclusive = True
            continue
        verdict, lines = judge(per_hour, mult)
        print("\n".join(lines))
        if verdict == "nodecision":
            print("  高峰窗内无可分档的请求 —— 判据不足，没验成"
                  "（要该日高峰窗内真有量，才可能下结论）")
            inconclusive = True
            continue
        if verdict == "mixed":
            print("  ⚠️ 高峰窗内两档并存 —— 不判（可能跨了窗口边界，或混了不同档位），没验成")
            inconclusive = True
            continue
        got_peak = verdict == "peak"
        agree = got_peak == want
        print(f"  站点实际：{'收高峰价（高峰窗 ×%g）' % mult if got_peak else '全天低谷'}"
              f" → {'✅ 与规则一致' if agree else '❌ 与规则不一致'}")
        if not agree:
            mismatch = True
            print("     " + mismatch_hint(day, want, mult))

    # 「没验成」不等于「验过了」：判据不足 / 两档并存同样算失败，否则一条什么都没验到的
    # 命令会绿着退出，看起来像通过。
    return 2 if (args.strict and (mismatch or inconclusive)) else 0


if __name__ == "__main__":
    sys.exit(main())
