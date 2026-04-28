<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PM 工作流规范

## 〇、全局规则

### 项目结构与 Skill 读取

【项目结构】
每个项目在 `projects/{项目名}/` 下独立管理：
- `context.md` — 产品现状 + 需求 + 场景编号 + 术语 + 决策 + 待办（开工前必读，Chat 更新后覆盖）
- `screenshots/` — 现有产品截图 + 竞品截图（context.md 引用）
- `scene-list.md` — 场景清单（确认后锁定）
- `inputs/` — 原始素材（会议纪要/竞品分析/口述整理等）
- `scripts/` — 产出物生成脚本（gen_prd_v1.py、gen_imap_v1.py 等），版本迭代时复用，不删除
- `deliverables/` — 交互大图 / 原型 / PRD 等产出物
  - `archive/` — 旧版归档

跨项目共用的竞品素材放 `references/competitors/{平台名}/`，按功能模块分子目录，项目 context.md 用相对路径引用。

【一键开项目】
触发：用户说「新项目」「开个项目」「做个新需求」、直接丢截图/文件说要做什么、或提到 `projects/` 下不存在的项目名。自动完成：

1. 建完整目录结构（context.md + screenshots/ + inputs/ + deliverables/archive/ + scene-list.md）
2. 按 `.claude/chat-templates/context-template.md` 九章模板填 context.md，截图存 screenshots/、会议纪要/口述存 inputs/
3. 给初步场景划分建议（不锁定）+ 链路推荐（简单/复杂/超复杂）
4. 一次性输出 context.md + 场景建议 + 链路给用户确认，不分三次问

已存在的项目直接读 `context.md`；缺素材时要求用户提供（截图/会议纪要/口述均可）。

【会议纪要自动处理】
触发：「会议纪要」「meeting notes」或丢 PDF/文本说是纪要。不确定哪个项目先问。

1. 拉取/提取存 `inputs/meeting-YYYY-MM-DD.md`（meeting-autopilot skill 承接拉取流程）
2. 决策追加第 7 章、变更追加第 9 章（动态章按日期追加，不改不删）
3. **回写静态章**：第 7 章新增决策中改架构 / 规则 / 术语 / 角色 / 场景的，必须同步更新第 2/3/4/5/6 章
4. **影响分析**：决策涉及已有产出物（改编号 / 术语 / 加场景 / 砍功能）时主动告知影响范围
5. **PRD 1.3 收敛提示**（PRD 已交付时必做）：本次决策含改 vs 线上基线 delta 项（新增 / 砍 / 改核心规则）时，列出清单问「需要收敛进 PRD 1.3 变更范围,是否更新 docx？」用户确认才动。讨论流水（方案细节多轮调整）不提示。

【Skill 读取规则】
执行链路中任何一步产出前，**必须先读取**对应 skill 的 SKILL.md 和 references/ 下所有 .md 参考文件，严格按照 skill 中定义的步骤、模板、组件库、样式规范执行。禁止跳过 skill 凭自身理解直接产出。

各 Skill 的文件读取清单以对应 SKILL.md 的 Step 1 为唯一权威来源，此处不再重复列出。

### 上下文管理

【上下文防丢规则】
每步产出前必须回读 scene-list.md + 上一步产出物。HTML 只 grep，禁止 Read 全文。回读是内部动作，不告知用户。

| 当前步骤 | 回读对象 | 方式 |
|----------|----------|------|
| 交互大图 | scene-list | Read |
| 原型 | + 交互大图 | `grep -A2 'class="st"'` 标题 + `grep "跨端"` 数据流表 |
| PRD | + 交互大图/原型 | grep 标题 + `grep "const.*Data"` JS 数据块；docx 可 Read |
| bspec/pspec | + PRD | Read（docx/md 体积可控） |
| test-cases | + bspec + PRD 合规章节 | Read |

变更后先更新 scene-list.md，再 grep 确认影响范围。>300 行文件先 `grep -n` 定位再 `Read offset/limit`。

CSS/JS/骨架脚本源码禁止模型主动读取（骨架脚本通过 `open().read()` 自动拼接）。SKILL.md 中的 API 速查表已包含调用所需全部信息。

