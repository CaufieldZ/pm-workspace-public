---
name: user-manual
description: >
  当用户提到「操作手册 / 使用手册 / 用户手册 / 帮助中心文章 / 带截图的 SOP 手册」时触发。
  「营销稿 / 宣发稿 / 上线宣传 / 推广文案」亦触发（走 promo- 模式，两者同为面向用户的上线交付物）。
  丢一份现有手册 / 营销稿要改版亦触发。「告警 SOP / 监控值班手册」不触发（那是 prd- 应急 runbook，另一物种）。
type: standalone
output_format: .md + .docx
output_prefix: user-manual- / promo-
depends_on: []
optional_inputs: [baseline, delta, prototype]
consumed_by: []
scripts:
  build_manual.py: "源 md → docx（pandoc + reference.docx + callout.lua）+ 图片清单 — python3 build_manual.py <source.md> [--allow-placeholder]"
  check_manual.sh: "Step B 自检 — bash check_manual.sh <source.md>"
---

# User Manual — Platform C 面向用户的上线交付物（手册 + 营销稿，docx + md，带截图）

## 触发与定位

**做什么**：把一个功能/活动写成面向使用者的对外产出物，两种模式共用截图获取 + 项目结构：
- **手册模式**（`user-manual-` 前缀）：操作 / 使用手册。单源 md → pandoc 转 docx，源 md 即帮助中心可发布版。教用户怎么操作。
- **营销模式**（`promo-` 前缀）：营销 / 宣发稿。渠道分版文案（Banner / 博客 / 更新日志）+ 配图索引，介绍功能卖点。docx 为可选产出（需发运营 / 传阅时 build）。

**何时触发**：手册——「操作手册 / 使用手册 / 帮助中心文章 / 带截图的 SOP」；营销——「营销稿 / 宣发稿 / 上线宣传 / 推广文案」；或丢一份旧手册 / 营销稿要改版。

**不做**：PRD / 需求文档（走 prd skill）；告警 / 监控值班 SOP（`prd-` 应急 runbook）；内部后台逻辑规格（归 PRD）。**上线宣发三件套**（视频/gif 分镜脚本 · 图文 4 宫格 · 短卖点文案，痛点→卖点→CTA，产物前缀 `launch-`）走 promo-kit skill；本 skill 的 `promo-` 只做**渠道分版长文案**（Banner / 官方博客长文 / 更新日志条目）。

**受众**：读者是**运营 / 主播 / C 端用户 / 潜在用户**，不是研发。正文一律业务白话，禁内部版本号 / 场景号 / 埋点名。

## 改脚本前 30 秒

> `skill-load-gate` 守的是「Read 过本文件」**不看读了多少行**。
> 改本 skill `scripts/*.py`：`Read 此文件 limit=80`（前两节就够）。
> 改产出物（手册 md）：建议全文 Read（写作规则散在 §3 / §4）。

**Public API（不可改签名 · 改前看调用方）**：
- `build_manual.py <source.md> [--allow-placeholder] [--docx-out <path>]` — 唯一 docx 生成入口
- `check_manual.sh <source.md>` — Step B 自检入口

**会拦你的 hook**：
- `script-syntax-gate` — pyflakes / bash -n（写 .py / .sh 自动跑）
- `plain-language-gate` — 产物落 `deliverables/` 且非 `prd-` 前缀 → 写盘自动 `--strict` 强阻断（内部锚点 / 决策号 / `[待补充]` / FIXME / 翻译腔禁入对外手册）
- `cjk-punct` — deliverable md CJK 标点强阻断
- `learned-rules-gate` — 工区习得规则

**改完跑啥**：
```bash
python3 .claude/skills/user-manual/scripts/build_manual.py /tmp/demo-manual.md --allow-placeholder
```

**深入读什么**（按需 grep 定位）：
- 完整 API：`grep -A 20 "^## API 速查" SKILL.md`
- 模板骨架：`Read references/user-manual-template.md`
- 帮助中心发布：`Read references/help-center-publish.md`

## 硬规则（FAIL 即拦）

