# 规则半衰期总表

<!-- 元数据文件 · 不在主线 Claude 注入路径上 · Felix 半年 review 用
  归类口径：
  - volatile：绕当前模型能力弱点的补丁，与模型版本强相关。每半年 review，
    如果模型已自愈 / 该规则触发数持续为 0，考虑删除或降级。
  - durable：PM 方法论抽象，与模型能力无关。长期持有，只在业务发生根本性变化时调整。
  - uncertain：边界不清 / 待进一步讨论。

  位置：.claude/_meta/half-life.md（2026-05-16 从 .claude/runbooks/ 迁入，与"主线按需 Read"
  的 runbook 物理分离）
-->

本文件不改规则正文，只做归类索引。对应的触发数据在 `scripts/dashboard.py` 输出中。

---

## volatile（补丁类，半年 review）

**下次 review：2026-11-01（6 个月后）**。Review 动作 = 拉 dashboard 看触发数，为 0 或极低的规则降级 / 删除。

### V1 · CJK 标点合规

**位置**：`.claude/runbooks/human-voice-rules.md` §⓪ 中文标点（对话场景）· `scripts/check_cjk_punct.py`（含 `--fix` / `--dry-run`）· hooks `post-cjk-punct-check.sh`（Write/Edit Branch A）/ `post-bash-deliverable-check.sh`（Bash 路径，含 `script-rebuild-cjk` gate）

**为什么 volatile**：当前模型（Opus 4.7）在中文文本里仍然高频混用半角标点（逗号 / 冒号 / 括号）。这是训练语料分布问题，下一代模型可能自愈。

**review 信号**：dashboard「hook 健康度」中 cjk-punct warn 触发数。如果连续 8 周 warn / block < 10 次，降级该 hook 为可选。

### V2 · 字体栈 / CJK 优先铁律

**位置**：`.claude/skills/_shared/claude-design/tokens.css`（设备规范 SSOT）· 各 SKILL.md 字体部分

**为什么 volatile**：模型默认给出的 `font-family` 栈通常是英文优先（`Inter`, `Roboto` 等），中文字符 fallback 到系统默认造成排版失败。下一代模型若训练时强化中文排版知识，该规则冗余。

**review 信号**：产出物视觉走查时的字体问题命中率。暂无 hook 直接观测，需手动统计。

### V3 · 分步生成 + Fill 自检

**位置**：`.claude/runbooks/html-pipeline.md` §一 · `.claude/hooks/post-audit-fast.sh` / `post-prototype-audit.sh`

**为什么 volatile**：模型一次性生成 >500 行 HTML 容易丢 Scene / 漏组件。当 Opus 5 / Sonnet 5 之后单轮生成能力提升，自检+fill 分轮的「工程补丁」价值弱化。**但骨架→确认→填充的产品价值（用户决策点）是 durable，保留**。

**review 信号**：post-audit-fast 的 block 率。降到 5% 以下可考虑把自检改为 opt-in。

### V4 · 脚本优先 / 大 HTML 禁 Write

**位置**：`CLAUDE.md` §修改入口防误操 · `.claude/hooks/pre-scripts-first.sh` / `pre-deliverable-source-gate.sh`

**为什么 volatile**：模型直接 Write 2000 行 HTML 容易中途截断 / 引号错乱。一旦模型支持流式 Write + 自动纠错，可放开直接 Write。

**review 信号**：deliverable-source-gate block 频次。

### V5 · 代理检查 / 被墙下载

**位置**：`CLAUDE.md` §Runbook 触发条件 · `.claude/runbooks/proxy-fallback.md` · `.claude/hooks/pre-bash-guard.sh`（聚合 proxy / git-https / skeleton-force 多规则）

**为什么 volatile**：跟 Felix 的网络环境（中国大陆）绑定，换个国家立刻冗余。跟模型无关但跟使用场景强相关。

**review 信号**：proxy-check block 频次。如 Felix 长期出差海外，可关闭。

### V6 · 子 Agent 调度规则