【执行模式】
当用户指定项目并说「按 context 执行」或类似指令时：
1. 读取 `projects/{项目名}/context.md`
2. 按「待办 & 下一步」表格的顺序，从第一个未完成项开始
3. 每个待办执行前，先读取对应 skill 的 SKILL.md + references/（.md 文档）
4. 每个待办完成并通过自检后，告知用户进度，等用户确认再做下一个
5. 不要重新判断复杂度和路由，不要重新讨论方案
6. context.md 中未覆盖的细节自行按 skill 规范补齐
注意：用户也可能不走 context.md 而直接指定任务（「帮我出交互大图」），此时正常按链路规则执行即可。

### 产出物质量约束

【反幻觉】
1. 用户前提含事实错误时直接指出
2. 缺业务规则/数据/上下文时直接提问，绝不编造
3. 不确定用"需确认/据我了解"标记，禁止肯定语气输出不确定内容
4. 方案默认补 edge case 和失败场景，不只给 happy path

【端能力校验】
产出物中画的每个交互，必须确认目标端有能力执行。跨端完成的用箭头 + 文案标注「→ 见 D-0d」，不要在当前端画完成态。

【交付验证与自检反压】
产出物声称完成时，必须先执行对应 skill 的自检清单（含验证脚本），全部通过后才能交付。不能先说"已完成"再补自检。HTML 产出物额外验证：对照 scene-list.md 编号逐个核对，无遗漏无空内容才可交付。
自检不通过时：① 尝试自动修复（最多 2 次）→ ② 仍不通过则停下来，把具体失败项报告给用户，不继续执行下一步 → ③ 用户确认「跳过」或给出修复方案后才继续。禁止静默跳过。

【版本同步规则（强制）】
context.md 新增或删除场景时，必须同步更新 scene-list.md，并在 scene-list 顶部更新版本号。
骨架脚本生成前，先 grep 两个文件的版本号，不一致则停止并提示用户先同步。

【逻辑链】场景→需求→方案→商业指标→技术可行性，竞品参照行业头部平台。缺上下文直接问。

【70% 先行】产出物先出 70% 版本确认方向，再补细节。大返工成本远高于两轮迭代。

【人读产出物讲人话（强制）】
适用：PRD / PPT / SOP / 数据周报 / 会议纪要 / 交互大图 / 原型 / 架构图 / 流程图。不适用：bspec / pspec / scene-list / context.md / requirement-framework。

原则：编号在锚点（scene_table 左列、IMAP `.st h2` / `.phone-label`、跨 skill id）保留 `B-1 · 业务白话` 格式；正文（PRD 段落、`.flow-note` / `.ann-text` / PPT 正文）禁裸 `A-1 / B-2 / 决策 N`，一律业务白话。判定：抽段给研发看要回查文档才懂 = 违规。

各 skill 自检脚本兜底（`check_prd.sh` / `check_imap.sh` 已加，PPT / data-report 同步配置）。

【PM 职责边界】新 Skill 候选和走查范围严格限定在 PM 自己要做的事：
- PM 侧的「走查」只做**功能/流程/业务规则**走查，不做样式还原（那是 UI/设计的事）
- 推荐新 Skill 前先过一遍「这是 PM 做的事吗」，不是就别推
- 集团规划/竞品工作流里看到的机会点，按角色过滤一遍再决定
- 跨角色的活可以提一句「这是设计/QA 的活，不在 PM 工区做」，但不主动建对应 skill

### 批量变更与 cross-check

【批量变更流程（强制）】
触发：变更涉及 ≥ 2 文件且影响跨文件一致性（删/新增场景、改术语/编号、改业务规则、升版、改流程节点）。单文件文案修改不触发。

流程：① 列变更清单给用户确认 → ② `bash scripts/impact-check.sh {项目名}` 测覆盖 → ③ 按 pipeline 顺序改（context → scene-list → 需求框架 → imap → 原型 → PRD → bspec/pspec）→ ④ 收尾 cross-check（再跑 impact-check + grep 旧术语/编号无残留 + grep 新术语已同步）→ ⑤ 不通过则修复后再交付，禁止跳过。

