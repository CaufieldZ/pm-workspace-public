<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# Templates Index · 产物模板索引手册

> **用途：** 新对话开头上传此文件 + 对应 template.html + context.md → Claude 精准产出
> **覆盖产物：** 方案架构图集 / 交互大图 / 可交互原型 / PRD / 需求框架

---

# 0. 使用 SOP

## 0.1 对话启动流程

```
用户 开新对话
│
├─ 从0-1需求？
│   ├── 用户 描述需求背景
│   ├── Claude 和 用户 讨论，对齐场景、角色、核心决策
│   ├── Claude 主动生成 context.md → 用户 确认
│   └── 进入 0.2 产物选择
│
├─ 已有项目迭代？
│   ├── 用户 上传历史 context.md
│   ├── Claude 读取，确认理解无误
│   ├── 用户 说明本轮变更点 → Claude 更新 context.md → 用户 确认
│   └── 进入 0.2 产物选择
│
└─ 用户 直接指定产物？
    ├── 用户 上传 context.md + templates-index.md + 对应模板文件
    └── Claude 直接产出（跳过 0.2）
```

## 0.2 产物选择（Claude 主动问）

Claude 读完 context.md 后，主动问 用户：

> "这个项目需要产出哪些产物？我基于复杂度建议 {{推荐组合}}，你确认或调整。"

用户 确认后，用户 上传对应的模板文件，Claude 开始产出。

**每个产物产出完成后，Claude 主动提醒：**
- 更新 context.md 的「当前状态」和「已交付产出物」
- 如果下一个产物有前置依赖，提醒 用户 确认前置产物

## 0.3 产物产出流程（每个产物通用）

```
Claude 读取 context.md
  ↓
Claude 读取 templates-index.md 中对应产物的章节（了解结构+组件+规则）
  ↓
Claude 读取对应 template 文件（了解骨架代码）
  ↓
Claude 基于 context.md 内容填充模板
  ↓
Claude 跑自检清单（templates-index.md 中每个产物末尾的 checklist）
  ↓
输出文件 → 用户 审阅 → 反馈修改 → 定稿
  ↓
Claude 更新 context.md（状态+已交付）
```

## 0.4 跨产物一致性规则

| 规则 | 说明 |
|------|------|
| **场景编号锁定** | context.md 场景编号一旦确定，所有产物必须沿用，不可改动 |
| **术语一致** | context.md 术语表是唯一真相源，需求框架/交互大图/原型/PRD 全局统一 |
| **编号对齐** | 需求框架编号 = 交互大图 Scene 编号 = 原型页面编号 = PRD 章节内 Scene 编号 |
| **截图来源** | PRD 左侧截图从可交互原型中截取 |
| **变更标记** | context.md 的「核心变更」驱动所有产物中的 NEW/变更/删除 标记 |

---

# 0.5 产物决策树

## 按需求路由选择产物组合

```
判定规则（满足任一即为复杂）：
  ≥2端/角色、≥5场景且有跨场景跳转、含数据同步/状态流转/多角色协作

┌─ 简单链路
│   纯功能点 → 直接 Markdown PRD
│   单页面交互 → 直接出原型
│   纯文案/策略 → 直接文档
│   不需要模板体系
│
├─ 复杂链路（每步等确认）
│   > Chat 轨中场景清单在 context.md 生成过程中完成（第 4 章），
│   > 不需要单独用模板产出。下方链路从需求框架开始。
│   ① 需求框架 ─────────── 可选，场景多(≥8)时建议出
│   ② 交互大图 ─────────── 必选
│   ③ 可交互原型 ────────── 可选，需演示/高保真时用
│   ④ PRD(.docx) ─────────── 必选
│
├─ 超复杂方案（涉及多系统对接/资金流转/架构设计/商业测算）
│   ① 需求框架 ─────────── 建议出
│   ② 方案架构图集 ──────── 必选（超复杂专属）
│   ③ 交互大图 ─────────── 必选
│   ④ 可交互原型 ────────── 可选，需演示/高保真时用
│   ⑤ PRD(.docx) ─────────── 必选
│
└─ 用户 要求跳步？
    可以，但 Claude 必须提醒风险：
    - 跳需求框架：场景多时容易遗漏模块
    - 跳交互大图：研发无法理解跨端数据流
    - 跳原型：老板/运营无法直观感受交互
    - 跳 PRD：研发没有需求细节参考
```

## 产物依赖关系

```
context.md（唯一真相源）
  │
  ├→ 需求框架（可选，无前置依赖）
  │
  ├→ 方案架构图集（超复杂专属，无前置依赖）
  │
  ├→ 交互大图（依赖：场景编号已锁定）
  │     │
  │     └→ 可交互原型（依赖：交互大图中的场景+布局已确认）
  │           │
  │           └→ PRD（依赖：原型已确认，截图从原型取）
  │
  └→ 纯文字 PRD（Markdown，不走模板体系，用于飞书/钉钉）
```

## 产物 × 模板文件对应

| 产物 | 模板文件 | 格式 | 章节 |
|------|---------|------|------|
| 需求框架 | `requirement-framework-template.html` | html | §5 |
| 方案架构图集 | `solution-atlas-template.html` | html | §1 |
| 交互大图 | `interaction-map-template.html` | html | §2 |
| 可交互原型 | `interactive-prototype-template.html` | html | §3 |
| PRD | `gen-prd-template.js` → `.docx` | js+docx | §4 |

