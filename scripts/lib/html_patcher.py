#!/usr/bin/env python3
"""HTML 产出物 patch 工具包。

等价于 PRD 的 update_prd_base.py——提供字符串替换、正则替换、版本号升级等
通用操作，项目 patch 脚本只需写业务变更内容。

用法：
    from lib.html_patcher import HtmlPatcher
    p = HtmlPatcher('deliverables/xxx_v4.7.html', 'deliverables/xxx_v4.9.html')
    p.bump_version('v4.7', 'v4.9')
    p.patch('<old html>', '<new html>', '1. 描述')
    p.save()
"""
import re
import sys


class HtmlPatcher:

    def __init__(self, src_path: str, dst_path: str | None = None):
        self._src = src_path
        self._dst = dst_path or src_path
        with open(src_path, 'r', encoding='utf-8') as f:
            self._html = f.read()
        self._count = 0

    @property
    def html(self) -> str:
        return self._html

    @html.setter
    def html(self, value: str):
        self._html = value

    def patch(self, old: str, new: str, desc: str, n: int = 1) -> None:
        """精确字符串替换。old 必须恰好出现 n 次，否则 raise。"""
        cnt = self._html.count(old)
        if cnt != n:
            sys.exit(f'[FAIL] {desc}: expected {n} match, got {cnt}')
        self._html = self._html.replace(old, new)
        self._count += 1
        suffix = f' (×{n})' if n != 1 else ''
        print(f'[OK] {desc}{suffix}')

    def patch_re(self, pattern: str, repl: str, desc: str, count: int = 1, flags: int = 0) -> None:
        """正则替换。替换次数必须恰好等于 count。"""
        compiled = re.compile(pattern, flags)
        matches = compiled.findall(self._html)
        if len(matches) != count:
            sys.exit(f'[FAIL] {desc}: expected {count} regex match, got {len(matches)}')
        self._html = compiled.sub(repl, self._html, count=count)
        self._count += 1
        print(f'[OK] {desc}')

    def bump_version(self, old_ver: str, new_ver: str) -> None:
        """替换 <title>、CSS 注释、JS 注释中的版本号字符串。"""
        hits = self._html.count(old_ver)
        if hits == 0:
            sys.exit(f'[FAIL] bump_version: "{old_ver}" not found')
        self._html = self._html.replace(old_ver, new_ver)
        self._count += 1
        print(f'[OK] bump_version: {old_ver} → {new_ver} ({hits} occurrences)')

    def save(self) -> None:
        with open(self._dst, 'w', encoding='utf-8') as f:
            f.write(self._html)
        label = self._dst if self._dst != self._src else 'in-place'
        print(f'✅ {self._count} patches applied → {label}')
