---
name: deck-grammar
description: PPT / SOP 每页四层结构 + 样式约定 + 视觉主角差异化规则（改自 Claude Design slide-decks.md）
type: reference
---

# Deck Grammar：PPT 产出物每页结构规范

> 适用：ppt skill。两套生成骨架——
> **① 纯 deck 范式（默认 · 演讲）**：1280×720 固定舞台，无 sidebar，键盘翻页，五幕章节胶囊。本文上半部。
> **② sidebar Doc 模式（可选 · 长文档 / SOP）**：240px sidebar + Doc/Deck 双模式。本文下半部「sidebar Doc 模式」节。
> 每页复用四层骨架 = 多页视觉一致、0 返工。

---

# 一、纯 deck 范式（默认）

> 风格来源：恒生 TA Spec Coding deck（已迁至 `agents-personal-main/vendor-deck/`，用户钦定视觉锚点）。
> 生成：`assets/deck-fill.js` 拼 slides 数组 → `assets/deck-template.html`（唯一类名源）+ `deck-runtime.js`。
> 主题：`_shared/claude-design/themes/vendor-editorial.css`（teal/amber 双语义 + 浅深双底）。

## 每页四层骨架

```
┌─ slide（浅底 .slide / 深底 .slide.dark）── 1280×720 ──────────┐
│  ── eyebrow（IBM Plex Mono · uppercase · teal · 前置短横线）  │
│  为什么做这件事 / 管理层视角                                  │
│                                                              │
│  h1.headline（Noto Serif SC 700 · 38px）                     │
│  核心观点一句话（10 字内最佳）                               │
│                                                              │
│  body-area（flex 居中）                                      │
│  [组件：card-grid / bluf-grid / track-3 / code-block ...]   │
│                                                              │
│  ── deck-foot（mono · 左=页脚一句话 · 右=.pagenum 页码）──    │
└──────────────────────────────────────────────────────────────┘
```

封面页（首页 / 章节转场 / 收尾）用 `.slide.dark .cover`：巨标 `Noto Serif SC 900 / 60px` + `.lead` 引言（左 teal 竖线）。

## 三字体分层（杂志感来源 · 铁律）

| 层 | 字体 | 字重 | 用在 |
|---|---|---|---|
| **标题层** | Noto Serif SC（衬线）| 700 / 封面 900 | h1.headline、卡片 h3、关键 key 名——所有「要被记住」的字 |
| **正文层** | Noto Sans SC（无衬线）| **300 细字重** | .lead 引言、card p、描述——给人连续阅读的字 |
| **元信息** | IBM Plex Mono（等宽）| 500 / 600 | eyebrow、编号（GOAL 01）、tag、deck-foot、code-block |

规律一句话：**衬线管标题、无衬线管正文、等宽管标签和编号**。三种对比张力 = 杂志感。

## 双语义 accent（颜色承载语义 · 不是装饰）

- **teal `#0F726B`** = 机器 / 自动 / 正常路径 / 主线（默认色）
- **amber `#A86A22`** = 人工 / 治理门 / 风险 / 需确认（变体色，组件加 `.warn` / `.gate` / `.confirm` 切）
- 只此两色 + 黑白底，**禁彩虹 tag**。olive `#6F8C56` 仅作 track-3 第二轨等极少数三元场景。

## 浅深交替节奏 + 五幕章节

- **浅深交替**：封面 dark → 论证 paper → 章节转场 dark → 论证 paper → 收尾 dark。深色页制造呼吸停顿，别整套全浅或全深。
- **五幕 ACTS**（顶部章节胶囊，`deck-fill.js` 的 `acts` 参数）：

```js
const ACTS = [
  { label: '开场',   start: 0 },   // 封面 + BLUF
  { label: '为什么', start: 2 },   // 痛点 / 现状
  { label: '是什么', start: 5 },   // 方案 / 形态
  { label: '怎么落', start: 12 },  // 路径 / 里程碑
  { label: '怎么稳', start: 18 },  // 治理 / 风险 / 第一步
];
```

`start` = 该幕首页 index（0-based）；首页（index 0）自动隐藏胶囊。

## 推荐叙事骨架（默认 · 非强制）

vendor 验证过的「结论先行 + 五幕展开」结构，新 deck 默认参考：

