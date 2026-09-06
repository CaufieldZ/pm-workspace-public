"""Step C 标杆对照自检 · prototype skill

对照范式标杆 HTML 检查候选 HTML：
  1) 必备组件计数 (.scr / .nav / .cta-bar / .hind ...)
  2) Fill 视觉铁律 (E1-E6)
  3) 字体栈 / 字重三级
  4) 反 AI slop 六禁
  5) V 组视觉门（数字排版 / 壳内素材 / 悬浮反馈 / 交互态）

V 组按端类型分档（手机不 hover、CMS 不铺行情数字），阈值照两条产线已交付
标杆标定：全绿的进 fail，标杆自身有合法反例的留 warn（warn 不计退出码）。

用法：
  python3 .claude/skills/prototype/scripts/audit_against_baseline.py <候选> [--baseline <标杆>] [--paradigm <key>]

退出码 0 = 全通过；非 0 = 有 fail（数字 = fail 项数）。
"""
import argparse
import re
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup, Comment, Tag
except ImportError:  # bs4 缺失时 V2 跳过，其余规则照跑
    BeautifulSoup = None

# ── E 节 Fill 视觉铁律 grep 规则 ────────────────────
E_RULES = [
    {
        "name": "E1 toggle 不 remove layout",
        "check": lambda h: bool(re.search(r"\.cta-blue\.cta-grey", h)) or "remove('cta-blue')" not in h,
        "hint": "JS 切换状态用 `add('cta-grey,subscribed')` 不 remove cta-blue；CSS 用复合选择器 `.cta-blue.cta-grey{...}`",
    },
    {
        "name": "E2 滚动条双引擎",
        "check": lambda h: ("::-webkit-scrollbar" in h) and ("scrollbar-width:none" in h or "scrollbar-width: none" in h),
        "hint": "需 webkit + scrollbar-width: none 双引擎覆盖",
    },
    {
        "name": "E3 抽屉 visibility:hidden",
        "check": lambda h: ":not(.show)" not in h or ("visibility:hidden" in h or "visibility: hidden" in h),
        "hint": "`.p-drawer:not(.show)` 必须配套 visibility:hidden",
    },
    {
        "name": "E4 不用 :has()",
        "check": lambda h: not re.search(r"[^\w]:has\(", h),
        "hint": ":has() 跨浏览器不稳，改用 [data-active] + JS",
    },
    {
        "name": "E5 .cta-bar 不在 .p-page 内",
        "check": lambda h: not re.search(r'<div[^>]*class="[^"]*p-page[^"]*"[^>]*>(?:[^<]|<(?!/div>))*<div[^>]*class="[^"]*cta-bar', h, re.DOTALL),
        "hint": ".cta-bar 必须放 .app-mock / .phone 直接子级，不能在 .p-page 内",
    },
]


# ── 反 AI slop 六禁 ────────────────────────────────
SLOP_RULES = [
    {
        "name": "禁全屏渐变背景",
        "check": lambda h: not re.search(r"body\s*\{[^}]*linear-gradient.*\}", h, re.DOTALL),
        "hint": "body 上不要 linear-gradient 全屏背景",
    },
    {
        "name": "禁 emoji 装饰标题",
        "check": lambda h: not re.search(r"<h[1-6][^>]*>\s*[🚀⚡✨🎯💡✅🔥💎]", h),
        "hint": "标题不带 emoji 装饰（六禁第 2 条）",
    },
    {
        "name": "字体栈 CJK 优先",
        "check": lambda h: bool(re.search(r"font-family:[^;]*Noto Sans SC[^;]*Inter|font-family:[^;]*HarmonyOS Sans SC|font-family:[^;]*Noto Sans SC", h)),
        "hint": "CJK 字体必须排英文字体前；示例项目优先 HarmonyOS Sans SC",
    },
]


# ── 单 phone + scene chips 范式必备组件 ─────────────
SINGLE_PHONE_REQUIRED = [
    (r'class="[^"]*\bphone\b[^"]*"', ".phone 容器"),
    (r'class="[^"]*\bscr\b[^"]*"', ".scr 场景 div"),
    (r'class="[^"]*\bnav\b[^"]*"', ".nav scene chips"),
    (r'class="[^"]*\bbody\b[^"]*"', ".body 滚动区"),
    (r'class="[^"]*\bhind\b[^"]*"', ".hind home indicator"),
    (r'function\s+go\s*\(', "go(id) 切换函数"),
]

MULTI_VIEW_REQUIRED = [
    (r'class="[^"]*\bapp-shell\b[^"]*"', ".app-shell 整端 shell"),
    (r'class="[^"]*\bgnav', "gnav 全局导航"),
    (r'class="[^"]*\bview', "view 容器"),
]

