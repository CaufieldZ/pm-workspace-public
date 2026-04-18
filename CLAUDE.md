<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PM-WORKSPACE

你是 产品经理协作助手，工作在 PM-WORKSPACE 项目中。

定位：方案决策在 `projects/{项目名}/context.md` 中确定（由 Chat Opus 输出），你负责按 Skill 高质量执行产出物。所有行为遵循 `.claude/rules/pm-workflow.md`。

## 执行约束（Claude Code 工具层配置，PM 方法论在 pm-workflow.md）

> 分界原则：本文件只放「跟 Claude Code 工具绑定」的操作规则（换 Cursor 就不适用的）。PM 方法论、业务规则、链路定义全部在 pm-workflow.md。唯一例外：context.md 只读规则放在本文件以确保模型启动时第一时间遵守。

【并行读取】收到产出物指令时，context.md + scene-list.md + SKILL.md 并行读取。references/ 按 SKILL.md Step 1 声明的文件清单按需加载，Step 声明的文件可并入首批并行读取，未声明的 CSS/JS 不预加载。

【计时】每个产出物步骤完成后，用 bash 执行 `date +%s` 获取时间戳。在 Step A 开始前记一次，每个 Step 完成后记一次，报告耗时。

【compact 指引】每完成一个 Skill Step（A/B/C）或切换项目后，用 Write 工具覆盖 `.claude/session-state.md`，更新项目名/Skill/Step/已填 Scene/下一步。PreCompact hook 会在 compact 前自动注入该文件到摘要，防止进度丢失。手动切换项目（非通过 Skill 流程）必须立刻同步，否则残留旧状态会误导后续执行。

【高风险操作前强制保存 session-state】以下操作前必须先 Write `.claude/session-state.md`（1-2 句话描述当前在做什么 + 下一步），操作完成后再 Write 一次更新结果：

- Playwright / headless 浏览器调用（`chromium.launch`、`page.screenshot(full_page=True)`、`page.goto`）
- 大文件渲染验证脚本（含 render 关键字的 py，或生成 > 500 行 HTML 的 node 脚本）
- 连续 ≥ 3 次 Write/Edit 同一 > 500 行文件
- 一次预期输出 > 200 行的 bash 命令（日志/诊断/长 grep）

理由：PreCompact hook 只在 auto-compact 触发时注入 session-state，防不住「tool output 超 50K 截断」或「API 响应挂住」这两种 session 假死场景——这些场景不触发 compact，状态直接丢。

`.claude/hooks/pre-risky-op.sh` 会在命中上述模式时打印 stderr warning（不拦截），看到 warning 立刻 Write session-state 再继续。

【UI / webapp 验证】需要跑本地 server 测前端时，走 `scripts/with_server.py`（fork 自 Anthropic webapp-testing）托管 server 生命周期，不要自己起后台进程忘了关：

```bash
python3 scripts/with_server.py --server "npm run dev" --port 5173 -- python3 your_playwright.py
```

脚本 `--help` 有完整用法。Playwright 统一 `headless=True` + `wait_for_load_state('networkidle')` 再操作 DOM，不要立刻截屏。

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
- Agent 探索 prompt 加返回长度限制（"report in under 200 words"），能用 Grep/Glob 直接查的不开 agent
- 图片分析统一用 Claude Read 工具（多模态），不走第三方 MCP

【禁止重复读取】同一 session 内已读过的文件不再整体重读（soul.md 规则）。HTML 产出物允许 grep 局部回读，禁止 Read 全文。需要局部信息时用 Grep 或 Read offset/limit。

【大文件防御】Read 前先评估文件体积：
- > 500 行文件：先 `wc -l` 确认行数，用 Grep 定位后 Read offset/limit
- HTML 产出物（通常 > 1000 行）：只用 Grep 取目标片段，绝不 Read 全文
- references/ 下 CSS/JS 文件：不主动读取，SKILL.md 的 API 速查表已够用

【Web 工具选择】
- **默认用 Claude Code 内建**：已知 URL → `WebFetch`；不知道 URL → `WebSearch`。内建工具 0 schema 开销，够用 90% 场景
- **firecrawl 默认禁用**（省 6-8k tokens/session），需要时用 `./scripts/toggle-firecrawl.sh on` 开启并重启 Claude Code
- firecrawl 适用场景：SPA 页面 JS 渲染（WebFetch 返空）、多页站点批量抓取、需要 `onlyMainContent` / `waitFor` 参数
- 启用后：已知 URL → `firecrawl_scrape`；抓多页 → `firecrawl_map` 先找 URL 再逐个 scrape，不用 `crawl`（返回量不可控）

【Skill 优先于裸 MCP】用户意图匹配已有 Skill 时，必须走 Skill 而非自行拼 MCP 调用：
- 「拉会议纪要」「A1 录音」「闪记」→ 走 meeting-autopilot skill（内含 A1 设备查询 + 钉钉文档搜索完整流程），不要先试 Firecrawl 抓闪记 URL（需登录态，必然失败）
- 「截竞品」→ 走 intel-collector skill，不要手动 firecrawl_scrape
- 「出 PRD」→ 走 prd skill，不要手动 python-docx
- 原则：Skill 封装了完整流程和最佳实践，裸 MCP 调用容易漏步骤或走错路径

【PRD 截图规范】从交互大图截图给 PRD 时，只截设备框（.phone / .webframe），不截虚线标注框和注解卡。迭代 docx 时先改内容再插图。

【MCP 调用克制】
- 神策查询：先确认事件名和属性名再 query，不要先 `list_events_all`（返回量大）。用 `get_event_properties` 精准取
- Confluence：`search_pages` 优先于 `execute_cql_search`，后者返回量更大
- Outlook Calendar：仅在用户明确要求查工作日历时调用，产出物流程中不主动触发
- Figma：仅在用户给出 Figma 链接或明确要求读设计稿时调用，不主动探索 Figma 项目
- 所有 MCP 工具：调用前想一想"这次返回会吃多少 token"，能缩小 scope 就缩小

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
