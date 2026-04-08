<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: page-structure
description: >
  当 PRD 完成后需要给设计师 AI 或前端 AI 提供消费文档时触发，
  或用户说「页面结构」「给设计师的文档」「给前端的说明」「pspec」时触发。
  无 AI 消费需求时可跳过此步。
type: pipeline
output_format: .md
output_prefix: pspec-
pipeline_position: 6
depends_on: [scene-list, prd]
optional_inputs: [interaction-map, prototype]
consumed_by: [cross-check]
---
<!-- pm-ws-canary-236a5364 -->

# 页面结构 PRD Skill（Page Structure）

## 作用

全局 PRD 写完并通过自检后，从中切分出一份**页面结构 PRD**。页面结构是 PRD 在表现层的投影，面向设计师 AI 和前端 AI，描述页面长什么样、怎么交互。

核心价值：
- **自包含**：设计师 AI 读完后不需要再读 PRD、交互大图或任何外部文件
- **视觉导向**：关注模块布局、交互细节、状态差异，不涉及业务逻辑和系统响应
- **可并行**：和 behavior-spec 并列，一个关注表现层，一个关注逻辑层

## 与 behavior-spec 的分工

| 维度 | behavior-spec | page-structure |
|------|--------------|----------------|
| 关注点 | 用户行为 + 系统响应 | 页面外观 + 交互表现 |
| 消费者 | 研发 AI | 设计师 AI / 前端 AI |
| 异常态 | 系统做什么（逻辑） | 用户看到什么（视觉） |
| 状态 | 状态流转的触发条件和规则 | 不同状态下页面的视觉差异 |
| 交互 | 操作的业务含义 | 操作的视觉反馈和页面变化 |

两者各自独立、各自自包含。同一场景的异常态在两个文档中都会出现，但描述角度不同。

## 硬规则

### 必须包含

1. 页面基本信息：入口、页面类型（列表/详情/表单/看板等）、适用端
2. 模块拆解：编号 / 类型（导航/内容/操作/反馈） / 展示内容 / 交互行为 / 操作结果
3. 页面状态矩阵：每个模块在不同状态下的展示差异
4. 主路径交互流：用户从进入到完成的完整视觉路径
5. 异常路径：弹窗 / Loading / 空态 / 错误提示的视觉规格
6. 术语表：从 scene-list.md + context.md 继承，写入文档内

### 禁止写入

业务策略和「为什么做」（属于全局 PRD）/ 接口路径 / 数据库字段名 / 精度类型 / 舍入算法 / 缓存方案 / 前后端分工建议 / Mermaid / JSON / 代码片段 / 服务名称 / 消息队列 / 技术架构图 / 排期和里程碑

### 写法对比

| 场景 | 禁止 | 正确 |
|------|------|------|
| 状态变化 | state 变为 ACTIVE | 按钮从灰色「报名」变为绿色「查看进度」 |
| 异常展示 | 返回 403 错误码 | 顶部弹出红色 Toast「无权限访问」，2 秒后自动消失 |
| 列表描述 | 渲染 rewardList 数组 | 3 列卡片网格，每张卡片含活动封面、状态角标、倒计时、CTA 按钮 |
| 弹窗描述 | 弹出 modal 组件 | 居中弹窗，白底圆角卡片，标题 + 表单 + 两个按钮，遮罩点击可关闭 |

## 输出格式

**Markdown**（`.md`），存 `projects/{项目名}/deliverables/pspec-{项目简称}-v{N}.md`

命名前缀 `pspec-`，版本规则同其他产出物。

## 链路位置

复杂 / 超复杂链路中，**可选**步骤，位于 PRD 之后、拉通自检之前，和 behavior-spec 并列：

```
5. PRD .docx
   ├── 6a. 行为规格 .md（可选，behavior-spec）
   └── 6b. 页面结构 .md（可选，page-structure）
7. 拉通自检
```

两者可只出一个，也可都出，顺序不限。

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

