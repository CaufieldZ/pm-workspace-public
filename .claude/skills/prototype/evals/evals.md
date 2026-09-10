# Prototype Skill Eval 集

## 任务 1：状态全集锚点对照（承载状态全集）

**输入**：给一段 IMAP ann-card 写 `→ 原型「community-feed」状态全集`，但 prototype 该页缺 state-chip。
**判 rubric**：
- [ ] prototype 页面出 ≥ 锚点列举的所有 state-chip
- [ ] state-chip 文案与 IMAP 锚点一致

## 任务 2：一端一文件（硬规则）

**输入**：给一个多端项目要求用顶栏 view 切换合并进一个 HTML。
**判 rubric**：
- [ ] 每端产独立 HTML（`-app` / `-web` / `-mgt` 后缀）
- [ ] 不用顶栏 view 切换合并多端

## 任务 3：page_fns 设备壳越界（prototype-shell-gate）

**输入**：给一段 page_fns 里生成 `.p-nav` / `.layout` 骨架元素的代码。
**判 rubric**：
- [ ] page_fns 不生成设备壳（`.app-mock` / `.layout` / `.p-nav` / sidebar）
- [ ] 设备壳由 build 骨架统一管理

## 任务 4：src/scenes 拆分

**输入**：给一个内联 page_fns 的 prototype orchestrator。
**判 rubric**：
- [ ] 拆成 `src/scenes/{end}_{page}.py` 一文件一页面
- [ ] orchestrator 只 import + 收口

## 任务 5：零 emoji 素材（硬规则 19）

**输入**：要求出一页 App 深色原型，页面含头像、状态栏、若干功能图标、一条走势线。
**判 rubric**：
- [ ] 图标 / 头像 / logo / 走势图走 `scripts/lib/icons.py`（`ic` / `avatar_monogram` / `logo_svg`）
- [ ] 渲染壳内无 emoji 顶替素材（`audit_against_baseline.py` V2 项）
- [ ] 头像不是灰色单色剪影

## 任务 6：用组件层不自写 CSS（硬规则 18）

**输入**：要求出一页含卡片、涨跌标签、Tab、底部弹层、价格数字的 App 深色页面。
**判 rubric**：
- [ ] `config.py` 的 project 带 `'css_packs': ['crypto-dark']`
- [ ] 卡片 / 标签 / Tab / sheet / 数字用 `cx-` class，未在 crud.py 重写等效 CSS
- [ ] 价格数字带 `tabular-nums`（`.cx-num`），单位与数值分层
- [ ] 卡片无 `border:1px solid`，hover 走 translateY + shadow（Web 端）

## 任务 7：样板页优先节奏（Step 2）

**输入**：给一个含 8 个页面的场景清单，要求出原型。
**判 rubric**：
- [ ] 先只做 1 页样板页做到可交付水准，不一次性铺完 8 页
- [ ] 样板页选的是信息最密的页面，不是空状态页
- [ ] 样板页 build 后做视觉自评（截图 + 对照标杆）并交用户确认后才继续
- [ ] 其余页复用样板页的 class / 密度 / 字号层级
