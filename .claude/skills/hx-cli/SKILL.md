---
name: hx-cli
description: >-
  Use whenever the user mentions 火效 / hx / hx-cli / huoxiao / HX / 内部项目管理系统, or asks about internal HX project-management, work-item, task, requirement, bug, sprint, staff, or progress workflows — the product-manager subset (项目 / 人员 / 需求任务 / 个人面板 / 分支进展 / 只读提测单查询；不含代码仓库写操作、TAG、MR、提测单创建、安全提测等研发发布链路). Trigger on system terms: 火效, hx, hx-cli, huoxiao, HX, 内部项目管理系统. Trigger on work-item terms: 任务, 我的任务, 手头的任务, 在做的任务, 需求, 研发任务, 后端任务, 事务任务, Bug, 缺陷, 工单, 工作项, ticket. Trigger on progress/status terms: 我在做什么, 最近在做什么, 有哪些待办, 任务状态, 任务进展, 做到哪一步了, in-progress, 待处理, 待修复, 研发中. Trigger on project/staff terms: 项目, 项目成员, 迭代, sprint, 版本, 负责人, owner, manager, 人员, 同事, staff, staff id. Trigger on checker (read-only) terms: 查提测单状态, 提测了没, 提测单查询. Trigger on current-branch progress terms: 当前分支, develop_H00000, 分支进展. Use this skill for Chinese or English requests such as "我手头的任务", "what am I working on", "list my hx work items", "查 H403914 子任务", "创建一个需求", "把这条需求标为已完成", "更新任务进度和风险", or "看下当前分支做到哪一步了".
type: standalone
binaries:
- hx-cli-linux
- hx-cli-macos
---

# hx-cli — 火效（hx）项目管理 / 任务 / 进展助手（PM 版）

适用于产品经理在公司内部 **火效 / hx / huoxiao** 系统里的日常操作：查看和管理 **任务 / 需求 / 工作项 / Bug / 研发任务 / 后端任务 / 事务任务**，查询 **项目 / 迭代 / 成员 / 人员**，跟进 **个人面板与当前分支任务进展**，只读查询 **提测单状态**。

通过随 skill 发布的 `hx-cli-macos` / `hx-cli-linux` 二进制调用火效（hx）后端接口，查询 / 创建 / 流转项目、工作项（任务、需求、Bug、研发任务、后端任务、事务任务）、人员。代码仓库写操作、TAG、MR、提测单创建、安全提测等研发发布链路不在本 skill 范围（CLI 二进制仍可裸调，但不提供文档指引）。

## 触发与定位

| 能力 | 说明 | 用户示例 | 详细说明 |
|------|------|----------|----------|
| AIHUB token 与用户 | 查看 AIHUB token 状态、当前用户、PM staff id | "确认 token 是否可用"、"我的 staff id 是多少" | `user.md` |
| 项目与人员 | 查询项目、成员、项目工作类型、标准类型目录、人员/同事 | "查项目成员"、"列项目工作类型"、"X 同事 staff id" | `project.md` |
| 工作项（任务/需求/Bug） | 查看详情、查询父子任务、列出/创建/流转/删除需求、研发任务、后端任务、事务任务、Bug；更新进度百分比、风险状态、进度详情、风险描述、变更描述 | "看看 H403914 详情和子任务"、"我在做什么"、"创建一个需求和后端任务"、"把这条需求标为已完成"、"更新一下任务进度和风险" | `work.md` |
| 个人面板 / 我的任务概览 | 复刻火效个人面板：统计待处理、进行中、已完成、已逾期任务；按个人面板筛选列任务；查看最近任务动态 | "看看我手头的任务"、"我现在有哪些逾期"、"我最近改了哪些任务"、"帮我快速过一下个人面板" | `personal-panel.md` |
| 当前分支任务进展（只读） | 从当前 Git 分支的 H 号查当前任务、上级任务/需求，结合代码管理 V2 只读证据判断做到哪一步 | "这个任务现在什么状态"、"看下当前分支进展"、"做到哪一步了" | `task-progress.md` |
| 提测单（只读查询） | 查询提测单状态、列出某任务的提测单 | "查提测单状态"、"这个任务提测了没" | `checker.md` |
| 排障 | 处理 AIHUB token 失效、权限、500、参数错误 | "为什么 work create 500"、"token 失效怎么办" | `troubleshooting.md` |

## 改脚本前 30 秒

> 本 skill 主接口是二进制（见 §硬规则「二进制位置」）；`scripts/` 是工区自建的**只读**封装，非 zip 原生。

