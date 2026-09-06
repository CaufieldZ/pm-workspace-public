"""场景编号严格匹配 + 父子覆盖 + scene-list 抽取。

跨脚本共享，替代以下三处各自手写的提取 / 匹配逻辑：
- scripts/check_html.sh:49-63（已迁移到 check_imap.sh / check_proto.sh 各自分支）
- scripts/audit-fast.sh:58-81（场景编号一致性）
- scripts/impact-check.sh:26-99（增量影响检测）

历史问题：
- 旧代码用 `grep -qi "${sid}[^a-zA-Z0-9]\\|${sid}\\$"` 单字符匹配
  → 单字母 ID `A / B / M` 在任意 HTML / md 里几乎必命中（class="add" / <a>），假阳率高
- 子编号 `B-1a/b/c` 斜杠并列只看首项
- scene-list 抽取三处规则不一，各有遗漏

新规则：
- 多字符 ID（B-1a 这种）：严格词边界
- 单字符 ID（A）：要求锚点形态（A-N 子编号 / A · / >A< / phone-label">A）
- 父子覆盖：A 在文本里有任意 A-N 即视为覆盖
"""
from __future__ import annotations

import re
from pathlib import Path

# scene-list.md 表格第一列编号格式：
# A / A-1 / A-1a / M0 / F-0a / B-1a/b/c（斜杠展开为多条）
_TABLE_CELL_RE = re.compile(
    r'^\|\s*([A-Z][0-9]*(?:-[0-9]+[a-z]?(?:/[a-z])*)?)\s*\|'
)
# 单格内斜杠并列展开形式：B-1a/b/c → ['B-1a','B-1b','B-1c']
_SLASH_EXPAND_RE = re.compile(r'^([A-Z][0-9]*-[0-9]+)([a-z](?:/[a-z])+)$')


def extract_scene_ids(scene_list_path: str | Path) -> list[str]:
    """从 scene-list.md 抽取所有场景编号（有序、去重）。

    格式：markdown 表格第一列，跳过表头分隔行 / 辅助说明段。
    """
    path = Path(scene_list_path)
    if not path.exists():
        return []
    text = path.read_text(encoding='utf-8', errors='replace')
    ids: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        line = line.rstrip()
        if not line.startswith('|'):
            continue
        # 跳过表头分隔行（整行仅 | : - 空格）与表头行；
        # 不用 `'---' in line`——那会误删说明列含 `---` 的真实场景行（如「A --- B 转账」）
        if set(line) <= set('|:- ') or line.startswith('| 编号') or line.startswith('|编号'):
            continue
        m = _TABLE_CELL_RE.match(line)
        if not m:
            continue
        raw = m.group(1)
        # 噪音过滤：业务词 / View 标记 / P0 / 占位
        if raw in {'View', 'P0', 'P1', 'P2', 'P3', '本项目场景', '动作', '目标'}:
            continue
        # 斜杠并列展开
        ms = _SLASH_EXPAND_RE.match(raw)
        if ms:
            head, tail = ms.group(1), ms.group(2)
            variants = tail.split('/')
            for v in variants:
                full = head + v
                if full not in seen:
                    seen.add(full)
                    ids.append(full)
        else:
            if raw not in seen:
                seen.add(raw)
                ids.append(raw)
    return ids


def id_covered_in_text(sid: str, text: str) -> bool:
    """判断场景编号 sid 是否在文本里"有效出现"。

    - 多字符 ID（含 `-`）：要求严格词边界，前后非 `[A-Za-z0-9-]`
    - 单字符 ID（A/B/M 等）：要求锚点形态之一：
        * 子编号形式 A-N（父级被子级覆盖）
        * A · 业务白话
        * >A<（HTML 文本节点单独成项）
        * phone-label / gd-num / id="scene-A" 类锚点容器
    """
    if not sid:
        return False
    if '-' in sid or len(sid) > 1:
        # 多字符或带子编号：严格词边界
        # 前边界允许 `-`（兼容 scene-B-1 / id="scene-B-1"），只防字母数字吞噬
        # 后边界禁字母 / 数字 / `-`，防 B-1 吞 B-10 / B-1a
        pat = re.compile(rf'(?<![A-Za-z0-9]){re.escape(sid)}(?![A-Za-z0-9-])')
        return bool(pat.search(text))
    # 单字符
    if not re.fullmatch(r'[A-Z]', sid):
        return False
    # 锚点形态之一
    patterns = [
        rf'\b{sid}-[0-9]',                                # 父级被子级覆盖：A-1 / A-2
        rf'\b{sid}\s*[·•]',                               # A · 业务名
        rf'>\s*{sid}\s*<',                                # >A< 文本节点
        rf'>\s*{sid}\s*[·•]',                             # >A · 业务名<
        rf'phone-label[^>]*>\s*{sid}\b',                  # IMAP phone-label
        rf'gd-num[^>]*>\s*{sid}\b',                       # PART 编号容器
        rf'id="scene-{sid}\b',                            # IMAP scene id
        rf'id="part-{sid.lower()}\b',                     # PART id
        rf'PART\s+{sid}\b',                               # PART A
    ]
    return any(re.search(p, text) for p in patterns)


def find_missing_ids(scene_ids: list[str], text: str) -> list[str]:
    """对照 scene_ids 列表，返回未在 text 中有效出现的编号清单。"""
    return [sid for sid in scene_ids if not id_covered_in_text(sid, text)]


# 带连字符的子场景编号：A-4 / D-1 / M-2 / F-0a（前后非字母数字，防吞 B-10 / x-1）
_REF_ID_RE = re.compile(r'(?<![A-Za-z0-9])([A-Z]-[0-9]+[a-z]?)(?![A-Za-z0-9-])')


def extract_referenced_ids(text: str) -> list[str]:
    """抽取产物里引用到的带连字符场景编号（A-4 / D-1 / M-2 / F-0a）。

    用于 partial delta 的 subset 校验：delta 引用的编号必须 ⊆ scene-list。
    只抽连字符形态（噪音低）；单字符父编号（A/B/M）噪音高不抽。
    """
    ids: list[str] = []
    seen: set[str] = set()
    for m in _REF_ID_RE.finditer(text):
        sid = m.group(1)
        if sid not in seen:
            seen.add(sid)
            ids.append(sid)
    return ids


def find_undefined_ids(referenced: list[str], scene_ids: list[str]) -> list[str]:
    """返回 referenced 中不在 scene_ids（scene-list 定义集）里的编号。

    抓 partial delta 引用了 scene-list 里不存在的场景编号。
    """
    defined = set(scene_ids)
    return [sid for sid in referenced if sid not in defined]


def scene_code_report(scene_ids: list[str], text: str) -> tuple[list[str], list[str]]:
    """delta IMAP 编号对照，返回 (引用越界编号, 未覆盖编号)。

    未覆盖属预期（delta 只覆盖本轮触及场景，warn 级）；引用越界是硬伤（FAIL 级）。
    """
    return find_undefined_ids(extract_referenced_ids(text), scene_ids), find_missing_ids(scene_ids, text)
