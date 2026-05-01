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
  check_paradigm.py: "Step 0 范式门 — python3 .claude/skills/prototype/scripts/check_paradigm.py {项目名}"
  gen_proto_skeleton.py: "Step A 骨架 — from gen_proto_skeleton import generate_skeleton"
  update_proto_base.py: "Step D 升版 — from update_proto_base import ProtoUpdater"
  audit_against_baseline.py: "Step C 标杆对照 — python3 .claude/skills/prototype/scripts/audit_against_baseline.py <html> [--baseline <baseline.html>]"
  imap_phone_shots.py: "IMAP 硬看 — python3 .claude/skills/prototype/scripts/imap_phone_shots.py <imap.html> -o <out_dir>"
  prototype.js: "运行时 JS — 骨架脚本自动内联，不手动读"
  scripts/check_html.sh: "Step C 自检 — bash scripts/check_html.sh <html> <scene-list> proto"
  scripts/lib/html_patcher.py: "HtmlPatcher 基类 — update_proto_base.py 的底层依赖"
---

# 可交互原型 Skill（Interactive Prototype）

## 硬规则（优先级最高）

### 反凭印象三红线（v1/v2 翻车沉淀，违反任一视为未交付）

- **凭印象画 = 红线**：任何 Crypto APP 元素（feed 卡片 / trader 卡 / 战绩组件 / 订阅 CTA / 抽屉 / 状态栏 / 底部导航）必须先查 [`references/crypto-app-vocabulary.md`](references/crypto-app-vocabulary.md) 对应词条 + Figma 真品 PNG（`assets/figma-anchors/`）+ interaction-map references（`biz-trading.md` / `biz-social.md` / `biz-livestream.md` / `components-core.md`）。三类源头任一缺失 → 必须先补再画
- **IMAP 硬看强制**：上游有 IMAP 时，Step A 前必须用 `imap_phone_shots.py` 单独截每张 phone（每张独立文件），Read 多模态确认元素细节后再骨架。详见 [`references/prototype-source-discipline.md § B`](references/prototype-source-discipline.md)
- **标杆对照强制**：Step C 必须跑 `audit_against_baseline.py` 对照范式标杆 HTML，关键组件计数 + Fill 视觉铁律 + 反 AI slop 六禁全过才允许声明完成

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

**必读规则**（HTML pipeline 通用，含演讲叙事 / 分步生成 / Fill 质量 / 美学硬底线）：

```
view .claude/rules/html-pipeline.md
```

**Crypto 认知 ground truth + 视觉锚点**（凭印象画 = 红线，本 Skill 强制）：

```
view .claude/skills/prototype/references/crypto-app-vocabulary.md           # 真品组件 + 路由表 + Figma anchors
view .claude/skills/prototype/references/baseline-pattern-card.md           # 3 标杆 × 5 场景对照
view .claude/skills/prototype/references/prototype-source-discipline.md     # 有/无 IMAP 双流程纪律
```

按 `check_paradigm.py` 输出的「必读 references」清单加载 imap references（biz-social / biz-trading / biz-livestream / components-core），不全量。

**Step A 不读模板** — 骨架脚本只需下方 API 速查表，CSS/JS 由 `open().read()` 自动拼接。

**Step B 填充开始前读取组件模板**：
```
view .claude/skills/prototype/assets/prototype-templates.html
```

