<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: prd
description: >
  当用户提到「PRD」「产品需求文档」「需求文档」「产品文档」「写个文档」
  「product requirements document」「product spec」时触发此 skill。
  也适用于：用户要求写功能需求、产品规格、feature spec、
  或基于交互大图/原型图输出需求文档。
  即使用户只说「写个需求文档」或「把这个功能写成文档」也应触发。
type: pipeline
output_format: .docx
output_prefix: prd-
pipeline_position: 5
depends_on: [scene-list]
optional_inputs: [interaction-map, prototype]
consumed_by: [behavior-spec, page-structure, test-cases, cross-check]
---
<!-- pm-ws-canary-236a5364 -->

# PRD Skill（产品需求文档）

## 硬规则（优先级最高）

### docx 版（复杂/超复杂链路产出）

- **Landscape 横版** docx-js
- 左 35% 截图占位 + 右 65% 完整需求
- 内容量不因加图缩减
- 九章：封面→目录→1 背景目标→2 场景地图→3 端A需求→4 端B需求→5 业务规则→6 非功能→7 技术架构→8 埋点监控→9 排期
- 格式：Arial 11pt，蓝色表头白字，页眉机密，H1 章 / H2 场景 / H3 子模块
- 编号全局一致，术语+字段与大图/原型对齐，跳转双向标注，异常不省

### 纯文字 PRD（简单链路产出）

- Markdown + mermaid 代码块（flowchart 优先）+ Markdown table
- **禁 HTML**，兼容飞书/钉钉文档原生渲染

## 输出格式

**输出 .docx 文件**，使用 `python-docx` 库生成。框架函数已封装在 `references/gen_prd_base.py` 中，直接 `from gen_prd_base import *` 调用，无需了解 docx 底层 API。

## PRD 标准结构

详细结构见 `references/prd-template.md`（完整的章节定义 + 填充规范）。

概览：封面元信息 → 1 背景目标 → 2 场景地图 → 3-5 各 View 详细需求（两列表格：左截图右说明）→ 6 业务规则 → 7 非功能性需求 → 8 埋点监控 → 9 里程碑排期。

## 如何使用

### Step 1：读取 Reference

**必读（SKILL 层规则）：**
```
view .claude/skills/prd/references/prd-template.md
```

**必读（项目层真相源）：**
```
view projects/{项目名}/scene-list.md
view projects/{项目名}/context.md
```

> 从 context.md 提取：第 4 章场景编号、第 5 章术语表、第 6 章业务规则。PRD 是这些决策的投影，不是重新发明。

按需（仅当用户说「参考例子」，或 prd-template.md 不足以支撑当前 PRD 结构时才读取）：
```
view .claude/skills/prd/references/prd-example.md
```

按需（需修改默认样式时）：
```
view .claude/skills/prd/references/prd-docx-styles.md
```

按需（需理解框架函数内部实现时）：
```
view .claude/skills/prd/references/gen_prd_base.py
```

- `prd-template.md` — PRD 章节结构 + 填充规范（**唯一的结构定义来源**）
- `scene-list.md` — 场景编号锁定，PRD 必须复用此编号体系
- `context.md` — 项目唯一真相源（第 4/5/6 章）
- `prd-example.md` — 实际 PRD 范例，仅当 template 描述不足以支撑或用户主动要求参考时才读
- `prd-docx-styles.md` — 样式定义，正常生成不需要读（gen_prd_base.py 已内置所有默认样式）
- `gen_prd_base.py` — 框架函数库源码，正常生成不需要读（看下方 API 速查即可）

### gen_prd_base.py API 速查

项目脚本开头写 `from gen_prd_base import *` 即可使用以下全部函数和常量，**不需要读源码**：

```python
# 导入方式（从 projects/{项目}/scripts/ 执行，向上 3 层到工作区根目录）
import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/prd/references'))
from gen_prd_base import *
```