【版本管理与升级流程】
方案变更/评审结构性改动 → 升版（`bash scripts/version-bump.sh {项目名}` 自动完成归档/改名/内部版本号/context.md 更新）。小修 → 不升版直接覆盖。变更记录在产出物内部体现（PRD 1.3 章、imap `（变更）` 标注）+ context.md 末尾追加一行。

### 大文件生成与文档同步

【大文件生成策略】
HTML 产出物 > 200 行：禁用 Write 直接写，必须脚本生成；Step B 填充必须用 fill 脚本，禁用 Edit 逐个替换。小幅文案/字段修改（不涉及结构）允许 Edit 直接改 HTML。

【大文档源码拆分（> 1500 行或 Tab ≥ 10）】
PPT/SOP 手册类产出物按「每页一个源文件 + orchestrator」拆分，不塞进单脚本。参考实现 `projects/htx-workflow-pre/scripts/sop-src/`（20 page 文件 + 9 数据/壳文件 + `gen_sop_v1.js`）。

【已脚本化产出物的修改纪律】
一旦产出物已有 gen 脚本，HTML 即为只读产物：禁止直接 Edit/Write 生成出来的 HTML，改动只进源文件（pages/{id}.js / nav.js / styles.css 等），改完 `node gen_{主题}_v{N}.js` 重新生成。违反此规则下次迭代会被脚本覆盖。

【脚本复用】
生成产出物前先检查 `projects/{项目名}/scripts/` 下有无同类脚本，有则复用修改，无则新写并保存为 `gen_{类型}_v{N}.py`（PPT 用 `.js`）。版本迭代复制旧脚本改名，不从头写。

【Skill 执行收尾】
1. 产出物存入 `deliverables/`
2. git commit

### md → Confluence 同步

走 `scripts/md_to_confluence.py`（`--parent-id` 建新页，`--update-id` 覆盖）。默认空间 `jituankejizhongxin`，creds 从 `.mcp.json` 读。禁止用 Confluence MCP `create_page` 直接传 md 内容。

### 决策缺口处理

执行任何 pipeline skill 前，如果发现 context.md 中缺少当前 skill 必需的决策信息（如页面层级、空状态处理、多端差异等），停下来向用户提问，优先给 A/B/C 选项，不要自行假设后继续执行。

### 演讲叙事顺序（所有 pipeline Skill 强制）

所有 pipeline 产出物（scene-list / imap / prototype / PRD / bspec）的 PART / Scene / 章节顺序按**演讲叙事逻辑**组织，不按"页面归属/功能模块"机械堆砌。判定：当幻灯片讲一遍，听众听到的顺序是什么，章节就那么排。

设计前先写一句「这个产出物讲的故事是 X → Y → Z」，再排序。常见叙事骨架：触达型 = 入口 → 落点 → 转化 → 留存 → 异常；配置型 = 列表 → 创建 → 配置 → 审核 → 监控；闭环型 = 发起方 → 跨团队衔接 → 接收方 → 反向回流；个人空间型 = 入口 → 核心承载 → 关键转化 → 自管理 → 资源位。

**PART / 章节用户故事陈述（IMAP + PRD 强制）**：每个 PART（IMAP）/ 一级功能章（PRD 第 3 章+）起头必须有一句用户故事（≤ 30 字，讲谁、做什么、为什么）。技术骨架章免。骨架脚本 `story` 字段缺则报错（imap `gen_imap_skeleton._validate_part_stories`，prd `chapter_story()`）。

### 逻辑拼图（方案变更自动推演）

用户在方案讨论中提出以下类型的变更时，自动触发影响推演，不需要用户主动要求：

**触发条件**（满足任一）：
- 改流程节点（如「报名先行」「取消 XX 限制」）
- 改入口位置（如「把入口移到首页」）
- 改门槛/阈值（如「降低 KYC 要求」「提高交易量门槛」）
- 改业务规则（如「改为按天发放」「增加白名单」）

**不触发**：用户只是描述现状、提问、讨论竞品、说「只是了解一下」。

**推演三维度**（简洁输出，附在回复末尾）：用户触达 / 转化漏斗 / 风控边界。

### 填充过程中间检查

填充脚本每完成 3 个 Scene 后，用 grep 检查已填充内容的术语/编号一致性：
- 场景编号是否和 scene-list.md 一致
- 术语是否和 context.md 第 5 章一致
不通过则停下来修正后再继续，不要填完全部再回头改。