**scripts/（改前看调用方）**：
- `hx_client.py` — 火效 API 只读 connector；根仓 `scripts/sync_hx_status.py` import 它
- `hx_task_progress.py` / `hx_panel.py` — 当前分支进展 / 个人面板只读封装

**改前必读**：重装 / 重解压本 skill 前先备份 `scripts/`，否则被覆盖。只抽只读链——写操作（create / transition work）走二进制 + §硬规则后果确认协议逐步人工确认，不脚本化。

## 使用哪个子文档

| 用户意图 | 必读文档 |
|----------|----------|
| AIHUB token 状态 / 当前用户 / 我的 staff id | `user.md` |
| 找项目 id、查成员、查同事 staff id、查工作类型、标准 leaf 类型 | `project.md` |
| 快速了解我手头的任务、个人面板统计、待处理/进行中/逾期、最近动态 | `personal-panel.md`，需要修改时再读 `work.md` |
| 创建需求/研发任务/后端任务/Bug、流转状态、通用 work 查询、更新进度/风险/工时 | `work.md` |
| 用户在代码仓库里问“这个任务状态/进展/做到哪一步了”，或当前分支类似 `develop_H00000` | `task-progress.md`，必要时再读 `work.md` |
| 查询提测单状态（只读） | `checker.md` |
| 命令失败、后端 500、token 失效 | `troubleshooting.md` |

先读对应子文档确认 ID 类型、参数和接口顺序，再执行命令。

---

## 硬规则（FAIL 即拦）

### 二进制位置（重要）

**二进制就在本 skill 的目录里**，与本 SKILL.md 同级。skill 加载时系统已经告诉你这个目录的绝对路径（在 skill header 的 "Base directory for this skill" 一行）。

根据运行平台选择制品：

| 平台 | 制品 |
|------|------|
| macOS / Darwin | `hx-cli-macos`（universal binary，包含 arm64 + x86_64） |
| Linux amd64 | `hx-cli-linux` |

调用时统一用 **skill 目录里的对应二进制**，不要去 `$PATH` 里找：

```bash
"<SKILL_DIR>/hx-cli-macos" <command>   # macOS
"<SKILL_DIR>/hx-cli-linux" <command>   # Linux amd64
```

其中 `<SKILL_DIR>` 就是 skill header 给出的 base directory（例如 `/Users/<user>/.config/opencode/skills/hx-cli`、或者别的 agent 配置下的 `/.../skills/hx-cli`）。**不要硬编码任何用户名或绝对路径**——每次都从 skill header 读取实际值后拼接。

为了文档清爽，下文的所有命令示例统一写成：

```bash
hx-cli <command>
```

执行时请把 `hx-cli` 替换为当前平台对应的 skill 制品。例如 skill 目录是 `~/.config/opencode/skills/hx-cli/` 且运行在 macOS，就执行 `"~/.config/opencode/skills/hx-cli/hx-cli-macos" status`。

> ⚠️ 不要先 `which hx-cli`、不要 `hx-cli --help`、不要 `command -v hx-cli`。直接用上面的绝对路径调用。`which` / 全局 PATH 多半找不到，浪费一轮工具调用。

### 认证与安全

- hx-cli 通过 AIHUB 代理访问 HX：所有请求发到 `https://INTERNAL_URL_REDACTED 后接原 HX API 路径，例如 `/api/v1/user/users/current`。
- 火效 Web 页面基础地址固定为 `https://INTERNAL_URL_REDACTED Web base 生成；AIHUB connector 地址只用于 CLI/API 调用，不能拿来当用户可点击页面链接。
- token 来自环境变量 `AIHUB_TOKEN`，命令会自动带 `Authorization: Bearer <token>`。`source .env` 设的是 shell 变量、不导出到二进制子进程，须 `set -a; source .env; set +a` 强制导出，否则 `status` 报 missing AIHUB_TOKEN。
- 所有命令都支持全局 `--token <token>`，仅对当前命令生效，并优先于 `AIHUB_TOKEN`。
- token 可用但 session 过期时（`auth check` 报 40102 Session 已过期），让用户打开 TOTP APP 提供 6 位 GA 验证码，然后执行 `hx-cli auth login --ga-code <code>`。GA 码 30 秒一变，过期或输错报 40103 GA 验证码错误，让用户重新给最新码。
- 如用户未绑定 GA，按 `troubleshooting.md`「GA 绑定」节用 curl 直调 bindreq / bindconfirm（二进制 `auth ga bindreq` 已知返回无响应体的 400 不可用）。
- 不要使用 `hx-cli status --show-token`，除非用户明确要求；不要把 token 原文写进对话或日志。
- 写操作前先用 `hx-cli status` 判断 AIHUB token 是否存在；需要确认 session 时用 `hx-cli auth check`。
- 所有 stdout 是一行 JSON；stderr 是日志。

