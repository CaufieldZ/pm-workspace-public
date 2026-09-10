# PPT 演示模式（Doc / Deck 双模式）完整规范

> 触发：SKILL.md Step 4 引用本文档。所有通过 `fill-template.js` 生成的产物自动内置 Doc / Deck 双模式，无需额外操作。

## 模式定义

- **Doc 模式**（默认）：左侧 sidebar + 主内容区，按 Tab 切页查阅，适合文档浏览 / 速查
- **Deck 模式**（按 P 进入）：全屏横排翻页，Keynote 同款 transform 横移，底部圆点导航 + chrome/foot 杂志感元数据，适合演讲

## 键盘操作

| 按键 | Doc 模式 | Deck 模式 |
|------|----------|-----------|
| `P` | 进入 Deck | 退出 Deck |
| `ESC` | — | 退出 Deck（Keynote 习惯） |
| `→` / `Space` / `PageDown` | — | 下一步（先显 data-step，再翻页） |
| `←` / `PageUp` | — | 上一步（先退 data-step，再退页） |
| `Home` / `End` | — | 跳首页 / 末页 |
| 滚轮 | 滚动主内容 | 翻页（throttle 800ms） |
| 触屏左右滑 | — | 翻页（≥ 50px） |

## URL hash 直达

`#deck:overview` 刷新后直接进入 Deck 模式定位到该页。Doc 模式下退出 Deck 会清除 hash。

## NAV 扩展字段（Deck 模式可选）

每个 NAV item 可加 4 个可选字段，Deck 模式自动注入到顶部 chrome / 底部 foot；Doc 模式不渲染。未配置则空白。

```javascript
{
  id: 'overview', icon: '📍', label: '总览',
  // ↓ 以下为 Deck 模式可选字段，Doc 模式忽略
  kicker: 'Act I',                  // 顶部右上：「Act I · 03 / 27」（与页号拼接）
  groupLabel: '总览 · 选路',         // 顶部左上：栏目 / 章节
  footTitle: '为什么从 X 切到 Y',   // 底部左下：本页一句话说明
  footRight: 'OVERVIEW · INTRO',    // 底部右下：英文章节标
}
```

### chrome / kicker 反 AI slop（详见 `_shared/claude-design/anti-ai-slop.md`）

- `chrome`（= `groupLabel`）跨页可相同，是栏目 / 章节标签
- `kicker` 每页独一份，是本页引导句
- ❌ 反例：chrome `'设计先行 · Design First'` + kicker `'Phase 01 · 设计阶段'` = 同义翻译，AI 味浓
- ✅ 正例：chrome `'Act II · Workflow'` + kicker `'BUT'`（每页都不同）

## 分步揭示（Keynote Build-in 同款）

元素加 `data-step="N"` 属性，Deck 模式下按 `→` 逐步显现，全部显完才翻到下一页：

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

Doc 模式所有 `data-step` 内容自动全显，不影响查阅体验。

## 演示前清单（Deck 模式交付前）

- [ ] 每页 NAV item 是否补齐 `kicker` / `groupLabel` / `footTitle` / `footRight`（至少 chrome 字段）
- [ ] 类名预检通过（SKILL.md Step 3.0）
- [ ] 主题色（Step 0.2 推荐项 / claude-native 默认 / 其他 9 套之一）已落到产物，CDN 字体已加载
- [ ] 数据密集页 Deck 模式下 `overflow-y: auto` 兜底滚动可用

## 大文档模式（Step 3b）演示模式集成

Step 3b 拆分模式下 fill-template.js 不参与，需手动集成：

1. 将 `skill/assets/presenter-mode.css` 复制到 `sop-src/presenter.css`
2. 将 `skill/assets/presenter-mode.js` 复制到 `sop-src/presenter.js`
3. 在 `sop-src/shell.html` 的 `</main>` 后追加：
   ```html
   <div id="presenterHUD"></div>
   <div id="presenterHelp">← → 翻页 · Space 下一步 · ESC 退出</div>
   <div id="presenterEnterHint">[P] 演示</div>
   ```
4. 在 orchestrator 中，`styles.css` 后拼接 `presenter.css`，`init.js` 前拼接 `presenter.js`
