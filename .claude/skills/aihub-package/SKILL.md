---
name: aihub-package
description: >
  当用户提到「出包 / 上架 SkillHub / 打包 hub 包 / 建 Agent / 建 Tool / 给 AIHUB 写包 /
  同事要 XX skill 的 zip」时触发。AIHUB 包生产线（hub/，Agent / Tool / Skill 三形态）
  的出包流程编排：形态判定 → 必读规范路由 → 脱敏 checklist → 预检 → 打包 → 验证 → 刷索引。
  规程不搬运——指向 hub/README.md + .claude/runbooks/ai-platform-specs.md。
type: standalone
output_format: 对话内
output_prefix: none
scripts:
  hub/_vet_local.sh: "上架预检（密钥 / frontmatter / 红旗 / 语法 / 用例）— bash hub/_vet_local.sh <包目录>"
  hub/_repack.sh: "重打 zip（打包前自动跑预检）— bash hub/_repack.sh <包>"
  hub/_verify.sh: "解压后端到端验证（zip 新鲜度 / 冒烟 / 包特定 e2e）— bash hub/_verify.sh <包|all>"
  hub/sync.sh: "源头 → 分发包同步（9 包纳管）— bash hub/sync.sh <skill> [--check|--apply]"
  hub/gen_index.py: "刷 INDEX.md（自动分类 + 部署态两列）— python3 hub/gen_index.py [--check]"
---

# AIHUB 包出包 Skill（aihub-package）

> hub/ 产线的出包编排器。规程不在这里——指向 `hub/README.md`（维护者手册）+ `.claude/runbooks/ai-platform-specs.md`（公司中台规范入口）。本 skill 只做 Step 路由 + 形态判定。

## 触发与定位

- **触发**：用户说「出包 / 上架 / 打 zip / 建 Agent / 建 Tool / 给同事分发 XX skill」
- **做**：从「想出什么包」到「zip 发出去 + INDEX 刷新」的完整流程编排
- **不做**：公司中台规范的语义判断（走 `ai-platform-specs.md` 路由到对应规范文档）；脱敏改造的逐条执行（走 `hub/README.md §抽象规则`）

## 调用脚本前 30 秒

> hub/ 的脚本不在本 skill 目录，在工区根 `hub/`。所有脚本 `bash -n` 已过、`set -e` 兜底，失败看 stderr。

**Public API（不可改签名）**：
- `bash hub/_vet_local.sh <包目录>` — 上架预检伞脚本；❌ fail-stop / ⚠ 不阻断
- `bash hub/_repack.sh <包>` — 重打 zip（自动清缓存 + 跑预检 + 打包 + 刷 INDEX）
- `bash hub/_verify.sh <包|all>` — 解压后端到端验证（模拟同事拿到 zip 的环境）
- `bash hub/sync.sh <skill> [--check|--apply]` — 源头迭代同步到分发包（9 包纳管）
- `python3 hub/gen_index.py [--check]` — INDEX.md 自动分类 + 部署态两列

**会拦你的 hook**：
- `pre-writeedit-guard.sh` — 改 `hub/*/aihub_tool.py` / `system-prompt.md` / `agent-model.json` 时强制先读 `ai-platform-specs.md` + 对应公司规范（L2 机械强制）
- `script-syntax-gate` — 写 .py / .sh 自动跑 pyflakes / bash -n
- `.githooks/pre-commit` — hub/ 变更触发 audit cat 21「hub 分发物健康」+ pytest

## 硬规则（FAIL 即拦）

- **打包禁手动 zip**：必须走 `bash hub/_repack.sh <包>`（自带缓存清理 + 预检 + INDEX 刷新）。手动 zip 会漏 `__pycache__` / `.DS_Store`、忘预检、INDEX drift
- **改完源码必重打 zip**：`check_hub_fresh.py --strict` 抓「源文件比 zip 新」红灯，audit cat 21 阻断 commit。改完顺序：改源码 → `_repack.sh` → `_verify.sh`
- **公司中台规范不可绕**：写 `hub/*/aihub_tool.py` / `system-prompt.md` / `agent-model.json` 前，`pre-writeedit-guard.sh` 会 block 直到读了 `ai-platform-specs.md` + 对应 L2 规范文档（MCP / Agent / Prompt 编写规范）
- **内部文档不入 git**：`hub/AI中台-规范及帮助文档/` 走 .gitignore（含 wiki.internal-domains.com 内网 host），重拉走 `dig_confluence.py` 父页 164485093；`sync_public.sh` 排除整个 `/hub/`，绝不进公开镜像
- **脱敏 fork 禁盲跑 sync --apply**：hub 是源头 skill 的脱敏泛化镜像，不是源头旧拷贝。`sync.sh` 显示的 diff 是「脱敏改造 + 源头新改动」混合，必须人工挑 backport，绝不 `--apply` 全量覆盖（会重新泄漏内网路径 + 抹掉脱敏改造）

