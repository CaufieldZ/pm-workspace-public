"""跨产物「描述当前态」铁律 - UI 视觉层 PATTERN（px / hex / 字体 / ms / CSS / HTML 属性）。

调用方：
- scripts/check_static_chapter.py（真相源静态章 lint）
- .claude/skills/prd/scripts/humanize/patterns.py（PRD humanize 接共享层，PRD_UI_STRIP_PATTERNS 保留 PRD 特化）
- .claude/skills/interaction-map/scripts/check_imap.sh（IMAP 注解扫描）
- .claude/skills/prototype/scripts/check_proto.sh（prototype 注解扫描）

规则源：.claude/runbooks/human-voice-rules.md ④ UI 视觉（UI 设计参数）

豁免：
- PRD §7 非功能性需求里 ≤ 300ms / 1280px 是性能 / 兼容契约，保留（调用方传 exempt_h2）
- 金融语义色（涨绿跌红）/ 数字字体等宽——`.claude/skills/_shared/claude-design/tokens.css` 设备规范明确豁免
- prototype 容器 inline style——渲染层，调用方 BS4 限定 class 不扫 attribute
"""
import re

# ── 像素 / 字号 / pt ─────────────────────────────────────────────────────
PX_RE = re.compile(r'\b\d+(?:\.\d+)?\s*px\b')
PT_RE = re.compile(r'\b\d+\s*pt\b')


# ── 颜色（hex / rgba）────────────────────────────────────────────────────
# 6 位 / 8 位标准 CSS hex 全收
# 3 位短形：必须含至少一个字母（a-f）以避开 #128 / #1024 这类编号假阳
#          只 a-f 三位（#fff/#abc）或 a-f + 数字混排（#f0a/#a1b）都算
HEX_COLOR_RE = re.compile(
    r'[#＃](?:'
    r'[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?'              # 6 位 / 8 位
    r'|'
    r'(?=[0-9]{0,2}[A-Fa-f])[0-9A-Fa-f]{3}'           # 3 位至少 1 个字母
    r')\b'
)
RGBA_RE = re.compile(r'\brgba?\([^)]+\)')


# ── 动画毫秒 / opacity ───────────────────────────────────────────────────
MS_DURATION_RE = re.compile(r'\b\d+\s*ms\b')
OPACITY_RE = re.compile(r'\bopacity\s*[:：.]?\s*\d+(?:\.\d+)?')


# ── CSS 属性 / 字体名 / 渐变 ────────────────────────────────────────────
FONT_FAMILY_RE = re.compile(r'font-family\s*:', re.IGNORECASE)
CSS_PROP_RE = re.compile(
    r'(?:border-radius|background-color|font-size)\s*:',
    re.IGNORECASE,
)
LINEAR_GRADIENT_RE = re.compile(r'linear-gradient')
SPECIFIC_FONT_RE = re.compile(r'IBM Plex Mono|DIN Alternate')


# ── HTML 属性原文（PM 不该写控件代码）───────────────────────────────────
# 扩元素白名单：原仅 input/div/span，补 section/button/header/main/footer/nav/a/p/ul/li
HTML_ATTR_RAW_RE = re.compile(
    r'<\s*(?:input|div|span|section|button|header|main|footer|nav|a|p|ul|li)\s+'
    r'(?:type|class|id|style)='
)


# ── 章节豁免（PRD §7 非功能性 / 性能 / 兼容性章节保留性能契约）─────────────
EXEMPT_H2_KW = (
    '非功能性',
    '性能',
    '兼容性',
    '兼容矩阵',
)


def _is_exempt_h2(h2_title):
    """判断 H2 标题是否触发豁免（如 ≤ 300ms / 1280px 性能契约）。"""
    if not h2_title:
        return False
    return any(kw in h2_title for kw in EXEMPT_H2_KW)


def scan_ui_visual(text, exempt_h2=None):
    """扫描文本，返回所有命中的 (category, match_str) 列表。

    参数：
    - text：要扫的文本（行级或段级）
    - exempt_h2：当前所在 H2 标题，命中 EXEMPT_H2_KW（非功能性 / 性能 / 兼容性）整段豁免

    返回：list[(category, match_str)]
        category ∈ {px, pt, hex, rgba, ms, opacity, font, css_prop, gradient, html_attr,
                    ui_component, ui_interaction, ui_layout, ui_design_system,
                    ui_animation, ui_visual_detail}
    """
    if _is_exempt_h2(exempt_h2):
        return []
    hits = []
    for m in PX_RE.finditer(text):
        hits.append(('px', m.group(0)))
    for m in PT_RE.finditer(text):
        hits.append(('pt', m.group(0)))
    for m in HEX_COLOR_RE.finditer(text):
        hits.append(('hex', m.group(0)))
    for m in RGBA_RE.finditer(text):
        hits.append(('rgba', m.group(0)))
    for m in MS_DURATION_RE.finditer(text):
        hits.append(('ms', m.group(0)))
    for m in OPACITY_RE.finditer(text):
        hits.append(('opacity', m.group(0)))
    for m in FONT_FAMILY_RE.finditer(text):
        hits.append(('font', m.group(0)))
    for m in SPECIFIC_FONT_RE.finditer(text):
        hits.append(('font', m.group(0)))
    for m in CSS_PROP_RE.finditer(text):
        hits.append(('css_prop', m.group(0)))
    for m in LINEAR_GRADIENT_RE.finditer(text):
        hits.append(('gradient', m.group(0)))
    for m in HTML_ATTR_RAW_RE.finditer(text):
        hits.append(('html_attr', m.group(0)))
    # UI 越界词（组件名 / 交互动作 / 布局 / 设计语言 / 动效 / 视觉细节）
    from .ui_jargon import scan_ui_jargon
    hits.extend(scan_ui_jargon(text))
    return hits
