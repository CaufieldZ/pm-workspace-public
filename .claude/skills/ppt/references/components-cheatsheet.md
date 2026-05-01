# PPT 组件速查表（Claude Design 编辑范式）

`ppt-template.html` 已内联全部组件类。本文档按「**Claude Design 推荐组件**」「通用结构组件」「工具类」「高级组合」「JS 工具函数」分区。

**六禁提醒**（出自 `_shared/claude-design/anti-ai-slop.md`）：禁 emoji 装饰、禁圆角卡片 + 左/顶 border-accent、禁烂大街 icon-box + emoji、禁彩色圆角徽章做编号、禁全文 font-weight:900 sans 堆叠、禁同页 ≥ 3 种强调色。

---

## Claude Design 编辑组件（优先用这些）

### `.eyebrow` — 章节 / 分类 / 编号小字

```html
<div class="eyebrow">§ 3 · 两轨工作流</div>
<div class="eyebrow eyebrow-accent">CHAPTER 01 — AI 产品工作流</div>
<span class="eyebrow">STEP 01</span>
```

- mono + uppercase + letter-spacing 0.22em + 11px
- `.eyebrow-accent` → 切换为 `--blue`
- **替代**：`.tag-blue`/`.tag-green` 彩色标签、`.hero-accent` 彩色 bg 徽章、Notion 风圆角数字圈

### `.hairline` / `.hairline-sm` / `.hairline-accent` — 1px 分隔线

```html
<div class="hairline"></div>          <!-- 全宽 1px --border 横线 -->
<div class="hairline-sm"></div>       <!-- 48px 短横线 -->
<div class="hairline-accent"></div>   <!-- 80px × 2px --blue 收尾刻度 -->
```

- 页内分段、hero 底部收尾、内容块之间的隔断
- **替代**：`.divider`（仍可用但只是 1px --border2，hairline 语义更强）、`.card` 的 `border-top:3px solid var(--color)` 顶部色条变体

### `.display` / `.display-xl|lg|md` — serif 大标题

```html
<h1 class="display display-xl">心智的<br>可塑性</h1>   <!-- 72px hero -->
<h2 class="display display-lg">一个文件长出全部产出物</h2> <!-- 48px 页标 -->
<h3 class="display display-md">简单</h3>                <!-- 32px 组件标题 -->
```

- Noto Serif SC 500 weight + letter-spacing -0.01em
- **line-height 按内容分档**（CJK 字形填满 em box，和纯英文标题不同，默认值抄错会导致两行粘连）：
  - 纯英文 display heading（如 `.display-xl` 全英 hero）：1.05 – 1.1
  - **含 CJK 的 display heading（中文 PPT 99% 情况）：1.25 – 1.35**，CJK + Latin 混排（如「在一个 Workspace 里\n连接现实世界」）下降部会和下一行中文顶端粘连，必须 ≥ 1.25
  - 组件标题（`.display-md` 32px 级）：1.2 – 1.3
  - 正文 / 段落：1.6 – 1.8（与 `content-slop-ban.md` 的「正文 1.5」对齐，偏叙事用 1.75，偏紧凑用 1.5）
- **替代**：`.hero-headline`（900 sans 堆叠）、`style="font-weight:900;font-size:16px"` inline 粗体堆

### `.lede` — hero 副标题

```html
<p class="lede">Agent 不是工具，它有自己的偏好。</p>
```

- serif 20px + weight 400 + --t2 色 + max-width 720px
- **替代**：`.hero-sub`（颜色和 size 一样但字体用 sans，editorial 感弱）

### `.section-label` — 章节分段（内联版转场）

```html
<div class="section-label">§ 6.2 — 防腐化机制</div>
```

- mono + uppercase + 大 tracking + bottom 1px border
- 用于页内分 section，非跨页转场
- 跨页转场用「整页 Hero + Part 转场」，见 gold-snippets §6

### `.figure-num` / `.figure-lbl` — editorial 数字冲击

```html
<div class="grid3 gap-6">
  <div>
    <div class="figure-num">20</div>
    <div class="figure-lbl">SKILLS COVERED</div>
  </div>
</div>
```

- figure-num = Noto Serif SC 64px 大数字（非 mono）
- figure-lbl = mono uppercase 10px 小字
- **替代**：`.stat-card` 居中卡片 + `.stat-val text-green` 彩色数字

