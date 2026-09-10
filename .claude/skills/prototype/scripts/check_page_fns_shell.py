#!/usr/bin/env python3
"""prototype page_fns 设备壳越界检测：扫 page_* 函数体内是否生成设备壳元素。

何时用：prototype-shell-gate hook 自动调（page_fns .py 落盘触发）；
被 hook 拦下时人工复跑定位违规行。

规则源：.claude/skills/prototype/SKILL.md §page_fns 内容契约
  page_fns 只产页面内 UI 元素（卡片 / 列表 / 表单 / Tab 栏）；设备壳
  （.app-mock / .phone / .layout / .gnav / .p-nav / .web-front / .wf-footer /
  .p-drawer / .modal-bg / sidebar）由 build 骨架统一负责，page_fns 再生成
  会与外层壳叠加打架。

参数：
    files      待检 .py 文件路径，可多个（非 .py 后缀自动跳过）
    --strict   阻断模式：有违规 exit 2（hook 用）；默认 exit 1 仅告警

前置：无（纯文本扫描，不依赖文件之外的环境）。

退出码：
    0 — 无违规
    1 — 有违规但未传 --strict
    2 — 传 --strict 且有违规
    临时绕过（仅 hook 侧生效，需源文件 head 注释说明理由）：SKIP_PROTOTYPE_SHELL_GATE=1
"""
import argparse
import re
import sys
from pathlib import Path

EPILOG = """\
示例：
    # 人工复跑单文件（hook 拦下后定位违规行）
    python3 .claude/skills/prototype/scripts/check_page_fns_shell.py projects/<产品线>/scripts/src/scenes/<场景>.py
    # 批量扫 + 阻断模式（hook 调用形态）
    python3 .claude/skills/prototype/scripts/check_page_fns_shell.py projects/<产品线>/scripts/src/scenes/*.py --strict
"""

# 设备壳元素 — 出现在 page_* 函数体内即违规
# 规则源：prototype SKILL.md L284-304 page_fns 内容契约
#   build 骨架职责（page_fns 不应再生成）：
#   - 设备框：.app-mock / .phone（前台 phone）/ .layout（后台）
#   - 多 view 切换：.gnav
#   - Web 后台/前台 nav：.p-nav
#   - Web 前台容器/底部：.web-front / .wf-footer
#   - 抽屉/弹窗容器壳：.p-drawer / .modal-bg
#   - Sidebar：<aside> 语义元素 / class="sidebar" 字面
SHELL_PATTERNS = [
    # 设备框
    (re.compile(r'''class\s*=\s*["'][^"']*\bapp-mock\b'''), ".app-mock 设备框"),
    (re.compile(r'''class\s*=\s*["'][^"']*\blayout\b'''), ".layout 后台设备壳"),
    (re.compile(r'''class\s*=\s*["'][^"']*\bphone\b(?!-)'''), ".phone 设备框"),
    # 多 view + nav 壳
    (re.compile(r'''class\s*=\s*["'][^"']*\bgnav\b'''), ".gnav 顶部多 view 切换壳"),
    (re.compile(r'''class\s*=\s*["'][^"']*\bp-nav\b'''), ".p-nav 顶部导航"),
    # Web 前台容器
    (re.compile(r'''class\s*=\s*["'][^"']*\bweb-front\b'''), ".web-front 对客 web 容器壳"),
    (re.compile(r'''class\s*=\s*["'][^"']*\bwf-footer\b'''), ".wf-footer web 底部壳"),
    # 抽屉/弹窗容器壳（panel/content 由 page_fns 提供，容器壳不行）
    (re.compile(r'''class\s*=\s*["'][^"']*\bp-drawer\b'''), ".p-drawer 抽屉容器壳"),
    (re.compile(r'''class\s*=\s*["'][^"']*\bmodal-bg\b'''), ".modal-bg 弹窗容器壳"),
    # Sidebar 两种写法
    (re.compile(r"<aside[\s>]"), "<aside> sidebar 语义元素"),
    (re.compile(r'''class\s*=\s*["'][^"']*\bsidebar\b'''), "class=\"sidebar\" 字面"),
]

# page_* 函数边界识别
PAGE_FN_DEF_RE = re.compile(r"^def\s+(page_\w+)\s*\(")
ANY_DEF_RE = re.compile(r"^(?:def|class)\s+\w+")


def scan(path: Path):
    """扫一个 .py 文件，返回 [(lineno, fn_name, category, snippet), ...]"""
    if not path.exists() or path.suffix.lower() != ".py":
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    lines = text.split("\n")

    hits = []
    in_page_fn = None
    page_fn_indent = None
    for i, line in enumerate(lines, 1):
        m = PAGE_FN_DEF_RE.match(line)
        if m:
            in_page_fn = m.group(1)
            page_fn_indent = len(line) - len(line.lstrip())
            continue
        # 退出条件：遇到同级或更外层的 def / class
        if in_page_fn and ANY_DEF_RE.match(line):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= page_fn_indent:
                in_page_fn = None
                page_fn_indent = None
        if not in_page_fn:
            continue
        # 在 page_* 函数体内，检查禁词
        for pat, category in SHELL_PATTERNS:
            if pat.search(line):
                snippet = line.strip()[:120]
                hits.append((i, in_page_fn, category, snippet))
    return hits


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+",
                    help="待检 .py 文件路径，可多个（非 .py 后缀自动跳过）")
    ap.add_argument("--strict", action="store_true",
                    help="阻断模式：有违规 exit 2（hook 用）；默认 exit 1 仅告警")
    args = ap.parse_args()

    total = 0
    for f in args.files:
        path = Path(f)
        hits = scan(path)
        if not hits:
            continue
        total += len(hits)
        print(f"\n{path} — page_fns 设备壳越界 {len(hits)} 处", file=sys.stderr)
        for lineno, fn, cat, snippet in hits:
            print(f"  ❌ L{lineno} [{fn}] {cat}", file=sys.stderr)
            print(f"     {snippet}", file=sys.stderr)

    if total:
        print("", file=sys.stderr)
        print("❌ page_fns 函数体内禁生成设备壳元素。", file=sys.stderr)
        print("   规则：page_fns 只产页面内 UI（卡片 / 列表 / 表单 / Tab）。", file=sys.stderr)
        print("   设备壳由 build 骨架统一负责，page_fns 不应再生成（完整清单见", file=sys.stderr)
        print("   prototype SKILL.md §page_fns 内容契约）。", file=sys.stderr)
        print("   临时绕过：SKIP_PROTOTYPE_SHELL_GATE=1", file=sys.stderr)

    if total == 0:
        sys.exit(0)
    sys.exit(2 if args.strict else 1)


if __name__ == "__main__":
    main()
