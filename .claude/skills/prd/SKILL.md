---
name: prd
description: >
  当用户提到「PRD」「需求文档」时触发。基于 IMAP / 原型输出 PRD 亦触发。
type: pipeline
output_format: .docx
output_prefix: prd-
pipeline_position: 5
depends_on: [scene-list]
optional_inputs: [interaction-map, prototype]
consumed_by: [behavior-spec, page-structure, test-cases, cross-check, ops-handbook]
scripts:
  gen_prd_base.py: "新建 PRD — from gen_prd_base import *"
  update_prd_base.py: "升版/更新已有 PRD — from update_prd_base import *"
  check_prd.sh: "自检 — bash .claude/skills/prd/scripts/check_prd.sh <docx> <scene-list>"
  push_to_confluence_base.py: "推 Confluence — python3 push_to_confluence_base.py <docx> [--page-id <id>]"
  prd_screenshots.py: "截图回填 — python3 prd_screenshots.py --project {项目名} [--shot-only|--insert-only] [--scenes A-1,B-1]"
  humanize/: "讲人话扫描 + 修复 + CLI 子包（被 check_prd.sh / push gate 共享）— python3 -m humanize <docx>"
  sections.py: "5 个产品思维章节 helper（north_star / non_goals / open_questions / risks / alternatives / assumptions_validation）+ 第 2 章三节 helper（journey_main / end_role_split / cross_end_sequence）+ 档位感知体检"
  mermaid_screenshots.py: "mermaid LR 横排 → PNG（PRD docx 嵌图专用，由 sections.py 第 2 章 helper 内部默认调用；flowchart skill 不服务 PRD docx 场景，参 flowchart/SKILL.md 边界）"
  active_decisions.py: "context.md 第 7 章 ADR 决策派生（兼容 6 列表格 + list 格式）"
---

# PRD Skill（产品需求文档）

PRD 是 context.md 决策的投影，不是重新发明。docx 的产品思维由 `sections.py` 强制（北极星 / Non-goals / Open Questions / Risks），文风由 `humanize/` + `check_prd.sh` 三道闸守住。

## 何时用 / 路由

- **复杂链路**（≥ 2 端 / ≥ 5 场景 / 含跨场景跳转）→ 走 docx 标准档或完整档（本 skill）
- **简单链路**（单页面、纯文案、配置项调整）→ 走极简档 Markdown（本 skill 内置）
- **方案型项目**（跨系统 / 资金流转 / 多团队共建）→ 不走 pipeline，PM 自定 inputs/ 共建 PRD（见末尾「方案型项目」一节）
- 已有 docx 升版 → Step B「升版 / patch」，不重生
- 不要先读 SKILL 再绕回脚本：CLAUDE.md 快捷路由表里命中的命令直接跑

## 5 条核心硬规则（FAIL 即拦）

> 完整 13 条 + 速查表见 [`references/prd-rules.md`](references/prd-rules.md)。这里只挂最致命的 5 条，`check_prd.sh` + `pre-wiki-push-gate` hook 自动拦截。

1. **PRD 必须讲人话** — 正文禁出现 ① 流水账 / 版本痕迹（`(YYYY-MM-DD)` / `(变更)` / `决策 #N` / `反转说明：`）② snake_case 字段名（除字段表 / 枚举值 / 埋点表豁免）③ UI 设计参数（px / hex / ms，第 7 章性能契约保留）。命中 FAIL：`save_prd()` 自动 humanize；本地 `python3 -m humanize <docx>` 扫；推 wiki 前 `gate_check_quality` 同源拒推。完整规范：[`references/prd-human-voice.md`](references/prd-human-voice.md)。
2. **字体三件套不能省** — 老 docx 升版必跑 `normalize_punctuation` + `normalize_headings` + `normalize_fonts` + `ensure_theme`。缺 theme1.xml → docDefaults themed 引用悬空 → Word 强制 Arial。`check_prd.sh` 自动扫。
3. **项目脚本禁硬编码 BASE 路径** — 用 `BASE = Path(__file__).resolve().parents[3]`，硬编码 `/Users/xxx/pm-workspace` 换机器立炸 + `sys.path` 错指 → `from gen_prd_base import *` 无声失败 → docx 全 Normal style。
4. **升版 patch 路线必调 `assert_screenshots_fresh`** — 改完文字保存 docx 后立即断言截图 mtime ≥ 原型 mtime，过期 raise。配套 `post-docx-screenshot-check` hook 兜底。
5. **禁重定义框架函数** — `set_cell_text` / `set_cell_blocks` / `replace_para_text` / `fill_cell_blocks` / `fix_dpi` / `h1` / `h2` / `scene_table` 全部来自 `gen_prd_base` / `update_prd_base`，必须 `import *`。自定义会导致 cell 塌成无层次纯文本（`set_cell_text` 多行裸塞段落是最高频踩坑）。