---
---

# 1. 方案架构图集（Solution Atlas）

> **模板文件：** `solution-atlas-template.html`
> **产物类型：** 多 Tab 信息文档，等同 PPT 给老板讲方案

## 1.1 结构

```
.tb (Tab 栏) → .pw#t0~tN (页面面板) → .pg (max-width:1120px)
每页：h1 → .sub → .rl → [内容区] → .co callout
```

## 1.2 组件

| 类名 | 用途 | 变体 |
|------|------|------|
| `.cd` | 卡片 | inline style 控色 |
| `.co` | Callout | `-b`蓝 `-a`橙 `-r`红 `-g`绿 `-v`紫 |
| `.st` | 段标题 | emoji 前缀 |
| `.sec` | 分隔线 | `<b>` 标签 + `.sl` 线 |
| `.tg` | 标签 | `-k`绿已有 `-n`青新建 `-w`橙复用 `-c`红风险 `-p`紫规划 |
| `.sn` | 步骤圆 | `-b`蓝 `-g`绿 `-r`红 `-a`橙 `-p`紫 |
| `.fx` | Flex等宽行 | — |
| `.leg` | 图例栏 | `.leg-i` + `.leg-s` |
| `.addr` | 地址高亮 | 红色固定 |

**布局：** 等宽Grid / 加权Grid / Flex / Flow链 / Swimlane / Span列

**颜色语义：** 核心=黄 / 新建=蓝紫 / 正面=绿 / 负面=红 / 中性=灰dashed / 规划=紫 / 信息=蓝

## 1.3 页面类型（13 种 A-M）

| Type | 名称 | 核心组件 |
|------|------|---------|
| A | 背景与定位 | 角色卡片grid + 循环链 + 术语表 |
| B | 方案选型 | 关系卡片 + 硬伤卡片 + 对比表(推荐列高亮) |
| C | 架构总览 | 高亮框 + sec分隔线 + grid模块卡片 + 图例 |
| D | 数据模型 | 嵌套卡片(大卡内flex子卡) + 状态变动table |
| E | 生命周期泳道 | 列头 + 步骤行(sn+N列) |
| F | 场景矩阵 | 大表(编号①②) + 风险callout |
| G | 流程详解 | 实体grid + 正常/异常双列 |
| H | 机制对比 | 模式卡(Phase标签) + 公式框 + 步骤grid |
| I | 风控告警表 | F表格 + C参数grid |
| J | 风险分析 | 红色大框 + 2×2方案grid + 推荐table |
| K | 定量测算 | 问题grid + 公式框 + 场景table |
| L | Phase路线图 | Phase大卡(绿→蓝→紫) |
| M | 待确认清单 | 分组标签 + 问题table + 话术框 |

**Tab 规划：** 中等6-8 / 复杂8-12 / 超复杂12-14

## 1.4 自检

- [ ] Tab 编号连续 sw(N)↔id="tN"
- [ ] 每页 h1+.sub+.rl+底部callout
- [ ] 术语+数字全文件一致
- [ ] 推荐=绿 / 风险=红 / Phase=绿→蓝→紫

---
---

# 2. 交互大图（Interaction Map）

> **模板文件：** `interaction-map-template.html`
> **产物类型：** 长页面静态文档，侧边栏锚点导航，HTML+CSS 画真实 UI
> **架构：** 产物2（长页面+PART分组+侧边栏+渐入动画），融合产物1的4项优势组件

## 2.1 结构

```
.progress-bar          — 顶部阅读进度条
.side-nav              — 左侧锚点导航（滚动跟随，1400px 以下隐藏）
.hd                    — sticky header + 图例
.cv                    — 内容区（≥1400px 时 margin-left:160px）
├── .gd.viewer         — PART 分隔：客户端/App（深色）
│   └── [.st + .flow] × N scenes
├── .gd.host           — PART 分隔：Web 工作台（浅蓝）
│   └── [.st + .flow] × N scenes
├── .gd.cms            — PART 分隔：CMS 后台（浅红）
│   └── [.st + .flow] × N scenes（用 .mg 组件）
├── .gd.cross          — PART 分隔：跨端数据流（浅绿）
│   └── 6列 grid 表
├── .sum-wrap          — 场景总览表（底部索引）
└── .co × 2            — 阅读指引 + 优先级
```

**PART 分组主题色：**

| class | 颜色 | 用于 |
|-------|------|------|
| `.gd.viewer` | 深色渐变 | 客户端/App 端 |
| `.gd.host` | 浅蓝渐变 | Web 工作台/管理端 |
| `.gd.cms` | 浅红渐变 | CMS 运营后台 |
| `.gd.cross` | 浅绿渐变 | 跨端数据流衔接 |

可自定义更多 PART 主题，按项目端数调整。

## 2.2 组件库

### 设备框

| 组件 | 用途 | 宽度 | 壳色 |
|------|------|------|------|
| `.phone` | App 壳 | 375px | 深色 var(--dark)，圆角 36px |
| `.webframe` | 浏览器壳 | 580px（大图） | 白色 var(--surface)，三色圆点 |
| `.mg` 前缀 | 后台 Arco 组件 | 嵌入 webframe 内 | 浅灰 #F5F6FA |

### Flow 核心

