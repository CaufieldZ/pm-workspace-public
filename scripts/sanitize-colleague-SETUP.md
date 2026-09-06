# PM-Workspace 上手指南（Platform C 内部同事版）

> 这是脱敏后的 PM 工作区副本，面向 Platform C 内部同事参考。
> 读完后应能：理解工区结构、配好环境、直接开跑。
>
> 这是**别人搭的工区**，拿来参考方法法和脚手架，按你自己的业务调整，不用照搬。

## 这是什么

一套围绕 Claude Code 搭建的 PM 工作区，把 PM 日常产物（场景清单 / 交互大图 / 原型 / PRD / 周报）沉淀成可复用的 **skill + 脚本 + hook** 体系：

- **skill**：每种产物一个 skill（scene-list / interaction-map / prototype / prd / cross-check ...），定义标准产出流程
- **hook**：写入时自动校验（CJK 标点 / 讲人话 / 规范编号），把规范强制进流程
- **脚本**：打包 / 推 Confluence / 拉数据 / 竞品采集 等工具
- **projects/**：业务文档（baseline / PRD / 场景清单 / 会议纪要），这里是原作者的 Platform C 业务文档，脱敏后保留供参考

总入口和路由规则在根目录 [`CLAUDE.md`](CLAUDE.md) —— **先读它**。

## 〇、前置依赖

```bash
python3 --version   # ≥ 3.10
node --version      # ≥ 18
git --version
brew install gh     # 可选：GitHub CLI（读开源仓库用）
```

任一缺失：macOS `brew install python@3.12 node git`；Ubuntu `sudo apt install -y python3 python3-pip nodejs git`。

## 一、装 Claude Code

```bash
# VSCode 扩展（推荐）
code --install-extension anthropic.claude-code
# 或 CLI：npm install -g @anthropic-ai/claude-code
```

配 Anthropic API key（从 console.anthropic.com 拿）：

```bash
export ANTHROPIC_API_KEY="sk-ant-你的key"
echo 'export ANTHROPIC_API_KEY="sk-ant-你的key"' >> ~/.zshrc
```

## 二、配 MCP 外部集成

工作区接入了 Figma / 神策 / Confluence / 钉钉 / Slack 等外部系统。**完整 token 清单和申请方式见 [`INTEGRATIONS.md`](INTEGRATIONS.md)**。

速通：

```bash
cp .mcp.json.example .mcp.json     # 复制模板
# 编辑 .mcp.json，按 INTEGRATIONS.md 把 REPLACE_ME 换成你的 token
# 重启 Claude Code，或会话内 /mcp 重连
```

**第一周建议先只配 confluence + figma**（PM 高频），跑顺了再扩。

## 三、工区结构速览

```
CLAUDE.md                  ← 工具操作层总入口（路由/启动规则），先读
README.md                  ← 工区总览
.claude/
  skills/                  ← 每种产物一个 skill（scene-list/imap/prototype/prd...）
  hooks/                   ← 写入时自动校验
  runbooks/                ← 判断类操作手册（选型/版本/文件落点...）
  output-styles/           ← 对话风格
scripts/                   ← 工具脚本（打包/推 wiki/拉数据）
projects/                  ← 业务文档（baseline/PRD/scene-list/会议纪要）
```

## 四、快速验证

```bash
# 看有哪些 skill
ls .claude/skills/
# 跑一遍工区健康检查
bash scripts/audit-fast.sh
# 看项目看板
cat .claude/workspace-dashboard.md 2>/dev/null || echo "（dashboard 首次需手动生成）"
```

## 五、怎么用起来

1. **改掉工区主人**：`CLAUDE.md` 开头「工区」段改成你自己（原作者已脱敏为"作者"），业务线范围改成你负责的
2. **清掉别人的业务文档**：`projects/` 下的 baseline/PRD 是原作者的 Platform C 业务，你可以参考结构但别直接用——删掉换成你自己的
3. **按 CLAUDE.md「收到需求路由」跑一遍**：它会根据复杂度引导你走 scene-list → imap → prototype → prd 流程
4. **保留 hook 和 skill**：这是工区的核心价值，跨业务通用

## 六、常见问题

- **hook 报错**：看报错指引，hook 是机械校验，按提示改
- **不知道文件该落哪**：`.claude/runbooks/project-mgmt.md` §文件落点查找表
- **产物间编号规则**：`.claude/runbooks/artifact-conventions.md`
- **脱敏报告**：`SANITIZE-REPORT.md` 列了原作者脱掉了什么、哪些待你确认

---

有疑问翻 `CLAUDE.md` 的「Runbook 触发条件」节，按关键词找到对应手册。
