# PM-WORKSPACE

> 工具操作层。每 session 自动注入。路由 / 工具调用 / 启动规则。

## 工区 / 全局术语 / 战略

**工区**：两条产线——`projects/` PM 生产线（含 aihub 平台 PM，规范走 `.claude/runbooks/skill-conventions.md`）；`hub/` AIHUB 包生产线（Agent / Tool / Skill 三形态，纳 git，规范走 `.claude/runbooks/ai-platform-specs.md`——公司中台规范入口）。Felix 在 PM 生产线 = 示例社区 PM（community / livestream / growth / 顶级方案型 / 顶级基建）。探索性任务（probe / 调研 / 采集）启动前反问「社区要用还是方法论示范」，别被 prompt「跨业务线 / 全站 / ~N 个」种子带偏。

**项目目录**：统一 baseline 建档模型——产品线 / 活动 / 方案的当前态真相在 `prd-{产品线/活动}-baseline.md` + `scene-list.md`（living、无版本号），本轮迭代写 delta（`deliverables/{季度}/{版本}/`），上线后反向合并。产品线（community / livestream / liquidity）baseline 落产品线根；一次性活动（campaign 变体，如 growth/queen）+ 方案型（变体，如 liquidity）落自身项目目录；无 baseline 例外 = biweekly（双周协调容器 `README.md`）+ sensors-metrics（指标目录），truth_source `EXEMPT_LINES` 豁免。**项目目录多为英文短名**（queen / leaderboard），中文项目名（如"Platform C一姐"）只在 baseline 业务描述——模糊中文名定位项目 → `find projects -mindepth 2 -maxdepth 2 -type d` 拿全清单语义匹配，别用 `-iname "*<中文>*"` 盲找。场景编号（A / B / C 主场景 / A-1 / A-2 子场景 / M-N 后台 / F-N 功能 / D-N 数据流 / E-N 异常）锁在 `scene-list.md`——定位编号先 grep 它，不盲扫 projects/。子目录结构见 `.claude/runbooks/project-mgmt.md` §文件落点查找表。


**战略宪法**：`projects/product-lines.md`。在一键开项目 / 主流程链路决策 / 跨产品线方案 / 用户提"战略 · 漏斗 · 协同 · 信任分层 · 北极星"关键词 / baseline 决策章战略级决策时 Read。projects/ 由 sync_public.sh 排除。

## 收到需求路由（先扫风险，再选链路）

收到产品需求第一步过 PM-GATE 4 风险扫描（一次一问，每问带推荐答案 + 理由，能从 context / inputs / 竞品查到的自己查）：

- **Value 价值**：解决谁的什么具体痛点？（场景化，不接受"优化体验"）
- **Usability 可用**：主流程几步？哪步用户最易流失？
- **Feasibility 可行**：涉及哪些端 / 新接口 / 跨团队依赖？
- **Viability 商业**：核心指标 + 具体数字 + 怎么判断成功？（对照 product-lines.md 北极星）

**跳过条件**（任一）：PM 说「跳过 / 快速 / 直接做」/ baseline 已含 4 风险结论 / 改 ≤ 1 场景 / 方案型项目（无 UI）。跳步可以，必须提醒跳的是哪个风险。

**复杂度 → 链路**（任一为复杂：≥ 2 端或角色 / ≥ 5 场景且有跨跳转 / 含数据同步 / 状态流转 / 多角色协作）：

- **简单**：纯功能点 → Markdown PRD；单页面 → 原型；纯文案 → 文档
- **复杂**：scene-list → imap → prototype → prd → cross-check（每步等确认；PRD 写入后 hook 自动跑 7 维结构校验，多 ❌ 项修复优先级 + Reader Testing 由 cross-check skill 承载）
- **超复杂**：scene-list 与 imap 之间插 arch-diagrams（pipeline 2.5）
- **方案型**（跨 ≥ 2 系统 / 资金 / 多团队 / 纯后端）：不走标准 pipeline，详见 prd SKILL.md
- **老项目迭代**（产品线已有 `prd-{产品线}-baseline.md`）：不重写 baseline，本轮需求写 delta（`gen_prd_skeleton.py --profile delta`）→ 上线后补 baseline changelog 行（状态=已合并）+ 反向合并进 baseline 模块章。模型见 `.claude/runbooks/artifact-conventions.md §六`

