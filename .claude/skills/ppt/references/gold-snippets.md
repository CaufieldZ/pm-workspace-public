<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PPT 满分产物片段库

从 SOP-final.html（PM AI 提效工作流 SOP V2.0）提炼。参考叙事模式和结构骨架，不复制业务内容。

## 1. Overview 页 — 呼吸开场 + 先冲击后选择

**满分模式**：page-hero 呼吸页开场（大字标题 + 副标题留白）→ stat-card 数字冲击（3 个核心指标）→ flow-h 横向流程（核心链路 ≤4 步）→ 决策树（3 级复杂度）→ page-split 分隔带 → 双路径选择卡片 → 差异对比表 → 最佳实践 note

**结构骨架**：

```html
<!-- 呼吸页开场 — 大量留白建立基调 -->
<div class="page-hero">
  <div class="hero-accent" style="background:var(--blue-bg);color:var(--blue);">标签文字</div>
  <div class="hero-headline">大标题<br><span class="text-blue">高亮关键词</span></div>
  <div class="hero-sub">一句话价值主张，建立听众预期。</div>
</div>

<div class="page active">
  <div class="page-title">标题</div>
  <div class="page-subtitle">一句话定位</div>

  <!-- stat-card 数字冲击 — 替代 hero-num -->
  <div class="grid3">
    <div class="card stat-card">
      <div class="stat-val text-green">数字</div>
      <div class="stat-lbl">指标名</div>
    </div>
    <!-- ×3 -->
  </div>

  <!-- flow-h 核心链路 — ≤4 步用横向时间线 -->
  <div class="flow-h">
    <div class="flow-h-step active">
      <div class="fh-num" style="background:var(--blue-bg);color:var(--blue);">1</div>
      <div class="fh-label">输入</div>
      <div class="fh-desc">简短描述</div>
    </div>
    <div class="flow-h-step">
      <div class="fh-num" style="background:var(--green-bg);color:var(--green);">2</div>
      <div class="fh-label">处理</div>
      <div class="fh-desc">简短描述</div>
    </div>
    <!-- ×3-4 步 -->
  </div>

  <!-- 决策树 — 帮听众选路 -->
  <div class="section-label">决策树</div>
  <div class="grid3">
    <div class="card" style="border-top:3px solid var(--green);">简单</div>
    <div class="card" style="border-top:3px solid var(--blue);">复杂</div>
    <div class="card" style="border-top:3px solid var(--purple);">超复杂</div>
  </div>

  <!-- page-split 分隔带 — 打破节奏 -->
  <div class="page-split">
    <div class="split-num text-blue">01</div>
    <div class="split-body">
      <div class="split-title">路径选择</div>
      <div class="split-desc">根据复杂度选择执行路径。</div>
    </div>
  </div>

  <!-- 双路径选择 -->
  <div class="grid2">
    <div class="track-card track-a">路径 A</div>
    <div class="track-card track-b">路径 B</div>
  </div>

  <!-- 差异表 + 收尾 note -->
  <table class="cmp-table">...</table>
  <div class="note green">最佳实践总结</div>
</div>
```

## 2. context.md 页 — 先图后理

**满分模式**：growth-tree 全景图开场（一个文件长出全部产出物）→ 四重身份卡片（解释为什么能做到）→ 生成流程 pipe → 两轨用法 → 9 章结构折叠 → 未来展望

**结构骨架**：

```html
<div class="page active">
  <div class="page-title">核心概念名</div>
  <div class="page-subtitle">一句话价值主张</div>

  <!-- growth-tree — 开场视觉冲击 -->
  <div class="section-label">从 X 长出的全部 Y</div>
  <div class="card" style="background:var(--bg);">
    <!-- 根节点 → 竖线 → 中间节点 → 叶子横排 → 虚线 → 附属 -->
  </div>
  <div class="note green">一句话总结这张图的核心信息</div>

  <!-- 四重身份 — 解释 why -->
  <div class="section-label">为什么能做到？</div>
  <div class="grid2">
    <div class="card" style="border-left:3px solid var(--green);">身份 1</div>
    <div class="card" style="border-left:3px solid var(--blue);">身份 2</div>
    <div class="card" style="border-left:3px solid var(--orange);">身份 3</div>
    <div class="card" style="border-left:3px solid var(--purple);">身份 4</div>
  </div>

  <!-- pipe 流程 — how -->
  <div class="section-label">怎么产生？</div>
  <div class="pipe">...</div>

  <!-- 参考细节折叠 -->
  <div class="accordion">
    <div class="acc-header">点开查看内部结构</div>
    <div class="acc-body">...</div>
  </div>
</div>
```

