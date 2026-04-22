<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: behavior-spec
description: >
  当用户说「行为规格」「bspec」,或需给研发 AI / Vibe Coding 消费文档时触发。
type: pipeline
output_format: .md
output_prefix: bspec-
pipeline_position: 6
depends_on: [scene-list, prd]
optional_inputs: [interaction-map, prototype]
consumed_by: [test-cases, cross-check]
---
<!-- pm-ws-canary-236a5364 -->

# 行为规格文档 Skill（Behavior Spec）

## 作用

全局 PRD 写完并通过自检后，从中切分出一份**行为规格文档**。行为规格是 PRD 的投影，面向研发 AI，描述 WHAT（用户行为 + 业务规则），不描述 HOW（技术实现）。

核心价值：
- **自包含**：研发 AI 读完后不需要再读 PRD、交互大图或任何外部文件
- **实现无关**：PM 描述用户行为和系统响应，研发 AI 自己决定技术方案
- **可并行**：一个 PRD 可切分出多份行为规格，按模块/场景分配给不同研发 AI

## 硬规则

### 必须包含

1. 用户行为描述：每个操作的触发条件、执行过程、预期结果
2. 系统响应规则：系统收到操作后应该做什么（不写怎么做）
3. 状态流转：自然语言 + Markdown 表格（禁止 Mermaid）
4. 业务规则：计算逻辑、限制条件、阈值（业务语言）
5. 异常处理：每个操作的异常场景 + 系统应如何响应
6. 术语表：从 scene-list.md + context.md 继承，写入文档内

### 禁止写入

接口路径 / 数据库字段名 / 精度类型 / 舍入算法 / 缓存方案 / 前后端分工建议 / Mermaid / JSON / 代码片段 / 服务名称 / 消息队列 / 技术架构图

### 写法对比

| 场景 | 禁止 | 正确 |
|------|------|------|
| 字段描述 | rewardAmount: Float(8) | 用户最终获得的奖励金额 |
| 状态流转 | Mermaid stateDiagram | 用 Markdown 表格：From → To → 触发条件 → 系统行为 |
| 操作描述 | 调用 /join 接口 | 用户点击报名后，系统记录其参与资格 |
| 计算逻辑 | 向下取整，余数留池 | 奖励金额不多发；剩余部分保留在奖励池中 |
| 数据存储 | 写入 MySQL activity_join 表 | 系统持久化用户的参与状态 |

## 输出格式

**Markdown**（`.md`），存 `projects/{项目名}/deliverables/bspec-{项目简称}-v{N}.md`

命名前缀 `bspec-`，版本规则同其他产出物（小修覆盖，结构变更升版）。

## 链路位置

复杂 / 超复杂链路中，**可选**步骤，位于 PRD 之后、拉通自检之前：

```
5. PRD .docx → 6. 行为规格 .md（可选，behavior-spec）→ 7. 拉通自检
```

不要求每个项目都出行为规格——仅在需要给研发 AI 切分任务时触发。

## 执行步骤

### Step 1：读取输入

**必读**（并行读取）：

```
view projects/{项目名}/context.md
view projects/{项目名}/scene-list.md
```

**PRD 读取**（按格式选择）：
- docx 格式：用 bash 提取文本 `python3 -c "from docx import Document; ..."` 或用 Read 工具读
- md 格式：直接 Read

**按需读取**（交互大图 / 原型有数据流时补充）：
- 交互大图：`grep -A2 'class="st"'` 取 Scene 标题 + `grep "跨端"` 取数据流表
- 原型：`grep "const.*Data"` 取 JS 数据数组块

### Step 2：确定切分粒度

行为规格支持两种切分方式：

**A. 整体文档**：一份文档覆盖全部场景，按 scene 编号分节。

**B. 按 View / 模块拆分**：每个 View 或模块独立一份文档，各自自包含。适用于多研发 AI 并行开发。

**默认推荐规则**（向用户推荐时依此）：

- 场景数 ≥ 20 **或** View ≥ 3 → 默认推 B（按 View 拆分）。理由：研发 AI 上下文消费压力，单份 ≤ 800 行更可用
- 场景数 < 20 **且** View ≤ 2 → 默认推 A（整体一份）

向用户确认切分方式后再开始写。

### Step 2.5：场景详略分档（强制）

不同优先级场景用不同详略，不一刀切 4 节全写：

| 优先级 | 节数 | 每节体量 | 说明 |
|--------|------|---------|------|
| P0 | 4 节全写（行为 / 响应 / 规则 / 异常） | 每节 ≥ 3 行 | 核心链路，详细展开 |
| P1 | 4 节全写 | 每节 2-3 行，精简版 | 次要链路，写骨架不堆细节 |
| P2 | 合并 2 节：「核心行为 + 关键异常」 | 每节 1-2 行 | 低频/辅助场景，一段话够 |
| 后续迭代 / 占位 | 不展开 | 1 段话说明原因 | 如 D-4 结算报告 V3 做，只标注「Q2 仅基础实现 + V3 规划」 |

