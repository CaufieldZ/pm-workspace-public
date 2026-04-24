<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: ppt
description: >
  当用户提到「PPT」「方案文档」「宣讲材料」「SOP 手册」时触发,产物为 HTML 多 Tab 信息文档。
argument-hint: [内容大纲文件 或 口述大纲]
type: standalone
output_format: .html
output_prefix: ppt-
depends_on: []
optional_inputs: [context.md]
consumed_by: []
scripts:
  fill-template.js: "Step B fill 模板 — 复制到项目 scripts/ 改写"
  gen-notes-docx.py: "导出演讲者备注 docx — python3 gen-notes-docx.py <html>"
  presenter-mode.js: "运行时演讲模式 JS — 骨架脚本自动内联，不手动读"
---
<!-- pm-ws-canary-236a5364 -->

# PPT 信息文档

## 定位

独立产出型 Skill。把方案/SOP/方法论类内容生成 HTML 多Tab信息文档（等同 PPT 给人讲方案）。

和 architecture-diagrams 的区别：
- **architecture-diagrams**：项目内链路型，依赖 scene-list + context.md，按 13 种页面类型输出架构图集
- **ppt**：独立产出型，不依赖任何链路。用户提供内容大纲，按模板输出多Tab信息文档

用途：团队分享、对外宣讲、方法论沉淀、SOP 手册。

## 核心原则

1. **数据驱动侧边栏**：NAV 数组驱动 sidebar 导航，不硬编码
2. **PAGE_RENDERERS 分页渲染**：每个 Tab 一个渲染函数，不堆砌 HTML
3. **组件复用**：card / grid / tag / note / table / ck-item 等组件统一使用，视觉一致
4. **内容与骨架分离**：骨架脚本负责结构，填充脚本负责内容
5. **Prompt 展示用 modal**：如需展示 prompt 文本，用 modal 弹窗 + 复制按钮

### 校验标准

- Tab 能切换，侧边栏高亮跟随 = 通过
- 所有组件 class 名在 cheatsheet 中有定义 = 通过
- 产出物 > 200 行 → 必须用 Node.js 脚本生成（见 Step 3）
- 产出物 > 1500 行或 Tab ≥ 10 → 必须按「大文档源码拆分」模式（见 Step 3b），不能把所有页面塞进单脚本

### 修改纪律（强制）

PPT 产出物一旦脚本化生成，HTML 就是**只读产物**：

- 禁止直接 Edit / Write 生成出来的 HTML 产物（如 SOP-final.html）
- 改动只进 `scripts/sop-src/pages/{id}.js` 或对应 source 文件，改完 `node gen_{主题}_v{N}.js` 重新生成
- 小到改一个文案也走脚本，不要「就这一处我直接改 HTML」——下次升版脚本会把改动覆盖
- 修改后必须 diff 验证产出物结构是否预期（行数对齐、关键页面存在）

违反此规则 = 下次迭代必定改错。

## 执行步骤

### Step 1：读取参考文件

**必读**（产出前加载）：
- `references/deck-grammar.md` — 每页四层骨架 + 样式约定 + 视觉主角轮换规则
- `references/components-cheatsheet.md` — 组件速查表
- `references/gold-snippets.md` — 满分产物片段库（叙事模式 + 结构骨架参考）
- `.claude/skills/_shared/claude-design/anti-ai-slop.md` — 反 AI slop 六禁 + 字号 / 颜色 / 留白规范（只 grep 决策速查表部分，不全量 Read）

**执行类**（模型不读，脚本调用）：
- `references/ppt-template.html` — 骨架 CSS + JS，由 fill-template.js `open().read()` 自动拼接
- `references/fill-template.js` / `gen-notes-docx.py` / `presenter-mode.js` — 脚本，通过 node/python3 调用

**用户输入**：
- 用户提供的内容大纲（文件或口述）

### Step 2：确认大纲

用户提供内容大纲（几个 Tab、每页什么内容）。模型整理为 NAV 结构：