## 3. b-daily 页 — 两个场景对比

**满分模式**：场景 A（flow-h 横向流程 + 命令速查表）→ quote-block 核心判断 → 场景 B（pipe 竖向流程 ≥5 步 + flow-h 依赖链）→ 对比表（同一变更两轨体验）→ troubleshooting 手风琴

**结构骨架**：

```html
<div class="page active">
  <div class="page-title">日常操作</div>
  <div class="page-subtitle">两个场景，后者是差异化杀手锏</div>

  <!-- 场景 A — 简单流程，用 flow-h 横向展示 -->
  <div class="section-label">场景 A</div>
  <div class="flow-h">
    <div class="flow-h-step done">
      <div class="fh-num" style="background:var(--green-bg);color:var(--green);">1</div>
      <div class="fh-label">步骤名</div>
      <div class="fh-desc">描述</div>
    </div>
    <!-- ×3-4 步 -->
  </div>
  <table class="cmp-table"><!-- 命令速查表 --></table>

  <!-- quote-block — 场景间的核心判断 -->
  <div class="quote-block">
    你的关键问题是<em>选项 A</em>，还是<em>选项 B</em>？
  </div>

  <!-- 场景 B — 复杂流程（≥5 步用 pipe，与场景 A 的 flow-h 形成横竖交替） -->
  <div class="section-label">场景 B <span class="tag tag-red">差异化</span></div>
  <div class="note">为什么这是杀手级场景</div>
  <div class="card">
    <div class="pipe"><!-- ≥5 步 pipe-node --></div>
  </div>
  <!-- dependency-chain 用 flow-h 可视化（横向展示依赖顺序） -->
  <div class="flow-h">
    <div class="flow-h-step">
      <div class="fh-num" style="background:var(--orange-bg);color:var(--orange);">1</div>
      <div class="fh-label">变更源</div>
    </div>
    <div class="flow-h-step">
      <div class="fh-num" style="background:var(--blue-bg);color:var(--blue);">2</div>
      <div class="fh-label">中间节点</div>
    </div>
    <div class="flow-h-step">
      <div class="fh-num" style="background:var(--blue-bg);color:var(--blue);">3</div>
      <div class="fh-label">受影响节点</div>
    </div>
  </div>

  <!-- 对比表 -->
  <table class="cmp-table"><!-- 步骤 | 方案A | 方案B --></table>

  <!-- Troubleshooting 手风琴 -->
  <div class="section-label">常见问题</div>
  <div class="accordion">...</div>
  <div class="accordion">...</div>
</div>
```

## 4. b-infra 页 — 总分总

**满分模式**：flow-h 四层防线全景图开场（横向时间线组件化）→ quote-block 核心判断 → 01-04 编号章节逐个展开（每个有 icon-box + checklist/表格）→ 对比收尾表 → 总结 note

**结构骨架**：

```html
<div class="page active">
  <div class="page-title">护城河</div>

  <!-- 全景图 — 用 flow-h 组件化（替代 inline flex） -->
  <div class="flow-h">
    <div class="flow-h-step done">
      <div class="fh-num" style="background:var(--green-bg);color:var(--green);">1</div>
      <div class="fh-label">层 1</div>
      <div class="fh-desc">描述</div>
    </div>
    <div class="flow-h-step">
      <div class="fh-num" style="background:var(--blue-bg);color:var(--blue);">2</div>
      <div class="fh-label">层 2</div>
      <div class="fh-desc">描述</div>
    </div>
    <!-- ×4 层 -->
  </div>

  <!-- quote-block 核心判断（替代 note 里塞金句） -->
  <div class="quote-block">
    为什么对手<em>做不到</em>？
  </div>

  <!-- 01-04 逐个展开 -->
  <div class="section-label">01 · 主题</div>
  <div class="card" style="border-left:3px solid var(--orange);">
    <div style="display:flex;gap:12px;align-items:flex-start;">
      <div class="icon-box" style="background:var(--orange-bg);">🛡️</div>
      <div><!-- 标题 + 描述 + grid/table/checklist --></div>
    </div>
  </div>
  <!-- 重复 02, 03, 04 -->

  <!-- 对比收尾 -->
  <table class="cmp-table"><!-- 维度 | 对手 | 我方 --></table>
  <div class="note green">一句话总结</div>
</div>
```

