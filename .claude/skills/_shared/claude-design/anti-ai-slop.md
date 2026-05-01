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

**例外 · UI mock 内部图标**（prototype / interaction-map 专属）：

交互大图和原型需要模拟被设计的产品本身，里面的 tab bar / 空态 / 功能按钮 icon **不是文档装饰**而是「装 UI」——真实产品会有图标，mock 只是示意「这里有个 icon」。按**尺寸和用途**分层：

| 区域 | 尺寸 | 允许做法 |
|---|---|---|
| UI mock 内部小图标（tab bar / 按钮内 / 空态提示 / 状态徽章） | ≤ 20px | emoji ✅ 或 Unicode 几何符号（`▶ ● ◆ ○ □ ★`）✅ |
| UI mock 内部大占位图（直播缩略图 / banner / 头像大图 / hero 插图） | ≥ 40px | 强制 `.cd-placeholder` 灰底 + mono 文字缩写（`IMG` / `AV` / `LIVE` / `HERO`），禁 emoji 放大当插图 |
| 文档本身装饰（SKILL.md / references md 的章节标题、列表前缀、section label） | — | 一律禁 emoji（本条原规则） |

**判定方法**：这个 emoji 是在**模拟真实产品的一部分**（prototype 的 tab 栏、空态），还是在**装饰文档结构**（「## 🎯 使用说明」）？前者允许，后者禁止。

### 禁 3：圆角卡片 + 任意方向 border accent（AI 签名卡片）

**任一方向**（左 / 右 / 上 / 下） ≥ 2px 的 accent color border 都是 AI 味签名，不是只禁左边。从 left 换 top / right 不算规避。

```css
/* ❌ 全部禁，无论方向 */
.card { border-radius: 12px; border-left:  4px solid #2F6CF2; }
.card { border-radius: 12px; border-top:   2px solid var(--cd-err); }  /* 红绿顶条分区也禁 */
.card { border-radius: 12px; border-right: 3px solid var(--cd-ok); }
.card { border-radius: 12px; border-bottom:2px solid var(--cd-accent); }
```

想做强调 / 分区用：背景色对比（两张卡一深一浅）、标题前加小圆点（`<span style="width:6px;height:6px;border-radius:50%;background:var(--cd-err)">`）、字重字号对比、plain hairline 分隔线（`border: 1px solid var(--cd-hairline)` 全边框均匀灰不算 accent）。

### 禁 4：SVG 画人物 / 场景 / 插画

AI 画的 SVG imagery 一眼就是 AI 味。用灰色 placeholder + 文字标签替代：

```html
<div class="cd-placeholder" style="height:400px" data-label="插画位 1200×800"></div>
```

SVG 只允许用于：真正的 icon（≤32×32px）、几何装饰元素、Data viz chart。

### 禁 5：烂大街字体

- 禁止作为主字体：Inter、Roboto、Arial、Helvetica、Fraunces、Space Grotesk、DM Sans
- 统一字体栈（三分工，CJK 优先排序，对标 Anthropic 官方 brand-guidelines + claude.ai chat UI）：
  - **标题 / 章节 / 重点金句**：`Noto Serif SC`（中文衬线主角）+ `Lora`（英文衬线，Anthropic 官方 brand-guidelines 钦定，对标 claude.ai 实际用的付费 Tiempos / Copernicus）
  - **正文 / 表格 / 长段阅读**：`Noto Sans SC`（中文 sans 主力）+ `Poppins`（英文 sans，Anthropic 官方 brand-guidelines 钦定，对标 claude.ai 实际用的付费 Styrene B）
  - **数字 / 代码 / kicker / 状态标签 / 编号 marker / meta**：`JetBrains Mono`（等宽，做信息节奏层）
- 备注：Lora + Poppins 是 Anthropic 公开 brand-guidelines skill 钦定的免费字体，授权可放心引；Source Serif 4 / Plus Jakarta Sans / Inter 仅供旧产物兼容，新产物不再用

### 禁 6：每个 card / feature 都带 icon

滥用 icon 让界面像 toy。Less is more。

---

## 进阶规则（字体三分工 · 图片裁切 · chrome 禁同义重复）

