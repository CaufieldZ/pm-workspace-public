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

独立产出物，直接给老板/业务方看，不一定接后续需求链路。本 skill 含两大动作：**情报采集**（APP/Web/Content/Interactive 四种模式，存 `references/competitors/{平台名}/`）+ **拆解分析**（三角对比 + CRBE，产报告）。

**入口路由**：
- 用户说「截 / 抓 / 采集」→ 走采集模式（仅采集归档，不写报告）
- 用户说「分析 / 调研」+ 已有素材 → 走分析模式（默认）
- 「先采集再分析」→ 串起来跑，采集完进 Step 1 入分析

**做什么**：拆设计、分析意图、评价优劣、判断壁垒、追踪我方进度。
**不做**：只罗列竞品有什么功能。

## 改脚本前 30 秒

> hook `skill-load-gate` 守的是「Read 过本文件」**不看读了多少行**。
> 改本 skill `scripts/*.py`：`Read 此文件 limit=80` 即可。
> 改报告产物（.md）：建议全文 Read（拆解模板 / Hook 模型 / 进度追踪规则散在各章）。

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
- 可借鉴点没标我方进度 = FAIL
- 正向结论多于反向结论 = 可疑
- 没有 Binance 和我方的三角对比 = FAIL
- 每个功能拆解没收在具体「建议」（落到我方动作 / 优先级）= FAIL
- 报告没直陈我方最关键的根本短板（回避我方问题只夸竞品）= FAIL

**反脑补三条（每个断言动笔前自查证据，违任一 = FAIL）**：

- **打分必有据**：每格分数要有截图或公开数据支撑，缺证据的维度标「—」不硬凑分。拍脑袋填分 = 编数据，是竞品报告最大的信任杀手
- **竞品断言先查证**：任何「它没有 / 它不支持 / 它靠 X 实现」的判断，动笔前必须查证（官方文档 / 实测 / 截图），别用己方框架想当然否定竞品的核心价值（如把「非同类交易」当「无此能力」）
- **我方现状回读 baseline**：涉及己方功能「有没有 / 怎么实现」的判断，必须回读 baseline / PRD 核实，不凭对话印象脑补——错误的己方现状会推出错误的建议

**打分矩阵口径**：功能维度 × 各平台用 1-9 分打分（先定「9 分长什么样」再打，别拍脑袋），每个维度的最强项挂 👍 标记，让强弱一眼可见。缺证据维度标「—」。

**素材门槛**：遵循 `_shared/claude-design/asset-quality-rubric.md` 的 5-10-2-8 规则（5 轮搜索 / 10 候选 / 选 2 个 / 评分 ≥ 8 分），低分素材进备选库不进报告。

## 核心输出规范

### 两种档位

**快速版**（5-8 页）：会议前快速准备 / 日常竞品跟踪
1. 功能设计拆解（逐功能：设计方案 + 优缺点）
2. 三角对比速览（关键差异可视化）
3. UI / 交互模式速览（截图 + 设计意图 + 优缺点）
4. 可借鉴点 + 我方进度
5. 要避的坑（直接抄会翻车的点）
6. 一句话结论 + 行动建议

**深度版**（12-18 页，CRBE 完整框架）：立项前调研 / 战略对标 / 汇报
- **C**apability — 逐项标注 ✅可复制 / ❌不可复制 / ⚠️路径红利 / 💎差异化机会
- **R**oute — 竞品怎么走到今天的，路径依赖是什么，我们能不能走同一条路
- **B**arrier — 网络效应 / 数据壁垒 / 品牌认知 / 生态锁定
- **E**fficiency — 同任务竞品几步完成 / 我们几步，转化漏斗差异
+ Hook 模型留存壁垒评估（外部触发 / 内部触发 / 行动 / 可变奖励 / 投入 → Hook 强度 \_\_/10）

### 单功能拆解模板（核心章节，不可省略）

> 每个功能填全下列 REQUIRED 槽位：先给竞品打法起个「模式命名」→ 横向讲各家怎么做 + 我方现状 → 每功能收在一条加粗「建议」（落到我方该怎么做，不是泛泛评价）。

```
### {功能名称}

**模式命名（REQUIRED）**：一句话概括竞品这套打法，起个有记忆点的名字（如「交易员闭环」/「实盘竞技场」/「五层漏斗发现页」）
**设计方案**：交互流程、页面结构、信息架构、关键截图引用
**设计意图**：为什么这么设计、服务什么业务目标、解决什么用户问题；能追问「为什么是 X 不是 Y」的拆一层（如「为什么直播佣金远高于帖子佣金」）
**JTBD 透镜**（深度版填，快速版可省）：
| 维度 | {竞品} | 我方 |
|------|--------|-----|
| 功能性目标 | 用户用它完成什么任务 | |
| 情感性目标 | 用户希望感受到什么 | |
| 社交性目标 | 用户在圈内想呈现什么形象 | |
| 非竞品替代 | 用户不用此功能时转而用什么 | |
| 切换阻力 | 已在竞品的用户为什么不迁移到我方 | |
**优点 / 缺点**：设计好/差在哪，体验如何
**三角对比**（入口位置 / 交互步骤 / 信息密度 / 核心差异）
**借鉴价值**：能不能学、学什么、直接抄的翻车风险
**我方进度**：🟢/🟡/🔵/🔴/⚫ + 具体说明
**建议（REQUIRED）**：加粗一句，落到「我方该怎么做」——具体动作 / 优先级，不接受「可以考虑优化」这类空话
```

