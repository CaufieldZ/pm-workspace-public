---
name: prd
description: >
  当用户提到「PRD」「需求文档」时触发。基于 IMAP / 原型输出 PRD 亦触发。
  PRD 形态为 md（含本地截图，推 Confluence 时脚本自动上传图片）。
type: pipeline
output_format: .md
output_prefix: prd-
pipeline_position: 5
depends_on: [scene-list]
optional_inputs: [interaction-map, prototype]
consumed_by: [cross-check]
owns: [字段口径, 池策略全局规则, 埋点事件属性, 状态机, 跳转规则文字]
forbids: [视觉规范, 技术实现, 状态机交互细节]
scripts:
  gen_prd_skeleton.py: "新建 PRD 空骨架 — python3 gen_prd_skeleton.py -p {产品线/项目} -v {版本} [--profile baseline|delta] [--tier patch|feature|bundle]（delta 落 deliverables/{季度}/{版本}/；baseline 落产品线根无版本号；缺省 profile = 旧 12 章 PRD）"
  read_prd_section.py: "按章节读 / TOC / grep — python3 read_prd_section.py <prd.md> --toc | -s 5.1 | --grep 关键词"
  check_prd_md.sh: "硬错自检（占位符 / Confluence 渲染 / 埋点表 / 文档结构 / 截图 / CJK 标点）— bash check_prd_md.sh <prd.md> [--skeleton]"
  cold_read.py: "冷读打包（开发者视角单探针，context 附 scene-list + baseline）— python3 cold_read.py --prepare <prd.md>；脚本只打包，冷读由 Step 4 派干净子代理跑"
  screenshot_for_prd.py: "PRD 截图 framework — python3 screenshot_for_prd.py --imap <html> -o <assets_dir> / --proto <html> -o <assets_dir>；--assert-fresh 供 check_prd_md.sh 调用。项目根有 scripts/screenshot_proto.py 时必须走项目脚本"
  export_tracking_xlsx.py: "埋点表导出合并单元格 xlsx（单独发研发时用；推 wiki 用 md_to_confluence.py --merge-tracking）— python3 export_tracking_xlsx.py <prd.md> [-o out.xlsx]"
  humanize/md_scan.py: "硬错扫描 — scan_prd_structural_md(md_text)"
  core/md_renderer.py: "md 输出原语 — MdWriter / image_spec_table / scene_block_card"
  sections_md.py: "旧 12 章骨架 + 场景卡生成（被 gen_prd_skeleton.py 调用）"
  sections_md_baseline.py: "baseline / delta 骨架（被 gen_prd_skeleton.py 调用）：build_baseline_skeleton / build_delta_skeleton"
  scripts/check_baseline_fresh.py: "baseline 反向合并新鲜度（根 scripts/）— python3 scripts/check_baseline_fresh.py {产品线}"
  # 推 Confluence 走根目录 scripts/md_to_confluence.py
---

# PRD Skill

## 触发与定位

> 收到新需求 → 先按 CLAUDE.md「收到需求路由」过 PM-GATE 4 风险扫描 + 复杂度判链路，再进 Step 0。

**做什么**：给开发、开发用的 AI、测试看的需求文档。读完知道这轮做什么业务、做到哪、怎么算做对。

**形态分流**：

- 产品线已有 `prd-{产品线}-baseline.md` → 写 **delta**（主路径，本文档默认讲它）
- 产品线首次建档 → 写 baseline（`--profile baseline`），之后都写 delta
- 方案型（跨 ≥ 2 系统 / 资金 / 多团队 / 纯后端）→ 自定章节，仍是 md，见注意事项
- biweekly 散件（≤ 50 行）→ 用 [`projects/biweekly/README.md`](../../../projects/biweekly/README.md) §4 的紧凑模板
- 旧 12 章 PRD（不带 `--profile`）→ 只在 PM 明确要求时用，写法见 `references/prd-12ch.md`

**不做**：视觉规范（设计稿承载）、技术方案（architecture-diagrams）、实现细节（接口 / 数据库 / 代码）。

## 改脚本前 30 秒

> `skill-load-gate` 守「Read 过本文件」不看行数：改 `scripts/*.py` 读 `limit=60`；改 PRD 产物前读全文 + `references/prd-writing-guide.md` + `.claude/runbooks/info-ownership.md`。

**Public API（不可改签名）**：

- `python3 gen_prd_skeleton.py -p {产品线/项目} -v {N} [--profile baseline|delta] [--tier patch|feature|bundle]`
- `bash check_prd_md.sh <prd.md> [--skeleton]` — 维度清单唯一真源 `humanize/patterns.py::prd_fail_keys`
- `python3 cold_read.py --prepare <prd.md>`
- `python3 read_prd_section.py <prd.md> --toc | -s 5.1 | --grep 关键词`
- `python3 screenshot_for_prd.py --imap <html> | --proto <html> -o <assets_dir>`
- `from humanize.md_scan import scan_prd_structural_md`
- `from core.md_renderer import MdWriter, image_spec_table, scene_block_card`
- `from sections_md_baseline import build_baseline_skeleton, build_delta_skeleton`