```
NAV = [
  { group:'分组名', dot:'green', items:[
    { id:'tab-id', icon:'📍', label:'Tab 标题' },
    ...
  ]},
];
```

确认要点：
- Tab 数量（建议 5-15 个，超过 15 考虑合并）
- 每页类型（总览 / 对比 / 清单 / 表格 / 详解 / Prompt 展示）
- 是否需要 modal 弹窗

等用户确认大纲后再进入 Step 3。

### 叙事编排规则（从满分产物 SOP-final.html 提炼）

填充每页内容时遵守以下 4 条叙事规则：

1. **先冲击后解释** — 每页先放最有视觉冲击力的元素（全景图/数据/对比图），再用卡片/表格解释细节。不要先铺定义再亮图。
2. **结论前置** — 速查表/推荐方案放在详情展开之前。听众先知道"用哪个"，再看"为什么"。
3. **参考细节折叠** — 目录列表/评测原理/技术参数等参考内容用 accordion 折叠，不抢主视觉空间。
4. **时间线顺序** — sidebar 页面顺序应匹配内容的时间线或逻辑依赖。不要把"事后"内容放在"事前"位置。

违反这些规则是满分产物迭代中最常犯的错误。每页填充完后回读检查叙事顺序。

### 节奏编排规则（去 AI 味）

AI 生成 PPT 最大破绽不在「花哨」，而在「太均匀」——每页都是 section-label → card/grid → note 的三明治，没有节奏变化。遵守以下 5 条：

1. **必须有呼吸页** — 每 4-6 个内容页之间插入一个 `page-hero`（大字居中留白）或 `page-split`（分隔带）。首页强烈建议用 `page-hero`。
2. **相邻两页禁止同一主组件** — 刚用了 `grid3`，下一页不能又是 `grid3`；刚用了 `cmp-table`，下一页换 `pipe` 或 `flow-h`。主组件指占据页面 ≥50% 面积的组件。
3. **横竖交替** — 竖向流程（`pipe`）和横向流程（`flow-h`）交替使用，同文档内不要全是 `pipe`。≤4 步用 `flow-h`，≥5 步用 `pipe`，中间混排最佳。
4. **emoji 密度控制** — `section-label` 不放 emoji，只在 `page-title` 和 `pipe-icon` 放。密度：每页 ≤3 个 emoji。
5. **文字密度控制** — 单页 HTML 渲染函数 ≤60 行。超过则拆分为子组件或用 accordion 折叠。金句/判断句用 `quote-block`（大字居中斜体）单独成段，不要塞进 `note` 盒子里。
6. **分步揭示节奏** — 呼吸页（`page-hero`）金句和清单页条目可加 `data-step`，演示时逐步揭示增加悬念。呼吸页主标题加 `data-step="1"`，清单各条加 `data-step="1"/"2"/"3"`。Doc 模式查阅不受影响（自动全显）。

### Step 3：生成 Node.js 骨架脚本

遵守 HTML > 200 行铁律，用 **Node.js** 脚本生成（优于 Python，避免三层转义地狱）。

**CSS 变量与字体引入纪律（弱模型易踩坑）**：

1. **禁止手抄 `:root` 整块 token 定义**。所有 `--cd-*` 变量源头唯一：`.claude/skills/_shared/claude-design/tokens.css`。脚本里必须 `fs.readFileSync(tokens.css)` 拼进 CSS 模板，项目级扩展 token（如 `--cd-surface2` / `--cd-ok`）在 tokens.css 后再加一个小 `:root { ... }` 追加即可。手抄的代价：tokens.css 改字体 / 改色，产物不跟着变。
2. **字体 `<link>` = 实际用到的字体**，不照搬 tokens.css 注释里那段完整 CDN URL。CJK PPT 最小集 = Noto Sans SC + Noto Serif SC + JetBrains Mono 三家。引 Source Serif 4 / Inter 但 CSS 里没用 = 白下载 ~60KB。
3. **CJK 混排字体栈铁律**：`--cd-sans` / `--cd-serif` 中文字体必须排在英文字体前。tokens.css 默认值是英文优先的（历史原因），用的时候在追加的 `:root` 里覆盖成 `'Noto Sans SC','Inter',system-ui` 和 `'Noto Serif SC','Source Serif 4',Georgia,serif`。

