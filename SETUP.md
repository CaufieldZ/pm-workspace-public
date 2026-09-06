<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PM-Workspace 上手指南

> 本文档面向接手此工作区的 PM 和他们的 Claude Code 实例。
> 读完后应能理解：工作区是什么、每个依赖干什么、一次性配全、直接开跑。
>
> **如果你是被另一个 LLM 调用来跑安装的，从下面 §0 开始读，不要读后面 1-9 章**。

---

## 〇、LLM 自动安装（给 AI Agent 看）

> 真人请直接跳到 §一。

**约定**：以下命令分两类——

- 普通 shell 命令：直接顺序执行，每步出错就停下报告，不要瞎猜重试
- **`# HUMAN-REQUIRED:`** 注释开头的步骤：**停下来，让用户在对话里把缺的值告诉你，不要编造 token / API key**

执行环境假设：macOS / Linux / WSL2。Windows 原生 PowerShell 自己换等价命令。

### 0.1 前置检查

```bash
python3 --version    # 需要 ≥ 3.10
node --version       # 需要 ≥ 18
git --version        # 任意版本
```

任一缺失：macOS 用 `brew install python@3.12 node git`；Ubuntu 用 `sudo apt install -y python3 python3-pip nodejs git`。

### 0.2 装 VSCode + Claude Code 扩展

```bash
# macOS
brew install --cask visual-studio-code

# Ubuntu / Debian
sudo snap install code --classic

# 装 Claude Code 扩展（任何平台，VSCode 装完后）
code --install-extension anthropic.claude-code
```

### 0.3 配置 Anthropic API key

CC Switch（GUI 多账号切换工具）对自动化场景没必要，直接走环境变量等价。

```bash
# HUMAN-REQUIRED: 让用户从 console.anthropic.com 拿 API key 后告诉你，替换下面占位
export ANTHROPIC_API_KEY="sk-ant-REPLACE_ME"

# 持久化到 shell 启动文件（按用户实际 shell 选 .zshrc / .bashrc）
echo 'export ANTHROPIC_API_KEY="sk-ant-REPLACE_ME"' >> ~/.zshrc

# 验证：
curl -sS https://api.anthropic.com/v1/models \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" | head -20
# 返回 JSON 含 model 列表 = OK；401 = key 无效，回去问用户重拿
```

如果用户在企业内网走代理网关，额外设 `export ANTHROPIC_BASE_URL="https://your-gateway/api"`，模型 ID 按网关支持的写。

### 0.4 Clone + 装依赖 + 激活 hook

```bash
git clone https://github.com/CaufieldZ/pm-workspace.git
cd pm-workspace

# Python deps（playwright 装完还要再装 chromium）
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium

# Git hooks（pre-commit 跑防腐化审计）
git config core.hooksPath .githooks
```

### 0.5 MCP 配置（可选，跳过也能跑大部分功能）

工作区默认 `.mcp.json` 为空，所有外部集成（wiki / 数据平台 / Figma / 通知）都懒加载。要开任一个：

```bash
# HUMAN-REQUIRED: 让用户告诉你要接哪些外部工具 + 提供对应 token
# 例：要 Confluence wiki → 用户给 CONF_TOKEN + base url
# 例：要 Figma 设计稿 → 用户给 FIGMA_API_KEY

# 编辑 .mcp.json 添加 server 块，结构参考：
cat .claude/runbooks/mcp-config.md | head -100

# 配完后启用：
./scripts/toggle-mcp.sh on confluence
./scripts/toggle-mcp.sh status   # 验证开了哪些
```

如果用户说「先不接外部工具，跑通本地能力就行」，跳过整个 0.5。

### 0.6 验证（machine-checkable）

每一行都应该输出在右边注释的预期，全绿才算装完。任一不符停下来报告，**不要静默继续**。

