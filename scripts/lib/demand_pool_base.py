"""需求池 Google Sheets 同步公共基类。

sync_growth_demand_pool.py / sync_ux_demand_pool.py 共用：Sheet 读取、SHA1 去重、
Markdown 写入、writeback 反写。子类 override filter_rows() + render_md() + 配置常量。
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from lib.google_sheets import col_letter, get_service, read_tab, update_cells  # noqa: E402


class DemandPoolBase:
    SHEET_ID: str = ""
    TAB_TITLE: str = ""
    GID: int = 0
    OUT_FILE: Path = ROOT

    def filter_rows(self, rows: list[list[str]]) -> list[tuple[int, list[str]]]:
        """返回 [(sheet_row_1based, row), ...]。子类必须 override。"""
        raise NotImplementedError

    def render_md(self, matched: list[tuple[int, list[str]]], total: int) -> str:
        """子类必须 override。"""
        raise NotImplementedError

    # 通用 Markdown 表格渲染（render_md 内复用）：行号列 + output_cols；
    # 单元格 \n→<br>、| 转义、超 max_len 截断
    @staticmethod
    def render_table(
        matched: list[tuple[int, list[str]]],
        output_cols: list[tuple[int, str]],
        max_len: int = 100,
    ) -> list[str]:
        headers = ["行号"] + [name for _, name in output_cols]
        lines = [
            "| " + " | ".join(headers) + " |",
            "|" + "|".join(["---"] * len(headers)) + "|",
        ]
        for row_idx, row in matched:
            cells = [str(row_idx)]
            for idx, _ in output_cols:
                v = str(row[idx]) if idx < len(row) else ""
                v = v.replace("\n", "<br>").replace("|", "\\|").strip()
                if len(v) > max_len:
                    v = v[: max_len - 3] + "..."
                cells.append(v)
            lines.append("| " + " | ".join(cells) + " |")
        return lines

    # ── pull ────────────────────────────────────────────────────────

    def _read_sheet(self):
        print(f"  拉取 sheet {self.SHEET_ID[:20]}... / tab {self.TAB_TITLE}", file=sys.stderr)
        svc = get_service(write=False)
        rows = read_tab(svc, self.SHEET_ID, self.TAB_TITLE)
        return svc, rows

    def _write_if_changed(self, md: str):
        new_hash = hashlib.sha1(md.encode("utf-8")).hexdigest()
        if self.OUT_FILE.exists():
            old_hash = hashlib.sha1(
                self.OUT_FILE.read_text(encoding="utf-8").encode("utf-8")
            ).hexdigest()
            if old_hash == new_hash:
                print(f"  ✅ 内容未变（hash {new_hash[:8]}），跳过写入", file=sys.stderr)
                return
        self.OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.OUT_FILE.write_text(md, encoding="utf-8")
        print(f"  ✅ 写入 {self.OUT_FILE.relative_to(ROOT)}", file=sys.stderr)

    def cmd_pull(self, args) -> int:
        _svc, rows = self._read_sheet()
        total = max(0, len(rows) - 1)  # 空表 len==0 时不下溢成 -1
        matched = self.filter_rows(rows)
        print(f"  全表 {total} 行 · 命中 {len(matched)} 行", file=sys.stderr)
        md = self.render_md(matched, total)
        if getattr(args, "dry_run", False):
            print(md)
            return 0
        self._write_if_changed(md)
        return 0

    # ── writeback ────────────────────────────────────────────────────

    def cmd_writeback(self, args) -> int:
        svc = get_service(write=True)
        if getattr(args, "match_name", ""):
            rows = read_tab(svc, self.SHEET_ID, self.TAB_TITLE)
            if args.row < 1 or args.row - 1 >= len(rows):
                # 下界必须查：--row 0 会让 rows[-1] 命中末行做 match-name 校验，写到非法 A1
                print(f"  ❌ row {args.row} 越界（合法范围 1..{len(rows)}）", file=sys.stderr)
                return 1
            current_name = rows[args.row - 1][2] if len(rows[args.row - 1]) > 2 else ""
            if args.match_name not in current_name:
                print(
                    f"  ❌ row {args.row} col 2 = {current_name!r}，"
                    f"不含 {args.match_name!r}，拒写",
                    file=sys.stderr,
                )
                return 1
            print(f"  ✅ match-name OK: row {args.row} col 2 = {current_name!r}", file=sys.stderr)
        cell = f"'{self.TAB_TITLE}'!{col_letter(args.col + 1)}{args.row}"
        print(f"  📝 写 {cell} = {args.value[:80]!r}", file=sys.stderr)
        if getattr(args, "dry_run", False):
            print("  (dry-run，未实写)", file=sys.stderr)
            return 0
        update_cells(svc, self.SHEET_ID, cell, [[args.value]])
        print("  ✅ 写回 OK", file=sys.stderr)
        return 0
