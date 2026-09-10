---
name: flowchart
description: >
  「流程图 / 泳道图 / 审批流 / 状态机」触发。输出 .svg + .png 供 PRD / IMAP / PPT / 架构图 `<img>` 引用。
argument-hint: [主题 或 data 文件]
type: standalone
output_format: .svg + .png
output_prefix: flow-
depends_on: []
optional_inputs: [baseline]
consumed_by: []
scripts:
  gen_flow_base.py: "mermaid 单引擎生成器 — from gen_flow_base import render_flowchart"
---

# Flowchart 流程图（mermaid 单引擎）

## 触发与定位

独立产出型 Skill。把业务流程 / 审批流 / 状态机 / 因果链路可视化，输出矢量 SVG + 位图 PNG。

按 chart `type` 自动选图型（引擎只有一个：mermaid，走 mmdc 落地）：

| type | mermaid 图型 | 适用场景 |
|---|---|---|
| `branch` | `flowchart TB` | 单角色 DAG、决策分支、触点路径 |
| `swimlane` | `swimlane-beta TB` | 多角色泳道、跨角色交接（顶层 subgraph = 一条泳道）|
| `state` | `stateDiagram-v2` | 状态机、生命周期（回路 / 多源汇聚天然支持）|

**不在范围**：时序图（IMAP 跨端时序）/ 系统架构（architecture-diagrams）/ UI 跳转图（interaction-map）。

## 改脚本前 30 秒

> `skill-load-gate`（pre-writeedit-guard）守的是「Read 过本文件」**不看读了多少行**。
> 改本 skill `scripts/gen_flow_base.py`：`Read 此文件 limit=80` 即可。
> 改产出 `.mmd`：脚本生成的，改项目侧 `gen_flow_v{N}.py` 重跑而非手改源。

**Public API（不可改签名 · 改前看调用方）**：
- `render_flowchart(output_path, title, subtitle, charts)` — 唯一入口；调用方位置 `projects/{产品线}/{项目}/scripts/gen_flow_v{N}.py`
- chart dict schema：`{type, title, nodes/edges | lanes/nodes/edges | states/transitions}` —— 改字段必同步本文件 §核心输出规范

**会拦你的 hook**：
- `script-syntax-gate` — pyflakes（写 .py 自动跑）
- CJK 标点 / 讲人话 hook（写 `.mmd` 自动跑，详见 §自检清单）

**改完跑啥**：
```bash
python3 projects/{产品线}/{项目}/scripts/gen_flow_v{N}.py
# 读产出 PNG 自检重叠 / 截断
```

**深入读什么**：
- 图型决策 / 节点视觉 / 数据结构：`grep -A 60 "^## 核心输出规范" SKILL.md`
- mermaid 语法坑（报错对照表）：`Read references/mermaid-gotchas.md`

## 硬规则（FAIL 即拦）

- **图型按「节点是什么」选，不按「有没有回路」选**：节点 = 状态 / 边 = 触发事件 → `state`；节点 = 动作且多角色 → `swimlane`；节点 = 动作单角色 → `branch`。mermaid 三种图型都支持回路，回路不再是选型依据
- **decision 菱形每条出边必须有 label**（"是" / "否" / "Yes" / "No"），缺 label = 视为未交付
- **失败分支用 `fail`，成功终态用 `success`**——不可混用 `process` 蓝色掩盖语义
- **swimlane 每个节点必须落在已声明的 lane 里**：没挂 lane 的节点会被 mermaid 塞进第一条泳道，图上表现为「角色跑错人」
- **label 只走 `_q()` 引号包裹，禁手写裸 label**：引号内 `/` `()` `1.` 等不再触发布局语法（原样显示）；半角 `"` 由 `_q()` 换单引号，禁在 label 里写 `\"`（mermaid 不支持转义，直接 parse 失败）
- **`state` 的边 label 例外，禁加引号**——mermaid 不脱那里的引号，会原文渲染成 `"业务系统同步入库"`
- **CJK 全角标点**（hook 自动拦截）：`.mmd` 提节点 / 状态 / 边 label 扫
- **禁裸编号**：图 label 不能出现 `M-1 / A-2 / 决策 N` 等内部锚点（hook check_plain_language 拦截）
- **产出统一前缀 `flow-`**，存 `projects/{项目}/deliverables/`
- **多 chart 时全局 chart index 编号**：`flow-xxx-v1-1.mmd.svg` / `flow-xxx-v1-2.mmd.svg`
- **渲染失败必须抛错修掉，不接受「图没出但脚本过了」**：mmdc 找不到 Chromium / parse 失败都会 `RuntimeError`，看报错改数据，别绕过

## 核心输出规范

### 产物文件

每个 chart 产 2 个图像 + 1 个源文件（**单图不带序号，多图带**）：

