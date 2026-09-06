"""md 输入版的扫描器 —— 与 scan.py（docx 版）平级，规则共享 patterns.py。

为什么不直接改 scan.py：
- docx 流程要保留（老项目修缮路径）
- md / docx 结构差异大，强行把 docx 接口套到 md 反而难读
- 规则源（patterns.py）100% 共享，行为一致

暴露：
    scan_human_voice_md(md_text) -> dict  # 对等 scan.scan_human_voice
    scan_prd_structural_md(md_text, scene_count) -> dict  # 对等 structural.scan_prd_structural

调用：
    md_text = open("prd-xxx-v1.md").read()  # 主 md
    # split 模式建议先 prd_compose.compose() 拼成完整 md 再扫
    voice_hits = scan_human_voice_md(md_text)
    struct_hits = scan_prd_structural_md(md_text, scene_count=10)
"""
from __future__ import annotations

import re
from typing import Iterator

from .patterns import (
    ASSERTABLE_RULE_CHAPTER_RE,
    BRANCH_MARKER_RE,
    BRANCH_MARKER_THRESHOLD,
    BULLET_LINE_RE,
    BULLET_RUNON_NARRATIVE_LABEL_RE,
    CIRCLE_NUM_RE,
    CJK_HALF_PUNCT_RE,
    CSS_IMPL,
    DATE_TAG,
    DECISION_NUM_RE,
    EXEMPT_H2_KW,
    EXEMPT_HEADER_KW,
    H2_V_TAG,
    LONG_SENTENCE_THRESHOLD,
    MD_NOISE_RE,
    NARRATIVE_LABEL_MAX_PERIODS,
    PERIOD_RUNON_RE,
    PLACEHOLDER_TOKENS,
    PM_EMOJI_RE,
    PM_OVERREACH_RE,
    PM_VISUAL_OVERREACH_RE,
    PRD_CHANGELOG_ITERATION_WORDS,
    ROUTE_URL_RE,
    SCENE_PROSE_LABEL_RE,
    SECTION_ANCHOR_RE,
    SEMICOLON_ABUSE_THRESHOLD,
    SEMICOLON_RE,
    SENTENCE_SPLIT_RE,
    SNAKE_FIELD,
    ZOMBIE_HEADING,
    is_exempt_chapter,
)

# 水平线：一行仅 3+ 个连字符。表格分隔行 |---| 含 | 不匹配，天然豁免；Confluence 不渲染且显示丑。
_HORIZONTAL_RULE_RE = re.compile(r"^-{3,}\s*$")


def _longest_sentence_len(line: str) -> int:
    """剥 markdown 噪音后按 。！？； 切句段，返回最长句段的字数。

    每段去掉行首列表 / 编号 / 引用标记再量，避免把 `- ` / `1. ` 算进长度。
    """
    cleaned = MD_NOISE_RE.sub("", line).replace("*", "")
    longest = 0
    for seg in SENTENCE_SPLIT_RE.split(cleaned):
        seg = seg.strip().lstrip("-*>#0123456789. 、)）")
        longest = max(longest, len(seg))
    return longest


_QUOTE_PAIR_RE = re.compile(r'[「『][^」』]*[」』]|“[^”]*”|"[^"]*"')


def _has_bullet_period_runon(line: str) -> bool:
    """剥引号内内容（引号内 。！？ 不算句末）+ 冒号结尾父 bullet 豁免后，判 bullet 行内句号是否串并列项。"""
    stripped = _QUOTE_PAIR_RE.sub("", line)
    cleaned = MD_NOISE_RE.sub("", stripped)
    if cleaned.rstrip().endswith(("：", ":")):
        return False
    return bool(PERIOD_RUNON_RE.search(cleaned))


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE_RE = re.compile(r"^```")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
_TECH_FIELDS_RE = re.compile(
    r"^\s*-?\s*\*\*(触发|读|写|事件|API\s*schema|API|DB\s*schema|DB|表结构|字段映射)\*\*[：:]"
)


