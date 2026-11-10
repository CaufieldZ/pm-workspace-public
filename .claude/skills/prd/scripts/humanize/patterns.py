"""regex / 常量定义（被 scan / fix / scene_codes 共用）。

与共性层关系（2 层架构）：
- 共性真相源：scripts/lib/banned_terms.py + scripts/lib/{changelog_residue, business_voice, thinking_process, ui_visual}.py
  覆盖跨 PRD / IMAP / prototype / context 的通用禁词与锚点。
- 本文件：PRD 自检维度清单（prd_fail_keys）+ 挤话计数原语 + docx 时代的修缮常量。
人读说明：scripts/lib/banned-terms-doc.md。
"""
import re

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


# ── 挤话治理 SSOT（章节豁免名单 + 计数原语）────────────────────────────────────
# 消费方：scripts/check_bullet_density.py（非 PRD 产物的挤话门；PRD 不走挤话门）。
# is_exempt_chapter 只服务「长句可以长」这一维：决策 / 变更 / 埋点章的论证句本就长。
EXEMPT_CHAPTER_KW = (
    "决策记录", "WHY", "Decision Log", "决策段", "决策溯源",
    "核心变更", "反向合并", "变更记录", "版本历史", "迭代记录",
    "埋点",
)


def is_exempt_chapter(heading_text: str) -> bool:
    """标题命中豁免名单 → 该章免「长句」判定（论证句可以长）。仅此一维豁免。"""
    return any(kw in heading_text for kw in EXEMPT_CHAPTER_KW)


def count_semicolons(s: str) -> int:
    """全角；+ 半角; 计数（挤话判定原语）。"""
    return s.count("；") + s.count(";")


def count_periods(s: str) -> int:
    """中文句号。计数（挤话判定原语）。"""
    return s.count("。")


# ── 句段切分原语（check_bullet_density 用）────────────────────────────────────
# 量长度前先剥 markdown 噪音（链接 / 图片 / 行内代码），避免 URL 撑长度。
SENTENCE_SPLIT_RE = re.compile(r'[。！？；]')
# 不含 CJK 的句段再按拉丁 / 西里尔句末标点切。只认「标点 + 空白」，
# 避开 2.4 / 1,234.56 这类无空格写法被切碎。
CJK_CHAR_RE = re.compile(r'[㐀-䶿一-鿿豈-﫿]')
LATIN_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')
MD_NOISE_RE = re.compile(r'!?\[[^\]]*\]\([^)]*\)|`[^`]*`')
URL_RE = re.compile(r'https?://\S+')                                  # 裸网址
QUOTE_PAIR_RE = re.compile(r'[「『][^」』]*[」』]|“[^”]*”|"[^"]*"')     # 成对引号内容
LEADING_MARKER_RE = re.compile(r'^\s*(?:[-*+]|\d+\.)\s+')             # 行首列表符号


def split_sentences(s: str) -> list[str]:
    """切句段：先按中文句末标点，纯拉丁 / 西里尔句段再按 . ! ? 切。

    只按中文标点切的话，整段英文会被当成一个「句子」，长句判定实际量的是
    段落长度——英文 / 俄文产物每段必然超阈值。
    """
    out: list[str] = []
    for seg in SENTENCE_SPLIT_RE.split(s):
        if not seg.strip():
            continue
        if CJK_CHAR_RE.search(seg):
            out.append(seg)
        else:
            out.extend(p for p in LATIN_SENTENCE_SPLIT_RE.split(seg) if p.strip())
    return out


