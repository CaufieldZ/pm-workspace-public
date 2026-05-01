#!/usr/bin/env python3
"""扫 context.md 第 7 章「设计决策」表格，吐出当前 Active 决策列表。

设计原则（pm-workflow.md 元问题 2 答复）：
- 旧决策行不改不删（守住「按日期追加不改不删」）
- Status 不在表格里维护，由本脚本扫描 supersedes 关系派生
- 新决策推翻旧决策时，在自己「关系/竞品」列写 `supersedes: D{n}`，多重用逗号分隔

兼容性：
- 新 6 列表格按显式 ID 列读取
- 旧 4/5 列表格无 ID 列时，按行号自动派生 D1, D2, ...
- **list 格式**（老项目第 7 章是 `1. **决策项**：...` 顺序号列表，
  如 activity-center context.md 第 7 章 38 条）：按行号派生 D1..Dn，
  supersedes 关系空（list 格式不维护推翻关系），全部当 Active 输出
  ——配合 chat-templates/context-template.md「老项目零迁移」声明。

边界：
- 循环引用（D5 supersedes D10 / D10 supersedes D5）→ raise + stderr，exit 1
- 悬空引用（supersedes: D99 但 D99 不存在）→ stderr warn，treat as standalone
"""
import argparse
import json
import re
import sys
from pathlib import Path


def extract_section_7(md_text: str) -> str:
    """从 context.md 全文中提取第 7 章「设计决策」内容。

    匹配 `## 7.` 或 `## 七、` 开头，到下一个 `## ` 为止。
    """
    pat = re.compile(r'^##\s+(?:7\.|七、)[^\n]*\n', re.MULTILINE)
    m = pat.search(md_text)
    if not m:
        raise SystemExit('❌ 找不到第 7 章「设计决策」（## 7. 或 ## 七、）')
    start = m.end()
    next_sec = re.search(r'^##\s+(?:8\.|八、)', md_text[start:], re.MULTILINE)
    end = start + next_sec.start() if next_sec else len(md_text)
    return md_text[start:end]


def find_first_table(section_text: str) -> list[list[str]] | None:
    """提取章节内第一个 markdown 表格，返回 [[header...], [row1...], ...]。
    没找到返回 None（让上层 fallback 到 list 格式）。
    """
    lines = [ln.rstrip() for ln in section_text.splitlines()]
    table_rows = []
    in_table = False
    for ln in lines:
        if ln.startswith('|'):
            cells = [c.strip() for c in ln.strip('|').split('|')]
            if all(set(c) <= set('-: ') for c in cells if c):
                continue  # 分隔行 |---|---|
            table_rows.append(cells)
            in_table = True
        elif in_table:
            break
    return table_rows or None


# ── list 格式兼容（老项目第 7 章 `1. **决策项**：...` 顺序号列表）─────────
# 例：activity-center context.md 38 条决策都是这个格式
LIST_ITEM_RE = re.compile(
    r'^\s*(\d+)\.\s+\*\*([^*]+)\*\*\s*[:：]?\s*(.*)$'
)
# 决策标题里嵌的日期，如 `**M-2 表单重排（2026-04-16）**`
DATE_IN_TOPIC_RE = re.compile(r'[（(](\d{4}-\d{2}-\d{2})[）)]')


def find_list_items(section_text: str) -> list[tuple[int, str, str]] | None:
    """解析 `1. **决策项**：内容` 顺序号列表。

    返回 [(index, topic, body), ...]，没匹配到返回 None。
    """
    items = []
    for ln in section_text.splitlines():
        m = LIST_ITEM_RE.match(ln)
        if m:
            idx = int(m.group(1))
            topic = m.group(2).strip()
            body = m.group(3).strip()
            items.append((idx, topic, body))
    return items or None


def parse_decisions_from_list(items: list[tuple[int, str, str]]) -> list[dict]:
    """list 格式 → decisions 列表。supersedes 空，全部 Active。"""
    decisions = []
    for idx, topic, body in items:
        m = DATE_IN_TOPIC_RE.search(topic)
        date = m.group(1) if m else ''
        decisions.append({
            'id': f'D{idx}',
            'date': date,
            'topic': topic,
            'conclusion': body[:100] if body else '',
            'reason': body[100:200] if len(body) > 100 else '',
            'relation': '',
            'supersedes': [],
        })
    return decisions


