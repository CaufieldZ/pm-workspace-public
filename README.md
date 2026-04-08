<div align="center">

# 🏗️ PM Workspace

**AI-Native Product Management System**

从会议纪要到交互大图、PRD、行为规格 —— 15 个 Skill 覆盖产品经理全链路。

[![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)](LICENSE)
[![Skills](https://img.shields.io/badge/Skills-15-58a6ff?style=for-the-badge)](https://github.com/CaufieldZ/pm-workspace/tree/main/.claude/skills)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white)]()
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)]()
[![Built with Claude Code](https://img.shields.io/badge/Built_with-Claude_Code-bc8cff?style=for-the-badge&logo=anthropic&logoColor=white)](https://docs.anthropic.com/en/docs/claude-code)

</div>

---

## 🎯 解决什么问题

|                    | 之前                                 | 之后                                                                    |
| :----------------- | :----------------------------------- | :---------------------------------------------------------------------- |
| **输入**     | 会议纪要 / MRD / 竞品截图 / 口头需求 | 同左                                                                    |
| **过程**     | PM 手动画原型、写 PRD、反复对齐      | AI 按 Skill 自动产出，PM 审核微调                                       |
| **耗时**     | 3-5 天                               | 10 分钟 - 2 小时                                                        |
| **一致性**   | 每次结果不同，术语混乱               | 编号锁定 + 术语全局一致 + 自检拉通                                      |
| **下游交付** | PRD 扔给研发自己理解                 | 自动切分 behavior-spec / page-structure / test-cases，AI Agent 直接消费 |

---

## 🚀 Quick Start（5 分钟上手）

### 方式一：Chat 轨（零门槛）

1. 打开 Claude Chat / ChatGPT / 任意大模型
2. 文字产物（场景清单/竞品分析/PRD）：复制 `.claude/chat-templates/` 下对应 Prompt，替换占位符，发送
3. HTML 产物（交互大图/原型/架构图）：上传 3 个文件（`context.md` + `templates-index.md` + 模板 HTML）
4. 审核 → 对话迭代 → 完成

### 方式二：Claude Code 轨（完整体验）

```bash
# 1. Clone
git clone git@github.com:CaufieldZ/pm-workspace.git
cd pm-workspace

# 2. 安装依赖
pip install -r requirements.txt   # python-docx
npm install                       # docx (Node.js)

# 3. 激活防腐化 hook
git config core.hooksPath .githooks

# 4. 个性化（可选）
#    编辑 .claude/rules/soul.md 写入你的沟通偏好

# 5. 开始第一个项目
#    在 Claude Code 中输入：
#    > 新项目 my-first-project，需求是……
```

> **tip**: `soul.md` 已在 `.gitignore` 中，你的个人偏好不会推到远端。

---

## 📄 核心概念：context.md

context.md 是整个系统的枢纽——PM 与 AI 讨论需求后的结构化沉淀，所有产出物从它生长。改一个术语，下游全部产出物跟着改；加一个场景，依赖链自动识别波及范围。

| 身份                     | 说明                                                                           |
| :----------------------- | :----------------------------------------------------------------------------- |
| **永久记忆体**     | 讨论结论存这里。换 session、换模型、换环境都不丢                               |
| **跨环境协议**     | Chat 和 Claude Code 共享同一份 context.md，随时切换                            |
| **唯一真相源**     | 场景编号、术语表、方案决策、业务规则——下游产出物全部从这里读取               |
| **全生命周期记录** | 项目每次迭代更新，新对话不用重讲背景                                           |

```
原始输入（会议纪要/MRD/竞品截图/口述）
        ↓
与 AI 讨论提炼（Chat 或 Claude Code 均可）
        ↓
沉淀为 context.md（九章结构，模板见 .claude/chat-templates/）
        ↓
进入产出物链路
```

---

## 🔀 双轨工作流

同一套方法论，两种使用方式，按需选择或混用。

|                       | 💬 Chat 轨                | ⚡ Claude Code 轨                       |
| :-------------------- | :------------------------ | :-------------------------------------- |
| **上手成本**    | 0，打开 Chat 即用         | 需安装 Claude Code + 环境              |
| **产出质量**    | 初版 60-80 分，需对话迭代 | 初版 85-90 分，骨架脚本 + 规则兜底      |
| **HTML 产出物** | ⚠️ 有模板兜底但波动大   | ✅ 骨架脚本 + 组件库 + 验证规则三重兜底 |
| **可复现性**    | 每次结果不同              | 规则 + 模板 + 脚本保障一致性            |
| **适合谁**      | 快速出产物、不想折腾环境  | 追求高质量、愿意投入搭建                |

> **最佳实践：两轨混用。** AI 负责方案讨论 → 沉淀为 context.md → Claude Code 批量产出。

---

## 🏗️ 三层架构

```
Layer 1 · 全局规则（= 公司制度手册）
  CLAUDE.md / pm-workflow.md / soul.md
        ↓
Layer 2 · Skill 技能包（= 岗位操作手册）
  每种产出物一本：SKILL.md + references/（模板/组件/脚本）
        ↓
Layer 3 · 项目文件（= 具体项目资料）
  context.md / scene-list.md / deliverables/
```

执行优先级：Layer 2 Skill 硬规则 > Layer 1 全局规则 > 模型默认行为

---

## ⚙️ Skill 流水线

> 10 个 Pipeline Skill 按顺序执行，5 个独立/工具 Skill 随时调用。

```
1 scene-list ─→ 2 req-framework* ─→ 2.5 arch-diagrams* ─→ 3 interaction-map
                                                                   │
  ┌────────────────────────────────────────────────────────────────┘
  ▼
4 prototype* ─→ 5 prd ──┬─→ 6 behavior-spec* ─┐
                        ├─→ 6 page-structure* ─┼─→ 8 cross-check
                        └─→ 7 test-cases*      ─┘

                                                     * = optional
```

| #   | Skill                           | 产出说明                             | 格式      |
| :-- | :------------------------------ | :----------------------------------- | :-------- |
| 1   | **scene-list**            | 需求拆解为场景，编号锁定全局引用     | `.md`   |
| 2   | **requirement-framework** | 按模块整理需求条目（场景多时）       | `.html` |
| 2.5 | **architecture-diagrams** | 多系统/资金流转架构，多 Tab 文档     | `.html` |
| 3   | **interaction-map**       | 多端 UI 流 + 跨端数据流，Mockup 级   | `.html` |
| 4   | **prototype**             | 可点击高保真原型，数据驱动联动       | `.html` |
| 5   | **prd**                   | 横版左图右文 PRD，九章结构           | `.docx` |
| 6   | **behavior-spec**         | 研发 AI 消费：状态机 + 异常处理      | `.md`   |
| 6   | **page-structure**        | 设计/前端 AI 消费：组件树 + 数据绑定 | `.md`   |
| 7   | **test-cases**            | QA AI 消费：Pairwise 建模 + 四类全覆盖 | `.md`   |
| 8   | **cross-check**           | 编号/术语/字段一致性拉通验证         | 终端输出  |

**独立 & 工具类**

| Skill                         | 说明                                             |
| :---------------------------- | :----------------------------------------------- |
| **competitor-analysis** | 竞品调研，三角对比 + 可借鉴点提取                |
| **ppt**                 | 方案/SOP → HTML 多 Tab 演示文档 + 配套口播稿    |
| **docx**                | 读取/编辑/接受修订已有 Word 文档                 |
| **workspace-audit**     | 6 类全局诊断（文件/数值/依赖/规则/Token/产出物） |
| **skill-creator**       | 创建新 Skill，自动生成 frontmatter + 注册        |

---

## 🤖 AI 可消费的下游文档

传统 PM 工作流到 PRD 就结束了。这套系统多走一步 —— **把 PRD 切分为 AI Agent 可直接消费的结构化文档**。

```
         ┌─→ behavior-spec  ─→ Dev AI    (Cursor / Copilot / Claude Code)
         │
PRD ─────┼─→ page-structure ─→ Design AI (Frontend AI)
         │
         └─→ test-cases     ─→ QA AI     (Automation)
```

| 文档               | 消费方             | 价值                                               |
| :----------------- | :----------------- | :------------------------------------------------- |
| `behavior-spec`  | 研发 AI            | "用户做 X → 系统响应 Y" 完整规格，无需读 PRD 全文 |
| `page-structure` | 设计 AI / 前端 AI  | 组件树 + 数据绑定 + 交互状态，无需看原型截图猜布局 |
| `test-cases`     | QA AI / 自动化测试 | 边界值 + 异常场景 + 合规校验，开箱即用             |

---

## 🛡️ 工程保障

| 机制 | 说明 |
| :--- | :--- |
| **防腐化 hook** | `.githooks/pre-commit` — Skill/规则变更时自动跑 `audit.sh`（完整性+依赖+规则冲突），不通过拦截 commit |
| **自检反压** | 每个 Skill 自带 checklist，不通过最多自动修复 2 次，仍失败停下报告，禁止静默跳过 |
| **impact-check** | `bash scripts/impact-check.sh <项目名>` 或 `/变更影响 <项目名>` — 改完 scene-list 后一键识别哪些 deliverable 需同步更新 |
| **workspace-audit** | 双阶段审计（脚本硬检查 + 模型软检查），11 类全局诊断：文件完整性、数值一致、依赖链路、规则冲突、Token 预算、产出物一致、SKILL_TABLE 同步、深度规则矛盾、安全扫描、优化建议、综合评估 |
| **HTML 铁律** | >200 行必须脚本生成（骨架 → 填充 → 自检），禁止 Write 直写 |
| **变更级联** | 改了 context.md → 依赖链自动扫描波及范围 → 按 pipeline 顺序升版下游产出物 → cross-check 拉通验证。PM 不用自己记哪些文档要同步改 |
| **编号锁定** | 场景编号确认后不可改动，新增只追加 |
| **context.md 只读** | 方案决策由 PM 在 Chat 中与 AI 讨论确定，本地模型不自行修改 |

---

## 📁 目录结构

```
pm-workspace/
├── CLAUDE.md                  # Claude Code 项目指令入口
├── .githooks/pre-commit       # 防腐化 hook
├── requirements.txt           # Python 依赖（python-docx）
├── package.json               # Node.js 依赖（docx）
├── scripts/                   # 公共验证脚本
│   ├── check_html.sh          #   HTML 产出物自检
│   ├── check_prd.sh           #   PRD docx 自检
│   ├── fill_utils.py          #   fill 脚本公共模块
│   └── impact-check.sh        #   场景变更影响面扫描
├── .claude/
│   ├── rules/
│   │   ├── pm-workflow.md     #   全局工作流规范
│   │   └── soul.md            #   个人偏好（gitignored）
│   ├── skills/                #   15 个 Skill（各含 SKILL.md + references/）
│   └── chat-templates/        #   Chat 轨模板 + context.md 九章模板
├── references/                # 本地素材（gitignored）
│   └── competitors/           # 竞品素材
└── projects/                  # 工作项目（gitignored）
    └── {项目名}/
        ├── context.md         # 项目唯一真相源
        ├── scene-list.md      # 锁定的场景编号
        ├── inputs/            # 原始素材
        ├── scripts/           # 项目生成脚本
        └── deliverables/      # 最终产出物
```

---

## 🧠 推荐模型

| 角色                                     | 模型                   | 说明                            |
| :--------------------------------------- | :--------------------- | :------------------------------ |
| **需求理解 / 架构决策 / 复杂推理** | Claude Opus 4.6 (1M)   | 方案决策 + 全链路执行主力       |
| **日常编码施工 / 格式化输出**      | Claude Sonnet 4.6 (1M) | Step B 填充可降级，省 ~46% 成本 |
| **备选（Sonnet 用不起时）**        | GLM 5.1 / Kimi K2.5    | 性价比备选，context 按模型查表  |

---

## 🧩 自定义 Skill

用 `skill-creator` 可以创建自己的 Skill：

```
> 创建 skill：需求评审检查清单
```

Skill Creator 会引导你完成：触发词定义 → 输入输出 → 执行步骤 → 自检清单 → 注册到 pipeline。

详见 [`.claude/skills/skill-creator/SKILL.md`](.claude/skills/skill-creator/SKILL.md)。

---

## 🤝 Contributing

欢迎提交 Issue 和 PR。

```bash
# 1. Fork & Clone
git clone git@github.com:YOUR_NAME/pm-workspace.git
cd pm-workspace

# 2. 激活防腐化 hook
git config core.hooksPath .githooks

# 3. 创建 feature branch
git checkout -b feat/your-feature

# 4. 修改后 commit（pre-commit hook 自动验证）
git add .
git commit -m "feat: your change"

# 5. 提交 PR
```

---

## 📄 License

[Apache License 2.0](LICENSE)

---

<div align="center">

**Built with**

[![Claude Code](https://img.shields.io/badge/Claude_Code-000?style=flat-square&logo=anthropic&logoColor=white)](https://docs.anthropic.com/en/docs/claude-code)
[![Python](https://img.shields.io/badge/Python-3776ab?style=flat-square&logo=python&logoColor=white)]()
[![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat-square&logo=nodedotjs&logoColor=white)]()
[![HTML/CSS/JS](https://img.shields.io/badge/HTML%2FCSS%2FJS-e34f26?style=flat-square&logo=html5&logoColor=white)]()

</div>