**使用 Skill 内置填充脚本**：

```javascript
#!/usr/bin/env node
/**
 * gen_ppt_{主题}_v1.js — PPT 信息文档生成脚本
 * 使用 Skill 内置的 fill-template.js 模块
 */
const { fillTemplate } = require('../../../../.claude/skills/ppt/references/fill-template.js');

// 定义 NAV 数据
const NAV = [
  { group: '分组名', dot: 'green', items: [
    { id: 'tab-id', icon: '📍', label: 'Tab 标题' }
  ]}
];

// 定义 PAGE_RENDERERS（每个 Tab 的渲染函数）
// 使用 JavaScript 模板字符串（反引号），HTML 属性用双引号，无需转义换行
const renderers = {
  'tab-id': `
    <div class="page active">
      <div class="page-title">标题</div>
      <div class="page-subtitle">副标题</div>
      <!-- 页面内容 -->
    </div>
  `
};

// 生成文件
fillTemplate({
  title: '文档标题',
  nav: NAV,
  renderers: renderers,
  outputPath: 'projects/{项目名}/deliverables/ppt-{主题}-v1.html'
});
```

脚本保存到项目 `scripts/` 目录。

**脚本拆分规则（Tab ≥ 8 时强制）**：

- 主脚本 `gen_ppt_{主题}_v1.js`：≤ 80 行，只做 require + NAV 定义 + 调用 fillTemplate
- 渲染函数按 NAV group 拆分为 `pages_group0.js` / `pages_group1.js`，每文件 ≤ 150 行
- 每个渲染函数返回 HTML 字符串，用 JS 模板字符串（反引号 `` `...` ``）包裹，HTML 属性用双引号

### Step 3b：大文档源码拆分（产出物 > 1500 行或 Tab ≥ 10）

当 PPT 规模达到「SOP 手册」级（3000+ 行、20+ Tab），单脚本会膨胀到 2000 行以上，修改一页仍需在巨型文件里 grep 定位——失去脚本化的意义。此时必须采用「每页一个源文件 + orchestrator 编排」模式。

**标准目录结构**（以 `projects/htx-workflow-pre/` 下 SOP-final.html 为参考实现）：

```
scripts/
  gen_sop_v1.js              # orchestrator（≤ 150 行，只做读文件 + concat）
  sop-src/
    head.html                # <head> 头部（meta + title + 字体）
    styles.css               # 全局 CSS（不含 <style> 标签）
    shell.html               # </head><body> + 壳（modal/sidebar/main 骨架）
    nav.js                   # NAV 数组 + renderNav + goPage
    prompts.js               # PROMPTS 数据（如有）
    templates.js             # TEMPLATES 数据（如有）
    renderer-head.js         # renderPage + const PAGE_RENDERERS = {}
    renderer-track-a.js      # 泛用辅助函数（如有跨页复用的 renderer）
    utils.js                 # 工具函数（escHtml / copyPrompt 等）
    init.js                  # renderNav(); renderPage();
    pages/
      home.js                # PAGE_RENDERERS['home'] = function(c) { ... };
      context.js             # 每页一个独立文件
      ...                    # 文件名 = NAV 中的 id
```

**orchestrator 职责**（极简）：

- 按固定顺序读取 sop-src/ 下的各文件
- concat 时在正确位置插入 `<style>` / `</style>` / `<script>` / `</script>` 等包装标签
- 写到 `../{产出物}.html`，打印行数和字节数供核对

**反向拆分方法**（对已有大 HTML）：

