"""export_tracking_xlsx.parse_table 分隔行识别回归。

锁回归：分隔行判定不能只看 cells[0]——所属页面留空（合并单元格续行）或填 `-` 占位的
真实埋点行，set(cells[0]) <= set(': -') 会为真被误删。改判「每格都是分隔字符」才是分隔行。
"""
import sys
from pathlib import Path

_PRD_SCRIPTS = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "prd" / "scripts"
sys.path.insert(0, str(_PRD_SCRIPTS))

import export_tracking_xlsx as et  # noqa: E402

_MD = """
| 所属页面 | 事件时机 | 事件英文名 | c4 | c5 | c6 | c7 | c8 | c9 | c10 |
|---|---|---|---|---|---|---|---|---|---|
| 首页 | 曝光 | home_expose | a | b | c | d | e | f | g |
|  | 点击 | home_click | a | b | c | d | e | f | g |
| - | 停留 | home_stay | a | b | c | d | e | f | g |
"""


def test_blank_and_dash_owner_rows_kept():
    rows = et.parse_table(_MD)
    events = [r[2] for r in rows]
    # 分隔行（第 2 行 |---|）跳过；空 / `-` 所属页面的续行全部保留
    assert events == ["home_expose", "home_click", "home_stay"]