### 通用规则

1. **先查再写**：写操作前查询项目、成员、类型；写后用 list 验证。
2. **写入前必须确认后果**：任何会创建、修改、删除、流转工作项的操作，执行前必须先停下来，在对话里向用户确认会产生什么结果。只读查询不用确认。
3. **缺失关键信息时直接提问**：如果缺少工作项、负责人、执行人、目标状态等继续执行所必需的信息，直接在对话里问用户补充，不要猜。
4. **确认内容面向结果，不面向命令**：确认消息里优先说明对象名称、将新增/修改/删除/流转的具体内容、可见影响和风险。不要默认要求用户确认 CLI 命令、接口路径或参数；这些是 agent 的执行细节，只有用户主动询问或排障需要时才展示。
5. **用户可见实体用名称/含义**：向用户展示或确认任何实体时，优先说名称、标题、人员姓名、项目名、流程节点名等可理解信息；除火效 H 号外，不要把项目 id、work_type_id、new_work_type_id、staff id、proc id 等内部 ID 直接暴露给用户，必须翻译成背后的对象或含义。
6. **用户未明确同意就不要写**：只有用户在当前对话中明确同意后，才能执行写接口。用户只描述意图、给 curl、问“对不对”、或让你“看看”都不算确认。
7. **不确定或关键风险要打断**：如果 ID、负责人、执行人、删除对象、目标状态任一项不确定，必须先查询；查询后仍不确定就直接询问用户，不要猜。
8. **ID 不要猜**：不同项目的项目 id、`work_type_id`、`new_work_type_id` 都不同，必须用 hx-cli 查询。
9. **staff id 口径**：创建工作项使用 PM staff id，不要用用户 id。
10. **真实写入提醒**：创建 work、流转状态、更新进度都会真实修改后端；执行前说明用户会看到什么变化。
11. **随时提醒更新需求/任务状态**：在查询进度等节点，如果实际进展已经超过或不匹配当前火效需求、研发任务、Bug 的流程状态，要主动提醒用户是否需要同步流转对应需求和任务状态。提醒只说明建议和依据；除非用户明确确认，不要擅自执行 `work transition`。
12. **创建需求/任务时推荐填写时间工时**：创建需求、研发任务、Bug、事务任务或拆分子任务时，主动根据任务理解给出推荐的开始日期、结束日期、预估工时（人天）和必要时的技术预估工时；默认建议写入，用户明确要求不填时可以不填，但确认消息里要说明哪些时间/工时字段将留空。
13. **影响进展时提醒更新时间工时**：拆分任务、补建子任务、调整负责人、返工、延期、关闭任务，或任何会改变实际进展/排期/工作量的节点，都要主动提醒用户是否需要同步更新开始/结束日期、预期完成时间、预估工时和进度百分比。
14. **发现风险时提醒并更新风险字段**：日常开发交流中如果发现逾期、剩余工时明显不足、依赖阻塞、返工、范围扩大、测试/上线窗口错过等风险，先说明依据和建议风险状态/风险描述；若用户确认，使用 `work update-progress` 更新 `risk_state_id`/`risk_description`，必要时同时更新 `expected_done_at`、`end_time`、`work_time`、`percentage_progress`。
15. **实体和字段变化优先表格**：向用户展示查询结果、状态对比、待确认写入对象、字段清单、字段变化、名称、状态、人员、时间、工时等结构化信息时，优先使用 Markdown 表格对齐；风险或不可逆点、用户可见影响、原因解释、下一步建议等偏文字描述的内容，不要强行塞进表格，优先用自然短段落或简短列表说明。
16. **能给链接就给链接，但不要猜链接**：每次回答火效相关结果时，都要按当前模块文档里的“用户可见链接”规则给 Markdown 链接。火效 Web base 是 `https://INTERNAL_URL_REDACTED `https://INTERNAL_URL_REDACTED<work_id>`，这是前端“复制任务链接”的实际格式。链接文本优先使用用户可理解的实体名，例如 `[Market-7418]`、`[H402111]`；不要展示裸长 URL。不能按模块规则确定页面 URL 时，不要编造链接，应说明“当前 CLI 结果没有返回可用页面链接”，并继续给出已核实的名称、H 号信息。

### 火效 Web 链接总规则

