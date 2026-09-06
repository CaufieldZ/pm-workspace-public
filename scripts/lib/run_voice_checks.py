"""统一 voice-checks 入口 — 给 check_proto.sh / check_imap.sh 调用。

合并两 hook 内重复的 Python heredoc。kind ∈ {'proto', 'imap'}：
- imap：全套（§1-§8 + FAIL 级内部代号 + 组件完整性 + 场景编号对照）
- proto：跳过 imap 专属（§4 编号 / §6-7 组件 / §8 FAIL 正则），改输出 §4 数据数组 info

stdout 格式保持与原两 hook 一致（避免破坏既有 CI / 阅读习惯）。

返回 exit_code（0/1/2）由调用方 sys.exit。
"""
from __future__ import annotations

import os
import re
import sys
from typing import Optional

from lib.business_voice import scan_business_voice
from lib.changelog_residue import scan_residue
from lib.html_basics import (
    check_fill_placeholders,
    check_font_cjk_priority,
    check_html_closed,
    check_line_count,
)
from lib.tech_jargon import load_jargon
from lib.thinking_process import scan_thinking
from lib.thresholds import VOICE_CHECK_HTML_MIN_LINES
from lib.ui_visual import scan_ui_visual
from lib.visible_text import iter_code_tags, iter_visible_text

# IMAP 专属 FAIL 级正则
_DECISION_RE = re.compile(r'决策\s*\d+')
_CONTEXT_RE = re.compile(r'context\s*第\s*\d+\s*章', re.I)
# 裸场景编号：后面不紧跟 · / ↗ / → / ↘ / 同结构 等锚点 / 跳转标记
_BARE_SCENE_RE = re.compile(r'(?<![A-Za-z0-9\-])([A-Z]-\d+[a-z]?)(?!\s*[·•→↗↘↙↖])')


