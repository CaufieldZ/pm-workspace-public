<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: interaction-map
description: >
  当用户提到「交互大图」「交互流程图」「IMAP」时触发。
  场景清单确认后进入视觉化阶段自动接续触发。
type: pipeline
output_format: .html
output_prefix: imap-
pipeline_position: 3
depends_on: [scene-list]
optional_inputs: [context.md, requirement-framework, architecture-diagrams]
consumed_by: [prototype, prd]
scripts:
  gen_imap_skeleton.py: "Step A 骨架 — from gen_imap_skeleton import generate_skeleton"
  fill-template.py: "Step B fill 模板 — 复制到项目 scripts/fill_imap_v{N}.py 改写"
  interaction-map.js: "运行时 JS — 骨架脚本自动内联，不手动读"
  scripts/fill_utils.py: "fill 公共函数 — from fill_utils import run_fill"
  scripts/check_html.sh: "Step C 自检 — bash scripts/check_html.sh <html> <scene-list> imap"
---
<!-- pm-ws-canary-236a5364 -->

# 交互大图 Skill（Interaction Map）

> 通用分步生成规则（强制规则 / 快速模式 / Fill 脚本规范 / 通用自检）见 `pm-workflow.md`「HTML 分步生成通用规则」。以下为本 Skill 补充规则：
> - Step B 每填充 1-3 个 Scene 后停下报告进度（非快速模式）
> - Step C 自检时逐个对照 scene-list.md 编号，列出「已覆盖 / 缺失」清单

## IMAP 三大规则（2026-04 起新规范）

> 本章节是新规范，覆盖以下所有「标注」「Tag 系统」相关条目。老 references/ 里的 `.anno` overlay 和 `ann-tag.new/chg/del` 示例按本章节为准，不要复制。

### 1. 场景粒度 = 主场景，不是子场景

IMAP scene 对齐 scene-list 的**主场景**（A/B/C/M/F/G 等一级编号），严禁把子场景（A-1/A-2/B-3）升为独立 scene。

子场景降为**主场景内部的手机节点**：同主场景下的子场景横排摆成一条故事流水线，`.phone-label` 写子场景编号（如「A-1 · 首页 Feed」），子场景间用 `.aw` 箭头连接。

跨 skill 编号契约不变：PRD / prototype / bspec / pspec 章节仍用子场景编号（A-1 章节对应 IMAP scene A 里面 phone-label="A-1" 的手机节点）。

### 2. `.anno` overlay 限用场景（不是禁用）

`.anno` / `.anno-n` 虚线框 + 编号徽章是合法的视觉工具，用途是为 `.ann-card` 里的编号（1/2/3...）提供屏幕上的定位锚点——读者知道「注释条目 1」对应手机哪个区块。

**允许场景**：复杂手机（多区块、多 UI 元素）需要 ann-card 精确定位时，在屏幕区块外套 `.anno.{色}` + `.anno-n.{色}`，和 ann-card 里的 `.ann-num` 一一对应。

**禁止场景**：
- 用 anno overlay 做差量标注（圈"改动"/"新增"区域）——这是差量叙事，归第 3 条
- 滥用（每个 UI section 都套一个，却没有 ann-card 对应）——让手机看起来全是虚线框

**判断**：如果每个 anno-n 编号在右侧 ann-card 里有对应的 ann-num 条目，就是合法定位工具；如果 anno overlay 单独存在或配合差量文案/标签，就是违规。

注解主体仍然用 `.flow-note`（每屏下方一行）+ 可选 `.ann-card`（横排末尾侧栏）。anno overlay 只是 ann-card 的辅助。

### 3. IMAP 不承载变更

IMAP 是静态数据，只画新态全景。禁止出现差量叙事：

- 禁用 `ann-tag.new` / `ann-tag.chg` / `ann-tag.del`（仅保留 `.p0` / `.p1` / `.p2` 优先级标签）
- 禁止出现 `V\d+\.\d+`（V2.6、V3.1 等版本号）、`NEW`、`变更`、`新增`、`改动` 等差量文案

变更叙事归 PRD 1.3「变更范围」章节。迭代项目也画新态全景，老 IMAP 归档，不增量叠。

---

## 核心输出规范

