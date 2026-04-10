<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PPT 组件速查表

从 SOP-final.html 提取的所有可复用组件模式。

## 布局组件

### `.page` — 页面容器
```html
<div class="page active">
  <div class="page-title">标题</div>
  <div class="page-subtitle">副标题描述</div>
  <!-- 内容 -->
</div>
```
- 每个 Tab 的顶层容器
- `.active` 控制显示/隐藏
- `max-width: 1200px; margin: 0 auto;`

### `.grid2` / `.grid3` / `.grid4` — 网格布局
```html
<div class="grid2">
  <div class="card">左栏</div>
  <div class="card">右栏</div>
</div>
```
- 响应式：`max-width: 900px` 以下自动变为单列
- `gap: 16px`

### `.pipe` — 纵向流程链
```html
<div class="pipe">
  <div class="pipe-node">
    <div class="pipe-icon" style="background:var(--blue-bg);">📥</div>
    <div>
      <div style="font-weight:800;margin-bottom:4px;">步骤标题</div>
      <div class="card-desc">步骤描述</div>
    </div>
  </div>
  <div class="pipe-arrow"></div>
  <div class="pipe-node">...</div>
</div>
```
- 适合 ≥5 步流程
- 与 `.flow-h` 交替使用，避免全文都是竖向 pipe

### `.flow-h` — 横向时间线

```html
<div class="flow-h">
  <div class="flow-h-step">
    <div class="fh-num" style="background:var(--blue-bg);color:var(--blue);">1</div>
    <div class="fh-label">步骤标题</div>
    <div class="fh-desc">简短描述</div>
  </div>
  <div class="flow-h-step active"><!-- 高亮当前步 -->...</div>
  <div class="flow-h-step done"><!-- 已完成步 -->...</div>
</div>
```
- 适合 ≤4 步流程、依赖链展示
- 首尾自动圆角，中间步骤间有 `::after` 三角箭头
- `.active` = 蓝色高亮，`.done` = 绿色高亮

### `.page-hero` — 呼吸页

```html
<div class="page-hero">
  <div class="hero-accent" style="background:var(--blue-bg);color:var(--blue);">标签文字</div>
  <div class="hero-headline">大标题<br><span class="text-blue">高亮词</span></div>
  <div class="hero-sub">副标题描述，一两句话。</div>
</div>
```
- 垂直居中，大量留白，用于首页开场或章节金句
- 每 4-6 个内容页之间应插入一个

### `.page-split` — 分隔带
```html
<div class="page-split">
  <div class="split-num text-blue">01</div>
  <div class="split-body">
    <div class="split-title">Part 标题</div>
    <div class="split-desc">一句话描述这个 Part 讲什么。</div>
  </div>
</div>
```
- 编号超大半透明 + 右侧标题，打破内容页的节奏
- 用在 Part/Track 之间的转场

### `.stat-card` — 数字统计卡

```html
<div class="card stat-card">
  <div class="stat-val text-green">2 min</div>
  <div class="stat-lbl">场景清单</div>
</div>
```
- 替代 `.hero-num` 的 inline style 写法
- 搭配 `.grid3` 展示 3 个核心数字

### `.quote-block` — 金句/引言块
```html
<div class="quote-block">
  你的下游研发是<em>人在写代码</em>，还是 <em>AI 在写代码</em>？
</div>
```
- 大字居中斜体，`<em>` 标签自动蓝色加粗高亮
- 用于核心判断、分叉问题，替代塞进 `.note` 里的金句

### `.icon-box` / `.flow-chip` — 通用 utility

```html
<div class="icon-box" style="background:var(--blue-bg);">📋</div>
<span class="flow-chip">会议纪要</span>
```
- `.icon-box`: 44px 圆角图标容器，替代 inline 的 width+height+border-radius 组合
- `.flow-chip`: 行内胶囊标签，替代 inline 的 padding+bg+border-radius 组合

## 内容组件

