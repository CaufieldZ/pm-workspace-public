<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: skill-creator
description: >
  创建 / 改造 skill 的元工具。触发时机：用户说「创建 skill / 做个新 skill / 加个 XX 工具 / 新增 XX 能力 / 需要一个 XX skill / 包装一下 XX 流程 / 把 XX 沉淀成规范」，或项目需求涉及定义新的 pm-workflow 步骤或工具。排他：已有 skill 的修改直接编辑对应 SKILL.md，不走此 skill。
argument-hint: [skill 名 或 改造目标]
type: tool
output_format: 新目录
output_prefix: none
depends_on: []
optional_inputs: []
consumed_by: []
scripts: []
---
<!-- pm-ws-canary-236a5364 -->

# Skill Creator

## 定位

元工具——创建新 skill 或改造已有 skill。产出全套文件，frontmatter 注册信息自动被 workspace-audit 扫描，无需手动维护 pm-workflow 注册表。**不直接修改**已有 skill 文件，等用户确认后再执行。

## 开场白（新建模式）

收到「做一个 XX skill」请求后，**先问一次 I/O 契约**（一次性问清，不分多轮）：

> 这个 skill 的 **输入**是什么（用户会提供什么/说什么触发）→ **输出**是什么（产物形态、落地位置）？触发词有哪些候选？

用户答完 → 直接进入 Step 2 生成。中途遇到类型/语言/字段选择时**用类型判断表自行决策**，不再多轮追问。

## 两种模式

**A. 新建模式** — 用户说「做一个 XX skill」/「新增 XX 能力」→ 问 I/O → 判断类型 → 生成文件 → 自检 → 提醒跑 workspace-audit

**B. 改造模式** — 用户说「给 XX skill 加个功能」→ 读取目标 SKILL.md → 输出 diff 形式建议 → 用户确认后执行

## SKILL.md 必须包含的章节

```
frontmatter:
  name / description（含触发词，见「Description 写作纪律」）/ argument-hint
  type（pipeline/standalone/tool）/ output_format / output_prefix
  pipeline_position（仅 pipeline 型）
  depends_on / optional_inputs / consumed_by
正文：定位 / 核心原则 / 执行步骤 / 输出格式 / 自检清单
```

**pm-workspace 自创字段**（官方没有、但 workspace-audit 扫描依赖，必填）：
- `type` — pipeline / standalone / tool
- `output_format` + `output_prefix` — 产物扩展名 + 命名前缀
- `depends_on` / `consumed_by` — 上下游依赖，用于 cross-check 拉通验证
- `pipeline_position` — 仅 pipeline 型填，表示链路中的顺序

## Skill 类型快速判断

| 类型 | 特征 | 额外章节 |
|------|------|----------|
| 链路型（pipeline） | 嵌入 pm-workflow 某步，有前后依赖 | 输入规范、编号继承、回读机制 |
| 独立产出型（standalone） | 不依赖链路，独立输出报告/文档 | 档位定义、沉淀规则 |
| 工具型（tool） | 审计/检查/辅助，不产出业务文档 | 扫描范围、检查维度、报告格式 |

详细骨架见 [references/templates.md](references/templates.md)。

## 脚本语言选择（生成 HTML/文档的 skill）

**看嵌套层级，不看语言优劣**：

| 产物结构 | 嵌套 | 选语言 | 理由 |
|----------|------|--------|------|
| 静态 HTML + 外部 CSS/JS（`open().read()` 内联）| 2 层：脚本 → HTML | **Python**（三引号 `'''...'''`）| 生态成熟，三引号绕过双引号转义就够 |
| HTML 里嵌 `<script>` 内含运行时渲染函数（`innerHTML = "..."`）| 3 层：脚本 → JS 字符串 → HTML | **Node.js**（反引号模板字符串）| 避免 Python→JS→HTML 三层转义地狱 |
| docx / xlsx / PDF / 数据分析 | — | **Python** | python-docx / pandas 等生态 |

**实例参考**：
- PPT skill：3 层嵌套 → Node.js（`fill-template.js`）
- interaction-map / prototype / architecture-diagrams：2 层 → Python（`gen_*_v{N}.py`）

不确定时：产物 `<script>` 里有没有「字符串形式的 HTML」要拼。有 → Node；没有 → Python。

## Description 写作纪律（关键——否则没人触发）

Claude 对 skill 有 **undertrigger 倾向**（官方 Anthropic 明确警告）。Description 必须 **pushy**：

1. **列 ≥ 5 个真实触发词**，覆盖用户可能的说法差异
   - 反例：「创建 skill 时触发」（只 1 个说法）
   - 正例：「创建 skill / 做个新 skill / 加个 XX 工具 / 新增 XX 能力 / 需要一个 XX skill / 包装 XX 流程」
2. **必须说明做什么 + 什么时候用** — 两条信息缺一不可
3. **明确排他条件** — 如「已有 skill 的修改不走此 skill」
4. **用第三人称** — ❌「帮你处理」 ✅「处理 XX 文件」

## 质量自检清单

- [ ] Frontmatter 完整（name / description / type / output_format / depends_on / consumed_by，pipeline 型含 pipeline_position）
- [ ] **Description 触发词 ≥ 5 个**且不和现有 skill 冲突
- [ ] **反向触发测试**：想一个「相似但不应触发」的请求，确认 description 不会误命中（例：给 competitor-analysis 写「我想分析用户行为」应该**不触发**，因为它是分析竞品，不是用户）
- [ ] **References 区块用三分类**（必读/按需/执行类），模板见 templates.md；每个文件有明确归类不留灰色地带
- [ ] 引用路径全部可达（SKILL.md 中引用的文件都存在或会被创建）
- [ ] 配色 Token 和 pm-workflow 一致（如有 HTML 输出）
- [ ] 数值规范一致（设备尺寸、字体、间距）
- [ ] 术语和现有 skills 一致
- [ ] 有自检清单（SKILL.md 末尾）
- [ ] 跑过 workspace-audit

## 注意事项

1. **不直接修改** pm-workflow.md 和已有 skill 文件——只输出建议，用户确认后执行
2. 每次创建/改造完主动提醒：「要不要跑一次 workspace-audit 验证？」
3. 需求跨类型（如链路型 + 独立产出型）时说明并建议拆成两个 skill 或选主模板扩展
4. 改造模式下，如果改动影响其他 skill，必须在影响评估中列出
5. 详细模板骨架和改造模式的 diff 输出格式 → 读 [references/templates.md](references/templates.md)
6. pm-workspace 约定（目录/配色/字体/编号/命名） → 读 [references/workspace-conventions.md](references/workspace-conventions.md)