1. **单文件 HTML**：所有 CSS/JS 内联，无外部依赖（字体 CDN 除外）。`interaction-map.css` 和 `interaction-map.js` 由骨架脚本 `gen_imap_skeleton.py` 通过 `open().read()` 自动内联，不在本文件中显式引用
2. **Web + Mobile 双端 Mockup**：App 用 `.phone`（深色），Web/CMS 用 `.webframe`（浅色）
3. **横向 Flow 布局**：`.flow` 容器 → 多个 `.flow-col` 屏幕（= 主场景下的子场景）→ 屏幕间 `.aw` 箭头 → 末尾可选 `.ann-card` 说明
4. **主注解 = `.flow-note`**：每屏幕下方一行写状态 / 触发。复杂 scene 可加 `.ann-card` 侧栏 + `.anno` 屏幕锚点（详见三大规则 #2）
5. **分组结构**：`.gd` 分隔符区分产品模块（PART 0/1/2/3/4...）
6. **响应式**：侧导航 1400px+ 显示，内容区水平滚动

## Fill 内容契约

骨架和 fill 脚本的 HTML 层级边界定义如下，**禁止同时在两者中生成设备壳**。

### 骨架提供

- `.fade-section` 容器 + `.st` 标题行（Scene 编号 + 名称 + 触发条件）
- 空 `.flow` 容器 + 单个 `FILL_START:scene-{id}` 标记
- 不生成设备壳（.phone / .webframe）、不生成占位内容、不生成箭头

### fill 提供（替换单个 FILL 标记）

| 元素 | 说明 |
|------|------|
| `.flow-col` + `.phone` | device=phone 的 Scene，375px 深色壳 |
| `.flow-col` + `.webframe` | device=web 的 Scene，720px+ 浅色壳 |
| `.aw` 箭头 | 屏幕间连接（fill 控制有无箭头和箭头文案） |
| `.ann-card` 注释卡 | 必须包在 `flex-direction:column` 纵向容器内 |
| `.flow-note` | 屏幕底部说明文字 |
| `.phone-label` | 屏幕顶部标签（fill 控制文案，不硬编码子状态编号） |

### device → 设备壳映射

设备类型由每个 Scene 的 `device` 字段决定（不是 PART 的 theme），同一 PART 下可混合：

| device 值 | 设备壳 | 典型场景 |
|-----------|--------|---------|
| `phone`（默认） | `.phone`（375px 深色） | App 端页面 |
| `web` | `.webframe`（720px+ 浅色） | Web 前台、后台 CMS、管理台 |

> **theme vs device**：theme 控制 PART 分隔条样式（深灰/蓝色/绿色），device 控制 Scene 内的设备壳类型。两者独立。

### Fill 必需组件清单（按新规范）

每个**主场景** fill 函数必须包含以下组件（一个主场景 = 横排多个子场景手机 + 箭头）：

| # | 组件 | class | 必需性 | 检查方式 |
|---|------|-------|--------|---------|
| 1 | 屏幕（子场景手机） | `.phone` 或 `.webframe` | **必需，多个**（= 该主场景下的子场景数） | 目视 + `grep -c` |
| 2 | 屏幕标签 | `.phone-label` | **必需**，每屏一个，写子场景编号（如「A-1 · 首页」） | `grep -c 'phone-label'` |
| 3 | 箭头 | `.aw` > `.al` + `.tx` | **必需**，子场景间连接 | `grep -c 'class="aw"'` |
| 4 | 屏幕说明 | `.flow-note` | **必需**，主注解载体 | `grep -c 'flow-note'` |
| 5 | 注释卡 | `.ann-card`（含 `.card-title` + `.ann-item` > `.ann-num` + `.ann-text`）| **可选**，复杂 scene 在末尾挂一张 | `grep -c 'ann-card'` |
| 6 | 优先级标签 | `.ann-tag.{p0/p1/p2}` | 可选，仅在 ann-card 内强调优先级时用 | `grep -c 'ann-tag'` |
| 7 | 信息框 | `.info-box.{色}` | 可选，按需补充说明 | `grep -c 'info-box'` |

**限用 / 退役组件**：
- `.anno` / `.anno-n`（手机内部 overlay）：**限用**——允许作为 ann-card 编号的屏幕锚点，禁止配合差量标签/文案滥用（详见三大规则 #2）
- ~~`.ann-tag.new` / `.ann-tag.chg` / `.ann-tag.del`~~（差量标签）：**退役**

> ann-card 不是只写外壳 + ann-num，必须包含完整子结构（card-title + ann-item > ann-num + ann-text）。`.ann-tag` 若使用仅限 p0/p1/p2。手机内部视觉还原密度按场景复杂度自行拿捏，不设行数硬上限——参考 `projects/htx-community/deliverables/imap-htx-community-v6.html` 的密集 inline-style 风格。

