---
name: promo-kit
description: >
  当用户提到「宣发脚本 / 视频脚本 / gif 脚本 / 分镜脚本 / 上线宣发 / 图文宣发 /
  4 宫格 / 宣发文案 / 卖点文案 / 功能宣发」时触发。把一个功能/活动写成对外宣发内容
  （视频分镜脚本 / 图文 4 宫格 / 短文案三选一或组合）亦触发。丢一份旧宣发脚本要改版亦触发。
type: standalone
version: 1.1.0
category: marketing
tags: [promo, copywriting, marketing, video-script, localization]
risk: safe
allowed-tools: [Read, Write, Bash]
output_format: .md
output_prefix: launch-
depends_on: []
optional_inputs: [prd, prototype]
consumed_by: []
scripts:
  check_promo_kit.sh: "Step B 自检（结构齐 / 讲人话 / 卖点字数 / 合规红线 / 多语言列对齐）— bash .claude/skills/promo-kit/scripts/check_promo_kit.sh <source.md>"
  wp_publish.py: "Step 5b 发布 Platform C Square（launch-*-wp.md frontmatter 驱动，md→Gutenberg→REST，默认草稿）— python3 .claude/skills/promo-kit/scripts/wp_publish.py <launch-*-wp.md> [--publish]"
---

# Launch Copy — 上线宣发内容（视频脚本 / 图文 4 宫格 / 短文案）

## 触发与定位

**做什么**：把一个功能/活动写成对外宣发内容。三形态 + 一个渠道变体共享一份卖点池 + 同一套「痛点 → 卖点 → CTA」哲学：

- **视频脚本**（`launch-{feature}-video.md`）：视频 / gif 逐镜头分镜表，一列中文文案（旁白或画面文字）+ 多语言截图列。
- **图文 4 宫格**（`launch-{feature}-grid.md`）：4 张图各承一个卖点，主标 + 副标。
- **短文案**（`launch-{feature}-copy.md`）：标题 + 中段卖点 + 结尾 CTA + 品牌 Tag。
- **WP 发布版**（`launch-{feature}-wp-{lang}.md` · 渠道变体）：发 Platform C Square 博客的正式版，frontmatter 带发布元信息、全篇禁 emoji；中英俄三语一组（`-wp-zh / -en / -ru.md`），`wp_publish.py` 一条命令齐发。

**何时触发**：用户说「宣发脚本 / 视频脚本 / gif 脚本 / 分镜 / 图文宣发 / 4 宫格 / 宣发文案 / 卖点文案」，或给一个功能要做上线宣发。

**不做**：
- 操作 / 使用手册、帮助中心文章 → 走 user-manual skill（教用户怎么操作，不是宣传卖点）。
- **渠道分版长文案**（Banner / 官方博客长文 / 更新日志条目）→ 走 user-manual skill 的 `promo-` 模式。本 skill 只做「上线宣发三件套」的短平快形态。
- PRD / 需求文档（内部行为规格）。

**受众**：读者是 **C 端用户 / 潜在用户**，不是研发、不是内部。全篇用户视角、业务白话。

## 改脚本前 30 秒

> 改本 skill `scripts/check_promo_kit.sh`：`Read 此文件 limit=80`（前两节就够）。
> 改产出物（宣发 md）：建议全文 Read（写作规则散在 §3 / §4 / references）。

**Public API（不可改签名 · 改前看调用方）**：
- `check_promo_kit.sh <source.md>` — Step B 自检唯一入口，无第三方依赖（纯 bash + grep）。
- `wp_publish.py <launch-*-wp.md> [--publish]` — Step 5b 发布唯一入口；元信息读文件 frontmatter（CLI 同名参数仅覆盖），凭据读 `.env`（WP_SITE / WP_USER / WP_APP_PASSWORD），代理按 `scripts/proxy_env.sh` 判定。

**改完跑啥**：
```bash
bash scripts/check_promo_kit.sh references/example-launch-video.md
python3 scripts/wp_publish.py /tmp/任意测试.md --lang zh --category 产品更新 --dry-run   # 不联网自跑通
```

**深入读什么**（按需 grep 定位）：
- 三形态骨架：`Read references/promo-kit-templates.md`
- 多语言 / Tag / 图上文字：`Read references/promo-kit-localization.md`

## 硬规则（FAIL 即拦）

