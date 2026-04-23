<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: architecture-diagrams
description: >
  当需求涉及多系统对接 / 资金流转,或用户提到「架构图」「技术架构」时触发。超复杂链路中场景清单后、IMAP 前自动接续,也适用于:系统设计文档、技术方案评审、风险分析、Phase 路线图等。
type: pipeline
output_format: .html
output_prefix: arch-
pipeline_position: 2.5
depends_on: [scene-list]
optional_inputs: [context.md]
consumed_by: [interaction-map]
scripts:
  js-template.js: "运行时 JS 模板 — 骨架脚本自动内联，不手动读"
---
<!-- pm-ws-canary-236a5364 -->

# 架构图集 Skill（Architecture Diagrams）

## 什么是架构图集

架构图集是一种**多 Tab 单页 HTML 技术方案文档**，用于：
- 在方案评审时用结构化卡片讲清楚技术设计
- 用 **CSS Grid 卡片 + 表格 + Callout** 组织信息（不是拓扑图！）
- 用 Tab 切换展示多个视角（总览 / 账户 / 资金流 / 风控 / 路线图等）
- 给老板/技术团队汇报方案，**等同 PPT**

## 与 interaction-map 的区别

| 维度 | interaction-map | architecture-diagrams |
|------|----------------|----------------------|
| 用途 | 产品交互流程 | 技术方案架构 |
| 布局 | 横向 Flow + Mockup | **CSS Grid 卡片 + 表格** |
| 导航 | 滚动 + 侧导航 | Tab 切换 |
| 适合 | 页面跳转、UI 改动标注 | 方案讲解、数据对比、风险分析 |

## 核心输出规范

1. **单文件 HTML**：CSS/JS 内联，字体 CDN 除外
2. **Tab 导航**：粘性 tab bar，JS 切换 `.pw.a`
3. **核心布局**：CSS Grid 卡片（2-5 列）+ Flex 行（等宽对比）
4. **表格**：蓝色表头，zebra 行，用于数据对比/参数清单
5. **Callout**：彩色左边框提示框，用于总结/风险/结论
6. **Tag 标签**：保留/新建/复用/关键/Phase 等状态标记

## 分步生成策略

架构图集天然适合分步，**每个 Tab 独立生成**：

> ⚡ **快速模式**
> 用户说「快速生成」「不用确认直接跑完」「一口气出」时激活：
> - 所有 Tab 连续生成，不在中间等用户确认
> - 只在全部 Tab 完成后停下来交付
> - 未激活快速模式时，每个 Tab 完成后等确认

### Fill 内容契约

骨架提供完整 HTML 结构（`<head>` + CSS + Tab Bar + 空 `.pw` 容器 + JS），Fill 提供每个 Tab 的 `.pw` 内部内容（标题/副标题/卡片/表格等）。无设备壳组件。

### 分步计划

| Step | 内容 | 预估行数 |
|------|------|----------|
| 1 | 创建文件 → `<head>` + CSS 模板 + `</head><body>` | ~60 行 |
| 2 | Tab Bar（所有 Tab 标题） | 10-20 行 |
| 3-N | 每个 Tab 的 `.pw` 内容（每步 1-2 个 Tab） | 每个 Tab 80-200 行 |
| N+1 | JS 模板 + `</body></html>` | ~10 行 |

**每个 Tab 典型结构**：
```html
<div class="pw" id="tN"><div class="pg">
  <h1>标题</h1>
  <div class="sub">副标题说明</div>
  <div class="rl"></div>

  <!-- Section 1 -->
  <div class="sec"><b>区域名</b><span class="sl"></span><em>说明</em></div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
    <div class="cd" style="background:#fffbeb;border:2px solid #fcd34d;">
      <!-- 卡片内容 -->
    </div>
    <!-- 更多卡片... -->
  </div>

  <!-- 表格 -->
  <table>...</table>

  <!-- Callout -->
  <div class="co co-g"><strong>总结：</strong>内容</div>
</div></div>
```

## 如何使用

