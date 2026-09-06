"""产品线真相源统一解析器。

工具层（check_paradigm / gen_weekly_all / cross-check 等）只认这一个接口，
不再各自判真相源存在性、各自解析章节。产品线真相统一在 baseline；
迭代容器（biweekly 等）走 EXEMPT_LINES，工具层不解析。

真相源形态：
  - baseline：产品线根 `projects/{line}/prd-{line}-baseline.md`（living 全量真相）

用法：
    from lib.truth_source import resolve, involved_ends, schedule_rows
    ts = resolve("livestream", projects_dir)  # → TruthSource(kind="baseline", ...)
    ends = involved_ends(ts)          # → {"app", "web-frontend", "web-backend"}
    rows = schedule_rows(ts)          # → [{"stage","range","progress","status","impact"}, ...]
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


# ── 排期解析（gen_weekly_all 用） ────────────────────────
# 统一 5 列表：阶段 | 起止 | 进度 | 状态 | 影响指标。
# 容忍 H1/H2 + 可选数字前缀：delta `# 5. 排期 / 上线节奏`。
_SCHEDULE_HEADER_RE = re.compile(
    r"^#{1,2}\s+(?:\d+\.\s*)?排期\s*/\s*上线节奏\s*$", re.MULTILINE
)
_NEXT_HEADING_RE = re.compile(r"^#{1,2}\s+", re.MULTILINE)
_PHASE_NOTE_RE = re.compile(r"^>\s*当前\s*Phase[:：]\s*(.+?)$", re.MULTILINE)


def _extract_schedule_section(text: str) -> str | None:
    m = _SCHEDULE_HEADER_RE.search(text)
    if not m:
        return None
    start = m.end()
    nxt = _NEXT_HEADING_RE.search(text, start)
    return text[start:(nxt.start() if nxt else len(text))]


def _parse_schedule_rows(section: str) -> list[dict]:
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 5:
            continue
        if cells[0].startswith("---") or cells[0] in ("阶段",):
            continue
        rows.append({
            "stage": cells[0], "range": cells[1], "progress": cells[2],
            "status": cells[3], "impact": cells[4],
        })
    return rows


def _current_quarter_deltas(line_root: Path) -> list[Path]:
    """产品线 deliverables 下所有 delta（季度/版本两层），按路径倒序（新季度优先）。"""
    deliv = line_root / "deliverables"
    if not deliv.exists():
        return []
    return sorted(deliv.glob("*/*/prd-*.md"), reverse=True)


def schedule_section(ts: TruthSource) -> tuple[str | None, str]:
    """返回 (排期段文本, 来源文件名)。baseline 找当季 delta §排期。"""
    if ts.path is None or ts.line_root is None:
        return None, ""
    # baseline：业务节奏在当季 delta
    for delta in _current_quarter_deltas(ts.line_root):
        sec = _extract_schedule_section(delta.read_text(encoding="utf-8"))
        if sec and _parse_schedule_rows(sec):
            return sec, delta.name
    return None, ""


def schedule_rows(ts: TruthSource) -> list[dict]:
    sec, _ = schedule_section(ts)
    return _parse_schedule_rows(sec) if sec else []


def phase_note(ts: TruthSource) -> str:
    sec, _ = schedule_section(ts)
    if not sec:
        return ""
    m = _PHASE_NOTE_RE.search(sec)
    return m.group(1).strip() if m else ""
