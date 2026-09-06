# 禁词清单 · 人读版

> 真相源 = 代码：[banned_terms.py](banned_terms.py)
> 此文档非自动载入，写新 skill / 怀疑禁词覆盖时 Read。
> hook 自动拦截：post-plain-language-check + check_cjk_punct + check_imap + check_proto + check_prd_md。

工作区禁词分 3 层，**层级越靠下越难治**：

| 层 | 禁什么 | 例子 | hook 拦不拦 |
|----|-------|------|------------|
| 第 1 层 词汇 | AI 煽动收尾词 / 空话起手 | 至关重要、赋能、众所周知 | ✅ |
| 第 2 层 句式 | 对比重构 / 三段对仗 | "不是 X，而是 Y" | ✅（部分） |
| 第 3 层 结构 | 段落均匀 / em dash 滥用 / 每段升华 | 整体节奏 | ❌ 只能 prompt 约束（见 human-voice-rules.md §⓪） |

---

## § 1 内部锚点（禁出现在产物正文 · 给读者看的文档）

> 「产物」= 给 leader / 业务 / 设计 / 研发读的文档（PRD / PPT / 数据周报 / IMAP / 原型）。
> 内部 PM 工作文档（baseline / scene-list.md / SKILL.md）豁免，编号是它们的载体。

| 类 | 反例 | 正例 | banned_terms.py 常量 |
|----|------|------|----------------------|
| 内部文件名 | "见 scene-list.md 第 4 章" | "见场景地图" | INTERNAL_FILES_RE |
| 决策号 | "决策 #14 推翻..." | "本次不做 CMS" | DECISION_RE |
| 章节锚点 | "第 4 章定义" | "场景编号锁定" | CHAPTER_RE |
| §X.Y 西文小节 | "按 §4.2 口径" | "按全局归因口径" | SECTION_ANCHOR_RE |
| PART 骨架 | "PART A 流程" | "PART A · 业务白话" | PART_ANCHOR_RE |
| 场景编号裸露 | "在 A-1 场景下流失" | "在策略卡展示场景下流失" | SCENE_ANCHOR_RE |
| 占位符 | "[待补充指标]" | （删除整段或补全） | PLACEHOLDER_RE |
| FIXME / TODO | "TODO: 补埋点" | （推 wiki 前必收敛） | FIXME_RE / TODO_RE |
| 圈数字 | "①②③" | "1. 2. 3." 或 bullet | CIRCLED_DIGIT_RE |
| 防御性三连 | "交互大图（IMAP / interaction map）" | "IMAP" 或 "交互大图"（一种叫法） | DEFENSIVE_TRIO_RE |

---

## § 2 AI slop 词表

### 2.1 收尾煽动词（硬禁）

| 词 | 替换 |
|----|-----|
| 真相 | 描述 / 现状 |
| 核爆级 | 关键 / 重大 |
| 重塑 | 改造 / 重做 |
| 多维度 | 多个角度（具体说几个） |
| 全方位 | 多个方面 |
| 深度赋能 | 让 X 能 |
| 全新升级 | 改版 / 升级 |
| 焕新 | 改版 |
| 迭代升级 | 升级 / 改 |
| 综合性 | 多方面 |

### 2.1b 软提醒词（WARN · 不阻断）

这些词被 AI 过度使用，但本身是中国 PM 圈的真实行业用语。hook 输出 `[AI_SLOP_WARN]` 标记，不改变退出码。

| 词 | 提醒 |
|----|------|
| 赋能 | 确认后面说了具体给了什么能力/数据/入口；写不出就删 |
| 智能化 | 确认不是「自动化」的同义替换；两个词含义不同 |
| 颠覆性 | 确认下一句话能说清颠覆了什么、怎么颠覆的；说不出来就删 |
| 革命性 | 同上——大概率是装饰词，除非后面跟了具体机制 |

### 2.2 空话起手（行首匹）

| 词 | 替换 |
|----|-----|
| 这是一个... | 直接陈述事实 |
| 值得注意的是... | 直接说点 |
| 需要强调的是... | 直接说点 |
| 众所周知... | 直接说点 |

### 2.3 业务豁免词（hook 故意放过）

「落地」「闭环」「打通」是业务真实用词（落地 = 上线 / 闭环 = 回路 / 打通 = 数据互通），hook 放过。但**写产物时仍尽量替换**：

- ❌ 数据打通 → ✅ 跨端数据同步
- ❌ 流程闭环 → ✅ 流程回路

「赋能」不在硬豁免，走 §2.1b 软提醒：能说出具体给了什么能力 / 数据 / 入口就保留，说不出就删。