方法论展开（Discovery 铁律 / 决策段 / 逻辑拼图 / Outcome / 70% / PR-FAQ）见 `.claude/runbooks/pm-methodology.md`。

## 快捷路由（优先级最高 · 命中即跑脚本 · 不读 SKILL.md）

> 命令前缀 `python3 scripts/` 省略，bash 脚本与特殊路径单独标注。多子命令 / 复杂参数（slack / youshu_cli / pack_for_opus / fetch_figma / sync_pools）→ Read `.claude/runbooks/cli-cheatsheet.md`；其余极少用参数走脚本 `--help`。

| 触发词 | 直接执行 |
|--------|----------|
| 会议纪要/拉纪要 | `pull_meeting_notes.py "关键词" -p {项目}` |
| 拉 Confluence/wiki | `fetch_confluence.py <url> [-p {项目}]` |
| 考古 feature（多篇迭代文档聚成时间线语料） | `dig_confluence.py "关键词" --space <KEY> [--parent-id <ID>] [-p {项目}]`（泛词加 `--title`；单页版本时间线用 `--page-id <ID>`）→ 喂 agent 重建时间线 |
| 不知道 pageId/URL 定位页面 | `nav_confluence.py find "标题词" [--space <KEY>]` 拿 pageId+URL；`nav_confluence.py tree <parentId> [--recursive] [--max-depth N]` 看子页树 |
| 直接调 Confluence REST（透传/调试/临时 CQL） | `confluence_api.py <endpoint> [-X POST] [-f k=v] [--jq '...']`（迷你 jq：点路径 / `.a[]` / `\| length`） |
| 下载 Figma 图片/批量素材 | `fetch_figma.py` → cheatsheet |
| 联网搜索（无 WebSearch 模型必跑 / 中文站点优先） | `call_mcp.py call web-search-prime web_search_prime search_query="..."` |
| 网页读取（已知 URL 抓正文，SPA/反爬可试） | `call_mcp.py call web-reader webReader url="..."` |
| 读开源仓库/GitHub 源码 | `call_mcp.py call zread search_doc repo_name="owner/repo" query="..."`（结构 `get_repo_structure` / 读文件 `read_file`，参数均 `repo_name`） |
| pdf/docx/pptx/xlsx → md | `doc_to_md.py <file> [--batch]` |
| 识图/OCR/图表/视频 | **多模态模型**（Sonnet 4.6+ / Opus 4.8+ / Fable 5）原生看图，不调 zai-mcp-server；**非多模态**走 `call_mcp.py call zai-mcp-server <tool>`（图片先放项目目录再传路径）。**Read 图片前预检**：任意维度 > 2000px 或 > 5MB 先跑 `compress_image.py` 再 Read（Bedrock 硬限制） |
| 打包工作区 | `pack_for_opus.py` → cheatsheet |
| 推 Confluence | `md_to_confluence.py <md> --parent-id <id>`（覆盖已有页加 `--update-id <pageId>`） |
| 神策数据（周报指标） | `.claude/skills/data-report/scripts/fetch_weekly_sensors.py` |
| 神策 ad-hoc 查数（去神策查 XX：UV/PV/漏斗/留存/分端分版本） | 先读 `.claude/skills/data-report/references/sensors-queries.md` §0 配方速查（R0-R10 可抄 body），照配方跑 `query_analytics.py`，别从 swagger 摸参数 |
| 神策事件属性（PRD 埋点章节填表前必跑，拿事件真名 + 真属性 + 真值候选） | `projects/sensors-metrics/scripts/probe_event_properties.py --events <事件名,逗号分隔> [--print]`；验证埋点加 `--env test`，默认 prod，不定先问 |
| Slack 消息 | `slack.py` → cheatsheet |
| 有数报告/BI 链接 | `youshu_cli.py` → cheatsheet |
| Platform C 公开行情（币价/K线/盘口/逐笔/币对清单） | `market_cli.py ticker btc`（子命令 tickers/kline/depth/trades/symbols；币对清单 `-t swap/coin/delivery`，`--cat tradfi` 按标签过滤；裸币名自动补 usdt，`--json` 出原始数据） |
| CJK 标点检查/修复 | `check_cjk_punct.py <file> [--fix] [--dry-run]` |
| 决策 note 格式校验 | `check_decisions.py`（默认扫 `.claude/decisions/`，`--strict` exit 2） |
| HTML 自检 | IMAP: `bash .claude/skills/interaction-map/scripts/check_imap.sh <html>` · 原型: `bash .claude/skills/prototype/scripts/check_proto.sh <html>` |
| 影响检测 | `bash scripts/impact-check.sh {项目}` |
| 并行 delta 冲突检测 | `check_delta_conflict.py {产品线}` |
| baseline / PRD 读章节 | `.claude/skills/prd/scripts/read_prd_section.py <baseline.md> --toc` |
| 导出埋点 xlsx / 埋点表格 / 埋点合并单元格 | `.claude/skills/prd/scripts/export_tracking_xlsx.py <prd.md>` |
| 场景清单视觉版 | `.claude/skills/scene-list/scripts/render_scene_list.py {项目}` |
| 发 vercel/分享 | `bash scripts/publish.sh <html>`（`--list` / `--unpublish`） |
| 项目看板 | Read `.claude/workspace-dashboard.md`（Stop hook 6h 自动刷；强刷 `dashboard.py`） |
| 需求池 | `bash scripts/sync_pools.sh` → cheatsheet |
| 火效 delta 状态/上线日期同步（火效为权威源，回写本地状态 + 排期行） | `sync_hx_status.py <delta.md>`（默认 dry-run，`--apply` 落盘；`-p {产品线}` 扫当季）先 `source .env` |
| 火效任务进展（分支/H 号做到哪一步） | `.claude/skills/hx-cli/scripts/hx_task_progress.py [H号]` 先 `source .env` |
| 火效个人面板（我手头/逾期的任务） | `.claude/skills/hx-cli/scripts/hx_panel.py [--filter overdue\|current]` 先 `source .env` |
| hub 刷包索引（INDEX.md 自动分类） | `python3 hub/gen_index.py`（`--check` 对账，drift 则 exit 1） |
| hub 上架预检（密钥 / frontmatter / 红旗 / 语法） | `bash hub/_vet_local.sh <包目录>`（❌ fail-stop / ⚠ 不阻断） |
| hub 重打 zip | `bash hub/_repack.sh <包>`（禁手动 zip） |
| hub 解压后端到端验证 | `bash hub/_verify.sh <包\|all>` |
| hub 源头 → 分发包同步 | `bash hub/sync.sh <skill>`（先 `--check` 干跑） |
| hub 发布物新鲜度（zip 过期 / OWUI 部署态漂移） | `python3 scripts/check_hub_fresh.py [--strict]` |

