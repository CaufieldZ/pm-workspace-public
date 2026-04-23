<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PPT 满分产物片段库（Claude Design 编辑范式）

参照 `_shared/claude-design/demos/ppt-sample.html` 与 Anthropic Claude Design 系统提炼。范式关键词：**editorial · 印刷感 · 大量留白 · mono eyebrow · serif display · 1px hairline**，拒绝 Notion/GitHub Primer 风的「圆角卡片 + 左 border accent + 彩色徽章 + emoji icon-box」。

所有片段基于 `ppt-template.html` 已内联的 editorial 工具类：`.eyebrow` / `.hairline` / `.display` / `.lede` / `.section-label` / `.figure-num` / `.pullquote` / `.watermark-tl` / `.film-grain`。

## 1. Hero 页 — eyebrow 起手 + serif display 主标 + hairline 结尾

**满分模式**：留白为王。eyebrow 小字 mono 定类别，display-xl 衬线大字下压 1/3 视觉重量，lede 一句话定基调，底部 hairline-accent 2px × 80px 作刻度收尾。整页不超过 4 个元素。

```html
<div class="page active film-grain">
  <div class="watermark-tl">PM · WORKSPACE</div>

  <div class="eyebrow eyebrow-accent">CHAPTER 01 — AI 产品工作流</div>
  <h1 class="display display-xl">心智的<br>可塑性</h1>
  <div class="lede">Agent 不是工具，它有自己的偏好。这一节解释 PM 如何在模型的偏好之上搭建工作台。</div>
  <div class="hairline-accent"></div>
</div>
```

**禁用**：彩色圆角徽章、`page-hero + hero-num + hero-accent` 三件套、任何 emoji 装饰。

## 2. Context 页 — eyebrow 分段 + figure-num 数字冲击

**满分模式**：不用 `stat-card` 居中三栏卡片。改为 editorial 横排：左 figure-num serif 大字，右 figure-lbl mono 小字，整体由 hairline 分隔，无 bg 无 border。

```html
<div class="page active">
  <div class="eyebrow">§ 2 · 项目枢纽</div>
  <h2 class="display display-lg">一个文件长出全部产出物</h2>
  <p class="lede">context.md 是 PM 与 AI 讨论的结构化沉淀，所有下游产出物从它生长。</p>

  <div class="hairline"></div>

  <div class="grid3 gap-6">
    <div>
      <div class="figure-num">20</div>
      <div class="figure-lbl">SKILLS COVERED</div>
    </div>
    <div>
      <div class="figure-num">9</div>
      <div class="figure-lbl">CHAPTERS IN CONTEXT.MD</div>
    </div>
    <div>
      <div class="figure-num">10 MIN</div>
      <div class="figure-lbl">FIRST DELIVERABLE</div>
    </div>
  </div>

  <div class="hairline"></div>
</div>
```

**禁用**：`stat-card` + 圆角卡片 bg、`stat-val text-green` 彩色数字、居中对齐的「数字 + 说明」三栏。

## 3. 对比页 — 两栏等权 + 顶栏 eyebrow 标签

**满分模式**：左右两栏文本层级自洽，不用 `border-top:3px solid var(--green)` 这种顶部色条区分方案。区分靠 eyebrow 标签 + 内部排版密度差异即可。

```html
<div class="page active">
  <div class="eyebrow">§ 3 · 两轨工作流</div>
  <h2 class="display display-lg">Chat 轨 vs Claude Code 轨</h2>
  <div class="hairline"></div>

  <div class="grid2 gap-8">
    <div>
      <div class="eyebrow">TRACK A — CHAT</div>
      <h3 class="display display-md">打开就用</h3>
      <p class="lede">零依赖，复制 prompt 发送即可。初版 60-80 分，需对话迭代。</p>
      <div class="hairline-sm"></div>
      <ul class="mt-4" style="list-style:none;padding:0;">
        <li class="py-2" style="border-bottom:1px solid var(--border2);color:var(--t2);">上手成本  0</li>
        <li class="py-2" style="border-bottom:1px solid var(--border2);color:var(--t2);">产出质量  60-80</li>
        <li class="py-2" style="color:var(--t2);">可复现性  每次不同</li>
      </ul>
    </div>

    <div>
      <div class="eyebrow eyebrow-accent">TRACK B — CLAUDE CODE</div>
      <h3 class="display display-md">规则兜底</h3>
      <p class="lede">骨架脚本 + 组件库 + 自检规则三重保障。初版 85-90 分。</p>
      <div class="hairline-sm"></div>
      <ul class="mt-4" style="list-style:none;padding:0;">
        <li class="py-2" style="border-bottom:1px solid var(--border2);color:var(--t2);">上手成本  需安装</li>
        <li class="py-2" style="border-bottom:1px solid var(--border2);color:var(--t2);">产出质量  85-90</li>
        <li class="py-2" style="color:var(--t2);">可复现性  规则保障</li>
      </ul>
    </div>
  </div>
</div>
```

