"""Markdown 输出原语 —— 对等 docx 版 core/headings.py + core/tables.py 的 API 表面。

下游脚本用法（writer 模式）：

    from core.md_renderer import MdWriter
    w = MdWriter()
    w.h1("1. 项目背景与目标")
    w.chapter_story("用户在社区里发帖、看帖、跟单，平台靠内容分发撑留存。")
    w.h2("1.1 背景")
    w.paragraph("当前社区日活 12w，发帖率 3%...")
    w.bullet_list(["痛点 A", "痛点 B"])
    w.table(headers=["编号", "场景名", "优先级"],
            rows=[["A-1", "发帖", "P0"], ["A-2", "删帖", "P1"]])
    w.image("./assets/scene-a1-wireframe.png", alt="发帖低保真")
    md = w.render()

设计原则：
1. 所有输出走 CommonMark + GFM tables（Confluence md 宏、GitHub、VS Code、Typora 通吃）
2. 不在 API 层做颜色注入 —— 语义标签（【新增】/【必填】/【变更】）保持纯文本，
   由 push 层 md_to_confluence.py 按规则映射成 Confluence XHTML 色
3. 标点规范化不在这里做 —— save_prd_md 调 normalize_punctuation 统一处理（幂等）
4. 字段归属边界由 sections_md 编排决定，md_renderer 只提供原语

风格约束：
- 标题前保留一个空行（markdownlint MD022）
- 表格前后保留空行（MD058）
- 不写任何 HTML（除图片 alt 里可能出现的），保持纯 md 可读
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence

# ── 语义标签常量（push 层映射色用，这里只负责纯文本输出） ────────────────
TAG_NEW = "【新增】"
TAG_REQUIRED = "【必填】"
TAG_CHANGED = "【变更】"
TAG_REMOVED = "【删除】"
TAG_DEFERRED = "【本期不做】"

SEMANTIC_TAGS = (TAG_NEW, TAG_REQUIRED, TAG_CHANGED, TAG_REMOVED, TAG_DEFERRED)


# ── 骨架版本戳（产物防腐化：drift checker 据首行戳判定旧产物该刷新） ──────
_SKEL_STAMP_RE = re.compile(r"^[ \t]*<!-- @pm-skel v\d+ -->[ \t]*\n", re.MULTILINE)


def _workspace_skel_version() -> str:
    """读 _shared/workspace.json 的 skel_version（如 'v1'）。缺失/异常返回 ''。"""
    cfg = (
        Path(__file__).resolve().parents[5]
        / ".claude"
        / "skills"
        / "_shared"
        / "workspace.json"
    )
    try:
        return json.loads(cfg.read_text(encoding="utf-8")).get("skel_version", "")
    except (json.JSONDecodeError, OSError):
        return ""


def stamp_skel_version(md: str) -> str:
    """前置骨架版本戳 HTML 注释（幂等：先剥首行旧戳再前置新戳）。

    无 skel_version（workspace.json 未配）→ 原样返回，向后兼容。
    载体用 HTML 注释非 YAML frontmatter：避开 md_to_confluence 推送吞 frontmatter。
    被 MdWriter.render 与 split_prd 落盘点共用，保证所有 PRD md 产物带戳。
    """
    ver = _workspace_skel_version()
    if not ver:
        return md
    stripped = _SKEL_STAMP_RE.sub("", md, count=1)
    return f"<!-- @pm-skel {ver} -->\n\n{stripped.lstrip()}"


# ── Inline 原语（返回字符串，用于拼段落） ────────────────────────────────

def bold(text: str) -> str:
    """**text** —— 正文里强调标题或字段名"""
    return f"**{text}**"


def italic(text: str) -> str:
    """*text* —— 引言 / 注释"""
    return f"*{text}*"


def code_inline(text: str) -> str:
    """`text` —— 编号 / 事件名 / 枚举值"""
    return f"`{text}`"


def link(text: str, url: str) -> str:
    """[text](url) —— 外链或章内锚点"""
    return f"[{text}]({url})"


def anchor_ref(chapter: str, label: Optional[str] = None) -> str:
    """章内引用 —— 按约定，正文**禁出现**裸 A-1 / B-2 编号，
    但允许引用章节（"见 4.1 一帖一卡"）。本函数只做格式化，不检查语义。

        anchor_ref("4.1", "一帖一卡") → "见 4.1「一帖一卡」"
        anchor_ref("4.1")              → "见第 4.1 节"
    """
    if label:
        return f"见 {chapter}「{label}」"
    return f"见第 {chapter} 节"


# ── Writer 主类 ────────────────────────────────────────────────────────────

@dataclass
class MdWriter:
    """累积 md 片段，最后 render() 出完整字符串。

    每个 .h1/.h2/.paragraph/.table/... 调用 append 一个逻辑块到 self.parts；
    render 时用 "\n" 连接（块之间自然形成空行）。
    """
    parts: list[str] = field(default_factory=list)

    # ── 标题 ────────────────────────────────────────────────────────────
    def h1(self, text: str) -> None:
        self.parts.append(f"# {text}")

    def h2(self, text: str) -> None:
        self.parts.append(f"## {text}")

    def h3(self, text: str) -> None:
        self.parts.append(f"### {text}")

    def h4(self, text: str) -> None:
        self.parts.append(f"#### {text}")

    # ── 章节用户故事 / 重点引言 ──────────────────────────────────────────
    def chapter_story(self, text: str) -> None:
        """场景级 h3 下的业务故事（粗体引导）≤ 30 字。

        按 artifact-conventions.md §五「PART / 场景用户故事陈述」规则：真有角色动作的场景填实，
        entity 定义 / 渲染规则 / 后端算法 / 纯配置 / 兼容声明类场景免，PM 直接不调此方法。
        骨架占位 `{{ 待填：... }}` 免校验，PM 填实后超 30 字 raise。
        """
        if "{{ 待填" not in text and len(text) > 30:  # 阈值登记: thresholds.yaml §E prd_checks.story_chars
            raise ValueError(
                f"chapter_story 超长（{len(text)} 字 > 30）：{text!r}"
            )
        self.parts.append(f"**业务故事**：{text}")

    def pullquote(self, text: str) -> None:
        """no-op：PRD 禁引用块 >（Confluence blockquote 渲染丑）。保留签名避免调用方 AttributeError。"""
        pass

    # ── 段落 / 列表 ──────────────────────────────────────────────────────
    def paragraph(self, text: str) -> None:
        """普通段落。多行自动合并为一段（md 里单换行视为空格）。"""
        self.parts.append(text.strip())

    def bullet_list(self, items: Sequence[str], indent: int = 0) -> None:
        """无序列表。items 里元素可含 inline md（**bold** / `code` / [link]）。

        indent 用于嵌套（每级 2 空格）：
            w.bullet_list(["顶层 1", "顶层 2"])
            w.bullet_list(["子项 A", "子项 B"], indent=1)
        """
        prefix = "  " * indent + "- "
        lines = [f"{prefix}{item}" for item in items if item.strip()]
        if lines:
            self.parts.append("\n".join(lines))

    def ordered_list(self, items: Sequence[str]) -> None:
        """有序列表。禁用圈数字 ①②③（CLAUDE.md 全局规则）。"""
        lines = [f"{i + 1}. {item}" for i, item in enumerate(items) if item.strip()]
        if lines:
            self.parts.append("\n".join(lines))

    def field_bullet(self, name: str, value: str) -> None:
        """字段化 bullet —— 5 段式模板的主力：

            w.field_bullet("业务描述", "用户点『发布』把内容发到社区")
            → "- **业务描述**：用户点『发布』把内容发到社区"
        """
        self.parts.append(f"- **{name}**：{value}")

    def field_bullet_list(self, name: str, items: Sequence[str]) -> None:
        """字段 + 子列表（5 段式里前置 / 系统检查 / 数据影响用）：

            w.field_bullet_list("前置条件", ["已登录", "未被禁言"])
            →
            - **前置条件**：
              - 已登录
              - 未被禁言
        """
        if not items:
            return
        sub = "\n".join(f"  - {it}" for it in items if it.strip())
        self.parts.append(f"- **{name}**：\n{sub}")

    # ── 图 / 代码 ────────────────────────────────────────────────────────
    def image(self, path: str, alt: str = "", caption: Optional[str] = None) -> None:
        """嵌图。path 用相对路径（./assets/xxx.png），push 时脚本自动上传。

        caption 会作为图下一行的斜体小字（md 原生不支持 caption，土法）。
        """
        self.parts.append(f"![{alt}]({path})")
        if caption:
            self.parts.append(f"*{caption}*")

    def codeblock(self, code: str, lang: str = "") -> None:
        """围栏代码块。lang 可空（通用 text），常用：python / bash / json / mermaid。"""
        self.parts.append(f"```{lang}\n{code.rstrip()}\n```")

    def mermaid(self, diagram: str) -> None:
        """Mermaid 图。Confluence + GitHub + Typora + VS Code 都能渲染。"""
        self.codeblock(diagram, lang="mermaid")

    # ── 表 ──────────────────────────────────────────────────────────────
    def table(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[str]],
        aligns: Optional[Sequence[str]] = None,
    ) -> None:
        """GFM 表格。aligns 可选，每列 'left'/'center'/'right'（默认 left）。

        单元格内换行走 `<br>`（md 表原生不支持多行）——但我们应尽量保持单行，
        复杂内容移到表外 bullet 列表。
        """
        if not headers:
            raise ValueError("table() 必须有 headers")
        n = len(headers)
        if any(len(r) != n for r in rows):
            raise ValueError(
                f"table() rows 列数和 headers 不一致（headers={n}, rows={[len(r) for r in rows]}）"
            )
        aligns = aligns or ["left"] * n
        if len(aligns) != n:
            raise ValueError("aligns 列数和 headers 不一致")

        def _cell(s: str) -> str:
            # 表单元格禁止裸 | 和换行，分别转义 / 替换
            return str(s).replace("|", "\\|").replace("\n", "<br>")

        def _sep(a: str) -> str:
            return {"left": ":---", "center": ":---:", "right": "---:"}.get(a, ":---")

        header_row = "| " + " | ".join(_cell(h) for h in headers) + " |"
        sep_row = "| " + " | ".join(_sep(a) for a in aligns) + " |"
        data_rows = [
            "| " + " | ".join(_cell(c) for c in r) + " |" for r in rows
        ]
        self.parts.append("\n".join([header_row, sep_row, *data_rows]))

    # ── 结构 ────────────────────────────────────────────────────────────
    def hr(self) -> None:
        """no-op：Confluence 不渲染 md 水平线且显示丑，章节靠 h1/h2 自然分隔。保留签名避免调用方 AttributeError。"""
        pass

    def raw(self, md: str) -> None:
        """直接塞一段 md 字符串（预拼接好的场景片段、手写附录等）。慎用。"""
        self.parts.append(md.rstrip())

    def blank(self) -> None:
        """显式加一个空行（一般不需要，块之间 render 时自然分开）。"""
        self.parts.append("")

    # ── 输出 ────────────────────────────────────────────────────────────
    def render(self) -> str:
        """拼接所有块 —— 每块之间一个空行（markdownlint 友好）。"""
        body = "\n\n".join(p for p in self.parts if p is not None)
        # 收尾换行 + 前置骨架版本戳（drift checker 判定旧产物该刷新）
        return stamp_skel_version(body.rstrip() + "\n")


# ── 组合高阶 helper（sections_md 常用，抽出避免重复拼接） ──────────────

def scene_5section_card(
    w: MdWriter,
    scene_id: str,
    scene_name: str,
    *,
    story: str,
    images: Sequence[tuple[str, str]] = (),  # [(path, caption), ...]
    preconditions: Sequence[str] = (),
    system_checks: Sequence[str] = (),
    user_sees_success: Optional[str] = None,
    user_sees_fail: Optional[str] = None,
    data_impact: Sequence[str] = (),
    exceptions: Sequence[Sequence[str]] = (),  # [[触发, 响应, 用户感知], ...]
    copy_list: Sequence[str] = (),
    page_structure: Sequence[Sequence[str]] = (),  # [[模块, 层次, 数据来源], ...]
    heading_level: int = 3,  # 默认 h3（主骨架 single 模式）；split 模式子文件用 h2
) -> None:
    """[DEPRECATED 2026-05] 旧 8 段式卡片。新项目用 `scene_block_card`。

    研发反馈 8 段式信息过散（同区块信息散在 4 段），改用区块表聚合。
    详见 `references/prd-scene-templates.md` §四「子场景模板」。

    场景编号出现在 heading 里（锚点合规），正文禁编号由上游 humanize 把关。
    参数全部可选 —— 缺哪段就跳过哪段（允许不完整，骨架阶段正常）。

    heading_level:
        3 = single 模式主 md 里（### 5.1 A-1 · 发帖）
        2 = split 模式子文件里（## 5.1 A-1 · 发帖，子文件自己做一级标题）
    """
    heading = f"{scene_id} · {scene_name}"
    if heading_level == 2:
        w.h2(heading)
    elif heading_level == 3:
        w.h3(heading)
    elif heading_level == 4:
        w.h4(heading)
    else:
        raise ValueError(f"heading_level 只支持 2/3/4，传入 {heading_level}")

    # 业务故事（≤ 30 字）
    if story:
        w.field_bullet("业务故事", story)

    # 截图（允许多张，低保真 + 高保真）
    for path, caption in images:
        w.image(path, alt=caption or scene_name, caption=caption or None)

    # 5 段式正文
    if preconditions:
        w.field_bullet_list("前置条件", preconditions)
    if system_checks:
        w.field_bullet_list("系统检查", system_checks)
    if user_sees_success or user_sees_fail:
        lines = []
        if user_sees_success:
            lines.append(f"成功：{user_sees_success}")
        if user_sees_fail:
            lines.append(f"失败：{user_sees_fail}")
        w.field_bullet_list("用户看到", lines)
    if data_impact:
        w.field_bullet_list("数据影响", data_impact)

    # 异常（触发 × 响应 × 用户感知）
    if exceptions:
        w.paragraph(bold("异常场景"))
        w.table(
            headers=["触发条件", "系统响应", "用户感知"],
            rows=list(exceptions),
        )

    # 本场景文案
    if copy_list:
        w.field_bullet_list("本场景文案", copy_list)

    # 页面结构 & 信息层次
    if page_structure:
        w.paragraph(bold("页面结构 & 信息层次"))
        w.table(
            headers=["模块", "层次", "数据来源"],
            rows=list(page_structure),
        )


def _xml_escape(text: str) -> str:
    """转义 HTML 特殊字符（文本节点用，不转义引号）。"""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _xml_attr_escape(text: str) -> str:
    """转义 HTML 属性值（在 _xml_escape 基础上追加引号转义）。"""
    return _xml_escape(text).replace('"', "&quot;")


def _leftright_html_table(
    scene_name: str,
    images: Sequence[tuple[str, str]],
    leftright_modules: Sequence[tuple[str, str, Sequence[str], Sequence[str]]],
) -> str:
    """左图右文 → 带表头的原生 HTML `<table>`。

    左列：每张图一个 `<img>`；右列：每个模块 `<strong>{idx}. {name}</strong>` +
    `<ul>`（三段式标签做组头各一次，规则一条一 bullet 缩进挂组头下；
    显示要素 / 交互有内容才出）。
    对齐 fetch_confluence.py pandoc 拉回的多行缩进格式，源码可读、可回流。
    """
    img_lines = [
        f'<img src="{_xml_attr_escape(path)}" alt="{_xml_attr_escape(caption or scene_name)}" />'
        for path, caption in images
    ]
    left_cell = "\n".join(f"        {line}" for line in img_lines)

    module_blocks: list[str] = []
    for idx, module in enumerate(leftright_modules, start=1):
        name, show_logic, elements, interactions = module
        groups: list[tuple[str, Sequence[str]]] = []
        if show_logic:
            groups.append(("显示逻辑", [show_logic]))
        if elements:
            groups.append(("显示要素", elements))
        if interactions:
            groups.append(("交互", interactions))
        group_blocks: list[str] = []
        for gname, items in groups:
            item_lis = "\n".join(
                f"              <li>{_xml_escape(it)}</li>" for it in items
            )
            group_blocks.append(
                "          <li><strong>" + gname + "</strong>\n"
                "            <ul>\n"
                f"{item_lis}\n"
                "            </ul>\n"
                "          </li>"
            )
        module_blocks.append(
            f"        <strong>{idx}. {_xml_escape(name)}</strong>\n"
            "        <ul>\n"
            + "\n".join(group_blocks)
            + "\n        </ul>"
        )
    right_cell = "\n".join(module_blocks)

    return (
        "<table>\n"
        "  <colgroup>\n"
        '    <col style="width: 30.0%;" />\n'
        '    <col style="width: 70.0%;" />\n'
        "  </colgroup>\n"
        "  <thead>\n"
        "    <tr>\n"
        "      <th>示意图</th>\n"
        "      <th>页面元素 &amp; 规则</th>\n"
        "    </tr>\n"
        "  </thead>\n"
        "  <tbody>\n"
        "    <tr>\n"
        "      <td>\n"
        f"{left_cell}\n"
        "      </td>\n"
        "      <td>\n"
        f"{right_cell}\n"
        "      </td>\n"
        "    </tr>\n"
        "  </tbody>\n"
        "</table>"
    )


# 规格 / 验收 列的 bullet 项：str（单层）或 (父, [子...])（两层，子项禁再嵌）
SpecItem = "str | tuple[str, Sequence[str]]"


def _render_spec_items(items: Sequence, base_indent: int) -> str:
    """规格 / 验收 cell 的 bullet 列表 → 原生 <ul><li>（支持一层嵌套）。

    每项 str → 单层 <li>；(父, [子...]) → <li>父<ul><li>子</li>...</ul></li>。
    子项只允许一层（研发规格不需要更深；更深说明该拆场景）。
    """
    pad = " " * base_indent
    inner = " " * (base_indent + 2)
    lis: list[str] = []
    for item in items:
        if isinstance(item, (tuple, list)):
            parent, children = item[0], item[1]
            sub = "\n".join(
                f"{inner}  <li>{_xml_escape(c)}</li>" for c in children
            )
            lis.append(
                f"{pad}<li>{_xml_escape(parent)}\n"
                f"{inner}<ul>\n{sub}\n{inner}</ul>\n"
                f"{pad}</li>"
            )
        else:
            lis.append(f"{pad}<li>{_xml_escape(item)}</li>")
    return f'{" " * (base_indent - 2)}<ul>\n' + "\n".join(lis) + f'\n{" " * (base_indent - 2)}</ul>'


def _spec_3col_html_table(
    scene_name: str,
    rows: Sequence[tuple[Sequence[tuple[str, str]], Sequence, Sequence]],
) -> str:
    """三列规格表 → 原生 HTML <table>：示意图 / 规格（页面元素 + 字段·状态）/ 验收。

    每行 = (images, spec_items, accept_items)：
    - images: [(path, caption), ...] 该屏截图
    - spec_items / accept_items: _render_spec_items 的项（str 或 (父,[子])）
    研发看规格列 build，QA 看验收列测，行对齐——同一屏的规格与验收横向并排。
    """
    body_rows: list[str] = []
    for images, spec_items, accept_items in rows:
        img_html = "\n".join(
            f'        <img src="{_xml_attr_escape(p)}" alt="{_xml_attr_escape(c or scene_name)}" />'
            for p, c in images
        )
        spec_html = _render_spec_items(spec_items, 10) if spec_items else ""
        accept_html = _render_spec_items(accept_items, 10) if accept_items else ""
        body_rows.append(
            "    <tr>\n"
            f"      <td>\n{img_html}\n      </td>\n"
            f"      <td>\n{spec_html}\n      </td>\n"
            f"      <td>\n{accept_html}\n      </td>\n"
            "    </tr>"
        )
    return (
        "<table>\n"
        "  <colgroup>\n"
        '    <col style="width: 22.0%;" />\n'
        '    <col style="width: 50.0%;" />\n'
        '    <col style="width: 28.0%;" />\n'
        "  </colgroup>\n"
        "  <thead>\n"
        "    <tr>\n"
        "      <th>示意图</th>\n"
        "      <th>规格（页面元素 + 字段 / 状态）</th>\n"
        "      <th>验收</th>\n"
        "    </tr>\n"
        "  </thead>\n"
        "  <tbody>\n"
        + "\n".join(body_rows)
        + "\n  </tbody>\n"
        "</table>"
    )


def scene_block_card(
    w: MdWriter,
    scene_id: str,
    scene_name: str,
    *,
    story: str | None = None,
    images: Sequence[tuple[str, str]] = (),  # [(path, caption), ...]
    leftright_modules: Sequence[tuple[str, str, Sequence[str], Sequence[str]]] = (),
    # 新默认模板（2026-05 起）：[(模块名, 显示逻辑, [显示要素...], [交互...]), ...]
    spec_rows: Sequence[tuple[Sequence[tuple[str, str]], Sequence, Sequence]] = (),
    # 三列规格表：[(images, spec_items, accept_items), ...]；每屏一行，规格与验收行对齐。
    # spec_items / accept_items 项 = str（单层）或 (父, [子...])（两层）。用此模式时
    # 验收内联在表内、acceptance_criteria 只放跨行 / 反向态断言。
    blocks: Sequence[Sequence[str]] = (),
    # 【兼容】老 4 列区块表模板：[[区块, 元素+规则, 文案, 数据来源], ...]
    cross_cutting_sections: Sequence[tuple[str, Sequence[str]]] = (),
    # 横切策略 / 后端流程模板：[(主题, [bullet1, bullet2]), ...]
    data_impact: Sequence[str] = (),
    exceptions: Sequence[Sequence[str]] = (),  # 3 列：触发条件 / 系统响应 / 用户感知
    acceptance_criteria: Sequence[str] = (),  # 验收标准 checkbox，baseline ↔ delta 反向合并的对齐锚
    heading_level: int = 3,
) -> None:
    """子场景模板卡片（PRD 2026-05 起规范）。

    三种模式（按场景类型互斥选，优先级：leftright > blocks > cross_cutting）：

    - **UI 场景默认**（`leftright_modules=[...]`）：有图 → 带表头的原生 HTML `<table>`
        左图右文（左列 `<img>` + 右列 `<strong>` 模块名 + `<ol>/<ul>` 嵌套三段式）；
        无图（baseline living 文档）→ 纯编号三段式。
        每个模块传 `(模块名, 显示逻辑文字, [显示要素 bullet], [交互 bullet])`
        研发对应分工：显示逻辑 → 后端；显示要素 → 前端；交互 → 前后端
    - **UI 场景兼容**（`blocks=[...]`）：4 列区块表（已有 PRD 维持）
    - **横切策略 / 后端流程**（`cross_cutting_sections=[...]`）：粗体段 + bullet，无 UI 截图场景

    三种模式都包含：
    - quote 业务故事
    - 截图 + caption
    - 数据影响 段
    - 异常场景 表（3 列：触发条件 / 系统响应 / 用户感知）
    - 验收标准 checkbox（baseline 与 delta 场景小节共用字段集，反向合并粘贴不缺段）

    参考：`references/prd-scene-templates.md` §四「子场景模板」。
    """
    heading = f"{scene_id} · {scene_name}"
    if heading_level == 2:
        w.h2(heading)
    elif heading_level == 3:
        w.h3(heading)
    elif heading_level == 4:
        w.h4(heading)
    else:
        raise ValueError(f"heading_level 只支持 2/3/4，传入 {heading_level}")

    if story:
        w.chapter_story(story)

    # 三列规格表（图 / 规格 / 验收）：每屏一行，规格与验收横向对齐，同一事实只出现一次。
    # 优先级最高——显式传 spec_rows 即走此模板。规格 / 显性验收内联表内；
    # data_impact 归「跨模块 / 全局」（表画不出的跨模块联动 / 迁移 / 全局规则），
    # acceptance_criteria 归「整体验收」（跨行 / 反向态断言，塞不进单屏）。
    if spec_rows:
        w.raw(_spec_3col_html_table(scene_name, spec_rows))
        if data_impact:
            w.paragraph(bold("跨模块 / 全局"))
            w.bullet_list(list(data_impact))
        if exceptions:
            w.paragraph(bold("异常场景"))
            w.table(headers=["触发条件", "系统响应", "用户感知"], rows=list(exceptions))
        if acceptance_criteria:
            w.paragraph(bold("整体验收（跨行 / 反向态）"))
            for c in acceptance_criteria:
                w.raw(f"- [ ] {c}")
        return

    # 左图右文三段式模板：有图 → 带表头的原生 HTML <table>（wiki 可视化编辑 +
    # 往返可回流）；无图（baseline living 文档）→ 纯编号三段式
    if leftright_modules:
        if images:
            w.raw(_leftright_html_table(scene_name, images, leftright_modules))
        else:
            lines: list[str] = []
            for idx, module in enumerate(leftright_modules, start=1):
                name, show_logic, elements, interactions = module
                lines.append(f"{idx}. **{name}**")
                lines.append("")
                lines.append("   - **显示逻辑**")
                lines.append(f"     - {show_logic}")
                if elements:
                    lines.append("   - **显示要素**")
                    for el in elements:
                        lines.append(f"     - {el}")
                if interactions:
                    lines.append("   - **交互**")
                    for it in interactions:
                        lines.append(f"     - {it}")
                lines.append("")
            w.raw("\n".join(lines).rstrip())
    else:
        for path, caption in images:
            w.image(path, alt=caption or scene_name, caption=caption or None)

    if blocks:
        w.paragraph(bold("页面元素 & 规则"))
        w.table(
            headers=["区块", "元素 + 规则", "文案", "数据来源"],
            rows=[list(b) for b in blocks],
        )

    for title, bullets in cross_cutting_sections:
        w.paragraph(bold(title))
        w.bullet_list(list(bullets))

    if data_impact:
        w.paragraph(bold("数据影响"))
        w.bullet_list(list(data_impact))

    if exceptions:
        w.paragraph(bold("异常场景"))
        w.table(
            headers=["触发条件", "系统响应", "用户感知"],
            rows=list(exceptions),
        )

    if acceptance_criteria:
        w.paragraph(bold("验收标准"))
        w.bullet_list([f"[ ] {c}" for c in acceptance_criteria])


def scene_map_table(w: MdWriter, scenes: Iterable[Sequence[str]]) -> None:
    """第 2.1 场景地图表：| 编号 | 场景名 | View | 优先级 | 说明 |

    scenes: [[id, name, view, priority, note], ...]
    """
    w.table(
        headers=["编号", "场景名", "View", "优先级", "说明"],
        rows=[list(s) for s in scenes],
    )
