---
name: ops-handbook
description: >
  当用户提到「运营手册」「操作手册」「后台使用文档」「运营操作手册」时触发。给运营 / 客服 / BD 看的步骤化文档（docx），PRD 终稿后产出。注：「SOP」走 ppt skill（HTML 多 Tab）。
type: pipeline
output_format: .docx
output_prefix: handbook-
pipeline_position: 9
depends_on: [prd]
optional_inputs: []
consumed_by: []
scripts:
  gen_handbook_base.py: "新建手册 — from gen_handbook_base import *（直接复用 PRD core/ 美学栈）"
  handbook_screenshots.py: "CMS 后台截图回填 — python3 handbook_screenshots.py --project {项目名} [--scenes step-1,step-2]"
  check_handbook.sh: "自检 — bash .claude/skills/ops-handbook/scripts/check_handbook.sh <docx>"
---

# ops-handbook Skill（运营操作手册）

PRD 是研发 / 评审看的需求源，运营手册是 **运营 / 客服 / BD 上手干活时翻的步骤书**。受众、时序、模板都不同，独立成 skill。

## 何时用 / 路由

- **触发条件**：PRD 终稿 + 后台已有可截图功能 → 出运营手册
- **不触发**：场景文档 / 需求文档（走 prd skill）；前端用户教学（不在 PM 工区）
- **基线参考**：[活动中心运营操作手册 v3](../../../projects/growth/activity-center/deliverables/活动中心_运营操作手册_v3.docx)（13 章实战版）

## 美学规范（与 PRD 完全一致）

⛔ **禁止重新发明配色 / 字体 / 标题样式 / 表格列宽**。全部走 PRD core/ 模块：

| 维度 | 来源 | 用法 |
|------|------|------|
| 配色 | `core.styles.C`（Anthropic Dark `#141413` + terra cotta `#D97757` + 表头 / 状态语义色） | `from core.styles import C` |
| 字体三件套 | `core.styles.FONT`（Lora / Poppins / Noto Serif SC / Noto Sans SC / JetBrains Mono） | 同上 |
| 标题样式 | `core.headings` 的 `h1` / `h2` / `h3`（terra cotta 下边框 / 左色块） | `from core.headings import h1, h2, h3` |
| 标点 / 字体 / theme 三件套 | `core.normalize` | `check_handbook.sh` 调用 |
| 截图圆角 / DPI | `core.images` 的 `round_phone_corners` + `fix_dpi` | `handbook_screenshots.py` 内置 |

`check_handbook.sh` 跑 PRD 同款字体三件套自检（缺 theme1.xml / 残留 Arial 即 fail）。

## 与 PRD 的关键区别

| 维度 | PRD | 运营手册 |
|------|-----|---------|
| 受众 | 研发 / 评审 / 项目 | 运营 / 客服 / BD |
| 行文 | 描述「做什么」 | 描述「**怎么操作**」（动词开头：点击 / 选择 / 填入） |
| snake_case 字段名 | ⛔ 禁，需白话化 | ✅ 允许（运营要照着字段名找配置项） |
| 像素值 / hex 色 | ⛔ 禁，归设计稿 | ✅ 允许（CMS 后台截图配置一致） |
| 决策编号 / 版本痕迹 | ⛔ 禁 | ⛔ 同样禁（运营不关心 PM 内部决策） |
| **不复用 humanize** | 三道闸守住 | 跳过 humanize；接受字段名 + 像素 |

## 章节模板

```
封面 + 元信息表（产品 / 版本 / 适用范围 / 维护人 / 更新日期）
├── 1. 模块概览                    什么系统 + 三方关系图 + C 端曝光位
├── 2. 角色与权限矩阵              三档 / 五档运营权限对照（谁能做什么）
├── 3. 核心操作流程                按用户旅程顺序：步骤 + 截图 + 异常态
│   ├── 3.x 操作 X
│   │   ├── 步骤 1：点击 ... → 看到 ... 截图
│   │   ├── 步骤 2：填入 ... → 校验规则 ...
│   │   └── ⚠️ 异常态：XX 时怎么办
├── 4. 字段定义                    枚举值 / 业务线 / 标签速查
├── 5. 故障排查（FAQ + 错误码）    高频问题 Q&A + 错误码索引
└── 6. 变更记录                    vs 上版差异
```

实际章节数随业务复杂度可扩到 10+（如活动中心 v3 有 13 章）。模板是骨架不是死规定。

详细章节定义：[`references/handbook-template.md`](references/handbook-template.md)
真实抽象示例：[`references/handbook-example.md`](references/handbook-example.md)

## 任务模式

### A. 新建手册（`gen_handbook_v{N}.py` 路径）

**Step 1 · Read**：`scene-list.md` + PRD docx + 已上线后台 / CMS（拿到截图来源）+ [`handbook-template.md`](references/handbook-template.md)。

**Step 2 · 收集**：

1. 产品名 + 版本号 + 维护人
2. 受众（运营 / 客服 / BD / 多方）
3. 章节优先级：核心操作流程 → 字段定义 → FAQ
4. 截图源：CMS 路径 / 是否有 staging 环境

**Step 3 · 分步生成 docx**：脚本路径 `projects/{项目}/scripts/gen_handbook_v{N}.py`。

