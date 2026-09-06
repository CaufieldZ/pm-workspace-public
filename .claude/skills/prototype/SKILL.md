---
name: prototype
description: >
  当用户提到「原型」「可交互原型」「prototype」时触发。PRD / IMAP 完成后可转为可交互版本。
type: pipeline
output_format: .html
output_prefix: proto-
pipeline_position: 4
depends_on: [scene-list]
optional_inputs: [interaction-map]
consumed_by: [prd]
owns: [状态全集, 交互细节, CRUD流转, Tab切换]
forbids: [字段表权威定义, 池策略权威定义, 埋点权威定义]
scripts:
  check_paradigm.py: "Step 0 范式门 — python3 .claude/skills/prototype/scripts/check_paradigm.py {项目名}"
  build_proto_skeleton.py: "Step 2 单步生成 — from build_proto_skeleton import generate"
  audit_against_baseline.py: "Step 3 标杆对照 — python3 .claude/skills/prototype/scripts/audit_against_baseline.py <html> [--baseline <baseline.html>]"
  pre_proto_phone_shots.py: "Step 2 前 IMAP 硬看 — python3 .claude/skills/prototype/scripts/pre_proto_phone_shots.py <imap.html> -o <out_dir>"
  check_proto.sh: "Step 3 综合自检（结构 + 文案 + 页面可达性）— bash .claude/skills/prototype/scripts/check_proto.sh <html> [<scene-list.md>]"
  check_page_fns_shell.py: "page_fns 设备壳越界检测（prototype-shell-gate 调用）— python3 .claude/skills/prototype/scripts/check_page_fns_shell.py <file.py>..."
  check_proto_split.py: "src/scenes 分场景拆分门（prototype-split-gate 调用）— python3 .claude/skills/prototype/scripts/check_proto_split.py <html>..."
  check_proto_repro.py: "共享场景库产线的原型可复现性（audit cat24 + proto-drift-warn hook 调用）— python3 .claude/skills/prototype/scripts/check_proto_repro.py [产线名] [--strict]。逐版本重建到 tmp 与已交付字节比对，不碰已交付产物"
  brand_assets.py: "品牌 Logo 注入 — from brand_assets import brand_logo_html; project['logo_html'] = brand_logo_html()"
  spot_annot.py: "演示点位标注库（import 复用）— from spot_annot import SPOT_CSS, SPOT_JS"
---

# 可交互原型 Skill（Interactive Prototype）

## 触发与定位

**做什么**：根据 scene-list / IMAP 生成可交互 HTML 原型（前台 App 深色 + Web 前台 + 后台 CMS 浅色三档），数据驱动 CRUD + 抽屉 / 弹窗 / Tab 切换齐备。

**一端一文件**：涉及多端（App / Web 前台 / 后台 任意 ≥ 2）时，**每端产一个独立 HTML**（`-app` / `-web` / `-mgt` 后缀），由同一个 orchestrator 循环调 `generate_single` 出多个文件。禁止把多端合并进一个 HTML 用顶栏 view 切换——单端单文件后导航天然全局 scope，page id 不跨端、不撞车。

**何时触发**：用户说「原型 / 可交互原型 / prototype」；scene-list 或 IMAP 完成后转可交互版本。

**不做**：PRD 行为规格（归 prd）/ 架构方案（归 architecture-diagrams）/ 静态展示页（用 IMAP 即可）。

**承载状态全集**：IMAP ann-card 出现 `→ 原型「{view}-{page}」状态全集` 锚点时，该页面必须出 ≥ 锚点列举的所有 state-chip。`check_proto.sh` 比对 IMAP 锚点 ↔ state-chip 文案，缺失 FAIL。

## 改脚本前 30 秒

