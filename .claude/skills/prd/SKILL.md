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
