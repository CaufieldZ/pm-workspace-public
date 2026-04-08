# PPT 满分产物片段库

从 SOP-final.html（PM AI 提效工作流 SOP V2.0）提炼。参考叙事模式和结构骨架，不复制业务内容。

## 1. Overview 页 — 先冲击后选择

**满分模式**：hero 数字开场（3 个核心指标）→ 核心概念图（context.md 驱动一切）→ 决策树（3 级复杂度）→ 双路径选择卡片 → 差异对比表 → 最佳实践 note

**结构骨架**：

```html
<div class="page active">
  <div class="page-title">标题</div>
  <div class="page-subtitle">一句话定位</div>

  <!-- hero 数字 — 开场冲击 -->
  <div class="grid3">
    <div class="card" style="text-align:center;">
      <div class="hero-num"><div class="val text-green">数字</div><div class="lbl">指标名</div></div>
    </div>
    <!-- ×3 -->
  </div>

  <!-- 核心概念图 — 建立心智模型 -->
  <div class="section-label">核心概念</div>
  <div class="card" style="border-top:3px solid var(--blue);">
    <!-- 竖向流程：输入 → 处理 → 核心产物 → 下游 -->
  </div>

  <!-- 决策树 — 帮听众选路 -->
  <div class="section-label">决策树</div>
  <div class="grid3">
    <div class="card" style="border-top:3px solid var(--green);">简单</div>
    <div class="card" style="border-top:3px solid var(--blue);">复杂</div>
    <div class="card" style="border-top:3px solid var(--purple);">超复杂</div>
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

**满分模式**：场景 A（新建流程图 + 命令速查表）→ 场景 B（变更级联 pipe 6 步 + 依赖链可视化）→ 对比表（同一变更两轨体验）→ troubleshooting 手风琴

**结构骨架**：

```html
<div class="page active">
  <div class="page-title">日常操作</div>
  <div class="page-subtitle">两个场景，后者是差异化杀手锏</div>

  <!-- 场景 A — 简单流程 -->
  <div class="section-label">场景 A</div>
  <div class="card" style="background:var(--bg);">
    <!-- 横排流程：span → → span → → span -->
  </div>
  <table class="cmp-table"><!-- 命令速查表 --></table>

  <!-- 场景 B — 复杂流程（重点） -->
  <div class="section-label">场景 B <span class="tag tag-red">差异化</span></div>
  <div class="note">为什么这是杀手级场景</div>
  <div class="card">
    <div class="pipe"><!-- 6 步 pipe-node --></div>
  </div>
  <!-- dependency-chain 可视化 -->
  <div class="card" style="background:var(--bg);"><!-- 依赖链 --></div>

  <!-- 对比表 -->
  <table class="cmp-table"><!-- 步骤 | 方案A | 方案B --></table>

  <!-- Troubleshooting 手风琴 -->
  <div class="section-label">常见问题</div>
  <div class="accordion">...</div>
  <div class="accordion">...</div>
</div>
```

## 4. b-infra 页 — 总分总

**满分模式**：四层防线全景图开场 → note 解释为什么对手做不到 → 01-04 编号章节逐个展开（每个有图标卡 + checklist/表格）→ 对比收尾表 → 总结 note

**结构骨架**：

```html
<div class="page active">
  <div class="page-title">护城河</div>

  <!-- 全景图 — 四层横排 -->
  <div class="card" style="background:var(--bg);">
    <div style="display:flex;justify-content:center;gap:12px;">
      <div>层 1</div> → <div>层 2</div> → <div>层 3</div> → <div>层 4</div>
    </div>
  </div>
  <div class="note">为什么对手做不到</div>

  <!-- 01-04 逐个展开 -->
  <div class="section-label">01 · 主题</div>
  <div class="card" style="border-left:3px solid var(--orange);">
    <!-- 图标 + 标题 + 描述 + grid/table/checklist -->
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
