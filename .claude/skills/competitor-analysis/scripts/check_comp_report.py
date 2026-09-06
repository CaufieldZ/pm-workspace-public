#!/usr/bin/env python3
"""竞品分析报告基础自检 — 机械可判的结构 / 证据项，拦不了的判断类靠 SKILL 自检清单。

用法：python3 check_comp_report.py <report.md>
退出码：0 = 全过，1 = 有 FAIL，2 = 用法错。
FAIL（阻断）：--- 分隔线 / 打分矩阵疑似硬编（全数字无 — 且规模大）/ 缺打分矩阵。
WARN（提示）：打分表无 👍 / 无「需验证」标注 / 无翻车风险列 / 无我方进度图例。
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

    # FAIL 2: 缺打分矩阵
    score_tables = find_score_tables(lines)
    if not score_tables:
        fails.append("没找到打分矩阵（功能维度 × 平台的 1-9 分表），深度版必须有")

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

    # WARN: 无我方进度图例
    if not re.search(r"[🟢🟡🔵🔴⚫]", text):
        warns.append("无我方进度图例（🟢🟡🔵🔴⚫）：每条可借鉴点应标我方进度")

    # WARN: 无翻车风险
    if "翻车" not in text and "风险" not in text:
        warns.append("全文无「翻车 / 风险」：每条可借鉴点应附直接抄的翻车风险")

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