### commit 规范 + 防腐 hook

commit 前缀：`feat / fix / refactor / docs / chore`。`.githooks/pre-commit` 在 Skill / 规则文件变更时自动跑 `audit.sh`，不通过则拦截。禁止 `--no-verify` 绕过。激活一次：`git config core.hooksPath .githooks`。

### HTML 分步生成通用规则

适用 imap / proto / arch / ppt（> 200 行）。必须 Step A 骨架 → B 填充 → C 自检，A 后等用户确认，B 每次填充前 grep 回读、每 3 Scene 后 grep 检查术语/编号。快速模式（用户说「快速生成/不用确认」）：A/B/C 仍分轮，但 A 完成后不停。

**Fill 脚本**：必须用 `re.sub` 块替换，禁止 Edit 逐个替换（小幅文案除外）。
**自检**：`audit-fast.sh` hook 自动检查编号/FILL 残留/字体/差量标签。全量自检走 `check_html.sh`。脚本存 scripts/ 命名 `gen_{类型}_v{N}.py`（PPT 用 `.js`）且成对交付。

**Fill 内容边界契约（跨 Skill 通用）**：每个 Skill 在 SKILL.md 声明「Fill 内容契约」，明确骨架 vs fill 各提供什么。**禁止同时在骨架和 fill 中生成设备壳**（.phone / .webframe / .app-mock）。两种合法模式：① 骨架生成壳，fill 写内部内容（prototype 模式）；② 骨架只生成空容器，fill 生成壳+内容（interaction-map 模式）。新建 HTML Skill 必须先定义 Fill 契约再写骨架。

**Fill 质量强制规则（所有模型）**：

- fill 函数单个 ≤ 80 行 HTML，单文件 ≤ 150 行，超过则拆分
- 禁止用 heredoc 传入含 HTML 的 Python 代码（引号冲突），必须先 Write 文件再 python3 执行
- 每次只填充 1 个 Scene，执行验证通过后再写下一个
- Write 工具连续失败 2 次 → 停下来，将当前函数拆为 2 个更小的函数，不要重试相同内容
- 禁止在修复 SyntaxError 时凭记忆改代码，必须先 `python3 -c "import ast; ..."` 定位具体行号
- **组件完整性**：交互大图 fill 函数必须包含全部 9 类组件（见 interaction-map SKILL.md「Fill 必需组件清单」），每 Scene 至少 1 个 `.aw` + 1 个 `.anno` + 1 个 `.ann-tag` + 1 个 `.flow-note`
- **排版三级层次**：font-weight 至少使用 3 级（900 标题/PART 头 → 700 卡片标题/按钮 → 400 正文说明），禁止全文只用 700
- **填充后逐 Scene 自检**：每完成一个 Scene 后必须 grep 验证 `.aw` / `.anno` / `.ann-tag` / `.flow-note` 计数，任一为 0 则返工后再继续下一个 Scene

**美学硬底线（HTML 产出物通用，本段即权威，与 skill references 冲突以本段为准）**：

- 反 AI slop 六禁：
  1. 全屏渐变背景（rainbow / mesh gradient）
  2. Emoji 装饰标题或列表（🚀⚡️✨🎯💡✅），例外见 anti-ai-slop.md「UI mock 内部图标」条款
  3. 圆角卡片 + **任一方向 ≥ 2px 的 accent color border**（左 / 右 / 上 / 下都禁，从 left 换 top 不算规避。想分区用背景色对比、标题前小色点、字重对比、全边均匀 hairline）
  4. SVG 画人物 / 场景 / 插画（用 `.cd-placeholder` 灰底 + mono 文字缩写代替）
  5. 烂大街字体作 CJK 主字体（禁 Inter / Roboto / Space Grotesk / Fraunces 作正文）
  6. 每个 card / feature 都带 icon
- 字号：标题 ≥ 正文 2.5 倍（正文 16px → 标题 ≥ 48px）
- line-height 按内容分档（CJK 字形填满 em box，英文下降部会粘下一行中文顶）：
  - 纯英文 display heading：1.05 – 1.1
  - 含 CJK 的 display heading（中文产出物 99% 情况）：1.25 – 1.35
  - 正文 / 段落：1.6 – 1.8
