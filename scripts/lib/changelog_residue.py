"""跨产物「描述当前态」铁律 - 时间态层 PATTERN（修订痕迹 / 决策号引用 / from-to 迁移）。

调用方：
- scripts/check_static_chapter.py（真相源静态章 lint）
- .claude/skills/prd/scripts/humanize/patterns.py（PRD humanize 接共享层）
- .claude/skills/interaction-map/scripts/check_imap.sh（IMAP 注解扫描）
- .claude/skills/prototype/scripts/check_proto.sh（prototype 注解扫描）

规则源：.claude/runbooks/human-voice-rules.md ① 时间态（流水账）
"""
import re

# ── 修订痕迹（变更 / 新增 / 砍掉 / 日期标注）─────────────────────────────────
# 命中：(YYYY-MM-DD ...) / (from vN) / (变更|新增|砍掉) / 反转说明：/ 砍掉：
REVISION_PATTERNS = [
    re.compile(r'[（(]\s*\d{4}-\d{2}-\d{2}[^）)]*[）)]'),
    re.compile(r'[（(]\s*from\s*v\d+[^）)]*[）)]'),
    re.compile(r'[（(]\s*(?:变更|新增|砍掉|删除|已删除|废弃|已废弃|'
               r'精简|简化|简化版|取消|合并|拆分|延后|前置)'
               r'(?:[：:、，,·\s][^）)]*)?[）)]'),
    re.compile(r'反转说明：'),
    re.compile(r'砍掉：'),
    re.compile(r'\d{4}-\d{2}-\d{2}\s*决策(?:\s*#\d+)?'),
    re.compile(r'\b\d{2}-\d{2}\s*(?:删|改|新|加|减|拆|合)\b'),
]


# ── 版本号 + 动作词流水账（V x.y · 变更 / V x.y 系列）────────────────────────
# 文件名引用 (V3.0-Phase2-连麦.docx) 由 lookahead 排除
VERSION_TAG_PATTERNS = [
    re.compile(r'[（(]\s*V\d+(?:\.\d+)*\s*[:：、，,\s]+\s*'
               r'(?:变更|砍掉|精简|新增|简化|废弃|删除|已删除|取消|合并|拆分|改|延后|前置|降级)'
               r'[^）)]*[）)]'),
    re.compile(r'\bV\d+(?:\.\d+)*\s*(?:变更|新增|砍掉|删除|已删除|精简|简化|移除|废弃|取消)[\s的]*'),
    re.compile(r'[（(][^）)]*?\bV\d+(?:\.\d+)*\s*[：:、，,·\s]\s*'
               r'(?:变更|新增|砍掉|删除|已删除|精简|简化|移除|废弃|取消)'
               r'[^）)]*[）)]'),
    re.compile(r'[（(][^）)]*V\d+(?:\.\d+)*[^）)]*?'
               r'(?:PM|确认|review|审核|拍板|讨论|\d{4}-\d{2}-\d{2})'
               r'[^）)]*[）)]'),
    re.compile(r'[（(]\s*V\d+(?:\.\d+)*'
               r'(?![^）)]*\.(?:docx|html|md|pdf|js|py)\b)'
               r'(?:\s*[：:、，,\s][^）)]{0,60})?'
               r'[）)]'),
]


# ── 决策号引用 ──────────────────────────────────────────────────────────────
# 命中：决策 #N / 决策 N · vN.M / 反转决策 N / 覆盖决策 N
DECISION_REF_PATTERNS = [
    re.compile(r'决策\s*#\s*\d+'),
    re.compile(r'决策\s*\d+\s*[·•・]\s*v\d+(?:\.\d+)*'),
    re.compile(r'反转决策\s*#?\s*\d+'),
    re.compile(r'覆盖决策\s*#?\s*\d+'),
]


# ── from-to 迁移叙事 ───────────────────────────────────────────────────────
# "由 X 替代" / "改为 Y" / "不再 Z" 这种流水叙事归 PRD §1.3 变更范围 / context §9 Changelog
MIGRATION_PATTERNS = [
    re.compile(r'由[^，。\n]{1,30}?替代'),
    re.compile(r'改为[^，。\n]{1,30}'),
    re.compile(r'不再(?:使用|有|支持|硬性|必配|提供|存在|展示|出现|是)'),
    re.compile(r'沿用(?:旧版|旧逻辑|V\d+(?:\.\d+)*|原(?:方案|逻辑|版本))'),
    re.compile(r'从\s*[^，。\n]{1,30}?迁移到\s*\S+'),
    re.compile(r'拆出(?:到|为)\s*\S+'),
    re.compile(r'合并到\s*\S+'),
    re.compile(r'废弃保留兼容'),
    re.compile(r'保留兼容(?:层|方案|逻辑)?'),
]


# ── 已删除清单 H3/H4 整段标题（含「已删除字段 / 已废弃 / 已下线 / 迁移说明」）─
ZOMBIE_HEADING_RE = re.compile(
    r'(已删除字段|已删除|已废弃|废弃|已移除|已下线|已合并|迁移说明)'
)


# ── 既有 PRD ZOMBIE_HEADING 兼容（patterns.py ZOMBIE_HEADING 同源）──────────
LEGACY_ZOMBIE_HEADING_RE = re.compile(r'(砍掉|取消)')


def scan_residue(text, is_heading=False):
    """扫描单行文本，返回所有命中的 (category, match_str) 列表。

    参数：
    - text：单行文本（行级扫描，调用方自行按行拆 + 跳过 fenced code / HTML 注释）
    - is_heading：是否为 H1-H6 标题行，True 时额外跑 ZOMBIE 系列

    返回：list[(category, match_str)]
        category ∈ {revision, version_tag, decision_ref, migration, zombie_heading}
    """
    hits = []
    for p in REVISION_PATTERNS:
        for m in p.finditer(text):
            hits.append(('revision', m.group(0)))
    for p in VERSION_TAG_PATTERNS:
        for m in p.finditer(text):
            hits.append(('version_tag', m.group(0)))
    for p in DECISION_REF_PATTERNS:
        for m in p.finditer(text):
            hits.append(('decision_ref', m.group(0)))
    for p in MIGRATION_PATTERNS:
        for m in p.finditer(text):
            hits.append(('migration', m.group(0)))
    if is_heading:
        for m in ZOMBIE_HEADING_RE.finditer(text):
            hits.append(('zombie_heading', m.group(0)))
        for m in LEGACY_ZOMBIE_HEADING_RE.finditer(text):
            hits.append(('zombie_heading', m.group(0)))
    return hits
