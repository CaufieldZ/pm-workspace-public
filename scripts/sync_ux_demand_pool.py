#!/usr/bin/env python3
"""体验专项需求池同步 — Google Sheets API（Service Account），按业务规则筛选 Felix 工区。

凭据：~/.config/gcloud/pm-sheet-sa.json（chmod 600）
Sheet: 体验专项需求池 / 需求主表 tab (gid 561565713)

筛选规则（Felix · 社区+直播 工区）：
1. Col 3 或 Col 4 命中「增长」（一级或子类属增长大盘）
2. Col 12 排除「已上线」状态（10-已上线）
3. Col 7 描述包含社区 / 直播 / 内容生态 / 角色 / 跳转交互 类关键词

输出：references/ux-demand-pool.md（gitignored）
"""

from __future__ import annotations

import argparse

# route-log: 调用埋点（scripts/lib/route_log.py）
import pathlib as _pl
import sys
from datetime import datetime
from pathlib import Path

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (sys.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("sync_ux_demand_pool"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lib.demand_pool_base import DemandPoolBase

SHEET_ID = "1AzifrlpKP4NLWVLiKeun_ekk8BUIhuF7Kvp1UmetE5c"
TAB_TITLE = "需求主表"
GID = 561565713

DIRECTION_COLS = (2, 3)
DIRECTION_KEYWORD = "增长"
STATUS_COL = 11
DESC_COL = 6
EXCLUDE_STATUS = ["已上线", "不处理"]

WORK_KEYWORDS = [
    "社区", "直播", "Feed", "feed", "发帖", "评论", "点赞", "直播间",
    "榜单", "牛人榜",
    "文章", "帖子", "内容", "创作者",
    "KOL", "kol", "主播", "带单", "牋人",
    "币种卡片", "K线卡", "k线卡", "关注",
]

OUTPUT_COLS = [
    (0, "日期"), (2, "方向"), (3, "子类"), (4, "来源"), (5, "类型"),
    (7, "端"), (9, "优先级"), (11, "状态"), (12, "迭代"), (15, "季度"),
    (16, "PM 备注"), (6, "描述"),
]


class UxDemandPool(DemandPoolBase):
    SHEET_ID = SHEET_ID
    TAB_TITLE = TAB_TITLE
    GID = GID
    OUT_FILE = ROOT / "references" / "ux-demand-pool.md"

    def filter_rows(self, rows: list[list]) -> list[tuple[int, list]]:
        out = []
        for i, row in enumerate(rows, 1):
            if i == 1:
                continue
            if len(row) <= max(DESC_COL, STATUS_COL):
                continue
            col3 = str(row[DIRECTION_COLS[0]]).strip()
            col4 = str(row[DIRECTION_COLS[1]]).strip()
            status = str(row[STATUS_COL]).strip()
            desc = str(row[DESC_COL])
            if DIRECTION_KEYWORD not in col3 and DIRECTION_KEYWORD not in col4:
                continue
            if any(x in status for x in EXCLUDE_STATUS):
                continue
            if not any(k in desc for k in WORK_KEYWORDS):
                continue
            out.append((i, row))
        return out

    def render_md(self, matched: list[tuple[int, list]], total: int) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            "# 体验专项需求池 · Felix（社区+直播）视图", "",
            f"_拉取时间：{ts} · 命中 {len(matched)} / 全表 {total} 条_", "",
            f"数据源：[Google Sheet](https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid={GID})"
            f" · 同步脚本 `scripts/sync_ux_demand_pool.py`（SA 模式）", "",
            f"**筛选规则**：Col 3/4 含「增长」+ Col 12 排除「已上线」+ "
            f"描述含社区/直播相关词（共 {len(WORK_KEYWORDS)} 个，详见脚本 `WORK_KEYWORDS`）", "",
        ]
        if not matched:
            lines.append("> 无匹配行。")
            return "\n".join(lines) + "\n"

        lines += self.render_table(matched, OUTPUT_COLS, max_len=200)
        return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd")

    p_pull = sub.add_parser("pull", help="拉取并筛选 → md（默认）")
    p_pull.add_argument("--dry-run", action="store_true", help="只打印 md，不写文件")

    p_wb = sub.add_parser("writeback", help="反写单元格")
    p_wb.add_argument("--row", type=int, required=True, help="sheet 1-based 行号")
    p_wb.add_argument("--col", type=int, required=True, help="0-based 列号")
    p_wb.add_argument("--value", required=True, help="要写入的值")
    p_wb.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    cmd = args.cmd or "pull"
    pool = UxDemandPool()

    if cmd == "pull":
        return pool.cmd_pull(args)
    elif cmd == "writeback":
        return pool.cmd_writeback(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
