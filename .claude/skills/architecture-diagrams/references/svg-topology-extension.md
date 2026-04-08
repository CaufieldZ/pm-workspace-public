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
    <text x="248" y="148" fill="#3b82f6" font-size="9" font-family="IBM Plex Mono" text-anchor="middle">标注</text>
  </svg>
</div>
```

### 箭头颜色约定

| 颜色 | Hex | 用途 |
|------|-----|------|
| 蓝 | #3b82f6 | 数据流 / API 调用 |
| 琥珀 | #d97706 | 内部联动 / 撮合 |
| 紫 | #7c3aed | 真实资金流（链上）|
| 青 | #0d9488 | 链上余额 |
| 灰 | #94a3b8 | 监控 / 暂停 |
| 红 | #dc2626 | 拒绝 / 风险 |
| 绿 | #15803d | 成功 |

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

## 完整拓扑图模板

参考 `components-cheatsheet.md` 中的拓扑图节点和 SVG 箭头模板。

## 注意事项

1. **坐标精确**：节点和 SVG 箭头共享坐标系，箭头起终点要对准节点边缘
2. **容器高度**：`.dia` 的 `height` 要大于最底部节点的 `top + height`
3. **虚线箭头**：`stroke-dasharray="4 3"` 用于监控/间接/虚线连接