def _iter_lines_with_h2(text: str) -> Iterator[tuple[int, str, str, str, bool]]:
    """逐行迭代 md，产生 (line_no, line_text, current_h1, current_h2, in_heading)。

    跳过 fenced codeblock 内容 + HTML 注释块（<!-- ... -->）。
    """
    in_fence = False
    in_html_comment = False
    current_h1 = ""
    current_h2 = ""
    for i, line in enumerate(text.splitlines(), 1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue  # 围栏行本身不 yield
        if in_fence:
            continue  # fence 内行不 yield（mermaid / code 不参与扫描）
        # 多行 HTML 注释
        if not in_html_comment and "<!--" in line and "-->" not in line:
            in_html_comment = True
            continue
        if in_html_comment:
            if "-->" in line:
                in_html_comment = False
            continue
        # 行内 <!-- ... --> 一行闭合
        if "<!--" in line and "-->" in line:
            continue
        m = _HEADING_RE.match(line)
        if m:
            hashes, title = m.groups()
            if len(hashes) == 1:
                current_h1 = title.strip()
                current_h2 = ""
            elif len(hashes) == 2:
                current_h2 = title.strip()
            yield i, line, current_h1, current_h2, True
            continue
        yield i, line, current_h1, current_h2, False


def _is_in_chapter_2(h1: str) -> bool:
    """是否在第 2 章场景地图章节内（裸场景编号在此豁免）"""
    return h1.startswith("2.")


def _gather_table_cells(text: str) -> list[tuple[str, str, str, int, dict[str, str]]]:
    """提取表格 cell 内容 [(cell_text, h2_context, header_text, line_no, row_dict), ...]"""
    cells: list[tuple[str, str, str, int, dict[str, str]]] = []
    in_fence = False
    current_h2 = ""
    table_headers: list[str] = []
    in_table_body = False
    for i, line in enumerate(text.splitlines(), 1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING_RE.match(line)
        if m:
            hashes, title = m.groups()
            if len(hashes) == 2:
                current_h2 = title.strip()
            in_table_body = False
            table_headers = []
            continue
        if not _TABLE_ROW_RE.match(line):
            in_table_body = False
            table_headers = []
            continue
        if _TABLE_SEP_RE.match(line):
            in_table_body = True
            continue
        cells_in_line = [c.strip() for c in line.strip("|").split("|")]
        if not in_table_body and not table_headers:
            table_headers = cells_in_line
            continue
        row_dict = {
            (table_headers[ci] if ci < len(table_headers) else f"_col{ci}"): ct
            for ci, ct in enumerate(cells_in_line)
        }
        for col_idx, cell_text in enumerate(cells_in_line):
            if not cell_text:
                continue
            header = table_headers[col_idx] if col_idx < len(table_headers) else ""
            cells.append((cell_text, current_h2, header, i, row_dict))
    return cells


def _is_exempt_h2(h2_text: str) -> bool:
    return any(kw in h2_text for kw in EXEMPT_H2_KW)


def _is_exempt_header(header: str) -> bool:
    return any(kw in header for kw in EXEMPT_HEADER_KW)


def scan_human_voice_md(md_text: str) -> dict:
    """扫 md PRD 的「讲人话」违规。返回各类 hits 列表。

    返回字段：
        date_tag_hits        list[str]
        snake_field_hits     list[str]
        css_impl_hits        list[str]
        zombie_heading_hits  list[str]
        v_tag_heading_hits   list[str]
        tech_field_hits      list[str]   # md 版独有：5 段式禁用研发字段
        pm_overreach_hits    list[str]   # PM 角色越界（hover / DOM / i18n / modal 等）
        visual_overreach_hits list[str]  # PM 视觉越界（颜色 / 尺寸 / 描边 / 圆角 / ✕ 等）
        semicolon_abuse_hits list[str]   # 单行 ≥ 2 分号（应拆 bullet / 编号）
        long_sentence_hits   list[str]   # 句段 ≥ 100 字（应拆句 / 转列表）
        bullet_runon_hits    list[str]   # bullet 行内句号串并列项（应一项一 bullet）
        scene_prose_runon_hits list[str] # §2.x 现状 / 本轮标签 bullet 句号串句（FAIL 级）
    """
    date_tag_hits: list[str] = []
    snake_field_hits: list[str] = []
    css_impl_hits: list[str] = []
    zombie_heading_hits: list[str] = []
    v_tag_heading_hits: list[str] = []
    tech_field_hits: list[str] = []
    pm_overreach_hits: list[str] = []
    visual_overreach_hits: list[str] = []
    semicolon_abuse_hits: list[str] = []
    long_sentence_hits: list[str] = []
    bullet_runon_hits: list[str] = []
    scene_prose_runon_hits: list[str] = []

    for line_no, line, _h1, h2, in_heading in _iter_lines_with_h2(md_text):
        if in_heading:
            if ZOMBIE_HEADING.search(line):
                zombie_heading_hits.append(f"L{line_no}: {line.strip()[:80]}")
            if H2_V_TAG.search(line):
                v_tag_heading_hits.append(f"L{line_no}: {line.strip()[:80]}")
            continue
        # 章节豁免（句号维度）：H1 或 H2 命中豁免名单即整章免查长句 / bullet 串句
        # （与 check_bullet_density block 一致——它在任一 H1/H2 边界重置 in_exempt）
        _exempt_chapter = is_exempt_chapter(_h1) or is_exempt_chapter(h2)
        if _FENCE_RE.match(line) or line.strip().startswith("```"):
            continue
        if not line.strip():
            continue
        m = DATE_TAG.search(line)
        if m:
            date_tag_hits.append(f"L{line_no}: {m.group()}")
        m = CSS_IMPL.search(line)
        if m:
            css_impl_hits.append(f"L{line_no}: {m.group()}")
        if not _is_exempt_h2(h2):
            m = SNAKE_FIELD.search(line)
            if m:
                snake_field_hits.append(f"L{line_no} [{h2[:20]}]: {m.group()}")
        m = _TECH_FIELDS_RE.match(line)
        if m:
            tech_field_hits.append(f"L{line_no}: {m.group(0).strip()}")
        for m in PM_OVERREACH_RE.finditer(line):
            pm_overreach_hits.append(f"L{line_no} [{h2[:20]}]: {m.group()} in {line.strip()[:60]}")
        for m in PM_VISUAL_OVERREACH_RE.finditer(line):
            visual_overreach_hits.append(f"L{line_no} [{h2[:20]}]: {m.group()} in {line.strip()[:60]}")
        for m in PM_EMOJI_RE.finditer(line):
            visual_overreach_hits.append(f"L{line_no} [{h2[:20]}]: 图标 emoji「{m.group()}」（写功能名即可，图标由设计定）in {line.strip()[:60]}")
        # 分号滥用 + 长句：表格行豁免（cell 内 `；` 是 md_to_confluence 切 bullet 的约定分隔符）
        if not _TABLE_ROW_RE.match(line):
            sc = len(SEMICOLON_RE.findall(line))
            if sc >= SEMICOLON_ABUSE_THRESHOLD:
                semicolon_abuse_hits.append(f"L{line_no} [{h2[:20]}]: {sc} 个分号 in {line.strip()[:60]}")
            # 长句：决策 / 变更 / 埋点章豁免——「方案。理由。阻塞。」论证叙事一句可以长，
            # 硬砍反而割裂推理。这是章节豁免唯一的口子（block 层不给，仅此 WARN 维度放过）。
            seg_len = _longest_sentence_len(line)
            if seg_len >= LONG_SENTENCE_THRESHOLD and not _exempt_chapter:
                long_sentence_hits.append(f"L{line_no} [{h2[:20]}]: 最长句段 {seg_len} 字 in {line.strip()[:50]}")
            # bullet 串句：bullet 行内句号没落行尾、后面还跟实质内容 = 多条并列断言焊一行。
            # 无章节豁免——决策 / 埋点章 3 句焊一行照样该拆标签 bullet（与 block 句号维度一致）。
            # 仅 delta 叙事标签豁免（「**现状**：X。本轮：Y」因果对照双段，句号 ≤2）——句号 ≥3
            # 说明标签下焊多件独立事，不再算叙事对，仍报。
            _narrative_ok = (BULLET_RUNON_NARRATIVE_LABEL_RE.match(line)
                             and line.count("。") <= NARRATIVE_LABEL_MAX_PERIODS)
            if BULLET_LINE_RE.match(line) and not _narrative_ok:
                if _has_bullet_period_runon(line):
                    bullet_runon_hits.append(f"L{line_no} [{h2[:20]}]: bullet 句号串并列项 in {line.strip()[:60]}")
            # 场景正文串句（FAIL）：§2.x 需求正文的 现状 / 本轮 标签 bullet 不吃叙事豁免，
            # 该结构化（一 bullet 一原子事实 / 多阶段用 →）。§6 决策 h1='6.' 够不着，零误伤。
            if _is_in_chapter_2(_h1) and SCENE_PROSE_LABEL_RE.match(line):
                if _has_bullet_period_runon(line):
                    scene_prose_runon_hits.append(f"L{line_no} [{h2[:20]}]: 场景正文标签 bullet 焊多句（改一 bullet 一事实 / 多阶段用 →）in {line.strip()[:60]}")

    for cell, h2, header, line_no, _ in _gather_table_cells(md_text):
        if _is_exempt_h2(h2) or _is_exempt_header(header):
            continue
        m = SNAKE_FIELD.search(cell)
        if m:
            snake_field_hits.append(
                f"L{line_no} [表/{h2[:15]}/{header[:10]}]: {m.group()}"
            )

    return {
        "date_tag_hits": date_tag_hits,
        "snake_field_hits": snake_field_hits,
        "css_impl_hits": css_impl_hits,
        "zombie_heading_hits": zombie_heading_hits,
        "v_tag_heading_hits": v_tag_heading_hits,
        "tech_field_hits": tech_field_hits,
        "pm_overreach_hits": pm_overreach_hits,
        "visual_overreach_hits": visual_overreach_hits,
        "semicolon_abuse_hits": semicolon_abuse_hits,
        "long_sentence_hits": long_sentence_hits,
        "bullet_runon_hits": bullet_runon_hits,
        "scene_prose_runon_hits": scene_prose_runon_hits,
    }


def scan_prd_structural_md(md_text: str, scene_count: int = 0) -> dict:
    """扫 md PRD 的结构 / 内容硬错误。

    Args:
        md_text: 完整 md 字符串（split 模式先 compose 后传入）
        scene_count: 场景数（来自 scene-list.md），用于段落 / 表格数下限
    """
    circle_nums = sorted(set(CIRCLE_NUM_RE.findall(md_text)))
    placeholders = [kw for kw in PLACEHOLDER_TOKENS if kw in md_text]
    if "{{ 待填" in md_text:
        placeholders.append("{{ 待填")

    decision_nums: list[str] = []
    section_anchors: list[str] = []
    route_urls: list[str] = []
    cjk_half_punct: list[str] = []
    bare_scene_codes: list[str] = []
    broken_image_alt: list[str] = []
    iteration_traces: list[str] = []
    branch_prose_hits: list[str] = []
    horizontal_rule_hits: list[str] = []
    blockquote_hits: list[str] = []

    in_changelog = False
    section_text_lines: list[str] = []
    for _line_no, line, _h1, _h2, in_heading in _iter_lines_with_h2(md_text):
        if in_heading:
            if line.startswith("## 1.4"):
                in_changelog = True
                continue
            else:
                in_changelog = False
        if in_changelog:
            section_text_lines.append(line)
    section_changelog = "\n".join(section_text_lines)
    iteration_traces = [w for w in PRD_CHANGELOG_ITERATION_WORDS if w in section_changelog]

    # 用户故事引言现在只在场景级 h3（### X.Y M-/A-/D- ...）下要求，
    # 所有 H1 一级章（含场景章 5/6/7）都是骨架章，不查 H1 引言。
    # artifact-conventions.md §五「PART / 场景用户故事陈述」铁律对齐。
    for line_no, line, h1, h2, in_heading in _iter_lines_with_h2(md_text):
        if _FENCE_RE.match(line):
            continue
        if not in_heading and DECISION_NUM_RE.search(line):
            decision_nums.append(f"L{line_no} [{h2[:20]}]: {line.strip()[:60]}")
        if not in_heading and SECTION_ANCHOR_RE.search(line):
            section_anchors.append(f"L{line_no} [{h2[:20]}]: {line.strip()[:60]}")
        if not in_heading:
            # 扫具体 URL / 路由：仅豁免 markdown 链接 / 图片（[text](url)）与 HTML <img> 的 URL 部分；
            # 反引号包裹的 `/xxx` 不豁免 —— PM 用 backtick 包路径仍是越权
            cleaned_for_url = re.sub(r"!?\[[^\]]*\]\([^)]*\)", "", line)
            cleaned_for_url = re.sub(r"<img\b[^>]*>", "", cleaned_for_url, flags=re.IGNORECASE)
            for m in ROUTE_URL_RE.finditer(cleaned_for_url):
                route_urls.append(f"L{line_no} [{h2[:20]}]: {m.group()} in {line.strip()[:60]}")
        if not in_heading and CJK_HALF_PUNCT_RE.search(line):
            cjk_half_punct.append(f"L{line_no}: {line.strip()[:60]}")
        # heading 豁免（章节标题允许「编号 · 白话名」格式）
        # 表格行豁免（场景地图表左列、Phase 表是锚点）
        # 注：第 2 章正文（非表格 / 非 heading）也要扫 —— 删掉过往过宽的整章豁免
        if not in_heading and not _TABLE_ROW_RE.match(line):
            # 整段擦掉 markdown 链接 / 图片（[text](url) / ![alt](path) 内的编号是锚点引用，豁免）
            cleaned = re.sub(r"!?\[[^\]]*\]\([^)]*\)", "", line)
            # 行级豁免：列表 bullet 行（- / *）+ ≥ 2 个编号 + / · | 分隔符 → 视为范围列表（P0 / Phase）
            # 例：「- **P0**：A 入口导航 / B-1 Tab 状态筛选 / ...」
            # 段落 / blockquote（> 起的）不豁免，那里通常是叙述性引用，应抓
            stripped = line.lstrip()
            is_bullet = stripped.startswith(("- ", "* "))
            all_codes = re.findall(r"\b[ABCDEFM]-\d+[a-z]?\b", cleaned)
            if is_bullet and len(all_codes) >= 2 and re.search(r"[/·|]", cleaned):
                continue
            for m in re.finditer(r"\b([ABCDEFM])-\d+[a-z]?\b", cleaned):
                pos = m.start()
                ctx = cleaned[max(0, pos - 5):pos + 10]
                # 引号 / 括号包裹豁免（场景名作专有名词时，如「A-1」、(M-2) 等）
                if any(c in ctx for c in ("「", "『", "(")):
                    continue
                bare_scene_codes.append(f"L{line_no}: {m.group()} in {line.strip()[:60]}")
        if not in_heading:
            for m in re.finditer(r"!\[\]\(([^)]+)\)", line):
                broken_image_alt.append(f"L{line_no}: empty alt for {m.group(1)}")
        # 条件分支散文规则（WARN）：仅全局业务规则章、非表格行 ≥ 2 个分支标记 → 建议改可断言表
        if not in_heading and not _TABLE_ROW_RE.match(line) and ASSERTABLE_RULE_CHAPTER_RE.search(h1):
            n = len(BRANCH_MARKER_RE.findall(line))
            if n >= BRANCH_MARKER_THRESHOLD:
                branch_prose_hits.append(f"L{line_no} [{h2[:20]}]: {n} 个分支标记 in {line.strip()[:60]}")
        # 水平线 ---（FAIL）：Confluence 不渲染 md 水平线且显示丑，章节用 h1/h2 自然分隔
        if not in_heading and _HORIZONTAL_RULE_RE.match(line):
            horizontal_rule_hits.append(f"L{line_no}: {line.rstrip()}")
        # 引用块 >（FAIL）：Confluence blockquote 渲染丑（竖线 + 灰底），业务故事用 **业务故事**：正文
        if not in_heading and re.match(r"^\s*>", line):
            blockquote_hits.append(f"L{line_no}: {line.rstrip()}")

    scene_count_observed = 0
    for _, line, _, _, in_heading in _iter_lines_with_h2(md_text):
        if not in_heading:
            continue
        # 兼容 single（## N.x A-y · 名）和 split 子文件展开后（## N.x A-y · 名）
        if re.search(r"^##+ \d+\.\d+\s+[A-Z][-\w]*\s*·", line):
            scene_count_observed += 1

    # 5/6/7 章子场景嵌套检查：允许一层物理分组嵌套（5.1.1），禁两层（5.1.1.1）
    # 规则：5/6/7 章里 heading 含 4 级编号（5.1.1.1 / 6.2.3.1 / 7.1.1.1 ...）即违规。
    # 合法形态：`### 5.1 主舞台`（无场景号）+ `#### 5.1.1 A-1 · 推流`（H4 叶子带场景号）。
    # 不限 `#` 数（项目 scene 可能在 h2/h3/h4 层级），不抓未编号子区（### 创建开播 类组织性区段豁免）。
    nested_subscenes: list[str] = []
    _NESTED_HEADING_RE = re.compile(r"^#+\s+([567])\.\d+\.\d+\.\d+\b")
    in_fence = False
    for line_no, raw_line in enumerate(md_text.splitlines(), 1):
        if _FENCE_RE.match(raw_line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _NESTED_HEADING_RE.match(raw_line)
        if m:
            nested_subscenes.append(f"L{line_no}: {raw_line.strip()[:80]}")

    # 场景块 li 重复标签前缀（WARN）：三段式标签（显示逻辑 / 显示要素 / 交互）每个区块
    # 只该做一次组头、子规则缩一级 bullet；逐条 li 都焊「显示逻辑：」前缀 = 结构冗余，
    # 行形状检查（分号 / 长句）各自看单行都合格，抓不到。连续 ≥ 3 条同前缀 li 报一处。
    label_li_runs: list[str] = []
    _LABEL_LI_RE = re.compile(r"^\s*<li>\s*(显示逻辑|显示要素|交互)：")
    _LABEL_RUN_THRESHOLD = 3
    run_label, run_start, run_len = None, 0, 0
    in_fence = False
    for line_no, raw_line in enumerate(md_text.splitlines(), 1):
        if _FENCE_RE.match(raw_line):
            in_fence = not in_fence
        if in_fence:
            continue
        m = _LABEL_LI_RE.match(raw_line)
        if m and m.group(1) == run_label:
            run_len += 1
        else:
            if run_len >= _LABEL_RUN_THRESHOLD:
                label_li_runs.append(
                    f"L{run_start}: 连续 {run_len} 个「{run_label}：」前缀 li（标签做组头一次，子项缩一级 bullet）"
                )
            run_label = m.group(1) if m else None
            run_start, run_len = line_no, (1 if m else 0)
    if run_len >= _LABEL_RUN_THRESHOLD:
        label_li_runs.append(
            f"L{run_start}: 连续 {run_len} 个「{run_label}：」前缀 li（标签做组头一次，子项缩一级 bullet）"
        )

    return {
        "circle_nums": circle_nums,
        "placeholders": placeholders,
        "decision_nums": decision_nums,
        "section_anchors": section_anchors,
        "route_urls": route_urls,
        "cjk_half_punct": cjk_half_punct,
        "iteration_traces": iteration_traces,
        "bare_scene_codes": bare_scene_codes,
        "broken_image_alt": broken_image_alt,
        "nested_subscenes": nested_subscenes,
        "branch_prose_hits": branch_prose_hits,
        "horizontal_rule_hits": horizontal_rule_hits,
        "blockquote_hits": blockquote_hits,
        "label_li_runs": label_li_runs,
        "scene_count_observed": scene_count_observed,
    }