| 步 | 内容 | 行上限 |
|----|------|--------|
| 3a 骨架 | `init_doc` + `cover_page` + 第 1-2 章（模块概览 + 角色权限矩阵）+ 各 H1 占位 | ≤ 80 行 |
| 3b 按操作流程填 step_table | 每个核心操作一次 Write，全 `step_table(doc, step_id, name, [(action, note, exception)])` | ≤ 300 行/次 |
| 3c 收尾 | 字段定义 + FAQ + 变更记录 | ≤ 200 行 |

每次 Write 后 `python3 gen_handbook_v{N}.py` 跑通 + 验证 docx 打得开。

**Step 4 · 截图**（见 C）+ **Step 5 · 自检**（`check_handbook.sh`）+ **Step 6 · 推 wiki**（见 D）。

### B. 升版 / patch（不重生 docx，原地改）

完全复用 PRD 升版纪律。`from core.patch import *` 拿到 `replace_para_text` / `insert_heading_before` / `insert_paragraph_before` / `insert_description_after` / `remove_table`。

字体三件套必跑（升旧 docx）：

```python
from core.normalize import normalize_punctuation, normalize_fonts, ensure_theme
from core.headings import normalize_headings
normalize_punctuation(doc)
normalize_headings(doc)
normalize_fonts(doc)
doc.save(path)
ensure_theme(path)
```

### C. CMS 截图回填（`handbook_screenshots.py`）

```bash
python3 .claude/skills/ops-handbook/scripts/handbook_screenshots.py --project {项目名} \
    --base-url https://mgt.example.com [--scenes step-1,step-2]
```

**截图规范**（与 PRD 一致）：
- viewport 1440×900 + deviceScaleFactor 2 + PNG
- `fix_dpi(144)` 防虚化（内置）
- CMS 后台先 dismissAllOverlays → 截目标元素 / 全屏
- 存放：`screenshots/handbook/`，升版 `screenshots/handbook_v{N}/`

⚠️ **登录 / cookie**：CMS 通常有登录态。脚本支持 `--cookie-file` 读取 staging 环境的 sessionid，或先 `playwright codegen` 录脚本。

### D. 推 Confluence

复用 PRD 的 `push_to_confluence_base.py`（mammoth + REST 是通用的，与内容类型无关）。**必须加 `--skip-self-check`**，因为 `gate_check_quality` 是 PRD 专属（扫圈数字 / 决策编号 / 1.3 流水账），运营手册不应被它拦：

```bash
python3 .claude/skills/prd/scripts/push_to_confluence_base.py \
    "projects/{项目}/deliverables/handbook-{项目}-v{N}.docx" \
    --page-id 155xxxxxx \
    --skip-self-check
```

`check_handbook.sh` 替代 PRD gate 作运营手册质量门。

## 关联 Hook 矩阵

ops-handbook 不引入新 hook。复用现有 6 个：

| hook | 拦什么 | 触发 |
|------|--------|------|
| `pre-wiki-push-gate.sh` | 推 wiki 前未过 `check_handbook.sh` | Bash 含 `push_to_confluence_base.py` 且 docx 名以 `handbook-` 开头 |
| `post-docx-screenshot-check.sh` | docx 改完截图过期 | Bash 跑 `update_*.py` |
| `pre-deliverable-source-gate.sh` | 直接 Edit/Write 已脚本化的 docx | Edit/Write 命中 `deliverables/handbook-*.docx` |
| `post-cjk-punct-check.sh` | 中文旁半角 `, : ( )` | Write/Edit |

## API 速查表

项目脚本开头：

```python
import sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / '.claude/skills/prd/scripts'))      # 复用 PRD core/
sys.path.insert(0, str(BASE / '.claude/skills/ops-handbook/scripts'))
from gen_handbook_base import *
```

**`gen_handbook_base`** 提供（薄封装层）：

- `init_doc(landscape=False)` / `cover_page(doc, title, version, owner, audience, scope)` — 运营手册默认竖版
- `h1` / `h2` / `h3` — 直接 re-export 自 `core.headings`
- `add_p` / `bullet` / `make_table` / `cell_text` — 同上
- `step_table(doc, step_id, name, rows)` — 三列步骤表（动作 / 校验 / 异常态），运营手册专属
- `field_table(doc, fields)` — 字段定义表（字段名 / 类型 / 枚举值 / 含义），允许 snake_case
- `faq_block(doc, question, answer)` — FAQ 单条（Q 粗体 + A 缩进段）
- `permission_matrix(doc, roles, capabilities)` — 角色权限矩阵
- `save_handbook(doc, path)` — 保存 + normalize_punctuation + normalize_fonts + ensure_theme（不调 humanize）
- 颜色 / 字体直接 import：`from core.styles import C, FONT`

## 自检清单

- [ ] 编号和 PRD 关联场景一致
- [ ] 生成脚本已存 `projects/{项目}/scripts/gen_handbook_v{N}.py`
- [ ] 角色权限矩阵覆盖所有出现的角色（不留「TBD」）
- [ ] 每个操作步骤至少 1 张 CMS 截图（`fix_dpi(144)` 已修正）
- [ ] FAQ 覆盖项目实际踩坑（不是套话填充）
- [ ] 字段定义表枚举值穷举（业务线 / 标签 / 状态等）
- [ ] 通过 `bash .claude/skills/ops-handbook/scripts/check_handbook.sh <docx>`：
  - 无圈数字 ①②③ 残留
  - 字体三件套（theme1.xml + 无 Arial run + Noto Sans SC 已用）
  - 无中文旁半角标点
  - 截图 DPI ≥ 130
