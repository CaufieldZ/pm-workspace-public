<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: skill-creator
description: >
  当用户需要新建一个 skill（说「创建 skill」「做个新 skill」「帮我设计一个新技能」）时触发。
  已有 skill 的内容修改直接编辑对应 SKILL.md，不走此 skill。
  即使用户只说「我想让你记住一个新规则/新流程」也应询问是否要创建 skill。
type: tool
output_format: 新目录
depends_on: []
optional_inputs: []
consumed_by: []
---
<!-- pm-ws-canary-236a5364 -->

# Skill Creator

## 定位

元工具——创建新 skill 或改造已有 skill 的 skill。
产出全套文件，frontmatter 中的注册信息自动被 workspace-audit 和 cross-check 扫描，无需手动维护 pm-workflow 注册表。**不直接修改**已有 skill 文件，等用户确认后再执行。

## 两种模式

### A. 新建模式

用户说「做一个 XX skill」「新建 skill」→ 分四步执行：

1. **需求对齐**（交互式，分两轮问）
   - 第一轮：skill 类型（链路型 / 独立产出型 / 工具型）、核心定位、和现有链路的关系
   - 第二轮：输出格式、核心维度、特殊规则、参考素材

2. **生成全套文件**（参考 `workspace-conventions.md` 文件规范）

3. **注册确认**（frontmatter 已含注册信息，自动被 workspace-audit 扫描；仅链路/结构变化时才需更新 pm-workflow）

4. **自动运行 workspace-audit 验证**

### B. 改造模式

用户说「给 XX skill 加个功能」「改一下 XX skill」→ 读取已有 SKILL.md，输出 diff 形式建议，用户确认后才执行。

---

## SKILL.md 必须包含的章节

```
frontmatter: name + description（含触发词）+ argument-hint
正文：定位 / 核心原则 / 执行步骤 / 输出格式 / 自检清单
```

## Skill 类型快速判断

| 类型 | 特征 | 额外章节 |
|------|------|----------|
| 链路型 | 嵌入 pm-workflow 某步，有前后依赖 | 输入规范、编号继承规则、回读机制 |
| 独立产出型 | 不依赖链路，独立输出报告/文档 | 档位定义、沉淀规则 |
| 工具型 | 审计/检查/辅助，不产出业务文档 | 扫描范围、检查维度、报告格式 |

## 质量自检清单

- [ ] Frontmatter 完整，触发词不和现有 skill 冲突
- [ ] 引用路径全部可达
- [ ] 配色 Token 和 pm-workflow 一致（如有 HTML 输出）
- [ ] 有自检清单
- [ ] pm-workflow 更新建议完整
- [ ] 跑过 workspace-audit

## 注意事项

1. **不直接修改** pm-workflow.md 和已有 skill 文件
2. 每次完成后主动提醒：「要不要我跑一次 workspace-audit 验证？」
3. 如需了解详细模板（链路型/独立产出型/工具型骨架），读取：
   ```
   view .claude/skills/skill-creator/references/workspace-conventions.md
   ```

---

<!-- 以下为详细参考内容，触发后如需深度指导可参考 -->

### Phase 1：需求对齐（交互式）

收到新建请求后，**必须**按以下顺序向用户确认设计决策。每轮问 3-5 个问题，不要一次性全部丢出来。

#### 第一轮：定位 & 分类

1. **Skill 类型**——先判断属于哪种模式（见下方「三种内置模板」），建议给用户选：
   - 链路型（嵌入需求链路某一步）
   - 独立产出型（不依赖链路，独立输出报告/文档）
   - 工具型（审计/检查/辅助类，不产出业务文档）

2. **核心定位**——一句话说清这个 skill 干什么、给谁用、产出什么

3. **和现有链路的关系**——
   - 链路型：插入哪一步？前后依赖什么？
   - 独立产出型：分析完要不要沉淀到项目 context.md？
   - 工具型：触发时机是什么？

4. **注册字段**（链路型必填，其他型按需）——
   - 产出物格式是什么？（.html / .docx / .md / 对话内 / 新目录）
   - 文件命名前缀是什么？（例如 imap- / proto-，工具型可跳过）
   - 如果是链路型：在链路中排第几步（pipeline_position）？
   - 上游依赖哪些 skill（depends_on）？被哪些下游 skill 消费（consumed_by）？

#### 第二轮：输出 & 维度

4. **输出格式**——可选组合：
   - Markdown（对话内 / 贴飞书）
   - HTML（高保真，和其他产出物统一）
   - PPT（.pptx，汇报用）
   - docx（正式文档）
   - 对话内直接输出（工具型常见）

