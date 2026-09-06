# 外部集成 Token 配置

> 本工作区接入了多个外部系统的 MCP server。把 `.mcp.json.example` 复制为 `.mcp.json`，按本文档填入你自己的 token，重启 Claude Code 即可启用。
>
> `.mcp.json` 已在 `.gitignore`，填了真实 token 也不会被提交。

## 启用流程

```bash
cp .mcp.json.example .mcp.json        # 复制模板
# 编辑 .mcp.json，把 REPLACE_ME 换成你自己的 token（按下表）
# 重启 Claude Code，或在会话里 /mcp 重连
```

## Server 清单

模板里共 10 个 server（`dingtalk-a1` 是原作者 A1 录音笔专用，已剔除）。

### 需要你填 token 的

| Server | 接入类型 | 凭证字段 | 哪里申请 |
|--------|---------|---------|---------|
| **figma** | stdio (npx) | `FIGMA_API_KEY` | Figma → Settings → Account → Personal access tokens |
| **sensors** | stdio (node) | `SA_URL` `SA_PROJECT` `SA_API_KEY` `SA_API_SECRET` | 神策后台 → 项目设置 → 数据接入 API |
| **sensors-test** | stdio (node) | 同上（测试环境） | 同上，切到 test 项目 |
| **confluence** | stdio (npx) | `CONF_BASE_URL` `CONF_TOKEN` | Confluence → 头像 → 个人访问令牌（PAT） |
| **zai-mcp-server** | stdio (npx) | `Z_AI_API_KEY`（`Z_AI_MODE` 已填） | 智谱开放平台 bigmodel.cn |
| **web-search-prime** | http | `headers.Authorization: Bearer xxx` | 智谱 BigModel API key |
| **web-reader** | http | 同上 | 同上（与 web-search-prime 共用一个 key） |
| **zread** | http | 同上 | 同上 |
| **dingtalk-doc** | http | url 里的 `?key=` | 钉钉 → 工作台 → MCP 网关，绑定后复制链接 |
| **slack** | http (OAuth) | `oauth.clientId`（keychainKey 本机存） | Slack 首次连接浏览器授权 |

### 各 server 说明

- **sensors / sensors-test**：node 跑本机 SensorsMCPServer。`args` 里的 `/Users/REPLACE_ME/SensorsMCPServer/dist/index.js` 要改成你自己 clone 的路径（`git clone` 神策 MCP server 仓库后指向其 `dist/index.js`）。
- **web-search-prime / web-reader / zread**：都是智谱 BigModel 的 MCP，**共用一个 API key**。在 bigmodel.cn 申请后，三个 server 的 `Bearer` 都填同一个。
- **confluence**：`CONF_BASE_URL` 填你的 Confluence 站点根（如 `https://INTERNAL_URL_REDACTED 保持 `bearer`，`CONF_TOKEN` 填 PAT。
- **slack**：走 OAuth，首次连接会跳浏览器授权，无需手动填长期 token。`keychainKey` 是 macOS keychain 存 token 的键名，本机自动管理。
- **dingtalk-doc**：钉钉 MCP 网关是按人绑定的，你自己在钉钉工作台绑定后拿到的 url 直接整个替换。

## 不配也能跑的功能

| 功能 | 替代方式 |
|------|---------|
| 联网搜索 | Claude Code 内置 WebSearch（模型自带） |
| 网页正文抓取 | 内置 WebFetch |
| GitHub 仓库读码 | `gh` CLI（`brew install gh` 后 `gh api` / `gh repo view`） |
| 图片 OCR | 多模态模型（Sonnet 4.6+ / Opus 4.8+）原生看图 |

**建议**：第一周先只配 `confluence` + `figma`（PM 高频用），跑顺了再扩。

## 安全

- `.mcp.json` 在 `.gitignore` 里，永不提交
- 不要把填好真实 token 的 `.mcp.json` 转发给别人
- token 过期重申，不在脚本/文档里硬编码
- 离职/换机：在各平台后台 revoke 旧 token
