"""12 章骨架生成函数（md 版）。

每个 `build_chapter_N(w, info)` 往 writer 里 append 该章的骨架，
含 {{ 待填 }} 占位符告诉 PM 要填什么、写在哪。

info 的最小字段：
    {
        "project_name": "社区 v1",       # 必填，出现在 h1
        "version": "1.0",                # 必填
        "author": "Felix",               # 可选
        "date": "2026-05-09",            # 可选，缺则今天
        "baseline": "V0 线上版",          # 可选，1.3 章引用
        "scenes": [                      # 可选，从 scene-list.md 解析
            {"id": "A-1", "name": "发帖", "view": "前台", "priority": "P0", "note": "..."},
            ...
        ],
        "mode": "single" | "split",      # 默认 single
    }

输出规则：
- 没传的字段用占位符 `{{ 待填：... }}` 提示 PM
- 传了 scenes 时自动填第 2.1 表 + 第 5/6/7 章子场景骨架
- mode=split 时第 5/6/7 章只列场景引用链接，子场景骨架由 gen_prd_skeleton 写到独立文件

设计原则：
1. 本模块**只生成骨架**，不做任何内容判断 / 智能填充 —— PM + AI 填内容
2. 占位符格式统一：`{{ 待填：描述 }}`，便于 check_prd_md.sh 统计填充度
3. 每个 build_chapter_N 独立，失败不影响其他章节
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional


def _strip_date_tag(name: str) -> str:
    """去掉场景名里的流水账日期标签：(2026-04-23 迁入) / （04-23 重定）等。

    PRD 静态章不该带日期，迁入 / 重定 / 修订 等动作语义不在 PRD 标题层级表达。
    """
    return re.sub(r"\s*[（(]\s*\d{2,4}[-./]\d{1,2}([-./]\d{1,2})?[^）)]*[）)]\s*", "", name).strip()

from core.md_renderer import (
    TAG_CHANGED,
    TAG_DEFERRED,
    TAG_NEW,
    MdWriter,
    bold,
    scene_block_card,
    scene_map_table,
)

# ── 占位符常量 ───────────────────────────────────────────────────────────

def placeholder(hint: str) -> str:
    """统一的占位符格式。`check_prd_md.sh` 靠 `{{ 待填` 开头扫填充度。"""
    return f"{{{{ 待填：{hint} }}}}"


PL = placeholder  # 短别名，生成函数内频繁用


# ── 场景 info 解析 ────────────────────────────────────────────────────────

@dataclass
class SceneInfo:
    id: str           # 如 "A-1"
    name: str         # 如 "发帖"
    view: str         # "前台" / "后台" / "跨端"
    module: str = ""  # scene-list「模块」列，baseline profile 按此分组成模块树
    priority: str = "P0"
    note: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "SceneInfo":
        return cls(
            id=d["id"],
            name=_strip_date_tag(d["name"]),
            view=d.get("view", ""),
            module=d.get("module", ""),
            priority=d.get("priority", "P0"),
            note=d.get("note", ""),
        )

    @property
    def view_prefix(self) -> str:
        """split 模式子文件名前缀：front / back / cross"""
        if self.view in ("前台", "App", "用户端"):
            return "front"
        if self.view in ("后台", "CMS", "管理端"):
            return "back"
        return "cross"

    def scene_filename(self) -> str:
        """split 模式下的子文件名：front-A-1-发帖.md

        只取主名（— : · + ( （ & 等分隔符前），完整白话名仍保留在 h2 标题。
        避免长描述拼出 front-B-2-专题胶囊筛选-+-统一-Grid.md 这种丑陋形态。
        """
        main = re.split(r"[—–:：·+(（&]", self.name, maxsplit=1)[0].strip()
        if not main:  # 名字以分隔符开头（如「（既有）发帖」）→ 回退整名，避免空段 front-A-1-.md 撞名
            main = re.sub(r"[—–:：·+(（&]", " ", self.name).strip()
        safe_name = main.replace(" ", "-").replace("/", "-")
        return f"{self.view_prefix}-{self.id}-{safe_name}.md"


def _parse_scenes(scenes_raw: Optional[list]) -> list[SceneInfo]:
    if not scenes_raw:
        return []
    return [SceneInfo.from_dict(s) for s in scenes_raw]


def _group_by_view(scenes: list[SceneInfo]) -> dict[str, list[SceneInfo]]:
    """按 View 分桶，用于分派给 5/6/7 章。"""
    groups = {"前台": [], "后台": [], "跨端": []}
    for s in scenes:
        if s.view_prefix == "front":
            groups["前台"].append(s)
        elif s.view_prefix == "back":
            groups["后台"].append(s)
        else:
            groups["跨端"].append(s)
    return groups


# ── 章节骨架生成函数 ──────────────────────────────────────────────────────

def build_cover(w: MdWriter, info: dict) -> None:
    """首页元数据表（h1 + 信息表）。"""
    project = info.get("project_name", PL("项目名"))
    version = info.get("version", "1.0")
    author = info.get("author", PL("作者"))
    d = info.get("date") or date.today().isoformat()
    baseline = info.get("baseline", "无线上基线（新项目）")

    w.h1(f"{project} PRD")
    w.table(
        headers=["字段", "值"],
        rows=[
            ["版本", f"v{version}"],
            ["作者", author],
            ["日期", d],
            ["线上基线", baseline],
            ["场景数", str(len(info.get("scenes", [])) or PL("填场景数"))],
        ],
    )


def build_chapter_1(w: MdWriter, info: dict) -> None:
    """1. 项目背景与目标"""
    w.h1("1. 项目背景与目标")

    w.h2("1.1 现状分析")
    w.bullet_list([
        bold("产品现状") + "：" + PL("当前功能怎么实现 / 关键入口 / 已知问题"),
        bold("用户现状") + "：" + PL("用户怎么用 / 日活 / 关键行为分布 / 反馈 / 舆情"),
        bold("数据现状") + "：" + PL("核心指标基线 / 数据趋势 / 异常分析"),
        bold("关联影响") + "：" + PL("涉及哪些上下游模块 / 对现有功能的影响评估"),
    ])

    w.h2("1.2 价值论证")
    w.paragraph(PL("常规迭代可整段填「不涉及价值论证」"))
    w.bullet_list([
        bold("业务价值") + "：" + PL("对业务指标的预期贡献（GMV / DAU / 留存 / 转化）"),
        bold("用户价值") + "：" + PL("对用户解决什么痛点 / 带来什么体验提升"),
        bold("ROI") + "：" + PL("预期收益 vs 投入成本（开发 + 运维 + 风险），判断是否值得做"),
        bold("不做代价") + "：" + PL("不做的话会失去什么 / 风险有多大"),
    ])

    w.h2("1.3 目标 + 成功指标")
    w.paragraph(bold("核心目标") + "：" + PL("一句话说清要把事情推进到什么状态"))
    w.paragraph(bold("成功指标") + "：")
    w.table(
        headers=["指标", "当前", "目标", "说明"],
        rows=[
            [PL("指标名"), PL("基线值"), PL("目标值"), PL("口径说明")],
            [PL("指标名"), PL("基线值"), PL("目标值"), PL("口径说明")],
        ],
    )
    w.paragraph(bold("Guardrail（不能退步的指标）") + "：" + PL("举报率 / 删帖率 / 客诉率 等"))

    w.h2("1.4 核心变更（vs 线上基线）")
    w.bullet_list([
        f"{TAG_NEW} " + PL("新增什么"),
        f"{TAG_CHANGED} " + PL("改了什么"),
        f"{TAG_DEFERRED} " + PL("本期不做的（明确标出来避免扯皮）"),
    ])

    w.h2("1.5 用户角色")
    w.table(
        headers=["角色", "画像", "核心诉求", "可见 / 可操作范围"],
        rows=[
            [PL("角色名"), PL("谁"), PL("要什么"), PL("能看什么 / 能做什么（按模块列）")],
            [PL("角色名"), PL("谁"), PL("要什么"), PL("能看什么 / 能做什么")],
        ],
    )


def build_chapter_2(w: MdWriter, info: dict) -> None:
    """2. 场景地图"""
    scenes = _parse_scenes(info.get("scenes"))

    w.h1("2. 场景地图")

    w.h2("2.1 场景编号表")
    if scenes:
        scene_map_table(
            w,
            [[s.id, s.name, s.view, s.priority, s.note or "—"] for s in scenes],
        )
    else:
        scene_map_table(
            w,
            [
                ["A-1", PL("前台场景 1"), "前台", "P0", PL("说明")],
                ["M-1", PL("后台场景 1"), "后台", "P0", PL("说明")],
                ["F-1", PL("跨端场景 1"), "跨端", "P0", PL("说明")],
            ],
        )

    w.h2("2.2 优先级")
    w.bullet_list([
        bold("P0（本期必须）") + "：" + PL("列出 P0 场景编号，如 A-1 / A-2 / M-1"),
        bold("P1（有空做）") + "：" + PL("P1 场景"),
        bold("P2（探索性）") + "：" + PL("P2 场景，可选"),
    ])

    w.h2("2.3 跨端数据流总览")
    w.paragraph(PL("端×端数据走向；复杂流程出 SVG 引入"))
    w.table(
        headers=["起点", "终点", "触发", "延迟"],
        rows=[
            [PL("前台 App"), PL("后端"), PL("用户操作触发"), PL("实时")],
            [PL("后端"), PL("后台 CMS"), PL("数据落库后异步"), PL("≤ 1s")],
        ],
    )


def build_chapter_3(w: MdWriter, info: dict) -> None:
    """3. 术语与业务对象词典"""
    w.h1("3. 术语与业务对象词典")

    w.h2("3.1 术语表")
    w.table(
        headers=["术语", "定义", "禁用同义词"],
        rows=[
            [PL("术语名"), PL("一句话定义"), PL("避免用的说法")],
            [PL("术语名"), PL("一句话定义"), PL("避免用的说法")],
        ],
    )

    w.h2("3.2 业务对象")
    w.paragraph(bold(PL("对象名 1，如「帖子」")))
    w.table(
        headers=["属性", "类型范畴", "数据来源", "说明"],
        rows=[
            [PL("属性名"), PL("ID / 字符串 / 枚举 / 金额 等"), PL("用户输入 / 系统生成 / 接口"), PL("业务含义")],
        ],
    )
    w.paragraph(bold("生命周期") + "：" + PL("草稿 → 待审核 → 已发布 → 已删除 等"))
    w.paragraph(bold("关系") + "：" + PL("和其他业务对象的关联，如 1 个帖子属于 1 个作者"))

    w.h2("3.3 枚举 + 状态机")
    w.paragraph(bold(PL("对象名")) + " 状态枚举：")
    w.bullet_list([PL("状态 1"), PL("状态 2"), PL("状态 3")])
    w.paragraph(bold("状态机") + "：状态迁移表（多状态多触发场景可走 flowchart skill 出 SVG `![状态机](./assets/flow-state.svg)`）")
    w.table(
        headers=["起始状态", "触发事件", "终止状态", "谁触发"],
        rows=[
            [PL("—（不存在）"), PL("创建动作"), PL("草稿"), PL("用户")],
            [PL("草稿"), PL("提交审核"), PL("待审核"), PL("用户")],
            [PL("待审核"), PL("通过"), PL("已发布"), PL("审核员")],
            [PL("待审核"), PL("拒绝"), PL("已拒绝"), PL("审核员")],
        ],
    )


def build_chapter_4(w: MdWriter, info: dict) -> None:
    """4. 全局业务规则"""
    w.h1("4. 全局业务规则")

    w.h2("4.1 跨场景规则")
    w.paragraph(bold(PL("规则名 1")) + "：" + PL("规则描述 + 违反时的处理"))
    w.paragraph(bold(PL("规则名 2")) + "：" + PL("规则描述 + 违反时的处理"))

    w.h2("4.2 归因规则")
    w.paragraph(bold(PL("核心归因事件")) + "：" + PL("什么算一次转化 + 归因窗口"))
    w.table(
        headers=["漏斗", "定义", "归因窗口"],
        rows=[
            ["L1", PL("曝光口径"), "—"],
            ["L2", PL("点击口径"), PL("实时 / Nh")],
            ["L3", PL("下一层转化"), PL("归因窗口")],
        ],
    )


def _build_scene_section_chapter(
    w: MdWriter,
    *,
    chapter_num: int,
    chapter_title: str,
    scenes: list[SceneInfo],
    mode: str,
    scenes_dir_name: str = "",
) -> None:
    """5/6/7 章公共逻辑：按 view 类型生成扁平子场景。"""
    w.h1(f"{chapter_num}. {chapter_title}")

    if not scenes:
        w.paragraph(PL(f"本章无 {chapter_title} 场景（如有按扁平列表追加 {chapter_num}.1 / {chapter_num}.2 / ...）"))
        return

    if mode == "split":
        # 主骨架只放引用链接，子场景写在独立文件
        links = [
            f"[{chapter_num}.{i + 1} {s.id} · {s.name}]({scenes_dir_name}/{s.scene_filename()})"
            for i, s in enumerate(scenes)
        ]
        w.bullet_list(links)
        return

    # single 模式：每个场景骨架直接铺在这里（左图右文三段式模板，详见 §四）
    for i, scene in enumerate(scenes):
        scene_id_label = f"{chapter_num}.{i + 1} {scene.id}"
        scene_block_card(
            w,
            scene_id_label,
            scene.name,
            story=PL("谁/做什么/为什么"),
            images=[(f"./assets/scene-{scene.id}.png", f"{scene.name}低保真")],
            leftright_modules=[
                (
                    PL("模块名"),
                    PL("何时显示/不显示"),
                    [PL("字段/控件/文案"), PL("再一条")],
                    [PL("点 X → 跳 Y")],
                ),
                (
                    PL("模块名"),
                    PL("何时显示/不显示"),
                    [PL("字段/控件/文案"), PL("再一条")],
                    [PL("点 X → 跳 Y")],
                ),
            ],
            data_impact=[PL("数据变化，业务语言"), PL("再一条")],
            exceptions=[
                [PL("触发条件"), PL("系统响应"), PL("用户感知")],
            ],
            acceptance_criteria=[PL("可验证的验收点"), PL("再一条")],
            heading_level=3,
        )


def build_chapter_5(w: MdWriter, info: dict, scenes_dir_name: str = "") -> None:
    """5. 前台功能需求"""
    scenes = _parse_scenes(info.get("scenes"))
    groups = _group_by_view(scenes)
    _build_scene_section_chapter(
        w,
        chapter_num=5,
        chapter_title="前台功能需求",
        scenes=groups["前台"],
        mode=info.get("mode", "single"),
        scenes_dir_name=scenes_dir_name,
    )


def build_chapter_6(w: MdWriter, info: dict, scenes_dir_name: str = "") -> None:
    """6. 后台功能需求"""
    scenes = _parse_scenes(info.get("scenes"))
    groups = _group_by_view(scenes)
    _build_scene_section_chapter(
        w,
        chapter_num=6,
        chapter_title="后台功能需求",
        scenes=groups["后台"],
        mode=info.get("mode", "single"),
        scenes_dir_name=scenes_dir_name,
    )


def build_chapter_7(w: MdWriter, info: dict, scenes_dir_name: str = "") -> None:
    """7. 跨端 / 后端需求"""
    scenes = _parse_scenes(info.get("scenes"))
    groups = _group_by_view(scenes)
    _build_scene_section_chapter(
        w,
        chapter_num=7,
        chapter_title="跨端 / 后端需求",
        scenes=groups["跨端"],
        mode=info.get("mode", "single"),
        scenes_dir_name=scenes_dir_name,
    )


def build_chapter_8(w: MdWriter, info: dict) -> None:
    """8. 通用文案清单"""
    w.h1("8. 通用文案清单")

    w.h2("8.1 Loading / 空态 / Toast")
    w.table(
        headers=["状态", "文案"],
        rows=[
            ["Loading（骨架屏）", PL("文案，一般无文字")],
            ["空态（无内容）", PL("文案 + 引导")],
            ["空态（未登录）", PL("文案 + 登录引导")],
            ["Toast 操作成功", PL("文案")],
            ["Toast 操作失败", PL("文案")],
        ],
    )

    w.h2("8.2 弹窗 / 确认类")
    w.table(
        headers=["场景", "标题", "内容", "按钮"],
        rows=[
            [PL("弹窗场景"), PL("标题文案"), PL("内容说明"), PL("按钮组「取消/确认」")],
        ],
    )

    w.h2("8.3 错误提示")
    w.table(
        headers=["错误类型", "文案"],
        rows=[
            ["网络错误", PL("文案")],
            ["服务器错误", PL("文案")],
            ["权限错误", PL("文案")],
        ],
    )


def build_chapter_9(w: MdWriter, info: dict) -> None:
    """9. 埋点与数据监控"""
    w.h1("9. 埋点与数据监控")

    w.h2("9.1 事件列表")
    w.table(
        headers=["业务事件", "触发时机", "关键属性（业务字段）", "关联漏斗"],
        rows=[
            [PL("业务事件描述"), PL("触发点描述"), PL("中文业务字段列表"), PL("L1 / L2 / ...")],
        ],
    )

    w.h2("9.2 看板指标")
    w.table(
        headers=["指标", "计算口径", "支撑 §1.3 目标指标"],
        rows=[
            [PL("CTR"), PL("分子 / 分母"), PL("对应 §1.3 哪个目标")],
        ],
    )


def build_chapter_10(w: MdWriter, info: dict) -> None:
    """10. 非功能性需求"""
    w.h1("10. 非功能性需求")

    w.table(
        headers=["需求", "指标", "说明"],
        rows=[
            [PL("核心操作响应"), PL("P95 ≤ Ns"), PL("口径")],
            [PL("数据生效"), PL("≤ N 秒"), PL("异步 / 同步")],
            [PL("并发"), PL("QPS"), PL("高峰场景")],
            [PL("数据一致性"), PL("强 / 最终"), PL("可接受的不一致窗口")],
        ],
    )


def build_chapter_11(w: MdWriter, info: dict) -> None:
    """11. 里程碑与排期"""
    w.h1("11. 里程碑与排期")

    w.h2("Phase 划分")
    w.table(
        headers=["Phase", "范围", "周期", "依赖"],
        rows=[
            ["Phase 1", PL("场景列表"), PL("N 周"), PL("依赖项")],
        ],
    )

    w.h2("依赖 & 阻塞")
    w.bullet_list([PL("阻塞项 1（需 XX 团队 XX 时间前准备好）")])

    w.h2("后续规划（本期不做）")
    w.bullet_list([PL("未来规划项")])

    w.h2("上线后验证 & 回滚")
    w.table(
        headers=["验证项", "判定指标 / 阈值", "回滚触发条件"],
        rows=[
            [PL("核心功能可用"), PL("成功率 / 指标达标线"), PL("低于阈值 / 报错率超标")],
        ],
    )


def build_chapter_12(w: MdWriter, info: dict) -> None:
    """12. 附录"""
    w.h1("12. 附录")

    w.h2("兼容矩阵")
    w.table(
        headers=["端", "支持版本"],
        rows=[
            ["iOS", PL("≥ X.0")],
            ["Android", PL("≥ X.0")],
            ["Web", PL("Chrome / Edge / Safari 最新版")],
        ],
    )

    w.h2("历史数据处理")
    w.paragraph(PL("已有数据迁移 / 兼容方案 / 清理策略。无历史数据填「本期为全新功能，无历史数据」"))
    w.bullet_list([
        bold("迁移方案") + "：" + PL("旧字段映射 / 数据 backfill 步骤 / 默认值填充"),
        bold("兼容方案") + "：" + PL("旧版客户端如何降级展示 / 灰度期新旧并存策略"),
        bold("清理策略") + "：" + PL("旧数据保留期 / 归档 / 删除"),
    ])

    w.h2("旧版本差异")
    w.paragraph(PL("vs 线上版的变更项（必要时列；1.4 已概述则可省）"))


# ── 主组装入口 ────────────────────────────────────────────────────────────

def build_full_skeleton(info: dict, scenes_dir_name: str = "") -> str:
    """single 模式：12 章全部生成到一个 md 字符串。"""
    w = MdWriter()
    build_cover(w, info)
    build_chapter_1(w, info)
    build_chapter_2(w, info)
    build_chapter_3(w, info)
    build_chapter_4(w, info)
    build_chapter_5(w, info, scenes_dir_name)
    build_chapter_6(w, info, scenes_dir_name)
    build_chapter_7(w, info, scenes_dir_name)
    build_chapter_8(w, info)
    build_chapter_9(w, info)
    build_chapter_10(w, info)
    build_chapter_11(w, info)
    build_chapter_12(w, info)
    return w.render()


def build_scene_file(scene: SceneInfo, chapter_label: str = "") -> str:
    """split 模式下的单个子场景独立 md 文件内容（h2 层级）。

    chapter_label: 如 "5.1"，子文件标题会是 `## 5.1 A-1 · 发帖`；
    缺省则只有 `## A-1 · 发帖`（用于预览，不进主 md）。

    模板：左图右文三段式（2026-05 起规范），详见 references/prd-chapter-rules.md §4.1。
    """
    w = MdWriter()
    scene_id = f"{chapter_label} {scene.id}" if chapter_label else scene.id
    scene_block_card(
        w,
        scene_id,
        scene.name,
        story=PL("谁/做什么/为什么"),
        images=[(f"../assets/scene-{scene.id}.png", f"{scene.name}低保真")],
        leftright_modules=[
            (
                PL("模块名"),
                PL("何时显示/不显示"),
                [PL("字段/控件/文案"), PL("再一条")],
                [PL("点 X → 跳 Y")],
            ),
            (
                PL("模块名"),
                PL("何时显示/不显示"),
                [PL("字段/控件/文案"), PL("再一条")],
                [PL("点 X → 跳 Y")],
            ),
        ],
        data_impact=[PL("数据变化，业务语言"), PL("再一条")],
        exceptions=[[PL("触发条件"), PL("系统响应"), PL("用户感知")]],
        acceptance_criteria=[PL("可验证的验收点"), PL("再一条")],
        heading_level=2,
    )
    return w.render()


