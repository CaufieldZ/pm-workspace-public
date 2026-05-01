# SVG 拓扑图扩展（可选）

> 大部分方案文档**不需要**画真正的拓扑图。用 CSS Grid 卡片 + 表格就能讲清楚。
> 只有当方案**必须**用节点连线展示时，才使用本扩展。

## 什么时候需要拓扑图

- 系统间有复杂的**调用关系**需要可视化
- 需要展示**数据流向**（谁调谁、钱从哪到哪）
- 需要**决策树/流程图**（分支、拒绝路径）

## 绝对定位节点

节点用 `position:absolute` + `left/top/width/height` 定位：

```html
<div class="n c-u" style="left:200px;top:0;width:660px;height:52px;text-align:center;">
  <b style="justify-content:center;">👤 用户层</b>
  <small>说明文字</small>
</div>
```

### 节点颜色 class

| class | 背景 | 边框 | 标题色 | 用途 |
|-------|------|------|--------|------|
| `.c-u` | #eef2ff | #a5b4fc | #4338ca | 用户层 |
| `.c-p` | #f0fdfa | #5eead4 | #0f766e | 现有系统（保留）|
| `.c-pn` | #ecfeff | #22d3ee(2px) | #0e7490 | 新建系统 |
| `.c-h` | #fffbeb | #fcd34d | #b45309 | 对方/复用系统 |
| `.c-ch` | #f5f3ff | #c4b5fd | #6d28d9 | 链上/特殊 |
| `.c-r` | #fef2f2 | #fca5a5 | #b91c1c | 风险/告警 |
| `.c-g` | #f0fdf4 | #86efac | #15803d | 估算/正向 |

### 坐标规划

1. 确定 `.dia` 容器宽高（通常 1060×540 ~ 1060×740）
2. 用 `.sec` 分层，每层约 120-180px 高
3. 节点间留 30-40px 间距
4. 水平排列：每行 3-4 个节点，宽度约 200-280px

## SVG 箭头连线

每个 `.dia` 内叠一层 SVG：

```html
<div class="dia" style="position:relative;width:1060px;height:540px;">
  <!-- 节点... -->

  <!-- SVG 箭头层 -->
  <svg viewBox="0 0 1060 540" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;">
    <defs>
      <!-- 定义箭头 marker -->
      <marker id="ab1" markerWidth="7" markerHeight="5" refX="7" refY="2.5" orient="auto">
        <polygon points="0 0,7 2.5,0 5" fill="#3b82f6"/>
      </marker>
      <!-- 更多 marker... -->
    </defs>

    <!-- 直线箭头 -->
    <line x1="230" y1="154" x2="268" y2="154" stroke="#3b82f6" stroke-width="1.5" marker-end="url(#ab1)"/>

    <!-- 折线箭头 -->
    <path d="M350,52 L350,68 L115,68 L115,94" fill="none" stroke="#3b82f6" stroke-width="1.5" marker-end="url(#ab1)"/>

    <!-- 虚线箭头 -->
    <line x1="548" y1="301" x2="586" y2="301" stroke="#d97706" stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#aa1)"/>

    <!-- 文字标注 -->
    <text x="248" y="148" fill="#3b82f6" font-size="9" font-family="JetBrains Mono" text-anchor="middle">标注</text>
  </svg>
</div>
```

### 箭头语义编码系统

> 颜色 + 线型组合编码含义，不只是装饰。读图者无需图例即可区分同步/异步、读/写、主路径/反馈。

#### 颜色 × 线型矩阵

| 语义 | 颜色 | Hex | 线型 | stroke-dasharray | 宽度 | 典型场景 |
|------|------|-----|------|-----------------|------|---------|
| 主数据流（同步） | 蓝 | #3b82f6 | 实线 | — | 1.5 | API 请求/响应、主链路调用 |
| 控制/触发 | 琥珀 | #d97706 | 实线 | — | 1.5 | 系统 A 触发系统 B、撮合 |
| 内存/存储读取 | 绿 | #15803d | 实线 | — | 1.5 | 从 DB/缓存读数据 |
| 内存/存储写入 | 绿 | #15803d | 虚线 | `5,3` | 1.2 | 向 DB/缓存写数据 |
| 异步/事件驱动 | 灰 | #94a3b8 | 虚线 | `4,2` | 1.2 | MQ 消息、Webhook、定时任务 |
| 反馈/回环 | 紫 | #7c3aed | 曲线 | — | 1.5 | 迭代推理、重试、自纠正 |
| 真实资金流 | 紫 | #7c3aed | 粗实线 | — | 1.8 | 链上转账、出入金 |
| 链上余额查询 | 青 | #0d9488 | 虚线 | `4,3` | 1.2 | 余额校验、对账 |
| 风险/拒绝 | 红 | #dc2626 | 实线 | — | 1.5 | 风控拦截、审批驳回 |
| 监控/审计 | 灰 | #94a3b8 | 点线 | `2,3` | 1.0 | 日志采集、告警上报 |

