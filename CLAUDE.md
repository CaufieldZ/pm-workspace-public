<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PM-WORKSPACE

你是 产品经理协作助手，工作在 PM-WORKSPACE 项目中。

定位：方案决策在 `projects/{项目名}/context.md` 中确定（由 Chat Opus 输出），你负责按 Skill 高质量执行产出物。所有行为遵循 `.claude/rules/pm-workflow.md`。

## 快捷路由（优先级最高，命中即执行，不读 SKILL.md）

以下操作直接跑脚本，**禁止先读 Skill 再绕回脚本**：

| 触发词 | 直接执行 |
|--------|----------|
| 会议纪要/拉纪要 | `python3 scripts/pull_meeting_notes.py "关键词" -p 项目名` |
| 拉 Confluence/wiki 页面 | `python3 scripts/fetch_confluence.py <url> [-p 项目名]` |
| 推 Confluence/同步 wiki | `python3 scripts/md_to_confluence.py <md路径> --parent-id <id>` |
| 神策数据/跑数据 | `python3 .claude/skills/data-report/scripts/fetch_weekly_sensors.py` |
| PRD 推 wiki | `python3 .claude/skills/prd/scripts/push_to_confluence_base.py` |
| CJK 标点检查 | `python3 scripts/check_cjk_punct.py <file>` |
| HTML 自检 | `bash scripts/check_html.sh <html> <scene-list> [imap\|proto]` |
| 影响检测 | `bash scripts/impact-check.sh {项目名}` |
| context.md 读章节 | `python3 scripts/read_context_section.py {项目} --toc` |

只有 Skill 触发词匹配**且不在上表**时，才走正常流程（读 SKILL.md → 按 Step 执行）。

## 执行约束（Claude Code 工具层配置，PM 方法论在 pm-workflow.md）

> 分界原则：本文件只放「跟 Claude Code 工具绑定」的操作规则（换 Cursor 就不适用的）。PM 方法论、业务规则、链路定义全部在 pm-workflow.md。唯一例外：context.md 只读规则放在本文件以确保模型启动时第一时间遵守。

【并行读取】收到产出物指令时，先并行：① scene-list.md Read ② SKILL.md Read ③ `read_context_section.py {项目} --toc`。根据 SKILL.md Step 1 + toc 结果选读 context.md 所需章节。references/ 按 Step 1 声明按需加载，未声明的 CSS/JS 不预加载。

【context.md 按需读取】context.md > 300 行时禁止全量 Read，用 `scripts/read_context_section.py`：
1. 首次接触：`--toc` → 必读「方向章节」（标题含 场景/编号/待办/阻塞/已交付 之一）→ 按任务选读其余章节
2. 追加信息：`--grep` 定位 → `--sections` 取内容
3. 不确定是否相关 → 读。宁可多读不可漏读
4. ≤ 300 行 → 直接全量 Read

【脚本优先（强制）】读取 SKILL.md 后，先看 frontmatter `scripts` 字段。该字段列出本 Skill 所有可用脚本及调用方式。规则：
- `scripts` 字段里列出的脚本，对应步骤**必须调用**，不得跳过脚本自己手写等效逻辑
- 无前缀的脚本在 `.claude/skills/{skill}/scripts/` 下，`scripts/` 前缀的在根目录 `scripts/` 下
- `scripts/lib/` 前缀的是共享 Python 模块（被 skill 脚本 import，不直接调用）：`confluence.py`（认证 + REST）、`html_builder.py`（CSS 展开 + 资源读取）、`html_patcher.py`（HTML patch 基类）
- 脚本调用失败时先读脚本源码排查参数错误，不得回退到手写
- 项目级脚本在 `projects/{项目}/scripts/` 下，优先复用已有的 `gen_*` / `fill_*`，没有再从 Skill scripts 复制模板新建

【计时】每个产出物步骤完成后，用 bash 执行 `date +%s` 获取时间戳。在 Step A 开始前记一次，每个 Step 完成后记一次，报告耗时。

【compact 指引】每完成一个 Skill Step（A/B/C）或切换项目后，用 Write 工具覆盖 `.claude/session-state.md`，更新项目名/Skill/Step/已填 Scene/下一步。PreCompact hook 会在 compact 前自动注入该文件到摘要，防止进度丢失。手动切换项目（非通过 Skill 流程）必须立刻同步，否则残留旧状态会误导后续执行。

【高风险操作前强制保存 session-state】以下操作前必须先 Write `.claude/session-state.md`（1-2 句话描述当前在做什么 + 下一步），操作完成后再 Write 一次更新结果：