| 组件 | 用途 |
|------|------|
| `.flow` | 横向容器（flex, overflow-x:auto） |
| `.flow-col` | 设备框列（label + 框 + note） |
| `.aw` → `.al.b/g/r/o/p` + `.tx` | 箭头（线+文字），5色 |
| `.aw .al.da` | 虚线箭头 |
| `.flow-note` | 框下说明文字 |
| `.reuse-box.blue/green/amber/purple` | 复用/跳转占位（虚线框） |

### 标注（两种方式并存）

| 方式 | 组件 | 适用 |
|------|------|------|
| **轮廓式** | `.hi.blue/green/red/amber/purple` + `.badge` | 单元素快速标注，加 class 即可 |
| **覆盖式** | `.anno` + `.anno-n` | 跨多子元素的区域标注，需手动定位 |

| 组件 | 用途 |
|------|------|
| `.ann-card` | 标注说明卡（flow 右侧，width:320px） |
| `.ann-item` = `.ann-num` + `.ann-text` | 单条说明 |
| `.ann-tag.p0/p1/p2/new/chg/del` | 优先级/状态标签 |

### 颜色语义（箭头 + 标注 + 虚线框统一）

| 色 | 变量 | 含义 | 箭头 | 编号圆 | 虚线框 |
|----|------|------|------|--------|--------|
| 蓝 | `--blue` | 主链路 | `.al.b` | `.ann-num.blue` | `.hi.blue` / `.anno.blue` |
| 绿 | `--green` | 新增 | `.al.g` | `.ann-num.green` | `.hi.green` / `.anno.green` |
| 红 | `--red` | 删除/风险 | `.al.r` | `.ann-num.red` | `.hi.red` / `.anno.red` |
| 橙 | `--amber` | 跨端/注意 | `.al.o` | `.ann-num.amber` | `.hi.amber` / `.anno.amber` |
| 紫 | `--purple` | 特殊 | `.al.p` | `.ann-num.purple` | `.hi.purple` / `.anno.purple` |

### 后台 Arco 组件（.mg）

| 组件 | 用途 |
|------|------|
| `.mg .sidebar` + `.s-item` / `.s-item.act` | 深色侧边栏 + 菜单项 |
| `.mg .main` | 浅灰主内容区 |
| `.mg .toolbar` + `.btn-p` / `.btn-s` | 工具栏（主按钮蓝/次按钮白） |
| `.mg .tbl` | 数据表格 |
| `.mg .modal` + `.modal-hd` / `.modal-bd` / `.modal-ft` | 弹窗三段式 |
| `.mg .f-row` + `.f-lbl` / `.f-inp` / `.f-sel` / `.f-hint` | 表单行 |
| `.mg .f-sec` + `.f-sec-t` | 表单分段 |

### 其他

| 组件 | 用途 |
|------|------|
| `.co.bl/.gn/.am/.rd` | Callout（蓝/绿/橙/红） |
| `.info-box.blue/.purple/.amber/.green` | 技术说明小框 |
| `.lane-hd` | Scene 内子分支分隔 |
| `.gd` | PART 分组大分隔 |
| `.sum-wrap` + `.sum-tbl` | 场景总览表 |
| `.fade-section` | 滚动渐入动画 |

## 2.3 核心 Flow 模式

```
.flow
├── .flow-col (phone-label + .phone + .flow-note)
├── .aw (.al.b + .tx.b "2-4字动作")
├── .flow-col (phone-label + .phone/.webframe + .flow-note)
├── div(width:20px)  — 间距
└── .ann-card (card-title + .ann-item × N)
```

**规则：**
- 一个 `.flow` 通常 2-3 个设备框 + 1 个标注卡
- 设备框内是**真实 UI**（深色画 App / 浅色画 Web / Arco 画后台），不是线框图
- 标注用虚线框 + 编号圆点，编号在标注卡里对应解释
- 简单标注用 `.hi`（轮廓式），跨区域标注用 `.anno`（覆盖式）
- Scene 内分支用 `.lane-hd` 分隔
- 跨端引用用 `.reuse-box` 占位，不重复画设备框

## 2.4 跨端数据流表

放在最后一个 PART（`.gd.cross`）下方，6 列 grid：

```
# | 起点(名称+动作) | →(箭头) | 终点(名称+动作) | 数据字段 | 触发方式+延迟
```

下方跟 `.info-box.green` 写同步机制、延迟分级、容错说明。

## 2.5 context.md → 交互大图映射

| context.md Section | 驱动 |
|---|---|
| 产品现状 → 端描述 + 页面结构 | PART 划分 + 设备框 UI 布局 |
| 场景编号 | Scene 编号/名称/锚点 |
| 术语表 | 框内文案 + 标注卡用词 |
| 本轮方案决策 → 核心变更 | 标注颜色（绿=新增 蓝=改动 红=删除） |
| 关键业务规则 | 标注卡规则说明 + info-box |
| 竞品参考 | UI 还原参考 |

## 2.6 PART 规划规则

| 项目特征 | PART 数量 | 典型组合 |
|---------|----------|---------|
| 单端（纯 App） | 1+1 | PART 0 App + PART 1 跨端 |
| 双端（App + 后台） | 2+1 | PART 0 App + PART 1 CMS + PART 2 跨端 |
| 三端（App + Web工作台 + 后台） | 3+1 | PART 0 App + PART 1 Web + PART 2 CMS + PART 3 跨端 |
| 复杂（含前置链路） | 4+1 | PART 0 前置链路 + PART 1 App + PART 2 Web + PART 3 CMS + PART 4 跨端 |

