---
name: workspace-audit
description: >
  「审计 / 诊断 / 跑一遍审计」触发。Phase 1 脚本自动 + Phase 2 模型推理，支持按类别选执行。
type: tool
output_format: .md
output_prefix: none
depends_on: []
optional_inputs: []
consumed_by: []
disallowed-tools: Edit, Write, NotebookEdit
scripts:
  audit.sh: "全局审计 — bash .claude/skills/workspace-audit/scripts/audit.sh [类别号]"
  rules-review.py: "季度规则瘦身 review — python3 .claude/skills/workspace-audit/scripts/rules-review.py --model <ver>"
---

# Workspace Audit

## 触发与定位

**做什么**：全局诊断工具。两阶段审计：**Phase 1 脚本硬检查**（audit.sh，零推理纯 bash）+ **Phase 2 模型软检查**（语义推理的矛盾分析、安全扫描、瘦身建议）。

**何时触发**：用户说「审计 / 诊断 / 跑一遍审计」。

**不做**：业务决策（仅给出问题清单 + 严重度，不替 PM 拍板）/ 自动修复（输出报告即停）。

## 改脚本前 30 秒

> hook 守的是「Read 过本文件」**不看读了多少行**。改 scripts/audit.sh / rules-review.py 用 `Read 此文件 limit=80`（§1+§2 即够）。

**Public API（不可改签名）**：
- `bash audit.sh [类别号]` — 全局审计入口（类别号逗号分隔）
- `python3 rules-review.py --model <ver> [--dry-run]` — 季度规则瘦身 review

**会拦你的 hook**：
- `script-syntax-gate` — bash -n / pyflakes
- `skill-load-gate` — 改 `.claude/skills/workspace-audit/scripts/*` 必先 Read 本 SKILL.md
- `pre-commit` 钩 audit.sh 默认类别（`1,2,3,4,7,12,13,14,15,16,17,19,20,21,23,25`），audit.sh exit code 非 0 阻 commit

**改完跑啥**：
```bash
bash .claude/skills/workspace-audit/scripts/audit.sh 1,2,3,4,7,12,13,14,15,16,17,19,20,21,23,25  # 跑 pre-commit 覆盖类别
bash .claude/skills/workspace-audit/scripts/audit.sh 18                              # 跑场景编号悬空（warn-only，不进 pre-commit）
bash .claude/skills/workspace-audit/scripts/audit.sh 19                              # 跑跨平台兼容 lint
```

**深入读什么**：完整类别清单 `grep -A 5 "^## 执行步骤" SKILL.md`；新增 cat 时改 audit.sh 对应 case 段；SKILL.md 章节标准 `Read .claude/runbooks/skill-conventions.md`。

## 执行步骤

### Step 0：让用户选择审计范围

展示以下菜单，用户选哪些跑哪些。默认全选。

请选择审计范围（输入编号，多选用逗号分隔，直接回车=全部执行）：

**Phase 1 — 脚本自动检查（audit.sh）**

