<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: anti-ai-slop
description: HTML 产出物反 AI slop 规范——六禁、字号、留白、颜色、CSS 神器速查
type: reference
---

# 反 AI Slop 规范（pm-workspace HTML 产出物通用）

> 摘录自 claude-design content-guidelines.md，适配 pm-workspace 场景。
> "当你觉得'加一下会更好看'时——那通常是 AI slop 的征兆。先做最简版本，只在用户要求时加。"

---

## 六禁（硬性禁止）

### 禁 1：全屏渐变背景

```css
/* ❌ 以下全部禁止 */
background: linear-gradient(135deg, #667eea, #764ba2);  /* rainbow */
background: radial-gradient(circle, purple, pink, blue); /* mesh feel */
```

可以用渐变的唯一场景：按钮 hover 的单色系 subtle 点缀。

### 禁 2：Emoji 装饰标题 / 列表

- 禁止：`🚀` `⚡️` `✨` `🎯` `💡` 做标题装饰
- 禁止：`✅` 做 Feature 列表
- 没有图标需要时用 placeholder 文字标注，或用 Lucide/Phosphor 真 icon 库

### 禁 3：圆角卡片 + 左 border accent（AI 签名卡片）

```css
/* ❌ 这是 AI 味卡片的典型签名，禁止 */
.card {
  border-radius: 12px;
  border-left: 4px solid #2F6CF2;
  padding: 16px;
}
```

想做强调用：背景色对比、字重 / 字号对比、plain 分隔线。

### 禁 4：SVG 画人物 / 场景 / 插画

AI 画的 SVG imagery 一眼就是 AI 味。用灰色 placeholder + 文字标签替代：

```html
<div class="cd-placeholder" style="height:400px" data-label="插画位 1200×800"></div>
```

SVG 只允许用于：真正的 icon（≤32×32px）、几何装饰元素、Data viz chart。

### 禁 5：烂大街字体

- 禁止作为主字体：Inter、Roboto、Arial、Helvetica、Fraunces、Space Grotesk
- 统一用：`Noto Serif SC`（中文标题）+ `Source Serif 4`（英文副标题）+ `JetBrains Mono`（数字/代码/eyebrow）+ `Inter`（仅 sans-serif 正文降级）

### 禁 6：每个 card / feature 都带 icon

滥用 icon 让界面像 toy。Less is more。

---

## 字号对比（强制）

- 标题至少正文的 **2.5 倍**（正文 16px → 标题 ≥ 48px 起）
- PPT 正文最小 **24px**，标题 **60-120px**
- Web / App 正文最小 **14px**，移动端正文 **16px**（iOS 防缩放）
- 印刷文档：正文 **10pt**，标题 **18-36pt**，caption **8-9pt**

---

## 颜色（强制）

最多：**1 主色 + 1 辅色 + 1 强调色 + 灰阶**，禁止凭空调色。

pm-workspace 默认配色：
- 主色：`--cd-bg: #000000`
- 强调：`--cd-accent: #2F6CF2`
- 文字层次：`--cd-ink` / `--cd-ink-82` / `--cd-ink-58` / `--cd-ink-40`

---

## 留白（强制）

- 留白 **≥ 40%** 总面积（极简风 60%+）
- 间距只用 8pt 网格：**8 / 16 / 24 / 32 / 48 / 64px**

---

## Data / Quote Slop（禁止编造内容）

- 禁编造数字装饰：`10,000+ happy customers`、`99.9% uptime`、metric cards
- 禁编造用户评价 / 名人名言
- 没有真数据 → 留 placeholder 或问用户要
- 禁止加 filler content：去掉这段设计会变差吗？不会就去掉

---

## CSS 神器速查

```css
/* 中文标题换行更自然 */
h1, h2, h3 { text-wrap: balance; }

/* 正文避免孤儿/寡妇行 */
p { text-wrap: pretty; }

/* 中文排版：标点挤压 */
p {
  text-spacing-trim: space-all;
  hanging-punctuation: first;
}

/* 统一间距系统 */
gap: var(--sp-3); /* 24px */
padding: var(--sp-4) var(--sp-6); /* 32px 48px */

/* hover 颜色变化（不凭空调色）*/
.btn:hover {
  background: color-mix(in oklch, var(--cd-accent) 85%, black);
}

/* 滚动条 */
* { scrollbar-width: thin; scrollbar-color: var(--cd-ink-18) transparent; }
```

---

## 决策速查（犹豫时）

| 想法 | 答案 |
|------|------|
| 加个渐变背景？ | 大概率不加 |
| 加个 emoji 装饰？ | 不加 |
| 给卡片加圆角 + border-left accent？ | 不加，换其他方式 |
| 用 SVG 画 hero 插画？ | 不画，用 placeholder |
| 加一排 icon features？ | 先问要不要 |
| 用 Inter 作中文主字体？ | 换 Noto Serif SC |
| 没数据的 metric card？ | placeholder，不编造 |
