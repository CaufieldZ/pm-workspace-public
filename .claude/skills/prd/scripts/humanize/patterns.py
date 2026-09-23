"""regex / 常量定义（被 scan / fix / scene_codes 共用）。

与共性层关系（2 层架构）：
- 共性真相源：scripts/lib/banned_terms.py + scripts/lib/{changelog_residue, business_voice, thinking_process, ui_visual}.py
  覆盖跨 PRD / IMAP / prototype / context 的通用禁词与锚点。
- 本文件：PRD 形态特化版。多数正则故意更窄（例：DECISION_NUM_RE 无边界判定，
  CIRCLE_NUM_RE 用 Unicode 范围而非枚举，CSS_IMPL 是合并版）—— 故 PRD 不简单 alias 共性版本。
仅 SECTION_ANCHOR_RE 与共性层完全相同，从 banned_terms 引入；其他保留 PRD 特化实现。
人读说明：scripts/lib/banned-terms-doc.md。
"""
import re
import sys
from pathlib import Path

# 复用共性 SECTION_ANCHOR_RE（PRD / banned_terms 完全等价）
_REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))
from lib.banned_terms import SECTION_ANCHOR_RE  # noqa: E402,F401

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


# ── 流水账 / 版本痕迹（FAIL 阻断） ──────────────────────────────────────────
DATE_TAG = re.compile(
    r'[（(]\s*\d{4}-\d{2}-\d{2}[^）)]*[）)]'   # (2026-04-22 ...)
    r'|[（(]\s*from\s*v\d+[^）)]*[）)]'         # (from v47)
    r'|[（(]\s*(?:变更|新增)[^）)]*[）)]'        # (变更) (新增)
    # 行内版本标签（v2.1 新增 / v3 更新）：版本号必须紧跟变更词——放开会让括号列表
    # （「（1.1 现状 / 1.4 核心变更）」）与长括号（「（v1.0.0，…覆盖…）」）误命中。
    r'|[（(]\s*v\d+(?:\.\d+)*\s{0,2}(?:新增|反转|更新|变更|覆盖|删除|废止)'
    r'|反转说明：'
    r'|砍掉：'
)

# ── 代码字段 snake_case（WARN） ─────────────────────────────────────────────
SNAKE_FIELD = re.compile(r'\b[a-z]+(?:_[a-z]+){1,4}\b')

# ── 挤话治理 SSOT（章节豁免名单 + 计数原语）────────────────────────────────────
# 单一真源：check_bullet_density.py（hook block）与 md_scan.py（check_prd WARN）两个
# 独立检测器共用同一份，避免各持副本漂移（曾漂成 10 类 vs 3 类，「核心变更」章长句分叉）。
# 决策 / 变更 / 埋点章也配写好看——句号≥3 焊一行、分号串列举，哪章都是挤话该拆，
# 拆成「标签：」+ 子 bullet 反而更好读。故 block 层一视同仁、不做章节豁免。
# is_exempt_chapter 只服务 WARN 层「长句可以长」这唯一口子：「方案。理由。阻塞。」论证叙事
# 一句本就长，硬砍割裂推理，且只是 WARN。除此之外这些章跟正文同规矩。
EXEMPT_CHAPTER_KW = (
    "决策记录", "WHY", "Decision Log", "决策段", "决策溯源",
    "核心变更", "反向合并", "变更记录", "版本历史", "迭代记录",
    "埋点",
)


def is_exempt_chapter(heading_text: str) -> bool:
    """标题命中豁免名单 → 该章免「长句 run-on」WARN（论证句可以长）。仅此一维豁免，
    句号密度 / 分号串 block 不吃这个（决策章 3 句焊一行照样拦）。"""
    return any(kw in heading_text for kw in EXEMPT_CHAPTER_KW)


def count_semicolons(s: str) -> int:
    """全角；+ 半角; 计数（挤话判定原语，两检测器共用）。"""
    return s.count("；") + s.count(";")


def count_periods(s: str) -> int:
    """中文句号。计数（挤话判定原语，两检测器共用）。"""
    return s.count("。")


# ── 分号滥用（WARN） ────────────────────────────────────────────────────────
# 单行 ≥ 2 个分号（全角；/ 半角;）= 3+ 子句并列堆成一段，应拆成 bullet 或 1.2.3. 编号
# 让描述结构化。表格行豁免（cell 内 `；` 是 md_to_confluence 切 bullet 的约定分隔符）。
SEMICOLON_RE = re.compile(r'[；;]')
SEMICOLON_ABUSE_THRESHOLD = 2

