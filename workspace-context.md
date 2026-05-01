<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PM-WORKSPACE 仓库全貌（给 Claude Opus 的系统背景）

> 导出时间：2026-04-26 | 目的：供 Opus 了解仓库结构、Skill 体系、工作流规则，用于诊断或协作

---

## 一、仓库定位

这是一个 **PM 协作工作台**，用 Claude Code CLI（VSCode 插件）驱动产品经理日常工作流：
- 从需求素材 → 场景清单 → 交互大图 → 原型 → PRD → 自检，全链路自动化
- 产出物为 HTML（交互大图/原型）和 .docx（PRD），通过 Python 脚本生成
- 每个「项目」独立目录，有一套固定的文件结构
- **projects/ 已 gitignore**，GitHub 只存系统框架（skills / rules / references）

---

## 二、目录树

```
pm-workspace/
├── CLAUDE.md                  ← Claude Code 项目指令入口
├── README.md                  ← 系统介绍 + 系统级 context
├── workspace-context.md       ← 本文件：给 Opus 的系统全貌
├── package.json               ← docx 生成依赖（docx/jszip/pako）
├── .githooks/
│   └── pre-commit             ← 防腐化 hook（git commit 时自动审计）
├── .claude/
│   ├── rules/
│   │   ├── pm-workflow.md     ← 全局工作流规范
│   │   └── soul.md            ← 个人偏好
│   ├── skills/                ← 19 个标准化 Skill（每个 = SKILL.md + scripts/ + references/ + assets/ 三件套）
│   ├── hooks/
│   │   ├── pre-compact.sh     ← Claude Code runtime hook（compact 前注入 session-state）
│   │   └── post-cjk-punct-check.sh ← PostToolUse hook（Write/Edit 后扫 CJK 旁半角标点）
│   ├── chat-templates/        ← Chat 轨模板 + context.md 九章模板
│   ├── session-state.md       ← 当前 session 进度快照（gitignored，Claude 维护）
│   └── settings.json
├── references/                ← 本地素材（gitignored）
│   └── competitors/           ← 竞品素材（Binance/OKX/Gate/Bybit）
└── projects/                  ← 工作项目（gitignored）
    └── {项目名}/
        ├── context.md         ← Chat Opus 输出，本地模型只读（九章：静态1-6 当前真相 / 动态7,9 演进记录 / 混合8）
        ├── scene-list.md
        ├── inputs/
        ├── scripts/
        └── deliverables/
            └── archive/
```

---

## 三、核心工作流（三层链路）

### 简单链路

不满足复杂条件时走此链路：纯功能点直接出 Markdown PRD；单页面直接出原型；纯文案直接出文档。

### 复杂链路（默认）

满足以下任一条件即走复杂：≥2 端/角色、≥5 场景且有跨场景跳转、含数据同步/状态流转/多角色协作。
按下方 Pipeline 步骤速查表的顺序依次执行，标注「可选」的步骤可跳过，每步等用户确认。

### 超复杂链路（多系统/资金流转/架构）

在复杂链路基础上，于需求框架之后插入架构图集步骤。

> 具体步骤顺序、依赖关系见下方自动生成的 Pipeline 步骤速查表。
> 场景编号确定后全局锁定，所有产出物复用。

| 顺序 | Skill | 输出格式 | 必须依赖 | 可选输入 |
|------|-------|---------|---------|---------|
| 1 | scene-list | .md | [] | [context.md] |
| 2 | requirement-framework | .html | [scene-list] | [context.md] |
| 2.5 | architecture-diagrams | .html | [scene-list] | [context.md] |
| 3 | interaction-map | .html | [scene-list] | [context.md, requirement-framework, architecture-diagrams] |
| 4 | prototype | .html | [scene-list] | [interaction-map] |
| 5 | prd | .docx | [scene-list] | [interaction-map, prototype] |
| 6 | behavior-spec | .md | [scene-list, prd] | [interaction-map, prototype] |
| 6 | page-structure | .md | [scene-list, prd] | [interaction-map, prototype] |
| 7 | test-cases | .md | [scene-list, prd] | [behavior-spec] |
| 8 | cross-check | 对话内 | [scene-list] | [interaction-map, prototype, prd, behavior-spec, page-structure, test-cases] |

---