#### 线型速查 SVG 片段

```html
<!-- 同步数据流（蓝实线） -->
<line ... stroke="#3b82f6" stroke-width="1.5" marker-end="url(#ab)"/>

<!-- 异步事件（灰虚线） -->
<line ... stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="4 2" marker-end="url(#ag)"/>

<!-- 存储写入（绿虚线） -->
<line ... stroke="#15803d" stroke-width="1.2" stroke-dasharray="5 3" marker-end="url(#agg)"/>

<!-- 存储读取（绿实线） -->
<line ... stroke="#15803d" stroke-width="1.5" marker-end="url(#agg)"/>

<!-- 反馈回环（紫曲线） -->
<path d="M x1,y1 C cx1,cy1 cx2,cy2 x2,y2" fill="none" stroke="#7c3aed" stroke-width="1.5" marker-end="url(#ap)"/>

<!-- 监控/审计（灰点线） -->
<line ... stroke="#94a3b8" stroke-width="1.0" stroke-dasharray="2 3" marker-end="url(#ag)"/>
```

#### 图例组件（推荐放在拓扑图右下角）

```html
<g transform="translate(X, Y)" font-size="9" font-family="'Noto Sans SC','Inter',sans-serif">
  <text x="0" y="0" fill="#64748b" font-weight="700" font-size="10">图例</text>
  <!-- 同步数据流 -->
  <line x1="0" y1="14" x2="36" y2="14" stroke="#3b82f6" stroke-width="1.5" marker-end="url(#ab)"/>
  <text x="42" y="17" fill="#64748b">同步数据流</text>
  <!-- 异步/事件 -->
  <line x1="0" y1="28" x2="36" y2="28" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="4 2" marker-end="url(#ag)"/>
  <text x="42" y="31" fill="#64748b">异步/事件</text>
  <!-- 存储读 -->
  <line x1="0" y1="42" x2="36" y2="42" stroke="#15803d" stroke-width="1.5" marker-end="url(#agg)"/>
  <text x="42" y="45" fill="#64748b">存储读取</text>
  <!-- 存储写 -->
  <line x1="0" y1="56" x2="36" y2="56" stroke="#15803d" stroke-width="1.2" stroke-dasharray="5 3" marker-end="url(#agg)"/>
  <text x="42" y="59" fill="#64748b">存储写入</text>
  <!-- 资金流 -->
  <line x1="0" y1="70" x2="36" y2="70" stroke="#7c3aed" stroke-width="1.8" marker-end="url(#ap)"/>
  <text x="42" y="73" fill="#64748b">资金流</text>
  <!-- 风控拦截 -->
  <line x1="0" y1="84" x2="36" y2="84" stroke="#dc2626" stroke-width="1.5" marker-end="url(#ar)"/>
  <text x="42" y="87" fill="#64748b">风控拦截</text>
</g>
```

### Marker ID 唯一性

每个 Tab 的 SVG marker id 要加后缀避免冲突：
- Tab 0: `ab0`, `aa0`, `ap0`...
- Tab 1: `ab1`, `aa1`, `ap1`...

### 坐标计算

- 节点右边缘 x = left + width
- 节点左边缘 x = left
- 节点顶边缘 y = top
- 节点底边缘 y = top + height
- 节点中心 y = top + height/2
- 箭头起点 = 源节点边缘，终点 = 目标节点边缘

## 形状语义词汇表

> 不同形状编码不同角色，跨图保持一致。读图者靠形状即可识别组件类型，不依赖文字标签。

### 形状 × 语义对照

| 形状 | 语义 | 典型实例 | 视觉特征 |
|------|------|---------|---------|
| 六边形 | Agent / 编排器 | AI Agent、调度中心、网关 | 尖角六边形，强调"枢纽"角色 |
| 圆角矩形（双边框） | LLM / 模型 | GPT-4、Claude、Gemini | 内外双 border + 闪电标记 |
| 圆柱体 | 数据库 / 持久存储 | PostgreSQL、MongoDB、Redis | 顶部椭圆 + 矩形体 |
| 圆柱体（内环） | 向量数据库 | Pinecone、Qdrant、Weaviate | 圆柱体内加 1-2 条椭圆环线 |
| 虚线矩形 | 短期记忆 / 缓存 | Session、对话上下文、Redis 缓存 | `stroke-dasharray` 虚线边框 |
| 实线圆柱 | 长期存储 | 用户画像、历史记录、审计日志 | 普通圆柱，实线 |
| 菱形 | 决策点 | 风控判断、条件分支、审批 | 45° 旋转正方形 |
| 圆形 | 起点 / 终点 | 流程入口、结束状态 | 实心或空心圆 |
| 平行四边形 | 外部输入/输出 | 用户请求、API 返回、文件导入 | 倾斜矩形 |