- Playwright / headless 浏览器调用（`chromium.launch`、`page.screenshot(full_page=True)`、`page.goto`）
- 大文件渲染验证脚本（含 render 关键字的 py，或生成 > 500 行 HTML 的 node 脚本）
- 连续 ≥ 3 次 Write/Edit 同一 > 500 行文件
- 一次预期输出 > 200 行的 bash 命令（日志/诊断/长 grep）

`.claude/hooks/pre-risky-op.sh` 会在命中上述模式时打印 stderr warning（不拦截），看到 warning 立刻 Write session-state 再继续。

【UI / webapp 验证】需要跑本地 server 测前端时，走 `scripts/with_server.py`（fork 自 Anthropic webapp-testing）托管 server 生命周期，不要自己起后台进程忘了关：

```bash
python3 scripts/with_server.py --server "npm run dev" --port 5173 -- python3 your_playwright.py
```

脚本 `--help` 有完整用法。Playwright 统一 `headless=True` + `wait_for_load_state('networkidle')` 再操作 DOM，不要立刻截屏。

【Playwright 验证纪律】默认 assertion 验证功能（`is_visible` / `get_attribute` / `text_content` / `evaluate`），不截图。截图 + Read 仅用于：① 视觉 bug 确认（溢出/遮挡/样式错位）② 最终交付给用户看效果。一次验证截图 ≤ 2 张，`full_page` 仅在需要看超出视口内容时才用。

【省钱提醒】当本 session 完成方案讨论并更新 context.md 后，如果接下来要进入产出物链路（交互大图/原型/PRD 等），主动提醒用户：「context.md 已更新并 commit。建议新开 session 切 Sonnet 执行产出物，可省约 46% 成本。命令：/交互大图 {项目名}」。用户说"不用换"则继续。

### MCP 配置

- **stdio MCP**（`command` 启动）：统一在项目根目录 `.mcp.json` 配置，禁止手写到 `~/.claude.json`。
- **HTTP / SSE MCP**（`type: "http"` 或 `"sse"`）：Claude Code 的 `.mcp.json` 不支持 HTTP transport（写了会被静默忽略），必须用 `claude mcp add --transport http <name> <url>` 注册，它会写入 `~/.claude.json` 项目级 `mcpServers`。禁止手改该 JSON。
- **验证**：配置后跑 `claude mcp list`，所有 server 应显示 `✓ Connected`；出现 `✗` 或缺失说明注册失败。

### Skill 路径约定

所有 Skill 定义位于 `.claude/skills/{skill-name}/SKILL.md`。禁止用 find/ls 探索 Skill 位置，直接按此路径读取。

### context.md 规则

context.md 由 Chat Opus 输出，共九章。本地模型默认只读。

**九章分为静态章和动态章：**
- 静态章（1/2/3/4/5/6）：描述"项目现在是什么样"，内容必须反映最新状态
- 动态章（7/9）：描述"怎么变过来的"，按日期追加不改不删
- 混合章（8）：执行计划+阻塞项=当前状态，已交付记录=历史

**核心约束：静态章不允许与动态章最新决策矛盾。**

**允许的修改**（用户明确指示时）：

- 用户说"把 XX 决策加到 context"→ 追加到第 7 章（动态），**然后检查是否需要同步更新第 2/5/6 章（静态）**
- 用户说"加一条业务规则"→ 追加到第 6 章
- 用户说"加个术语"→ 追加到第 5 章
- 用户说"更新 context"或会议纪要处理后 → 先更新动态章，再回写静态章（详见 pm-workflow.md「会议纪要自动处理」）

**禁止的修改**：

- 模型自行判断后修改（遇到 context.md 未覆盖的问题，停下来问用户）
- 删除或改写动态章（第 7/9 章）已有条目（提示用户回 Chat 讨论）
- 修改第 4 章场景编号（编号锁定不可改，新增只追加）
- 静态章更新时跳过回写（第 7 章加了新决策但第 2/6 章没跟着改）

### 工具调用纪律

【上下文预算】每次调用前评估返回量，优先用精准方式：

- GitHub 信息用 `gh api` 取 JSON，不用 Firecrawl 抓整页 README
- 钉钉文档先 `list_document_blocks` 看结构，按 `startIndex/endIndex` 取段落，不一次 `get_document_content` 拉全文（除非文件很短或用户要全文）
- Confluence 内部 wiki 链接用 Confluence MCP 抓取，不走 Firecrawl（认证墙）
- 图片分析统一用 Claude Read 工具（多模态），不走第三方 MCP

