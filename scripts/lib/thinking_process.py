"""跨产物「描述当前态」铁律 - 设计动机层 PATTERN（评审心路 / 元注解）。

调用方：
- scripts/check_static_chapter.py（真相源静态章 lint）
- .claude/skills/prd/scripts/humanize/md_scan.py（PRD humanize，传入当前 H2 命中豁免）
- .claude/skills/interaction-map/scripts/check_imap.sh（IMAP 注解扫描，完全禁不传豁免）
- .claude/skills/prototype/scripts/check_proto.sh（prototype 注解扫描，完全禁不传豁免）

规则源：.claude/runbooks/human-voice-rules.md ③ 设计动机（思考过程）

设计哲学：业务规则配套「理由：xxx」「因为 X 所以」「避免 Y」**保留**（删了影响研发实施 / QA 写 case）；
评审心路 + 元注解 **禁**（删了不丢实施信息）。差异点在章节豁免。
"""
import re

# ── 评审心路词 v0（复用 check_static_chapter.py PROCESS_PATTERNS 已 prod 跑通）─
THINKING_VERBS = [
    re.compile(r'改名原因|审视后|权衡后|纠结|曾经|起初|最初'),
    re.compile(r'反思|此次评审|本次评审|讨论结果|经讨论|思考下来|斟酌'),
    re.compile(r'本轮(?!输入|输出|主题)'),
    re.compile(r'\bv\d+\.\d+\s+(?:从|改|新增|删除)'),
]


# ── 元注解（极保守 PATTERN，避免误伤）──────────────────────────────────────
# 「关键设计」三种形态：行首独立 / 括号注 / 加冒号
META_ANNOTATION_HEADER = [
    re.compile(r'^\s*(?:#{1,6}\s+)?关键设计(?:[:：\s]|$)', re.MULTILINE),
    re.compile(r'[（(]\s*关键设计\s*[）)]'),
    re.compile(r'精髓在于'),
    re.compile(r'核心思想'),
    re.compile(r'考虑到[^，。\n]{1,30}?所以'),
    re.compile(r'出于(?:风险|稳妥|保守|合规|体验|性能)考虑'),
    re.compile(r'之所以[^，。\n]{1,30}?是因为'),
    re.compile(r'我们(?:决定|选择|最终|最后|权衡)'),
]


# ── 章节豁免（仅 PRD / context 有保留场景）──────────────────────────────────
# PRD §4.x 业务规则 / 跨场景规则 / 归因规则；§1.4 核心变更；context §7 Decision Log
# 调用方传 exempt_h2（当前 H2 标题），命中关键词整段跳过
EXEMPT_H2_KW = (
    '业务规则',
    '跨场景规则',
    '归因规则',
    '核心变更',
    '设计决策',
    '方案决策',
    'Decision Log',
)


def _is_exempt_h2(h2_title):
    """判断 H2 标题是否触发豁免。"""
    if not h2_title:
        return False
    return any(kw in h2_title for kw in EXEMPT_H2_KW)


def scan_thinking(text, exempt_h2=None):
    """扫描文本，返回所有命中的 (category, match_str) 列表。

    参数：
    - text：要扫的文本（行级或段级）
    - exempt_h2：当前所在 H2 标题（如「## 4.1 跨场景规则」），命中 EXEMPT_H2_KW 整段豁免
                 IMAP / prototype 调用时传 None 完全扫

    返回：list[(category, match_str)]
        category ∈ {thinking_verb, meta_annotation}
    """
    if _is_exempt_h2(exempt_h2):
        return []
    hits = []
    for p in THINKING_VERBS:
        for m in p.finditer(text):
            hits.append(('thinking_verb', m.group(0)))
    for p in META_ANNOTATION_HEADER:
        for m in p.finditer(text):
            hits.append(('meta_annotation', m.group(0)))
    return hits
