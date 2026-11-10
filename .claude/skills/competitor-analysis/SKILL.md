---
name: competitor-analysis
description: >
  「竞品分析 / 调研 / 抓情报 / 采集 XX」触发，丢竞品截图或链接亦触发。「截图 / 截一下」单独不触发。
argument-hint: "竞品平台 + 功能模块，如 Binance 活动中心；采集模式可加 --web / --content"
type: standalone
output_format: .md
output_prefix: comp-
depends_on: []
optional_inputs: [baseline]
consumed_by: []
scripts:
  capture.py: "APP 模式采集 — python3 capture.py --output-dir <dir>"
  scheduled-scrape.py: "定时批量抓取 — python3 scheduled-scrape.py --all|--platforms <p>|--media"
  intel-cron.sh: "crontab 入口 — 调 scheduled-scrape.py"
  check_comp_report.py: "报告基础自检 — python3 check_comp_report.py <report.md>"
---

# 竞品分析 Skill（Competitor Analysis）

## 触发与定位

独立产出物，直接给老板/业务方看，不一定接后续需求链路。本 skill 含两大动作：**情报采集**（APP/Web/Content/Interactive 四种模式，存 `references/competitors/{平台名}/`）+ **拆解分析**（默认写决策型报告，帮读者定「我方改什么」；立项深挖用 CRBE 深度版）。

**入口路由**：
- 用户说「截 / 抓 / 采集」→ 走采集模式（仅采集归档，不写报告）
- 用户说「分析 / 调研」+ 已有素材 → 走分析模式（默认）
- 「先采集再分析」→ 串起来跑，采集完进 Step 1 入分析

**做什么**：拆设计、分析意图、评价优劣、给出我方要改什么。
**不做**：只罗列竞品有什么功能。

## 改脚本前 30 秒

> hook `skill-load-gate` 守的是「Read 过本文件」**不看读了多少行**。
> 改本 skill `scripts/*.py`：`Read 此文件 limit=80` 即可。
> 改报告产物（.md）：建议全文 Read（章节顺序 / 证据取值 / 写法规则散在各章）。

**Public API（不可改签名）**：
- `python3 capture.py --output-dir <dir>` — APP 模式镜像截图唯一入口
- `python3 scheduled-scrape.py --all | --platforms <p> | --media` — 定时批量抓取，crontab 调
- `intel-cron.sh` — crontab wrapper，调上面 .py
- `python3 check_comp_report.py <report.md>` — 报告基础自检；退出 1 = 有 FAIL

**会拦你的 hook**：
- `script-syntax-gate` — pyflakes / bash -n（写 .py / .sh 自动跑）
- `plain-language-gate` — 报告 .md 写完自动扫违规口径

**改完跑啥**：
```bash
python3 .claude/skills/competitor-analysis/scripts/capture.py --output-dir /tmp/comp-test
# 或 demo 一份分析报告，看自检清单全过
```

**深入读什么**：
- 采集模式四种：`references/collection-playbook.md`
- 输出结构：`references/output-structure.md`
- PPT 输出（用户要 PPT 时）：`references/ppt-spec.md`

## 硬规则（FAIL 即拦）

**三角对比锚点（强制）**：

- **所有分析必须包含三角对比**：分析对象 vs Binance vs 我方
- Binance = 行业基准线，永远作为参照
- 我方 = 我方现状，永远作为落地锚点
- 即使只分析一个竞品，也必须拉上 Binance 和我方做横向对比

**反思维惯性五条（每次分析前自检，违任一 = 失败）**：

1. **反「功能堆砌」**——不因功能丰富而高估竞争力
2. **反「用户量即正义」**——不因 DAU 大而误判护城河
3. **反「大厂都这么做」**——团队规模 / 技术栈 / 用户结构 / 资源差异巨大，直接抄 = 翻车
4. **反「技术万能论」**——算法推荐 ≠ 用户留存，技术是手段不是目的
5. **反「行业报告权威论」**——行业报告是平均水平，不是你的具体场景