```bash
python3 -c "import docx, matplotlib, numpy, playwright, bs4, requests, yaml, PIL; print('Python deps OK')"   # → Python deps OK
node --version                                            # → v18+
git config core.hooksPath                                 # → .githooks
test -f .mcp.json && echo "MCP config OK"                 # → MCP config OK
test -f CLAUDE.md && echo "CLAUDE.md OK"                  # → CLAUDE.md OK
ls .claude/runbooks/*.md | wc -l                          # → 13
ls -d .claude/skills/*/ | grep -v _shared | wc -l         # → 12
```

### 0.7 把控制权交回真人

以下事情 LLM 自己做不了，装完上面 0.1-0.6 后明确告诉用户接下来要他做这几件：

1. **打开工作区**：在 VSCode 里 File → Open Folder，选刚 clone 下来的 `pm-workspace` 整个文件夹。**必须打开文件夹，不是单个文件**，否则 12 个 Skill 全部不生效。
2. **重启终端 / source 配置**：让 `ANTHROPIC_API_KEY` 生效。
3. **（可选）写个人偏好**：根目录建 `LEARNED.md`，写沟通风格 / 术语约定 / 审美倾向。每次 session 自动读。
4. **开第一个项目**：在 Claude Code 终端里说「我要做 XX 功能」，让 Claude 帮你建项目目录、生成 context.md、跑场景清单。

### 0.8 装失败的常见原因（自动化场景）