### Step 2.6：场景组合并（强制）

识别条件（满足任一即合并）：

- 共享同一状态机的连续编号场景（如 B-3 上麦 / B-4 发言 / B-4a 拉黑 / B-4b 锁麦 本质是「在麦状态机」4 个状态）
- 共享同一容器/底栏/壳子的场景（如 C-1 悬浮态 / C-1c 历史态 共用策略卡容器）

合并写法：

- 合成 1 个「Scene Group」节，标题写 `Scene B-3 ~ B-4b：在麦状态组`
- 行为/响应章节写共性部分，状态差异用**状态矩阵表**展开
- 每个子状态只写与共性的差异，不重复描述底栏等共享元素

反例：B-3 的「底栏保留全部功能」在 B-4 / B-4a / B-4b 重复描述 4 次 → 改为 Scene Group 共性章节写 1 次。

### Step 3：生成行为规格

严格按 `references/behavior-spec-template.md` 的章节结构填充。

填充规则：
- 按 scene 编号逐场景展开，编号复用 scene-list
- 每个场景必须覆盖：正常流程 + 异常场景
- 状态流转用 Markdown 表格，不用 Mermaid
- 术语表从 scene-list.md + context.md 提取，写入文档内
- 业务规则从 PRD 提取，转为业务语言（去技术术语）
- 数值、阈值、限制条件原样保留，不省略

### Step 4：自检

按下方自检清单逐项验证，全部通过后才可交付。

### Step 5：保存 & 通知

保存到 `projects/{项目名}/deliverables/bspec-{项目简称}-v{N}.md`

通知用户：
- 文件路径
- 覆盖的场景编号列表
- 是否需要拆分多份

## 自检清单

- [ ] **单份行数 ≤ 800**：超出则必须按 View 拆分或精简 P2/占位场景，防止研发 AI 上下文撑爆
- [ ] **场景详略分档**：P0 详写、P1 精简、P2 合并 2 节、后续迭代不展开
- [ ] **场景组合并**：共享状态机的连续场景已合并为 Scene Group（如 B-系列在麦状态组）
- [ ] **无实现层语言**：grep 检查无接口路径、数据库字段名、精度类型、缓存方案、服务名称、消息队列
- [ ] **无 Mermaid/JSON/代码块**：grep 检查无 ` ```mermaid `、` ```json `、`function `、`const ` 等
- [ ] **状态流转用自然语言 + 表格**：状态流转章节只用文字 + Markdown table
- [ ] **每个操作覆盖正常 + 异常**：每个场景至少有一个异常场景描述
- [ ] **术语表自包含**：文档内使用的所有业务术语在术语表中都有定义，无需查阅外部文件
- [ ] **编号与 scene-list 一致**：grep 场景编号，逐个比对
- [ ] **数值完整**：PRD 中的阈值、限制、计算公式全部保留，无遗漏
- [ ] **无前后端分工建议**：不出现"前端负责"/"后端负责"/"接口联调"等表述

**强制验证脚本**：

```bash
# 检查禁止项
FILE="projects/{项目名}/deliverables/bspec-{项目简称}-v{N}.md"
echo "=== 禁止项检查 ==="
grep -n '```mermaid\|```json\|/api/\|Float\|INT\|VARCHAR\|Redis\|MySQL\|Kafka\|MQ\|interface\|前端负责\|后端负责\|接口联调' "$FILE" && echo "❌ 发现禁止项" || echo "✅ 无禁止项"

# 行数上限检查
echo "=== 行数体量检查 ==="
LINES=$(wc -l < "$FILE")
echo "行数: $LINES"
[ "$LINES" -gt 800 ] && echo "❌ 超出 800 行上限，请按 View 拆分或精简 P2/占位场景（研发 AI 上下文消费压力）" || echo "✅ 行数可控"

# 检查异常覆盖
echo "=== 异常覆盖检查 ==="
SCENE_COUNT=$(grep -c '^## [A-Z]' "$FILE" 2>/dev/null || echo 0)
EXCEPTION_COUNT=$(grep -ci '异常\|失败\|错误\|超时\|不存在\|已过期\|不可用' "$FILE" 2>/dev/null || echo 0)
echo "场景节数: $SCENE_COUNT, 异常相关行数: $EXCEPTION_COUNT"
[ "$EXCEPTION_COUNT" -lt "$SCENE_COUNT" ] && echo "⚠️ 部分场景可能缺少异常描述" || echo "✅ 异常覆盖充分"

# 检查术语表存在
echo "=== 术语表检查 ==="
grep -q '^## 术语表' "$FILE" && echo "✅ 术语表存在" || echo "❌ 缺少术语表"
```
