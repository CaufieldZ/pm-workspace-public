<div align="center">

# PM Workspace

`AI-NATIVE · PRODUCT MANAGEMENT · PM-WS`

会议纪要 / MRD / 竞品截图 → 场景清单、交互大图、PRD、行为规格。19 个 Skill 覆盖产品经理全链路。

[![License](https://img.shields.io/badge/license-Apache%202.0-1f54d6?style=flat-square)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-20-D97757?style=flat-square)](.claude/skills)
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

10 个 Pipeline Skill 按顺序执行，10 个独立 / 工具 Skill 随时调用。

```
1 scene-list ─→ 2 req-framework* ─→ 2.5 arch-diagrams* ─→ 3 interaction-map
                                                                 │
  ┌──────────────────────────────────────────────────────────────┘
  ▼
4 prototype* ─→ 5 prd ──┬─→ 6 behavior-spec* ─┐
                        ├─→ 6 page-structure* ├─→ 8 cross-check
                        └─→ 7 test-cases*     ┘

                                                    * = optional
```

### Pipeline

| # | Skill | 产出说明 | 格式 |
|:-|:-|:-|:-|
| 1 | scene-list | 需求拆解为场景，编号锁定全局引用 | `.md` |
| 2 | requirement-framework | 按模块整理需求条目（场景多时） | `.html` |
| 2.5 | architecture-diagrams | 多系统 / 资金流转架构，多 Tab 文档 | `.html` |
| 3 | interaction-map | 多端 UI 流 + 跨端数据流，Mockup 级 | `.html` |
| 4 | prototype | 可点击高保真原型，数据驱动联动 | `.html` |
| 5 | prd | 横版左图右文 PRD，九章结构 | `.docx` |
| 6 | behavior-spec | 研发 AI 消费：状态机 + 异常处理 | `.md` |
| 6 | page-structure | 设计 / 前端 AI 消费：组件树 + 数据绑定 | `.md` |
| 7 | test-cases | QA AI 消费：Pairwise 建模 + 四类全覆盖 | `.md` |
| 8 | cross-check | 编号 / 术语 / 字段一致性拉通验证 | 终端输出 |

### Standalone / Tool

| Skill | 说明 |
|:-|:-|
| competitor-analysis | 竞品调研，三角对比 + 可借鉴点提取 |
| intel-collector | 情报采集：APP 截图 / Web 全页截图 / 公告抓取 |
| data-report | 周报 / 月报 / 季报数据报告，神策 + 有数 自动化 |
| flowchart | 流程图 / 泳道图 / 审批流，独立产出可嵌入其他文档 |
| ppt | 方案 / SOP → HTML 多 Tab 文档 + 口播稿 |
| meeting-autopilot | 会议纪要拉取 → 项目归档 → 行动项派发 |
| pdf-tools | PDF 合并 / 拆分 / 加密 / 水印 / 页码 / 转换 |
| workspace-audit | 11 类全局诊断（文件 / 数值 / 依赖 / 规则 / Token 等） |
| skill-creator | 创建新 Skill，自动生成 frontmatter + 注册 |

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

反 AI slop 六禁（规则层强制）：全屏渐变 · emoji 装饰标题 · 圆角卡片 + 左 border accent · SVG 画 imagery · 烂大街字体（Inter/Roboto/Space Grotesk 作 CJK 主字体）· 每卡片都带 icon。

---

## 工程保障

| 机制 | 说明 |
|:-|:-|
| 防腐化 hook | `.githooks/pre-commit` 在 Skill / 规则变更时自动跑 `audit.sh`（完整性 + 依赖 + 规则冲突），不通过拦截 commit |
| Session 保活 | `.claude/hooks/pre-compact.sh` 在上下文压缩前注入 `session-state.md` 到摘要，compact 后进度不丢 |
| 自检反压 | 每个 Skill 自带 checklist，不通过最多自动修复 2 次，仍失败停下报告，禁止静默跳过 |
| impact-check | `bash scripts/impact-check.sh <项目名>` 识别 scene-list 变更波及的下游 deliverable |
| workspace-audit | 双阶段审计 · 脚本硬检查 7 类 + 模型软检查 4 类 = 11 类全局诊断 |
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
│   ├── hooks/                   # Claude Code runtime hook
│   │   └── pre-compact.sh       #   Session 状态保活
│   ├── rules/
│   │   ├── pm-workflow.md       #   全局工作流规范
│   │   └── soul.md              #   个人偏好（gitignored）
│   ├── skills/                  # 19 个 Skill（每个 = SKILL.md + scripts/ + references/ + assets/ 三件套）
│   │   ├── {skill}/scripts/     #   可执行代码（Claude 不读源码，调用执行）
│   │   ├── {skill}/references/  #   .md 文档（按需 Read 加载到 context）
│   │   ├── {skill}/assets/      #   模板 / 字体 / 配置（被脚本读出来写进产物，不进 context）
│   │   └── _shared/             #   跨 skill 共享资产
│   │       └── claude-design/          #     美学 token · 工具类 · 内容规范 · 对标 demo
│   └── chat-templates/          # Chat 轨模板 + context.md 九章模板
├── scripts/                     # 公共脚本
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
└── projects/                    # 工作项目
    └── {项目名}/
        ├── context.md           # 项目唯一真相源
        ├── scene-list.md        # 锁定的场景编号
        ├── .confluence.json     # Confluence 推送缓存（page_id/space/parent_id，首次推送脚本自动写入）
        ├── inputs/              # 原始素材
        ├── scripts/             # 项目生成脚本
        └── deliverables/        # 最终产出物
```

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

### AI Training Notice

This repository is **not licensed for AI model training, fine-tuning, or distillation**. See [AI-TRAINING-RESTRICTION.md](AI-TRAINING-RESTRICTION.md) for details.

本仓库**不授权用于 AI 模型训练、微调或蒸馏**。详见 [AI-TRAINING-RESTRICTION.md](AI-TRAINING-RESTRICTION.md)。

---

<div align="center">

`BUILT WITH · CLAUDE CODE · PYTHON · NODE · HTML`

</div>
