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
  gen_prd_skeleton.py: "新建 PRD 空骨架 — python3 gen_prd_skeleton.py -p {产品线/项目} -v 1 [--mode single|split] [--profile baseline|delta] [--tier patch|feature|bundle] [--clean-stale]（baseline 落产品线根无版本号 / delta 落 deliverables 有版本号；缺省 = 普通 PRD。--tier 仅 delta 生效，定迭代档位 + §2 行文，见下文 delta 档位。split 生成前自动扫描 scenes/ 下 stale 并打印清单，--clean-stale 一键删除）"
  prd_compose.py: "split 模式拼接成完整 md（push 前自动调用）— python3 prd_compose.py <prd.md> -o composed.md"
  read_prd_section.py: "按章节读 / TOC / grep — python3 read_prd_section.py <prd.md> --toc | -s 5.1 | --grep 关键词。--toc 给每章标 [静态]/[动态]（动态 = 变更记录/决策/排期等演化章）"
  split_prd.py: "single → split 一次性迁移 — python3 split_prd.py <prd.md>"
  screenshot_for_prd.py: "PRD 截图 framework（IMAP 模式 shoot_from_imap + 原型模式 shoot_from_proto（骨架原型按 view × page discover）+ 截图同步落 .freshness.json manifest（v2：hash 而非 mtime，IMAP 按 .flow / 原型按 .p-page DOM 子树 hash 判定，无关 CSS/注释/reformat 不再误报；缺 manifest 自动降级 mtime）+ 通用 helpers）— python3 screenshot_for_prd.py --imap <html> -o <assets_dir> / --proto <html> -o <assets_dir>；项目原型脚本 import shoot_from_imap / shoot_from_proto / dismiss_all_overlays / assert_screenshots_fresh。--assert-fresh 模式供 check_prd_md.sh 调用"
  check_prd_md.sh: "md 自检（FAIL/WARN 分级，--skeleton 模式跳占位符 + 截图 + freshness）— bash check_prd_md.sh <prd.md> [--skeleton]。§X.Y 锚点 + 裸场景编号死链查只对 split（有 `-scenes/` 子目录）开，单文件（single delta / baseline）天然豁免；profile（按文件名 prd-*-baseline.md 判）只控 baseline 其他行为"
  cold_read.py: "交付前冷读反测打包（叶子完整性 7 类盲区）— python3 cold_read.py --prepare <prd.md> [--targets 3.1,4.1,5.1]。compose 全文 + 附 scene-list 落 context 文件 + 生成 N 个干净子代理探针 prompt + 落 cold-read-{date}.md 盲点清单模板。脚本只打包，实际冷读由「交付前冷读」Step 派 Agent 子代理跑"
  humanize/md_scan.py: "md 版扫描 — scan_human_voice_md(md_text) / scan_prd_structural_md(md_text)"
  core/md_renderer.py: "md 输出原语 — MdWriter / scene_5section_card / 等（被 sections_md.py 调用）"
  sections_md.py: "普通 12 章骨架 + 场景卡生成（被 gen_prd_skeleton.py 调用）：build_full_skeleton（普通 12 章）/ build_scene_file（split 子场景）+ 章节 render 原语与 SceneInfo 模型"
  sections_md_baseline.py: "baseline / delta 迭代文档集骨架（被 gen_prd_skeleton.py 调用）：build_baseline_skeleton（baseline 模块树）/ build_delta_skeleton（delta 单轮迭代）。依赖 sections_md 的 SceneInfo / build_chapter_4"
  scripts/check_baseline_fresh.py: "baseline 反向合并新鲜度校验（根 scripts/，非本 skill 目录）— python3 scripts/check_baseline_fresh.py {产品线}。已上线 delta 未合并报红 + 模块章超期报黄"
  export_tracking_xlsx.py: "埋点章节导出合并单元格 xlsx（备用：需单独发给研发时用）— python3 export_tracking_xlsx.py <prd.md> [-o out.xlsx]。按 10 列表头签名定位埋点表，通吃 baseline §9.1 / delta §7。**推 Confluence 时不用此脚本**，直接在 md_to_confluence.py 加 --merge-tracking 即可在 wiki 上实现同等合并单元格效果"
  # 推 Confluence 走根目录 scripts/md_to_confluence.py（自动检测 split 模式调 prd_compose.py + 上传本地截图）
---

# PRD Skill（产品需求文档，md 版）

## 触发与定位

> 收到新需求 → 先按 CLAUDE.md「收到需求路由」过 PM-GATE 4 风险扫描 + 复杂度判链路，再进 Step 0。

**做什么**：scene-list / IMAP / prototype 之后的最终行为规格 md 文档（md + 本地截图，推 Confluence 时图片自动上传）。自包含、PM 与研发 / 设计 / QA AI 都能直接消化。承载业务对象词典 / 业务动作区块表 / 通用文案清单 / 信息层次矩阵。

**何时触发**：用户说「PRD / 需求文档」；IMAP / prototype 完成后输出 PRD 亦触发。

**写给谁（立场）**：PRD **首先要 PM 自己读得懂**。**全文讲人话**——契约层（业务对象词典 / 状态机章：12 章 PRD = §3.2/§3.3，delta = §3/§4）也用中文业务名（写「主播 TRTC 标志」不写 `trtc_enabled`）。spec coding 能力靠**业务语义精度**达成（类型 / 约束 / 枚举 / 状态全集写全）。PM 手写的英文 key 多为杜撰、研发会当真采用；中文业务描述把命名权交还研发 AI 反推——**宁可欠确定，不可错确定**。**唯一英文标识符例外 = 埋点事件 / 属性名**（神策外部契约，已注册 key 不可翻译，详见 `references/prd-chapter-rules.md` §三点八）。**业务方案专名**（TRTC / OBS / RTMP 等行业通用词）保留。