**位置**：`CLAUDE.md` §工具调用红线 · 子 Agent 调度段（无 hook 兜底，主线自评）

**为什么 volatile**：早期为省 token 设计（派 Haiku 做机械活）。公司 1000 USD/月 token 报销额度后省 token 不再是首要目标。曾试 `pre-bash-runner-gate` 强制改派 + `bash-runner` 专用 agent，2026-05-19 移除——主线 Opus 几乎都判断「不派」，hook 净误伤。规则改为主线自评：长输出 / 跨项目扫描派通用 agent，含业务判断自跑。

**review 信号**：sub-agent 调度量（dashboard sub-agent section）。

### V7 · Token 预算 / 按需加载

**位置**：`CLAUDE.md` §启动契约（baseline 按需读取）· `.claude/runbooks/artifact-conventions.md` §三 上下文防丢

**为什么 volatile**：为 200K/128K 上下文模型做的保险。Opus 4.7 已经 1M，Sonnet 5/6 只会更大。

**review 信号**：一旦所有常用模型都是 1M+，`read_prd_section.py` 按需读不再必要；Felix 直接读全文 baseline 就好。预计 2027 年可以动。

### V8 · Session-state / PreCompact 防丢

**位置**：`CLAUDE.md` §启动契约 · session-state.md 纪律 · `.claude/hooks/pre-compact.sh` / `pre-risky-op.sh`

**为什么 volatile**：为 Claude Code 当前的 auto-compact 行为补丁。compact 机制升级 / context 上限进一步提升后，防丢机制冗余。

**review 信号**：pre-compact triggered 频次（一次 session 应该只触发 0-1 次，频繁触发说明上下文吃紧）。

---

## durable（方法论，长期持有）

这些规则表达 PM 思维抽象，与模型能力无关。持续投入维护。

### D1 · 场景编号锁定与跨产出物串联

**位置**：各 SKILL.md frontmatter `depends_on` / `consumed_by` + `.claude/runbooks/version-bump.md`（场景编号锁定由 SKILL 链路 + version-bump 承接）

**为什么 durable**：场景编号是 PM 方法论的索引系统——PRD 的 B-1 = 原型的 B-1 = 交互大图的 B-1。这个映射关系不依赖任何工具。

### D2 · Baseline 静态 / 动态章分层（稳定态 / 变化历史 / 计划）

**位置**：baseline 骨架 `sections_md.build_baseline_skeleton` + `prd/scripts/read_prd_section.py --toc`（每章标 [静态]/[动态]）· `.claude/runbooks/artifact-conventions.md` §四 静态章四不细节

**为什么 durable**：把产品知识分"稳定态 / 变化历史 / 计划"三类分层管理，是产品知识管理方法。即使换 AI 工具，该分层仍是 PM 做产品的 mental model 依据。

### D3 · Pipeline 节点排序（scene-list → ... → cross-check）

**位置**：`CLAUDE.md`「收到需求路由」节 · 各 SKILL.md frontmatter `pipeline_position`

**为什么 durable**：这是 "PM 产出物的依赖顺序" 本身，不依赖执行者。即使给人做也该按这个顺序。

### D4 · 叙事骨架 PART（演讲叙事顺序）

**位置**：`.claude/runbooks/artifact-conventions.md` §五 演讲叙事顺序

**为什么 durable**：产出物按「用户故事线」组织（触达 → 转化 → 留存），不按「技术模块」组织。这是产品表达方式，与工具无关。

### D5 · PM-GATE / 需求澄清关卡

**位置**：`CLAUDE.md`「收到需求路由」节 PM-GATE 4 风险扫描

**为什么 durable**：三问（解决谁的痛点 / 核心指标 / 判断成功）是 PM 必修思维框架，与工具无关。

### D6 · 三闸口质量（PRD 讲人话 / 业务白话 / 字体三件套）

**位置**：`.claude/skills/prd/SKILL.md` §核心规则 · `.claude/skills/prd/references/prd-chapter-rules.md §三` · `.claude/runbooks/human-voice-rules.md`

