# ClaudeDesign 主题包

9 套主题色板，覆盖 SOP / 商业发布 / 人文 / 极简 / 技术 / 学术 / 国风等场景。

**铁律**：一份 PPT 只用一套。不允许混搭。

---

## 场景对照表

| 主题文件 | 调性 | 适合场景 | 关键色 | 推荐 layout |
|---------|------|---------|--------|------------|
| `fintech-dark.css` | 深黑 + Platform C 蓝，专业金融感 | 内部产品评审、金融类对外演讲 | bg `#0f0f11` / accent `#2F6CF2` | 全部 layout |
| `ink-classic.css` | 墨黑 + 暖米，Monocle 杂志感 | 通用分享、商业发布、科技产品 | bg `#f1efea` / accent `#B22222` | 1/3/4/8 |
| `indigo-porcelain.css` | 深靛蓝 + 瓷白，学术期刊感 | 研究/数据/工程师文化分享 | bg `#f1f3f5` / accent `#1565C0` | 3/5/6/9 |
| `kraft-paper.css` | 深棕 + 暖米，牛皮纸人文感 | 文学/历史/人文/怀旧主题 | bg `#eedfc7` / accent `#8B4513` | 4/7/8/10 |
| `swiss-grid.css` | 纯白 + 纯黑 + 品牌红，瑞士网格 | 品牌发布、设计年报 | bg `#FFFFFF` / accent `#E8341E` | 1/2/9 |
| `muji-minimal.css` | 暖白 + 极淡灰，无印/Kenya Hara | 生活方式、审美优先私享会 | bg `#FAFAF8` / accent `#8A8A86` | 7/8/10 |
| `cyber-noir.css` | 深空黑 + 霓虹紫，电影质感 | 技术大会主题演讲、赛博美学 | bg `#050814` / accent `#A855F7` | 1/2/6 |
| `book-architecture.css` | 象牙 + 深棕 + 朱红，书籍排印 | 出版/内容品牌/深度内容场合 | bg `#F5F0E6` / accent `#B91C1C` | 4/8/10 |
| `paper-zen.css` | 东方质感的西方学院派 / 出版物美感（《读库》/ FT Weekend 系） | 一图流 / 教研文档 / 研究报告封面 / 教学海报 / 庆典级 PRD 配图 | bg `#FAF6EC` / accent `#1B3A2F` + gold `#A8804A` | A4 横版一图流（非 PPT layout）；配套 `paper-zen.prompt.md` 是设计 brief，做新一图流前 Read 该文件 |
| `vendor-editorial.css` | 中文衬线杂志感 + teal/amber 双语义 + 浅深双底交替 | 方案宣讲 / 方法论沉淀 / 管理层 deck（叙事型演讲） | bg `#F4F5F6` + dark `#15181C` / accent teal `#0F726B` + amber `#A86A22` | ppt 纯 deck 范式默认主题；定义 vendor 调色板原名供 `deck-template.html` 组件引用 |

---

## 切换方式

在 `tokens.css` import 之后追加一行即可：

```css
@import url('../../_shared/claude-design/tokens.css');
@import url('../../_shared/claude-design/themes/ink-classic.css');
```

主题文件只覆盖 `--cd-*` 变量，`tokens.css` 中未被覆盖的变量（间距、圆角等）保持原样。

在生成脚本里：

```js
const tokens = fs.readFileSync('.claude/skills/_shared/claude-design/tokens.css', 'utf8');
const theme  = fs.readFileSync('.claude/skills/_shared/claude-design/themes/ink-classic.css', 'utf8');
// 拼入 <style>：tokens 在前，theme 在后（覆盖）
```

---

## 字体注意事项

部分主题覆盖了字体 token：

| 主题 | 覆盖变量 | 效果 |
|------|---------|------|
| `muji-minimal` | `--cd-serif-cn` → Noto Sans SC | 标题也用细黑，呈现极简气质 |
| `book-architecture` | `--cd-sans` → Noto Serif SC | 正文也走衬线，强化书版感 |
| `paper-zen` | `--cd-serif-cn/en` → Noto Serif CJK SC + Songti | 标题层全衬线（连数字也是），强化古籍气；招式扩展（5 色国画 palette / 双线 header / dotted divider / radial 宣纸晕染）见 `paper-zen.css` 文件头注释 |
| `vendor-editorial` | `--cd-mono` → IBM Plex Mono | eyebrow / 编号 / 标签 / 代码块走 IBM Plex Mono（比 JetBrains 更杂志感）；标题 Noto Serif SC 700/900、正文 Noto Sans SC 300 沿用默认栈 |

其余主题不覆盖字体，沿用 `tokens.css` 的字体栈。

---

## 不要做的事

- 不允许混搭（如 bg 取 ink-classic、accent 取 cyber-noir）
- 不允许手写 hex 颜色进 PPT 页面（所有颜色走 `var(--cd-*)`）
- 不允许在同一份 PPT 中途换主题

---

## vendor-editorial 风格：哪些 skill 该用 / 不该用

这套衬线杂志风只适合**叙事型产物**（给人讲 / 给人看的方案与方法论），别无差别推给所有视觉 skill：

| skill | 用不用 | 原因 |
|------|-------|------|
| **ppt** | ✅ 纯 deck 范式默认 | 演讲型叙事产物，正中下怀 |
| **architecture-diagrams** | ⚠️ 可选 | 列为推荐主题之一，但架构图颜色常承载分层 / 数据流语义，保留多色能力，不强制压两色 |
| **interaction-map** | ❌ 不动 | 金融业务交互，Platform C 蓝是业务品牌资产（tokens.css 注释「故意保留蓝色」），套学术衬线 = 砸辨识度 |
| **prototype** | ❌ 不动 | 金融 App 移动端，Binance 蓝系业务视觉，同上 |
| **flowchart** | ❌ 不动 | mermaid / drawio 引擎渲染，样式引擎托管，套不进去 |

> 看到这条别手贱「统一全工区风格」——业务 skill 的蓝是资产，不是待清理的不一致。
