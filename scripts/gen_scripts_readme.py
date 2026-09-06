#!/usr/bin/env python3
"""生成 scripts/README.md —— 当前 scripts 清单（零腐化，自动从文件 + CLAUDE.md 提取）。

Usage:
    python3 scripts/gen_scripts_readme.py            # 写盘
    python3 scripts/gen_scripts_readme.py --check     # 对账，drift 则 exit 1（audit §15.8 用）

数据来源（全自动，不手维护）：
- 文件清单：scripts/*.py + scripts/*.sh + scripts/lib/*.py（含子目录）
- 职责：每个 .py 的模块 docstring 首行 / .sh 的首行 # 注释；缺失显示（待补）
- 快捷路由：解析 CLAUDE.md「快捷路由」表，提取 scripts/ 顶层脚本 → 触发词映射
- 分类：命中快捷路由的优先归「快捷路由入口」组，其余按文件名前缀归组

判定 scripts/ 顶层：执行列里路径以 scripts/ 开头，或裸 name.py/.sh（无 /，靠 CLAUDE.md
「命令前缀 python3 scripts/ 省略」约定）；.claude/skills/*/ 与 projects/*/ 子目录路径过滤。
"""
import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
LIB_DIR = SCRIPTS_DIR / "lib"
CLAUDE_MD = ROOT / "CLAUDE.md"
README = SCRIPTS_DIR / "README.md"

# ── 顶层脚本前缀 → 分组（未命中快捷路由时用）──────────────────────────────
PREFIX_GROUPS = [
    ("校验 / lint（check_*）", ["check_"]),
    ("抓取（fetch_*）", ["fetch_"]),
    ("分析（analyze_*）", ["analyze_"]),
    ("同步（sync_*）", ["sync_"]),
]
DEFAULT_TOP_GROUP = "其他工具"
SHELL_GROUP = "Shell 工具（.sh）"

TOP_GROUP_ORDER = [
    "快捷路由入口（CLAUDE.md 触发即跑）",
    "校验 / lint（check_*）",
    "抓取（fetch_*）",
    "分析（analyze_*）",
    "同步（sync_*）",
    DEFAULT_TOP_GROUP,
    SHELL_GROUP,
]

# ── lib 子目录 → 分组（静态，对应 human-voice-rules 四层 + 外部服务封装）────
LIB_GROUPS = [
    ("voice-checks 规则层（human-voice-rules 四层镜像）", [
        "banned_terms", "business_voice", "changelog_residue", "thinking_process",
        "ui_visual", "ui_jargon", "ui_annotation", "run_voice_checks",
        "visible_text", "tech_jargon",
    ]),
    ("HTML 生成 / 检查", [
        "html_basics", "html_builder", "html_components", "md_to_html",
    ]),
    ("外部服务封装", [
        "confluence", "confluence_storage", "google_sheets", "demand_pool_base",
    ]),
]
LIB_DEFAULT_GROUP = "其他"


def first_line_py(path: Path) -> str:
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    except Exception:
        return "(解析失败)"
    if not doc:
        return "(待补 docstring)"
    first = doc.splitlines()[0].strip() if doc.strip() else "(空 docstring)"
    return first or "(空 docstring)"