**链路分流**（复杂度判定走 CLAUDE.md，本表只列 PRD 专属形态）：
- single 模式 → 场景 ≤ 10，单 md
- split 模式 → 场景 > 10，主骨架 + scenes/，`gen_prd_skeleton.py` 自动判
- 散件链路（biweekly 内 / 单功能点 / 小修，≤ 50 行 md）→ 不走 12 章骨架，用 6 章紧凑模板（见 [`projects/biweekly/README.md`](../../../projects/biweekly/README.md) §4），自检仍跑 `check_prd_md.sh`
- 方案型项目（跨 ≥ 2 系统 / 资金流转 / 多团队 / 纯后端）→ 不走 pipeline，PM 自定章节，文档仍 md（详见 § 注意事项）
- **老项目持续迭代（baseline 文档集模型）**：产品线已立 `prd-{产品线}-baseline.md` → 本轮需求写 delta（`gen_prd_skeleton.py --profile delta`），上线后先补 baseline changelog 行、再反向合并进 baseline 模块章（手动 Edit 不重跑骨架）。baseline / delta 都要达 spec coding 规范。详见 Step 5 + [artifact-conventions.md §六](../../runbooks/artifact-conventions.md)
- 老项目 docx 维护 → 从零写新 md v{N+1} 推覆盖原 wiki 页，老 docx 进 archive/legacy-docx/

**不做**：UI 视觉规范（设计稿 + design system 承载）/ 技术方案（归 architecture-diagrams）/ 实现细节（不写 SQL / 接口 schema / 框架状态）。

## 改脚本前 30 秒