- 颜色：最多 1 主 + 1 辅 + 1 强调 + 灰阶，禁凭空调色；Claude Design 系用 `--cd-accent: #D97757`（Anthropic terra cotta）
- 留白 ≥ 40% 总面积；间距只用 8pt 网格（8 / 16 / 24 / 32 / 48 / 64px）
- 字体栈见 §三 设备规范（CJK 优先铁律）。实际用到哪种才在 `<link>` 里引，不照抄完整 CDN URL
- CSS 变量源头唯一：生成脚本里必须 `fs.readFileSync('.claude/skills/_shared/claude-design/tokens.css')` 拼进 CSS 模板；**禁止手抄 `:root { --cd-bg:... }` 整块定义**。项目级扩展 token（如 `--cd-surface2` / `--cd-ok`）在 tokens.css 后追加一个小 `:root {}` 块即可
- 无真数据用 `.cd-placeholder`，禁编造 stats / quote / metric cards

---

## 一、需求路由

### PM-GATE：需求澄清关卡

<PM-GATE>
收到模糊或新发起的需求时，先完成需求澄清，再判定复杂度。

**必答三问**（逐个问，不合并）：
1. 解决谁的什么具体痛点？（要有场景，不接受「优化体验」）
2. 核心指标是什么？（具体数字：留存率/转化率/DAU/客单价）
3. 怎么判断成功？（量化标准，非「用户反馈好」）

基于回答提出 2-3 个方向，每个说明：核心差异、涉及端/模块、预计规模、推荐理由。PM 选定后进入复杂度判定。

**跳过条件**（满足任一）：
- PM 说「跳过澄清」「快速模式」「按 context 执行」「直接做」
- 已有完整 context.md 含明确目标指标
- 已有功能改动，规模 ≤ 1 场景
- 方案型项目（无 UI 改动、跨系统对接、纯后端/架构方案）
</PM-GATE>

### 复杂度判定（满足任一即为「复杂」）

- ≥ 2 端/角色
- ≥ 5 场景且有跨场景跳转
- 含数据同步 / 状态流转 / 多角色协作

### 三条链路

**简单链路**（不满足上述任一条件）：
- 纯功能点 → 直接 Markdown PRD
- 单页面交互 → 直接出原型（prototype skill）
- 纯文案/策略 → 直接文档

**复杂链路**（每步等确认再进下一步）：
① scene-list → ②* req-framework → ③ imap → ④* prototype → ⑤ prd → ⑥* bspec / pspec → ⑦* test-cases → ⑧ cross-check
（* = 可选。bspec 需切分给研发 AI 时用，pspec 需切分给设计/前端 AI 时用，test-cases 依赖 prd，bspec 可选增强）

**超复杂链路**（多系统/资金/架构）：在 ② 和 ③ 之间插入 arch-diagrams（pipeline 2.5），其余同上。

**方案型项目**（满足以下任一条件时触发）：

- 跨两个或以上独立系统（不是前后端分离，是真的两个系统对接）
- 涉及资金流转 / 结算 / 授信
- 需要多团队共建（PRD 有"🔲 待填"占位）
- 没有用户界面改动（纯后端/架构方案）

方案型项目**不走标准 pipeline**（scene-list → imap → proto → PRD），产出物由 PM 按实际需要决定。context.md 章节结构按项目特点自定义（建议对标共建 PRD 章节），不强制九章模板。文档分工详见 prd SKILL.md「方案型项目」章节。

### 路由规则

- 收到需求后，先过 PM-GATE 澄清，再判定复杂度，告知用户走哪条链路
- **方案型项目**：识别到多组共建特征时主动提醒 PM 走方案型文档分工
- PM 要求跳步可以，但必须提醒风险
- 场景编号、术语规则见 §二

---

## 二、跨 Skill 串联约束

### 场景编号

- 编号在场景清单阶段确定后**不可改动**
- 编号规则：前台主场景 `A/B/C`、子场景 `B-1/B-2`、后台 `M-1/M-2`、功能前缀 `F-0/E-1`
- 交互大图、原型、PRD、行为规格、页面结构、测试用例集必须复用同一套编号
- 新增场景在场景清单中追加，不可复用已有编号

### View 划分