## Fill 执行规则（所有模型强制）

以下规则在执行 Step B 填充时**强制生效**：

### fill 脚本拆分规则

1. **每个 fill 函数 ≤ 80 行 HTML**（含 return 的三引号字符串）。超过则拆分为多个屏幕函数
2. **每个 .py 文件 ≤ 150 行**。超过则按 PART 拆分为 `scenes_part0.py` / `scenes_part1.py`
3. **先用 Write 工具写文件，再用 `python3 scripts/fill_xxx.py` 执行**。禁止用 `python3 - << 'PYEOF'` heredoc 传入含 HTML 的 Python 代码（引号冲突风险极高）
4. **每次只写 1 个 Scene 的 fill 函数**，执行验证通过后再写下一个

### HTML 字符串安全规则

fill 函数中的 HTML 字符串统一用 Python 三引号 `'''...'''` 包裹：

- HTML 属性统一用双引号 `""`（如 `style="color:red"`）
- 禁止在 HTML 中使用 Python 三引号或反斜杠转义
- 中文注释写在函数 docstring 里，不写在 return 字符串内

### 失败恢复

- Write 工具报错（参数为空/内容截断）→ 将函数拆得更小，不要重试相同内容
- SyntaxError → 用 `python3 -c "import ast; ast.parse(open('xxx.py').read())"` 定位行号，不要盲改
- fill 后 HTML 结构破坏 → `git checkout -- deliverables/xxx.html` 恢复骨架，重新执行 fill

### 组件完整性规则

5. **每个主场景 fill 函数必须包含必需组件**：多屏幕 + phone-label + 箭头 + flow-note。ann-card 可选
6. **填充完成后 grep 验证必需项**：`grep -c 'class="phone\|class="webframe\|class="aw"\|phone-label\|flow-note' deliverables/xxx.html` — 必需项任一为 0 则返工
7. **反模式 grep 断言**（必须全部为 0）：`grep -cE 'ann-tag (new|chg|del)|V[0-9]+\.[0-9]+|>NEW<|>改动<|>变更<'` — 新 IMAP 禁用差量标签和差量文案。注意 `.anno` overlay 本身允许，只有配合差量标签/文案才算违规
8. **ann-card 使用规则**（若使用）：内部必须有 `.card-title` + 至少 1 个 `.ann-item`（含 `.ann-num` + `.ann-text`）。`.ann-tag` 仅限 `p0/p1/p2`

## ★ 分步生成策略（性能优化）

> **重要**：交互大图 HTML 通常 2000-3000 行，一次性生成会非常慢。
> 必须采用分步渐进生成，分 3 个阶段完成。

### 总体流程

```
用户确认场景清单
      ↓
Step A：生成骨架文件（CSS + JS + PART 分组 + Scene 占位）
      ↓ 用户确认骨架结构
Step B：逐 Scene 填充内容（每次 1-3 个 Scene）
      ↓ 每批填完用户确认
Step C：收尾（跨端表 + Callout + 自检）
      ↓
交付
```

### Step A：生成骨架文件（约 300-500 行）

**优先使用骨架脚本**：
1. 参考下方 API 速查表了解 `project / legends / parts` 数据结构
2. 根据 context.md + scene-list.md 填充数据。每个 Scene 的 `device` 字段按以下优先级确定：
   - **有设备列** → 直接读取 scene-list.md 的「设备」列（📱phone / 🖥web）
   - **无设备列**（老项目兼容）→ **停下来**，列出所有 Scene 让用户逐个确认 phone 还是 web，确认后再写骨架脚本。禁止默认 phone 或自行推断
3. 将脚本复制到 `projects/{项目名}/scripts/gen_imap_v{N}.py`，修改数据，运行
4. 骨架文件自动生成到 deliverables/

骨架文件可在浏览器打开，看到完整 PART 结构和 Scene 标题，Scene 内容为空。

**骨架输出后询问用户**（列出每个 Scene 的设备类型供确认）：
> 骨架结构已生成，包含 N 个 PART、M 个 Scene：
> - PART 0 用户端：A · 首页 📱phone, A-1 · Web 交易 🖥web
> - PART 1 管理台：M-1 · 配置管理 🖥web
> 请确认 Scene 编号和设备类型正确，我开始逐 Scene 填充内容。
> 你想一次填几个 Scene？建议每次 2-3 个。
**⛔ 硬停点：输出骨架后必须在此停止。（快速模式除外）**
不要自动进入 Step B。不要在同一轮对话中继续填充 Scene。
等用户明确回复后再继续。如果用户没有回复，就等着。

