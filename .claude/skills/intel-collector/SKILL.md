<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: intel-collector
description: >
  当用户提到「截竞品」「竞品截图」「抓竞品页面」「抓情报」「采集 XX」「capture competitor」时触发。
  也在用户说「截 XX 的 YY」「看看 XX 最近动态」「抓 XX 的报道」时触发。
  即使用户只说「截一下」「抓一下」并指明平台或媒体也应触发。
argument-hint: "平台/媒体 + 功能模块，如 binance 活动中心、coindesk 最新报道；可选 --web / --content"
type: tool
output_format: 目录
output_prefix: —
depends_on: []
optional_inputs: []
consumed_by: [competitor-analysis]
---
<!-- pm-ws-canary-236a5364 -->

# 情报采集 Skill（Intel Collector）

## 定位

工具型 Skill，自动采集竞品交易所的 APP/Web 截图、公告内容、以及 Crypto 媒体报道，归档到 `references/competitors/`。
是 competitor-analysis 的上游素材供给工具——先采集，再分析。

支持所有主流 Crypto 交易所（Binance、OKX、Gate、Bybit、MEXC、Bitget、Kucoin 等）及权威 Crypto 媒体（CoinDesk、The Block、BlockBeats、PANews 等），平台列表不封闭。

## 三种模式

| 模式 | 触发词 | 技术 | 产出 |
|------|--------|------|------|
| APP | 「截竞品 XX YY」（默认） | iPhone 镜像 + screencapture | PNG 截图 |
| Web | 「截竞品 XX YY --web」「截网页版」 | Playwright 桌面端全页截图 | PNG 截图 |
| Content | 「截竞品 XX 最新公告」「看看 XX 最近活动」「抓 XX 媒体报道」 | Firecrawl MCP | Markdown + 可选截图 |

## 执行步骤

### Step 1: 确认采集目标

问用户两个问题（如果参数未提供）：
1. **平台**：哪个交易所或媒体？（不给固定选项，用户说什么就是什么）
2. **模块**：哪个功能模块或内容类型？（如：活动中心、社区、earn、直播间、新闻、访谈等）

确定模式：
- 默认 APP 模式
- 用户说 `--web` / 「网页版」→ Web 模式
- 用户说「公告」「活动列表」「最近动态」「媒体报道」「访谈」「新功能讲解」→ Content 模式

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

1. 读取 `references/url-registry.json` 查找 URL
2. 没有匹配 → 问用户要 URL，获取后追加到 registry
3. 检查 `references/auth/{platform}.json` 是否存在登录态
   - 有 → 加 `--load-storage` 参数
   - 无且页面需登录 → 提示用户执行一次性登录：
     ```bash
     npx playwright open --save-storage=references/auth/{platform}.json "{登录页URL}"
     ```
     用户登录完关闭浏览器即可保存
4. 逐 URL 执行：
```bash
npx playwright screenshot --load-storage=references/auth/{platform}.json --viewport-size="1440,900" --wait-for-timeout=5000 --full-page "{url}" /tmp/captures-{ts}/{n}.png
```
无登录态文件时省略 `--load-storage` 参数。

#### Content 模式

1. 读取 `references/url-registry.json` 查找 URL
   - 交易所公告/活动 → 从对应平台分区查找
   - Crypto 媒体 → 从 `_media` 分区查找（key 格式 `{媒体名}-{栏目}`）
2. 抓取策略（省 firecrawl 配额）：
   - **首选**：调 `WebFetch`（内置），prompt 设为「提取文章标题、日期、链接列表，markdown 格式」
   - **降级**：若返回内容 < 300 字或明显为空 HTML（判断特征：含 `<noscript>` 无正文、标题数为 0），再调 `firecrawl_scrape`（markdown + `onlyMainContent: true`）
   - 媒体源（CoinDesk / PANews / BlockBeats 等服务端渲染）通常首选即可；交易所 SPA 页面（OKX / Gate 活动列表）通常需降级
3. 解析标题、日期、链接
4. 保存位置：
   - 交易所内容 → `references/competitors/{platform}/announcements/YYYY-MM.md`
   - 媒体内容 → `references/competitors/_media/{媒体名}/YYYY-MM.md`

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
| Playwright 404 | 反爬或 URL 变更 | 换 URL 或加 --wait-for-timeout=10000 |
| WebFetch 返回空 | JS 渲染的 SPA 页面 | 降级走 firecrawl_scrape + waitFor: 5000 |
| Firecrawl 返回空 | JS 渲染页面 | 加 waitFor: 5000 参数 |
| capture.py 检测不到页面变化 | 页面只有微小动画 | 降低 diff 阈值或手动截（screencapture -l） |
