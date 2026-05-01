---
name: flowchart
description: >
  当用户提到「流程图」「泳道图」「审批流」时触发。独立产出,可被 IMAP / PPT / 架构图消费(截图或嵌入横屏 HTML)。**PRD docx 嵌图请走 PRD skill 内部 mermaid_screenshots renderer**(参 `.claude/skills/prd/scripts/mermaid_screenshots.py`)——X6/dagre 渲染嵌入 docx 时字号偏小留白巨大,不适合 15.5cm 紧凑嵌图场景。
argument-hint: [主题 或 data 文件]
type: standalone
output_format: .html
output_prefix: flow-
depends_on: []
optional_inputs: [context.md]
consumed_by: []
scripts:
  gen_flow_base.py: "骨架生成 — from gen_flow_base import generate_flowchart"
  flowchart-core.js: "运行时 JS — 骨架脚本自动内联，不手动读"
---

# Flowchart 流程图

## 定位

独立产出型 Skill。把业务流程 / 审批流 / 判定链路可视化,输出浅色白板嵌入深色画布的 HTML 流程图,**仅服务横屏 HTML 嵌入场景**(IMAP / arch / PPT)。

渲染引擎 AntV X6 + dagre:
- 分支图走 dagre 自动布局,声明 nodes/edges 即可
- 泳道图走二维栅格(lane × col),精确控制节点位置
- 连线走 manhattan + rounded connector(同行相邻自动降级 normal 避免绕圈)
- 内置自检:边不穿节点(菱形内切 + rect bbox 4px buffer)

### 适用场景

✅ IMAP / architecture-diagrams / PPT 等横屏 HTML 容器嵌入(视觉空间 1200px+,X6 渲染字号 / 留白合适)
❌ **PRD docx 嵌图不在本 skill 范围**——docx 宽度 15.5cm 是紧凑嵌图场景,X6/dagre 默认 .whiteboard padding 会让节点字号缩到无法阅读。PRD 走 `.claude/skills/prd/scripts/mermaid_screenshots.py`(mermaid LR 横排 + Claude Design 主题,docx 嵌图视觉适配)。

### 与相邻 Skill 的边界

- **interaction-map** 画页面跳转(UI flow),流程图画业务流程(谁在做什么 + 状态怎么转),不混用
- **architecture-diagrams** 画系统架构 + 资金流,流程图画单一业务过程,粒度不同
- **prd** 走 mermaid_screenshots 自己渲染 docx 嵌图,不消费本 skill

用途:
- 复杂判定链路(如 KYC 校验、合规校验、资格认证)
- 跨角色审批流(如大额赎回、报销审批、发布上线流程)
- 状态机可视化(如订单状态流转、工单流转)
- PPT/PRD/交互大图内嵌的业务流程示意图

---

## 产出物格式

单个 HTML 文件,包含 1 ~ N 张图(branch 或 swimlane 混合)。

命名:`flow-{项目简称}-{主题}-v{N}.html`

存放:`projects/{项目}/deliverables/` 或 `deliverables/` (独立主题)

---

## 节点类型速查

| 类型 | 形状 | 填色 | 描边 | 用途 |
|------|------|------|------|------|
| `terminal` | 圆角矩形(rx=21) | 浅紫 #E8E5FF | 黑 | 起点/终点 |
| `process`  | 圆角矩形(rx=8)  | 浅蓝 #E7EFFE | 黑 | 处理/操作节点 |
| `decision` | 菱形             | 浅黄 #FDF3D5 | 黑 | 判定分支(Yes/No) |
| `success`  | 圆角矩形(rx=8)  | 浅绿 #D9F5E5 | 绿 #0ECB81 | 成功分支终态 |
| `fail`     | 圆角矩形(rx=8)  | 浅红 #FEE3E6 | 红 #F6465D | 失败/拦截分支 |

---

## 数据结构

### 分支流程(branch)

```python
{
    "type": "branch",
    "title": "合格投资者认证流程",
    "subtitle": "用户进入认购前的前后端双重校验",
    "layout": "TB",   # TB 纵向 或 LR 横向,默认 TB
    "nodesep": 70,    # 同 rank 节点间距,默认 70
    "ranksep": 60,    # rank 间距,默认 60
    "nodes": [
        {"id": "START", "type": "terminal", "label": "点击「立即认购」"},
        {"id": "Q1",    "type": "decision", "label": "QI 已认证?"},
        {"id": "AUTH",  "type": "fail",     "label": "拦截 + 引导「去认证」"},
        # ...
    ],
    "edges": [
        {"s": "START", "t": "Q1"},
        {"s": "Q1",    "t": "AUTH", "label": "No"},
        {"s": "Q1",    "t": "NEXT", "label": "Yes"},
    ],
}
```

### 泳道流程(swimlane)

```python
{
    "type": "swimlane",
    "title": "大额赎回审批流程",
    "subtitle": "投资人 / 运营 / 风控 / 基金经理 四泳道",
    "lanes": ["投资人", "运营", "风控", "基金经理"],
    "laneHeight": 90,    # 单泳道高度,默认 90
    "colWidth": 150,     # 列宽,默认 150
    "headWidth": 84,     # 左侧 header 列宽,默认 84
    "nodes": [
        {"id": "I1", "lane": "投资人", "col": 0, "type": "terminal", "label": "发起赎回申请"},
        {"id": "O1", "lane": "运营",   "col": 1, "type": "process",  "label": "接收+资料核验"},
        # ...
    ],
    "edges": [
        {"s": "I1", "t": "O1"},
        {"s": "Q4", "t": "F3", "label": "No", "sp": "bottom", "tp": "bottom"},  # 可选端口覆盖
    ],
}
```

