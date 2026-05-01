# PM 工作流规范

## 〇、全局规则

### ChatOpus vs 本地 Opus 分工

- **ChatOpus（顾问）**：决策辩论 / 方案 review / 审计 / 元问题讨论。不写产出物，不修改文件。
- **本地 Opus（执行主力）**：所有产出物由你写——context.md / scene-list / IMAP / PRD / bspec / pspec / 测试用例 等。ChatOpus 在 chat 轨给出的决策建议由你落地到 context.md 对应章节。
- **协作流程**：你出方案 → 你直接落地 → Felix 主导 review。review 中拿不准的判断点由 Felix 单独贴 ChatOpus 讨论，不再整个 diff 贴过去审批。

### 项目结构与 Skill 读取

【项目结构】

`projects/{产品线}/{项目}/` 两层。**没有产品线级 context.md** — 产品线认知靠 `@product-lines.md`（每 session 必读），项目认知靠各自的 `context.md`。

```
projects/
├── {产品线-A}/{项目1, 项目2, 项目3, ...}/   ← 业务线下展开多个并列项目
├── {产品线-B}/{项目1, 项目2}/
├── {产品线-C}/{项目1, 项目2, 项目3}/
├── {顶级方案型项目}/         ← 不归任何产品线（如跨组织共建方案）
└── {顶级基建项目}/           ← 不走 PRD pipeline（如埋点目录、流动性底座）
```

每个项目目录下：`context.md` + `scene-list.md` + `inputs/` + `scripts/` + `deliverables/`（具体见 `.claude/chat-templates/context-template.md`）。

**路径占位约定**：SKILL.md / 脚本里的 `{项目}` 是**完整项目路径片段**——产品线下项目用两段（`{产品线}/{项目}`），顶级项目用一段（`{顶级项目}`）。即 `projects/{项目}/deliverables/` 实例化时用对应实际路径。无需改 SKILL.md 模板。

> 具体业务线 / 项目命名按你的工作内容自定义，不进 public sync。

跨项目共享：竞品素材 `references/competitors/{平台}/`；同产品线下若术语 / 业务规则真重复，季度 review 拆到 `projects/{产品线}/glossary.md`。

【一键开项目】

触发：「新项目」「开个项目」、丢截图/文件说要做什么、或提到 `projects/` 下不存在的项目名。

1. 按 `product-lines.md` 识别归属（community / livestream / growth / 顶级方案型 / 顶级基建）— 不明确先问
2. 建 `projects/{产品线}/{项目}/` 目录 + 九章 context.md
3. 给场景划分建议 + 链路推荐 + context 一次性输出，等用户确认

【迁移历史】Schema v1（扁平 `htx-*`）→ v2（业务分类两层）已 2026-05-01 完成。SOP 与回滚见 `.claude/runbooks/migration-schema-v2.md`。

【会议纪要自动处理】
触发：「会议纪要」「meeting notes」或丢 PDF/文本说是纪要。不确定哪个项目先问。

1. 拉取/提取存 `inputs/meeting-YYYY-MM-DD.md`（用 `scripts/pull_meeting_notes.py` 拉钉钉闪记纪要）
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
骨架脚本生成前两文件版本号一致性由 hook 强阻断（2026-04-29 加 `pre-version-sync-gate`）。

【逻辑链】场景→需求→方案→商业指标→技术可行性，竞品参照行业头部平台。缺上下文直接问。

【70% 先行】产出物先出 70% 版本确认方向，再补细节。大返工成本远高于两轮迭代。

【人读产出物讲人话（强制）】
适用：PRD / PPT / SOP / 数据周报 / 会议纪要 / 交互大图 / 原型 / 架构图 / 流程图。不适用：bspec / pspec / scene-list / context.md。

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

流程：① 列变更清单给用户确认 → ② `bash scripts/impact-check.sh {项目名}` 测覆盖 → ③ 按 pipeline 顺序改（context → scene-list → imap → 原型 → PRD → bspec/pspec）→ ④ 收尾 cross-check（再跑 impact-check + grep 旧术语/编号无残留 + grep 新术语已同步）→ ⑤ 不通过则修复后再交付，禁止跳过。

