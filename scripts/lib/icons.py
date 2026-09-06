"""工作区共享 SVG 图标库（Feather 风格线性 icon + Platform C 品牌 logo + 头像占位）。

被 IMAP / Prototype / architecture-diagrams 等 skill 产出物 `from lib.icons import ic` 复用。
项目级 icons.py 可在此基础上追加业务特有素材，见 projects/livestream/scripts/src/icons.py。
"""
import itertools

# ── 配色 token ───────────────────────────────────────────────────────────────
BG_PAGE = '#181A20'      # 页面底
BG_CARD = '#1E2329'      # 卡片 / 面板
BORDER = '#2B3139'       # 分割线 / 边框
TEXT_1 = '#EAECEF'       # 一级文字
TEXT_2 = '#848E9C'       # 二级文字
TEXT_3 = '#5E6673'       # 三级 / 禁用

# 品牌色：Platform C 蓝，三档各司其职
BRAND = '#007FFF'        # logo 与品牌露出
ACCENT = '#4DA6FF'       # 深底强调色（激活态、可点文字、图标高亮）
FILL = '#0066CC'         # 实心 CTA 底色

# 涨跌色（行情图唯一色源）
_TONE = {'up': '#0ECB81', 'down': '#F6465D'}

_AVATAR_BG = BORDER      # 头像底
_AVATAR_FG = TEXT_3      # 头像剪影

_MONO = "'JetBrains Mono',ui-monospace,monospace"   # 数字字体

# 素材内部 id 去重计数器。带前缀避免跟宿主页面 id 冲突。
_id_seq = itertools.count()


# ── Platform C Logo ─────────────────────────────────────────────────────────────────
# 29×44 双火焰（Figma 导出），viewBox 统一转 44×44 正方形按边长缩放。
_LOGO_VB = 44
_LOGO_LEFT = ('M18.9168 13.4978C19.0476 7.02217 15.3807 1.37942 13.4709 0.0232385'
             'C13.4622 0.0145171 13.2921 -0.0770567 13.3052 0.175864'
             'C13.3052 0.180225 13.3008 0.180223 13.3008 0.184584'
             'C13.1046 12.4164 6.81716 15.7131 3.4031 20.1959'
             'C-4.18371 30.1644 2.14735 41.5372 10.3489 43.6913'
             'C10.4885 43.7262 10.8678 43.8396 11.5873 43.9879'
             'C11.9622 44.0664 12.0712 43.748 11.7965 43.2727'
             'C10.8155 41.5677 9.0714 38.6896 8.72694 34.9917'
             'C7.9421 26.4055 18.7642 21.0331 18.9168 13.4978Z')
_LOGO_RIGHT = ('M23.0499 17.6413C22.9845 17.5934 22.8929 17.5977 22.8842 17.6806'
               'C22.7098 19.2373 21.1009 22.4643 18.9818 25.4819'
               'C11.8485 35.6554 15.4413 40.269 18.2318 43.4698'
               'C18.7464 44.0628 19.0036 43.932 19.2739 43.509'
               'C19.5268 43.1078 19.9105 42.5976 21.5587 41.8171'
               'C21.8159 41.695 28.0424 38.3896 28.7182 30.863'
               'C29.3679 23.5762 24.6981 18.9757 23.0499 17.6413Z')

# 头像 monogram 6 色盘，按名称 hash 分配
_MONO_PALETTE = ['#2F6CF2', '#0ECB81', '#F0B90B', '#8A63D2', '#00B0D1', '#F6465D']


