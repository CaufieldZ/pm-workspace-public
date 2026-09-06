---
name: scene-list
description: >
  当用户提到「场景清单」「场景梳理」「梳理一下需求」时触发。新项目 / 复杂链路第一步自动触发，场景边界模糊或需求描述笼统时优先于其他 skill 触发。
type: pipeline
output_format: .md
output_prefix: scene-list-
pipeline_position: 1
depends_on: []
optional_inputs: []
consumed_by: [architecture-diagrams, interaction-map, prototype, prd, cross-check]
owns: [view-划分, 编号, 优先级, 设备, 叙事主线]
forbids: [字段表, 状态全集, 池策略, 埋点, 跳转规则]
scripts:
  render_scene_list.py: "可选 HTML 视觉版 — python3 .claude/skills/scene-list/scripts/render_scene_list.py {项目名}"
  check_scene_list.py: "结构自检（重复编号 / 优先级值 / 设备空）— python3 .claude/skills/scene-list/scripts/check_scene_list.py {scene-list.md} [--strict]"
---

# 场景清单 Skill（Scene List）

## 触发与定位

**做什么**：所有复杂链路的第一步，锁定三件事供下游 skill 复用：
1. **View 划分** — 产品拆为几个独立端 / 视角
2. **场景编号** — 每个场景的唯一编号（确定后不可改动）
3. **优先级** — P0 / P1 / P2 / 后续

**何时触发**：新项目 / 复杂链路第一步 / 场景边界模糊时优先于其他 skill 触发。

**不做**：交互细节（归 interaction-map）/ 行为规格（归 prd）/ 页面结构（归 prototype）。

## 改脚本前 30 秒

> hook 守的是「Read 过本文件」**不看读了多少行**。改 scripts/render_scene_list.py 用 `Read 此文件 limit=80`（§1+§2 即够）。改产出物建议全文。

**Public API（不可改签名）**：
- `python3 render_scene_list.py {项目名}` — 唯一入口，读 `projects/{项目}/scene-list.md`，输出 `projects/{项目}/deliverables/scene-list-{项目}.html`
- `python3 check_scene_list.py {scene-list.md} [--strict]` — 结构自检；hook + 人工自检共用

**会拦你的 hook**：
- `script-syntax-gate` — pyflakes / py_compile
- `cjk-punct` — 全角标点强制（输出 HTML 中文文案）
- `scene-list-gate` — 存 scene-list.md 自动跑 check_scene_list.py（warn 级，重复编号等）

**改完跑啥**：
```bash
python3 .claude/skills/scene-list/scripts/render_scene_list.py {真实项目} && open projects/{真实项目}/deliverables/scene-list-*.html
```

**深入读什么**：完整自检规则 `grep -A 20 "^## 自检清单" SKILL.md`

## 硬规则（FAIL 即拦）

1. **编号锁定**：scene-list.md 确认后编号不可改动；新增场景在末尾追加，禁插入老编号中间
2. **叙事主线唯一源**：scene-list 顶部 `叙事主线：xxx` 一行（≤ 30 字）是 IMAP `parts[].story` 的唯一来源。脱钩 → IMAP build 报错
3. **场景顺序**：按 §5 Step 2.5 叙事主线（叙事型）/ IA 归属（规则系统型）排，**禁按字母序硬排**——A 在 B 前是因为故事先讲 A
4. **项目形态分流硬度**：
   - **叙事型**（用户旅程清晰）：Step 0 痛点提问 + Step 2.5 叙事一句话**强制**
   - **规则系统型**（IA + 数据枚举 + 规则映射，无典型主流程）：Step 0 改问 IA 切分，Step 2.5 叙事主线可填「—」显式跳过
5. **设备列必填**：每个场景标 `📱phone` 或 `🖥web`，下游 IMAP 骨架脚本读此列决定设备壳类型

## 核心输出规范

- **位置**：`projects/{项目名}/scene-list.md`（md 是 source of truth）
- **结构**：顶部叙事主线一句话 → 每个 View 一张表 → 末尾统计
- **两套 canonical schema（按项目形态二选一，`check_scene_list.py` 列名感知不强绑）**：
  - **叙事型**（用户旅程清晰）：`| 编号 | 场景 | 模块 | 设备 | P | 说明 |` — 设备列 📱phone / 🖥web 必填（下游 IMAP 骨架读此列定设备壳），P 列 P0/P1/P2/后续
  - **规则系统型 / 主题索引**（方案型 / 无典型主流程）：`| 编号 | 主题 | 章节/模块 | … | 说明 |` — 无设备 / P / 叙事主线列；顶部首行写 `audit-fast：跳过 scene code 严格匹配`

### 编号规则

