"""神策数值口径：API 返回的负值（如 -1）是稀疏漏斗「无基数」哨兵，统一判 None。

调用方：
- .claude/skills/data-report/scripts/fetch_weekly_sensors.py（周漏斗 + 日粒度漏斗）
"""
from typing import Any


def sa_cnt(v: Any) -> "int | None":
    """UV / 计数类：负值或空 = 神策稀疏漏斗无基数哨兵 → None（不落 0 也不落负数）。"""
    return int(float(v)) if v not in (None, "") and float(v) >= 0 else None


def sa_pct(v: Any) -> "float | None":
    """转化率类：API 给小数 → 百分比（两位小数）；负值或空哨兵 → None。"""
    return round(float(v) * 100, 2) if v not in (None, "") and float(v) >= 0 else None