1. 文件完整性 — SKILL.md 存在性、frontmatter、references 引用、配置文件
2. 数值与格式一致 — 设备尺寸、配色 token、命名前缀、字体规范、字体栈顺序
3. 依赖与链路 — depends_on 闭环、循环依赖、链路覆盖、孤立 skill
4. 规则冲突 — 章节引用扫描、触发词重叠、术语一致
5. Token 预算 — 规则层总量、体积棘轮（CLAUDE.md + runbooks 逐文件上限，破限红灯，pre-commit 直调 check_rule_volume.py）、单 skill 成本、全链路 session 预算、臃肿文件
6. 产出物一致性 — 场景编号、术语、文件命名（按 scene-list.md 发现活跃项目）
7. SKILL_TABLE 一致性 — workspace-context.md 表格 ↔ frontmatter 比对
12. Scripts 字段存在性 — 各 SKILL.md frontmatter `scripts:` 声明的脚本必须真实存在
13. scripts/lib import 链路 — 共享模块能被 skill 脚本正确 import
14. 三件套纯洁性 — scripts/ 仅可执行代码 · references/ 仅 .md · assets/ 不含 .md（按 Anthropic Progressive Disclosure 规范）
15. Hooks 健康度 — `.claude/hooks/`（含 lib/）语法检查、BSD sed 兼容性、引用脚本存在性、settings.json 注册一致性、pre-commit trigger 覆盖
16. SKILL.md 内部结构合规 — 行数上限、必需章节、禁用同义词章节名（红灯，进 pre-commit）
17. 内链断链 — CLAUDE.md / SKILL.md / references / runbooks / hooks 里 `.md` 相对链接目标存在性（红灯，进 pre-commit）
18. 场景编号悬空 — baseline 引用 scene-list 未定义的场景编号（字母族收敛自动滤决议号 + 项目级 `.audit-ignore-scene` 豁免，黄灯 warn-only）
19. 跨平台兼容 — mktemp 后缀模板 / Python open() 缺 encoding / sed -i 裸用 / GNU-only coreutils 无 BSD fallback（macOS BSD ↔ Linux GNU ↔ Windows，红灯，进 pre-commit）
20. 计数对账 — 门面文档（README / README-EN / workspace-context）手写的「N 个 skill/hook/runbook」+ badge 与文件系统真实数比对，漂移即红灯（进 pre-commit）
21. hub 分发物健康 — zip 新鲜度（源码比 zip 新 = 忘重打）/ zip 缺失 / OWUI 部署态漂移 + INDEX.md drift + 各包按形态的必备文件齐全（红灯，进 pre-commit）
22. 脚本健康度 — py 语法/未定义名（ruff E9/F821）+ sh 双版本 bash -n + shellcheck error 级（按需跑，不进 pre-commit 默认）
23. 阈值分布报告 — thresholds.yaml 键与消费者覆盖 + 产物阈值实测分布（信息类，不判红绿）
24. 原型可复现性 — 有共享场景库（`scripts/src/registry.py`）的产线逐版本重建到 tmp 与已交付字节比对，漂移报黄（黄灯 warn-only，重建耗时约 10s，不进 pre-commit）
25. Gate 健康度 — usage.jsonl 反查 gate 名册：死 gate（日志有名注册表无）+ 死豁免（GHOST_GATES 登记却零事件）红灯；零触发 / skip 失衡 / 无解释 skip 黄灯（进 pre-commit）

**Phase 2 — 模型推理检查**

8. 规则层矛盾深度扫描 — 逐条比对 CLAUDE.md / pm-methodology.md / artifact-conventions.md / 各 SKILL.md 中的规则是否冲突
9. 安全 & 泄露扫描 — API key / token / password 模式、.gitignore 覆盖度、大文件
10. 工程健壮性 — hook 机制、依赖声明、Python 包管理
11. 瘦身与优化建议 — >10K token Skill 的按需加载机会、重复内容提取

### Step 1：Phase 1 执行（脚本硬检查）

所有硬检查逻辑在 `scripts/audit.sh` 中实现（执行类脚本，模型无需读取源码）。

```bash
bash .claude/skills/workspace-audit/scripts/audit.sh <类别编号逗号分隔>
```

示例：
- 全部执行：`bash .claude/skills/workspace-audit/scripts/audit.sh 1,2,3,4,5,6,7,12,13,14,15,16,17,18,19,20,21,22,23,24,25`
- 只跑 pre-commit 覆盖的：`bash .claude/skills/workspace-audit/scripts/audit.sh 1,2,3,4,7,12,13,14,15,16,17,19,20,21,23,25`
- 只跑 SKILL.md 结构合规：`bash .claude/skills/workspace-audit/scripts/audit.sh 16`（章节顺序 / 命名 / 行数 / 同义词禁用，参考 skill-conventions.md §SKILL.md 内部章节标准）

### Step 2：Phase 2 执行（模型语义推理）

逐项用 bash 命令取数据，模型做语义推理判断。每项给出 ✅/⚠️/❌ + 证据（文件名：行号）。

### 8. 规则层矛盾深度扫描