| 页面 / 对象 | 用户链接模式 | 说明 |
|-------------|--------------|------|
| 工作项详情 / 需求 / 研发任务 / Bug / 事务任务 | `https://INTERNAL_URL_REDACTED<work_id>` | 默认使用数字 `work_id`，链接文本可用 H 号或标题。前端兼容 `/project/task/:taskId`，但复制任务链接实际使用裸 `/<work_id>`。 |
| 个人面板 | `https://INTERNAL_URL_REDACTED | 用于“我的任务/个人面板”总入口；列表里的每个任务仍给工作项详情链接。 |
| 项目总览 | `https://INTERNAL_URL_REDACTED<tab>/?prj_id=<project_id>` | `<tab>` 必须按模块文档确认，例如 `demand`、`develop`、`bugList`、`workItem`、`offLine`、`design`。不确定 tab 时给项目总入口或只给已核实工作项链接。 |
| QA 提测列表 | `https://INTERNAL_URL_REDACTED | 这是提测单列表入口，不是单个 checker 详情。 |
| 提测历史详情 | `https://INTERNAL_URL_REDACTED<history_id>` | 只有拿到提测历史记录 id 时使用；`checker_id` 不能放进这个 path。 |

### 向用户提问

当本 Skill 需要用户补充信息、确认操作、输入验证码，或做出选择时，直接在对话里提出问题，并等待用户回答后再继续。

提问要求：

- 只问完成任务所必需的问题。
- 优先只问 1 个问题；一次最多不要超过 3 个问题。
- 如果需要提供选项，给出 2-3 个清晰选项，并把推荐选项放在第一位。
- 对删除、生产环境变更、凭证、验证码，或其他有明显影响的操作，必须获得用户明确确认。

### 后果确认模板

执行写操作前，先在对话里展示结果摘要，并等待用户明确确认。确认重点是结果和影响，不是内部命令；实体、含义和字段变化用表格，影响和风险等文字描述用自然段：

```text
我准备做一次真实写入，结果会是：

| 对象 | 名称 / 含义 | 将产生的变化 |
|------|-----------|----------------|
| 工作项 | <标题 / H 号> | <例如创建需求、流转状态、更新进度/风险> |

用户可见影响：个人面板 / 项目列表里对应工作项状态、进度、风险字段会更新。

风险或不可逆点：<例如删除工作项、流转到不可回退状态等>。
```

然后提出一个明确问题：

```text
确认按上表结果真实写入吗？请回复“确认执行”，或说明要调整/取消。
```

如果是多个写步骤组成的标准流程，可以一次性确认最终结果；但如果执行中出现未预期的高风险分支，必须暂停并二次确认新的结果。CLI 命令和接口路径可以在内部使用，不要拿它们代替后果说明。

### 快速检查

```bash
hx-cli status
hx-cli user
hx-cli --token <aihub_token> user
hx-cli project list --name <project_keyword>
```

---

## 核心输出规范

CLI 每条 stdout 是一行 JSON（stderr 是日志）。给用户的答复形态：实体 / 状态 / 字段变化用 Markdown 表格；影响 / 风险 / 建议用自然段（见 §硬规则 15）；能给链接就给 `https://INTERNAL_URL_REDACTED 16）。

CLI 原始返回：

成功：

```json
{"status":"ok","cmd":"...","data":{}}
```

失败：

```json
{"status":"error","cmd":"...","code":"api_error","msg":"..."}
```

常见错误码见 `troubleshooting.md`。

---

## 执行步骤

> 只读查询直接执行；写操作全程守 §硬规则（先查再写 · 后果确认 · 用户明确同意）。

### Step 0 读子文档

按 §使用哪个子文档 选对应文档，确认 ID 类型 / 参数 / 接口顺序，再执行。

### Step 1 查

`status` / `user` 确认 AIHUB token 与 PM staff id；`project` / 成员 / 工作类型查 ID（§硬规则 8「ID 不猜」）。

### Step 2 确认后果（仅写操作）

按 §硬规则「后果确认模板」展示对象 / 变化 / 影响 / 风险，等用户明确「确认执行」再写。

### Step 3 执行 + 回验

执行写接口后用 list 验证；实际进展与火效状态不匹配时，按 §硬规则 11 提醒是否同步流转 + 更新时间工时 / 风险字段。

## 自检清单

写操作前逐条过（依据见 §硬规则）：

- [ ] 已 `status` 确认 token 存在；需要 session 时已 `auth check`
- [ ] 项目 id / `work_type_id` / staff id 均查得，未猜（§8）
- [ ] 已展示后果并获用户明确「确认执行」（§2 / §6）
- [ ] 用户可见实体用名称 / H 号，未暴露内部 ID（§5）
- [ ] 时间 / 工时字段已建议填写或说明将留空（§12 / §13）
- [ ] 结果给了 `INTERNAL_DOMAIN_REDACTED 链接，未编造（§16）
