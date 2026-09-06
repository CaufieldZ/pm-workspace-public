---
name: architecture-diagrams
description: >
  当需求涉及多系统对接 / 资金流转，或用户提到「架构图」「技术架构」时触发。超复杂链路中场景清单后、IMAP 前自动接续；也适用于系统设计文档、技术方案评审、风险分析、Phase 路线图等。
type: pipeline
output_format: .html
output_prefix: arch-
pipeline_position: 2.5
depends_on: [scene-list]
optional_inputs: [baseline]
consumed_by: [interaction-map]
scripts:
  build_arch_skeleton.py: "Step 1 骨架 — from build_arch_skeleton import generate"
---

# 架构图集 Skill（Architecture Diagrams）

## 触发与定位

**做什么**：多 Tab 单页 HTML 技术方案文档，**CSS Grid 卡片 + 表格 + Callout** 讲清技术设计，等同评审 PPT。

**何时触发**：超复杂链路（≥ 2 系统 / 资金流 / 多团队依赖）在 scene-list 后、interaction-map 前接续；技术方案评审、风险分析、Phase 路线图。

**不做**：页面跳转交互（归 interaction-map）/ UI 高保真（归 prototype）/ 拓扑节点连线（按需查 references/svg-topology-extension.md，**大部分方案不需要**）。

**与 interaction-map 区别**：imap 是横向 Flow + Mockup 讲交互；arch 是 Tab + CSS Grid 卡片讲架构。

## 改脚本前 30 秒

> hook 守的是「Read 过本文件」**不看读了多少行**。改 scripts/build_arch_skeleton.py 用 `Read 此文件 limit=80`（§1+§2 即够）。改产出物建议全文。

**Public API（不可改签名）**：
- `from build_arch_skeleton import generate` — `generate(project, nav, tab_fns, output_path, extra_css='', extra_js='')`
- `project = {"name": str, "subtitle": str (可选)}` · `nav = [(tab_id, label), ...]` · `tab_fns = {tab_id: () -> html_str}`

**会拦你的 hook**：
- `script-syntax-gate` — pyflakes / py_compile
- `cjk-punct` — 全角标点强制（中文文案）
- `skill-load-gate` — 改 `arch-*.html` 必先 Read 本 SKILL.md

**改完跑啥**：
```bash
python3 .claude/skills/architecture-diagrams/scripts/build_arch_skeleton.py && open .claude/skills/architecture-diagrams/scripts/archive/build-arch-demo.html
```

**深入读什么**：组件 HTML 模板 `Read references/components-cheatsheet.md`；SVG 拓扑 `Read references/svg-topology-extension.md`；自检规则 `grep -A 20 "^## 自检清单" SKILL.md`。

## 硬规则（FAIL 即拦）

1. **配色 2 色上限**：同一 Tab 最多 2 种强调色（accent 蓝 + 1 辅助语义色），其余账户/模块用中性灰。`.co-b/-a/-r/-g/-v` 五色 callout 是**跨页色板**，不是同页可并用——同一 Tab 出现 ≥ 3 色 callout 必须改 accent + 灰中性范式
2. **Tab 索引一致**：`sw(i)` 的 `i` 从 0 开始，与 `.pw` 的 `id="tN"` 一一对应；`nav[(tab_id, label), ...]` 顺序锁定 Tab 显示顺序
3. **字体栈**：正文 `'Noto Sans SC','Inter',system-ui,sans-serif`；代码 / 数据 / 地址 `JetBrains Mono`。不混写
4. **Tab 与场景同源**：Tab 数量与 scene-list / 真相源（baseline）模块数一致；Tab 标题用真相源原术语，禁自创
5. **build 模式唯一**：产物用 `build_arch_v{N}.py` orchestrator + `tab_fns` 字典生成，禁直接 Write HTML（> 200 行硬规则）。改单 Tab 只改对应 `tab_fns[id]` 重跑
6. **无占位符**：交付前 grep `待填充|TBD|TODO` 必须为空

## 核心输出规范

- **位置**：`projects/{项目}/deliverables/arch-{项目}-v{N}.html`
- **生成脚本**：`projects/{项目}/scripts/build_arch_v{N}.py`
- **结构**：单文件 HTML / CSS 内联 / JS 内联 / 字体 CDN
- **导航**：粘性 tab bar（`.tb > .t`）+ `.pw` 内容区切换
- **每个 Tab 80-200 行**（超出拆 `scripts/arch_v{N}/tabs/tab_{id}.py`）

### Tab 内典型结构

```html
<div class="pg">
  <h1>标题</h1><div class="sub">副标题</div><div class="rl"></div>
  <div class="sec"><b>区域名</b><span class="sl"></span><em>说明</em></div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
    <div class="cd"><!-- 卡片 --></div>
  </div>
  <table>...</table>
  <div class="co co-g"><strong>总结：</strong>...</div>
</div>
```

### 卡片配色约定（背景 / 边框 / 标题色 / 用途）

| 背景 | 边框 | 标题色 | 用途 |
|------|------|--------|------|
| `#fffbeb` | `#fcd34d` | `#b45309` | 我方 / 核心 / 琥珀 |
| `#eef2ff` | `#a5b4fc` | `#4338ca` | 用户 / 蓝 |
| `#f0fdfa` | `#5eead4` | `#0f766e` | 现有系统（保留） |
| `#ecfeff` | `#22d3ee`(2px) | `#0e7490` | 新建系统 |
| `#f5f3ff` | `#c4b5fd` | `#6d28d9` | 链上 / 紫 |
| `#f0fdf4` | `#86efac` | `#15803d` | 成功 / 绿 |
| `#fef2f2` | `#fca5a5` | `#b91c1c` | 风险 / 红 |
| `#f8fafc` | `#e2e8f0` | `#64748b` | 中性 / 灰 |