## PRD 三档判定

| 档位 | 触发 | 章节 | 推 wiki |
|------|------|------|---------|
| **极简 One-pager** | ≤ 3 场景 / 单端 / 纯文案 / 配置项 | 4 节 Markdown（背景目标 + 场景方案 + 业务规则 + 度量含反向指标） | `scripts/md_to_confluence.py`（CLAUDE.md 快捷路由） |
| **标准** | 4-10 场景 / 2-3 端 | 九章 + 1.5 Non-goals + 6.x Open Questions（必填） | `push_to_confluence_base.py` |
| **完整** | 10+ 场景 / 多系统 / 跨团队 / 资金流转 | 标准 + 1.6 方案选型 + 7.x Risks & Mitigations | 同标准 |

判定原则：**没拿准往上一档**（保守优于事后补章节）。模板与判档示例：[`references/prd-template.md`](references/prd-template.md)。

## 任务模式

### A. 新建 PRD（`gen_prd_v{N}.py` 路径）

**Step 1 · Read**：`scene-list.md` + `context.md` 第 4/5/6 章（场景/术语/业务规则）+ [`prd-template.md`](references/prd-template.md) + [`prd-human-voice.md`](references/prd-human-voice.md) + [`prd-storytelling.md`](references/prd-storytelling.md)（叙事投影：context 主线 → PRD 各章串起来）+ [`metrics-framework.md`](references/metrics-framework.md)（1.2 节四件套方法论：北极星 / 配套 / Guardrail / 非目标）。

**Step 2 · 收集** + 档位判定 + 迭代模式判定（改已有功能时强制做规则冲突检测 + 存量数据处理 + 1.3 基线收集，发现「冲突」立即停问用户）。

**Step 3 · 边写边审**（PRD 质量内建）：每完成一个核心区块（背景目标 / 各 View / 业务规则 / NFR）暂停一次，按 5 个维度抛预审问题（边界 / 异常 / 歧义 / 研发-QC 一致性 / 现存冲突），用户答完写入对应位置再继续。`快速模式` 跳过暂停一气写完，最后统一给问题清单。

**Step 4 · 分步生成 docx**（标准 / 完整档；极简档跳到 4D 直推）：脚本路径 `projects/{项目}/scripts/gen_prd_v{N}.py`。

| 步 | 内容 | 行上限 |
|----|------|--------|
| 4a 骨架 | `init_doc` + `cover_page` + 第 1-2 章 + 各 H1 占位 + `doc.save()` | ≤ 80 行 |
| 4b 按 View 填 scene_table | 每个 View 一次 Write 追加，全 `scene_table(doc, scene_id, name, [(title, [lines])])` | ≤ 300 行/次 |
| 4c 收尾 | 第 6-9 章（业务规则 + NFR + 埋点 + 里程碑） | ≤ 200 行 |

每次 Write 后 `python3 gen_prd_v{N}.py` 跑通 + grep 确认 scene 数对齐 scene-list。骨架完成必停问用户（除非「快速模式」）。

**4 项产品思维 helper**（来自 `sections.py`，按档位选用）：

```python
from sections import (
    north_star_section,             # 1.2 北极星 + 配套 + 反向指标 + 非目标（全档位必填）
    non_goals_section,              # 1.5 Non-goals（标准 + 完整必填）
    alternatives_table,             # 1.6 方案选型（仅完整档）
    open_questions_table,           # 6.x Open Questions（全档位选填，无未决项写「无」）
    assumptions_validation_table,   # 6.x 关键假设清单 6 列（项目级假设追踪，源 context 第 6 章）
    risks_table,                    # 7.x Risks & Mitigations（完整必填，标准选填）
    scan_completeness, report_completeness,  # save_prd 内调用，warn 不阻断
)
```

**Step 5 · 截图**（见 C）+ **Step 6 · 自检**（`check_prd.sh`）+ **Step 7 · 推 wiki**（见 D）。

### B. 升版 / patch（不重生 docx，原地改文字 + 截图）

**强制顺序**（缺一不可，违反 hook 拦截）：