跨端数据流始终是最后一个 PART。

## 2.7 自检

- [ ] Scene 编号与 context.md 一致
- [ ] 每 Scene 至少 1 设备框 + 1 标注卡
- [ ] 标注编号连续，虚线框颜色 = 编号圆点颜色
- [ ] 设备框 UI 是真实 UI，非线框图
- [ ] App 用 `.dk` 深色 / Web 用 `.webframe` 浅色 / 后台用 `.mg` Arco
- [ ] 箭头无物理交叉，动作文字 2-4 字
- [ ] 异常路径在标注卡里覆盖
- [ ] 底部有场景总览表
- [ ] 底部有阅读指引 + 优先级 callout
- [ ] side-nav 锚点与 PART/Scene id 对应

---
---

# 3. 可交互原型（Interactive Prototype）

> **模板文件：** `interactive-prototype-template.html`
> **产物类型：** 可点击的高保真原型，纯内联 HTML/CSS/JS
> **触发条件：** 需求路由命中"可交互原型"
> **核心用途：** 给老板和运营演示（主），讲 PRD 时辅助（次）

## 3.1 结构

```
.gnav (顶部全局导航)
├── View 0: Web 用户端 (.web-view, 深色全宽)
│   ├── .p-nav          — 产品顶部导航（含 dropdown）
│   ├── .p-page × N     — 多页面切换（goWebPage）
│   │   ├── .p-header   — 页面 Header + 统计
│   │   ├── .p-tabs     — Tab 切换内容
│   │   ├── .p-topic    — 专题分组 Header
│   │   └── .p-grid     — 卡片网格
│   └── .p-drawer       — 右侧抽屉面板
├── View 1: App 端 (.app-view, 居中 phone 壳)
│   └── .app-phone (375×812)
│       ├── .app-status  — 状态栏
│       ├── .app-body    — 页面容器（.app-page 切换）
│       ├── .app-sheet   — 底部弹起 Sheet
│       └── .app-tabbar  — 底部 Tab Bar
├── View 2: 后台 (.mgt-view, 浅色 Arco 风格)
│   ├── .modal-bg        — 弹窗（放在 layout 外）
│   └── .mgt-layout
│       ├── .mgt-sidebar — 固定侧边栏
│       └── .mgt-main
│           ├── .mgt-topbar — 面包屑
│           └── .mgt-page × N — 页面切换（swMgtPage）
└── <script>             — 全部交互逻辑
```

## 3.2 三种端壳

| 端 | 容器 class | 宽度 | 背景 | 导航 |
|----|-----------|------|------|------|
| Web 用户端 | `.web-view` | 全宽（内容 960px 居中由你控制） | `--dk-bg` 深色 | `.p-nav` 顶部 Nav + Dropdown |
| App 端 | `.app-view` → `.app-phone` | 375px phone 壳 | `--dk-bg` 深色 | `.app-tabbar` 底部 Tab |
| 后台 | `.mgt-view` → `.mgt-layout` | 全宽（sidebar 200px + main 弹性） | `--lt-bg` 浅色 | `.mgt-sidebar` 侧边栏 |

## 3.3 CSS 变量体系

统一一个 `:root`，前缀区分：

| 前缀 | 用于 | 示例 |
|------|------|------|
| （无前缀） | 功能色，全局共享 | `--blue` `--green` `--red` `--orange` `--gold` |
| `--dk-` | 深色端（App / Web 前端） | `--dk-bg` `--dk-surface` `--dk-border` `--dk-text` |
| `--lt-` | 浅色端（CMS 后台） | `--lt-bg` `--lt-surface` `--lt-border` `--lt-text` |

## 3.4 组件库

### Web 端组件（.p- 前缀）

| 组件 | 用途 |
|------|------|
| `.p-nav` + `.p-nav-item` | 顶部导航（含 active 态 + red-dot） |
| `.p-dropdown` + `.p-drop-item` | Nav 下拉菜单 |
| `.p-bc` | 面包屑 |
| `.p-header` + `.p-hdr-stats` | 页面 Header + 统计数字 |
| `.p-tabs` + `.p-tab` | 内容 Tab 切换 |
| `.p-topic` + `.p-topic-hd` | 专题分组 Header（图标+标题+数量+查看全部） |
| `.p-grid` + `.p-card` | 卡片网格（3列，含 hover 动效） |
| `.p-card .p-cb-on/soon/end` | 卡片状态标记 |
| `.p-drawer` + `.p-overlay` | 右侧抽屉面板（遮罩+滑入） |
| `.p-page` | 页面容器（show/hide 切换） |

### App 端组件（.app- 前缀）

| 组件 | 用途 |
|------|------|
| `.app-phone` | Phone 壳（375px, 圆角 44px） |
| `.app-status` | 状态栏（时间+信号） |
| `.app-body` + `.app-page` | 页面容器 |
| `.app-tabbar` + `.app-tabbar-item` | 底部 Tab Bar（5个图标Tab） |
| `.app-sheet` + `.app-sheet-overlay` | 底部弹起 Sheet（遮罩+滑入） |
| `.app-home-ind` | Home Indicator |

### 后台组件（.mgt- 前缀）

