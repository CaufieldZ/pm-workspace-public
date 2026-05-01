---
name: deck-grammar
description: PPT / SOP 每页四层结构 + 样式约定 + 视觉主角差异化规则（改自 Claude Design slide-decks.md）
type: reference
---

# Deck Grammar：PPT / SOP 产出物每页结构规范

> 适用：ppt skill（HTML 多 Tab 信息文档）。每页复用四层骨架 = 多页视觉一致、0 返工。
> 来源：Claude Design slide-decks.md「出版物 grammar 模板」段，适配 pm-workspace 场景。

---

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
  color: var(--cd-ink-82);
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
