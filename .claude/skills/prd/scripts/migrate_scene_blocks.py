#!/usr/bin/env python3
"""场景块形态迁移：平铺式 → 组头式（单遍扫描原地替换，改前过文本等价门）。

平铺式与组头式的差别只在标签挂法，正文一字不动：
    平铺  <ol><li>显示逻辑：<ul><li>规则</li></ul></li><li>显示要素：文本</li></ol>
    组头  <ul><li><strong>显示逻辑</strong><ul><li>规则</li></ul></li>…</ul>

安全构造（禁拆段重组——不用 partition / split 取头尾再拼回）：
    ① 平衡扫描定位 <ol> 块，块外字符按偏移原样切片拼回，构造上不会丢段
    ② 只转「顶层 li 全部以三段式标签开头」的块；混标签块整块跳过并列出行号
    ③ 文本等价门：剥标签与标签词后逐块比对 + 非空白字符数不变量（按实际丢弃的分隔符
       与并掉的重复标签计）；任一块不过 = 解析器有 bug，整篇中止不写盘
    ④ 缺省 dry-run；--apply 才写盘，写前落 <file>.bak

用法：
    python3 migrate_scene_blocks.py <file> [--apply]          # 单文件干跑 / 落盘
    python3 migrate_scene_blocks.py <dir> --report            # 目录存量普查（递归）

示例：
    python3 migrate_scene_blocks.py projects/<产品线>/deliverables/<季度>/<版本>/prd-<产品线>-<版本>.md
    python3 migrate_scene_blocks.py projects/<产品线>/deliverables/<季度>/<版本>/prd-<产品线>-<版本>.md --apply
    python3 migrate_scene_blocks.py projects/<产品线> --report

参数：
    <file|dir>  目标 .md；--report 模式可给目录（递归扫 *.md）
    --apply     真写盘（缺省 dry-run 只打印块数与样例）；写前落 <file>.bak
    --report    只统计存量，不改任何文件

前置：
    - 目标存在且是 .md；块解析依赖 li / ol 开闭标签平衡
    - 只认 HTML 场景块（<ol> + <li>）；md 原生列表不在此脚本范围
    - --help 本身无前置

退出码：
    0 — 完成（无可转块、或有混标签块被跳过）
    2 — 路径不存在 / 文本等价门或字符数不变量不过（不写盘）/ 写盘失败
"""
import argparse
import re
import sys
from pathlib import Path

LABELS = ("显示逻辑", "显示要素", "交互", "验收")
_LAB = '|'.join(LABELS)
# 顶层项开头 = 标签 + 可选（括注）+ 分隔符
# 分隔符三种平铺写法都认：冒号 / 间隔号 / 无分隔符直跟嵌套列表（纯加粗，零字符丢弃）
HEAD_RE = re.compile(r'^\s*(?:<strong>\s*)?(?P<label>' + _LAB + r')'
                     r'(?P<suffix>\s*(?:（[^）]*）)?)'
                     r'(?P<sep>\s*[：:]\s*|\s*·\s*|(?=\s*<(?:ul|ol)>))')
TAG_RE = re.compile(r'<[^>]+>')
# 任意位置的 li 标签头（不锚行首）：用于「块里疑似场景块但解析不出完整顶层项」的兜底判定
LABEL_ANY_RE = re.compile(r'<li>\s*(?:<strong>\s*)?(?:' + _LAB + r')')
GROUPED_RE = re.compile(r'<li>\s*<strong>\s*(?:' + _LAB + r')\s*</strong>\s*$', re.M)
# 归一化比对只看规则正文：两侧都把「标签 + 可选括注 + 分隔符」剥掉
# （平铺每项都带标签，组头只带一次，并被连续同标签合并吃掉重复项）
LABEL_STRIP_RE = re.compile(r'(?:' + _LAB + r')(?:\s*(?:（[^）]*）))?\s*(?:[：:]|·)?')