| 组件 | 用途 |
|------|------|
| `.mgt-sidebar` + `.mgt-sb-item` | 侧边栏（深色，active=蓝色高亮） |
| `.mgt-topbar` + `.mgt-bc` | 面包屑导航栏 |
| `.mgt-cd` | 卡片容器 |
| `.mgt-fb` + `.mgt-fs` / `.mgt-fi` | 筛选栏 + Select/Input |
| `.mgt-tw` + `table` | 数据表格 |
| `.mgt-vt` + `.mgt-vtb` | 子视图 Tab（列表/编辑切换） |
| `.mgt-f-sec` + `.mgt-f-row` | 表单区段 + 表单行 |
| `.mgt-lt` + `.mgt-ltb` | 语种 Tab |
| `.mgt-switch` | 开关 Toggle |
| `.mgt-info` | 说明信息框 |

### 通用组件

| 组件 | 用途 |
|------|------|
| `.modal-bg` + `.modal-box` | 全屏遮罩 + 居中弹窗 |
| `.modal-hd` / `.modal-bd` / `.modal-ft` | 弹窗三段式 |
| `.b` `.b-blue` `.b-green` `.b-red` `.b-ghost` `.b-sm` | 按钮系列 |
| `.badge` `.badge-n` `.badge-d` `.badge-m` | 状态标记 |
| `.s-on` `.s-off` | 在线/离线状态文字 |
| `.ops` + `.op-on/.op-off/.op-e/.op-d` | 操作按钮组 |

## 3.5 核心 JS 模式

### 全局导航
```js
switchGlobalView(idx)  // gnav 切 View
```

### Web 端
```js
goWebPage('name')       // p-page 切换
switchWebTab(el, tab)   // p-tab 切换内容
toggleDropdown(e)       // Nav dropdown
openDrawer() / closeDrawer()  // 右侧抽屉
```

### App 端
```js
goAppPage('name')       // app-page 切换
switchAppTab(idx)       // 底部 Tab Bar
openAppSheet() / closeAppSheet()  // 底部 Sheet
```

### 后台
```js
swMgtPage(el, idx)      // sidebar 切页面
```

### 数据驱动 CRUD（仅用于有增删改的模块）

```
核心模式：
JS 数组 itemData[] → renderItems() 渲染列表 → 弹窗按索引读/写
─ currentIdx = -1 → 新增（弹出空表单+默认值）
─ currentIdx >= 0 → 编辑（弹出对应数据）
─ saveModal() = 写数据 + renderItems() + closeModal()（三步缺一不可）
─ deleteItem(idx) = confirm 二次确认 + splice + renderItems()
```

**何时用数据驱动 vs 静态 HTML：**

| 场景 | 用什么 |
|------|--------|
| 有增删改（专题管理、轮播管理等） | 数据驱动：JS 数组 + render + 弹窗 |
| 纯展示 + 筛选（活动列表、审核列表） | 静态 HTML：写死表格 + 筛选 select |
| 弹窗详情（只读查看） | 静态 HTML：写死弹窗内容 |

**数据驱动踩坑清单（写进 system prompt 的规则）：**
- 列表和弹窗必须读同一个数组 → 杜绝"列表摘要 ≠ 弹窗数据"
- 保存 = 写数据 + render + 关弹窗，三步原子操作
- 新增和编辑共用同一弹窗组件，通过 currentIdx 区分
- 删除必须 confirm() 二次确认
- 遮罩层点击也要能关弹窗

## 3.6 context.md → 可交互原型映射

| context.md Section | 驱动 |
|---|---|
| 产品现状 → 端描述 + 页面结构 | View 划分 + 每端内的页面数量和导航 |
| 产品现状 → 页面细节 | 组件选择 + UI 布局 |
| 场景编号 | 页面和弹窗的编排 |
| 术语表 | 所有文案和字段名 |
| 关键业务规则 | 筛选条件选项、数据驱动的数组初始值、表单校验规则 |
| 竞品参考 | UI 还原 |

## 3.7 设备规范（对齐 system prompt）

- App 壳：375×812，圆角 44px，深色底，Flex 布局
- Web 框：960px 全宽深色（无浏览器壳，直接当网站用）
- 后台：深色侧边栏 200px + 浅灰内容区，Arco 风格
- 弹窗：`.modal-bg` 全屏遮罩 + 居中卡片
- 字体：HarmonyOS Sans SC + Plus Jakarta Sans + system-ui
- 深色板：`--dk-bg:#0B0E11` `--blue:#2D81FF` `--green:#0ECB81` `--red:#F6465D` `--gold:#FFD740`
- 浅色板：`--lt-bg:#F5F6FA` `--blue:#2D81FF` `--green:#00B42A` `--red:#F53F3F` `--orange:#FF7D00`

## 3.8 自检

- [ ] gnav Tab 数量与项目端数一致
- [ ] 每个 View 的导航系统正确（Web=p-nav / App=app-tabbar / 后台=mgt-sidebar）
- [ ] 数据驱动模块：编辑弹窗读的数据 = 列表显示的数据（同一个数组）
- [ ] 保存 = 写数据 + render + 关弹窗（三步）
- [ ] 新增弹出空表单 + 默认值，编辑弹出对应数据
- [ ] 删除有 confirm 二次确认
- [ ] 遮罩层（.modal-bg / .p-overlay / .app-sheet-overlay）点击可关闭
- [ ] ✕ 关闭按钮功能正常
- [ ] Tab / 侧边栏切换后内容正确显示/隐藏
- [ ] 面包屑随页面切换联动
- [ ] 统计数字随增删实时更新
- [ ] 术语与 context.md 一致
- [ ] 无底部空白 bug（App 壳 Flex 布局）
- [ ] 接近最终视觉，非线框图

