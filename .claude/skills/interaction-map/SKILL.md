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
optional_inputs: [architecture-diagrams]
consumed_by: [prototype, prd]
owns: [跳转骨架-aw箭头, 代表态phone-mockup, 跨场景动线-锚点, UI决策点-ann-card]
forbids: [字段表, 状态全集列举, 池策略参数, 埋点事件名, 完整文案表]
scripts:
  build_imap_skeleton.py: "Step 1 单步生成 — from build_imap_skeleton import generate"
  check_imap.sh: "Step 2 综合自检（结构 + 文案讲人话）— bash .claude/skills/interaction-map/scripts/check_imap.sh <html> [<scene-list.md>]"
  _validators.py: "IMAP 结构校验函数（validate_part_stories）— from _validators import validate_part_stories"
  check_imap_split.py: "src/scenes 分场景拆分门（imap-split-gate hook 调用）— python3 .claude/skills/interaction-map/scripts/check_imap_split.py <html>..."
---

# 交互大图 Skill（Interaction Map）

## 触发与定位

**做什么**：横向 Flow + 双端 Mockup 单页 HTML，展示场景间跳转、UI 状态、注解说明。给 leader / 评审 / 协作方看的**轻可视化 + 叙事链**——phone mockup 演故事 + 箭头串跳转 + ann-card 标 UI 决策点。

**何时触发**：scene-list 确认后视觉化阶段自动接续；用户说「交互大图 / IMAP / 交互流程图」。

**不做**：变更叙事（归 PRD 1.3）/ 高保真原型（归 prototype）/ 技术架构（归 architecture-diagrams）。**IMAP 是静态新态全景，迭代项目也画新态**。

**不持有**：字段口径 / 状态全集 / 池策略参数 / 埋点事件名 / 完整文案表 — 见 `.claude/runbooks/info-ownership.md` §A.1。违反 = `check_imap.sh` FAIL（ann-card 四禁，硬规则 10）。

## 改脚本前 30 秒

> hook 守的是「Read 过本文件」**不看读了多少行**。改 scripts/build_imap_skeleton.py / _validators.py / check_imap.sh 用 `Read 此文件 limit=80`（§1+§2 即够）。改产出物建议全文。

**Public API（不可改签名）**：
- `from build_imap_skeleton import generate` — `generate(project, legends, parts, scene_fns, output_path)`
- `from _validators import validate_part_stories` — build 时自动调用
- `bash check_imap.sh <html> [<scene-list.md>]` — Step 2 自检入口

**会拦你的 hook**：
- `script-syntax-gate` — pyflakes / py_compile / bash -n
- `cjk-punct` — 全角标点强制
- `skill-load-gate` — 改 `imap-*.html` / `interaction-*.html` 必先 Read 本 SKILL.md
- `deliverable-source-gate` — 禁直接 Edit/Write IMAP HTML，必须走 build 脚本
- `imap-split-gate` — imap-*.html 产出时校验 src/scenes 已拆分（找不到即 FAIL）
- `ui-annotation-gate` — `.phone` / `.webframe` 屏内禁开发注解（注解只能进 mockup 外的 ann-card / flow-note）；build 后 Bash 路径拦截

**改完跑啥**：
```bash
python3 .claude/skills/interaction-map/scripts/build_imap_skeleton.py  # demo 自跑
bash .claude/skills/interaction-map/scripts/check_imap.sh deliverables/imap-*.html
```

**深入读什么**：完整 parts 结构 `grep -A 30 "^## API 速查" SKILL.md`；自检规则 `grep -A 25 "^## 自检清单" SKILL.md`；组件 HTML `Read references/templates-quickref.md`。

## 硬规则（FAIL 即拦）