### `.pullquote` / `.pullquote-cite` — 核心判断引用块

```html
<div class="pullquote">
  模型能替你做的事，写 SKILL.md 之前先判断是不是「你自己会做的事」。
  <div class="pullquote-cite">— PM-WORKFLOW §1</div>
</div>
```

- serif 28px + 左侧 1px --blue 竖线 + 下方 mono 小字 cite
- **替代**：`.quote-block` 居中斜体 + 蓝加粗 `<em>` 范式

### `.watermark-tl` — 低调水印

```html
<div class="page active film-grain">
  <div class="watermark-tl">PART II</div>
  <!-- ... -->
</div>
```

- 左上角 mono 11px + uppercase + rgba(255,255,255,0.16)
- 配合 `.film-grain` 用，给 Hero 页增加 editorial 质感

### `.film-grain` — 2% 噪点质感

```html
<div class="page active film-grain">...</div>
```

- 给 page 容器加这个 class 即出现 SVG noise overlay
- 只在 Hero / Part 转场页用，内容密集页不加

---

## 通用结构组件

### `.page` — 页面容器

```html
<div class="page active">
  <div class="page-title">标题</div>
  <div class="page-subtitle">副标题（可选，多数情况改用 .lede）</div>
  <!-- 内容 -->
</div>
```

- 每个 Tab 顶层容器，`.active` 控显隐，`max-width: 1200px`
- Claude Design 范式下优先用 `.eyebrow + .display + .lede` 起手，`.page-title/subtitle` 保留作为 legacy

### `.grid2` / `.grid3` / `.grid4` — 网格布局

```html
<div class="grid3 gap-6">
  <div>...</div>
  <div>...</div>
  <div>...</div>
</div>
```

- 响应式：900px 以下自动变单列
- 搭配 `.gap-{1..8}` 8pt 网格工具类控间距

### `.cmp-table` — 对比表

```html
<table class="cmp-table">
  <thead><tr>
    <th>步骤</th>
    <th>方案 A</th>
    <th>方案 B</th>
  </tr></thead>
  <tbody>
    <tr>
      <td style="color:var(--t1);font-weight:700;">步骤名</td>
      <td>A 做法</td>
      <td>B 做法</td>
    </tr>
  </tbody>
</table>
```

- 表头**不用彩色区分**（Claude Design 禁同页多色），用 eyebrow 风格小标签或直接纯文字
- 第一列加粗 + --t1 突出

### `.accordion` — 折叠展开

```html
<div class="accordion">
  <div class="acc-header" onclick="toggleAcc(this)">
    <span>问题文本</span>
    <span class="arrow">▶</span>
  </div>
  <div class="acc-body">展开内容</div>
</div>
```

### `.prompt-block` — 代码块（含复制）

```html
<div class="prompt-block">
  <div class="prompt-header">
    <span class="label">文件名.txt</span>
    <button class="copy-btn" onclick="copyPrompt(this, 'key')">复制</button>
  </div>
  <div class="prompt-body">展示内容</div>
</div>
```

- 需要自定义 `copyPrompt()` + `PROMPTS = {}` 对象

### `.modal-overlay` — 全屏弹窗

```html
<span style="cursor:pointer;color:var(--blue);" onclick="openModal('标题', '内容')">点击打开</span>
```

- 结构已在 ppt-template.html 预设，`openModal()` 模板已内置

---

## 工具类

### 8pt 网格间距

`.mt-{1,2,3,4,6,8}` / `.mb-*` / `.ml-*` / `.mr-*` / `.mx-*` / `.my-*`
`.p-*` / `.px-*` / `.py-*`
`.gap-*`

对应 `--sp-1 = 8px` / `--sp-2 = 16px` / `--sp-3 = 24px` / `--sp-4 = 32px` / `--sp-6 = 48px` / `--sp-8 = 64px`。

### 文字颜色（克制使用）

```html
<span class="text-blue">仅在 accent 高亮时用</span>
```

- Claude Design 同页 ≤ 1 种强调色（blue）
- `.text-green/orange/purple/red/pink` 仅在数据图表等功能性区分场景用，文字排版禁用

### 其他