---
---

# 4. PRD（产品需求文档）

> **模板文件：** `gen-prd-template.js`（生成脚本） → 输出 `prd-template.docx`
> **产物类型：** Landscape 横版 docx，左图右文，九章结构
> **触发条件：** 需求路由命中"PRD"且指定 .docx 格式
> **生成方式：** `node gen-prd-template.js output.docx`

## 4.1 结构

```
Cover (Portrait)
├── 项目标题 + 副标题 + 范围
├── 属性表（产品名/版本/日期/产品线/平台/状态）
└── 目录（TOC，自动生成）

Ch1 项目背景与目标 (Portrait)
├── 1.1 背景
├── 1.2 核心目标
├── 1.3 变更范围
└── 1.4 用户角色（表格）

Ch2 场景地图 (Portrait)
├── 2.1 View 1 场景表
├── 2.2 View 2 场景表
└── 2.3 View 3 场景表

Ch3 端A详细需求 (Landscape, 左图右文)
├── 3.1 Scene X · 名称 → lrTable(截图占位, 需求段落)
├── 3.2 Scene Y · 名称 → lrTable(...)
└── ...

Ch4 端B详细需求 (Landscape, 左图右文)
└── 同上结构

Ch5 后台详细需求 (Landscape, 左图右文)
└── 同上结构

Ch6 业务规则 (Portrait)
├── 6.1~N 规则表格
├── 组件复用 & 数据关系（矩阵表）
└── 页面层级

Ch7 非功能性需求 (Portrait, 表格)
Ch8 埋点与监控 (Portrait, 表格 + 告警规则)
Ch9 里程碑与排期 (Portrait, 表格 + 后续规划)
```

## 4.2 页面方向

| 章节 | 方向 | 原因 |
|------|------|------|
| 封面 + 目录 | Portrait | 标准封面 |
| Ch1-2 | Portrait | 纯文字+表格，竖版够用 |
| **Ch3-5** | **Landscape** | **左35%截图 + 右65%需求文字，横版宽度足够** |
| Ch6-9 | Portrait | 规则/表格/排期，竖版够用 |

## 4.3 字体规范

| 用途 | 字体 | 字号 |
|------|------|------|
| 英文 | Arial | — |
| 中文 | SimSun（宋体） | — |
| H1（章） | Arial + SimSun Bold | 16pt |
| H2（场景） | Arial + SimSun Bold | 14pt |
| H3（子模块） | Arial + SimSun Bold | 12pt |
| 正文 | Arial + SimSun | 11pt |
| 表格内容 | Arial + SimSun | 10pt |
| 表头 | Arial + SimSun Bold White | 10pt |
| 页眉/页脚 | Arial + SimSun | 8pt |

字体通过 docx-js 的 `font: { ascii: "Arial", eastAsia: "SimSun", hAnsi: "Arial" }` 设置，中英文自动匹配。

## 4.4 核心组件

### 标准表格 `stdTable(headers, rows, colWidths)`
- 蓝色表头（#2D81FF 背景 + 白字）
- 隔行浅灰底（#F8FAFC）
- 列宽用 DXA 单位精确控制

### 左图右文表格 `lrTable(screenshotLabel, requirementParagraphs)`
- **仅在 Ch3-5 横版 section 中使用**
- 左列 35%：浅灰底 + 截图占位文字（居中斜体灰色）
- 右列 65%：需求段落，用 `reqTitle()` + `reqBody()` 组合
- 截图占位后续可手动替换为真实截图

### 需求段落 helpers
- `reqTitle(text)` — 需求小节标题（加粗，11pt）
- `reqBody(text)` — 需求正文（10pt，行距 1.25）

### 页眉页脚
- 页眉：右对齐，"机密 · 项目名"，蓝色底线
- 页脚：居中，"第 X 页"，灰色顶线

## 4.5 颜色体系

| 用途 | 色值 |
|------|------|
| 表头背景 | #2D81FF（蓝） |
| 表头文字 | #FFFFFF（白） |
| 正文 | #1E293B（深灰） |
| 辅助文字 | #64748B（中灰） |
| 隔行背景 | #F8FAFC（极浅灰） |
| 截图占位背景 | #F8FAFC |
| 属性表标签列 | #EEF2FF（浅蓝） |
| 边框 | #CBD5E1 |
| 页眉底线 | #2D81FF |

## 4.6 context.md → PRD 映射

| context.md Section | PRD 章节 |
|---|---|
| 产品现状 | Ch1.1 背景 |
| 场景编号 | Ch2 场景地图（直接搬） |
| 术语表 | 全文统一用词 |
| 本轮方案决策 | Ch1.3 变更范围（PM 从讨论流水收敛成线上→终稿 delta，不直搬）+ Ch3-5 标注"（变更）" |
| 关键业务规则 | Ch6 业务规则 |
| 竞品参考 | Ch1.1 背景中引用 |
| 待办 & 下一步 | Ch9 里程碑 |

**与交互大图/原型的对齐：**
- Ch2 场景编号 = context.md 场景编号 = 交互大图 Scene 编号 = 原型页面编号（三文件一致）
- Ch3-5 左侧截图从可交互原型中截取
- Ch6 术语/字段与交互大图标注卡、原型 UI 文案一致

## 4.7 生成方式

