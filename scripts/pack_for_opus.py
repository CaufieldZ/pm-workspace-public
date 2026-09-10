#!/usr/bin/env python3
"""把工作区按 scope 任意范围打包成单文件 markdown（外部 review / 离线分享 / 备份），包装 repomix CLI。

可选 scope（用 -s / --scope，逗号分隔可多选）:
  framework  默认。框架全貌入口：每个 skill 的 SKILL.md + agents + commands + hooks + scripts + 顶级 md
  hooks      钩子相关：.claude/hooks/ + .githooks/ + settings.json（hook 注册）
  rules      规则层：.claude/output-styles/ + CLAUDE.md + projects/product-lines.md + README.md + scripts/lib/thresholds.yaml
  skills     skill 系统全展开（含每个 skill 的 scripts/ + references/，量大）
  agents     sub-agent 配置：.claude/agents/
  commands   slash commands：.claude/commands/
  scripts    根 scripts/ 工具
  hooks-runtime  hook 运行时埋点：hooks + logs + dashboard
  all        整个工作区（含 projects/，量很大）

用法:
  python3 scripts/pack_for_opus.py                                  # 默认 framework
  python3 scripts/pack_for_opus.py -s hooks                         # 钩子
  python3 scripts/pack_for_opus.py -s hooks,rules,agents            # 多个 scope 合并
  python3 scripts/pack_for_opus.py -s all                           # 整个工作区
  python3 scripts/pack_for_opus.py -p community/base                # 单项目（与 -s 互斥）
  python3 scripts/pack_for_opus.py -p liquidity                     # 顶级项目
  python3 scripts/pack_for_opus.py -s skills --exclude "**/assets/**"  # scope + 追加 exclude
  python3 scripts/pack_for_opus.py --include "scripts/**"           # 完全自定义（绕过 scope）
  python3 scripts/pack_for_opus.py -o /tmp/foo.md --open            # 自定义输出 + 拉起

依赖: 全局装 `npm install -g repomix`，未装则 fallback 到 npx（首次较慢）。
"""

# route-log: 调用埋点（scripts/lib/route_log.py）
import pathlib as _pl
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("pack_for_opus"))
import argparse
import datetime
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path(tempfile.gettempdir())

COMMON_EXCLUDES = [
    '.git/**', '**/.DS_Store', 'node_modules/**',
    '.claude/projects/**', '.claude/file-history/**', '.claude/session-state.md',
    '.claude/skills/*/assets/fonts/**',
    '.claude/skills/competitor-analysis/**/auth/**',
    '.claude/skills/intel-collector/**/auth/**',
    '**/.private/**',
    '**/*.png', '**/*.jpg', '**/*.jpeg', '**/*.gif', '**/*.svg', '**/*.ico',
    '**/*.pdf', '**/*.docx', '**/*.pptx', '**/*.xlsx',
    '**/*.mp3', '**/*.wav', '**/*.mp4', '**/*.zip', '**/*.tar.gz',
    '**/*.woff', '**/*.woff2', '**/*.ttf', '**/*.otf',
    '_demos/**', 'examples/**', '.public/**',
]

SCOPES = {
    'framework': [
        '.claude/skills/*/SKILL.md',
        '.claude/agents/**',
        '.claude/commands/**',
        '.claude/output-styles/**',
        '.claude/runbooks/**',
        '.claude/chat-templates/**',
        '.claude/hooks/**',
        '.claude/settings.json',
        'scripts/*.py', 'scripts/*.sh',
        'CLAUDE.md', 'README.md', 'projects/product-lines.md', 'package.json', '.mcp.json',
        '.githooks/**',
    ],
    'hooks': [
        '.claude/hooks/**',
        '.githooks/**',
        '.claude/settings.json',
    ],
    'hooks-runtime': [
        '.claude/hooks/**',
        '.claude/logs/**',
        '.claude/workspace-dashboard.md',
        'scripts/dashboard.py',
    ],
    'rules': [
        '.claude/output-styles/**',
        'scripts/lib/thresholds.yaml',
        'CLAUDE.md',
        'projects/product-lines.md',
        'README.md',
    ],
    'skills': [
        '.claude/skills/**',
        '.claude/agents/**',
    ],
    'agents': [
        '.claude/agents/**',
    ],
    'commands': [
        '.claude/commands/**',
    ],
    'scripts': [
        'scripts/**',
    ],
    'all': [
        '**/*',
    ],
}

# all scope 时不应用 projects/deliverables 的 exclude，但其他 scope 默认排
# 用 projects/*/** 而非 projects/** 是为保留顶层 projects/product-lines.md（projects 域入口宪法，rules scope 需要）
PROJECTS_EXCLUDES = ['projects/*/**', 'references/**', 'deliverables/**', '**/*.html']


def check_repomix():
    if shutil.which('repomix'):
        return ['repomix']
    print("[INFO] repomix 未全局安装，用 npx fallback（首次较慢）", file=sys.stderr)
    print("[INFO] 加速：npm install -g repomix（国内装时保证 Clash 在线，代理判定自动）", file=sys.stderr)
    return ['npx', '-y', 'repomix@latest']