- `flow-xxx-v1{,-N}.mmd` — 可编辑源
- `flow-xxx-v1{,-N}.mmd.svg` — 矢量，`<img>` 嵌 HTML / IMAP / PPT（本工区流程 / 状态图 SVG 是真 `<text>`，非 foreignObject）
- `flow-xxx-v1{,-N}.mmd.png` — 位图，PRD 嵌图 + Confluence 上传走这个

### 节点类型 + 视觉

| type | mermaid 形状 | fill / stroke | 用途 |
|------|------|-----------|------|
| `terminal` | 胶囊 `([...])` | `#E8E5FF` 紫 / `#1F2329` | 起点 / 终点 |
| `process`  | 矩形 `[...]` | `#E7EFFE` 蓝 / `#1F2329` | 处理 / 操作 |
| `decision` | 菱形 `{...}` | `#FDF3D5` 黄 / `#1F2329` | 判定（Yes/No 分支） |
| `success`  | 矩形 `[...]` | `#D9F5E5` 绿 / `#0ECB81` 绿描边 | 成功终态 |
| `fail`     | 矩形 `[...]` | `#FEE3E6` 红 / `#F6465D` 红描边 | 失败 / 拦截 |

状态机 `kind` 用同一套语义色：`active` 绿 / `terminal` 紫 / `rejected` 红。字体 PingFang SC / Noto Sans SC，字号 15px，标签超宽自动换行（`wrappingWidth: 220`）。

### 数据结构

#### 分支流程（branch）

```python
{
    "type": "branch",
    "title": "QI 认证分支",
    "nodes": [
        {"id": "Q1", "type": "decision", "label": "QI 已认证？"},
        {"id": "AUTH", "type": "fail", "label": "拦截 + 引导"},
        {"id": "DONE", "type": "success", "label": "进入认购"},
    ],
    "edges": [
        {"s": "Q1", "t": "AUTH", "label": "否"},
        {"s": "Q1", "t": "DONE", "label": "是"},
    ],
}
```

`id` 禁空格 / 特殊字符；布局交给 dagre，不用算坐标。

#### 泳道流程（swimlane）

```python
{
    "type": "swimlane",
    "title": "赎回全链路",
    "lanes": ["投资人", "运营", "风控"],
    "nodes": [
        {"id": "I1", "lane": "投资人", "col": 0, "type": "terminal", "label": "发起赎回"},
        {"id": "R1", "lane": "风控",   "col": 0, "type": "decision", "label": "合规？"},
    ],
    "edges": [
        {"s": "I1", "t": "O1"},
        {"s": "R1", "t": "X1", "label": "否"},
    ],
}
```

字段：`lane` 必出现在 `lanes` 列表；`col` = 泳道内左右次序偏好（0-indexed，按 col 排序后声明）；跨泳道边正常连，`sp` / `tp` 端口字段已废弃、传了不读。

#### 状态机（state）

```python
{
    "type": "state",
    "title": "活动生命周期",
    "states": [
        {"id": "s1", "label": "待补全"},
        {"id": "s3", "label": "已上线", "kind": "active"},     # 强调态
        {"id": "s5", "label": "已结束", "kind": "terminal"},   # 普通终态
        {"id": "s6", "label": "已删除", "kind": "rejected"},   # 异常终态
    ],
    "transitions": [
        {"from": "[*]", "to": "s1", "label": "业务系统同步入库"},
        {"from": "s3", "to": "s1", "label": "退回字段不达标"},   # 回路天然支持
    ],
}
```

字段：`id` 禁空格 / 特殊字符；`kind` ∈ {active / terminal / rejected}；`[*]` 表起点 / 终点。

## 执行步骤

### Step 1：读必要文件

**必读**：本 SKILL.md + `scripts/gen_flow_base.py`（API）。
**按需**：用户原始流程描述（baseline / 会议纪要 / 截图）；报错时 `references/mermaid-gotchas.md`。

### Step 2：梳理数据

先把流程问清楚再画：**节点是状态还是动作？几个角色？有没有回路？**

- 节点 = 状态、边 = 触发事件 → `state`
- 节点 = 动作、跨多个角色 → `swimlane`
- 节点 = 动作、单角色一条链 → `branch`

检查清单：
- 节点 type 是否准确（尤其别拿 `process` 掩盖失败分支）
- 决策菱形每条出边 label 是否齐
- swimlane 是否每个节点都填了 `lane`
- 泳道顺序是否按业务交接顺序排（第一条在最左）

### Step 3：写项目侧 gen 脚本

`projects/{产品线}/{项目}/scripts/gen_flow_v{N}.py`：