1. **单源不分叉**：docx 与帮助中心 md 同一份正文，禁两边写不同文案 / 不同截图。docx 由 `build_manual.py` 从 md 转出，**禁手改 docx**（改 md 重 build）。
2. **每张截图必带 `图：` caption**：图用 `![图：一句话说明](images/NN-slug.png)`，alt 文本以 `图：` 开头并说清这张画的是哪一步。禁裸 `![](...)` 无说明。
3. **缺图阻断**：正式交付 `build_manual.py` 不带 `--allow-placeholder`，引用的本地图必须都存在；占位阶段才用该参数。
4. **正文讲人话**（hook 强阻断）：受众是运营 / 用户，禁内部文件名 / 场景号（A-1）/ 决策号 / 埋点事件名 / 数据库字段名 / API 参数。手册禁工程学术词；营销稿（`promo-`）禁内部迭代版本号（如「社区 3.2」，用户不认，`plain-language` 对 promo- 前缀 strict 拦）。说「点『开始直播』」不说「触发 live_start 事件」。
5. **人称按前缀分流**（违反即视角打架）：
   - `user-manual-`（手册）→ **第二人称 + 动作祈使**：对读者说「你」，步骤用「点击 / 选择 / 填写」。
   - `promo-`（营销稿）→ **第三人称陈述**：站在介绍产品能力的位置，不对特定一方喊话。禁「你的仓位…读者看到」这种同段混用两种视角（营销稿读者既是发帖者也是围观者，是同一批人，分「你 vs 读者」必打架）。
     ❌ 反例：`发帖挂上你的实盘仓位……读者看到的是你的完整过程`
     ✅ 正例：`发帖时可挂载真实实盘仓位……呈现的是一次交易判断的完整过程`
6. **命名前缀 `user-manual-` / `promo-`**：手册用前者、营销稿用后者，落项目 `deliverables/{季度}/{版本}/`。
7. **callout 用 blockquote**（手册模式）：提示框写 `> **【提示】** …`（类型见 §4），禁在 md 源里手画单元格表格当提示框（那是 docx 渲染产物，由 `callout.lua` 自动生成）。
8. **Figma 只读 · 图上文字不改图**：figma MCP + `fetch_figma.py` 走 REST API，只能读结构 / 导图，**改不了画布文字**。截图里的外文一律由设计侧在 Figma 替换，模型交付 On-Image String Map（字串译文表）而非声称能编辑 Figma。详见 `references/promo-localization.md`。

## 核心输出规范

### 产物目录

```
projects/{项目}/deliverables/{季度}/{版本}/
├── user-manual-{feature}.md       ← 手册源 = 帮助中心可发布版
├── user-manual-{feature}.docx     ← build_manual.py 转出，截图内嵌
├── promo-{feature}.md             ← 营销稿（渠道分版 + 配图索引），docx 可选
├── images/                        ← 手册截图（营销图另存 inputs/figma/，不内嵌）
│   ├── 01-{slug}.png              ← 两位序号 + 语义 slug
│   └── 02-{slug}.png
└── images-manifest.txt            ← build 自动产，帮助中心上传清单
```

> **同目录多手册共享 `images/`**：靠 slug 区分归属（`01-web-create` vs `01-h5-entry`），加图到中间要倒序 `mv` 顺延序号 + 全文改引用，改前先 `grep -o "images/[a-z0-9-]*" *.md` 查是否被同目录其他手册引用。`images-manifest.txt` 由最后一次 build 覆盖 —— 每张图 build 都重写清单，`--promo`（营销稿不内嵌图）会把清单刷成 0 张，收尾必须以「内嵌图最全的那份手册」`build_manual.py` 重跑一次恢复清单。

### 手册骨架（`user-manual-` · 混合式 · 详见 references/user-manual-template.md）

- **标题块**：粗体标题行 + 副标 + 一行版本/适用对象/更新日期 + 元信息表（纯 markdown，不用 YAML frontmatter）。
- **`# 欢迎使用 …`**：一段总览 + 能力清单 bullet + 「本手册分两部分」导读。
- **`# 第一部分 · {操作主体}操作`**：H2 章节标题**动词化**（「如何预约并开播」而非「直播中管理」），每章四段式：
  - **前置条件**：开始前你需要什么（已认证 / Chrome 90+ …）
  - **操作步骤**：有序列表 `1. 2. 3.`，与截图标注点呼应（截图里的标注角标随设计走，正文不用圈号）
  - **预期结果**：成功后你会看到什么
  - **提示与风险**：`> **【提示】**` / `> **【重要】**` / `> **【⚠️ 风险提示】**`