1. **改文字**：`update_prd_v{N}.py` 用 `replace_para_text` / `set_cell_blocks` / `insert_*` helper patch 原 docx
2. **重拍截图**：`screenshot_prd_v{N}.py` 基于新原型重拍受影响截图
3. **回填截图**：`screenshot_prd_v{N}.py.insert_into_prd()` 把新 PNG 写入 docx 内嵌位
4. **断言新鲜**：`assert_screenshots_fresh(TARGET, PROTOTYPE_HTML, SHOT_DIR)`，过期 raise（参 R7a）
5. **字体三件套**（升旧 docx 必做）：`normalize_punctuation` → `normalize_headings` → `normalize_fonts` → `doc.save` → `ensure_theme(path)`（参 R12）
6. 推 wiki

**patch 安全姿势**（参 R8）：

- 插新章节 → `insert_heading_before(anchor, '6.4 归因漏斗', level=2)`
- 插描述段 → `insert_description_after(doc, '2.2 View 2', '描述...')`
- 改单元格多段 → `set_cell_blocks(cell, [(title, lines)])`
- 删空 2 列 scene_table → `insert_scene_blocks` + `remove_table`（参 R9）

**python-docx 陷阱**：`table.add_row()` 不继承 cell 级 bold / size / color，必须照同表已有数据行手动逐 cell 设格式。

### C. 截图回填（`prd_screenshots.py`）

来源优先级：**可交互原型 > 交互大图（降级）**。有原型必须用原型，交互大图截图仅在「无原型 / 原型未覆盖」时降级。

```bash
python3 .claude/skills/prd/scripts/prd_screenshots.py --project {项目名} \
    [--shot-only | --insert-only] [--scenes A-1,B-1]
```

**截图规范**：viewport 1440×900 + deviceScaleFactor 2 + 必须 PNG。Phone 类（aspect < 0.7）截 `.app-shell` + `round_phone_corners` 圆角透明化（参 R5）。交互大图降级时只截 `.phone` / `.webframe`，先 `dismissAllOverlays()` + 隐藏 `.anno / .anno-n / .ann-card / .ann-tag / .aw / .flow-note / .side-nav`。截图存放：新建 `screenshots/prd/`，升版 `screenshots/prd_v{N}/`。

**插入规范**：`replace_cell_image` 内置 `fix_dpi(144)` 防止虚化。前端 7.0 cm，App 5.0 cm。

### D. 推 Confluence

**极简档（Markdown）** → 走根目录 `scripts/md_to_confluence.py`（CLAUDE.md 快捷路由覆盖），`pre-wiki-push-gate` hook 给 md 路径走 warn 模式。

**标准 / 完整档（docx）** → `push_to_confluence_base.py`，三种用法：

```bash
# 路径 0：已推送过（项目级 .confluence.json 缓存 page_id，零参数）
python3 .claude/skills/prd/scripts/push_to_confluence_base.py "<docx>"

# 路径 A：新建页面 / 按标题 upsert
python3 .claude/skills/prd/scripts/push_to_confluence_base.py "<docx>" \
    --title "Platform C · {项目名} · v{N}" --space jituankejizhongxin --parent-id "<id>"

# 路径 B：已知 pageId 直接覆盖
python3 .claude/skills/prd/scripts/push_to_confluence_base.py "<docx>" --page-id 155652375
```

`gate_check_quality` 默认拒推（圈数字 / 裸场景编号 / 决策编号 / 1.3 流水账启发式），误报加 `--skip-self-check` 强推。图片宽度按宽高比自动选（phone 300px / web 600px）。

## 关联 Hook 矩阵

| hook | 拦什么 | 触发 |
|------|--------|------|
| `pre-wiki-push-gate.sh` | 推 wiki 前 docx 未过 `check_prd.sh` / md 路径走 warn | Bash 含 `push_to_confluence_base.py` 或 `md_to_confluence.py` |
| `post-docx-screenshot-check.sh` | docx 改完截图过期 | Bash 跑 `update_*.py` / `patch_proto_*.py` |
| `pre-deliverable-source-gate.sh` | 直接 Edit/Write 已脚本化的 docx | Edit/Write 命中 `deliverables/*.docx` |
| `pre-version-sync-gate.sh` | scene-list 与 context.md 版本不一致 | 骨架脚本生成前 |
| `post-cjk-punct-check.sh` | 中文旁半角 `, : ( )` | Write/Edit 任何中文 md |
| `pre-commit` | Skill / 规则文件变更跑防腐审计 | git commit |

## API 速查表

项目脚本开头：

```python
import sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[3]                       # pm-workspace 根
sys.path.insert(0, str(BASE / '.claude/skills/prd/scripts'))
from gen_prd_base import *      # 新建：C / FONT / h1/h2/h3 / scene_table / make_table / save_prd / ...
from update_prd_base import *   # 升版：replace_para_text / set_cell_blocks / replace_cell_image / normalize_* / humanize_* / assert_screenshots_fresh / ...
from sections import (
    north_star_section, non_goals_section, alternatives_table,
    open_questions_table, risks_table,
)
```

