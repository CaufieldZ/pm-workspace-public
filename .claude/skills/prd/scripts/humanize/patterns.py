"""regex / 常量定义（被 scan / fix / scene_codes 共用）。"""
import re


W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


# ── 流水账 / 版本痕迹（FAIL 阻断） ──────────────────────────────────────────
DATE_TAG = re.compile(
    r'[（(]\s*\d{4}-\d{2}-\d{2}[^）)]*[）)]'   # (2026-04-22 ...)
    r'|[（(]\s*from\s*v\d+[^）)]*[）)]'         # (from v47)
    r'|[（(]\s*(?:变更|新增)[^）)]*[）)]'        # (变更) (新增)
    r'|反转说明：'
    r'|砍掉：'
)

# ── 代码字段 snake_case（WARN） ─────────────────────────────────────────────
SNAKE_FIELD = re.compile(r'\b[a-z]+(?:_[a-z]+){1,4}\b')

# ── CSS 实现细节（WARN） ────────────────────────────────────────────────────
CSS_IMPL = re.compile(
    r'rgba?\([^)]+\)|#[0-9A-Fa-f]{6}\b|\d+px\b|font-size\s*[:：]'
    r'|border-radius\s*[:：]|linear-gradient'
)

# ── 豁免规则 ────────────────────────────────────────────────────────────────
EXEMPT_H2_KW = ('枚举值', '字段', '埋点', '事件', '参数', '对照', '核心 ID', '归因')
EXEMPT_HEADER_KW = ('ID', '字段', '事件', '参数', '枚举', '指标', '触发', '层级', '路由')

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


# ── 圈数字归一 + PM 内部场景编号清理 ───────────────────────────────────────
CIRCLE_NUMS = {'①': '1.', '②': '2.', '③': '3.', '④': '4.', '⑤': '5.',
               '⑥': '6.', '⑦': '7.', '⑧': '8.', '⑨': '9.', '⑩': '10.'}


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

# 决策编号:PRD 正文不允许出现「决策 N」内部 ID 引用(只在 context.md 第 7 章存活)
DECISION_NUM_RE = re.compile(r'决策\s*\d+')

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

# 中文相邻半角标点(soul.md 禁止)
CJK_HALF_PUNCT_RE = re.compile(r'[一-鿿][,:()]|[,:()][一-鿿]')

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