【版本管理与升级流程】
方案变更/评审结构性改动 → 升版（`bash scripts/version-bump.sh {项目名}` 自动完成归档/改名/内部版本号/context.md 更新）。小修 → 不升版直接覆盖。变更记录在产出物内部体现（PRD 1.3 章、imap `（变更）` 标注）+ context.md 末尾追加一行。

### 大文件生成与文档同步

【大文件生成策略】
HTML 产出物 > 200 行：禁用 Write 直接写，必须脚本生成；Step B 填充必须用 fill 脚本，禁用 Edit 逐个替换。小幅文案/字段修改（不涉及结构）允许 Edit 直接改 HTML。

【大文档源码拆分（> 1500 行或 Tab ≥ 10）】
PPT/SOP 手册类产出物按「每页一个源文件 + orchestrator」拆分，不塞进单脚本。典型结构：`scripts/sop-src/pages/{id}.js`（每 Tab 一个源文件）+ `scripts/sop-src/data.js`（数据层）+ `gen_sop_v1.js`（orchestrator）。

【已脚本化产出物的修改纪律】
一旦产出物已有 gen 脚本，HTML 即为只读产物：改动只进源文件（pages/{id}.js / fill_*.py / scenes_*.py / patch_*.py），改完重生 HTML。已 hook 强阻断（2026-04-29 加 `pre-deliverable-source-gate`），真要小幅文案改且不重生 → `SKIP_DELIVERABLE_GATE=1` 临时绕过。

【脚本复用】
生成产出物前先检查 `projects/{项目名}/scripts/` 下有无同类脚本，有则复用修改，无则新写并保存为 `gen_{类型}_v{N}.py`（PPT 用 `.js`）。版本迭代复制旧脚本改名，不从头写。

【Skill 执行收尾】
1. 产出物存入 `deliverables/`
2. git commit

### md → Confluence 同步

走 `scripts/md_to_confluence.py`（`--parent-id` 建新页，`--update-id` 覆盖）。默认空间 `jituankejizhongxin`，creds 从 `.mcp.json` 读。禁止用 Confluence MCP `create_page` 直接传 md 内容。

### 决策缺口处理

执行任何 pipeline skill 前，如果发现 context.md 中缺少当前 skill 必需的决策信息（如页面层级、空状态处理、多端差异等），停下来向用户提问，优先给 A/B/C 选项，不要自行假设后继续执行。

### 演讲叙事顺序 / HTML 分步生成 / Fill 质量 / 美学硬底线

详见 `.claude/rules/html-pipeline.md`。imap / prototype / arch / ppt 在 SKILL.md Step 1 必须 Read 该文件。其他 pipeline Skill（scene-list / prd / bspec）按需引用其中「演讲叙事顺序」一节。

### 逻辑拼图（方案变更自动推演）

用户在方案讨论中提出以下类型的变更时，自动触发影响推演，不需要用户主动要求：

**触发条件**（满足任一）：
- 改流程节点（如「报名先行」「取消 XX 限制」）
- 改入口位置（如「把入口移到首页」）
- 改门槛/阈值（如「降低 KYC 要求」「提高交易量门槛」）
- 改业务规则（如「改为按天发放」「增加白名单」）

**不触发**：用户只是描述现状、提问、讨论竞品、说「只是了解一下」。

**推演三维度**（简洁输出，附在回复末尾）：用户触达 / 转化漏斗 / 风控边界。

### commit 规范 + 防腐 hook

commit 前缀：`feat / fix / refactor / docs / chore`。`.githooks/pre-commit` 在 Skill / 规则文件变更时自动跑 `audit.sh`，不通过则拦截。禁止 `--no-verify` 绕过。激活一次：`git config core.hooksPath .githooks`。

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
① scene-list → ② imap → ③* prototype → ④ prd → ⑤* bspec / pspec → ⑥* test-cases → ⑦ cross-check
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