1. **封面**（dark）：一句话价值主张 + 关键词 teal 高亮
2. **BLUF 一页纸**（paper，封面后第 2 页）：四格结论 `bluf-grid`（WHAT / COST / VALUE / RISK 或按项目调整），页脚一句「后面每页都在展开这一页」
3. **为什么**：痛点 / 现状 / 三目标（`card-grid`）
4. **是什么**：方案形态 / 分层（`layer-stack` / `kv-split` / `hub`）
5. **怎么落**：路径 / 里程碑（`item-list` / `phase-flow` / `track-3`）
6. **怎么稳 + 收尾**（dark）：治理门 / 风险前置 / 第一步（`qgate-list` / `firststep`）

幕数与命名按项目调整，但「结论前置 + 浅深交替」保持。

## 可复用组件（类名唯一源 = `assets/deck-template.html`）

| 组件 class | 用途 | 关键变体 |
|---|---|---|
| `card-grid` | 三栏卡片（目标 / 维度）| `.col2` `.col4`；卡片 `.card.warn` 切 amber |
| `two-up` + `bigpt` | 双栏大点（两个并列论点）| — |
| `bluf-grid` + `bcell` | 四格结论先行 | `.bcell.warn` = 风险格 |
| `layer-stack` + `layer` | 分层栈（架构 / 演进）| `.base` `.warn` `.vision`（虚线未来态）|
| `kv-split` + `panel` | 分栏 + 实色面板 | `.panel.accent` = 深底强调 |
| `phase-flow` + `phasecard` | 横向阶段卡 + 箭头 | `.alt`（olive）`.warn`（amber）|
| `track-3` + `mcol` | 三轨并行（自动三色）| 第 1 teal / 2 olive / 3 amber |
| `item-list` + `item` | 编号步骤清单 | `.item.warn` = 治理步 |
| `hub` + `node` | 中心节点图 | `.truth`（深底真相源）`.proj` `.gate` |
| `qgate-list` + `qgate` | 质量门清单 | `.gate` = 人工门 amber |
| `tree-list` + `tnode` | 目录树分层 | `.truth` `.infra` |
| `integ-split` | 双栏对比（保留 vs 新增）| `.keep`（teal）`.add`（amber）|
| `kf-2` + `kf` | 双栏特性卡 | `.build`（teal）`.verify`（amber）|
| `role-table` | 角色对照表 | td `.now` `.fut` `.hook` |
| `map-stack` + `mlayer` | 行业分层图 | `.hi-teal` `.hi-amber` |
| `bet-band` + `bet` | 双格方向 / 投注带 | `.teal` `.amber` |
| `callout` / `loopbar` / `amber-bar` | 三种强调条 | 深底 / teal / amber |
| `firststep` | 渐变首步块（第一步行动）| 深底渐变 |
| `principles` + `prin` | 三联原则带 | — |
| `code-block` + `cb-head` + `pre` | **代码 / 终端块（IDE 标签页式）** | `.term`（黑底青绿终端）`.md`（teal 头）`.java`/`.code`（amber 头）`.pts`（要点浅底）|

`.code-block.term` 是用户特别看重的样式：黑标题条 + 深底 `#11151a` + 青绿字 `#cfe8e3`，演示「一条命令跑起来」最专业。

## 内容纪律

- 每页只传递 **1 个核心观点**，观点即 h1.headline（≤ 12 字）
- 正文补论据不写结论（结论已在标题）；正文走 300 细字重 + 大行高，别堆密
- amber 高亮承载「人工 / 风险」语义，不滥用——一页通常 0-2 处
- 数字 / 比率必须有来源，无来源用 `[数据待填]`

---

# 二、sidebar Doc 模式（可选 · 长文档 / SOP）

> 240px sidebar + Doc/Deck 双模式，适合需要侧边导航的长文档 / SOP 手册。
> 生成：`assets/fill-template.js` + `assets/ppt-template.html`。以下为该模式的页面 grammar。

## 每页骨架（四层）

```
┌─ masthead（顶部条 + 横线）─────────────────────────────────┐
│  [logo/项目名 14px mono]          Issue · Date · Version │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ── eyebrow（mono uppercase + accent 色）                  │
│  CHAPTER 01 · 模块名称                                      │
│                                                             │
│  H1（Noto Serif SC 900，重点词上 accent 蓝）               │
│  核心观点一句话                                              │
│                                                             │
│  English subtitle（Lora italic，副标题）                   │
│  ─────────── hairline 分隔线 ──────────                    │
│                                                             │
│  [body：双栏 60/40 / 2×2 grid / 列表 / big-quote / 表格]  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ section-name（mono，左）              页码 / 总页数（右）   │
└─────────────────────────────────────────────────────────────┘
```