### `.card` — 通用卡片
```html
<div class="card">
  <div class="card-title">标题</div>
  <div class="card-desc">描述文字</div>
</div>
```
- 变体：`style="border-top:3px solid var(--blue);"` 顶部色条
- 变体：`style="border-left:3px solid var(--green);"` 左侧色条
- 变体：`style="background:var(--bg);border-color:var(--border);"` 深底色

### `.section-label` — 章节标签
```html
<div class="section-label">章节标题</div>
<div class="section-label" style="margin-top:40px;">带间距的章节标题</div>
```

### `.hero-num` — 大数字展示
```html
<div class="card" style="text-align:center;padding:20px;">
  <div class="hero-num">
    <div class="val text-green">2 min</div>
    <div class="lbl">场景清单</div>
  </div>
</div>
```

## 标签 & 徽章

### `.tag-*` — 彩色标签
```html
<span class="tag tag-blue">蓝色标签</span>
<span class="tag tag-green">绿色标签</span>
<span class="tag tag-orange">橙色标签</span>
<span class="tag tag-purple">紫色标签</span>
<span class="tag tag-red">红色标签</span>
```

### `.score` — 分数徽章
```html
<span class="score score-mid">预期 60-80 分</span>
<span class="score score-high">预期 85-90 分</span>
```

### `.text-*` — 文字颜色
```html
<span class="text-blue">蓝色</span>
<span class="text-green">绿色</span>
<span class="text-orange">橙色</span>
<span class="text-purple">紫色</span>
<span class="text-red">红色</span>
```

## 提示框

### `.note` — 左边框提示框
```html
<div class="note">
  <strong>标题：</strong>内容
</div>
<div class="note green"><strong>正面：</strong>内容</div>
<div class="note orange"><strong>警告：</strong>内容</div>
```
- 默认蓝色左边框
- `.green` 绿色、`.orange` 橙色变体

## 表格

### `.cmp-table` — 对比表格
```html
<table class="cmp-table">
  <thead><tr><th>列1</th><th>列2</th><th>列3</th></tr></thead>
  <tbody>
    <tr>
      <td style="color:var(--t1);font-weight:700;">行标题</td>
      <td>内容</td>
      <td>内容</td>
    </tr>
  </tbody>
</table>
```

## 列表

### `.ck-item` + `.ck-num` — 编号清单
```html
<div class="card">
  <div class="ck-item">
    <div class="ck-num">1</div>
    <div>内容文字</div>
  </div>
  <div class="ck-item">
    <div class="ck-num" style="background:var(--green-bg);color:var(--green);">2</div>
    <div>带颜色编号的内容</div>
  </div>
</div>
```
- `.ck-num` 颜色变体：`style="background:var(--green-bg);color:var(--green);"` 等

## 折叠

### `.accordion` — 折叠展开
```html
<div class="accordion">
  <div class="acc-header" onclick="toggleAcc(this)">
    <span>问题文本</span>
    <span class="arrow">▶</span>
  </div>
  <div class="acc-body">展开内容</div>
</div>
```

## 代码/文本展示

### `.prompt-block` — 代码块（含复制）
```html
<div class="prompt-block">
  <div class="prompt-header">
    <span class="label">文件名.txt</span>
    <button class="copy-btn" onclick="copyPrompt(this, 'key')">复制 Prompt</button>
  </div>
  <div class="prompt-body">展示内容</div>
</div>
```
- 需要 JS 配合：`PROMPTS = {};` + `copyPrompt()` 函数

## 展示卡片

### `.gallery-card` — 图文展示
```html
<div class="gallery-card">
  <div class="gallery-preview">📐</div>
  <div class="gallery-info">
    <h4>标题</h4>
    <p>描述文字</p>
  </div>
</div>
```

### `.skill-card` — 技能卡片
```html
<div class="skill-card">
  <span class="model-tag sonnet">Sonnet</span>
  <div style="font-size:14px;font-weight:800;margin-bottom:4px;">标题</div>
  <div style="font-size:11px;color:var(--t3);">副标题</div>
</div>
```

