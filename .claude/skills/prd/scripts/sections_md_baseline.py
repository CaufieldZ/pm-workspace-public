"""baseline / delta profile 骨架生成（迭代文档集模型）。

从 sections_md 拆出：baseline = 线上当前态全量真相源（模块树 + changelog），
delta = 单轮迭代（本轮改动按模块 / 页面组织，引 baseline）。被 gen_prd_skeleton.py 调用。
"""
from __future__ import annotations

from datetime import date

from core.md_renderer import MdWriter, bold, image_spec_table, scene_block_card
from sections_md import PL, SceneInfo, _parse_scenes, build_chapter_4

# ── baseline / delta profile（迭代文档集模型） ──────────────────────────────
#
# baseline = 线上当前态全量真相源（living，按模块树组织，含 changelog 索引章）
# delta    = 单轮迭代（本轮改动按模块 / 页面组织，术语 / 模块树不重复，引 baseline）
# delta §3/§4/§5 与 baseline 对应章同构，反向合并直接搬章。


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


def _delta_module_block(w: MdWriter, num: str) -> None:
    """§2 一个模块 / 页面需求块的空模板：图 + 规格两列表、变体差异表、验收。

    一块对应一个模块或页面（几个场景是同一组件的变体时合成一块），
    骨架只吐一块示范，PM 按本轮实际模块数复制——块数跟着需求走，不跟 scene-list 走。
    """
    w.h2(f"{num} " + PL("模块或页面名（覆盖的场景编号写括号里）"))
    w.raw(image_spec_table(
        [("./assets/" + PL("截图文件名") + ".png", PL("截图说明"))],
        [(PL("区块名，只有一块时删掉"), [PL("一条一件事：条件 → 结果，或 对象：取值")])],
    ))
    w.paragraph(bold("差异") + "（同一模块有几种情况时用，每种情况一列，线上已有的那种也算；只有一种就删掉）")
    w.table(
        headers=["", PL("情况 A"), PL("情况 B")],
        rows=[[PL("不同的那一项"), PL("A 的取值"), PL("B 的取值")]],
    )
    w.paragraph(bold("验收"))
    w.bullet_list([PL("最容易做错的判定点：临界值 / 情况之间的差别 / 反向情况")])