### Step B：逐 Scene 填充（每个 Scene 约 150-400 行）

写 `fill_imap_v{N}.py` 脚本到 `projects/{项目名}/scripts/`：
- 每个 Scene 定义一个函数（`def fill_a(): return '''...'''`）
- 替换骨架中单个占位块：`FILL_START:scene-{id}`
- 脚本超 200 行按 PART 拆分数据文件

> fill 脚本参考：references/fill-template.py（仅写 fill 脚本时读取）

**每个主场景 fill 函数包含**：多个 Phone/Web Mockup（= 主场景下的子场景数，每个 phone-label 写子场景编号）+ 子场景间 `.aw` 箭头 + 每屏 `.flow-note` 说明 + 末尾可选 `.ann-card`（复杂 scene 用）+ 可选 `.anno` 屏幕锚点（和 ann-card 编号对应时使用）

**填充节奏**（非快速模式）：简单 Scene 3 个一批，复杂 Scene 1 个一批，每批报告进度。
填充时不能破坏已有 CSS / JS / 其他 Scene。

### Step C：收尾（约 200-300 行）

最后一批填充完成后：

1. **插入跨端数据流表格**（如果有跨 View 交互）
2. **插入底部 Callout**（阅读指引 + 优先级说明）
3. **执行自检**（见下方自检清单）
4. **告知用户交付**

### 增量升版（已有 Vn → Vn+1）

当已有完整交互大图需要升级（而非从零生成）时，走增量 patch 而非重新骨架→填充：

1. **归档旧版**：`cp Vn.html archive/` + `cp Vn.html V{n+1}.html`
2. **版本号替换**：HTML 内 title + h1 的版本号
3. **按 Scene 写 patch 脚本**：每个受影响 Scene 一个 `patch_imap_v{n+1}_{scene}.py`，用 `re.sub` 锚定 `<div class="fade-section" id="{scene}">` 到下一个 `<!-- ═══` 边界，整块替换
4. **逐个执行 + 验证**：每个 patch 跑完验证 div 平衡 + grep 关键术语
5. **自检同完整生成**（Step C 自检清单）
6. **不要用 Edit 工具逐行改大块 HTML**——正则替换更安全，且可回滚（`git checkout -- deliverables/xxx.html`）

**端能力校验**：patch 前检查每个 Screen 画的交互是否能在目标端实际执行（H5 不能跑 TRTC 推流、OBS 主播看不到 Web 工作台等），不要画目标端做不到的按钮/功能。

### 分步生成的占位模板

骨架中每个 Scene 有 1 个占位块（`FILL_START:scene-{id小写}` / `FILL_END:scene-{id小写}`），fill 脚本替换该块为完整的屏幕组 + 箭头 + 注释卡：

```html
<div class="fade-section" id="scene-{编号}">
  <div class="st">
    <h2>{编号} · {场景名称}</h2>
    <span class="note">{触发条件}</span>
  </div>
  <div class="flow">
    <!-- FILL_START:scene-{id小写} -->
    <!-- FILL_END:scene-{id小写} -->
  </div>
</div>
```

fill 脚本用 `re.sub()` 替换 `FILL_START...FILL_END` 整块，替换后标记一并清除。
fill 内容包含：`.flow-col`（设备壳 + 内部 UI）+ `.aw`（箭头）+ 注释卡纵向容器。
参考 `references/fill-template.py` 的 phone 和 webframe 双示例。

## 如何使用

### Step 1：读取 Reference

**Step A 不读模板** — 骨架脚本只需下方 API 速查表，CSS/JS 由 `open().read()` 自动拼接。

**Step B 填充前必读组件速查表**：
```
view .claude/skills/interaction-map/references/templates-quickref.md
```
速查表列出所有组件的 class、必填子元素、模板行号。大多数 Scene 凭速查表即可写 fill 函数。

**黄金片段参考（可直接复制修改）：**
```
view .claude/skills/interaction-map/references/gold-snippets.md
```

**按需读取完整模板（首次使用某组件类型、或速查表不够确认结构时，按行号读局部）：**
```
view .claude/skills/interaction-map/references/interaction-map-templates.html
```

**按需读取（仅扩展骨架生成器本身时才读）：**
```
view .claude/skills/interaction-map/references/gen_imap_skeleton.py
```