| 函数 | 签名 | 用途 |
|------|------|------|
| `init_doc` | `(landscape=True) → Document` | 创建 Landscape 横版文档 |
| `cover_page` | `(doc, title, subtitle="产品需求文档（PRD）", scope="", meta_rows=[[label,val],...])` | 封面页（标题+副标题+属性表） |
| `h1` | `(doc, text)` | 一级标题（16pt 深色 + 蓝色底线） |
| `h2` | `(doc, text)` | 二级标题（13pt 蓝色） |
| `h3` | `(doc, text)` | 三级标题（11pt 深色） |
| `add_p` | `(doc, text="", size_pt=10, bold=False, color=None, italic=False, align=LEFT, before=0, after=4)` | 普通段落 |
| `bullet` | `(doc, text, size_pt=10)` | 列表项（• 前缀） |
| `make_table` | `(doc, headers: list[str], rows_data: list[list[str]], col_widths_cm: list[float], row_height_cm=None) → Table` | 通用表格（蓝底白字表头 + 隔行灰底） |
| `scene_table` | `(doc, scene_id, scene_name, right_blocks: list[tuple[str, list[str]]])` | 两列 Scene 表格（左截图占位 + 右说明） |
| `cell_text` | `(cell, text, size_pt=9, bold=False, color=None, italic=False, align=LEFT)` | 填充单元格文字 |
| `set_cell_bg` | `(cell, hex_color)` | 设置单元格背景色 |
| `set_cell_border` | `(cell, bottom={...}, top={...}, ...)` | 设置单元格边框 |
| `para_run` | `(para, text, font="Arial", size_pt=10, bold=False, color=None, italic=False) → Run` | 底层：给段落加 run |
| `C` | `dict` | 颜色常量：`C["textHeading"]="1A1A2E"`, `C["tableHeaderBg"]="2D81FF"`, `C["tagChange"]="D97706"` 等 |

### Step 2：收集产品信息

向用户确认：
1. **产品名称和版本**
2. **涉及哪些端/View**
3. **有几个核心场景**
4. **是否有会议纪要/方案变更需要体现**
5. **是否需要埋点/非功能性需求章节**

### Step 2.1：迭代模式判定（改已有功能时必做）

context.md 标注为「迭代现有功能」或用户说「改 XX 功能」时，自动进入迭代模式。迭代 PRD 和新建 PRD 的核心区别：

**原则**：PRD 只写本次增量的业务行为变化，不写历史规则全文。

**前置：规则冲突检测**

逐条对照新需求与现有系统规则，输出冲突表：

| 规则/场景 | 状态 | 现有内容 | 本次变更 | 影响的用户感知 |
|-----------|------|---------|---------|--------------|
| [规则A] | 沿用 | [原规则] | — | — |
| [规则B] | 修改 | [原规则] | [变更后] | [用户看到什么变化] |
| [规则C] | **冲突** | [原规则] | [本次要求] | 需业务决策 |
| [规则D] | 新增 | — | [新规则] | [新增感知] |

状态取值：**沿用 / 修改 / 新增 / 冲突**。

**冲突硬停**：发现「冲突」状态的规则后立即暂停，向用户说明冲突和影响范围，等用户给出明确决策后才继续。冲突未解决不得继续写 PRD。

**存量数据处理（迭代模式必填章节）**

判断本次变更上线后，已有数据/用户状态/进行中订单是否受影响：

| 触发条件 | 示例 |
|---------|------|
| 规则变更影响进行中的活动/订单 | 活动进行中修改奖励系数 |
| 用户状态枚举新增或删除 | 新增「已撤回」状态，历史用户如何迁移 |
| 计算公式变更影响历史结算 | 利率调整，已起息订单是否按新利率 |
| 门槛/上限变更影响已满足条件的用户 | 降低门槛，原不满足的用户是否自动获得资格 |