### SVG 形状模板

```html
<!-- 六边形（Agent/编排器）：cx,cy=中心坐标, r=外接圆半径 -->
<!-- 公式：6 个顶点，角度 0°/60°/120°/180°/240°/300° -->
<polygon points="cx+r,cy cx+r/2,cy-r*0.866 cx-r/2,cy-r*0.866 cx-r,cy cx-r/2,cy+r*0.866 cx+r/2,cy+r*0.866"
  fill="#eef2ff" stroke="#6366f1" stroke-width="1.5"/>
<!-- 示例：中心(200,100), r=40 -->
<polygon points="240,100 220,65.4 180,65.4 160,100 180,134.6 220,134.6"
  fill="#eef2ff" stroke="#6366f1" stroke-width="1.5"/>
<text x="200" y="104" text-anchor="middle" fill="#4338ca" font-size="11" font-weight="700">Agent</text>

<!-- 圆柱体（数据库）：x,y=左上角, w=宽, h=体高, ry=椭圆半径 -->
<ellipse cx="300" cy="200" rx="40" ry="12" fill="#f0fdfa" stroke="#5eead4" stroke-width="1.5"/>
<rect x="260" y="200" width="80" height="50" fill="#f0fdfa" stroke="#5eead4" stroke-width="1.5" stroke-dasharray="0 80 50 80"/>
<ellipse cx="300" cy="250" rx="40" ry="12" fill="#f0fdfa" stroke="#5eead4" stroke-width="1.5"/>
<line x1="260" y1="200" x2="260" y2="250" stroke="#5eead4" stroke-width="1.5"/>
<line x1="340" y1="200" x2="340" y2="250" stroke="#5eead4" stroke-width="1.5"/>
<text x="300" y="230" text-anchor="middle" fill="#0f766e" font-size="10" font-weight="700">PostgreSQL</text>

<!-- 圆柱体 + 内环（向量数据库）：在普通圆柱基础上加内部椭圆 -->
<ellipse cx="300" cy="225" rx="40" ry="12" fill="none" stroke="#5eead4" stroke-width="0.8" opacity="0.5"/>

<!-- 菱形（决策点）：cx,cy=中心, s=半对角线长 -->
<polygon points="500,160 540,190 500,220 460,190"
  fill="#fffbeb" stroke="#fcd34d" stroke-width="1.5"/>
<text x="500" y="194" text-anchor="middle" fill="#b45309" font-size="10" font-weight="700">风控?</text>

<!-- 双边框圆角矩形（LLM）：外层 + 内层 rect -->
<rect x="100" y="80" width="120" height="48" rx="8" fill="#f5f3ff" stroke="#c4b5fd" stroke-width="2"/>
<rect x="104" y="84" width="112" height="40" rx="6" fill="none" stroke="#c4b5fd" stroke-width="0.8" opacity="0.5"/>
<text x="160" y="108" text-anchor="middle" fill="#6d28d9" font-size="11" font-weight="700">&#9889; Claude</text>

<!-- 虚线矩形（短期缓存） -->
<rect x="400" y="300" width="140" height="48" rx="6" fill="#f8fafc"
  stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="6 3"/>
<text x="470" y="328" text-anchor="middle" fill="#64748b" font-size="10">Session Cache</text>
```

### 使用规则

1. 同一架构图中，相同语义角色必须用相同形状（不能一个 Agent 用六边形另一个用矩形）
2. 形状选择优先于颜色区分（颜色用于分组/分层，形状用于角色识别）
3. 决策点（菱形）的出口箭头必须标注分支条件（"通过" / "拒绝"）
4. 圆柱体统一用于持久化存储，短期缓存用虚线矩形

## 完整拓扑图模板

参考 `components-cheatsheet.md` 中的拓扑图节点和 SVG 箭头模板。

## 注意事项

1. **坐标精确**：节点和 SVG 箭头共享坐标系，箭头起终点要对准节点边缘
2. **容器高度**：`.dia` 的 `height` 要大于最底部节点的 `top + height`
3. **虚线箭头**：`stroke-dasharray="4 3"` 用于监控/间接/虚线连接