PRD 与其他三个产物不同——不是 HTML 模板直接填充，而是一个 **JS 生成脚本**。原因是 docx 是 XML 压缩包，不能像 HTML 一样文本替换。

**工作流：**
1. Claude 读取 context.md
2. Claude 基于 `gen-prd-template.js` 的结构，替换 `{{PLACEHOLDER}}` 为实际内容
3. Claude 执行 `node gen-prd-template.js output.docx` 生成文件
4. Claude 验证 `python scripts/office/validate.py output.docx`
5. 用户在 Mac WPS 中打开，手动粘贴原型截图到左侧占位区

## 4.8 自检

- [ ] 封面属性表完整（6 项）
- [ ] 目录能正确生成（需在 WPS 中右键"更新域"）
- [ ] Ch1-2 竖版 / Ch3-5 横版 / Ch6-9 竖版
- [ ] 左图右文表格左列有截图占位文字
- [ ] 场景编号与 context.md 一致
- [ ] 术语+字段与交互大图/原型对齐
- [ ] 蓝色表头白字，非黑底
- [ ] 页眉显示"机密"
- [ ] 页脚显示页码
- [ ] 字体：中文宋体 + 英文 Arial，Mac WPS 中无乱码
- [ ] 变更项标注"（变更）"或"（新增）"
- [ ] 异常场景不省略
- [ ] 编号全局一致，跳转双向标注

---
---

# 5. 需求框架（Requirement Framework）

> **模板文件：** `requirement-framework-template.html`
> **产物类型：** 静态 HTML 文档，一张全景表 + 统计卡 + Callout
> **触发条件：** 场景清单对齐后、交互大图之前，需要快速对齐"做哪些模块、谁负责、什么优先级"
> **定位：** 比场景清单重（多了模块分组+平台标签+描述），比 PRD 轻（无截图无详细规则）

## 5.1 结构

```
.hd              — sticky header（项目名 + scope 摘要）
.wrap            — max-width:1200px 内容区
├── .st + .summary    — 项目概览（3张统计卡）
├── .st + table       — 需求框架明细（分组表格，核心内容）
└── .co × 3           — 平台说明 + 优先级说明 + 与上版变化
```

## 5.2 组件

### Summary Cards（.scard）

3 张卡片横排，典型内容：

| 卡片 | .label | .val | .desc |
|------|--------|------|-------|
| 涉及平台 | "涉及平台" | 数字 | 平台名称列举 |
| 需求模块 | "需求模块" | 数字 | 各模块需求数分布 |
| 优先级分布 | "优先级分布" | P0×N · P1×N · P2×N | P0 核心链路一句话 |

### Main Table（5 列固定）

| 列 | 宽度 | 内容 |
|----|------|------|
| # | 36px | 编号（如 E1, B2, F4） |
| 所属模块 | 140px | 模块名 + 可选 `.tag-new` |
| 所属平台 | 120px | `.plat` 标签 + 平台描述 |
| 大致描述 | flex | 需求描述，1-3 句话 |
| 期望优先级 | 80px | `.pri` 标签 |

### Module Group Row（.mod-group，分组行）

| class | 颜色 | 建议用于 |
|-------|------|---------|
| （无额外） | 蓝 | 常规模块 |
| `.green` | 绿 | 核心/新增模块 |
| `.red` | 红 | 高风险/关键链路 |
| `.amber` | 橙 | 前置/基础设施 |
| `.purple` | 紫 | 辅助/后台 |

分组行用 `<td colspan="5">`，内容格式：`{{GROUP_ID}} · {{GROUP_NAME}}`，可选追加 `.tag-new`。

### 标签组件

| 组件 | 变体 | 用途 |
|------|------|------|
| `.pri` | `.p0`绿 `.p1`蓝 `.p2`橙 `.later`灰 | 优先级 |
| `.plat` | `.app`紫 `.web`绿 `.srv`红 `.cms`橙 | 平台 |
| `.tag-new` | — | 新增标记（绿） |
| `.tag-chg` | — | 变更标记（蓝） |
| `.tag-del` | — | 删除标记（红） |

### Callout（.co，3 个固定）

| 顺序 | class | 内容 |
|------|-------|------|
| 1 | `.co.bl` 蓝 | 平台说明（每个 `.plat` 标签含义解释） |
| 2 | `.co.gn` 绿 | 优先级说明（P0/P1/P2/后续的划分逻辑） |
| 3 | `.co.am` 橙 | 与上版主要变化（编号列举） |

## 5.3 context.md → 需求框架映射

| context.md Section | 驱动 |
|---|---|
| 产品现状 → 端描述 | Summary Card 平台数 + 平台说明 Callout |
| 场景编号 | 表格行编号（需求框架编号可以是场景编号的超集或子集） |
| 术语表 | 模块名、平台名统一 |
| 本轮方案决策 | `.tag-new` / `.tag-chg` 标记 + 变化 Callout |
| 关键业务规则 | 大致描述列的细节 |

## 5.4 编号规则

- 分组用字母标识（E / A / B / C / D / F / G...）
- 组内用数字递增（E1, E2, E3...）
- 编号在后续交互大图、原型、PRD 中保持一致
- 如果需求框架先于场景清单产出，编号在此确定后锁定

## 5.5 自检

