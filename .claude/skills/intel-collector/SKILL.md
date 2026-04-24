<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: intel-collector
description: >
  当用户提到「截竞品」「抓情报」「采集 XX」时触发。指明平台 / 媒体名 + 「截一下 / 抓一下」亦触发。
argument-hint: "平台/媒体 + 功能模块，如 binance 活动中心、coindesk 最新报道；可选 --web / --content"
type: tool
output_format: 目录
output_prefix: none
depends_on: []
optional_inputs: []
consumed_by: [competitor-analysis]
scripts:
  capture.py: "单次抓取 — python3 capture.py <url> --output <dir>"
  scheduled-scrape.py: "定时批量抓取 — python3 scheduled-scrape.py <config>"
  intel-cron.sh: "crontab 入口 — 调 scheduled-scrape.py"
---
<!-- pm-ws-canary-236a5364 -->

# 情报采集 Skill（Intel Collector）

## 定位

工具型 Skill，自动采集竞品交易所的 APP/Web 截图、公告内容、以及 Crypto 媒体报道，归档到 `references/competitors/`。
是 competitor-analysis 的上游素材供给工具——先采集，再分析。

支持所有主流 Crypto 交易所（Binance、OKX、Gate、Bybit、MEXC、Bitget、Kucoin 等）及权威 Crypto 媒体（CoinDesk、The Block、BlockBeats、PANews 等），平台列表不封闭。

## 四种模式

| 模式 | 触发词 | 技术 | 产出 |
|------|--------|------|------|
| APP | 「截竞品 XX YY」（默认） | iPhone 镜像 + screencapture | PNG 截图 |
| Web | 「截竞品 XX YY --web」「截网页版」 | browser-use CLI 全页截图 | PNG 截图 |
| Content | 「截竞品 XX 最新公告」「看看 XX 最近活动」「抓 XX 媒体报道」 | WebFetch → browser-use eval 兜底 | Markdown + 可选截图 |
| Interactive | 「翻完 XX 前 N 页」「把 XX 列表全抓下来」 | browser-use CLI 脚本式交互 | PNG / JSON |

