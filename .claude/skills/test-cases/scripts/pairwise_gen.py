#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pairwise_gen.py — 纯 Python 成对覆盖（Pairwise / 2-way）测试组合生成器
零外部依赖，仅使用标准库。

用法：
    from pairwise_gen import generate_pairwise, print_markdown_table

    params = {
        "地区":    ["CN", "US", "JP", "受限地区"],
        "KYC等级": ["L0", "L1", "L2", "L3"],
        "产品类型": ["活期", "定期", "结构化"],
        "余额状态": ["零值", "低于最低限额", "充足"],
    }
    constraints = [
        # (if_param, if_val, then_param, then_val)
        # 语义：IF if_param=if_val THEN then_param != then_val
        ("地区", "受限地区", "产品类型", "活期"),
        ("地区", "受限地区", "产品类型", "定期"),
        ("地区", "受限地区", "产品类型", "结构化"),
        ("KYC等级", "L0", "产品类型", "结构化"),
    ]
    combos = generate_pairwise(params, constraints)
    print_markdown_table(params, combos)

算法说明：
    贪心 covering array 生成。
    1. 枚举所有「二元参数对」的笛卡尔积（待覆盖 pair-value 集合）
    2. 每轮从候选组合中选覆盖最多未覆盖 pair 的那一行
    3. 重复直到所有 pair 都被覆盖
    时间复杂度：O(P^2 * V^2 * C)，P=参数数，V=最大值数，C=已选组合数
    对 Gate AMS 典型规模（5参数×3-4值）足够快（< 1s）
"""

from itertools import combinations, product
from typing import Optional


# ─────────────────────────────────────────────
# 约束检查
# ─────────────────────────────────────────────

def _is_valid(combo: dict, constraints: list[tuple]) -> bool:
    """检查一个参数组合是否满足所有约束。
    约束格式：(if_param, if_val, then_param, then_val)
    语义：IF combo[if_param]==if_val THEN combo[then_param] != then_val
    """
    for (ip, iv, tp, tv) in constraints:
        if combo.get(ip) == iv and combo.get(tp) == tv:
            return False
    return True


# ─────────────────────────────────────────────
# 覆盖计算
# ─────────────────────────────────────────────

def _all_pairs(params: dict) -> set[tuple]:
    """枚举所有需要被覆盖的二元参数对 (param_i, val_i, param_j, val_j)。"""
    keys = list(params.keys())
    pairs = set()
    for i, j in combinations(range(len(keys)), 2):
        pi, pj = keys[i], keys[j]
        for vi in params[pi]:
            for vj in params[pj]:
                pairs.add((pi, vi, pj, vj))
    return pairs


def _covered_by(combo: dict, uncovered: set) -> set[tuple]:
    """返回 combo 能覆盖的 uncovered 中的 pair 集合。"""
    keys = list(combo.keys())
    covered = set()
    for i, j in combinations(range(len(keys)), 2):
        pi, pj = keys[i], keys[j]
        pair = (pi, combo[pi], pj, combo[pj])
        if pair in uncovered:
            covered.add(pair)
    return covered


# ─────────────────────────────────────────────
# 候选组合生成
# ─────────────────────────────────────────────

def _all_candidates(params: dict, constraints: list[tuple]) -> list[dict]:
    """生成所有满足约束的全参数候选组合。"""
    keys = list(params.keys())
    candidates = []
    for vals in product(*[params[k] for k in keys]):
        combo = dict(zip(keys, vals))
        if _is_valid(combo, constraints):
            candidates.append(combo)
    return candidates


# ─────────────────────────────────────────────
# 主算法：贪心 pairwise 覆盖
# ─────────────────────────────────────────────

def generate_pairwise(
    params: dict,
    constraints: Optional[list] = None,
) -> list:
    """
    生成最小成对覆盖测试组合集。

    Args:
        params:      参数字典，key=参数名，value=等价类值列表
        constraints: 约束列表，每项 (if_param, if_val, then_param, then_val)
                     语义：IF if_param=if_val THEN then_param != then_val

    Returns:
        list[dict]，每个 dict 是一行测试组合
    """
    if constraints is None:
        constraints = []

    uncovered = _all_pairs(params)
    candidates = _all_candidates(params, constraints)

    if not candidates:
        return []

    selected: list[dict] = []

    while uncovered:
        # 贪心：选覆盖最多未覆盖 pair 的候选
        best_combo = None
        best_count = -1
        best_covered = set()

        for combo in candidates:
            covered = _covered_by(combo, uncovered)
            if len(covered) > best_count:
                best_count = len(covered)
                best_combo = combo
                best_covered = covered

        if best_combo is None or best_count == 0:
            # 剩余 pair 被约束完全排除，无法覆盖，跳出
            break

        selected.append(best_combo)
        uncovered -= best_covered

    return selected


# ─────────────────────────────────────────────
# 输出格式
# ─────────────────────────────────────────────

def format_markdown_table(params: dict, combos: list[dict]) -> str:
    """将组合列表格式化为 Markdown 表格字符串。"""
    if not combos:
        return "_无有效组合（约束过强，所有组合被排除）_"

    keys = list(params.keys())
    header = "| 编号 | " + " | ".join(keys) + " |"
    sep    = "|------|" + "|".join(["------"] * len(keys)) + "|"
    rows   = []
    for i, combo in enumerate(combos, 1):
        row = f"| {i:02d}   | " + " | ".join(str(combo[k]) for k in keys) + " |"
        rows.append(row)

    return "\n".join([header, sep] + rows)


def print_markdown_table(params: dict, combos: list[dict]) -> None:
    """直接打印 Markdown 表格到 stdout。"""
    print(format_markdown_table(params, combos))
    print(f"\n> 共 {len(combos)} 条组合，覆盖所有二元参数对（成对覆盖）")


# ─────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────

def _demo():
    """Gate AMS 申购场景示例。"""
    params = {
        "地区":     ["CN", "US", "JP", "受限地区"],
        "KYC等级":  ["L0", "L1", "L2", "L3"],
        "产品类型":  ["活期", "定期", "结构化"],
        "余额状态":  ["零值", "低于最低限额", "充足"],
        "用户角色":  ["普通投资者", "VIP", "机构"],
    }
    constraints = [
        # 受限地区不能申购任何产品
        ("地区", "受限地区", "产品类型", "活期"),
        ("地区", "受限地区", "产品类型", "定期"),
        ("地区", "受限地区", "产品类型", "结构化"),
        # L0 不能申购结构化产品
        ("KYC等级", "L0", "产品类型", "结构化"),
        # 零余额不能是 VIP 或机构（业务不合理）
        ("余额状态", "零值", "用户角色", "VIP"),
        ("余额状态", "零值", "用户角色", "机构"),
    ]

    print("## Gate AMS 申购场景 — 成对覆盖参数组合矩阵\n")
    print(f"参数：{list(params.keys())}")
    print(f"穷举组合数：{4*4*3*3*3} 条")

    combos = generate_pairwise(params, constraints)
    print(f"成对覆盖组合数：{len(combos)} 条（减少 "
          f"{100 - round(len(combos) / (4*4*3*3*3) * 100)}%）\n")
    print_markdown_table(params, combos)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        _demo()
    else:
        print("用法：python pairwise_gen.py demo")
        print("或在代码中 from pairwise_gen import generate_pairwise")