- [ ] Summary Cards 数字准确（平台数、模块总数、P0/P1/P2 计数）
- [ ] 每个分组至少 1 个需求行
- [ ] 编号全局唯一，无重复无跳号
- [ ] `.plat` 标签与平台说明 Callout 对应
- [ ] `.pri` 分布与 Summary Card 中的统计一致
- [ ] 大致描述是 1-3 句话级别，不展开到字段级
- [ ] 三个 Callout 都填写完整
- [ ] `.tag-new` 只标在真正新增的模块/需求上

## 6 侧边栏演示文稿（sidebar-deck-template.html）

### 定位

信息密度高、需要反复翻阅的演示场景：SOP 手册、培训材料、方案宣讲、产品介绍。不是翻页 PPT，是 sidebar 导航的多页应用，适合浏览器全屏讲。

### 整体架构

```
sidebar(240px 固定) + main(flex:1 滚动)
├── .sidebar-head — Logo + 副标题
├── .sidebar-nav — NAV[] 数据驱动，按 group 分组
├── .main-header — 面包屑 + 右侧标签
└── .main-content — PAGE_RENDERERS[pageId] 动态渲染
```

### JS 架构（3 个核心数据结构）

| 数据 | 作用 | 说明 |
|------|------|------|
| `NAV[]` | 侧边栏导航 | `{group, dot, items:[{id, icon, label}]}` 数组驱动 |
| `PAGE_RENDERERS{}` | 页面渲染 | 每个 pageId 对应一个 `function(container)` |
| `COPYABLE_DATA{}` | 可复制内容 | Prompt / 模板 / 代码片段，按 key 存取 |

### 两种通用页面渲染器

| 渲染器 | 适用场景 | 结构 |
|--------|---------|------|
| `renderPromptPage(c, opts)` | 有可复制 Prompt 的操作页 | tag + title + IN/OUT 双栏 + note + prompt-block + expectation |
| `renderTemplatePage(c, opts)` | 需上传文件 + 查组件表的页面 | tag + title + 上传指引 ×3 + 结构树 + 组件速查表 + 自检清单 |

### 定制页面（4 种）

| 页面 | pageId | 结构 |
|------|--------|------|
| 总览/封面 | `home` | 居中大标题 + hero-num ×3 + 核心概念 + 决策树 grid3 + 路径选择 track-card ×2 + 对比表 |
| 详解页 | `overview` | page-title + grid2 色条卡 ×4 + pipe 垂直流程图 |
| 展示页 | `gallery` | gallery-card ×N + 性能表 |
| FAQ | `faq` | accordion 折叠问答 + grid2 上手路线图 |

### 组件库（15 种）

| 组件 | class | 变体 |
|------|-------|------|
| 卡片 | `.card` | border-top/left 加色条 |
| 网格 | `.grid2` `.grid3` `.grid4` | 响应式，≤900px 单列 |
| 标签 | `.tag` | `-blue` `-green` `-orange` `-purple` `-red` |
| 分数徽章 | `.score` | `-mid`(橙) `-high`(绿) `-low`(红) |
| 分区标题 | `.section-label` | mono 字体 + 大写 |
| 提示框 | `.note` | 默认蓝 / `.green` / `.orange` / `.red` / `.purple` |
| 代码块 | `.prompt-block` | `.prompt-header`(标题+复制按钮) + `.prompt-body` |
| 大数字 | `.hero-num` | `.val` + `.lbl`，mono 字体 |
| 路径选择卡 | `.track-card` | `.track-a`(绿) / `.track-b`(蓝)，带模糊光晕 |
| 对比表 | `.cmp-table` | hover 高亮行 |
| 编号列表 | `.ck-item` + `.ck-num` | ck-num 背景色 inline style 控制 |
| 折叠面板 | `.accordion` | `.acc-header`(点击) + `.acc-body`(展开) |
| 展示卡 | `.gallery-card` | `.gallery-preview`(图标区) + `.gallery-info` |
| 技能卡 | `.skill-card` | 右上角 `.model-tag`(`.variant-a` 紫 / `.variant-b` 绿) |
| 垂直流程图 | `.pipe` | `.pipe-node` + `.pipe-arrow` 交替，icon 背景色区分步骤 |
| 嵌套架构图 | `.nest-outer` > `.nest-mid` > `.nest-inner` | 三层嵌套，紫>蓝>绿，`.nest-label` + `.nest-chip` |
| 弹窗 | `.modal-overlay` + `.modal-box` | 全屏遮罩 + 居中卡片，`openModal(title, content)` 调用 |

### 导航分组 dot 色规则

| dot | 含义 |
|-----|------|
| null | 无圆点（通用分组） |
| `green` | 入门/低门槛路径 |
| `blue` | 进阶/工程化路径 |
| `pink` | 展示/附录 |
| `purple` / `orange` | 自定义扩展 |

### 颜色语义（和其他模板统一）

功能色全局共享：`--blue` 主链路 / `--green` 正面/新增 / `--orange` 警告/中等 / `--red` 负面/风险 / `--purple` 进阶/特殊 / `--pink` 展示/装饰

### 自检清单

1. NAV 中每个 item.id 都有对应的 PAGE_RENDERERS 注册
2. goPage() 切换后面包屑文字正确
3. COPYABLE_DATA 中每个 key 都有对应的 prompt-block 引用
4. 折叠面板点击展开/收起正常
5. 弹窗打开/关闭/复制功能正常
6. sidebar 滚动不溢出，nav-item active 状态高亮正确
7. 响应式：≤900px grid 降为单列