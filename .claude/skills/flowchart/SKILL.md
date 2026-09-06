---
name: flowchart
description: >
  「流程图 / 泳道图 / 审批流 / 状态机」触发。引擎自动选（mermaid / drawio），输出 .svg + .png 供 PRD / IMAP / PPT / 架构图 `<img>` 引用。
argument-hint: [主题 或 data 文件]
type: standalone
output_format: .svg + .png
output_prefix: flow-
depends_on: []
optional_inputs: [baseline]
consumed_by: []
scripts:
  gen_flow_base.py: "双引擎统一生成器 — from gen_flow_base import render_flowchart"
---

# Flowchart 流程图（双引擎：drawio + mermaid）

## 触发与定位

独立产出型 Skill。把业务流程 / 审批流 / 状态机 / 因果链路可视化，输出矢量 SVG + 位图 PNG。

**双引擎自动 dispatch**（按 chart `type` 字段）：

| 引擎 | 触发 type | 适用场景 | 输出文件 |
|---|---|---|---|
| **drawio CLI** | `branch` / `swimlane` | DAG 流程、泳道、决策分支、因果矩阵 | `.drawio` 多 page 源 + `-N.drawio.svg` + `-N.drawio.png` |
| **mermaid (mmdc)** | `state` | 状态机（含回路）、生命周期 | `-N.mmd` 源 + `-N.mmd.svg` + `-N.mmd.png` |

**不在范围**：时序图（用 IMAP 跨端时序）/ 系统架构（用 architecture-diagrams skill）/ UI 跳转图（用 interaction-map skill）。

## 改脚本前 30 秒

> hook `skill-load-gate` 守的是「Read 过本文件」**不看读了多少行**。
> 改本 skill `scripts/gen_flow_base.py`：`Read 此文件 limit=80` 即可。
> 改产出 `.drawio` / `.mmd` 源：脚本生成的，改项目侧 `gen_flow_v{N}.py` 重跑而非手改源。

**Public API（不可改签名 · 改前看调用方）**：
- `render_flowchart(output_path, title, subtitle, charts)` — 唯一入口；调用方位置 `projects/{产品线}/{项目}/scripts/gen_flow_v{N}.py`
- chart dict schema：`{type, title, nodes/states, edges/transitions, lanes?}` —— 改字段必同步本文件 §核心输出规范

**会拦你的 hook**：
- `script-syntax-gate` — pyflakes（写 .py 自动跑）
- CJK 标点 hook（写 `.drawio` / `.mmd` 自动跑，详见 §自检清单）

**改完跑啥**：
```bash
python3 projects/{产品线}/{项目}/scripts/gen_flow_v1.py
# 看 PNG 文字 / 边无重叠
```

**深入读什么**：
- 引擎决策 / 节点视觉 / 数据结构：`grep -A 30 "^## 核心输出规范" SKILL.md`
- drawio CLI 局限 + 手工 ELK 重排：`grep -A 15 "^### Step 5" SKILL.md`

## 硬规则（FAIL 即拦）

- **引擎选型按数据特征**：有「状态」语义就用 `state` → mermaid（不管有无回路）；多角色 / 因果矩阵就用 `swimlane`；单角色 DAG 流程才用 `branch`
- **回路图禁硬塞 branch / swimlane**：mermaid stateDiagram-v2 原生支持回路，drawio BFS 在回路前要么炸要么靠手动 col/row 控
- **decision 菱形每条出边必须有 label**（"是" / "否" / "Yes" / "No"），缺 label = 视为未交付
- **失败分支用 `fail`，成功终态用 `success`**——不可混用 `process` 蓝色掩盖语义
- **swimlane 同 lane 同 col 不重复**（base 会 auto-bump 但建议自己排清楚）
- **label 内禁用半角 `:`**（mermaid 语法分隔符），用全角 `：`，引擎自动转
- **CJK 全角标点**（hook 自动拦截）：`.drawio` 提 `<mxCell value="...">` 内容、`.mmd` 提 state label + 边 label 扫
- **禁裸编号**：图 label 不能出现 `M-1 / A-2 / 决策 N` 等内部锚点（hook check_plain_language 拦截）
- **产出统一前缀 `flow-`**，存 `projects/{项目}/deliverables/`
- **多 chart 时全局 chart index 编号**（无论引擎）：`flow-xxx-v1-1.mmd.png` / `flow-xxx-v1-2.drawio.png`

## 核心输出规范

### 产物文件

每个 chart 产 2 个图像 + 1 个源文件：
- `flow-xxx-v1-N.{engine}.svg` — 矢量，`<img>` 嵌 HTML / PRD md / Confluence
- `flow-xxx-v1-N.{engine}.png` — 位图，docx 嵌入 + 预览
- `flow-xxx-v1.drawio`（drawio 合并多 page）/ `flow-xxx-v1-N.mmd`（mermaid 各自一文件）— 可编辑源

### 节点类型 + 视觉

| type | 形状 | fillColor | strokeColor | 用途 |
|------|------|-----------|-------------|------|
| `terminal` | 圆角矩形 arcSize=40（胶囊） | `#E8E5FF` 紫 | `#1F2329` 黑 | 起点 / 终点 |
| `process`  | 圆角矩形 arcSize=18 | `#E7EFFE` 蓝 | `#1F2329` 黑 | 处理 / 操作 |
| `decision` | 菱形 rhombus | `#FDF3D5` 黄 | `#1F2329` 黑 | 判定（Yes/No 分支） |
| `success`  | 圆角矩形 arcSize=18 | `#D9F5E5` 绿 | `#0ECB81` 绿描边 | 成功终态 |
| `fail`     | 圆角矩形 arcSize=18 | `#FEE3E6` 红 | `#F6465D` 红描边 | 失败 / 拦截 |