```python
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[4]  # 两级产品线 + 项目
sys.path.insert(0, str(BASE / ".claude/skills/flowchart/scripts"))
from gen_flow_base import render_flowchart

CHARTS = [
    {"type": "branch", "title": "...", "nodes": [...], "edges": [...]},
]

render_flowchart(
    output_path=str(Path(__file__).parents[1] / "deliverables/flow-xxx-v1"),
    title="流程图 · XXX",
    subtitle="...",
    charts=CHARTS,
)
```

### Step 4：执行

```bash
python3 projects/{产品线}/{项目}/scripts/gen_flow_v1.py
```

渲染失败会直接抛 `RuntimeError`（mmdc 缺失 / Chromium 找不到 / mermaid parse error 三类），按报错修数据再跑。

### Step 5：读图自检（必做）

**必须 Read 产出的 PNG**（多模态看一眼），逐条核对：

1. 有没有文字压线 / 压在箭头上
2. 有没有节点溢出画布、被裁掉
3. 决策菱形出边 label 是否都贴着对应箭头
4. 泳道图里角色有没有串道
5. 长 label 换行是否正常（没被截断成半句）

发现重叠 → 回 Step 2 改数据（拆长 label、加中间节点、调整泳道归属），**最多迭代 3 轮**；3 轮仍在同一处重叠就换更省地方的图型（如 `swimlane` 换 `branch`），别硬调。

## API 速查

```python
from gen_flow_base import render_flowchart
```

| 参数 | 说明 |
|---|---|
| `output_path` | 路径 base，扩展名会被剥离；`deliverables/flow-xxx-v1` |
| `title` | 图题，engine 层不渲染，用于日志 |
| `subtitle` | 副标题，同上 |
| `charts` | `list[dict]`，每条 `type` ∈ {branch, swimlane, state} |

`_q(text)` — label 引号包裹 + 双引号换单引号 + `\n` 转 `<br/>`。

环境依赖：
- `mmdc`（`npm i -g @mermaid-js/mermaid-cli`），**≥ 11.16**——`swimlane-beta` 图型需要
- Chromium 由 `_find_chromium()` 自动探测：`PUPPETEER_EXECUTABLE_PATH` → Playwright 缓存 → puppeteer 缓存 → 系统 Chrome

## 自检清单

- [ ] **PNG 已 Read 目视**：无文字 / 边重叠，无截断（Step 5 五项逐条过）
- [ ] 所有 decision 节点每条出边都有 label
- [ ] `fail` 红 / `success` 绿，语义没有用 `process` 蓝糊过去
- [ ] swimlane 每个节点都有 `lane`，且 lane 顺序符合业务交接顺序
- [ ] 脚本存 `projects/{项目}/scripts/gen_flow_v{N}.py`
- [ ] 输出存 `projects/{项目}/deliverables/`，前缀 `flow-`
- [ ] `python3 scripts/check_cjk_punct.py projects/{项目}/deliverables/flow-*.mmd --strict` 通过
- [ ] `python3 scripts/check_plain_language.py projects/{项目}/deliverables/flow-*.mmd --strict` 通过（防裸编号）

## References 索引

| 文件 | 何时读 |
|---|---|
| `.claude/skills/flowchart/references/mermaid-gotchas.md` | mermaid parse error / 图渲染异常 / label 显示不对时对照排查 |

## 下游消费

- **PRD md 嵌图**：`![alt](./assets/flow-xxx-v1-N.mmd.png)`（Confluence 上传走 PNG）
- **IMAP / PPT / 架构图**：`<img src="flow-xxx-v1-N.mmd.svg">`（矢量缩放无损）
- **改图**：改项目侧 `gen_flow_v{N}.py` 重跑，不手改 `.mmd`

## 失败恢复

| 现象 | 原因 | 处理 |
|------|------|------|
| `RuntimeError: 找不到 mmdc 可用的 Chromium` | mmdc 不自带浏览器 | `npx puppeteer browsers install chrome-headless-shell`，或 `export PUPPETEER_EXECUTABLE_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'` |
| `mmdc 渲染 svg 失败` + parse error | label 里出现裸 `"` 或未走 `_q()` | 对照 `references/mermaid-gotchas.md` 报错表 |
| `swimlane-beta` 报图型未知 | mmdc / mermaid < 11.16 | 升级 mermaid-cli |
| 泳道标题在 SVG 里空白、节点正常 | mermaid 的 subgraph 标题固定走 foreignObject，不受 `htmlLabels: false` 管 | 非浏览器场景（Inkscape / 印刷）用 PNG；浏览器嵌 SVG 不受影响 |
| 节点被塞进第一条泳道 | 该节点没填 `lane` | 补 `lane` 字段 |
| 长 label 挤成一条横杠 | 单行过长、换行点太少 | label 里用 `\n` 显式断行，或拆成两个节点 |
