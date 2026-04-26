<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# Skill Creator 模板库

> skill-creator 的详细参考：三种内置模板骨架 + 改造模式 diff 格式。
> SKILL.md 主体只讲规范，此文件讲「具体怎么写」。

## 三件套语义边界（所有模板共用，强制）

每个 skill 目录按 Anthropic Progressive Disclosure 规范的三件套组织。新建 skill 时三件套全部预创建（哪怕暂时为空）：

| 子目录 | 内容 | 模型如何使用 |
|---|---|---|
| `scripts/` | 可执行代码：.py / .sh / .js library | 不读源码，按 frontmatter `scripts:` 字段调用执行 |
| `references/` | .md 文档：模板规范、组件清单、cheat sheet | 按 SKILL.md Step 1 声明按需 Read 加载到 context |
| `assets/` | HTML/CSS/JS 模板、字体、运行时 JSON 配置、图标 | 被脚本 `open().read()` 拼进产物，模型不读 |

**禁止跨界**（audit.sh 第 14 类自动校验，pre-commit hook 拦截）：
- assets/ 不放 .md → 应去 references/
- references/ 不放 .py/.sh/.css/.js/.html/.json → 按可执行 vs 资源去 scripts/ 或 assets/
- scripts/ 不放 .md → 应去 references/

下方三种模板的 References 章节按此边界写。

---

## 三种内置模板

### 模板 A：链路型（pipeline）

嵌入 pm-workflow 需求链路某一步。特征：
- 有前置输入（上一步产出物）和后续消费者（下一步 skill）
- 必须遵守场景编号、View 划分、术语一致性
- 产出物有固定命名前缀和版本管理
- 需要回读机制

**SKILL.md 骨架**：

```markdown
---
name: {skill-name}
description: >
  触发时机：用户说「{主触发词}」{或其他 4+ 说法}。基于 {上一步 skill} 产出物生成 {本步产出物}。
type: pipeline
output_format: .{html|docx|md}
output_prefix: {prefix-}
pipeline_position: {数字}
depends_on: [scene-list, {上一步}]
consumed_by: [{下一步 1}, {下一步 2}]
---

## 定位
链路第 N 步，接收 {上一步} 的产出物，为 {下一步} 提供输入。

## References

**必读**（产出前加载）：
- `scene-list.md` — 场景编号
- {上一步产出物路径} — 上游输入
- `references/{本 skill 模板}.md` — 结构定义/样式规范

**按需**（满足条件才读）：
- `references/{业务组件}.md` — 仅当 Scene 含对应业务类型时读

**执行类**（模型不读，脚本调用）：
- `scripts/gen_{产物}_skeleton.py` — 骨架脚本
- `scripts/fill-template.py` — 填充模板

## 执行步骤
### Step 1：回读上下文
强制回读 scene-list + 上一步产出物。

### Step 2：执行产出
...

### Step 3：自检 + 交叉验证
对照 scene-list 编号逐个核对，无遗漏无空内容才可交付。

## 编号 & 术语规则
- 复用 scene-list.md 的编号体系
- 术语必须和前序产出物完全一致

## 输出格式
- 格式：{HTML/docx/md}
- 命名：`{prefix}-{project}-v{N}.{ext}`
- 存放：`projects/{project}/deliverables/`

## 设备规范
继承 pm-workflow 第三章。

## 自检
- [ ] 编号和 scene-list 一致
- [ ] 术语与上一步产出物一致
- [ ] ...
```

### 模板 B：独立产出型（standalone）

不依赖链路、独立输出报告/文档。特征：
- 独立触发，不需要前置链路
- 可能分快速版/深度版
- 产出物可沉淀到 references 或 deliverables
- 可能需要读取 profile.md 作为约束

**SKILL.md 骨架**：

```markdown
---
name: {skill-name}
description: >
  触发时机：用户说「{触发词 1/2/3/4/5+}」。独立产出 {产物类型} 给 {受众}。
type: standalone
output_format: .{html|md|pptx|docx}
output_prefix: {prefix-}
depends_on: []
consumed_by: []
---

## 定位
独立产出物，直接给 {目标受众} 看。

## 核心原则
{该领域的方法论 / 分析框架}

### 校验标准
- {失败条件 1} = 失败
- {失败条件 2} = 失败

## References

**必读**（产出前加载）：
- `references/{产物模板}.md` — 结构/字段规范

**按需**（满足条件才读）：
- `references/{可选参考}.md` — 仅当 {条件} 时读

**执行类**（模型不读，脚本调用）：
- `scripts/{生成脚本}.py` — 调用方式

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
- [ ] ...
```

### 模板 C：工具型（tool）

审计/检查/辅助，不产出业务文档。特征：
- 扫描/检查/校验已有文件
- 输出报告在对话中，不生成独立文件
- 可能有「辅助修复」能力
- 通常不进入 pm-workflow 链路

**SKILL.md 骨架**：

```markdown
---
name: {skill-name}
description: >
  触发时机：用户说「{触发词 1/2/3/4/5+}」。扫描/检查 {范围}，输出修复建议。
type: tool
output_format: 对话内
depends_on: []
consumed_by: []
---

## 定位
元工具，扫描/检查 {范围}。

## 触发时机
- {时机 1}
- {时机 2}
- 用户主动要求

## 扫描范围
{文件列表 / 目录}

## References

**必读**（产出前加载）：
- `references/{规则定义}.md` — 校验规则清单

**执行类**（模型不读，脚本调用）：
- `scripts/{审计脚本}.sh` — 调用方式

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

## 自检
- [ ] ...
```

---

## 改造模式：diff 输出格式

当用户说「给 XX skill 加个功能」「改一下 XX skill」时，skill-creator 走改造模式。

### Step 1：读取现有 skill

```
.claude/skills/{target}/SKILL.md
.claude/skills/{target}/references/*
pm-workflow.md 中关于该 skill 的所有引用
```

### Step 2：分析改造需求

识别影响范围：
- SKILL.md 哪些章节需要改
- references 是否需要新增/修改
- pm-workflow.md 是否需要联动更新
- 其他 skill 是否受影响（交叉引用）

### Step 3：输出 diff 形式建议（不直接修改）

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

用户说「改吧」/「OK」/「确认」→ 逐项执行修改 → 跑 workspace-audit 验证。

---

## 自由度匹配（参考）

判断 skill 的指令松紧程度：

| 自由度 | 适用场景 | 示例 |
|--------|----------|------|
| 高 | 多种方法都可行 | competitor-analysis（分析框架有多种） |
| 中 | 有首选模式但允许变化 | data-report（数据拉取有模板但参数灵活）|
| 低 | 操作脆弱、一致性关键 | prd / interaction-map（编号/术语不能变） |

自由度低的 skill → 写死步骤 + 多条硬规则
自由度高的 skill → 给方法论 + 校验标准，不写死步骤
