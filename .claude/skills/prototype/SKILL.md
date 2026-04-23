<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: prototype
description: >
  当用户提到「原型」「可交互原型」「prototype」时触发。PRD / IMAP 完成后可转为可交互版本。
type: pipeline
output_format: .html
output_prefix: proto-
pipeline_position: 4
depends_on: [scene-list]
optional_inputs: [interaction-map]
consumed_by: [prd]
scripts:
  gen_proto_skeleton.py: "Step A 骨架 — from gen_proto_skeleton import generate_skeleton"
  prototype.js: "运行时 JS — 骨架脚本自动内联，不手动读"
  scripts/check_html.sh: "Step C 自检 — bash scripts/check_html.sh <html> <scene-list> proto"
---
<!-- pm-ws-canary-236a5364 -->

# 可交互原型 Skill（Interactive Prototype）

## 硬规则（优先级最高）

### 数据驱动

- JS 数组存数据 → render 函数渲染列表 → 弹窗按索引读 → 保存 = 写回 + 重渲染 + 关弹窗
- **禁止**列表写死 HTML 而弹窗另一套数据
- 新增弹出空表单 + 默认值，编辑弹出对应数据，两者共用同一弹窗组件
- 增删改全联动，统计实时更新，删除二次确认

### 踩坑速查（交付前过一遍）

- [ ] 一级页面展示的摘要 = 编辑弹窗数据（数据驱动根治）
- [ ] 同一概念没有两种叫法
- [ ] 多个编辑按钮传了索引参数，弹窗内容正确对应
- [ ] 保存 = 写数据 + render + 关弹窗三步
- [ ] 两个文件的同一场景数据一致
- [ ] 编辑对应数据 → 保存刷新列表 → 列表摘要 = 弹窗数据 → 术语统一 → 无空白 bug

## 如何使用

### Step 1：读取 Reference

**Step A 不读模板** — 骨架脚本只需下方 API 速查表，CSS/JS 由 `open().read()` 自动拼接。

**Step B 填充开始前读取组件模板**：
```
view .claude/skills/prototype/references/prototype-templates.html
```

**按需读取（Step B 填充时遇到不确定的组件结构再读对应章节，禁止全量加载）：**
- 前台 App 页面 → 只读 `## A. 前台深色组件`
- 后台管理页面 → 只读 `## B. 管理台浅色组件` + `## D. 数据驱动 CRUD 模式`
- 弹窗/Toast/底部弹出 → 只读 `## C. 通用交互组件`
```
grep -n "^## " .claude/skills/prototype/references/prototype-components.md  # 定位章节行号
sed -n '{起始行},{结束行}p' .claude/skills/prototype/references/prototype-components.md  # 只读需要的章节
```

**美学规范（产出前 grep 决策速查表段）：**
```
grep -A 20 "决策速查" .claude/skills/_shared/claude-design/anti-ai-slop.md
```

**Claude Design 后台深色主题（手动挂 class）：**
- `.theme-cd` 作用域已在 prototype.css 末尾定义，覆盖 Arco 浅色变量为 Claude Design 深色
- Web 后台 / CMS 场景：手动在生成后的 HTML body 加 `class="theme-cd"` 即可切换
- App 移动端**不应用**此 theme（移动端保留「深色 nav + 浅色内容」功能性设计）
- `.app-mock` 设备框已升级至 iPhone 15 Pro 精细数值（圆角 48px / 状态栏 54px / Dynamic Island 124×36 / Home Indicator 140×5）

### Step 2：确定 View 结构

向用户确认：几个 View、每个 View 前台/后台、**每个 View 的设备类型（App 手机框 / Web 全宽）**、包含哪些页面。

**设备类型判定规则**：
- View 是 App 端（iOS/Android）→ 必须用 `device: "phone"`，生成 375×812 手机壳
- View 是 Web 端（浏览器全宽）→ 不设 device，默认全宽
- View 是 CMS 管理台 → 用 `theme: "light"`（自带侧边栏布局）
- 如果不确定，问用户

## ★ 分步生成策略

> 通用分步规则（强制规则 / 快速模式 / Fill 脚本规范）见 `pm-workflow.md`「HTML 分步生成通用规则」。
> 本 Skill 补充：Step B 每填充 1-2 个页面后报告进度（非快速模式）。

### 总体流程