5. **核心分析/产出维度**——这个 skill 的内容骨架是什么？（Claude 可以根据类型建议，用户确认或修改）

6. **要不要分档位**——比如快速版 vs 深度版、简单链路 vs 复杂链路

#### 第三轮：规范 & 约束

7. **配色/设备规范**——
   - 继承 pm-workflow 的深色板/浅色板？
   - 还是有特殊需求？

8. **和现有 skill 的引用关系**——
   - 需要读取哪些其他 skill 的产出物？
   - 其他 skill 需要读取它的产出物吗？

9. **特殊规则**——有没有类似 pm-workflow 第四/五章那种「硬规则」要额外强制的？

10. **参考素材**——用户有没有现成的 prompt/模板/示例可以融合？（类似 competitor-analysis 融合了用户的 CRBE prompt）

### Phase 2：生成全套文件

根据对齐结果，生成以下文件：

```
.claude/skills/{skill-name}/
├── SKILL.md              ← 核心规范
└── references/
    ├── output-structure.md   ← 输出结构示例（如有）
    └── {其他参考文件}        ← 视需要
```

#### SKILL.md 必须包含的章节

```markdown
---
name: {skill-name}
description: >
  {触发描述，包含正向触发词和排他条件}
argument-hint: [{参数提示}]
type: {pipeline | standalone | tool}
output_format: {.html | .docx | .md | 对话内 | 新目录}
output_prefix: {前缀-}
pipeline_position: {数字，仅 pipeline 型填写}
depends_on: [{上游 skill 名}]
optional_inputs: [{可选输入，skill 名或文件名}]
consumed_by: [{下游 skill 名}]
---

# {Skill 标题}

## 定位
（一段话说清干什么、给谁、产出什么、和链路的关系）

## 核心原则
（该领域的方法论/反常识规则/校验标准）

## 执行步骤
### Step 1: ...
### Step 2: ...
...

## 输出格式
（每种格式的具体规范）

## 自检
- [ ] ...
```

#### 根据类型追加的章节

**链路型**额外包含：
- 和前后步骤的数据传递规范
- 编号/术语继承规则
- 回读机制（参照 pm-workflow 上下文防丢规则）

**独立产出型**额外包含：
- 档位定义（如有）
- 沉淀规则（存到哪、怎么命名）
- PPT/docx 的 slide/page 结构（如有）

**工具型**额外包含：
- 扫描范围定义
- 检查维度清单
- 报告输出格式
- 辅助修复规则（改 vs 只建议）

### Phase 3：注册确认 & 建议

新 Skill 已创建。frontmatter 中的注册信息（type / output_format / depends_on / consumed_by 等）会被 workspace-audit 和 cross-check 自动扫描，**无需手动更新 pm-workflow 或 README**。

**建议跑一次 workspace-audit** 验证注册信息的完整性和依赖关系正确性。

仅在以下情况需要手动更新外部文件：
- 新增了全新的 pipeline 链路分支（需更新 pm-workflow 链路说明）
- README 目录结构发生变化（需更新 README 目录树和 Skill 表）
- CLAUDE.md 描述的 skill 数量明显偏差（需更新）

如需更新，逐项列出建议，等用户确认后执行。

### Phase 4：自动审计

生成完毕后，**自动执行 workspace-audit**（如果已安装），检查新 skill 是否和现有 skills 冲突。

如果 workspace-audit 不存在，手动检查以下最小集：
- [ ] 触发词不和现有 skill 重叠
- [ ] 配色 Token 和 pm-workflow 一致
- [ ] 引用路径全部可达
- [ ] 术语和现有 skills 一致

---

## 改造模式：执行步骤

### Step 1：读取现有 skill

读取目标 skill 的完整内容：
- `.claude/skills/{target}/SKILL.md`
- `.claude/skills/{target}/references/*`
- pm-workflow.md 中关于该 skill 的所有引用

### Step 2：分析改造需求

用户描述想改什么 → Claude 分析影响范围：
- SKILL.md 哪些章节需要改
- references 是否需要新增/修改
- pm-workflow.md 是否需要联动更新
- 其他 skill 是否受影响（交叉引用）

### Step 3：输出改造建议（diff 形式）

**不直接修改**，输出建议：

```markdown
## 改造建议：{skill-name}

### 变更 1：SKILL.md — {章节名}
原文：
> {原内容摘要}

建议改为：
> {新内容}

理由：{为什么改}

### 变更 2：新增 references/{文件名}
内容：{新文件内容摘要}

### 变更 3：pm-workflow.md 联动
位置：{具体位置}
原文：...
改为：...

### 影响评估
- 受影响的其他 skill：{列表或「无」}
- 受影响的已有产出物：{列表或「无」}

确认后我来执行修改。
```

