# PPT 整页骨架速查（10 种）

改造自歸藏 layouts.md，换成 Claude Design 暗色 token + 现有组件库。
每种 layout 给出完整可粘贴的 `<div class="page">` 代码块。

> **使用方式**：在 PAGE_RENDERERS 对象里粘贴，替换 `【…】` 占位文案，其余结构不动。
> **Deck 模式元数据**（`.deck-chrome` / `.deck-foot`）在 Phase 3 任务 6 实现，此处保留注释槽位。

---

## Layout 1 — Hero Cover（开场封面）

**用途**：第 1 页必用，章节 Part 幕末可复用（改文案）。
**主组件**：`page-hero` + eyebrow + display-xl + lede + hairline-accent
**节奏**：全页留白 ≥ 60%，去掉一切装饰，字型做全部工作。

```html
<div class="page active film-grain">
  <!-- deck-chrome 槽位（Phase 3 任务 6 自动注入） -->

  <div class="watermark-tl">【PART I】</div>

  <div class="page-hero">
    <div class="eyebrow eyebrow-accent">【栏目标签 · eg. PM WORKFLOW 01】</div>
    <h1 class="display display-xl" style="line-height:1.28">
      【主标题<br>两行效果最佳】
    </h1>
    <div class="hairline-accent" style="margin:28px auto;"></div>
    <p class="lede">【副标题一句话，15-25 字，不超过两行】</p>
  </div>

  <!-- deck-foot 槽位 -->
</div>
```

**要点**：
- `display-xl` line-height 含 CJK 时必须 ≥ 1.25（这里用 1.28）
- `film-grain` 给页面加 2% 噪点，去掉 AI 感；只在 Hero / Divider 页用
- `watermark-tl` 低调水印，rgba 16% 透明，不抢主视觉
- `hairline-accent` 80px 蓝线做节奏停顿
- 加 `data-step` 到 headline / lede 可启用 Deck 分步揭示

**常见踩坑**：
- 禁止加 emoji 到标题（反 AI slop 六禁之一）
- 禁止在 eyebrow 写中文（mono uppercase 做栏目标签，中文 tracking 失效）

---

## Layout 2 — Act Divider（章节幕封）

**用途**：每个 Part 之间的转场页，仅文字，极简。
**主组件**：`page-split` + split-num + split-title + split-desc

```html
<div class="page active film-grain">
  <!-- deck-chrome 槽位 -->

  <div class="page-split">
    <div class="split-num">【01】</div>
    <div>
      <div class="eyebrow" style="margin-bottom:16px;">【Act I · 英文章节名】</div>
      <div class="split-title">【章节中文标题】</div>
      <p class="split-desc">【1-2 句章节概述，不超过 60 字，说清这一 Part 要解决什么问题】</p>
    </div>
  </div>

  <!-- deck-foot 槽位 -->
</div>
```

**要点**：
- `split-num` 字号 72px + opacity 0.15，做装饰背景数字
- `split-title` 28px 900 weight，这里是全页视觉重心
- eyebrow 写英文章节名，搭配 split-title 中文，形成双语节奏
- `film-grain` 同 Layout 1

**常见踩坑**：
- `split-num` 写 1/2/3 即可，不要写「第一章」——数字做装饰，文字做语义
- split-desc 禁止抄 page-title 内容（同义重复 = AI 味）

---

## Layout 3 — Big Numbers（数据大字报）

**用途**：抛核心指标 / 业务数据，3-6 个大数并排。
**主组件**：`grid3` + figure-num + figure-lbl + hairline

