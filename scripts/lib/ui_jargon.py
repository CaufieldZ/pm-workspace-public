"""UI 组件 / 交互 / 视觉术语黑名单（PM 越界）。

接入：
- scripts/check_static_chapter.py（真相源静态章）
- scripts/lib/ui_visual.py（PRD / IMAP / proto 注解扫描）

设计哲学：
PM 写「底部弹层 / 长按 / 点外部关闭」，
不写「Bottom Sheet / long-press / dismiss on outside click」。
PM 写「输入框 / 单选 / 复选」，不写「Input / Radio / Checkbox」。
PM 写「金融语义色（涨绿跌红）/ 数字字体等宽」，不写 hex / px / font-family。

豁免：
- 金融语义色 / 数字字体等宽业务术语保留（见 human-voice-rules.md「豁免」段）
- PRD §7 非功能性 / 性能 / 兼容性章节豁免（性能契约保留 px / ms）
"""
from __future__ import annotations

import re

# ── 组件名（UI 控件，PM 描述用户行为而非控件实现）─────────────────────────
# 单词 'Sheet' 太宽（业务"床单/纸张"），用 'Bottom Sheet' / 'Action Sheet' 复合形式
COMPONENT_WORDS = [
    'Drawer', 'Modal', 'Dialog', 'Toast', 'Snackbar', 'Popover', 'Tooltip',
    'Skeleton', 'Spinner', 'Loader', 'Picker', 'Bottom Sheet',
    'Action Sheet', 'Stepper', 'Carousel', 'Slider',
    'Breadcrumb', 'Pagination', 'Accordion', 'Collapse',
    'TreeSelect', 'Cascader', 'Datepicker', 'DateRangePicker',
    'TimePicker', 'Image Cropper',
]
# 注：单词 Switch / Checkbox / Radio / Tabs / Tree / Upload / Tags 等单词
# 也太常见（业务"切换/选项/单选/标签页/分类树/上传/标签"），暂从黑名单移除

# ── 交互动作（用户行为描述用中文）─────────────────────────────────────
INTERACTION_WORDS = [
    'hover', 'focus', 'blur', 'click', 'dblclick', 'tap',
    'long-press', 'swipe', 'scroll', 'pinch', 'zoom',
    'drag-drop', 'drag', 'drop',
]

# ── 布局 / CSS 属性 ────────────────────────────────────────────────────
LAYOUT_WORDS = [
    'flexbox', 'flex-grow', 'grid-layout', 'z-index', 'overflow',
    'transform', 'translate', 'viewport', 'breakpoint', 'media query',
    '@media',
]
# 注意：'flex' / 'grid' / 'absolute' / 'fixed' / 'sticky' 单词太常见
# 易误伤，从黑名单移除（human-voice-rules.md 豁免段已覆盖就够）

# ── 设计语言 / 组件库（出现在 PM 文档说明用研发口径，越界）─────────────
DESIGN_SYSTEM_WORDS = [
    'Material Design', 'AntDesign', 'Ant Design', 'Arco Design',
    'Chakra UI', 'shadcn', 'HeadlessUI', 'Radix UI',
]

# ── 动效 / 过渡 ────────────────────────────────────────────────────
ANIMATION_WORDS = [
    'transition', 'animation', 'keyframes',
    'ease-in', 'ease-out', 'ease-in-out', 'cubic-bezier',
]

# ── 视觉细节（PM 不写控件 CSS 属性）─────────────────────────────────
VISUAL_DETAIL_WORDS = [
    'border-radius', 'box-shadow', 'backdrop-filter',
    'linear-gradient', 'radial-gradient',
    'border-color', 'border-width', 'border-style',
]


def _compile_words(words: list[str]) -> list[re.Pattern]:
    """编译词表为 regex。含空格 / 特殊符号用字面量边界；纯标识符用 \\b。"""
    pats = []
    for w in words:
        if ' ' in w or any(c in w for c in '.+-@'):
            pats.append(re.compile(rf'(?<![A-Za-z0-9]){re.escape(w)}(?![A-Za-z0-9])'))
        else:
            pats.append(re.compile(rf'\b{re.escape(w)}\b'))
    return pats


COMPONENT_PATTERNS = _compile_words(COMPONENT_WORDS)
INTERACTION_PATTERNS = _compile_words(INTERACTION_WORDS)
LAYOUT_PATTERNS = _compile_words(LAYOUT_WORDS)
DESIGN_SYSTEM_PATTERNS = _compile_words(DESIGN_SYSTEM_WORDS)
ANIMATION_PATTERNS = _compile_words(ANIMATION_WORDS)
VISUAL_DETAIL_PATTERNS = _compile_words(VISUAL_DETAIL_WORDS)

ALL_PATTERNS: list[tuple[re.Pattern, str]] = []
for p in COMPONENT_PATTERNS:
    ALL_PATTERNS.append((p, 'ui_component'))
for p in INTERACTION_PATTERNS:
    ALL_PATTERNS.append((p, 'ui_interaction'))
for p in LAYOUT_PATTERNS:
    ALL_PATTERNS.append((p, 'ui_layout'))
for p in DESIGN_SYSTEM_PATTERNS:
    ALL_PATTERNS.append((p, 'ui_design_system'))
for p in ANIMATION_PATTERNS:
    ALL_PATTERNS.append((p, 'ui_animation'))
for p in VISUAL_DETAIL_PATTERNS:
    ALL_PATTERNS.append((p, 'ui_visual_detail'))


def scan_ui_jargon(text: str) -> list[tuple[str, str]]:
    """返回 [(category, match_str), ...]。"""
    hits = []
    for p, cat in ALL_PATTERNS:
        for m in p.finditer(text):
            hits.append((cat, m.group(0)))
    return hits
