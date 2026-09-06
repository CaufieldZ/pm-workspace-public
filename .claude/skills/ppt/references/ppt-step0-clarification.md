# PPT Step 0 · 需求澄清门完整规则

> 触发：SKILL.md Step 0 引用本文档。PM 第一次接需求时按此走 0.1 → 0.2 → 0.3 三步澄清。

## 跳过条件（满足任一即跳过）

- 用户说「跳过澄清」「快速模式」「按 context 执行」「直接做」
- 已有大纲 / 简报含明确用途 + 受众
- 极小改动（≤ 1 个 Tab 的修改 / 补充）

注：用户「直接提供完整大纲」**不算跳过条件** —— 大纲不能替代用途 / 论点判定，仍要走 0.1 / 0.2。

## Step 0.1：用途识别（10 秒判定）

第 0 问：这份 PPT 主要场景？

| 选项 | 说明 | 走的子门 |
|---|---|---|
| A · SOP 手册 / 工作流文档 | 读者自查、长期维护 | 文档型门 |
| B · 演讲材料 / 内部汇报 / 评审 | 台上现场讲 | 演讲型门 |
| C · 对外宣讲 / 营销物料 | 外部受众、品牌物料 | 演讲型门（外部分支） |
| D · 方法论沉淀 / 培训复盘 | 自看 + 培训 | 文档型门 |

## Step 0.2：主题色推荐（按用途自动推 1 主 + 1 备选 + 一句理由）

模型主动给推荐，**不让 PM 在 9 套裸选**：

| 用途 | 主推 | 一句理由 | 备选 |
|---|---|---|---|
| B 演讲 / D 方法论沉淀（纯 deck 默认） | **vendor-editorial** | 中文衬线杂志感 + teal/amber 双语义 + 浅深双底，结论先行五幕叙事 | claude-native（更克制的暖近黑 sidebar Doc） |
| A SOP 手册（长文档 sidebar Doc） | **claude-native**（默认 tokens.css，#1F1F1E + #D97757） | 暖近黑长读不刺眼、品牌一致、Felix 钦定典范 | ink-classic（怕暗底累就切纸感亮底） |
| B 演讲（金融 / 交易主题） | **fintech-dark** | 暗底 + 涨绿跌红，金融语义 + Deck 视觉冲击 | vendor-editorial（非交易数据场景更杂志感） |
| C 对外宣讲 | **paper-zen** | 国风暖色，品牌温度 + 一图流 / 海报场景 | indigo-porcelain（青花瓷克制） |

**「claude-native」定义** = 不 import 任何 `themes/*.css`，只用 `_shared/claude-design/tokens.css` 默认值（暖近黑 `#1F1F1E` + terra cotta `#D97757` + Lora + Poppins + Noto SC + JetBrains Mono）。

PM 看主推 OK 就过；要换备选 / 上其他 5 套（cyber-noir / kraft-paper / swiss-grid / muji-minimal / book-architecture）说一声再调。

### 主题落地说明

fillTemplate 调用时传 `theme` 参数自动加载对应主题（默认 `claude-native` = tokens.css 默认值，其余主题在 tokens.css 之后追加 `_shared/claude-design/themes/{theme}.css`，CSS 后写覆盖先写自动 override `--cd-*` 变量）。**无需手工调色 / 无需后处理替换。**

### 可用主题清单（10 套）

| theme name | 视觉一句话 |
|---|---|
| `vendor-editorial` | 中文衬线杂志感 + teal/amber 双语义 + 浅深双底（纯 deck 范式默认） |
| `claude-native` | 暖近黑 #1F1F1E + terra cotta + Lora/Poppins/Noto SC/JetBrains Mono（sidebar Doc 默认） |
| `fintech-dark` | 暗底 + 金融语义色（涨绿跌红 / 蓝 accent） |
| `paper-zen` | 国风暖色 #FAF6EC + 深绿 + 茶金 |
| `ink-classic` | 纸感亮底 + 墨色，长读不刺眼 |
| `cyber-noir` | 赛博朋克暗紫，地下文化 |
| `kraft-paper` | 牛皮纸暖底，手作 / 复古 |
| `swiss-grid` | 瑞士网格白底，严肃排版 |
| `muji-minimal` | 无印良品极简，灰白克制 |
| `book-architecture` | 书籍排印感，奶油底 + 衬线 |
| `indigo-porcelain` | 青花瓷克制（对外宣讲备选） |