### 2.4 AI 味词组（WARN · 不阻断）

产物里高频但低误杀的 AI 套话，`check_plain_language.py` WARN_PATTERNS 命中只提醒。真相源 `banned_terms.py` `BANNED_WARN_EXTRA`。

| 词类 | 反例 | 改法 | 常量 |
|------|------|------|------|
| 过渡废话 | 综上所述 / 归根结底 / 由此可见 / 换句话说 | 删掉，直接给结论 | TRANSITION_FILLER_PATTERNS |
| 无源引用 | 研究表明 / 数据显示 / 业内人士认为 / 据报道 | 给具体数据 / 来源，或删铺垫（不补虚构出处） | UNSOURCED_CITATION_PATTERNS |
| 自媒体腔 | 保姆级 / 硬核 / 一文读懂 / 划重点 / 干货 | 删掉（产物不该有爆款文风） | SELF_MEDIA_SLOP_PATTERNS |

不收：工程师腔（根因 / 收窄 / 兜底）、商业黑话扩列（链路 / 触达 / 沉淀）——合法 PM 术语，入库误杀高。接住体 / 谄媚 / 心理判断腔属对话层，走 human-voice-rules.md §⓪。

误杀回归集：`scripts/tests/test_plain_language_boundary.py`（正常产物 + PM 术语必须 0 strict）。

---

## § 3 句式黑名单

### 3.1 对比重构（CONTRAST_REFRAME_RE）

❌ 不是「快」，而是「快得能让用户感知不到等待」
❌ 这不是优化，这是重构

→ 改：直接陈述结论。"这次改造让感知等待 < 200ms"

### 3.2 三段对仗（TRIPLE_PARALLEL_RE）

❌ 不只是工具，更是平台，是生态

→ 改：选一个核心定位。"这是社区基建平台"

### 3.3 其他无法 regex 但必须避免（human-voice-rules.md §⓪ 兜底）

- 假直白开场："说实话 / 关键在于 / 核心是"
- 每段末尾升华："这意味着... / 这正是... / 这就是为什么..."
- 设问回答："为什么 X？因为 Y"（自问自答型）

---

## § 4 跳过规则

- 文件后缀豁免（不扫描）：见 `SKIP_FILE_SUFFIXES`（docx / pdf / 图片 / 字体 / 压缩包等）
- 目录豁免：见 `SKIP_DIR_NAMES`（`__pycache__` / `node_modules` / `.git` / `archive` / `audits` 等）
- 文件 glob 豁免：规则表 `lib/lint_exempt.txt`（`audit-*.md` / `fix-plan-*.md` / `imap-*.html` 等）——bash（`hooks/lib/guards.sh`）与 Python（`lib/lint_exempt.py`）共读同一份，加 / 改豁免只动这张表

---

## § 5 修改 / 扩词 SOP

### 准入三问（新增禁词前必须过）

1. **这个词在中国 PM 的评审会 / 周会上会说吗？** 会 → 不是 AI 词，不硬禁
2. **去掉这个词，替换方案能保持语义精度吗？** 不能 → 不替换（如「拉新」≠「新用户」、「结构性」≠「整盘」）
3. **这是 AI 独有的空洞用法，还是中国 PM 圈的真实行业术语？** 后者 → 不硬禁，最多放软提醒

### 操作流程

1. 过三问 → 确定放 `AI_SLOP_TAILS`（硬禁）还是 `AI_SLOP_WARN`（软提醒）还是不改
2. 改 `banned_terms.py` 对应的列表
3. 改本文档 §2 表格同步
4. 跑 `python3 scripts/check_plain_language.py <既有文档>` 看是否误伤
5. 若误伤业务真词 → 回退到软提醒或移除

---

## § 6 反 AI Slop 总纲（结构层 · 只能 prompt 不能 hook）

写完产物自查 3 问（无法 hook 检测）：

1. **段落长度是否过于均匀**？AI 倾向 3-4 句一段、节奏整齐。人会混用 1 句段和 8 句段
2. **是否每段末尾都在升华**？真信息密度产物会有平淡段落
3. **是否有 "Bold 词: 解释" 三段式 bullet**？这是 ChatGPT 招牌结构

→ 共性铁律 / 反 AI slop 总纲在 [.claude/runbooks/human-voice-rules.md §⓪](../../.claude/runbooks/human-voice-rules.md)。

---

## 历史

- 2026-05-23 建本文档。整合 pm-strict.md / check_plain_language.py / output-style.md 三处分散禁词到单一真相源。中文 ChatGPT 味词扩 15 个（基于外部社区 ban list 调研）。