### 层次说明

| 层次 | HTML class | 字体 | 字号 | 说明 |
|------|-----------|------|------|------|
| eyebrow | `.cd-eyebrow` | JetBrains Mono | 11px | uppercase + 0.24em letter-spacing + accent 蓝 |
| H1 | `h1.deck-title` | Noto Serif SC | 80-140px（看信息量）| 重点词用 `<span class="accent">` 单独上色 |
| 英文副标题 | `.deck-subtitle` | Lora italic | 26-46px | 品牌签名词粗体 + accent 斜体 |
| 正文 | `.deck-body` | Noto Serif SC | 17-21px | line-height 1.75-1.85 |

---

## 样式约定（直接用）

```css
/* ── H1 标题 ── */
h1.deck-title {
  font-family: "Noto Serif SC", serif;
  font-weight: 900;
  font-size: clamp(48px, 8vw, 140px);
  line-height: 1.1;
  text-wrap: balance;
  color: var(--cd-ink);
}
h1.deck-title .accent {
  color: var(--cd-accent);  /* #D97757 Anthropic terra cotta */
}

/* ── 英文副标题 ── */
.deck-subtitle {
  font-family: "Lora", Georgia, serif;
  font-style: italic;
  font-size: clamp(22px, 3vw, 46px);
  color: var(--cd-ink-58);
  margin-top: 16px;
}

/* ── 正文 ── */
.deck-body {
  font-family: "Noto Serif SC", serif;
  font-size: clamp(15px, 1.5vw, 21px);
  line-height: 1.8;
  color: var(--cd-ink);
}

/* ── Accent 高亮（每页 ≤ 3 处）── */
.deck-body strong {
  font-weight: 700;
  color: var(--cd-ink);
}
.deck-body .accent-inline {
  color: var(--cd-accent);
  font-weight: 700;
}

/* ── 背景：暖黑 + 极淡 noise（比纯黑更有质感）── */
.deck-page {
  background: var(--cd-bg);
  position: relative;
}
.deck-page::after {
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 30% 20%, rgba(47,108,242,0.04), transparent 60%);
  pointer-events: none;
}
```

---

## 视觉主角差异化（多页时必须轮换）

多页 PPT 如果全是「文字 + 一张截图」会太单调。**每页的视觉主角类型轮换**：

| 视觉类型 | 适合的 section | 实现方式 |
|---------|---------------|---------|
| 封面排版（大字 + masthead）| 首页 / 篇章封面 | H1 200px + eyebrow + 留白 ≥ 60% |
| Big-quote（半页大字引言）| 问题页 / 情绪页 | `font-size: 72px` + `"` 装饰 |
| 双栏 60/40 | 数据对比 / 功能分析 | CSS Grid `3fr 2fr` |
| 2×2 Grid | 四象限 / 四维度 | CSS Grid `1fr 1fr` + gap 32px |
| 时间轴卡片递进 | 演进 / Roadmap | Flexbox + 连接线 |
| 产品 UI 截图 + 设备框 | 具体功能展示 | `.app-mock` 壳 + 截图 |
| 数字 + 说明（Hero num）| KPI / 数据结论 | `font-size: 120px` mono + 16px 说明 |
| 前后对比（Before/After）| 改变 / 差异 | 双列 + 中间 → 箭头 |
| 表格（横向滚动）| 详细规则 / 对比表 | `<table>` 暗色系样式 |
| 大字 CTA + URL | 结尾页 | H1 + 椭圆按钮 |

**规则**：连续 3 页不得出现相同视觉类型。

---

## 内容纪律（配合 anti-ai-slop.md）

- 每页只传递 **1 个核心观点**，观点即 H1（10 字以内）
- Body 补充论据，不写结论（结论已在 H1）
- 禁止在 PPT 页面放 > 5 行 bullet list（拆成多页）
- 数字 / 比率必须有来源，无来源用 `[数据待填]` placeholder
- Accent 蓝高亮每页 **≤ 3 处**，超过则失去锚点作用