### Step 1：读取模板

```
view .claude/skills/architecture-diagrams/references/css-template.css
view .claude/skills/architecture-diagrams/references/js-template.js
```

### Step 2：收集方案信息

向用户确认：
1. **方案名称**（用于标题）
2. **需要几个 Tab 视角**：每个 Tab 的主题
3. **每个 Tab 包含哪些内容模块**
4. **是否需要数据可视化**（表格/对比卡/步骤流）

### Step 3：组装 HTML

```
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title><!-- [FILL] 项目名称 · 架构图集 --></title>
<style>
  <!-- 从 css-template.css 复制完整内容 -->
</style>
</head>
<body>

<!-- Tab Bar -->
<div class="tb">
  <div class="t a" onclick="sw(0)"><span class="i">0</span><!-- [FILL] Tab名 --></div>
  <div class="t" onclick="sw(1)"><span class="i">1</span><!-- [FILL] --></div>
  <!-- 按需增减 -->
</div>

<!-- Tab 0 -->
<div class="pw a" id="t0"><div class="pg">
  <h1><!-- [FILL] --></h1>
  <div class="sub"><!-- [FILL] --></div>
  <div class="rl"></div>
  <!-- [FILL] 内容 -->
</div></div>

<!-- Tab 1 -->
<div class="pw" id="t1"><div class="pg">
  <!-- [FILL] -->
</div></div>

<!-- 更多 Tab... -->

<script>
  <!-- 从 js-template.js 复制 -->
</script>
</body>
</html>
```

## 组件速查（class 名 + 用途）

> 详细 HTML 代码见 `references/components-cheatsheet.md`，按需读取。此处仅列 class 名供快速参考。

| 组件 | 关键 class / 结构 | 用途 |
|------|------------------|------|
| Tab 导航 | `.tb` > `.t` + `.pw` > `.pg` | 粘性 tab bar，JS `sw(i)` 切换 |
| CSS Grid 卡片 | `display:grid` + `.cd` | 2-5 列等宽/比例布局 |
| Flex 行 | `.fx` > `.cd` | 等宽对比、流程箭头 |
| Callout | `.co.co-b/.co-a/.co-r/.co-g/.co-v` | 蓝/琥珀/红/绿/紫提示框 |
| 表格 | `<table>` 蓝色 `<th>` + zebra 行 | 数据对比/参数清单 |
| Section 线 | `.sec` > `<b>` + `.sl` + `<em>` | 区域分隔 |
| 步骤编号 | `.sn.sn-b/.sn-g/.sn-r` | 蓝/绿/红编号圆圈 |
| Tag 标签 | `.tg.tg-k/.tg-n/.tg-w/.tg-c/.tg-p` | 保留/新建/复用/关键/Phase |
| 地址高亮 | `.addr` | 链上地址 monospace |
| 图例 | `.leg` > `.leg-i` > `.leg-s` | 颜色图例说明 |

## 卡片配色约定

| 背景 | 边框 | 标题色 | 用途 |
|------|------|--------|------|
| `#fffbeb` | `#fcd34d` | `#b45309` | 我方 / 核心方 / 琥珀 |
| `#eef2ff` | `#a5b4fc` | `#4338ca` | 用户 / 蓝色 |
| `#f0fdfa` | `#5eead4` | `#0f766e` | 现有系统（保留） |
| `#ecfeff` | `#22d3ee`(2px) | `#0e7490` | 新建系统 |
| `#f5f3ff` | `#c4b5fd` | `#6d28d9` | 链上 / 紫色 |
| `#f0fdf4` | `#86efac` | `#15803d` | 成功 / 绿色 |
| `#fef2f2` | `#fca5a5` | `#b91c1c` | 风险 / 红色 |
| `#f8fafc` | `#e2e8f0` | `#64748b` | 中性 / 灰色 |

## 常用卡片模板

### 大指标卡