**禁用**：`track-card track-a/track-b` 预设色板卡片、左 / 顶 border-accent、圆角 + bg-tint 卡片。

## 4. 流程页 — 编号 + hairline 分段，不用彩色圆形徽章

**满分模式**：流程步骤竖排或横排都可，但编号用 `.eyebrow` 形式（「STEP 01」）而不是 `fh-num` 彩色圆圈。步骤间用 hairline 分隔，描述文字层级自洽。

```html
<div class="page active">
  <div class="eyebrow">§ 4 · 复杂链路</div>
  <h2 class="display display-lg">8 步从需求到交付</h2>
  <div class="hairline"></div>

  <div class="grid1 gap-0">
    <div class="py-4" style="border-bottom:1px solid var(--border2);">
      <div class="eyebrow">STEP 01 — SCENE-LIST</div>
      <h3 class="display display-md">场景拆解</h3>
      <p style="color:var(--t2);font-size:14px;line-height:1.7;max-width:640px;">把需求拆解为编号锁定的场景单元，后续所有产出物复用同一套编号。</p>
    </div>
    <div class="py-4" style="border-bottom:1px solid var(--border2);">
      <div class="eyebrow">STEP 02 — REQUIREMENT-FRAMEWORK</div>
      <h3 class="display display-md">需求框架（可选）</h3>
      <p style="color:var(--t2);font-size:14px;line-height:1.7;max-width:640px;">场景 ≥ 5 个时用模块化需求条目整理，为 IMAP 做准备。</p>
    </div>
    <div class="py-4">
      <div class="eyebrow eyebrow-accent">STEP 03 — INTERACTION-MAP</div>
      <h3 class="display display-md">交互大图</h3>
      <p style="color:var(--t2);font-size:14px;line-height:1.7;max-width:640px;">多端 UI 流 + 跨端数据流，Mockup 级视觉化。</p>
    </div>
  </div>
</div>
```

**禁用**：`flow-h-step` 彩色圆圈编号、`fh-num` + `--blue-bg/--green-bg` bg 徽章、`pipe-icon` + emoji 盒。

## 5. 结论前置页 — pullquote 引用 + 下方细节收折

**满分模式**：核心判断做成 `.pullquote`（serif 28px + 左侧 1px accent 竖线 + mono cite 小字署名）。下方再铺展细节。不用 `quote-block` 居中斜体。

```html
<div class="page active">
  <div class="eyebrow">§ 5 · 一条结论</div>

  <div class="pullquote">
    模型能替你做的事，写 SKILL.md 之前先判断是不是「你自己会做的事」。
    <div class="pullquote-cite">— PM-WORKFLOW §1·PM 职责边界</div>
  </div>

  <div class="hairline"></div>

  <h3 class="display display-md mt-6">三条具体规则</h3>
  <ul style="list-style:none;padding:0;margin-top:16px;">
    <li class="py-3" style="border-bottom:1px solid var(--border2);color:var(--t2);">
      <span class="eyebrow" style="margin-right:12px;">01</span>走查只做功能 / 流程 / 业务规则，不做样式还原
    </li>
    <li class="py-3" style="border-bottom:1px solid var(--border2);color:var(--t2);">
      <span class="eyebrow" style="margin-right:12px;">02</span>推荐新 Skill 前先过「这是 PM 做的事吗」过滤
    </li>
    <li class="py-3" style="color:var(--t2);">
      <span class="eyebrow" style="margin-right:12px;">03</span>跨角色的活提一句就走，不主动建对应 skill
    </li>
  </ul>
</div>
```

