<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: requirement-framework
description: >
  场景 ≥5 个需在 IMAP 前整理每条需求时触发,或用户提到「需求框架」「需求明细」时触发。
argument-hint: "项目名或需求描述"
type: pipeline
output_format: .html
output_prefix: rf-
pipeline_position: 2
depends_on: [scene-list]
optional_inputs: [context.md]
consumed_by: [interaction-map]
---
<!-- pm-ws-canary-236a5364 -->

# 需求框架生成

## 触发时机
场景清单已确认，进入需求拆解阶段。输出一份结构化 HTML 需求框架文档。

## 参考模板与读取指引

**Step 0：必读**
```
view .claude/skills/requirement-framework/references/requirement-framework-templates.html
```

**按需读取（需理解 CSS 细节或修改样式时）：**
```
view .claude/skills/requirement-framework/references/requirement-framework.css
```

CSS 通过 `open().read()` 拼接到骨架 `<style>` 标签，不需要模型逐行阅读或手写。SKILL.md 下方的标签对照表已包含所有需要的 class 名。

## Fill 内容契约

骨架提供完整 HTML 结构（`<style>` + Header + 概览卡片 + 表格表头 + 模块标题行占位 + Callout），Fill 提供每个模块的需求行内容。无设备壳组件。

## ★ 分步生成策略

需求框架文档通常 200-400 行，按以下两步执行：

**Step A：生成骨架**（先出，等用户确认模块结构）
- 完整 `<style>` 块（从 `requirement-framework.css` 通过 `open().read()` 读入）
- Header + 概览卡片组（3 张，填实际数字）
- 表格表头 + 每个模块的 `.mod-group` 标题行（无需求行，只占位）
- 底部 3 条 Callout

骨架输出后询问用户：「骨架已出，共 N 个模块（A~X）。请确认模块划分是否正确，我开始逐模块填需求行。」

**Step B：逐模块填需求行**
- 每次填 2-3 个模块的需求行（用 str_replace 插入占位行后面）
- 填完后告知进度，等用户「继续」
- 全部完成后执行自检

## 生成步骤

### 1. 信息收集（缺什么问什么，不编造）
- 项目名、版本号、作者
- 涉及哪些平台/端（App / Web / 后台 / 后端 / H5 …）
- 需求按哪些模块分组（从场景清单推导）
- 每条需求的：子模块名、所属平台、一句话描述、优先级

### 2. 概览卡片组（固定 3 张）
| 卡片 | val | desc |
|---|---|---|
| 涉及平台 | 平台总数 | 逐个列出平台及职责 |
| 需求模块 | 需求总条数 | 按模块列出子项数量 |
| 优先级分布 | P0×n · P1×n · 后续×n | P0 涵盖哪些模块 + 一句话理由 |

### 3. 需求明细表（核心区块）
- 固定 5 列：`#` / `所属模块` / `所属平台` / `大致描述` / `期望优先级`
- 按模块分组，每组先插一行 `.mod-group` 彩色标题行
- 模块编号 A / B / C / …，需求编号 A1 / A2 / B1 / B2 / …
- 彩色标题行颜色轮换（4 色循环）：默认蓝 → `.green` → `.amber` → `.red` → 默认蓝 → …
- 末尾固定放一个「后续迭代方向」模块，优先级统一为 `后续迭代`
- 新增项 / 变更项加 `.tag-new` 或 `.tag-v2` 标签（语义 = vs 线上基线,不是 vs 上版 req-framework)

### 4. 平台标签对照
| 标签 class | 含义 | 示例 |
|---|---|---|
| `.plat.app` | 客户端（iOS/Android） | App 端 |
| `.plat.web` | Web 前端 | Web 端 |
| `.plat.srv` | 后端服务 | 后端 |
| `.plat.cms` | 运营后台 | CMS 管理台 |

可按需扩展（如 `.plat.h5`），保持配色风格统一。

### 5. 优先级标签对照
| 标签 class | 含义 | 判定标准 |
|---|---|---|
| `.pri.p0` | 必须上线 | 缺一环链路跑不通 |
| `.pri.p1` | 增强能力 | 不阻塞核心但运营需要 |
| `.pri.p2` | 锦上添花 | 体验优化 |
| `.pri.later` | 后续迭代 | 依赖 V1 数据验证 |

### 6. 底部 Callout（固定 3 条）
1. **蓝色 `.co.bl`** — 平台说明：每个平台标签对应的职责解释
2. **绿色 `.co.gn`** — 优先级说明：P0 / P1 / 后续各自的判定逻辑
3. **琥珀色 `.co.am`** — 变更范围说明（迭代项目列出 vs 线上基线的差异,与 PRD 1.3 变更范围保持一致；语义非 vs 上版 req-framework,避免 PM 内部迭代流水堆叠);新项目无基线对比时替换为「开放问题 / 待确认项」

## 输出规则
- 文件名格式：`requirement-framework-{{项目简称}}.html`
- 纯内联 HTML + CSS，单文件，无外部依赖（字体 CDN 除外）
- 字体：Noto Sans SC + Inter + JetBrains Mono
- 编号一旦确定不可改动
- 描述列写核心动作 + 关键规则，不写空泛描述
- 跨模块依赖在描述中用 `→ {{编号}}` 标注（如「→ D1」）
- 数字自洽：概览卡片的统计数 = 表格实际行数

## 自检清单（生成后逐项过）
- [ ] 概览卡片数字 = 表格实际统计
- [ ] 模块编号连续无跳号
- [ ] 每条需求有且仅有一个优先级标签
- [ ] 平台标签与实际涉及端一致
- [ ] 跨模块引用编号存在且正确
- [ ] 底部 3 条 Callout 齐全
- [ ] 无 {{占位符}} 残留
