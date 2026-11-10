#!/usr/bin/env python3
"""竞品分析报告基础自检 — 机械可判的结构 / 证据项，拦不了的判断类靠 SKILL 自检清单。

用法：
    python3 check_comp_report.py <report.md>     # 检查一份报告
    python3 check_comp_report.py --help          # 本帮助

参数：<report.md> = 竞品分析报告 md 路径（comp-*.md）。

检查项：
    FAIL（阻断）：--- 分隔线 / 第一个 ## 章节不是结论（CRBE 深度版除外）。
    WARN（提示）：决策型缺差异分析表或落地清单 / 有打分矩阵时：疑似硬编、无 👍 /
                  正文出现「模式命名」/ 无「需验证 / 未公开」标注。

前置：无（纯文本扫描，--help 亦不需要）。
退出码：0 = 全过或仅 WARN；1 = 有 FAIL；2 = 用法错 / 读不到文件。
"""
import re
import sys


def find_score_tables(lines):
    """返回疑似打分矩阵的表格块（含多个 1-9 分单元格的连续表格行）。"""
    tables, cur = [], []
    for ln in lines:
        if ln.lstrip().startswith("|"):
            cur.append(ln)
        else:
            if cur:
                tables.append(cur)
            cur = []
    if cur:
        tables.append(cur)
    score = []
    for t in tables:
        cells = " ".join(t)
        header = t[0]
        # 打分矩阵特征：多个 1-9 分单元格，且（表头含「维度」列 或 表内有 👍）
        # 用 header 关键词排除「可借鉴点 / 进度」等含零散数字的表
        n = len(re.findall(r"[1-9]👍?\s*\|", cells))
        is_score = n >= 8 and ("维度" in header or "👍" in cells)
        if is_score:
            score.append(t)
    return score


def main():
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print(__doc__, end="")
        return 0
    if len(sys.argv) != 2:
        print("用法：python3 check_comp_report.py <report.md>")
        return 2
    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"读不到文件：{e}")
        return 2

    lines = text.splitlines()
    fails, warns = [], []

    # FAIL 1: --- 水平分隔线（Confluence 渲染崩）
    for i, ln in enumerate(lines, 1):
        if re.match(r"^\s*-{3,}\s*$", ln):
            fails.append(f"L{i} 用了 --- 水平分隔线（Confluence 渲染崩），改用 ## 标题或空行")

    # FAIL 2: 第一个 ## 章节不是结论（CRBE 深度版按立项调研结构，不卡）
    h2 = [ln for ln in lines if ln.startswith("## ")]
    is_crbe = "CRBE" in text or "Capability" in text
    if h2 and not is_crbe and "结论" not in h2[0]:
        fails.append(f"第一个 ## 章节是「{h2[0][3:].strip()}」，决策型报告第一章应是结论（问题表 + 我方截图 + 建议速览）")

    # WARN: 决策型缺差异分析表 / 落地清单
    if not is_crbe:
        if not any("对我方的判断" in ln or "对 Platform C 的判断" in ln for ln in lines):
            warns.append("没找到差异分析表（列：维度 | 差异点 | 原因分析 | 对我方的判断）")
        if not any(ln.startswith("|") and "优先级" in ln and "配合方" in ln for ln in lines):
            warns.append("没找到落地清单（列含 优先级 / 需配合方）")

    # WARN: 给竞品打法起名字
    if "模式命名" in text:
        warns.append("正文出现「模式命名」：给打法起名字读起来像口号，直接写差异和判断")

    score_tables = find_score_tables(lines)

    # WARN: 打分矩阵疑似硬编（规模够大却一个 — 都没有，可能存在拍脑袋填分）
    for t in score_tables:
        body = [r for r in t if not re.match(r"^\s*\|[-:\s|]+\|?\s*$", r)]  # 去掉表头分隔行
        cells = " ".join(body)
        n_scores = len(re.findall(r"[1-9]", cells))
        if n_scores >= 20 and "—" not in cells:
            warns.append(
                "打分矩阵规模较大却无一格标「—」：确认每格都有截图 / 公开数据支撑，"
                "缺证据的维度应标「—」不硬凑（反脑补第一条）"
            )
            break

    # WARN: 打分表无 👍
    if score_tables and "👍" not in text:
        warns.append("打分矩阵没有 👍 标记最强项，强弱不够一眼可见")

    # WARN: 无「需验证」标注（多为二手数据却全无来源审慎标注）
    if "需验证" not in text and "未公开" not in text:
        warns.append("全文无「需验证 / 未公开」标注：竞品数据多为二手，无来源的数字应标注")

    for m in fails:
        print(f"❌ FAIL: {m}")
    for m in warns:
        print(f"⚠️  WARN: {m}")
    if not fails and not warns:
        print("✅ 基础自检全过")
    elif not fails:
        print("✅ 无 FAIL（WARN 建议处理）")

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