> **browser-use 是什么**：本地 CLI 浏览器代理（`uv tool install browser-use` 安装），daemon 常驻 ~50ms 延迟，支持 `--profile` 复用 Chrome 登录态，取代原先 `npx playwright + storage_state` 方案。详见 [browser-use GitHub](https://github.com/browser-use/browser-use)。

> **必须设置环境变量 `BROWSER_USE_DISABLE_EXTENSIONS=1`**：默认 browser-use 会从 `clients2.google.com` 下载 uBlock 等 Chrome 扩展，在国内网络下 daemon 会卡死在下载步骤，60s 超时后 client 报 `TimeoutError`。本 workspace 已在 `.claude/settings.json` 的 `env` 段设置该变量，外部 session 手工执行命令时务必加前缀：`BROWSER_USE_DISABLE_EXTENSIONS=1 browser-use ...`

## References

**必读**（产出前加载）：
- `references/url-registry.json` — 竞品/媒体 URL 注册表，Step 1 查 URL 用
- `.claude/skills/_shared/claude-design/asset-quality-rubric.md` — 素材质量 5-10-2-8 评分规则

**按需**（满足条件才读）：
- `references/competitors/{platform}/index.md` — 已有采集汇总，仅在追加某平台已有模块时查

**执行类**（模型不读，脚本调用）：
- `references/capture.py` — APP 模式采集（iPhone 镜像 + screencapture）
- `references/scheduled-scrape.py` — Content 模式定时任务
- `references/intel-cron.sh` — crontab 包装脚本
- `references/auth/*.json` — 遗留登录态（已废弃，保留供老项目使用，不读）

## 执行步骤

### Step 1: 确认采集目标

> **素材质量门槛**：采集后按 `.claude/skills/_shared/claude-design/asset-quality-rubric.md` 的 5-10-2-8 规则评分，低分素材（< 8/10）输出 stderr warning，不进报告正文。

问用户两个问题（如果参数未提供）：
1. **平台**：哪个交易所或媒体？（不给固定选项，用户说什么就是什么）
2. **模块**：哪个功能模块或内容类型？（如：活动中心、社区、earn、直播间、新闻、访谈等）

确定模式：
- 默认 APP 模式
- 用户说 `--web` / 「网页版」→ Web 模式
- 用户说「公告」「活动列表」「最近动态」「媒体报道」「访谈」「新功能讲解」→ Content 模式
- 用户说「翻页」「前 N 页」「全抓下来」「滚动加载完」→ Interactive 模式

> **媒体源**：url-registry.json 的 `_media` 分区收录了 CoinDesk / The Block / CoinTelegraph / Decrypt / BlockBeats / PANews / Foresight News / ChainCatcher / Odaily / 吴说区块链 等权威 Crypto 媒体。用户说「抓 XX 的报道」「看看 XX 媒体怎么说」时，从 `_media` 查 URL。

创建目标目录（如不存在）：
```bash
mkdir -p references/competitors/{platform}/{module}/
```

### Step 2: 执行采集

#### APP 模式

```bash
python3 .claude/skills/intel-collector/references/capture.py \
  --output-dir /tmp/captures-{timestamp}/
```

脚本运行期间，用户在 iPhone 镜像里翻阅竞品 APP 页面。
脚本自动检测画面变化 → 稳定后截图 → 保存到临时目录。
用户翻完后按 Ctrl+C 结束。

脚本输出 JSON：
```json
{
  "captures": [
    {"path": "/tmp/captures-xxx/001.png", "timestamp": "2026-04-11T23:01:15"},
    {"path": "/tmp/captures-xxx/002.png", "timestamp": "2026-04-11T23:01:28"}
  ],
  "total": 2
}
```

#### Web 模式

1. 读取 `references/url-registry.json` 查找 URL，没有匹配 → 问用户要 URL，获取后追加 registry
2. 选择浏览器模式：
   - **无需登录页**（公告/活动列表/媒体） → 默认 headless Chromium，无需 profile
   - **需要登录态**（后台/付费内容） → 先 `browser-use profile list` 看可用 profile，确认后加 `--profile "{Name}"` 用真实 Chrome
3. 逐 URL 执行（daemon 常驻，多 URL 批处理效率高）：
   ```bash
   # 无登录场景
   browser-use open "{url}" \
     && browser-use wait selector "body" --state visible --timeout 8000 \
     && browser-use screenshot /tmp/captures-{ts}/{n}.png --full

   # 有登录场景（profile 模式）
   browser-use --profile "Default" open "{url}" \
     && browser-use wait selector "main, [role=main], article" --timeout 8000 \
     && browser-use screenshot /tmp/captures-{ts}/{n}.png --full
   ```
4. 所有 URL 采集完后执行 `browser-use close` 释放 daemon

> **迁移说明**：旧方案 `npx playwright + references/auth/{platform}.json` 已废弃。Chrome profile 原生管登录态，不再需要 `references/auth/` 目录；老项目遗留的 auth JSON 可保留但不再使用。

#### Content 模式

1. 读取 `references/url-registry.json` 查找 URL
   - 交易所公告/活动 → 从对应平台分区查找
   - Crypto 媒体 → 从 `_media` 分区查找（key 格式 `{媒体名}-{栏目}`）
2. 抓取策略（降级链）：
   - **首选** `WebFetch`（内置，0 baseline）：prompt 设为「提取文章标题、日期、链接列表，markdown 格式」
   - **SPA 兜底** `browser-use eval`：WebFetch 返回 < 300 字 或含 `<noscript>` 无正文 或标题数为 0 时触发。**禁止直接 `get html` 给 LLM 理解**（tokens 黑洞），必须写 JS 精准抽取：
     ```bash
     browser-use open "{url}" && browser-use wait selector "article, .news-item, [data-item]" --timeout 8000
     browser-use eval "[...document.querySelectorAll('article, .news-item, [data-item]')].slice(0, 20).map(el => ({title: el.querySelector('h1,h2,h3,.title')?.innerText?.trim(), date: el.querySelector('time,.date')?.innerText?.trim(), url: el.querySelector('a')?.href})).filter(x => x.title)"
     ```
     返回 JSON 数组，直接写入 markdown。
   - **最后兜底** `firecrawl_scrape`：仅当 browser-use eval 也失败（页面结构未知/反爬）时，手动启用 firecrawl（`./scripts/toggle-mcp.sh on firecrawl` → 重启 session）。日常流程中不默认触发。
   - 媒体源（CoinDesk / PANews / BlockBeats 等 SSR）通常首选即可；交易所 SPA 页面（OKX / Gate 活动列表）直接走 browser-use eval
3. 解析标题、日期、链接
4. 保存位置：
   - 交易所内容 → `references/competitors/{platform}/announcements/YYYY-MM.md`
   - 媒体内容 → `references/competitors/_media/{媒体名}/YYYY-MM.md`

#### Interactive 模式

适用于分页列表、无限滚动、Tab 切换等需要交互才能拿到完整数据的场景。

1. 明确采集目标（列表 / 分页 / Tab）
2. 打开页面并等 idle：
   ```bash
   browser-use open "{url}" && browser-use wait selector "{主容器 selector}" --timeout 8000
   ```
3. 根据场景选策略：
   - **无限滚动**：循环 `browser-use scroll down --amount 2000` + 短暂 wait，DOM 稳定后退出
   - **分页**：`browser-use eval` 取当前页数据 → `browser-use click <下一页索引>` → 重复
   - **Tab 切换**：`browser-use click <tab 索引>` → `browser-use eval` 取该 Tab 数据
4. 每次循环用 `eval` 写 JS 抽取结构化 JSON（**禁止用 `state`**，见 Token 预算），汇总后写入 markdown/JSON
5. 结束 `browser-use close`

#### Token 预算纪律（所有 browser-use 场景强制）

**目标**：比 firecrawl 更省，核心是避开 `state` 和 `get html` 这两个 token 黑洞。

| 命令 | 单次 tokens | 使用原则 |
|------|-------------|----------|
| `open` / `click` / `input` / `scroll` / `wait` / `close` | ~20 | 随便用 |
| `screenshot <path>` | ~30 | ⭐ 最省，落盘不进 context |
| `eval "JS"` | 200–800 | ⭐ 结构化抽取首选 |
| `state` | 2k–8k | ⚠️ 每 session 最多 2 次，仅用来认入口 |
| `get html --selector` | 1k–15k | ⚠️ 禁止直接给 LLM 理解，只允许落盘后 grep |

硬性规则：

1. **screenshot 优先于 state**：能视觉判断的不读 DOM 结构
2. **eval 优先于 get html**：能用 CSS selector + JS 抽取的不给 LLM 原始 HTML
3. **禁止 `--mcp` 模式**：MCP 会重新吃 schema baseline（~6k），失去 CLI 省钱优势
4. **批处理优先于单次**：多 URL 用 `&&` 链式调用复用 daemon
5. **采集结束必须 `browser-use close`**：释放 daemon，避免后续 session 命中异常状态

### Step 3: Vision 过滤 + 自动命名（APP/Web 模式）

逐张 Read 截图，执行两步判断：

**过滤**：判断是否为交易所/金融类 APP 界面。
- 是 → 进入命名
- 不是（微信、设置页、桌面、其他无关 APP）→ 标记 `[跳过]`

**命名**：识别页面内容，生成文件名。
- 格式：`{功能}-{页面}-{状态}.png`
- 示例：`activity-list-default.png`、`earn-detail-staking.png`、`community-feed-trending.png`

### Step 4: 用户确认

展示结果列表：
```
本次采集 8 张，其中 6 张有效、2 张跳过：

  1. activity-list-default.png        ✅
  2. activity-detail-newbie-task.png   ✅
  3. [跳过] 微信聊天界面
  4. activity-rules-page.png           ✅
  5. signup-confirmation-modal.png     ✅
  6. [跳过] iOS 设置页
  7. activity-share-drawer.png         ✅
  8. activity-success-toast.png        ✅

改名输入序号+新名（如 `1 首页推荐列表`），回车跳过，`ok` 确认全部。
```

### Step 5: 归档

1. 移动有效截图到 `references/competitors/{platform}/{module}/`
2. 更新或创建 `index.md`：

```markdown
# 竞品截图索引

> 截图命名规范：`{功能点}-{状态/场景}.png`
> 更新截图后在此处补充说明。

### {模块名} — {采集日期}

- `activity-list-default.png` — 活动中心首页推荐列表
- `activity-detail-newbie-task.png` — 活动详情-新手任务进度
```

3. 清理临时目录

## 定时采集（Scheduled Scrape）

独立于 Claude Code session 运行的 Playwright 脚本，零 AI Token 消耗。

**脚本位置**：`.claude/skills/intel-collector/references/scheduled-scrape.py`

```bash
# 手动运行
python3 .claude/skills/intel-collector/references/scheduled-scrape.py --all          # 全部
python3 .claude/skills/intel-collector/references/scheduled-scrape.py --platforms okx # 指定平台
python3 .claude/skills/intel-collector/references/scheduled-scrape.py --media        # 仅媒体
```

**crontab**：每月 1 号和 15 号 10:03 自动运行（`references/intel-cron.sh`）

**产出位置**：
- 交易所 → `references/competitors/{platform}/announcements/YYYY-MM-DD.md`
- 媒体 → `references/competitors/_media/{媒体名}/YYYY-MM-DD.md`
- 日志 → `references/competitors/_logs/scrape-YYYYMMDD.log`

**去重**：对比同目录最新 .md，内容无变化则跳过不存。

**提取策略**（按优先级）：
1. JSON-LD 结构化数据（最干净，CoinDesk 等支持）
2. `main` / `article` / `[role="main"]` 容器的 inner_text
3. `body` inner_text 兜底 + 噪音过滤

**已知限制**：Binance 有 WAF/CAPTCHA 反爬，headless 被拦（即使带 storage_state）。其他交易所和媒体均正常。

## 自检清单

- [ ] 截图存入了正确目录 `references/competitors/{platform}/{module}/`
- [ ] 文件命名符合规范 `{功能}-{页面}-{状态}.png`
- [ ] index.md 已更新
- [ ] 临时文件已清理
- [ ] 非竞品截图已跳过（APP 模式）
- [ ] url-registry.json 已追加新 URL（Web/Content 模式，如有新增）
- [ ] Content 模式产出存入正确目录（交易所 → `{platform}/announcements/`，媒体 → `_media/{媒体名}/`）

## Troubleshooting

| 问题 | 原因 | 解决 |
|------|------|------|
| `iPhone镜像` 窗口找不到 | APP 未打开 | 打开 iPhone 镜像 APP |
| 截图全黑 | screencapture 权限问题 | 系统设置 → 隐私 → 屏幕录制 → 允许终端 |
| browser-use 全黑截图 / 超时 | 页面未加载完 | 加 `wait selector` 或 `--timeout 10000` 再 screenshot |
| browser-use daemon 卡死 | 前次 session 异常 | `browser-use close` 清理后重试 |
| WebFetch 返回空 | JS 渲染的 SPA 页面 | 降级走 `browser-use eval` 写 JS 抽取 |
| `eval` 返回空数组 | selector 不匹配或 DOM 结构变 | 先 `screenshot` 看下页面 → 手写更精准的 selector |
| 需要登录的页面 | headless 无登录态 | `browser-use profile list` 选 profile 后加 `--profile "{Name}"` |
| `browser-use open` 卡死 60s 后 `TimeoutError: timed out` | daemon 在下载 Chrome 扩展（uBlock 等），国内网络拉 `clients2.google.com` 被墙 | 设置 `BROWSER_USE_DISABLE_EXTENSIONS=1`（本 workspace 已写入 settings.json env），然后 `pkill -9 -f browser_use; rm -f ~/.browser-use/*.sock ~/.browser-use/*.pid` 重置 |
| `browser-use` 版本过旧（无 `config` / `tunnel` 命令） | uv tool 装了旧版 | `uv tool upgrade browser-use` |
| capture.py 检测不到页面变化 | 页面只有微小动画 | 降低 diff 阈值或手动截（screencapture -l） |
