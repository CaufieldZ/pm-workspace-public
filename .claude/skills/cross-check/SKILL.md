---
name: cross-check
description: >
  当 PRD 完成后最终交付前验收，或用户说「拉通检查」「校验一下」「检查一致性」「reader test」时触发。
  7 维结构性校验已脚本化（PRD 写入自动跑），本 skill 保留两件脚本替代不了的事：① 多 ❌ 项的修复优先级编排 ② Reader Testing 评审实践。
type: standalone
output_format: 对话内
output_prefix: none
disallowed-tools: Edit, Write, NotebookEdit
scripts:
  cross-check-auto.sh: "7 维自动对账（场景编号 / 术语 / View / 业务规则 / 跳转目标 / 编号格式 / 必填字段）— bash .claude/skills/cross-check/scripts/cross-check-auto.sh <产品线/项目>"
---

# 跨产出物拉通自检 Skill（Cross Check）

> 7 维机械校验由脚本 + `prd-cross-check-gate` hook 自动兜底。本 SKILL.md 承载脚本替代不了的两件事：修复优先级编排 + Reader Testing。

## 触发与定位

- **自动**：写入 `deliverables/prd-*.md` 时 `prd-cross-check-gate` 自动跑脚本，warn 类不阻断（stderr 报告 + Claude 自修）
- **手动**：PM 中途校验 / 改完后再验时，跑 `bash .claude/skills/cross-check/scripts/cross-check-auto.sh <产品线/项目>`
- **不做**：单文件自检（归各 skill 自己的 `## 自检清单`）

## 改脚本前 30 秒

> hook `skill-load-gate` 守的是「Read 过本文件」**不看读了多少行**。
> 改本 skill `scripts/cross-check-auto.sh`：`Read 此文件 limit=80` 即可。
> 改 PRD / scene-list 等被校验产物：走对应 skill。

**Public API（不可改签名）**：
- `bash cross-check-auto.sh <产品线/项目>` — 7 维校验唯一入口；`prd-cross-check-gate` hook 链调用

**会拦你的 hook**：
- `prd-cross-check-gate` — 写 PRD 后自动跑本 skill 脚本（warn 不阻断）
- `script-syntax-gate` — bash -n（写 .sh 自动跑）

**改完跑啥**：
```bash
bash .claude/skills/cross-check/scripts/cross-check-auto.sh <已知产品线/项目>
```

## 硬规则（FAIL 即拦）

- 本 skill **只读不写**——修复决定权归 PM，绝不直接 Edit / Write 产物文件
- 多 ❌ 项必须按 §执行步骤 修复优先级表**从上到下逐项修**——下游问题可能被上游修复连带消化，跳序改 = 重复劳动
- Reader Testing 走 prd「交付前冷读」工序，**必须派干净上下文子代理**（不在同 session 自跑）——已读上下文会脑补，测不出盲点
- 校验粒度精确到行号 / 编号，禁说「大致一致 / 整体没问题」
- 最低触发条件：scene-list.md + ≥ 1 个 pipeline 产出物，缺则报「校验素材不足」

## 核心输出规范

- **形态**：对话内回复（不写文件）
- **结构**：① 7 维脚本结果（pass / warn / fail 计数）+ ② 修复优先级排序的 ❌ 项清单 + ③ Reader Testing 报告（如已跑）
- **粒度**：每条 ❌ 给「文件名:行号 + 原文片段 + 修法 + 改哪个文件」四件套，不给整段诊断

## 执行步骤

### Step 1：跑脚本拿 7 维结果

```bash
bash .claude/skills/cross-check/scripts/cross-check-auto.sh <产品线/项目>
```

脚本输出 7 维 pass / warn / fail。warn 不阻断，fail 必须修。

### Step 2：按修复优先级编排

脚本只报错不教修。多 ❌ 项按下表排序，**从上到下逐项修，改完一项重跑一次**——下游问题可能由上游修复连带消失。

| 序 | 维度 | 修法 | 改哪个文件 |
|---|---|---|---|
| 1 | 编号格式错误（2.6 / 7） | 改不规则 ID 为 `[A-Z]-[0-9]+` | scene-list.md |
| 2 | 场景编号缺失（2.1 / 5）| 补 scene-list 缺号 或 删下游孤儿引用 | scene-list.md / 下游产出物 |
| 3 | View 划分不一致（2.2）| 对齐 View 数量到 scene-list | imap / PRD 章节 |
| 4 | 术语不一致（2.3） | 以真相源术语表为权威（baseline `# 2. 术语词典` / campaign 变体 `## 5. 术语表`），下游统一 | 下游产出物 |
| 5 | 跳转目标不存在（2.4 / 5）| 补目标 scene 或删跳转 | 引用方 |
| 6 | 业务规则 Rule ID 漂移（2.4） | 以真相源主表为准，PRD §6 对齐（campaign 变体 §6 用 Rule ID；产品线 baseline 用具名锚点，此维对产品线 baseline N/A） | PRD §6 |
| 7 | 必填字段缺失（2.7） | 按字段补 | 对应文件 |

> 优先级 1-3 是**结构问题**（不修下游全坏），4-7 是**文案问题**（局部可控）。

### Step 3：Reader Testing（PRD 评审 / 交付前 → 调 prd「交付前冷读」工序）

> **写文档的人永远有默认假设**——7 维校验只能验「自己和自己一致」，Reader Testing 验「陌生人能不能读懂」。脚本无法替代。这套手艺已被 prd skill **算法化 + 固化成可复现工序**，cross-check 不再复述机制，终验时直接调用。

**何时跑**：PRD 即将评审 / 交付研发 / 推 Confluence 前，或用户说「做一次 reader test」。

跑 prd skill 的 **「交付前冷读」Step**（`.claude/skills/prd/SKILL.md`）：
```bash
python3 .claude/skills/prd/scripts/cold_read.py --prepare <prd.md> [--targets 3.1,4.1,5.1]
```
脚本打包 context 文件 + 7 类盲区探针 prompt + `cold-read-{date}.md` 盲点清单模板 → 派**干净上下文子代理**（Agent 工具，硬约束：同 session 会脑补）逐 target 跑 → 回填盲点清单 → 逐条 triage。7 类盲区权威定义见 `../prd/references/prd-scene-templates.md` §4.6。

**产出**：盲点清单（`cold-read-{date}.md`）作为本工序产物；cross-check 报告末尾附一句汇总——「冷读已发现 N / 已补 M / 留版本 K」。

## 自检清单

- [ ] 脚本 7 维结果完整列出，fail / warn 计数明确
- [ ] 多 ❌ 项已按修复优先级表排序（不是按报错出现顺序）
- [ ] 每条 ❌ 给了「文件名:行号 + 原文 + 修法 + 改哪个文件」四件套
- [ ] 没动产物文件（只读不写）
- [ ] Reader Testing 跑了的话报告附在末尾

## 注意事项

- 本 skill 只承载脚本替代不了的两件事；7 维机械校验全在 `cross-check-auto.sh`，不在 SKILL.md 复述
- cross-check 是 PRD 主流程链路终点（scene-list → imap → prototype → prd → cross-check），不退役