**按需读取（Step B 填充时遇到不确定的组件结构再读对应章节，禁止全量加载）：**
- 前台 App 页面 → 只读 `## A. 前台深色组件`
- 后台管理页面 → 只读 `## B. 管理台浅色组件` + `## D. 数据驱动 CRUD 模式`
- 弹窗/Toast/底部弹出 → 只读 `## C. 通用交互组件`
```
grep -n "^## " .claude/skills/prototype/scripts/prototype-components.md  # 定位章节行号
sed -n '{起始行},{结束行}p' .claude/skills/prototype/scripts/prototype-components.md  # 只读需要的章节
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

## Step 0：范式选择门 + 竞品截图收集（强制）

prototype 触发后**禁止直接跑 generate_skeleton**。必须先完成本步：

### 0.1 范式推断

```bash
python3 .claude/skills/prototype/scripts/check_paradigm.py {项目名}
```

脚本读 context.md 第 2 章 + scene-list.md，推断端构成，给出 4 选 1 推荐 + 标杆 HTML 路径 + 必读 references 清单。模型必须向用户**口头确认**范式正确，确认后才进 Step A。

4 个范式 × 标杆映射：

| 端构成 | 范式 | 标杆 |
|--------|------|------|
| 纯 App + 多场景（≥ 5）| 单 phone + scene chips | V8 / community v3 |
| 纯 App + 简单流（≤ 3）| 单 phone 无 nav | （小型项目）|
| Web 前台 + Web 后台共建 | 多 view 切换 (gnav) | activity-center v5.1 |
| 纯 Web 后台 / CMS | 单 view + sidebar | activity-center mgt-view |

脚本推断不出范式时（端类型混合 / 场景数模糊）→ 模型必须向用户问 4 选 1，禁止自行假设。

### 0.2 竞品截图 / Figma 真品收集（Crypto 认知 ground truth）

范式确认后，模型主动问用户：

> 这个项目对标哪些真品？请给 1-3 个来源（任选其一）：
> 1. **Figma 真品链接**（HTX 项目优先 — 直接 fetch_figma 入档最高权威）
> 2. **竞品截图**（Binance / OKX / Bitget / Gate / HTX 实际页面截图）
> 3. **已有 IMAP**（上游 IMAP 已存在则直接用）

收集动作：

- Figma 链接 → `python3 scripts/fetch_figma.py <url> --batch ... --out-dir .claude/skills/prototype/assets/figma-anchors/`（持久 anchor，下次复用）
- 竞品截图 → 存 `projects/{项目}/inputs/competitors/`
- 模型 Read 多模态读每张图，写 1 段「视觉提炼」追加到 context.md 第 5 章末尾（配色 / 字号层级 / 关键组件 / 交互模式）

**只有用户明确说「不需要竞品 / 直接做 / 已有 IMAP 看就够」时才允许跳过**；模型不可主动跳过。v1 翻车就翻在没竞品 anchor 凭印象 — 这是硬底线。

### 0.3 上游分支判定

详见 [references/prototype-source-discipline.md § A0](references/prototype-source-discipline.md)。有 IMAP 走硬看流程，无 IMAP 走双 anchor 替代流程。

## 美学规范（前台 App 主题 + 通用底线）

prototype HTML 的两层美学约束：

### 主题层（按范式选）

- **前台 App / 交易所视觉**（单 phone + scene chips / 单 phone 无 nav）：Binance 深色系合法主题 — `--bg:#0B0E11` + 涨绿 `#0ECB81` + 跌红 `#F6465D` + 金 `#FCD535`，金融语义保留。HTX 项目字体栈 `'HarmonyOS Sans SC','Noto Sans SC',...`（CJK 优先 + HTX 钦定）
- **Web 后台 / CMS**（单 view + sidebar）：Claude Design 系暖近黑 — `--cd-bg:#1F1F1E` + accent `#D97757`，token 来自 `.claude/skills/_shared/claude-design/tokens.css`
- **多 view（gnav 共建）**：前台 App 走 Binance、后台 view 走 Claude Design，两套主题在同一 HTML 共存合法（参考 activity-center v5.1）

### 通用底线（所有范式必吃）

引 `.claude/rules/html-pipeline.md` § 三：

- 反 AI slop 六禁（全屏渐变 / emoji 装饰标题 / accent border / SVG 画人 / 烂大街字体作 CJK / 每卡都带 icon）
- 字号比：标题 ≥ 正文 2.5 倍，line-height 含 CJK display 1.25-1.35 / 正文 1.6-1.8
- 颜色克制：≤ 1 主 + 1 辅 + 1 强调 + 灰阶
- 留白 ≥ 40%，间距 8pt 网格
- 字重三级层次：900 display / 700 标题/CTA / 400 正文（禁全文只 700）
- CSS 变量源头唯一：tokens.css 拼入，禁手抄 :root 整块

Step C `audit_against_baseline.py` grep 验证以上六禁 + 字重三级，违规即 fail。fail 必须修，不允许跳过。

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
sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/prototype/scripts'))
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

### Step D · 升版（已有 vN → vN+1）

已有完整原型需要升级时，**禁止直接 Edit/Write 生成出的 HTML**。按改动性质分两条路径：

**判断口诀（开工前先判）**：

| 改动对象 | 路径 | 原因 |
|---------|------|------|
| JS 里 `var xxxData = [...]` / CRUD 初始数据 | 改 `fill_proto_v{N}.py` 源，重跑 fill | render 生成，patch HTML 等于改产物不改源 |
| mock 设备壳内写死文案 / `<div class="f-row">` 字段 block / 模态框 HTML | 写 `patch_proto_v{N}.py` | HTML 里就是 source of truth |
| 单一 CSS 调优 / ≤5 行文案微调 / 颜色调色 | 允许 Edit 直改 HTML | 收益大于规范代价 |
| 结构性改动（字段增删 / 区块重写 / 版本号 bump） | **必须** patch 脚本 | Edit 会被下次 gen/fill 覆盖 |

**命名与位置**：

- `projects/{proj}/scripts/patch_proto_v{N}.py`（每个 v{N} 一个独立脚本，**不归档**，保留在 `scripts/` 便于回溯）
- 底本规则：`SRC = 上一个正式版 HTML`（如 v4.7），不是过渡版（如 v4.8）
- **SRC 路径必须指向 `deliverables/archive/`**：升版完成后旧版 HTML 会归档，若脚本 SRC 写成 `deliverables/xxx_v{N-1}.html` 归档后就跑不动，未来无法回归验证
- 脚本头注释列出本次所有 delta 条目（对应 context.md 决策编号）

**脚本结构**（内联模板，复制到项目改写即可）：