## 核心输出规范

三种包形态（判据与 `hub/gen_index.py` 自动分类同源）：

| 形态 | 必备文件 | 上线平台 | 分发方式 |
|------|---------|---------|---------|
| **Skill** | `SKILL.md` | Claude Code / SkillHub | zip 解压进 `.claude/skills/` |
| **Tool** | `aihub_tool.py`（+ 可选 `SKILL.md` 双形态） | AIHUB Chat (OpenWebUI) | zip 上传 OWUI Tools |
| **Agent** | `agent-model.json` + `system-prompt.md` | AIHUB Chat (OpenWebUI) | raw 分发（无 zip，手动贴 OWUI） |

不分形态就建目录 = 后期补文件。先定形态再动手。

## 执行步骤

### Step 0 · 形态判定（最先做）

问用户「这包给谁用、在哪个平台跑」：

- Claude Code 里命令行触发 / SkillHub 上架 → **Skill**
- AIHUB Chat 里挂给 Agent 调（取数 / 推送 / 解析）→ **Tool**
- AIHUB Chat 里组装一个完整 Agent（system-prompt 驱动 + 挂工具）→ **Agent**

不确定就看 `hub/INDEX.md` 找同形态的现成包当模板。

### Step 1 · 必读规范路由（写代码前）

形态定下后，**写第一个文件之前**先读对应规范（hook 会强制拦）：

```
Read .claude/runbooks/ai-platform-specs.md    （L1 入口 · 必读）
```

L1 按形态路由到 L2：

| 形态 | L2 必读公司规范（落 `hub/AI中台-规范及帮助文档/`） |
|------|--------------------------------------------------|
| Skill | AI中台-Skill 编写规范 + 基础/高级用户手册 |
| Tool | AI中台-MCP 编写规范（aihub_tool.py = OpenWebUI Local Python Tool 形态） |
| Agent | AI 中台-Agent 创建规范 + AI中台-Prompt 编写规范（system-prompt 是灵魂） |

写「skill → OWUI Agent」的剥耦合流程（判断值不值得 / 四要素映射 / Valves / daemon vs 内联两范式）看 `hub/SKILL-TO-AGENT.md`。

### Step 2 · 脱敏 checklist（从源头搬时）

源头是 `.claude/skills/{skill}/` 或 `scripts/` 时，搬进 hub 前按 `hub/README.md §抽象规则` 6 条脱敏：路径硬编码 / 业务名 / 内部依赖 / 凭证发现（env → .env → .mcp.json 三级 fallback）/ runbook 引用 / hook 路径 / 共享资源。

自查命令：
```bash
grep -rn -E "(projects/|Platform C|internal-domain|context\.md|lib\.|runbooks/|/Users/)" hub/<新包>/
```

### Step 3 · 上架预检

```bash
bash hub/_vet_local.sh hub/<包>          # ❌ 必须清零；⚠ 建议处理不阻断
```

预检六维度：secret / frontmatter / structure / redflag / syntax / example。规则详见 `hub/AUTHORING-RULES.md`。

### Step 4 · 打包

```bash
bash hub/_repack.sh <包>                  # 自动清缓存 + 预检 + 打 zip + 刷 INDEX
```

**禁手动 zip**。`_repack.sh` 失败看 stderr，确认 ❌ 全是误报可 `--force` 跳预检（慎用）。

### Step 5 · 解压后端到端验证

```bash
bash hub/_verify.sh <包>                  # 模拟同事拿到 zip 解压后的环境
```

四层：zip 新鲜度 / unpack / 形态必备文件 / argparse 冒烟 + 包特定 e2e（prd / scene-list / promo-kit / token-audit 有；其他包 warn 不假绿）。

加新包的 e2e 用例改 `_verify.sh` 的 `e2e()` case。

### Step 6 · 刷索引 + 部署态登记

```bash
python3 hub/gen_index.py                  # INDEX.md 自动分类
```

新包形态判定靠包内文件特征（gen_index 自动分类，不手维护）。