1. **主场景粒度**：IMAP scene 对齐 scene-list **主场景**（A/B/C/M/F/G 一级编号），严禁把子场景（A-1/A-2）升为独立 scene。子场景降为主场景内部的横排手机节点，`.phone-label` 写子场景编号（如 `A-1 · 首页 Feed`），子场景间用 `.aw` 箭头连接。跨 skill 编号契约不变：PRD / prototype 章节仍用子场景编号
2. **`.anno` overlay 仅作 ann-card 锚点**：`.anno` / `.anno-n` 虚线框 + 编号徽章必须与下方 `.scene-anno` 区 ann-card 的 `.ann-num` 一一对应（1↔1, 2↔2）。该编号**驱动 hover 联动**（移到屏幕徽章 `2` → 卡内条目 `2` 高亮，反之亦然）——对应不上则联动静默失效。**禁止**用它做改动标注（圈"改动 / 新增"）或单独存在（让手机看起来全是虚线框）
3. **零改动叙事**：禁 `ann-tag.new/chg/del`（仅保留 `.p0/.p1/.p2`）；禁 `V\d+\.\d+`、`NEW`、`变更`、`新增`、`改动` 文案。变更归 PRD 1.3
4. **anno-n 与 ann-num 字符样式一致**：屏幕徽章和 ann-card 编号要么都阿拉伯数字 `1 2 3`，要么都圆圈数字 `① ② ③`，不能混用。**默认建议阿拉伯数字**（跟跨端表 / 漏斗序号一致）。规则 2 对应 + 本条字符一致由 `check_imap.sh §10` 自动校验（混用 / 死链即 FAIL）
5. **跨场景引用零死链**：禁 `详见 X-N` / `→ 见 X-N` 纯文字占位。合法两路：① `<a href="#scene-x">查看完整 → X ↗</a>`（骨架 `fade-section` 已带 `id="scene-{x}"`）② 占位区画 2-3 行结构化迷你缩略
6. **叙事主线唯一源**：`parts[].story` 必须是 scene-list 顶部 `叙事主线：xxx` 一行的子串（≤ 30 字）。规则系统型项目可填 `"—"` 显式跳过。脱钩 → `validate_part_stories_from_scene_list` build 时报错；缺主线行 → 降级仅校验非空 + warn
7. **正文讲人话**：编号锚点（`.st > h2` / `.phone-label` / `id` 属性 / 锚点 href / 侧导航编号）合法；但 `.flow-note` / `.ann-text` / `.ann-card .card-title` / `.aw .tx` / `.part-story` / `.gd-desc` 正文位置禁裸编号（`触发 A-1 进入 B`）和决策号（`见决策 3` / `参考决策章 #2`）。规则源头 `.claude/runbooks/human-voice-rules.md`
8. **build 模式唯一**：改 HTML = 改 `scene_fns[id]` 函数体 + 重跑 build，禁 Edit/Write 直改 HTML（hook 阻断）
9. **业务组件复用**：交易卡片 / Feed 极简卡 / 帖子列表 / $币种胶囊 / 半屏交易抽屉 / 直播间卡片 / CMS 表格 必须从对应 `biz-*.md` 复制 HTML 结构，只替换占位内容，不改 HTML / CSS
10. **ann-card 四禁**（违一条 → `check_imap.sh` FAIL）：
    - **a) 禁字段表**：ann-card 内禁 ≥ 2 列 ≥ 3 行 HTML `<table>`；字段引用统一 `<span class="ref">→ PRD §3.2「{对象}.{字段中文名}」</span>`。例外：IMAP `.cross-grid` 跨端数据流 6 列表（不在 ann-card 内）合法
    - **b) 禁状态全集列举**：同页面多状态只画 1 代表态，其余写 `<span class="ref">→ 原型「{view}-{page}」状态全集</span>`，prototype 用 state-chip 承载
    - **c) 禁池策略参数**：禁出现 `Top \d+` / `\d+d 收益率` / `近 \d+ 天` / 权重数；池策略引用 `<span class="ref">→ baseline §全局规则「{规则名}」</span>`
    - **d) 禁埋点事件名**：ann-card 禁出现 snake_case 形如 `[a-z]+_[a-z_]+` 的事件名 / 属性 key（CSS class / id 例外）；引用 `<span class="ref">→ PRD §9「{event 中文名}」</span>`
    - 字数 ≤ 80 字 = WARN（不阻断），ann-item ≤ 5 = FAIL