| 类型 | 格式 | 示例 | 说明 |
|------|------|------|------|
| 主场景 | 大写字母 | `A` `B` `C` | 独立页面 / 流程入口 |
| 子场景 | 字母-数字 | `B-1` `B-2` | 同一主场景下的子页面 / 子状态 |
| 后台场景 | M-数字 | `M-1` `M-2` | MGT / CMS 后台 |
| 功能前缀 | 缩写-数字 | `F-0` `E-1` | 特殊功能模块（F=Futures, E=Entry 等）|
| 入口子场景 | 字母-数字+字母 | `F-0a` `F-0b` | 同一场景多条独立入口路径 |

**视觉版（HTML，可选）**：`python3 scripts/render_scene_list.py {项目名}` 输出 `deliverables/scene-list-{项目}.html`。renderer 自适应表头，自动识别编号 / 优先级 / 设备 / 触发端 / 响应端等语义列。

## 执行步骤

> 收到新需求 → 先按 CLAUDE.md「收到需求路由」过 PM-GATE 4 风险扫描，再进入 Step 0。

### Step 0：需求发散（新需求 / 模糊需求时执行）

**触发条件**：用户只说了一句话（如「做个活动中心」「优化留存」），或真相源（`lib.truth_source.resolve`：baseline）缺明确目标 / 指标。

**跳过条件**（任一即自动跳过）：
- 真相源（baseline §1 概览）已有完整目标 / 指标 / 场景
- PM 说「直接梳理场景」/「跳过澄清」/「快速模式」
- 已有功能小改动，规模 ≤ 1 个场景
- **规则系统型项目**：问 1 痛点改问「核心 IA 怎么切（按业务线 / 角色 / 页面层级）」，问 2/3 照常

**0.1 确认问题定义**（逐个问，等回答再问下一个，禁合并）：

1. **解决谁的什么痛点？** 一个具体场景，禁「优化体验」
2. **业务目标？** 具体指标，如「提升活动参与率 15%」
3. **上线后用什么数据衡量？** 1-2 个核心指标 + 时间窗口

**0.2 提出 2-3 个实现方向**，每个说明：核心差异 / 涉及范围 / 关键假设 / 明确推荐 + 理由。等 PM 确认进 Step 1。

### Step 1：收集信息

向用户确认：① 产品 / 项目名 ② 涉及哪些端（App / Web / 后台 CMS / 后端 / H5）③ 每端核心页面 / 模块 ④ 跨端交互（如 App 操作 → Web 后台审核）⑤ 优先级分层 P0/P1/P2/后续。

### Step 2：确定 View 划分

按**独立的产品端 / 视角**拆 View：

```
View 1 · [前台名称]（Web + App）
View 2 · [专区名称]（Web + App）— 如果有独立子产品
View 3 · [后台名称]（Web）
```

- 同一端但功能完全独立的模块可拆 View
- 前后台必须分 View
- View 名称要具体，不用「View 1 / 2 / 3」抽象命名

### Step 2.5：写场景叙事顺序（演讲叙事逻辑）

scene-list.md 顶部必须有一句叙事主线，作为 IMAP `parts[].story` 和 PRD 第 2 章主线图的种子（**三处同源**，见 §硬规则 #2）。

**叙事型**：写从入口到收束的主线，例：
> 叙事主线：入口（A）→ 核心承载（B / C）→ 关键转化（D）→ 自己侧管理（E / F）→ 资源位（G）

**规则系统型**：可填「—」显式跳过，但主线位写一句 IA 切分说明，例：
> IA 切分：业务线维度（A-C）+ 活动类型维度（D-E）+ 后台配置（M）

**继承规则**：真相源已有主线（baseline §1 概览主线）→ 一字不改复用；真相源缺则停下来问 PM，禁自编。

### Step 3：编号并输出表格

每个 View 一张表，按 §核心输出规范 §编号规则 填。

### Step 4：汇总统计

表末尾附：

```
**统计**：共 X 个场景 · P0 × N · P1 × N · P2 × N
**涉及端**：App + Web + CMS 后台
```

### Step 5：等用户确认

明确询问：
> 场景清单确认后编号将锁定，后续交互大图 / 原型 / PRD 全部复用。请确认或提出修改。

确认后才进链路下一步。

## 自检清单

> 机械项（重复编号 / 优先级值 / 设备列空）已脚本化 `check_scene_list.py`，存 scene-list.md 时 `scene-list-gate` hook 自动跑（warn 级，不阻断）。以下含脚本未覆盖的人工复核项：

- [ ] 每个 View 有独立表格
- [ ] 编号连续无跳号
- [ ] 每个场景有且仅有一个优先级
- [ ] View 名称具体（不是 View 1 / 2 / 3）
- [ ] 每个场景有设备标识（📱phone / 🖥web）
- [ ] 统计数字 = 实际场景数
- [ ] 顶部有叙事主线（叙事型）/ IA 切分（规则系统型）一句话，且与真相源主线（baseline §1）一字不差
- [ ] 场景顺序符合主线讲述 / IA 归属，未按字母序硬排
