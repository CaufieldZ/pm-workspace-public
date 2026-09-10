---
name: ppt
description: >
  当用户提到「PPT」「宣讲材料」「SOP 手册」「多 Tab 信息文档」时触发，产物为 HTML 多 Tab 信息文档。「方案文档」走 prd skill（方案型项目）。
argument-hint: [内容大纲文件 或 口述大纲]
type: standalone
output_format: .html
output_prefix: ppt-
depends_on: []
optional_inputs: [baseline]
consumed_by: []
scripts:
  gen-notes-docx.py: "导出演讲者备注 docx — python3 gen-notes-docx.py <html>"
  # deck-fill.js / fill-template.js 在 assets/（模板源，非可执行），用法：复制 *-script-template.js 到项目 scripts/ 改写
---

# PPT 信息文档

## 触发与定位

**做什么**：把方案 / SOP / 方法论类内容生成 HTML 演讲 / 信息文档（等同 PPT 给人讲方案），支持演讲提词器。两套生成骨架：
- **纯 deck 范式（默认 · 演讲）**：1280×720 固定舞台，无 sidebar，键盘翻页，五幕章节胶囊。主题 `vendor-editorial`（衬线杂志感 + teal/amber 双语义 + 浅深双底）。`deck-fill.js` 生成。
- **sidebar Doc 模式（可选 · 长文档 / SOP）**：240px sidebar + Doc/Deck 双模式。`fill-template.js` 生成。

**何时触发**：用户说「PPT / 宣讲材料 / SOP 手册 / 多 Tab 信息文档」。演讲 / 方案宣讲默认走纯 deck；长 SOP 手册 / 需侧边导航走 sidebar Doc。

**不做**：方案型项目文档（归 prd skill）/ 项目内链路型架构图（归 architecture-diagrams，按 13 种页面类型输出）。

**与 architecture-diagrams 区别**：arch 依赖 scene-list + baseline 项目链路；ppt 独立产出型，不依赖任何链路，用户提供内容大纲。

**用途**：团队分享 / 对外宣讲 / 方法论沉淀 / SOP 手册。

## 改脚本前 30 秒