> hook 守的是「Read 过本文件」**不看读了多少行**。改 scripts/*.py 用 `Read 此文件 limit=90`（§1+§2 即够，本文件 §2 比 conventions 模板长）。改产出物（prd-*.md）建议全文。

**Public API（不可改签名）**：
- `python3 gen_prd_skeleton.py -p {产品线/项目} -v {N} [--mode single|split] [--profile baseline|delta] [--clean-stale]` — 新建空骨架（baseline 落产品线根无版本号 / delta 落 deliverables / 缺省普通 12 章；split 自动扫 stale 打印清单，--clean-stale 删）
- `python3 prd_compose.py <prd.md> -o composed.md` — split → 单页（push 前自动调用）
- `python3 read_prd_section.py <prd.md> --toc | -s 5.1 | --grep 关键词` — 按章节读 / TOC / grep
- `python3 split_prd.py <prd.md>` — single → split 一次性迁移
- `python3 screenshot_for_prd.py --imap <html> -o <assets_dir>` — IMAP 模式截图；`--proto <html>` 骨架原型通用截图（view × page discover）。**路由规则：项目根有 `scripts/screenshot_proto.py` → 必须走项目脚本，禁用 `--proto`**（项目脚本读 registry.shot_setup，含多场景页面会截到正确态；通用模式不读 registry，会停在默认态；框架已加 `screenshot-route-gate` 拦截）
- `bash check_prd_md.sh <prd.md> [--skeleton]` — md 自检（FAIL/WARN 分级；死链查按是否有 `-scenes/` 判 split，单文件 delta / baseline 豁免）
- `python3 cold_read.py --prepare <prd.md> [--targets 3.1,4.1,5.1]` — 交付前冷读打包（context 文件 + 探针 prompt + 报告模板），实际冷读派子代理跑
- `python3 export_tracking_xlsx.py <prd.md> [-o out.xlsx]` — 埋点章节导出合并单元格 xlsx（事件级列同事件 merge）
- `from humanize.md_scan import scan_human_voice_md, scan_prd_structural_md` — md 扫描
- `from core.md_renderer import MdWriter, scene_5section_card` — md 输出原语
- `from sections_md import build_full_skeleton, build_scene_file, SceneInfo` — 普通 12 章骨架编排；`from sections_md_baseline import build_baseline_skeleton, build_delta_skeleton` — baseline / delta 迭代骨架

**改场景块前读 quickref**：`references/prd-scene-template-quickref.md`（左图右文骨架（组头式）+ 三段式定义 + 4 条约束），比读 300 行全量模板省 token。

**会拦你的 hook**（真实 gate 名，dispatcher 在 `lib/post-checks.sh` / `lib/checkers.sh` / `lib/pre-writeedit-guards.sh`）：
- `script-syntax-gate` / `cjk-punct` — 写 .py/.sh + md 自动跑
- `prd-check-gate` — `gen_prd*.py` 后自动跑 `check_prd_md.sh --skeleton`
- `prd-cross-check-gate` — PRD 写入后自动跑 7 维结构校验
- `plain-language-gate` — 扫正文裸编号 / 锚点 / 翻译腔
- `pm-visual-gate` — 扫视觉越界（颜色 / 尺寸 / 描边 / 圆角 / 设备壳等视觉规格）
- `baseline-fresh-gate` — 编辑 baseline / delta 后查反向合并新鲜度
- `cold-read-gate` — delta PRD 推 Confluence 前查同目录冷读产物（缺则拦，`SKIP_COLD_READ_GATE=1` 跳过）
- `skill-load-gate` — 改 `prd-*.md` / `prd-*-scenes/*.md` 必先 Read 本 SKILL.md + info-ownership.md

**改完跑啥**：
```bash
bash .claude/skills/prd/scripts/check_prd_md.sh projects/{项目}/deliverables/prd-*.md
```

**深入读什么**：完整章节归属 `Read references/prd-chapter-rules.md`；场景模板 `Read references/prd-scene-templates.md`（写 5/6/7 章前）；自检规则 `grep -A 15 "^## 自检清单" SKILL.md`。

## 硬规则（FAIL 即拦）

> 写 PRD 前脑里装 **4 条正文红线**（踩一条 `check_prd_md.sh` 就 FAIL）：
> 1. 禁裸场景编号 `A-1 / B-2`（编号只许出现在章节标题 / 2.1 表 / 截图名 / 埋点名 / md 链接），引用用「编号 + 白话名」或纯白话。**单文件豁免**（baseline + single delta 都是单文件，模块树按编号索引合法）——死链只在 split（有 `-scenes/`）查
> 2. 禁章节锚点 `§5.1 / §X.Y`（§ 锚点在 Confluence 不解析、split 拼页后编号漂移，两头都是死链；跨章引用的稳定锚是**白话名**，章节号只作辅助定位：写「见 4.1 一帖一卡」或纯白话「见『发帖』章节」）。**单文件豁免**（baseline + single delta 内 §具名锚点是合法内跳）——死链只在 split 查
> 3. **全文讲人话，契约层也用中文**：契约层（业务对象 / 状态机章：12 章 PRD = §3.2/§3.3，delta = §3/§4）写中文字段名 + 类型 + 约束 + 枚举（不写 `trtc_enabled`，写「主播 TRTC 标志｜布尔｜默认关」）。**唯一例外 = 埋点章**：PM 起事件英文名 + 属性英文名，既有事件抄神策真名（走 `probe_event_properties.py`），新事件按 `references/prd-chapter-rules.md` §三点八 命名约定
> 4. 禁「（新增）」「（变更）」行内版本标签（会被 `date_tag_hits` 抓）。版本变更集中列（12 章 PRD 在 1.4 章，delta 在 §2 本轮需求）

### 10 条核心硬规则

1. **全文讲人话，不写技术黑话** — 全文（含契约层，章号见红线 3）禁 snake_case 研发字段（`trtc_enabled` / `card_id`）+ 禁旧模板五件套字段名（`**触发** / **读** / **写** / **事件** / **API**`）做 bullet 标签——禁的是行首标签用法（自检清单「模板字段名锁定」grep 的模式），不是正文自然语言里的「触发」一词。PM 用业务语义描述（「新增一条帖子记录」），研发 AI 自己反推 SQL / 事件名 / key。**唯一例外 = 埋点章事件 / 属性英文名**（神策外部契约）。业务方案专名（TRTC / OBS / RTMP）保留。完整禁用清单 `references/prd-scene-templates.md`
2. **正文禁裸场景编号 + 禁 §X.Y 章节锚点**（见红线 1/2，单文件 = baseline + single delta 同样豁免，死链只在 split 查）— `A-1 / B-2 / M-1 / F-1` 和 `§5.1 / §4.1` 只能在章节标题、第 2.1 场景地图表、截图文件名、埋点事件名、md 链接里出现。正文跨章引用用「章节号 + 白话名」（`见 4.1 一帖一卡`）或「编号 + 白话名」（`F-1 推荐加权`）或纯白话名。`plain-language-gate` hook + `check_prd_md.sh` 兜底
3. **5/6/7 章子场景必须扁平** — 禁 `5.1.1 / 5.1.2` 嵌套。一件事需要拆就拆并列 `5.1 / 5.2`。`split_prd.py` 检测嵌套直接报错
4. **同一字段只写一次** — 跨场景共用规则进第 4 章，场景独有进 5/6/7.x 系统检查；通用文案进第 8 章，场景文案进 5/6/7.x；状态机进 3.3，场景状态分支进 5/6/7.x；**异常场景共性进第 4 章「全局异常降级总则」**（接口超时 / 缓存兜底 / 全站规则继承 / 承载方边界），场景文件只留 1–3 条独有项 + 一行豁免注释。异常表 4 不写规则见 `references/prd-scene-templates.md §4.3.1`。完整归属矩阵 `references/prd-chapter-rules.md §二`
5. **CJK 标点 + 圈数字** — CJK 旁禁半角 `,:;()`，禁圈数字 `①②③`。`check_cjk_punct.py --strict` + `humanize/md_scan.py` 兜底
6. **禁 mermaid / PlantUML / HTML 注释** — Confluence markdown 宏不渲染，写了在 wiki 上看到源码。流程图改「起点 / 终点 / 触发 / 延迟」表 + 一句路径文字；状态机改「起始状态 / 触发事件 / 终止状态 / 谁触发」表。必须图走 `flowchart` skill 出 SVG / PNG 后 `![](./assets/xxx.svg)` 引用。详见 `references/prd-chapter-rules.md §三点五`
7. **禁具体 URL / 路由** — PM 定业务不定技术实现。出现 `/activity-center` `/user/profile` = 越权。业务语义用「独立页 / 独立路由 / 独立落地页」描述，具体路径让前端决定。唯一例外：后台配置表单里教运营填路径的字段说明文字（「相对路径」是字段本身的业务含义，不算定路由）。`check_prd_md.sh` 兜底
8. **PM 角色越界禁词** — 八类：JS 事件（`hover` / `onclick`）、DOM API（`DOM` / `display:none`）、国际化（`i18n key`）、缓存（`cache` / `localStorage`）、框架状态（`dirty` / `pristine`）、UI 英文（`modal` / `chip` / `tooltip` 用「弹窗 / 胶囊 / 提示」）、像素断点（`<768px` / `@media`）、技术变量名（`topicData` / `tag.hot` 驼峰）。**埋点章节是 PM 必写区**：事件英文名 / 属性英文名 / 数据类型 / 触发机制 PM 必填，10 列模板见 `references/prd-chapter-rules.md §三点八`
   - **核埋点真伪先看该 PRD 是否自标「拟名 / 待注册」**：`probe_event_properties.py` 查不到神策真实事件，若该 PRD 埋点章本就标了拟名 / 待注册，说明是本轮新增埋点、神策还没这个事件是预期状态，不等于 PM 杜撰；只有正文声称"已有事件"却查不到才是真问题。
9. **禁 `---` 水平线分隔符** — Confluence 不渲染 md 水平线且显示丑（横线断裂 / 撑满整宽），章节靠 `# / ##` 标题自然分隔。`MdWriter.hr()` 为 no-op（禁用入口），`check_prd_md.sh` 扫单独成行 `---` → FAIL；表格分隔符 `|---|` 不受影响（含 `|`）
10. **禁 `>` 引用块** — Confluence blockquote 渲染丑（左竖线 + 灰底 + 缩进，破坏文档流）。业务故事（章节 / 场景定调）改 `**业务故事**：正文`（「业务故事」加粗、正文不加粗），章首不要定调金句。`MdWriter.pullquote()` 为 no-op、`chapter_story()` 已改粗体引导，`check_prd_md.sh` 扫 `^>` → FAIL（baseline 历史 living 文档豁免，等迭代消化）

### 行文 WARN 三件套（写作时就按这个写，别等 check 抓）

写 bullet / 散文时守这三条，`check_prd_md.sh` 报 WARN 只是兜底——写时就该写对：

1. **单行 ≥ 2 分号** → 拆 bullet 或 `1. 2. 3.` 编号（表格行豁免）
2. **句段 ≥ 100 字** → 拆句或转列表（表格行豁免）
3. **bullet 行内句号串并列项**（`打点口径 = X。B 点 = Y。展示位置 = Z`）→ 一项一 bullet，句号只落行尾（表格行 / 决策记录章 / 冒号引子 bullet 豁免）

**别换标点绕检测**：把多件独立事从分号改成逗号 / 顿号焊同一行只是骗过 checker（它数不到逗号），认知负荷更高。判断该不该拆看语义（多件独立事 vs 一件事的子项），不看凑没凑过阈值。权威定义 + Red Flags 见 `.claude/runbooks/human-voice-rules.md ⑥`。

**§2.x 场景正文的 `**现状**` / `**修改点**`（delta，旧称「本轮」）bullet 是 FAIL 级契约（不是 WARN）**：这几个标签下的 bullet 一条只扛一个原子事实——一件事的多阶段（原状态 → 变更 → 现状）用 `→` 串成一行链，多件独立事各自一条 bullet，句号只落行尾不做行内焊接。`check_prd_md.sh` 的 `scene_prose_runon` 维阻断 commit（§6 决策记录章天然够不着，论证句照旧可长）。连贯叙事确实该整段保留时走逃生阀 `SKIP_SCENE_PROSE_GATE=1`——**用前先向用户说明为什么这段不该拆**（知会制）。

正反例 + 细则（含 delta 叙事对保留指引）见 `references/prd-chapter-rules.md §三`，自检清单 9/10/11。

### 语义去重三条（delta 最大字数黑洞，句法三件套管不到）

三件套只管一行内怎么写；下面前两条管**同一件事被写几遍**（delta 臃肿的真源是跨小节复读，不是长句），第三条管否定式表述：

1. **一条规则只完整讲一次（单一真相位）**：每条业务规则的完整表述只落**一个**位置（delta 走三列时 = 规格表格子；见 `prd-scene-templates.md §4.0`）。跨模块 / 验收 / §6 决策需带到时**只写差异或指针**（「见 5.1 规格」/「同上，仅 H5 不同：…」），不重抄原句。
2. **验收写"可验证判定点"，不复述规格**：每条验收 = QA 能勾的断言（做了 X → 应观察到 Y）。能从规格表直读的（有 X 字段、显示 Y）不写；只写反向 / 边缘 / 跨端断言。若某条只是规格加 `[ ]` 前缀、1:1 对应，**删掉**。
3. **禁反向声明（展示 / 字段规则域）**：规则不写「不展示 X」「不做 Y」这类反向否定，把「是什么」列清楚（「不展示已删除评论」→「仅展示未删除」）。范围边界不算反向声明——scope 由 §2.0 索引表 / 优先级表承载（不在表 = 不做），别在正文再否定一遍。

判据：读者在 A 处已知的规则，B 处再出现全文 = 废话；B 处只在"这里有什么不同 / 跳哪看"时才写。

## 核心输出规范

PRD 是 baseline 决策的集中体现，不是重新发明。md 形态保证：**自包含 / 人读友好 / AI 可消费**。

### 模式判定

| 模式 | 触发 | 结构 |
|------|------|------|
| **Single** | 场景数 ≤ 10 | `prd-{简称}-v{N}.md`（单文件，12 章全在内）+ `assets/` |
| **Split** | 场景数 > 10 / `--mode split` 强制 | `prd-{简称}-v{N}.md`（主骨架）+ `prd-{简称}-v{N}-scenes/`（每场景一个 md，~80-150 行）+ `assets/` |

模式自动判定：`gen_prd_skeleton.py` 读 scene-list.md 数场景数。single → split 用 `split_prd.py`，反向用 `prd_compose.py`。split 界只管普通版本 PRD——baseline 是 living 文档集，无论场景数恒单文件（红线 1/2「单文件豁免」的另一半豁免对象就是它）。

### 章节归属表（行为规格 / 页面结构落位）

PRD md 是单一权威产出物，下列类型信息直接写进对应章节：

| 类型 | 落位 |
|------|------|
| 业务对象词典（属性 / 生命周期 / 数据来源 / 关系）| 第 3.2 章 |
| 业务动作（UI 场景）| 5/6/7.x 子场景的「页面元素 & 规则」区块表 4 列 |
| 业务动作（横切策略 / 后端流程）| 5/6/7.x 子场景的粗体段 + bullet |
| 条件分支业务规则（可断言形式 · 可选档）| 第 4 章「给定 ｜ 当 ｜ 则」三列表（含分支 / 阈值 / 多业务态时用，见 `references/prd-scene-templates.md §4.5`；`branch_prose_hits` WARN 兜底）|
| 状态机 | 第 3.3 章 |
| 非功能性 SLA | 第 10 章 |
| 优先级 P0/P1/P2 | 第 2.2 章 |
| 通用文案清单 | 第 8 章 |
| 场景独有文案 | 区块表「文案」列 |
| 信息层次 / 数据来源 | 区块表「数据来源」列 |
| 视觉调性 | 不单独记录（UI 设计稿 + design system 承载）|

### 流程图政策

PRD 里**禁写 mermaid / PlantUML 源码**——Confluence 不渲染。按复杂度分档：

- 简单二端流程（≤ 3 节点 / 单分支）→ 起点 / 终点 / 触发 / 延迟表，骨架默认生成在 §2.3 / §3.3
- 多角色 / 多分支 / 跨系统（内审 L58 硬指标必填）→ 走 `flowchart` skill 出 drawio + SVG，PRD 用 `![](./assets/flow-XX.svg)` 引图

详见 `references/prd-chapter-rules.md §三点五`。

## 执行步骤

> 写 §1 PR-FAQ 前 → Read `.claude/runbooks/pm-methodology.md §三 Outcome over Output`（含 PR-FAQ 自检）。写 delta §6 决策段 → Read `pm-methodology.md §二 决策段四段法`（§6 只写 WHY / 否决 / 取舍，禁复述 §2 已有的交互 / 字段 / 页面细节——这是 delta 最大字数黑洞）。

### Step 0：新建 PRD（scaffold + 手填）

```bash
python3 .claude/skills/prd/scripts/gen_prd_skeleton.py -p {产品线/项目} -v {N}
```

生成空骨架（含 `{{ 待填：... }}` 占位符）。PM + AI 按章节填，截图放 `deliverables/assets/`，md 用 `./assets/xxx.png` 相对路径。

**填充顺序**（自上而下，编号规则 → `artifact-conventions.md §一`，回读上下文 → `§三`）：

1. 第 1 章背景目标（对照 baseline 概览 / 术语章 + projects/product-lines.md）
   - **1.4 核心变更的基线是「当前线上」**，不是「之前的 PRD 版本」。线上无此功能 → 全部【新增】，**不写【变更】**；元数据「线上基线」字段也写「无（本期全新增）」
   - 1.5 用户角色写真实角色（发帖者 / 阅读者 / 运营 / 数据分析）+ 可见 / 可操作范围，不凑没上的角色
2. 第 2 章场景地图（已自动从 scene-list 填好，PM 调整优先级）
3. 第 3 章术语 + 业务对象
   - **3.2 业务对象只写本期新增对象**，既有对象（帖子 / 评论 / 作者等社区线上已有实体）一句「沿用线上现状，本 PRD 不重新定义」带过，**不脑补状态机 / 字段 / 生命周期**
   - 3.3 状态机同理：只画本期新对象，既有对象状态沿用现状
4. 第 4 章全局业务规则（先定 contract）
5. 第 5/6/7 章子场景（按模板逐个填，可并行；UI 场景走区块表 4.1，横切策略走粗体段 4.2，详见 `references/prd-scene-templates.md`）
6. 第 8/9/10 章（文案 / 埋点 / SLA，并行）。埋点表写完后：
   - **推 Confluence（首选）**：`md_to_confluence.py <prd.md> --merge-tracking`，wiki 上事件级列自动合并单元格，无需额外文件
   - **单独发给研发（备用）**：`python3 .claude/skills/prd/scripts/export_tracking_xlsx.py <prd.md>` 导 xlsx，用于不看 wiki 的场景
7. 第 11/12 章（排期 + 附录，最后）

每填完一段跑一次 `check_prd_md.sh <md> --skeleton`（宽松模式跳占位符 / 截图 / freshness）。终态推 Confluence 前去 `--skeleton` 跑严格。

### Step 1：升版（直接改 md）

md 是源文件，PM 直接 VS Code / Edit 改。改完跑 `check_prd_md.sh` 过则推。**不需要 gen_prd_v{N+1}.py 这种 per-project 生成器**。

split 模式：
- 改主骨架（1-4 / 8-12 章）→ 直接编辑 `prd-xxx-v{N}.md`
- 改某场景 → 编辑 `prd-xxx-v{N}-scenes/{view}-{编号}-{名}.md`
- 加新场景 → 主 md 的 5/6/7 章 bullet 加链接 + scenes/ 目录建新 md
- 删场景 → 主 md 删链接行 + 删 scenes/ 文件

### Step 2：重生骨架的 stale 清理（--force 陷阱）

`--force` 覆盖生成文件，但 stale（scene-list 已删场景的子文件 / view 前缀调整后的旧前缀文件 / 误嵌套子目录）不在覆盖范围。**脚本生成前自动扫描并打印 stale 清单**（scenes/ 下不在 scene-list 期望集的 .md + 任何子目录），确认内容已迁移后：

```bash
python3 .claude/skills/prd/scripts/gen_prd_skeleton.py -p {项目} -v {N} --force --clean-stale
```

`--clean-stale` 逐个打印删除项。不删的后果：stale 被拼进 compose，`check_prd_md.sh` 抓裸编号 / 消失场景引用 / 类型错位。主 md 手动 rename（骨架短名 → 项目全称）脚本不感知——单步 mv 别累加，rename 后再 `--force` 会按期望名再生成一份原名文件。

### Step 3：截图回填

**何时必须重拍**（任一触发）：源 HTML 改了 / 新增 / 修改 / 删除场景编号 / 改设备布局 / 视觉规范 / 截图覆盖范围。

**优先级 & 调用**：

1. **项目内有 `projects/{项目}/scripts/screenshot_for_prd*.py`** → **直接调，不自己写**：
   ```bash
   python3 projects/{项目}/scripts/screenshot_for_prd.py
   ```
   历史项目脚本多是 wrapper（保留项目 SCENE_MAP 白名单 + 调 framework `shoot_from_imap`）；原型截图模式自管的（如 activity-center），应 import framework helpers
2. **IMAP 模式新项目** → framework CLI：
   ```bash
   python3 .claude/skills/prd/scripts/screenshot_for_prd.py --imap <imap.html> -o deliverables/assets/
   ```
   省略 `--scenes` 时按 `.st h2` discover 全截；白名单格式 `--scenes "scene-A-1.png=A-1 · 完整全貌,..."`
3. **骨架原型模式（小迭代只做 prototype 常用）** → framework CLI，**无需写项目脚本**：
   ```bash
   python3 .claude/skills/prd/scripts/screenshot_for_prd.py --proto <proto.html> -o deliverables/assets/
   ```
   按 `build_proto_skeleton` 约定（`.gnav-view-section` × `.p-page`）自动遍历 view × page，出 `proto-{view}-{page}.png`；白名单 keyword 匹配 `view_id/page_id`。**仅适用骨架生成的原型**（现行标准）
4. **手写 / 非骨架原型** → 写项目脚本 import framework helpers（`launch_page` / `dismiss_all_overlays` / `fix_dpi` / `assert_screenshots_fresh`），**不从零起步**（`--proto` 遇非骨架结构会报错引导到此）：
   ```python
   sys.path.insert(0, "<repo>/.claude/skills/prd/scripts")
   from screenshot_for_prd import launch_page, dismiss_all_overlays, fix_dpi
   ```

**源 HTML 探测**：`discover_source_html` 合并 prototype + IMAP 候选（`*原型*.html` / `proto-*.html` / `*交互大图*.html` / `imap-*.html`），取 mtime 最新。任一源动了 → PNG stale。archive / deprecated 子串排除。

**命名 / 路径**：
- 文件 `scene-{编号}.png`（如 `scene-A-1.png` / `scene-D-0-mylive.png`）；原型模式 `proto-{view}-{page}.png`（如 `proto-h5-center.png`）
- 输出 `deliverables/assets/`，md 引用 `![alt](./assets/xxx.png)`（split 子场景用 `../assets/`）

**自动守门**：`check_prd_md.sh --assert-fresh` 比对源 HTML mtime（实为 .freshness.json hash 判定 .flow DOM 子树，无关 CSS / 注释不再误报；缺 manifest 降级 mtime），FAIL raise + 列过期清单。

**推 Confluence**：图片由 `scripts/md_to_confluence.py` 自动上传 attachment（扫 `./assets/`），PM 无需手调。

### Step 3.5：交付前冷读（叶子完整性反测 · 推 Confluence / 交付研发前必跑）

> 机械自检（`check_prd_md.sh` + cross-check 7 维）抓「形」——编号 / 术语 / 字段格式 / 死链。叶子完整性盲区（实时字段刷新触发点没写、快照字段生命周期模糊、展示窗口与数据保留期不对齐、跨章口径打架）是**单文档语义缺口**，机械抓不到，靠冷读反测。7 类盲区权威定义在 `references/prd-scene-templates.md §4.6`。
>
> **硬约束：冷读判断必须派干净上下文子代理**（Agent 工具）——同 session 已读上下文会脑补，测不出盲点。脚本只打包探针，不调 Agent。

1. **打包探针**：
   ```bash
   python3 .claude/skills/prd/scripts/cold_read.py --prepare <prd.md> [--targets 3.1,4.1,5.1]
   ```
   省略 `--targets` 时自动选「静态」实体 / 规则 / 状态机章（最易埋叶子洞的章）。脚本产出三件：context 文件（compose 全文 + scene-list，落 /tmp）、每个 target 一段 `=== PROBE ===` 探针 prompt、`cold-read-{date}.md` 盲点清单模板（落 PRD 同目录）。
2. **派干净子代理逐 target 跑**：把每段 PROBE prompt 原样喂 Agent 工具（`Explore` / `general-purpose`），N 个 target 并行派。子代理 prompt 已内置隔离铁律（只 Read context 文件、禁读写 session-state、不脑补作者本意）。
3. **回填盲点清单**：把各子代理返回的盲点聚合进 `cold-read-{date}.md`，每条四件套（位置 + 盲区类别 + 冷读者会怎么误读 + 建议补法）。
4. **逐条 triage**：每条标「补文档 / 留版本 / 误报」。补 = 回 PRD 对应章补一句 / 一列 / 一行（业务语言）；属承重不变量则同步反向合并进 baseline（走 §9 指引）。补完重跑 `check_prd_md.sh`。

cross-check skill 的 Reader Testing 终验时调用本工序（不在 cross-check 复述机制）。

### Step 4：推 Confluence

**split 模式：脚本检测到 `-scenes/` 强制 PM 选推送方式**（不再静默 compose 推单页）。

**方式 A · 1 父页 + N 章节子页（推荐 split 项目）**：
```bash
# 新建
python3 scripts/md_to_confluence.py <prd.md> --split-children-by-chapter --parent-id <PARENT_SPACE_ID>
# 更新
python3 scripts/md_to_confluence.py <prd.md> --split-children-by-chapter --update-id <PARENT_PAGE_ID>
```
父页含 §1-3 + §8-12 全文 + §4-7 章节链接到子页；子页 = 该章全部场景内容。更新模式按子页 title 自动匹配（子页名固定「{Part 0/1/2/3 白话标题}」）。

**方式 B · 单页 compose（场景少 / 历史页已是单页）**：
```bash
python3 scripts/md_to_confluence.py <prd.md> --no-split --parent-id <id>
python3 scripts/md_to_confluence.py <prd.md> --no-split --update-id <id>
```
`--no-split` 绕开 split 门强制 compose 单页；single 模式 PRD（无 `-scenes/`）不需要此 flag。

**single 模式 PRD**：
```bash
python3 scripts/md_to_confluence.py <prd.md> --parent-id <id>
python3 scripts/md_to_confluence.py <prd.md> --update-id <id>
```

**自动行为**（所有模式，细节见 `cli-cheatsheet.md §推送`）：
- 正文原生渲染（markdown-it → Confluence storage，不包宏）；本地图片自动上传 attachment；区块表 4 列识别 → cell 内 `；` 切 bullet（**source 写 `；` 串多条规则，不手敲 `<br>`**）
- **推送前剥离内部内容**：反向合并指引整章（delta §9）+ 决策记录整章（delta §6）+ 排期整章（delta §8「排期 / 上线节奏」/ 普通 PRD §11「里程碑与排期」）+ 文档头元信息块（判据 = H1 与首章间全为 `-`/`>`/`---`/空行）。承重约定：**协作头用表格（`|` 开头）→ 保留上 wiki；内部机制用 bullet → 剥掉**。`--exclude-section <关键词>` 追加 / `--keep-preamble` 保留头部

**推送方式选择规则**：
- split 项目首推 → AI 必须问 PM 选 A / B 再执行
- split 项目复推 → 默认 A 方式（保持 1 父 N 子结构）
- 父子页结构一旦上线就不要轻易变（B 转 A 要手工删旧子页或反之）

**首推同名冲突**：`--parent-id create` 时若 space 下已有同名页，Confluence 返回 HTTP 400。**脚本在 create 前已做 `search_pages` 同名预检**，命中会打印同名页 URL + 提示 PM 三选一：
1. **新建新版页**：加 `--title "示例社区交易卡片 PRD（2026-05-12）"` 改名（带日期 / 版本号 / 场景范围）
2. **覆盖历史页**：改用 `--update-id <历史 pageId>` 覆盖推
3. **历史页先归档**：手工 wiki 把历史页移到 archive 空间 / 加后缀「- 历史版本」，再跑原命令

AI 在 PM 推之前主动问一次。

### Step 5：老项目迭代（baseline / delta 循环）

产品线已立 `prd-{产品线}-baseline.md` 时，迭代走文档集循环。模型全貌（四产物归属 / 承重不变量 / 状态受控词表 / 四支柱 / 迭代循环 / 新鲜度多层 / delta 正文写作纪律）见 [artifact-conventions.md §六](../../runbooks/artifact-conventions.md)，本节只列命令与 PRD 专属行为。

1. **baseline 首建**：`gen_prd_skeleton.py -p {产品线} -v 1 --profile baseline`（落产品线根、无版本号、living）。**此后绝不重跑骨架**（`--force` clobber 已填内容），反向合并手动 Edit。
2. **写本轮 delta**：`gen_prd_skeleton.py -p {产品线} -v {版本} --profile delta`，脚本落 `deliverables/{季度}/{版本}/`。`--quarter` 缺省当前季；启动时打印 baseline 路径 + 该季已有版本供定版（**不自动 +1**）。整包 delta PRD + imap + prototype + assets。
3. **上线后承重不变量**（顺序不可乱）：changelog 行 → 反向合并进 baseline → 状态推进「已合并」→ 归 `archive/{季度}/`。细节见 artifact-conventions §六。
   - **高价值 delta 的 Outcome 闭环**：§1 价值段一句写清假设 + 反转条件；archive 前回填一句 Review 结论（成立 / 部分成立 / 被证伪）。**只对高价值 delta，非每轮**；不加表、不加骨架字段。
4. **新鲜度**：`check_baseline_fresh.py {产品线}` + `baseline-fresh-gate` 守第一层（已上线 delta 未合并报红）；模块章头 `最后核对线上` 超 60d 报黄。

骨架真实产出章节集：baseline = 概览 / 术语 / 模块树 / 全局规则 / N 个模块章 / 文案 / 非功能 / 变更记录；delta = **协作头表** + 9 章树（§1 背景价值 / §2 本轮需求 / §3 业务对象增量 / §4 状态机增量 / §5 全局规则增量 / §6 决策记录 / §7 埋点 / §8 排期 / §9 反向合并指引）。

**delta 协作头表**（紧跟 H1，对齐公司 PRD 模板的 PRD 信息 / 团队信息 / 资源对接三张表，压成一张）：PRD 版本 / 状态 / 拟制人 · 日期 / 火效 / 重要性 · 紧迫性 / 迭代档位 / 端侧范围 / 提测 · 走查 · 上线 / 产品 · 交互 / 设计 · 设计稿 / 前端 · 后端 / 测试。三条约束：

- **「状态」「火效」两格固定在第 3 列 key、第 4 列 value**（值落行尾单元格），`sync_hx_status.py` 按此回写，勿调列位
- **日期不写进协作表**，「提测 / 走查 / 上线」格写「待定」——排期章不上 wiki（推送时整章剥离），写「见排期章」会在 wiki 上变死引用；日期的单一权威位是 §8 排期表（同一字段只写一次）
- **文档机制说明（baseline 指针 / delta 性质）不进头部**，落 §9（推送时整章剥离）

**delta 迭代档位（`--tier`，决定 §2 行文）**：一份 delta 先认档位，再按档位组织 §2 本轮需求。

| 档位 | `--tier` | 触发 | 版本号 | §2 行文 |
|------|----------|------|--------|---------|
| 补丁包 | `patch` | 散修复 + 小调，互不依赖 | x.y.**z** 三段 | §2.0 索引表 6 列（编号 / 需求 / 端 · 模块 / 修改点 / 验收 / 优先级）收口，**默认全部进表**；命中升块判据的重项才另起 H3（见下） |
| 内聚特性 | `feature`（默认）| 单一能力，有新对象 / 状态机 | x.y 两段 | 平铺，按用户旅程叙事 |
| 集合体 / 多团队 | `bundle` | N 个松耦合需求跨模块 / 团队 | x.y 两段 | 强制 §2.0 索引表 + 按单轴分组 H2 |

`patch` / `bundle` 自动吐 §2.0 本轮需求索引表。**两档列不同**：

- `patch` = `编号 / 需求 / 端 · 模块 / 修改点 / 验收 / 优先级`。骨架**不为任何需求预生成 H3 块**——轻项在表里就讲完了，重项才另起。**升块判据**（任一命中）：新增 / 变更业务对象 · 涉状态流转 · 跨端行为不一致 · 有取舍要在 §6 交代；重项模板在骨架 §2.0 表后的 HTML 注释里，复制出来用。「默认最轻、升块是加法」是承重设计，反过来（预生成四槽靠删）必然被填满。`check_prd_md.sh` 的「delta 分量伸缩启发式」报 WARN 兜底（该塌没塌 + 「详见 2.N」悬空指针）
- `bundle` = `编号 / 需求 / 分组 / 反向合并目标 / 优先级`，分组**只许沿一条轴**（模块 > 用户旅程 > 跟版边界 > 团队，选读者跨引最少的一条），每条需求仍出 H3 块
- **bundle 按端拆文件**（触发条件：各端有独立研发团队 + 开发明确要求）：一个版本号下产多个文件 `prd-{线}-{版本}-{端}.md`（如 `-web.md` / `-app.md`），每个文件是完整独立的 delta（含自己的 §1–§9），静态章按本端内容裁剪（无关的业务对象 / 状态机 / 规则整章删），原合并文件加废弃注释指向拆分后的文件。同版本的索引表只在原文件或约定的一端保留，拆分后各文件 §2.0 只列本端需求。

详见 [prd-chapter-rules.md §2 行文](references/prd-chapter-rules.md)。

**`--tier`（§2 组织）与四支柱填充（§3/§4/§5）正交，是两根独立的轴**：
- §3/§4/§5 **不需要二级开关**——全新能力 delta 填实即与 baseline 对应章（§3.2 业务对象 / §3.3 状态机 / §4 全局规则）同构、反向合并直接搬章；只动既有场景的 delta 本轮无该支柱变更直接删空章（符「迭代只写真有改动」铁律）。
- `--tier` 只管 §2 怎么排版（索引 + 分组 vs 平铺叙事），不决定四支柱有没有内容。两者各管各的，别混。

**反向合并映射唯一落在 §9 表**：骨架正文不吐「本轮无 X 则删本章 / 上线后反向合并进 baseline §X」这类章首导语（plumbing 进不了交付物）。哪章可删、合并到 baseline 哪章，看 §9 反向合并指引表（推 Confluence 时 §9 自动剥离，见 Step 4）。

## API 速查

```python
# 输出 md 字符串
from core.md_renderer import MdWriter, scene_5section_card, bold, italic
w = MdWriter()
w.h1("1. 项目背景与目标")
w.h2("1.1 背景")
w.bullet_list(["痛点 A", "痛点 B"])
w.field_bullet("业务描述", "用户点「发布」把内容发到社区")
w.field_bullet_list("前置条件", ["已登录", "未被禁言"])
w.table(headers=["编号", "场景"], rows=[["A-1", "发帖"]])
w.image("./assets/scene-A-1-wireframe.png", alt="发帖低保真")
md = w.render()

# 12 章骨架编排
from sections_md import build_full_skeleton, build_scene_file, SceneInfo
md = build_full_skeleton(info={"project_name": "xxx", "version": "1", "scenes": [...]})

# 解析现有 md
from humanize.md_scan import scan_human_voice_md, scan_prd_structural_md
voice_hits = scan_human_voice_md(md_text)
struct_hits = scan_prd_structural_md(md_text, scene_count=10)
```

埋点表交付方式（两种，按场景选）：

```bash
# 推 Confluence（首选）——wiki 上事件级列自动 rowspan 合并，无需额外文件
python3 scripts/md_to_confluence.py <prd.md> --merge-tracking --update-id <pageId>

# 单独发给研发（备用）——导 xlsx，用于不看 wiki 的场景
python3 .claude/skills/prd/scripts/export_tracking_xlsx.py <prd.md> [-o out.xlsx]
```

## 自检清单（PM 交付前过一遍）

**机器已拦（信任 checker，不用人肉复查第二遍）**：`bash check_prd_md.sh <prd.md>` exit 0 已覆盖——§X.Y 锚点 + 裸场景编号死链（只对 split 开，单文件 = baseline + single delta 天然豁免；profile 仅控 baseline 其他行为）、行内版本标签、mermaid / URL 路由、`---` 水平线、`>` 引用块（baseline 例外）、占位符（终态）、行文三件套 WARN（单行 ≥ 2 分号 / 句段 ≥ 100 字 / bullet 行内串句，豁免细则 `references/prd-chapter-rules.md §三`）、组头式三段式标签（`label_li_runs`）。`python3 scripts/check_cjk_punct.py <md> --strict` exit 0 已覆盖 CJK 标点。FAIL/WARN 直接修。

**人肉盲区（机器抓不到，真要过）**：

1. **截图齐全**：`./assets/` 下所有引用文件存在（split 子场景注意 `../assets/` 前缀）
2. **模板字段名锁定**：`grep -E "^- \*\*(触发|读|写|事件|API)" <md>` 无命中（UI 场景统一走区块表）
3. **跨章引用合规**：`见 X.Y 白话名` 而非裸 `见 X.Y` / `见 A-1`（split 由 checker 拦，单文件人肉自查）
4. **全文讲人话**：契约层（章号见红线 3）无 snake_case 研发字段（用中文业务名），唯埋点章事件 / 属性英文名例外
5. **叶子完整性**：实时 / 快照字段标清生命周期与刷新触发点，阈值标端点（含不含），状态机穷举（含自环 / 离线再上线），展示窗口与数据保留期对齐。交付 / 推 Confluence 前跑「交付前冷读」Step（`cold_read.py` + 派干净子代理），盲点逐条 triage。7 类盲区见 `references/prd-scene-templates.md §4.6`

## References 索引

**必读**（写 PRD 前加载）：
- `references/prd-chapter-rules-quickref.md` — 12 章结构 / 迭代 scope / baseline-vs-delta / 字段归属 / Confluence 约束 / 越界禁词 / must-have / split 结构（~100 行速查，写 PRD 前读这页）

**按需读**（命中具体步骤再加载）：
- `references/prd-chapter-rules.md` — 章级细则（禁词完整清单 / 状态机模板 / 埋点边界 / 自检清单），写具体章节命中细则时读
- `references/prd-scene-templates.md` — 写第 5/6/7 章场景前加载（UI 场景区块表 / 横切策略模板 / 数据影响写法）
- `references/prd-optional-sections.md` — §1.6 竞品调研 / §1.7 多方案对比 模板，PM 加可选章节时 copy
- `references/metrics-framework.md` — 写 §9 埋点 / §1.4 北极星指标时加载
- 讲人话共性铁律见 `.claude/runbooks/human-voice-rules.md`，PRD 形态规则在 prd-chapter-rules §三 / §三点八

## 注意事项

### 可选章节（按需 copy）

`gen_prd_skeleton.py` 默认生成 12 章骨架。以下两节按需追加在 §1.5 后、§2 前：
- **§1.6 竞品调研**：项目首次涉足某场景 / 内审要求竞品参照 / 决策依据需向 leader 说明时加。简单迭代不加
- **§1.7 多方案对比**：本期有 2+ 候选方案 / 技术路径有分歧 / 需说明为何选 A 不选 B 时加。单方案需求不加

模板见 `references/prd-optional-sections.md`，骨架不默认生成，PM 觉得需要时从模板 copy 进 PRD md。

### 方案型项目（不走标准 pipeline）

判定信号（任一）：
- 涉及独立 mid-office + 业务系统 + 风控系统跨系统对接
- 含资金路径 / 跨账户结算
- 涉及法务 / 合规批复路径
- 仅后端架构无 UI 流（如打分引擎 / 数据 pipeline）

不强制 12 章。PM 自定章节（建议对标共建 PRD 模板），文档仍 md，仍走 `md_to_confluence.py` 推 wiki。

文档分工建议：方案概览 / 系统拓扑 / 各系统职责 / 接口 schema / 资金对账 / 风险与回滚 / 灰度计划。