| 现象 | 原因 | 自救 |
|------|------|------|
| `pip install` 超时 / reset | 网络环境（公司代理 / GFW） | 切镜像 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ...` 或看 `.claude/runbooks/proxy-fallback.md` |
| `playwright install` 卡住 | chromium 下载慢 | 先 `export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright`再装 |
| `code --install-extension` 报 command not found | VSCode 命令行工具没注册 | macOS：VSCode 里 Cmd+Shift+P → "Shell Command: Install 'code' command" |
| 0.6 验证 Skill 数 ≠ 12 | clone 不完整或在错误目录 | `pwd` 确认在 pm-workspace 根；重新 clone |

---

## 一、这是什么

PM-Workspace 是一套 **PM 产出物自动化工作台**，运行在 Claude Code（VSCode 插件 / Web / CLI 均可）里。

它能做的事：
- 用户丢截图 / 会议纪要 / 口述需求 → 自动生成 `context.md`（项目唯一真相源）
- 从 context.md 出发，沿固定链路自动产出：场景清单 → 交互大图（HTML）→ 原型（HTML）→ PRD（**md + 本地截图**，推 Wiki 时脚本自动上传）
- **12 个标准化 Skill**，每个 Skill 的执行流程写在 `.claude/skills/{skill}/SKILL.md` 里
- 产出物通过 Python 脚本生成，不是手写

**指令分层**（Claude Code 启动时自动读 `CLAUDE.md`，其他按需 Read）：
1. `CLAUDE.md` — 工具层操作规则（路由、并行 Read、上下文预算、修改入口防误操、MCP 纪律）
2. `.claude/runbooks/*.md` — 13 份按需手册（PM 方法论 / 决策框架 / 项目管理 / git&hooks / MCP / 代理回退 / 技术债等）
3. `LEARNED.md`（根目录，每 session 自动读）+ `.claude/session-state.md`（高风险操作前 checkpoint）
4. `.claude/output-styles/*.md` — 沟通风格

---

## 二、一次性配置（全部步骤）

### 2.1 安装 VSCode + Claude Code 插件

1. 下载安装 [VSCode](https://code.visualstudio.com)
2. 左侧栏 → 扩展 → 搜索「Claude Code」→ 安装 Anthropic 官方插件

### 2.2 安装 CC Switch（模型网关）

CC Switch 是个第三方多供应商切换工具，支持 Anthropic 官方 API、各家代理、企业内网网关。普通用户走 Anthropic 官方就行。

1. 去 [github.com/farion1231/cc-switch](https://github.com/farion1231/cc-switch) 下载安装
2. 打开后点「添加新供应商」→ 展开「高级选项」→「配置 JSON」
3. 勾选「写入通用配置」，粘贴下面任一模板：

**模板 A：Anthropic 官方**

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "<你的 Anthropic API key>",
    "ANTHROPIC_MODEL": "claude-opus-4-7",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4-5-20251001",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-4-6",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-4-7",
    "CLAUDE_CODE_SUBAGENT_MODEL": "claude-haiku-4-5-20251001",
    "MAX_MCP_OUTPUT_TOKENS": "10000",
    "MAX_THINKING_TOKENS": "20000",
    "DISABLE_TELEMETRY": "1",
    "DISABLE_AUTOUPDATER": "1",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING": "1",
    "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1"
  },
  "includeCoAuthoredBy": false
}
```

**模板 B：企业内网网关**（公司有 Claude API 代理时）

在模板 A 基础上加 `"ANTHROPIC_BASE_URL": "https://your-internal-gateway/api"`，模型 ID 按网关支持的名称写（常见为透传官方名，部分网关用 `aws*` / `bedrock-*` 前缀）。

**API key 哪里拿**：
- 个人：[console.anthropic.com](https://console.anthropic.com) 注册后 API Keys 页面
- 企业：找内部 AI 网关管理员要 token + base_url

**验证**：VSCode 终端里输入「你好」，Claude 回复了就成功。报 401 说明 token 不对。

### 2.3 打开工作区

1. 把仓库 clone 或解压到本地，文件夹建议命名 `pm-workspace`
2. VSCode → File → **Open Folder** → 选中 `pm-workspace` 文件夹
3. **必须打开整个文件夹，不能打开单个文件**，否则 CLAUDE.md 和 12 个 Skill 都不生效

### 2.4 激活防腐化 hook

```bash
git config core.hooksPath .githooks
```

改 Skill / 规则文件 / 产出物时 commit 会自动跑一致性检查（pre-commit + post-commit 都已就位）。只需执行一次。

### 2.5 配置 MCP 服务（外部工具连接）

MCP = Model Context Protocol，让 Claude Code 能调外部工具。**本工作区默认 `.mcp.json` 为空（全关），需要哪个手动开**——MCP server 加载会吃 token，所以默认懒加载。

启停命令：

```bash
./scripts/toggle-mcp.sh status            # 看当前开了哪些
./scripts/toggle-mcp.sh on confluence     # 开某个
./scripts/toggle-mcp.sh off figma         # 关某个
```

工作区**示例**集成的 4 类外部工具（任一可换成你团队在用的）：

| 类别 | 示例集成 | 不配的后果 | 使用它的 Skill |
|------|---------|-----------|---------------|
| **Wiki / 知识库** | Confluence（示例：Notion / 飞书文档 / Outline 同理） | 不能搜内部文档、PRD 无法推 Wiki | prd, data-report, competitor-analysis |
| **数据平台**（选装）| 神策 Sensors（示例：GA / Amplitude / Mixpanel 同理） | 不能查埋点、跑不了 data-report | data-report |
| **设计稿** | Figma | 不能读设计稿 | 被动触发（用户给链接时） |
| **联网搜索** | web-search-prime（无 WebSearch 模型用） | 内置 WebSearch 兜底，但中文站点效果差 | 所有需联网检索的 Skill |

详细配置走 `.claude/runbooks/mcp-config.md`。

**最低可用**：只开 Wiki 类（Confluence 或同类）就能跑大部分日常产出物。其他按需补。结构参考 mcp-config runbook 自己写 `.mcp.json`，没有 `.mcp.json.example`。

### 2.6 环境变量（按需）

工作区不强制 `.env`。如果用了通知集成（Slack / 飞书 / 钉钉 / 企微机器人），把 token 直接 export 到 shell 或写进 `~/.zshrc`：

```bash
export SLACK_BOT_TOKEN="xoxb-..."   # 示例：竞品采集推 Slack 通知用，不需要可省
```

### 2.7 安装 Python 依赖

```bash
pip install -r requirements.txt
```

12 个包，按用途分组：

| 包 | 用途 | 依赖它的 Skill / 脚本 |
|----|------|---------------------|
| `python-docx` ≥1.1.0 | docx 兼容 + ppt 兜底 | ppt / 历史归档 |
| `playwright` ≥1.40.0 | 浏览器自动化截图（PRD / 原型校验） | prd / prototype |
| `matplotlib` ≥3.9.0 | 数据图表（折线 / 柱状） | data-report |
| `numpy` ≥2.0.0 | matplotlib 底层 | data-report |
| `Pillow` ≥10.0.0 | 图片裁剪 / 拼接 | prd / competitor-analysis |
| `beautifulsoup4` ≥4.12.0 | HTML 产出物结构校验 | imap / proto 自检 |
| `markdown` ≥3.5.0 | md → html 渲染（推 Wiki 前转换） | md_to_confluence |
| `requests` ≥2.31.0 | REST 调用（Wiki / 通知 / 数据平台） | 几乎所有外部集成脚本 |
| `PyYAML` ≥6.0.0 | thresholds.yaml 等配置读取 | scripts/lib/thresholds.py |
| `humanize` ≥4.9.0 | 时间 / 文件大小可读化 | dashboard.py |
| `google-api-python-client` ≥2.100.0 | BI / Sheets 拉数（按需）| data-report / sync_pools |
| `google-auth` ≥2.23.0 | Google API 鉴权（按需）| 同上 |

不需要 Google / BI 集成时，最后两个可以从 requirements.txt 注释掉。

### 2.8 npm 依赖

```bash
npm install
```

`package.json` 目前只校验 Node ≥18，无运行时 npm 包。预留给后续 Skill 接入 puppeteer / mermaid-cli 等场景。

### 2.9 创建个人偏好文件（可选）

工作区不再使用 `.claude/rules/soul.md`。个人沟通风格 / 审美 / 术语补丁现在两条路：

- **轻量**：直接编辑根目录 `LEARNED.md`（每 session 自动读，存在即生效）
- **重型**：在 `.claude/output-styles/` 下新建自己的 style 文件，参考已有样例

不配也能跑，只是 AI 不会按你的风格来。

---

## 三、一键验证（配完后跑这个）

```bash
# 1. Python 依赖完整性
python3 -c "import docx, matplotlib, numpy, playwright, bs4, requests, yaml, PIL; print('Python deps OK')"

# 2. Node 版本
node --version    # 应 ≥ v18

# 3. git hooks
git config core.hooksPath    # 应输出 .githooks

# 4. MCP 配置文件存在
test -f .mcp.json && echo "MCP config OK" || echo "MISSING: 手动新建 .mcp.json"

# 5. CLAUDE.md / runbooks 完整
test -f CLAUDE.md && ls .claude/runbooks/*.md | wc -l    # 应输出 13

# 6. Skill 完整
ls -d .claude/skills/*/ | grep -v _shared | wc -l    # 应输出 12
```

全绿就开干。

---

## 四、第一个项目

### 4.1 最快的方式

直接在 Claude Code 终端里说你的需求，比如：
- 「开个项目，我们要做 XX 功能」
- 或直接丢截图 + 「这个功能要做，帮我开个需求」

Claude 会自动建目录、生成 context.md、给你场景建议和链路推荐。

### 4.2 手动建

项目目录是 **两层结构**：`projects/{产品线}/{项目}/`。产品线由你自己定义（例如按业务线分 `web / mobile / backend`，或按产品分 `product-a / product-b`），顶级方案型 / 基建项目可直挂 `projects/` 下。

```bash
mkdir -p projects/your-line/your-project/{inputs/{meetings,docs,figma,raw,competitors},deliverables/{archive,assets}}
touch projects/your-line/your-project/context.md
```

子目录用途：
- `inputs/meetings/` — 会议纪要落点
- `inputs/docs/` — 永久参考文档（接口 spec / 技术方案 / 拉取的 wiki 页面）
- `inputs/figma/` — Figma 节点 / 截图
- `inputs/raw/` — 用户手丢的原始素材（pdf / docx / 未分类截图）
- `inputs/competitors/{平台}/` — 竞品截图
- `deliverables/` — 产物（前缀 `prd- / imap- / proto- / arch- / ppt- / flow- / report-`）
- `deliverables/assets/` — 产物图片（PRD 截图 / 架构图 / 流程图源文件）
- `deliverables/archive/` — 老版本（grep 时用 `--exclude-dir=archive`）

完整规范见 `.claude/runbooks/project-mgmt.md`。

然后按「场景清单 → 交互大图 → 原型 → 出 PRD」的顺序走（详见下表）。

---

## 五、常用命令速查

斜杠命令不是必须，自然语言一样能触发。下面是高频路径：

| 触发 | 作用 | 前提 |
|------|------|------|
| 「场景清单 / 梳理需求」 | 梳理需求场景，建编号锁 | 有 context.md |
| 「交互大图 / IMAP」 | 生成可交互 UI 流程图（HTML） | 有 scene-list.md |
| 「原型 / prototype」 | 生成高保真可点击原型（HTML） | 有 IMAP |
| 「PRD / 需求文档」 | 生成 md 版 PRD + 本地截图 | 有 IMAP 或原型 |
| 「架构图 / 技术架构」 | 生成系统架构图(HTML)| 有 scene-list.md |
| 「流程图 / 泳道图 / 状态机」 | 输出 .svg + .png(mermaid / drawio 自选) | 任意 |
| 「拉通检查 / 校验一致性 / cross-check」 | PRD 完成前最终一致性校验 | 有 PRD |
| 「PPT / 宣讲材料 / SOP 手册」 | HTML 多 Tab 信息文档 | 任意 |
| 「竞品分析 / 截一下 XX」 | 竞品采集 + 调研 | 任意 |
| 「数据报告 / 周报 / 月报」 | 数据平台拉取 + 图表 + 文档 | 有数据源 |
| 「MRD 评审 / 该不该做」 | 市场 + UE 判断 + 评审意见 | 有需求草案 |
| 「审计 / 诊断」 | workspace-audit Phase 1 脚本 + Phase 2 模型推理 | 任意 |

---

## 六、本拷贝不含的内容

| 目录 / 文件 | 为什么不含 | 怎么补 |
|-----------|-----------|--------|
| `projects/` | 业务隐私 | 按第四节自建 |
| `LEARNED.md` | 个人沉淀 | 自建（按需）|
| `.mcp.json` | API 密钥 | 按 2.5 节配，从空开始填 |
| `.claude/skills/competitor-analysis/assets/auth/` | 登录态凭证 | 按 competitor-analysis SKILL.md「采集模式」自己抓 |
| `inputs/competitors/` 历史素材 | 体积大 + 版权 | 用竞品采集 Skill 现抓 |

---

## 七、工作区目录结构

```
pm-workspace/
├── CLAUDE.md                         ← AI 指令入口（启动自动读）
├── LEARNED.md                        ← 个人沉淀，session 自动读
├── SETUP.md                          ← 本文件
├── requirements.txt                  ← Python 依赖
├── package.json                      ← Node 版本约束
├── .mcp.json                         ← MCP 服务配置（默认空，按需开）
├── .githooks/                        ← pre-commit + post-commit
├── .claude/
│   ├── runbooks/                     ← 13 份按需手册
│   │   ├── pm-methodology.md             ← PM 方法论（链路 / 决策段 / 逻辑拼图）
│   │   ├── artifact-conventions.md       ← 产物编号 + 静态章规范
│   │   ├── cli-cheatsheet.md             ← CLI 速查
│   │   ├── decision-framework.md         ← 方案选型 + 竞品对照
│   │   ├── git-and-hooks.md              ← commit / 推 wiki / 新写 hook
│   │   ├── html-build-split.md           ← HTML > 1500 行拆分规则
│   │   ├── human-voice-rules.md          ← 人话规则（PRD §4.x「理由」边界）
│   │   ├── mcp-config.md                 ← MCP 配置策略
│   │   ├── project-mgmt.md               ← 项目落点 / 命名 / 迁移
│   │   ├── proxy-fallback.md             ← pip / npm 网络回退
│   │   ├── skill-conventions.md          ← Skill 命名 / frontmatter / 产物前缀
│   │   ├── tech-debt-backlog.md          ← 技术债待办
│   │   └── version-bump.md               ← 升版 / 改场景 / 改术语
│   ├── skills/                       ← 12 个 Skill 定义（+ _shared 公共）
│   │   ├── scene-list/                   ← 场景清单
│   │   ├── interaction-map/              ← 交互大图（IMAP）
│   │   ├── prototype/                    ← 可交互原型
│   │   ├── prd/                          ← PRD（md 版）
│   │   ├── architecture-diagrams/        ← 架构图
│   │   ├── flowchart/                    ← 流程 / 泳道 / 状态机
│   │   ├── ppt/                          ← 多 Tab 信息文档
│   │   ├── competitor-analysis/          ← 竞品分析 + 情报采集
│   │   ├── data-report/                  ← 数据报告
│   │   ├── mrd-review/                   ← MRD 评审
│   │   ├── cross-check/                  ← 产出物一致性校验
│   │   ├── workspace-audit/              ← 全局诊断
│   │   └── _shared/                      ← 跨 skill 共享规则 / fixtures
│   ├── chat-templates/               ← context.md / IMAP / 原型 / PPT 模板
│   ├── output-styles/                ← 沟通风格
│   ├── commands/                     ← 慢命令
│   ├── workspace-dashboard.md        ← 项目看板（Stop hook 6h 刷新）
│   ├── session-state.md              ← 高风险操作 checkpoint
│   └── settings.json                 ← 项目级权限
├── scripts/                          ← 通用工具脚本（25 个，详见第八节）
└── projects/                         ← 你的项目（自建，两层产品线 / 项目）
    └── {产品线}/{项目}/
        ├── context.md                ← 项目唯一真相源
        ├── scene-list.md             ← 场景清单（编号锁）
        ├── inputs/                   ← meetings / docs / figma / raw / competitors
        ├── deliverables/             ← 产物（prd- / imap- / proto- / arch- 前缀）
        │   ├── assets/               ← 产物图片
        │   └── archive/              ← 旧版归档
        └── scripts/                  ← 项目级生成脚本（按需）
