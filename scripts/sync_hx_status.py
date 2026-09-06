#!/usr/bin/env python3
"""火效 → 本地 delta 状态/上线日期同步（火效是唯一权威源，本地是缓存投影）。

从 delta 头部「火效」字段解析 H 号 → 读火效真实流程状态 + PRD TAG 上线日期
→ 回写本地两条管线：
  管线 1（反向合并门）：delta 头部「状态」字段
  管线 2（周报上线归因）：delta §排期 / 上线节奏表 含「上线/灰度/全量」行的 起止 + 状态

默认 dry-run（print diff）；--apply 才落盘。本地「已合并」是本地动作（火效无此态），不被覆盖。

用法：
    python3 scripts/sync_hx_status.py <delta.md>            # dry-run 单个
    python3 scripts/sync_hx_status.py -p livestream         # dry-run 当季全部 delta
    python3 scripts/sync_hx_status.py <delta.md> --apply    # 落盘
    python3 scripts/sync_hx_status.py <delta.md> --token <t>

退出码：0 正常（含 dry-run / 无改动）；2 认证失败。
上线日期口径：火效 PRD TAG 打标时间（repo tag history --prefix PRD 最早一条）。
纯后端/无代码取不到 TAG → 降级用流程完成节点，输出标注「口径=流程完成（非 PRD TAG）」。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.repo import find_root  # noqa: E402

# 复用 skill 的 hx-cli 封装
_SKILL_SCRIPTS = find_root() / ".claude" / "skills" / "hx-cli" / "scripts"
sys.path.insert(0, str(_SKILL_SCRIPTS))
import hx_client as hx  # noqa: E402

CONTROLLED = ("待排期", "开发中", "已上线", "已合并")

# 火效 current_process → 本地受控词。已合并是本地动作，火效无此态，此表不产出「已合并」。
_LIVE_PROCESSES = {"已完成", "已上线", "已发布"}  # 配合 PRD TAG 判「已上线」
_DEV_PROCESSES = {
    "需求已终评", "研发中", "技术方案设计", "技术评审", "待开发", "设计中",
    "测试中", "验收中", "延期修复", "待测试", "提测中", "联调中",
}

_HX_FIELD = re.compile(r"^[\s\-*]*\**\s*火效\s*\**\s*[:：]\s*(.+?)\s*$", re.MULTILINE)
_STATUS_FIELD = re.compile(r"^([\s\-*]*\**\s*状态\s*\**\s*[:：]\s*)(.+?)\s*$", re.MULTILINE)
# 协作表形态（骨架 v5 起头部是表格，不再是 bullet）：`| key | value |` 键值对。
# 只在头部块内搜——§排期表有「状态」列头，全文搜会把它的邻格误当值。
_HX_CELL = re.compile(r"\|\s*火效\s*\|\s*([^|\n]*?)\s*\|")
_STATUS_CELL = re.compile(r"(\|\s*状态\s*\|\s*)([^|\n]*?)(\s*\|)")
_TOP_HEADING = re.compile(r"^# ", re.MULTILINE)
# work_id 提取：优先显式 H 号；退回裸数字时排除日期形态（前后带 - 的 2026-07-28）
_H_PREFIXED = re.compile(r"H(\d{4,})", re.I)
_H_BARE = re.compile(r"(?<![\d-])(\d{4,})(?![-\d])")
_SCHEDULE_HEADER = re.compile(r"^#{1,2}\s+(?:\d+\.\s*)?排期\s*/\s*上线节奏\s*$", re.MULTILINE)
_NEXT_HEADING = re.compile(r"^#{1,2}\s+", re.MULTILINE)
_ROLLOUT_KW = ("上线", "灰度", "全量")
_DATE_IN = re.compile(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})")


# ── 纯函数：delta 头部字段解析 ────────────────────────────────────────────

def header_span(delta_text: str) -> tuple[int, int]:
    """头部块区间 = 首个 H1 行尾 ~ 下一个顶级标题（无则到文末）。

    协作表的「状态」「火效」格只在此区间内认，避免撞上 §排期表的「状态」列头。
    """
    tops = [m.start() for m in _TOP_HEADING.finditer(delta_text)]
    if not tops:
        return 0, len(delta_text)
    nl = delta_text.find("\n", tops[0])
    start = len(delta_text) if nl < 0 else nl + 1
    end = tops[1] if len(tops) > 1 else len(delta_text)
    return start, max(start, end)


def parse_hx_work_id(delta_text: str) -> str | None:
    """从头部「火效」字段抽 work_id（bullet 或协作表两种形态）。占位符返回 None。"""
    m = _HX_FIELD.search(delta_text)
    if m:
        val = m.group(1)
    else:
        hs, he = header_span(delta_text)
        cm = _HX_CELL.search(delta_text, hs, he)
        if not cm:
            return None
        val = cm.group(1)
    if "<" in val and ">" in val:
        return None  # 占位符未填
    if "{{" in val:
        return None  # 骨架占位符未填
    hm = _H_PREFIXED.search(val) or _H_BARE.search(val)
    return hm.group(1) if hm else None


def current_local_status(delta_text: str) -> str | None:
    # 两种形态都只在头部块内认：正文里的「状态：」字样（决策段等）不是头部状态
    hs, he = header_span(delta_text)
    m = _STATUS_FIELD.search(delta_text[hs:he])
    if m:
        return m.group(2).strip()
    cm = _STATUS_CELL.search(delta_text, hs, he)
    return cm.group(2).strip() if cm else None


# ── 纯函数：火效状态映射 ──────────────────────────────────────────────────

def map_status(current_process: str, has_prd_tag: bool) -> str:
    """火效流程 + 是否有 PRD TAG → 本地受控词。未知节点返回空串（保留本地值）。"""
    proc = (current_process or "").strip()
    if has_prd_tag or proc in _LIVE_PROCESSES:
        return "已上线"
    if proc in _DEV_PROCESSES:
        return "开发中"
    return ""


# ── 纯函数：PRD TAG 上线日期 ──────────────────────────────────────────────

def earliest_prd_date(tag_rows: list[dict]) -> str | None:
    """从 PRD TAG 历史取最早打标日期（YYYY-MM-DD）。"""
    dates = []
    for r in tag_rows or []:
        blob = " ".join(str(v) for v in r.values() if v)
        dm = _DATE_IN.search(blob)
        if dm:
            y, mo, d = dm.groups()
            dates.append(f"{y}-{int(mo):02d}-{int(d):02d}")
    return min(dates) if dates else None


# ── 纯函数：头部状态回写（管线 1）─────────────────────────────────────────

def rewrite_header_status(delta_text: str, new_status: str) -> tuple[str, str | None]:
    """回写头部「状态」字段。本地「已合并」不被覆盖。返回 (新文本, 改动说明 or None)。"""
    old = current_local_status(delta_text)
    if old == "已合并":
        return delta_text, None
    if not new_status or old == new_status:
        return delta_text, None
    # 两种形态都只在头部块内替，切片改完再拼回
    # （bullet 全文替会撞正文里的「状态：」字样，表格全文替会撞 §排期表的「状态」列头）
    hs, he = header_span(delta_text)
    head, changed = _STATUS_FIELD.subn(
        lambda m: f"{m.group(1)}{new_status}", delta_text[hs:he], count=1
    )
    if not changed:
        head, changed = _STATUS_CELL.subn(
            lambda m: f"{m.group(1)}{new_status}{m.group(3)}", delta_text[hs:he], count=1
        )
    if not changed:
        return delta_text, None
    new_text = delta_text[:hs] + head + delta_text[he:]
    return new_text, f"头部状态：{old} → {new_status}"


# ── 纯函数：§排期表回写（管线 2，按列名定位，容忍 4/5 列变体）─────────────

def _find_col(header_cells: list[str], name: str) -> int | None:
    for i, c in enumerate(header_cells):
        if name in c:
            return i
    return None


def rewrite_schedule(delta_text: str, launch_date: str) -> tuple[str, list[str]]:
    """§排期表里含 上线/灰度/全量 的行：起止列填 launch_date、状态列填「已完成」。

    按表头列名定位「起止」「状态」列（容忍 4 列变体）。返回 (新文本, 改动说明列表)。
    """
    changes: list[str] = []
    m = _SCHEDULE_HEADER.search(delta_text)
    if not m:
        return delta_text, ["§排期表未找到，跳过管线 2"]
    start = m.end()
    nxt = _NEXT_HEADING.search(delta_text, start)
    end = nxt.start() if nxt else len(delta_text)
    section = delta_text[start:end]

    lines = section.splitlines(keepends=True)
    header_seen = False
    col_range = col_status = None
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().split("|")[1:-1]]
        if not header_seen:
            header_seen = True
            col_range = _find_col(cells, "起止")
            col_status = _find_col(cells, "状态")
            continue
        if cells and cells[0].startswith("---"):
            continue
        if col_range is None:
            continue
        if not any(kw in cells[0] for kw in _ROLLOUT_KW):
            continue
        raw_cells = line.strip().split("|")[1:-1]
        changed = False
        if col_range is not None and col_range < len(raw_cells):
            old = raw_cells[col_range].strip()
            if old != launch_date:
                raw_cells[col_range] = f" {launch_date} "
                changes.append(f"§排期「{cells[0][:20]}」起止：{old} → {launch_date}")
                changed = True
        if col_status is not None and col_status < len(raw_cells):
            olds = raw_cells[col_status].strip()
            if olds != "已完成":
                raw_cells[col_status] = " 已完成 "
                changes.append(f"§排期「{cells[0][:20]}」状态：{olds} → 已完成")
                changed = True
        if changed:
            indent = line[:len(line) - len(line.lstrip())]
            trail = "\n" if line.endswith("\n") else ""
            lines[i] = f"{indent}|{'|'.join(raw_cells)}|{trail}"
    if not changes:
        changes.append("§排期表无 上线/灰度/全量 行命中，管线 2 未改")
    return delta_text[:start] + "".join(lines) + delta_text[end:], changes


# ── I/O 层：单个 delta 同步（调网络）──────────────────────────────────────

def _try(fn, rec, label):
    try:
        return fn()
    except hx.HxError as e:
        rec["notes"].append(f"{label} 查询失败：{e}")
        return {}


def sync_one(path: Path, token: str | None, apply: bool) -> dict:
    rec: dict = {"path": str(path), "changes": [], "notes": []}
    try:
        # 不用 errors="replace"：本函数会回写，容错读会把非法字节替换成 U+FFFD 写死
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        rec["notes"].append("❌ 文件非 UTF-8，跳过（避免回写腐蚀原字节）")
        return rec

    work_id = parse_hx_work_id(text)
    if not work_id:
        rec["notes"].append("❌ 头部无「火效」字段或为占位符（未填 H 号）——先补火效链接再同步")
        return rec
    rec["work_id"] = work_id

    work = hx.run(["work", "get", work_id], token=token)
    # work get 返回 current_proc；personal list 返回 current_process。取兼容。
    proc = work.get("current_proc") or work.get("current_process") or ""
    rec["work_name"] = work.get("work_name")
    rec["current_process"] = proc
    rec["link"] = hx.work_link(work_id)

    launch_date = None
    related = _try(lambda: hx.run(["repo", "work", "related-repo", work_id], token=token), rec, "related-repo")
    repo_id = None
    if isinstance(related, dict):
        rows = related.get("rows") or related.get("repos") or []
        for r in (rows if isinstance(rows, list) else []):
            repo_id = r.get("repo_id") or r.get("gitlab_repo_id") or r.get("id")
            if repo_id:
                break
    if repo_id:
        th = _try(
            lambda: hx.run(["repo", "tag", "history", "--work-id", work_id,
                            "--repo-id", str(repo_id), "--prefix", "PRD"], token=token),
            rec, "tag-PRD",
        )
        tag_rows = (th.get("rows") or th.get("tags") or []) if isinstance(th, dict) else []
        launch_date = earliest_prd_date(tag_rows)

    has_prd = launch_date is not None
    if not has_prd:
        rec["notes"].append("口径=流程完成（未取到 PRD TAG；纯后端/无代码/未上线）")

    new_status = map_status(proc, has_prd)
    if not new_status:
        rec["notes"].append(f"火效流程「{proc}」未在映射表内 → 保留本地状态，未改（请人工确认映射）")
    else:
        text, ch = rewrite_header_status(text, new_status)
        if ch:
            rec["changes"].append(ch)

    if launch_date:
        text, sched_changes = rewrite_schedule(text, launch_date)
        rec["changes"].extend(sched_changes)
        rec["launch_date"] = launch_date
    else:
        rec["notes"].append("无 PRD TAG 上线日期 → 管线 2（§排期）未改")

    has_real_change = any("→" in c for c in rec["changes"])
    if apply and has_real_change:
        path.write_text(text, encoding="utf-8")
        rec["applied"] = True
    else:
        rec["applied"] = False
    return rec


def collect_deltas(project: str, repo_root: Path) -> list[Path]:
    line = repo_root / "projects" / project
    deliv = line / "deliverables"
    if not deliv.is_dir():
        return []
    archive = deliv / "archive"
    return sorted(
        p for p in deliv.rglob("prd-*.md")
        if "baseline" not in p.name and archive not in p.parents
    )


def render(rec: dict) -> str:
    lines = [f"■ {rec['path']}"]
    if rec.get("work_id"):
        tail = f"，PRD TAG 上线 {rec['launch_date']}" if rec.get("launch_date") else ""
        lines.append(f"  火效：[{rec.get('work_name') or ''}]({rec.get('link')})"
                     f" 流程「{rec.get('current_process')}」{tail}")
    if rec["changes"]:
        lines.append("  改动：" + ("已落盘" if rec.get("applied") else "dry-run，未落盘"))
        for c in rec["changes"]:
            lines.append(f"    · {c}")
    else:
        lines.append("  无改动")
    for n in rec["notes"]:
        lines.append(f"  ⚠ {n}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="火效 → 本地 delta 状态/上线日期同步")
    ap.add_argument("delta", nargs="?", help="delta 文件路径；与 -p 二选一")
    ap.add_argument("-p", "--project", help="产品线名，同步当季全部 delta")
    ap.add_argument("--apply", action="store_true", help="落盘（默认 dry-run 只 print diff）")
    ap.add_argument("--token", help="覆盖 AIHUB_TOKEN，仅本次")
    args = ap.parse_args()

    repo_root = find_root()
    if args.delta:
        one = Path(args.delta).resolve()
        if not one.is_file():
            print(f"文件不存在：{args.delta}", file=sys.stderr)
            return 1
        targets = [one]
    elif args.project:
        targets = collect_deltas(args.project, repo_root)
        if not targets:
            print(f"未找到 {args.project} 的 delta。")
            return 0
    else:
        print("需指定 <delta.md> 或 -p <产品线>。", file=sys.stderr)
        return 1

    try:
        hx.ensure_auth(token=args.token)
    except hx.HxAuthError as e:
        print(f"认证失败：{e}\n下一步：{e.hint}", file=sys.stderr)
        return 2

    print(f"{'落盘模式（--apply）' if args.apply else 'dry-run（不落盘，加 --apply 生效）'}\n")
    for t in targets:
        try:
            print(render(sync_one(t, token=args.token, apply=args.apply)))
        except hx.HxError as e:
            print(f"■ {t}\n  调用失败：{e}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