def find_blocks(text):
    """平衡扫描 <ol>…</ol>，返回 [(start, end)]（含标签本身）。"""
    spans, depth, start = [], 0, None
    for m in re.finditer(r'</?ol>', text):
        if m.group(0) == '<ol>':
            if depth == 0:
                start = m.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0 and start is not None:
                spans.append((start, m.end()))
                start = None
    return spans


def top_lis(inner):
    """取容器内顶层 <li>，返回 [(标签起点, 内容起点, 内容终点)]（相对 inner，不含标签本身）。"""
    items, depth, start, tstart = [], 0, None, None
    for m in re.finditer(r'</?li>', inner):
        if m.group(0) == '<li>':
            if depth == 0:
                start, tstart = m.end(), m.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0 and start is not None:
                items.append((tstart, start, m.start()))
                start = None
    return items


def item_children(rest):
    """取顶层项正文的子项：行内文本 + 尾部嵌套列表的顶层子项（原样保留子项内层标记）。"""
    children = []
    nested = re.search(r'<(ul|ol)>', rest)
    if nested is not None:
        lead = rest[:nested.start()].strip()
        if lead:
            children.append(lead)
        close = rest.rfind('</%s>' % nested.group(1))
        body = rest[nested.end():close]
        for _t, cstart, cend in top_lis(body):
            child = body[cstart:cend].strip()
            if child:
                children.append(child)
    else:
        lead = rest.strip()
        if lead:
            children.append(lead)
    return children


def convert_block(block, base_indent):
    """<ol> 块 → 组头式 <ul> 块；任一顶层项解析不了返回 (None, 0)。

    同一标签连续出现时并成一个组头（组头在每个区块内只出现一次），子项按原顺序排。
    """
    inner = block[len('<ol>'):-len('</ol>')]
    spans = top_lis(inner)
    if not spans:
        return None, 0, 0
    items, dropped = [], 0
    for _t, cstart, cend in spans:
        item = inner[cstart:cend]
        m = HEAD_RE.match(item)
        if not m:
            return None, 0, 0
        dropped += 1 if m.group('sep').strip() else 0   # 被吃掉的分隔符数（组头不带分隔符）
        items.append((m.group('label'), m.group('suffix').strip(), item_children(item[m.end():])))
    groups = []  # [label, suffix, 子项, 组头落在第几个顶层项]
    for idx, (label, suffix, kids) in enumerate(items):
        if groups and groups[-1][0] == label and groups[-1][1] == suffix:
            groups[-1][2].extend(kids)
            dropped += len(label) + len(suffix)     # 并掉的重复标签（组头只留一个）
        else:
            groups.append([label, suffix, list(kids), idx])
    at = {g[3]: g for g in groups}
    out, cursor = ['<ul>'], 0
    for idx, (tstart, _cstart, cend) in enumerate(spans):
        gap = inner[cursor:tstart]
        if gap.strip():
            out.append(gap.rstrip('\n'))
        cursor = cend + len('</li>')
        g = at.get(idx)
        if g is None:
            continue
        out.append('%s<li><strong>%s</strong>%s' % (base_indent + '  ', g[0], g[1]))
        out.append('%s  <ul>' % (base_indent + '  '))
        for c in g[2]:
            out.append('%s    <li>%s</li>' % (base_indent + '  ', c))
        out.append('%s  </ul>' % (base_indent + '  '))
        out.append('%s</li>' % (base_indent + '  '))
    tail = inner[cursor:]
    if tail.strip():
        out.append(tail.rstrip('\n'))
    out.append(base_indent + '</ul>')
    return '\n'.join(out), len(items), dropped


def norm(s):
    """比对基准：剥标签、剥三段式标签词（含括注与分隔符）、归一空白，只剩规则正文。"""
    return re.sub(r'\s+', '', LABEL_STRIP_RE.sub('', TAG_RE.sub('', s)))


def nonspace(s):
    return len(re.sub(r'\s+', '', TAG_RE.sub('', s)))