### 补 1：字体三分工（必须）

| 字体类型 | 用于 | 变量 |
|---------|------|------|
| 衬线（serif-cn / serif-en） | 标题、重点金句、数字大字 | `--cd-serif-cn` / `--cd-serif-en` |
| 非衬线（sans） | 正文描述、大段阅读内容 | `--cd-sans` |
| 等宽（mono） | kicker、meta 标签、foot 装饰、代码 | `--cd-mono` |

**禁止**：

- 标题用非衬线（Noto Sans SC 做 hero 标题 = 瞬间降级成 AI 通稿）
- 正文用衬线（长段落用 Noto Serif SC = 阅读疲劳）
- 元数据（kicker / chrome / foot）用 sans（应该是等宽 mono，缺了节奏感）

判断：如果三种字体的视觉分工在页面上看不出来，说明用错了。

### 补 2：图片只裁底部 + 网格内禁 aspect-ratio

```css
/* ✓ 正确：固定 height + overflow hidden + object-position:top */
figure.frame-img { height: 26vh; overflow: hidden; }
figure.frame-img img { object-fit: cover; object-position: top center; }

/* ❌ 禁止：网格内用 aspect-ratio（会撑破父容器，图片堆叠或切顶） */
figure.frame-img { aspect-ratio: 16/9; }

/* ❌ 禁止：align-self:end 贴底（低分屏被工具栏遮挡） */
figure.frame-img { align-self: end; }
```

**例外**：单张主视觉（非网格内）可用 `aspect-ratio + max-height`，父容器会兜底。

### 补 3：chrome / kicker 禁同义重复（杂志感关键）

- `chrome` = 杂志页眉 / 栏目标签，跨多页可相同（如「Act II · Workflow」「lukew.com · 2026.04」）
- `kicker` = 本页独一份的引导句，每页必须不同（如「BUT」「Phase 01 · 设计阶段」「The Question」）

**反例**（AI 味浓）：

```
chrome: 「设计先行 · Design First」
kicker: 「Phase 01 · 设计阶段」
→ 同义翻译，两个都在说设计，信息重复
```

**正例**：

```
chrome: 「Act II · Workflow」（描述栏目/幕次）
kicker: 「BUT」（给大标题做钩子）
```

判断：chrome 回答「我在哪一章」，kicker 回答「这页要传达什么情绪/钩子」。两个问题不同，就不会重复。

---

## 字号对比（强制）

- 标题至少正文的 **2.5 倍**（正文 16px → 标题 ≥ 48px 起）
- PPT 正文最小 **24px**，标题 **60-120px**
- Web / App 正文最小 **14px**，移动端正文 **16px**（iOS 防缩放）
- 印刷文档：正文 **10pt**，标题 **18-36pt**，caption **8-9pt**

---

## 颜色（强制）

最多：**1 主色 + 1 辅色 + 1 强调色 + 灰阶**，禁止凭空调色。

pm-workspace 默认配色（claude.ai chat UI 实测 + Anthropic 官方 brand-guidelines）：
- 主色：`--cd-bg: #1F1F1E` / 文字 `--cd-ink: #C3C2B7`（claude.ai chat UI 同款暖近黑 + 暖灰白）
- 强调：`--cd-accent: #D97757`（Anthropic terra cotta，logo 同款；次 `#6A9BCC` 蓝 / 三 `#788C5D` 绿）
- 文字层次：`--cd-ink` / `--cd-ink-82` / `--cd-ink-58` / `--cd-ink-40`
- 营销级高对比切 `.theme-cd-brand` 拿官方品牌 `#141413` / `#FAF9F5`

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
| 加个 emoji 装饰？ | 文档结构装饰不加；UI mock 内部 ≤20px icon（tab/按钮/空态）可加，≥40px 占位图用 `.cd-placeholder` 不用 emoji |
| 给卡片加圆角 + border-left accent？ | 不加，换其他方式 |
| 用 SVG 画 hero 插画？ | 不画，用 placeholder |
| 加一排 icon features？ | 先问要不要 |
| 用 Inter 作中文主字体？ | 换 Noto Serif SC |
| 没数据的 metric card？ | placeholder，不编造 |
