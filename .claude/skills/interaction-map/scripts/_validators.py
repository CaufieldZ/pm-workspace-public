#!/usr/bin/env python3
"""IMAP invariant 共享校验。规则定义见 .claude/runbooks/info-ownership.md §A.3。"""
import re
from pathlib import Path

POOL_POLICY_RE = re.compile(
    r'Top\s*\d+|\d+\s*d\s*收益率|近\s*\d+\s*天|权重\s*[\d\.]+%?'
)
EVENT_NAME_RE = re.compile(r'\b[a-z]{3,}(?:_[a-z]+){1,}\b')
FIELD_TABLE_RE = re.compile(
    r'<table[^>]*>(?:[\s\S]*?<tr[^>]*>[\s\S]*?</tr>){3,}[\s\S]*?</table>'
)
STATE_ENUM_RE = re.compile(
    r'(loading|空态|错误态|状态\s*\d|empty|error)\s*[/／、,，]\s*'
    r'(loading|空态|错误态|状态\s*\d|empty|error)',
    re.IGNORECASE,
)
ANN_CARD_OPEN_RE = re.compile(r'<div\s+class="ann-card[^"]*"[^>]*>')
DIV_TAG_RE = re.compile(r'<(/?)div\b[^>]*>')

# anno-n ↔ ann-num 对应校验（规则 2/4）。注解下沉到 .scene-anno 后，靠编号维持
# 「屏幕元素 ↔ 注解条目」关联并驱动 hover 联动，故对应关系升级为自动门。
_SECTION_OPEN_RE = re.compile(
    r'<div\b[^>]*\bclass="[^"]*\bfade-section\b[^"]*"[^>]*\bid="([^"]*)"[^>]*>'
)
_ANNO_N_RE = re.compile(r'<div\s+class="[^"]*\banno-n\b[^"]*"[^>]*>(.*?)</div>', re.S)
_ANN_NUM_RE = re.compile(r'<div\s+class="[^"]*\bann-num\b[^"]*"[^>]*>(.*?)</div>', re.S)
# 圈号 ①..⑳ → 阿拉伯，用于样式归类
_CIRCLED = {chr(c): str(i + 1) for i, c in enumerate(range(0x2460, 0x2474))}


def _num_text(raw):
    return re.sub(r'<[^>]+>|\s', '', raw).strip()


def _num_style(s):
    if not s:
        return 'other'
    # 限 ASCII 0-9：Python str.isdigit() 对 ① 等圈号也返回 True，会误判
    if all(ch in '0123456789' for ch in s):
        return 'arabic'
    if all(ch in _CIRCLED for ch in s):
        return 'circled'
    return 'other'