## 四、Skill 体系（19 个）

每个 Skill 按 Anthropic Progressive Disclosure 规范的三件套组织：
- `scripts/` — 可执行代码（.py / .sh / .js library），Claude 不读源码，调用执行
- `references/` — .md 文档，Claude 按 SKILL.md Step 1 声明按需 Read 到 context
- `assets/` — 模板（HTML/CSS/JS）/ 字体 / 运行时配置 JSON，被脚本读出来写进产物，不进 context

| Skill | 类型 | 输出格式 | 前缀 | 必须依赖 | 被谁消费 |
|-------|------|---------|------|---------|---------|
| architecture-diagrams | pipeline | .html | arch- | [scene-list] | [interaction-map] |
| behavior-spec | pipeline | .md | bspec- | [scene-list, prd] | [test-cases, cross-check] |
| competitor-analysis | standalone | .md | comp- | [] | [] |
| cross-check | pipeline | 对话内 | — | [scene-list] | [] |
| flowchart | standalone | .html | flow- | [] | [] |
| interaction-map | pipeline | .html | imap- | [scene-list] | [prototype, prd] |
| page-structure | pipeline | .md | pspec- | [scene-list, prd] | [cross-check] |
| ppt | standalone | .html | ppt- | [] | [] |
| prd | pipeline | .docx | prd- | [scene-list] | [behavior-spec, page-structure, test-cases, cross-check] |
| prototype | pipeline | .html | proto- | [scene-list] | [prd] |
| requirement-framework | pipeline | .html | rf- | [scene-list] | [interaction-map] |
| scene-list | pipeline | .md | scene- | [] | [requirement-framework, architecture-diagrams, interaction-map, prototype, prd, behavior-spec, page-structure, test-cases, cross-check] |
| intel-collector | tool | 目录 | — | [] | [competitor-analysis] |
| workspace-audit | tool | 对话内 | — | [] | [] |
| pdf-tools | tool | 原文件同目录 | — | [] | [] |
| skill-creator | tool | 新目录 | — | [] | [] |
| data-report | standalone | .md + .png | report- | [] | [] |
| test-cases | pipeline | .md | tc- | [scene-list, prd] | [cross-check] |
| meeting-autopilot | tool | 对话内 | — | [] | [] |

> **`_shared/claude-design/`**：跨 skill 共享资产目录（token / 工具类 / 内容规范），不是 skill，不参与 pipeline，文件见 [`.claude/skills/_shared/README.md`](.claude/skills/_shared/README.md)。被上述 10 个 skill 引用。

### Skill 执行模式（通用）

所有 HTML 产出物 > 200 行的 Skill 统一走三步流程（详见 `pm-workflow.md`「HTML 分步生成通用规则」）：
- **Step A**：生成 Python 骨架脚本（从 assets/ 读取模板 + 拼接）——**不读组件模板**
- **Step B**：填充脚本替换占位符——此时才读 assets/templates.html + 按需读 components
- **Step C**：自检清单验证（通用条目在 pm-workflow.md，专项条目在各 SKILL.md）

---

## 五、关键技术约束

| 约束 | 说明 |
|------|------|
| HTML > 200行 | 禁止 Write 直接写，必须 Python 脚本生成 |
| 上下文保护 | HTML 禁止全量 Read，只能 grep 局部提取 |
| 脚本复用 | scripts/ 下同类脚本复用修改，版本号递增；公共工具在根 scripts/ |
| bash 优先 | 提取/替换/复制/验证一律用 bash，不手写内容 |
| 场景编号不可改 | 确认后锁定，新增只追加 |
| 术语全局一致 | 同一概念跨文档必须用同一命名 |
| 命名规范 | `{类型前缀}-{项目简称}-v{N}.{扩展名}` |
| 版本管理 | 升版归档到 deliverables/archive/，根目录只放最新 |
| 禁止并行代理 | 所有任务串行执行，无 Background Agent |
| 自检反压 | 自检不通过最多自动修复 2 次，仍失败则停下报告用户，禁止静默跳过 |
| 决策缺口处理 | 缺少必需决策信息时停下来提问给 A/B/C 选项，禁止自行假设后继续 |
| 防腐化 hook | `.githooks/pre-commit` 检测 Skill/规则文件变更时自动跑 `audit.sh 1,2,3,4,7`（文件完整性 + 数值一致 + 依赖链路 + 规则冲突 + SKILL_TABLE 一致性），不通过拦截 commit。激活：`git config core.hooksPath .githooks` |
| Session 状态保活 | `.claude/hooks/pre-compact.sh` 在上下文压缩前自动注入 `.claude/session-state.md`（项目名/Skill/Step/已填 Scene/待办）到 compact 摘要。Claude 在 Skill Step 边界主动 Write 更新此文件。防 compact 后丢失进度 |
| CJK 标点护栏 | `.claude/hooks/post-cjk-punct-check.sh` + `scripts/check_cjk_punct.py` 在每次 Write/Edit md/html/含中文 py/js 后自动扫中文字旁的半角 `:,;()`，stderr 报行号。看到 warning 立刻改成全角，防产出物漏转换被嘲讽像 AI 写的 |