```

废弃路径：`projects/{项目}/screenshots/`、`inputs/assets/` —— 已迁移到 `inputs/raw/` 或 `deliverables/assets/`。

---

## 八、脚本速查

`scripts/` 下共 **25 个脚本**，按用途分组。**Claude Code 大部分场景会自动调用**，下表给人和模型一份参考。

外部数据源相关脚本是**示例集成**——内置实现绑定了特定厂商（钉钉闪记 / Confluence / 神策 / 有数 BI / Slack），但接口都是 REST，自己换 wiki / 数据平台 / 通知工具时改对应脚本里的 base_url + auth 头就行。

### 8.1 外部数据源（示例集成，按需替换）

| 脚本 | 作用 | 当前绑定 / 替换提示 |
|------|------|---------------------|
| `pull_meeting_notes.py` | 拉会议纪要到 `inputs/meetings/`，剥离转写原文 | 钉钉闪记 → 飞书妙记 / Otter.ai / Notion 同接口模式 |
| `fetch_confluence.py` | 拉 wiki 页面（直调 REST） | Confluence → Notion / 飞书文档 改 API endpoint |
| `md_to_confluence.py` | md 推到 wiki，自动上传截图 | 同上 |
| `fetch_figma.py` | 拉 Figma 节点 / 下载截图 | Figma 通用 |
| `call_mcp.py` | 兜底直调任何 MCP server | 通用 |
| `toggle-mcp.sh` | 启停 MCP server | 通用 |
| `slack.py` | 推通知 / 拉历史 | Slack → 飞书 / 钉钉 / 企微机器人替换 webhook |
| `youshu_cli.py` | BI 报告链接生成 / 数据拉取 | 有数 BI → Metabase / Superset / Looker 改 API |

### 8.2 项目状态管理

| 脚本 | 作用 | 典型用法 |
|------|------|---------|
| `read_context_section.py` | context.md > 300 行按章节读 | `--toc` / `--sections "..."` / `--grep` |
| `impact-check.sh` | 对比 scene-list 和 deliverables 找过期产出 | `bash scripts/impact-check.sh {项目}` |
| `version-bump.sh` | 自动归档旧版 + 改名 + 写 context.md | `bash scripts/version-bump.sh {项目}` |
| `dashboard.py` | 强刷项目看板（默认 Stop hook 6h 自动） | `python3 scripts/dashboard.py` |
| `sync_pools.sh` | 同步需求池到本地（示例：Google Sheets） | 详见 cli-cheatsheet |

### 8.3 产出物质量

| 脚本 | 作用 |
|------|------|
| `check_cjk_punct.py` | CJK 旁半角标点违规扫描（hook 自动跑），`--fix` 自动修复 |
| `check_context_static.py` | context.md 静态章「四不」校验（hook 自动跑） |
| `check_plain_language.py` | 人话规则扫描（产物里的 PM 黑话） |
| `check_staged_large_files.py` | commit 大文件拦截 |
| `check_learned_rules.py` | LEARNED.md 规则一致性校验 |
| `with_server.py` | 托管 dev server 跑 Playwright 自动化 |
| `audit-fast.sh` | PostToolUse hook 自动跑，写完产出物即时校验 |
| `publish.sh` | 产出物发 vercel 分享（`--list` / `--unpublish`） |
| `doc_to_md.py` | pdf / docx / pptx / xlsx 一键转 md，支持 `--batch` |
| `pack_for_opus.py` | 打包工作区给外部 LLM（脱敏 + 压缩） |

### 8.4 内部模块（无需手动调用）

| 路径 | 作用 |
|------|------|
| `lib/` | Python 共享模块（REST 封装 / HTML 构建 / 场景编号匹配 / HTML 可见文本抽取 / 技术词表 / UI 越界词 / 阈值表 / md 渲染等） |
| `archive/` | 历史脚本归档 |

### 8.5 各 Skill 自带脚本

每个 Skill 在 `.claude/skills/{skill}/scripts/` 下还有专属脚本（如 `prd/scripts/gen_prd_skeleton.py`、`prd/scripts/check_prd_md.sh`、`interaction-map/scripts/check_imap.sh`、`prototype/scripts/check_proto.sh`、`scene-list/scripts/render_scene_list.py`）。具体调用方式看对应 SKILL.md 的 frontmatter `scripts` 字段。

---

## 九、问题排查

| 现象 | 原因 | 解决 |
|------|------|------|
| 终端打不开 | 快捷键不对 | Ctrl+\` 或菜单 Terminal → New Terminal |
| 报 401 | API key 不对 | 重新从 Anthropic console 或公司网关获取 |
| Skill 不触发 | 打开的是文件不是文件夹 | File → Open Folder，选整个 pm-workspace |
| MCP 工具不出现 | `.mcp.json` 没启或 JSON 格式错 | `./scripts/toggle-mcp.sh status` 检查，重启 VSCode |
| `pip install` 报 timeout / reset | 网络代理 | 看 `.claude/runbooks/proxy-fallback.md` |
| commit 被拦截 | 防腐化 hook 检查不通过 | 看报错信息，修完再提交，**不要 --no-verify** |
| 找不到项目 | 没建 `projects/{产品线}/{项目}/` 两层结构 | 按第四节建，或让 Claude 自动建 |
| context.md 越读越慢 | 文件 > 300 行 | 用 `scripts/read_context_section.py` 按章节读 |
| 写产出物报警告 | hook 提示静态章四不 / CJK 标点 / 人话规则 | 看 `.claude/runbooks/artifact-conventions.md` + `human-voice-rules.md` |
| Skill 改完想加 hook | 配置入口 | `.claude/settings.json` + `.githooks/`，参考 `runbooks/git-and-hooks.md` |

搞不定欢迎提 issue。
