#!/usr/bin/env python3
"""同步中国放假日历 → 本地节假日表，供 user-prompt-warn.sh 判峰谷价。

用法：
    python3 scripts/sync_cn_holidays.py                    # 同步「前一年 ~ 次年」
    python3 scripts/sync_cn_holidays.py --years 2025-2028  # 指定年份区间
    python3 scripts/sync_cn_holidays.py --check            # 只比对本地产物，发现 drift 退出 2

产物：`.claude/hooks/cn-holidays.json`（`--out` 覆盖）。按年存「全天低谷」的放假日——
    峰谷按「交易所日历」判：周一到周五且非放假日才可能高峰，周末与放假日一律低谷。
    含落在周末的放假日，消费方只查成员资格。数据源另给补班日标记，本表不收——语义相反
    且用不上（补班日必是周末，已被周几那道条件排除）。

改了源数据 / 跨年后重跑本脚本即刷新产物；勿手改产物（下次同步会覆盖）。
消费方：`.claude/hooks/user-prompt-warn.sh`（`peak.holidays_file` 指过来）。

前置：能访问数据源（默认 GitHub raw，`CN_HOLIDAY_SOURCE_BASE` 覆盖为镜像基址）。
    `--help` 本身不需要网络。

退出码：0 成功 / 2 取数失败，或 `--check` 发现与产物不一致
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / ".claude" / "hooks" / "cn-holidays.json"
DEFAULT_SOURCE_BASE = "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master"
DEFAULT_TIMEOUT = 20.0
NOTE = ("DeepSeek 峰谷价的节假日前提：放假日全天低谷。峰谷按「交易所日历」判——"
        "周一到周五且非放假日才可能高峰，周末与放假日一律低谷。"
        "补班日不入表：调休补班一定是周末，已被「周一~周五」那道条件挡在外面；"
        "而数据源对补班日给的标记（isOffDay=false）语义正好相反，误收会把周末算成高峰。"
        "本表只列「全天低谷」的放假日（含落在周末的），消费方查成员资格即可。"
        "由 scripts/sync_cn_holidays.py 生成，勿手改。")


def parse_year_payload(doc: object, year: int) -> list[str]:
    """数据源某年的 JSON → 该年放假日（isOffDay=true）的排好序的日期串。

    只取放假日：补班日在判定里根本用不上——它们一定是周末，已被「周一~周五」那道条件
    挡在外面；而数据源的两组标记语义相反，误取补班日会把周末算成高峰。

    认不出结构 / 年份对不上 → ValueError，不静默返回空表（空表会被当成「该年已覆盖」）。
    """
    if not isinstance(doc, dict):
        raise ValueError("顶层不是对象")
    if doc.get("year") not in (year, str(year)):
        raise ValueError(f"year 字段是 {doc.get('year')!r}，与本轮请求的 {year} 不符")
    days = doc.get("days")
    if not isinstance(days, list):
        raise ValueError("缺 days 数组")
    out = []
    for d in days:
        if not isinstance(d, dict) or not d.get("isOffDay"):
            continue
        date = str(d.get("date") or "")
        try:
            datetime.date.fromisoformat(date)
        except ValueError as e:
            raise ValueError(f"日期认不出：{date!r}") from e
        out.append(date)
    return sorted(set(out))


def diff_years(old: dict, new: dict) -> list[str]:
    """两年份表的差异行（新增 / 消失的年份，年内新增 / 移除的日期）。无差异返回空表。"""
    lines = []
    for year in sorted(set(old) | set(new)):
        a, b = set(old.get(year) or []), set(new.get(year) or [])
        if a != b:
            lines.append(f"{year}: {'新增' if not a else '更新'} {len(b)} 天"
                         f"（+{len(b - a)} / -{len(a - b)}）")
            for d in sorted(b - a):
                lines.append(f"    + {d}")
            for d in sorted(a - b):
                lines.append(f"    - {d}")
    return lines


def fetch_year(year: int, source_base: str, timeout: float) -> object:
    """取某年的源 JSON。"""
    url = f"{source_base.rstrip('/')}/{year}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "pm-workspace/1.0",
                                              "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def parse_year_arg(spec: str) -> list[int]:
    """`2026` / `2025-2028` / `2025,2027` → 年份列表。"""
    years: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            years.update(range(int(a), int(b) + 1))
        else:
            years.add(int(part))
    if not years:
        raise ValueError(f"年份区间认不出：{spec!r}")
    return sorted(years)


def main() -> int:
    this_year = datetime.date.today().year
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  python3 scripts/sync_cn_holidays.py\n"
               "  python3 scripts/sync_cn_holidays.py --years 2025-2028\n"
               "  python3 scripts/sync_cn_holidays.py --check\n")
    ap.add_argument("--years", default=f"{this_year - 1}-{this_year + 1}",
                    help=f"本次刷新的年份范围，`2025-2028` / `2026` / `2025,2027`"
                         f"（默认 {this_year - 1}-{this_year + 1}）；产物里其余年份原样保留")
    ap.add_argument("--out", default=str(DEFAULT_OUT),
                    help=f"产物落点（默认 {DEFAULT_OUT.relative_to(ROOT)}）")
    ap.add_argument("--source-base", default=os.environ.get("CN_HOLIDAY_SOURCE_BASE")
                    or DEFAULT_SOURCE_BASE,
                    help="数据源基址，逐年在后面接 /<年份>.json（默认 env CN_HOLIDAY_SOURCE_BASE 或内置上游）")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"单年请求超时秒（默认 {DEFAULT_TIMEOUT}）")
    ap.add_argument("--check", action="store_true",
                    help="只比对源与本地产物，不一致则退出 2、不落盘（CI / 巡检用）")
    args = ap.parse_args()

    try:
        years = parse_year_arg(args.years)
    except ValueError as e:
        print(f"sync_cn_holidays: {e}", file=sys.stderr)
        return 2

    out_path = Path(args.out)
    off_days: dict[str, list[str]] = {}
    pending: list[int] = []
    for year in years:
        try:
            doc = fetch_year(year, args.source_base, args.timeout)
            days = parse_year_payload(doc, year)
        except Exception as e:
            print(f"sync_cn_holidays: 取 {year} 失败：{str(e)[:160]}", file=sys.stderr)
            return 2
        # 源里该年为空的 days = 次年安排还没公布。不写空表——空表会被消费方
        # 当成「该年已覆盖」，反而把未公布年份的峰谷判静默判错。
        if not days:
            pending.append(year)
            continue
        off_days[str(year)] = days

    if not off_days:
        print(f"sync_cn_holidays: {years} 都没拿到放假日（安排未公布？）", file=sys.stderr)
        return 2

    old: dict = {}
    if out_path.exists():
        try:
            old = (json.loads(out_path.read_text(encoding="utf-8")) or {}).get("off_days") or {}
        except Exception as e:
            print(f"sync_cn_holidays: 旧产物读不出（{out_path}）：{str(e)[:120]}", file=sys.stderr)
            old = {}
        if not isinstance(old, dict):
            old = {}

    # 只比本次请求覆盖的年份：产物里更宽的年份是「产物比源广」，不是漂移——
    # 拿窄 --years 跑巡检不该报红（否则会误判产物过期，进而做一次没必要的全量重写）。
    wanted = [str(y) for y in years]
    extra = sorted(set(old) - set(wanted))
    lines = diff_years({y: old[y] for y in wanted if y in old}, off_days)

    if args.check:
        if not out_path.exists():
            print(f"sync_cn_holidays: 产物不存在（{out_path}）——先跑一次不带 --check 的同步",
                  file=sys.stderr)
            return 2
        if lines:
            print("sync_cn_holidays: 产物与源不一致：")
            print("\n".join("  " + x for x in lines))
            return 2
        note = f"（另有产物独有年份 {', '.join(extra)}，不在本次比对范围）" if extra else ""
        print(f"sync_cn_holidays: 产物与源一致（{len(off_days)} 年 / "
              f"{sum(len(v) for v in off_days.values())} 天）{note}")
        return 0

    # 写盘只替请求内的年份，其余原样保留——否则 `--years 2026` 会把产物里的 2025 静默抹掉，
    # 而消费方读不到 2025 只表现为「表未覆盖该年」，没人会联想到是一次刷新弄丢的。
    payload = {"_note": NOTE, "source": args.source_base, "fetched": str(datetime.date.today()),
               "off_days": {**{y: v for y, v in old.items() if y not in wanted}, **off_days}}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"sync_cn_holidays: 写入 {out_path}（本次刷新 {len(off_days)} 年，产物共 "
          f"{len(payload['off_days'])} 年）")
    for year, days in sorted(off_days.items()):
        wd = sum(1 for d in days if datetime.date.fromisoformat(d).weekday() < 5)
        print(f"  {year}: {len(days)} 天放假日（其中 {wd} 天落在周一~周五，真正影响峰谷的部分）")
    if extra:
        print(f"  未刷新、原样保留：{', '.join(extra)}")
    if pending:
        print(f"  未公布（不写空表，消费方会自报未覆盖）：{', '.join(str(y) for y in pending)}")
    if lines:
        print("  与旧产物相比：")
        print("\n".join("  " + x for x in lines))
    else:
        print("  与旧产物相比：无变化")
    return 0


if __name__ == "__main__":
    sys.exit(main())