11. **src/scenes 分场景拆分（强制）**：每个 IMAP 一律拆 `projects/{项目}/scripts/src/scenes/{scene_id}.py` 一文件一主场景（≤ 300 行），由 `build_imap_v{N}.py` orchestrator import 收口成 `scene_fns`。**禁止把 scene_fns 内联在 orchestrator 单文件里**（不分简单 / 大产物，无条件）。`imap-split-gate` hook 在 imap-*.html 产出时校验，找不到任何 `src/scenes/*.py` 即 FAIL。结构见 `.claude/runbooks/html-build-split.md §二`
12. **手机/Web 屏内禁注解**：注解是 IMAP 一等功能，但只能落 mockup **外**的 `.ann-card` / `.flow-note`。`.phone` / `.webframe` 屏内禁写开发注解——`（动态加载）` / `（此处占位）` / `（接口返回）` / `注：` / `TODO` 这类括注混进手机屏，开发会误读为真实产品文案。屏内只放真实文案，注解移到旁注区。`ui-annotation-gate` hook 在 build 后拦截（只扫 mockup 内部，旁注区合法）

## 核心输出规范

- **位置**：imap 是 **delta-scoped 产物，不做 living base 版**，scoped 到本轮变更场景，随 delta 包落 `projects/{产品线}/deliverables/{季度}/{版本}/imap-{产品线}-{版本}.html`（版本 = delta 版本，如 2.2），随 delta 整包归 `archive/{季度}/`。
- **生成脚本**：与产物同目录 delta 包内 `scripts/build_imap_{版本}.py`
- **结构**：单文件 HTML / CSS / JS 全内联（字体 CDN 除外）。`interaction-map.css` / `interaction-map.js` 由 `build_imap_skeleton.py` 通过 `open().read()` 自动内联
- **布局**：`.flow` 容器（横向滚动）→ 多个 `.flow-col` 屏幕（= 主场景下的子场景）→ 屏幕间 `.aw` 箭头。注解卡 `.ann-card` **下沉到 `.flow` 下方 `.scene-anno` 区**（同属该 scene，竖向自然滚动可达；不再钉在横向流最右端）。屏幕徽章 `.anno-n` 与卡内同号 `.ann-item` hover 互亮，靠编号维持「元素 ↔ 注解」关联
- **分组**：`.gd` 分隔符按 PART 0/1/2/3 划分产品模块
- **响应式**：侧导航 1400px+ 显示，内容区水平滚动

### device → 设备壳映射

每个 Scene 的 `device` 字段决定设备壳类型，同一 PART 下可混合：

| device 值 | 设备壳 | 典型场景 |
|-----------|--------|---------|
| `phone`（默认） | `.phone`（375 × 812px 深色） | App 端 |
| `web` | `.webframe`（720px+ 浅色） | Web 前台 / 后台 CMS / 管理台 |

> **theme vs device**：theme 控制 PART 分隔条样式（深灰 / 蓝 / 绿），device 控制 Scene 内的设备壳类型。两者独立。

### 必需组件清单（每个主场景 scene_fn）

| # | 组件 | class | 必需性 |
|---|------|-------|--------|
| 1 | 屏幕（子场景手机） | `.phone` 或 `.webframe` | **必需多个**（= 子场景数）|
| 2 | 屏幕标签 | `.phone-label` | **必需**（写 `{编号} · {业务白话}`）|
| 3 | 箭头 | `.aw > .al + .tx` | **必需**（子场景间连接）|
| 4 | 屏幕说明 | `.flow-note` | **必需**（主注解载体）|
| 5 | 注释卡 | `.ann-card`（含 `.card-title` + `.ann-item > .ann-num + .ann-text`）| 可选（复杂 scene 经 dict `anno` 字段下沉到 `.scene-anno` 区）|
| 6 | 优先级标签 | `.ann-tag.{p0/p1/p2}` | 可选 |
| 7 | 信息框 | `.info-box.{色}` | 可选 |