**FAIL 校验项（违任一视为未交付）**：

- 只列功能有无没拆设计细节 = FAIL
- 没分析「为什么这么设计」 = FAIL
- 没评价设计优缺点 = FAIL
- 没考虑我方约束 = FAIL
- 正向结论多于反向结论 = 可疑
- 没有 Binance 和我方的三角对比 = FAIL
- 每个功能拆解没收在具体「建议」（落到我方动作 / 优先级）= FAIL
- 报告没直陈我方最关键的根本短板（回避我方问题只夸竞品）= FAIL
- 建议和差异分析里的判断互相矛盾（如差异分析说 A 窗口伤冷启动，建议却选 A）= FAIL

**反脑补（每个断言动笔前自查证据，违任一 = FAIL）**：

- **打分必有据**：每格分数要有截图或公开数据支撑，缺证据的维度标「—」不硬凑分。拍脑袋填分 = 编数据，是竞品报告最大的信任杀手
- **竞品断言先查证**：任何「它没有 / 它不支持 / 它靠 X 实现」的判断，动笔前必须查证（官方文档 / 实测 / 截图），别用己方框架想当然否定竞品的核心价值（如把「非同类交易」当「无此能力」）
- **我方现状回读 baseline**：涉及己方功能「有没有 / 怎么实现」的判断，必须回读 baseline / PRD 核实，不凭对话印象脑补——错误的己方现状会推出错误的建议
- **查不到 ≠ 没这么做**：公开资料查不到不能当「业界不这么做」的证据——灰色实践只从诉讼 / 泄露 / 事后招认浮出，该换检索方向而非下结论

**打分与否看调研要回答什么**：

- 若要回答「谁强谁弱、我方整体排第几」：用 1-9 分打分矩阵（先定「9 分长什么样」再打），每维度最强项挂 👍，缺证据标「—」
- 若要回答「各家怎么做、我方改什么」（比形态、规则、字段）：用事实表，附原文或截图，不打分

**素材门槛**：遵循 `_shared/claude-design/asset-quality-rubric.md` 的 5-10-2-8 规则（5 轮搜索 / 10 候选 / 选 2 个 / 评分 ≥ 8 分），低分素材进备选库不进报告。

## 核心输出规范

### 两种报告

| 报告 | 什么时候用 | 结构 |
|------|-----------|------|
| **决策型**（默认） | 读者要据此定「我方改什么」：给产品总监 / 业务方的调研都走这个 | 见下方「决策型章节顺序」，样例见 `references/output-structure.md` 范式 A |
| **CRBE 深度版** | 用户说「立项调研 / 战略对标 / 深挖」 | 逐功能五层拆解 + CRBE 四维 + Hook 模型，见 `references/output-structure.md` 范式 B |

### 决策型章节顺序（按此顺序产出，不增不减）

```
## 一、结论
  1. 一句话：我方和竞品差在哪（不写口号式总结）
  2. 问题表：问题 | 我方现状（带真实数字）| 竞品怎么做
  3. 我方截图并排（证明问题真实存在）
  4. 建议速览：# | 建议 | 改动量 | 需要拍板
## 二、各家有哪些组件 / 功能   ← 事实表 + 截图
## 三、横向对比                 ← 按 Step 1 定下的维度逐节，每张表下配截图
  3.N 差异分析：维度 | 差异点 | 原因分析 | 对我方的判断
## 四、{我方}产品建议           ← 写成可开发的规则
  - 每条建议给：改前 / 改后对照表、文案草案、观察指标 + 回退条件（按适用）
  - 需要拍板的选项列方案表：方案 | 好处 | 代价，给出推荐
  - 「本期不动的」：事项 | 判断 | 重新评估的时机
## 五、要做什么                 ← # | 模块 | 事项 | 做什么 | 优先级 | 需配合方
## 附录                         ← 规则原文（带链接与日期）/ 截图原图位置 / 采集缺口
```

