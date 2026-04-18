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

### 方案型项目（不走标准 pipeline）

满足以下任一条件时为方案型项目：
- 跨两个或以上独立系统（不是前后端分离，是真的两个系统对接）
- 涉及资金流转 / 结算 / 授信
- 需要多团队共建（PRD 有"🔲 待填"占位）
- 没有用户界面改动（纯后端/架构方案）

方案型项目**不走标准 pipeline**（scene-list → imap → proto → PRD），产出物由 PM 按实际需要决定。context.md 章节结构按项目特点自定义（建议对标共建 PRD 章节），不强制九章模板。

文档分工：

| 文档 | 定位 | 谁维护 | 体量 |
|------|------|--------|------|
| context.md | Claude Code 工作上下文：当前状态+关键决策+术语+待办 | PM + Claude Code | 300-500 行 |
| 共建 PRD（inputs/） | 完整方案自包含，各组填空 | PM（骨架）+ 各组（填空）| 1000+ 行 |
| 机制说明等深度推演 | Chat 讨论产出，归档到 inputs/ | Chat Opus | 归档后不单独维护 |

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
- `gen_prd_base.py` — **新建** PRD 的框架函数库源码，正常生成不需要读（看下方 API 速查即可）
- `update_prd_base.py` — **升版/更新**已有 PRD 的辅助函数（replace_para_text / set_cell_text / replace_cell_image / fix_dpi），正常不需要读源码
- `push_to_confluence_base.py` — 推送到 Confluence Server 的脚本（mammoth 转换 + 附件上传）

### gen_prd_base.py API 速查（新建 PRD）

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

### update_prd_base.py API 速查（升版/更新已有 PRD）

升版脚本写 `from update_prd_base import *` 即可使用以下函数，**不需要读源码**：

```python
# 导入方式（同 gen_prd_base）
import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/prd/references'))
from update_prd_base import *
```

| 函数 | 签名 | 用途 |
|------|------|------|
| `replace_para_text` | `(para, new_text: str)` | 整体替换段落文字，保留首 run 格式 |
| `search_replace_para` | `(para, old: str, new: str) → bool` | 段落内搜索替换（跨 run 拼接匹配），命中返回 True |
| `set_cell_text` | `(cell, text: str)` | 清空单元格全部内容，写入纯文本（仅限短字符串，多行用 set_cell_blocks） |
| `set_cell_blocks` | `(cell, blocks: list[tuple[str, list[str]]], numbered=True)` | 清空单元格，按结构化 blocks 重建（title 粗体 + 子条目自动加 `1./2./3.` 编号），视觉与 scene_table 右列一致。**升版 Scene/后台 table 时优先用它**。lines 已含 `N. ` 前缀或以 `  - ` 开头的二级缩进行不会被重复编号；纯序号数据（如 P0 同步"Launch Pool / 现货充值赛"列表）传 `numbered=False` |
| `replace_cell_image` | `(cell, img_path, width_cm=7.0)` | 清空单元格旧图，插入新截图（**内部自动调 fix_dpi，无需手动调**） |
| `fix_dpi` | `(png_path, dpi=144) → str` | 修正 @2x 截图 DPI 元数据，防止 docx 里虚化（replace_cell_image 已内置，单独调用于调试） |
| `normalize_headings` | `(doc) → (h1_count, h2_count)` | 旧 docx 修缮专用:补 Heading 1/2 的 run 级字色字号粗体 + H1 段落下边框 #2E75B6。幂等。老脚本常用 `add_paragraph(style='Heading N')` 直接产段落,run 级属性缺失,渲染成黑色无下划线,视觉与 `gen_prd_base.h1()/h2()` 产出不一致——升版前调此函数归一化 |

**⚠️ set_cell_text vs set_cell_blocks 选择**：升版 Scene 表格右列、后台 table 这种"多段落+层次"的单元格，**必须**用 `set_cell_blocks` 结构化填充。用 `set_cell_text` 塞多行含 `\n` 的字符串会被渲染成**单段落无层次纯文本**（历史项目已有此类问题，如 htx-activity-center v4.7）。