**8.1 字体规范一致性**

```bash
grep -rn "font-family" .claude/skills/*/assets/*.css 2>/dev/null
```

- 逐个比较每个 CSS 文件的 font-family 声明与 tokens.css `@audit-spec` 规范
- 特别检查：正文栈 vs 等宽栈是否混写；PPT JetBrains Mono 白名单
- **editorial 产出物豁免**：`scene-list` / `architecture-diagrams` 这类叙事 / 阅读型产出物允许正文栈挂 `'Noto Serif SC'` 做主字或 fallback（例：`'Noto Sans SC', 'Noto Serif SC', 'Poppins', ...` 或 arch 的 `var(--arch-serif-cn),'Noto Sans SC',system-ui,sans-serif`），增强中文阅读感，符合 Claude Design 系 display serif 风格。非 editorial 类（imap / prototype / ppt / flowchart）正文栈必须是 `'Noto Sans SC','Poppins'`，不得掺 Serif
- **同文件字体一致性**：同一 CSS 内多处 `font-family` 声明必须用同一套英文 fallback（如 :44 和 :558 一处 `'Inter'` 一处 `'Poppins'` 算真 bug，通常是焕新时遗漏）

**8.2 色板一致性**

```bash
grep -rn "#0B0E11\|#0ECB81\|#F6465D\|#00B42A\|#F53F3F" .claude/skills/*/assets/*.css 2>/dev/null
```

- 同一语义色（success/danger）在不同文件中 hex 是否一致
- 深色板 vs 浅色板是否有混用（prototype 双色系已白名单）

**8.3 设备尺寸一致性**

```bash
grep -rn "375\|812\|width.*px" .claude/skills/*/SKILL.md 2>/dev/null
```

- App 壳、Web 框的宽高在各 SKILL.md 中是否与 tokens.css `@audit-spec` 一致

**8.4 HTML 行数阈值一致性**

```bash
grep -rnE ">\s*200\s*行|200\s*行.*HTML|HTML.*200\s*行|脚本生成" CLAUDE.md .claude/runbooks/ .claude/skills/*/SKILL.md 2>/dev/null
```

- "> 200 行必须脚本" 在各处表述是否统一
- 收紧正则避免误命中 "tab 80-200 行 / < 200 段" 等非 HTML 行数表达

**8.5 执行优先级描述一致性**

```bash
grep -rn "优先级\|Layer\|层级" CLAUDE.md .claude/runbooks/ README.md workspace-context.md 2>/dev/null
```

- 各文件对「谁覆盖谁」的表述是否一致

### 9. 安全 & 泄露扫描

**9.1 明文密钥扫描**

```bash
grep -rn "sk-\|api[_-]key\|token.*=\|password\|secret\|Bearer " . --include='*.md' --include='*.json' --include='*.js' --include='*.py' --include='*.sh' -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null
```

- 判断匹配项是否为真正的明文密钥
- .mcp.json 是否在 .gitignore 中

**9.2 双层脱敏覆盖度**

本工作区双层脱敏，判断"是否会泄露"时必须同时查：

- **Layer 1 `.gitignore`** — 不进 private git。覆盖真 secret / 本机配置：`.mcp.json / .env / node_modules/ / .claude/session-state.md / projects/ / references/ / deliverables/`
- **Layer 2 `sync_public.sh` `--exclude` 列表** — 进 private git 但不同步到 public repo。覆盖个人偏好 / 战略主线 / 项目内容：`workspace-context.md / .claude/runbooks/（含对话风格 human-voice-rules.md §⓪）/ .claude/skills/data-report/ 等`（战略层 `projects/product-lines.md` 由 `projects/` 整体排除自动覆盖）

```bash
# 看 Layer 2 实际覆盖
grep -- '--exclude' sync_public.sh
```

判定规则：文件在 Layer 1 **或** Layer 2 任一层即为"已脱敏"，不算泄露。只有既不在 .gitignore 又不在 sync_public.sh exclude 列表里的敏感内容才报 🔴。

