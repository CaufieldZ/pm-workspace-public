#!/usr/bin/env python3
r"""渲染 UI 屏内禁开发注解 — ui-annotation-gate 入口。

模型常把开发注解写进 prototype / IMAP 的实际渲染屏里（如
「带单战绩（无资格则不展示，此处隐藏占位）」），开发误读为真实文案。
本检查只扫 mockup 渲染屏内部：
- prototype（proto-*.html）：.app-mock / .web-front / .layout
- IMAP（imap-*.html）：.phone / .webframe（ann-card / flow-note 旁注区合法，不扫）

规则源：.claude/skills/prototype/SKILL.md + .claude/skills/interaction-map/SKILL.md

Usage:
    python3 scripts/check_ui_annotation.py <html>... [--strict]

退出码：
    0 — 无违规
    1 — 有违规但未传 --strict
    2 — 传 --strict 且有违规（hook 用）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.ui_annotation import find_mockup_annotations  # noqa: E402


def _kind_for(path: Path):
    name = path.name
    if name.startswith('proto-'):
        return 'proto'
    if name.startswith('imap-') or 'interaction' in name:
        return 'imap'
    return None


def check_file(path: Path):
    """返回 (kind, findings)。kind=None 表示非 proto/imap，跳过。"""
    kind = _kind_for(path)
    if kind is None:
        return None, []
    try:
        html = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return kind, []
    return kind, find_mockup_annotations(html, kind)


def main():
    args = sys.argv[1:]
    strict = '--strict' in args
    files = [Path(a) for a in args if not a.startswith('-')]
    if not files:
        print('用法: check_ui_annotation.py <html>... [--strict]', file=sys.stderr)
        sys.exit(0)

    total = 0
    for f in files:
        if not f.exists():
            continue
        kind, findings = check_file(f)
        if not findings:
            continue
        total += len(findings)
        print(f"\n{f} — mockup 屏内注解 {len(findings)} 处", file=sys.stderr)
        for loc, snippet, hits in findings[:20]:
            hit_str = ', '.join(f'{c}={v}' for c, v in hits)
            print(f"  ❌ [{loc}] {snippet!r}", file=sys.stderr)
            print(f"     → {hit_str}", file=sys.stderr)
        if len(findings) > 20:
            print(f"  ... （共 {len(findings)} 处，仅显示前 20）", file=sys.stderr)

    if total:
        print('', file=sys.stderr)
        print('❌ 渲染 UI 屏内写了开发注解，开发会误读为真实产品文案。', file=sys.stderr)
        print('   修法（原型）：删掉注解，屏内只放真实文案。', file=sys.stderr)
        print('   修法（IMAP）：注解移到 mockup 外的 ann-card / flow-note，手机/Web 屏内只放真实文案。', file=sys.stderr)
        print('   改源后重 build。临时绕过：SKIP_UI_ANNOTATION_GATE=1', file=sys.stderr)
        sys.exit(2 if strict else 1)
    sys.exit(0)


if __name__ == '__main__':
    main()