### 写法

- **对比格取值**：`✅ + 做法` / `❌`（实机或用户确认没有）/ `未见`（截图或网页里没看到；网页看不到的组件多半是 App 专属）
- **举例用真数字**：例子取截图或原文里的数字；没依据的阈值（回退线、门槛）写进「需要拍板」
- **截图跟着表走**：每张对比表下面放对应截图，图题写「看什么」（如「Platform C Feed：只显示 +33.83%」），不写「截图 1」
- **推断要标**：原因分析里没有公开依据的，句首写「推断：」；推断以外不用「多半 / 可能 / 大概」
- **称呼**：正文称「我们 / 我方」，要读者决定的写「需要拍板」，不出现人名，不写「待某某定」
- **内部约束写进判断**：推荐加权、卡片渲染方式、埋点有没有注册这类只有内部人知道的约束，影响建议时写进差异分析的「对我方的判断」列和建议里
- **推 Confluence 的强调**：橙色 `rgb(255,102,0)` 标核心判断与需要拍板的点；红色 `rgb(255,0,0)` 标我方问题与风险；浅红底 `rgb(255,235,230)` 标我方落后的格子；浅绿底 `rgb(227,252,239)` 标我方持平或领先的格子；关键数字与字段名加粗。写法 `<span style="color: rgb(255,102,0);"><strong>…</strong></span>`，含样式的行若被挤话检查误报，行尾加 `<!-- lint-skip:density -->`

### 产物形态 + 命名

- **格式**：Markdown（默认，对话内输出贴飞书 / 会议纪要工具）/ PPT（用户要求时走 ppt skill）
- **命名前缀**：`comp-`
- **存放**：`projects/{项目}/deliverables/`（关联项目）/ `references/competitors/`（独立分析）
- **结构**：按 `references/output-structure.md`

## 执行步骤

> 入口路由：「采集 / 截 / 抓」→ 跑采集模式后结束。「分析 / 调研」→ 进 Step 1。「先采集再分析」→ 采集完进 Step 1。

### Step 0：采集模式（仅采集路线读，分析路线跳过）

自动采集竞品 APP / Web 截图、公告内容、Crypto 媒体报道，归档到 `references/competitors/`。支持所有主流 Crypto 交易所（Binance / OKX / Gate / Bybit / MEXC / Bitget / Kucoin）及权威 Crypto 媒体，平台列表不封闭。

四种模式：

| 模式 | 触发词 | 技术 | 产出 |
|------|--------|------|------|
| APP | 「截竞品 XX YY」（默认） | iPhone 镜像 + screencapture | PNG |
| Web | 「截网页版 XX」「--web」 | browser-use CLI 全页截图 | PNG |
| Content | 「最新公告」「最近活动」「媒体报道」 | WebFetch → browser-use eval 兜底 | Markdown + 可选截图 |
| Interactive | 「翻完前 N 页」「全抓下来」「滚动加载完」 | browser-use CLI 脚本式交互 | PNG / JSON |

> **环境变量铁律**：必须 `BROWSER_USE_DISABLE_EXTENSIONS=1`，否则 daemon 卡死下载 Chrome 扩展。本 workspace 已在 settings.json env 段设置。

完整执行命令 + Step A-E（确认目标 / 执行采集 / Vision 过滤 / 用户确认 / 归档）+ Token 预算纪律 + 定时采集 + Troubleshooting 见 `references/collection-playbook.md`。

### Step 1：先定三件事，再采集

动手采集前向用户确认，一次一问，每问带推荐答案：

1. **这份调研服务哪个决定**：如「持仓卡下个版本改哪些字段」。答不出就先问，不开始采
2. **比哪几个维度**：用户给出关心的点，模型补全成维度清单再确认（如「挂什么 / 数据真实性 / 快照还是实时 / 收益怎么显示」）。维度就是第三章的小节
3. **读者是谁**：决定结论写多重、细节放多少
4. **竞品和素材**：哪几家；用户手里的截图、链接直接丢