# ── 多端拆分（generate_single）范式必备组件 ─────────────
# 一端一文件：只留单个 .gnav-view-section 壳，没有 gnav 顶栏也没有 .app-shell，
# 设备壳按端在 .app-mock / .web-front / .layout 三档里选一。
SINGLE_END_REQUIRED = [
    (r'class="gnav-view-section', "view 容器"),
    (r'class="[^"]*\b(p-page|ct page)\b[^"]*"', "页容器（.p-page / .ct.page）"),
    (r'class="[^"]*\b(app-mock|web-front|layout)\b', "设备壳"),
    (r'function\s+goPage\s*\(', "goPage 切换函数"),
]


# ── V 组视觉门 ─────────────────────────────────
# 渲染壳选择器：chips 范式用 .phone，generate_single 用 .app-mock / .web-front / .layout
_SHELL_CLASSES = ('app-mock', 'web-front', 'layout', 'phone')

# 壳内允许出现的符号（UI 控件本身，非装饰素材）
_SYMBOL_WHITELIST = set('✕⚠✓→←↑↓·✔✖×')
_EMOJI_RE = re.compile(
    '[\U0001F300-\U0001FAFF\U0001F000-\U0001F0FF'
    '\U00002600-\U000027BF\U00002B00-\U00002BFF]'
)


def shell_text(html: str) -> str:
    """取渲染壳内的可见文本（不含 script / style / HTML 注释）。"""
    if BeautifulSoup is None:
        return ''
    soup = BeautifulSoup(html, 'html.parser')
    roots = soup.select(', '.join('.' + c for c in _SHELL_CLASSES))
    chunks = []
    for root in roots:
        for node in root.descendants:
            if isinstance(node, (Tag, Comment)):
                continue
            parent = node.parent
            if parent is None:
                continue
            if any(a.name in ('script', 'style')
                   for a in [parent] + list(parent.parents) if isinstance(a, Tag)):
                continue
            chunks.append(str(node))
    return ''.join(chunks)


def _is_dark_front(html: str) -> bool:
    """对客深色端（App / Web 前台）—— 行情数字排版只对这类端有意义。"""
    return ('class="app-mock' in html or "class='app-mock" in html
            or 'class="web-front' in html or "class='web-front" in html
            or 'class="phone"' in html or "class='phone'" in html)


def _is_web(html: str) -> bool:
    """带鼠标的端（Web 前台 / 后台）—— hover 反馈只对这类端有意义。"""
    return ('class="web-front' in html or "class='web-front" in html
            or 'class="layout' in html or "class='layout" in html)


def audit_visual(html: str) -> list:
    """V 组：返回 [{'name','pass','hint','warn'}, ...]。warn=True 的项不计 fail。"""
    results = []

    # V1 数字排版：价格 / 金额 / 数量 / 百分比列要等宽对齐，数值与单位分层。
    if _is_dark_front(html):
        n = len(re.findall(r'tabular-nums', html)) + len(
            re.findall(r"JetBrains Mono|IBM Plex Mono|ui-monospace", html))
        results.append({
            "name": "V1 数字排版等宽（对客深色端）",
            "pass": n >= 1,
            "warn": False,
            "hint": "价格 / 金额 / 涨跌幅套 .cx-num（font-variant-numeric:tabular-nums），"
                    "数值提亮加粗、单位留灰；不等宽的数字列上下位数对不齐",
        })

    # V2 壳内素材：图标 / 头像 / logo / 走势图走 scripts/lib/icons.py 的矢量件。
    # 标杆里有合法的内容型 emoji（礼物名之类），故留 warn。
    st = shell_text(html)
    if st:
        bad = sorted({c for c in _EMOJI_RE.findall(st) if c not in _SYMBOL_WHITELIST})
        results.append({
            "name": "V2 渲染壳内零 emoji 素材",
            "pass": not bad,
            "warn": True,
            "hint": f"壳内 emoji {bad[:10]} —— 图标 / 头像 / logo / 走势图走 "
                    "scripts/lib/icons.py（ic / avatar_monogram / logo_svg）；"
                    "确属产品文案内容（礼物名等）可忽略本条",
        })

    # V3 悬浮反馈：可点卡片抬升 + 投影，不靠边框变色。手机端无 hover，不检。
    if _is_web(html):
        results.append({
            "name": "V3 可点卡片悬浮反馈（Web 端）",
            "pass": bool(re.search(r'translateY\(-', html)) and 'box-shadow' in html,
            "warn": False,
            "hint": "hover 用 transform:translateY(-2px) + box-shadow（.cx-card.tap 自带），"
                    "不用 border-color 变色",
        })

    # V4 交互态：声明了却点不出状态变化的原型等于静态图。
    n_on = len(re.findall(r'class="[^"]*\b(?:on|active)\b', html))
    results.append({
        "name": "V4 交互态类 ≥ 2",
        "pass": n_on >= 2,
        "warn": False,
        "hint": f"当前 {n_on} 处 .on/.active——Tab / 筛选 / 开关的选中态要在 DOM 上体现，"
                "否则 Playwright 断不了、评审也点不出反馈",
    })

    return results


