# HTML Pipeline 规则

适用 Skill：interaction-map / prototype / architecture-diagrams / ppt（HTML 产出物 > 200 行）。
其他 pipeline Skill（scene-list / prd / bspec / pspec / test-cases）按需引用「演讲叙事顺序」一节。

各对应 SKILL.md 的 Step 1 必须 Read 本文件，否则跳过。

---

## 〇、演讲叙事顺序（所有 pipeline Skill 强制）

所有 pipeline 产出物（scene-list / imap / prototype / PRD / bspec）的 PART / Scene / 章节顺序按**演讲叙事逻辑**组织，不按"页面归属/功能模块"机械堆砌。判定：当幻灯片讲一遍，听众听到的顺序是什么，章节就那么排。

设计前先写一句「这个产出物讲的故事是 X → Y → Z」，再排序。常见叙事骨架：触达型 = 入口 → 落点 → 转化 → 留存 → 异常；配置型 = 列表 → 创建 → 配置 → 审核 → 监控；闭环型 = 发起方 → 跨团队衔接 → 接收方 → 反向回流；个人空间型 = 入口 → 核心承载 → 关键转化 → 自管理 → 资源位。

**PART / 章节用户故事陈述（IMAP + PRD 强制）**：每个 PART（IMAP）/ 一级功能章（PRD 第 3 章+）起头必须有一句用户故事（≤ 30 字，讲谁、做什么、为什么）。技术骨架章免。骨架脚本 `story` 字段缺则报错（imap `gen_imap_skeleton._validate_part_stories`，prd `chapter_story()`）。

---

## 一、HTML 分步生成通用规则

适用 imap / proto / arch / ppt（> 200 行）。必须 Step A 骨架 → B 填充 → C 自检，A 后等用户确认，B 每次填充前 grep 回读、每 3 Scene 后 grep 检查术语/编号。快速模式（用户说「快速生成/不用确认」）：A/B/C 仍分轮，但 A 完成后不停。

**Fill 脚本**：必须用 `re.sub` 块替换，禁止 Edit 逐个替换（小幅文案除外）。

**自检**：`audit-fast.sh` hook 自动检查编号/FILL 残留/字体/差量标签。全量自检走 `check_html.sh`。脚本存 scripts/ 命名 `gen_{类型}_v{N}.py`（PPT 用 `.js`）且成对交付。

**Fill 内容边界契约（跨 Skill 通用）**：每个 Skill 在 SKILL.md 声明「Fill 内容契约」，明确骨架 vs fill 各提供什么。**禁止同时在骨架和 fill 中生成设备壳**（.phone / .webframe / .app-mock）。两种合法模式：① 骨架生成壳，fill 写内部内容（prototype 模式）；② 骨架只生成空容器，fill 生成壳+内容（interaction-map 模式）。新建 HTML Skill 必须先定义 Fill 契约再写骨架。

**大文档源码拆分（> 1500 行或 Tab ≥ 10，PPT / SOP 手册类）**：三层架构——`gen_{类型}_v{N}.js`（orchestrator 只拼接，不含业务逻辑）+ `{类型}-src/data.js`（全局数据层，pages 只读）+ `{类型}-src/pages/page-0X.js`（每 Tab 一个源文件，≤ 150 行超过继续拆）。改动流程：改单页文案只动 `pages/page-0X.js`；改全局数据（术语改名）动 `data.js`；加新 Tab 建新 page + orchestrator 注册。

---

## 二、Fill 质量强制规则（所有模型）

- fill 函数单个 ≤ 80 行 HTML，单文件 ≤ 150 行，超过则拆分
- 禁止用 heredoc 传入含 HTML 的 Python 代码（引号冲突），必须先 Write 文件再 python3 执行
- 每次只填充 1 个 Scene，执行验证通过后再写下一个
- Write 工具连续失败 2 次 → 停下来，将当前函数拆为 2 个更小的函数，不要重试相同内容
- 禁止在修复 SyntaxError 时凭记忆改代码，必须先 `python3 -c "import ast; ..."` 定位具体行号
- **组件完整性**：交互大图 fill 函数必须包含全部 9 类组件（见 interaction-map SKILL.md「Fill 必需组件清单」），每 Scene 至少 1 个 `.aw` + 1 个 `.anno` + 1 个 `.ann-tag` + 1 个 `.flow-note`
- **排版三级层次**：font-weight 至少使用 3 级（900 标题/PART 头 → 700 卡片标题/按钮 → 400 正文说明），禁止全文只用 700
- **填充后逐 Scene 自检**：每完成一个 Scene 后必须 grep 验证 `.aw` / `.anno` / `.ann-tag` / `.flow-note` 计数，任一为 0 则返工后再继续下一个 Scene

### 填充过程中间检查

填充脚本每完成 3 个 Scene 后，用 grep 检查已填充内容的术语/编号一致性：
- 场景编号是否和 scene-list.md 一致
- 术语是否和 context.md 第 5 章一致

不通过则停下来修正后再继续，不要填完全部再回头改。

---

## 三、美学硬底线（HTML 产出物通用，本段即权威，与 skill references 冲突以本段为准）

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
- 字体栈见 pm-workflow.md §三 设备规范（CJK 优先铁律）。实际用到哪种才在 `<link>` 里引，不照抄完整 CDN URL
- CSS 变量源头唯一：生成脚本里必须 `fs.readFileSync('.claude/skills/_shared/claude-design/tokens.css')` 拼进 CSS 模板；**禁止手抄 `:root { --cd-bg:... }` 整块定义**。项目级扩展 token（如 `--cd-surface2` / `--cd-ok`）在 tokens.css 后追加一个小 `:root {}` 块即可
- 无真数据用 `.cd-placeholder`，禁编造 stats / quote / metric cards