只有 Skill 触发词匹配**且不在上表**才走 Skill 流程（读 SKILL.md → 按 Step 执行）。音视频能力事实（TRTC / OBS · 推流 · 连麦 · 编码档位 · 错误码 · 计费）固定查证路由：TRTC 走 `trtc-docs` skill，OBS 走 `references/repos/obs-studio` 源码 grep（耦合点见 `projects/livestream/lessons.md`），不凭模型记忆答。

## 启动规则

- **baseline 按需读取**：> 300 行禁全量 Read，走 `.claude/skills/prd/scripts/read_prd_section.py <baseline.md>`：先 `--toc` → 必读方向章节 → 按任务选读；追加信息 `--grep` 定位 → `-s` 取章节。≤ 300 行直接全量 Read。
- **项目视图自动注入**：session-start hook 已注入 dashboard「## 项目视图」节（每 6h 刷新）。**不要再 ls projects/ 探项目状态**；某项目 inputs/deliverables 细节用 `ls projects/{项目}/inputs/ deliverables/ scene-list.md 2>/dev/null` 一次。
- **LEARNED.md**：根目录 `LEARNED.md`，session 开始读取（如存在且非空）。被用户纠正 / 踩坑修正 / 发现可复用工区教训时，回复末尾**单独起一行** `[LEARN] 一句话规则`（单行、< 500 字、不以 ``` 或 — 开头，否则 hook 静默丢弃）。
- **决策记录（decisions）**：`.claude/decisions/`（proposed / implemented / rejected 三态）。工区治理类非平凡变更（建模 / 路由 / 门槛 / gate / skill 形态 / 目录结构 / 术语）同轮必须写或更新一篇，`## Alternatives considered` 强制。产品业务决策走 baseline 决策章。边界与格式见 `.claude/decisions/README.md`。
- **session-state.md**：`.claude/session-state.md`，按需手动 checkpoint（**切 session 前** / 手动 compact 前 / 高风险操作前 Write）。SessionStart 与 PreCompact hook 自动注入；72h 未更新自动清理。**首选切 session 而非 compact**：新 session 是干净 slate，compact summary 是 LLM 不可控产物——仅「顺利做事但 ctx 长了、没误判」时 compact。
- **Skill 路径**：所有 Skill 定义在 `.claude/skills/{skill-name}/SKILL.md`，禁 find/ls 探索。