```html
<div class="page active">
  <div class="eyebrow eyebrow-accent">【数据区间 · eg. Q1 2025】</div>
  <h2 class="display display-lg" style="margin-bottom:8px;">【核心指标标题】</h2>
  <p class="lede" style="margin-bottom:40px;">【一句话交代数据背景，来源或统计口径】</p>

  <div class="hairline"></div>

  <div class="grid3" style="margin-top:40px;gap:0;">
    <div style="padding:32px 24px;border-right:1px solid var(--border2);">
      <div class="figure-num">【73%】</div>
      <div class="figure-lbl">【METRIC NAME】</div>
      <p style="font-size:12px;color:var(--t3);margin-top:8px;line-height:1.6;">【补充说明，12px，可省略】</p>
    </div>
    <div style="padding:32px 24px;border-right:1px solid var(--border2);">
      <div class="figure-num">【2.4×】</div>
      <div class="figure-lbl">【METRIC NAME】</div>
    </div>
    <div style="padding:32px 24px;">
      <div class="figure-num">【18s】</div>
      <div class="figure-lbl">【METRIC NAME】</div>
    </div>
  </div>

  <div class="hairline" style="margin-top:0;"></div>
</div>
```

**要点**：
- `figure-num` 用 Noto Serif SC，64px，有别于 mono 数字的工具感
- `figure-lbl` mono uppercase 10px，做单位 / 指标名
- 格子之间用 `border-right` 分隔，不用 `gap`，避免「卡片堆叠」感
- 上下各一条 hairline 做收束

**常见踩坑**：
- 禁止给每个数字加 card 背景（会变成「彩色卡片大字」= 典型 AI PPT）
- 数字单位写在 figure-num 里，不要拆分（「73」+「%」会对不齐）
- 禁止用 `stat-val text-green` 彩色数字（除非有功能语义，如涨跌）

---

## Layout 4 — Quote + Image（左文右图）

**用途**：身份反差 / 故事引子 / 核心判断 + 视觉证据。
**主组件**：自定义 7:5 grid + pullquote + figure

```html
<div class="page active">
  <div style="display:grid;grid-template-columns:7fr 5fr;gap:48px;align-items:center;min-height:calc(100vh - 200px);">

    <!-- 左：文字区 -->
    <div>
      <div class="eyebrow" style="margin-bottom:24px;">【KICKER · eg. THE PARADOX】</div>
      <div class="pullquote">
        【核心判断句，20-35 字，serif 28px，用 &lt;em&gt; 高亮关键词】<em>【关键词】</em>【续文】
        <div class="pullquote-cite">— 【来源：人物 / 文件 / 数据】</div>
      </div>
      <div class="hairline-accent" style="margin-top:32px;"></div>
      <p style="font-size:13px;color:var(--t3);line-height:1.8;margin-top:20px;">
        【补充说明，2-3 句，说明这个判断的背景或反常之处】
      </p>
    </div>

    <!-- 右：图片区 -->
    <figure style="margin:0;border-radius:8px;overflow:hidden;height:60vh;">
      <img src="【图片路径或 placeholder】"
           alt="【图片描述】"
           style="width:100%;height:100%;object-fit:cover;object-position:top center;">
    </figure>

  </div>
</div>
```

**要点**：
- 7:5 比例保证文字区够宽，不被图片压缩
- `figure` 用 `height:60vh` + `overflow:hidden`，img 用 `object-fit:cover`——图片只裁底部
- `pullquote` 左竖线是唯一允许的 accent 装饰
- `<em>` 在 pullquote 里颜色为 `var(--blue)`，做焦点词高亮

**常见踩坑**：
- 禁止用 `aspect-ratio` 给图片容器设比例（会撑破父容器，导致图片超出或被裁顶）
- 禁止用 `align-self: end` 贴底（会掉到文档流末尾被工具栏遮挡）
- 无真实图片时用 `.cd-placeholder`（灰底 + 文字缩写），禁止编造图片数据

```html
<!-- 无图时的 placeholder -->
<figure style="margin:0;border-radius:8px;overflow:hidden;height:60vh;background:var(--surface2);display:flex;align-items:center;justify-content:center;">
  <span style="font-family:var(--font-mono);font-size:11px;color:var(--t4);letter-spacing:.2em;text-transform:uppercase;">IMAGE PLACEHOLDER</span>
</figure>
```

---

## Layout 5 — Image Grid（图片网格）

