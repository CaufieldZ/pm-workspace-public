<div align="center">

# PM Workspace

`AI-NATIVE · PRODUCT MANAGEMENT · PM-WS`

会议纪要 / MRD / 竞品截图 → 场景清单、交互大图、PRD、行为规格。18 个 Skill 覆盖产品经理全链路。

[![License](https://img.shields.io/badge/license-Apache%202.0-1f54d6?style=flat-square)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-18-D97757?style=flat-square)](.claude/skills)
[![Hooks](https://img.shields.io/badge/hooks-17-000?style=flat-square)](.claude/hooks)
[![Audit](https://img.shields.io/badge/audit-15_categories-000?style=flat-square)](.claude/skills/workspace-audit)
[![Python](https://img.shields.io/badge/python-3.10+-000?style=flat-square)]()
[![Node](https://img.shields.io/badge/node-18+-000?style=flat-square)]()
[![Claude Code](https://img.shields.io/badge/claude_code-native-000?style=flat-square)](https://docs.anthropic.com/en/docs/claude-code)

</div>

---

## 解决什么问题

| 维度 | 之前 | 之后 |
|:--|:--|:--|
| 输入 | 会议纪要 / MRD / 竞品截图 / 口头需求 | 同左 |
| 过程 | PM 手动画原型、写 PRD、反复对齐 | AI 按 Skill 自动产出，PM 审核微调 |
| 耗时 | 3-5 天 | 10 分钟 − 2 小时 |
| 一致性 | 每次结果不同，术语混乱 | 编号锁定 + 术语全局一致 + 15 类 audit 拉通 |
| 下游 | PRD 扔给研发自己理解 | 切分 behavior-spec / page-structure / test-cases，AI Agent 直接消费 |
| 方法论沉淀 | 散落在个人习惯和文档 | 战略层 + 工作流层 + 项目层三层落盘，可跨 session / 跨模型复用 |

---

## 先看 Demo · 20 分钟跑完基金认申赎

虚构的私募基金认申赎项目，完整走完 context → scene-list → 交互大图 → PRD 四步，Sonnet 4.6 模型实测 ~20 分钟：[`examples/private-fund-demo/`](examples/private-fund-demo/)。

![交互大图 hero](https://raw.githubusercontent.com/CaufieldZ/pm-workspace-public/main/examples/private-fund-demo/screenshots/imap-hero.png)

> 上图是交互大图顶部 PART 0 · H5 投资人端（A-1 基金详情 + 认购下单 / A-2 协议签署 + 冷静期）。全部 5 Scene + 跨端数据流表见 [完整 HTML](examples/private-fund-demo/deliverables/imap-private-fund-v1.html)。

| 产出物 | 规模 |
|:--|:--|
| [context.md](examples/private-fund-demo/context.md) | 九章 / 5 个场景锁定 |
| [scene-list.md](examples/private-fund-demo/scene-list.md) | 2 View / 5 Scene / P0 × 5 |
| [交互大图 HTML](examples/private-fund-demo/deliverables/) | 单文件 / 9 手机 mockup + 1 Web 后台 + 跨端数据流表 |
| [PRD docx](examples/private-fund-demo/deliverables/) | 横版 8 章 / 20 表格 / 5 张 Scene 截图自动插入 |

选私募基金是因为合规链条典型（合格投资者 / 冷静期 / 大额赎回 / 净值披露），能完整展示"从模糊需求到 PRD 交付"全流程。生成脚本在 `examples/private-fund-demo/scripts/`，拷到自己项目改数据即可。

---

## Quick Start

```bash
# 1. Clone
git clone git@github.com:CaufieldZ/pm-workspace.git
cd pm-workspace

# 2. 装依赖
pip install -r requirements.txt   # python-docx · defusedxml · playwright · matplotlib · numpy
npx playwright install chromium   # 竞品采集无头浏览器
npm install                       # docx (Node)

# 3. 激活防腐化 hook（pre-commit 跑 audit.sh 1,2,3,4,7,12,13,14,15）
git config core.hooksPath .githooks

# 4. 个性化（可选）
#    编辑 .claude/rules/soul.md 写入沟通偏好（已 gitignored）

# 5. 打开项目
#    VSCode + Claude Code 扩展（推荐）
#    不建议 Cursor —— Agent 体系会与 Skill / Hook 冲突

# 6. 第一个项目
#    在 Claude Code 中输入：
#    > 新项目 my-first-project，需求是…
```

---

## 三层认知

整个系统由**战略 → 工作流 → 项目**三层知识支撑，下层引用上层，上层不关心下层：

### Layer 1 · 战略层

`product-lines.md` · **产品线地图**。每 session 必读（CLAUDE.md 顶部 `@` 引用），让模型做单条产品线决策时仍能看到整体盘（核心漏斗 / 北极星 KPI / 产品线协同矩阵）。**本文件 gitignored**，不进 public sync —— 每家公司自己写一份。

### Layer 2 · 工作流层

产品经理方法论落盘，跨项目复用：

| 文件 | 管什么 |
|:--|:--|
| `CLAUDE.md` | Claude Code 工具层配置 · 快捷路由 · 上下文管理 |
| `.claude/rules/pm-workflow.md` | 需求路由 · 三条链路 · 跨 Skill 串联约束 · 批量变更流程 |
| `.claude/rules/html-pipeline.md` | HTML 产出物分步生成（Step A/B/C）+ 美学硬底线（反 AI slop 六禁） |
| `.claude/rules/soul.md` | 个人沟通偏好 + 纠正记录（gitignored） |

### Layer 3 · 项目层

`projects/{产品线}/{项目}/context.md` · **项目唯一真相源**。PM 与 AI 讨论需求后的结构化沉淀，所有下游产出物都从它生长。改一个术语、加一个场景，依赖链自动扫描波及范围。

九章结构：静态章（1-6 · 项目现在是什么样）+ 动态章（7/9 · 怎么变过来的）+ 混合章（8 · 执行计划）。核心约束：动态章按日期追加不改不删，静态章必须反映最新状态。

```
素材（会议纪要 / MRD / 竞品 / 口述）
        ↓ 与 AI 讨论提炼
   context.md 九章
        ↓ 进入产出物链路
   scene-list → imap → prototype → prd → bspec/pspec/test-cases → cross-check
        ↓
   下游 AI Agent 直接消费
```

执行优先级：**Skill 硬规则 > 工作流规则 > 模型默认行为**。

---

## Skill 流水线

10 个 Pipeline Skill 按依赖顺序执行，5 个独立 + 3 个工具 Skill 随时调用。共 18 个。

```
1 scene-list ─→ 2.5 arch-diagrams* ─→ 3 interaction-map
                                              │
  ┌───────────────────────────────────────────┘
  ▼
4 prototype* ─→ 5 prd ──┬─→ 6 behavior-spec* ─┐
                        ├─→ 6 page-structure* ├─→ 8 cross-check
                        ├─→ 7 test-cases*     ┘
                        └─→ 9 ops-handbook*

                                                    * = optional
```

### Pipeline（10 个）

| # | Skill | 产出 | 格式 |
|:-|:-|:-|:-|
| 1 | scene-list | 需求拆解为场景，编号锁定全局引用（md + 可选 HTML 视觉版） | `.md` / `.html` |
| 2.5 | architecture-diagrams | 多系统 / 资金流转架构，多 Tab 文档 | `.html` |
| 3 | interaction-map | 多端 UI 流 + 跨端数据流，Mockup 级 | `.html` |
| 4 | prototype | 可点击高保真原型，数据驱动联动 | `.html` |
| 5 | prd | 横版左图右文 PRD，context 6.x 关键假设清单驱动 | `.docx` |
| 6 | behavior-spec | 研发 AI 消费：状态机 + 异常处理 | `.md` |
| 6 | page-structure | 设计 / 前端 AI 消费：组件树 + 数据绑定 | `.md` |
| 7 | test-cases | QA AI 消费：Pairwise 建模 + 四类全覆盖 | `.md` |
| 8 | cross-check | 7 维自动对账（编号 / 术语 / 字段 / 状态 / 合规 / 埋点 / 假设） | 终端输出 |
| 9 | ops-handbook | 运营 / 客服 / BD 步骤化文档，PRD 终稿后产出 | `.docx` |

### Standalone（5 个）

| Skill | 说明 |
|:-|:-|
| competitor-analysis | 竞品调研，三角对比 + 可借鉴点提取 |
| data-report | 周报 / 月报 / 季报，神策 + 有数自动化 |
| flowchart | 流程图 / 泳道图 / 审批流，独立产出可嵌入其他文档 |
| mrd-review | MRD 评审：投票表 + 价值判断 + 市场窗口验证 |
| ppt | 方案 / SOP → HTML 多 Tab 文档 + 口播稿 |

### Tool（3 个）

| Skill | 说明 |
|:-|:-|
| intel-collector | 情报采集：APP 截图 / Web 全页截图 / 公告抓取 |
| skill-creator | 创建新 Skill，自动生成 frontmatter + 注册 |
| workspace-audit | 15 类全局诊断（10 硬检查 + 5 软检查），含 Hooks 健康度 |

---

## 下游 AI 消费

传统 PM 工作流到 PRD 就结束了。这套系统多走一步 —— **把 PRD 切分为 AI Agent 可直接消费的结构化文档**。

```
         ┌─→ behavior-spec  ─→ Dev AI    (Cursor · Copilot · Claude Code)
         │
PRD ─────┼─→ page-structure ─→ Design / Frontend AI
         │
         └─→ test-cases     ─→ QA AI · 自动化测试
```

| 文档 | 消费方 | 价值 |
|:-|:-|:-|
| behavior-spec | 研发 AI | "用户做 X → 系统响应 Y" 完整规格，无需读 PRD 全文 |
| page-structure | 设计 / 前端 AI | 组件树 + 数据绑定 + 交互状态，无需看原型截图猜布局 |
| test-cases | QA AI · 自动化 | 边界值 + 异常场景 + 合规校验，开箱即用 |

---

## 工程保障

### 硬约束（代码拦截）

| 机制 | 说明 |
|:-|:-|
| 防腐化 hook | `.githooks/pre-commit` 在 Skill / 规则 / `.claude/hooks/` 变更时跑 `audit.sh 1,2,3,4,7,12,13,14,15`（9 类硬检查），不通过拦截 commit。secret scan 拦 figd/sk-ant/ghp/AKIA 等 token |
| 17 个 runtime hook | CJK 标点 / 讲人话 / 版本同步 / 设备命名 / wiki push / Dippy 破坏性命令拦截 / Learn-Rule 纠错捕获等闸门。stderr warning 看到立改，阻断级的直接拒写 |
| 15 类 workspace-audit | 脚本硬检查 10 类（文件 / 数值 / 依赖 / 规则 / Token / 产出物 / SKILL_TABLE / scripts / imports / 三件套纯洁性）+ 软检查 5 类（含 Hooks 健康度） |
| HTML 铁律 | > 200 行必须脚本生成（Step A 骨架 → B fill → C 自检），禁止 Write 直写 |
| 自检反压 | 每个 Skill 自带 checklist，不通过最多自动修复 2 次，仍失败停下报告，禁止静默跳过 |
| pre-deliverable-source-gate | 有 gen 脚本的 HTML 即只读，改动只进源文件 |

### 软约束（方法论）

| 机制 | 说明 |
|:-|:-|
| 编号锁定 | 场景编号确认后不可改动，新增只追加 |
| 术语一致性 | 模块 / 组件 / 状态名一处定义，全链路复用 |
| 变更级联 | context.md 改动 → impact-check 扫描依赖 → pipeline 顺序升版 → cross-check 拉通 |
| context.md 静动分层 | 静态章反映最新状态，动态章按日期追加不改不删，两者不矛盾 |
| 关键假设清单 | PRD context 6.x 显式列前置假设，cross-check 验证落地 |
| 批量变更流程 | ≥ 2 文件跨文件变更强制走 impact-check → 按 pipeline 顺序改 → 收尾 cross-check |

### 数据驱动

| 机制 | 说明 |
|:-|:-|
| 全链路埋点 | 17 个 hook 通过 `lib/log.sh` 写 `.claude/logs/usage.jsonl`（skill 触发 / hook warn-block-clean / gate skip），半月一次 dashboard 决策 |
| dashboard | `python3 scripts/dashboard.py` 聚合 hook + skill + 项目快照，输出 `.claude/workspace-dashboard.md` |
| Session 保活 | `pre-compact.sh` 在上下文压缩前注入 `session-state.md` + git 动态快照到摘要，compact 后进度不丢 |
| 规则半衰期 | `.claude/runbooks/half-life.md` 给规则打 volatile / durable 标签，半年 review 砍弱触发规则 |
| public repo 脱敏同步 | `sync_public.sh` 把框架层脱敏到独立 public repo，`.public/overrides/` 存替换文件，战略层 / 项目 / 素材全部排除 |

### 视觉底线

HTML 产出物（imap / prototype / ppt / flowchart / arch）共享 `_shared/claude-design/tokens.css`：

| 维度 | 值 |
|:-|:-|
| 主色 | claude.ai chat UI 暖近黑 `#1F1F1E` + 暖灰白 `#C3C2B7` |
| Accent | Anthropic terra cotta `#D97757`（次 `#6A9BCC` / 三 `#788C5D`，多 track 循环） |
| 营销级高对比 | `.theme-cd-brand` → `#141413` / `#FAF9F5` |
| 语义色 | 成功 `#00B42A` · 失败 `#F53F3F`（跨主题通用） |
| 字体 · display | `Noto Serif SC` + `Lora` |
| 字体 · body | `Noto Sans SC` + `Poppins` |
| 字体 · mono | `JetBrains Mono` |
| **CJK 优先铁律** | 任何字体栈，中文字体必须排英文字体前 |

对标 [Anthropic 官方 brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines) 免费授权。

**反 AI slop 六禁**（规则层强制 · 违反拒写）：全屏渐变 / emoji 装饰标题 / 圆角卡片 + ≥2px accent border（任一方向）/ SVG 画人物场景 / 烂大街字体（Inter·Roboto·Space Grotesk）作 CJK 正文 / 每卡片都带 icon。

---

## 目录结构

```
pm-workspace/
├── CLAUDE.md                    # Claude Code 项目指令入口
├── product-lines.md             # 战略层 · 产品线地图（gitignored）
├── sync_public.sh               # 框架层 → public repo 脱敏同步
├── .githooks/pre-commit         # 防腐化 hook（跑 audit.sh 9 类）
├── .public/
│   └── overrides/               # public sync 替换文件
├── .claude/
│   ├── hooks/                   # 17 个 runtime hook
│   │   ├── lib/log.sh           #   共享埋点（写 logs/usage.jsonl）
│   │   ├── pre-compact.sh       #   Session 状态保活
│   │   ├── post-cjk-punct-check.sh
│   │   ├── post-plain-language-check.sh  # 讲人话自检（禁内部锚点外泄）
│   │   ├── pre-version-sync-gate.sh
│   │   ├── pre-wiki-push-gate.sh
│   │   ├── stop-learn-capture.sh         # 从 transcript 提取 [LEARN] 追加 LEARNED.md
│   │   └── ...                  #   共 17 个
│   ├── rules/
│   │   ├── pm-workflow.md       #   工作流层 · 方法论
│   │   ├── html-pipeline.md     #   工作流层 · HTML 生成 + 美学
│   │   └── soul.md              #   个人偏好（gitignored）
│   ├── skills/                  # 18 个 Skill（三件套：SKILL.md + scripts/ + references/ + assets/）
│   │   ├── {skill}/scripts/     #   可执行代码（Claude 调用执行，不读源码）
│   │   ├── {skill}/references/  #   .md 文档（按需 Read 加载）
│   │   ├── {skill}/assets/      #   模板 / 字体 / 配置（被脚本读出写进产物）
│   │   └── _shared/
│   │       └── claude-design/   #     共享美学 token
│   ├── chat-templates/          # Chat 轨备用模板
│   ├── runbooks/                # 规则半衰期 / 迁移档案
│   ├── logs/                    # 埋点（usage.jsonl / skip-gates.log）
│   └── settings.json
├── examples/                    # 脱敏示例项目（public 版可见）
│   └── private-fund-demo/       #   基金认申赎全链路样本
├── scripts/                     # 公共脚本
│   ├── dashboard.py             #   聚合 hook / skill / 项目 → workspace-dashboard.md
│   ├── call_mcp.py              #   通用 MCP 调用（0 schema 开销）
│   ├── fetch_confluence.py
│   ├── fetch_figma.py
│   ├── fetch_web.py             #   SPA / 多页抓取（替代 firecrawl）
│   ├── pull_meeting_notes.py    #   钉钉闪记纪要拉取
│   ├── md_to_confluence.py
│   ├── impact-check.sh          #   场景变更影响面扫描
│   └── version-bump.sh          #   产出物升版
├── requirements.txt
├── package.json
├── references/                  # 本地素材（gitignored）
│   └── competitors/
└── projects/                    # 工作项目（gitignored，Schema v2 两层）
    ├── {产品线}/
    │   └── {项目}/
    │       ├── context.md       #   项目唯一真相源（九章）
    │       ├── scene-list.md    #   锁定的场景编号
    │       ├── inputs/
    │       ├── scripts/
    │       └── deliverables/
    └── {顶级项目}/              # 不归业务线的方案型 / 基建
```

---

## Chat 轨（备用）

没装 Claude Code 环境也能用，但会失去战略层 / hooks / 埋点 / 脚本自动化，初版质量下降一截。流程：

- 文字产出（场景清单 / 竞品分析 / PRD 文字版）：复制 `.claude/chat-templates/` 对应 prompt，替换占位符发到 Claude / ChatGPT
- HTML 产出（交互大图 / 原型 / 架构图）：上传 3 个文件（`context.md` + `templates-index.md` + 模板 HTML）

Chat 轨适合临时应急 / 不想折腾环境。长期使用建议切 Claude Code。

---

## 推荐模型

| 角色 | 模型 | 说明 |
|:-|:-|:-|
| 需求理解 · 架构决策 · 复杂推理 | Claude Opus 4.7 (1M) | 方案决策 + 全链路执行主力 |
| 日常编码施工 · 格式化输出 | Claude Sonnet 4.6 (1M) | Step B 填充可降级，省 ~46% 成本 |
| 备选（Sonnet 用不起时） | GLM 5.1 · Kimi K2.6 | 性价比备选，context 按模型查表 |

---

## 自定义 Skill

用 `skill-creator` 创建自己的 Skill：

```
> 创建 skill：需求评审检查清单
```

Skill Creator 引导完成：触发词定义 → 输入输出 → 执行步骤 → 自检清单 → 注册到 pipeline。详见 [`.claude/skills/skill-creator/SKILL.md`](.claude/skills/skill-creator/SKILL.md)。

---

## Contributing

欢迎 Issue 和 PR。

```bash
git clone git@github.com:CaufieldZ/pm-workspace.git
cd pm-workspace
git config core.hooksPath .githooks
git checkout -b feat/your-feature
# 修改后 commit（pre-commit hook 自动验证）
git commit -m "feat: your change"
```

---

## License

[Apache License 2.0](LICENSE)

---

<div align="center">

`BUILT WITH · CLAUDE CODE · PYTHON · NODE · HTML`

</div>