## 工具调用红线

- **脚本优先（强制）**：SKILL.md frontmatter `scripts` 字段列出的对应步骤**必须调用**，不手写等效逻辑；失败读源码排错不回退手写。路径：无前缀 = `.claude/skills/{skill}/scripts/`，`scripts/` 前缀 = 根目录，`scripts/lib/` = 共享模块（被 import）。
- **并行 Read 三件套**：产出物指令并行 Read scene-list.md + SKILL.md + `read_prd_section.py <baseline.md> --toc`，按 SKILL.md Step 1 + toc 选读 baseline 章节。
- **大文件 / 重复 Read**：同 session 已读文件不重读；> 500 行先 `wc -l` + Grep 定位 + offset/limit；HTML 产出物（> 1000 行）只 Grep；assets/ CSS/JS 不主动读（SKILL.md API 表够用）。
- **Web 工具**：已知 URL → `WebFetch`；未知 URL → `WebSearch`（无 WebSearch 的模型 fallback 见快捷路由表 web-search-prime）；SPA / 反爬 / 需交互 → browser-use（见 competitor-analysis collection-playbook）。
- **MCP 调用**：默认全关，详细策略见 `.claude/runbooks/mcp-config.md`。
- **子 Agent**：无项目自定义 agent，按需调通用（`Explore` / `general-purpose`）。长输出 / 跨项目扫描 / 独立可并行研究 → 派；业务判断 / 选型 / 跨文件一致性比对 / 长文档消化 → 主线自跑。sub-agent prompt 必须显式禁读写 session-state.md。

## 修改入口防误操

> 已被 hook 机械拦截的（改产物前未 Read SKILL.md / 直 Edit 脚本化 HTML / 静态章四不 / 图片路径 / 骨架版本号同步 / 原型范式 / 推 wiki / 大文件 Read）—— 看 hook 报错按指引执行，不在此列。

- **改业务规则 / 流程节点 / 入口位置 / 门槛阈值 / 权限规则 / 状态机 / 场景定位 / 场景属性 / 场景归属 前必先 Read `.claude/runbooks/pm-methodology.md`**（§二 逻辑拼图 + 决策段四段法）。业务规则 / 场景变动一律按方法论推演——三维度按 pm-methodology §二「逻辑拼图」豁免规则附回复末尾，再动文件。
- **改 baseline / scene-list.md / 产物文件前必先回读上下文**：baseline > 300 行用 read_prd_section.py；产物间引用与编号规则见 artifact-conventions.md。
- **HTML 生成规模**：> 200 行禁 Write 直接写、必须脚本生成；> 1500 行或 Tab ≥ 10 拆分规则见 `.claude/runbooks/html-build-split.md`。本节阈值（200 / 300 / 500 / 1500 / Tab≥10）见 [scripts/lib/thresholds.yaml](scripts/lib/thresholds.yaml)，Python 调用 `from lib.thresholds import T`。

## 代码与工程纪律

- **只动该动的 + 善后只清自己留的 orphan**：每行改动必须能追溯到用户请求；禁顺手"改进"无关代码 / 格式 / 注释；不主动 refactor 没坏的东西。你的改动让 import / 变量 / 函数变 unused → 删；已有死代码提一句不主动删；一次性 fixture / 半成品脚本（`test_*.py` / `inject-canary.sh`）跑完即删
- **最简能解决就最简**：不主动加抽象 / configurability；不写"impossible 场景"的 error handling；单次使用的代码不抽公共方法
- **多步骤先列计划 + 验证标准**：「1. X → verify: Y / 2. … → verify: …」让循环可自验证；只说"做 X"没说怎么验证 = 循环没收敛信号
- 数据结构变更一次想完整链路（上游产出 → 下游消费 → 老数据降级），一个 commit 搞定
- prompt 里的精确数字（"20 个" "5 条"）多是参考，覆盖范围 / 维度完整性比数字本身重要，不当硬指标
- **规则文件只讲当前规则，不写沿革**：CLAUDE.md / SKILL.md / runbooks/ / 脚本 docstring & 注释禁时间向量 + 因果叙述（「YYYY-MM-DD 起 / 改成」「老 X 兼容」「vN 翻车」「修订前 / 修订后」「起源：xxx」「（精简 / 合并 / 下沉）」），沿革进 git log / commit message。例外：tech-debt-backlog.md 本质是时间线；human-voice-rules / artifact-conventions 把沿革词作为「禁止表达」反例展示