**按需读取**（交互大图 / 原型已存在时补充）：
- 交互大图：`grep -A2 'class="st"'` 取 Scene 标题 + `grep "跨端"` 取数据流表
- 原型：`grep "const.*Data"` 取 JS 数据数组块 + `grep -A2 'class="st"'` 取页面标题

### Step 2：确定切分粒度

支持两种切分方式：

**A. 整体文档**（默认）：一份文档覆盖全部场景，按 scene 编号分节。

**B. 按页面/模块拆分**：每个页面或模块独立一份文档，各自自包含。适用于多设计师 AI 并行工作。

向用户确认切分方式后再开始写。

### Step 3：生成页面结构

严格按 `references/page-structure-template.md` 的章节结构填充。

填充规则：
- 按 scene 编号逐场景展开，编号复用 scene-list
- 模块拆解必须编号（M1/M2/M3...），编号在文档内唯一
- 页面状态矩阵必须覆盖所有 PRD 中定义的状态
- 交互流用步骤编号 + 文字描述，不用 Mermaid
- 异常路径必须描述视觉表现（弹窗样式、Toast 位置、空态插图等）
- 术语表从 scene-list.md + context.md 提取，写入文档内
- 如有可交互原型 HTML，在「配套说明」中引用文件路径；无原型则标注「原型待生成」

### Step 4：自检

按下方自检清单逐项验证，全部通过后才可交付。

### Step 5：保存 & 通知

保存到 `projects/{项目名}/deliverables/pspec-{项目简称}-v{N}.md`

通知用户：
- 文件路径
- 覆盖的场景编号列表
- 是否需要拆分多份

## 自检清单

- [ ] **模块有编号**：每个页面下的模块都有 M1/M2/M3 编号
- [ ] **状态矩阵覆盖全状态**：PRD 中定义的所有状态在矩阵中都有对应行
- [ ] **交互流含异常路径**：主路径之外至少覆盖 Loading / 空态 / 错误提示
- [ ] **无业务策略**：不出现「为什么做」「商业目标」「增长指标」等内容
- [ ] **无实现层语言**：grep 检查无接口路径、数据库字段名、精度类型、缓存方案、服务名称
- [ ] **无 Mermaid/JSON/代码块**：grep 检查无 ` ```mermaid `、` ```json `、`function `、`const ` 等
- [ ] **术语表自包含**：文档内使用的所有术语在术语表中都有定义
- [ ] **编号与 scene-list 一致**：grep 场景编号，逐个比对
- [ ] **视觉描述具体**：不出现「适当展示」「合理布局」等模糊表述，必须有位置、样式、交互细节

**强制验证脚本**：

```bash
FILE="projects/{项目名}/deliverables/pspec-{项目简称}-v{N}.md"
echo "=== 禁止项检查 ==="
grep -n '```mermaid\|```json\|/api/\|Float\|INT\|VARCHAR\|Redis\|MySQL\|Kafka\|MQ\|interface\|前端负责\|后端负责\|商业目标\|增长指标' "$FILE" && echo "❌ 发现禁止项" || echo "✅ 无禁止项"

echo "=== 模块编号检查 ==="
MODULE_COUNT=$(grep -c '^| M[0-9]' "$FILE" 2>/dev/null || echo 0)
echo "模块数: $MODULE_COUNT"
[ "$MODULE_COUNT" -lt 1 ] && echo "⚠️ 未发现模块编号（M1/M2/...）" || echo "✅ 模块已编号"

echo "=== 状态矩阵检查 ==="
grep -q '状态矩阵\|状态.*矩阵' "$FILE" && echo "✅ 状态矩阵存在" || echo "❌ 缺少状态矩阵"

echo "=== 异常路径检查 ==="
grep -qi '空态\|Loading\|加载\|错误提示\|异常.*路径\|弹窗.*错误\|Toast' "$FILE" && echo "✅ 异常路径已覆盖" || echo "⚠️ 可能缺少异常路径描述"

echo "=== 术语表检查 ==="
grep -q '^## 术语表' "$FILE" && echo "✅ 术语表存在" || echo "❌ 缺少术语表"
```