> hook 守的是「Read 过本文件」**不看读了多少行**。改 scripts/*.py / *.sh 用 `Read 此文件 limit=80`（§1+§2 即够）。改产出物建议全文。

**Public API（不可改签名）**：
- `from build_proto_skeleton import generate_single` — `generate_single(project, view, page_fns, crud_js, output_path)`：单端单文件（**新项目多端默认走这个**，每端一文件，无顶栏）。**web-front 端注意**：骨架 `.p-nav` sticky `top:52px`（多端 gnav 高度）会压正文，需项目 CSS 覆盖 `.web-front > .p-nav{top:0}`
- `from build_proto_skeleton import generate` — `generate(project, views, page_fns, crud_js, output_path)`：多 view gnav 合并单文件（**仅存量 archive rebuild**，新项目勿用）
- `python3 check_paradigm.py {项目名}` — Step 0 范式门
- `python3 pre_proto_phone_shots.py <imap.html> -o <out_dir>` — Step 2 前 IMAP 硬看截图
- `python3 audit_against_baseline.py <html> --baseline <baseline.html>` — Step 3 标杆对照
- `bash check_proto.sh <html> [<scene-list.md>]` — Step 3 综合自检
- `python3 check_page_fns_shell.py <file.py>...` — page_fns 设备壳越界检测（hook 调用）
- `build_proto_v{N}.py --end X`（项目 orchestrator）：`--end` 只决定迭代端，但全量重建所有端 HTML；改单端后需同步重拍全端截图，否则其他端 freshness stale
- `screenshot_proto.py`（项目侧，读 `registry.shot_setup` + `extra_shots`）— web 端原型截图走它，**禁用通用 `screenshot_for_prd.py --proto`**（含多场景切换的页面会停在默认态）

**会拦你的 hook**：
- `script-syntax-gate` / `cjk-punct`
- `plain-language-gate` — proto-*.html 文案讲人话（禁裸编号 / 决策号）
- `ui-annotation-gate` — 渲染壳内禁开发注解（`（此处占位）`/`注：`/`TODO` 会被开发误读为真实文案）；build 后 Bash 路径拦截
- `prototype-shell-gate` — page_fns 不生成设备壳
- `prototype-split-gate` — proto-*.html 产出时校验 src/scenes 已拆分（找不到即 FAIL）
- `prototype-audit` — 产出后自动跑 audit_against_baseline 摘要
- `skill-load-gate` — 改 `proto-*.html` 必先 Read 本 SKILL.md
- `deliverable-source-gate` — 禁直接 Edit/Write proto HTML，必须走 build

**改完跑啥**：
```bash
python3 .claude/skills/prototype/scripts/build_proto_skeleton.py  # demo 自跑
bash .claude/skills/prototype/scripts/check_proto.sh deliverables/proto-*.html
```

**深入读什么**：完整 views/page_fns 结构 `grep -A 40 "^## API 速查" SKILL.md`；自检规则 `grep -A 30 "^## 自检清单" SKILL.md`；组件 HTML `Read references/crypto-app-vocabulary.md` + `Read assets/prototype-templates.html`。

## 硬规则（FAIL 即拦）

### 反凭印象三红线

1. **凭印象画 = 红线**：任何 Crypto APP 元素（feed 卡片 / trader 卡 / 战绩组件 / 订阅 CTA / 抽屉 / 状态栏 / 底部导航）必须先查 `references/crypto-app-vocabulary.md` 对应词条 + Figma 真品 PNG（`assets/figma-anchors/`）+ imap references（`biz-trading.md` / `biz-social.md` / `biz-livestream.md` / `components-core.md`）。三源任一缺失 → 必须先补再画。Figma frame 名不可信，下图肉眼核对再映射场景编号
2. **IMAP 硬看强制**：上游有 IMAP 时，Step 2 前必须用 `pre_proto_phone_shots.py` 单独截每张 phone（每张独立文件），Read 多模态确认元素细节后再骨架。详见 `references/prototype-source-discipline.md § B`
3. **标杆对照强制**：Step 3 必须跑 `audit_against_baseline.py` 对照范式标杆 HTML，关键组件计数 + Fill 视觉铁律 + 反 AI slop 六禁全过才允许声明完成

### 数据驱动 CRUD

4. **数据驱动**：JS 数组存数据 → render 函数渲染列表 → 弹窗按索引读 → 保存 = 写回 + 重渲染 + 关弹窗
5. **禁止**列表写死 HTML 而弹窗用另一套数据
6. 新增弹出空表单 + 默认值；编辑弹出对应数据；两者共用同一弹窗组件
7. 增删改全联动，统计实时更新，删除二次确认

### 设备壳边界

8. **page_fns 不生成设备壳**：禁在 page_fns 函数里生成 `.app-mock` / `.layout` / `.p-nav` / sidebar 等设备壳元素——这些由 build 骨架统一管理。`prototype-shell-gate` hook 拦截
9. **build 模式唯一**：改 HTML = 改 page_fns 函数体 + 重跑 build，禁 Edit/Write 直改 HTML（hook 阻断）
   - **单端单文件 = 导航天然全局**：`generate_single` 每端只产一个 view，无 gnav 顶栏，`goPage` / `openDrawer` 在整份文档全局查找（JS `|| document` fallback），page id 不跨端、不撞 `getElementById`。无需任何 scope 技巧
   - **app 端 .p-nav 隐藏**：`.p-nav` 硬编码在 `build_proto_skeleton.py`（skill 文件不可改），app 端在 `crud.py` 补 `.app-mock > .p-nav{display:none}`，由各 scene 自行接管顶导

### 每页都得点得到

10. **每个 page 必须有入口**：`view.pages` 里声明的页面，必须能从入口页顺着 `goPage` 点到（顶栏 logo / Tab 栏 / 列表卡片 / 按钮任一）。声明了页面却没入口 = 评审只能改代码才能看到 = 等于没做。多端拆分尤其易漏：某页只在另一端有入口，本端就成孤儿。`goPage` 目标也必须是**本端真实存在**的 `data-page`，指向别端的 page id 点了直接黑屏。build 时 `_warn_unreachable` 提示，`check_proto.sh` §页面可达性 FAIL 拦截

### src/scenes 分场景拆分（强制）

11. **必须拆 src/scenes**：每个原型一律拆 `projects/{项目}/scripts/src/scenes/{end}_{page}.py` 一文件一页面（≤ 300 行），由 `build_proto_v{N}.py` orchestrator import 收口成 `page_fns`。**禁止把 page_fns 内联在 orchestrator 单文件里**（不分简单 / 大产物，无条件）。`prototype-split-gate` hook 在 proto-*.html 产出时校验，找不到任何 `src/scenes/*.py` 即 FAIL。结构见 `.claude/runbooks/html-build-split.md §二`

### 文案讲人话

12. **正文禁 PM 内部代号**：原型 HTML 文案给用户看，禁正文出现决策 N / 场景编号 A-1 / context 内部条目。规则源头 `.claude/runbooks/human-voice-rules.md`，`plain-language-gate` hook 拦截
13. **屏内只放真实文案**：原型整份就是 UI，禁在渲染壳（`.app-mock` / `.web-front` / `.layout`）内写开发注解——`（此处占位）` / `（灰条占位）` / `（动态加载）` / `注：` / `TODO` 这类括注会被开发误读为真实产品文案。注解一律删掉。`ui-annotation-gate` hook 在 build 后拦截。留删判据：使用者在本页做决定需要知道的才留，系统内部机制 / 版本语言 / 算法口径归 PRD

### 共享场景库的装配纪律（建了 src/registry.py 就必吃）

> 总纲：**共享层只放与版本无关的东西。任何与本轮 scope 有关的（装配清单 / 导航映射 / 校验范围 / 页序）必须由 orchestrator 注入，不写死在共享层。**
> 这是 `html-build-split.md §二`「素材工厂须信息中性」从素材层到装配层的延伸。

14. **按 scope 装配，禁无条件全拼**：`build()` 拼 CSS / JS 时必须按本端、本轮入选页选包，禁 `js = A + B + C + D` 一把梭。判据：产物里不得出现本轮 scope 之外的端 / 页的代码。**违反后果是跨版本污染** —— 前台改一处 OBS 选币逻辑，会串进只含 CMS 页的另一个版本产物。
15. **registry 自洽性校验随 scope 收敛**：`check_links()` 只校验本轮入选集合内的场景与两端都在集合内的边，禁全局校验。全局校验会让「改了 A 端跳转忘同步 registry」阻断**所有**版本的 build，且报错指着与本轮毫不相干的场景 —— 这是最难定位的一类假故障。
16. **跨版本共享清单禁位置索引**：侧栏 / 导航这类共享清单，场景侧一律存**名字**（`sidebar_name`）由 build 查位置，禁存整数下标。下标在清单中间插一项时整体错位且不报错；按名查找插项自动跟随，名字对不上直接抛错。
17. **停放区（暂不启用的代码）必须保持语法合法**：注释掉的功能段落若丢了 `//` 前缀，恢复时会一次性炸掉整个 `<script>` 块（所有交互失效）。停放前跑一次 `node --check` 验证「拼回主块」不报错。

### 视觉：用组件层，不自写 CSS

18. **通用视觉件不自己发明**。先跑判据决定走哪条，**禁在一条产线里混用两套词汇**：
    ```bash
    ls projects/{产品线}/scripts/src/crud.py 2>/dev/null && grep -coE '^\.[a-z]{2,4}-' projects/{产品线}/scripts/src/crud.py
    ```
    - **无 crud.py，或自有前缀类 < 20（新产线 / 新建 crud.py）**：`config.py` 的 project 必须加 `'css_packs': ['crypto-dark']`，卡片 / 标签 / Tab / 数字排版 / 浮层 / sheet / 按钮 / 列表行一律写 `cx-` class，crud.py 只留本业务特有样式。清单 `grep '^\.cx-' assets/crypto-dark.css`，交互函数 `cxTab / cxPill / cxRow / cxSheet / cxToggle / cxToast`
    - **存量产线已自成体系（如 livestream 607 个自有前缀类）**：保持产线既有词汇，**不引入 `cx-`**；照产线现有同类组件复制结构。此时 `references/visual-rework-atlas.md` 仍逐条适用 —— 它约束的是数字排版 / 素材 / 圆角尺度 / 悬浮 / 浮层的**做法**，与用哪套 class 名无关
19. **零 emoji 素材**：图标 / 头像 / logo / 走势图 / 状态栏走 `scripts/lib/icons.py`（`ic` / `avatar_monogram` / `logo_svg`），禁用 emoji 顶替。骨架顶导默认的 `🔥` 用 `brand_assets.brand_logo_html()` 换掉。`audit_against_baseline.py` V2 项检测壳内 emoji

### 标注面板（Anno）

20. **page_fns 支持 anno dict**：给页面挂说明卡时 value 返回 `{'page': html, 'anno': [{'n','p','title','text','tx','ty'}]}` 替代纯 str，骨架自动渲染边缘 Pin + 折线 + Popover（纯 str 向后兼容）。坐标系 / `anno_debug` 调试层 / 内容禁止项见 `references/annotation-layers.md`
21. **anno 内容禁止**：`ann-text` / `title` 内禁裸场景编号（`A-1`）/ 决策号 / 开发注解，字段表 / 池策略参数 / 埋点事件名同样禁写（归 PRD）。`plain-language-gate` 拦
22. **演示点位标注**：要高亮「本轮改动落点」时用 `spot_annot`（屏内只放光圈 + 序号，文字走壳外图例；金 = 改接 / 蓝 = 新增）。用法见 `references/annotation-layers.md`

### 业务组件复用

23. **业务组件**：交易卡片 / Feed 列表 / 直播间 / CMS 后台表格 / 表单 必须从 `references/prototype-components.md` 或对应 imap biz-*.md 复制 HTML 结构，禁自行设计样式

## 核心输出规范

- **位置**：原型是 **delta-scoped 产物，不做 living base 版**（上线后线上 app 即 UI 真相，活原型是与现实重复的维护黑洞），scoped 到本轮变更场景，随 delta 包落 `projects/{产品线}/deliverables/{季度}/{版本}/`（版本 = delta 版本），随 delta 整包归 `archive/{季度}/`。
- **命名**：单端项目 `proto-{产品线}-{版本}.html`；多端项目每端一文件，加端后缀 `proto-{产品线}-{版本}-app.html` / `-web.html` / `-mgt.html`。
- **生成脚本**：与产物同目录 delta 包内 `scripts/build_proto_{版本}.py`；产品线若已建共享场景库（`projects/{产品线}/scripts/src/registry.py` 存在），脚本落项目根 `projects/{产品线}/scripts/`，本轮只写选单，产出物仍 delta-scoped。`check_proto_split.py` 两种落点都认
- **结构**：单文件 HTML / CSS / JS 全内联（字体 CDN 除外）；CSS / JS 由 `build_proto_skeleton.py` 通过 `open().read()` 自动拼接

### device + theme 三档设备壳

prototype 覆盖三档（views 字段 `device` + `theme` 决定壳）：

| 范式 | device | theme | 壳 | 用途 |
|------|--------|-------|----|----|
| 对客 App | `phone` | `dark` | `.app-mock` 375×812 | 深色系合法主题，涨绿 `#0ECB81` / 跌红 `#F6465D` / 金 `#FCD535` |
| 对客 Web | `web-front` | `dark` | `.web-front` 全宽 + `.p-nav` + `.wf-footer` | 深色底 `#0B0E11` + 品牌蓝 accent `#007FFF` |
| 内部后台 Web | 忽略 | `light` | `.layout` + sidebar | MGT 浅色 `#F5F6FA` + 品牌蓝 + 深蓝 sidebar `#001529`；可叠 `.theme-cd` 切换到 Claude Design 暖近黑 `#1F1F1E` + `#D97757` |

**多端 = 多文件**：项目涉及 ≥ 2 端时，每端按上表选壳，各产一个独立文件（`generate_single` 一端一调用）。同一 orchestrator 循环出 `-app` / `-web` / `-mgt`，不合并。`generate`（gnav 顶栏合并单文件）仅供 activity-center 等存量 archive rebuild。

字体栈：`prototype.css` 已补 `-apple-system,'SF Pro Text'` 作英文 fallback（CJK 仍以 Noto Sans SC 优先），不需要在 crud.py 重覆写。

### page_fns vs build 骨架边界

| 提供方 | 内容 |
|--------|------|
| **build 骨架** | 完整设备壳（`.app-mock` / `.layout` / `.p-nav` / sidebar）+ 抽屉 / 弹窗容器壳（`.p-drawer` / `.modal-bg`）+ ✕ 按钮 + 基础 JS 交互（View 切换 / 页面跳转 / 抽屉 / 弹窗开关）+ `<script>` 末尾拼入 `crud_js` 字符串 |
| **page_fns** | 页面内 UI 元素（卡片 / 列表 / 表单 / 抽屉 / 弹窗内容） |

**page_fns key**：
| key | 内容 | 注意 |
|----------|------|------|
| `(view_id, page_id)` | 页面内部 UI 元素 | **不包含设备壳** |
| `(view_id, 'drawer')` | 抽屉面板内容 | 不包含抽屉容器壳 |
| `(view_id, 'modal')` | 弹窗内容区 | 不包含弹窗容器壳 |
| `(view_id, 'footer')` | web-front view 自定义 footer | 可选，省略用默认 |

**骨架原型的通用截图红利**：build 骨架约定的 `.gnav-view-section[id]`（view）× `.p-page#page-{id}`（page）结构，让 `screenshot_for_prd.py --proto <proto.html>` 能自动遍历批量截图喂 PRD。`generate_single` 单端文件保留单个 `.gnav-view-section.gnav-active` 节点（无顶栏），截图脚本零改动遍历该端所有 page；多端逐文件各跑一次。手写原型无此结构，需 per-project 截图脚本。

**品牌 Logo 注入**：`generate_single` phone / web 壳顶导默认渲染 `🔥` emoji。需替换为真实品牌 Logo 时，在 orchestrator 里用 `brand_assets.py` 给 project dict 加 `logo_html` 字段，骨架自动替换所有顶导位：

```python
from brand_assets import brand_logo_html
project = {'name': 'Demo 直播', 'version': '2.3',
           'logo_html': brand_logo_html(size=22)}  # 骨架自动注入顶导
```

`brand_assets.py` 同时提供 `brand_logo_html_mono(size, color)` 单色版。Logo SVG path data 从 Figma 官方文件用 `fetch_figma.py --format svg` 导出（不截图，直接拿 `<path d>`）。

**App 端接管整条顶导**（如需头像 + 搜索框 + 操作图标替代默认 p-nav）：在 crud CSS 补 `.app-mock > .p-nav{display:none}`，page_fns 自行渲染 `.app-nav` 替代。

**改某页文案 / 场景结构后必须重拍该页全部自定义态截图**（如弹窗 TRTC/OBS 两态、直播间直播 / 回放两态）：`.freshness.json` manifest 按整页 `.p-page` DOM 子树 hash 判定，漏拍同页任一状态都会连带报 stale。同页多态截图在 `registry.py` 的 `Scene.extra_shots` 声明（每条 `{'suffix': 'replay', 'setup': 'switchXxx(true);'}`，输出 `proto-{end}-{end}-{page}-{suffix}.png`），screenshot 脚本通用循环遍历，不在脚本里硬编码 `if` 块。

### 美学通用底线（所有范式必吃）

引 `.claude/skills/_shared/claude-design/anti-ai-slop.md`：

- 反 AI slop 六禁：全屏渐变 / emoji 装饰标题 / accent border / SVG 画人 / 烂大街字体作 CJK / 每卡都带 icon
- 字号比：标题 ≥ 正文 2.5 倍；line-height CJK display 1.25-1.35 / 正文 1.6-1.8
- 颜色克制：≤ 1 主 + 1 辅 + 1 强调 + 灰阶
- 字重三级：900 display / 700 标题 / CTA、400 正文（禁全文只 700）
- CSS 变量源头唯一：tokens.css 拼入，禁手抄 :root 整块

**补齐顺序 = 内容密度 → 动效 → 质感 → 微交互 → 层次**。空屏是评审第一眼最大的减分项：交易 / 直播页面一屏要承载真实字段全集（持仓卡八个字段同屏），字段名照抄真品、数据用接近真实的示例。**本条覆盖 anti-ai-slop 的「留白 ≥ 40%」——那条适用于 ppt / 架构图，不适用于对客交易页面**，密度按真品走。

Step 3 `audit_against_baseline.py` grep 验证以上，违规即 fail。

## 执行步骤

> 通用规则（强制规则 / 快速模式 / Fill 质量）见 `.claude/runbooks/html-pipeline.md`。本节为 prototype 补充。

### Step 0：范式选择门 + 竞品截图收集（强制）

prototype 触发后**禁止直接跑 generate**，必须先完成本步。

**0.1 范式推断**：
```bash
python3 .claude/skills/prototype/scripts/check_paradigm.py {项目名}
```

脚本读真相源（`lib.truth_source.resolve`：baseline）涉及端 + scene-list.md，推断端构成，给出推荐 + 标杆 HTML 路径 + 必读 references 清单。模型必须向用户**口头确认**范式正确，确认后才进 Step 2。

| 端构成 | 范式 | 产出 | 标杆 |
|--------|------|------|------|
| 纯 App + 多场景（≥ 5）| 单 phone + scene chips | 1 文件 | V8 / community v3 |
| 纯 App + 简单流（≤ 3）| 单 phone 无 nav | 1 文件 | 小型项目 |
| 纯 Web 后台 / CMS | 单 view + sidebar | 1 文件 | activity-center mgt-view |
| 多端（App / Web 前台 / 后台 任意 ≥ 2）| 多端拆分 (`generate_single`) | **每端 1 文件**（`-app`/`-web`/`-mgt`）| 各端按 device 壳分别对标 |

脚本推断不出（端类型混合 / 场景数模糊）→ 模型向用户问，禁自行假设。多端时**禁合并进单文件用顶栏切换**——这是过去返修的根因。

**0.2 竞品截图 / Figma 真品收集**（Crypto 认知 ground truth）：

范式确认后主动问用户：
> 这个项目对标哪些真品？请给 1-3 个来源：① Figma 真品链接（行业头部 项目优先 — 直接 fetch_figma 入档最高权威） ② 竞品截图（Binance / OKX / Bitget / Gate / 行业头部 实际页面） ③ 已有 IMAP（上游存在则直接用）

收集动作：
- Figma 链接 → `python3 scripts/fetch_figma.py <url> --batch ... --out-dir .claude/skills/prototype/assets/figma-anchors/`（持久 anchor，下次复用）
- 竞品截图 → 存 `projects/{项目}/inputs/competitors/`
- 模型 Read 多模态读每张，写「视觉提炼」存 `projects/{项目}/inputs/anchors/visual-extracts.md`（配色 / 字号层级 / 关键组件 / 交互模式）。**禁污染真相源静态章**——artifact-conventions §四「静态章四不」禁 UI 视觉

**素材权威性排序**（冲突时按此裁决）：① PM 直接给的矢量 / 源文件（源码注释标了「PM 给的矢量」的最高，别拿事后补的真机截图覆盖它）② Figma 真品 ③ 竞品 / 线上真机截图。

**动手画版式前，`inputs/` 里的截图逐张 Read 完**，页面结构 / Tab 名 / 字段名一律照抄不推测、不精简——凭印象画出来的假 Tab 假字段，返修时要整屏重排。交易页组件尤其逐字段核对（真品合约持仓卡含保证金三列 + 强平价 + 已实现盈亏条 + 四按钮）；缺实拍截图就向用户要，不要先画了再说。

**只有用户明确说「不需要 / 直接做 / 已有 IMAP 看就够」才允许跳过**。

**0.3 上游分支判定**：详见 `references/prototype-source-discipline.md § A0`。有 IMAP 走硬看流程，无 IMAP 走双 anchor 替代流程。

### Step 1：回读 + View 结构确定

并行 Read scene-list.md + 真相源（baseline）+ IMAP（如有）+ `references/crypto-app-vocabulary.md` + `references/baseline-pattern-card.md` + `references/prototype-source-discipline.md`。

向用户确认：涉及几端（App / Web 前台 / 后台）/ 每端设备类型 / 每端包含哪些页面。多端 = 多文件，每端独立确认。

**设备类型判定**：
- App 端（iOS / Android）→ `device: "phone"`
- Web 端（浏览器全宽）→ `device: "web-front"`（新项目）或省略（legacy）
- CMS 管理台 → `theme: "light"`（自带侧边栏布局）
- 不确定就问用户

### Step 2：写 orchestrator + src/scenes（强制拆分）

**禁止把 page_fns 内联在 orchestrator 单文件里**（硬规则 11，不分简单 / 大产物）。固定结构：

```
projects/{项目}/scripts/
  build_proto_v{N}.py        # orchestrator（≤ 150 行，只 import scenes/ + 收 page_fns + 循环调 generate_single）
  src/
    config.py                # project / ends（每端一个 view dict + 输出路径）
                             # project = {"name":..., "version":..., "css_packs": ["crypto-dark"]}
    helpers.py               # 跨场景复用 HTML 片段（可选）
    scenes/
      __init__.py
      {end}_{page}.py        # 一文件一页面 ≤ 300 行；def page_{end}_{page}(): return '''...'''
```

orchestrator 范式（**多端循环 generate_single，每端一文件**）：

```python
import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/prototype/scripts'))
sys.path.insert(0, os.path.dirname(__file__))  # 让 src 包可 import
from build_proto_skeleton import generate_single
from src.config import project, ends   # ends = [{"view": {...单端 view...}, "out": "...-app.html"}, ...]
from src.scenes.app_center import page_app_center
from src.scenes.web_create import page_web_create

page_fns = {
    ('app', 'center'): page_app_center,
    ('web', 'create'): page_web_create,
}
crud_js = """const items = [...]; function render() {...} ..."""

for end in ends:
    view = end["view"]
    sub = {k: v for k, v in page_fns.items() if k[0] == view["id"]}
    generate_single(project, view, sub, crud_js, end["out"])
```

单端项目则 `ends` 只一条。CSS / JS 不进源码树，由 `build_proto_skeleton.py` 通过 `open().read()` 自动内联。

**节奏 = 样板页优先**（非快速模式）。分两段，禁一次性把所有页铺完：

1. **样板页**：先只做信息最密的那一页（通常是列表 / 详情 / 工作台，不是空状态页），做到可交付水准 —— 用 `cx-` 组件、真实字段全集、真实文案、`lib/icons.py` 矢量素材。build 后跑 Step 3 的**视觉自评**并把截图给用户确认。
2. **其余页**：以样板页为准复用它的 class、信息密度、字号层级、间距。前台复杂页面 1 个一批，后台简单页面 2 个一批，每批往 src/scenes 加文件 + orchestrator 注册 + build 验证 + 报告进度。

先立标准再铺量，返修从「每页各调 N 轮」收敛成「样板页调 N 轮 + 其余页对齐一轮」。

**Step 2 不读模板** — 骨架脚本只需下方 API 速查表，CSS / JS 由 `open().read()` 自动拼接。**Step 2 填充开始前 Read** `assets/prototype-templates.html`，按需读 `references/prototype-components.md`：

- 前台 App 页面 → 只读 `## A. 前台深色组件`
- 后台管理页面 → 只读 `## B. 管理台浅色组件` + `## D. 数据驱动 CRUD 模式`
- 弹窗 / Toast / 底部弹出 → 只读 `## C. 通用交互组件`

```bash
grep -n "^## " .claude/skills/prototype/references/prototype-components.md  # 定位章节
sed -n '{起始},{结束}p' .claude/skills/prototype/references/prototype-components.md
```

### Step 3：自检与交付

视觉自评 + 自检三件套 + Playwright click 全 pass 才视为通过。详见 § 自检清单。

**视觉自评（脚本替代不了，样板页做完与最终交付各跑一次）**：截关键页 2-3 张 PNG，**Read 自己的截图与标杆 PNG 并排看**（标杆：`assets/figma-anchors/livestream-v2/*.png`、`projects/{community,livestream}/deliverables/*/assets/*.png`），逐项写「我的 / 标杆 / 差在哪」再修：

内容密度（空屏是最大减分项）· 数字排版（等宽 / 数值与单位分层）· 素材（有无 emoji 顶替图标头像）· 圆角与胶囊 · 卡片分层（无边框 vs hairline）· 浮层底色 · 选中态 · 文案是否真实业务语言

脚本查得到的项在 `audit_against_baseline.py` V 组，查不到的（密度 / 层级 / 真实感）只能靠这一步看图。

### Step 4：版本与归档

- 原型随 delta 包命名 / 归档，**版本 = delta 版本**，无独立 `v{N}` 快照阶梯：本轮 delta 上线后整季度 / 版本文件夹（含原型）归 `archive/{季度}/`。
- 改 page_fns / src/scenes 后重跑 build 覆盖本版原型；历史版本随旧 delta 包已在 archive，git blame + git log 提供变更溯源。
- 无 patch 脚本。

**共享场景库的安全前提：同一时刻只有一个在途版本。** 上一条「历史版本已在 archive」隐含这个假设 —— 前序版本都归档了，改共享 `src/` 才伤不到它们。**多个 delta 版本并行在途（都还在 `deliverables/` 未归档）时该假设失效**：改共享层会同时改掉其他在途版本的产物，且不报错、不留 diff（下次谁重建谁才发现）。

并行在途时：

- 动 `src/` 前先跑 `python3 .claude/skills/prototype/scripts/check_proto_repro.py {产线}` 拿到基线，改完再跑一次看多出哪些漂移
- 漂移是有意的（该版本也要这个改动）→ 重建那些版本并说明；无意的 → 说明共享面划错了，按 §硬规则 14 收窄装配范围
- `proto-drift-warn` hook 在 build 后按 src 指纹秒级提示，精确结论以 `check_proto_repro.py` 为准

## API 速查

### generate 签名

```python
# 单端单文件（新项目多端默认，每端调一次）
generate_single(project: dict, view: dict, page_fns: dict, crud_js: str, output_path: str)
# 多 view gnav 合并单文件（仅存量 archive rebuild）
generate(project: dict, views: list, page_fns: dict, crud_js: str, output_path: str)
```

### views 结构

```python
{
    "id": "user-view",         # DOM id
    "name": "用户端",           # Tab 显示名
    "icon": ic('phone', 14),   # Tab icon（仅 gnav 合并存量用；走 lib.icons，不用 emoji）
    "theme": "dark",           # "dark" | "light"（light 强制后台壳 .layout + sidebar）
    "device": "phone",         # "phone" 对客 App | "web-front" 对客 web | 省略 = legacy Web 全宽
    "nav_name": "产品名",      # dark 主题 p-nav 显示名（可选）
    "pages": [
        {"id": "main", "name": "首页"},
        {"id": "detail", "name": "详情"},
    ],
    # device="web-front" 可选字段：
    "nav_items": ["买币", "行情", "交易", "合约", "赚币"],
    # light 主题字段：
    "sidebar_group": "功能管理",
    "sidebar": [{"icon": "📋", "name": "列表管理"}],
}
```

### 组件层与素材库（不自己发明）

```python
# CSS/JS 组件层（走哪条看硬规则 18 的判据）：class 清单 grep '^\.cx-' assets/crypto-dark.css
project = {"name": "...", "version": "...", "css_packs": ["crypto-dark"],
           "logo_html": logo_svg(20), "status_html": ic("signal", 12),  # 壳上的 emoji 位可覆盖
           "nav_right_html": ic("wallet", 13)}

# 矢量素材：跨 skill 共享库，emoji 一概不用（sys.path 加 {_ROOT}/scripts 后 import）
from lib.icons import ic, avatar_monogram, logo_svg, _TONE
ic('chart', 16, '#848E9C')      # 线性图标（名字传错会抛错并列出全部可用名）
avatar_monogram('Edward', 34)   # 字母头像，6 色盘按名字 hash 分色
_TONE['up'] / _TONE['down']     # 涨跌色
```

业务特有素材（行情封面 / 迷你走势线）建项目 `src/icons.py` 复用 lib 的 token 再补；**建之前先 `ls` 项目 `src/` 看有没有现成的**。SVG 内部 id 必须自增生成，多处复用同一字符串会撞 `clipPath` id 导致后者空白。

### 交互函数（build 骨架内置）

| 函数 | 用途 |
|------|------|
| `switchGlobalView(idx)` | 切换全局 View（仅 gnav 合并存量用；单端文件无顶栏不调用）|
| `switchTab(el, prefix, tab)` | Tab 切换 |
| `goPage(name)` | 页面跳转 |
| `toggleDropdown(e)` | 下拉开关 |
| `openDrawer() / closeDrawer()` | 抽屉开关 |
| `switchChip(el, prefix, tab)` | Chip 筛选 |
| `switchDevice(webId, appId, btns, idx)` | Web/App 切换 |
| `swPage(el, idx)` | 后台侧栏切换 |

**crud_js**：后台 CRUD 数据驱动 JS（数据数组 + render + openEdit + saveItem + deleteItem + 初始 renderList 调用），整段作为字符串传入 generate，build 时拼到 `<script>` 末尾。

## 自检清单（Step 3 执行）

> 通用条目（编号一致、脚本保存、FILL 残留、术语一致）见 `.claude/runbooks/artifact-conventions.md §三 上下文防丢`。

**踩坑速查**（交付前过一遍）：
- [ ] 一级页面展示的摘要 = 编辑弹窗数据（数据驱动根治）
- [ ] 渲染壳内无开发注解（`（此处占位）`/`注：`/`TODO`），屏内只放真实文案
- [ ] 同一概念没有两种叫法
- [ ] 多个编辑按钮传了索引参数，弹窗内容正确对应
- [ ] 保存 = 写数据 + render + 关弹窗三步
- [ ] 两个文件的同一场景数据一致

**专项条目**：
- [ ] 每个 page 都能从入口页点到，`goPage` 目标都是本端存在的 page（`check_proto.sh` §页面可达性）
- [ ] 所有 View 可通过全局导航切换
- [ ] 前台深色 / 后台浅色；App 端 375×812 手机壳内不溢出
- [ ] 抽屉在手机壳内底部上推，不脱出手机框
- [ ] 后台 CRUD 数据驱动：列表数据 = 弹窗数据 = render 输出
- [ ] 弹窗 / 抽屉有遮罩 + ✕ + 遮罩点击关闭

### 强制验证三件套（不可跳过）

```bash
# 1) 综合自检（结构 + 页面可达性 + 描述当前态四禁 warn）
bash .claude/skills/prototype/scripts/check_proto.sh projects/{项目}/deliverables/XXX.html

# 2) 标杆对照（必备组件 + Fill 视觉铁律 E1-E6 + 反 AI slop 六禁 + 字重三级）
python3 .claude/skills/prototype/scripts/audit_against_baseline.py \
  projects/{项目}/deliverables/XXX.html \
  --baseline {check_paradigm 输出的标杆 HTML 路径}
```

### Playwright click 强制验证（替换原「浏览器验证」软建议）

单纯 screenshot self-check **不算**通过，必须 playwright assertion 验证 DOM 状态：

```bash
python3 scripts/with_server.py --server "python3 -m http.server 5173" --port 5173 -- \
  python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    page = p.chromium.launch(headless=True).new_page()
    page.goto('http://localhost:5173/projects/{项目}/deliverables/XXX.html')
    page.wait_for_load_state('networkidle')
    # ... 写下方最小 click 集 assertions
"
```

**最小 click 集**（含相关组件的场景全跑过，无 console error / 视觉无错位才算通过）：
1. 每个 scene chip 点击 → `.scr.on` 切换正确（`page.locator('.scr.on').count() == 1`）
2. 含订阅 CTA 的场景：click 后文案变「已订阅」+ 宽度不变（保留 flex:1）+ 铃铛出现
3. 含铃铛的场景：click → 开/关两态图标切换（`ic('bell')` ↔ `ic('bell-off')`，不用 emoji）+ toast 文案对应
4. 含 toggle 的场景：click → on/off 状态切换 + 跨场景同 toggle 联动
5. 含抽屉 / sheet 的场景：scrim click + ✕ click 都能关
6. 含 TAB 的场景：每个 TAB 切换 .on 类正确

screenshot 用于：① Step 3 视觉自评（与标杆并排 Read）② 视觉 bug 复现 ③ 标杆对照 zoom 局部 ④ 最终交付截图。**不能拿 screenshot 替代 Playwright 断言**——截图看不出 DOM 状态对不对。

三件套全过 + Playwright click 全 pass 才视为自检通过 → 才允许声明完成。任一 fail → 必须修，禁止跳过。

## References 索引

### 必读

| 文件 | 触发条件 |
|------|---------|
| `.claude/runbooks/html-pipeline.md` | HTML pipeline 通用规则（生成模式 / 内容质量 / Fill 视觉铁律 E1-E6 / 美学硬底线）|
| `references/crypto-app-vocabulary.md` | 真品组件 + 路由表 + Figma anchors（凭印象红线源头）|
| `references/annotation-layers.md` | 需要给原型挂说明标注 / 演示点位光圈时 |
| `references/visual-rework-atlas.md` | 视觉失分图鉴（症状 / 反例 / 正例）——Step 2 样板页做完与 Step 3 自评逐项过 |
| `references/baseline-pattern-card.md` | 3 标杆 × 5 场景对照（Step 0 范式确认）|
| `references/prototype-source-discipline.md` | 有 / 无 IMAP 双流程纪律（Step 0.3 / Step 2）|

### 按需读

| 文件 | 触发条件 |
|------|---------|
| `assets/crypto-dark.css` | 组件 class 清单（`grep '^\.cx-'` 即可，不必全文 Read）|
| `assets/prototype-templates.html` | Step 2 填充开始前 Read |
| `references/prototype-components.md` | 按页面类型读对应 section（## A / B / C / D）|
| `interaction-map/references/components-core.md` | 空态 / Tab 栏 / 列表页 / 表单等通用组件（共享单一信息源，去重后 prototype-components.md A11 / C3 已改路由指引）|
| `assets/figma-anchors/*.png` | 凭印象红线触发时 Read 多模态 |

### 美学与主题

- 产出前 grep 决策速查：`grep -A 20 "决策速查" .claude/skills/_shared/claude-design/anti-ai-slop.md`
- Claude Design opt-in 主题：CSS 中 `.theme-cd` 作用域已定义（覆盖 Arco 浅色变量为 CD 深色），需切换时手动在 HTML body 加 `class="theme-cd"`。**App 移动端不应用**此 theme

## 注意事项

1. 组件不绑定业务——ref 是通用骨架，按具体产品填充内容；ref 与组件层都没有的场景件（直播间 / K 线 / 聊天区）按 CSS Token 自行构建
2. `.app-mock` 设备框为 iPhone 15 Pro 数值（圆角 48px / 状态栏 54px / Dynamic Island 124×36 / Home Indicator 140×5）