- **`# 第二部分 · {受众}端体验说明`**：让操作者了解终端用户看到什么。
- **`# 常见问题`**：`**Q：…**` / `A：…`。
- **`# 附录 · 名词解释`**：两列表。

### 营销骨架（`promo-` · 渠道分版 + 文末配图索引）

营销稿一份 md 内按渠道分节（一次上线多渠道复用同批卖点 + 同批图），第三人称陈述：

- **文档头**：加粗引导块（不用 blockquote 墙），列一句话卖点 + 上线时间 + 配图源目录。
- **`## 渠道一 · 站内 Feed / Banner`**：主标题（可给 2 选 1）+ 副标题 + 一段正文 + 行动按钮文案。
- **`## 渠道二 · 社媒 / 官方博客`**：标题 + 开头点破痛点 + 3 个卖点小节（每节小标题 + 连贯散文，**不拆 bullet**——营销散文要连贯，bullet-density 对 promo- 是误报，命中加 `<!-- lint-skip:density -->` 或整段绕过）+ 结尾行动召唤（可含二期预告钩子）。
- **`## 渠道三 · 站内公告 / 更新日志`**：`【新增】{功能}：{一句话}` 条目式。
- **`## 配图索引`**：表格（卖点 / 场景 / App 图名 / Web 图名）+ 配图用法建议。**场景号（B-1/A-2）只出现在此索引表**，正文禁用。

配图不内嵌正文（营销排版设计侧另做），只在文末索引登记路径。docx 可选：需发运营 / 传阅时 `build_manual.py --promo` 转出。

**多语言版本**：外文版落 `promo-{feature}-{lang}.md`（如 `-en`），与主稿并列、卖点/结构/配图一一对应。调性**按渠道分别本地化**，不逐句直译（英文 mock 走 native CT 语感而非中译英）。图上外文交 On-Image String Map（不改图）。mock 晒单文案默认中等档（有 KOL 味不脏）。详规见 `references/promo-localization.md`。

### callout 四类（手册模式 · blockquote，docx 由 callout.lua 渲成底纹框）

| 写法 | 用途 |
|---|---|
| `> **【说明】** …` | 背景 / 能力边界 / 二期预告 |
| `> **【提示】** …` | 顺手的好习惯、可选项 |
| `> **【重要】** …` | 不照做会卡流程 / 出错 |
| `> **【⚠️ 风险提示】** …` | 不可逆 / 对外可见 / 资金相关操作（交易、推送信号） |

四类标签固定用【说明】【提示】【重要】【⚠️ 风险提示】，别自造标签 —— docx 靠 `callout.lua` 认标签渲底纹框，推 wiki（`md_to_confluence.py`）也靠标签自动转 Confluence 原生彩色面板宏（说明→info / 提示→tip / 重要→note / 风险提示→warning），标签写错两边都退化成灰色引用条。源 md 保持 blockquote 不动，两条渲染路径各自转换。

当产物需推送到不支持 Confluence callout 宏渲染的页面（如 Platform C 公告页 / 帮助中心）时，所有 blockquote callout 展平为普通正文：「注意」类保留加粗「**注意**：」前缀，普通提示直接融入正文段落、不加任何标签。

### 截图

- 命名 `NN-slug.png`（`01-workbench-entry.png`），序号 = 正文出现顺序。
- 引用 `![图：主播工作台入口（频道页右上角「主播工作台」按钮）](images/01-workbench-entry.png)`。
- **单张说明图**：走文本流 `![图：…](images/NN.png)`，推 wiki 时按纵横比自动定宽（竖屏 360 / Web 700 / 横屏 900）。
- **多图步骤 / 两端对比 / 二选一**：用 `:::steps` 围栏包一个带表头的 markdown 表格（表头写步骤语义，如「第一步：点头像｜第二步：点主播中心」「手机端｜电脑端」），每列一张图。围栏内图片推 wiki 自动收窄（竖屏 260 / 横屏 340），避免并排撑满半屏显大。pandoc 侧 `:::steps` 是 fenced div，docx 不显示围栏文字、表格正常渲染，单源不破。