**9.3 git tracked 大文件**

```bash
git ls-files | xargs ls -la 2>/dev/null | sort -k5 -n -r | head -20
```

- 有无 >500KB 的文件不合理地进入 git tracked

### 10. 工程健壮性

**10.1 防腐化 hook**

```bash
cat .githooks/pre-commit
```

- hook 是否调用 audit.sh 且覆盖范围正确（当前应为 1,2,3,4,7,12,13,14,15,16,17,19,20,21,23,25）
- 退出码机制是否正确

**10.2 依赖声明**

```bash
cat package.json
cat requirements.txt
```

- 依赖列表是否只含必要项
- Python 实际使用的第三方包是否都在 requirements.txt 中

### 11. 瘦身与优化建议

对 Phase 1 Cat5 报告中 >10K token 的 Skill：
- references/ 中是否有文件可改为 Step B 按需加载
- 有无重复内容可提取为 quickref
- 有无过时注释/示例可删除

### Step 3：输出报告

## 核心输出规范

审计完成后，输出两份：

**1. 对话内报告（精简版）**

```
# Workspace Audit Report
审计时间：{日期}
审计范围：类别 {用户选的编号}

## 总览
| 类别 | 结果 | 问题数 |
|------|------|--------|
| 1. 文件完整性 | ✅/❌ | N |
| ... |

**总计**：N/12 通过，M 个问题

## 需要修复的问题（按严重度排序）
1. 🔴 {严重问题} — {文件:行号}
2. 🟡 {中等问题} — {文件:行号}
3. 🟢 {建议优化} — {文件:行号}
```

**2. 文件报告（完整版）**，含所有检查项的详细输出

保存到 `deliverables/audit-{日期}.md`。
- 如果在某个项目上下文中运行，保存到 `projects/{项目名}/deliverables/audit-{日期}.md`
- 如果不在项目上下文中，保存到仓库根目录 `deliverables/audit-{日期}.md`

## 注意事项

### 季度规则瘦身 review（独立流程，不进默认 Cat）

**触发**：每 3-6 月一次 / 重大模型升级后 / 感觉规则层让模型变笨时。源自 [Anthropic 大代码库实践](https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start) §"Actively maintaining CLAUDE.md as model intelligence evolves" — 补偿旧模型局限的规则在新模型下可能成 overhead。

**用法**：

```bash
python3 .claude/skills/workspace-audit/scripts/rules-review.py --model sonnet-4.7
# 或 dry-run 只看统计不写文件
python3 .claude/skills/workspace-audit/scripts/rules-review.py --model sonnet-4.7 --dry-run
```

输出 `deliverables/rules-review-{date}.md`：规则清单 + hook 触发统计（30/60/90d）+ 空白「候选评估」列。

**人工 review 流程**：

1. 先看「模型补丁」分类（补偿旧模型的规则，新模型可能不需要）
2. 其次看 90d 0 触发 hook 对应规则（数据稀疏 ≠ 该删，但是问题信号）
3. 逐条填「候选评估」列：保留 / 简化 / 删除 + 理由
4. 单独 commit 收尾，commit message 引用本 review 文件

**为何不进 audit.sh 默认 Cat**：节奏不匹配（季度级 vs pre-commit 每次跑）+ 输出形态不同（可编辑 md vs 终端 ✅/❌）。

## 自检清单

- [ ] 用户选择了审计范围
- [ ] Phase 1: audit.sh 执行无报错，输出全部所选类别
- [ ] Phase 2: 每项检查有 bash 命令取证 + 模型判断 + ✅/⚠️/❌ 结论
- [ ] 所有结论基于实际文件内容，引用具体文件：行号
- [ ] 不确定的标注「⚠️ 需人工确认」，不编造
- [ ] 对话内输出了精简版总览
- [ ] 完整报告保存到了 deliverables/
- [ ] 报告中的问题按严重度排序（🔴 > 🟡 > 🟢）
- [ ] 类别 6 在无项目时正确跳过而非报错
- [ ] 审计完成后不循环验证，输出一次总结就停