```html
<div style="padding:20px;border-radius:8px;background:#fffbeb;border:2px solid #fcd34d;">
  <div style="font-size:11px;color:#92400e;font-weight:600;margin-bottom:8px;">指标名</div>
  <div style="font-size:32px;font-weight:900;color:#b45309;">1,234 <span style="font-size:14px;">USDT</span></div>
  <div style="font-size:11px;color:#92400e;margin-top:4px;">补充说明</div>
</div>
```

### 对比双栏

```html
<div class="fx">
  <div class="cd" style="background:#f0fdf4;border:2px solid #86efac;">
    <div style="font-size:13px;font-weight:700;color:#15803d;">✅ 方案 A</div>
    <div style="font-size:11px;color:#334155;line-height:1.8;">
      <div>• 优势1</div>
      <div>• 优势2</div>
    </div>
  </div>
  <div class="cd" style="background:#fef2f2;border:2px solid #fca5a5;">
    <div style="font-size:13px;font-weight:700;color:#b91c1c;">❌ 方案 B</div>
    <div style="font-size:11px;color:#334155;line-height:1.8;">
      <div>• 劣势1</div>
      <div>• 劣势2</div>
    </div>
  </div>
</div>
```

### Phase 路线图

```html
<div style="display:flex;border-radius:8px;overflow:hidden;">
  <div style="flex:1;border:2px solid #22c55e;border-radius:8px 0 0 8px;overflow:hidden;">
    <div style="padding:14px 16px;background:#f0fdf4;border-bottom:1px solid #dcfce7;">
      <div style="font-size:16px;font-weight:900;color:#15803d;">Phase 1</div>
      <div style="font-size:10px;color:#22c55e;">时间范围</div>
    </div>
    <div style="padding:16px;font-size:11px;line-height:2;">
      <div><span class="sn sn-b">1</span> 里程碑1</div>
      <div><span class="sn sn-g">2</span> 里程碑2</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;background:#f0fdf4;border-top:2px solid #22c55e;border-bottom:2px solid #22c55e;padding:0 4px;">
    <span style="color:#22c55e;font-size:20px;font-weight:900;">→</span>
  </div>
  <div style="flex:1;border:2px solid #3b82f6;border-left:none;overflow:hidden;">
    <!-- Phase 2 -->
  </div>
</div>
```

## 注意事项

1. **Tab 索引**：`sw(i)` 的 `i` 从 0 开始，与 `.pw` 的 `id="tN"` 一一对应
2. **字体**：正文 `'HarmonyOS Sans SC','Plus Jakarta Sans',system-ui,sans-serif`，代码/数据用 `IBM Plex Mono`
3. **内联样式**：卡片样式推荐内联写，方便快速调整
4. **性能**：每个 Tab 80-200 行，不需要像 interaction-map 那样严格分步

## SVG 拓扑图（可选扩展）

如果确实需要画**真正的系统拓扑图**（节点 + 箭头连线），请读取：

```
view .claude/skills/architecture-diagrams/references/components-cheatsheet.md
view .claude/skills/architecture-diagrams/references/svg-topology-extension.md
```

components-cheatsheet.md 包含绝对定位节点 `.n` 和 SVG 箭头的完整模板。但**大部分方案文档不需要拓扑图**，用 CSS Grid 卡片 + 表格就能讲清楚。

## 自检清单

- [ ] Tab 数量与 context.md / scene-list.md 中的模块/阶段一致
- [ ] 每个 Tab 标题与 context.md 中的术语一致
- [ ] SVG 拓扑图（如有）节点可点击、箭头方向正确
- [ ] 字体：正文 `'HarmonyOS Sans SC','Plus Jakarta Sans',system-ui,sans-serif`，代码 `IBM Plex Mono`
- [ ] 配色使用 css-template.css 中定义的语义色（蓝/绿/红/灰），无硬编码色值冲突
- [ ] 所有表格列宽合理、无溢出截断
- [ ] 无占位符残留（`待填充`、`TBD`、`TODO`）
- [ ] 脚本存入 `scripts/` 命名 `gen_arch_v{N}.py`，与产出物成对交付
