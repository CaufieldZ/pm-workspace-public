# Scripts 清单

> 本文件由 `python3 scripts/gen_scripts_readme.py` 自动生成，**勿手改**。
> 本文件只回答「当前有哪些 script、各管什么」；具体用法见各脚本 docstring / `--help`。
> 加 / 删脚本后重跑生成脚本；audit §15.8 会校验是否 drift。

## 入口脚本（scripts/*.py + *.sh）

### 快捷路由入口（CLAUDE.md 触发即跑）

| 脚本 | 快捷路由 | 职责 |
|------|---------|------|
| `call_mcp.py` | 联网搜索（无 WebSearch 模型必跑 / 中文站点优先） / 网页读取（已知 URL 抓正文，SPA/反爬可试） / 读开源仓库/GitHub 源码 / 识图/OCR/图表/视频 | 通用 MCP 调用脚本——HTTP 和 stdio 均支持，不需要在 Claude Code 里加载 server。 |
| `check_cjk_punct.py` | CJK 标点检查/修复 | 中文产出物排版自检 — 全 PM-WORKSPACE 唯一规则源。 |
| `check_decisions.py` | 决策 note 格式校验 | 决策记录（.claude/decisions/）格式校验：生命周期目录一致、必需章节、alternatives 实质非空。 |
| `check_delta_conflict.py` | 并行 delta 冲突检测 | 并行 delta 冲突检测（在途 delta 间的反向合并目标重叠提示）。 |
| `check_hub_fresh.py` | hub 发布物新鲜度（zip 过期 / OWUI 部署态漂移） | hub 分发物新鲜度校验（改完源码忘重打 zip / 忘重贴 OWUI 的机械检出）。 |
| `compress_image.py` | 识图/OCR/图表/视频 | 图片压缩 · 满足 Bedrock 多图 2000px / 5MB 限制，供多模态 Read 前预处理。 |
| `dashboard.py` | 项目看板 | Workspace Dashboard — 聚合 .claude/logs/usage.jsonl + projects/ 状态。 |
| `dig_confluence.py` | 考古 feature（多篇迭代文档聚成时间线语料） | 考古：按 feature 关键词批量拉一组历史迭代文档，聚成一份按时间正序的语料 md。 |
| `doc_to_md.py` | pdf/docx/pptx/xlsx → md | 把 docx / pdf / pptx / xlsx / 图片等转成 markdown，包装 markitdown CLI。 |
| `fetch_confluence.py` | 拉 Confluence/wiki | 从 Confluence URL 拉取页面内容，自动适配 4 种形态。 |
| `fetch_figma.py` | 下载 Figma 图片/批量素材 | 从 Figma 拉取文件/节点/截图。 |
| `market_cli.py` | Platform C 公开行情（币价/K线/盘口/逐笔/币对清单） | Platform C 现货公开行情查询（api.example.com 公开 REST，免鉴权）——快速查币价 / K线 / 盘口 / 成交 / 币对清单。 |
| `impact-check.sh` | 影响检测 | Scene Change Impact Check |
| `md_to_confluence.py` | 推 Confluence | Push a Markdown file to Confluence as a child page, wrapped in the Markdown macro. |
| `nav_confluence.py` | 不知道 pageId/URL 定位页面 | Confluence 页面导航：不知道 pageId/URL 时按标题定位页面、按父页看子页树。 |
| `pack_for_opus.py` | 打包工作区 | 把工作区按 scope 任意范围打包成单文件 markdown（外部 review / 离线分享 / 备份），包装 repomix CLI。 |
| `publish.sh` | 发 vercel/分享 | publish.sh — 把 deliverables 下的 HTML 发布到 ~/pm-deliverables (Vercel) |
| `pull_meeting_notes.py` | 会议纪要/拉纪要 | 从钉钉闪记拉取会议纪要到项目 inputs/ 目录。 |
| `slack.py` | Slack 消息 | Slack CLI —— 调用 Slack MCP，不加载 MCP server 到 Claude Code。 |
| `sync_hx_status.py` | 火效 delta 状态/上线日期同步（火效为权威源，回写本地状态 + 排期行） | 火效 → 本地 delta 状态/上线日期同步（火效是唯一权威源，本地是缓存投影）。 |
| `sync_pools.sh` | 需求池 | 一键刷新两个需求池 md（增长 + 体验专项） |
| `youshu_cli.py` | 有数报告/BI 链接 | 网易有数（YouData）报告下载 CLI |