def grep_count(html: str, pattern: str) -> int:
    return len(re.findall(pattern, html))


def detect_paradigm(html: str) -> str:
    if 'class="phone"' in html or "class='phone'" in html:
        if grep_count(html, r'class="[^"]*\bscr\b') >= 3:
            return "single-phone-scenes"
        return "single-phone-no-nav"
    # gnav 顶栏 tab 才算多 view 合并；generate_single 只留 .gnav-view-section 不出顶栏
    if "app-shell" in html or re.search(r'class="gnav"', html):
        return "multi-view-gnav"
    if "gnav-view-section" in html:
        return "single-end"
    return "unknown"


def audit(html: str, paradigm: str) -> list:
    """跑全部规则，返回 [{'name', 'pass', 'hint'}, ...]"""
    results = []

    # E 节
    for rule in E_RULES:
        ok = rule["check"](html)
        results.append({"name": rule["name"], "pass": ok, "hint": rule["hint"]})

    # slop
    for rule in SLOP_RULES:
        ok = rule["check"](html)
        results.append({"name": rule["name"], "pass": ok, "hint": rule["hint"]})

    # 必备组件
    if paradigm == "single-phone-scenes":
        required = SINGLE_PHONE_REQUIRED
    elif paradigm == "multi-view-gnav":
        required = MULTI_VIEW_REQUIRED
    elif paradigm == "single-end":
        required = SINGLE_END_REQUIRED
    else:
        required = []
    for pat, name in required:
        ok = bool(re.search(pat, html))
        results.append({"name": f"必备 · {name}", "pass": ok, "hint": f"未找到匹配模式 {pat[:40]}..."})

    # 字重三级
    has_900 = bool(re.search(r"font-weight:\s*(900|800)\b", html))
    has_700 = bool(re.search(r"font-weight:\s*(700|600)\b", html))
    has_400 = bool(re.search(r"font-weight:\s*(400|500)\b|font-weight:\s*normal", html)) or "font-weight" not in html
    results.append(
        {
            "name": "字重三级层次 (900/700/400)",
            "pass": has_900 and has_700 and has_400,
            "hint": f"display(900/800)={has_900} title(700/600)={has_700} body(400)={has_400}",
        }
    )

    results.extend(audit_visual(html))

    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html", help="候选 HTML 文件路径")
    ap.add_argument("--baseline", help="标杆 HTML（可选，仅用于比对组件计数）")
    ap.add_argument("--paradigm", help="范式 key（默认自动探测）")
    args = ap.parse_args()

    html_path = Path(args.html)
    if not html_path.exists():
        print(f"❌ HTML 不存在: {html_path}", file=sys.stderr)
        sys.exit(1)

    html = html_path.read_text(encoding="utf-8")
    paradigm = args.paradigm or detect_paradigm(html)
    print(f"== 候选 HTML: {html_path.name} ==")
    print(f"== 范式（探测）: {paradigm} ==")
    if args.baseline:
        bl_path = Path(args.baseline)
        if bl_path.exists():
            print(f"== 标杆: {bl_path.name} ==")
        else:
            print(f"⚠️  标杆不存在: {bl_path}")

    print()
    results = audit(html, paradigm)
    fail_count = 0
    warn_count = 0
    for r in results:
        if r["pass"]:
            mark = "✓"
        elif r.get("warn"):
            mark = "⚠"
        else:
            mark = "✗"
        print(f"  {mark} {r['name']}")
        if not r["pass"]:
            if r.get("warn"):
                warn_count += 1
            else:
                fail_count += 1
            print(f"      → {r['hint']}")

    print()
    tail = f"（另有 {warn_count} 项 warn，不阻断）" if warn_count else ""
    if fail_count == 0:
        print(f"✅ 全部 {len(results) - warn_count} 项通过{tail}")
        sys.exit(0)
    else:
        print(f"❌ {fail_count}/{len(results)} 项 fail，必须修后再交付{tail}")
        sys.exit(min(fail_count, 99))


if __name__ == "__main__":
    main()