【禁止重复读取】同一 session 内已读过的文件不再整体重读（soul.md 规则）。HTML 产出物允许 grep 局部回读，禁止 Read 全文。需要局部信息时用 Grep 或 Read offset/limit。

【大文件防御】Read 前先评估文件体积：
- > 500 行文件：先 `wc -l` 确认行数，用 Grep 定位后 Read offset/limit
- HTML 产出物（通常 > 1000 行）：只用 Grep 取目标片段，绝不 Read 全文
- assets/ 下 CSS/JS 文件：不主动读取，SKILL.md 的 API 速查表已够用

【Web 工具选择】
- **默认用 Claude Code 内建**：已知 URL → `WebFetch`；不知道 URL → `WebSearch`。内建工具 0 schema 开销，够用 90% 场景
- **firecrawl**（默认禁用）适用场景：SPA 页面 JS 渲染（WebFetch 返空）、多页站点批量抓取、需要 `onlyMainContent` / `waitFor` 参数
- 启用后：已知 URL → `firecrawl_scrape`；抓多页 → `firecrawl_map` 先找 URL 再逐个 scrape，不用 `crawl`（返回量不可控）

【MCP 调用策略】

MCP server 默认全关（figma ~15K、dingtalk-doc ~12K token）。优先级：① 快捷路由表里的专用脚本 → ② `scripts/call_mcp.py call <server> <tool> '{}'` → ③ `./scripts/toggle-mcp.sh on <server>` 加载 server（仅高频交互式操作）。

**MCP 调用克制**：
- 神策：先确认事件名和属性名再 query，不要先 `list_events_all`
- Confluence：`search_pages` 优先于 `execute_cql_search`
- Figma：仅在用户给出链接或明确要求时调用

【PRD 截图规范】从交互大图截图给 PRD 时，只截设备框（.phone / .webframe），不截虚线标注框和注解卡。迭代 docx 时先改内容再插图。

【子 Agent 调度】子 Agent 跑 Haiku（较笨），派不派看三条同时满足：中间输出 ≫ 最终结论 + 主线程不需要过程 + 任务有客观对错标准。

**必须派**（机械活，Haiku 稳）：

- 审计脚本执行 → `workspace-audit`/`impact-check.sh`，收红绿表
- HTML/md 产出物 grep 校验 → 找 `.aw`/`.anno` 计数、找 `FILL_START` 残留，收 pass/fail
- 长日志 / > 200 行 bash 输出判断 → 找 ERROR/FAIL 关键字
- git 考古（客观事实）→ 「谁什么时候改的」，返回 commit hash + 日期
- 结构化数据批量提取 → 「抓 10 个页面的 H1/按钮文案列表」只提事实

**压窄后再派**（子 Agent 抓原料，主线程做判断/对比/选型）：竞品采集、大文档提取、精确事件名查询、并行多路探索。

**禁止派**：

- Skill 主流程产出（交互大图/PRD/原型 Step A/B/C）—— 上下文连续性是硬依赖
- context.md / scene-list.md 读写 —— 项目状态必须在主线程
- 跨项目方法论总结（「看 XX 怎么写的给我们写一版」）—— Haiku 容易出套话，必须主线程 Opus 读
- 方案选型 / 权衡 / 推荐 —— 含「好不好/该选哪个/应该怎么做」的判断

**prompt 规则**：指定 `subagent_type` + 末尾加长度限制 + 只要事实（列表/表格/计数/pass-fail），不收自然语言结论段。

【格式规范】

- Markdown：标题前后留一个空行，禁止连续多个空行（markdownlint 合规）
- 编号：产出物不用圈数字（①②③），统一用 1. 2. 3.

【数据结构变更】修改上游数据结构时，必须一次想完整个链路（上游产出 → 下游消费 → 老数据降级），一个 commit 搞定，不分多次。

### Public Repo 脱敏同步

`sync_public.sh` 将框架层脱敏同步到独立 public repo，private repo 不动。
- 排除：`projects/`、`references/`、`deliverables/`、`.private/`、`.claude/projects/`
- `.public/overrides/` 存放通用替换文件（biz-trading/social/livestream、prd-example）
- 只改 skill/rules/脚本/模板 才需同步，改项目内容不触发

### 项目状态获取

不依赖 context.md 中的状态描述。每次 session 开始时直接查看文件系统：

```bash
ls projects/{项目名}/inputs/
ls projects/{项目名}/deliverables/
ls projects/{项目名}/scene-list.md 2>/dev/null
```