**用途**：多图对比 / 截图实证 / 产品界面展示。
**主组件**：`grid3` + figure × 3-6（height:26vh）

```html
<div class="page active">
  <div class="eyebrow eyebrow-accent" style="margin-bottom:8px;">【VISUAL EVIDENCE · eg. COMPETITOR AUDIT】</div>
  <h2 class="display display-lg" style="margin-bottom:32px;">【图片展示标题】</h2>

  <div class="grid3" style="gap:12px;">

    <div>
      <figure style="margin:0 0 8px;border-radius:8px;overflow:hidden;height:26vh;">
        <img src="【图1路径】" alt="【图1说明】"
             style="width:100%;height:100%;object-fit:cover;object-position:top center;">
      </figure>
      <div class="eyebrow" style="margin-bottom:4px;">【CAPTION 01】</div>
      <p style="font-size:12px;color:var(--t3);line-height:1.6;">【一句图说，≤20 字】</p>
    </div>

    <div>
      <figure style="margin:0 0 8px;border-radius:8px;overflow:hidden;height:26vh;">
        <img src="【图2路径】" alt="【图2说明】"
             style="width:100%;height:100%;object-fit:cover;object-position:top center;">
      </figure>
      <div class="eyebrow" style="margin-bottom:4px;">【CAPTION 02】</div>
      <p style="font-size:12px;color:var(--t3);line-height:1.6;">【一句图说】</p>
    </div>

    <div>
      <figure style="margin:0 0 8px;border-radius:8px;overflow:hidden;height:26vh;">
        <img src="【图3路径】" alt="【图3说明】"
             style="width:100%;height:100%;object-fit:cover;object-position:top center;">
      </figure>
      <div class="eyebrow" style="margin-bottom:4px;">【CAPTION 03】</div>
      <p style="font-size:12px;color:var(--t3);line-height:1.6;">【一句图说】</p>
    </div>

  </div>
</div>
```

**要点**：
- `height:26vh` = 约 200px @1080p，刚好让 3 图并排不拥挤
- `object-position: top center` = 保留图片上部，裁掉底部（截图通常顶部是重要内容）
- eyebrow 做图注标签，比 `<figcaption>` 更有设计感

**常见踩坑**：
- 6 图以上改为 grid4 并缩小 height 为 20vh，否则溢出
- 禁止用 `aspect-ratio` 替代 `height`（见 Layout 4 踩坑说明）

---

## Layout 6 — Pipeline（纵向流程链）

**用途**：≥5 步流程、工作流、审批链路。
**主组件**：`pipe` + `pipe-node` × N + `pipe-arrow`

```html
<div class="page active">
  <div class="eyebrow eyebrow-accent" style="margin-bottom:8px;">【PROCESS · eg. CONTENT PIPELINE】</div>
  <h2 class="display display-lg" style="margin-bottom:32px;">【流程标题】</h2>

  <div class="pipe">

    <div class="pipe-node">
      <div style="flex-shrink:0;">
        <div class="eyebrow" style="margin-bottom:2px;">STEP 01</div>
        <div style="font-size:15px;font-weight:700;color:var(--t1);">【步骤名称】</div>
      </div>
      <p style="font-size:13px;color:var(--t2);line-height:1.7;font-weight:500;">
        【步骤说明，≤40 字】
      </p>
    </div>

    <div class="pipe-arrow"></div>

    <div class="pipe-node">
      <div style="flex-shrink:0;">
        <div class="eyebrow" style="margin-bottom:2px;">STEP 02</div>
        <div style="font-size:15px;font-weight:700;color:var(--t1);">【步骤名称】</div>
      </div>
      <p style="font-size:13px;color:var(--t2);line-height:1.7;font-weight:500;">
        【步骤说明】
      </p>
    </div>

    <div class="pipe-arrow"></div>

    <div class="pipe-node">
      <div style="flex-shrink:0;">
        <div class="eyebrow" style="margin-bottom:2px;">STEP 03</div>
        <div style="font-size:15px;font-weight:700;color:var(--t1);">【步骤名称】</div>
      </div>
      <p style="font-size:13px;color:var(--t2);line-height:1.7;font-weight:500;">
        【步骤说明】
      </p>
    </div>

  </div>
</div>
```

