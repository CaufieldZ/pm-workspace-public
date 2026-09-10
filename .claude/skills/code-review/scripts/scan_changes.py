#!/usr/bin/env python3
"""增量代码 review 的 Phase 1 机械层聚合——算 diff 范围、路由规范、反查消费者与覆盖缺口。

四段输出喂给模型做 Phase 2 语义 review：① 变更清单 + 规范路由 ② 机械层结果
③ 消费者反查（改动符号被谁引用）④ 覆盖缺口（测试 / 自证 / README 该补什么）。

用法：
    python3 .claude/skills/code-review/scripts/scan_changes.py --staged
    python3 .claude/skills/code-review/scripts/scan_changes.py --range HEAD~3
    python3 .claude/skills/code-review/scripts/scan_changes.py <file>...
    python3 .claude/skills/code-review/scripts/scan_changes.py --staged --json-out -

前置：无（纯本地 git + 工区已有 checker；--help 本身不需要任何输入）。
      ruff / shellcheck 缺失时对应项标「未跑通」并说明原因，不中断也不静默吞。

退出码：
    0 — 恒 0。本脚本是报告器，不进 hook 链，阻断由 pre-commit 承担。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

try:
    from lib.repo import find_root
except ImportError:  # 仓库外 / sys.path 异常时退回路径推导
    def find_root() -> Path:
        return Path(__file__).resolve().parents[4]


# ── 规范路由表：口径沿用 .claude/hooks/lib/pre-writeedit-guards.sh 的 required-read 归属 ──
SPEC_OF_BUCKET = {
    "root_scripts": ["scripts/SCRIPTS_WRITING.md"],
    "hooks": [".claude/hooks/HOOK_WRITING-quickref.md"],
    "skill_scripts": ["scripts/SCRIPTS_WRITING.md"],
    "project_scripts": [],  # 产物生成器规则归对应产出物 skill，见 guess_product_skill
}

BUCKET_LABEL = {
    "root_scripts": "工区根 scripts/",
    "hooks": ".claude/hooks/",
    "skill_scripts": ".claude/skills/*/scripts/",
    "project_scripts": "projects/*/scripts/",
    "out_of_scope": "本 skill 不审",
}

# projects/*/scripts/ 产物生成器 → 对应产出物 skill（文件名关键词判定）
PRODUCT_SKILL_HINTS = (
    ("proto", "prototype"),
    ("imap", "interaction-map"),
    ("arch", "architecture-diagrams"),
    ("scene", "scene-list"),
)

CODE_SUFFIXES = (".py", ".sh")

# 跨模块引用面：顶层 def / class / 模块级大写常量 / bash 函数
_REMOVED_SYMBOL_PATTERNS = (
    re.compile(r"^-def\s+(\w+)"),
    re.compile(r"^-class\s+(\w+)"),
    re.compile(r"^-([A-Z][A-Z0-9_]*)\s*="),
    re.compile(r"^-(\w+)\(\)\s*\{?"),
)


# ────────────────────────── 纯函数（pytest 直接 import）──────────────────────────

def bucket_files(paths: list[str]) -> dict[str, list[str]]:
    """按仓库相对路径分桶。非 .py / .sh 一律进 out_of_scope。"""
    buckets: dict[str, list[str]] = {k: [] for k in BUCKET_LABEL}
    for p in paths:
        parts = PurePosixPath(p).parts
        if not p.endswith(CODE_SUFFIXES):
            buckets["out_of_scope"].append(p)
        elif parts[:1] == ("scripts",):
            buckets["root_scripts"].append(p)
        elif parts[:2] == (".claude", "hooks"):
            buckets["hooks"].append(p)
        elif len(parts) >= 5 and parts[:2] == (".claude", "skills") and parts[3] == "scripts":
            buckets["skill_scripts"].append(p)
        elif parts[:1] == ("projects",) and "scripts" in parts:
            buckets["project_scripts"].append(p)
        else:
            buckets["out_of_scope"].append(p)
    return buckets


def guess_product_skill(path: str) -> str:
    """projects/*/scripts/ 下的生成器 → 猜对应产出物 skill 名，猜不出返回空串。"""
    name = PurePosixPath(path).name.lower()
    for keyword, skill in PRODUCT_SKILL_HINTS:
        if keyword in name:
            return skill
    return ""


def route_specs(buckets: dict[str, list[str]]) -> dict[str, list[str]]:
    """桶 → 该读哪些规范文件（去重保序）。"""
    routes: dict[str, list[str]] = {}
    for bucket, files in buckets.items():
        if not files or bucket == "out_of_scope":
            continue
        specs = list(SPEC_OF_BUCKET.get(bucket, []))
        if bucket == "skill_scripts":
            for f in files:
                skill = PurePosixPath(f).parts[2]
                specs.append(f".claude/skills/{skill}/SKILL.md")
        elif bucket == "project_scripts":
            for f in files:
                skill = guess_product_skill(f)
                specs.append(
                    f".claude/skills/{skill}/SKILL.md" if skill
                    else f"（{f} 产物类型未知，读脚本 docstring 判断归属 skill）"
                )
        seen: set[str] = set()
        routes[bucket] = [s for s in specs if not (s in seen or seen.add(s))]
    return routes


def extract_changed_symbols(diff_text: str) -> list[tuple[str, str]]:
    """从 unified diff 抽「被删 / 被改签名」的顶层符号，返回 [(文件, 符号), ...] 去重保序。"""
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    current = ""
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            continue
        if not line.startswith("-") or line.startswith("---"):
            continue
        for pattern in _REMOVED_SYMBOL_PATTERNS:
            m = pattern.match(line)
            if m:
                key = (current, m.group(1))
                if key not in seen:
                    seen.add(key)
                    out.append(key)
                break
    return out


def coverage_gaps(statuses: dict[str, str], added_lines: str) -> list[str]:
    """按 SCRIPTS_WRITING 硬约束反查该补没补的东西，返回提示行。"""
    gaps: list[str] = []
    changed = set(statuses)
    stems = {PurePosixPath(p).stem for p in changed}

    for path in sorted(changed):
        name = PurePosixPath(path).name
        if name.startswith("check_") and name.endswith(".py") and f"test_{PurePosixPath(path).stem}" not in stems:
            gaps.append(f"{path} — checker 改了但 scripts/tests/test_{PurePosixPath(path).stem}.py 未同改（§三-G）")
        if (name.startswith("gen_") or name.startswith("build_")) and name.endswith((".py", ".sh")):
            gaps.append(f"{path} — 生成脚本须自证「怎么跑 + 产物落哪 + 改哪重生」（§三-J），跑 check_generator_docstring.py 复核")

    if any(p.startswith("scripts/lib/") for p in changed):
        gaps.append("改了 scripts/lib/ — 跑 `mypy scripts/lib/`（§六 自检清单）；改签名 / 常量前须全仓 grep 消费者（§三-D）")
    if any(re.fullmatch(r"scripts/[^/]+\.(py|sh)", p) and statuses[p] in ("A", "D") for p in changed):
        gaps.append("根 scripts/ 有增删 — 跑 `python3 scripts/gen_scripts_readme.py`，audit §15 会校验 drift（§三-F）")
    if any(p.startswith(".claude/hooks/") for p in changed):
        gaps.append("改了 hooks — 跑 `bash .claude/hooks/test/test-hooks.sh` 验 exit code 契约（§三-G）")
    if re.search(r"fail_key|FAIL_KEYS", added_lines):
        gaps.append("新增 fail_key / 检查维度 — 须补正例断言证明真能命中，否则形同虚设（§三-K）")
    return gaps


# ────────────────────────── I/O 层 ──────────────────────────

def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if proc.returncode != 0 and proc.stderr.strip():
        sys.stderr.write(f"[git {' '.join(args)}] {proc.stderr.strip()}\n")
    return proc.stdout


def collect_diff(root: Path, staged: bool, rev: str, files: list[str]) -> tuple[dict[str, str], str, str]:
    """返回 ({路径: A/M/D 状态}, diff 全文, 范围说明)。"""
    if files:
        base = ["diff", "--", *files]
        scope = "工作区改动（指定路径）"
    elif staged:
        if not _git(root, "diff", "--cached", "--name-only").strip():
            base = ["diff", "HEAD~1"]
            scope = "暂存区为空 → 自动回落 HEAD~1"
        else:
            base = ["diff", "--cached"]
            scope = "暂存区（git diff --cached）"
    else:
        base = ["diff", rev]
        scope = f"git diff {rev}"

    name_status = _git(root, *base, "--name-status", "--diff-filter=ACMRD")
    statuses: dict[str, str] = {}
    for line in name_status.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            statuses[parts[-1]] = parts[0][0]
    return statuses, _git(root, *base), scope


def find_consumers(root: Path, symbols: list[tuple[str, str]], limit: int = 8) -> dict[str, list[str]]:
    """符号名全仓反查引用（.py + .sh，覆盖 from lib.X / from .X / bash heredoc 三形态）。"""
    out: dict[str, list[str]] = {}
    for defining_file, symbol in symbols:
        raw = _git(root, "grep", "-n", "-w", "--", symbol, "*.py", "*.sh")
        hits = [ln for ln in raw.splitlines() if ln and not ln.startswith(f"{defining_file}:")]
        out[f"{defining_file} :: {symbol}"] = hits[:limit] + (
            [f"…… 另有 {len(hits) - limit} 处"] if len(hits) > limit else []
        )
    return out


def _run(root: Path, cmd: list[str], label: str, timeout: int = 180) -> tuple[str, str, str]:
    """跑一条机械检查，返回 (图标, 标签, 明细)。错误不吞，原样带回。"""
    if not shutil.which(cmd[0]) and cmd[0] != sys.executable:
        return "⚠️", label, f"未跑通：找不到命令 {cmd[0]}"
    try:
        proc = subprocess.run(
            cmd, cwd=root, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "⚠️", label, f"未跑通：超时 {timeout}s"
    if proc.returncode == 0:
        return "✅", label, ""
    return "❌", label, (proc.stdout + proc.stderr).strip()[:2000]


def run_mechanical(root: Path, statuses: dict[str, str]) -> list[tuple[str, str, str]]:
    """只对改动文件跑机械层；全仓项仅保留秒级的 audit 19 当回归信号。"""
    results: list[tuple[str, str, str]] = []
    alive = [p for p in statuses if statuses[p] != "D" and (root / p).is_file()]
    pys = [p for p in alive if p.endswith(".py")]
    shs = [p for p in alive if p.endswith(".sh")]

    if pys:
        results.append(_run(root, [sys.executable, "-m", "ruff", "check", "--select", "F", "--no-cache", *pys],
                            "ruff F 类（含 F401，收尾态该查）"))
    for sh in shs:
        results.append(_run(root, ["bash", "-n", sh], f"bash -n {sh}"))
    if shs and shutil.which("shellcheck"):
        results.append(_run(root, ["shellcheck", "-S", "error", *shs], "shellcheck error 级"))
    elif shs:
        results.append(("⚠️", "shellcheck error 级", "未跑通：未安装 shellcheck"))

    gen = [p for p in alive if PurePosixPath(p).name.startswith(("gen_", "build_"))]
    if gen and (root / "scripts/check_generator_docstring.py").is_file():
        results.append(_run(root, [sys.executable, "scripts/check_generator_docstring.py", *gen],
                            "生成脚本 docstring 自证（§三-J）"))

    audit = root / ".claude/skills/workspace-audit/scripts/audit.sh"
    if (pys or shs) and audit.is_file():
        results.append(_run(root, ["bash", str(audit), "19"], "跨平台兼容 lint（全仓 · 回归信号）"))

    if pys and (root / "scripts/tests").is_dir():
        results.append(_run(root, [sys.executable, "-m", "pytest", "scripts/tests/", "-q"],
                            "pytest scripts/tests/", timeout=300))
    return results


# ────────────────────────── 渲染 ──────────────────────────

def render(scope: str, statuses: dict[str, str], buckets: dict, routes: dict,
           mech: list, consumers: dict, gaps: list[str], skipped_mech: bool = False) -> str:
    L = ["===== code-review Phase 1 =====", f"范围：{scope} · 命中 {len(statuses)} 个文件", ""]

    L.append("--- ① 变更清单 + 规范路由 ---")
    for bucket, files in buckets.items():
        if not files:
            continue
        L.append(f"[{BUCKET_LABEL[bucket]}]")
        for f in files:
            L.append(f"  {statuses.get(f, '?')} {f}")
        for spec in routes.get(bucket, []):
            L.append(f"  → {spec}" if spec.startswith("（") else f"  → 读 {spec}")
        if bucket == "out_of_scope":
            L.append("  → 不审，指向对应 skill（hub/ 走 aihub-package；.md / .html 走产出物 skill）")
    if not statuses:
        L.append("  git 未返回任何改动 —— 先确认范围对不对（路径是否在本仓库内、rev 写对没）。")
        L.append("  这是「取不到」不是「干净」，别当成审过了。")
    elif not any(buckets[b] for b in buckets if b != "out_of_scope"):
        L.append("  本次改动无代码文件，不在 code-review 范围")

    L.append("")
    L.append("--- ② 机械层结果（已有 gate，只汇总不重述）---")
    if skipped_mech:
        L.append("  （--no-mechanical 已跳过，机械层结论缺失，报告第 ② 块须如实声明）")
    elif not mech:
        L.append("  （本次无代码文件，无可跑项）")
    for icon, label, detail in mech:
        L.append(f"  {icon} {label}")
        if detail:
            L.extend(f"      {ln}" for ln in detail.splitlines()[:30])

    L.append("")
    L.append("--- ③ 消费者反查（SCRIPTS_WRITING §三-D）---")
    if not consumers:
        L.append("  无被删 / 被改签名的顶层符号")
    for key, hits in consumers.items():
        L.append(f"  {key}")
        if hits:
            L.extend(f"      {h}" for h in hits)
        else:
            L.append("      零引用（可安全删）")

    L.append("")
    L.append("--- ④ 覆盖缺口 ---")
    if not gaps:
        L.append("  无")
    L.extend(f"  ⚠️ {g}" for g in gaps)
    return "\n".join(L)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  scan_changes.py --staged\n"
               "  scan_changes.py --range HEAD~3\n"
               "  scan_changes.py scripts/<name>.py scripts/lib/<mod>.py\n"
               "  scan_changes.py --staged --json-out -\n",
    )
    parser.add_argument("files", nargs="*", help="要审的文件（仓库相对路径）；给了就审这些文件的工作区 diff")
    parser.add_argument("--staged", action="store_true", help="审暂存区；暂存区为空自动回落 HEAD~1。默认行为")
    parser.add_argument("--range", dest="rev", default="", help="审 git diff <rev>，如 HEAD~3 / main")
    parser.add_argument("--json-out", dest="json_out", default="", help="四段结果写 JSON，'-' 走 stdout")
    parser.add_argument("--no-mechanical", action="store_true", help="跳过第 ② 段机械层（audit / pytest 慢时用），其余段照跑")
    args = parser.parse_args()

    root = find_root()
    staged = args.staged or not (args.files or args.rev)
    statuses, diff, scope = collect_diff(root, staged, args.rev or "HEAD~1", args.files)

    buckets = bucket_files(sorted(statuses))
    routes = route_specs(buckets)
    in_scope = {p: s for p, s in statuses.items() if p not in buckets["out_of_scope"]}
    mech = [] if args.no_mechanical else run_mechanical(root, in_scope)
    # 符号反查限在范围内文件——范围外的 .sh / 产物脚本不归本 skill 审（SKILL.md §硬规则 R5）
    symbols = [(f, s) for f, s in extract_changed_symbols(diff) if f in in_scope]
    consumers = find_consumers(root, symbols)
    added = "\n".join(ln for ln in diff.splitlines() if ln.startswith("+"))
    gaps = coverage_gaps(in_scope, added)

    print(render(scope, statuses, buckets, routes, mech, consumers, gaps, args.no_mechanical))

    if args.json_out:
        payload = {
            "scope": scope, "statuses": statuses, "buckets": buckets, "routes": routes,
            "mechanical": [{"icon": i, "label": lb, "detail": d} for i, lb, d in mech],
            "consumers": consumers, "gaps": gaps,
        }
        blob = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json_out == "-":
            print(blob)
        else:
            Path(args.json_out).write_text(blob, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