**⛔ 禁止在项目脚本里重新定义这些函数。** 已有实现处理了 python-docx 的段落/run 边界、多余段落清理、DPI 修正等细节，手写容易遗漏导致行为漂移。

### Step 1.5：迭代已有 docx 的操作顺序（升版时必读）

当任务是「更新已有 PRD docx」（而非从头生成）时，严格按此顺序：

1. **先改内容**：更新文字、表格、章节标题等文本变更
2. **再插截图**：内容定稿后再截图插入左列
3. **最后推送**：Confluence / 归档

反过来（先截图再改内容）会导致截图与内容不匹配，或插入的截图被内容变更覆盖。

**python-docx `table.add_row()` 格式陷阱**：新增行只继承表级属性（边框/列宽），**不继承** cell 级格式（bold / font.size / font.color / shading）。新增行后必须手动对齐格式——参照同表已有数据行的 bold、size、color 逐 cell 设置，否则新行会和旧行视觉不一致。

### ⛔ 升版硬规则（违反即重来，check_prd.sh 会自动拦截）

1. **禁止在项目脚本里重定义** `set_cell_text` / `set_cell_blocks` / `replace_para_text` / `fill_cell_blocks` / `fix_dpi`。必须 `from update_prd_base import *`。
   - 旧脚本常见错误：自己写一个 `set_cell_text(cell, text)`，把含 `\n` 的多行字符串塞进单段落——右列会塌成无层次纯文本。
   - 正确做法：多段落/多层次内容用 `set_cell_blocks(cell, [(title, [lines])...])`，它会渲染粗体模块 title + numbered 子项。
2. **禁止圈数字 ①②③④⑤⑥⑦⑧⑨⑩**（CLAUDE.md 格式规范）。章节/小节/步骤一律 `1. 2. 3.`。
3. **Scene 右列 lines 默认被 `fill_cell_blocks` 自动加 `1./2./3.` 编号**（`numbered=True`）。lines 里写白话即可：
   - 已含 `N. ` 前缀的行保持原样（不重复编号）
   - 以 `  - ` 开头的二级缩进行跳过编号
   - 需要关闭自动编号时显式传 `numbered=False`（如纯序号列表"1. Launch Pool / 2. 现货充值赛"这种本来就是数据枚举）
4. **docx 已有 PNG 截图 DPI 默认 72（Playwright deviceScaleFactor=2 产物）**，需遍历 `doc.part.rels` 用 PIL 重写 `dpi=(144, 144)`。`replace_cell_image` 会自动 `fix_dpi`；批量修旧 docx 时自己写 loop。
5. **Phone 比例截图（aspect < 0.7）必须圆角透明化**，否则深色主题里 4 角残留白方块。用 `PIL.ImageDraw.rounded_rectangle` 生成 alpha mask。
6. **所有 docx 产出必调 `normalize_punctuation(doc)`**（soul.md 硬规则：中文相邻的半角 `,:()` 必须全角 `，：（）`）。gen/update/refine 脚本保存 docx 前调用，check_prd.sh 会扫残留。
7. **升旧 docx 必调 `normalize_headings(doc)`**：老脚本用 `add_paragraph(style='Heading 1')` 直接产 H1/H2 时不染 run，Word 渲染成黑色无下划线，视觉与新 PRD 不一致。`normalize_headings` 幂等：H1 补 `fg=#1A1A2E + 下边框#2E75B6`，H2 补 `fg=#2E75B6`。同步处理表头 bg 从旧 `D5E8F0` 升到 `2D81FF` + 白字（`set_cell_bg` 已修复旧 shd 残留 bug，可直接调）。

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

### Step 3：生成 docx（强制分步，违反即重来）

**脚本复用优先**：先检查 `projects/{项目名}/scripts/` 下是否有已有的 `gen_prd_*.py`：
- 有 → 读取已有脚本，修改数据/参数后重跑
- 没有 → 按下方 3a/3b/3c 三步分段产出，**禁止单次 Write 写完整脚本**