**要点**：
- `eyebrow` 做步骤编号（`STEP 01`），替代 emoji + pipe-icon 组合（遵循反 AI slop 六禁）
- `pipe-node` 用 `display:flex;gap:16px`，左侧步骤编号区固定宽度，右侧说明文字
- ≥5 步必用 pipe，≤4 步改用 Layout（横向流程见组件速查表 flow-h）
- 分支判断 / 决策树用 flowchart skill 独立产出 → 截图嵌入 PPT

**常见踩坑**：
- `pipe-node` 里禁用 emoji 当图标（六禁中的 pipe-icon 规定）
- 相邻两页禁止都用 pipe（节奏规则：竖横交替）

---

## Layout 7 — Hero Question（悬念收束）

**用途**：幕末收尾、制造悬念、引出下一章核心问题。
**主组件**：`page-hero` + display-xl（大问号）+ data-step

```html
<div class="page active film-grain">
  <!-- deck-chrome 槽位 -->

  <div class="watermark-tl">【PART II · TRANSITION】</div>

  <div class="page-hero">
    <div class="eyebrow" style="margin-bottom:24px;">【THE QUESTION · eg. BUT WAIT】</div>
    <h2 class="display display-xl" style="line-height:1.25;max-width:800px;" data-step="1">
      【大问句，15-25 字，<br>末尾用问号结束？】
    </h2>
    <div class="hairline-accent" style="margin:36px auto;" data-step="2"></div>
    <p class="lede" data-step="2">【问题的隐含前提或反常之处，一句话】</p>
  </div>

  <!-- deck-foot 槽位 -->
</div>
```

**要点**：
- `data-step` 控制 Deck 模式下问号先出、答案再出
- 问句 hero 通常是一个 Part 的最后一页，下一页是 Act Divider（Layout 2）
- 极简：去掉一切装饰，让问句本身成为视觉重心

**常见踩坑**：
- 问句不要超过 25 字（否则字号会被压缩，失去冲击力）
- `lede` 是提示，不是答案——答案在下一章

---

## Layout 8 — Big Quote（大引用页）

**用途**：核心判断 / 金句 / takeaway，独立成页，给听众留时间消化。
**主组件**：`pullquote` + `pullquote-cite` + `hairline-accent`

```html
<div class="page active">
  <div style="display:flex;flex-direction:column;justify-content:center;min-height:calc(100vh - 200px);max-width:820px;">

    <div class="eyebrow" style="margin-bottom:36px;">【TAKEAWAY · eg. THE FINDING】</div>

    <div class="pullquote">
      「【核心引用或判断，20-40 字。
      用 &lt;em&gt; 高亮 1-3 个关键词，
      不超过全文 20%。】
      <em>【关键词】</em>【句子结尾】」
      <div class="pullquote-cite">— 【来源：作者 / 研究 / 数据时间范围】</div>
    </div>

    <div class="hairline-accent" style="margin-top:40px;"></div>

    <p style="font-size:13px;color:var(--t3);line-height:1.8;margin-top:24px;max-width:600px;">
      【可选：一句背景说明，说清这个引用来自哪个场景。省略时删除此段。】
    </p>

  </div>
</div>
```

**要点**：
- `pullquote` 左竖线 + serif 28px，是最有力的「金句容器」
- 书名号「」替代引号（中文排版习惯）
- `hairline-accent` 在 pullquote 下方做视觉收束
- 背景说明字号降至 13px / t3 色，不与主引用争视觉权重

**常见踩坑**：
- 禁止用 `quote-block`（遗留组件，居中斜体 = AI 味）——统一用 `pullquote`
- 高亮词不超过 3 个，超过则失去焦点

---

## Layout 9 — Before / After（并列对比）

**用途**：旧 vs 新 / 问题 vs 方案 / As-is vs To-be。
**主组件**：`grid2` + eyebrow 分类 + 内部 hairline + `cmp-table`（可选）

