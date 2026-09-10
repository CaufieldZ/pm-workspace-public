---
name: code-review
description: >
  当用户说「code review / 审代码 / 过一遍代码 / 提交前审一下 / 看看我这次改的」时触发。
  改完 scripts/ · .claude/hooks/ · .claude/skills/*/scripts/ · projects/*/scripts/ 想在 commit 前收口亦触发。
  「审计 / 诊断」不触发（走 workspace-audit）；PRD 产出物一致性不触发（走 cross-check）。
type: tool
output_format: 对话内
output_prefix: none
scripts:
  scan_changes.py: "Phase 1 机械层聚合 — python3 .claude/skills/code-review/scripts/scan_changes.py [--staged | --range <rev> | <file>...]"
---

# 增量代码 Review Skill（Code Review）

> 工区已有的机械层（`script-syntax-gate` / `audit.sh 19,22` / pre-commit / pytest）只查语法、跨平台、secret 这些形式项。本 skill 承载机械层查不到的语义判断：`SCRIPTS_WRITING.md §四` 反模式、`HOOK_WRITING.md` 纪律、跨模块消费者与测试覆盖。

## 触发与定位

- **做什么**：按 `git diff` 审增量代码，两阶段——Phase 1 脚本聚合机械层结论 + 消费者反查 + 覆盖缺口，Phase 2 模型读 diff 做语义 review。
- **审哪些**：`scripts/**` · `.claude/hooks/**` · `.claude/skills/*/scripts/**` · `projects/*/scripts/**`
- **不审**：`hub/`（分发包走 aihub-package + `_vet_local.sh`）· `.md` / `.html` 产出物（归各产出物 skill）
- **不做**：全仓结构体检（走 workspace-audit）· PRD 跨产出物拉通（走 cross-check）· 落盘修复（见 §硬规则 R1）

## 改脚本前 30 秒

> `skill-load-gate`（pre-writeedit-guard）守的是「Read 过本文件」**不看读了多少行**。
> 改本 skill `scripts/scan_changes.py`：`Read 此文件 limit=80` 即可（前两节就够）。

**Public API（不可改签名 · 改前看调用方）**：
- `python3 scan_changes.py [--staged | --range <rev> | <file>...] [--json-out <path>]` — 唯一入口；Step 1 调用
- `bucket_files(paths)` / `route_specs(buckets)` / `extract_changed_symbols(diff)` — 纯函数；`scripts/tests/test_scan_changes.py` 直接 import

**会拦你的 hook**：
- `script-syntax-gate` — ruff F（除 F401）/ `bash -n`，写 `.py` / `.sh` 自动跑
- `skill-load-gate` — 改本 skill scripts 前必先 Read 本文件

**改完跑啥**：
```bash
python3 -m pytest scripts/tests/test_scan_changes.py -q
python3 .claude/skills/code-review/scripts/scan_changes.py --range HEAD~1   # 自跑通即可
```

**深入读什么**（按需 grep 定位）：完整参数 `grep -A 30 "^## API 速查" SKILL.md`；维度分工 `Read references/review-dimensions.md`

## 硬规则（FAIL 即拦）

违反一条 = 本轮 review 视为未交付。

**R1 · 全程 review-only，禁改被审代码与工区文件。** 修复等用户明确说「修」之后再做。这条**纯靠自觉、没有机械兜底**——review 轮里手一滑改了被审文件，报告与代码状态就对不上、整份报告作废。**禁止用 Bash 绕**：`sed -i`、`cat > file`、`tee`、`python3 -c "open(...,'w')"`、`>` 重定向写代码文件，一律禁止。

合理化对照表（想到左边就是在违规）：

| 心里冒出的念头 | 事实 |
|---|---|
| 「这个 typo 一行就改完了」 | 一行也是改。记进 findings 表，用户点头再动 |
| 「都审出来了不修等于白审」 | review 的交付物是报告，不是 diff |
| 「用户肯定希望我顺手修」 | 用户已在建 skill 时选定 review-only。别替他改主意 |
| 「先修了再在报告里说明」 | 报告与代码状态对不上，比不修更糟 |