### `.track-card` — 路径选择卡片
```html
<div class="track-card track-a" onclick="goPage('tab-id')">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
    <span class="tag tag-green">标签</span>
    <span class="score score-mid">分数</span>
  </div>
  <h3 style="font-size:18px;font-weight:900;margin-bottom:8px;">标题</h3>
  <div class="card-desc">描述内容</div>
</div>
```
- `.track-a` 绿色边框、`.track-b` 蓝色边框

## 嵌套图

### `.nest-*` — 层级关系图
```html
<div class="nest-outer">
  <div class="nest-label purple">外层标签</div>
  <div style="font-size:12px;color:var(--t2);margin-bottom:12px;">描述</div>
  <div class="nest-mid">
    <div class="nest-label blue">中层标签</div>
    <div class="nest-inner">
      <div class="nest-label green">内层标签</div>
      <div class="nest-chip">内容1</div>
      <div class="nest-chip">内容2</div>
    </div>
  </div>
</div>
```

## 弹窗

### `.modal-overlay` — 全屏弹窗
```html
<!-- 触发 -->
<span style="cursor:pointer;color:var(--blue);" onclick="openModal('标题', '内容')">点击打开</span>

<!-- 弹窗结构（已在模板中预设） -->
<!-- JS 函数：
function openModal(title, content) {
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalContent').textContent = content;
  document.getElementById('promptModal').classList.add('show');
}
-->
```

## 杂项

### `code` — 行内代码
```html
<code>context.md</code>
```

### `.divider` — 分割线
```html
<div class="divider"></div>
```

### `.fw9` / `.mono` — 工具类
```html
<span class="fw9">加粗</span>
<span class="mono">等宽字体</span>
```

## 高级组合组件（从满分产物提炼）

### Growth Tree — 发散图

从一个核心节点向下发散出多层子节点。适用于：展示"一个源头生长出多个产出物"、组织架构、技术栈分层等。

```html
<div class="card" style="background:var(--bg);border-color:var(--border);">
  <div style="text-align:center;padding:16px 0 8px;">
    <!-- 根节点 -->
    <div style="display:inline-flex;align-items:center;gap:10px;padding:14px 28px;background:linear-gradient(135deg,rgba(63,185,80,.15),rgba(56,139,253,.10));border:2px solid rgba(63,185,80,.4);border-radius:14px;font-weight:900;font-size:16px;">
      <span style="font-size:22px;">📄</span> 核心节点
    </div>
    <div style="font-size:10px;color:var(--t3);margin-top:6px;">节点说明</div>

    <!-- 竖线连接 -->
    <div style="width:2px;height:24px;background:var(--border);margin:0 auto;"></div>

    <!-- 中间节点（可选） -->
    <div style="display:inline-flex;padding:8px 18px;background:var(--surface);border:1px solid var(--border2);border-radius:8px;font-size:12px;font-weight:700;color:var(--t2);">中间节点</div>

    <div style="width:2px;height:16px;background:var(--border);margin:0 auto;"></div>
    <div style="font-size:10px;color:var(--t3);margin-bottom:12px;">↓ 说明文字</div>

    <!-- 叶子节点横排 -->
    <div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap;">
      <div style="padding:10px 16px;background:var(--surface);border:1.5px solid rgba(56,139,253,.25);border-radius:10px;min-width:120px;">
        <div style="font-weight:800;color:var(--blue);font-size:11px;">叶子 A</div>
        <div style="font-size:10px;color:var(--t3);">描述</div>
      </div>
      <!-- 更多叶子... -->
    </div>

    <!-- 虚线分割 + 附属节点（可选） -->
    <div style="width:100%;border-top:1px dashed var(--border);margin:12px 0;"></div>
    <div style="font-size:10px;color:var(--t3);margin-bottom:10px;">附属说明</div>
    <div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap;">
      <div style="padding:8px 14px;background:var(--surface);border:1px solid var(--border2);border-radius:8px;">
        <div style="font-weight:700;color:var(--orange);font-size:11px;">附属节点</div>
      </div>
    </div>
  </div>
</div>
```