def parse_decisions(table: list[list[str]]) -> list[dict]:
    """解析表格成决策列表。

    兼容三种列布局：
    - 4 列旧版：决策项 / 结论 / 理由 / 竞品参考
    - 5 列旧版：日期 / 决策项 / 结论 / 理由 / 竞品参考
    - 6 列新版：日期 / ID / 决策项 / 结论 / 理由 / 关系/竞品
    """
    header = [h.lower() for h in table[0]]
    rows = table[1:]
    has_id = any('id' in h for h in header)
    has_date = any('日期' in h or 'date' in h for h in header)

    decisions = []
    for idx, row in enumerate(rows, 1):
        # 跳过示例行（含「（示例）」标记）
        if any('（示例）' in c or '(示例)' in c for c in row):
            continue
        if has_id and has_date:
            # 6 列：日期 ID 决策项 结论 理由 关系
            date, did, topic, conclusion, reason, rel = (row + [''] * 6)[:6]
        elif has_date:
            # 5 列：日期 决策项 结论 理由 竞品
            date, topic, conclusion, reason, rel = (row + [''] * 5)[:5]
            did = f'D{idx}'
        else:
            # 4 列：决策项 结论 理由 竞品
            topic, conclusion, reason, rel = (row + [''] * 4)[:4]
            date, did = '', f'D{idx}'
        decisions.append({
            'id': did,
            'date': date,
            'topic': topic,
            'conclusion': conclusion,
            'reason': reason,
            'relation': rel,
            'supersedes': parse_supersedes(rel),
        })
    return decisions


SUPERSEDES_RE = re.compile(r'supersedes\s*:\s*([D\d,\s]+)', re.IGNORECASE)


def parse_supersedes(rel_text: str) -> list[str]:
    """从「关系/竞品」列文本提取 supersedes 引用，支持逗号分隔多重。"""
    m = SUPERSEDES_RE.search(rel_text)
    if not m:
        return []
    raw = m.group(1)
    return [t.strip() for t in re.split(r',\s*', raw) if t.strip()]


def detect_cycle(decisions: list[dict]) -> list[str] | None:
    """DFS 检测 supersedes 关系图中的环，返回环上 ID 列表（无环返回 None）。"""
    by_id = {d['id']: d for d in decisions}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {d['id']: WHITE for d in decisions}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        if color.get(node) == GRAY:
            i = stack.index(node)
            return stack[i:] + [node]
        if color.get(node) == BLACK or node not in by_id:
            return None
        color[node] = GRAY
        stack.append(node)
        for tgt in by_id[node]['supersedes']:
            cyc = visit(tgt)
            if cyc:
                return cyc
        stack.pop()
        color[node] = BLACK
        return None

    for d in decisions:
        cyc = visit(d['id'])
        if cyc:
            return cyc
    return None


def compute_active(decisions: list[dict]) -> list[dict]:
    """返回未被任何活跃决策 supersedes 的决策列表。

    悬空引用：supersedes 的目标不存在 → stderr warn 但保留该决策为 standalone Active。
    """
    ids = {d['id'] for d in decisions}
    superseded = set()
    for d in decisions:
        for tgt in d['supersedes']:
            if tgt not in ids:
                print(
                    f'⚠️  {d["id"]} references unknown decision {tgt}, '
                    f'treated as standalone',
                    file=sys.stderr,
                )
            else:
                superseded.add(tgt)
    return [d for d in decisions if d['id'] not in superseded]


def render_markdown(active: list[dict]) -> str:
    out = ['| 日期 | ID | 决策项 | 结论 | 理由 | 关系/竞品 |',
           '|------|-----|--------|------|------|-----------|']
    for d in active:
        out.append(
            f'| {d["date"]} | {d["id"]} | {d["topic"]} | '
            f'{d["conclusion"]} | {d["reason"]} | {d["relation"]} |'
        )
    return '\n'.join(out)


def load_active_decisions(context_path: Path) -> list[dict]:
    """模块入口：供下游 sections.py 调用。

    解析顺序：先尝试表格格式（新模板 / 旧 4-5 列），fallback 到 list 格式
    （老项目第 7 章 `1. **决策项**：...`）。两种都找不到才 raise。
    """
    text = context_path.read_text(encoding='utf-8')
    section = extract_section_7(text)

    table = find_first_table(section)
    if table is not None:
        decisions = parse_decisions(table)
    else:
        items = find_list_items(section)
        if items is None:
            raise SystemExit(
                '❌ 第 7 章既无 markdown 表格也无 `1. **决策项**：...` 列表。'
                '\n   规范见 .claude/chat-templates/context-template.md 第 7 章'
            )
        decisions = parse_decisions_from_list(items)

    cycle = detect_cycle(decisions)
    if cycle:
        raise ValueError(f'❌ 发现循环引用: {" → ".join(cycle)}')
    return compute_active(decisions)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('context', type=Path, help='context.md 路径')
    ap.add_argument('--json', action='store_true', help='输出 JSON 而非 markdown')
    args = ap.parse_args()

    if not args.context.exists():
        sys.exit(f'❌ 文件不存在: {args.context}')

    try:
        active = load_active_decisions(args.context)
    except ValueError as e:
        sys.exit(str(e))

    if args.json:
        print(json.dumps(active, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(active))


if __name__ == '__main__':
    main()