```markdown
:::steps

| 第一步：点头像进入个人中心 | 第二步：点「主播中心」 |
| :---: | :---: |
| ![图：App 首页点头像](images/01-entry-avatar.png) | ![图：点主播中心](images/02-anchor-center.png) |

:::
```

## 执行步骤

### Step 0 — 定模式、项目与范围
先定**模式**：教操作 → 手册（`user-manual-`）；介绍卖点做推广 → 营销稿（`promo-`）。再确认属于哪个项目、覆盖哪个功能/活动、受众是谁（手册：运营 / 主播 / C 端；营销：潜在用户 / 全体用户）。产物落 `projects/{项目}/deliverables/{季度}/{版本}/`。

### Step 1 — 读信源（并行）
并行 Read：
- 本轮迭代 **delta PRD**（`deliverables/{季度}/{版本}/prd-*.md`）为主信源，`read_prd_section.py --toc` 选章节；
- **baseline** 补背景（`.claude/skills/prd/scripts/read_prd_section.py <baseline.md> --toc`）；
- 有原型则读原型 HTML 抓页面/流程；
- 本 skill `references/user-manual-template.md`（骨架）。

### Step 2 — 备截图进 images/
按正文顺序备图，三种来源：
- **用户直接给 PNG** → 放进 `images/`，按 `NN-slug.png` 命名。
- **用户给 Figma canvas 链接** → `python3 scripts/fetch_figma.py <url> --image -o images/NN-slug.png`（多帧用 `--batch "node=NN-slug.png,..."`；找 node-id 先 `--search "关键词"` / `--tree`）。下载后**自己看图**确认每张画的哪一步、配准 caption。
- **已有原型 HTML** → `python3 .claude/skills/prototype/scripts/pre_proto_phone_shots.py <proto.html> -o images/`。
- 还没图 → 先在正文用 `图：…` caption 占位，build 时带 `--allow-placeholder`。

### Step 3 — 写源 md（按模式分骨架）
- **手册**：按 §4 手册骨架写 `user-manual-{feature}.md`。第二人称、动词标题、四段式、callout blockquote、图带 `图：` caption。
- **营销**：按 §4 营销骨架写 `promo-{feature}.md`。第三人称陈述、渠道分版、配图只进文末索引、场景号禁入正文。博客散文连贯不拆 bullet。多语言版 / mock 晒单口吻分档 / 图上文字 → 先 Read `references/promo-localization.md`。
- **语气去 AI 味**（两模式都守，领导验收高频吐槽点）：讲人话只是及格线，还要有温度 —— 提问 / 场景开场（不平铺功能）、短句祈使（删「方可 / 通过…来」）、结尾给感召收尾（不戛然而止）、克制修饰不堆 emoji。四条正向契约 + 参考交易所范例见 `references/user-manual-template.md §三`（写前必读）。

两者写盘即过 `plain-language-gate` / `cjk-punct` hook（promo- 前缀自动走营销语境分流：放行「全新上线」等营销词、strict 拦内部版本号），按报错改。

### Step 4 — 转 docx + 清单
- **手册**（必出 docx）：
```bash
python3 .claude/skills/user-manual/scripts/build_manual.py \
  projects/{项目}/deliverables/{季度}/{版本}/user-manual-{feature}.md
```
缺图阶段加 `--allow-placeholder`；正式交付去掉，确保零缺图。
- **docx 视觉验证不靠猜**：装 LibreOffice 后 `soffice --headless --convert-to pdf` 把 docx 转 PDF，再 Read 出图核对排版；pandoc 表格单元格默认套用 `Compact` 段落样式，`reference.docx` 必须显式定义 `Compact` 为紧凑行距，否则回退 `Normal` 把行距撑高。
- **营销**（docx 可选，需发运营 / 传阅时才转，缺图常态放行）：
```bash
python3 .claude/skills/user-manual/scripts/build_manual.py \
  projects/{项目}/deliverables/{季度}/{版本}/promo-{feature}.md --promo
```
纯站内文案则跳过本步，md 即交付。

