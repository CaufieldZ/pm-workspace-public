#!/usr/bin/env python3
"""hook 批量检查器运行器：单 python3 进程按原 argv 依次跑多个 checker 的 main()。

用法（spool 格式从 stdin 读，_pc_enqueue 逐行写入）：
    printf 'learned\\n1\\n<file>\\nplain\\n3\\n<file>\\n--strict\\n--json-out\\n' \\
      | python3 scripts/hook_py_batch.py <out_dir>
spool 每槽三段：槽名一行 / 参数个数一行 / 参数逐行（参数不含换行——文件路径本工区恒成立）。

输出（写 out_dir，不写 stdout）：
    <out_dir>/<slot>.rc    退出码（int；模块加载失败 / 未捕获异常 = 1）
    <out_dir>/<slot>.all   stdout+stderr 合并捕获（等价 bash 侧 > $TMPOUT 2>&1）
    <out_dir>/<slot>.dur   耗时毫秒（int）
    <out_dir>/_summary     每槽一行：slot rc dur_ms（埋点 / 排障）

前置：无。退出码：0 = 全槽跑完（各槽 rc 在文件里）；2 = spool 损坏 / out_dir 不可写。

等价性纪律（decisions/2026-09-13-user-prompt-warn-merge「先分离验证再合并」的机制化）：
跑的是同一份代码对象——importlib 按文件路径加载、sys.argv 原样伪装、main() 原样调用，
不重写判定逻辑。SystemExit 捕获为退出码；其余异常 traceback 进 .all、rc=1（等价今天
进程崩溃，bash 侧按 ne0 拦 / eq2 放）。bash 侧配套见 .claude/hooks/lib/pybatch.sh。
"""
from __future__ import annotations

import importlib.util
import io
import sys
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


def parse_spool(text: str) -> list[tuple[str, list[str]]]:
    """spool 文本 → [(slot, argv), ...]。格式损坏抛 ValueError（裸 except 都不允许）。"""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    slots: list[tuple[str, list[str]]] = []
    i = 0
    while i < len(lines):
        slot = lines[i]
        if not slot or not slot.replace("_", "a").isalnum():
            raise ValueError(f"bad slot name at line {i + 1}: {slot!r}")
        i += 1
        if i >= len(lines) or not lines[i].isdigit():
            raise ValueError(f"bad argc at line {i}: {lines[i]!r}")
        argc = int(lines[i])
        i += 1
        if i + argc > len(lines):
            raise ValueError(f"argc {argc} overruns spool for slot {slot}")
        slots.append((slot, lines[i:i + argc]))
        i += argc
    return slots


def run_slot(out_dir: Path, slot: str, argv: list[str]) -> None:
    """加载 checker 模块按 argv 跑 main()，写 rc / 合并输出 / 耗时。异常自兜不外抛。"""
    buf = io.StringIO()
    t0 = time.perf_counter()
    rc = 1
    try:
        spec = importlib.util.spec_from_file_location(f"pcbatch_{slot}_{id(argv)}", argv[0])
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load module from {argv[0]}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        old_argv = sys.argv
        sys.argv = list(argv)
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                main_fn = getattr(mod, "main", None)
                if main_fn is None:
                    raise ImportError(f"{argv[0]} has no main()")
                rc = main_fn()
                if rc is None:
                    rc = 0
        except SystemExit as e:
            code = e.code
            rc = code if isinstance(code, int) else (0 if code is None else 1)
        finally:
            sys.argv = old_argv
    except BaseException:
        traceback.print_exc(file=buf)
        rc = 1
    dur_ms = int((time.perf_counter() - t0) * 1000)
    (out_dir / f"{slot}.rc").write_text(f"{rc}\n", encoding="utf-8")
    (out_dir / f"{slot}.all").write_text(buf.getvalue(), encoding="utf-8")
    (out_dir / f"{slot}.dur").write_text(f"{dur_ms}\n", encoding="utf-8")


def main() -> int:
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        print(__doc__)
        return 0
    if len(args) != 1:
        print("用法: python3 scripts/hook_py_batch.py <out_dir>（spool 从 stdin 读）", file=sys.stderr)
        return 2
    out_dir = Path(args[0])
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        slots = parse_spool(sys.stdin.read())
        summary = []
        for slot, argv in slots:
            run_slot(out_dir, slot, argv)
            rc = (out_dir / f"{slot}.rc").read_text(encoding="utf-8").strip()
            dur = (out_dir / f"{slot}.dur").read_text(encoding="utf-8").strip()
            summary.append(f"{slot} {rc} {dur}")
        (out_dir / "_summary").write_text("\n".join(summary) + "\n", encoding="utf-8")
        return 0
    except (ValueError, OSError) as e:
        print(f"hook_py_batch: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