def run_voice_checks(
    *,
    kind: str,
    html_path: str,
    scene_list_path: Optional[str] = None,
) -> int:
    """执行 voice-checks 全套，print 到 stdout/stderr，返回 exit_code。

    kind: 'proto' 或 'imap'
    """
    if kind not in ('proto', 'imap'):
        raise ValueError(f"kind must be 'proto' or 'imap', got {kind!r}")

    label = 'IMAP' if kind == 'imap' else 'prototype'

    with open(html_path, encoding='utf-8') as f:
        html_text = f.read()

    fail_msgs: list[str] = []
    warn_count = 0

    # ── §1. 基础结构 ─────────────────────────────────────
    print()
    print('--- §1. 基础结构 ---')
    n_lines, ok = check_line_count(html_text, min_lines=VOICE_CHECK_HTML_MIN_LINES)
    print(f'  总行数: {n_lines}')
    if not ok:
        fail_msgs.append(f'行数异常 (< {VOICE_CHECK_HTML_MIN_LINES}): {n_lines}')
        if kind == 'imap':
            print('  ❌ 行数 < 500，HTML 不完整')
    if check_html_closed(html_text):
        print('  ✅ HTML 已闭合')
    else:
        print('  ❌ HTML 未闭合')
        fail_msgs.append('HTML 未闭合')

    # ── §2. 字体顺序 ─────────────────────────────────────
    print()
    print('--- §2. 字体顺序 ---')
    font_bad = check_font_cjk_priority(html_text)
    if font_bad:
        for b in font_bad:
            print(f'  ❌ {b}')
            fail_msgs.append(
                f'字体顺序违规: {b}' if kind == 'imap' else f'字体顺序: {b}'
            )
    else:
        print('  ✅ 字体顺序正确')

    # ── §3. 占位符 ─────────────────────────────────────
    print()
    print('--- §3. 占位符 ---')
    fill_hits = check_fill_placeholders(html_text)
    if fill_hits:
        for kw, n in fill_hits:
            print(f'  ❌ 残留「{kw}」共 {n} 处')
            fail_msgs.append(
                f'占位残留 {kw} ×{n}' if kind == 'imap' else f'占位 {kw} ×{n}'
            )
    else:
        print('  ✅ 无占位残留')

    # ── §4. 分支：imap 编号对照 / proto 数据数组 ───────────
    if kind == 'imap':
        from lib.scene_match import extract_scene_ids, scene_code_report

        print()
        print('--- §4. 场景编号对照 ---')
        if scene_list_path:
            scene_ids = extract_scene_ids(scene_list_path)
            if not scene_ids:
                print('  ⚠️  scene-list 未提取到编号（格式可能坏）')
            else:
                undefined, missing = scene_code_report(scene_ids, html_text)
                if undefined:
                    print(f'  ❌ 引用越界编号: {" ".join(undefined)}')
                    fail_msgs.append(f'引用越界场景编号: {" ".join(undefined)}')
                if missing:
                    print(
                        f'  ⚠️  未覆盖编号 ({len(missing)}/{len(scene_ids)}): '
                        f'{" ".join(missing)}（delta IMAP 只覆盖本轮触及场景，属预期）'
                    )
                else:
                    print(f'  ✅ 全部 {len(scene_ids)} 个编号已覆盖')
        else:
            print('  ⏭️  无 scene-list（跳过）')
    else:
        # proto: info 输出，不阻断
        print()
        print('--- §4. 数据数组 ---')
        data_arrs = re.findall(r'const\s+(\w+)\s*=\s*\[', html_text)
        if data_arrs:
            for arr in sorted(set(data_arrs))[:20]:
                print(f'  • {arr}')

    # ── §5. JS 交互 ─────────────────────────────────────
    print()
    print('--- §5. JS 交互 ---')
    ev_count = len(re.findall(r'addEventListener|onclick|onchange|onClick', html_text))
    print(f'  事件绑定数: {ev_count}')
    if ev_count == 0:
        print('  ❌ 无任何交互事件')
        fail_msgs.append('无 JS 交互事件' if kind == 'imap' else '无 JS 交互')

    onclick_fns = set(
        re.findall(r'onclick="([A-Za-z_][A-Za-z0-9_]*)\s*\(', html_text)
    )
    missing_fns: list[str] = []
    for fn in onclick_fns:
        fn = fn.strip()
        if not fn:
            continue
        if fn in ('event', 'this', 'window', 'document', 'alert', 'console'):
            continue
        if not re.search(
            rf'function\s+{re.escape(fn)}\b|const\s+{re.escape(fn)}\b|'
            rf'{re.escape(fn)}\s*=',
            html_text,
        ):
            missing_fns.append(fn)
    if missing_fns:
        # proto 截前 10，imap 全报（保持原行为）
        report = missing_fns[:10] if kind == 'proto' else missing_fns
        for fn in report:
            print(f'  ❌ onclick 引用了不存在的函数: {fn}')
            fail_msgs.append(f'未定义函数: {fn}')

    # ── §6/§7. imap 专属：组件完整性 + 逐 Scene 检查 ─────────
    if kind == 'imap':
        from lib.html_components import (
            count_global_components,
            count_per_scene_components,
        )

        print()
        print('--- §6. IMAP 组件完整性 ---')
        counts = count_global_components(html_text)
        print(
            f'  Scene: {counts["scene"]} | .aw: {counts["aw"]} | '
            f'.anno: {counts["anno"]} | .ann-tag: {counts["ann-tag"]} | '
            f'.flow-note: {counts["flow-note"]}'
        )

        if counts['scene'] == 0:
            print('  ❌ 无 id="scene-*" 标记（结构错）')
            fail_msgs.append('无 scene 锚点')
        else:
            for cls in ('aw', 'anno', 'ann-tag', 'flow-note'):
                if counts[cls] == 0:
                    print(f'  ❌ 无任何 .{cls}')
                    fail_msgs.append(f'缺组件 .{cls}')
            min_aw = counts['scene'] - 1
            if min_aw > 0 and counts['aw'] < min_aw:
                print(f'  ⚠️  箭头数 ({counts["aw"]}) < Scene-1 ({min_aw})')

        print()
        print('--- §7. 逐 Scene 组件检查 ---')
        per_scene = count_per_scene_components(html_text)
        if per_scene:
            for sid, missing in per_scene:
                miss_str = ' '.join(f'.{c}' for c in missing)
                print(f'  ❌ Scene {sid} missing: {miss_str}')
                fail_msgs.append(f'Scene {sid} 缺组件 {miss_str}')
        else:
            if counts['scene'] > 0:
                print('  ✅ 所有 Scene 组件完整')

    # ── §8. 描述当前态四禁（warn）+ imap 专属 FAIL 级 ──────
    print()
    if kind == 'imap':
        print('--- §8. 文案讲人话 / 描述当前态 ---')
    else:
        print('--- §6. 描述当前态四禁 ---')

    domain_text = ''
    if scene_list_path and os.path.exists(scene_list_path):
        domain_text = open(scene_list_path, encoding='utf-8').read()[:3000]
    m_title = re.search(r'<title>([^<]+)</title>', html_text)
    if m_title:
        domain_text += '\n' + m_title.group(1)
    tech_patterns = load_jargon(context_text=domain_text)

    violations: list = []  # imap FAIL
    warn_hits: list = []

    for text, loc in iter_visible_text(html_text):
        if kind == 'imap':
            bad: list = []
            for m in _DECISION_RE.finditer(text):
                bad.append(('决策编号', m.group()))
            for m in _CONTEXT_RE.finditer(text):
                bad.append(('context 引用', m.group()))
            for m in _BARE_SCENE_RE.finditer(text):
                bad.append(('裸场景编号', m.group()))
            if bad:
                violations.append((loc, text[:80], bad))

        shared: list = []
        shared.extend(scan_residue(text))
        shared.extend(
            scan_business_voice(text, is_html=False, tech_patterns=tech_patterns)
        )
        shared.extend(scan_thinking(text, exempt_h2=None))
        shared.extend(scan_ui_visual(text, exempt_h2=None))
        if shared:
            warn_hits.append((loc, text[:80], shared))

    for code_text in iter_code_tags(html_text):
        warn_hits.append(('<code>', code_text[:80], [('code_tag', code_text)]))

    warn_count = len(warn_hits)
    if warn_count:
        print(f'  ⚠️  描述当前态 warn: {warn_count} 处（详见 stderr'
              + ('' if kind == 'imap' else '，不阻断')
              + '）')
        print(f'⚠️  {label} 描述当前态四禁 warn ({warn_count} 处)',
              file=sys.stderr)
        for loc, snippet, hits in warn_hits[:20]:
            hits_str = ', '.join(f'{c}={v}' for c, v in hits[:5])
            if len(hits) > 5:
                hits_str += f' ... (+{len(hits)-5})'
            print(f'  [{loc}] {snippet!r}', file=sys.stderr)
            print(f'    → {hits_str}', file=sys.stderr)
        if warn_count > 20:
            print(f'  ... 还有 {warn_count - 20} 处', file=sys.stderr)
    elif kind == 'proto':
        print('  ✅ 无 warn')

    # imap FAIL 级输出
    if kind == 'imap' and violations:
        print(f'  ❌ 内部代号违规: {len(violations)} 处')
        fail_msgs.append(f'内部代号违规 ×{len(violations)}')
        for loc, snippet, bads in violations[:10]:
            bad_str = ', '.join(f'{t}={v}' for t, v in bads)
            print(f'    [{loc}] {snippet!r} → {bad_str}')
        if len(violations) > 10:
            print(f'    ... +{len(violations) - 10}')

    # ── §N. 渲染 UI 屏内禁注解 ────────────────────────────
    from lib.ui_annotation import find_mockup_annotations

    print()
    print('--- 渲染 UI 屏内禁注解 ---')
    anno_findings = find_mockup_annotations(html_text, kind)
    if anno_findings:
        print(f'  ❌ mockup 屏内注解: {len(anno_findings)} 处（开发会误读为真实文案）')
        fail_msgs.append(f'mockup 屏内注解 ×{len(anno_findings)}')
        for loc, snippet, hits in anno_findings[:10]:
            hit_str = ', '.join(f'{c}={v}' for c, v in hits)
            print(f'    [{loc}] {snippet!r} → {hit_str}')
        if len(anno_findings) > 10:
            print(f'    ... +{len(anno_findings) - 10}')
        if kind == 'imap':
            print('    修法: 注解移到 mockup 外的 ann-card / flow-note，屏内只放真实文案')
        else:
            print('    修法: 删掉注解，屏内只放真实文案')
    else:
        print('  ✅ 渲染 UI 屏内无注解')

    # ── 页面可达性（proto：页面点不到 = 评审看不到 = 等于没做）──
    if kind == 'proto':
        from lib.proto_reachability import check_page_reachability

        print()
        print('--- 页面可达性 ---')
        reach = check_page_reachability(html_text)
        if reach.entry is None:
            print('  ⏭️  无 data-page 页面（非骨架原型，跳过）')
        else:
            if reach.unreachable:
                print(f'  ❌ 无入口页面: {" ".join(reach.unreachable)}'
                      f'（入口页 {reach.entry}，顺着 goPage 点不到）')
                fail_msgs.append(f'页面无入口: {" ".join(reach.unreachable)}')
            if reach.dead_static:
                print(f'  ❌ goPage 指向不存在的页面: {" ".join(reach.dead_static)}'
                      f'（点了黑屏）')
                fail_msgs.append(f'跳转死链: {" ".join(reach.dead_static)}')
            if reach.unreachable or reach.dead_static:
                print('    修法: 从已可达页面加入口（Tab 栏 / 按钮 / 卡片 onclick），'
                      '或改 goPage 目标为本端真实存在的 data-page')
            elif reach.dead_script:
                print('  ✅ 页面全部可达')
            else:
                print('  ✅ 页面全部可达，无跳转死链')
            if reach.dead_script:
                print(f'  ⚠️  脚本内跳转指向本端不存在的页面: '
                      f'{" ".join(reach.dead_script)}（多端共享 JS 的 dead code，不阻断）')

        print()
        print('--- 重复 id ---')
        _ids = re.findall(r'\bid="([^"]+)"', html_text)
        _seen: dict[str, int] = {}
        for _i in _ids:
            _seen[_i] = _seen.get(_i, 0) + 1
        _dups = sorted(k for k, c in _seen.items() if c > 1)
        if _dups:
            print(f'  ❌ 重复 id: {len(_dups)} 个（getElementById 只命中第一个，多 view 易致点击黑屏）')
            fail_msgs.append(f'重复 id ×{len(_dups)}')
            for _d in _dups[:10]:
                print(f'    - id="{_d}" ×{_seen[_d]}')
            if len(_dups) > 10:
                print(f'    ... +{len(_dups) - 10}')
            print('    修法: 页面用 data-page + 唯一 id（多 view 加 view 前缀），导航按 data-page scoped 查找')
        else:
            print('  ✅ 无重复 id')

    # ── 总结 ─────────────────────────────────────────────
    print()
    print('==========================================')
    if fail_msgs:
        print(f'  ❌ {label} 自检 FAIL ({len(fail_msgs)} 类)')
        for msg in fail_msgs:
            print(f'    - {msg}')
        if warn_count:
            print(f'  ⚠️  另有 {warn_count} 处 warn（不阻断'
                  + ('，详见 stderr' if kind == 'imap' else '')
                  + '）')
        return 1

    print(f'  ✅ {label} 自检通过')
    if warn_count:
        print(f'  ⚠️  另有 {warn_count} 处描述当前态 warn（不阻断，详见 stderr）')
    return 0