### Step B — 自检
```bash
bash .claude/skills/user-manual/scripts/check_manual.sh \
  projects/{项目}/deliverables/{季度}/{版本}/user-manual-{feature}.md
```

## API 速查

**build_manual.py**（唯一 docx 入口）
```bash
python3 .claude/skills/user-manual/scripts/build_manual.py <source.md> \
  [--allow-placeholder]   # 缺图降级 warning（手册占位阶段）
  [--promo]               # 营销稿：docx 可选产出，缺图常态放行
  [--docx-out <path>]     # 默认同名 .docx
# 产物：<source>.docx + <dir>/images-manifest.txt
```

**check_manual.sh**（Step B 自检）
```bash
bash .claude/skills/user-manual/scripts/check_manual.sh <source.md>
# 跑：缺图校验 + build 冒烟 + 讲人话 + CJK 标点
```

**取图（复用现成脚本，不新写）**
```bash
python3 scripts/fetch_figma.py <url> --image -o images/NN-slug.png        # 单帧
python3 scripts/fetch_figma.py <url> --batch "1:2=01-a.png,3:4=02-b.png"  # 多帧
python3 .claude/skills/prototype/scripts/pre_proto_phone_shots.py <html> -o images/
```

## 自检清单

**手册模式**（`check_manual.sh` 跑完，逐条确认）：

- [ ] 源 md 与 docx 同一份正文，docx 未手改（改 md 重 build）
- [ ] 每张图 `![图：…](images/NN-slug.png)`，alt 以 `图：` 开头、说清哪一步
- [ ] 正式交付零缺图（不带 `--allow-placeholder` build 通过）
- [ ] 标题动词化、第二人称、四段式（前置 / 步骤 / 预期 / 提示与风险）齐
- [ ] 有温度不 AI 味：开场有提问 / 场景钩子、句子短用祈使、结尾有感召收尾（对照 `user-manual-template.md §三`）
- [ ] 多图步骤 / 两端对比 / 二选一用 `:::steps` 表格（表头写步骤语义），单图走文本流
- [ ] 不可逆 / 对外 / 资金操作有 `⚠️ 风险提示`
- [ ] 正文无内部锚点 / 决策号 / 埋点名 / 字段名（`plain-language-gate` 绿）
- [ ] CJK 标点 gate 绿
- [ ] `images-manifest.txt` 已生成，帮助中心发布时按它逐张传图替链接

**营销模式**（逐条确认）：

- [ ] 全篇第三人称陈述，无「你的仓位…读者看到」视角混用
- [ ] 正文无内部迭代版本号（如「社区 3.2」，`plain-language` promo 分流 strict 绿）
- [ ] 场景号（B-1/A-2）只在文末配图索引，不在正文
- [ ] 三渠道分节齐（Banner / 博客 / 更新日志）+ 配图索引表
- [ ] 有温度不 AI 味：博客开场戳痛点 / 提问、句子短、结尾行动召唤有感染力（对照 `user-manual-template.md §三`）
- [ ] 营销词符合中文语境不堆砌（warn 提示自查，非硬拦）
- [ ] CJK 标点 gate 绿
- [ ]（多语言）外文版与主稿卖点/结构/配图一一对应，品牌名全篇统一（Platform C→Platform C），外文 mock 走 native 语感非中译英
- [ ]（有图上文字）On-Image String Map 按面板分组，只映射本次 scope frame，未声称能编辑 Figma

## References 索引

- `references/user-manual-template.md` — 混合式骨架 + 各段写法范例（写源 md 前 Read，**必读**）
- `references/help-center-publish.md` — 帮助中心发布约定：图片上传替链、标题层级、callout 降级（发帮助中心时 Read）
- `references/promo-localization.md` — 营销稿多语言 + 图上文字交付：Figma 只读铁律 / On-Image String Map / promo- 外文版落法 / KOL 口吻中英分档（做 promo- 多语言版或要动 Figma 图上文字时 Read）