> 执行优先级：全局规则（CLAUDE.md / pm-workflow）< Skill 硬规则

---

> 版本记录
> v8: 2026-04-05 降本增效优化：删除 DEPRECATED cheatsheet(-19K tok)、CLAUDE.md 瘦身(-267 tok)、自检脚本化(scripts/check_html.sh + check_prd.sh)、fill_utils.py 公共模块、prd-example.md 精简(-3.1K tok)、prototype 按需章节加载
> v9: 2026-04-05 Token 优化第二轮：删除 §六配置文件关系表 + §七已知问题备忘（全部已修复），精简版本记录
> v10: 2026-04-05 模型分工统一：Claude Opus 4.6（决策/推理）→ Claude Sonnet 4.6（施工/格式化）→ GLM 5.1 / Kimi K2.5（备选）
> v11: 2026-04-05 防腐化 hook：.githooks/pre-commit + audit.sh 退出码支持
> v12: 2026-04-06 Token 降本 + 工程健壮性：pm-workflow 原地压缩(-24%)、imap quickref 速查表(-48%)、audit.sh 去硬编码改动态提取、commands 参数防御、pre-commit 加规则冲突检查、CLAUDE.md 标注分界原则
> v13: 2026-04-07 workspace-audit 诊断修复：§三字体规范拆分正文栈+等宽栈解决矛盾、PPT JetBrains Mono 白名单、分级表 200K→256K、arch body 字体补齐、优先级表述修正
> v14: 2026-04-08 全局诊断修复 11 项：XSD schemas 移出 git(1MB)、prototype.css CJK 优先、imap optional_inputs+arch、arch/docx 自检清单、imap CSS/JS 引用说明、requirements.txt、cross-check optional_inputs 补全、竞品字体加注、impact-check.sh 新工具
> v15: 2026-04-08 能力升级：test-cases Pairwise 建模+覆盖密度+依赖改为 prd、PRD 边写边审+迭代模式(冲突检测+存量数据)+埋点模板重写、逻辑拼图(方案变更自动推演)、一键开项目+会议纪要自动处理、/变更影响 command
> v16: 2026-04-08 防蒸馏防护：AI-TRAINING-RESTRICTION.md+NOTICE+ai.txt 被动声明层、canary token 注入(38文件)、sync_public.sh 水印注入+保护验证、degrade.sh 离职降级工具(~/.claude/scripts/)
> v17: 2026-04-11 产出物视觉质量提升：PPT 去 AI 味(gold-snippets 组件化+节奏编排模式7)、interaction-map 易读性(flow-note WCAG AA+clip-path 箭头+ann-tag/arrow-text 放大)、PRD Step 4 原型截图自动插入(Playwright)
> v18: 2026-04-12 全局字体栈换代：Noto Sans SC+DM Sans → HarmonyOS Sans SC+Plus Jakarta Sans（减少 AI 味），覆盖 pm-workflow/4 CSS/5 chat-templates/4 SKILL.md/audit.sh 共 19 文件；Skill 过时内容修复(test-cases 依赖描述、competitor-analysis pptxgenjs、workspace-audit 类别数)
> v19: 2026-04-12 requirements.txt 补齐 matplotlib+numpy（data-report chart_template.py 依赖）；Skill 计数修正 15→18；README 依赖注释同步
> v20: 2026-04-15 脚本归位：check_prd.sh/intel-cron.sh/capture.py 移入各自 Skill 的 references/；confluence_sync.py 移入 data-report/references/；新增 sync-holidays.py；Skill 计数修正 18→19；references 改为按 SKILL.md Step 1 按需加载
> v21: 2026-04-18 Session 状态保活：新增 `.claude/hooks/pre-compact.sh` + `.claude/session-state.md` 机制，PreCompact hook 自动注入进度快照到 compact 摘要，Claude 在 Step 边界主动 Write 更新；CLAUDE.md 【compact 指引】从被动规则改为主动维护；README/workspace-context 同步工程保障一栏
> v22: 2026-04-19 新增 flowchart skill：AntV X6 + dagre 渲染分支流程图/泳道图，浅色白板嵌入深色画布（参照飞书风），内置边不穿节点自检；独立产出型（standalone，可被 imap/prd/ppt 截图消费）；节点类型 terminal/process/decision/success/fail；同行相邻边自动用 normal router 避免 manhattan 降级 orth 绕圈；Skill 计数 19→20
> v23: 2026-04-23 三项升级：(1) PRD 1.3「核心变更」→「变更范围」改名 + 语义修正（基线 = 当前线上版本，非 PRD 版本间 diff；PM 从讨论流水收敛成线上→终稿 delta，不直搬），pm-workflow/chat-templates/prd/imap/req-framework/cross-check 全链路同步；cross-check 新增 §2.8 变更范围一致性校验；(2) PRD 无截图 Scene 降级模式：新增 `insert_scene_blocks` + `remove_table` helpers，CMS / 纯后台 / 本期不改 UI 的 Scene 走 body 级 H3 + numbered list，取代空占位的 2 列 scene_table（SKILL.md 硬规则 #9）；(3) 中文标点护栏：新增 PostToolUse hook `post-cjk-punct-check.sh` + `scripts/check_cjk_punct.py`，Write/Edit 后自动扫 md/html/含中文 py/js 的半角标点（`:,;()`）并 stderr 报行号，防产出物漏全角转换被嘲讽像 AI 写的
> v24: 2026-04-23 Token 降本：删除 8 个冗余 command（仅保留 probe-quick），新增 fetch_figma.py 脚本直调 Figma REST API 替代 MCP server（省 ~15K token/session），README 补全 scripts/ 目录说明
> v25: 2026-04-26 data-report 端到端改造：新增 gen_weekly_all.py（一条命令跑全流程）+ fetch_market_context.py（CoinGecko/FRED 行情采集）；chart_template.py 换白底商务风（参照 Google Sheets/飞书）+ 隔周灰底色带；parse_weekly_csvs.py 新增 --daily 日粒度输出；confluence_sync.py 升级 sync_full() API（说明列自动填充/洞察XHTML提取/week_periods自动计算/附件multipart上传）；修复 4 个脚本 bug（CSV%后缀/千分位逗号/全角括号normalize/附件同名400）；Confluence 表格加 4 周日期列+涨绿跌红色+单箭头趋势列
> v26: 2026-04-26 Skill 目录按 Anthropic Progressive Disclosure 规范化：21 个 skill 全部拆为 SKILL.md + scripts/（可执行 .py/.sh）+ references/（.md 文档）+ assets/（HTML/CSS/JS 模板 / 字体 / 运行时 JSON）三件套；删除 docx skill（从未使用，Skill 计数 20→19）；intel-collector auth/url-registry.json 移入 assets/；meeting-autopilot mcp-config.json 移入 assets/；CLAUDE.md / pm-workflow / hooks / settings 路径约定全量同步；tag pre-skill-restructure 是 rollback 锚点
> v27: 2026-04-28 Confluence 推送 pageId 缓存：push_to_confluence_base.py 自动读写 `projects/{项目}/.confluence.json`（含 prd_page_id / space / parent_id / title），首次推送写入，后续零参数推送，新 session 不再问 pageId；多 PRD 项目用 pages map 按 docx 文件名匹配（直播间 V2.8/V3.0 自动分发）；--space 默认 jituankejizhongxin；删除遗留 scripts/confluence-pages.json（无人读取）；回填 5 个活跃项目配置（proj-activity-center / proj-community / proj-community-leaderboard / proj-live-streaming / proj-liquidity）
