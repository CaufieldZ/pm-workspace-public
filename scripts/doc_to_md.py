#!/usr/bin/env python3
"""把 docx / pdf / pptx / xlsx / 图片等转成 markdown，包装 markitdown CLI。

用法:
  python3 scripts/doc_to_md.py <file>                       # 单文件，输出同目录同名 .md
  python3 scripts/doc_to_md.py <file> -o <out.md>           # 指定输出路径
  python3 scripts/doc_to_md.py <file> --stdout              # 输出到 stdout 不写文件
  python3 scripts/doc_to_md.py <file> -p 项目名             # 输出到 projects/{项目}/inputs/
  python3 scripts/doc_to_md.py <dir> --batch                # 批量整个目录
  python3 scripts/doc_to_md.py <dir> --batch -p 项目名      # 批量 + 输出到项目 inputs

支持格式: .docx .pptx .xlsx .pdf .html .htm .png .jpg .jpeg .gif .bmp .tiff .mp3 .wav .m4a

依赖: pipx install 'markitdown[all]'
"""

# route-log: 调用埋点（scripts/lib/route_log.py）
import pathlib as _pl
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("doc_to_md"))
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUPPORTED = {
    '.docx', '.pptx', '.xlsx', '.pdf', '.html', '.htm',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff',
    '.mp3', '.wav', '.m4a',
}


def check_markitdown():
    if not shutil.which('markitdown'):
        sys.exit("markitdown 未安装。跑：pipx install 'markitdown[all]'")


def resolve_output(input_path: Path, args) -> Path:
    if args.output:
        return Path(args.output)
    if args.project:
        proj_inputs = find_project_inputs(args.project)
        return proj_inputs / (input_path.stem + '.md')
    return input_path.with_suffix('.md')


def find_project_inputs(project: str) -> Path:
    candidates = list(ROOT.glob(f'projects/*/{project}/inputs')) + list(ROOT.glob(f'projects/{project}/inputs'))
    if not candidates:
        sys.exit(f"找不到项目 {project} 的 inputs/ 目录")
    if len(candidates) > 1:
        sys.exit(f"项目名 {project} 不唯一: {[str(c) for c in candidates]}")
    return candidates[0]


def convert(input_path: Path, output_path: Path = None, to_stdout=False, verbose=False) -> bool:
    cmd = ['markitdown', str(input_path)]
    stderr_target = None if verbose else subprocess.DEVNULL
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=stderr_target, text=True)
    except FileNotFoundError:
        sys.exit("错误：markitdown 未安装。跑：pipx install 'markitdown[all]'")
    if result.returncode != 0:
        # verbose=False 时 stderr=DEVNULL → result.stderr 为 None，取 [:300] 会 TypeError
        err = (result.stderr or "(stderr 已抑制，加 --verbose 查看)")[:300]
        print(f"[FAIL] {input_path.name}: {err}", file=sys.stderr)
        return False
    content = result.stdout
    if to_stdout:
        sys.stdout.write(content)
        return True
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding='utf-8')
    size_kb = output_path.stat().st_size / 1024
    print(f"[OK] {input_path.name} → {output_path.relative_to(ROOT) if output_path.is_relative_to(ROOT) else output_path} ({size_kb:.1f} KB)")
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('path', help='输入文件或目录（--batch 时为目录）')
    p.add_argument('-o', '--output', help='输出路径（单文件模式）')
    p.add_argument('-p', '--project', help='输出到 projects/{项目}/inputs/，自动定位项目目录')
    p.add_argument('--batch', action='store_true', help='批量处理目录下所有支持格式文件')
    p.add_argument('--stdout', action='store_true', help='输出到 stdout 不写文件（仅单文件）')
    p.add_argument('-v', '--verbose', action='store_true', help='显示 markitdown 内部警告')
    args = p.parse_args()

    check_markitdown()
    path = Path(args.path).expanduser().resolve()

    if args.batch:
        if not path.is_dir():
            sys.exit(f"--batch 需要目录，{path} 不是目录")
        files = sorted([f for f in path.iterdir() if f.suffix.lower() in SUPPORTED])
        if not files:
            sys.exit(f"{path} 下没找到支持格式的文件 ({sorted(SUPPORTED)})")
        ok = 0
        for f in files:
            out = resolve_output(f, args)
            if convert(f, out, verbose=args.verbose):
                ok += 1
        print(f"\n完成 {ok}/{len(files)}", file=sys.stderr)
        sys.exit(0 if ok == len(files) else 1)

    if not path.is_file():
        sys.exit(f"{path} 不存在或不是文件")
    if path.suffix.lower() not in SUPPORTED:
        print(f"[WARN] {path.suffix} 不在支持列表，markitdown 仍会尝试", file=sys.stderr)

    if args.stdout:
        convert(path, to_stdout=True, verbose=args.verbose)
    else:
        out = resolve_output(path, args)
        ok = convert(path, out, verbose=args.verbose)
        sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