**⛔ 新建 PRD 硬规则（check_prd.sh 会拦截）**：

1. **禁止单次 Write > 300 行**。骨架一次、每个 View 一次、业务规则+埋点+排期一次，至少 3 次 Write。
2. **每次 Write 后立即 `python3 gen_prd_v{N}.py` 跑通验证无 SyntaxError / 无异常**，失败先修复再继续。
3. **3a 骨架完成后必须停下等用户确认结构**，除非用户明确说「快速模式 / 不用暂停」。
4. **⛔ 禁止重写框架函数**。`set_cell_bg` / `para_run` / `h1` / `h2` / `scene_table` / `make_table` / `bullet` / `fill_cell_blocks` 全部来自 `gen_prd_base`，直接 import 调用。自定义一个立刻被 check_prd.sh 拦截。

**为什么分步**：PRD 15+ scene 的脚本常到 500-700 行，一把梭容易埋 SyntaxError、scene 编号串味、章节漏章。分段写每段 200-300 行好 review、好定位错、弱模型也能照抄骨架补填。

#### Step 3a · 骨架（≤ 80 行）

只写：import + `init_doc` + `cover_page` + 第 1-2 章（背景 / 目标 / 核心变更 / 用户角色 / 场景地图两个 View 的 `make_table`）+ 各 H1 占位（第 3/4/5/6/7/8/9 章用 `h1(doc, "3. ...")` 留题头，不填内容）+ `doc.save()`。

产出后立即 `python3 scripts/gen_prd_v{N}.py` 验证产出 docx 打得开、章节结构对，**停下来告诉用户「骨架完成，章节 X/Y/Z，可以继续填内容吗」**。

#### Step 3b · 按 View 填充 scene_table（每次 ≤ 300 行）

每个 View 一次 Write 追加，内容为该 View 全部 `scene_table(doc, scene_id, name, [(title, [lines]), ...])` 调用。典型节奏：
- View 1（H5 主场景 + 组件）一次
- View 2（后台 / 第二端）一次
- 场景 ≥ 10 个的 View 继续拆（先主场景、再组件弹窗）

每次追加后立即 python3 跑通 + grep 确认 scene 数量对齐 `scene-list.md`。scene 编号错、内容塌成扁平字符串、忘记 `[(title, lines)]` 结构——这些 bug 此时就能发现。

#### Step 3c · 收尾（业务规则 + 非功能 + 埋点 + 里程碑）

一次追加第 6-9 章（`make_table` + `bullet` 为主，内容来自 context.md 第 6 章业务规则表）。

产出后跑 **Step 4 截图** → **check_prd.sh 自检**。

**重复 Scene 抽函数**：相似结构场景（如"结果公示" A-2/B-2/C-2 只是文案换）写一个 `render_result_scene(doc, scene_id, stage_name, next_stage)` 调用 `scene_table`，省 15-20% 行数。

## 写作规范

1. **场景说明要具体**：不写「展示列表」，写「3 列 Grid，卡片含封面图 + 状态角标 + 倒计时 + CTA」
2. **变更要标注**：所有相对上一版的变更在标题后加 `（变更）`，并在 1.3 核心变更中汇总
3. **引用要闭环**：提到其他场景时用 `→ 见 [编号]`，确保编号存在
4. **枚举要穷举**：所有下拉选项、状态值、业务线等在业务规则章节完整列出
5. **数值要量化**：目标、阈值、限制都用具体数字，不用「若干」「多个」
6. **截图自动插入**：左列通过 Playwright 截图 + python-docx 自动插入，不留占位符交付（见 Step 4）
7. **平台差异要说明**：Web/App/后台有差异时分别描述
8. **组件复用表**：跨 View 复用的组件在业务规则章节用矩阵表标注

## Step 4：原型截图插入（docx 产出时必做）