边字段:
- `s` / `t`:source / target 节点 id(必填)
- `label`:边标签(可选,如 Yes/No)
- `sp` / `tp`:端口方向覆盖(可选,top/bottom/left/right),仅 swimlane 场景使用;branch 走 dagre 自动决定

---

## 执行步骤

### Step 1:读取必要文件

**必读**:
- `.claude/skills/flowchart/SKILL.md`(本文件)
- `.claude/skills/flowchart/scripts/gen_flow_base.py`(base 生成器 API)

**按需读**:
- `.claude/skills/flowchart/assets/flowchart-core.js`(调试节点类型/路由逻辑时)
- `.claude/skills/flowchart/assets/flowchart.css`(调整白板样式时)
- `.claude/skills/_shared/claude-design/anti-ai-slop.md`(产出前 grep「决策速查」段，确认无 slop 视觉陷阱)

### Step 2:梳理流程数据

用户提供的流程信息整理成结构化 charts 列表。一个 HTML 文件可含多张图(混合 branch 和 swimlane)。

数据梳理时必须确认:
- 节点类型准确(terminal / process / decision / success / fail)
- 菱形判定节点的 Yes/No 分支都有边覆盖(别漏分支)
- 失败分支用 fail 类型(红描边),成功终态用 success 类型(绿描边)
- swimlane 场景 col 编号从 0 开始,相邻节点 col 差值 ≥ 1

### Step 3:写项目侧 gen 脚本

在 `projects/{项目}/scripts/gen_flow_v1.py` 写数据 + 调用 base:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[3] / ".claude/skills/flowchart/scripts"))
from gen_flow_base import render_flowchart

CHARTS = [
    {
        "type": "branch",
        "title": "...",
        # ...
    },
    {
        "type": "swimlane",
        "title": "...",
        # ...
    },
]

render_flowchart(
    output_path=str(Path(__file__).parents[1] / "deliverables/flow-xxx-v1.html"),
    title="流程图 · XXX",
    subtitle="...",
    charts=CHARTS,
)
```

### Step 4:执行 + 自检

```bash
python3 projects/{项目}/scripts/gen_flow_v1.py
```

浏览器打开 HTML,底部自检面板应显示 `✓ 自检通过`(绿字)。

Playwright 验证命令(无头截图 + 读 console):
```bash
python3 -c "
from playwright.sync_api import sync_playwright
import time
HTML='file://$(pwd)/projects/XXX/deliverables/flow-xxx-v1.html'
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1400,'height':2000},device_scale_factor=2)
    logs=[]
    pg.on('console',lambda m: logs.append(f'[{m.type}] {m.text[:200]}'))
    pg.goto(HTML); pg.wait_for_load_state('networkidle'); time.sleep(2)
    pg.screenshot(path='/tmp/flow.png',full_page=True); b.close()
    for l in logs: print(l)"
```

期望 console 末尾看到 `[log] [SELF-CHECK] PASS []`。

---

## 自检清单

- [ ] console 输出 `[SELF-CHECK] PASS`(无边穿节点)
- [ ] 所有 decision 节点都有 ≥ 2 条出边(Yes/No 分支完整)
- [ ] success 节点用浅绿+绿描边,fail 节点用浅红+红描边(视觉一致)
- [ ] swimlane 图无节点跨泳道误放(lane 字段写错)
- [ ] 脚本存 `projects/{项目}/scripts/gen_flow_v{N}.py`,命名符合规范
- [ ] HTML 放 `projects/{项目}/deliverables/`,前缀 `flow-`

## 常见问题

### 连线有绕圈小回环
发生在同行相邻节点之间(如两个菱形横排)。base JS 已自动处理(isHoriz → normal router)。若仍出现,说明节点实际不同行——检查 swimlane 的 lane 字段或 branch 的 dagre 布局是否正确。

### manhattan algorithm warning
base JS 对非同行边走 manhattan + rounded,某些布局下 manhattan 找不到路径会降级 orth 并产生 warning。如果自检通过,可忽略。如果自检失败,说明 orth 把边塞进其他节点——需要调整 nodesep/ranksep 拉大间距。

### dagre 把所有节点挤到一列
branch 默认 layout=TB 会纵向排列。若判定节点的 Yes/No 分支需要横向展开,改 `layout: "LR"`,或者手动把 success/fail 放到 decision 的同行(通过显式 rank 控制,dagre.setNode 加 `rank` 字段——需扩展 base JS)。当前 base 只支持默认 dagre 行为,复杂布局建议用 swimlane 精确定位。

### 截图插入 PRD
标准流程:Playwright 截图 → Pillow 圆角透明(可选) → docx 插入。参考 prd skill 的截图脚本模板(`.claude/skills/prd/scripts/` 下的 Step 4 说明),增加 selector 参数截取 `.whiteboard` 而非 `.phone`。
