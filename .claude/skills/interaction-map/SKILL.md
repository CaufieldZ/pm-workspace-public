<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: interaction-map
description: >
  当用户提到「交互大图」「UI flow」「交互流程图」「前端交互图」「画个交互图」
  「screen flow」「interaction map」时触发。也在场景清单已确认、复杂/超复杂链路
  进入视觉化阶段时自动接续触发。即使用户只说「画图」也应先确认是否需要交互大图。
type: pipeline
output_format: .html
output_prefix: imap-
pipeline_position: 3
depends_on: [scene-list]
optional_inputs: [context.md, requirement-framework, architecture-diagrams]
consumed_by: [prototype, prd]
---
<!-- pm-ws-canary-236a5364 -->

# 交互大图 Skill（Interaction Map）

> 通用分步生成规则（强制规则 / 快速模式 / Fill 脚本规范 / 通用自检）见 `pm-workflow.md`「HTML 分步生成通用规则」。以下为本 Skill 补充规则：
> - Step B 每填充 1-3 个 Scene 后停下报告进度（非快速模式）
> - Step C 自检时逐个对照 scene-list.md 编号，列出「已覆盖 / 缺失」清单
## 核心输出规范

1. **单文件 HTML**：所有 CSS/JS 内联，无外部依赖（字体 CDN 除外）。`interaction-map.css` 和 `interaction-map.js` 由骨架脚本 `gen_imap_skeleton.py` 通过 `open().read()` 自动内联，不在本文件中显式引用
2. **Web + Mobile 双端 Mockup**：App 用 `.phone`（深色），Web/CMS 用 `.webframe`（浅色）
3. **横向 Flow 布局**：`.flow` 容器 → `.flow-col` 屏幕 → `.aw` 箭头 → `.ann-card` 说明
4. **标注系统**：`.anno` 虚线框 + `.anno-n` 编号圆点（多色）
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

### Fill 必需组件清单（强制）

每个 Scene 的 fill 函数必须包含以下全部组件，缺一不可：

| # | 组件 | class | 缺失后果 | 检查方式 |
|---|------|-------|---------|---------|
| 1 | 屏幕 | `.phone` 或 `.webframe` | 无内容 | 目视 |
| 2 | 箭头 | `.aw` > `.al` + `.tx` | 屏幕间无流向 | `grep -c 'class="aw"'` |
| 3 | 标注框 | `.anno.{色}` > `.anno-n` | 注释无法对应屏幕区域 | `grep -c 'class="anno '` |
| 4 | 注释卡 | `.ann-card` | 无改动说明 | `grep -c 'ann-card'` |
| 5 | 卡片标题 | `.card-title` + `.ann-tag` | 卡片无标题和优先级 | `grep -c 'card-title'` |
| 6 | 注释条目 | `.ann-item` > `.ann-num` + `.ann-text` | 说明不可读 | `grep -c 'ann-item'` |
| 7 | 优先级标签 | `.ann-tag.{new/chg/del/p0/p1/p2}` | 无优先级区分 | `grep -c 'ann-tag'` |
| 8 | 屏幕说明 | `.flow-note` | 屏幕缺状态描述 | `grep -c 'flow-note'` |
| 9 | 信息框 | `.info-box.{色}` (至少 1 个/PART) | 缺补充说明 | `grep -c 'info-box'` |

> **注意**：ann-card 不是只写外壳 + ann-num，必须包含完整子结构（card-title + ann-item > ann-num + ann-text + ann-tag）。参考 `fill-template.py` 和 `gold-snippets.md` 示例。

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

### 组件完整性规则（强制）

5. **每个 fill 函数必须包含上方"Fill 必需组件清单"全部 9 类组件**（info-box 至少每 PART 1 个）
6. **填充完成后，对每个 Scene 执行 grep 验证**：`grep -c 'class="aw"\|class="anno \|ann-tag\|info-box\|flow-note' deliverables/xxx.html` — 任一为 0 则返工
7. **禁止"裸 ann-card"**：ann-card 内部必须有 `.card-title`（含至少 1 个 `.ann-tag`）+ 至少 1 个 `.ann-item`（含 `.ann-num` + `.ann-text`）

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

**每个 fill 函数包含**：Phone/Web Mockup + UI 元素 + `.aw` 箭头 + `.anno` 标注 + `.ann-card` 注释 + `.flow-note` 说明

**填充节奏**（非快速模式）：简单 Scene 3 个一批，复杂 Scene 1 个一批，每批报告进度。
填充时不能破坏已有 CSS / JS / 其他 Scene。

### Step C：收尾（约 200-300 行）

最后一批填充完成后：

1. **插入跨端数据流表格**（如果有跨 View 交互）
2. **插入底部 Callout**（阅读指引 + 优先级说明）
3. **执行自检**（见下方自检清单）
4. **告知用户交付**

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

**标注规则**：
- 用 `.anno.{color}` 虚线框圈住改动区域
- 用 `.anno-n.{color}` 编号（右上角）
- 颜色分类：`blue`（布局）、`green`（新增）、`red`（策略/重要）、`purple`（Web 端）、`amber`（流程）
- 在 `.ann-card` 中用 `.ann-item` + `.ann-num` 逐条解释

**Tag 系统**：
- `.ann-tag.new` — 绿底 NEW
- `.ann-tag.chg` — 蓝底 改动
- `.ann-tag.del` — 红底 删除
- `.ann-tag.p0` / `.p1` / `.p2` — 优先级

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

1. **标注要匹配**：`.anno` 框的编号要与 `.ann-card` 内的 `.ann-num` 一一对应
2. **跨端表格**：用 `grid-template-columns` 6列布局（序号/起点/箭头/终点/数据/触发方式）

## 自检清单（Step C 执行）

> 通用条目（编号一致、脚本保存、FILL 残留、术语一致）见 pm-workflow.md，以下为本 Skill 专项：

- [ ] 异常场景已覆盖
- [ ] 箭头零交叉
- [ ] 每个 Scene 的标注编号与 `.ann-card` 编号一一对应
- [ ] 侧导航锚点全部可跳转
- [ ] 数据（字段名/枚举值/状态）全文一致

### UX 质量检查（仅 `.phone` 深色 mockup）

- [ ] **触摸目标** — 主操作按钮 ≥ 44px，无纯文字链跳转
- [ ] **对比度 + 涨跌色** — 关键数字 ≥ 4.5:1，次级 ≥ 3:1；涨跌用 ↑↓/+- 辅助，不仅靠颜色
- [ ] **Safe Area + 弹窗** — 底部 ≥ 34px；弹窗有 ✕ + 遮罩关闭
- [ ] **导航 + 数据状态** — Tab ≤ 5；异步区域标注 loading；数字列 IBM Plex Mono 右对齐

**强制验证脚本**（自检最后一步，不可跳过）：
```bash
bash scripts/check_html.sh projects/{项目}/deliverables/XXX.html projects/{项目}/scene-list.md imap
```

## 业务组件引用规则

【业务组件】交易卡片、Feed 极简卡、帖子列表、$币种胶囊、半屏交易抽屉、直播间卡片、直播详情、CMS 表格/看板——这些组件必须从对应的 biz-*.md 文件复制 HTML 结构，禁止自行设计样式。只替换占位符内容，不改 HTML 结构和 CSS。