PRD 两列表格左列的「← 此处粘贴原型截图」必须替换为真实截图，不允许交付占位符。

**流程**：Playwright 打开原型 HTML → 切换到目标视图/Tab → 元素级截图 → python-docx 插入到对应 Table 左列 cell。

**截图来源优先级（强制）**：可交互原型 > 交互大图（降级）
- 有原型时，截图必须来自原型，不得从交互大图截
- 交互大图截图仅在「无原型」或「原型未覆盖该场景」时使用（如 M-7 同步逻辑图等纯流程场景）

**截图脚本**（Python 优先，依赖 `playwright`）：
```
projects/{项目}/scripts/screenshot_for_prd.py
```

**插入脚本**（Python，依赖 `python-docx`）：
```
projects/{项目}/scripts/insert_screenshots_to_prd.py
```

**截图规范**：
- viewport: 1440x900, deviceScaleFactor: 2（Retina）
- 格式：**必须 PNG**（`path` 以 `.png` 结尾），禁止 JPEG，避免压缩失真
- Web/MGT 视图：截对应容器元素（`#acDeviceWeb` / `#czDeviceWeb` / `#mgt-view`）
- App 视图：只截手机壳（`.app-shell`），不截外层容器
- **交互大图截图（无原型时的降级方案）**：只截设备框元素（`.phone` / `.webframe`），计算同一 Scene 内所有设备框的 bounding box 合并截取。**禁止截整个 Scene 区域**——右侧标注（`.anno` / `.aw` / `.flow-note`）是大图的阅读辅助，不属于 PRD 截图范围
- **标注清理（强制，交互大图截图专用）**：截 `.phone` / `.webframe` 前必须隐藏所有标注元素，避免 `.anno-n` 编号圆点、`.anno` 虚线框叠加在设备上被截进：
  ```js
  page.evaluate("""
      document.querySelectorAll(
        '.anno, .anno-n, .ann-card, .ann-tag, .aw, .flow-note, .side-nav'
      ).forEach(el => el.style.display = 'none');
  """)
  ```
- **Phone 圆角透明化（强制，仅 `.phone` 截图）**：`.phone` 是圆角矩形（`border-radius: 36px`），Playwright 元素截图的 bounding box 是正矩形，4 个角会残留 imap 画布背景色。PNG 在深色主题下（GitHub README dark mode、docx 以外的任何深色阅读器）呈现为 4 个突兀方块。插入前必须 Pillow 圆角蒙版处理：
  ```python
  from PIL import Image, ImageDraw
  def round_phone_corners(png_path: str, radius_px: int = 72):
      """CSS border-radius 36px × deviceScaleFactor 2 = 72 像素半径。
      CSS 改 radius 后此处同步。仅 phone 处理，webframe 本就是矩形。"""
      img = Image.open(png_path).convert("RGBA")
      mask = Image.new("L", img.size, 0)
      ImageDraw.Draw(mask).rounded_rectangle(
          [(0, 0), img.size], radius=radius_px, fill=255)
      img.putalpha(mask)
      img.save(png_path, "PNG")
  # 调用：device.screenshot(path=out, omit_background=True) 后
  #       if device_type == "phone": round_phone_corners(out)
  ```
- 抽屉/弹窗：先触发 JS 打开，再截父容器
- MGT 各子页：通过 `swPage()` / `swView()` 切换后截图
- 截图存放：新建 PRD → `screenshots/prd/`；升版 PRD → `screenshots/prd_v{N}/`（避免覆盖旧截图）
- **浮层清理（强制）**：每次切换视图前 + 每次截图前，必须调用 `dismissAllOverlays()` 清除所有 `position: fixed` 浮层（drawer / modal / overlay / sheet），用 `el.style.display='none'` 强制隐藏，仅 `classList.remove('show')` 不够（JS 副作用可能重新触发）