## 执行步骤

### Step 0：方案信息确认

向用户确认：① 方案名称（标题）② Tab 数 + 每个 Tab 主题 ③ 每个 Tab 模块清单 ④ 是否需要数据可视化（表格 / 对比卡 / 步骤流 / 时序泳道）。

> ⚡ **快速模式**：用户说「快速生成 / 一口气出 / 不用确认」时，所有 Tab 连续生成，只在全部完成后停。未激活时每个 Tab 完成等确认。

### Step 1：必读规则

```
view .claude/runbooks/html-pipeline.md         # 演讲叙事 / 分步生成 / 美学硬底线
view .claude/skills/_shared/claude-design/anti-ai-slop.md  # 按需 grep「决策速查」段
```

### Step 1：build 模式生成

简单产物（≤ 8 Tab）：复制 `build_arch_skeleton.py` 到 `projects/{项目}/scripts/build_arch_v{N}.py`，填 `project / nav / tab_fns / OUTPUT`，一键 `python3` 即出完整 HTML。

大产物（> 8 Tab 或 > 1500 行）：拆 `scripts/arch_v{N}/tabs/tab_{id}.py`，orchestrator 用 `__import__` 集中收口（模式见 `runbooks/html-build-split.md §一档B / §二 Python 轨` + 冻结样板 `.claude/skills/interaction-map/assets/example-split/`）。

**最小可运行骨架**：
```python
import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/architecture-diagrams/scripts'))
from build_arch_skeleton import generate

project = {"name": "方案 X", "subtitle": "技术架构"}
nav = [('0', '一页全景'), ('1', '账户结构'), ('2', '资金流')]

def tab0(): return '<div class="pg">...</div>'
# tab1 / tab2 ...

tab_fns = {'0': tab0, '1': tab1, '2': tab2}
generate(project, nav, tab_fns, 'projects/{项目}/deliverables/arch-{项目}-v{N}.html')
```

### Step 2：单 Tab 重跑迭代

改 `tab_fns[id]` 函数体 → 重跑 build → 浏览器检阅。`grep` 定位 Tab 块直接局部改即可。

**老项目反向拆分**（fill 模式遗留 / 手写 HTML）：写一次性 `_extract_arch_v{N}.py` 切每个 `.pw` 块到 `tabs/tab_{id}.py`，验证 build 重跑等价后 archive 老 gen 脚本。流程见 `runbooks/html-build-split.md §四 反向拆分方法`。

## API 速查

### 组件 class（详见 references/components-cheatsheet.md）

| 组件 | 关键 class / 结构 | 用途 |
|------|------------------|------|
| Tab 导航 | `.tb > .t` + `.pw > .pg` | 粘性 tab bar，JS `sw(i)` 切换 |
| CSS Grid 卡片 | `display:grid` + `.cd` | 2-5 列等宽 / 比例布局 |
| Flex 行 | `.fx > .cd` | 等宽对比、流程箭头 |
| Callout | `.co.co-b/-a/-r/-g/-v` | 蓝 / 琥 / 红 / 绿 / 紫提示框 |
| 表格 | `<table>` 蓝色 `<th>` + zebra | 数据对比 / 参数清单 |
| Section 线 | `.sec > <b> + .sl + <em>` | 区域分隔 |
| 步骤编号 | `.sn.sn-b/-g/-r` | 蓝 / 绿 / 红编号圆圈 |
| Tag 标签 | `.tg.tg-k/-n/-w/-c/-p` | 保留 / 新建 / 复用 / 关键 / Phase |
| 地址高亮 | `.addr` | 链上地址 monospace |
| 图例 | `.leg > .leg-i > .leg-s` | 颜色图例说明 |

### generate() 签名

```python
generate(project: dict, nav: list, tab_fns: dict, output_path: str,
         extra_css: str = '', extra_js: str = '')
```
- 第一个 nav 项默认 active
- `tab_fns` 缺 nav 中的 id 会 raise KeyError

## 自检清单

- [ ] Tab 数量与真相源（baseline）/ scene-list.md 模块数一致
- [ ] Tab 标题与真相源术语一字不差
- [ ] 同一 Tab ≤ 2 强调色（accent + 1 辅助语义色）
- [ ] 字体栈：正文 `'Noto Sans SC','Inter',system-ui,sans-serif`，代码 `JetBrains Mono`
- [ ] 配色全部用 css-template.css 语义色，无硬编码冲突
- [ ] 表格列宽合理，无溢出截断
- [ ] 无占位符（`待填充` / `TBD` / `TODO`）残留
- [ ] 生成脚本存入 `projects/{项目}/scripts/build_arch_v{N}.py`，与产物成对交付
- [ ] SVG 拓扑图（若有）节点可点击、箭头方向正确

## References 索引

- `references/components-cheatsheet.md` — CSS Grid 卡片组件全模板（步骤流转 / 数据可视化 / SVG 箭头 / 产品图标 / 常用卡片模板）。Step 1 生成具体 Tab 内容时按需 Read
- `references/svg-topology-extension.md` — SVG 拓扑图（节点 + 箭头连线）。仅当用户明确要画拓扑图时 Read，**大部分方案不需要**