```html
<div class="page active">
  <div class="eyebrow eyebrow-accent" style="margin-bottom:8px;">【COMPARISON · eg. THE SHIFT】</div>
  <h2 class="display display-lg" style="margin-bottom:40px;">【对比标题】</h2>

  <div class="grid2" style="gap:32px;align-items:start;">

    <!-- Before -->
    <div>
      <div class="eyebrow" style="color:var(--t4);margin-bottom:16px;">BEFORE · 现状</div>
      <div class="hairline-sm"></div>
      <div style="margin-top:16px;display:flex;flex-direction:column;gap:12px;">
        <div style="display:flex;gap:12px;align-items:flex-start;">
          <span style="font-family:var(--font-mono);font-size:10px;color:var(--red);margin-top:2px;flex-shrink:0;">✗</span>
          <span style="font-size:13px;color:var(--t2);line-height:1.7;">【Before 问题点 1】</span>
        </div>
        <div style="display:flex;gap:12px;align-items:flex-start;">
          <span style="font-family:var(--font-mono);font-size:10px;color:var(--red);margin-top:2px;flex-shrink:0;">✗</span>
          <span style="font-size:13px;color:var(--t2);line-height:1.7;">【Before 问题点 2】</span>
        </div>
        <div style="display:flex;gap:12px;align-items:flex-start;">
          <span style="font-family:var(--font-mono);font-size:10px;color:var(--red);margin-top:2px;flex-shrink:0;">✗</span>
          <span style="font-size:13px;color:var(--t2);line-height:1.7;">【Before 问题点 3】</span>
        </div>
      </div>
    </div>

    <!-- After -->
    <div>
      <div class="eyebrow eyebrow-accent" style="margin-bottom:16px;">AFTER · 方案</div>
      <div class="hairline-accent" style="width:48px;margin-bottom:16px;"></div>
      <div style="margin-top:0;display:flex;flex-direction:column;gap:12px;">
        <div style="display:flex;gap:12px;align-items:flex-start;">
          <span style="font-family:var(--font-mono);font-size:10px;color:var(--green);margin-top:2px;flex-shrink:0;">✓</span>
          <span style="font-size:13px;color:var(--t2);line-height:1.7;">【After 改进点 1】</span>
        </div>
        <div style="display:flex;gap:12px;align-items:flex-start;">
          <span style="font-family:var(--font-mono);font-size:10px;color:var(--green);margin-top:2px;flex-shrink:0;">✓</span>
          <span style="font-size:13px;color:var(--t2);line-height:1.7;">【After 改进点 2】</span>
        </div>
        <div style="display:flex;gap:12px;align-items:flex-start;">
          <span style="font-family:var(--font-mono);font-size:10px;color:var(--green);margin-top:2px;flex-shrink:0;">✓</span>
          <span style="font-size:13px;color:var(--t2);line-height:1.7;">【After 改进点 3】</span>
        </div>
      </div>
    </div>

  </div>

  <!-- 可选：加一行结论 -->
  <div class="hairline" style="margin-top:40px;"></div>
  <p class="pullquote" style="font-size:18px;margin-top:32px;max-width:600px;">
    【一句总结：Before → After 的核心价值转变，≤ 20 字。<em>【关键词】</em>。】
    <div class="pullquote-cite">— 【来源可省略】</div>
  </p>
</div>
```

**要点**：
- Before 区：eyebrow 用 `color:var(--t4)`（偏灰，暗示「旧/问题」）
- After 区：eyebrow 用 `eyebrow-accent`（蓝，暗示「新/方案」）
- ✗/✓ 用 mono 字体，语义色（红/绿），不要圆角徽章
- `hairline-sm` vs `hairline-accent`：Before 用灰色短线，After 用蓝色短线，视觉做暗示

**常见踩坑**：
- 两列禁止用不同背景色区分（会变成「彩色卡片对比」= AI PPT）——用 eyebrow 颜色和 hairline 类型隐性区分
- 条目数两列必须对齐（都是 3 条或都是 4 条）