1. **用户视角，不写"我们新增了什么"**：每句表达「用户获得了什么」。❌「新增 AI 总结」 ✅「AI 帮你秒懂市场热点」。禁"新增 / 支持 / 优化 / 升级"堆砌，多用"更快 / 更简单 / 更方便 / 更安全 / 更省心"。
2. **痛点 → 卖点 → CTA，不按功能逐项列**：开场先戳痛点场景引共鸣，中段每个卖点回答「解决什么问题」，结尾引导马上体验。禁「XX 功能全新上线」直接开讲功能。
3. **一句话一个卖点、≤ 20 字**：每句只传一个信息点。卖点句、图文副标一律 ≤ 20 字；图文主标 8～10 字。
4. **讲人话**（`check_promo_kit.sh` 拦）：禁内部术语 / 技术名 / 场景号（A-1）/ 埋点事件名 / 字段名 / API / 内部迭代版本号（如「社区 3.2」）。❌「支持 TRTC 实时通信」 ✅「直播延迟低至 1 秒，互动更实时」。
5. **金融宣发合规红线**（硬拦 · 比通用营销更严）：
   - **无承诺收益**：禁「稳赚 / 必涨 / 抓住暴涨 / 收益翻倍」等暗示盈利的表达，痛点钩子也不例外（❌「总是错过暴涨行情？」）。
   - **无绝对化用语**：禁「最 / 第一 / 唯一 / 100% / 永久」等。
   - 痛点钩子可写「操作繁琐 / 找不到 / 反应慢」这类**体验痛点**，不碰行情涨跌与收益。
6. **视频节奏 30s 死秒锚定官方**：黄金三段式开场 0–3s / 中段 3–20s / 结尾 20–30s（指南硬约束），非 30s 时长按比例缩放；中段 3～4 个核心卖点，受口播字数预算约束，禁 15s 硬塞 4 个（15s 可减到 2～3）。
7. **命名前缀 `launch-` + 形态后缀**：`launch-{feature}-video.md` / `-grid.md` / `-copy.md` / `-wp-{lang}.md`，落 `{项目}/deliverables/{季度}/{版本}/`（无此结构则落用户指定目录）。

## 核心输出规范

### 一份卖点池，三形态复用

先从信源提炼 **2～4 个核心卖点**（`功能 + 用户价值` 句式，每条 ≤ 20 字），三种形态都从这一份池子取，不各写各的。卖点数随载体缩放：

| 载体 | 卖点数 | 依据 |
|---|---|---|
| 视频 30s | 3～4 | 中段 3～20s 每镜头一个卖点 |
| 视频 15s | 2～3 | 口播字数预算（中文口播 ~4–5 字/秒 → 15s 约 60–75 字，含钩子 + CTA 塞不下 4 句卖点） |
| 图文 4 宫格 | 4（不足则 2～3） | 一图一卖点 |
| 短文案 | 2～4 | 中段每条聚焦一个信息 |

### 视频脚本骨架（`-video` · 官方分镜表）

黄金三段式（30s 死秒锚定官方，非 30s 按比例缩放）：

| 段 | 时间（30s） | 作用 |
|---|---|---|
| 开场·痛点钩子 | 0–3s | 引共鸣，不划走（提问/痛点/场景/对比式） |
| 中段·核心卖点 | 3–20s | 每镜头一个卖点，答「解决什么问题」 |
| 结尾·行动召唤 | 20–30s | 引导马上体验（体现价值，不止「立即更新」）|

分镜表列（逐字照官方评审模板）：`中文文案 | 重点突出（将中文截图内需要突出的内容圈出） | 截图（中文） | 截图（英文） | 截图（俄语）`（语言列可配）。行标签 `开场 / 功能一~四 / 结尾·CTA`，**结尾镜头带Platform CLogo+二维码**。完整骨架 + 示例见 `references/promo-kit-templates.md`。

### 图文 4 宫格骨架（`-grid`）

4 张图，每图一卖点，风格统一、阅读顺序自然。每格：`主标（8-10 字）+ 副标（≤20 字）+ 配图说明`。骨架见 templates。

### 短文案骨架（`-copy`）

- **标题**：一句话点明主题，可用「全新上线 / 重磅升级 / 正式发布」，突出功能名。
- **中段**：2～4 条卖点，每条 `功能 + 用户价值`（✅「新增『现货盈亏』展示，收益情况一目了然」）。
- **结尾**：价值总结一句 + CTA（打开 App / 前往某页 / 立即体验）+ **品牌 Tag（必加）**。

品牌 Tag 按团队配置（Platform C 示例：中文 `#Platform C进化论`、英俄 `#Platform CEVOLVE`），配法见 localization。

## 执行步骤

### Step 0 — 定形态 + 收齐 4 个输入
先确认要哪种形态（视频 / 图文 / 短文案，可组合）。起草前必须拿到 4 个输入（AI 替代不了前两个的判断）：
1. **功能描述**（一句话）
2. **用户痛点**（具体场景，不是「体验不好」）
3. **核心卖点**（1～3 条，`功能 + 用户价值`）
4. **视频时长**（15s / 30s，仅视频形态需要）