**为什么 durable**：产出物讲人话是 PM 职业的核心素养，不是模型能力问题。

### D7 · 产品线协同战略（内容促交易）

**位置**：`projects/product-lines.md`（Phase 3 落地，2026-05-16 从顶层迁入 projects/）

**为什么 durable**：业务战略主线。community / livestream / growth 的协同矩阵是 Felix 在 Platform C 做 PM 的战略判断，跟工具无关。

### D8 · 三层目录 Schema（Product-Iteration-Module）

**位置**：`.claude/runbooks/project-mgmt.md`

**为什么 durable**：产品线 / 迭代 / 模块的分层反映业务组织本质。

---

## uncertain（边界不清，待后续决策）

### U1 · 反 AI slop 六禁

**位置**：`.claude/skills/_shared/claude-design/anti-ai-slop.md`（HTML 产物美学硬底线 + CSS 变量源头唯一） · `.claude/runbooks/human-voice-rules.md` §⓪ 反 AI slop（对话/文本类产物统一入口）

**状态**：当前是 volatile 还是 durable？
- 偏 volatile：反的具体症状（全屏渐变 / Emoji 装饰 / 花里胡哨 icon）是当前一代模型 slop 特征，下代可能变化
- 偏 durable：反 slop = 反"炫技不克制"，是审美原则

**结论**：**偏 durable**，规则名改为 "审美克制" 更通用。原始六禁保留作为当前阶段的具体症状清单（volatile），但美学原则本身 durable。

### U2 · 讲人话产物锚点 vs 正文分离

**位置**：`.claude/runbooks/human-voice-rules.md`

**状态**：规则本身 durable（给人读的产物不用内部编号），但「锚点 = 内部编号」是当前实现选择，可能演化。

**结论**：核心 durable（分离锚点 vs 业务白话），实现细节 volatile。

### U3 · MCP 调用克制 / firecrawl 禁用

**位置**：`.claude/runbooks/mcp-config.md` §MCP 调用策略（2026-05-16 从 CLAUDE.md 下沉）

**状态**：跟具体 MCP 生态绑定，属于执行层优化。**偏 volatile**，但 "不要默认加载 15K token 的 MCP server" 原则 durable。

`last-reviewed: 2026-05-16 · triggered: 0（.mcp.json 当前为空）· action: 冬眠 · 下次 review 2026-11-01 决定删除或保留`

---

## Review SOP

**周期**：每 6 个月（固定日期：5-1、11-1）

**步骤**：

1. 跑 `python3 scripts/dashboard.py --days 180`，拿 hook / skill 触发数
2. 对每条 **volatile** 规则：
   - 触发数 = 0 → 考虑删除（需 Felix 确认是否因为现象不再出现）
   - 触发数 < 5/月 → 考虑从 block 降级为 warn
   - 触发数 > 50/月 → 说明模型未自愈，保留
3. 对每条 **durable** 规则：review 是否仍代表最新方法论；如有偏离，升级规则文本
4. 对每条 **uncertain**：推动拍板

**更新本文件**：review 完成后，在对应规则加一行 `last-reviewed: YYYY-MM-DD · triggered: N · action: 保留/降级/删除`

---

## 元数据

- 首次创建：2026-05-01
- 维护：Felix + 本地 Claude Opus（Opus 出具 review 建议，Felix 决策）
- 半衰期：本文件结构本身是 durable，具体条目归属会变化
- 2026-05-16 规则层五层重构：迁入 `.claude/_meta/`，stale 引用全部修对（soul.md / 旧 CLAUDE.md 章节 / pm-workflow.md → pm-thinking.md + artifact-spec.md + output-style.md 重新归位）
- 2026-05-24 pm-thinking.md 下放至 runbooks/pm-methodology.md，路由部分上抬 CLAUDE.md「收到需求路由」节
- 2026-05-24 artifact-spec.md + output-style.md 完成下放至 runbooks/artifact-conventions.md，规则层只留 CLAUDE.md + runbook