### Step 4：用户确认后执行

用户说「改吧」「OK」「确认」→ 逐项执行修改 → 跑 workspace-audit 验证。

---

## 三种内置模板

### 模板 A：链路型

适用于嵌入 pm-workflow 需求链路的某一步。

特征：
- 有明确的前置输入（上一步产出物）和后续消费者（下一步 skill）
- 必须遵守场景编号、View 划分、术语一致性
- 产出物有固定命名前缀和版本管理
- 需要回读机制

骨架：
```markdown
## 定位
链路第 N 步，接收 {上一步} 的产出物，为 {下一步} 提供输入。

## 输入
- 必读：`scene-list.md`
- 必读：{上一步产出物}

## 执行步骤
### Step 1：回读上下文
（强制回读 scene-list + 上一步产出物）
### Step 2：执行产出
...
### Step 3：自检 + 交叉验证
...

## 编号 & 术语规则
- 复用 scene-list.md 的编号体系
- 术语必须和前序产出物完全一致

## 输出格式
- 格式：{HTML/docx/md}
- 命名：`{prefix}-{project}-v{N}.{ext}`
- 存放：`projects/{project}/deliverables/`

## 设备规范
继承 pm-workflow 第三章。
```

### 模板 B：独立产出型

适用于不依赖需求链路、独立输出报告/文档的 skill。

特征：
- 独立触发，不需要前置链路步骤
- 可能分快速版/深度版
- 产出物可以沉淀到 references 或 deliverables
- 可能需要读取 profile.md 作为约束

骨架：
```markdown
## 定位
独立产出物，直接给 {目标受众} 看。

## 核心原则
{该领域的方法论/分析框架}

### 校验标准
- {失败条件 1} = 失败
- {失败条件 2} = 失败

## 两种档位（如有）
### 快速版
...
### 深度版
...

## 执行步骤
### Step 1：收集信息
### Step 2：读取我方约束（profile.md）
### Step 3：执行分析/产出
### Step 4：输出 & 沉淀

## 输出格式
### Markdown
...
### PPT（如有）
Slide 结构、配色、设计规则

## 自检
```

### 模板 C：工具型

适用于审计/检查/辅助类 skill，不产出业务文档。

特征：
- 扫描/检查/校验已有文件
- 输出报告在对话中，不生成独立文件
- 可能有「辅助修复」能力
- 通常不进入 pm-workflow 链路

骨架：
```markdown
## 定位
元工具，扫描/检查 {范围}。

## 触发时机
- {时机 1}
- {时机 2}
- 用户主动要求

## 扫描范围
{文件列表/目录}

## 检查维度
### 维度 1：{名称}
- [ ] {检查项}
...

## 输出报告格式
```markdown
# {报告标题}
| 维度 | 结果 | 问题数 |
...
## 问题明细
...
## 修复清单
...
```

## 辅助修复规则
- 默认只建议，用户确认后执行
- 修复后重新跑检查
```

---

## 质量检查清单

生成任何 skill 后，skill-creator 必须自检：

- [ ] **Frontmatter 完整**：name + description + argument-hint + type + output_format + depends_on + consumed_by（pipeline 型额外需要 pipeline_position）
- [ ] **Description 触发词明确**：包含正向触发词，排他条件清晰
- [ ] **不和现有 skill 触发词冲突**
- [ ] **引用路径全部可达**：SKILL.md 中引用的文件都存在或会被创建
- [ ] **配色 Token 一致**：如继承深色/浅色板，色值和 pm-workflow 完全一致
- [ ] **数值规范一致**：设备尺寸、字体、间距和 pm-workflow 一致
- [ ] **术语一致**：和现有 skills 使用相同术语
- [ ] **有自检清单**：SKILL.md 末尾有 checklist
- [ ] **注册信息完整**：frontmatter 包含 type / output_format / depends_on / consumed_by，pipeline 型含 pipeline_position
- [ ] **外部文件更新建议**（仅在链路/结构变化时）：pm-workflow 链路说明、README 目录树
- [ ] **跑过 workspace-audit**（如已安装）

---

## 注意事项

1. **不直接修改** pm-workflow.md 和已有 skill 文件——只输出建议，用户确认后才执行
2. 每次创建/改造完，主动提醒用户：「要不要我跑一次 workspace-audit 验证？」
3. 如果用户提供了参考 prompt/模板，先分析其核心价值再融合，不是全盘照搬
4. 如果用户的需求跨了两种模板（如链路型 + 独立产出型），说明并建议拆成两个 skill 或选一个主模板扩展
5. 改造模式下，如果改动影响了其他 skill，必须在影响评估中列出
