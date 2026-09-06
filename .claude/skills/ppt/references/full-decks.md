# Full-Deck 视觉参考库

> ⚠️ **已归档**：素材移至 `assets/archive/full-deck-refs/`（第三方风格画册，与工区 claude-design token 非同一套）。本文留作历史灵感索引，纯 deck 范式视觉锚点已切 `vendor-editorial` 主题 + `deck-grammar.md §一`。
> 来源：[lewislulu/html-ppt-skill](https://github.com/lewislulu/html-ppt-skill) `templates/full-decks/`
> 归档路径 [`.claude/skills/ppt/assets/archive/full-deck-refs/`](../assets/archive/full-deck-refs/)
> 15 套整套视觉语言，每套自包含 3 个文件：`index.html` + `style.css` + `README.md`
> scoped `.tpl-<name>` CSS 避免污染主流程；浏览器直接打开 `<deck>/index.html` 即可看完整 demo

## 定位与用法

**这些不是 fillTemplate 体系下的产物模板**，是**视觉灵感 / 完整 deck 参考库**。两种用法：

1. **作为视觉锚点**：PM 在 Step 0.3 子门讨论视觉风格时，指定某套模板让模型在生成 PAGE_RENDERERS 时**模仿其视觉特征**（色卡 / 字体搭配 / 卡片处理 / 排版节奏），但生成产物仍走标准 fillTemplate 流程
2. **直接 scaffold 复制**：PM 想完全用某套模板做 deck，手动 `cp -R assets/archive/full-deck-refs/{name}/ projects/{项目}/deliverables/` 改内容，**不走 fillTemplate**——这种走法等于把 lewislulu 体系整体引入此项目，需要保留 `_assets/` 路径

> 浏览器单独打开 `assets/archive/full-deck-refs/<name>/index.html` 即可看完整 deck demo（依赖 `_assets/` 同目录已就位）。左右键翻页、F 全屏、O 总览、T 切主题、S 演讲者视图全部可用（lewislulu runtime.js 提供）

## 强适用（社区 PM 工区高频场景）

### `presenter-mode-reveal` — 演讲专用

- **视觉**：tokyo-night 默认 + dracula / catppuccin-mocha / nord / corporate-clean 5 主题 T 键切换
- **关键特征**：每页带 150-300 字示例逐字稿（`<aside class="notes">`），底部键位提示
- **场景**：技术分享 / 内部演讲 / 评审 / 路演——任何按 S 键看逐字稿的场景
- **路径**：[`assets/archive/full-deck-refs/presenter-mode-reveal/`](../assets/archive/full-deck-refs/presenter-mode-reveal/)
- **补强 1 落地参考样本**——演讲者模式 popup 的 4 卡片实现就在此 deck 的 runtime 部分

### `tech-sharing` — 内部技术分享

- **视觉**：GitHub-dark + JetBrains Mono + terminal code blocks
- **关键特征**：8 页含 agenda + Q&A，cyber 但克制
- **场景**：内部技术分享 / conference talk
- **路径**：[`assets/archive/full-deck-refs/tech-sharing/`](../assets/archive/full-deck-refs/tech-sharing/)

### `weekly-report` — 数据周报

- **视觉**：corporate clarity，8-cell KPI grid + shipped list + 8-week bar chart + next-week table
- **关键特征**：7 页商务感，配 data-report skill 输出做视觉模板
- **场景**：周报 / 业务月报 / business review
- **路径**：[`assets/archive/full-deck-refs/weekly-report/`](../assets/archive/full-deck-refs/weekly-report/)

### `knowledge-arch-blueprint` — 架构图风

- **视觉**：奶油纸 #F0EAE0 底 + 单一 rust accent #B5392A + 48px 蓝图网格 + 2px 黑边卡片 + Playfair serif 大数字
- **关键特征**：管道步骤盒（其中 1 个 hero 抬起）+ 右侧 rust insight callout + SVG 虚线 feedback-loop 箭头
- **场景**：系统架构图 / 数据流图 / engineering 白皮书——需要严肃 / 可印刷感
- **路径**：[`assets/archive/full-deck-refs/knowledge-arch-blueprint/`](../assets/archive/full-deck-refs/knowledge-arch-blueprint/)

### `hermes-cyber-terminal` — 暗终端 honest review

- **视觉**：`#0a0c10` 黑 + 56px cyber 网格 + CRT vignette + scanlines + window traffic-light
- **关键特征**：`$ prompt` 命令行标题 + mint-green `#7ed3a4` 大字 + JetBrains Mono + stroke-only 柱状图 + blinking cursor
- **场景**：CLI / agent / dev tool 评测——「honest technical reviewer」语调
- **路径**：[`assets/archive/full-deck-refs/hermes-cyber-terminal/`](../assets/archive/full-deck-refs/hermes-cyber-terminal/)

## 中适用（场景型）

### `pitch-deck` — VC 路演

- **视觉**：白 + 蓝→紫渐变，YC/VC vibe，大数字 + traction chart
- **场景**：融资路演 / 战略汇报 / 投资人会议（Platform C 内部战略级路演也适用）
- **路径**：[`assets/archive/full-deck-refs/pitch-deck/`](../assets/archive/full-deck-refs/pitch-deck/)

### `product-launch` — 产品发布会

- **视觉**：暗色 hero + 浅色内容 + 暖橙→桃渐变 + 功能卡片 + pricing tiers + CTA
- **场景**：社区功能发布 / 产品发布会 keynote
- **路径**：[`assets/archive/full-deck-refs/product-launch/`](../assets/archive/full-deck-refs/product-launch/)

### `dir-key-nav-minimal` — 极简方向键

- **视觉**：8 页各用独立 mono 背景色（靛蓝 / 奶油 / 红 / 翠 / 石板 / 紫 / 白 / 炭黑）+ 各自 accent + 160px 大标题 + 4px 短装饰线
- **关键特征**：箭头 `→` 前缀 Mono 列表 + 巨大留白 + 一思想 / 页
- **场景**：keynote 风极简演讲 / 公开 talks / launch
- **路径**：[`assets/archive/full-deck-refs/dir-key-nav-minimal/`](../assets/archive/full-deck-refs/dir-key-nav-minimal/)

### `xhs-white-editorial` — 白底杂志风

- **视觉**：纯白底 + 顶 10 色彩虹条 + 80-110px 大标题 + 紫→蓝→绿→橙→粉 渐变文字 + 马卡龙软卡 + 黑底白字 `.focus` 药丸
- **场景**：双用（小红书图文 + 横版 deck）/ 文字密度大 + 强烈强调 / 中文为主受众
- **路径**：[`assets/archive/full-deck-refs/xhs-white-editorial/`](../assets/archive/full-deck-refs/xhs-white-editorial/)

## 弱适用（视觉灵感储备）

### `graphify-dark-graph` — 暗底知识图谱

- **视觉**：`#06060c→#0e1020` 深夜渐变 + 漂浮 blur 光球 + SVG 力导向图谱 cover + 彩虹渐变标题
- **场景**：dev-tool / CLI / 知识图谱 / 数据可视化 launch；live-demo deck 想要「AI-native + sci-fi + 暖色」
- **路径**：[`assets/archive/full-deck-refs/graphify-dark-graph/`](../assets/archive/full-deck-refs/graphify-dark-graph/)

### `obsidian-claude-gradient` — GitHub 暗紫渐变

- **视觉**：GitHub-dark `#0d1117` + 紫蓝径向环境光 + 60px masked 网格 + 居中布局 + 紫色 pill 标签 + 三色渐变文字
- **场景**：developer workflow / MCP / Agent / dev-tool 教程——GitHub Blog / Linear Changelog 感
- **路径**：[`assets/archive/full-deck-refs/obsidian-claude-gradient/`](../assets/archive/full-deck-refs/obsidian-claude-gradient/)

### `testing-safety-alert` — 红琥珀警示

- **视觉**：上下 45° 红黑危险条纹 + 红色 strike-through 否定标题 + L1/L2/L3 绿琥珀红三档卡 + alert box 圆形状态点 + policy-yaml 代码块（红左边框 + bad 关键词高亮）
- **场景**：安全 / 风险 / 事故复盘 / red-team / 上线前 AI review / policy-as-code——需要「严肃，别 skim」感
- **路径**：[`assets/archive/full-deck-refs/testing-safety-alert/`](../assets/archive/full-deck-refs/testing-safety-alert/)

### `xhs-pastel-card` — 柔和马卡龙慢生活

- **视觉**：奶油 `#fef8f1` 底 + 3 个柔模糊光球 + Playfair italic 衬线大标题（混 sans 正文）+ 全色 28px 圆角马卡龙卡片
- **场景**：生活方式 / 个人成长 / 慢生活 / 情绪内容——「杂志 / 手作 / 非技感」
- **路径**：[`assets/archive/full-deck-refs/xhs-pastel-card/`](../assets/archive/full-deck-refs/xhs-pastel-card/)

### `xhs-post` — 小红书 3:4 图文

- **视觉**：3:4 @ 810×1080 + 暖马卡龙 + 虚线贴纸卡 + 页点
- **场景**：小红书 9 页图文 post / Instagram carousel
- **路径**：[`assets/archive/full-deck-refs/xhs-post/`](../assets/archive/full-deck-refs/xhs-post/)

### `course-module` — 教学模块

- **视觉**：暖纸 + Playfair 衬线 + 持续左侧学习目标 sidebar + 选择题自查
- **场景**：教学模块 / 在线课程 / workshop
- **路径**：[`assets/archive/full-deck-refs/course-module/`](../assets/archive/full-deck-refs/course-module/)

## 跟我们 ppt skill 主流程的关系

- 主流程（`ppt-template.html` + `fill-template.js` + `PAGE_RENDERERS` + ClaudeDesign `--cd-*` 体系）**保持不变**
- full-deck-refs/ 是**纯参考库**，没有任何代码进 fillTemplate 的注入路径
- 模型 / PM 看到某套喜欢，**只参考视觉语言**（色卡 / 字体 / 卡片处理 / 排版节奏），不抠原 HTML 进 fillTemplate（变量名空间冲突）
- 例外：scaffold 复制路径不走 fillTemplate（用 lewislulu 全套 base.css + runtime.js）

## 注意事项

- `_assets/` 是 lewislulu 全套基础设施（base.css / fonts.css / runtime.js / 36 主题 / animations.css），仅给 full-deck-refs/ 内部用，**不要**让主 ppt-template 引用
- 36 个 lewislulu 主题文件用 `--bg / --text-1 / --accent` 等变量名，跟我们 `--cd-*` 体系**不兼容**，仅供 full-deck demo 渲染用
- 跳过了 lewislulu 的 20 个 Canvas FX（`fx-runtime.js` + `fx/*.js`）—— Felix 工区 PM 评审 / SOP / 数据周报场景用不到，少 ~30 个 JS 文件维护面
