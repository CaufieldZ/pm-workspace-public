"""baseline / delta profile 骨架生成（迭代文档集模型）。

从 sections_md 拆出：baseline = 线上当前态全量真相源（模块树 + changelog），
delta = 单轮迭代（本轮 N 需求 + WHY，引 baseline）。被 gen_prd_skeleton.py 调用。
"""
from __future__ import annotations

from datetime import date

from core.md_renderer import MdWriter, bold, scene_block_card
from sections_md import PL, SceneInfo, _parse_scenes, build_chapter_4

# ── baseline / delta profile（迭代文档集模型） ──────────────────────────────
#
# baseline = 线上当前态全量真相源（living，按模块树组织，含 changelog 索引章）
# delta    = 单轮迭代（本轮 N 需求 + WHY，术语 / 模块树不重复，引 baseline）
# 两者 5/6/7 场景小节走同一个 scene_block_card 原语（字段集含 acceptance），
# 保证反向合并「粘贴 + 改非重写」不缺段。


def _group_by_module(scenes: list[SceneInfo]) -> "list[tuple[str, list[SceneInfo]]]":
    """按 scene-list「模块」列分组，保序。无 module 的归入「未分组」。"""
    order: list[str] = []
    buckets: dict[str, list[SceneInfo]] = {}
    for s in scenes:
        key = s.module or "未分组"
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(s)
    return [(k, buckets[k]) for k in order]


def build_changelog_chapter(w: MdWriter, chapter_num: int) -> None:
    """变更记录索引章（baseline 专属，append-only）。

    承重不变量索引：每条 = 日期｜触及模块｜delta 链接｜状态（已登记 / 已合并）。
    标题含「变更记录」→ check_static_chapter.py 自动判为动态章豁免静态 lint。
    """
    w.h1(f"{chapter_num}. 变更记录")
    w.paragraph("append-only，每条 = 日期｜触及模块｜delta 链接｜状态（已登记 → 已合并）。")
    w.table(
        headers=["日期", "触及模块", "delta PRD", "状态"],
        rows=[
            [date.today().isoformat(), PL("模块名（对应模块章）"), PL("deliverables/prd-xxx-delta.md"), "已合并"],
        ],
    )


def build_baseline_skeleton(info: dict) -> str:
    """baseline profile：线上当前态全量真相源。

    章节集 = 概览 + 术语 + 模块树 + 全局规则 + N 个模块章（按 module 分组）
             + 文案 + 非功能 + 附录 + 变更记录。
    去掉 delta-only：价值论证 / 核心变更 / 埋点事件设计 / 里程碑排期。
    """
    w = MdWriter()
    scenes = _parse_scenes(info.get("scenes"))
    project = info.get("project_name", PL("产品线名"))

    # 头部：只留承重不变量（反向合并操作锚）；living 性质 / 粒度 / 非交付物等机制说明在 SKILL.md
    w.h1(f"{project} · Baseline PRD（线上当前态全量真相源）")
    w.bullet_list([
        bold("承重不变量") + "：任何现状改动，先在变更记录章写 changelog 行（日期｜触及模块｜delta 链接｜状态），状态推进到「已合并」后才改对应模块章。",
    ])

    # 1. 产品概览（无价值论证）
    w.h1("1. 产品概览")
    w.field_bullet("产品形态", PL("产品当前提供什么能力 / 涉及哪些端"))
    w.field_bullet("用户角色", PL("真实角色 + 可见 / 可操作范围"))

    # 2. 术语词典
    w.h1("2. 术语词典")
    w.table(
        headers=["术语", "定义"],
        rows=[[PL("术语名"), PL("一句话定义")]],
    )

    # 3. 模块树（编号 of record）
    w.h1("3. 模块树（场景编号 of record）")
    module_groups = _group_by_module(scenes)
    if module_groups:
        rows = []
        for mod, ms in module_groups:
            ids = " / ".join(f"{s.id} {s.name}" for s in ms)
            rows.append([mod, ids, PL("涉及端")])
        w.table(headers=["模块", "子场景", "涉及端"], rows=rows)
    else:
        w.table(
            headers=["模块", "子场景", "涉及端"],
            rows=[[PL("模块名"), PL("A-1 / A-2 ..."), PL("App / Web / CMS")]],
        )

    # 4. 全局业务规则
    build_chapter_4(w, info)

    # 5..N 模块章（每模块一章，含各端段 + 规则段）
    chapter_num = 5
    if module_groups:
        for mod, ms in module_groups:
            _build_module_chapter(w, chapter_num, mod, ms)
            chapter_num += 1
    else:
        _build_module_chapter(w, chapter_num, PL("模块名"), [])
        chapter_num += 1

    # 文案 / 非功能 / 附录（沿用既有章，重编号无意义，用固定标题）
    w.h1(f"{chapter_num}. 通用文案清单")
    chapter_num += 1
    w.h1(f"{chapter_num}. 非功能性需求")
    chapter_num += 1

    # 末章：变更记录
    build_changelog_chapter(w, chapter_num)
    return w.render()


