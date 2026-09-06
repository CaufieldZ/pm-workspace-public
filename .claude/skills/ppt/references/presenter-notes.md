# 演讲者模式指南

> 适用场景：B 内部演讲 / C 对外宣讲（Step 0.1 用途识别）。Step 0.3 演讲型门问 4 选「要演讲稿」时按本文档写 NOTES。
> 文档型（SOP / 方法论）不用看本文档——没演讲场景就不需要逐字稿。
> 方法论源自 [lewislulu/html-ppt-skill `references/presenter-mode.md`](https://github.com/lewislulu/html-ppt-skill)，本文档是 Felix 工区适配版。

## 何时启用演讲者模式

PM 在 Step 0.3 演讲型门答「要演讲稿」时启用。常见关键词：

- 提到「演讲」「分享」「讲稿」「逐字稿」「speaker notes」
- 提到「presenter view」「演讲者视图」「演讲者模式」「提词器」
- 要做「30 分钟 / 45 分钟 / 1 小时分享」
- 说「不想忘词」「怕讲不流畅」

如果是静态好看的 PPT（小红书图文 / 产品图册 / 周报自看 / SOP 手册），**不需要**演讲者模式。

## 体系架构

### 主窗口 + 独立 popup（S 键）

```
观众窗口（主窗口）           演讲者窗口（独立 popup）
┌─────────────────┐   ┌─────────────────────┬──────────────────┐
│                 │   │ ● CURRENT          │ ● NEXT             │
│  ppt-template   │   │ ━━━━━━━━━━━━━━━━ │ ━━━━━━━━━━━━━ │
│  Tab 切换       │◄►│  iframe ?preview= │  iframe ?preview=  │
│  全屏展示       │   │  当前 tab ID      │  下一 tab ID       │
│                 │   ├─────────────────────┼──────────────────┤
│                 │   │ ● TIMER            │ ● SPEAKER SCRIPT   │
│                 │   │ 12:34   3 / 8     │ 大字号逐字稿       │
│                 │   │ [←][→][Reset]     │ 可滚动             │
└─────────────────┘   └─────────────────────┴──────────────────┘
       BroadcastChannel('ppt-deck') 双向同步翻页
```

**核心技术**：

1. **`?preview=ID` URL 参数**：popup 内 iframe 加载主 deck，runtime 检测 `?preview` → 只显当前 tab + 隐 chrome（sidebar / header / hud）
2. **CSS `transform: scale()`**：iframe 等比缩 1920×1080 到卡片尺寸，**与观众视图 100% 同色同字体同排版**
3. **BroadcastChannel 双向同步**：观众和 popup 互发 `{type:'goto', id}`，任一端切 tab 另一端自动跟随
4. **postMessage 零闪烁切页**：iframe 常驻不 reload，切 tab 时 popup 向 iframe `postMessage({type:'preview-goto', id})`，iframe 内 runtime 只切 `.is-active`
5. **4 卡片磁吸 drag/resize**：拖 header 移位，拖右下角 resize，位置 / 尺寸 `localStorage` 持久化

### 与现有 P 键的关系

- `P` 键（presenter-mode.js）= **整窗 Doc⇄Deck 切换**，单屏台上自看场景
- `S` 键（ppt-template.html）= **弹独立 popup 提词器窗口**，双屏 / 投屏场景

两者互不干扰，可同时开（主窗 P 模式 + popup S 提词）。

## 逐字稿三铁律（NOTES 字段必守）

### 铁律 1：不是讲稿，是「提示信号」

❌ **错误写法**（像在念稿）：

```html
<aside class="notes">
<p>大家好，欢迎来到今天的分享。今天我将要给大家介绍一下我们团队
在过去三个月做的工作。首先，我们来看一下背景情况。在过去的三个月
中，我们遇到了以下几个问题……</p>
</aside>
```

✅ **正确写法**（提示信号 + 加粗核心 + 过渡句独立成段）：

```html
<aside class="notes">
<p>欢迎！今天分享团队<strong>过去 3 个月</strong>的工作。</p>
<p>先说<em>背景</em>——三个月前遇到 <strong>3 个核心问题</strong>：
延迟高、成本炸、稳定性差。</p>
<p>接下来逐个讲怎么解的。</p>
</aside>
```

**差别**：关键词 `<strong>` 加粗，过渡句独立成段，扫一眼能接上。

### 铁律 2：每页 150-300 字

- **少于 150 字**：提示不够，讲到一半会卡
- **多于 300 字**：眼睛根本扫不过来，等于没写
- **2-3 分钟 / 页** 最舒服

### 铁律 3：用口语，不用书面语

| ❌ 书面语 | ✅ 口语 |
|---|---|
| 因此 | 所以 |
| 该方案 / 该问题 | 这个方案 / 这个问题 |
| 然而 | 但是 / 不过 |
| 进行优化 / 进行调研 | 优化一下 / 调研一下 |
| 我们将会 | 我们会 / 接下来 |
| 综上所述 | 简单来说 / 所以 |
| 较为 | 比较 |
| 多方面 | 好几个方面 |

**自检**：写完读一遍，听起来像说话才对。

## NOTES 数据如何注入

### Step 3 fillTemplate 调用示例

```js
const { fillTemplate } = require('../../../../.claude/skills/ppt/assets/fill-template.js');

const NOTES = {
  cover: `<p>大家好，今天分享 <strong>社区运营 3 个月复盘</strong>。</p>
          <p>3 个数字：<strong>用户量 +50%</strong>、<strong>留存 +20%</strong>、<strong>GMV +30%</strong>。</p>
          <p>怎么做的？接下来一一拆解。</p>`,
  problems: `<p>先看<em>问题</em>——3 个月前我们卡在哪。</p>
             <p>第一，<strong>新用户进来 7 天就流失 60%</strong>。</p>
             <p>第二，老用户活跃度连续 4 周下滑。</p>
             <p>这两个一起，DAU 撑不住了。</p>`,
  solutions: `<p>所以我们做了 <strong>3 件事</strong>。</p>
              <p>第一是新手引导改版，第二是积分体系上线，第三是社群召回。</p>
              <p>下面一个一个讲。</p>`,
  // ... 每个 tab 一段，150-300 字
};

fillTemplate({
  title: '社区 Q1 复盘',
  theme: 'claude-native',
  nav: [...],
  renderers: {...},
  notes: NOTES,
  outputPath: 'projects/community/deliverables/ppt-q1-review-v1.html'
});
```

### 使用方式

1. 浏览器打开生成的 `ppt-*.html`
2. 按 `S` 键 → 弹独立 popup 提词器窗口
3. 把**观众窗口**（主 ppt-template）拖到投影屏，按 `F` 全屏
4. 把**演讲者窗口**（popup）留在面前的屏幕
5. 任一窗口按 ← → 翻页，两边自动同步
6. popup 内看：当前页预览 / 下一页预览 / 大字号逐字稿 / 计时器

### 演讲者 popup 键位

| 键 | 动作 |
|---|---|
| ← → / Space / PgDn | 翻页（同步主窗口） |
| R | 重置计时器 |
| ESC | 关闭 popup |

### 主窗口键位（除 popup 外）

| 键 | 动作 |
|---|---|
| S | 弹 popup 提词器 |
| P | 整窗 Doc ⇄ Deck 切换（presenter-mode.js） |
| 点击 sidebar 项 | 切 tab |

## 推荐主题搭配

| 场景 | 主题 | 理由 |
|---|---|---|
| 技术分享 / 内部演讲 | `fintech-dark` / `cyber-noir` | 暗底 + 金融语义色 / 赛博朋克，技术语调 |
| 商务汇报 / 战略级 | `swiss-grid` / `book-architecture` | 瑞士网格 / 书籍排印，克制严肃 |
| 对外宣讲 / 品牌物料 | `paper-zen` / `kraft-paper` | 国风暖色 / 牛皮纸，品牌温度 |
| 通用 / 默认 | `claude-native` | 暖近黑 + terra cotta，长读不刺眼 |

## 常见错误

### ❌ 把逐字稿写在 page 可见位置

```html
<!-- 错误：观众会看到这段灰色小字 -->
<p style="font-size:12px;color:gray">
  这里讲 xxx，然后讲 yyy...
</p>
```

✅ 正确：走 `notes` 参数注入 `window.__PPT_NOTES__`，**完全不进 page DOM**：

```js
fillTemplate({
  notes: { 'tab-id': '<p>这里讲 xxx...</p>' },
  ...
});
```

### ❌ 逐字稿用书面语

念出来像 AI 机器人。**写完一定读一遍**听是否像说话。

### ❌ 每页 50 字 / 500 字

50 字提示不够照样忘词；500 字眼睛扫不过来等于没写。**150-300 字**是底线。

### ❌ 用 NOTES 数组（lewislulu 写法）

lewislulu 是 `<aside class="notes">` 嵌入 slide HTML 内。我们走**集中字典注入**（`window.__PPT_NOTES__`），方便从 NOTES 数组单独管理 + 导出 docx。

## 用 AI 生成逐字稿的标准 prompt

> "请为以下每个 tab 写一段 **150-300 字的逐字稿**，作为 `NOTES` 字典传给 fillTemplate（key = tab id，value = HTML 字符串）。
> 要求：
> 1. 用**口语**，不要书面语（所以 / 但是 / 接下来 / 简单来说，不是因此 / 然而 / 综上所述）
> 2. 把**核心关键词**用 `<strong>` 加粗，关键概念用 `<em>` 强调
> 3. 过渡句独立成段（每段 1-3 句）
> 4. 读起来像说话，不像念稿
> 5. 结尾要有自然过渡，引出下一页"

## 与 docx 演讲稿导出的关系

走 [`scripts/gen-notes-docx.py`](../scripts/gen-notes-docx.py) 导 docx：脚本从 HTML 产物里抽 `window.__PPT_NOTES__` 数据，按 NAV 顺序生成 docx 文件给 PM 打印 / 备用。