- View = 独立的产品端/视角，场景清单阶段确定
- 所有产出物中 View 名称和数量必须一致
- 交互大图 PART = PRD 章 = 原型全局 Tab

### 术语一致性

- 模块/组件命名一旦定义，所有文档必须完全相同
- 状态名、枚举值不可各文档自行创造
- 同一概念两种叫法（如 Tab/专题）→ 开工前和用户确认术语

### 变更管理

- 方案变更须同步体现在所有已产出文档
- PRD 用 1.3 变更范围章节汇总（基线 = 当前线上版本，非 PRD 版本间 diff）
- 交互大图/原型用 `（变更）` `（新增）` 标注

### 文件命名

`{output_prefix}{项目简称}-v{N}.{扩展名}`，`output_prefix` / `output_format` 由各 SKILL.md frontmatter 定义。

### 需求变更处理

编号只追加不改，已有编号锁定。变更流程：
① 在 context.md 第 4 章追加新场景 → ② 更新 scene-list.md → ③ `grep -l 'depends_on:.*scene-list' .claude/skills/*/SKILL.md` 识别受影响下游 → ④ 等用户确认后按 pipeline_position 顺序升版 → ⑤ 旧版归档 archive/。

### Skill 依赖矩阵

> 依赖关系定义在各 SKILL.md frontmatter 的 `depends_on` / `consumed_by` 字段。
> 运行 `bash .claude/skills/workspace-audit/scripts/audit.sh 3` 可查看完整 registry。

---

## 三、设备规范

设备尺寸、字体、配色以各 skill 的 ref CSS 为准。通用约定：
- App 壳：375×812px，border-radius: 44px，深色底（iPhone 15 Pro 精细数值详见 `prototype.css`：Dynamic Island 124×36、状态栏 54、Home Indicator 140×5、圆角 48）
- 弹窗：全屏遮罩 + 居中卡片，遮罩点击 / ✕ 均可关闭

**字体（全 skill 统一一套，对标 Anthropic 官方 brand-guidelines + claude.ai chat UI 实测）**：
- 正文 sans：`'Noto Sans SC','Poppins',system-ui,sans-serif`（Poppins 是 Anthropic 官方 brand-guidelines 钦定的 heading 字体，对标 claude.ai 实际用的付费 Styrene B）
- display serif：`'Noto Serif SC','Lora',Georgia,serif`（Lora 是 Anthropic 官方 brand-guidelines 钦定的 body 字体，对标 claude.ai 实际用的付费 Tiempos / Copernicus，hero 标题 / 卡片大标题）
- 等宽：`'JetBrains Mono','SF Mono',ui-monospace,monospace`
- CJK 优先铁律：任何字体栈，中文字体必须排在英文字体前
- Google Fonts 统一 @import：`Noto+Sans+SC:wght@300;400;500;700;900&family=Noto+Serif+SC:wght@300;400;500;600;900&family=Lora:ital,wght@0,400..700;1,400..700&family=Poppins:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700`

**配色分类**（设计意图，非冲突）：
- 前台 App / 交易所视觉（交互大图、移动端原型）：深色系（`--bg: #0B0E11`，涨绿 `#0ECB81`，跌红 `#F6465D`，**金融语义**）
- Claude Design 系（ppt / flowchart / architecture-diagrams / Web 后台 / 方案文档 / SOP）：claude.ai chat UI 同款暖近黑 `#1F1F1E` + 暖灰白文字 `#C3C2B7` + Anthropic 官方 terra cotta `--cd-accent: #D97757`（次 accent 蓝 `#6A9BCC` / 三 accent 绿 `#788C5D`，按多 track 对比时循环用），token 定义见 `.claude/skills/_shared/claude-design/tokens.css`。营销级高对比场景切 `.theme-cd-brand` 拿官方品牌色 `#141413` / `#FAF9F5`
- 语义色（跨主题通用，单独使用不构成主题）：成功 `#00B42A` / 失败 `#F53F3F`（Arco Design，用于状态标「已上线/下线」、审批节点「通过/拒绝」、必填星号、删除按钮）
- 各 skill ref CSS 按定位选主题，语义色作为附加层叠加，不需要整套色板统一

<!-- pm-ws-canary-236a5364 -->