## Runbook 触发条件（hook 未覆盖的判断类）

> 触发后 `Read .claude/runbooks/{下表文件名}`。文件名右侧括号若提及 hook，说明该 trigger 部分场景已被 hook 兜底（看 hook 报错按指引执行即可）。

- Playwright / headless / 截图 → `cli-cheatsheet.md` §Playwright
- `pip` / `npm` / `brew` / `curl` / `wget` / `go get` / `cargo` 出现 `timeout` / `connection refused` / `reset` → `proxy-fallback.md`
- 调 MCP 工具 / 改 `.mcp.json` / 新增 MCP server → `mcp-config.md`（常驻落 `.mcp.json`，按需落 `.mcp-disabled.json` 配 `call_mcp.py`）
- 方案选型 / 评估竞品做法 / 找不到竞品 pattern → `decision-framework.md`
- 改 ≥ 2 文件 / 删新增场景 / 改术语 / 决定要不要升版 → `version-bump.md`
- 新建项目 / 提到不存在的项目名 / 项目命名疑问 / 不确定文件落点 / 改 .gitignore 项目相关条目 → `project-mgmt.md`
- 建火效需求 / 新建 delta 火效单 / 给 GA 码建需求 → `hx-create.md`（流程编排：认证 → work create → 回填 delta）
- 模糊需求需 Discovery 澄清 / 写 baseline 决策章 / delta §6 决策段 / 写 PRD §1 PR-FAQ / 评估方案 Outcome / 拒绝跨角色 O 类活 / 判断要不要建新 skill / 周月时间档位排序 / LNO 重排 → `pm-methodology.md`
- 写产物多项并列编号不确定 / 改产物前需回读 scene-list + 上一步 → `artifact-conventions.md`
- 字段口径 / 状态全集 / 池策略 / 埋点 / 跳转规则 该写哪个 skill 拿不准 → `info-ownership.md`
- 考古 Confluence 历史文档 / 用 dig 语料反哺 baseline / 重建 feature 演进 → `confluence-archaeology.md`
- 新写 PRD §4.x 不确定「理由」保留边界 → `human-voice-rules.md`
- commit / git 安全 / 新写 hook / 推代码 / 推两边 / 双 repo / sync public → `git-and-hooks.md`（「推两边」= push private origin + 跑 `./sync_public.sh` 同步公开镜像）
- 新建 / 改造 skill / 加 frontmatter / 加产出物前缀 / 写任何塑形模型行为的规则 · 红线（含改 CLAUDE.md · runbook · SKILL.md 行为段）→ `skill-conventions.md`（按失败类型选形态；行为塑形改动先 micro-test）
- audit / rules-review 后补充技术债 / 想看待办重活清单 / 立项框架层重构 → `tech-debt-backlog.md`
- 动 `hub/` 分发包 / 出包 / 上架 SkillHub / 打 zip / 加 aihub_tool / 同步源头到 hub / 抽象 skill 发给同事 → 先 `Read hub/README.md`（维护者手册：三层文件分类 / 脱敏规则 / sync.sh / 打包走 `_repack.sh` / Tool 两范式）
- 新建 / 改 `hub/` 下 skill / agent / tool / CLI / 知识库产物 / 建 Agent / 建 Tool 前 → 先 `Read .claude/runbooks/ai-platform-specs.md`（公司中台官方规范：产物→必读规范映射；Claude Code skill 走工区 skill-conventions，AI 中台 Agent·Tool 走公司规范，冲突按此优先级。规范库 `hub/AI中台-规范及帮助文档/` 本地存在不入 git，重拉走 `dig_confluence.py` 父页 164485093）