def _proxy_decision() -> str | None:
    """调 scripts/proxy_env.sh --print 拿代理判定，返回代理 URL（判定非 proxy / 调用失败 → None）。"""
    try:
        r = subprocess.run(
            ['bash', str(ROOT / 'scripts' / 'proxy_env.sh'), '--print'],
            capture_output=True, text=True, timeout=15,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    mode = proxy = ''
    for line in r.stdout.splitlines():
        key, _, val = line.partition('=')
        if key == 'mode':
            mode = val.strip()
        elif key == 'proxy':
            proxy = val.strip()
    return proxy if mode == 'proxy' else None


def resolve_project_path(project: str) -> Path:
    candidates = list(ROOT.glob(f'projects/*/{project}')) + list(ROOT.glob(f'projects/{project}'))
    candidates = [c for c in candidates if c.is_dir()]
    if not candidates:
        sys.exit(f"找不到项目 {project}（试过 projects/*/{project} 和 projects/{project}）")
    if len(candidates) > 1:
        sys.exit(f"项目名 {project} 不唯一: {[str(c.relative_to(ROOT)) for c in candidates]}")
    return candidates[0]


def parse_scopes(scope_arg: str) -> list[str]:
    scopes = [s.strip() for s in scope_arg.split(',') if s.strip()]
    invalid = [s for s in scopes if s not in SCOPES]
    if invalid:
        sys.exit(f"未知 scope: {invalid}。可选: {list(SCOPES.keys())}")
    return scopes


def build_includes(args) -> list[str]:
    if args.project:
        proj = resolve_project_path(args.project)
        return [f'{proj.relative_to(ROOT)}/**']
    if args.include:
        return args.include
    scopes = parse_scopes(args.scope)
    includes = []
    seen = set()
    for s in scopes:
        for pat in SCOPES[s]:
            if pat not in seen:
                includes.append(pat)
                seen.add(pat)
    return includes


def build_excludes(args) -> list[str]:
    base = list(COMMON_EXCLUDES)
    scopes = parse_scopes(args.scope) if not args.project else []
    if 'all' not in scopes and not args.include and not args.project:
        base += PROJECTS_EXCLUDES
    if args.project:
        base += ['**/deliverables/**', '**/screenshots/**', '**/*.html']
    if args.exclude:
        base += args.exclude
    return base


def output_tag(args) -> str:
    if args.project:
        return f"project-{args.project.replace('/', '-')}"
    if args.include:
        return 'custom'
    scopes = parse_scopes(args.scope)
    return '+'.join(scopes)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('-s', '--scope', default='framework',
                   help=f"逗号分隔的 scope 列表，默认 framework。可选: {', '.join(SCOPES.keys())}")
    p.add_argument('-p', '--project', help='项目名（projects/{产品线}/{项目} 或 projects/{项目}），与 -s 互斥')
    p.add_argument('--include', action='append', help='完全自定义 include glob（绕过 scope，可重复）')
    p.add_argument('--exclude', action='append', help='追加 exclude glob（在 scope 默认 exclude 之上叠加）')
    p.add_argument('-o', '--output', help='输出路径（默认 ~/agents-a9ec8455d0/pack-{tag}-{date}.md）')
    p.add_argument('--open', action='store_true', help='打包完后用 open 拉起文件')
    p.add_argument('-v', '--verbose', action='store_true', help='打印 repomix 完整日志')
    args = p.parse_args()

    cmd_base = check_repomix()
    includes = build_includes(args)
    excludes = build_excludes(args)

    SCRATCH.mkdir(parents=True, exist_ok=True)
    date = datetime.date.today().isoformat()
    output = Path(args.output) if args.output else SCRATCH / f'pack-{output_tag(args)}-{date}.md'
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = cmd_base + [
        '--include', ','.join(includes),
        '--ignore', ','.join(excludes),
        '--style', 'markdown',
        '-o', str(output),
    ]

    print(f"[pack] scope/source: {output_tag(args)}", file=sys.stderr)
    print(f"[pack] include: {len(includes)} 条 | exclude: {len(excludes)} 条", file=sys.stderr)
    print(f"[pack] 输出: {output}", file=sys.stderr)

    env = os.environ.copy()
    if cmd_base[0] == 'npx' and not env.get('ALL_PROXY'):
        _url = _proxy_decision()
        if _url:
            env['ALL_PROXY'] = _url  # npx fallback 按 proxy_env.sh 判定注入，国外直连不注入
        else:
            print("[INFO] 代理判定 direct，npx 直连", file=sys.stderr)

    result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=not args.verbose, text=True)
    if result.returncode != 0:
        print(f"[FAIL] repomix 退出码 {result.returncode}", file=sys.stderr)
        if not args.verbose:
            print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    if not args.verbose and result.stdout:
        for line in result.stdout.split('\n'):
            if any(k in line for k in ['Token', 'Files', 'Total', '📊', '📈']):
                print(line, file=sys.stderr)

    if not output.exists():
        sys.exit(f"[FAIL] 输出文件未生成: {output}")
    size_kb = output.stat().st_size / 1024
    print(f"\n[OK] {output} ({size_kb:.1f} KB)", file=sys.stderr)

    token_estimate = output.stat().st_size // 4
    if token_estimate > 400_000:
        print(f"[WARN] 估算 ~{token_estimate:,} token，超过常见单次输入推荐上限，建议加 --exclude 缩范围", file=sys.stderr)
    elif token_estimate > 200_000:
        print(f"[INFO] 估算 ~{token_estimate:,} token，接近常见上限，注意可能截断", file=sys.stderr)

    if args.open:
        if platform.system() == 'Windows':
            os.startfile(str(output))
        elif platform.system() == 'Darwin':
            subprocess.run(['open', str(output)])
        else:
            subprocess.run(['xdg-open', str(output)])


if __name__ == '__main__':
    main()