def _build_module_chapter(
    w: MdWriter, chapter_num: int, module_name: str, scenes: list[SceneInfo]
) -> None:
    """单个模块章：模块规则段 + 各端场景小节（走 scene_block_card）。"""
    w.h1(f"{chapter_num}. {module_name}模块")
    w.paragraph(bold("最后核对线上") + "：" + PL("YYYY-MM-DD / 核对人"))

    w.h2(f"{chapter_num}.0 模块规则（全场）")
    w.table(
        headers=["规则", "详情"],
        rows=[[PL("规则名"), PL("规则详情")]],
    )

    for i, scene in enumerate(scenes, start=1):
        scene_block_card(
            w,
            f"{chapter_num}.{i} {scene.id}",
            scene.name,
            story=PL("谁/做什么/为什么"),
            images=(),  # baseline 是 living 文档，不放截图（UI 真相源在原型 / delta）
            leftright_modules=[
                (
                    PL("模块名"),
                    PL("何时显示/不显示"),
                    [PL("字段/控件/文案"), PL("再一条")],
                    [PL("点 X → 跳 Y"), PL("再一条")],
                ),
            ],
            data_impact=[PL("数据变化，业务语言"), PL("再一条")],
            exceptions=[[PL("触发条件"), PL("系统响应"), PL("用户感知")]],
            acceptance_criteria=[PL("可验证的验收点")],
            heading_level=3,
        )


def _delta_patch_heavy_template() -> str:
    """补丁包（patch）重项 H3 需求块模板（HTML 注释形态，供复制）。

    patch 档默认全部需求只落 §2.0 表（轻项读完表即止），命中升块判据的重项才
    从本模板复制出一个 H3。模板摆注释里而非活槽 = 默认产出最轻形态，升块是
    加法而非删减——规则见 references/prd-chapter-rules.md §2 第 3 条。
    patch 需求块是散功能点（无图），标题用需求序号 + 需求名，不套 scene-list
    场景号，也不套 §4.0 三列规格表（无截图）。术语与三列模板对齐。
    """
    return (
        "<!-- 重项模板（命中升块判据才复制一份出来，编号沿用 §2.0 表的 2.N）：\n"
        "\n"
        "### 2.N 需求名\n"
        "\n"
        "- **现状**：一行前置态锚点（具体场景号 / 字段 / 旧行为），不复述 §1 痛点\n"
        "- **修改点**：做 X（原 Y 问题）\n"
        "- **跨模块 / 全局**：做到哪为止的护栏（『仅校验 X 三类字段，其余不变』），"
        "不写『属前端修复』这类归类元评论\n"
        "- **数据影响**：数据变化，业务语言；无数据变化删本行\n"
        "\n"
        "**验收标准**\n"
        "\n"
        "- [ ] 可验证的验收点\n"
        "-->"
    )


