# ClaudeDesign 主题包

8 套主题色板，覆盖 SOP / 商业发布 / 人文 / 极简 / 技术 / 学术等场景。

**铁律**：一份 PPT 只用一套。不允许混搭。

---

## 场景对照表

| 主题文件 | 调性 | 适合场景 | 关键色 | 推荐 layout |
|---------|------|---------|--------|------------|
| `fintech-dark.css` | 深黑 + HTX 蓝，专业金融感 | 内部产品评审、金融类对外演讲 | bg `#0f0f11` / accent `#2F6CF2` | 全部 layout |
| `ink-classic.css` | 墨黑 + 暖米，Monocle 杂志感 | 通用分享、商业发布、科技产品 | bg `#f1efea` / accent `#B22222` | 1/3/4/8 |
| `indigo-porcelain.css` | 深靛蓝 + 瓷白，学术期刊感 | 研究/数据/工程师文化分享 | bg `#f1f3f5` / accent `#1565C0` | 3/5/6/9 |
| `kraft-paper.css` | 深棕 + 暖米，牛皮纸人文感 | 文学/历史/人文/怀旧主题 | bg `#eedfc7` / accent `#8B4513` | 4/7/8/10 |
| `swiss-grid.css` | 纯白 + 纯黑 + 品牌红，瑞士网格 | 品牌发布、设计年报 | bg `#FFFFFF` / accent `#E8341E` | 1/2/9 |
| `muji-minimal.css` | 暖白 + 极淡灰，无印/Kenya Hara | 生活方式、审美优先私享会 | bg `#FAFAF8` / accent `#8A8A86` | 7/8/10 |
| `cyber-noir.css` | 深空黑 + 霓虹紫，电影质感 | 技术大会主题演讲、赛博美学 | bg `#050814` / accent `#A855F7` | 1/2/6 |
| `book-architecture.css` | 象牙 + 深棕 + 朱红，书籍排印 | 出版/内容品牌/深度内容场合 | bg `#F5F0E6` / accent `#B91C1C` | 4/8/10 |

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

其余主题不覆盖字体，沿用 `tokens.css` 的字体栈。

---

## 不要做的事

- 不允许混搭（如 bg 取 ink-classic、accent 取 cyber-noir）
- 不允许手写 hex 颜色进 PPT 页面（所有颜色走 `var(--cd-*)`）
- 不允许在同一份 PPT 中途换主题
