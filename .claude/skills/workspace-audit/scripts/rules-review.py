#!/usr/bin/env python3
"""
rules-review.py — 季度规则瘦身 review 工具

定位：不进 audit.sh 默认 Cat，3-6 月手动跑一次或重大模型升级后跑。
读 CLAUDE.md / .claude/runbooks/*.md / .claude/skills/*/SKILL.md 提取规则条款，
聚合 .claude/logs/usage.jsonl 的 hook 触发统计，输出 md 报告供人工 review。

用法：
    python3 .claude/skills/workspace-audit/scripts/rules-review.py --model sonnet-4.7
    python3 .../rules-review.py --model sonnet-4.7 --dry-run   # 只打印不写文件
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # pm-workspace 根
LOG_FILE = ROOT / ".claude" / "logs" / "usage.jsonl"
HOOK_DIR = ROOT / ".claude" / "hooks"
OUT_DIR = ROOT / "deliverables"

RULE_SOURCES = [
    ROOT / "CLAUDE.md",
    *sorted((ROOT / ".claude" / "runbooks").glob("*.md")),
    *sorted((ROOT / ".claude" / "output-styles").glob("*.md")),
    *sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")),
]

RULE_PATTERNS = [
    re.compile(r"\[强制\]|（强制）|· hook 兜底|强制\s*·|强制\s*）"),
    re.compile(r"^\s*[-*]\s*\*\*?(禁|必须|不要|不能|禁止|必读|只|默认|永远|从不)"),
    re.compile(r"^\s*[-*]\s*(禁|必须|不要|不能|禁止|必读)[^a-zA-Z]"),
    re.compile(r"\*\*(禁|禁用|必须|必读|不要|不能|禁止)\*\*"),
    re.compile(r"红线|铁律|硬约束|四不|四禁|硬底线|绝不|绝对不"),
    re.compile(r"^\s*[-*]\s*\*\*"),  # 任何 bullet 起首带粗体（多半是规则项）
]

# 中文关键词 → log 中实际的 hook name 映射
HOOK_CN_ALIASES = {
    "cjk-punct": ["中文标点", "全角", "CJK", "标点"],
    "plain-language-gate": ["白话", "AI slop", "禁词", "锚点", "讲人话"],
    "pm-visual-gate": ["UI 视觉", "视觉超界", "px ", "hex", "PM 走查", "样式"],
    "deliverable-source-gate": ["只改源", "改源不改产物", "脚本生成", "产出物只改源"],
    "context-static-lint": ["静态章", "四不", "四禁"],
    "risky-op": ["高风险", "Playwright", "render 大文件"],
    "scripts-first": ["脚本优先", "frontmatter scripts", "不手写等效"],
    "skill-load-gate": ["skill 加载", "已 in_progress"],
    "prototype-paradigm-gate": ["paradigm", "原型范式"],
    "prd-check-gate": ["PRD 自检", "check_prd_md"],
    "prototype-audit": ["prototype 自检", "原型审计"],
    "audit-fast": ["快速审计"],
}

CATEGORY_KEYWORDS = [
    ("模型补丁", [
        "自动修复", "静默跳过", "自检反压", "不要假装", "不要遗漏", "不要重复",
        "不要散文化", "不要发明", "禁止静默", "失败.*停", "反 AI slop", "AI slop",
        "兜底", "验证", "证据", "回读", "防腐", "防退化", "幻觉",
        "70%", "PR-FAQ", "Working Backwards", "未覆盖问题停下",
    ]),
    ("防腐-hook", [
        "hook 兜底", "hook 强阻断", "强阻断", "pre-commit", "post-",
        "hook 触发", "hook 检测", "SKIP_", "Escape hatch",
    ]),
    ("Voice", [
        "不写", "禁词", "锚点", "白话", "Voice", "话术", "讲人话",
        "圈数字", "句式", "标点",
    ]),
    ("视觉", [
        "px ", "hex", "字体", "设备", "tokens.css", "@audit-spec",
        "深色板", "浅色板", "双主题", "颜色", "CSS",
    ]),
    ("流程", [
        "Step ", "触发", "链路", "depends_on", "pipeline", "SKILL.md",
        "frontmatter", "Skill 路径", "命名前缀", "并行 Read",
    ]),
    ("数据/格式", [
        "json", "yaml", "schema", "模块树", "Decision Log", "Changelog",
        "RFC", "baseline", "session-state",
    ]),
]


# 占位标题：「**必读**（产出前加载）：」/「**XX 模式**（默认）」等纯说明，非规则
PLACEHOLDER_RE = re.compile(
    r"^\s*[-*]?\s*\*\*?(必读|可选|说明|示例|参考|备注|前置|后置)\*\*?[（(].*?[）)].*[:：]\s*$"
)

# 组件清单 bullet：「**name** — 描述」起首的 bullet。单独一行不报，
# 但若连续 ≥ COMPONENT_LIST_THRESHOLD 个相邻行同模式，整段判定为组件清单，全部跳过
COMPONENT_BULLET_RE = re.compile(
    r"^\s*[-*]\s*\*\*[a-zA-Z][\w/\-*\\]*\*\*\s*[—\-]"
)
COMPONENT_LIST_THRESHOLD = 5


def _detect_component_blocks(lines):
    """返回需跳过的行号集合（组件清单段）。"""
    skip = set()
    run_start = None
    run_count = 0
    for i, line in enumerate(lines, 1):
        if COMPONENT_BULLET_RE.match(line):
            if run_start is None:
                run_start = i
            run_count += 1
        else:
            if run_count >= COMPONENT_LIST_THRESHOLD:
                for j in range(run_start, run_start + run_count):
                    skip.add(j)
            run_start = None
            run_count = 0
    # tail flush
    if run_count >= COMPONENT_LIST_THRESHOLD:
        for j in range(run_start, run_start + run_count):
            skip.add(j)
    return skip


def extract_rules(path):
    """从 md 文件提取规则条款。返回 List[dict]。"""
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    lines = text.split("\n")
    skip_lines = _detect_component_blocks(lines)
    rules = []
    in_code = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if i in skip_lines:
            continue
        if PLACEHOLDER_RE.match(line):
            continue
        matched = False
        for pat in RULE_PATTERNS:
            if pat.search(line):
                matched = True
                break
        if not matched:
            continue
        text_clean = re.sub(r"\s+", " ", stripped).strip()
        text_clean = re.sub(r"^[-*]\s*", "", text_clean)
        if len(text_clean) < 8:
            continue
        rules.append({
            "source": str(path.relative_to(ROOT)),
            "line": i,
            "raw": text_clean,
            "text": text_clean[:80] + ("…" if len(text_clean) > 80 else ""),
        })
    return rules


def classify_rule(raw):
    """启发式分类。返回 category 名。"""
    for cat, kws in CATEGORY_KEYWORDS:
        for kw in kws:
            if kw in raw:
                return cat
    return "其他"


def parse_usage_log(path):
    """聚合 hook/gate 触发次数到 30d/60d/90d 三档。返回 Dict[name, {d30, d60, d90}]。"""
    if not path.exists():
        return {}
    now = datetime.now(timezone.utc)
    cutoffs = {"d30": now - timedelta(days=30),
               "d60": now - timedelta(days=60),
               "d90": now - timedelta(days=90)}
    stats = defaultdict(lambda: {"d30": 0, "d60": 0, "d90": 0})
    parse_fail = 0
    ts_fail = 0
    with path.open() as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                parse_fail += 1
                continue
            if d.get("type") not in ("hook", "gate"):
                continue
            action = d.get("action", "")
            if action not in ("triggered", "warn", "block"):
                continue
            ts_str = d.get("ts", "")
            try:
                ts = datetime.fromisoformat(ts_str)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                ts_fail += 1
                continue
            name = d.get("name", "?")
            for window, cutoff in cutoffs.items():
                if ts >= cutoff:
                    stats[name][window] += 1
    if parse_fail:
        print(f"⚠️  usage.jsonl 解析跳过 {parse_fail} 行", file=sys.stderr)
    if ts_fail:
        print(f"⚠️  usage.jsonl 时间戳解析跳过 {ts_fail} 行", file=sys.stderr)
    return dict(stats)


def collect_hook_names():
    """提取 .claude/hooks/*.sh 文件名词根。如 post-cjk-punct-check.sh → cjk-punct, check."""
    if not HOOK_DIR.exists():
        return []
    roots = set()
    for f in HOOK_DIR.glob("*.sh"):
        stem = f.stem
        stem = re.sub(r"^(post|pre|stop|session|user)-?", "", stem)
        stem = re.sub(r"-(check|gate|hook|refresh|capture|warn|log)$", "", stem)
        for token in stem.split("-"):
            if len(token) >= 3:
                roots.add(token)
        roots.add(stem)
    return sorted(roots)


def associate_to_hook(rule_text, hook_roots, log_names):
    """启发式把规则关联到 hook。返回匹配的 hook 名（log 里的）或 None。"""
    text_lower = rule_text.lower()
    # 1. 中文别名匹配（最高优先级，规则文本多为中文）
    for hook_name, aliases in HOOK_CN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in text_lower:
                return hook_name
    # 2. log_names（usage.jsonl 实际出现的 name）直接匹配
    for name in sorted(log_names, key=lambda x: -len(x)):
        if len(name) < 4:
            continue
        if name.lower() in text_lower:
            return name
    # 3. hook 文件名词根兜底
    for root in sorted(hook_roots, key=lambda x: -len(x)):
        if len(root) < 4:
            continue
        if root.lower() in text_lower:
            return root
    return None


def render_md(rules, hook_stats, model, source_groups):
    """渲染 md 报告。"""
    today = datetime.now().strftime("%Y-%m-%d")
    total = len(rules)
    cat_counts = defaultdict(int)
    desc_only = 0
    for r in rules:
        cat_counts[r["category"]] += 1
        if not r["hook"]:
            desc_only += 1

    zero_90d = [name for name, s in hook_stats.items() if s["d90"] == 0]

    lines = []
    lines.append(f"# 规则瘦身 Review · {today}")
    lines.append("")
    lines.append(f"- **当前模型**：{model}")
    lines.append(f"- **总规则数**：{total}")
    lines.append(f"- **分类计数**：{dict(cat_counts)}")
    lines.append(f"- **仅描述性（无 hook 兜底）**：{desc_only} 条")
    lines.append(f"- **0 触发 hook（90d 内，含未在 log 出现）**：{len(zero_90d)} 个")
    if zero_90d:
        lines.append(f"  - {', '.join(sorted(zero_90d))}")
    lines.append("")
    lines.append("## 摘要：优先关注的候选")
    lines.append("")
    model_patch = [r for r in rules if r["category"] == "模型补丁"]
    model_patch_zero = [r for r in model_patch
                        if not r["hook"] or hook_stats.get(r["hook"], {}).get("d90", 0) == 0]
    lines.append(f"- 「模型补丁」分类 + 0 触发 90d → **{len(model_patch_zero)} 条**（最高优先 review）")
    lines.append(f"- 「仅描述性」标记（无 hook 兜底）→ **{desc_only} 条**（删除成本低，但要确认模型自觉遵守）")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 主表（按 source 分组）")
    lines.append("")

    for source, group_rules in source_groups.items():
        if not group_rules:
            continue
        lines.append(f"### {source}")
        lines.append("")
        lines.append("| 规则 | 行 | 分类 | hook 兜底 | hit (30/60/90d) | 候选评估 |")
        lines.append("|------|----|------|----------|----------------|---------|")
        for r in group_rules:
            hook = r["hook"] or "—"
            if r["hook"] and r["hook"] in hook_stats:
                s = hook_stats[r["hook"]]
                hit = f"{s['d30']}/{s['d60']}/{s['d90']}"
            elif r["hook"]:
                hit = "0/0/0"
            else:
                hit = "—"
            safe_text = r["text"].replace("|", "\\|")
            lines.append(f"| {safe_text} | {r['line']} | {r['category']} | {hook} | {hit} |  |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 人工 review 流程")
    lines.append("")
    lines.append("1. 先看「模型补丁」分类（文章原话：补偿旧模型局限的规则，新模型不需要）")
    lines.append("2. 其次看 90d 0 触发 hook 对应规则（数据稀疏 ≠ 该删，但是问题信号）")
    lines.append("3. 逐条填「候选评估」列：保留 / 简化 / 删除 + 理由")
    lines.append("4. 单独 commit 收尾，commit message 引用本 review 文件")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="季度规则瘦身 review 工具")
    parser.add_argument("--model", required=True, help="当前模型版本，如 sonnet-4.7")
    parser.add_argument("--dry-run", action="store_true",
                        help="只打印统计不写文件")
    args = parser.parse_args()

    # Step 1: 扫描规则
    all_rules = []
    source_groups = {}
    for path in RULE_SOURCES:
        rules = extract_rules(path)
        if rules:
            source_groups[str(path.relative_to(ROOT))] = rules
            all_rules.extend(rules)

    # Step 2: hook 统计
    hook_stats = parse_usage_log(LOG_FILE)
    log_names = list(hook_stats.keys())
    hook_roots = collect_hook_names()

    # Step 3: 关联 + 分类
    for r in all_rules:
        r["category"] = classify_rule(r["raw"])
        r["hook"] = associate_to_hook(r["raw"], hook_roots, log_names)

    # Step 4: 统计快报
    cat_counts = defaultdict(int)
    for r in all_rules:
        cat_counts[r["category"]] += 1
    hook_associated = sum(1 for r in all_rules if r["hook"])
    assoc_rate = hook_associated / len(all_rules) * 100 if all_rules else 0

    print("📊 规则扫描完成")
    print(f"   规则总数：{len(all_rules)}")
    print(f"   分类分布：{dict(cat_counts)}")
    print(f"   hook 关联率：{assoc_rate:.1f}%（{hook_associated}/{len(all_rules)}）")
    print(f"   hook 触发记录覆盖：{len(hook_stats)} 个 hook name 出现在 log 内")

    if args.dry_run:
        print("\n💡 --dry-run 模式，不写文件。前 5 条规则预览：")
        for r in all_rules[:5]:
            print(f"   [{r['category']}] {r['source']}:{r['line']} → {r['text']}")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"rules-review-{datetime.now().strftime('%Y-%m-%d')}.md"
    out_file.write_text(render_md(all_rules, hook_stats, args.model, source_groups),
                        encoding="utf-8")
    print(f"\n✅ 报告已写入：{out_file.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