> ann-card 不是只写外壳 + ann-num，必须包含完整子结构。`.ann-tag` 仅限 `p0/p1/p2`。手机内部视觉还原密度按场景复杂度自行拿捏，不设行数硬上限。

### build 骨架 vs scene_fns 边界

- **build 骨架提供**：`.fade-section` 容器 + `.st` 标题行（Scene 编号 + 名称 + 触发）+ `.flow` 容器 + `.flow` 下方 `.scene-anno` 注解区 + 注入 hover 联动 JS。**不生成设备壳 / 占位 / 箭头 / 注解内容**
- **scene_fns 函数提供**，返回值二选一：
  - **纯字符串**（多数 scene，无注解）= `.flow` 内部 HTML：`.flow-col` + `.phone/.webframe` + `.aw` 箭头（含 `.al + .tx`）+ `.flow-note` + `.phone-label`
  - **dict `{'flow': ..., 'anno': ...}`**（带注解的复杂 scene）：`flow` 同上手机流（屏幕内嵌 `.anno`/`.anno-n` 编号锚点）；`anno` = 一张或多张 `.ann-card`，由骨架渲染到 `.flow` 下方 `.scene-anno` 区

## 执行步骤

> 通用规则（强制规则 / 快速模式 / 通用自检）见 `.claude/runbooks/html-pipeline.md`。本节为 IMAP 补充。

### Step 0：回读 + device 字段确定（核心防倾倒）

并行 Read：
1. scene-list.md（全文，含顶部「叙事主线：xxx」）
2. 真相源（`lib.truth_source.resolve`：baseline）的项目档位 + 主线段（读 baseline §1 概览）
3. `.claude/runbooks/info-ownership.md` §A.3 forbids 列
4. IMAP 上一版（如有）

**显式禁读**真相源的业务规则 / 决策段 / 数据枚举原文（baseline §全局规则 / 决策章）。需要时通过 `→ baseline §全局规则「...」` / `→ PRD §3.2「...」` 占位引用，不读原文。

每个 Scene 的 `device`：
1. scene-list.md 有「设备」列 → 直接读取（📱phone / 🖥web）
2. 老项目无设备列 → **停下逐 Scene 问用户**，禁默认 phone 或推断

写前回读详则 → `.claude/runbooks/artifact-conventions.md §三 上下文防丢`。

### Step 1：写 orchestrator + src/scenes（强制拆分）

**禁止把 scene_fns 内联在 orchestrator 单文件里**（硬规则 11，不分简单 / 大产物）。固定结构：

```
projects/{项目}/scripts/
  build_imap_v{N}.py         # orchestrator（≤ 150 行，只 import scenes/ + 收 scene_fns + 调 generate）
  src/
    config.py                # project / legends / parts 数据
    helpers.py               # 跨场景复用 HTML 片段（可选）
    scenes/
      __init__.py
      {scene_id}.py          # 一文件一主场景 ≤ 300 行；def scene_{id}(): return '''...'''
                             # 跨端表 → cross_data_flow.py，def cross_data_flow()
```

orchestrator 范式：

```python
import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/interaction-map/scripts'))
sys.path.insert(0, os.path.dirname(__file__))  # 让 src 包可 import
from build_imap_skeleton import generate
from src.config import project, legends, parts
from src.scenes.a import scene_a
from src.scenes.b import scene_b

scene_fns = {'scene-a': scene_a, 'scene-b': scene_b}
generate(project, legends, parts, scene_fns, 'projects/{项目}/deliverables/imap-...html')
```

