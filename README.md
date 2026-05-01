<div align="center">

# PM Workspace

`AI-NATIVE · PRODUCT MANAGEMENT · PM-WS`

会议纪要 / MRD / 竞品截图 → 场景清单、交互大图、PRD、行为规格。18 个 Skill 覆盖产品经理全链路。

[![License](https://img.shields.io/badge/license-Apache%202.0-1f54d6?style=flat-square)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-18-D97757?style=flat-square)](.claude/skills)
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
| 一致性 | 每次结果不同，术语混乱 | 编号锁定 + 术语全局一致 + 自检拉通 |
| 下游 | PRD 扔给研发自己理解 | 切分 behavior-spec / page-structure / test-cases，AI Agent 直接消费 |

---

## Quick Start

### 方式一 · Chat 轨（零依赖）

打开 Claude / ChatGPT / 任意大模型，按下面两类走：

- 文字产出（场景清单、竞品分析、PRD 文字版）：复制 `.claude/chat-templates/` 对应 Prompt，替换占位符发送
- HTML 产出（交互大图、原型、架构图）：上传 3 个文件（`context.md` + `templates-index.md` + 模板 HTML）

### 方式二 · Claude Code 轨

```bash
# 1. Clone
git clone git@github.com:CaufieldZ/pm-workspace.git
cd pm-workspace

# 2. 安装依赖
pip install -r requirements.txt   # python-docx · defusedxml · playwright · matplotlib · numpy
npx playwright install chromium   # 竞品采集无头浏览器
npm install                       # docx (Node)

# 3. 激活防腐化 hook
git config core.hooksPath .githooks

# 4. 个性化（可选）
#    编辑 .claude/rules/soul.md 写入你的沟通偏好（已在 .gitignore 中）

# 5. 打开项目
#    VSCode + Claude Code 扩展（推荐）
#    不建议 Cursor —— 其 Agent 会与 Skill / Hook 体系冲突

# 6. 第一个项目
#    在 Claude Code 中输入：
#    > 新项目 my-first-project，需求是…
```

---

## 核心概念 · context.md

`context.md` 是系统的枢纽 —— PM 与 AI 讨论需求后的结构化沉淀，所有产出物从它生长。改一个术语，下游全部产出物跟着改；加一个场景，依赖链自动识别波及范围。

| 身份 | 说明 |
|:--|:--|
| 永久记忆体 | 讨论结论存这里，换 session / 换模型 / 换环境都不丢 |
| 跨环境协议 | Chat 和 Claude Code 共享同一份 context.md，随时切换 |
| 唯一真相源 | 场景编号 · 术语表 · 方案决策 · 业务规则 —— 下游产出物全部从这里读取 |
| 全生命周期 | 项目每次迭代更新，新对话不用重讲背景 |

九章分为**静态章**（1-6 · 项目现在是什么样）、**动态章**（7/9 · 怎么变过来的），第 8 章混合。核心约束：动态章按日期追加不改不删，静态章必须反映最新状态 —— 新决策加到第 7 章后，必须同步更新第 2/5/6 章中被推翻的旧描述。

```
会议纪要 / MRD / 竞品截图 / 口述
          ↓
   与 AI 讨论提炼（Chat 或 Claude Code）
          ↓
   沉淀为 context.md（九章结构）
          ↓
       进入产出物链路
```

---

## 双轨工作流

同一套方法论，两种使用方式，按需选择或混用。

| | Chat 轨 | Claude Code 轨 |
|:--|:--|:--|
| 上手成本 | 0，打开 Chat 即用 | 需安装 Claude Code + 环境 |
| 产出质量 | 初版 60-80 分，需对话迭代 | 初版 85-90 分，骨架脚本 + 规则兜底 |
| HTML 产出 | 有模板兜底但波动大 | 骨架脚本 + 组件库 + 验证规则三重兜底 |
| 可复现性 | 每次结果不同 | 规则 + 模板 + 脚本保障一致性 |
| 适合 | 快速出产物、不想折腾环境 | 追求高质量、愿意投入搭建 |

> 最佳实践：两轨混用。AI 负责方案讨论 → 沉淀为 context.md → Claude Code 批量产出。

---

## 三层架构

```
Layer 1 · 全局规则（公司制度手册）
  CLAUDE.md · pm-workflow.md · soul.md
         ↓
Layer 2 · Skill 技能包（岗位操作手册）
  每种产出物一本：SKILL.md + scripts/（可执行）+ references/（.md 文档）+ assets/（模板/配置）
         ↓
Layer 3 · 项目文件（具体项目资料）
  context.md · scene-list.md · deliverables/
```

执行优先级：Layer 2 Skill 硬规则 > Layer 1 全局规则 > 模型默认行为

---

## Skill 流水线

10 个 Pipeline Skill 按依赖顺序执行，5 个独立 Skill + 3 个工具 Skill 随时调用。共 18 个。

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

| # | Skill | 产出说明 | 格式 |
|:-|:-|:-|:-|
| 1 | scene-list | 需求拆解为场景，编号锁定全局引用 | `.md` / `.html` |
| 2.5 | architecture-diagrams | 多系统 / 资金流转架构，多 Tab 文档 | `.html` |
| 3 | interaction-map | 多端 UI 流 + 跨端数据流，Mockup 级 | `.html` |
| 4 | prototype | 可点击高保真原型，数据驱动联动 | `.html` |
| 5 | prd | 横版左图右文 PRD，九章结构 | `.docx` |
| 6 | behavior-spec | 研发 AI 消费：状态机 + 异常处理 | `.md` |
| 6 | page-structure | 设计 / 前端 AI 消费：组件树 + 数据绑定 | `.md` |
| 7 | test-cases | QA AI 消费：Pairwise 建模 + 四类全覆盖 | `.md` |
| 8 | cross-check | 编号 / 术语 / 字段一致性拉通验证 | 终端输出 |
| 9 | ops-handbook | 运营 / 客服 / BD 步骤化文档，PRD 终稿后产出 | `.docx` |

### Standalone（5 个）

| Skill | 说明 |
|:-|:-|
| competitor-analysis | 竞品调研，三角对比 + 可借鉴点提取 |
| data-report | 周报 / 月报 / 季报数据报告，神策 + 有数 自动化 |
| flowchart | 流程图 / 泳道图 / 审批流，独立产出可嵌入其他文档 |
| mrd-review | MRD 评审：投票表 + 价值判断 + 市场窗口验证 |
| ppt | 方案 / SOP → HTML 多 Tab 文档 + 口播稿 |

### Tool（3 个）

| Skill | 说明 |
|:-|:-|
| intel-collector | 情报采集：APP 截图 / Web 全页截图 / 公告抓取 |
| skill-creator | 创建新 Skill，自动生成 frontmatter + 注册 |
| workspace-audit | 14 类全局诊断（10 硬检查 + 4 软检查），跨文件完整性 / 数值 / 依赖 / 规则 / Token / 三件套纯洁性 |

---

## AI 可消费的下游文档

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
| page-structure | 设计 AI · 前端 AI | 组件树 + 数据绑定 + 交互状态，无需看原型截图猜布局 |
| test-cases | QA AI · 自动化 | 边界值 + 异常场景 + 合规校验，开箱即用 |

---

## 视觉体系

HTML 产出物（imap · prototype · ppt · flowchart · arch-diagrams）基于 `_shared/claude-design/` 共享美学资产：

| Token | 值 |
|:-|:-|
| 主色 | claude.ai chat UI 同款暖近黑 `#1F1F1E` + 暖灰白 `#C3C2B7` + 4 级透明灰阶 |
| Accent | Anthropic terra cotta `#D97757`（次 `#6A9BCC` 蓝 / 三 `#788C5D` 绿，多 track 循环） |
| 营销级高对比 | 切 `.theme-cd-brand` → 官方 `#141413` / `#FAF9F5` |
| 语义色 | 成功 `#00B42A` · 失败 `#F53F3F`（跨主题通用） |
| 字体 · display | `Noto Serif SC` + `Lora`（Anthropic brand-guidelines 钦定 body serif） |
| 字体 · body | `Noto Sans SC` + `Poppins`（Anthropic brand-guidelines 钦定 heading sans） |
| 字体 · mono | `JetBrains Mono` |
| 工具类 | film grain · eyebrow · hairline · 带色阴影 · 低调水印 |

色板与字体均对标 [Anthropic 官方 brand-guidelines skill](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines)，免费授权可放心引用。

反 AI slop 六禁（规则层强制）：全屏渐变 · emoji 装饰标题 · 圆角卡片 + **任一方向 ≥ 2px 的 accent border**（左/右/上/下都禁）· SVG 画 imagery / 人物 / 场景 · 烂大街字体（Inter/Roboto/Space Grotesk 作 CJK 主字体）· 每卡片都带 icon。

---

## 工程保障

| 机制 | 说明 |
|:-|:-|
| 防腐化 hook | `.githooks/pre-commit` 在 Skill / 规则变更时自动跑 `audit.sh 1,2,3,4,7,12,13,14`（8 类硬检查），不通过拦截 commit。secret scan 拦 figd/sk-ant/ghp/AKIA 等 token |
| Session 保活 | `.claude/hooks/pre-compact.sh` 在上下文压缩前注入 `session-state.md` + git 动态快照到摘要，compact 后进度不丢 |
| 全链路埋点 | 14 个 hook 通过 `lib/log.sh` 写 `.claude/logs/usage.jsonl`（skill 触发 / hook warn-block-clean / gate skip），半月跑一次 dashboard 拿数据决策 |
| 规则半衰期 | `.claude/runbooks/half-life.md` 给规则打 volatile / durable 标签：补丁类（CJK 标点 / 字体 / token 预算）半年 review 砍弱触发；方法论类（场景编号 / 九章 / 漏斗）持续投入 |
| 自检反压 | 每个 Skill 自带 checklist，不通过最多自动修复 2 次，仍失败停下报告，禁止静默跳过 |
| impact-check | `bash scripts/impact-check.sh <项目名>` 识别 scene-list 变更波及的下游 deliverable |
| workspace-audit | 双阶段审计 · 脚本硬检查 10 类 + 模型软检查 4 类 = 14 类全局诊断 |
| dashboard | `python3 scripts/dashboard.py` 聚合 14 hook 触发 + 18 skill 使用 + 项目快照，输出 `.claude/workspace-dashboard.md` 一屏看全 |
| HTML 铁律 | > 200 行必须脚本生成（骨架 → 填充 → 自检），禁止 Write 直写 |
| 变更级联 | context.md 改动 → 依赖链扫描 → pipeline 顺序升版 → cross-check 拉通 |
| 编号锁定 | 场景编号确认后不可改动，新增只追加 |
| context.md 只读 | 方案决策由 PM 在 Chat 中与 AI 讨论确定，本地模型不自行修改 |

---

## 目录结构

```
pm-workspace/
├── CLAUDE.md                    # Claude Code 项目指令入口
├── .githooks/pre-commit         # 防腐化 hook
├── .claude/
│   ├── hooks/                   # 14 个 Claude Code runtime hook
│   │   ├── lib/log.sh           #   共享日志函数（统一埋点到 logs/usage.jsonl）
│   │   ├── pre-compact.sh       #   Session 状态保活
│   │   ├── post-cjk-punct-check.sh  # CJK 标点护栏
│   │   ├── post-skill-load.sh   #   Skill 触发埋点
│   │   └── ...                  #   10 个其他 gate（CJK / docx 截图 / 版本同步 / wiki push 等）
│   ├── rules/
│   │   ├── pm-workflow.md       #   全局工作流规范
│   │   ├── html-pipeline.md     #   HTML 产出物分步生成 + 美学硬底线
│   │   └── soul.md              #   个人偏好（gitignored）
│   ├── skills/                  # 18 个 Skill（每个 = SKILL.md + scripts/ + references/ + assets/ 三件套）
│   │   ├── {skill}/scripts/     #   可执行代码（Claude 不读源码，调用执行）
│   │   ├── {skill}/references/  #   .md 文档（按需 Read 加载到 context）
│   │   ├── {skill}/assets/      #   模板 / 字体 / 配置（被脚本读出来写进产物，不进 context）
│   │   └── _shared/             #   跨 skill 共享资产
│   │       └── claude-design/   #     美学 token · 工具类 · 内容规范
│   ├── chat-templates/          # Chat 轨模板 + context.md 九章模板
│   └── settings.json
├── scripts/                     # 公共脚本
│   ├── dashboard.py             #   聚合 hook / skill / 项目状态，输出 workspace-dashboard.md
│   ├── call_mcp.py              #   通用 MCP 调用（HTTP/stdio，0 token schema 开销）
│   ├── fetch_confluence.py      #   Confluence REST API 拉取
│   ├── fetch_figma.py           #   Figma REST API 拉取
│   ├── pull_meeting_notes.py    #   钉钉闪记纪要拉取
│   ├── md_to_confluence.py      #   Markdown → Confluence 同步
│   ├── impact-check.sh          #   场景变更影响面扫描
│   └── version-bump.sh          #   产出物升版
├── requirements.txt             # Python 依赖
├── package.json                 # Node 依赖
├── references/                  # 本地素材（gitignored）
│   └── competitors/
└── projects/                    # 工作项目（gitignored，按业务分类两层）
    ├── {业务线}/                # 你按公司业务分类（例：内容产品线、增长产品线）
    │   └── {项目}/              # 业务线下具体产品 / 模块
    │       ├── context.md       #   项目唯一真相源（九章）
    │       ├── scene-list.md    #   锁定的场景编号
    │       ├── .confluence.json #   Confluence 推送缓存
    │       ├── inputs/          #   原始素材
    │       ├── scripts/         #   项目生成脚本
    │       └── deliverables/    #   最终产出物
    └── {顶级项目}/              # 不归任何业务线的方案型项目 / 基建（结构同上，无业务线层）
```

> 业务线 / 项目命名按你的工作内容自定义。完整工作流约定见 `.claude/rules/pm-workflow.md`。

---

## 推荐模型

| 角色 | 模型 | 说明 |
|:-|:-|:-|
| 需求理解 · 架构决策 · 复杂推理 | Claude Opus 4.6 (1M) | 方案决策 + 全链路执行主力 |
| 日常编码施工 · 格式化输出 | Claude Sonnet 4.6 (1M) | Step B 填充可降级，省 ~46 % 成本 |
| 备选（Sonnet 用不起时） | GLM 5.1 · Kimi K2.5 | 性价比备选，context 按模型查表 |

---

## 自定义 Skill

用 `skill-creator` 创建自己的 Skill：

```
> 创建 skill：需求评审检查清单
```

Skill Creator 会引导完成：触发词定义 → 输入输出 → 执行步骤 → 自检清单 → 注册到 pipeline。详见 [`.claude/skills/skill-creator/SKILL.md`](.claude/skills/skill-creator/SKILL.md)。

---

## Contributing

欢迎提交 Issue 和 PR。

```bash
git clone git@github.com:YOUR_NAME/pm-workspace.git
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