**按需读取通用组件（Phone/Web/CMS 组件结构不确定时才读）：**
```
view .claude/skills/interaction-map/references/components-core.md
```

**按需读取业务组件（仅 Scene 包含对应业务组件时才读对应文件，禁止全量读取）：**
- Scene 含交易卡片/K线/持仓/半屏抽屉/跟单 → `view .claude/skills/interaction-map/references/biz-trading.md`
- Scene 含 Feed 极简卡/帖子列表/$币种胶囊/交易 CTA → `view .claude/skills/interaction-map/references/biz-social.md`
- Scene 含直播间/OBS/连麦/策略卡/主播工作台 → `view .claude/skills/interaction-map/references/biz-livestream.md`

**美学规范（产出前 grep 决策速查表段）：**
```
grep -A 20 "决策速查" .claude/skills/_shared/claude-design/anti-ai-slop.md
```

**Claude Design opt-in 主题（手动挂 class）：**
- CSS 中 `.theme-cd` 作用域已定义，覆盖 Binance 默认色板为 Claude Design 深色
- 默认不加（保留 Binance 深色系，前台交易所视觉）；需切换时手动在生成后 HTML 的 body 加 `class="theme-cd"`

### gen_imap_skeleton.py API 速查

骨架生成只需调用一个函数，**不需要读源码**：

```python
# 导入方式（从 projects/{项目}/scripts/ 执行，向上 3 层到工作区根目录）
import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/interaction-map/references'))
from gen_imap_skeleton import generate_skeleton
```