# ── 长句 run-on（WARN） ──────────────────────────────────────────────────────
# 句段（终止标点 。！？； 之间）≥ 100 字 = 一口气读不完，应拆句或转 bullet / 编号。
# 与分号校验互补：分号管「；」串，长句管「，」串 + 句子过密。表格行豁免。
# 量长度前先剥 markdown 噪音（链接 / 图片 / 行内代码），避免 URL 撑长度。
LONG_SENTENCE_THRESHOLD = 100  # 阈值登记: thresholds.yaml §E prd_checks.long_sentence_chars
SENTENCE_SPLIT_RE = re.compile(r'[。！？；]')
MD_NOISE_RE = re.compile(r'!?\[[^\]]*\]\([^)]*\)|`[^`]*`')
URL_RE = re.compile(r'https?://\S+')                                  # 裸网址
QUOTE_PAIR_RE = re.compile(r'[「『][^」』]*[」』]|“[^”]*”|"[^"]*"')     # 成对引号内容
LEADING_MARKER_RE = re.compile(r'^\s*(?:[-*+]|\d+\.)\s+')             # 行首列表符号


def sentence_lengths(s: str, quote_mode: str = "mask") -> list[int]:
    """按 。！？； 切句段，返回每段字数（挤话判定原语，两检测器共用）。

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
    return [len(seg.strip()) for seg in SENTENCE_SPLIT_RE.split(s) if seg.strip()]


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

# ── bullet 串句（WARN · 一个 bullet 只扛一个原子断言） ────────────────────────
# bullet 行内出现「句号 + 后续实质内容」= 句号没落行尾 = 把多条并列断言焊成一行
# （`打点口径 = X。B 点 = Y。展示位置 = Z` 应拆成各自一条 bullet）。只抓全角 。！？，
# 半角 . 放过（小数 / 版本号 / 编号）。引号「」『』“”""内的 。！？ 不算句末（md_scan 检测时剥引号内内容）。
# 父 bullet 以「：」结尾领起子 bullet（「总根数 50 根。窗口规则分三种情况：」）合法，md_scan 按行尾冒号整体豁免。
# 表格行豁免。与分号 / 长句校验互补：那两条管「单行太挤」，这条管「并列项该拆没拆」。
BULLET_LINE_RE = re.compile(r'^\s*(?:[-*+]|\d+\.)\s+')
_SENTENCE_TAIL = '）)】〕」』“”‘’"\'，、；：。！？'
PERIOD_RUNON_RE = re.compile(r'[。！？]\s*[^\s' + re.escape(_SENTENCE_TAIL) + r']')
# bullet 串句无章节豁免：决策 / 变更 / 埋点章 3 句焊一行照样该拆标签 bullet（与 block 一致）。
# 章节豁免只给「长句 run-on」一维（is_exempt_chapter，论证句可以长）。
# 叙事 / 论证标签引子豁免：以标签领起 + 句号分段是「论点→论据」或「现状→本轮」的合法节奏，
# 不是并列项焊一行——delta §1/§2 叙事对（现状 / 本轮）与决策段（取舍 / 理由 / 影响面）同理。
# 覆盖加粗（**取舍**：）与裸标签（取舍：）两形态；标签后可带「/ 另一标签」「（批注）」。
# 只认标签开头 = 叙事 / 论证引子，不泛豁免（scene 卡 显示逻辑：A。B 不在名单，照报）。
BULLET_RUNON_NARRATIVE_LABEL_RE = re.compile(
    r'^\s*[-*+]\s*(?:\*\*)?'
    r'(现状问题|现状|本轮不做|本轮|背景|痛点|取舍|理由|待拍|承接关系|影响面|方案|阻塞)')
# 合法句号上限：论点→论据 / 现状→本轮 双段句号 ≤2；≥3 说明标签下焊多件独立事，仍算挤话该拆
# ——与 check_bullet_density.py period_limit(3) block 阈值对齐，两检测器不分叉。
NARRATIVE_LABEL_MAX_PERIODS = 2

# ── 场景正文串句（FAIL · 只作用于 §2.x 需求正文的 现状 / 本轮 标签 bullet）──────
# 与 bullet_runon 的分工：bullet_runon 是全文 WARN + 叙事标签放行，管明显并列焊行；
# 本维是 §2.x 需求正文的 FAIL——场景正文的现状 / 本轮描述该结构化（一 bullet 一原子事实，
# 多阶段用 → 串链），叙事标签在这里不构成豁免。scope 双卡：① h1 属第 2 章（_is_in_chapter_2）
# ② 标签属场景叙事集（不含 取舍 / 理由 / 背景 等决策标签）。§6 决策记录 h1='6.' 天然够不着，
# 决策论证句照旧走 bullet_runon 的叙事豁免，零误伤。
SCENE_PROSE_LABEL_RE = re.compile(
    r'^\s*[-*+]\s*(?:\*\*)?(现状问题|现状|本轮不做|本轮)')

# ── 条件分支散文规则（WARN · 可断言形式） ──────────────────────────────────────
# 全局业务规则章里非表格行出现 ≥ 2 个条件分支标记 = 多分支挤在一句散文里，
# 应改「给定 | 当 | 则」可断言表（见 prd-scene-templates §4.5），让条件→结果唯一可断言、
# 分支可穷举（治下游歧义 / 遗漏）。表格行 / 标题豁免。
# 只数「分支起始」标记，不数 consequent 连接词「则」（「若 X 则 Y」是单分支，数 则 会误伤每条
# 简单 if-then）。也排除裸「当」（当前 / 相当 噪音）。≥ 2 个起始标记 = 真有多分支挤一句。
BRANCH_MARKER_RE = re.compile(r'若|如果|一旦|否则|反之|超过|低于|达到|不足')
BRANCH_MARKER_THRESHOLD = 2
# 仅扫「全局业务规则 / 全局规则」契约章（baseline §4 / delta §5 同覆盖），别处不查（控误报）。
ASSERTABLE_RULE_CHAPTER_RE = re.compile(r'全局(?:业务)?规则')

# ── CSS 实现细节（WARN） ────────────────────────────────────────────────────
CSS_IMPL = re.compile(
    r'rgba?\([^)]+\)|#[0-9A-Fa-f]{6}\b|\d+px\b|font-size\s*[:：]'
    r'|border-radius\s*[:：]|linear-gradient'
)

# ── 豁免规则 ────────────────────────────────────────────────────────────────
# snake_case 豁免只给「埋点 / 数据契约」语境（行为分析平台事件名 / 属性英文名是外部契约，不可翻译）。
# 业务对象词典 / 状态机的字段用中文业务名（全文讲人话立场），故移除「字段」「核心 ID」豁免。
EXEMPT_H2_KW = ('枚举值', '埋点', '事件', '参数', '对照', '归因', '指标')
EXEMPT_HEADER_KW = ('事件', '参数', '枚举', '指标', '触发', '层级', '路由')

# ── 僵尸 H2/H3：标题含「砍掉/已删除/废弃/已下线/已移除/已合并/取消」（FAIL）──
# PRD 描述当前态，砍掉的 Scene 应物理删除整段，delta 归 1.3 变更范围
ZOMBIE_HEADING = re.compile(
    r'(砍掉|已删除|已废弃|废弃|已移除|已下线|已合并|取消（V|^取消)'
)

# ── H2/H3 里的「(V x.y …)」流水（FAIL）─────────────────────────────────────
# 标题应描述当前态，版本 delta 归 1.3。lookahead 排除文件名引用 (xxx.docx) 等
H2_V_TAG = re.compile(
    r'\s*[（(]\s*V\d+(?:\.\d+)*'
    r'(?![^）)]*\.(?:docx|html|md|pdf|js|py)\b)'
    r'(?:\s*[：:、，,\s][^）)]{0,60})?'
    r'\s*[）)]'
)

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

# 决策编号:PRD 正文不允许出现「决策 N」内部 ID 引用(只在 baseline 决策记录 / delta §6 存活)
DECISION_NUM_RE = re.compile(r'决策\s*\d+')

# 章节锚点:正文里 §X.Y / §X 是内部死链(split 模式跨子页跳不过去),禁用,用「白话章节名」替代
# 例: ❌「按 §4.2 口径」 → ✅「按全局归因规则口径」/「见 6.5 自动同步」
# SECTION_ANCHOR_RE 从共性层 banned_terms 引入（见文件头 import）

# 具体 URL / 路由:PM 不定义技术实现的 URL,业务语义用「独立页 / 独立路由」描述
# 紧前不能是 \w(避免 S/N 1/2 这类比例)/ + 小写字母开头 + 后续可多段
# 例: ❌「/activity-center/my」 ✅「独立路由」/ 「独立页」
ROUTE_URL_RE = re.compile(r'(?<!\w)/[a-z][a-z0-9-]*(?:/[a-z0-9{}][a-z0-9{}-]*)+')

# ── PM 角色越界禁词（FAIL）─────────────────────────────────────────────
# PM 描述业务，不写实现层 / 不出 UI 英文术语 / 不写技术状态词
# 分类详见 references/prd-chapter-rules.md 「PM 越界禁词清单」
# 注：埋点章节 PM 必写事件 / 属性英文名，不归此清单管
PM_OVERREACH_RE = re.compile(
    r'\bhover\b'                                          # JS 事件名 → 「悬停」
    r'|\b(?:onclick|onfocus|onblur)\b'                    # JS 事件名
    r'|\bDOM\b'                                           # 实现层
    r'|display:\s*(?:none|block|flex|grid|inline)'        # CSS 属性值
    r'|\bclassName\b|\bquerySelector\b|\binnerHTML\b'     # DOM API
    r'|\bi18n\b'                                          # 国际化技术词 → 「翻译文案 / 多语种字典」
    r'|\bcache(?:Key|失效)?\b'                            # 缓存术语
    r'|\b(?:localStorage|sessionStorage)\b'               # 浏览器存储
    r'|\b(?:dirty|pristine)\s*(?:状态|state)?'            # 框架内部状态
    r'|(?<![a-zA-Z])\bmodal\b(?![a-zA-Z])'                # UI 英文 → 「弹窗」
    r'|(?<![a-zA-Z])\bchip\b(?![a-zA-Z])(?!\s+样式)'      # UI 英文 → 「胶囊 / 标签」
    r'|(?<![a-zA-Z])\btooltip\b(?![a-zA-Z])'              # UI 英文 → 「提示」（Toast 已通用保留）
    r'|@media\b'                                          # CSS 媒体查询
    r'|<\s*\d+\s*px\b|\d+px\s*断点'                       # 像素值断点
    r'|JS\s*加载'                                         # 「JS 加载失败」→ 「脚本加载」
)

# ── PM 视觉细节越界（FAIL）─────────────────────────────────────────────
# PM 写承载形态 / 交互行为 / 字段口径，不写颜色 / 尺寸 / 描边 / 圆角等视觉规格
# 合规写法：「按视觉规范」/「视觉规范由设计定」/「按金融语义色规范（涨绿跌红）」
# 违规典型：「560 宽」「页面遮罩 + 中央卡片」「蓝色描边 + 浅蓝底」「深色 phone」「✕ 删除按钮」
PM_VISUAL_OVERREACH_RE = re.compile(
    # 颜色词 + UI 元素
    r'(?:蓝|绿|红|黄|紫|金|橙|粉|青)色\s*(?:FAB|按钮|圆角|胶囊|描边|底|字|框|图标|文字|文本|箭头)'
    # 颜色作底 / 字 / 描边（排除"颜色语义"合规用法）
    r'|(?:蓝|绿|红|黄|紫|橙|青|粉)底(?!色)'
    r'|(?:蓝|绿|红|金|银)字(?!符|段|幕|节|串)'
    r'|(?:浅|深)(?:蓝|绿|红|黄|紫|灰)(?:底|描边|框)'
    # 行业语义颜色——「涨绿跌红」「绿正红负」是金融产品数据→颜色映射需求，非 UI 设计细节，PM 可描述
    r'|(?:绿|红)色\s*/\s*(?:红|绿)色'
    # 视觉术语
    r'|页面遮罩|中央卡片'
    r'|(?:底部|顶部|左侧|右侧)贴边'
    r'|下划线\s*active|active\s*下划线'
    r'|外加\s*(?:细黑|蓝|红|绿)?\s*边框'
    # 形状 / 装饰（排除已有业务词组合）
    r'|(?<![圆])圆角(?!矩形)(?!\s*胶囊)'
    r'|阴影(?!\s*[分图])'
    r'|内边距|外边距|内距|外距'
    # 尺寸数值
    r'|\d{2,4}\s*宽(?![松度带])'
    r'|\d{2,4}\s*高(?![频度兴])'
    r'|\d{2,4}\s*px\b'
    r'|\d+\s*%\s*(?:区域|宽|高)'
    # 设备壳描述
    r'|深色\s*phone|浅色\s*webframe|\d{3,4}\s*设备壳'
    # UI 符号（任何位置）
    r'|✕'
)


# 图标 emoji 越界：PM 指定图标长什么样属设计细节（🪙 打赏 → 写「打赏」即可）。
# 排除语义箭头 → ← ↔ ↑ ↓ ↕ ⇄（流程连接 / 方向，是合法语义符，非装饰图标）。
# 覆盖：表情符号块 / 杂项符号 / 装饰符号 / 补充符号 / 旗帜 / 常见装饰箭头变体（排除上述语义箭头）。
PM_EMOJI_RE = re.compile(
    '[\U0001F300-\U0001FAFF'   # 表情 + 杂项符号与象形 + 补充符号 + 扩展A
    '\U00002600-\U000026FF'    # 杂项符号（☀ ⛔ 等）
    '\U00002700-\U000027BF'    # 装饰符号（✂ ✅ ✓ ✕ 等）
    '\U0001F1E6-\U0001F1FF'    # 区域指示符（旗帜）
    '⬀-⯿'            # 杂项符号与箭头（⬆ ⭐ 等装饰箭头）
    '⤴⤵'             # 弯曲箭头装饰
    '↩↪➡'       # 带钩箭头 / 粗右箭头（装饰类）
    '↻↺'             # 循环箭头 ↻ ↺
    ']'
)


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

# 中文相邻半角标点(soul.md 禁止 · 与 scripts/check_cjk_punct.py 规则同源)
CJK_HALF_PUNCT_RE = re.compile(r'[㐀-䶿一-鿿豈-﫿][,:;()]|[,:;()][㐀-䶿一-鿿豈-﫿]')

# 圈数字残留(CLAUDE.md 禁止 ①②③)
CIRCLE_NUM_RE = re.compile(r'[①-⑳⓫-⓿]')

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
# check_prd_md.sh 与 hook 侧新门都从这里取维度，不再各自维护副本。
# 每项 = (md_scan 返回键, 人读标签)。按运行条件选入见下面两支函数。

# 无条件 FAIL 维度
_PRD_FAIL_BASE: list[tuple[str, str]] = [
    ("date_tag_hits", "流水账日期 / 版本标记"),
    ("zombie_heading_hits", "僵尸 heading（应物理删除）"),
    ("v_tag_heading_hits", "heading 含 V 版本流水"),
    ("tech_field_hits", "5 段式禁用研发字段（触发/读/写/事件/API）"),
    ("circle_nums", "圈数字 ①②③（CLAUDE.md 全局禁）"),
    ("decision_nums", "正文「决策 N」（应在 baseline 决策记录 / delta §6）"),
    ("route_urls", "正文具体 URL / 路由（PM 不定义技术实现，应用「独立页 / 独立路由」业务语义）"),
    ("pm_overreach_hits", "PM 角色越界禁词（hover / DOM / i18n / modal / cache / dirty / @media 等）"),
    ("visual_overreach_hits", "PM 视觉细节越界（颜色 / 尺寸 / 描边 / 圆角 / 设备壳 / ✕ 等，应由设计规范定）"),
    ("iteration_traces", "§1.4 核心变更迭代流水词"),
    ("broken_image_alt", "图片 alt 为空"),
    ("nested_subscenes", "5/6/7 章两层嵌套（##### N.x.y.z 禁，一层 #### N.x.y 物理分组放行）"),
    ("horizontal_rule_hits", "水平线 ---（Confluence 渲染丑，章节用 h1/h2 自然分隔；表格 |---| 不算）"),
]

# 场景正文串句：§2.x 需求正文 现状 / 本轮 标签 bullet 焊多句。
# 逃生阀 SKIP_SCENE_PROSE_GATE=1（连贯叙事确实该保留时用，用前先向用户说明原因——知会制）。
_PRD_FAIL_SCENE_PROSE = (
    "scene_prose_runon_hits",
    "场景正文标签 bullet 焊多句（一 bullet 一原子事实 / 多阶段用 →；逃生阀 SKIP_SCENE_PROSE_GATE=1）",
)

# §X.Y 锚点死链 / 裸场景编号只在 split（多文件拼接）成立：拼页后锚点跨文件失效，
# 裸编号在 scenes/ 散件里无上下文。单文件（single delta / baseline）内跳与编号索引是设计模式。
_PRD_FAIL_SPLIT_ONLY: list[tuple[str, str]] = [
    ("section_anchors", "正文「§X.Y」章节锚点（应用白话章节名）"),
    ("bare_scene_codes", "正文裸场景编号（应用「编号 + 白话名」或纯白话）"),
]

_PRD_FAIL_PLACEHOLDERS = ("placeholders", "占位符残留（TBD/TODO/{{ 待填）")

# 引用块 >：baseline 历史 living 文档存量豁免（等迭代消化），delta / single / split 都拦。
_PRD_FAIL_BLOCKQUOTE = (
    "blockquote_hits",
    "引用块 >（Confluence 渲染丑，业务故事用 **业务故事**：正文；表格 | 不算）",
)

# 埋点表「应埋点平台」列出现服务端 / 后台类（CMS）→ FAIL（Platform C 只做 APP / Web 端埋点）。
# baseline 存量豁免——历史事件已按服务端注册，不拦存量。
_PRD_FAIL_SERVER_PLATFORM = (
    "server_platform_tracking",
    "埋点表应埋点平台含服务端 / 后台（只做 APP / Web 端埋点）",
)

# 无条件 WARN 维度
PRD_WARN_KEYS: list[tuple[str, str]] = [
    ("snake_field_hits", "snake_case 字段名（字段表已豁免）"),
    ("css_impl_hits", "CSS 实现细节（PM 不应写）"),
    ("cjk_half_punct", "CJK 旁半角标点"),
    ("semicolon_abuse_hits", "分号滥用（单行 ≥ 2 分号 → 拆成 bullet 或 1.2.3. 编号；表格行豁免）"),
    ("long_sentence_hits", "长句 run-on（句段 ≥ 100 字 → 拆句或转列表；表格行豁免）"),
    ("bullet_runon_hits", "bullet 串句（行内句号串并列项 → 一项一 bullet，句号只落行尾；表格行豁免）"),
    ("branch_prose_hits", "条件分支散文规则（全局规则章单行 ≥ 2 分支标记 → 改「给定｜当｜则」可断言表，见 prd-scene-templates §4.5；表格行豁免）"),
    ("label_li_runs", "场景块 li 重复标签前缀（同一标签 ≥ 3 条连排 → 标签做组头一次、子项缩一级 bullet，见 prd-scene-template-quickref）"),
    ("acceptance_echo_hits", "验收复述规格（同场景单元内验收 bullet 与规格 bullet 近重复 → 验收只写可验证判定点，能从规格直读的删掉）"),
]

# 骨架阶段：占位符从 FAIL 降 WARN（PM 填完前要清掉）
_PRD_WARN_PLACEHOLDERS = ("placeholders", "占位符残留（骨架阶段允许，PM 填完前要清掉）")


def prd_fail_keys(
    split: bool = False,
    skeleton: bool = False,
    profile: str = "delta",
    scene_prose: bool = True,
) -> list[tuple[str, str]]:
    """按运行条件返回 FAIL 维度清单。

    Args:
        split: PRD 是否 split 形态（同级有 {stem}-scenes/）
        skeleton: 骨架阶段模式（占位符降 WARN）
        profile: "baseline" 走 baseline 豁免集，其余按 delta
        scene_prose: 是否查场景正文串句（逃生阀 SKIP_SCENE_PROSE_GATE=1 时传 False）
    """
    keys = list(_PRD_FAIL_BASE)
    if scene_prose:
        keys.append(_PRD_FAIL_SCENE_PROSE)
    if split:
        keys.extend(_PRD_FAIL_SPLIT_ONLY)
    if not skeleton:
        keys.append(_PRD_FAIL_PLACEHOLDERS)
    if profile != "baseline":
        keys.append(_PRD_FAIL_BLOCKQUOTE)
        keys.append(_PRD_FAIL_SERVER_PLATFORM)
    return keys


def prd_warn_keys(skeleton: bool = False) -> list[tuple[str, str]]:
    """按运行条件返回 WARN 维度清单。"""
    keys = list(PRD_WARN_KEYS)
    if skeleton:
        keys.append(_PRD_WARN_PLACEHOLDERS)
    return keys