**R2 · 未跑 `scan_changes.py` 不得开审。** 直接 Read 文件凭印象点评违反 CLAUDE.md「脚本优先（强制）」，且会漏掉消费者反查与覆盖缺口。

**R3 · 每条 finding 必须带 `文件:行号` + 规范锚点**（如 `SCRIPTS_WRITING.md §三-D`、`HOOK_WRITING.md §三-A`）。给不出锚点的「感觉不太好 / 建议优化一下」不进报告。

**R4 · 机械 gate 已出结论的维度只汇总不重述。** ruff F / `bash -n` / shellcheck / audit 19 / pytest 的结果进第 2 块一行一条，不在 findings 表里重讲一遍。

**R5 · 只审 diff 命中的文件。** 不顺手审没改的老代码、不提「顺便重构一下」。对应 CLAUDE.md「只动该动的」与 `pm-methodology.md §五`「先确认现有基建已覆盖什么再报盲区，别把已有 gate 当缺口」。

**R6 · 🔴 级 finding 上报前必须实跑证实。** 「会崩 / 静默错数据」结论禁止单凭读代码推断——用最小输入跑一次复现（只读调用，或 `tempfile` 造一次性 fixture 用后即删；系统临时目录里的 fixture 不属于 R1 禁的被审 / 工区文件）。复现不了 → 降 🟡 并在问题栏标「未复现」+ 写明推断依据。锚点：`SCRIPTS_WRITING.md §四`「凭内联测试 / 表象反推 bug」。

Red Flags（命中即停）：报告里出现没有行号的条目 · 出现 `hub/` 或 `.md` 产出物的 finding · findings 数超过改动文件数 3 倍（多半在审老代码）· 🔴 条目说不出怎么复现。

## 核心输出规范

对话内报告由四块组成，按此顺序：

**① 范围声明**（一行）：审了 N 个文件 / 什么 diff 范围 / 跳过了什么及原因。

**② 机械层结论**：一行一项，`✅ ruff F（含 F401）零命中` / `❌ pytest 2 failed`，不展开细节。

**③ findings 表**，🔴 在前：

| 严重度 | 位置 | 问题 | 规范锚点 | 建议改法 |
|---|---|---|---|---|
| 🔴 | `scripts/foo.py:42` | 一句话说清 | `SCRIPTS_WRITING.md §三-D` | 一句话说清 |

严重度口径（沿用工区既有三级，不引 P0-P3）：

- **🔴** 会崩 / 静默错数据 / 破坏跨模块调用（须实跑证实，R6；复现不了降 🟡）
- **🟡** 违反 SCRIPTS_WRITING 硬约束 · 可测性缺失 · 口径分叉
- **🟢** 建议

**④ 收尾动作清单**：本轮该跑但还没跑的命令，可直接复制（`gen_scripts_readme.py` / `mypy scripts/lib/` / 补 `test_*.py` / `test-hooks.sh`）。

零 finding 时第 ③ 块写「无」，不凑数、不为凑满表格降级报 🟢。

## 执行步骤

### Step 0：定范围

优先级：用户点名的文件 > `--staged`（有暂存内容时）> `--range HEAD~1`。范围定完在报告第 ① 块声明，不闷头开审。

### Step 1：跑 Phase 1 脚本

```bash
python3 .claude/skills/code-review/scripts/scan_changes.py --staged
```

脚本输出四段：变更清单 + 规范路由 / 机械层结果 / 消费者反查 / 覆盖缺口。

### Step 2：按路由表加载规范

读脚本第 ① 段给出的规范清单（每个 bucket 指向哪份文件），加 `references/review-dimensions.md`。不在路由表里的文件不读规范也不审。

### Step 3：逐文件语义 review

只读 diff hunk + 判断所必需的上下文，**不全文 Read 大文件**（CLAUDE.md 大文件纪律：> 500 行先 `wc -l` + Grep 定位 + offset/limit）。

审的维度以 `references/review-dimensions.md` 为准——那张表只列机械层空白项，逐项对着 diff 过。脚本第 ③ ④ 段给的消费者与覆盖缺口逐条判断是真漏还是无关。

### Step 4：出报告

按 §核心输出规范四块输出。报告出完即停，不循环复查、不追加「要不要我帮你修」之外的动作。

## API 速查