```python
generate_skeleton(project, legends, parts, output_path)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `project` | `dict` | `{"name": "产品名", "subtitle": "交互大图 v1.0", "nav_desc": "用户端 → 管理台 ｜ 分组阅读"}` |
| `legends` | `list[dict]` | `[{"color": "blue", "label": "布局"}, {"color": "green", "label": "新增"}, ...]` |
| `parts` | `list[dict]` | 见下方结构 |
| `output_path` | `str` | 输出文件路径 |

**parts 结构**：
```python
{
    "id": "part0",              # 锚点 id
    "num": "PART 0",            # 显示编号
    "name": "🚀 用户端核心交互",  # 模块名
    "desc": "App 端用户交互流程", # 描述
    "theme": "frontend",        # "frontend" | "admin" | "cross-end" | "custom"
    "dot_color": "amber",       # 侧导航圆点颜色
    "scenes": [
        {"id": "A", "name": "首页", "trigger": "启动 App", "device": "phone"},
        {"id": "A-1", "name": "Web 交易", "trigger": "浏览器访问", "device": "web"},
    ],
    # scene.device: "phone"（默认）| "web" — 决定 fill 生成的设备壳
    # custom 主题需额外字段：bg, color, num_bg
    # 跨端 PART 可选："cross_table": True → 插入数据流表格占位
}
```

### Step 4：填充内容指南

**Phone Mockup 内部结构**（从上到下）：
1. `.ph-status` — 状态栏（时间 + 电池）
2. `.ph-top` — 顶部栏（头像 / 标题 / 操作）
3. `.ph-stage` — 主舞台（视频 / 图表 / 内容区）
4. 功能区域 — 自定义模块（聊天、表单、媒体等）
5. `.ph-bar` — 底部操作栏
6. `.home-ind` — Home 指示器

**Web Frame 内部结构**：
1. `.wf-bar` — 浏览器地址栏（三色圆点 + URL）
2. 顶部导航栏 — 产品名 + 状态
3. 内容区 — 自由布局

**注解策略（新规范）**：

主注解写在 `.flow-note`（每屏幕下方一行）。复杂 scene 可在横排末尾挂一张 `.ann-card` 侧栏说明业务规则，用 `.ann-item` + `.ann-num` 编号列条目。

- 颜色分类（用于 `.aw` 箭头、`.ann-num`、`.anno-n`）：`blue`（导航/布局）、`green`（正向操作）、`red`（警示/重要）、`purple`（Web 端）、`amber`（跨端/流程）
- `.anno` overlay 限用场景：**仅作为 ann-card 编号的屏幕锚点**（每个 anno-n 编号要在 ann-card 的 ann-num 里有对应条目）。禁止用来圈"改动/新增"区域——那是差量叙事

**Tag 系统**：

- `.ann-tag.p0` / `.p1` / `.p2` — 优先级（唯一允许的 ann-tag 类型）
- ~~`.ann-tag.new`~~ / ~~`.ann-tag.chg`~~ / ~~`.ann-tag.del`~~ — 已退役（IMAP 不承载变更，差量叙事归 PRD 1.3）

## 设计系统速查

### 颜色变量

| 变量 | 值 | 用途 |
|------|------|------|
| `--blue` | #2979FF | 布局改动、主操作 |
| `--green` | #0ECB81 | 新增功能、正向 |
| `--red` | #F6465D | 重要/策略/删除 |
| `--purple` | #8b5cf6 | Web 端标识 |
| `--amber` | #d97706 | 流程/链路 |
| `--dark` | #0B0E11 | Phone 背景 |
| `--surface` | #fff | Web Frame 背景 |

### 组件尺寸

| 组件 | 宽度 | 说明 |
|------|------|------|
| Phone | 375px | 固定宽度，模拟手机 |
| Web Frame | 480-960px | 根据内容调整 |
| Arrow (.aw) | 80px | 屏幕间连接 |
| Annotation Card | 320px | 注释卡片 |

### PART 分组主题

| 类型 | class | 背景 | 适用 |
|------|-------|------|------|
| 深色 | `.gd.viewer` | 深灰渐变 | App 用户端 |
| 蓝色 | `.gd.host` | 蓝色渐变 | Web 管理端 |
| 绿色 | `.gd.cross` | 绿色渐变 | 跨端衔接 |
| 自定义 | inline style | 自定义渐变 | 特殊模块 |

## 注意事项

1. **ann-card 编号 ↔ anno-n 编号对应**：若使用 anno overlay 做屏幕锚点，每个 `.anno-n` 的编号必须在 ann-card 的 `.ann-num` 里有对应条目（1↔1, 2↔2）。这是 anno overlay 合法性的判断依据
2. **phone-label 是跨 skill 编号对齐的唯一入口**：`<span class="phone-label">A-1 · 首页 Feed</span>` 让 PRD/prototype/bspec 的 A-1 章节能定位到 IMAP scene A 里面这个手机节点
3. **跨端表格**：用 `grid-template-columns` 6列布局（序号/起点/箭头/终点/数据/触发方式）

## 自检清单（Step C 执行）

> 通用条目（编号一致、脚本保存、FILL 残留、术语一致）见 pm-workflow.md，以下为本 Skill 专项：

**新规范三条硬断言**（必须全过）：
- [ ] **主场景粒度**：IMAP scene id 只是主场景（A/B/C 等），子场景（A-1/A-2）作为手机节点放在主场景内部；`grep -c 'phone-label'` ≥ 手机节点数
- [ ] **anno overlay 合法性**：若使用，每个 `.anno-n` 编号必须在对应 ann-card 的 `.ann-num` 里有条目（1↔1, 2↔2）；孤立 anno 或配差量标签/文案的一律不合法
- [ ] **零差量叙事**：`grep -cE 'ann-tag (new|chg|del)|V[0-9]+\.[0-9]+|>NEW<|>改动<|>变更<'` = 0（「新增」作为数据表字段值不计，仅禁标签和主体差量文案）

**传统条目**：
- [ ] 异常场景已覆盖
- [ ] 箭头零交叉
- [ ] ann-card 内编号（若使用）自洽
- [ ] 侧导航锚点全部可跳转
- [ ] 数据（字段名/枚举值/状态）全文一致

### UX 质量检查（仅 `.phone` 深色 mockup）

- [ ] **触摸目标** — 主操作按钮 ≥ 44px，无纯文字链跳转
- [ ] **对比度 + 涨跌色** — 关键数字 ≥ 4.5:1，次级 ≥ 3:1；涨跌用 ↑↓/+- 辅助，不仅靠颜色
- [ ] **Safe Area + 弹窗** — 底部 ≥ 34px；弹窗有 ✕ + 遮罩关闭
- [ ] **导航 + 数据状态** — Tab ≤ 5；异步区域标注 loading；数字列 JetBrains Mono 右对齐

**强制验证脚本**（自检最后一步，不可跳过）：
```bash
bash scripts/check_html.sh projects/{项目}/deliverables/XXX.html projects/{项目}/scene-list.md imap
```

## 业务组件引用规则

【业务组件】交易卡片、Feed 极简卡、帖子列表、$币种胶囊、半屏交易抽屉、直播间卡片、直播详情、CMS 表格/看板——这些组件必须从对应的 biz-*.md 文件复制 HTML 结构，禁止自行设计样式。只替换占位符内容，不改 HTML 结构和 CSS。
