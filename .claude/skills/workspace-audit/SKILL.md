<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: workspace-audit
description: >
  当用户说「审计」「诊断」「跑一遍审计」时触发。覆盖全局诊断 11 类(文件 / 数值 / 依赖 / 规则 / Token / 工程健壮性等)。支持按类别选择执行。
type: tool
output_format: .md
depends_on: []
optional_inputs: []
consumed_by: []
---
<!-- pm-ws-canary-236a5364 -->

# Workspace Audit

## 定位

全局诊断工具。两阶段审计：**Phase 1 脚本硬检查**（audit.sh，零推理纯 bash）+ **Phase 2 模型软检查**（需要语义推理的矛盾分析、安全扫描、瘦身建议等）。

## 触发后第一步：让用户选择审计范围

展示以下菜单，用户选哪些跑哪些。默认全选。

请选择审计范围（输入编号，多选用逗号分隔，直接回车=全部执行）：

**Phase 1 — 脚本自动检查（audit.sh）**

1. 文件完整性 — SKILL.md 存在性、frontmatter、references 引用、配置文件
2. 数值与格式一致 — 设备尺寸、配色 token、命名前缀、字体规范、字体栈顺序
3. 依赖与链路 — depends_on 闭环、循环依赖、链路覆盖、孤立 skill
4. 规则冲突 — context.md 章节引用、触发词重叠、术语一致
5. Token 预算 — 规则层总量、单 skill 成本、全链路 session 预算、臃肿文件
6. 产出物一致性 — 场景编号、术语、文件命名、context.md 九章验证（需有活跃项目）
7. SKILL_TABLE 一致性 — workspace-context.md 表格 ↔ frontmatter 比对

**Phase 2 — 模型推理检查**

8. 规则层矛盾深度扫描 — 逐条比对 CLAUDE.md / pm-workflow / 各 SKILL.md 中的规则是否冲突
9. 安全 & 泄露扫描 — API key / token / password 模式、.gitignore 覆盖度、大文件
10. 工程健壮性 — hook 机制、依赖声明、Python 包管理
11. 瘦身与优化建议 — >10K token Skill 的按需加载机会、重复内容提取

## Phase 1 执行方式

所有硬检查逻辑在 `references/audit.sh` 中实现（执行类脚本，模型无需读取源码）。

```bash
bash .claude/skills/workspace-audit/references/audit.sh <类别编号逗号分隔>
```

示例：
- 全部执行：`bash .claude/skills/workspace-audit/references/audit.sh 1,2,3,4,5,6,7`
- 只跑 pre-commit 覆盖的：`bash .claude/skills/workspace-audit/references/audit.sh 1,2,3,4,7`

## Phase 2 执行方式

逐项用 bash 命令取数据，模型做语义推理判断。每项给出 ✅/⚠️/❌ + 证据（文件名:行号）。

### 8. 规则层矛盾深度扫描

**8.1 字体规范一致性**

```bash
grep -rn "font-family" .claude/skills/*/references/*.css 2>/dev/null
```

- 逐个比较每个 CSS 文件的 font-family 声明与 pm-workflow §三 规范
- 特别检查：正文栈 vs 等宽栈是否混写；PPT JetBrains Mono 白名单

**8.2 色板一致性**

```bash
grep -rn "#0B0E11\|#0ECB81\|#F6465D\|#00B42A\|#F53F3F" .claude/skills/*/references/*.css 2>/dev/null
```

- 同一语义色（success/danger）在不同文件中 hex 是否一致
- 深色板 vs 浅色板是否有混用（prototype 双色系已白名单）

**8.3 设备尺寸一致性**

```bash
grep -rn "375\|812\|width.*px" .claude/skills/*/SKILL.md 2>/dev/null
```

- App 壳、Web 框的宽高在各 SKILL.md 中是否与 pm-workflow §三 一致

**8.4 HTML 行数阈值一致性**

```bash
grep -rn "200.*行\|脚本生成" .claude/rules/ .claude/skills/*/SKILL.md 2>/dev/null
```

- "> 200 行必须脚本" 在各处表述是否统一

**8.5 自检反压规则一致性**

```bash
grep -rn "自动修复.*次\|失败.*停\|静默.*跳过" .claude/rules/ .claude/skills/*/SKILL.md 2>/dev/null
```

- "最多自动修复 2 次" 各处是否一致；有无 Skill 写了不同策略

**8.6 执行优先级描述一致性**

```bash
grep -rn "优先级\|Layer\|层级" CLAUDE.md .claude/rules/ README.md workspace-context.md 2>/dev/null
```

- 各文件对「谁覆盖谁」的表述是否一致

### 9. 安全 & 泄露扫描

**9.1 明文密钥扫描**

```bash
grep -rn "sk-\|api[_-]key\|token.*=\|password\|secret\|Bearer " . --include='*.md' --include='*.json' --include='*.js' --include='*.py' --include='*.sh' -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null
```

- 判断匹配项是否为真正的明文密钥
- .mcp.json 是否在 .gitignore 中

**9.2 .gitignore 覆盖度**

确认以下全被 ignore：projects/ / /references/ / soul.md / node_modules/ / .mcp.json / deliverables/

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

- hook 是否调用 audit.sh 且覆盖范围正确（当前应为 1,2,3,4,7）
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

## 输出格式

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

**总计**：N/11 通过，M 个问题

## 需要修复的问题（按严重度排序）
1. 🔴 {严重问题} — {文件:行号}
2. 🟡 {中等问题} — {文件:行号}
3. 🟢 {建议优化} — {文件:行号}
```

**2. 文件报告（完整版）**，含所有检查项的详细输出

保存到 `deliverables/audit-{日期}.md`。
- 如果在某个项目上下文中运行，保存到 `projects/{项目名}/deliverables/audit-{日期}.md`
- 如果不在项目上下文中，保存到仓库根目录 `deliverables/audit-{日期}.md`

## 自检

- [ ] 用户选择了审计范围
- [ ] Phase 1: audit.sh 执行无报错，输出全部所选类别
- [ ] Phase 2: 每项检查有 bash 命令取证 + 模型判断 + ✅/⚠️/❌ 结论
- [ ] 所有结论基于实际文件内容，引用具体文件:行号
- [ ] 不确定的标注「⚠️ 需人工确认」，不编造
- [ ] 对话内输出了精简版总览
- [ ] 完整报告保存到了 deliverables/
- [ ] 报告中的问题按严重度排序（🔴 > 🟡 > 🟢）
- [ ] 类别 6 在无项目时正确跳过而非报错
- [ ] 审计完成后不循环验证，输出一次总结就停