# ── 线性 icon ────────────────────────────────────────────────────────────────
# 24×24 viewBox，Feather 风格（MIT），fill:none 线条，currentColor 由父元素控制。
_PATHS: dict[str, str] = {
    # 用户 / 社交
    'user':          '<circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>',
    'users':         '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    'heart':         '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>',
    'message':       '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    'share':         '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>',
    'thumbs-up':     '<path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>',
    'shield':        '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    'award':         '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/>',
    'gift':          '<polyline points="20 12 20 22 4 22 4 12"/><rect x="2" y="7" width="20" height="5"/><line x1="12" y1="22" x2="12" y2="7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/>',
    'star':          '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',

    # 音视频
    'mic':           '<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>',
    'mic-off':       '<line x1="1" y1="1" x2="23" y2="23"/><path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"/><path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>',
    'video':         '<polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>',
    'monitor':       '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
    'cast':          '<path d="M2 16.1A5 5 0 0 1 5.9 20M2 12.05A9 9 0 0 1 9.95 20M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6"/><line x1="2" y1="20" x2="2.01" y2="20"/>',
    'eye':           '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/>',
    'eye-off':       '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>',
    'camera':        '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>',
    'play':          '<polygon points="5 3 19 12 5 21 5 3"/>',
    'pause':         '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>',
    'volume':        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>',

    # UI 操作
    'x':             '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    'home':          '<path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>',
    'repeat':        '<polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>',
    'chevron-left':  '<polyline points="15 18 9 12 15 6"/>',
    'chevron-right': '<polyline points="9 18 15 12 9 6"/>',
    'chevron-down':  '<polyline points="6 9 12 15 18 9"/>',
    'chevron-up':    '<polyline points="18 15 12 9 6 15"/>',
    'chevrons-left': '<polyline points="11 17 6 12 11 7"/><polyline points="18 17 13 12 18 7"/>',
    'chevrons-right':'<polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/>',
    'arrow-up':      '<line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>',
    'arrow-down':    '<line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>',
    'check':         '<polyline points="20 6 9 17 4 12"/>',
    'search':        '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    'bell':          '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
    'settings':      '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    'send':          '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>',
    'clock':         '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    'lock':          '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    'hand':          '<path d="M18 11V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2"/><path d="M14 10V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2"/><path d="M10 10.5V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>',
    'smile':         '<circle cx="12" cy="12" r="10"/><path d="M8 13s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>',
    'more-h':        '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>',
    'copy':          '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    'pip':           '<rect x="2" y="4" width="20" height="16" rx="2"/><rect x="12" y="12" width="8" height="6" rx="1"/>',
    'maximize':      '<polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/>',
    'plus':          '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    'minus':         '<line x1="5" y1="12" x2="19" y2="12"/>',
    'menu':          '<line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>',
    'filter':        '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
    'edit':          '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>',
    'trash':         '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    'download':      '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    'upload':        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
    'refresh':       '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
    'external-link': '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>',
    'link':          '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    'log-out':       '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',

    # 信息 / 状态
    'info':          '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    'help':          '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    'alert-tri':     '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    'wifi-off':      '<line x1="1" y1="1" x2="23" y2="23"/><path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/><path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/><path d="M10.71 5.05A16 16 0 0 1 22.56 9"/><path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/>',
    'signal':        '<line x1="1" y1="20" x2="1" y2="14"/><line x1="6" y1="20" x2="6" y2="11"/><line x1="11" y1="20" x2="11" y2="6"/><line x1="16" y1="20" x2="16" y2="2"/>',

    # 金融 / 图表
    'trending-up':   '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    'trending-down': '<polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/>',
    'bar-chart':     '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    'layers':        '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    'credit-card':   '<rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>',
    'wallet':        '<path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4z"/>',

    # 文件 / 编辑
    'file':          '<path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/>',
    'folder':        '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
    'image':         '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
    'tag':           '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/>',
    'bookmark':      '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>',
    'flag':          '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/>',
    'calendar':     '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',

    # 通讯 / 定位
    'mail':          '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
    'phone':         '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    'map-pin':       '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',

    # 布局
    'list':          '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
    'grid':          '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>',
}


def ic(name: str, size: int = 16, color: str = 'currentColor',
       stroke_width: float | None = None) -> str:
    """单个线性 icon SVG。描边宽度按 clamp(36/size, 1.5, 2.25) 取值。"""
    if name not in _PATHS:
        raise KeyError(f'没有 icon {name!r}，现有：{", ".join(sorted(_PATHS))}')
    sw = stroke_width if stroke_width is not None else min(2.25, max(1.5, 36 / size))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" stroke="{color}" stroke-width="{sw:g}" '
            f'stroke-linecap="round" stroke-linejoin="round" fill="none" '
            f'aria-hidden="true" focusable="false" '
            f'style="vertical-align:middle;flex-shrink:0">{_PATHS[name]}</svg>')


def logo_svg(size: int = 24,
             color_left: str = 'currentColor',
             color_right: str = BRAND) -> str:
    """Platform C 双火焰 Logo SVG。原始比例 29:44，size 按高度缩放。"""
    w = round(size * 29 / 44, 1)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{size}" '
            f'viewBox="0 0 29 44" fill="none" aria-label="Platform C" '
            f'style="display:inline-block;vertical-align:middle;flex-shrink:0">'
            f'<path d="{_LOGO_LEFT}" fill="{color_left}"/>'
            f'<path d="{_LOGO_RIGHT}" fill="{color_right}"/>'
            f'</svg>')