1. `grep -n "^PAGE_RENDERERS\[" {产出物}` 列出所有页面起始行
2. 用 `awk 'NR==N {print}'` 核对页面边界（comment / 空行 / `};`）
3. `sed -n 'start,endp' {产出物} > sop-src/pages/{id}.js` 字节级抽取每页
4. 同法抽取 CSS / shell / 数据区 / 工具函数
5. 写 orchestrator → 运行 → `diff -q` 验证产出物与原文件字节级一致

**修改流程**：

- 改一页 = 改 `sop-src/pages/{id}.js`（通常 < 300 行，可以 Read 全文）
- 改导航 = 改 `sop-src/nav.js`
- 改全局样式 = 改 `sop-src/styles.css`
- 改完 `node gen_{主题}_v1.js` 重新生成，diff 确认只改了预期部分

**收益**：
- 原来改一页要在 3000+ 行 HTML 里 grep 定位、担心改错 → 现在改 100-300 行的独立文件
- 新增页面 = 加一个 pages/xxx.js + 在 nav.js 注册，不用在巨型文件里插入
- 回退单页变更 = git checkout 一个文件，不影响其他页

**为什么用 Node.js 而不是 Python**：

Python 处理「Python → JS 字符串 → HTML」三层嵌套时转义极易出错：
- `"` 在 Python 字符串里需要转义为 `\"`，但 `"` 在 Python 中不是合法转义 → `SyntaxError`
- 用 raw string `r'''...'''` 写入文件变成 `\n`（字面两个字符）→ JS 报错
- Node.js 的模板字符串天然支持多行 HTML，无需手动处理换行转义

### Step 4：填充内容

按确认的大纲逐 Tab 填充内容。每个 Tab 对应一个 PAGE_RENDERERS 函数。

**页面类型 → 组件映射**：

| 页面类型 | 推荐组件 | 示例 |
|---------|---------|------|
| 呼吸页 | page-hero（hero-accent + hero-headline + hero-sub） | 首页开场、章节金句 |
| 分隔页 | page-split（split-num + split-title + split-desc） | Part 之间的转场 |
| 总览页 | stat-card + grid3 + note | 数据概览 |
| 对比页 | grid2 双栏 + card | 优劣势对比、方案对比 |
| 清单页 | ck-item 列表 | 步骤、检查项 |
| 表格页 | cmp-table | 规格对比、价格表 |
| 详解页 | card + note 混排 | 概念解释、功能说明 |
| Prompt 展示页 | prompt-block + modal | 可复制的 Prompt/模板 |
| 竖向流程页 | pipe + pipe-node + pipe-arrow | ≥5 步流程 |
| 横向流程页 | flow-h + flow-h-step（fh-num + fh-label + fh-desc） | ≤4 步流程、依赖链 |
| 嵌套图页 | nest-outer/mid/inner | 层级关系、架构嵌套 |
| 金句页 | quote-block（em 高亮关键词） | 核心判断、分叉问题 |

填充过程中：
- 先填充前 2-3 个 Tab → 用户确认方向
- 确认后批量填充剩余 Tab
- **每个 Tab 填充后 2 层语法校验**，任一不过立即修正：
  1. `node --check <生成脚本路径>`：检查生成脚本本身（能抓 `'\\n'` 等字符串转义错误、console 输出里误写的代码）
  2. 生成 HTML 后用 `node -e "new Function(scriptMatch[1])"` 检查内嵌 `<script>` 块的 JS 语法
  仅校验第 2 层会漏掉第 1 层 bug（脚本能跑出产物，但 console 打印或其他字符串处理错误）。

**HTML 内容书写规范（Node.js 模板字符串模式）**：

```javascript
const renderers = {
  'overview': `
    <div class="page active">
      <div class="page-title">标题</div>
      <div class="page-subtitle">副标题</div>
      <div class="card">
        <!-- 卡片内容 -->
      </div>
    </div>
  `
};
```