素材门槛见 `_shared/claude-design/asset-quality-rubric.md`（5-10-2-8 规则）。

### Step 2：核对我方现状

1. 从 baseline 读出我方在各维度上的现状，列成清单
2. 清单交给用户逐条核对线上（「对 / 不对，实际是…」）
3. 线上和 baseline 不一致处，同轮改 baseline（先在变更记录章加行）
4. 顺带问内部约束：推荐加权、渲染方式、埋点注册情况这类会改变建议可行性的事

### Step 3：采集与分析

1. **采集**：关键形态以 App 实机截图为准，网页抓取只当线索。截图目录 `references/competitors/{平台}/{主题}/`，目录下放一份截图清单 README 给用户照着截。用户贴进对话的截图当轮复制归档
2. **分析**：决策型按「决策型章节顺序」写；CRBE 深度版按 `references/output-structure.md` 范式 B
3. **贯穿**：
   - 每个判断拆到「怎么做的 + 为什么 + 对我方意味着什么」
   - 数据没来源标「未公开，需验证」
   - Binance 和我方贯穿全文

### Step 4：产出 + 沉淀

1. 报告存 `projects/{项目}/deliverables/`（关联项目）/ `references/competitors/`（独立）；正文截图复制到 `deliverables/assets/{主题}/`，用 `./assets/` 相对路径引用
2. 推 Confluence：`python3 scripts/md_to_confluence.py <md> --parent-id <id>`，更新已有页用 `--update-id`；pageId 记在报告头部
3. 借鉴进度同步到关联项目 baseline 决策记录（如有）

### Step 5：PPT 专属 QA

生成 PPT 后必须执行：
1. 转 PDF → 转图片 → 视觉检查
2. 深色底文字可读性（对比度够不够）
3. 截图清晰、无裁切
4. 三角对比表格内容无截断
5. 修复后重新验证

## References 索引

**按需读**（场景命中才加载）：
- `references/collection-playbook.md` — 四种采集模式执行命令 + Step A-E + Token 预算 + Troubleshooting（仅采集路线）
- `references/output-structure.md` — 三套报告结构：A 决策型（默认，含样例路径）/ B CRBE 深度版 / C 打分对比型
- `references/ppt-spec.md` — PPT 输出专用（仅 PPT 路线）
- `_shared/claude-design/asset-quality-rubric.md` — 5-10-2-8 素材门槛（每次分析前必读）

## 自检清单

先跑脚本拦机械项：`python3 .claude/skills/competitor-analysis/scripts/check_comp_report.py <report.md>`（拦 --- 分隔线 / 结论不在第一章；有打分矩阵时查硬编与 👍）。脚本过后再走人工判断项：

- [ ] 第一章是结论：问题表带真实数字 + 我方截图 + 建议速览（含需要拍板）
- [ ] 每个维度都有 Binance 和我方，我方现状经用户核对过线上
- [ ] 对比格只用 ✅ / ❌ / 未见；「没有」类断言都经实机或用户确认
- [ ] 差异分析表每行都有「对我方的判断」，推断句标了「推断：」
- [ ] 建议和差异分析的判断一致，不自相矛盾
- [ ] 建议写成规则（改前改后 / 文案草案 / 观察指标 + 回退条件），有「本期不动的」
- [ ] 举例数字都来自截图或原文；没依据的阈值写成「需要拍板」
- [ ] 正文没有人名、「待某某定」、口号式总结句、给打法起的名字
- [ ] 报告直陈了我方最关键的根本短板
- [ ] 打分矩阵（若用）：1-9 分 + 👍，每格有据、缺证据标「—」
- [ ] PPT：每页有视觉元素，无纯文字页
- [ ] PPT：深色底文字可读性 OK
- [ ] PPT：功能拆解页有截图