## 5. b-models 页 — 结论前置、细节折叠

**满分模式**：CC Switch 说明 note → 速查表前置（什么任务用什么模型）→ 模型详情卡片逐个展开 → 探针评测折叠

**结构骨架**：

```html
<div class="page active">
  <div class="page-title">模型介绍</div>
  <div class="note">前置说明</div>

  <!-- 速查表 — 先给结论 -->
  <div class="section-label">先看结论</div>
  <table class="cmp-table"><!-- 任务 | 推荐 | 理由 --></table>

  <!-- 详情卡片 — 再展开 -->
  <div class="section-label">模型详情</div>
  <div class="card" style="border-left:3px solid var(--purple);">
    <!-- logo + 名称 + 标签 + 描述 + 探针评测摘要 -->
  </div>
  <!-- 重复每个模型 -->

  <!-- 参考细节折叠 -->
  <div class="accordion">
    <div class="acc-header">评测原理详情</div>
    <div class="acc-body"><!-- 完整评测表 --></div>
  </div>

  <div class="note green">成本模型总结</div>
</div>
```

## 6. b-skills 页 — 总览 + 按需展开

**满分模式**：顶部速查表（全部 Skill 一行一条）→ 手风琴逐个展开详情（工作原理 + 核心能力 + vs 对手）→ 共同模式总结 note

**结构骨架**：

```html
<div class="page active">
  <div class="page-title">产出物总览</div>

  <!-- 速查表 -->
  <table class="cmp-table">
    <!-- 名称 | 类型 | 模型 | 耗时 | 格式 | 质量 -->
  </table>

  <!-- 手风琴详情 -->
  <div class="accordion">
    <div class="acc-header">产出物名 + 命令</div>
    <div class="acc-body">
      <!-- 工作原理 / 核心能力 / vs 对手 三段 -->
    </div>
  </div>
  <!-- 重复每个产出物 -->

  <div class="note green">共同模式总结</div>
</div>
```

## 7. 节奏编排 — 页面类型交替示意

**核心原则**：AI 生成 PPT 最大破绽是「太均匀」，每页同一套三明治。用呼吸页打断、横竖交替、主组件不重复来制造节奏变化。

**10 页文档的节奏示例**：

```
页 1  page-hero          ← 呼吸页开场（大字留白）
页 2  stat-card + grid3  ← 数字冲击
页 3  flow-h             ← 横向流程（≤4 步）
页 4  card + cmp-table   ← 卡片 + 表格混排
页 5  page-split         ← 分隔带（Part 转场）
页 6  pipe               ← 竖向流程（≥5 步，与页3横竖交替）
页 7  quote-block + grid2← 金句 + 双栏对比
页 8  accordion + note   ← 折叠细节 + 提示
页 9  page-hero          ← 呼吸页（每 4-6 页插入一个）
页10  cmp-table + note   ← 收尾对比表 + 总结
```

**反面教材（均匀三明治）**：

```
页 1  section-label → grid3 → note     ← 三明治 A
页 2  section-label → grid3 → note     ← 三明治 A（重复！）
页 3  section-label → pipe → note      ← 三明治 B
页 4  section-label → pipe → note      ← 三明治 B（重复！）
页 5  section-label → cmp-table → note ← 三明治 C
... 全文无呼吸页、无 quote-block、无 flow-h、无 page-split
```

**自检清单**：
- [ ] 相邻两页主组件不同
- [ ] 每 4-6 页有一个 page-hero 或 page-split
- [ ] pipe 和 flow-h 交替出现（不全是竖向）
- [ ] quote-block 用于核心判断（不塞进 note）
- [ ] stat-card 用于数字展示（不用 inline hero-num）
- [ ] 每页 emoji ≤ 3 个，section-label 无 emoji