---

## Layout 10 — Lead Image + Side Text（图文混排）

**用途**：信息密集图文页，图大文小，适合产品截图 + 说明。
**主组件**：自定义 8:4 grid + figure + card 内容

```html
<div class="page active">
  <div class="eyebrow eyebrow-accent" style="margin-bottom:8px;">【PRODUCT SHOWCASE · eg. THE INTERFACE】</div>
  <h2 class="display display-lg" style="margin-bottom:32px;">【页面标题】</h2>

  <div style="display:grid;grid-template-columns:8fr 4fr;gap:32px;align-items:start;">

    <!-- 左：主图区（8/12 宽） -->
    <figure style="margin:0;border-radius:10px;overflow:hidden;height:55vh;position:relative;">
      <img src="【主图路径】" alt="【主图描述】"
           style="width:100%;height:100%;object-fit:cover;object-position:top center;">
      <!-- 可选：图片内浮标注 -->
      <div style="position:absolute;bottom:16px;left:16px;right:16px;background:rgba(0,0,0,.6);backdrop-filter:blur(8px);border-radius:8px;padding:12px 16px;">
        <div class="eyebrow" style="margin-bottom:4px;">【图内标注标题】</div>
        <p style="font-size:12px;color:var(--t3);line-height:1.5;margin:0;">【图内一句补充，≤20 字】</p>
      </div>
    </figure>

    <!-- 右：文字区（4/12 宽） -->
    <div style="display:flex;flex-direction:column;gap:20px;">

      <div>
        <div class="eyebrow" style="margin-bottom:8px;">【POINT 01】</div>
        <div style="font-size:14px;font-weight:700;color:var(--t1);margin-bottom:6px;">【小标题】</div>
        <p style="font-size:13px;color:var(--t2);line-height:1.7;">【说明 1-2 句，≤30 字】</p>
      </div>

      <div class="hairline-sm"></div>

      <div>
        <div class="eyebrow" style="margin-bottom:8px;">【POINT 02】</div>
        <div style="font-size:14px;font-weight:700;color:var(--t1);margin-bottom:6px;">【小标题】</div>
        <p style="font-size:13px;color:var(--t2);line-height:1.7;">【说明】</p>
      </div>

      <div class="hairline-sm"></div>

      <div>
        <div class="eyebrow" style="margin-bottom:8px;">【POINT 03】</div>
        <div style="font-size:14px;font-weight:700;color:var(--t1);margin-bottom:6px;">【小标题】</div>
        <p style="font-size:13px;color:var(--t2);line-height:1.7;">【说明】</p>
      </div>

    </div>

  </div>
</div>
```

**要点**：
- 8:4 比例让图片占主导（67% 宽），文字做补充，不争视觉权重
- 图内浮标注用 `backdrop-filter:blur(8px)` 做玻璃质感，比白底 card 更自然
- 右侧 3 个要点用 `hairline-sm` 分隔，不用 card 包裹（去「AI 卡片堆叠」感）
- 右侧内容区不设 min-height，自然对齐主图高度

**常见踩坑**：
- 图片缺失时右侧文字会被拉伸到满宽，需要提前放 placeholder
- 浮标注超过 2 行时，图片底部会被遮挡——用 `bottom:16px` 留余量，并缩减文案

---

## 附：节奏编排参考

| 场景 | 推荐序列 |
|------|---------|
| 开场三连 | Hero Cover → Act Divider → Big Numbers |
| 问题陈述 | Big Numbers → Before/After → Hero Question |
| 方案说明 | Act Divider → Pipeline → Lead Image |
| 数据收束 | Big Quote → Image Grid → Hero Question |
| 结尾交付 | Big Numbers → Before/After → Hero Cover（改为结语版） |

**节奏铁律**（来自 SKILL.md）：
- 相邻两页禁止同一主组件
- 每 4-6 内容页插入一个 Hero 或 Divider 页
- 竖向 Pipeline 和横向 flow-h 交替使用