- 颜色区分层级：根 = gradient border、主干 = blue、核心叶子 = purple、附属 = orange
- 竖线用 `width:2px;height:24px;background:var(--border);margin:0 auto;`

### Comparison Flow — 对比流程表

左右两列对比同一个操作在不同条件下的体验。适用于：Chat vs Claude Code、旧方案 vs 新方案、人工 vs 自动化等对比场景。

```html
<table class="cmp-table">
  <thead><tr>
    <th style="width:18%;">步骤</th>
    <th style="width:41%;"><span style="color:var(--green);">方案 A</span></th>
    <th style="width:41%;"><span style="color:var(--blue);">方案 B</span></th>
  </tr></thead>
  <tbody>
    <tr>
      <td style="color:var(--t1);font-weight:700;">步骤名</td>
      <td>方案 A 的做法</td>
      <td>方案 B 的做法</td>
    </tr>
    <!-- 更多行... -->
  </tbody>
</table>
```

- 基于 `.cmp-table` 组件，表头用颜色区分阵营
- 第一列是步骤/维度名，加粗 + `color:var(--t1)`

### Dependency Chain — 依赖链可视化

从根节点向下展示依赖关系 + pipeline 顺序。适用于：变更波及范围、构建链路、数据流向等。

```html
<div class="card" style="background:var(--bg);border-color:var(--border);">
  <div style="text-align:center;padding:8px 0;">
    <!-- 变更源 -->
    <div style="display:inline-flex;padding:10px 20px;background:var(--surface);border:1.5px solid rgba(210,153,34,.3);border-radius:10px;font-weight:800;font-size:13px;color:var(--orange);">变更源头</div>
    <div style="font-size:16px;color:var(--t3);margin:8px 0;">↓</div>

    <!-- 中间节点 -->
    <div style="display:inline-flex;padding:10px 20px;background:var(--surface);border:1.5px solid rgba(56,139,253,.3);border-radius:10px;font-weight:800;font-size:13px;color:var(--blue);">中间节点</div>
    <div style="font-size:16px;color:var(--t3);margin:8px 0;">↓ depends_on</div>

    <!-- 受影响的叶子节点横排 -->
    <div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap;">
      <div style="padding:8px 16px;background:var(--surface);border:1px solid var(--border2);border-radius:8px;font-size:12px;font-weight:700;">
        节点 A <span style="color:var(--t3);font-weight:500;">pos:3</span>
      </div>
      <div style="padding:8px 16px;background:var(--surface);border:1px solid var(--border2);border-radius:8px;font-size:12px;font-weight:700;">
        节点 B <span style="color:var(--t3);font-weight:500;">pos:4</span>
      </div>
      <!-- 更多节点... -->
    </div>
    <div style="font-size:11px;color:var(--t3);margin-top:10px;">
      按 pos 顺序处理：A → B → ...
    </div>
  </div>
</div>
```

- 源头用 orange 边框，中间用 blue，叶子用默认
- `pos:N` 标注执行顺序
- 底部一行说明处理顺序

## JS 工具函数（模板已内置）

| 函数 | 用途 |
|------|------|
| `renderNav()` | 渲染侧边栏导航 |
| `goPage(id)` | 切换页面 |
| `renderPage()` | 渲染当前页面 |
| `escHtml(s)` | HTML 转义 |
| `closeModal()` | 关闭弹窗 |
| `copyModalPrompt()` | 复制弹窗内容 |
| `toggleAcc(el)` | 折叠展开 |

## 需自定义的 JS 函数（填充时按需添加）

| 函数 | 用途 | 模板 |
|------|------|------|
| `copyPrompt(btn, key)` | 复制 prompt-block 内容 | 见 SOP-final.js |
| `copyTemplate(btn, key)` | 复制模板内容 | 见 SOP-final.js |
