<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PM-Workspace 同事上手指南

> 本文档面向接手此工作区的 PM 和他们的 Claude Code 实例。
> 读完后应能理解：工作区是什么、每个依赖干什么、一次性配全、直接开跑。

---

## 一、这是什么

PM-Workspace 是一套 **PM 产出物自动化工作台**，运行在 Claude Code（VSCode 插件）里。

它能做的事：
- 用户丢截图/会议纪要/口述需求 → 自动生成 `context.md`（项目唯一真相源）
- 从 context.md 出发，沿固定链路自动产出：场景清单 → 交互大图（HTML）→ 原型（HTML）→ PRD（.docx）
- 19 个标准化 Skill，每个 Skill 的执行流程写在 `.claude/skills/{skill名}/SKILL.md` 里
- 产出物通过 Python 脚本生成，不是手写

**三层架构**（Claude Code 启动时自动加载）：
1. `CLAUDE.md` — 工具层操作规则（并行读取、上下文预算、MCP 调用纪律）
2. `.claude/rules/pm-workflow.md` — PM 方法论（三条链路、场景编号规则、自检清单）
3. `.claude/rules/soul.md` — **个人偏好，需你自己创建**（沟通风格、审美倾向、术语约定）

---

## 二、一次性配置（全部步骤）

### 2.1 安装 VSCode + Claude Code 插件