```python
#!/usr/bin/env python3
"""v{N-1} 原型 → v{N} patch（触发原因 + 决策编号）"""
import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_WS = os.path.abspath(os.path.join(ROOT, '..', '..'))
sys.path.insert(0, os.path.join(_WS, 'scripts'))
sys.path.insert(0, os.path.join(_WS, '.claude/skills/prototype/scripts'))

from update_proto_base import ProtoUpdater

SRC = os.path.join(ROOT, 'deliverables/archive/{type}_可交互原型_v{N-1}.html')  # ← archive/ 路径
DST = os.path.join(ROOT, 'deliverables/{type}_可交互原型_v{N}.html')

u = ProtoUpdater(SRC, DST)

# ═══ 1. 版本号 ═══
u.bump_version('v{N-1}', 'v{N}')

# ═══ 2+. 按 delta 逐条 patch（对应 context.md 决策编号）═══
# u.replace_element_by_id('acDev0', '<new html>', '决策 XX')
# u.replace_form_field('其他标签', '<new field>', '决策 XX')
# u.patch('<old>', '<new>', '决策 XX')  # 通用方法

u.save()
```

**ProtoUpdater API 速查**（继承 HtmlPatcher）：

| 方法 | 用途 |
|------|------|
| `bump_version(old, new)` | 替换全文版本号 |
| `patch(old, new, desc, n=1)` | 精确字符串替换（通用） |
| `replace_element_by_id(id, new_inner, desc)` | 替换指定 id 元素内容 |
| `replace_form_field(label, new_html, desc)` | 替换包含指定 label 的表单行 |
| `replace_gnav_tab(old_label, new_label, desc)` | 替换全局导航 Tab |
| `replace_sidebar_item(old_text, new_html, desc)` | 替换侧栏导航项 |
| `save()` | 写出 + 打印统计 |

**执行 & 验证**：

1. 跑脚本：`python3 projects/{proj}/scripts/patch_proto_v{N}.py`
2. 无损复现校验（推荐）：
   ```bash
   cp deliverables/xxx_v{N}.html /tmp/manual.html
   python3 scripts/patch_proto_v{N}.py
   diff -q /tmp/manual.html deliverables/xxx_v{N}.html && echo MATCH
   ```
3. `check_html.sh` 跑 Step C 自检清单
4. 旧版归档到 `deliverables/archive/`（脚本保留）

**真实样本参考**：

- [projects/growth/activity-center/scripts/patch_proto_v48.py](../../projects/growth/activity-center/scripts/patch_proto_v48.py) — 19-delta 大规模案例
- [projects/growth/activity-center/scripts/patch_proto_v49.py](../../projects/growth/activity-center/scripts/patch_proto_v49.py) — 4-delta 精简案例，`MATCH` 已验证

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

### 强制验证脚本（自检三件套，不可跳过）

```bash
# 1) 通用 HTML 自检（编号 / FILL 残留 / 字体 / 差量标签）
bash scripts/check_html.sh projects/{项目}/deliverables/XXX.html projects/{项目}/scene-list.md proto

# 2) 标杆对照（必备组件 + Fill 视觉铁律 E1-E6 + 反 AI slop 六禁 + 字重三级）
python3 .claude/skills/prototype/scripts/audit_against_baseline.py \
  projects/{项目}/deliverables/XXX.html \
  --baseline {check_paradigm 输出的标杆 HTML 路径}
```

### Playwright click 强制验证（替换原「浏览器验证」软建议）

单纯 screenshot self-check **不算**通过，必须 playwright assertion 验证 DOM 状态：

```bash
python3 scripts/with_server.py --server "python3 -m http.server 5173" --port 5173 -- \
  python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    page = p.chromium.launch(headless=True).new_page()
    page.goto('http://localhost:5173/projects/{项目}/deliverables/XXX.html')
    page.wait_for_load_state('networkidle')
    # ... 写下方最小 click 集 assertions
"
```

**最小 click 集**（含相关组件的场景全跑过，无 console error / 视觉无错位才算通过）：

1. 每个 scene chip 点击 → `.scr.on` 切换正确（assertion：`page.locator('.scr.on').count() == 1`）
2. 含订阅 CTA 的场景：click 后文案变「已订阅」+ 宽度不变（保留 flex:1）+ 铃铛出现
3. 含铃铛的场景：click → 🔔 ↔ 🔕 toggle + toast 文案对应
4. 含 toggle 的场景：click → on/off 状态切换 + 跨场景同 toggle 联动（如设置页 + 抽屉同一 toggle）
5. 含抽屉 / sheet 的场景：scrim click + ✕ click 都能关
6. 含 TAB 的场景：每个 TAB 切换 .on 类正确

screenshot 仅用于：① 视觉 bug 复现 ② 标杆对照（zoom 局部）③ 最终交付截图。

三件套全过 + Playwright click 全 pass 才视为自检通过 → 才允许声明完成。任一 fail → 必须修，禁止跳过（v1 / v2 翻车都翻在「自检通过 → 交付 → 用户挑出 bug」的循环）。

## 业务组件引用规则

【业务组件】交易卡片、Feed 列表、直播间、CMS 后台表格/表单——这些组件必须从 prototype-components.md 的对应 section 复制 HTML 结构，禁止自行设计样式。