- 有存量影响 → 在 PRD 第 6 章业务规则中写明：受影响范围、处理规则、用户是否有感知
- 无存量影响 → 显式写「本次变更仅影响上线后的新数据，存量不受影响」，不得留空

**新建模式**则跳过此步，直接进 Step 2.5。

### Step 2.5：边写边审（PRD 质量内建）

PRD 不是一口气写完再审。每完成一个核心区块后暂停，以 QC 视角提出边界问题，用户回复后将结论**直接写入 PRD 对应位置**，再继续下一区块。

**节奏**：

| 暂停点 | 完成后暂停的区块 | 重点检查 |
|--------|----------------|---------|
| ① | 第 1 章背景目标 + 第 2 章场景地图 | 场景覆盖完整性、View 划分合理性 |
| ② | 第 3-5 章详细需求（每个 View 写完暂停一次） | 异常场景遗漏、边界定义模糊、研发 QC 可能理解不一致的地方 |
| ③ | 第 6 章业务规则 | 规则冲突、枚举值完整性、与现有功能冲突 |
| ④ | 第 7-9 章 | 非功能指标合理性、埋点覆盖度 |

**每次暂停的 5 个检查维度**：
1. 边界不清晰的描述（列出具体位置）
2. 缺失的异常场景
3. 可能产生歧义的表述（原文 + 建议改法）
4. 研发与 QC 可能理解不一致的地方
5. 与现有功能/已有产出物可能冲突的地方

**输出格式**：
```
我完成了「XXX」区块，在继续之前有以下问题需要确认：

【高优先级】需要明确回答
1. [问题]——影响：___

【中优先级】建议补充
2. [场景]——建议：___
```

**跳过条件**：用户说「快速模式」「不用审直接写完」→ 一气呵成写完，最后在末尾输出完整预审问题清单。

### Step 3：生成 docx

**脚本复用优先**：先检查 `projects/{项目名}/scripts/` 下是否有已有的 `gen_prd_*.py`：
- 有 → 读取已有脚本，修改数据/参数后重跑
- 没有 → 新写脚本，使用上方 API 速查表的导入方式和函数，只写内容区

脚本完成后保存到 `scripts/gen_prd_v{N}.py`。

**⛔ 禁止从头重写框架函数。** gen_prd_base.py 已包含上表全部函数和颜色常量。直接 import 调用，不要自己重新定义 `set_cell_bg`、`para_run`、`h1` 等函数。

## 写作规范

1. **场景说明要具体**：不写「展示列表」，写「3 列 Grid，卡片含封面图 + 状态角标 + 倒计时 + CTA」
2. **变更要标注**：所有相对上一版的变更在标题后加 `（变更）`，并在 1.3 核心变更中汇总
3. **引用要闭环**：提到其他场景时用 `→ 见 [编号]`，确保编号存在
4. **枚举要穷举**：所有下拉选项、状态值、业务线等在业务规则章节完整列出
5. **数值要量化**：目标、阈值、限制都用具体数字，不用「若干」「多个」
6. **截图占位符**：左列固定为截图占位，写 `← 此处粘贴原型截图`
7. **平台差异要说明**：Web/App/后台有差异时分别描述
8. **组件复用表**：跨 View 复用的组件在业务规则章节用矩阵表标注

## 自检清单

- [ ] 编号和 scene-list.md 一致，无遗漏
- [ ] 生成脚本已保存在 `projects/{项目}/scripts/` 目录，命名 `gen_prd_v{版本}.py`；产出物和脚本成对交付，缺一不可
- [ ] 术语与交互大图/原型对齐
- [ ] 所有 `→ 见 [编号]` 跳转编号存在
- [ ] 枚举值、状态名穷举完整
- [ ] 变更项已在 1.3 核心变更汇总

**强制验证脚本**（自检最后一步，不可跳过）：
```bash
bash scripts/check_prd.sh projects/{项目}/deliverables/XXX.docx projects/{项目}/scene-list.md
```