CSS / JS 不进源码树，由 `build_imap_skeleton.py` 通过 `open().read()` 自动内联。

**复用项目已有素材工厂**：项目已有 `src/`（prototype 先建）时，先看 `src/` 根有无 `icons.py` 等素材工厂——有则 IMAP scene_fn 直接 `from ..icons import ic, cover` 复用 SVG，不重画。约定见 `.claude/runbooks/html-build-split.md §二 项目级 src/ 跨 skill 共享`。

**scene_fn 规模**：
- 每个 scene_fn ≤ 80 行 HTML（含 return 三引号字符串）；超过拆子函数
- 每个 `src/scenes/{id}.py` ≤ 300 行
- HTML 字符串统一 Python 三引号 `'''...'''`，属性双引号 `""`，禁 heredoc（`python3 - << 'PYEOF'` 引号冲突风险高）；中文注释入函数 docstring，不入 return 字符串

**分步节奏**：每填完 1-3 个 Scene 往 src/scenes 加文件 + 在 orchestrator 注册 + 跑一次 build 验证，停下报告进度（非快速模式）。可幂等重跑，无 FILL marker。

### Step 2：自检 + check_imap.sh

```bash
bash .claude/skills/interaction-map/scripts/check_imap.sh projects/{项目}/deliverables/imap-...html
```

输出三层：① 结构 FAIL（行数 / 闭合 / 字体顺序 / 占位 / 编号缺失 / 组件缺失）必须修 ② 文案 FAIL（裸编号 / 决策号 / context 引用）必须修 ③ warn（描述当前态四禁）不阻断但整改。scene-list 自动从项目目录推断。

### Step 3：版本与归档

- imap 随 delta 包命名 / 归档，**版本 = delta 版本**（如 2.2），无独立 `v{N}` 快照阶梯：本轮 delta 上线反向合并后，整季度 / 版本文件夹（含 imap）归 `archive/{季度}/`。
- 改 scene_fns / src/scenes 后重跑 build 覆盖本版 imap；历史版本随旧 delta 包已在 archive，git blame + git log 提供完整变更溯源。
- 无 patch 脚本。

### Step 4：触发下游截图同步（仅当项目已有 PRD）

改 ann-card 后 PRD freshness manifest 失效，跑：

```bash
python3 .claude/skills/prd/scripts/screenshot_for_prd.py \
  --imap projects/{项目}/deliverables/imap-*.html \
  -o projects/{项目}/deliverables/assets/
```

## API 速查

### generate() 签名

| 参数 | 类型 | 说明 |
|------|------|------|
| `project` | `dict` | `{"name": "产品名", "subtitle": "交互大图 v1.0", "nav_desc": "用户端 → 管理台"}` |
| `legends` | `list[dict]` | `[{"color": "blue", "label": "布局"}, {"color": "green", "label": "新增"}, ...]` |
| `parts` | `list[dict]` | 见下方结构 |
| `scene_fns` | `dict[str, callable]` | key = `scene-{id.lower()}` 或 `cross-data-flow`；value = 无参函数返回 `html_str`（仅手机流）或 `{'flow':.., 'anno':..}`（anno = 下沉到 `.scene-anno` 区的 ann-card）|
| `output_path` | `str` | 输出路径 |

**parts 结构**：
```python
{
    "id": "part0",              # 锚点 id
    "num": "PART 0",            # 显示编号
    "name": "用户端核心交互",      # 模块名
    "desc": "App 端用户交互流程",
    "story": "用户从 Feed 看见好友战绩，被吸引点进个人主页",  # 必填，≤ 30 字
                                # 同源：scene-list 顶部叙事主线 → 此字段
                                # 规则系统型 / 技术骨架 / 数据流 PART 可填 "—" 跳过
                                # 缺字段或脱钩 → build 报错
    "theme": "frontend",        # frontend | admin | cross-end | custom
    "dot_color": "amber",       # 侧导航圆点颜色
    "scenes": [
        {"id": "A", "name": "首页", "trigger": "启动 App", "device": "phone"},
        {"id": "A-1", "name": "Web 交易", "trigger": "浏览器访问", "device": "web"},
    ],
    # scene.device: "phone"（默认）| "web" — 决定 scene_fn 应生成的设备壳
    # custom 主题需额外字段：bg, color, num_bg
    # 跨端 PART 可选："cross_table": True → 需在 scene_fns 提供 "cross-data-flow"
}
```