```
用户确认 View 结构
      ↓
Step A：生成骨架文件（CSS + JS + 全局导航 + View/页面占位）
      ↓ 用户确认骨架结构
Step B：逐页面/View 填充内容（每次 1-2 个页面）
      ↓ 每批填完用户确认
Step C：收尾（数据驱动 CRUD 补全 + 自检）
      ↓
交付
```

### Step A：生成骨架文件（约 300-500 行）

**优先使用骨架脚本**：
1. 读取下方 `gen_proto_skeleton.py API 速查`，了解 `project / views` 数据结构
2. 根据 context.md + scene-list.md 填充数据
3. 将脚本复制到 `projects/{项目名}/scripts/gen_proto_v{N}.py`，修改数据，运行
4. 骨架文件自动生成到 deliverables/

如果因故不能用脚本，则手动生成，包含：
- 完整 `<style>` 块（从 `prototype.css` 通过 `open().read()` 读入，不删减）
- 全局导航栏 `.gnav`（含所有 View 的 Tab）
- 每个 View 的 `<div class="gnav-view-section">`（只有容器 + 注释占位）
- 前台 View：产品导航栏 `.p-nav` + 空页面容器
- 后台 View：侧边栏 `.sb` + 空页面容器 + 弹窗空壳
- 完整 `<script>` 块（从 `prototype.js` 通过 `open().read()` 读入，末尾含 `// FILL_START:crud` / `// FILL_END:crud` 占位）

骨架文件可以直接在浏览器打开，看到全局导航和 View 切换，但页面内容是空的。

**骨架输出后询问用户**：
> 骨架结构已生成，包含 N 个 View、M 个页面。请确认结构正确，我开始逐页面填充内容。
> 你想一次填几个页面？建议每次 1-2 个。

**⛔ 硬停点：输出骨架后必须在此停止。**（快速模式除外）

### gen_proto_skeleton.py API 速查

骨架生成只需调用一个函数，**不需要读源码**：

```python
# 导入方式（从 projects/{项目}/scripts/ 执行，向上 3 层到工作区根目录）
import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/prototype/references'))
from gen_proto_skeleton import generate_skeleton
```

```python
generate_skeleton(project, views, output_path)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `project` | `dict` | `{"name": "产品名", "version": "v1.0"}` |
| `views` | `list[dict]` | 见下方结构 |
| `output_path` | `str` | 输出文件路径 |

**views 结构**：
```python
{
    "id": "user-view",         # DOM id
    "name": "用户端",           # Tab 显示名
    "icon": "📱",              # Tab icon
    "theme": "dark",           # "dark" | "light"
    "device": "phone",         # "phone" = 375×812 手机壳（App 端必须用）| 省略 = Web 全宽
    "nav_name": "产品名",      # dark 主题的 p-nav 显示名（可选）
    "pages": [
        {"id": "main", "name": "首页"},
        {"id": "detail", "name": "详情"},
    ],
    # light 主题额外字段：
    "sidebar_group": "功能管理",  # 侧边栏分组标题
    "sidebar": [
        {"icon": "📋", "name": "列表管理"},
    ],
}
```

**骨架自动生成的占位符**（成对块，替换时需连同中间 fallback 内容一并清除）：
- 前台页面：`<!-- FILL_START:page-{id} --> ... <!-- FILL_END:page-{id} -->`
- 后台页面：`<!-- FILL_START:page-{id} --> ... <!-- FILL_END:page-{id} -->`
- 前台抽屉：`<!-- FILL_START:drawer-{view_id} --> ... <!-- FILL_END:drawer-{view_id} -->`
- 后台弹窗：`<!-- FILL_START:modal-{view_id} --> ... <!-- FILL_END:modal-{view_id} -->`
- CRUD 脚本：`// FILL_START:crud` / `// FILL_END:crud`（在 `<script>` 末尾）

### Step B：逐页面填充（每个页面约 200-500 行）

写 `fill_proto_v{N}.py` 脚本到 `projects/{项目名}/scripts/`：
- 每个页面定义一个函数（`def fill_page_main(): return '''...'''`）
- 脚本超 200 行按 View 拆分数据文件

**每个 fill 函数包含**：Tab 栏 / 卡片网格 / 表格 / 表单 / 弹窗内容，从 prototype-components.md 选组件。

**填充节奏**（非快速模式）：前台复杂页面 1 个一批，后台简单页面 2 个一批。
**即使占位块内容为空也必须替换**以清除 FILL 标记。
填充时不能破坏已有 CSS / JS / 其他页面。

