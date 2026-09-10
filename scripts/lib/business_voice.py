"""跨产物「描述当前态」铁律 - 业务话语层 PATTERN（后端字段 / 函数 API / 章节号 / 技术黑名单）。

调用方：
- scripts/check_static_chapter.py（真相源静态章 lint）
- .claude/skills/prd/scripts/humanize/patterns.py（PRD humanize 接共享层，SNAKE_FIELD 等保留 PRD 特化）
- .claude/skills/interaction-map/scripts/check_imap.sh（IMAP 注解扫描）
- .claude/skills/prototype/scripts/check_proto.sh（prototype 注解扫描）

规则源：.claude/runbooks/human-voice-rules.md ② 业务话语（技术实现）
"""
import re

# ── 后端字段显式赋值（含 `=` `:` 边界）─────────────────────────────────────
# 命中：trade_perf_public=true / is_copy_trader=true / card_type:futures
# 不含边界的 snake_case（普通 ID `card_id`）在 PRD 有 H2 / 表头豁免，保留 PRD 特化
SNAKE_FIELD_EXPLICIT = re.compile(r'\b[a-z]+(?:_[a-z]+){1,4}\s*[=:]\s*\S+')


# ── HTML <code> 标签（IMAP / prototype 渲染层包代码）────────────────────────
# 命中：<code>getSubscriberCount(uid)</code>
# BS4 调用方用 find_all('code') 直接拿到节点；纯文本扫用此 regex
CODE_TAG_RE = re.compile(r'<code\b[^>]*>([^<]+)</code>', re.IGNORECASE)


# ── 跨产物章节号引用 ─────────────────────────────────────────────────────
# 命中：§5.1 / 第 4 章 / 6.2 TAB 显示规则 / baseline.md / SKILL.md / scene-list / CR 单号
# SECTION_ANCHOR_RE / CHAPTER_REF_RE（不含「节」，本层「节」由下方 SECTION_NUM_INLINE_RE
# 的 `6.2 节` 形态覆盖）收口到 anchor_patterns 单一真相源。
from .anchor_patterns import CHAPTER_REF_RE, SECTION_ANCHOR_RE

SECTION_NUM_INLINE_RE = re.compile(r'\b\d+\.\d+\s*(?:TAB|节|章|规则|显示规则)')
FILE_REF_RE = re.compile(r'(?:baseline\.md|SKILL\.md|scene-list(?:\.md)?)\b')
CR_REF_RE = re.compile(r'\bCR\s*[#-]?\s*\d+')


# ── 技术黑名单 v1（按 domain 拆到 scripts/lib/tech_jargon/ 词表）────────────
# 调用方传 domains 选词表（infra 始终在），或传 context_text 自动推断
from . import tech_jargon as _tj

# 兜底默认 patterns（不传 domains 时用 infra + livestream）
_DEFAULT_PATTERNS = _tj.load_jargon(domains=['infra', 'livestream'])


def scan_business_voice(text, is_html=False, tech_patterns=None):
    """扫描文本，返回所有命中的 (category, match_str) 列表。

    参数：
    - text：要扫的文本（行级或段级，调用方自行处理 fenced code / 注释豁免）
    - is_html：是否为 HTML 渲染层文本（True 时跑 <code> 标签扫描；md backtick 块由调用方先剥离）
    - tech_patterns：技术黑名单 patterns（None 时用默认 infra + livestream）

    返回：list[(category, match_str)]
        category ∈ {snake_field, code_tag, section_anchor, chapter_ref, section_num,
                    file_ref, cr_ref, tech_jargon}
    """
    hits = []
    for m in SNAKE_FIELD_EXPLICIT.finditer(text):
        hits.append(('snake_field', m.group(0)))
    if is_html:
        for m in CODE_TAG_RE.finditer(text):
            hits.append(('code_tag', m.group(0)))
    for m in SECTION_ANCHOR_RE.finditer(text):
        hits.append(('section_anchor', m.group(0)))
    for m in CHAPTER_REF_RE.finditer(text):
        hits.append(('chapter_ref', m.group(0)))
    for m in SECTION_NUM_INLINE_RE.finditer(text):
        hits.append(('section_num', m.group(0)))
    for m in FILE_REF_RE.finditer(text):
        hits.append(('file_ref', m.group(0)))
    for m in CR_REF_RE.finditer(text):
        hits.append(('cr_ref', m.group(0)))
    patterns = tech_patterns if tech_patterns is not None else _DEFAULT_PATTERNS
    for p in patterns:
        for m in p.finditer(text):
            hits.append(('tech_jargon', m.group(0)))
    return hits
