#!/usr/bin/env python3
"""生成 .claude/hooks/README.md —— 当前 hook 清单（零腐化，自动从 settings + 文件提取）。

Usage:
    python3 scripts/gen_hooks_readme.py            # 写盘
    python3 scripts/gen_hooks_readme.py --check     # 对账，drift 则 exit 1（audit §15 用）

数据来源（全自动，不手维护）：
- 事件 / matcher：.claude/settings.json hooks 节
- 职责：每个 hook 文件第 2 行注释（`# <事件> hook: <职责>`）
- 内含 gate：hook 文件 + 它 source 的 lib/*.sh 里的 `log_event <type> <gate>`

dispatcher 类 hook（一个文件跑多个 gate）靠 lib 提取，文件名看不出的 gate 在此一目了然。
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK_DIR = ROOT / ".claude" / "hooks"
LIB_DIR = HOOK_DIR / "lib"
SETTINGS = ROOT / ".claude" / "settings.json"
README = HOOK_DIR / "README.md"

# git pre-commit 显式调用，非 Claude PreToolUse/PostToolUse 注册
SKIP_PREFIXES = ("pre-commit-",)

SOURCE_RE = re.compile(r'\.claude/hooks/(lib/[a-z0-9_-]+\.sh)')
# gate 字面量出现在六类调用：
#   log_event hook|gate <g>   ·   _check_block|clean|warn <g>   ·   _log_skip_gate <g>
#   ·   _pc_line_warn "<g>"   ·   _pc_skip "<g>"   ·   GATE="<g>"
GATE_RE = re.compile(
    r'(?:\blog_event\s+(?:hook|gate)\s+'
    r'|\b_check_(?:block|clean|warn)\s+'
    r'|\b_log_skip_gate\s+'
    r'|\b_pc_line_warn\s+["\']?'
    r'|\b_pc_skip\s+["\']?'
    r'|\bGATE\s*=\s*["\']?'
    r')'
    r'([a-z][a-z0-9-]+)'
)
# 变量引用形式（log_event hook "$gate"）gate 名是变量，静态提取不到——
# gate 名字面量落在上述六类的调用方 / 赋值处


def hook_desc(path: Path) -> str:
    """第 2 行注释去掉事件前缀（`PostToolUse Write|Edit hook:` / `PreToolUse:` / 无冒号），取职责部分。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        return ""
    line = lines[1].lstrip("# ").strip()
    # 剥前缀：事件名打头时，连同其后到冒号/'hook' 的整段一起剥
    #   "PostToolUse hook: X" → X ·  "Read hook: X" → X ·  "Write|Edit 统一 dispatcher…" → 原样（无冒号无 hook，保留）
    m = re.match(
        r'^(SessionStart|UserPromptSubmit|PreToolUse|PostToolUse|Stop|PreCompact)'
        r'[\w\s|/]*?(?:hook\s*[:：]|[:：])\s*(.+)$',
        line,
    )
    if m:
        return m.group(2).strip()
    # 无冒号/hook 分隔（dispatcher 类 "PreToolUse Write|Edit 统一 …"）：只剥事件名 token
    line = re.sub(
        r'^(SessionStart|UserPromptSubmit|PreToolUse|PostToolUse|Stop|PreCompact)\s+', '', line
    )
    return line.strip()


def sourced_libs(path: Path) -> list[str]:
    return SOURCE_RE.findall(path.read_text(encoding="utf-8"))


def gates_in(path: Path) -> set[str]:
    return set(GATE_RE.findall(path.read_text(encoding="utf-8")))


def hook_gates(path: Path) -> list[str]:
    """hook 自身 + 它 source 的 lib 里的全部 gate 名。"""
    gates = gates_in(path)
    for lib in sourced_libs(path):
        lib_path = HOOK_DIR / lib
        if lib_path.is_file():
            gates |= gates_in(lib_path)
    return sorted(gates)


def parse_settings() -> dict[str, list[str]]:
    """返回 {hook 文件名: [事件:matcher, ...]}。"""
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    reg: dict[str, list[str]] = {}
    for event, entries in data.get("hooks", {}).items():
        for entry in entries:
            matcher = entry.get("matcher", "*")
            for h in entry.get("hooks", []):
                cmd = h.get("command", "")
                m = re.search(r'\.claude/hooks/([a-zA-Z0-9_.-]+\.sh)', cmd)
                if m:
                    reg.setdefault(m.group(1), []).append(f"{event}:{matcher}")
    return reg


def build() -> str:
    reg = parse_settings()
    rows = []  # (event_sort_key, event, matcher, filename, desc, gates)

    event_order = {
        "SessionStart": 0, "UserPromptSubmit": 1, "PreToolUse": 2,
        "PostToolUse": 3, "Stop": 4, "PreCompact": 5,
    }

    for f in sorted(HOOK_DIR.glob("*.sh")):
        base = f.name
        if base.startswith(SKIP_PREFIXES):
            continue
        desc = hook_desc(f)
        gates = hook_gates(f)
        regs = reg.get(base, [])
        if regs:
            for r in regs:
                event, matcher = r.split(":", 1)
                rows.append((event_order.get(event, 9), event, matcher, base, desc, gates))
        else:
            rows.append((8, "（未注册）", "—", base, desc, gates))

    rows.sort(key=lambda x: (x[0], x[3]))

    out = []
    out.append("# Hooks 清单")
    out.append("")
    out.append("> 本文件由 `python3 scripts/gen_hooks_readme.py` 自动生成，**勿手改**。")
    out.append("> 怎么写 / 改 hook → [HOOK_WRITING.md](HOOK_WRITING.md)；本文件只回答「当前有哪些 hook、各管什么」。")
    out.append("> 加 / 删 hook 后重跑生成脚本；audit §15 会校验是否 drift。")
    out.append("")
    out.append("| 事件 | matcher | hook 文件 | 职责 | 内含 gate |")
    out.append("|------|---------|-----------|------|-----------|")
    for _, event, matcher, base, desc, gates in rows:
        gate_str = " · ".join(f"`{g}`" for g in gates) if gates else "—（纯观测 / 无埋点）"
        # 转义单元格内的 | （Markdown 表格列分隔符），如 matcher `Write|Edit`
        cell_matcher = matcher.replace("|", "\\|")
        cell_desc = desc.replace("|", "\\|")
        out.append(f"| {event} | `{cell_matcher}` | `{base}` | {cell_desc} | {gate_str} |")
    out.append("")

    # 全 gate 名索引（dashboard 聚合键 · SKIP env 同源），便于反查
    all_gates = sorted({g for *_, gates in rows for g in gates})
    out.append("## gate 名索引")
    out.append("")
    out.append(f"共 {len(all_gates)} 个 gate（`log_event` 字符串 = dashboard 聚合键 = `SKIP_<UPPER>_GATE` 同源）：")
    out.append("")
    out.append("，".join(f"`{g}`" for g in all_gates))
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="对账模式：drift 则 exit 1，不写盘")
    args = ap.parse_args()

    content = build()

    if args.check:
        if not README.is_file():
            print("❌ .claude/hooks/README.md 不存在，跑 python3 scripts/gen_hooks_readme.py 生成", file=sys.stderr)
            return 1
        if README.read_text(encoding="utf-8") != content:
            print("❌ .claude/hooks/README.md 与当前 hooks 不一致（drift）", file=sys.stderr)
            print("   修法：python3 scripts/gen_hooks_readme.py 重新生成", file=sys.stderr)
            return 1
        print("✅ hooks/README.md 与当前 hooks 一致")
        return 0

    README.write_text(content, encoding="utf-8")
    print(f"✅ 写入 {README.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