**`gen_prd_base`（新建专用，~30 个）**：

`init_doc` / `cover_page(doc, title, subtitle, scope, meta_rows)` / `h1` / `h2` / `h3` / `chapter_story(doc, text)`（功能章 3-5 必填，斜体浅灰） / `add_p` / `bullet` / `make_table(doc, headers, rows_data, col_widths_cm)` / `scene_table(doc, scene_id, name, right_blocks)` / `cell_text` / `set_cell_bg` / `set_cell_border` / `para_run` / `C`（颜色 dict，`textHeading=141413` Anthropic Dark / `accentBlue=D97757` terra cotta） / `FONT`（Lora+Noto Serif SC / Poppins+Noto Sans SC / JetBrains Mono） / `save_prd(doc, path, tier='standard'|'mini'|'full', extra_jargon=...)`（一键保存 + humanize + 标点 + 字体 + theme + 体检）

**`update_prd_base`（升版专用，~33 个）**：

`replace_para_text` / `search_replace_para` / `set_cell_text` / **`set_cell_blocks(cell, blocks, numbered=True)`** ← 多段层次单元格必用 / `replace_cell_image(cell, img_path, width_cm)`（内置 `fix_dpi`） / `normalize_headings` / `normalize_fonts` / `normalize_punctuation` / `ensure_theme(path)` / `insert_heading_before(anchor, text, level)` / `insert_paragraph_before` / `insert_description_after(doc, anchor_keyword, text)`（锚点未命中抛异常） / `insert_scene_blocks(anchor, blocks, heading_level=3)`（无截图 Scene 降级 body 级） / `remove_table(table)` / `humanize_doc(doc, scene_to_human=[(code, human)...])` / `humanize_prd_voice(doc, extra_jargon=[...])` / `fix_scene_cell_numbering` / `cell_paragraphs_to_blocks(cell)` / `assert_screenshots_fresh(docx_path, prototype_html, shot_dir)`

**`sections`（产品思维章节，5 个 helper + 体检）**：见 Step 4 helper 列表。

> **`set_cell_text` vs `set_cell_blocks` 选择**：升版 Scene 表格右列、后台 table 这种「多段落 + 层次」的单元格，**必须**用 `set_cell_blocks` 结构化填充。`set_cell_text` 塞多行含 `\n` 字符串会被渲染成单段无层次纯文本（活动中心 v4.7 历史踩坑）。

## 自检清单

**全档位通用**：

- [ ] 编号和 scene-list.md 一致，无遗漏
- [ ] 生成脚本已存 `projects/{项目}/scripts/gen_prd_v{N}.py`，产出物和脚本成对交付
- [ ] 术语与 context.md 第 5 章 / IMAP / 原型对齐
- [ ] `→ 见 [编号]` 跳转目标编号存在
- [ ] 通过 `bash .claude/skills/prd/scripts/check_prd.sh <docx> <scene-list>`（不可跳）

**标准 + 完整档增量**：

- [ ] 1.2 含反向指标 / 非目标关键词
- [ ] 1.5 Non-goals 章存在（标准 + 完整必填）
- [ ] 6.x Open Questions 表存在（无未决项也要显式「无」）
- [ ] 两列表格左列全部为真实截图，无「← 此处粘贴」占位
- [ ] App 截图为 `.app-shell` 级别，phone 截图已圆角透明化
- [ ] 所有截图已 `fix_dpi(144)` 修正
- [ ] 迭代项目 1.3 变更范围已收敛到「vs 线上 delta」一行（不是版本 diff 流水）

**完整档增量**：

- [ ] 7.x Risks & Mitigations 表存在
- [ ] 1.6 方案选型说明（多方案讨论时必填）

## 方案型项目（不走标准 pipeline）

满足任一条件即为方案型：跨两个或以上独立系统 / 资金流转 / 结算 / 授信 / 多团队共建（含「🔲 待填」占位）/ 无 UI 改动（纯后端架构）。

文档分工：

| 文档 | 定位 | 维护者 | 体量 |
|------|------|--------|------|
| `context.md` | Claude Code 工作上下文：当前状态 + 关键决策 + 术语 + 待办 | PM + Claude Code | 300-500 行 |
| `inputs/共建 PRD` | 完整方案自包含，各组填空 | PM 骨架 + 各组填空 | 1000+ 行 |
| `inputs/机制说明` 等深度推演 | Chat 讨论产出，归档不再单独维护 | Chat Opus | 一次性 |

context.md 章节按项目特点自定义，不强制九章模板。