注意：
- 使用 **模板字符串**（反引号 `` `...` ``），不是普通引号
- HTML 属性用 **双引号** `"class="page"`
- 内容中如果包含 `${}` 需要转义为 `\${}`（很少见）
- 内容中如果包含反引号 `` ` `` 需要转义为 `\``（很少见）
- 如需展示可复制文本，用 prompt-block 组件

### 演示模式（Presenter Mode）

所有通过 `fill-template.js` 生成的产物自动内置演示模式，无需额外操作。

**切换方式**：打开 HTML 后按 `P` 键切换 Doc ⇄ Presenter。

**键盘操作**：

| 按键 | 动作 |
|------|------|
| `→` / `Space` / `PageDown` | 下一步（先显 data-step，再翻页） |
| `←` / `PageUp` | 上一步（先退 data-step，再退页） |
| `Home` / `End` | 跳到首页 / 末页 |
| `ESC` | 退出演示，回到 Doc 模式 |
| `P` | 再次按返回 Doc 模式 |

**分步揭示（Keynote Build-in 同款）**：

元素加 `data-step="N"` 属性，演示时按 `→` 逐步显现，全部显完才翻到下一页：

```html
<div class="page-hero">
  <div class="hero-headline" data-step="1">核心结论</div>
  <div class="hero-sub" data-step="2">补充说明</div>
</div>

<div class="card">
  <div class="ck-item" data-step="1">第一条</div>
  <div class="ck-item" data-step="2">第二条</div>
  <div class="ck-item" data-step="3">第三条</div>
</div>
```

Doc 模式（侧边栏查阅）下所有 `data-step` 内容自动全显，不影响查阅体验。

**大文档模式（Step 3b）演示模式集成**：

Step 3b 拆分模式下 fill-template.js 不参与，需手动集成：

1. 将 `skill/references/presenter-mode.css` 复制到 `sop-src/presenter.css`
2. 将 `skill/references/presenter-mode.js` 复制到 `sop-src/presenter.js`
3. 在 `sop-src/shell.html` 的 `</main>` 后追加：
   ```html
   <div id="presenterHUD"></div>
   <div id="presenterHelp">← → 翻页 · Space 下一步 · ESC 退出</div>
   <div id="presenterEnterHint">[P] 演示</div>
   ```
4. 在 orchestrator 中，`styles.css` 后拼接 `presenter.css`，`init.js` 前拼接 `presenter.js`

### Step 5：自检

产出物声称完成前必须执行：

```bash
# 1. Tab 完整性：NAV items 数量 = PAGE_RENDERERS 函数数量
grep -c "PAGE_RENDERERS\[" {产出物}
grep -c "{ id:" {产出物}  # 或从脚本 NAV 数

# 2. 组件 class 名合法
# 对照 components-cheatsheet.md 检查

# 3. 浏览器可打开（至少检查 HTML 结构闭合）
grep -c '</html>' {产出物}

# 4. Sidebar 可导航
grep "renderNav\|goPage" {产出物} | head -5

# 5. 每个 page 有 active class（数量应 = PAGE_RENDERERS 函数数量）
grep -c 'class="page active"' {产出物}

# 6. 行数统计
wc -l {产出物}
```

全部通过后交付 HTML 产出物，然后进入 Step 6。

### Step 6：生成口播稿 docx（可选）

**触发规则**：默认不生成。HTML 产出物交付后 Claude 主动问一次：

> 「这是最终版吗？需要生成 docx 口播稿吗？（微信发手机当提词器）」

用户说「要」才执行；用户明示「最终版了」或「出口播稿」也直接触发；迭代版本说「不要」则跳过。

**产物**：`ppt-{主题}-notes-v{N}.docx`（放 deliverables 同目录）

**技术选型**：python-docx（参考模板 `references/gen-notes-docx.py`）

项目使用时复制到 `projects/{项目}/scripts/gen_notes_v{N}.py`，填入 NOTES 数据：

