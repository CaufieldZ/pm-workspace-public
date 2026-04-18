#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""
同步中国法定节假日到 holiday-calendar.md

数据源: python-holidays 库 (内置国务院公告数据)
用法:  python3 scripts/sync-holidays.py [年份]
       默认当年，可传 2025 / 2026 等
依赖:  pip install holidays
"""

import sys
from datetime import date, timedelta
from collections import defaultdict

try:
    import holidays
except ImportError:
    print("缺少依赖: pip install holidays")
    sys.exit(1)


def get_holiday_data(year: int):
    """从 holidays 库提取法定假日和调休信息"""
    cn = holidays.China(years=year)

    # 分组：法定假日 vs 调休休息日
    # 法定假日连片归为一组
    statutory = []   # (date, name)
    swapped_rest = []  # (rest_date, work_date) 调休休息日

    for d, name in sorted(cn.items()):
        if "调休" in name:
            # 格式: "休息日（由 2025-01-26 调休）"
            # 提取调休上班日
            import re
            m = re.search(r"由 (\d{4}-\d{2}-\d{2}) 调休", name)
            if m:
                work_date = date.fromisoformat(m.group(1))
                swapped_rest.append((d, work_date))
        else:
            statutory.append((d, name))

    # 将连续的法定假日归组
    # 同名节日 + 补假视为一组（如 "端午节" 和 "端午节（补假）"）
    def base_name(n):
        """提取基础节日名（去掉括号后缀）"""
        for root in ("元旦", "春节", "农历除夕", "清明节", "清明", "劳动节",
                      "端午节", "端午", "中秋节", "中秋", "国庆节", "国庆"):
            if root in n:
                return root.replace("农历", "").replace("节", "")
        return n

    groups = []
    current_group = {"dates": [], "name": ""}

    for d, name in statutory:
        bn = base_name(name)
        if current_group["dates"]:
            last = current_group["dates"][-1]
            gap = (d - last).days
            cur_bn = base_name(current_group["name"])
            same_kind = (bn == cur_bn)

            # 同类节日：gap ≤3 合并（端午+补假 gap=2）
            # 跨类：gap=1 合并（除夕→春节）
            if (same_kind and gap <= 3) or (not same_kind and gap == 1):
                current_group["dates"].append(d)
                # 取主名称
                if "国庆" in name or "国庆" in current_group["name"]:
                    current_group["name"] = "国庆节"
                elif "春节" in name or "除夕" in name or "春节" in current_group["name"] or "除夕" in current_group["name"]:
                    current_group["name"] = "春节"
                elif "端午" in name or "端午" in current_group["name"]:
                    current_group["name"] = "端午节"
                elif "中秋" in name or "中秋" in current_group["name"]:
                    current_group["name"] = "中秋节"
                else:
                    current_group["name"] = name.replace("（补假）", "")
            else:
                groups.append(current_group)
                current_group = {"dates": [d], "name": name}
        else:
            current_group = {"dates": [d], "name": name}

    if current_group["dates"]:
        groups.append(current_group)

    return groups, swapped_rest


def weekday_cn(d: date) -> str:
    """返回中文星期"""
    days = ["一", "二", "三", "四", "五", "六", "日"]
    return f"周{days[d.weekday()]}"


def format_date_range(dates: list) -> str:
    """格式化日期范围显示"""
    if len(dates) == 1:
        d = dates[0]
        return f"{d.month:02d}.{d.day:02d}（{weekday_cn(d)}）"

    start, end = dates[0], dates[-1]
    return f"{start.month:02d}.{start.day:02d}~{end.month:02d}.{end.day:02d}（{weekday_cn(start)}~{weekday_cn(end)}）"


def calc_affected_weeks(groups: list) -> list:
    """计算每个假期影响的周报周期（上周六~本周五）"""
    affected = []
    for g in groups:
        start = g["dates"][0]
        end = g["dates"][-1]
        # 找到假期所在的周五
        # 周报周期: 上周六~本周五
        # 如果假期在某周周期内，那周就受影响
        # 先找 end 所在周的周五
        d = end
        while d.weekday() != 4:  # Friday
            d += timedelta(days=1)
        # 这个周五是 target_friday
        week_start = d - timedelta(days=6)

        weeks = set()
        # 检查假期的每一天落在哪些周报周期内
        for hd in g["dates"]:
            # 找 hd 所在的周五
            fri = hd
            while fri.weekday() != 4:
                fri += timedelta(days=1)
            sat = fri - timedelta(days=6)
            weeks.add((sat, fri))

        affected.append(sorted(weeks))
    return affected


def generate_markdown(year: int) -> str:
    """生成 holiday-calendar.md 内容"""
    groups, swapped_rest = get_holiday_data(year)
    affected_weeks = calc_affected_weeks(groups)

    lines = []
    lines.append(f"# {year} 年中国法定节假日 & 调休日历")
    lines.append("")
    lines.append("周报日期范围默认为上周六~本周五。遇节假日时标注「节假周」，数据完整展示但分析说明节假影响。")
    lines.append("")
    lines.append("> 本文件由 `scripts/sync-holidays.py` 自动生成，数据源为 python-holidays 库。")
    lines.append(f"> 生成时间: {date.today().isoformat()}")
    lines.append("")
    lines.append("## 法定节假日")
    lines.append("")
    lines.append("| 节日 | 放假时间 | 调休上班 | 影响周报周期 |")
    lines.append("| --- | --- | --- | --- |")

    for i, g in enumerate(groups):
        name = g["name"]
        date_range = format_date_range(g["dates"])

        # 找对应的调休上班日
        workdays = []
        holiday_start = g["dates"][0]
        holiday_end = g["dates"][-1]
        for rest_d, work_d in swapped_rest:
            if holiday_start - timedelta(days=3) <= work_d <= holiday_end + timedelta(days=14):
                workdays.append(work_d)

        work_str = "、".join(
            f"{wd.month:02d}.{wd.day:02d}({weekday_cn(wd)})"
            for wd in sorted(workdays)
        ) if workdays else "无"

        # 影响周报
        if i < len(affected_weeks):
            week_strs = []
            for sat, fri in affected_weeks[i]:
                week_strs.append(f"{sat.month:02d}.{sat.day:02d}~{fri.month:02d}.{fri.day:02d}")
            week_str = "、".join(week_strs)
            count = len(affected_weeks[i])
            if count > 1:
                week_str += f" {count} 周标注"
            else:
                week_str += " 周报标注"
        else:
            week_str = "—"

        lines.append(f"| {name} | {date_range} | {work_str} | {week_str} |")

    lines.append("")
    lines.append("## 周报周期计算逻辑")
    lines.append("")
    lines.append("```python")
    lines.append("def get_week_range(target_friday):")
    lines.append('    """')
    lines.append("    周报周期 = 上周六 ~ 本周五")
    lines.append("    target_friday: 本周五的日期")
    lines.append('    """')
    lines.append("    start = target_friday - timedelta(days=6)  # 上周六")
    lines.append("    end = target_friday                         # 本周五")
    lines.append("    return start, end")
    lines.append("```")
    lines.append("")
    lines.append("## 节假日标注规则")
    lines.append("")
    lines.append("1. 如果周期内包含法定假日 ≥1 天，在报告标题后追加「（含 XX 假期）」")
    lines.append("2. 分析洞察中主动说明：「本周含 X 天法定假期，数据可能偏低/偏高，环比仅供参考」")
    lines.append("3. 节假周的环比不纳入趋势判断（不标 ↑/↓，标 ⚠️）")
    lines.append("")
    lines.append("## 月报 & 季报周期")
    lines.append("")
    lines.append("- 月报：本月 1 日 ~ 下月 1 日（不含），如 04.01~05.01")
    lines.append(f"- 季报：Q1=01.01~04.01, Q2=04.01~07.01, Q3=07.01~10.01, Q4=10.01~{year+1}-01-01")
    lines.append("")
    lines.append("## 备注")
    lines.append("")
    lines.append(f"- 以上日期基于 python-holidays 库（{year} 年国务院放假通知数据）")
    lines.append("- 调休日虽为工作日，但用户行为模式可能受影响，分析时注意")
    lines.append(f"- 如需更新：`python3 scripts/sync-holidays.py [{year}]`")

    return "\n".join(lines) + "\n"


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else date.today().year
    print(f"生成 {year} 年节假日日历...")

    md = generate_markdown(year)
    out_path = f".claude/skills/data-report/references/holiday-calendar.md"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"已写入 {out_path}")

    # 预览
    groups, _ = get_holiday_data(year)
    print(f"\n{year} 年法定假日共 {len(groups)} 组:")
    for g in groups:
        print(f"  {g['name']}: {g['dates'][0]} ~ {g['dates'][-1]}")


if __name__ == "__main__":
    main()