### 我方进度图例（每条可借鉴结论必须附）

| 状态 | 标记 | 说明 |
|------|------|------|
| 已上线 | 🟢 | 附上线版本 / 日期 |
| 开发中 | 🟡 | 附预计上线时间 |
| 已排期 | 🔵 | 在 Roadmap 中但未开始 |
| 未开始 | 🔴 | 本次分析后可考虑是否立项 |
| 评估后放弃 | ⚫ | 附放弃原因 |

### 产物形态 + 命名

- **格式**：Markdown（默认，对话内输出贴飞书 / 钉钉）/ PPT（用户要求时走 ppt skill）
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

### Step 1：收集信息 + 读取素材门槛

采集前必读 `_shared/claude-design/asset-quality-rubric.md`（5-10-2-8 规则）。

向用户确认（缺什么问什么，不编造）：
1. **分析对象**：哪些竞品 × 哪个功能模块
2. **档位**：快速版 or 深度版
3. **竞品分层**（Claude 建议，用户确认）：Tier 1 直接竞品 / Tier 2 间接竞品 / Tier 3 跨界参考
4. **输出格式**：Markdown or PPT
5. **素材**：用户有截图 / URL / 体验录屏直接丢
6. **我方当前进度**：用户口述即可

### Step 2：读取我方约束

如有根目录 `profile.md`，读取拿团队能力 / 资源上限 / 用户基础。没有则从 baseline 提取，或跳过。

### Step 3：执行分析

**快速版**：逐功能拆解设计 → 每功能三角对比 → 可借鉴点标我方进度 → 精炼结论。

**深度版**：CRBE 框架逐维度 → 每功能深度拆解（设计方案 + 意图 + 优缺点）→ 全量三角对比 → 借鉴点标我方进度 + 建议排期。

强制贯穿：
- 每功能必须拆「怎么设计的」+「为什么」+「好不好」
- 每条「可借鉴」必须附「直接抄会翻车的原因」+ 我方当前进度
- 数据没来源标「未公开，需验证」
- 我方约束 + Binance 对比贯穿全文

### Step 4：产出 + 沉淀

1. 按选定格式输出（MD 对话 / PPT 调 ppt skill）
2. 竞品截图存 `references/competitors/{平台名}/{功能模块}/`
3. 报告存 `projects/{项目}/deliverables/`（关联项目）/ `references/competitors/`（独立）
4. **借鉴进度**同步更新到关联项目 baseline 决策记录（如有）

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
- `references/output-structure.md` — 报告章节结构 + 排版规范
- `references/ppt-spec.md` — PPT 输出专用（仅 PPT 路线）
- `_shared/claude-design/asset-quality-rubric.md` — 5-10-2-8 素材门槛（每次分析前必读）

## 自检清单

先跑脚本拦机械项：`python3 .claude/skills/competitor-analysis/scripts/check_comp_report.py <report.md>`（拦 --- 分隔线 / 缺打分矩阵，提示硬编嫌疑 / 缺 👍 / 缺来源标注）。脚本过后再走人工判断项：

- [ ] **每个功能都拆了设计方案 + 设计意图 + 优缺点**（不只列有无）
- [ ] **每个功能都起了模式命名 + 收在具体「建议」**（落到我方动作 / 优先级）
- [ ] **每个功能都做了三角对比**（竞品 vs Binance vs 我方）
- [ ] **每条可借鉴都标了我方进度**（🟢🟡🔵🔴⚫）
- [ ] 打分矩阵用 1-9 分 + 👍 标记最强项，每格有据、缺证据标「—」不硬凑
- [ ] 竞品「没有 / 不支持 / 靠 X 实现」类断言都查证过（不想当然否定竞品价值）
- [ ] 涉及我方现状的判断都回读过 baseline / PRD（不凭印象脑补）
- [ ] 报告直陈了我方最关键的根本短板（不回避自身问题）
- [ ] 反向结论 ≥ 正向结论
- [ ] 我方约束贯穿全文
- [ ] 每个「可借鉴」都附了翻车风险
- [ ] 数据有来源标注，无来源的标「需验证」
- [ ] 竞品分层合理（Tier 1/2/3）
- [ ] 行动建议可执行（具体步骤，不是「可以考虑」）
- [ ] PPT：每页有视觉元素，无纯文字页
- [ ] PPT：深色底文字可读性 OK
- [ ] PPT：功能拆解页有截图
