#!/usr/bin/env python3
"""规则层体积棘轮 —— 逐文件上限，只降不升，升须论证。

每 session 必加载的 CLAUDE.md 与按需读的 runbooks 是模型注意力的固定开销。audit
类 5 一直在打印这两个数，但从不判红，于是它们只会单调上涨——加规则永远比删规则容易。
本脚本给每个文件冻一个上限，涨破就红。

口径 tokens = bytes/2，沿用 audit §5.1（中文没有空格，wc -w 那套在这儿没意义）。

上限清单在 scripts/rule-budgets.manifest.json。棘轮语义：

  1. 先搬走 —— 内容属于别的层就挪过去（info-ownership.md 管归属），留一行链接
  2. 再压缩 —— 确实属于这里但能写得更短
  3. 最后才谈抬上限 —— 内容值得占这个位置时才抬，抬这个动作要在 decision note
     里论证。上限太低是预算 bug，不是让你删内容的理由。

上限是护栏不是瘦身指标：低于上限不代表该继续压，冻结值自带 5% headroom，
稳定态就该待在里面。降上限只在文件真瘦下来之后做。

四条红灯：
    超上限          — 涨破了冻结值
    文件不存在      — 改名 / 删除忘了同轮改 manifest
    上限非正整数    — manifest 手改写坏了
    未登记          — .claude/runbooks/ 新增了 .md 却没进 manifest（预算面被绕开）

用法：
    python3 scripts/check_rule_volume.py
    python3 scripts/check_rule_volume.py --list      # 打全表当前用量，调上限前看它
    python3 scripts/check_rule_volume.py --strict    # 有红灯 exit 2（pre-commit / audit 类 5 用）

退出码：
    0 — clean（未传 --strict 时恒 0）
    2 — 传 --strict 且有红灯
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.repo import find_root  # noqa: E402

MANIFEST = "scripts/rule-budgets.manifest.json"
BUDGETED_DIR = ".claude/runbooks"   # 此目录下新增 .md 必须登记


def tokens_of(text_bytes: int) -> int:
    """audit §5.1 口径：tokens ≈ bytes/2。"""
    return text_bytes // 2


def check_budgets(budgets: dict, sizes: dict[str, int | None], present: set[str]) -> dict:
    """纯判定：budgets = {路径: 上限}，sizes = {路径: 字节数或 None(不存在)}，
    present = BUDGETED_DIR 下实际存在的 .md 路径集合。返回四类红灯 + 报表行。
    """
    over, missing, invalid, rows = [], [], [], []
    for path, ceiling in budgets.items():
        if not isinstance(ceiling, int) or isinstance(ceiling, bool) or ceiling <= 0:
            invalid.append((path, ceiling))
            continue
        size = sizes.get(path)
        if size is None:
            missing.append(path)
            continue
        now = tokens_of(size)
        rows.append((path, now, ceiling))
        if now > ceiling:
            over.append((path, now, ceiling))
    unregistered = sorted(present - set(budgets))
    return {
        "over": over, "missing": missing, "invalid": invalid,
        "unregistered": unregistered, "rows": rows,
    }


def has_red(r: dict) -> bool:
    return bool(r["over"] or r["missing"] or r["invalid"] or r["unregistered"])


def report(r: dict, list_only: bool = False) -> None:
    if list_only:
        for path, now, ceiling in sorted(r["rows"], key=lambda x: -x[1]):
            flag = "OVER" if now > ceiling else "ok  "
            print(f"  {flag}  {now:>6} / {ceiling:<6} {path}")
        total = sum(now for _, now, _ in r["rows"])
        print(f"\n  合计 {total}t，{len(r['rows'])} 个文件")
        return

    if r["over"]:
        print(f"🔴 超上限（{len(r['over'])}）：")
        for path, now, ceiling in r["over"]:
            print(f"  · {path} — {now}t / 上限 {ceiling}t（超 {now - ceiling}t）")
        print("  修：先搬走（内容属于别的层）→ 再压缩 → 内容确实值得占这个位置时才抬上限，"
              "抬上限在 decision note 里论证\n")

    if r["missing"]:
        print(f"🔴 登记了但文件不存在（{len(r['missing'])}）：")
        for path in r["missing"]:
            print(f"  · {path}")
        print(f"  修：改名 / 删除时同轮改 {MANIFEST}\n")

    if r["invalid"]:
        print(f"🔴 上限值非法（{len(r['invalid'])}）：")
        for path, ceiling in r["invalid"]:
            print(f"  · {path} — {ceiling!r}（须为正整数）")
        print()

    if r["unregistered"]:
        print(f"🔴 未登记（{len(r['unregistered'])}）—— {BUDGETED_DIR}/ 新增文件绕开了预算面：")
        for path in r["unregistered"]:
            print(f"  · {path}")
        print(f"  修：在 {MANIFEST} 里给它定个上限（当前体积 +5% headroom）\n")

    if not has_red(r):
        total = sum(now for _, now, _ in r["rows"])
        headroom = sum(c for _, _, c in r["rows"]) - total
        print(f"🟢 规则层体积在棘轮内 —— {len(r['rows'])} 个文件合计 {total}t，"
              f"距上限还有 {headroom}t")


def main() -> int:
    ap = argparse.ArgumentParser(description="规则层体积棘轮（逐文件上限，只降不升）")
    ap.add_argument("--strict", action="store_true", help="有红灯时 exit 2")
    ap.add_argument("--list", action="store_true", dest="list_only",
                    help="打全表当前用量 / 上限")
    args = ap.parse_args()

    root = find_root()
    manifest = root / MANIFEST
    if not manifest.is_file():
        print(f"⚠ 无 {MANIFEST}，skip")
        return 0

    budgets = json.loads(manifest.read_text(encoding="utf-8"))
    sizes = {
        path: ((root / path).stat().st_size if (root / path).is_file() else None)
        for path in budgets
    }
    present = {
        str(p.relative_to(root)) for p in (root / BUDGETED_DIR).glob("*.md")
    } if (root / BUDGETED_DIR).is_dir() else set()

    r = check_budgets(budgets, sizes, present)
    report(r, args.list_only)
    return 2 if (args.strict and has_red(r)) else 0


if __name__ == "__main__":
    sys.exit(main())