```python
NOTES = [
  { 'id': 'home', 'title': '总览 & 选路',
    'core': '一句话核心论点',
    'points': ['要点 1', '要点 2', '要点 3'],
    'transition': '→ 下一页讲 XXX，承接关系是 YYY' },
  # ... 每页一个对象
]
OUTPUT_PATH = '../deliverables/ppt-{主题}-notes-v1.docx'
```

运行 `python3 gen_notes_v1.py` 生成 docx。

**排版规格**（手机阅读优化）：
- 正文 16pt，行距 1.5
- 标题 20pt 粗体（微软雅黑）
- 每页之间分页符——微信打开翻一页看一页
- 过渡句斜体灰色，视觉上和正文内容区分

**写作要求**：
- 每页 100-200 字，整份 ≤ 3000 字
- 是演讲提纲不是逐字稿——看着能讲，不是照念
- 引用的数据/术语必须和 HTML 内容一致
- 过渡句帮演讲者自然衔接到下一页

## 输出格式

- 格式：单文件 `.html`
- 命名：`ppt-{主题}-v{N}.html`
- 存放：`projects/{项目}/deliverables/`（如有项目关联）或 `deliverables/`（独立产出）
- 版本管理：遵循 pm-workflow 8.2 版本管理规则

### 设备规范

继承 pm-workflow 第三章暗色主题：
- 侧边栏 240px，深色 `--bg2`
- 主内容区 max-width 1200px
- 字体：Noto Sans SC + Inter + JetBrains Mono
- 配色变量：以 `--bg: #0a0c10` 系为准

### 组件规范

详见 `references/components-cheatsheet.md`，核心组件：
- **card** — 通用卡片容器
- **grid2/3/4** — 响应式网格
- **tag-\*** — 彩色标签（blue/green/orange/purple/red）
- **note** — 左边框提示框（蓝/绿/橙）
- **cmp-table** — 对比表格
- **ck-item + ck-num** — 编号清单
- **prompt-block** — 代码/文本展示块（含复制按钮）
- **pipe/pipe-node** — 纵向流程链（≥5 步）
- **flow-h/flow-h-step** — 横向时间线（≤4 步，含 fh-num/fh-label/fh-desc；支持 .active/.done 状态）
- **page-hero** — 呼吸页（hero-accent + hero-headline + hero-sub，大量留白居中）
- **page-split** — 分隔带（split-num + split-title + split-desc，Part 间转场）
- **stat-card** — 数字统计卡（stat-val + stat-lbl，替代 inline style 的 hero-num）
- **quote-block** — 金句/引言块（大字居中斜体，em 标签高亮关键词）
- **icon-box** — 44px 圆角图标容器
- **flow-chip** — 行内胶囊标签（替代 inline 的 padding+bg+border-radius 组合）
- **hero-num** — 大数字展示（保留兼容，新代码推荐 stat-card）
- **track-card** — 路径/方案选择卡片
- **accordion** — 折叠展开
- **gallery-card** — 图片/案例展示
- **modal-overlay** — 全屏弹窗
- **score** — 分数/评级徽章

## 自检

- [ ] NAV items 数量 = PAGE_RENDERERS 函数数量
- [ ] 所有组件 class 名在 cheatsheet 中有定义
- [ ] sidebar 导航正常高亮
- [ ] Tab 切换正常，页面渲染正确
- [ ] HTML 结构闭合（`</html>` 存在）
- [ ] > 200 行的产出物通过 Node.js 脚本生成
- [ ] 产出物命名符合 `ppt-{主题}-v{N}.html` 规范
- [ ] 如有 prompt 展示，复制按钮功能正常
- [ ] 按 `P` 键可进入演示模式（sidebar/header 消失，内容居中放大）
- [ ] 演示模式下 `→`/`Space` 能翻页，`ESC` 退出回 Doc 模式
- [ ] 含 `data-step` 的元素在 Doc 模式下全显；演示模式下默认隐藏，按 `→` 逐步揭示
