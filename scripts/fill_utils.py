#!/usr/bin/env python3
"""
通用填充工具 — 所有 fill 脚本 import 此模块。
用法: from fill_utils import fill_block, run_fill
"""
import os, re, sys

def fill_block(html, tag, content):
    """替换 <!-- FILL_START:tag -->...<!-- FILL_END:tag --> 整块。
    即使 content 为空也必须替换以清除标记。"""
    pattern = f'<!-- FILL_START:{tag} -->.*?<!-- FILL_END:{tag} -->'
    matches = re.findall(pattern, html, flags=re.DOTALL)
    if not matches:
        raise RuntimeError(f'FILL 标记未找到: {tag}。骨架可能损坏或标记格式不匹配')
    result = re.sub(pattern, content, html, count=1, flags=re.DOTALL)
    return result


def run_fill(target_path, fills):
    """
    批量填充。
    fills: list of (tag, content_or_fn) — content_or_fn 可以是字符串或无参函数
    """
    if not os.path.exists(target_path):
        print(f'❌ 文件不存在: {target_path}')
        sys.exit(1)

    with open(target_path, 'r', encoding='utf-8') as f:
        html = f.read()

    for tag, content in fills:
        if callable(content):
            content = content()
        html = fill_block(html, tag, content)

    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(html)

    remaining = len(re.findall(r'FILL_START:', html))
    filled = len(fills)
    print(f'✅ 填充 {filled} 个块，剩余 {remaining} 个未填充块')

    if remaining > 0:
        # 列出剩余标记
        tags = re.findall(r'FILL_START:(\S+)', html)
        for t in tags:
            print(f'   待填充: {t}')

    return remaining