### 调用示例

```js
fillTemplate({
  title: '...',
  theme: 'fintech-dark',
  nav: [...],
  renderers: {...},
  outputPath: '...'
});
```

theme 未找到时自动 fallback 到 claude-native 并打 warning，不阻断生成。

## Step 0.3：子门对齐

**视觉锚点（可选）**：`references/full-decks.md` 列了 15 套从真实作品提炼的整套视觉语言（lewislulu/html-ppt-skill 提供），PM 可指定参考某套（如「按 `tech-sharing` 视觉做」/「按 `weekly-report` 配色 + 8-cell KPI grid」），让模型在生成 PAGE_RENDERERS 时**模仿其视觉特征**（色卡 / 字体搭配 / 卡片处理 / 排版节奏），产物仍走标准 fillTemplate 流程。强适用：`presenter-mode-reveal` / `tech-sharing` / `weekly-report` / `knowledge-arch-blueprint` / `hermes-cyber-terminal`。

### 文档型门（A SOP / D 方法论）4 问

| # | 问题 | 决定什么 |
|---|---|---|
| 1 | 读者岗位职级？（运营 / 产品 / 研发 / leader / 跨部门） | 术语深度 + 是否需要术语表页 |
| 2 | 章节切分逻辑？（按工作流阶段 / 按角色 / 按工具 / 按项目） | NAV 分组结构 |
| 3 | 要不要 prompt / 模板展示页？ | 是否启用 modal 弹窗 + prompt-block |
| 4 | 硬约束？（必含 X / 不出现 Y） | 避免返工 |

文档型**不问**：核心论点、时长、谁讲、要不要演讲稿（自查文档无演讲场景）。

### 演讲型门（B 内部 / C 对外）5 问，论点必答

| # | 问题 | 决定什么 |
|---|---|---|
| 1 | **核心论点**（讲完听众带走的一句话，**必答不可跳**） | 全文骨架 + 反 AI slop 收尾 |
| 2 | 受众 + 时长 → 模型推算页数（不让 PM 自己算） | Tab 数量 + 节奏密度 |
| 3 | 谁在台上讲？（自讲 / leader 讲 / 录屏自看） | 语气 + chrome/foot 字段密度 + data-step 用量 |
| 4 | 要不要演讲稿 docx？（提前定，避免 Step 6 才补） | 是否预留 NOTES 字段 |
| 5 | 硬约束？（C 对外场景必加问法务 / 品牌色限制） | 避免返工 |

### 演讲型门附：逐字稿三铁律（NOTES 字段必守）

问 4 选「要演讲稿」时，按这三条铁律写 `<aside class="notes">` 内容（来自 `references/presenter-notes.md` lewislulu 方法论）：

1. **不是讲稿，是提示信号** —— 加粗核心词 `<strong>`，过渡句独立成段。看一眼能接上，不是逐字念
2. **每页 150-300 字** —— 少于 150 字提示不够会卡，多于 300 字眼睛扫不过来。2-3 分钟 / 页节奏
3. **用口语，不用书面语** —— 「所以」不是「因此」，「但是」不是「然而」，「这个」不是「该」，「简单来说」不是「综上所述」。写完读一遍听起来像说话才对

NOTES 数据走 `fillTemplate({ notes: { tabId: '<p>...</p>' } })`，注入 `window.__PPT_NOTES__`，按 S 键弹独立 popup 提词器窗口（CURRENT / NEXT iframe 像素级预览 + SPEAKER SCRIPT 大字号 + TIMER 计时）。详细见 `references/presenter-notes.md`。