def build_delta_skeleton(info: dict) -> str:
    """delta profile：单轮迭代。只写本轮 N 需求 + WHY，引 baseline，不重复术语 / 模块树。"""
    w = MdWriter()
    scenes = _parse_scenes(info.get("scenes"))
    project = info.get("project_name", PL("产品线名"))
    version = info.get("version", "1")
    tier = info.get("tier", "feature")
    tier_label = {"patch": "补丁包", "feature": "内聚特性", "bundle": "集合体"}.get(tier, "内聚特性")

    w.h1(f"{project} · Delta PRD · {version} · 【业务名与本轮主题待填充】")
    # 协作头（对齐公司 PRD 模板的 PRD信息 / 团队信息 / 资源对接三张表，压成一张）。
    # 用表格而非 bullet 是承重设计：md_to_confluence 的 _preamble_all_meta 只把
    # `- ` / `> ` / `---` / 空行判为「内部元信息」整块剥离，表格行（`|` 开头）→ 保留上 wiki。
    # 即：表 = 对外协作信息，bullet = 内部机制。文档机制说明（baseline 指针等）一律
    # 不进头部，落 §9（推送时整章剥离）。
    # 「状态」「火效」两格由 sync_hx_status.py 按火效回写，故固定摆第 3 列 key / 第 4 列 value
    # （值落行尾单元格，回写正则好锚），勿调列位。
    w.table(
        headers=["项", "内容", "项", "内容"],
        rows=[
            ["PRD 版本", version,
             "状态", PL("待排期 / 开发中 / 已上线 / 已合并（sync_hx_status.py 按火效回写，勿手填）")],
            ["拟制人 / 日期", PL("姓名 / YYYY-MM-DD"),
             "火效", PL("H 号（上线日期 / 状态唯一权威源）")],
            ["重要性 / 紧迫性", PL("高 / 中 / 低"),
             "迭代档位", tier_label],
            ["端侧范围", PL("App / H5 / Web 工作台 / CMS"),
             "提测 / 走查 / 上线", "见排期章"],
            ["产品 / 交互", PL("姓名"),
             "设计 / 设计稿", PL("姓名 / 设计稿链接")],
            ["前端 / 后端", PL("姓名 / 姓名"),
             "测试", PL("姓名")],
        ],
    )

    # 1. 背景与价值
    w.h1("1. 背景与价值")
    w.field_bullet("痛点", PL("解决谁的什么具体痛点（引 baseline 现状章说明从什么变到什么）"))
    w.field_bullet("价值", PL("业务价值 + 核心指标 + 具体数字"))
    w.field_bullet("不在本期范围", PL("本期明确不做的相邻能力（划边界防范围争议）；确无则删本行"))

    # 2. 本轮需求（仅本轮变更，走 scene_block_card，与 baseline 同字段集）
    w.h1("2. 本轮需求")
    # 散需求档（补丁包 / 集合体）：先给读者地图（§2.0 索引），再按单轴分组散开；
    # 「反向合并目标」列与 §9 表呼应。内聚特性档（feature）无索引，平铺按用户旅程叙事。
    if tier == "patch":
        # 补丁包：默认全部需求只落索引表（轻项读完表即止），命中升块判据的重项才起 H3。
        # 「默认最轻、升块是加法」是承重设计——反过来（预生成带槽 H3 靠删）必然被填满。
        # 列取「端 / 模块」而非「反向合并目标」：后者与 §9 表重复（同一字段只写一次），
        # 且 §9 推 wiki 时整章剥离、该列却留在 wiki 上给研发看内部维护机制。
        w.h2("2.0 本轮需求索引")
        w.paragraph(PL(
            "分组轴（跟版边界 / 改动所在端 等，只许一条）：一句话说明即可，不强行拆 H2 组。"
            "四条升块判据任一命中 → 另起 ### 2.N 需求块（模板见下方注释）："
            "新增 / 变更业务对象 · 涉状态流转 · 跨端行为不一致 · 有取舍要在决策记录章交代；"
            "都不命中 = 轻项，读完本表即止"
        ))
        if scenes:
            # 编号列用需求序号 2.{i}；重项另起的 H3 沿用同一编号空间（读者在表或块里都找得到）。
            # scene-list 场景号（A-1）不进 patch 需求块——散点需求未必对应单一场景。
            index_rows = [
                [f"2.{i}", s.name, PL("H5 / Web / 通用"),
                 PL("做 X（原 Y 问题）"), PL("判定点；判定点"), PL("P0/P1")]
                for i, s in enumerate(scenes, start=1)
            ]
        else:
            index_rows = [[PL("编号"), PL("需求名"), PL("端 / 模块"),
                           PL("做 X（原 Y 问题）"), PL("判定点；判定点"), PL("P0/P1")]]
        w.table(
            headers=["编号", "需求", "端 / 模块", "修改点", "验收", "优先级"],
            rows=index_rows,
        )
        w.raw(_delta_patch_heavy_template())
    elif tier == "bundle":
        w.h2("2.0 本轮需求索引")
        w.paragraph(PL(
            "分组只许沿一条轴（模块 / 主题 等，选读者跨引最少的一条）："
            "把下列需求拆成 N 个 ## 组 X · 组名 H2，每组归拢相关需求"
        ))
        if scenes:
            index_rows = [
                [f"2.{i}", s.name, PL("组名"), PL("baseline 哪个模块章"), PL("P0/P1")]
                for i, s in enumerate(scenes, start=1)
            ]
        else:
            index_rows = [[PL("编号"), PL("需求名"), PL("组名"), PL("baseline 模块章"), PL("P0/P1")]]
        w.table(headers=["编号", "需求", "分组", "反向合并目标", "优先级"], rows=index_rows)
    # patch 档已在 §2.0 表收口（重项由上方注释模板按需复制），不预生成需求块。
    if tier != "patch":
        if scenes:
            for i, scene in enumerate(scenes, start=1):
                scene_block_card(
                    w,
                    f"2.{i} {scene.id}",
                    scene.name,
                    story=PL("谁/做什么/为什么"),
                    spec_rows=[
                        (
                            [(f"./assets/scene-{scene.id}.png", f"{scene.name}低保真")],
                            [
                                (PL("父规格，如「表单内二选一」"), [PL("子项 A"), PL("子项 B")]),
                                PL("字段 / 状态：创建时落定 → 此后只读"),
                            ],
                            [PL("这一屏 QA 能勾的判定点")],
                        ),
                    ],
                    data_impact=[PL("跨模块联动 / 全局规则 / 迁移（表画不出的）")],
                    exceptions=[[PL("触发条件"), PL("系统响应"), PL("用户感知")]],
                    acceptance_criteria=[PL("跨行 / 反向态验收（塞不进单屏的）")],
                    heading_level=3,
                )
        else:
            w.paragraph(PL("本轮需求场景（scene-list 为空时手填）"))

    # 3. 业务对象增量（可删 · 与 baseline §3.2 同构，反向合并直接搬章 → §9 表）
    w.h1("3. 业务对象增量")
    w.paragraph(PL("本轮无新增 / 变更业务对象则整章删除（§3/§4/§5 同）。"))
    w.h2("3.1 新增 / 变更业务对象")
    w.paragraph(bold(PL("对象名，如「交易卡片」")))
    w.table(
        headers=["属性", "类型范畴", "数据来源", "说明"],
        rows=[
            [PL("属性名"), PL("ID / 字符串 / 枚举 / 金额 等"), PL("用户输入 / 系统生成 / 接口"), PL("业务含义")],
        ],
    )
    w.paragraph(bold("生命周期") + "：" + PL("草稿 → 待审核 → 已发布 → 已删除 等"))
    w.paragraph(bold("关系") + "：" + PL("和其他业务对象的关联，如 1 个帖子附 1 张交易卡片"))

    # 4. 状态机增量（可删 · 与 baseline §3.3 同构，反向合并直接搬章 → §9 表）
    w.h1("4. 状态机增量")
    w.h2("4.1 新增 / 变更状态机")
    w.paragraph(bold(PL("对象名")) + " 状态迁移表：")
    w.table(
        headers=["起始状态", "触发事件", "终止状态", "谁触发"],
        rows=[
            [PL("起始态"), PL("触发事件"), PL("终止态"), PL("用户 / 系统")],
        ],
    )

    # 5. 全局规则增量（可删 · 与 baseline §4 同构，反向合并直接搬章 → §9 表）
    w.h1("5. 全局规则增量")
    w.h2("5.1 新增跨场景规则")
    w.paragraph(bold(PL("规则名")) + "：" + PL("规则描述 + 违反时的处理 + 适用场景"))
    w.h2("5.2 归因规则增量（可选）")
    w.table(
        headers=["漏斗", "定义", "归因窗口"],
        rows=[
            ["L1", PL("曝光口径"), "—"],
            ["L2", PL("点击口径"), PL("实时 / Nh")],
        ],
    )

    # 6. 决策记录（WHY）
    w.h1("6. 决策记录（WHY）")
    w.paragraph(PL("为什么这么定 / 否决了什么方案 / 取舍依据（delta 专属，不进 baseline）"))

    # 7. 埋点（本轮新增事件）+ 看板口径（连回 §1 本轮核心指标，闭环「定了指标→看板能看」）
    w.h1("7. 埋点与看板")
    w.h2("7.1 本轮新增事件")
    w.paragraph("事件名与属性名为本轮拟名，待神策注册后回填真名。多属性事件每属性一行，事件名 / 触发机制列重复，数据团队按事件英文名 group。")
    w.table(
        headers=["所属页面", "事件中文名", "事件英文名", "属性中文名", "属性英文名", "数据类型", "是否必填", "数据值示例", "应埋点平台", "触发机制"],
        rows=[[PL("页面 / 模块"), PL("操作中文名"), PL("snake_case 拟名"), PL("属性中文名"), PL("snake_case 拟名"), PL("NUMBER / STRING / BOOL"), PL("是 / 否"), PL("枚举值或 —"), PL("APP / Web / H5 / 服务端"), PL("用户做了什么 / 系统触发时机")]],
    )
    w.h2("7.2 看板口径")
    w.table(
        headers=["指标", "计算口径", "支撑 §1 哪个核心指标"],
        rows=[[PL("指标名"), PL("分子 / 分母"), PL("对应本轮核心指标")]],
    )

    # 8. 排期 / 上线节奏（5 列表，与产品线真相源同构，供周报扫业务节奏分桶）
    w.h1("8. 排期 / 上线节奏")
    w.h2("8.1 排期")
    # 一张表兼顾两个视角：研发 / 测试看提测~走查的交付节奏，PM 看上线影响哪些指标。
    w.table(
        headers=["阶段", "起止", "进度", "状态", "影响指标"],
        rows=[
            ["前端", PL("YYYY-MM-DD ~ YYYY-MM-DD"), PL("%"), PL("进行中 / 待启 / 已完成"), "—"],
            ["后端", PL("YYYY-MM-DD ~ YYYY-MM-DD"), PL("%"), PL("进行中 / 待启 / 已完成"), "—"],
            ["提测", PL("YYYY-MM-DD"), "—", PL("待启 / 已提测"), "—"],
            ["测试周期", PL("YYYY-MM-DD ~ YYYY-MM-DD"), PL("%"), PL("进行中 / 待启 / 已完成"), "—"],
            ["产品走查", PL("YYYY-MM-DD"), "—", PL("待启 / 已完成"), "—"],
            ["上线", PL("YYYY-MM-DD（app 跟版）"), "—", PL("待启 / 灰度中 / 已完成"), PL("影响哪些指标")],
        ],
    )
    w.h2("8.2 上线后验证 & 回滚")
    w.table(
        headers=["验证项", "判定指标 / 阈值", "回滚触发条件"],
        rows=[[PL("核心功能可用"), PL("成功率 / 指标达标线"), PL("低于阈值 / 报错率超标")]],
    )

    # 9. 反向合并指引（上线后执行）
    # 本章推 Confluence 时整章剥离（DEFAULT_EXCLUDE_SECTIONS），是内部机制的唯一落点。
    # baseline 路径不写进正文——工具按约定推导（scripts/lib/truth_source.resolve），
    # 写死路径既是 plumbing 又会被 plain-language-gate 判为内部文件名。
    w.h1("9. 反向合并指引（上线后执行）")
    w.paragraph(
        "本 delta 只写本轮需求 + WHY，术语 / 模块树 / 未变规则引产品线基线不重复。"
        "上线后按承重不变量执行：先写基线变更记录行（状态=已登记）→ 反向合并 → 状态推进「已合并」。"
    )
    w.table(
        headers=["baseline 目标章", "合并方式", "合并动作"],
        rows=[
            [PL("模块章名"), "插入 / 整块替换", PL("粘贴本 delta 哪个需求")],
            [PL("业务对象词典（§3.2）"), "插入 / 整块替换", PL("搬 §3 / 本轮无删行")],
            [PL("状态机全集（§3.3）"), "插入 / 整块替换", PL("搬 §4 / 本轮无删行")],
            [PL("全局规则（§4）"), "插入 / 整块替换", PL("搬 §5 / 本轮无删行")],
        ],
    )
    return w.render()