### Step C：收尾

最后一批填充完成后：

1. **补全数据驱动 CRUD**（后台页面必须有）：fill 脚本中用 `html.replace('// FILL_START:crud\n// FILL_END:crud', crud_js)` 注入 CRUD 逻辑（数据数组 + render + openEdit + saveItem + deleteItem + 初始 renderList 调用）
2. **补全弹窗/抽屉内容**（通过 `FILL_START:modal-xxx` / `FILL_END:modal-xxx` 等成对占位块注入）
3. **执行自检**（见下方自检清单）
4. **告知用户交付**

### 骨架占位模板

每个页面的占位格式（`FILL_START:page-{name}` / `FILL_END:page-{name}` 为成对边界）：
```html
<!-- ═══════════════════════════════════════ -->
<div class="p-page" id="page-{name}">
  <!-- FILL_START:page-{name} -->
  <!-- FILL_END:page-{name} -->
</div>
```

后台页面占位：
```html
<div class="ct page" id="page{N}">
  <!-- FILL_START:page{N} -->
  <!-- FILL_END:page{N} -->
</div>
```

## 交互函数

| 函数 | 用途 |
|------|------|
| `switchGlobalView(idx)` | 切换全局 View |
| `switchTab(el, prefix, tab)` | Tab 切换 |
| `goPage(name)` | 页面跳转 |
| `toggleDropdown(e)` | 下拉开关 |
| `openDrawer() / closeDrawer()` | 抽屉开关 |
| `switchChip(el, prefix, tab)` | Chip 筛选 |
| `switchDevice(webId, appId, btns, idx)` | Web/App 切换 |
| `swPage(el, idx)` | 后台侧栏切换 |

## Fill 内容契约

骨架和 fill 脚本的 HTML 层级边界定义如下。

### 骨架提供

- 完整设备壳：前台 dark view 提供 `.app-mock`（phone 模式）或全宽布局 + nav；后台 light view 提供 `.layout` + sidebar + topbar
- 空 FILL 标记在设备壳**内部**（页面容器、抽屉、弹窗、CRUD 脚本）
- 基础 JS 交互（View 切换、页面跳转、抽屉/弹窗开关）

### fill 提供（替换 FILL 标记）

| 标记类型 | 内容 | 注意 |
|----------|------|------|
| `page-{id}` | 页面内部 UI 元素（卡片/列表/表单） | **不包含设备壳**，骨架已提供 |
| `drawer-{view_id}` | 抽屉面板内容 | 不包含抽屉容器壳 |
| `modal-{view_id}` | 弹窗内容区 | 不包含弹窗容器壳 |
| `crud` | JS 数据数组 + render + CRUD 函数 | 纯 JS，不含 `<script>` 标签 |

**禁止**：fill 中再生成 `.app-mock` / `.layout` / `.p-nav` / sidebar 等设备壳元素。

## 注意事项

1. 组件不绑定业务——ref 是通用骨架，按具体产品填充内容
2. 遇到 ref 没有的场景组件（直播间、K线、聊天区、Feed 流等），按 CSS Token 自行构建
3. 数据用接近真实的示例，不用 Lorem ipsum

## 自检清单（Step C 执行）

> 通用条目（编号一致、脚本保存、FILL 残留、术语一致）见 pm-workflow.md，以下为本 Skill 专项：

- [ ] 所有 View 可通过全局导航切换
- [ ] 前台深色 / 后台浅色；App 端 375×812 手机壳内不溢出
- [ ] 抽屉在手机壳内底部上推，不脱出手机框
- [ ] 后台 CRUD 数据驱动：列表数据 = 弹窗数据 = render 输出
- [ ] 弹窗/抽屉有遮罩 + ✕ + 遮罩点击关闭
- [ ] **浏览器验证**：页面跳转 → 抽屉 → Tab → CRUD 增删改

**强制验证脚本**（自检最后一步，不可跳过）：
```bash
bash scripts/check_html.sh projects/{项目}/deliverables/XXX.html projects/{项目}/scene-list.md proto
```
检查全部通过后才视为自检通过。

## 业务组件引用规则

【业务组件】交易卡片、Feed 列表、直播间、CMS 后台表格/表单——这些组件必须从 prototype-components.md 的对应 section 复制 HTML 结构，禁止自行设计样式。