**禁用**：居中斜体 `quote-block`、`note green/blue/orange` 彩色提示块。

## 6. 章节转场 — section-label（mono 大 tracking）替代 page-split

**满分模式**：章节切换用 `.section-label`（bottom hairline + eyebrow 升级版）做内联分段，或者整页独立 hero 做 Part 转场。不用 `page-split` 的「大数字 01 + 标题 + 描述」彩色分隔带。

整页 Part 转场：

```html
<div class="page active film-grain" style="display:flex;flex-direction:column;justify-content:center;padding:120px 96px;">
  <div class="watermark-tl">PART II</div>
  <div class="eyebrow eyebrow-accent">— PART II —</div>
  <h1 class="display display-xl" style="margin:16px 0 32px;">工程化</h1>
  <div class="lede">从 SKILL 到 pipeline，从骨架到填充。</div>
  <div class="hairline-accent"></div>
</div>
```

内联分段（页中分 section）：

```html
<div class="section-label">§ 6.2 — 防腐化机制</div>
<!-- 下方正常内容 -->
```

**禁用**：`page-split + split-num text-blue + split-body` 三层嵌套、左竖条 + 大 01 + 多行描述的「转场卡」范式。

## 7. 节奏编排 — 页面类型交替示意

**核心原则**：AI 生成 PPT 的最大破绽是「太均匀」，每页同一套三明治。Claude Design 的节奏靠 **hero 呼吸页 ⇄ 内容密集页 ⇄ pullquote 断句页** 三种密度交替。

**10 页 deck 节奏示例**：

```
页 1  Hero（§1）                 ← 呼吸页开场：eyebrow + display-xl + lede + hairline-accent
页 2  Context figure-num（§2）   ← 数字冲击：editorial 横排 figure-num，非 stat-card
页 3  对比双栏（§3）             ← 两栏等权，eyebrow 分类，无 border-accent
页 4  流程步骤（§4）             ← 编号用 eyebrow（STEP 01），hairline 分段
页 5  Part 转场（§6）            ← film-grain + display-xl，大面积留白
页 6  对比表（cmp-table）        ← 密集数据页，表内不用彩色徽章
页 7  pullquote 结论（§5）       ← 断句页：serif 28px 引用 + 左侧 1px accent
页 8  流程步骤（§4 另一组）      ← 与页 4 呼应但编号 / 排列变化
页 9  Hero（§1 改版）            ← 呼吸页再现，每 4-6 页插入
页10  cmp-table + pullquote      ← 收尾：数据 + 判断
```

**反面教材（AI slop 三明治）**：

```
页 1  section-label → grid3(card+icon-box+border-top) → note
页 2  section-label → grid3(card+icon-box+border-top) → note  ← 重复
页 3  section-label → pipe(fh-num+emoji) → note
页 4  section-label → pipe(fh-num+emoji) → note               ← 重复
...
```

## 8. 自检清单（Claude Design 合规）

- [ ] 相邻两页主组件不同（hero / figure / 对比 / 流程 / pullquote / Part 转场 交替）
- [ ] 每 4-6 页插入一次 `film-grain + watermark-tl` 呼吸页
- [ ] pullquote 用于核心判断，不塞进彩色 note 块
- [ ] 编号 / 分类统一用 `.eyebrow`（mono + uppercase + 大 tracking），禁止彩色圆角徽章
- [ ] 页面分隔用 `.hairline` / `.section-label`，禁止 `border-top:3px solid var(--color)` 顶部色条
- [ ] 卡片禁带 icon-box + emoji 组合（反 AI slop 六禁）
- [ ] 大标题用 `.display`（Noto Serif SC），禁止全文只用 `font-weight:900` sans
- [ ] 强调色最多出现 `--blue` 一种（figure / accent / pullquote 左竖线），禁止 green/orange/purple/red/pink 同页堆叠
- [ ] 每页 emoji ≤ 0（Claude Design 禁 emoji 装饰），业务 icon 用 inline SVG 或 mono 字符