def first_line_sh(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines()[:6]:
        s = line.strip()
        if s.startswith("#!"):
            continue
        if s.startswith("#"):
            return s.lstrip("#").strip() or "(空注释)"
    return "(待补注释)"


# ── CLAUDE.md 快捷路由解析 ────────────────────────────────────────────────
_ROUTING_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$")
_SCRIPT_TOKEN_RE = re.compile(r"[\w./-]+\.(?:py|sh)")


def parse_routing() -> dict[str, list[str]]:
    """解析 CLAUDE.md 快捷路由表 → {scripts/ 顶层 basename: [触发词]}。

    判定顶层：路径以 scripts/ 开头（取 basename），或裸 name.py/.sh（无 /）。
    .claude/skills/...、projects/... 子目录路径过滤掉。
    """
    if not CLAUDE_MD.is_file():
        return {}
    text = CLAUDE_MD.read_text(encoding="utf-8")
    m = re.search(r"^## 快捷路由", text, re.MULTILINE)
    if not m:
        return {}
    section = text[m.start():]
    m2 = re.search(r"\n## ", section)
    if m2:
        section = section[:m2.start()]

    mapping: dict[str, list[str]] = {}
    for line in section.splitlines():
        rm = _ROUTING_ROW_RE.match(line)
        if not rm:
            continue
        trigger = rm.group(1).strip()
        exec_cell = rm.group(2).strip()
        for tok in _SCRIPT_TOKEN_RE.findall(exec_cell):
            if "/" in tok:
                if tok.startswith("scripts/"):
                    base = Path(tok).name
                else:
                    continue  # .claude/skills/... 或 projects/... 子目录
            else:
                base = tok  # 裸 name.py/.sh（命令前缀省略约定）
            mapping.setdefault(base, [])
            if trigger not in mapping[base]:
                mapping[base].append(trigger)
    return mapping


def classify_top(filename: str, routing: dict[str, list[str]]) -> str:
    if filename in routing:
        return "快捷路由入口（CLAUDE.md 触发即跑）"
    if filename.endswith(".sh"):
        return SHELL_GROUP
    for group, prefixes in PREFIX_GROUPS:
        if any(filename.startswith(p) for p in prefixes):
            return group
    return DEFAULT_TOP_GROUP


def build() -> str:
    routing = parse_routing()

    top_files = sorted(
        [p for p in SCRIPTS_DIR.glob("*") if p.is_file() and p.suffix in (".py", ".sh")],
        key=lambda p: p.name,
    )
    top_groups: dict[str, list[tuple[str, str]]] = {}
    for p in top_files:
        desc = first_line_py(p) if p.suffix == ".py" else first_line_sh(p)
        top_groups.setdefault(classify_top(p.name, routing), []).append((p.name, desc))

    lib_entries: list[tuple[str, str]] = []
    for p in sorted(LIB_DIR.iterdir()):
        if p.name == "__init__.py":
            continue
        if p.is_dir():
            if p.name == "__pycache__":
                continue
            init = p / "__init__.py"
            desc = first_line_py(init) if init.is_file() else "(目录无 __init__)"
            lib_entries.append((f"{p.name}/", desc))
        elif p.suffix == ".py":
            lib_entries.append((p.name, first_line_py(p)))

    out: list[str] = []
    out.append("# Scripts 清单")
    out.append("")
    out.append("> 本文件由 `python3 scripts/gen_scripts_readme.py` 自动生成，**勿手改**。")
    out.append("> 本文件只回答「当前有哪些 script、各管什么」；具体用法见各脚本 docstring / `--help`。")
    out.append("> 加 / 删脚本后重跑生成脚本；audit §15.8 会校验是否 drift。")
    out.append("")
    out.append("## 入口脚本（scripts/*.py + *.sh）")
    out.append("")
    for grp in TOP_GROUP_ORDER:
        items = top_groups.get(grp)
        if not items:
            continue
        out.append(f"### {grp}")
        out.append("")
        out.append("| 脚本 | 快捷路由 | 职责 |")
        out.append("|------|---------|------|")
        for name, desc in items:
            triggers = routing.get(name)
            tcell = " / ".join(triggers) if triggers else "—"
            out.append(f"| `{name}` | {tcell} | {desc} |")
        out.append("")

    out.append("## 共享层（scripts/lib/）")
    out.append("")
    placed: set[str] = set()
    for grp, members in LIB_GROUPS:
        out.append(f"**{grp}**")
        out.append("")
        out.append("| 模块 | 职责 |")
        out.append("|------|------|")
        for name in members:
            match = next(
                (e for e in lib_entries if e[0] in (name, f"{name}.py", f"{name}/")),
                None,
            )
            if match:
                out.append(f"| `{match[0]}` | {match[1]} |")
                placed.add(match[0])
        out.append("")

    others = [e for e in lib_entries if e[0] not in placed]
    if others:
        out.append(f"**{LIB_DEFAULT_GROUP}**")
        out.append("")
        out.append("| 模块 | 职责 |")
        out.append("|------|------|")
        for name, desc in others:
            out.append(f"| `{name}` | {desc} |")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="对账模式：drift 则 exit 1，不写盘")
    args = ap.parse_args()

    content = build()

    if args.check:
        if not README.is_file():
            print("❌ scripts/README.md 不存在，跑 python3 scripts/gen_scripts_readme.py 生成", file=sys.stderr)
            return 1
        if README.read_text(encoding="utf-8") != content:
            print("❌ scripts/README.md 与当前 scripts 不一致（drift）", file=sys.stderr)
            print("   修法：python3 scripts/gen_scripts_readme.py 重新生成", file=sys.stderr)
            return 1
        print("✅ scripts/README.md 与当前 scripts 一致")
        return 0

    README.write_text(content, encoding="utf-8")
    print(f"✅ 写入 {README.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
