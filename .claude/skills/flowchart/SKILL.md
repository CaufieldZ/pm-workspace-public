---
name: flowchart
description: >
  当用户提到「流程图」「泳道图」「审批流」时触发。独立产出 .drawio + .svg + .png（drawio 桌面 CLI 导出，PRD docx / IMAP / PPT / 架构图直接 `<img>` 引用 SVG）。原 X6/dagre HTML 渲染已弃用。
argument-hint: [主题 或 data 文件]
type: standalone
output_format: .drawio
output_prefix: flow-
depends_on: []
optional_inputs: [context.md]
consumed_by: []
scripts:
  gen_flow_base.py: "drawio XML 生成器 — from gen_flow_base import render_flowchart"
---

# Flowchart 流程图（drawio 版）

## 定位

独立产出型 Skill。把业务流程 / 审批流 / 判定链路可视化，输出 drawio 原生格式 + 矢量 SVG + 位图 PNG。

**渲染引擎**：drawio desktop CLI（`/Applications/draw.io.app/Contents/MacOS/draw.io`）。

**输出**：每张图产 3 个文件
- `flow-xxx-v1.drawio` — 源文件，drawio desktop 可编辑（含 ELK auto-layout，复杂图手动 Ctrl+L 微调）
- `flow-xxx-v1-N.drawio.svg` — 矢量，`<img>` 嵌入 HTML（IMAP / PPT / 架构图）
- `flow-xxx-v1-N.drawio.png` — 位图，docx 嵌入（PRD）+ 预览

多 chart 时按 page 拆出 `-1`、`-2` 后缀。

## 适用 vs 局限

✅ **能做好**：
- 单角色流程（branch）：起点 → 处理 → 判定 → 成功/失败终态
- 简单泳道（2-3 lane，时间轴向右流，跨 lane 边少）
- 决策分支（Yes/No 两路）+ success/fail 终态
- 多页流程合并到一个 .drawio

⚠ **drawio CLI 局限**：
- **跨多 lane + 多行 label 长跳转边渲染会重叠**（drawio CLI 不跑 ELK auto-layout）
- 同源 ≥ 3 条带 label 边在同方向出口会挤
- 大量节点（> 30）+ 频繁交叉边视觉拥挤

碰到上述局限：**生成完 .drawio 后在 drawio desktop 里手动 `Ctrl+A` → `Arrange` → `Layout` → `Vertical/Horizontal Flow`，desktop 内置 ELK 跑一遍重排**，再 File → Export 覆盖 SVG/PNG。每张图多 30 秒手动操作。

❌ **不在范围**：
- 时序图（用 IMAP 跨端时序）
- 系统架构（用 architecture-diagrams skill）
- UI 跳转图（用 interaction-map skill）

---

## 节点类型 + 视觉

| type | 形状 | fillColor | strokeColor | 用途 |
|------|------|-----------|-------------|------|
| `terminal` | 圆角矩形 arcSize=40（胶囊） | `#E8E5FF` 紫 | `#1F2329` 黑 | 起点 / 终点 |
| `process`  | 圆角矩形 arcSize=18 | `#E7EFFE` 蓝 | `#1F2329` 黑 | 处理 / 操作 |
| `decision` | 菱形 rhombus | `#FDF3D5` 黄 | `#1F2329` 黑 | 判定（Yes/No 分支） |
| `success`  | 圆角矩形 arcSize=18 | `#D9F5E5` 绿 | `#0ECB81` 绿描边 | 成功终态 |
| `fail`     | 圆角矩形 arcSize=18 | `#FEE3E6` 红 | `#F6465D` 红描边 | 失败 / 拦截 |

字体：PingFang SC / Noto Sans SC。决策菱形 180×80，其他节点 160×60（多行 label 由 drawio whiteSpace=wrap 自动撑高）。

---

## 数据结构

### 分支流程（branch）

```python
{
    "type": "branch",
    "title": "合格投资者认证流程",
    "nodes": [
        {"id": "START", "type": "terminal", "label": "点击「立即认购」"},
        {"id": "Q1",    "type": "decision", "label": "QI 已认证？"},
        {"id": "AUTH",  "type": "fail",     "label": "拦截 + 引导「去认证」"},
        {"id": "NEXT",  "type": "process",  "label": "进入风险测评"},
        {"id": "DONE",  "type": "success",  "label": "进入认购"},
    ],
    "edges": [
        {"s": "START", "t": "Q1"},
        {"s": "Q1",    "t": "AUTH", "label": "否"},
        {"s": "Q1",    "t": "NEXT", "label": "是"},
        {"s": "NEXT",  "t": "DONE"},
    ],
}
```

布局：base 用 topo BFS 自动算 col/row，decision 分支节点向左右展开。如要精确控制，给 node 加 `col` `row` 字段覆盖。

### 泳道流程（swimlane）