def build_delta_skeleton(info: dict) -> str:
    """delta profile：单轮迭代。只写本轮改动，每个事实只落一处，线上现状引 baseline。"""
    w = MdWriter()
    project = info.get("project_name", PL("产品线名"))
    version = info.get("version", "1")
    tier = info.get("tier", "feature")
    tier_label = {"patch": "补丁包", "feature": "内聚特性", "bundle": "集合体"}.get(tier, "内聚特性")

    w.h1(f"{project} · Delta PRD · {version} · 【业务名与本轮主题待填充】")
    # 协作头（对齐公司 PRD 模板的 PRD信息 / 团队信息 / 资源对接三张表，压成一张）。
    # 用表格而非 bullet 是承重设计：md_to_confluence 的 _preamble_all_meta 只把
    # `- ` / `> ` / `---` / 空行判为「内部元信息」整块剥离，表格行（`|` 开头）→ 保留上 wiki。
    # 「状态」「内部项目系统」两格由 sync_hx_status.py 按内部项目系统回写，故固定摆第 3 列 key / 第 4 列 value
    # （值落行尾单元格，回写正则好锚），勿调列位。日期只在 §8 排期表（推送时整章剥离）。
    w.table(
        headers=["项", "内容", "项", "内容"],
        rows=[
            ["PRD 版本", version,
             "状态", PL("待排期 / 开发中 / 已上线 / 已合并（sync_hx_status.py 按内部项目系统回写，勿手填）")],
            ["拟制人 / 日期", PL("姓名 / YYYY-MM-DD"),
             "内部项目系统", PL("H 号（上线日期 / 状态唯一权威源）")],
            ["重要性 / 紧迫性", PL("高 / 中 / 低"),
             "迭代档位", tier_label],
            ["端侧范围", PL("App / H5 / Web 工作台 / CMS"),
             "提测 / 走查 / 上线", "待定"],
            ["产品 / 交互", PL("姓名"),
             "设计 / 设计稿", PL("姓名 / 设计稿链接")],
            ["前端 / 后端", PL("姓名 / 姓名"),
             "测试", PL("姓名")],
        ],
    )

    # 1. 概述：问题 / 方案 / 成功标准 + 范围表，全文唯一讲「为什么做、做多大」的地方
    w.h1("1. 概述")
    w.field_bullet("要解决的问题", PL("谁在什么场景遇到什么问题，一两句"))
    w.field_bullet("本轮做什么", PL("一两句说清方案"))
    w.field_bullet("成功标准", PL("指标 + 目标值；有回滚条件也写这里"))
    w.paragraph(bold("范围"))
    w.table(
        headers=["模块 / 页面", "本轮改动", "实施方"],
        rows=[[PL("模块名"), PL("一句话"), PL("哪个团队 / 端")]],
    )
    w.field_bullet("不做", PL("相邻但本轮不做的事，一行；没有就删"))
    w.paragraph(bold("待确认"))
    w.bullet_list([PL("输入里没给、要 PM 或相关方拍板的点；没有就删本段")])

    # 2. 本轮需求：按模块 / 页面组织。patch 只出索引表；feature 出一块示范；bundle 两者都出
    w.h1("2. 本轮需求")
    if tier == "patch":
        w.table(
            headers=["编号", "需求", "端 / 模块", "改动", "验收", "优先级"],
            rows=[["2.1", PL("需求名"), PL("H5 / Web / 通用"),
                   PL("做 X（原 Y 问题）"), PL("判定点"), PL("P0/P1")]],
        )
    else:
        if tier == "bundle":
            w.table(
                headers=["编号", "需求", "分组", "优先级"],
                rows=[["2.1", PL("需求名"), PL("组名"), PL("P0/P1")]],
            )
        _delta_module_block(w, "2.1")

    # 3–5 四支柱增量：与 baseline 对应章同构，反向合并直接搬章；本轮没有就整章删
    w.h1("3. 业务对象增量")
    w.h2("3.1 " + PL("对象名"))
    w.table(
        headers=["属性", "类型", "来源", "说明"],
        rows=[[PL("属性中文名"), PL("ID / 文本 / 枚举 / 金额 等"), PL("用户输入 / 系统生成 / 接口"), PL("业务含义")]],
    )

    w.h1("4. 状态机增量")
    w.h2("4.1 " + PL("对象名") + "状态")
    w.table(
        headers=["起始状态", "触发", "终止状态", "谁触发"],
        rows=[
            ["不存在", PL("创建动作"), PL("初始状态"), PL("用户 / 系统")],
            [PL("起始状态"), PL("触发"), PL("终止状态"), PL("用户 / 系统")],
        ],
    )

    w.h1("5. 全局规则增量")
    w.bullet_list([bold(PL("规则名")) + "：" + PL("两个以上模块共用的规则写这里，模块里只写规则名")])

    # 6. 决策：推送时整章剥离，只给 PM 和后来的维护者看。只收输入里给过理由的取舍，
    # 不设「否掉的方案」列——空列会诱导模型编理由。
    w.h1("6. 决策记录")
    w.paragraph("只记输入材料里给过理由的取舍，理由照输入写。输入没给理由的决策不记；整章没有就删。")
    w.table(
        headers=["决策", "理由（来自输入）"],
        rows=[[PL("定了什么，一句"), PL("输入里给的理由；选 A 不选 B 时写上 B")]],
    )

    w.h1("7. 埋点与看板")
    w.h2("7.1 本轮新增事件")
    w.paragraph("事件名与属性名为本轮拟名，待行为分析平台注册后回填真名。多属性事件每属性一行。")
    w.table(
        headers=["所属页面", "事件中文名", "事件英文名", "属性中文名", "属性英文名", "数据类型", "是否必填", "数据值示例", "应埋点平台", "触发机制"],
        rows=[[PL("页面 / 模块"), PL("操作中文名"), PL("snake_case 拟名"), PL("属性中文名"), PL("snake_case 拟名"), PL("NUMBER / STRING / BOOL"), PL("是 / 否"), PL("枚举值或 —"), PL("APP / Web"), PL("客户端可观测的触发点，如「提交成功响应后」")]],
    )
    w.h2("7.2 看板口径")
    w.table(
        headers=["指标", "计算口径"],
        rows=[[PL("指标名（与概述的成功标准同名）"), PL("分子 / 分母")]],
    )

    # 8. 排期（5 列表，与产品线真相源同构，供周报扫业务节奏分桶；推送时整章剥离）
    w.h1("8. 排期 / 上线节奏")
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

    # 9. 反向合并指引：推送时整章剥离，是内部机制的唯一落点。
    # baseline 路径不写进正文——工具按约定推导（scripts/lib/truth_source.resolve）。
    w.h1("9. 反向合并指引（上线后执行）")
    w.paragraph(
        "上线后按顺序执行：先写基线变更记录行（状态=已登记）→ 反向合并 → 状态推进「已合并」。"
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