> hook 守的是「Read 过本文件」**不看读了多少行**。改 scripts/*.py 用 `Read 此文件 limit=80`（§1+§2 即够）。改产出物建议全文 + Read `assets/fill-template.js`。

**Public API（不可改签名）**：
- `fillDeck({ title, theme, acts, slides, outputPath })` — `assets/deck-fill.js` 拼纯 deck（默认范式）
- `fillTemplate({ title, theme, nav, renderers, notes, outputPath })` — `assets/fill-template.js` 拼 sidebar Doc 模式
- `python3 gen-notes-docx.py <html>` — 导出演讲者备注 docx

**会拦你的 hook**：
- `script-syntax-gate` / `cjk-punct`
- `skill-load-gate` — 改 `ppt-*.html` 必先 Read 本 SKILL.md

**改完跑啥**：
```bash
node scripts/gen_deck_v{N}.js  # 纯 deck（fillDeck）／或 gen_ppt_v{N}.js（fillTemplate）
python3 scripts/check_cjk_punct.py deliverables/ppt-*.html --strict
```

**深入读什么**：语法骨架 `Read references/deck-grammar.md`（必读 · 纯 deck 范式在上半部）；Step 0 澄清门 `Read references/ppt-step0-clarification.md`；sidebar Doc / Deck 双模式 `Read references/doc-deck-modes.md`；Step 6 口播稿 `Read references/ppt-notes-docx.md`；sidebar 组件 `grep -n "^### " references/components-cheatsheet.md` 按需。

## 硬规则（FAIL 即拦）

1. **数据驱动**：NAV 数组驱动 sidebar 导航，不硬编码；PAGE_RENDERERS 每个 Tab 一个渲染函数，不堆砌 HTML
2. **组件复用**：统一使用模板内置组件，**不发明新 class 名**。唯一类名来源按范式分：纯 deck = `deck-template.html`；sidebar Doc = `ppt-template.html`（Step 3.0 类名预检兜底）
3. **内容与骨架分离**：骨架脚本负责结构，填充脚本负责内容
4. **修改纪律**：PPT 产出物一旦脚本化生成，HTML 就是**只读产物**。禁直接 Edit / Write 生成出来的 HTML；改动只进 `scripts/sop-src/pages/{id}.js` 或对应 source 文件，改完 `node gen_{主题}_v{N}.js` 重生。违反 = 下次迭代必定改错
5. **HTML > 200 行铁律**：必须用 Node.js 脚本生成（不是 Python，避免三层转义地狱）；> 1500 行或 Tab ≥ 10 → 必须按「大文档源码拆分」（见 `.claude/runbooks/html-build-split.md`），不能把所有页面塞进单脚本
6. **CSS 变量源头唯一**：所有 `--cd-*` 变量源头 `_shared/claude-design/tokens.css`。脚本必须 `fs.readFileSync(tokens.css)` 拼进 CSS 模板，**禁手抄 `:root` 整块 token**。项目级扩展 token 在 tokens.css 后追加 `:root {}`
7. **动画节制**：
   - 纯 deck 范式：**不混 animations.css**，节奏靠浅深底交替 + slide 自带 transition（`opacity/transform .5s`），保持杂志感克制
   - sidebar Doc 模式：每页 1 个强调动画，`anim-rise-in` 等 27 个来自 `assets/animations.css`，混 3-5 个看着乱。cover→`anim-rise-in`；bullets→`anim-stagger-list`；KPI→`counter`
8. **讲人话**（强制）：PPT / SOP 读者是运营 / 员工 / leader，没有 PM 内部上下文：
   - 禁正文出现：决策 N（决策 1 / 决策 12）、baseline 内部条目编号、bug / CR 单号
   - 禁正文出现：场景编号 A-N / B-N / M-N（PM 内部编号，运营看不懂）
   - 自检 grep（生成后必跑，命中即返工）：
     ```bash
     grep -nE '决策\s*[0-9]+|[A-G]-[0-9]+\s*(/\s*[A-G]-[0-9]+)*' deliverables/ppt-*.html | grep -v "scene-[a-g]" | grep -v "id=\""
     ```
     应为 0（`scene-x` anchor id / DOM id 不算违规，正文含「决策 N / A-N」即违规）

## 核心输出规范

- **位置**：`projects/{项目}/deliverables/ppt-{主题}-v{N}.html`（有项目关联）或 `deliverables/`（独立产出）
- **命名**：`ppt-{主题}-v{N}.html`
- **生成脚本**：项目级 `scripts/gen_ppt_v{N}.js`（fillTemplate 调用范例见 `assets/script-template.js`）
- **版本管理**：`.claude/runbooks/version-bump.md`

### 设备规范

继承 `_shared/claude-design/tokens.css`：

**纯 deck 范式（默认）**：
- 固定舞台 1280×720，`fit()` 整体缩放贴合窗口
- 浅深双底交替：浅底 `--paper #F4F5F6` / 深底 `--ink #15181C`（封面 / 章节转场 / 收尾用深底）
- 默认主题 `vendor-editorial`：teal `#0F726B` + amber `#A86A22` 双语义色
- 顶部五幕章节胶囊 + 进度条 + 底部页码 + 边缘点击翻页

**sidebar Doc 模式（可选）**：
- 侧边栏 240px，深色 `--bg2`；主内容区 max-width 1200px
- 配色变量：claude-native 默认 `#1F1F1E`

**改视觉风格新增独立 theme，不改 `tokens.css` 全局**：PPT 想换配色 / 字体调性时新建一套 theme 变量集，别动 `_shared/claude-design/tokens.css` 的共享 token——那份被 imap / prototype 依赖，必须保留业务蓝等既定语义色。

### 核心组件（详见 `references/components-cheatsheet.md`）

- **card** — 通用卡片容器
- **grid2/3/4** — 响应式网格
- **tag-***  — 彩色标签（blue/green/orange/purple/red）
- **note** — 左边框提示框（蓝 / 绿 / 橙）
- **cmp-table** — 对比表格
- **ck-item + ck-num** — 编号清单
- **prompt-block** — 代码 / 文本展示块（含复制按钮）
- **pipe / pipe-node** — 纵向流程链（≥ 5 步）
- **flow-h / flow-h-step** — 横向时间线（≤ 4 步）
- **page-hero / page-split** — 呼吸页 / 分隔带（替代套娃模板）
- **stat-card** — 数字统计卡（替代 inline style 的 hero-num）
- **quote-block** — 金句块（大字居中斜体）
- **icon-box / flow-chip / track-card / accordion / gallery-card / modal-overlay / score**

### 字体引入纪律

- **纯 deck 默认三字体**：标题 Noto Serif SC（衬线 700/900）· 正文 Noto Sans SC（无衬线 **300 细字重**）· 元信息 IBM Plex Mono。`deck-template.html` 已内置正确 `<link>`，`vendor-editorial` 主题把 `--cd-mono` 切 IBM Plex Mono。三字体分工见 `deck-grammar.md §一`
- **字体 `<link>` = 实际用到的字体**，不照搬 tokens.css 注释里的完整 CDN URL。sidebar Doc 模式 CJK 最小集 = Noto Sans SC + Noto Serif SC + JetBrains Mono
- **CJK 混排字体栈**：`--cd-sans` / `--cd-serif` 中文字体必须排在英文字体前（tokens.css 默认已 CJK 优先）

## 执行步骤

### Step 0：需求澄清门（动手前必做）

PPT 用法分四类（SOP 手册 / 演讲材料 / 对外宣讲 / 方法论沉淀），用法差极大，门按用途分流：

1. **0.1 用途识别** → 文档型 / 演讲型 子门
2. **0.2 主题色推荐** → 1 主 + 1 备选 + 一句理由（9 套主题清单）
3. **0.3 子门对齐** → 文档型 4 问 / 演讲型 5 问（论点必答）

完整规则 → `Read references/ppt-step0-clarification.md`（跳过条件 / 用途表 / 9 套主题清单 / 子门细则 / 逐字稿三铁律）。

### Step 1：读取参考文件

**必读规则**（HTML pipeline 通用）：
```bash
view .claude/runbooks/html-pipeline.md
view references/deck-grammar.md   # 每页四层骨架 + 样式约定 + 视觉主角轮换规则
grep -A 20 "决策速查" .claude/skills/_shared/claude-design/anti-ai-slop.md
```

> **核心原则**：Step 1 只加载 deck-grammar.md（语法骨架）；其余 references 在 Step 2 大纲确认后，按页面 layout / 组件类型 / 叙事模式按需 grep 局部段，**禁止全量 Read**。

**按需 grep**（Step 2 大纲确认后）：

| 触发条件 | 查阅指令 |
|---|---|
| 每页归属哪个 layout | `grep -n "^## Layout" references/page-layouts.md` 看清单，再 `grep -A 30 "Layout N — "` |
| 写填充函数前确定要用的组件 | `grep -n "^### " references/components-cheatsheet.md` 看清单，再按 class 拉局部 |
| 叙事模板参考 | `grep -n "^## " references/gold-snippets.md` 看 8 种叙事模式，按页面定位选 1-2 种 |
| 含架构图 / 流程图形状 | `grep -n "^## " references/shapes-toolkit.md` 看 10 种 shape，按需 grep |

### Step 2：确认大纲

用户提供内容大纲（几个 Tab、每页什么内容）。模型整理为 NAV 结构：

```javascript
NAV = [
  { group: '分组名', dot: 'green', items: [
    { id: 'tab-id', icon: '📍', label: 'Tab 标题' },
  ]},
];
```

确认要点：Tab 数量（建议 5-15 个）/ 每页类型（总览 / 对比 / 清单 / 表格 / 详解 / Prompt 展示）/ 是否需 modal 弹窗。等用户确认后进 Step 3。

#### 叙事编排 4 规则（从满分产物 SOP-final.html 提炼）

1. **先冲击后解释** — 每页先放最有视觉冲击力的元素，再用卡片 / 表格解释细节
2. **结论前置** — 速查表 / 推荐方案放在详情展开之前
3. **参考细节折叠** — 目录列表 / 评测原理 / 技术参数用 accordion 折叠
4. **时间线顺序** — sidebar 页面顺序应匹配内容的时间线或逻辑依赖

#### 节奏编排

去 AI 味 6 规则 + 推荐序列 + 反面教材 → 见 `references/gold-snippets.md §7 节奏编排`（单一来源，Step 4 填充前 `grep -A 40 "^## 7" references/gold-snippets.md`）。

### Step 3.0：类名预检（生成骨架前必做）

写任何页面之前，先确认所用类都在对应模板的 `<style>` 里定义（纯 deck = `deck-template.html`，sidebar Doc = `ppt-template.html`）。下例为 sidebar Doc：

```bash
node -e "
const f = require('fs').readFileSync('.claude/skills/ppt/assets/ppt-template.html','utf8');
const used = ['page-hero','hero-headline','page-split','stat-card','grid2','grid3','grid4',
  'flow-h','pipe','cmp-table','quote-block','eyebrow','hairline','display','section-label'];
used.forEach(c => console.log(c.padEnd(24), f.includes('.'+c+'{') || f.includes('.'+c+' ') ? '✓' : '✗'));
"
```

任一 ✗ 时停下：
- 类名是 layout 标准类（见 `page-layouts.md`）→ 在 `ppt-template.html` `<style>` 里补定义（不要 inline 重写）
- 类名是临时定制 → 用 `style="..."` inline 写，不发明新 class

### Step 3：生成 Node.js 骨架脚本

遵守 HTML > 200 行铁律，用 **Node.js** 生成。先按形态选模板：

**纯 deck 范式（默认 · 演讲）**：
- 复制 `assets/deck-script-template.js` 到项目 `scripts/gen_deck_v{N}.js` 改写
- slides 为 HTML 字符串数组（每个 = 一张 `<section class="slide">`），调 `fillDeck({ title, theme:'vendor-editorial', acts, slides, outputPath })`
- 类名唯一源 = `deck-template.html`；四层骨架 + 浅深交替 + 五幕 ACTS 见 `deck-grammar.md §一`

**sidebar Doc 模式（可选 · 长文档 / SOP）**：
- 复制 `assets/script-template.js` 改写（fillTemplate 调用 + NAV / PAGE_RENDERERS 结构）
- **脚本拆分规则**（Tab ≥ 8 或产出 > 1500 行）：详见 `.claude/runbooks/html-build-split.md`

### Step 4：填充内容

**纯 deck**：按五幕叙事逐页填 slides 数组，每页对应一个 `<section class="slide">`。页面类型 → 组件映射见 `deck-grammar.md §一 可复用组件`（card-grid / bluf-grid / track-3 / code-block 等）。

**sidebar Doc**：按确认的大纲逐 Tab 填充，每个 Tab 对应一个 PAGE_RENDERERS 函数。

**页面类型 → 组件映射**：

| 页面类型 | 推荐组件 |
|---------|---------|
| 呼吸页 | page-hero（hero-accent + hero-headline + hero-sub）|
| 分隔页 | page-split（split-num + split-title + split-desc）|
| 总览页 | stat-card + grid3 + note |
| 对比页 | grid2 双栏 + card |
| 清单页 | ck-item 列表 |
| 表格页 | cmp-table |
| 详解页 | card + note 混排 |
| Prompt 展示页 | prompt-block + modal |
| 竖向流程页 | pipe + pipe-node + pipe-arrow（≥ 5 步）|
| 横向流程页 | flow-h + flow-h-step（≤ 4 步）|
| 嵌套图页 | nest-outer/mid/inner |
| 金句页 | quote-block（em 高亮关键词）|
| 流程图页 | flowchart skill 独立产出 → 截图嵌入 |
| 架构图页 | 手画 platform-card 三段式 + 中央 callout，或 flowchart skill 截图 |

**填充节奏**：先填前 2-3 个 Tab → 用户确认方向 → 批量填剩余。

**每个 Tab 填充后 2 层语法校验**（任一不过立即修）：
1. `node --check <生成脚本路径>`：检查生成脚本本身（能抓 `'\\n'` 等字符串转义错误）
2. 生成 HTML 后 `node -e "new Function(scriptMatch[1])"` 检查内嵌 `<script>` 块的 JS 语法

仅校验第 2 层会漏掉第 1 层 bug。

**Node.js 模板字符串规范**：

```javascript
const renderers = {
  'overview': `
    <div class="page active">
      <div class="page-title">标题</div>
      <div class="card"><!-- 卡片内容 --></div>
    </div>
  `
};
```

- 使用**模板字符串**（反引号），不是普通引号
- HTML 属性用**双引号** `class="page"`
- 内容含 `${}` 需转义 `\${}`（很少见）
- 如需展示可复制文本，用 prompt-block 组件

**演示模式 Doc / Deck 双模式** → `Read references/doc-deck-modes.md`（键盘操作 / NAV 扩展字段 / chrome / data-step / 大文档模式集成）。

### Step 5：自检

```bash
# 1. Tab 完整性：NAV items 数量 = PAGE_RENDERERS 函数数量
grep -c "PAGE_RENDERERS\[" {产出物}

# 2. HTML 结构闭合
grep -c '</html>' {产出物}

# 3. Sidebar 可导航
grep "renderNav\|goPage" {产出物} | head -5

# 4. 每个 page 有 active class
grep -c 'class="page active"' {产出物}

# 5. 中文排版（pangu / heti，全工程唯一规则源）
#    PPT HTML 是 node 脚本生成的，hook 触发不到，必须显式调
python3 scripts/check_cjk_punct.py {产出物} --strict
# RC=2 阻断；warn 级（中英文间空格 / 全角标点旁空格）只 stderr 提示，不阻断
```

### Step 5b：增量升版（已有 vN → vN+1）

PPT 是 `fill-template.js` 拼 PAGE_RENDERERS / NAV 数据驱动的，**升版只改源文件重跑**，禁直接 Edit HTML：

- 加 / 改 / 删页面：改 `pages_*.js` 中对应 renderer + `nav` 数组
- 改文案 / 数据：改对应 page renderer 内的 JS 字符串
- 加 Tab：在 nav 数组追加 + 加 renderer
- 重跑 `node scripts/gen_ppt_v{N}.js` 出新版本 HTML

老项目若还有手写 Edit / patch_ppt_* 脚本，参 leaderboard / activity-center 反向拆分思路：把 HTML 反向切回 `pages_*.js` 散件 + orchestrator，archive 老 patch 脚本。

### Step 6：生成口播稿 docx（可选）

HTML 产出物交付后按需生成 → `Read references/ppt-notes-docx.md`（触发规则 / 产物路径 / python-docx 模板 / 排版规格 / 写作要求）。

## 自检清单

**通用**：
- [ ] HTML 结构闭合（`</html>` 存在）
- [ ] > 200 行的产出物通过 Node.js 脚本生成
- [ ] 产出物命名符合 `ppt-{主题}-v{N}.html` 规范
- [ ] 讲人话 grep 无命中（决策 N / A-N 裸编号）
- [ ] 中文排版 `check_cjk_punct.py --strict` 通过

**纯 deck 范式**：
- [ ] slides 数组每项类名都在 `deck-template.html` `<style>` 中定义（不发明新 class）
- [ ] 浅深底交替（封面 / 章节转场 / 收尾用 `.slide.dark`，论证页浅底）
- [ ] 三字体分层正确（衬线标题 / 无衬线 300 正文 / mono 元信息）
- [ ] `← → / Space` 翻页，`Home/End` 跳首尾，边缘点击可翻
- [ ] 顶部五幕章节胶囊随页高亮，`fit()` 缩放贴合窗口
- [ ] 每页有 `.deck-foot` + `.pagenum` 占位（运行时注入页码）

**sidebar Doc 模式**：
- [ ] NAV items 数量 = PAGE_RENDERERS 函数数量
- [ ] 所有组件 class 名在 `assets/ppt-template.html` 的 `<style>` 中有定义（唯一类名源 · Step 3.0 类名预检；`components-cheatsheet.md` 仅人读速查）
- [ ] sidebar 导航正常高亮
- [ ] Tab 切换正常，页面渲染正确
- [ ] 如有 prompt 展示，复制按钮功能正常
- [ ] 按 `P` 键可进入 Deck 模式（sidebar / header 消失，全屏横排翻页）
- [ ] Deck 模式下 `→` / `Space` 翻页，`ESC` 退出回 Doc 模式
- [ ] Deck 模式底部圆点导航点击可跳转，HUD 显示当前页号 / 总页数
- [ ] 含 `data-step` 的元素在 Doc 模式下全显；Deck 模式下默认隐藏，按 `→` 逐步揭示
- [ ] URL `#deck:{pageId}` 刷新后直达 Deck 模式定位到该页
- [ ] 类名预检（Step 3.0）通过

## References 索引

### 必读

| 文件 | 触发条件 |
|------|---------|
| `.claude/runbooks/html-pipeline.md` | HTML pipeline 通用规则 |
| `references/deck-grammar.md` | Step 1 必读（每页四层骨架 + 样式约定 + 视觉主角轮换） |
| `_shared/claude-design/anti-ai-slop.md` | grep 决策速查表，不全量 Read |

### 按需读

| 文件 | 触发条件 |
|------|---------|
| `references/ppt-step0-clarification.md` | Step 0 需求澄清门完整规则（用途识别 / 主题色 9 套 / 子门细则 / 逐字稿三铁律） |
| `references/doc-deck-modes.md` | Step 4 Doc / Deck 双模式细节（键盘 / kicker / data-step / 大文档模式集成） |
| `references/ppt-notes-docx.md` | Step 6 口播稿 docx（触发规则 / python-docx 模板 / 排版规格） |
| `references/page-layouts.md` | Step 2 大纲确认后按 layout 名 grep |
| `references/components-cheatsheet.md` | Step 3 写填充函数前按 class 名 grep |
| `references/gold-snippets.md` | 叙事模板参考（8 种叙事模式） |
| `references/shapes-toolkit.md` | 含架构图 / 流程图形状（10 种 shape） |
| `references/full-decks.md` | ⚠️ 归档参考：素材已移至 `assets/archive/full-deck-refs/`，本文为历史索引 |
| `references/page-layouts.md` 内单页样例 | ⚠️ 归档参考：HTML 已移至 `assets/archive/page-layouts/`，layout 名仍可 grep |
| `references/presenter-notes.md` | 逐字稿方法论（演讲型门附逐字稿三铁律 + S 键独立 popup 提词器） |

### 执行类（模型不读，脚本调用）

**纯 deck 范式（默认）**：
- `assets/deck-template.html` — 1280×720 舞台 + ~20 组件 + code-block，由 deck-fill.js 拼接（唯一类名源）
- `assets/deck-fill.js` — `fillDeck(...)` 拼 slides 数组；`assets/deck-runtime.js` — 注入的运行时（翻页 / ACTS / fit）
- `assets/deck-script-template.js` — 项目 gen 脚本范例，复制到 `scripts/` 改写

**sidebar Doc 模式（可选）**：
- `assets/ppt-template.html` — 骨架 CSS + JS，由 fill-template.js `open().read()` 自动拼接
- `assets/fill-template.js` / `assets/script-template.js` / `scripts/gen-notes-docx.py` / `assets/presenter-mode.js` — 脚本，通过 node / python3 调用