def sentence_lengths(s: str, quote_mode: str = "mask") -> list[int]:
    """按句末标点切句段，返回每段字数（挤话判定原语）。

    量长度前依次剥：行首列表符号 → 链接 / 图片 / 行内代码 → 裸网址 → 引号内原文 →
    强调符。只剥**行首**的列表符号——行中的 `1.` 是正文，剥了会把长度算短。

    quote_mode 决定引号内原文怎么算（两种判据要的语义相反，不能共用一种）：
      mask — 替成 1 个字符，长度不算进本文。长句判定用：引一段长公告不算自己写了长句。
      fill — 替成等长填充，长度照算但不许内部标点切句。碎句判定用：若按 mask 算，
             引一句长文案会把该句压成很短，把中位数拖低、把正常散文误判成碎句。
    """
    s = LEADING_MARKER_RE.sub('', s)
    s = MD_NOISE_RE.sub('', s)
    s = URL_RE.sub('', s)
    if quote_mode == "fill":
        s = QUOTE_PAIR_RE.sub(lambda m: "甲" * len(m.group(0)), s)
    else:
        s = QUOTE_PAIR_RE.sub('"', s)
    s = s.replace('*', '')
    return [len(seg.strip()) for seg in split_sentences(s)]


def median_sentence_len(s: str, quote_mode: str = "mask") -> float:
    """句长中位数（无句段时 0）。偶数个取中间两个的均值。

    用下中位数会把「几句短 + 一句中长」的段落误判成碎句（中位落到短的那侧）。
    """
    lens = sorted(sentence_lengths(s, quote_mode))
    if not lens:
        return 0.0
    n = len(lens)
    if n % 2:
        return float(lens[n // 2])
    return (lens[n // 2 - 1] + lens[n // 2]) / 2

# ── 旧版 cell shading（FAIL）──────────────────────────────────────────────
# V2.7-era PRD 用的蓝底 / 浅蓝表头，新规范：表头 #141413 + 数据行 #F8FAFB / 无填色
LEGACY_BLUE_FILLS = {'2D81FF', 'D5E8F0'}

# ── 视觉死字检测：白字（color=FFFFFF）+ cell 非深色填色 → 字看不见（FAIL）──
DARK_FILLS_KEEP_WHITE = {'141413', '1F1F1E', '0B0E11', '000000'}

# ── Dirty cell：单段超长 + 多 list 标记 = set_cell_text 误塞 \n 串（FAIL）──
# PRD SKILL.md R1 警告：set_cell_text 塞多行 \n 字符串会渲染成单段无层次纯文本
# 应改用 set_cell_blocks 结构化（title + lines）。这是上游 gen 脚本 bug，下游靠 humanize 擦屁股
# 判定：cell 内任一段 > 80 字 + 含 ≥ 2 个 emoji 或 ≥ 2 个 list 标记符
EMOJI_RE = re.compile(r'[\U0001F300-\U0001FAFF\U00002600-\U000027BF]')
DIRTY_CELL_MIN_CHARS = 80


# ── PM 内部场景编号清理 ─────────────────────────────────────────────────
# 圈数字 ①②③ 不再机械归一（`①→1.` 在行内并列场景反而难读）
# 改为 save_prd 用 humanize.assert_no_circle_nums 硬阻断


# ── 通用 PRD 抛光规则常量（PRD_* 系列，被 humanize_prd_voice 调用）─────────

PRD_CHANGELOG_PATTERNS = [
    (re.compile(r'\s*[（(]\s*from\s*v\d+[^）)]*[）)]'), ''),
    (re.compile(r'\s*[（(]\s*\d{4}-\d{2}-\d{2}[^）)]*[）)]'), ''),
    (re.compile(r'\s*\d{4}-\d{2}-\d{2}\s*决策(?:\s*#\d+)?'), ''),
    # 广义「（动作词 + 可选分隔符 + 可选内容）」流水
    # 分隔符集合：全/半角冒号、顿号、逗号、间隔号、空格
    (re.compile(
        r'\s*[（(]\s*(?:变更|新增|砍掉|删除|已删除|废弃|已废弃|'
        r'精简|简化|简化版|取消|合并|拆分|延后|前置)'
        r'(?:[：:、，,·\s][^）)]*)?\s*[）)]'
    ), ''),
    (re.compile(r'反转说明：.*?(?=$|\n|\|)'), ''),
    (re.compile(r'\s*[（(]\s*中文别名匹配[^）)]*?砍掉\s*[）)]'), ''),
    # 版本号开头的流水账：「(V2.6: 精简)」「(V2.7 砍掉, 改静默路由)」「(V2.4: 极简条取消)」
    # 仅在版本号后跟变更动作词时删除（避免误伤文件名引用「(V3.0-Phase2-连麦.docx)」）
    (re.compile(r'\s*[（(]\s*V\d+(?:\.\d+)*\s*[:：、，,\s]+\s*'
                r'(?:变更|砍掉|精简|新增|简化|废弃|删除|已删除|取消|合并|拆分|改|延后|前置|降级)'
                r'[^）)]*[）)]'), ''),
    # 括号内 V 版本号 + PM 批注 / 评审痕迹（含 PM 名 / 确认 / review / 日期）
    # 例：「(V2.7 · 合约 PM 2026-04-22 最新确认)」「(V3.0 · 张三 review 后拍板)」
    (re.compile(r'\s*[（(][^）)]*V\d+(?:\.\d+)*[^）)]*?'
                r'(?:PM|确认|review|审核|拍板|讨论|\d{4}-\d{2}-\d{2})'
                r'[^）)]*[）)]'), ''),
    # 段首 / 句中裸 V x.y + 动作词（不在括号里）：「V2.6 变更移除 xxx」「V2.7 新增 3 个 Scene」
    # 删整个 V 版本号 + 动作词短语，保留之后的内容描述
    (re.compile(r'\bV\d+(?:\.\d+)*\s*(?:变更|新增|砍掉|删除|已删除|精简|简化|移除|废弃|取消)[\s的]*'), ''),
    # 括号内任意位置含「V x.y + 动作词」：「(H5 主播中心 · V2.5 变更)」
    # 不命中 (V3+) / (V3.0-Phase2-连麦.docx) 等无动作词的合法引用
    (re.compile(r'\s*[（(][^）)]*?\bV\d+(?:\.\d+)*\s*[：:、，,·\s]\s*'
                r'(?:变更|新增|砍掉|删除|已删除|精简|简化|移除|废弃|取消)'
                r'[^）)]*[）)]'), ''),
    # 孤立括号 V 版本引用「（V2.5）」「（V2.4)」无内容标注 = 流水
    # 注意：(V3+) 因 V 后是 + 非空白非闭合不匹配；(V3.0-Phase2-连麦.docx) 由 lookahead 排除
    (re.compile(r'\s*[（(]\s*V\d+(?:\.\d+)*'
                r'(?![^）)]*\.(?:docx|html|md|pdf|js|py)\b)'
                r'(?:\s*[：:、，,\s][^）)]{0,60})?'
                r'\s*[）)]'), ''),
]

PRD_JARGON_REPLACEMENTS = [
    # 卡片类型枚举 → 中文（项目无关，业务通用语义）
    # 项目特定的字段映射由调用方传 extra_jargon 注入
    (re.compile(r'card_type[：:]\s*'), '卡片类型：'),
    (re.compile(r'\bis_same_symbol\b'), '是否同一币对'),
    (re.compile(r'\brelated_card_id\b'), '卡片归因 ID'),
    (re.compile(r'\bcard_id\b'), '卡片 ID'),
    (re.compile(r'\bproject_id\b'), '项目 ID'),
    (re.compile(r'\bpost_id\b'), '帖子 ID'),
    (re.compile(r'\border_id\b'), '订单号'),
    (re.compile(r'\bplaceholder\b'), '占位'),
    (re.compile(r'\blabel\b'), '标签'),
    (re.compile(r'\btoggle\b'), '切换'),
    (re.compile(r'\bconfirm\b'), '确认'),
    # 残留 backtick
    (re.compile(r'`([^`]+)`'), r'\1'),
]

PRD_UI_STRIP_PATTERNS = [
    # px / pt 数值
    (re.compile(r'\s*[，,]?\s*\b\d+(?:\.\d+)?\s*px\b'), ''),
    (re.compile(r'\s*[，,]?\s*\b\d+\s*pt\b'), ''),
    # 颜色 hex
    (re.compile(r'\s*[，,]?\s*[#＃][0-9A-Fa-f]{3,8}\b'), ''),
    # 动画毫秒
    (re.compile(r'\s*[，,]?\s*\b\d+\s*ms\b'), ''),
    # opacity
    (re.compile(r'\s*[，,]?\s*opacity[\s:.]*\d+(?:\.\d+)?'), ''),
    # 字体规格子句
    (re.compile(r'\s*字体：[^|，；。、\n]+[|，；。、]?'), ''),
    (re.compile(r'\s*字号：[^|，；。、\n]+[|，；。、]?'), ''),
    (re.compile(r'\s*\bmono\b'), ''),
    (re.compile(r'\s*\b\d+\s*粗\b'), ''),
    (re.compile(r'\s*\bgray-text\b'), ''),
    # "蓝底白字，固宽 / 高 / 圆角，固定底部" → "蓝底白字，固定底部"
    (re.compile(r'，?\s*固宽\s*[,，/／]\s*高\s*[,，/／]\s*圆角\s*'), ''),
]

PRD_TRAILING_JUNK_PATTERNS = [
    (re.compile(r'（\s*[/／]\s*[^）]*）'), ''),
    (re.compile(r'\s*[/／]\s*不可点\s*'), '不可点'),
    (re.compile(r'，\s*$'), ''),
    (re.compile(r'\|\s*\|'), '|'),
    (re.compile(r'tiny\s+label\s*\+\s*输入值\s*堆叠'), '价格输入值'),
    (re.compile(r'\btiny\s+label\b'), ''),
    (re.compile(r'：\s*[，,]\s*'), '：'),
    (re.compile(r'\s*[，,]\s*([）)\|])'), r'\1'),
    (re.compile(r'^\s*[，。、]'), ''),
    (re.compile(r'([一-鿿])\s+([一-鿿])'), r'\1\2'),
    (re.compile(r'([一-鿿])\+\s*'), r'\1 + '),
    (re.compile(r'：\s+'), '：'),
    (re.compile(r'（\s*）|\(\s*\)'), ''),
    (re.compile(r' {2,}'), ' '),
    (re.compile(r'\s+([，。；：、])'), r'\1'),
]

# 整段删除条件：以 "N." 开头且包含以下关键词之一
PRD_KILL_BULLET_KEYWORDS = ('字体：', '字号：', '砍掉：', '反转说明：')
EMPTY_BULLET_RE = re.compile(r'^\d+\.\s*$')
NUMBERED_LINE_RE = re.compile(r'^(\d+)\.\s*(.+)$')


# ── PRD 结构性扫描常量（scan_prd_structural 共享）──────────────────────────
# 这些与 check_prd.sh 第 2 段 python heredoc 同源,统一在此定义避免词集分裂

# 占位符:gen 阶段的 TBD 残留,推 wiki 前必须收敛
PLACEHOLDER_TOKENS = ('待填充', 'TBD', 'TODO', 'FIXME', '← 此处粘贴')

# 技术骨架章关键词:这些 H1 章节免「用户故事引言」(chapter_story)要求
# 只有功能章(第 3/4/5 章 各 View)才必须有用户故事引言
TECH_CHAPTER_KW = (
    '背景', '目标', '业务规则', '非功能', '技术架构', '埋点', '监控',
    '排期', '里程碑', '目录', '附录', '封面', '场景地图',
)

# Scene 右列扁平化阈值
SCENE_FLAT_SINGLE_PARA_CHARS = 100   # 单段 > 100 字符判扁平
SCENE_FLAT_MIN_PARAS = 4              # ≥ 4 段必须有 numbered list 标记

# 截图 DPI 下限:Playwright 默认 72 太虚,需 fix_dpi 抬到 144
LOW_DPI_THRESHOLD = 130

# 段落数 / 表格数异常下限计算:基于 scene_count
def docx_min_paragraphs(scene_count: int) -> int:
    return max(20, scene_count * 3)

def docx_min_tables(scene_count: int) -> int:
    return scene_count

# 老字体清单(normalize_fonts 兜底)
LEGACY_FONTS = {
    'Arial', 'Calibri', 'Times New Roman', 'Times', 'Helvetica',
    'Microsoft YaHei', '微软雅黑', 'SimSun', '宋体', 'SimHei', '黑体',
}


# ── 1.3 变更范围流水账词集（check_prd.sh + gate_check_quality 共享）──────────
# 三档语义不同，保留分立：
# - LANE：1.3 第 0 列允许出现（lane 名本身可能是「早决策/晚决策」），用于 gate 排除/启发式
# - BODY：全文禁止的迭代痕迹（决策日期 / 改名记录），范围最广
# - ITERATION_WORDS：1.3 节内禁止的口语化迭代词（与 BODY 互补，PM 叙述口吻）
PRD_CHANGELOG_LANE_HISTORY = re.compile(
    r'(早决策|晚决策|中间稿|PRD 草稿|v\d+\.\d+|\d+月\d+日)'
)
PRD_CHANGELOG_BODY_HISTORY = re.compile(
    r'(\d{1,2}-\d{1,2}\s*(早|晚)?决策|早决策|晚决策|本期决策'
    r'|从「[^」]+」改名|形态从「[^」]+」改为|页面标题从「[^」]+」改名)'
)
PRD_CHANGELOG_ITERATION_WORDS = ['覆盖条目', '反转回', '中间稿', '上一稿', '前一版']


# ── PRD 自检维度清单（唯一真源）──────────────────────────────────────────────
# check_prd_md.sh 与 prd-content-gate 都从这里取维度。只收「会把文档弄坏」的硬错：
# 写法（句长 / 分号 / 用词）交给作者，不在这里管。
# 每项 = (md_scan 返回键, 人读标签)。

_PRD_FAIL_BASE: list[tuple[str, str]] = [
    ("diagram_code_hits", "mermaid / PlantUML 代码块（Confluence 不渲染，改表格或走 flowchart skill 出图）"),
    ("horizontal_rule_hits", "水平线 ---（Confluence 渲染难看，章节靠标题分隔；表格 |---| 不算）"),
    ("broken_image_alt", "图片 alt 为空"),
    ("tracking_header_hits", "埋点表表头不是固定 10 列（推送合并单元格与 xlsx 导出按表头认表）"),
]

_PRD_FAIL_PLACEHOLDERS = ("placeholders", "占位符残留（TBD/TODO/{{ 待填）")

# baseline 历史 living 文档存量豁免下面两维。
_PRD_FAIL_BLOCKQUOTE = ("blockquote_hits", "引用块 >（Confluence 渲染难看，改普通段落）")
_PRD_FAIL_SERVER_PLATFORM = (
    "server_platform_tracking",
    "埋点表应埋点平台含服务端 / 后台（只做 APP / Web 端埋点）",
)

_PRD_WARN_PLACEHOLDERS = ("placeholders", "占位符残留（骨架阶段允许，交付前清掉）")


def prd_fail_keys(
    skeleton: bool = False,
    profile: str = "delta",
) -> list[tuple[str, str]]:
    """按运行条件返回 FAIL 维度清单。

    Args:
        skeleton: 骨架阶段模式（占位符降 WARN）
        profile: "baseline" 走 baseline 豁免集，其余按 delta
    """
    keys = list(_PRD_FAIL_BASE)
    if not skeleton:
        keys.append(_PRD_FAIL_PLACEHOLDERS)
    if profile != "baseline":
        keys.append(_PRD_FAIL_BLOCKQUOTE)
        keys.append(_PRD_FAIL_SERVER_PLATFORM)
    return keys


def prd_warn_keys(skeleton: bool = False) -> list[tuple[str, str]]:
    """按运行条件返回 WARN 维度清单（只剩骨架阶段的占位符提醒）。"""
    return [_PRD_WARN_PLACEHOLDERS] if skeleton else []