**插入规范**：
- **DPI 修正（必做，否则截图在 docx 里虚化）**：`deviceScaleFactor: 2` 截图的 PNG DPI 元数据默认 72，python-docx 会误判尺寸并强行缩放导致模糊。插入前必须用 Pillow 修正为 144：
  ```python
  from PIL import Image
  def fix_dpi(path: str) -> str:
      """修正 @2x 截图 DPI 元数据，返回原路径（in-place）"""
      img = Image.open(path)
      img.save(path, dpi=(144, 144))
      return path
  # 调用：fix_dpi(screenshot_path) 后再 cell.add_picture(...)
  ```
- 前端 Scene 截图宽度 7.0cm，App 截图 5.0cm
- Table 索引与 PRD 结构对应（Table 5 起为 Scene 表格，按章节顺序）
- M-7 同步逻辑无独立视图时复用 M-1 截图

**已有项目复用**：先检查 `projects/{项目}/scripts/` 下是否已有 `screenshot_for_prd.js` + `insert_screenshots_to_prd.py`，有则复用修改，无则新写。

**依赖安装**：
```bash
npm init playwright@latest   # 首次安装
npx playwright install chromium
```

## Step 5：推送到 Confluence（可选，每次问用户）

PRD 自检通过后，主动询问：「PRD 已生成，是否推送到 Confluence？」

### 路径 A：新建页面 / 按标题 upsert

```bash
python3 .claude/skills/prd/references/push_to_confluence_base.py \
    "projects/{项目}/deliverables/{PRD文件}.docx" \
    "{页面标题}" \
    "{spaceKey}" \
    "{父页面 pageId（可选）}"
```

- **页面标题格式**：`HTX · {项目名} · {版本号}`（例：HTX · 活动中心 · v4.7）
- spaceKey / 父页面 pageId 由用户提供，或用 Confluence MCP `confluence_get_page` 查父页面
- 重复推送自动 upsert；图片默认宽 600px，App 截图可传 `img_width=300`

### 路径 B：用户给了 Confluence URL（已知 pageId）

从 URL `?pageId=XXXXXX` 提取 pageId，先用 `confluence_get_page` 查当前版本号，再调内部函数直接更新（跳过 title 搜索，同时可重命名标题）：

```python
python3 -c "
import sys; sys.path.insert(0, '.claude/skills/prd/references')
from push_to_confluence_base import convert_docx, update_page

PAGE_ID = 'XXXXXX'          # 从 URL ?pageId= 提取
NEW_TITLE = 'HTX · 活动中心 · v4.7'
CURRENT_VERSION = 2         # 从 confluence_get_page 的 version 字段取
DOCX = 'projects/{项目}/deliverables/{PRD}.docx'

body = convert_docx(DOCX, PAGE_ID)
update_page(PAGE_ID, NEW_TITLE, body, CURRENT_VERSION)
print('完成')
"
```

## 自检清单

- [ ] 编号和 scene-list.md 一致，无遗漏
- [ ] 生成脚本已保存在 `projects/{项目}/scripts/` 目录，命名 `gen_prd_v{版本}.py`；产出物和脚本成对交付，缺一不可
- [ ] 术语与交互大图/原型对齐
- [ ] 所有 `→ 见 [编号]` 跳转编号存在
- [ ] 枚举值、状态名穷举完整
- [ ] 变更项已在 1.3 核心变更汇总
- [ ] 两列表格左列全部为真实截图，无「此处粘贴」占位符残留
- [ ] App 截图为手机壳级别（`.app-shell`），非全屏容器
- [ ] MGT 截图无浮层/弹窗/遮罩泄露（逐张目视确认）
- [ ] 所有截图已经过 `fix_dpi()` 修正（DPI=144），在 docx 中无虚化/模糊

**强制验证脚本**（自检最后一步，不可跳过）：
```bash
bash references/check_prd.sh projects/{项目}/deliverables/XXX.docx projects/{项目}/scene-list.md
```

**注意**：mammoth 会尽力转换表格结构，但 docx 的复杂排版（合并单元格、多级列表）在 Confluence 中可能有轻微变形，建议推送后目视确认一次。