### 校验 / lint（check_*）

| 脚本 | 快捷路由 | 职责 |
|------|---------|------|
| `check_baseline_fresh.py` | — | baseline PRD 新鲜度校验（文档集模型承重不变量的 definition-of-done）。 |
| `check_bullet_density.py` | — | bullet / 段落挤话检测（AI 味「挤话一团」维度）。 |
| `check_fork_drift.py` | — | 同源脚本副本漂移登记（源头改了、脱敏副本没跟上的可见化）。 |
| `check_generator_docstring.py` | — | 项目生成脚本 docstring 自证充分性检查（轻量 lint）。 |
| `check_learned_rules.py` | — | LEARNED.md 已沉淀规则的硬阻断检查器（按文件类型分发）。 |
| `check_plain_language.py` | — | 产出物「讲人话」自检 — 全 PM-WORKSPACE 唯一规则源（新）。 |
| `check_rule_version_drift.py` | — | 规则版本 drift 校验 — 验产物声明的骨架版本是否落后于当前规则版本。 |
| `check_rule_volume.py` | — | 规则层体积棘轮 —— 逐文件上限，只降不升，升须论证。 |
| `check_staged_large_files.py` | — | git staged 文件体检 — pre-commit 阻断超大文件 + project 本地源素材入库（warn / block 两级，阈值走 env var）。 |
| `check_static_chapter.py` | — | 真相源静态章写作纪律 lint（baseline 模块章 / 现状章 / scene-list）。 |
| `check_ui_annotation.py` | — | 渲染 UI 屏内禁开发注解 — ui-annotation-gate 入口。 |

### 分析（analyze_*）

| 脚本 | 快捷路由 | 职责 |
|------|---------|------|
| `analyze_gate_funnel.py` | — | 闸门漏斗分析 — 按 session 把 block 配对 resolved，量化「闸门在帮人还是在烦人」。 |
| `analyze_term_hits.py` | — | 词表命中率分析 — 反查 usage.jsonl 的 hits_words，报死词 / 漏收 / 高频。 |

### 同步（sync_*）

| 脚本 | 快捷路由 | 职责 |
|------|---------|------|
| `sync_growth_demand_pool.py` | — | 增长需求池同步 — 走 Google Sheets API（Service Account），按 PM 列筛选 Felix 行。 |
| `sync_ux_demand_pool.py` | — | 体验专项需求池同步 — Google Sheets API（Service Account），按业务规则筛选 Felix 工区。 |

### 其他工具

| 脚本 | 快捷路由 | 职责 |
|------|---------|------|
| `confluence_api.py` | — | Confluence REST 透传原语：任意端点直接调，不写专用脚本。 |
| `dump_term_inventory.py` | — | 词表成员清单快照 — 扫三类异构词表导出统一 JSON。 |
| `gate_health.py` | — | Gate 遥测健康度 —— 让 usage.jsonl 反过来管住 gate 名册。 |
| `gen_hooks_readme.py` | — | 生成 .claude/hooks/README.md —— 当前 hook 清单（零腐化，自动从 settings + 文件提取）。 |
| `gen_scripts_readme.py` | — | 生成 scripts/README.md —— 当前 scripts 清单（零腐化，自动从文件 + CLAUDE.md 提取）。 |
| `learned_stats.py` | — | LEARNED.md 教训→规则转化视图。 |
| `with_server.py` | — | Start one or more servers, wait for them to be ready, run a command, then clean up. |

### Shell 工具（.sh）

| 脚本 | 快捷路由 | 职责 |
|------|---------|------|
| `audit-fast.sh` | — | audit-fast.sh — PostToolUse 快速自检（< 1s） |
| `net_retry.sh` | — | 外网下载降级 wrapper：直连失败且非国内域名时自动加代理重试一次。 |
| `proxy_env.sh` | — | 代理模式判定（单一实现；策略源 = .claude/runbooks/proxy-fallback.md） |
| `toggle-mcp.sh` | — | toggle-mcp.sh — 按需启用/禁用 MCP server，省上下文 token |
| `version-bump.sh` | — | Version Bump Script |

## 共享层（scripts/lib/）

**voice-checks 规则层（human-voice-rules 四层镜像）**