def migrate_text(text):
    """整篇迁移。返回 (新文本, 转换块数, 跳过块数, 硬错误清单)。"""
    pieces, cursor, n_conv, hard = [], 0, 0, []
    skipped = []
    for s, e in find_blocks(text):
        block = text[s:e]
        line_start = text.rfind('\n', 0, s) + 1
        indent = text[line_start:s]
        if indent.strip():                      # <ol> 不在行首（行内嵌），不碰
            continue
        inner = block[len('<ol>'):-len('</ol>')]
        spans = top_lis(inner)
        if not spans:
            # 有标签头的痕迹却拆不出完整顶层项 = 标签不平衡（写坏的块），报出来别静默放过
            if LABEL_ANY_RE.search(inner):
                hard.append('L%d：块内标签头存在但 li 未闭合（标签平衡存疑），不写盘'
                            % (text.count('\n', 0, s) + 1))
            continue                            # 普通编号列表，静默跳过
        heads = [bool(HEAD_RE.match(inner[c:d])) for _t, c, d in spans]
        if not any(heads):
            continue                            # 普通编号列表，静默跳过
        ln = text.count('\n', 0, s) + 1
        if not all(heads):
            skipped.append('L%d：块内混有非三段式标签的顶层项，整块跳过（人工确认）' % ln)
            continue
        new_block, n_items, dropped = convert_block(block, indent)
        if new_block is None:
            hard.append('L%d：块解析失败（标签平衡存疑），不写盘' % ln)
            continue
        if norm(block) != norm(new_block):
            hard.append('L%d：文本等价门不过（归一后正文不一致），不写盘' % ln)
            continue
        delta = nonspace(block) - nonspace(new_block)
        if delta != dropped:
            hard.append('L%d：字符数不变量不过（少 %d 字，应为 %d 个分隔符），不写盘' % (ln, delta, dropped))
            continue
        pieces.append(text[cursor:s])
        pieces.append(new_block)
        cursor = e
        n_conv += 1
    pieces.append(text[cursor:])
    return ''.join(pieces), n_conv, skipped, hard


def run_file(path, apply_=False, quiet=False):
    text = path.read_text(encoding='utf-8')
    new, n_conv, skipped, hard = migrate_text(text)
    if not quiet:
        print(f'  {path.name}: 可转平铺块 {n_conv} / 已组头块 {len(GROUPED_RE.findall(text))} / 混标签跳过 {len(skipped)}')
    for s in skipped:
        print(f'    ⚠️  {s}')
    if hard:
        for h in hard:
            print(f'  ❌ {h}')
        return n_conv, True
    if apply_ and n_conv:
        path.with_suffix(path.suffix + '.bak').write_text(text, encoding='utf-8')
        path.write_text(new, encoding='utf-8')
        if not quiet:
            print(f'    ✓ 已写盘（备份 {path.with_suffix(path.suffix + ".bak").name}）；接着跑 check_prd_md.sh 复核')
    elif not apply_ and n_conv and not quiet:
        first = new.find('<ul>')
        print('    样例（首块转换后）：')
        for ln in new[first:first + 400].splitlines()[:9]:
            print('      ' + ln)
    return n_conv, False


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('path', help='目标 .md；--report 模式可给目录（递归扫 *.md）')
    ap.add_argument('--apply', action='store_true',
                    help='真写盘（默认 dry-run 只打印将改的块）；写前备份 <file>.bak')
    ap.add_argument('--report', action='store_true',
                    help='只统计存量（可转平铺块 / 已组头块 / 混标签块），不改任何文件')
    a = ap.parse_args()
    p = Path(a.path)
    if not p.exists():
        print(f'❌ 路径不存在：{p}', file=sys.stderr)
        return 2
    targets = sorted(p.rglob('*.md')) if (p.is_dir() and a.report) else [p]
    total_c, bad = 0, False
    for t in targets:
        c, hard = run_file(t, apply_=a.apply and not a.report, quiet=a.report)
        total_c += c
        bad = bad or hard
    if a.report:
        print(f'  合计可转平铺块 {total_c}')
    elif not a.apply:
        print(f'  干跑：可转 {total_c} 块（加 --apply 落盘）')
    return 2 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