**会拦你的 hook**：

- `skill-load-gate` — 改 `prd-*.md` 前必读本文件 + 写作指南 + info-ownership.md
- `prd-content-gate` — PRD 写入后查新增行的硬错（与 `check_prd_md.sh` 同源，`SKIP_PRD_CONTENT_GATE=1` 跳过）
- `prd-check-gate` — 跑 `gen_prd*.py` 后自动 `check_prd_md.sh --skeleton`
- `prd-cross-check-gate` — PRD 写入后跑跨产物 7 维结构校验
- `cjk-punct` — CJK 旁半角标点自动修
- `baseline-fresh-gate` — 改 baseline / delta 后查反向合并新鲜度

**改完跑啥**：

```bash
.venv/bin/python -m pytest scripts/tests/ -q && bash .claude/hooks/test/test-hooks.sh
```

## 硬规则（FAIL 即拦）

写内容时守六条：

1. **只写输入里有的。** 需求、会议纪要、原型、PM 口述里没给的机制、状态、数值、异常处理、决策理由，不补写，需要的写进 §1「待确认」等 PM 定。
2. **版本号、范围、实施归属由 PM 定。** 加了需求也不改版本号，不确定就问。
3. **每个事实只写一处。** 别处要用时写它的名字（「按『来源页回跳』规则」），不重写内容。阈值、次数、时长全文只出现一次。
4. **只写本轮改动。** 线上现状引 baseline，不重述；需要对照时一句「原来 X」。
5. **写业务，不写实现。** 不写接口、数据库、代码、字段英文名、颜色尺寸。埋点章的事件 / 属性英文名例外。
6. **承接上一版未上线需求**：先核 baseline 里的线上现状，把差异列为第一条待确认；新 delta 写全量可执行规格，不写「见 X 版」的引用。

`check_prd_md.sh` 机检 FAIL：占位符残留、mermaid / PlantUML 代码块、引用块 `>`、水平线 `---`、空 alt 图片、埋点表头不是固定 10 列、埋点平台填了服务端或后台、章节比上一版少、`<td>` 内空行、标题前缺空行、引用的截图缺失或过期。

## 核心输出规范

delta 的 9 章骨架由 `gen_prd_skeleton.py --profile delta` 生成，各章写法见 `references/prd-writing-guide.md` 第二节。要点：

- **§1 概述**：问题 / 本轮做什么 / 成功标准各一两句，加范围表、不做、待确认。半页以内。
- **§2 本轮需求按模块或页面分块。** 开发当一个组件做的写成一块；几个场景是同一组件的不同情况时合成一块，不同处放差异表。块里只有图、规格、差异表、验收四样，按需要出现。
- **规格一条一件事**，写成「条件 → 结果」或「对象：取值」；失败、为空、超时写在相关那条里。
- **验收三到五条**，只写临界值、情况之间的差别、不该发生的事。
- **§3 / §4 / §5** 只写本轮新增或变更的对象、状态、跨模块规则，没有就删章。整体结构（权限矩阵、状态机）写改后全量。
- **§6 决策**只记输入里给过理由的取舍，一行一条。
- **§7 埋点**用骨架的 10 列表，表头一字不改；平台只填 APP 或 Web。每列填法见写作指南第八节。

档位（`--tier`）只决定 §2 的形态：`patch` 一张需求表讲完；`feature`（默认）按模块分块；`bundle` 先一张索引表再分块。

命名：delta `deliverables/{季度}/{版本}/prd-{产品线}-{版本}.md`，截图在同目录 `assets/`；baseline `projects/{产品线}/prd-{产品线}-baseline.md`。每份 PRD 都是一个 md 文件，不拆分。

## 执行步骤

### Step 0：读输入

1. 需求原文、会议纪要、原型 / IMAP、scene-list
2. baseline 相关章：`read_prd_section.py <baseline.md> --toc` → 按需 `-s`
3. 同产品线最近一个 delta（看篇幅和颗粒度）

写 §1 成功标准前读 `.claude/runbooks/pm-methodology.md` §三；写 §6 前读 §二。

### Step 1：生成骨架

```bash
python3 .claude/skills/prd/scripts/gen_prd_skeleton.py -p {产品线} -v {版本} --profile delta [--tier patch|bundle]
```

脚本打印 baseline 路径和本季已有版本，版本号由 PM 定，不自动 +1。

### Step 2：写

顺序：§1（定下有几个模块）→ §2 → §3 / §4 / §5 → §7 → §6。骨架里的示范块按实际模块数复制，用不上的章和段落删掉。新场景先在 scene-list 落编号再进 PRD。

写完拿输入材料逐条对一遍：每条规则都在 PRD 里找得到（多种情况合成一块时，每种情况都在差异表里）；每个数字只出现一次；没有输入里没有、自己补上的规则或理由。

### Step 3：自检和截图

```bash
bash .claude/skills/prd/scripts/check_prd_md.sh <prd.md> --skeleton   # 写作中
bash .claude/skills/prd/scripts/check_prd_md.sh <prd.md>              # 交付前
```