1. 下载安装 [VSCode](https://code.visualstudio.com)
2. 左侧栏 → 扩展 → 搜索「Claude Code」→ 安装 Anthropic 官方插件

### 2.2 安装 CC Switch（模型网关）

公司内部模型切换工具，每月 $200 额度，走 AI Hub，不用自费。

1. 去 [github.com/farion1231/cc-switch](https://github.com/farion1231/cc-switch) 下载安装
2. 打开后点「添加新供应商」→ 展开「高级选项」→「配置 JSON」
3. 勾选「写入通用配置」，粘贴：

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "<你的 token>",
    "ANTHROPIC_MODEL": "awsclaude4.6",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "awsclaude4.6-haiku",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "awsclaude4.6",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "awsclaude4.6-opus",
    "CLAUDE_CODE_SUBAGENT_MODEL": "awsclaude4.6-haiku",
    "ANTHROPIC_BASE_URL": "https://INTERNAL_URL_REDACTED",
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

**获取 Auth Token**：浏览器打开 `INTERNAL_DOMAIN_REDACTED JSON 里的 `ANTHROPIC_AUTH_TOKEN` 复制粘贴。

**验证**：VSCode 终端里输入「你好」，Claude 回复了就成功。报 401 说明 token 不对。

### 2.3 打开工作区

1. 把拿到的压缩包解压，文件夹重命名为 `pm-workspace`
2. VSCode → File → **Open Folder** → 选中 `pm-workspace` 文件夹
3. **必须打开整个文件夹，不能打开单个文件**，否则 CLAUDE.md 和 19 个 Skill 都不生效

### 2.4 激活防腐化 hook

```bash
git config core.hooksPath .githooks
```

改 Skill/规则文件时 commit 会自动跑一致性检查。只需执行一次。

### 2.5 配置 MCP 服务（外部工具连接）

MCP = Model Context Protocol，让 Claude Code 能调外部工具。本工作区用到 4 个 MCP 服务。

```bash
cp .mcp.json.example .mcp.json
```

然后编辑 `.mcp.json`，把占位符替换成你的密钥：

| 服务 | 配置项 | 去哪拿 | 不配的后果 | 使用它的 Skill |
|------|--------|--------|-----------|---------------|
| **Confluence** | `CONF_TOKEN` | Wiki → 个人设置 → 个人访问令牌 → 创建 | 不能搜内部文档、PRD 无法推送 Wiki | prd, data-report, competitor-analysis |
| **神策 Sensors** | `SA_API_KEY` + `SA_API_SECRET` | 找数据团队申请 | 不能查埋点数据、不能跑数据报告 | data-report |
| | 还需改 `sensors.args` 路径 | 本地安装 SensorsMCPServer 后改成实际路径 | sensors MCP 启动失败 | data-report |
| **Figma** | `FIGMA_API_KEY` | figma.com → Settings → Personal Access Tokens | 不能读设计稿 | 被动触发（用户给 Figma 链接时） |
| **Firecrawl** | `FIRECRAWL_API_KEY` | [firecrawl.dev](https://firecrawl.dev) 注册 | 不能抓网页、竞品页面 | intel-collector, competitor-analysis |

**最低可用**：只配 Confluence 就能跑大部分日常产出物。其他按需补。

### 2.6 配置环境变量

```bash
cp .env.example .env
```

`.env` 里只有一项：`SLACK_BOT_TOKEN`（可选，竞品采集推 Slack 通知用，不需要可留空）。

### 2.7 安装 Python 依赖

```bash
pip install -r requirements.txt
```

每个包对应哪个 Skill：

| 包 | 版本 | 用途 | 依赖它的 Skill |
|----|------|------|---------------|
| `python-docx` | ≥1.1.0 | 生成 .docx 格式 PRD | prd（必须） |
| `defusedxml` | ≥0.7.1 | 防 XML 注入，docx 解析安全层 | docx（必须） |
| `playwright` | ≥1.40.0 | 浏览器自动化截图（PRD 插图） | prd（截图时必须） |
| `matplotlib` | ≥3.9.0 | 数据图表（折线图/柱状图） | data-report（必须） |
| `numpy` | ≥2.0.0 | matplotlib 底层数值计算 | data-report（必须） |

### 2.8 安装 npm 依赖

```bash
npm install
```

当前只有一个：`docx`（npm 包），供 PPT Skill 生成多 Tab 信息文档。

### 2.9 创建个人偏好文件

新建 `.claude/rules/soul.md`，这是你跟 AI 的协作风格约定。模板：

```markdown
# {你的名字} 个人偏好

## 沟通偏好
- 不解释"为什么"除非我问
- 长任务做完再说，不要中途汇报

## 审美倾向
- 原型/大图用深色主题

## 术语补丁
- {你们团队特有的术语约定}
```

没有这个文件不影响功能，但 AI 不会按你的风格来。

---

## 三、一键验证（配完后跑这个）

全部配完后，终端依次执行，确认每一步都没报错：

```bash
# 1. Python 依赖完整性
python3 -c "import docx; import matplotlib; import numpy; import playwright; print('Python deps OK')"

# 2. npm 依赖
node -e "require('docx'); console.log('npm deps OK')"

# 3. git hooks
git config core.hooksPath   # 应输出 .githooks

# 4. MCP 配置文件存在
test -f .mcp.json && echo "MCP config OK" || echo "MISSING: cp .mcp.json.example .mcp.json"

# 5. soul.md 存在
test -f .claude/rules/soul.md && echo "soul.md OK" || echo "MISSING: create .claude/rules/soul.md"
```

5 项全绿就可以开干了。

---

## 四、第一个项目

### 4.1 最快的方式

直接在 Claude Code 终端里说你的需求，比如：
- 「开个项目，我们要做 XX 功能」
- 或直接丢截图 + 「这个功能要做，帮我开个需求」

Claude 会自动建目录、生成 context.md、给你场景建议和链路推荐。

### 4.2 手动建

```bash
mkdir -p projects/your-project/{screenshots,inputs,deliverables/archive}
```

然后按 `/场景清单 your-project` → `/交互大图 your-project` → `/出PRD your-project` 的顺序走。

---

## 五、常用命令速查

| 命令 | 作用 | 前提 |
|------|------|------|
| `/场景清单 {项目名}` | 梳理需求场景 | 有 context.md |
| `/交互大图 {项目名}` | 生成可交互 UI 流程图（HTML） | 有 scene-list.md |
| `/出原型 {项目名}` | 生成高保真可点击原型（HTML） | 有交互大图 |
| `/出PRD {项目名}` | 生成 .docx 格式 PRD | 有交互大图或原型 |
| `/出架构图 {项目名}` | 生成系统架构图（HTML） | 有 scene-list.md |
| `/自检` | 跑全局一致性检查 | 无 |
| `/出测试用例 {项目名}` | 生成 QA 测试用例 | 有 PRD |
| `/截竞品 {平台}` | 抓竞品页面截图 | Firecrawl 已配 |

---

## 六、本拷贝不含的内容

| 目录/文件 | 为什么不含 | 怎么补 |
|-----------|-----------|--------|
| `projects/` | 业务隐私 | 按第四节自建 |
| `references/` | 竞品素材体积大 | 用 `/截竞品` 命令采集 |
| `.claude/rules/soul.md` | 个人偏好 | 按 2.9 节自建 |
| `.claude/skills/intel-collector/references/auth/` | 登录态凭证 | 按 intel-collector SKILL.md 自己抓 |
| `.env` / `.mcp.json` | API 密钥 | 按 2.5-2.6 节配置 |

---

## 七、工作区目录结构

```
pm-workspace/
├── CLAUDE.md                  ← AI 指令入口（模型启动时自动读）
├── SETUP.md                   ← 本文件
├── workspace-context.md       ← 系统全貌（给 AI 的全景参考）
├── requirements.txt           ← Python 依赖
├── package.json               ← npm 依赖
├── .env                       ← 环境变量（从 .env.example 创建）
├── .mcp.json                  ← MCP 服务配置（从 .mcp.json.example 创建）
├── .githooks/pre-commit       ← 提交时自动检查
├── .claude/
│   ├── rules/
│   │   ├── pm-workflow.md     ← PM 方法论（链路/编号/质量约束）
│   │   └── soul.md            ← 你的个人偏好（需自建）
│   ├── skills/                ← 19 个 Skill 定义
│   │   ├── interaction-map/   ← 交互大图
│   │   ├── prototype/         ← 原型
│   │   ├── prd/               ← PRD
│   │   ├── architecture-diagrams/ ← 架构图
│   │   ├── scene-list/        ← 场景清单
│   │   ├── requirement-framework/ ← 需求框架
│   │   ├── competitor-analysis/   ← 竞品分析
│   │   ├── intel-collector/       ← 竞品截图采集
│   │   ├── data-report/           ← 数据报告
│   │   ├── meeting-autopilot/     ← 会议录音/纪要
│   │   ├── test-cases/            ← 测试用例
│   │   ├── behavior-spec/         ← 行为规格（给研发 AI）
│   │   ├── page-structure/        ← 页面结构（给设计 AI）
│   │   ├── cross-check/           ← 产出物一致性校验
│   │   ├── workspace-audit/       ← 全局诊断
│   │   ├── ppt/                   ← 多 Tab 信息文档
│   │   ├── docx/                  ← Word 文档操作
│   │   ├── pdf-tools/             ← PDF 工具
│   │   └── skill-creator/         ← 创建新 Skill
│   ├── commands/              ← 快捷命令
│   ├── chat-templates/        ← context.md 模板 + HTML 产出物模板
│   └── settings.json          ← 项目级权限设置
├── scripts/                   ← 通用工具脚本
│   ├── impact-check.sh        ← 场景编号覆盖检查
│   ├── version-bump.sh        ← 升版归档
│   ├── check_html.sh          ← HTML 产出物验证
│   ├── fill_utils.py          ← 填充脚本工具函数
│   └── inject-canary.sh       ← 版权 canary token 注入
└── projects/                  ← 你的项目（需自建）
    └── {项目名}/
        ├── context.md         ← 项目唯一真相源（九章结构）
        ├── scene-list.md      ← 场景清单（编号锁定）
        ├── screenshots/       ← 截图
        ├── inputs/            ← 原始素材
        ├── scripts/           ← 生成脚本（自动生成）
        └── deliverables/      ← 产出物
            └── archive/       ← 旧版归档
```

---

## 八、问题排查

| 现象 | 原因 | 解决 |
|------|------|------|
| 终端打不开 | 快捷键不对 | Ctrl+\` 或菜单 Terminal → New Terminal |
| 报 401 | Auth Token 不对 | 重新从网关获取，检查内网/VPN |
| Skill 不触发 | 打开的是文件不是文件夹 | File → Open Folder，选整个 pm-workspace |
| MCP 工具不出现 | .mcp.json 没配或 JSON 格式错 | 检查文件存在 + JSON 语法，重启 VSCode |
| `python-docx` 报错 | 没装 Python 依赖 | `pip install -r requirements.txt` |
| commit 被拦截 | 防腐化 hook 检查不通过 | 看报错信息，修完再提交，不要 --no-verify |
| 找不到项目 | 没建 projects/ 目录 | 按第四节建，或让 Claude 自动建 |

搞不定找原作者（Felix）。
