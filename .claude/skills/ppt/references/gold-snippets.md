<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PPT 满分产物片段库（叙事模式 × Claude Design 视觉）

> ⚠️ **CSS 变量纪律**（所有生成脚本必读）
>
> **禁止**在生成脚本里手抄 `:root { --cd-bg: #000; --cd-ink: #fff; ... }` 整块定义。
> **必须**通过文件读取引入，源头唯一是 `.claude/skills/_shared/claude-design/tokens.css`。
>
> Node.js 脚本正确写法：
> ```js
> const SHARED_CD = path.join(__dirname, '..', '..', '..', '.claude', 'skills', '_shared', 'claude-design');
> const TOKENS_CSS = fs.readFileSync(path.join(SHARED_CD, 'tokens.css'), 'utf8');
> const CSS = `
> ${TOKENS_CSS}
>
> /* 项目级扩展 token，只写 tokens.css 没有的（如 --cd-surface2 / --cd-ok/err/warn） */
> :root { --cd-surface: #080808; --cd-ok: #00B42A; --cd-err: #F53F3F; --cd-warn: #D29922; }
> `;
> ```
>
> Python 脚本同理用 `open(tokens_css_path).read()` 拼接。手抄的后果：tokens.css 改字体 / 改色，产物不跟着变，两处不一致。
>
> **字体 `<link>` 纪律**：tokens.css 顶部注释里的 CDN URL 是**完整字体清单**，不是模板。实际用到哪几种就只引哪几种。中文 PPT 最小集 = Noto Sans SC + Noto Serif SC + JetBrains Mono 三家，多引一个 Lora / Poppins 白白多下载 ~50KB。

---

从 SOP-final.html 提炼 6 种 **通用叙事骨架**（和视觉系统正交，放 Anthropic/Apple/Notion keynote 都成立），外加 Claude Design **editorial 视觉填充**（`_shared/claude-design/demos/ppt-sample.html` 对标）。

**叙事选型**：先判断页面类型 → 选一种叙事骨架 → 用 Claude Design 组件填每一步。

| 页面类型 | 叙事骨架 | 关键动作 |
|---|---|---|
| 总览 / 开场 | §1 先冲击后选择 | 数字震撼 → 决策树分路 → 对比收尾 |
| 认知 / 概念 | §2 先图后理 | 全景图开场 → 为什么 → 怎么做 |
| 案例 / 日常 | §3 两情景对比 | 场景 A 演一遍 → 核心判断 → 场景 B 演一遍 |
| 纲领 / 护城河 | §4 总分总 | 全景 → 逐项展开 → 对比收尾 |
| Reference / 选型 | §5 结论前置 + 折叠 | 速查表前置 → 详情 → 原理折叠 |
| 索引 / 目录 | §6 总览 + 按需展开 | 速查表 → 手风琴逐个展开 |

所有示例用 `ppt-template.html` 已内联的 editorial 工具类：`.eyebrow` / `.hairline` / `.display` / `.lede` / `.section-label` / `.figure-num` / `.pullquote` / `.watermark-tl` / `.film-grain`。**禁用**反 AI slop 六禁：彩色圆角徽章、icon-box + emoji、**任意方向 ≥ 2px 的 accent border**（左 / 右 / 上 / 下都不行，换方向不算规避）、同页多色堆叠。

---

## 1. 先冲击后选择（Overview 页）

**叙事骨架**（8 步）：

```
Hero 呼吸开场 → figure-num 数字冲击 → 核心链路概览 → 决策树（分类路径）
  → Part 转场 → 双路径选择 → 差异对比表 → 最佳实践 pullquote
```

**关键动作**：先用大字 + 数字建立基调和可信度，再用决策树帮听众对号入座，最后双路径让听众选一条路走下去。**不给选择的总览 = 灌输**。

**Claude Design 填充**：

```html
<div class="page active film-grain">
  <div class="watermark-tl">OVERVIEW</div>

  <!-- 1. Hero 呼吸开场 -->
  <div class="eyebrow eyebrow-accent">CHAPTER 01 — PM WORKSPACE</div>
  <h1 class="display display-xl">AI 产品工作流<br>全链路工作台</h1>
  <div class="lede">会议纪要 / MRD / 竞品截图 → 场景清单 / 交互大图 / PRD。20 个 Skill 覆盖 PM 全链路。</div>
  <div class="hairline-accent"></div>

  <!-- 2. figure-num 数字冲击（3 个核心指标）-->
  <div class="grid3 gap-6 mt-8">
    <div><div class="figure-num">3-5d → 10min</div><div class="figure-lbl">FIRST DELIVERABLE</div></div>
    <div><div class="figure-num">20</div><div class="figure-lbl">SKILLS COVERED</div></div>
    <div><div class="figure-num">85-90</div><div class="figure-lbl">INITIAL QUALITY</div></div>
  </div>

  <!-- 3. 核心链路（≤4 步，用 eyebrow 编号 + hairline 分段）-->
  <div class="section-label">§ 1.1 · 核心链路</div>
  <div class="grid4 gap-4">
    <div><div class="eyebrow">01 INPUT</div><p class="mt-2" style="color:var(--t2);font-size:13px;">需求 / 纪要</p></div>
    <div><div class="eyebrow">02 CONTEXT</div><p class="mt-2" style="color:var(--t2);font-size:13px;">九章沉淀</p></div>
    <div><div class="eyebrow">03 PIPELINE</div><p class="mt-2" style="color:var(--t2);font-size:13px;">10 Skill 串联</p></div>
    <div><div class="eyebrow eyebrow-accent">04 DELIVERABLES</div><p class="mt-2" style="color:var(--t2);font-size:13px;">AI 可消费</p></div>
  </div>

  <!-- 4. 决策树（3 级复杂度，纯文本 + hairline-sm 分层）-->
  <div class="section-label">§ 1.2 · 决策树</div>
  <ul style="list-style:none;padding:0;">
    <li class="py-3" style="border-bottom:1px solid var(--border2);"><span class="eyebrow">A</span><span style="color:var(--t1);margin-left:12px;">简单（纯功能点 / 单页）</span><span style="color:var(--t3);margin-left:8px;">→ 直接出 Markdown / 原型</span></li>
    <li class="py-3" style="border-bottom:1px solid var(--border2);"><span class="eyebrow">B</span><span style="color:var(--t1);margin-left:12px;">复杂（≥ 2 端 / ≥ 5 场景）</span><span style="color:var(--t3);margin-left:8px;">→ 走 Pipeline 8 步</span></li>
    <li class="py-3"><span class="eyebrow eyebrow-accent">C</span><span style="color:var(--t1);margin-left:12px;">超复杂（多系统 / 资金流）</span><span style="color:var(--t3);margin-left:8px;">→ 插入架构图集</span></li>
  </ul>
</div>

<!-- 5. Part 转场（独立一页，film-grain hero）-->
<div class="page film-grain" style="display:flex;flex-direction:column;justify-content:center;padding:120px 96px;">
  <div class="eyebrow eyebrow-accent">— PART II —</div>
  <h1 class="display display-xl mt-4">路径选择</h1>
  <div class="lede">根据复杂度选择执行路径。</div>
  <div class="hairline-accent"></div>
</div>

<!-- 6-7-8. 双路径 / 对比表 / 最佳实践 pullquote -->
<div class="page active">
  <div class="eyebrow">§ 1.3 · 两轨工作流</div>
  <div class="grid2 gap-8">
    <div><div class="eyebrow">TRACK A — CHAT</div><h3 class="display display-md">打开就用</h3><p class="lede">零依赖，60-80 分。</p></div>
    <div><div class="eyebrow eyebrow-accent">TRACK B — CLAUDE CODE</div><h3 class="display display-md">规则兜底</h3><p class="lede">85-90 分。</p></div>
  </div>
  <div class="hairline mt-6"></div>
  <table class="cmp-table"><!-- 维度 | Chat | Claude Code --></table>
  <div class="pullquote mt-8">两轨混用最佳：AI 方案讨论 → context.md → Claude Code 批量产出。<div class="pullquote-cite">— PM-WORKFLOW 最佳实践</div></div>
</div>
```

---

## 2. 先图后理（认知 / 概念页）

**叙事骨架**（5 步）：

```
全景图开场（growth-tree / 依赖图）→ 四维身份卡（解释 why）
  → 生成流程（how）→ 两轨用法（when）→ 细节折叠（内部结构）
```

**关键动作**：**图先给**，让听众有整体心智模型再讲细节。**禁止**先讲概念定义再配图。

**Claude Design 填充**：

```html
<div class="page active">
  <div class="eyebrow">§ 2 · 项目枢纽</div>
  <h2 class="display display-lg">一个文件长出全部产出物</h2>
  <p class="lede">context.md 是 PM 与 AI 讨论的结构化沉淀，所有下游产出物从它生长。</p>
  <div class="hairline"></div>

  <!-- 1. 全景图开场（editorial 树形，不用彩色 gradient border）-->
  <div class="section-label">§ 2.1 · 从 context.md 长出的全部产出物</div>
  <div style="text-align:center;padding:48px 0;">
    <div class="display display-md">context.md</div>
    <div class="figure-lbl mt-2">ROOT · 唯一真相源</div>
    <div class="hairline-sm" style="margin:24px auto;"></div>
    <div class="grid4 gap-4">
      <div><div class="eyebrow">IMAP</div><div style="color:var(--t2);font-size:12px;">交互大图</div></div>
      <div><div class="eyebrow">PROTO</div><div style="color:var(--t2);font-size:12px;">原型</div></div>
      <div><div class="eyebrow">PRD</div><div style="color:var(--t2);font-size:12px;">docx</div></div>
      <div><div class="eyebrow">BSPEC</div><div style="color:var(--t2);font-size:12px;">行为规格</div></div>
    </div>
  </div>
  <div class="pullquote">改一个术语，下游全部产出物跟着改。<div class="pullquote-cite">— 唯一真相源原则</div></div>

  <!-- 2. 四维身份 — why -->
  <div class="section-label">§ 2.2 · 为什么能做到</div>
  <div class="grid2 gap-6">
    <div><div class="eyebrow">IDENTITY 01</div><h3 class="display display-md">永久记忆体</h3><p style="color:var(--t2);font-size:13px;">换 session / 换模型都不丢。</p></div>
    <div><div class="eyebrow">IDENTITY 02</div><h3 class="display display-md">跨环境协议</h3><p style="color:var(--t2);font-size:13px;">Chat 和 Claude Code 共享同一份。</p></div>
    <div><div class="eyebrow">IDENTITY 03</div><h3 class="display display-md">唯一真相源</h3><p style="color:var(--t2);font-size:13px;">下游产出物全部从这里读取。</p></div>
    <div><div class="eyebrow eyebrow-accent">IDENTITY 04</div><h3 class="display display-md">全生命周期</h3><p style="color:var(--t2);font-size:13px;">每次迭代更新，新对话不用重讲。</p></div>
  </div>

  <!-- 3. 生成流程 — how（eyebrow 编号替代彩色 pipe）-->
  <div class="section-label">§ 2.3 · 怎么产生</div>
  <div class="grid1 gap-0">
    <div class="py-3" style="border-bottom:1px solid var(--border2);"><span class="eyebrow">STEP 01</span><span style="color:var(--t1);margin-left:16px;">会议 / MRD / 截图原始素材</span></div>
    <div class="py-3" style="border-bottom:1px solid var(--border2);"><span class="eyebrow">STEP 02</span><span style="color:var(--t1);margin-left:16px;">与 AI 讨论提炼（Chat / Claude Code）</span></div>
    <div class="py-3"><span class="eyebrow eyebrow-accent">STEP 03</span><span style="color:var(--t1);margin-left:16px;">沉淀为 context.md 九章结构</span></div>
  </div>

  <!-- 4. 9 章折叠 — 内部细节 -->
  <div class="section-label">§ 2.4 · 九章结构（细节）</div>
  <div class="accordion">
    <div class="acc-header" onclick="toggleAcc(this)"><span>点开查看九章完整字段</span><span class="arrow">▶</span></div>
    <div class="acc-body"><!-- 九章字段清单 --></div>
  </div>
</div>
```

---

## 3. 两情景对比（案例 / 日常页）

**叙事骨架**（5 步）：

```
场景 A 完整演一遍 → pullquote 核心判断（两场景间的分叉问题）
  → 场景 B 完整演一遍 → 对比表（同一变更两路径体验差）→ troubleshooting 折叠
```

**关键动作**：**两场景都完整演**，不只列差异。pullquote 的判断要是 **用户真实会问的问题**（「我该选 A 还是 B？」），不是总结句。

**Claude Design 填充**：

```html
<div class="page active">
  <div class="eyebrow">§ 3 · 日常操作</div>
  <h2 class="display display-lg">两个场景 · 后者是差异化杀手锏</h2>
  <div class="hairline"></div>

  <!-- 1. 场景 A 完整流程 -->
  <div class="section-label">§ 3.1 · 场景 A — 单文件修改</div>
  <div class="grid1 gap-0">
    <div class="py-3" style="border-bottom:1px solid var(--border2);"><span class="eyebrow">01</span><span style="color:var(--t1);margin-left:12px;">读 SKILL.md + scene-list</span></div>
    <div class="py-3" style="border-bottom:1px solid var(--border2);"><span class="eyebrow">02</span><span style="color:var(--t1);margin-left:12px;">Edit 修改</span></div>
    <div class="py-3" style="border-bottom:1px solid var(--border2);"><span class="eyebrow">03</span><span style="color:var(--t1);margin-left:12px;">check_html.sh 自检</span></div>
    <div class="py-3"><span class="eyebrow eyebrow-accent">04</span><span style="color:var(--t1);margin-left:12px;">git commit</span></div>
  </div>
  <table class="cmp-table mt-4"><thead><tr><th>命令</th><th>用途</th></tr></thead><tbody><!-- 命令速查表 --></tbody></table>

  <!-- 2. pullquote — 场景间的分叉问题（不是总结，是提问）-->
  <div class="pullquote mt-8">你的变更是改 <em>一个场景</em>，还是改 <em>术语 / 编号</em>（波及全链路）？<div class="pullquote-cite">— 单文件 vs 批量变更的分叉</div></div>

  <!-- 3. 场景 B 完整流程（≥ 5 步，和场景 A 的 4 步呼应）-->
  <div class="section-label">§ 3.2 · 场景 B — 批量变更 <span class="eyebrow eyebrow-accent" style="margin-left:12px;">KILLER</span></div>
  <p class="lede">当变更涉及 ≥ 2 个产出物，走 impact-check 全链路波及扫描。</p>
  <div class="grid1 gap-0 mt-4">
    <div class="py-3" style="border-bottom:1px solid var(--border2);"><span class="eyebrow">01</span><span style="color:var(--t1);margin-left:12px;">列变更清单（所有受影响文件）</span></div>
    <div class="py-3" style="border-bottom:1px solid var(--border2);"><span class="eyebrow">02</span><span style="color:var(--t1);margin-left:12px;">impact-check.sh 波及扫描</span></div>
    <div class="py-3" style="border-bottom:1px solid var(--border2);"><span class="eyebrow">03</span><span style="color:var(--t1);margin-left:12px;">逐文件改（pipeline 顺序）</span></div>
    <div class="py-3" style="border-bottom:1px solid var(--border2);"><span class="eyebrow">04</span><span style="color:var(--t1);margin-left:12px;">cross-check grep 残留</span></div>
    <div class="py-3"><span class="eyebrow eyebrow-accent">05</span><span style="color:var(--t1);margin-left:12px;">旧版归档 archive/</span></div>
  </div>

  <!-- 4. 对比表 -->
  <div class="section-label">§ 3.3 · 同一变更 · 两路径体验</div>
  <table class="cmp-table">
    <thead><tr><th>维度</th><th>场景 A（单文件）</th><th>场景 B（批量）</th></tr></thead>
    <tbody>
      <tr><td style="color:var(--t1);font-weight:700;">耗时</td><td>5 分钟</td><td>30-90 分钟</td></tr>
      <tr><td style="color:var(--t1);font-weight:700;">自检</td><td>check_html.sh</td><td>impact-check + cross-check</td></tr>
    </tbody>
  </table>

  <!-- 5. Troubleshooting 手风琴 -->
  <div class="section-label">§ 3.4 · 常见问题</div>
  <div class="accordion"><div class="acc-header" onclick="toggleAcc(this)"><span>场景编号能改吗</span><span class="arrow">▶</span></div><div class="acc-body">不能。编号确认后全局锁定，新增只追加。</div></div>
  <div class="accordion"><div class="acc-header" onclick="toggleAcc(this)"><span>自检不通过怎么办</span><span class="arrow">▶</span></div><div class="acc-body">自动修复 2 次仍失败则停下报告用户。</div></div>
</div>
```

---

## 4. 总分总（纲领 / 护城河页）

**叙事骨架**（5 步）：

```
N 层全景图（横向时间线）→ pullquote 核心判断（为什么对手做不到）
  → 01-0N 逐个展开（每个 eyebrow 编号 + 内部 checklist）
  → 对比收尾表（维度 × 对手 / 我方）→ pullquote 总结
```

**关键动作**：**开头结尾都要全景**，中间展开细节。对比收尾不能省——「我方强 / 对手弱」要具体到维度。

**Claude Design 填充**：

```html
<div class="page active">
  <div class="eyebrow">§ 4 · 四层防线</div>
  <h2 class="display display-lg">护城河</h2>
  <div class="hairline"></div>

  <!-- 1. 四层全景（eyebrow 横排，非 flow-h 彩色徽章）-->
  <div class="section-label">§ 4.1 · 四层全景</div>
  <div class="grid4 gap-4">
    <div><div class="eyebrow">LAYER 01</div><h3 class="display display-md mt-2">规则层</h3><p style="color:var(--t2);font-size:12px;">CLAUDE.md / pm-workflow</p></div>
    <div><div class="eyebrow">LAYER 02</div><h3 class="display display-md mt-2">Skill 层</h3><p style="color:var(--t2);font-size:12px;">20 个 SKILL.md</p></div>
    <div><div class="eyebrow">LAYER 03</div><h3 class="display display-md mt-2">Hook 层</h3><p style="color:var(--t2);font-size:12px;">pre-commit / pre-compact</p></div>
    <div><div class="eyebrow eyebrow-accent">LAYER 04</div><h3 class="display display-md mt-2">Audit 层</h3><p style="color:var(--t2);font-size:12px;">12 类全局诊断</p></div>
  </div>

  <!-- 2. pullquote 核心判断 -->
  <div class="pullquote mt-8">为什么对手 <em>做不到</em>？<div class="pullquote-cite">— 四层防御互锁</div></div>

  <!-- 3. 01-04 逐个展开（每个独立小节，eyebrow 编号）-->
  <div class="section-label">§ 4.2 · 01 — 规则层</div>
  <p class="lede">PM 方法论 + 工具层操作约束，model-agnostic。</p>
  <ul style="list-style:none;padding:0;margin-top:16px;">
    <li class="py-2" style="border-bottom:1px solid var(--border2);color:var(--t2);">场景编号锁定（不可改）</li>
    <li class="py-2" style="border-bottom:1px solid var(--border2);color:var(--t2);">术语全局一致性</li>
    <li class="py-2" style="color:var(--t2);">70 % 先行，大返工成本远高于两轮迭代</li>
  </ul>

  <div class="section-label">§ 4.3 · 02 — Skill 层</div>
  <!-- 类似 01 结构 -->

  <div class="section-label">§ 4.4 · 03 — Hook 层</div>
  <!-- 类似 01 结构 -->

  <div class="section-label">§ 4.5 · 04 — Audit 层</div>
  <!-- 类似 01 结构 -->

  <!-- 4. 对比收尾 -->
  <div class="section-label">§ 4.6 · 对手 vs 我方</div>
  <table class="cmp-table">
    <thead><tr><th>维度</th><th>对手（通用 ChatGPT）</th><th>我方（PM-WS）</th></tr></thead>
    <tbody>
      <tr><td style="color:var(--t1);font-weight:700;">编号一致性</td><td>每次不同</td><td>全局锁定</td></tr>
      <tr><td style="color:var(--t1);font-weight:700;">变更波及</td><td>人工排查</td><td>impact-check 自动</td></tr>
    </tbody>
  </table>

  <!-- 5. pullquote 总结 -->
  <div class="pullquote mt-8">不是模型更强，是 <em>规则 + Hook + Audit</em> 兜底。<div class="pullquote-cite">— 护城河本质</div></div>
</div>
```

---

## 5. 结论前置 + 细节折叠（Reference / 选型页）

**叙事骨架**（4 步）：

```
前置说明（适用范围）→ 速查表前置（任务 × 推荐）
  → 选项详情展开（逐个模型 / 工具 / 方案）→ 原理折叠（评测 / benchmark / 深度理由）
```

**关键动作**：**先给结论**。听众真正关心的是「我这个场景选什么」，不是「模型 A 的全部参数」。原理放手风琴里给愿意深究的人。

**Claude Design 填充**：

```html
<div class="page active">
  <div class="eyebrow">§ 5 · 模型选型</div>
  <h2 class="display display-lg">Claude Code Switch</h2>
  <p class="lede">同一个 pipeline，不同任务派不同模型。选对模型省 ~46 % 成本。</p>
  <div class="hairline"></div>

  <!-- 1. 速查表前置 — 先看结论 -->
  <div class="section-label">§ 5.1 · 先看结论（速查表）</div>
  <table class="cmp-table">
    <thead><tr><th>任务</th><th>推荐模型</th><th>理由</th></tr></thead>
    <tbody>
      <tr><td style="color:var(--t1);font-weight:700;">方案讨论 / 架构决策</td><td>Opus 4.7</td><td>1M ctx + 推理深度</td></tr>
      <tr><td style="color:var(--t1);font-weight:700;">施工 / 格式化</td><td>Sonnet 4.6</td><td>省 46 %，质量仅差 5 %</td></tr>
      <tr><td style="color:var(--t1);font-weight:700;">机械验证（grep / audit）</td><td>Haiku 4.5</td><td>子 Agent 调度</td></tr>
    </tbody>
  </table>

  <!-- 2. 模型详情（每个模型单独展开，eyebrow 分类，无彩色卡片）-->
  <div class="section-label">§ 5.2 · 模型详情</div>

  <div class="py-6" style="border-bottom:1px solid var(--border2);">
    <div class="eyebrow eyebrow-accent">OPUS 4.7 · 1M CONTEXT</div>
    <h3 class="display display-md mt-2">方案决策 · 全链路执行主力</h3>
    <p class="lede">推理深度 + 长上下文。适合 context.md 讨论、架构决策、复杂变更推演。</p>
  </div>

  <div class="py-6" style="border-bottom:1px solid var(--border2);">
    <div class="eyebrow">SONNET 4.6 · 1M CONTEXT</div>
    <h3 class="display display-md mt-2">日常施工 · 格式化输出</h3>
    <p class="lede">Step B 填充可降级，节省 ~46 % 成本，质量 85-90。</p>
  </div>

  <div class="py-6">
    <div class="eyebrow">HAIKU 4.5</div>
    <h3 class="display display-md mt-2">机械验证 · 子 Agent 调度</h3>
    <p class="lede">grep / audit / git 考古等客观事实类任务。</p>
  </div>

  <!-- 3. 原理折叠 — 深度理由藏起来 -->
  <div class="section-label">§ 5.3 · 评测原理（细节）</div>
  <div class="accordion">
    <div class="acc-header" onclick="toggleAcc(this)"><span>探针评测方法详情</span><span class="arrow">▶</span></div>
    <div class="acc-body"><!-- 完整评测表 --></div>
  </div>
  <div class="accordion">
    <div class="acc-header" onclick="toggleAcc(this)"><span>成本模型完整公式</span><span class="arrow">▶</span></div>
    <div class="acc-body"><!-- 成本计算 --></div>
  </div>
</div>
```

---

## 6. 总览 + 按需展开（索引 / 目录页）

**叙事骨架**（3 步）：

```
顶部速查表（全部项一行一条）→ 手风琴逐个展开（工作原理 / 核心能力 / vs 对手 三段式）
  → pullquote 共同模式总结
```

**关键动作**：速查表要**一行看完一个项的关键属性**（名称 / 类型 / 格式 / 依赖），不是展开描述。手风琴默认全收起，让听众 **按需** 点开。

**Claude Design 填充**：

```html
<div class="page active">
  <div class="eyebrow">§ 6 · 产出物总览</div>
  <h2 class="display display-lg">20 个 Skill</h2>
  <p class="lede">一行看完一个 Skill 的关键属性，感兴趣再点开展开。</p>
  <div class="hairline"></div>

  <!-- 1. 速查表 — 一行一条 -->
  <table class="cmp-table">
    <thead><tr><th>名称</th><th>类型</th><th>格式</th><th>依赖</th><th>适用</th></tr></thead>
    <tbody>
      <tr><td style="color:var(--t1);font-weight:700;">scene-list</td><td>pipeline</td><td>.md</td><td>—</td><td>任何复杂需求起手</td></tr>
      <tr><td style="color:var(--t1);font-weight:700;">interaction-map</td><td>pipeline</td><td>.html</td><td>scene-list</td><td>多端 UI 流</td></tr>
      <tr><td style="color:var(--t1);font-weight:700;">prototype</td><td>pipeline</td><td>.html</td><td>scene-list</td><td>可交互原型</td></tr>
      <tr><td style="color:var(--t1);font-weight:700;">prd</td><td>pipeline</td><td>.docx</td><td>scene-list</td><td>横版九章</td></tr>
      <!-- ...剩余 16 行 -->
    </tbody>
  </table>

  <!-- 2. 手风琴详情（每个 Skill 三段式：工作原理 / 核心能力 / vs 对手）-->
  <div class="section-label">§ 6.1 · 详情（按需展开）</div>
  <div class="accordion">
    <div class="acc-header" onclick="toggleAcc(this)"><span>scene-list — /场景清单 项目名</span><span class="arrow">▶</span></div>
    <div class="acc-body">
      <div class="eyebrow mt-2">WORKING PRINCIPLE</div>
      <p style="color:var(--t2);font-size:13px;">需求拆解为编号锁定的场景单元，下游复用。</p>
      <div class="eyebrow mt-4">CORE CAPABILITY</div>
      <p style="color:var(--t2);font-size:13px;">前台 A/B/C 编号 + 后台 M-1/M-2 + 功能前缀 F-0/E-1。</p>
      <div class="eyebrow mt-4">VS GENERIC AI</div>
      <p style="color:var(--t2);font-size:13px;">场景编号锁定后所有产出物复用，通用 AI 每次重新编号。</p>
    </div>
  </div>
  <!-- ...每个 Skill 一条 accordion -->

  <!-- 3. pullquote 共同模式 -->
  <div class="pullquote mt-8">20 个 Skill 的共同模式：<em>输入声明 → Step A 骨架 → Step B 填充 → Step C 自检</em>。<div class="pullquote-cite">— Skill 架构原则</div></div>
</div>
```

---

## 7. 节奏编排

**核心原则**：AI 生成 PPT 的最大破绽是「太均匀」，每页同一套三明治。节奏靠 **叙事骨架交替** + **视觉密度交替** 双层制造。

**10 页 deck 节奏示例**（叙事 × 视觉交替）：

```
页 1  §1 先冲击后选择 / Hero       ← 呼吸页开场：film-grain + display-xl
页 2  §1 figure-num 数字冲击        ← 数字密集页
页 3  §1 决策树 + 核心链路          ← 文本密集页
页 4  §2 先图后理 / 全景图          ← 图示页（editorial 树形）
页 5  §1 Part 转场                  ← 呼吸页再现（每 4-6 页一个）
页 6  §3 两情景对比 / 场景 A        ← 流程页
页 7  §3 pullquote + 场景 B         ← 断句页（pullquote 打破节奏）
页 8  §4 总分总 / 全景 + 展开       ← 层级页
页 9  §5 结论前置 / 速查表          ← 密集数据页
页10  §6 总览 + 共同模式 pullquote  ← 收尾
```

**反面教材（AI slop 三明治）**：

```
每页都是 eyebrow → grid3 → pullquote    ← 组件同、叙事同 = AI 味最重
每页都是速查表 + 手风琴                  ← 叙事单一（reference 型）
```

## 8. 自检清单

**叙事层**：

- [ ] 选对叙事骨架（类型 × 骨架，见顶部表）
- [ ] 总分总 / 先图后理 / 情景对比等多步骤骨架，**每一步都落地**，不省略步骤
- [ ] Reference / 索引型页面把深度细节折叠，不堆到主线
- [ ] pullquote 是**判断 / 提问 / 结论**，不是「接下来我们讲 XX」这种填充句
- [ ] Part 转场页每 4-6 页插入一次，打破内容页节奏
- [ ] 相邻两页**叙事类型不同**（先图后理 → 两情景对比 → 总分总 交替）

**视觉层**：

- [ ] 编号 / 分类统一用 `.eyebrow`（mono + uppercase + tracking）
- [ ] 页面分隔用 `.hairline` / `.section-label`，禁 `border-top:3px solid var(--color)`
- [ ] 大标题用 `.display`（Noto Serif SC），禁全文只用 `font-weight:900` sans
- [ ] 同页强调色 ≤ 1 种（`--blue`），禁 green/orange/purple/red/pink 同页堆叠
- [ ] 禁 emoji 装饰（业务 icon 用 inline SVG 或 mono 字符）
- [ ] 禁 icon-box + emoji 组合、禁圆角卡片 + 左/顶 border-accent 色条、禁彩色圆角徽章做编号
