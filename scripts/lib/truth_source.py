"""产品线真相源统一解析器。

工具层（check_paradigm / gen_weekly_all / cross-check 等）只认这一个接口，
不再各自判真相源存在性、各自解析章节。产品线真相统一在 baseline；
迭代容器（biweekly 等）走 EXEMPT_LINES，工具层不解析。

真相源形态：
  - baseline：产品线根 `projects/{line}/prd-{line}-baseline.md`（living 全量真相）

用法：
    from lib.truth_source import resolve, involved_ends, current_deltas
    ts = resolve("livestream", projects_dir)  # → TruthSource(kind="baseline", ...)
    ends = involved_ends(ts)          # → {"app", "web-frontend", "web-backend"}
    deltas = current_deltas(ts)       # → [{"version","source","status","rows","phase"}, ...]
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# biweekly = 双周迭代协调容器，既非 baseline 也非项目业务真相，工具层豁免。
EXEMPT_LINES = {"biweekly", "sensors-metrics"}


@dataclass
class TruthSource:
    project: str           # 入参原值（"livestream" / "community/base"）
    line: str              # 产品线根（路径首段）
    kind: str | None       # "baseline" / "exempt" / None
    path: Path | None      # 真相源文件路径
    line_root: Path | None  # 产品线根目录（baseline / deliverables 挂这里）


def resolve(project: str, projects_dir: Path) -> TruthSource:
    """给项目名返回真相源。project 可为产品线名或 产品线/子项目。

    kind 取值：baseline / exempt（biweekly 等迭代容器）/ None（无真相源）。
    """
    line = project.split("/")[0]
    line_root = projects_dir / line
    if line in EXEMPT_LINES:
        return TruthSource(project, line, "exempt", None, line_root)
    baseline = line_root / f"prd-{line}-baseline.md"
    if baseline.exists():
        return TruthSource(project, line, "baseline", baseline, line_root)
    return TruthSource(project, line, None, None, line_root)


# ── 涉及端推断（check_paradigm 用） ──────────────────────

def _ends_from_keywords(text: str) -> set:
    """从自由文本关键词推断端类型集合（baseline §1 涉及端行 / 全文关键词通用）。"""
    ends = set()
    if any(k in text for k in ("App 端", "客户端", "iOS", "Android", "移动端", "前台 App", "App 原生", "App 内嵌")):
        ends.add("app")
    if any(k in text for k in ("Web 前台", "PC 前台", "网页前台", "H5", "Web 主播工作台", "Web 工作台")):
        ends.add("web-frontend")
    if any(k in text for k in ("后台", "管理端", "CMS", "后台管理", "运营端")):
        ends.add("web-backend")
    return ends


_INVOLVED_ENDS_RE = re.compile(r"^[-*]\s*\*\*涉及端\*\*[:：]\s*(.+)$", re.MULTILINE)


def involved_ends(ts: TruthSource) -> set:
    """推断涉及端。baseline 优先读 §1「涉及端」行，否则全文关键词。"""
    if ts.path is None:
        return set()
    text = ts.path.read_text(encoding="utf-8")
    if ts.kind == "baseline":
        m = _INVOLVED_ENDS_RE.search(text)
        if m:
            return _ends_from_keywords(m.group(1))
    return _ends_from_keywords(text)


# ── 排期解析（data-report 周报业务上下文用） ─────────────
# 统一 5 列表：阶段 | 起止 | 进度 | 状态 | 影响指标。
# 容忍 H1/H2 + 可选数字前缀：delta `# 8. 排期 / 上线节奏`，其下可有 `## 8.1` 子节。
_SCHEDULE_HEADER_RE = re.compile(
    r"^(#{1,2})\s+(?:\d+\.\s*)?排期\s*/\s*上线节奏\s*$", re.MULTILINE
)
_PHASE_NOTE_RE = re.compile(r"^>\s*当前\s*Phase[:：]\s*(.+?)$", re.MULTILINE)
# delta 头部元信息表：| PRD 版本 | 2.4 | 状态 | 待评审 |
_HEADER_STATUS_RE = re.compile(
    r"^\|\s*PRD 版本\s*\|[^|]*\|\s*状态\s*\|\s*([^|]+?)\s*\|", re.MULTILINE
)
_QUARTER_DIR_RE = re.compile(r"^\d{4}Q[1-4]$")


def _extract_schedule_section(text: str) -> str | None:
    """取排期章正文，截到下一个同级或更高级标题（子节 `## 8.1` 归入本章）。"""
    m = _SCHEDULE_HEADER_RE.search(text)
    if not m:
        return None
    level = len(m.group(1))
    nxt = re.compile(rf"^#{{1,{level}}}\s+", re.MULTILINE).search(text, m.end())
    return text[m.end():(nxt.start() if nxt else len(text))]


def _parse_schedule_rows(section: str) -> list[dict]:
    """解析表头首列为「阶段」的那张 5 列排期表；同章其他表（需求清单 / 验收表）不收。"""
    rows: list[dict] = []
    in_table = False
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            if in_table:
                break
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if not in_table:
            in_table = len(cells) >= 5 and cells[0] == "阶段"
            continue
        if cells[0].startswith((":--", "---")):
            continue
        rows.append({
            "stage": cells[0], "range": cells[1], "progress": cells[2],
            "status": cells[3], "impact": cells[4],
        })
    return rows


def _version_key(version: str) -> tuple:
    """版本号按数值排序：2.10 排在 2.9 之后。"""
    return tuple(int(x) if x.isdigit() else -1 for x in re.split(r"[.\-]", version))


def current_deltas(ts: TruthSource) -> list[dict]:
    """最新季度目录下每个版本 delta 的排期信息，按版本号升序。

    只认主 delta（`{季度}/{版本}/prd-{line}-{版本}.md`），附属文件（如 lexicon-seed）不算。
    返回 [{"version", "source", "status"（PRD 头部状态，占位符视为空）, "rows", "phase"}]。
    """
    if ts.line_root is None:
        return []
    deliv = ts.line_root / "deliverables"
    if not deliv.exists():
        return []
    quarters = sorted(d for d in deliv.iterdir() if d.is_dir() and _QUARTER_DIR_RE.match(d.name))
    if not quarters:
        return []
    out = []
    for vdir in quarters[-1].iterdir():
        delta = vdir / f"prd-{ts.line}-{vdir.name}.md"
        if not delta.is_file():
            continue
        text = delta.read_text(encoding="utf-8")
        sec = _extract_schedule_section(text) or ""
        st = _HEADER_STATUS_RE.search(text)
        status = st.group(1).strip() if st else ""
        if status.startswith("{{"):
            status = ""
        ph = _PHASE_NOTE_RE.search(sec)
        out.append({
            "version": vdir.name,
            "source": delta.name,
            "status": status,
            "rows": _parse_schedule_rows(sec),
            "phase": ph.group(1).strip() if ph else "",
        })
    return sorted(out, key=lambda e: _version_key(e["version"]))
