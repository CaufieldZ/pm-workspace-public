#!/usr/bin/env python3
"""baseline PRD 新鲜度校验（文档集模型承重不变量的 definition-of-done）。

三层校验：

第一层 · 流程新鲜度（机械可算，红灯）：
  已上线的 delta PRD，其 changelog 行必须存在**且状态 = 已合并**。
  - 缺行 ⇒ delta 已上线但没登记进 baseline changelog（漏登记）。
  - 状态 = 已登记 ⇒ 登记了但没反向合并（最易腐烂的窗口）。
  两者都报「baseline stale」。这是修正后的判据：不只验登记，验合并完成。

第二层 · 内容新鲜度（机械验不了，黄灯不卡）：
  baseline 各模块章头的「最后核对线上: 日期 / 人」超期（默认 60d）→ 提醒。
  按模块章精确报，不是整份一个日期。

第三层 · 合并痕迹（机械可算，红灯）：
  状态 = 已合并的 delta，其 §3 业务对象增量 / §4 状态机增量的具名实体
  必须真出现在 baseline 对应支柱章里——否则「已合并」是空声明（整段漏搬）。
  边界：只验整段漏搬（实体核心词是否出现），不验逐字合并对不对——反向合并
  会重写措辞，逐字比对必然误报。§5 全局规则增量是自由 bullet 无具名 key，不验。
  SKIP_MERGE_TRACE=1 整体跳过本层（实体确实改名 / 措辞对不上的 false positive 兜底）。

用法：
    python3 scripts/check_baseline_fresh.py livestream
    python3 scripts/check_baseline_fresh.py livestream --stale-days 90

退出码：恒 0（warn 级，供 hook / dashboard 调）。结构化结论走 stdout。
非 baseline 项目（无 prd-*-baseline.md）→ 直接 skip。
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.repo import find_root  # noqa: E402

# ── baseline 定位 ────────────────────────────────────────────────────────

def _find_baseline(project_dir: Path) -> Path | None:
    """产品线根下的 prd-*-baseline.md（约定一份）。"""
    hits = sorted(project_dir.glob("prd-*-baseline.md"))
    return hits[0] if hits else None


# ── changelog 解析 ───────────────────────────────────────────────────────

# 变更记录表行：| 日期 | 触及模块 | delta PRD | 状态 |
_CHANGELOG_ROW = re.compile(
    r"^\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$"
)
# delta 文件名（从链接列里抠出 prd-xxx.md）
_DELTA_FILE = re.compile(r"(prd-[\w.\-]+\.md)")


def parse_changelog(baseline_text: str) -> dict[str, str]:
    """返回 {delta_filename: 状态}。只取「变更记录」章内的表行。

    同一文件名出现多行且状态不一致时，不静默覆盖（旧实现后者覆盖前者会
    让「已合并」掩盖「未合并」→ stale 漏报），改记为「状态冲突（…/…）」。
    该态 ≠「已合并」，下游 stale 校验必报，交人工核对。
    """
    result: dict[str, str] = {}
    in_changelog = False
    chapter_level = 0
    for line in baseline_text.splitlines():
        # 任意层级 heading（# / ## / ###，带或不带编号）都可能是变更记录章
        hm = re.match(r"^(#{1,4})\s", line)
        if hm:
            level = len(hm.group(1))
            if "变更记录" in line or "变更日志" in line or "迭代记录" in line:
                in_changelog, chapter_level = True, level
            elif in_changelog and level <= chapter_level:
                in_changelog = False  # 同级/更高级标题才算出章
            # 章内更深的子标题（如「变更记录」下的 ### 说明）不打断表行解析
            continue
        if not in_changelog:
            continue
        m = _CHANGELOG_ROW.match(line)
        if not m:
            continue
        _d, _mod, delta_col, status = m.groups()
        if delta_col.strip() in ("delta PRD", "---") or status.strip() in ("状态", "---"):
            continue
        fm = _DELTA_FILE.search(delta_col)
        if not fm:
            continue
        name, st = fm.group(1), status.strip()
        prev = result.get(name)
        if prev is not None and prev != st and not prev.startswith("状态冲突"):
            result[name] = f"状态冲突（{prev}/{st}）"
        elif prev is None or not prev.startswith("状态冲突"):
            result[name] = st
    return result


# ── delta 状态解析 ───────────────────────────────────────────────────────

# delta 头部「状态：已上线」/「**状态**：已上线（2026-07-XX）」
_DELTA_STATUS = re.compile(r"状态\s*[\*）)]*\s*[:：]\s*\**\s*([^\n（(]+)")


def delta_is_live(delta_text: str) -> bool:
    m = _DELTA_STATUS.search(delta_text)
    if not m:
        return False
    return "已上线" in m.group(1)


# delta 头部「火效」字段（工作项链接，产研效能上线日期/状态唯一权威源）
_HX_FIELD = re.compile(r"^[\s\-*]*\**\s*火效\s*\**\s*[:：]\s*(.+?)\s*$", re.MULTILINE)


def delta_in_flight(delta_path: Path, changelog: dict[str, str], archive_dir: Path) -> bool:
    """delta 是否在途：changelog 状态 ≠「已合并」且不在 archive/ 下。

    第四层（火效链接）只该管在途的 —— 给已合并 / 已归档的历史 delta 补火效链接没有
    意义，全量扫会把命中率抬到被整体忽略，连带盖掉真该补的在途项。
    """
    return changelog.get(delta_path.name) != "已合并" and archive_dir not in delta_path.parents


def delta_hx_link_missing(delta_text: str) -> bool:
    """delta 头部无「火效」字段 / 字段为占位符（含 <work_id>）→ True。"""
    m = _HX_FIELD.search(delta_text)
    if not m:
        return True
    val = m.group(1)
    return "<" in val and ">" in val


# ── 模块章时效解析 ───────────────────────────────────────────────────────

# 模块章标题用 H1 带编号（# 7. 连麦模块）或 H2（## 连麦模块），都以「模块」结尾
_MODULE_HEADING = re.compile(r"^#{1,2}\s+(?:\d+\.\s*)?(.+?)\s*$")
_LAST_CHECK = re.compile(r"最后核对线上[\*）)]*\s*[:：]\s*\**\s*(\d{4}-\d{2}-\d{2})")
# 未上线模块（状态：未上线 / 待排期）不该核对线上，第二层跳过
_NOT_LIVE = re.compile(r"状态[\*）)]*\s*[:：]?\s*\**\s*(未上线|待排期|规划中)")


def parse_module_freshness(baseline_text: str) -> list[tuple[str, date | None, str]]:
    """返回 [(模块章标题, 核对日期 or None, 原始日期串), ...]。

    扫每个模块章（H1 带编号或 H2，以「模块」结尾）内的「最后核对线上」日期。
    标注「状态：未上线 / 待排期 / 规划中」的模块章跳过（未上线无线上可核对）。
    """
    def _is_module_ch(title: str) -> bool:
        # 模块章标题以「模块」结尾（如「连麦模块」），排除「模块树」这类索引章
        return title.rstrip().endswith("模块")

    out: list[tuple[str, date | None, str]] = []
    cur_title: str | None = None
    cur_found = False
    cur_not_live = False

    def _flush():
        if cur_title and not cur_found and not cur_not_live and _is_module_ch(cur_title):
            out.append((cur_title, None, ""))

    for line in baseline_text.splitlines():
        hm = _MODULE_HEADING.match(line)
        if hm:
            _flush()
            cur_title = hm.group(1).strip()
            cur_found = False
            cur_not_live = False
            continue
        if cur_title and _is_module_ch(cur_title):
            if _NOT_LIVE.search(line):
                cur_not_live = True
                continue
            if not cur_found and not cur_not_live:
                cm = _LAST_CHECK.search(line)
                if cm:
                    raw = cm.group(1)
                    try:
                        d = datetime.strptime(raw, "%Y-%m-%d").date()
                    except ValueError:
                        d = None
                    out.append((cur_title, d, raw))
                    cur_found = True
    _flush()
    return out


# ── 合并痕迹解析（第三层）─────────────────────────────────────────────────

# delta 增量章 H1：「# 3. 业务对象增量」/「# 4. 状态机增量」
_DELTA_PILLAR_CH = {
    "业务对象": re.compile(r"^#\s+\d+\.\s*业务对象增量"),
    "状态机": re.compile(r"^#\s+\d+\.\s*状态机增量"),
}
# 增量章下的具名小节「## 3.1 订阅关系（…）」→ 取核心词「订阅关系」
_DELTA_SUBSEC = re.compile(r"^##\s+\d+\.\d+\s+(.+?)\s*$")
# baseline 支柱章标题关键词（取章正文做子串命中）
_BASELINE_PILLAR_KW = {"业务对象": "业务对象", "状态机": "状态机"}


def _entity_core(title: str) -> str:
    """小节标题去括号 / 空格 / 间隔号后的核心词。

    「订阅关系（社区只读…）」→「订阅关系」；「订阅状态机」→「订阅状态机」。
    """
    for sep in ("（", "(", " ", "\t", "·"):
        idx = title.find(sep)
        if idx > 0:
            title = title[:idx]
    return title.strip()


def parse_delta_pillar_entities(delta_text: str) -> dict[str, list[str]]:
    """返回 {"业务对象": [实体核心词...], "状态机": [...]}。

    扫 delta §3 业务对象增量 / §4 状态机增量章下的 `## X.Y` 小节标题，取核心词。
    §5 全局规则增量不收（自由 bullet，无具名 key 机械验不了）。
    """
    out: dict[str, list[str]] = {"业务对象": [], "状态机": []}
    cur_kind: str | None = None
    for line in delta_text.splitlines():
        if re.match(r"^#\s", line):  # 任一 H1 章切换：先判是否落在目标章
            cur_kind = None
            for kind, pat in _DELTA_PILLAR_CH.items():
                if pat.match(line):
                    cur_kind = kind
                    break
            continue
        if cur_kind is None:
            continue
        sm = _DELTA_SUBSEC.match(line)
        if sm:
            core = _entity_core(sm.group(1))
            if core:
                out[cur_kind].append(core)
    return out


def baseline_pillar_text(baseline_text: str, kind: str) -> str:
    """取 baseline 对应支柱章正文（标题含关键词的章，切到下一同级 heading 前）。

    取不到（baseline 标题措辞偏离关键词）→ 返回空串，调用方降级为静默不误报。
    """
    kw = _BASELINE_PILLAR_KW[kind]
    lines = baseline_text.splitlines()
    start = None
    start_level = 0
    for i, line in enumerate(lines):
        hm = re.match(r"^(#{1,4})\s+(.*)$", line)
        if hm and kw in hm.group(2):
            start = i + 1
            start_level = len(hm.group(1))
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start, len(lines)):
        hm = re.match(r"^(#{1,4})\s", lines[j])
        if hm and len(hm.group(1)) <= start_level:
            end = j
            break
    return "\n".join(lines[start:end])


# ── 主校验 ───────────────────────────────────────────────────────────────

def check(project: str, repo_root: Path, stale_days: int) -> int:
    project_dir = repo_root / "projects" / project
    if not project_dir.is_dir():
        print(f"⚠ 项目目录不存在：{project_dir}")
        return 0

    baseline = _find_baseline(project_dir)
    if baseline is None:
        print(f"· {project}：非 baseline 项目（无 prd-*-baseline.md），skip")
        return 0

    baseline_text = baseline.read_text(encoding="utf-8")
    changelog = parse_changelog(baseline_text)

    # 扫所有 delta（deliverables/ + archive/）
    deliverables = project_dir / "deliverables"
    delta_files: list[Path] = []
    if deliverables.is_dir():
        archive = deliverables / "archive"
        # 递归收 delta（季度目录 deliverables/{季度}/{版本}/prd-*.md），排除 baseline 名与 archive/
        delta_files += [
            p for p in deliverables.rglob("prd-*.md")
            if "baseline" not in p.name
            and archive not in p.parents
        ]
        if archive.is_dir():
            delta_files += [
                p for p in archive.rglob("prd-*.md")
                if "baseline" not in p.name
            ]

    # ── 第一层：已上线 delta 必须在 changelog 且状态=已合并 ──
    # ── 第四层：delta 必绑火效链接（离线可验证，warn 不拦）──
    stale: list[str] = []
    hx_missing: list[str] = []
    archive_dir = project_dir / "deliverables" / "archive"
    for dp in delta_files:
        text = dp.read_text(encoding="utf-8")
        if delta_in_flight(dp, changelog, archive_dir) and delta_hx_link_missing(text):
            hx_missing.append(f"  · {dp.name} 头部无「火效」字段或为占位符——跑 sync_hx_status.py 前先补火效工作项链接")
        if not delta_is_live(text):
            continue
        status = changelog.get(dp.name)
        if status is None:
            stale.append(f"  ❌ {dp.name} 已上线，但 baseline changelog 无对应行（漏登记）")
        elif status != "已合并":
            stale.append(f"  ❌ {dp.name} 已上线，changelog 状态=「{status}」未推进到「已合并」（登记了没反向合并）")

    # ── 第三层：合并痕迹（状态=已合并的 delta，增量实体须真落进 baseline）──
    merge_gap: list[str] = []
    if not os.environ.get("SKIP_MERGE_TRACE"):
        for dp in delta_files:
            if changelog.get(dp.name) != "已合并":
                continue
            entities = parse_delta_pillar_entities(dp.read_text(encoding="utf-8"))
            for kind, names in entities.items():
                if not names:
                    continue
                pillar = baseline_pillar_text(baseline_text, kind)
                if not pillar:
                    continue  # baseline 标题措辞对不上 → 静默降级，不误报
                for name in names:
                    if name not in pillar:
                        merge_gap.append(
                            f"  ❌ {dp.name} 标记已合并，但 baseline {kind}章找不到"
                            f"「{name}」（疑似整段漏搬；§5 自由规则不校验）"
                        )

    # ── 第二层：模块章时效 ──
    today = date.today()
    overdue: list[str] = []
    no_date: list[str] = []
    for title, d, raw in parse_module_freshness(baseline_text):
        if d is None:
            no_date.append(f"  · {title}：无「最后核对线上」日期")
            continue
        age = (today - d).days
        if age > stale_days:
            overdue.append(f"  · {title}：最后核对 {raw}（{age} 天前 > {stale_days}d）")

    # ── 报告 ──
    print(f"baseline: {baseline.relative_to(repo_root)}")
    print(f"changelog 行: {len(changelog)} 条 / delta 文件: {len(delta_files)} 个")

    if stale:
        print(f"\n🔴 第一层 · 流程新鲜度 STALE（{len(stale)}）—— 上线未反向合并，必须修：")
        for s in stale:
            print(s)
    else:
        print("\n🟢 第一层 · 流程新鲜度：所有已上线 delta 均已合并")

    if merge_gap:
        print(f"\n🔴 第三层 · 合并痕迹 GAP（{len(merge_gap)}）—— 标已合并但 baseline 找不到，必须修：")
        for s in merge_gap:
            print(s)
    elif not os.environ.get("SKIP_MERGE_TRACE"):
        print("🟢 第三层 · 合并痕迹：所有已合并 delta 的增量实体均落进 baseline")

    if overdue:
        print(f"\n🟡 第二层 · 内容新鲜度过期（{len(overdue)}，提醒不卡）：")
        for s in overdue:
            print(s)
    if no_date:
        print(f"\n🟡 第二层 · 模块章缺核对日期（{len(no_date)}）：")
        for s in no_date:
            print(s)
    if not overdue and not no_date:
        print("🟢 第二层 · 内容新鲜度：所有模块章核对日期在期内")

    if hx_missing:
        print(f"\n🟡 第四层 · 火效链接缺失（{len(hx_missing)}，提醒不卡）——火效是上线日期/状态唯一权威源：")
        for s in hx_missing:
            print(s)
    else:
        print("🟢 第四层 · 火效链接：所有 delta 均已绑定火效工作项")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="baseline PRD 新鲜度校验")
    ap.add_argument("project", help="项目 / 产品线路径片段，如 livestream")
    ap.add_argument("--stale-days", type=int, default=60, help="模块章内容新鲜度过期阈值（天），默认 60（阈值登记: thresholds.yaml §E baseline.stale_days）")
    args = ap.parse_args()
    repo_root = find_root()
    return check(args.project, repo_root, args.stale_days)


if __name__ == "__main__":
    sys.exit(main())
