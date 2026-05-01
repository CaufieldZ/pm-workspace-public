"""Step C 标杆对照自检 · prototype skill

对照范式标杆 HTML 检查候选 HTML：
  1) 必备组件计数 (.scr / .nav / .cta-bar / .hind ...)
  2) Fill 视觉铁律 (E1-E6)
  3) 字体栈 / 字重三级
  4) 反 AI slop 六禁

用法：
  python3 .claude/skills/prototype/scripts/audit_against_baseline.py <候选> [--baseline <标杆>] [--paradigm <key>]

退出码 0 = 全通过；非 0 = 有 fail（数字 = fail 项数）。
"""
import argparse
import re
import sys
from pathlib import Path


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
        "hint": "CJK 字体必须排英文字体前；HTX 项目优先 HarmonyOS Sans SC",
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


def grep_count(html: str, pattern: str) -> int:
    return len(re.findall(pattern, html))


def detect_paradigm(html: str) -> str:
    if 'class="phone"' in html or "class='phone'" in html:
        if grep_count(html, r'class="[^"]*\bscr\b') >= 3:
            return "single-phone-scenes"
        return "single-phone-no-nav"
    if "app-shell" in html or "gnav" in html:
        return "multi-view-gnav"
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
    for r in results:
        mark = "✓" if r["pass"] else "✗"
        print(f"  {mark} {r['name']}")
        if not r["pass"]:
            fail_count += 1
            print(f"      → {r['hint']}")

    print()
    if fail_count == 0:
        print(f"✅ 全部 {len(results)} 项通过")
        sys.exit(0)
    else:
        print(f"❌ {fail_count}/{len(results)} 项 fail，必须修后再交付")
        sys.exit(min(fail_count, 99))


if __name__ == "__main__":
    main()