| 模块 | 职责 |
|------|------|
| `banned_terms.py` | 禁词 / 内部锚点 / AI slop 真相源。 |
| `business_voice.py` | 跨产物「描述当前态」铁律 - 业务话语层 PATTERN（后端字段 / 函数 API / 章节号 / 技术黑名单）。 |
| `changelog_residue.py` | 跨产物「描述当前态」铁律 - 时间态层 PATTERN（修订痕迹 / 决策号引用 / from-to 迁移）。 |
| `thinking_process.py` | 跨产物「描述当前态」铁律 - 设计动机层 PATTERN（评审心路 / 元注解）。 |
| `ui_visual.py` | 跨产物「描述当前态」铁律 - UI 视觉层 PATTERN（px / hex / 字体 / ms / CSS / HTML 属性）。 |
| `ui_jargon.py` | UI 组件 / 交互 / 视觉术语黑名单（PM 越界）。 |
| `ui_annotation.py` | 渲染 UI 屏内「开发注解」检测 — 防止开发把注解误读为真实文案。 |
| `run_voice_checks.py` | 统一 voice-checks 入口 — 给 check_proto.sh / check_imap.sh 调用。 |
| `visible_text.py` | blacklist 模式抽取 HTML 可见文本节点。 |
| `tech_jargon/` | 按 domain 加载技术词表，命中即视为「描述当前态」违规。 |

**HTML 生成 / 检查**

| 模块 | 职责 |
|------|------|
| `html_basics.py` | HTML 产出物基础结构检查 - FILL 占位 / HTML 闭合 / 字体 CJK 优先顺序。 |
| `html_builder.py` | HTML 骨架生成共享工具。 |
| `html_components.py` | 逐 Scene 组件计数（IMAP 专项）。 |
| `md_to_html.py` | md_to_html.py — 把 md 转成带 "Copy for LLM" 按钮的自包含 HTML |

**外部服务封装**

| 模块 | 职责 |
|------|------|
| `confluence.py` | Confluence REST API 共享模块。 |
| `confluence_storage.py` | Confluence storage XML 图片语法读写共享层。 |
| `google_sheets.py` | Google Sheets API 薄封装（Service Account）。 |
| `demand_pool_base.py` | 需求池 Google Sheets 同步公共基类。 |

**其他**

| 模块 | 职责 |
|------|------|
| `anchor_patterns.py` | 章节 / §小节锚点正则的单一真相源。 |
| `confluence_md.py` | Markdown → Confluence storage XML 渲染层（md_to_confluence 写入端拆分）。 |
| `corpus_tokens.py` | 审核语料「命中内容」列的拆词口径（多词合写拆分）。 |
| `diagram_text.py` | 从 .drawio / .mmd 抽取可扫描的自然语言文本（跳过 XML / mermaid 语法噪音）。 |
| `env_refs.py` | `.env` 加载 + `${VAR}` 引用展开。 |
| `icons.py` | 工作区共享 SVG 图标库（Feather 风格线性 icon + Platform C 品牌 logo + 头像占位）。 |
| `json_out.py` | lint 命中明细导出 JSON（供 post-checks 取命中词做词表防腐化埋点）。 |
| `lint_exempt.py` | 行文类 lint 的产物豁免判定（规则数据见同目录 lint_exempt.txt）。 |
| `oauth_keychain.py` | Keychain 凭据 JSON 读写（security 命令包装）。 |
| `path_skip.py` | 产物 lint 的跳过规则（二进制 / 资源后缀 + 非内容目录段）。 |
| `proto_reachability.py` | 原型页面可达性 — 检出「页面存在但点不到」与「跳转指向不存在的页面」。 |
| `repo.py` | pm-workspace 仓库根定位。 |
| `route_log.py` | 快捷路由脚本调用埋点 - 写入 .claude/logs/usage.jsonl。 |
| `sa_metrics.py` | 神策数值口径：API 返回的负值（如 -1）是稀疏漏斗「无基数」哨兵，统一判 None。 |
| `scene_match.py` | 场景编号严格匹配 + 父子覆盖 + scene-list 抽取。 |
| `skill_log.py` | Skill 完成/失败埋点 - 写入 .claude/logs/usage.jsonl。 |
| `thresholds.py` | 阈值配置 Python 加载器。 |
| `truth_source.py` | 产品线真相源统一解析器。 |