截图：

- 项目有 `projects/{项目}/scripts/screenshot_for_prd*.py` 时直接跑它
- 骨架原型：`screenshot_for_prd.py --proto <proto.html> -o <delta>/assets/`；IMAP：`--imap <imap.html> -o ...`
- 文件名 `scene-{编号}.png` 或 `proto-{view}-{page}.png`，md 里用 `./assets/xxx.png` 引用；图片 alt 写这张图是什么
- 拍不出来的示意（系统通知、跨系统时序）可用 `scripts/image_gen.py --edit <最接近的原型截图>` 生成，文件名 `mock-*.png`，alt 写「示意，非原型实拍」，生成后逐字核对图里的文字。新页面还没原型时不生成。`--edit` 会把参考图发到外部服务，含未发布界面时先确认
- 源 HTML 改了要重拍，`check_prd_md.sh` 会报过期

### Step 4：冷读（交付研发前建议跑）

```bash
python3 .claude/skills/prd/scripts/cold_read.py --prepare <prd.md>
```

把输出的 PROBE 原样交给一个干净的子代理（Agent 工具，general-purpose），它以开发者视角回答四类问题：开工前要问的、前后矛盾的、重复的、可以不看的。结果填进同目录 `cold-read-{日期}.md`，逐条标「补 / 删 / 误报」后改 PRD。冷读必须用干净上下文，同 session 读过材料的模型会自动脑补。

### Step 5：推 Confluence

- `python3 scripts/md_to_confluence.py <prd.md> --parent-id <id>`（更新已有页用 `--update-id <id>`）
- 埋点表加 `--merge-tracking`，wiki 上事件级列自动合并单元格
- 脚本自动上传 `./assets/` 图片，剥离决策、排期、反向合并三章和文档头元信息
- 同名页已存在时脚本会提示：改标题新建 / `--update-id` 覆盖 / 先归档旧页，推之前问 PM 选哪个
- Confluence 不显示 mermaid、引用块 `>`、水平线 `---`、HTML 注释，这些不写；流程图走 flowchart skill 出图后用 `![](./assets/flow-xxx.png)` 引用

### Step 6：上线后（baseline / delta 循环）

顺序不可乱：baseline 变更记录补一行 → 按 delta §9 反向合并进 baseline → 状态推进「已合并」→ 归档到 `archive/{季度}/`。`check_baseline_fresh.py {产品线}` 查漏合并。模型全貌见 `.claude/runbooks/artifact-conventions.md` §六。

baseline 是产品线的线上现状全集，按模块组织，只写现在是什么样：

- 只首建一次骨架（`--profile baseline`），之后手动 Edit，不重跑骨架
- 反向合并时删掉 delta 里的「本轮改动：X → Y」这类迭代说明，baseline 只留结果

## API 速查

```python
from core.md_renderer import MdWriter, image_spec_table, bold
w = MdWriter()
w.h1("2. 本轮需求")
w.h2("2.1 盈利顶飘（T-6 ~ T-9）")
w.raw(image_spec_table([("./assets/scene-T-6.png", "顶飘")], [("", ["5 秒无操作自动消失"])]))
w.table(headers=["", "合约", "现货"], rows=[["频控", "每日 3 次", "每日 10 次"]])
md = w.render()

from humanize.md_scan import scan_prd_structural_md
from humanize.patterns import prd_fail_keys
hits = scan_prd_structural_md(md_text)
fail = [k for k, _ in prd_fail_keys() if hits.get(k)]
```

## 自检清单

- [ ] `check_prd_md.sh <prd.md>` exit 0
- [ ] §1 范围表里的每个模块，§2 都有对应的块；没有多出来的块
- [ ] 每个阈值、次数、时长全文只出现一次
- [ ] 待确认里列了输入没给、自己没法定的点
- [ ] 输入材料里的每条规则都能在 PRD 里找到
- [ ] §6 只有输入给过理由的取舍，没有自己补的理由
- [ ] 交付研发前跑过 Step 4 冷读，清单逐条处理过

## References 索引

**必读**：

- `references/prd-writing-guide.md` — 各章写法和示例（概述 / 模块块 / 状态表 / 补丁包 / 决策 / 埋点）、写完对照检查

**按需读**：

- `references/prd-optional-sections.md` — 需要竞品参考或多方案对比时
- `references/prd-12ch.md` — 写或维护旧 12 章 PRD 时
- `references/metrics-framework.md` — 定成功标准和看板指标时
- `.claude/runbooks/artifact-conventions.md` §六 — baseline / delta 文档集模型全貌
- `.claude/runbooks/pm-methodology.md` — 成功标准（§三）、决策取舍（§二）

## 注意事项

**方案型项目**（跨系统对接 / 资金路径 / 法务合规 / 纯后端）不走 delta 骨架。PM 自定章节，建议包含：方案概览、系统拓扑、各系统职责、接口约定、资金对账、风险与回滚、灰度计划。文档仍是 md，仍走 `md_to_confluence.py` 推 wiki。

