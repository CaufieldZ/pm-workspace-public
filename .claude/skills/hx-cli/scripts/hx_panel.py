#!/usr/bin/env python3
"""个人面板汇总（只读链，抽象 personal-panel.md 的 stats + list 查询）。

personal stats + personal list --filter overdue/current/future → 汇总成
「待处理/进行中/已完成/逾期」统计 + 逾期&进行中明细表（Markdown）。

用法：
    python3 hx_panel.py                # 统计 + 逾期 + 进行中明细
    python3 hx_panel.py --json         # 结构化 JSON
    python3 hx_panel.py --filter future --filter current   # 指定要拉明细的分组

只读，不写入。改状态/进度/风险走 work.md 写流程（须人工确认）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hx_client as hx  # noqa: E402

_STATS_LABEL = {
    "future_me": "待处理",
    "current_me": "进行中",
    "past_me": "已完成",
    "overdue_me": "已逾期",
}


def _row_brief(r: dict) -> dict:
    """从 personal list 的行抽出展示字段。"""
    execs = ", ".join(e.get("name", "") for e in (r.get("executor") or []))
    return {
        "pha_id": r.get("pha_id"),
        "work_id": r.get("id"),
        "title": r.get("work_name"),
        "type": (r.get("new_work_type") or {}).get("type_name"),
        "project": r.get("prj_name"),
        "process": r.get("current_process"),
        "end_time": r.get("end_time"),
        "progress": r.get("percentage_progress"),
        "priority": r.get("priority_display"),
        "executors": execs,
        "link": hx.work_link(r.get("id")),
    }


def gather(filters: list[str], token: str | None = None, page_size: int = 30) -> dict:
    hx.ensure_auth(token=token)
    stats = hx.run(["personal", "stats"], token=token)
    out: dict = {"stats": stats, "lists": {}}
    for f in filters:
        data = hx.run(
            ["personal", "list", "--filter", f, "--page", "1", "--page-size", str(page_size)],
            token=token,
        )
        rows = data.get("rows") or []
        out["lists"][f] = {
            "total": data.get("total", len(rows)),
            "rows": [_row_brief(r) for r in rows],
        }
    return out


def _table(rows: list[dict]) -> str:
    if not rows:
        return "（无）"
    head = "| 优先级 | 工作项 | 类型 | 项目 | 流程状态 | 截止 | 进度 |"
    sep = "| --- | --- | --- | --- | --- | --- | --- |"
    body = [
        f"| {r['priority'] or '—'} | [{r['pha_id']}]({r['link']}) {r['title']} "
        f"| {r['type'] or '—'} | {r['project'] or '—'} | {r['process'] or '—'} "
        f"| {r['end_time'] or '—'} | {r['progress'] if r['progress'] is not None else '—'} |"
        for r in rows
    ]
    return "\n".join([head, sep, *body])


def render(data: dict) -> str:
    s = data["stats"]
    parts = [
        "个人面板：" + " · ".join(
            f"{lbl} {s.get(k, 0)}" for k, lbl in _STATS_LABEL.items()
        ),
    ]
    order = ["overdue", "current", "future", "past"]
    label = {"overdue": "已逾期", "current": "进行中", "future": "待处理", "past": "已完成"}
    for f in order:
        if f in data["lists"]:
            lst = data["lists"][f]
            parts.append("")
            parts.append(f"### {label.get(f, f)}（{lst['total']}）")
            parts.append(_table(lst["rows"]))
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description="个人面板汇总（只读）")
    ap.add_argument("--filter", action="append", dest="filters",
                    help="要拉明细的分组，可多次：overdue/current/future/past/all/create。缺省 overdue+current")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ap.add_argument("--token", help="覆盖 AIHUB_TOKEN，仅本次")
    args = ap.parse_args()
    filters = args.filters or ["overdue", "current"]

    try:
        data = gather(filters, token=args.token)
    except hx.HxAuthError as e:
        print(f"认证失败：{e}\n下一步：{e.hint}", file=sys.stderr)
        return 2
    except hx.HxError as e:
        print(f"调用失败：{e}", file=sys.stderr)
        return 1

    print(json.dumps(data, ensure_ascii=False) if args.json else render(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