缺痛点或卖点先反问用户，别凭空编。

### Step 1 — 读信源（并行）
有 PRD / 原型则并行 Read 抓功能事实与页面流程；没有就用 Step 0 的 4 个输入起草。截图 / Wiki 文档亦可作信源——多模态直接看图，从界面反推卖点与分镜（哪屏对应哪个卖点镜头）；**只认截图真实可见的元素，推不出的别脑补、问用户，不为凑镜头硬编卖点**（硬规则 5 / 缺卖点不凭空造）。信源里的内部术语/版本号一律翻成用户白话（硬规则 4）。

### Step 2 — 提炼卖点池
从信源提炼 2～4 个核心卖点，写成 `功能 + 用户价值` 短句（≤20 字）。这份池子三形态共用。逐条自检：是不是站用户收益角度？有没有暗示收益/绝对化（硬规则 5）？

### Step 3 — 按形态写 md
- **视频**：按 templates 官方分镜骨架写（5 列 + 行标签 开场/功能一~四/结尾），30s 死秒锚定官方、非 30s 按比例换算，卖点数按时长（§4），结尾带Platform CLogo+二维码。
- **图文**：4 宫格，一图一卖点，主标 8-10 字 / 副标 ≤20 字。
- **短文案**：标题 + 中段 + 结尾三段，结尾必带品牌 Tag。

多语言版 / 品牌 Tag / 图上文字 → 先 Read `references/promo-kit-localization.md`。

### Step 4 — 自检
```bash
bash scripts/check_promo_kit.sh {项目}/deliverables/{季度}/{版本}/launch-{feature}-video.md
```

### Step 5 — 发布到 Platform C Square（WordPress · 可选）

**Step 5a 写 `launch-{feature}-wp-{lang}.md`（发布预览版，中英俄各一篇）**：check 全绿、用户要发布才写。frontmatter 承载全部发布元信息，正文所见即所得（骨架见 templates §四；分类三语对照与站点画像见 `references/wp-square-api.md`，发布前 Read 免重新探测）：
- **全篇禁 emoji**（含 ✅🚀；站内正式文风抽样 9/9 零 emoji，标题可用感叹号）
- **公告体**：头图 + 导语段 + 3～4 条卖点裸列表 + 结尾 CTA 段，不设小标题，300～800 字
- 4 宫格宣发改「段落配图」循环体；视频作尾部 video 块嵌入，不发分镜脚本本身

**Step 5b 用户确认预览后发布**（三语一条命令齐发，篇间自动留间隔、429 自动重试）：
```bash
python3 scripts/wp_publish.py launch-{feature}-wp-*.md
```
- **默认建草稿**返回编辑 / 预览链接；`--publish` 显式才直发（金融宣发合规审校先行）。
- **`lang` 必给**（frontmatter；zh / en / ru / ur）：缺省站点按默认语 en 落库，中文 / 俄文分类会被 Polylang 服务端重映射成英文。
- 分类用站内三语现成名（中「产品更新 / 平台活动 / 市场观察…」· 英 `Product Updates…` · 俄 `-ru` 系列）；不存在报错不自建，标签缺失自动建。
- 多语言三件套 = 每语言一篇 `-wp-{lang}.md`（lang + 对应语言分类 + 语言版封面；站内头图 CN- / RU- 前缀惯例）。**三帖互链 REST 做不了**（Polylang 免费版不暴露 translations，实测写入被忽略）——需互链时 wp-admin 编辑页 Polylang 语言面板手动关联，或接受三帖独立（各语言树内正常展示）。

## 错误处理

- **输入缺失**：Step 0 若用户未给「用户痛点」或「核心卖点」，停止起草、向用户反问具体场景，不得凭空编造。
- **形态不明确**：用户未指定形态时，列出三形态（视频脚本 / 图文 4 宫格 / 短文案）让用户选，不默认输出全部。
- **自检 FAIL**：`check_promo_kit.sh` 返回非 0 时，按输出的 ✗ 行逐条修，修完重跑，直至 exit 0 方可交付。合规红线（承诺收益 / 绝对化用语）命中一律改写，不豁免。
- **信源含内部术语**：PRD / 原型里的技术名、版本号、场景号一律翻成用户白话再写入，禁原样搬运。
- **发布报网络不通**：按 `.claude/runbooks/proxy-fallback.md` 排沙箱与 Clash（square.example.com 直连不通，必须代理）；凭据缺失看 `.env` 三件套（应用密码含空格，值必须加双引号）。
- **发布报分类不存在**：换站内三语现成名重试，禁自建分类（Polylang 体系防脏）。
- **发布报 HTTP 429**：WordPress.com REST 节流（连续建帖过快触发），等 30～60 秒重试即可。