```bash
# 审暂存区（默认场景，commit 前收口）
python3 .claude/skills/code-review/scripts/scan_changes.py --staged

# 审最近 N 个 commit
python3 .claude/skills/code-review/scripts/scan_changes.py --range HEAD~3

# 审指定文件（未提交的工作区改动）
python3 .claude/skills/code-review/scripts/scan_changes.py scripts/dashboard.py scripts/lib/repo.py

# 结构化输出（供二次消费）
python3 .claude/skills/code-review/scripts/scan_changes.py --staged --json-out -
```

| 参数 | 含义 |
|---|---|
| `--staged` | 审 `git diff --cached`；无暂存内容时脚本自动回落 `HEAD~1` 并在输出里声明 |
| `--range <rev>` | 审 `git diff <rev>`，如 `HEAD~3` / `main` |
| `<file>...` | 位置参数，审这些文件的工作区 diff；与 `--staged` / `--range` 互斥 |
| `--json-out <path\|->` | 四段结果写 JSON，`-` 走 stdout |
| `--no-mechanical` | 跳过第 ② 段机械层（audit / pytest 较慢时用），其余段照跑 |

退出码恒 `0`——本脚本是报告器，不进 hook 链，不做阻断（阻断已由 pre-commit 承担）。

## 自检清单

- [ ] 跑过 `scan_changes.py`，范围与用户意图一致
- [ ] 报告四块齐全且按序（范围声明 / 机械层 / findings / 收尾动作）
- [ ] 每条 finding 有 `文件:行号` + 规范锚点
- [ ] 🔴 级 finding 已实跑复现（复现不了的已降 🟡 并标「未复现」）
- [ ] 没有 `hub/` 或 `.md` 产出物的 finding（超范围）
- [ ] 没有针对未改动老代码的 finding
- [ ] 机械层结论只汇总一行，没在 findings 表里重述
- [ ] 全程零文件写入（R1 无机械兜底，靠自觉；未用 Bash 绕）
- [ ] 脚本第 ③ 段消费者、第 ④ 段覆盖缺口每条都给了判断（真漏 / 无关），没有整段略过

## References 索引

**必读**（Step 2）：

- `.claude/skills/code-review/references/review-dimensions.md` — 维度分工表：哪些归机械 gate、哪些要人眼过、锚点在哪

**按需读**（按脚本第 ① 段路由，命中哪个读哪个）：

| 改动落在 | 读 |
|---|---|
| `scripts/*.py` · `scripts/*.sh` · `scripts/lib/*.py` | `scripts/SCRIPTS_WRITING.md` |
| `.claude/hooks/**` | `.claude/hooks/HOOK_WRITING-quickref.md`（不够再读全量 `HOOK_WRITING.md`）|
| `.claude/skills/*/scripts/**` | `scripts/SCRIPTS_WRITING.md` + 该 skill 的 `SKILL.md` |
| `projects/*/scripts/**` | 对应产出物 skill 的 `SKILL.md`（产物生成器规则归对应 skill，不套 SCRIPTS_WRITING）|

## 失败恢复

| 症状 | 处理 |
|---|---|
| `--staged` 报「暂存区为空」 | 脚本已自动回落 `HEAD~1` 并在输出声明；要审工作区未暂存改动就直接传文件名 |
| diff 范围内零代码文件（全是 `.md` / `.html`） | 直说「本次改动不在 code-review 范围」+ 指向对应 skill，不硬凑 findings |
| 机械层某项超时 / 报错 | 该项在第 ② 块标 `⚠️ 未跑通` + 原因，继续跑语义 review；禁 `2>/dev/null` 吞掉后当通过 |
| 消费者反查命中几十条（改了高扇出 lib） | 只把「签名 / 语义变了因而真受影响」的列进 findings，其余在第 ③ 块折叠成一行计数 |
| review 轮里手滑改了被审文件 | R1 靠自觉、没有机械兜底。报告与代码状态已对不上 → 该文件 `git checkout` 还原后重审，别在「报告没提、但代码已经改了」的状态下交付 |
| 用户看完说「修吧」 | 本轮把 findings 报完即停；用户回复后直接改。禁让用户手贴代码代劳，禁用 Bash 绕 |