### 设计系统速查

| 变量 | 值 | 用途 |
|------|------|------|
| `--blue` | `#2979FF` | 布局改动 / 主操作 |
| `--green` | `#0ECB81` | 新增 / 正向 |
| `--red` | `#F6465D` | 重要 / 删除 |
| `--purple` | `#8b5cf6` | Web 端标识 |
| `--amber` | `#d97706` | 流程 / 链路 |
| `--dark` | `#0B0E11` | Phone 背景 |
| `--surface` | `#fff` | Web Frame 背景 |

| 组件 | 尺寸 |
|------|------|
| Phone | 375 × 812px（iPhone 15 Pro 模拟）|
| Web Frame | 480-960px 宽 |
| Arrow (.aw) | 80px 宽 |
| Annotation Card | 320px 宽 |

| PART theme | class | 适用 |
|------|-------|------|
| 深色 | `.gd.viewer` | App 用户端 |
| 蓝色 | `.gd.host` | Web 管理端 |
| 绿色 | `.gd.cross` | 跨端衔接 |
| 自定义 | inline style | 特殊模块 |

### 自检 grep 速查

```bash
# anno-n 与 ann-num 对应 + 字符一致：已由 check_imap.sh §10 自动校验（规则 2/4，FAIL 即拦）
# 手动复核两组字符集（应相同）：
grep -onE 'anno-n [a-z]+">[^<]+</div>' deliverables/imap-*.html | grep -oE '">[^<]+</' | sort -u
grep -onE 'ann-num [a-z]+">[^<]+</div>' deliverables/imap-*.html | grep -oE '">[^<]+</' | sort -u

# 跨场景死链（应为 0）
grep -nE '详见 [A-Z]-[0-9]|→ 见 [A-Z]-[0-9]|详细交互 → 见' deliverables/imap-*.html

# 改动叙事（应为 0）
grep -cE 'ann-tag (new|chg|del)|V[0-9]+\.[0-9]+|>NEW<|>改动<|>变更<' deliverables/imap-*.html
```

## 自检清单（Step 2 执行）

> 通用条目（编号一致、脚本保存、术语一致）见 `.claude/runbooks/artifact-conventions.md §三 上下文防丢`。

**新规范硬断言**（必须全过）：
- [ ] **主场景粒度**：IMAP scene id 只是主场景，子场景作为手机节点放在主场景内部；`grep -c 'phone-label'` ≥ 手机节点数
- [ ] **anno overlay 合法性**：若使用，每个 `.anno-n` 编号在对应 ann-card 的 `.ann-num` 里有条目（1↔1, 2↔2）
- [ ] **零改动叙事**：`grep -cE 'ann-tag (new|chg|del)|V[0-9]+\.[0-9]+|>NEW<|>改动<|>变更<'` = 0
- [ ] **anno-n 与 ann-num 字符样式一致**：两组 grep 输出字符集相同
- [ ] **跨场景引用零死链**：所有跨 scene 引用必须 `<a href="#scene-x">` 锚点或迷你缩略
- [ ] **同源**：`parts[].story` = scene-list 顶部叙事主线
- [ ] **正文讲人话**：`.flow-note` / `.ann-text` / `.aw .tx` / `.part-story` 无裸编号 / 决策号