## API 速查

**check_promo_kit.sh**（Step B 自检 · 无第三方依赖）
```bash
bash scripts/check_promo_kit.sh <source.md>
# 按文件名后缀（-video / -grid / -copy）自动选校验集：
#   通用：讲人话禁词 / 金融合规红线（承诺收益 + 绝对化）/ 卖点句 ≤20 字
#   -video：三段式在场 / 文案列齐 / 截图列在场
#   -grid：4 格结构 / 主标副标字数
#   -copy：三段齐 + 品牌 Tag 在场
# exit 0 = 全绿；非 0 = 有 FAIL，按输出修
```

**wp_publish.py**（Step 5b 发布 · Platform C Square）
```bash
python3 scripts/wp_publish.py launch-x-wp-*.md [--publish]     # 三语组批量，一条命令齐发
python3 scripts/wp_publish.py <launch-*-wp-*.md> [--publish]   # 单发 / 多文件批量，默认草稿
python3 scripts/wp_publish.py <md> --title … --lang zh …       # 无 frontmatter 裸用 / 参数覆盖
python3 scripts/wp_publish.py --delete <post_id>               # 移入回收站
# frontmatter 键：title / lang（zh|en|ru|ur，必给）/ category（站内三语现成名）/ tags / cover / excerpt
# md→Gutenberg 块；cover 上传→featured_media+正文头图块；md 内本地图自动传媒体库换远端 URL
# emoji 检出仅告警；分类按名精确匹配不自建、标签缺失自建；凭据 .env（WP_*），代理 proxy_env.sh
```

## 自检清单

`check_promo_kit.sh` 跑完，逐条确认：

- [ ] 全篇用户视角（「你获得什么」），无「新增/支持/优化」堆砌
- [ ] 结构是痛点 → 卖点 → CTA，开场没直接报功能名
- [ ] 每个卖点一句话、≤20 字（图文主标 8-10 字）
- [ ] 无内部术语 / 技术名 / 场景号 / 埋点名 / 内部版本号（checker 绿）
- [ ] 金融合规：无承诺收益、无绝对化用语，痛点钩子不碰涨跌收益（checker 绿）
- [ ]（视频）官方 5 列 + 截图列在场；30s 死秒 0–3/3–20/20–30；结尾带Platform CLogo+二维码；卖点数匹配时长
- [ ]（图文）4 格风格统一、逻辑连贯
- [ ]（短文案）品牌 Tag 已加（中/英/俄按团队配置）
- [ ]（多语言）外文版走 native 语感非中译英，图上文字交 On-Image String Map（未声称能改 Figma）
- [ ]（发布）WP 版全篇无 emoji（含 ✅🚀），公告体结构：头图 + 导语 + 裸列表 + CTA，无小标题
- [ ]（发布）frontmatter lang / category 齐备（lang 缺则分类被重映射成英文），默认草稿未直发

## 示例

### 示例 1：视频脚本（30s · 摘要，全文见 references/example-launch-video.md）

功能：现货成本价　|　时长：30s　|　核心卖点数：3

- 开场·痛点钩子（0–3s）｜中文文案：「买了这么多，到底赚没赚，你算得清吗？」
- 功能一（3–9s）｜中文文案：「真实成本自动计算，不用手动对账。」
- 结尾·CTA（20–30s · Platform CLogo+二维码）｜中文文案：「看得见真实成本，算得准实际收益，立即打开Platform C App 体验！」

### 示例 2：短文案

```
## 标题
Platform C现货成本价功能全新上线！🚀

## 中段
- ✅ 真实成本自动计算，不用手动对账。
- ✅ 盈亏明细一目了然，每笔收益清清楚楚。

## 结尾
看得见真实成本，算得准实际收益。
立即打开Platform C App，前往【资产页】查看你的现货盈亏！#Platform C进化论
```

## References 索引

- `references/promo-kit-templates.md` — 三形态骨架 + 黄金三段式 + 分镜表示例（写 md 前 Read，**必读**）
- `references/promo-kit-localization.md` — 多语言 N 语可配 / 品牌 Tag 配法 / On-Image String Map（Figma 只读）（做多语言版或动图上文字时 Read）
- `references/example-launch-video.md` — 一份跑得通的视频脚本样例（checker 冒烟用）
- `references/wp-square-api.md` — Platform C Square API 画像（语言 slug / 三语分类对照 / 端点行为 / 块结构实证 / 429 节流与互链结论；发布前 Read 免重复探测，漂移时按文内命令重跑并更新）