def _split_sections(html_text):
    """按 fade-section 切片，返回 [(section_id, section_text), ...]（含 PART 分隔块）。"""
    starts = [(m.group(1), m.start()) for m in _SECTION_OPEN_RE.finditer(html_text)]
    out = []
    for i, (sid, start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(html_text)
        out.append((sid, html_text[start:end]))
    return out


def _extract_ann_card_blocks(html_text):
    """提取 ann-card 块，返回 [(start_offset, block_text), ...]。"""
    blocks = []
    for m in ANN_CARD_OPEN_RE.finditer(html_text):
        start = m.start()
        depth = 1
        pos = m.end()
        while depth > 0:
            tag_m = DIV_TAG_RE.search(html_text, pos)
            if not tag_m:
                depth = 0
                pos = len(html_text)
                break
            depth += -1 if tag_m.group(1) == '/' else 1
            pos = tag_m.end()
        blocks.append((start, html_text[start:pos]))
    return blocks


def validate_part_stories(parts):
    """每个 PART 必须填 story 字段（.claude/runbooks/artifact-conventions.md §五 演讲叙事顺序「PART/章节用户故事陈述」强制）。

    技术骨架 / 数据流类 PART 可填 '—' 显式跳过；缺字段直接报错，不静默放空。
    """
    missing = [p.get('id', '?') for p in parts if not p.get('story')]
    if missing:
        raise ValueError(
            f'❌ 以下 PART 缺 story 字段（用户故事一句话，≤30 字）：{missing}\n'
            '   .claude/runbooks/artifact-conventions.md §五 演讲叙事顺序要求每个 PART 起头一句用户故事陈述。\n'
            '   技术骨架/数据流 PART 可填 "—" 显式跳过。'
        )


def validate_part_stories_from_scene_list(parts, scene_list_path):
    """parts[].story 必须是 scene-list 顶部「叙事主线：xxx」一行的子串。
    缺主线行 → 降级回 validate_part_stories + warn。"""
    if not scene_list_path or not Path(scene_list_path).exists():
        validate_part_stories(parts)
        return

    sl_text = Path(scene_list_path).read_text(encoding='utf-8')
    # 匹配 `> 叙事主线：xxx` / `叙事主线：xxx` / `> IA 切分：xxx` / `IA 切分：xxx`
    m = re.search(
        r'^\s*(?:>\s*)?(?:叙事主线|IA\s*切分)\s*[：:]\s*(.+?)\s*$',
        sl_text,
        re.M,
    )
    main_story = m.group(1).strip() if m else ''

    if not main_story:
        import sys
        print(
            f'⚠️  scene-list 顶部缺「叙事主线：xxx」一行（路径：{scene_list_path}）\n'
            f'   修法：在 scene-list.md 顶部加 `> 叙事主线：xxx`（≤ 30 字）；规则系统型可写「IA 切分：xxx」。',
            file=sys.stderr,
        )
        validate_part_stories(parts)
        return

    bad = [(p.get('id', '?'), s) for p in parts
           if (s := p.get('story', '')) and s != '—' and s not in main_story]
    if bad:
        lines = '\n'.join(f'   PART {pid}：「{story}」' for pid, story in bad)
        raise ValueError(
            f'❌ 以下 PART story 与 scene-list 顶部叙事主线脱钩：\n{lines}\n'
            f'   主线：{main_story}\n'
            f'   规则：parts[].story 必须是叙事主线的子串，或填 "—" 跳过。'
        )

    validate_part_stories(parts)


def validate_ann_card_four_bans(html_path):
    """ann-card 四禁 lint，返回 [(severity, msg), ...]，severity ∈ {'FAIL', 'WARN'}。"""
    findings = []
    text = Path(html_path).read_text(encoding='utf-8')

    for block_offset, block in _extract_ann_card_blocks(text):
        if FIELD_TABLE_RE.search(block):
            findings.append((
                'FAIL',
                f'ann-card 含 ≥ 3 行字段表（offset {block_offset}） → '
                '改为 `<span class="ref">→ PRD §3.2「{对象}.{字段中文名}」</span>`',
            ))

        for hit in STATE_ENUM_RE.finditer(block):
            findings.append((
                'FAIL',
                f'ann-card 含状态全集列举「{hit.group()}」（offset {block_offset + hit.start()}） → '
                '改为 `<span class="ref">→ 原型「{view}-{page}」状态全集</span>`',
            ))

        for hit in POOL_POLICY_RE.finditer(block):
            findings.append((
                'FAIL',
                f'ann-card 含池策略参数「{hit.group()}」（offset {block_offset + hit.start()}） → '
                '改为 `<span class="ref">→ context §6「{规则名}」</span>`',
            ))

        for hit in EVENT_NAME_RE.finditer(block):
            prefix = block[max(0, hit.start() - 20):hit.start()]
            if re.search(r'class\s*=\s*"[^"]*$|id\s*=\s*"[^"]*$', prefix) or \
               prefix.endswith('.') or prefix.endswith('#'):
                continue
            findings.append((
                'FAIL',
                f'ann-card 疑似 event / 属性 key「{hit.group()}」（offset {block_offset + hit.start()}） → '
                '改为 `<span class="ref">→ PRD §9「{event 中文名}」</span>`',
            ))

        plain = re.sub(r'<[^>]+>|\s', '', block)
        if len(plain) > 80:
            findings.append((
                'WARN',
                f'ann-card 正文 {len(plain)} 字 > 80（offset {block_offset}）',
            ))

        item_count = len(re.findall(r'class="ann-item[^"]*"', block))
        if item_count > 5:
            findings.append((
                'FAIL',
                f'ann-card ann-item 数 {item_count} > 5（offset {block_offset}） → '
                '拆多张 ann-card 或精简',
            ))

    return findings


def validate_anno_correspondence(html_path):
    """anno-n ↔ ann-num 对应校验（规则 2/4），返回 [(severity, msg), ...]。

    逐 fade-section：仅对含屏幕徽章 .anno-n 的 scene 生效。
      - 规则 4：anno-n 与 ann-num 数字样式须一致（全阿拉伯 或 全圈号），混用 → FAIL
      - 规则 2：每个 anno-n 编号须在本 scene ann-card 的 .ann-num 里有对应条目，
        否则死链（hover 联动失效）→ FAIL
    """
    findings = []
    text = Path(html_path).read_text(encoding='utf-8')

    for sid, block in _split_sections(text):
        anno_vals = [v for v in (_num_text(m) for m in _ANNO_N_RE.findall(block)) if v]
        if not anno_vals:
            continue  # 该 scene 无屏幕锚点，跳过
        num_vals = [v for v in (_num_text(m) for m in _ANN_NUM_RE.findall(block)) if v]

        styles = {_num_style(v) for v in anno_vals + num_vals} - {'other'}
        if len(styles) > 1:
            findings.append((
                'FAIL',
                f'scene {sid}：anno-n 与 ann-num 数字样式混用（{"/".join(sorted(styles))}）'
                ' → 统一为阿拉伯数字 `1 2 3`（规则 4；混用则 hover 配不上）',
            ))
            continue  # 样式不一致时对应检查无意义，避免噪声

        num_set = set(num_vals)
        for a in anno_vals:
            if a not in num_set:
                findings.append((
                    'FAIL',
                    f'scene {sid}：屏幕徽章 anno-n「{a}」在本 scene ann-card 无对应 .ann-num'
                    ' → 补对应条目或删该徽章（规则 2 死链；hover 联动失效）',
                ))

    return findings