```python
{
    "type": "swimlane",
    "title": "大额赎回审批",
    "lanes": ["投资人", "运营", "风控", "基金经理"],
    "nodes": [
        {"id": "I1", "lane": "投资人", "col": 0, "type": "terminal", "label": "发起赎回"},
        {"id": "O1", "lane": "运营",   "col": 1, "type": "process",  "label": "接收 + 核验"},
        {"id": "R1", "lane": "风控",   "col": 2, "type": "decision", "label": "合规？"},
        {"id": "R2", "lane": "风控",   "col": 2, "type": "fail",     "label": "否决"},
        {"id": "M1", "lane": "基金经理", "col": 3, "type": "process",  "label": "审批"},
        {"id": "I2", "lane": "投资人", "col": 4, "type": "success",  "label": "收到资金"},
    ],
    "edges": [
        {"s": "I1", "t": "O1"},
        {"s": "O1", "t": "R1"},
        {"s": "R1", "t": "R2", "label": "否"},
        {"s": "R1", "t": "M1", "label": "是"},
        {"s": "M1", "t": "I2"},
    ],
}
```

字段：
- `lane`：必填，泳道名（必须出现在 `lanes` 列表里）
- `col`：必填，列编号（0-indexed）。**同 lane 同 col 重复时 base 会自动 bump 后续节点到下一 col 并打印 warning**——但建议自己排清楚 col
- `s` / `t` / `label`：边 source / target / 可选标签
- `sp` / `tp`：可选端口提示（top / bottom / left / right），跨 lane 长跳建议显式 `sp="top", tp="bottom"` 引导路由

---

## 执行步骤

### Step 1：读必要文件

**必读**：
- `.claude/skills/flowchart/SKILL.md`（本文件）
- `.claude/skills/flowchart/scripts/gen_flow_base.py`（API）

**按需**：用户原始流程描述（context.md / 会议纪要 / 截图）

### Step 2：梳理数据

把流程整理成 `nodes` + `edges`（branch）或 `nodes` + `edges` + `lanes`（swimlane）。检查清单：
- 节点 type 是否准确（terminal / process / decision / success / fail）
- 决策菱形的每条出边是否都有 label（"是" / "否" / "Yes" / "No"）
- 失败分支用 `fail`，成功终态用 `success`
- swimlane 同 lane 同 col 不重复（base 会自动 bump 但建议自己排好）

### Step 3：写项目侧 gen 脚本

`projects/{产品线}/{项目}/scripts/gen_flow_v{N}.py`：

```python
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[4]  # 注意是 parents[4]！两级产品线 + 项目
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

输出 `.drawio` + `-N.drawio.svg` + `-N.drawio.png`。打开 PNG 自检。

### Step 5：复杂图手动微调（按需）

如果 swimlane 跨 lane 长跳 / 同源多边 label 重叠：
1. 双击 `flow-xxx-v1.drawio`（drawio desktop 打开）
2. `Ctrl+A` 全选 → 菜单 `Arrange` → `Layout` → `Vertical Flow` 或 `Horizontal Flow`
3. desktop 内置 ELK 重排，无重叠
4. `File` → `Export As` → `SVG` / `PNG`，覆盖原文件

---

## 自检清单

- [ ] PNG 打开无文字 / 边重叠
- [ ] 所有 decision 节点 ≥ 2 条出边都有 label
- [ ] success / fail 节点视觉一致（绿 / 红描边）
- [ ] swimlane 同 lane 同 col 无重复（或已接受 auto-bump）
- [ ] 脚本存 `projects/{项目}/scripts/gen_flow_v{N}.py`
- [ ] 输出存 `projects/{项目}/deliverables/`，前缀 `flow-`
- [ ] `python3 scripts/check_cjk_punct.py projects/{项目}/deliverables/flow-*.drawio --strict` 通过（`.drawio` XML 里 `<mxCell value="...">` 的 CJK 旁半角标点必须全角；hook 已自动拦截，此条为手动兜底）

## 下游消费

- **PRD docx 嵌图**：`<img src="flow-xxx-v1-1.drawio.png">` 或 docx 直插 PNG（取代 mermaid_screenshots）
- **IMAP / PPT / 架构图**：`<img src="flow-xxx-v1-1.drawio.svg">`（矢量缩放无损）
- **drawio desktop 编辑**：双击 `.drawio` 源文件，可视化微调

## 已知问题

| 现象 | 原因 | 处理 |
|------|------|------|
| 跨 lane 长边 label 重叠 | drawio CLI 不跑 ELK | desktop Ctrl+L 重排 |
| 同源 ≥ 3 带 label 边出口挤 | 同上 | 拆数据 / 手动调端口 sp/tp |
| 中文 lane title 竖排（每字独立一行） | drawio horizontal=0 swimlane 对 CJK 默认渲染 | 接受（标准 BPMN 中文风格）|
| 边箭头超出节点 | 节点宽度不够装 label | 拆 label 多行（用 `\n`）|