def avatar_svg(size: int = 34) -> str:
    """圆形头像占位：灰底 + 人物剪影。肩部用 clipPath 裁掉贴边。"""
    r = size / 2
    uid = f'av{next(_id_seq)}'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" aria-hidden="true" style="display:block">'
        f'<defs><clipPath id="{uid}">'
        f'<circle cx="{r}" cy="{r}" r="{r - 0.5:.2f}"/>'
        f'</clipPath></defs>'
        f'<circle cx="{r}" cy="{r}" r="{r - 0.5:.2f}" fill="{_AVATAR_BG}"/>'
        f'<g clip-path="url(#{uid})">'
        f'<circle cx="{r}" cy="{r * 0.82:.2f}" r="{r * 0.34:.2f}" fill="{_AVATAR_FG}"/>'
        f'<ellipse cx="{r}" cy="{r * 1.72:.2f}" rx="{r * 0.62:.2f}" '
        f'ry="{r * 0.48:.2f}" fill="{_AVATAR_FG}"/>'
        f'</g></svg>'
    )


def avatar_monogram(name: str = 'U', size: int = 34) -> str:
    """圆形 monogram 头像：按名称 hash 取色盘背景 + 白色首字母。"""
    r = size / 2
    uid = f'av{next(_id_seq)}'
    letter = (name.strip()[0].upper() if name.strip() else '?')
    # sum(ord) 而非内置 hash()：str 的 hash() 受 PYTHONHASHSEED 影响、每进程随机，
    # 会导致同一批头像每次重跑 build 颜色随机重排，破坏"生成即完整，可幂等重跑"的约定
    bg = _MONO_PALETTE[sum(ord(c) for c in name) % len(_MONO_PALETTE)]
    fg = '#FFFFFF'
    font_size = round(size * 0.42)
    baseline_y = round(r + font_size * 0.35, 1)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" aria-hidden="true" style="display:block">'
        f'<defs><clipPath id="{uid}"><circle cx="{r}" cy="{r}" r="{r - 0.5:.2f}"/></clipPath></defs>'
        f'<circle cx="{r}" cy="{r}" r="{r - 0.5:.2f}" fill="{bg}"/>'
        f'<text x="{r}" y="{baseline_y}" text-anchor="middle" dominant-baseline="auto" '
        f'font-size="{font_size}" font-weight="700" fill="{fg}" clip-path="url(#{uid})" '
        f'font-family="-apple-system,\'SF Pro Text\',\'Noto Sans SC\',system-ui,sans-serif">'
        f'{letter}</text>'
        f'</svg>'
    )


if __name__ == '__main__':
    """python3 scripts/lib/icons.py：全部 icon XML 合法 + avatar/logo 合法 + id 不冲突。"""
    import re
    import sys
    import xml.etree.ElementTree as ET

    failures = []
    for name in _PATHS:
        try:
            ET.fromstring(ic(name, 16))
        except Exception as e:
            failures.append(f'ic({name!r}): {e}')
    for fn, args in [(logo_svg, (24,)), (avatar_svg, (34,))]:
        try:
            ET.fromstring(fn(*args))
        except Exception as e:
            failures.append(f'{fn.__name__}: {e}')
    for n in ('Edward', 'Anthony', '小Q', ''):
        try:
            ET.fromstring(avatar_monogram(n, 34))
        except Exception as e:
            failures.append(f'avatar_monogram({n!r}): {e}')

    ids: set[str] = set()
    dup = []
    for frag in (avatar_svg(34), avatar_svg(34),
                 avatar_monogram('Edward', 34), avatar_monogram('Anthony', 34)):
        for i in re.findall(r'id="([^"]+)"', frag):
            if i in ids:
                dup.append(i)
            ids.add(i)
    if dup:
        failures.append(f'id 冲突: {dup}')

    if failures:
        print(f'❌ {len(failures)} 项失败：')
        for f in failures:
            print('  -', f)
        sys.exit(1)
    print(f'✅ {len(_PATHS)} 个 icon + logo_svg + avatar_svg + avatar_monogram 全部通过，id 无冲突')