```html
<code>context.md</code>      <!-- 行内代码 -->
<span class="fw9">加粗</span>  <!-- font-weight:900（慎用，印刷范式优先用 display serif）-->
<span class="mono">等宽</span>
```

---

## 遗留组件（legacy，不推荐但保留）

以下组件出自 SOP V2.0 范式，与 Claude Design editorial 风格不符。**优先用上方 Claude Design 组件替代**，下方仅作已有文档维护参考。

| 遗留组件 | Claude Design 替代 | 原因 |
|---|---|---|
| `.hero-accent` / `.tag-*` 彩色 bg 标签 | `.eyebrow` / `.eyebrow-accent` | mono tracking 替代彩色徽章 |
| `.hero-headline` / `.hero-num` | `.display-xl` + `.figure-num` | serif 替代 weight:900 sans |
| `.hero-sub` | `.lede` | serif lede 比 sans 更 editorial |
| `.stat-card` 居中卡片 | `.figure-num` + `.figure-lbl` | 去 card bg / border，editorial 横排 |
| `.quote-block` 居中斜体 | `.pullquote` | 左竖线 + serif 28px |
| `.page-split` 彩色分隔带 | `.film-grain` Hero + `.section-label` | Part 转场做整页 Hero |
| `.page-hero` + `.hero-accent` | 见 gold-snippets §1 Hero 模式 | 用 eyebrow + display + lede + hairline-accent 四件套 |
| `.flow-h` + `.fh-num` 彩色圆角数字 | eyebrow `STEP 01` + hairline 分段 | 见 gold-snippets §4 |
| `.pipe` + `.pipe-icon` emoji | 同上 | 去 emoji，编号 eyebrow 化 |
| `.card` + `border-top:3px solid var(--color)` | `.eyebrow` 区分 + 内部 hairline-sm | 六禁之二：禁「圆角卡片 + 左/顶 border-accent」 |
| `.note green/orange/red` 彩色提示 | `.pullquote`（核心判断）或 `.hairline` + eyebrow 小节 | 禁同页多色 |
| `.track-card track-a/track-b` 预设色板 | 两栏等权 `.grid2` + `.eyebrow` 分类 | 见 gold-snippets §3 |
| `.ck-num` 彩色圆角编号 | `.eyebrow` 行首 `01`/`02`/`03` | 见 gold-snippets §5 |
| `.nest-*` 多色嵌套层级 | 外层 `.eyebrow` 分层 + 内部缩进 + `.hairline-sm` | 避免三色嵌套堆叠 |
| `.gallery-card` / `.skill-card` + model-tag | `.grid3` + `.eyebrow` 分类 + 内部 `.display-md` | 组件化程度更高 |

---

## 高级组合（需自定义，遵循 Claude Design）

高级组合（Growth Tree / Dependency Chain 等）**不提供样式模板**。如需展示：

- 树形结构：用 HTML 语义（`<ul>` 缩进 + `.eyebrow` 层级标识 + `.hairline-sm` 分段），避免「彩色 gradient border + emoji icon + 带阴影圆角卡」三件套
- 依赖链：用 `.cmp-table` 或 `.grid2`（源/目标）+ eyebrow 标注顺序（`POS 01` / `POS 02`），避免 orange/blue/green 三色边框
- 分支流程图 / 泳道图：用 flowchart skill 独立产出 HTML，截图嵌入 PPT（PPT 内嵌 X6 在暗色主题下视觉不对齐，已 rolled back）

---

## JS 工具函数（ppt-template.html 已内置）

| 函数 | 用途 |
|---|---|
| `renderNav()` | 渲染侧边栏导航 |
| `goPage(id)` | 切换页面 |
| `renderPage()` | 渲染当前页面 |
| `escHtml(s)` | HTML 转义 |
| `closeModal()` | 关闭弹窗 |
| `copyModalPrompt()` | 复制弹窗内容 |
| `toggleAcc(el)` | 折叠展开 |

## 需自定义的 JS 函数（填充时按需添加）

| 函数 | 用途 | 模板 |
|---|---|---|
| `copyPrompt(btn, key)` | 复制 prompt-block 内容 | 在 fill 阶段补 |
| `copyTemplate(btn, key)` | 复制模板内容 | 在 fill 阶段补 |