字体 PingFang SC / Noto Sans SC。决策菱形 180×80，其他节点 160×60（whiteSpace=wrap 自动撑高）。

### 引擎决策表

设计前问一遍：**节点之间有没有回路？多角色还是单角色？需不需要状态语义？**

| 数据特征 | 选 type | 引擎 |
|---|---|---|
| 节点 = 状态，边 = 触发事件，**有回路** | `state` | mermaid |
| 节点 = 状态，纯单向无回路 | `state` | mermaid |
| 单角色 DAG 流程 ≤ 15 节点 | `branch` | drawio |
| 多角色泳道（≥ 2 lane） | `swimlane` | drawio |
| 因果矩阵（多列动作 × 多层响应） | `swimlane` | drawio |

### 数据结构

#### 状态机（state，mermaid）

```python
{
    "type": "state",
    "title": "活动生命周期状态机",
    "states": [
        {"id": "s1", "label": "待补全"},
        {"id": "s3", "label": "已上线", "kind": "active"},     # 强调态
        {"id": "s5", "label": "已结束", "kind": "terminal"},   # 普通终态
        {"id": "s6", "label": "已删除", "kind": "rejected"},   # 异常终态
    ],
    "transitions": [
        {"from": "[*]", "to": "s1", "label": "业务系统同步入库"},
        {"from": "s2", "to": "s1", "label": "退回字段不达标"},   # 回路天然支持
    ],
}
```

字段：`id` 禁空格 / 特殊字符；`kind` ∈ {active 绿 / terminal 紫 / rejected 红}；`[*]` 表起点 / 终点。布局自动（dagre / ELK），回路 / 多源汇聚 / 扇出无需 col/row。

#### 分支流程（branch，drawio）

```python
{
    "type": "branch",
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

布局：base topo BFS 自动算 col/row，decision 向左右展开。精确控制给 `col` `row` 字段覆盖。

#### 泳道流程（swimlane，drawio）

```python
{
    "type": "swimlane",
    "lanes": ["投资人", "运营", "风控", "基金经理"],
    "nodes": [
        {"id": "I1", "lane": "投资人", "col": 0, "type": "terminal", "label": "发起赎回"},
        {"id": "R1", "lane": "风控",   "col": 2, "type": "decision", "label": "合规？"},
    ],
    "edges": [
        {"s": "I1", "t": "O1"},
        {"s": "R1", "t": "M1", "label": "是", "sp": "top", "tp": "bottom"},
    ],
}
```

字段：`lane` 必出现在 `lanes` 列表；`col` 0-indexed；跨 lane 长跳建议显式 `sp`/`tp` 引导路由。

## 执行步骤

### Step 1：读必要文件

**必读**：本 SKILL.md + `scripts/gen_flow_base.py`（API）。
**按需**：用户原始流程描述（baseline / 会议纪要 / 截图）。

### Step 2：梳理数据

把流程整理成 `nodes` + `edges`（branch）或 `lanes` + `nodes` + `edges`（swimlane）。检查清单：
- 节点 type 是否准确
- 决策菱形每条出边 label 是否齐
- 失败分支用 `fail`，成功终态用 `success`
- swimlane 同 lane 同 col 不重复

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

输出按 chart type 引擎自动选。打开 PNG 自检。

### Step 5：复杂图手动微调（按需）

drawio CLI 不跑 ELK auto-layout。如出现跨 lane 长跳 / 同源多边 label 重叠：

1. 双击 `flow-xxx-v1.drawio`（drawio desktop 打开）
2. `Ctrl+A` → `Arrange` → `Layout` → `Vertical / Horizontal Flow`，desktop 内置 ELK 重排
3. `File` → `Export As` → `SVG` / `PNG`，覆盖原文件

回路图直接选 `state` 走 mermaid，不要硬塞 branch / swimlane。

## 自检清单

- [ ] PNG 打开无文字 / 边重叠
- [ ] 所有 decision 节点 ≥ 2 条出边都有 label
- [ ] success / fail 节点视觉一致（绿 / 红描边）
- [ ] swimlane 同 lane 同 col 无重复（或已接受 auto-bump）
- [ ] 脚本存 `projects/{项目}/scripts/gen_flow_v{N}.py`
- [ ] 输出存 `projects/{项目}/deliverables/`，前缀 `flow-`
- [ ] `python3 scripts/check_cjk_punct.py projects/{项目}/deliverables/flow-*.{drawio,mmd} --strict` 通过
- [ ] `python3 scripts/check_plain_language.py projects/{项目}/deliverables/flow-*.{drawio,mmd} --strict` 通过（防裸编号）

## 下游消费

- **PRD md 嵌图**：`![alt](./assets/flow-xxx-v1-N.{mmd,drawio}.png)`
- **IMAP / PPT / 架构图**：`<img src="flow-xxx-v1-N.{mmd,drawio}.svg">`（矢量缩放无损）
- **drawio desktop 编辑**：双击 `.drawio` 源文件可视化微调

## 失败恢复

| 现象 | 原因 | 处理 |
|------|------|------|
| 跨 lane 长边 label 重叠 | drawio CLI 不跑 ELK | desktop Ctrl+L 重排 |
| 同源 ≥ 3 带 label 边出口挤 | 同上 | 拆数据 / 手动调端口 sp/tp |
| 中文 lane title 竖排 | drawio horizontal=0 swimlane 对 CJK 默认 | 接受（标准 BPMN 中文风格）|
| 边箭头超出节点 | 节点宽度不够装 label | 拆 label 多行（用 `\n`）|