**传统条目**：
- [ ] `.phone` / `.webframe` 屏内无开发注解（`（动态加载）`/`注：`/`TODO`），注解只在 mockup 外的 ann-card / flow-note
- [ ] 异常场景已覆盖
- [ ] 箭头零交叉
- [ ] ann-card 内编号（若使用）自洽
- [ ] 侧导航锚点全部可跳转
- [ ] 数据（字段名 / 枚举值 / 状态）全文一致
- [ ] 脚本存入 `projects/{项目}/scripts/build_imap_v{N}.py`，与产物成对交付

**UX 质量检查**（仅 `.phone` 深色 mockup）：
- [ ] 触摸目标：主操作按钮 ≥ 44px，无纯文字链跳转
- [ ] 对比度 + 涨跌色：关键数字 ≥ 4.5:1，次级 ≥ 3:1；涨跌用 ↑↓ / +- 辅助
- [ ] Safe Area + 弹窗：底部 ≥ 34px；弹窗有 ✕ + 遮罩关闭
- [ ] 导航 + 数据状态：Tab ≤ 5；异步区域标注 loading；数字列 JetBrains Mono 右对齐

**强制验证**（自检最后一步，不可跳过）：
```bash
bash .claude/skills/interaction-map/scripts/check_imap.sh projects/{项目}/deliverables/XXX.html
```

## References 索引

### 必读

| 文件 | 触发条件 |
|------|---------|
| `.claude/runbooks/html-pipeline.md` | HTML pipeline 通用规则；演讲叙事顺序见 `artifact-conventions.md §五`，美学硬底线见 `_shared/claude-design/anti-ai-slop.md` |
| `references/templates-quickref.md` | 写 scene_fn 前必读（组件 class / 必填子元素 / 模板行号速查）|
| `references/gold-snippets.md` | 黄金片段，可直接复制修改 |

### 按需读

| 文件 | 触发条件 |
|------|---------|
| `assets/interaction-map-templates.html` | 速查表不够时按行号读局部 |
| `references/components-core.md` | Phone / Web / CMS 通用组件结构不确定（同为 Prototype 共享组件单一信息源，§6 含跨 Skill Token 映射）|
| `references/biz-trading.md` | Scene 含交易卡 / K 线 / 持仓 / 跟单 |
| `references/biz-social.md` | Scene 含 Feed 极简卡 / 帖子 / $币种胶囊 |
| `references/biz-livestream.md` | Scene 含直播间 / OBS / 连麦 / 主播工作台 |
| `scripts/build_imap_skeleton.py` | 扩展 build 生成器本身才读 |

### 美学与主题

- 产出前 grep 决策速查：`grep -A 20 "决策速查" .claude/skills/_shared/claude-design/anti-ai-slop.md`
- Claude Design opt-in 主题：CSS 中 `.theme-cd` 作用域已定义（覆盖默认色板为 Claude Design 深色）；默认不加，需切换时手动在 body 加 `class="theme-cd"`

## 失败恢复

- Write 报错（参数空 / 内容截断）→ 函数拆更小，不重试相同内容
- SyntaxError → `python3 -c "import ast; ast.parse(open('xxx.py').read())"` 定位行号
- build 后 HTML 不符预期 → 改 scene_fn 函数体重跑 build；**禁 Edit/Write 直改 HTML**（hook 阻断）

## 注意事项

1. **ann-card 编号 ↔ anno-n 编号对应**：若使用 anno overlay 做屏幕锚点，每个 `.anno-n` 编号必须在 ann-card 的 `.ann-num` 里有对应条目（1↔1, 2↔2）。这是 anno overlay 合法性的判断依据
2. **phone-label 是跨 skill 编号对齐唯一入口**：`<span class="phone-label">A-1 · 首页 Feed</span>` 让 PRD / prototype 的 A-1 章节能定位到 IMAP scene A 里面的手机节点
3. **跨端表格**：用 `grid-template-columns` 6 列布局（序号 / 起点 / 箭头 / 终点 / 数据 / 触发方式）