Tool / Agent 包上线 OWUI 后，在 `hub/deployed.json` 补一行（人工填，平台无 API）：
```json
"<包名>": {"version": "1.0.0", "deployed_at": "2026-07-25"}
```
`check_hub_fresh.py` 会比对本地 vs OWUI 已部署版本，漂移报黄灯。

### Step 7 · 源头同步（仅 sync.sh 纳管的 9 包）

源头 `.claude/skills/{skill}/` 改了，要同步到 `hub/{skill}/`：

```bash
bash hub/sync.sh <skill> --check          # 先干跑看 diff
bash hub/sync.sh <skill>                  # 交互模式，Tier 2 逐个确认
```

**关键**：sync 显示的 diff 是「脱敏改造 + 源头新改动」混合（hub 是有意脱敏的镜像不是旧拷贝），人工挑 backport，绝不 `--apply` 全量覆盖。判断方法见 `hub/README.md §同步源头迭代`。

未纳入 sync.sh 的包（dist own / 无源头 skill）：直接改 `hub/<包>/`，无此步。

## API 速查

| 任务 | 命令 |
|------|------|
| 上架预检 | `bash hub/_vet_local.sh hub/<包>` |
| 重打 zip | `bash hub/_repack.sh <包>` |
| 端到端验证 | `bash hub/_verify.sh <包>` |
| 源头同步 | `bash hub/sync.sh <skill> [--check\|--apply]` |
| 刷索引 | `python3 hub/gen_index.py [--check]` |
| 发布物新鲜度 | `python3 scripts/check_hub_fresh.py [--strict]` |
| 加新包到 sync.sh | 在 `hub/sync.sh` 加 `sync_<new>() + main case`，`hub/_repack.sh` 的 SKILLS 加名 |

## 自检清单

出包前过一遍：

- [ ] 形态判定做完（Skill / Tool / Agent），必备文件齐全
- [ ] 必读规范读过（hook 兜底，但主动读省被拦一次）
- [ ] 脱敏 grep 无内网路径 / 内部 host 残留
- [ ] `_vet_local.sh` 0 ❌
- [ ] `_repack.sh` 打出 zip
- [ ] `_verify.sh` 全绿
- [ ] `gen_index.py` INDEX 无 drift（`--check` exit 0）
- [ ] 上线 OWUI 的包在 `deployed.json` 补登记
- [ ] 改了源码别忘了重打 zip（`check_hub_fresh --strict` 抓红灯）

全跑一遍：
```bash
bash hub/_vet_local.sh hub/<包> && bash hub/_repack.sh <包> && bash hub/_verify.sh <包> && python3 scripts/check_hub_fresh.py
```

## References 索引

| 文件 | 何时读 |
|------|--------|
| [hub/README.md](../../../hub/README.md) | 维护者手册（三层文件分类 / 脱敏规则 / sync.sh / 验证 / SKILL-TO-AGENT 入口） |
| [hub/AUTHORING-RULES.md](../../../hub/AUTHORING-RULES.md) | 上架总准则（frontmatter 合规 / 红旗行为 / 用例 / 密钥误报规避） |
| [hub/SKILL-TO-AGENT.md](../../../hub/SKILL-TO-AGENT.md) | skill → OWUI Agent 剥耦合（Valves / daemon vs 内联两范式） |
| [hub/INDEX.md](../../../hub/INDEX.md) | 22 包当前态清单（自动生成，看包分类与一句话） |
| [.claude/runbooks/ai-platform-specs.md](../../runbooks/ai-platform-specs.md) | 公司中台规范入口路由（L1，产物→必读规范映射） |
| [scripts/check_hub_fresh.py](../../../scripts/check_hub_fresh.py) | 发布物新鲜度校验（zip 过期 / 部署态漂移） |

## 失败恢复

- **`_vet_local.sh` 报真密钥 ❌**：从 env / `.mcp.json` 读，别硬编码。`hub/AUTHORING-RULES.md §密钥误报规避` 区分真密钥 vs LLM 误判的变量名
- **`_verify.sh` 报 zip 过期**：源码改了忘重打 → `bash hub/_repack.sh <包>`
- **`_verify.sh` argparse 冒烟挂**：多半漏 import / 缺依赖。hub 包设计为零第三方依赖（标准库），挂了说明误引入外部包
- **sync.sh diff 太多看不懂**：先 `git log --since="上次 sync 日期" -- .claude/skills/<skill>/` 看源头改了什么，再对照挑 backport
- **`gen_index.py --check` drift**：跑无参版本写盘刷新即可
- **改完源码 commit 被拦**：`audit cat 21` 报 zip 过期 → 跑 `_repack.sh` 重打
