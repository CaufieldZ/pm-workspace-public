# PRD 讲人话规范

PRD 是产品 / 业务 / 项目经理读的文档，**正文必须讲人话**。一眼看出 AI 写的就违规。

下游消费文档（bspec / pspec / test-cases）不受此约束——研发 / QA / 设计师消费，允许字段名 + 像素 + 编号引用。

---

## 三类违规

### 1. 流水账 / 版本痕迹（FAIL，硬阻断）

PRD 描述当前状态，不写讨论流水。多轮迭代过程归 `context.md` 第 7 章。

| 违规 | 反例 | 正例 |
|------|------|------|
| `(YYYY-MM-DD ...)` | "选中态（2026-04-23 新增）" | "选中态" |
| `(from vN ...)` | "数据看板指标（from v47）" | "数据看板指标" |
| `(变更)` `(新增)` | "📱 E-1 · 合约抽屉（变更）" | "📱 E-1 · 合约抽屉" |
| 决策 #N | "本次决策 #14 不做 CMS" | "本次不做 CMS" |
| `反转说明：` | "反转说明：推翻 3-14 决策 #2" | （整段删除） |
| `砍掉：` | "砍掉：原对手价快捷按钮" | （整段删除，PRD 描述当前状态不写来历） |
| `（中文别名匹配 ... 砍掉）` | "Symbol 精确匹配（中文别名匹配 2026-04-22 砍掉）" | "Symbol 精确匹配" |

### 2. 代码字段 snake_case（WARN）

PRD 给 PM 读，正文应改白话。

| 字段 | 白话 |
|------|------|
| `card_type:futures_holding` | 卡片类型：合约持仓 |
| `is_same_symbol` | 是否同一币对 |
| `related_card_id` | 卡片归因 ID |
| `card_id` / `post_id` / `order_id` | 卡片 ID / 帖子 ID / 订单号 |
| `pair_init` / `pair_final` | 初始交易对 / 最终交易对 |
| `has_trade_card: bool` | 是否含交易卡片 |
| `closed (normal)` / `closed (liquidated)` | 已平仓（普通）/ 已平仓（强平） |
| `holding` `closed` | 当前持仓 / 已平仓 |
| `placeholder` `label` `toggle` `confirm` | 占位 / 标签 / 切换 / 确认 |

**例外（豁免）**——这些位置必须保留原始 snake_case 给研发对账：

| 豁免位置 | 判定方式 |
|----------|----------|
| H2 标题含「枚举值 / 字段 / 埋点 / 事件 / 参数 / 对照 / 核心 ID / 归因」 | 整章豁免 |
| 表头含「ID / 字段 / 事件 / 参数 / 枚举 / 指标 / 触发 / 层级 / 路由」 | 整表豁免 |

例：6.7 枚举值列表 / 6.4 归因字段对照 / 8.3 事件列表 / 核心 ID 对照表，全部保留原始字段名。

### 3. UI 设计参数（WARN）

PRD 描述 What 不描述 How。像素 / 颜色 hex / 动画 ms / 字体 / 字号字重，归设计稿。

| 违规 | 处理 |
|------|------|
| `342px / 高 44px / 圆角 8px` | 删 |
| `#007FFF` `rgba(0,0,0,.4)` | 删 |
| `300ms` 动画时长 | 删 |
| `opacity .4 / 不可点` | 改 "灰态不可点" |
| `mono 26px 900 粗` | 整段 "字体：xxx" / "字号：xxx" bullet 删除 |
| `font-size:` `border-radius:` `linear-gradient` | 删 |

**例外**：第 7 章非功能性需求里的 `≤ 300ms` 响应指标、`1280px` 兼容性下限——是性能 / 兼容契约，保留。

---

## 工具链

```
                       讲人话规范在 references/prd-human-voice.md（本文）
                              │
                              ▼
            check_prd_human_voice.py  ← 共享扫描模块（被两边调用）
            ├─ scan_human_voice(doc) → 三类 hits
            └─ report_violations(result) → stderr 报告
                  │                            │
                  ▼                            ▼
     check_prd.sh                    push_to_confluence_base.gate_check_quality
     （本地高频自检）                  （推 wiki 前最后兜底）
                  ▲
                  │
                  └────── humanize_prd_voice(doc, extra_jargon)  ← 自动修复 helper
                          PRD_CHANGELOG_PATTERNS
                          PRD_JARGON_REPLACEMENTS
                          PRD_UI_STRIP_PATTERNS
                          PRD_TRAILING_JUNK_PATTERNS
                          KILL_BULLET_KEYWORDS
                  ▲
                  │
                  └────── save_prd(doc, path, extra_jargon)  ← 一键保存 wrapper
                          自动 humanize + 标点 + 字体 + theme + 扫描
```

### gen / update / patch 脚本写法（推荐）

```python
import re
from gen_prd_base import save_prd

# 项目特定字段映射（业务术语换中文）
PROJECT_JARGON = [
    (re.compile(r'`?futures_holding`?'), '合约持仓'),
    (re.compile(r'`?spot_holding`?'), '现货持仓'),
    # ...
]

# 写完 doc 后一键保存（自动 humanize + 标点 + 字体 + theme）
save_prd(doc, OUTPUT, extra_jargon=PROJECT_JARGON)
```

### 老脚本（直接 doc.save）改造

把 `doc.save(path)` 改成 `save_prd(doc, path, extra_jargon=...)`。或自己手动调：

```python
from update_prd_base import (
    humanize_prd_voice, normalize_punctuation, normalize_fonts, ensure_theme,
)

humanize_prd_voice(doc, extra_jargon=PROJECT_JARGON)
normalize_punctuation(doc)
normalize_fonts(doc)
doc.save(path)
ensure_theme(path)
```

### 单独跑扫描

```bash
python3 .claude/skills/prd/scripts/check_prd_human_voice.py <docx>
# exit 1 if 流水账 hits（FAIL）；snake_case + CSS 只 WARN 不阻断
```

---

## 三道闸串联（设计原则）

1. **save_prd**（gen / update 时）—— 第一道，doc.save 前自动洁化，新产 PRD 默认人话
2. **check_prd.sh**（本地自检 / hook 拉起）—— 第二道，所有改动后自动跑，本地阅读也能拦
3. **push gate**（推 Confluence 前）—— 第三道，最后兜底，违规拒推

只在第 3 道做意义不大——本地 docx 也是给人读的，且不是所有 PRD 都推 Confluence。第 1 道是治本，第 2/3 道是兜底。

---

## 历史

- 2026-04-29: 沉淀。proj-community v3.4 PRD 抛光后用户反馈「PRD 是人读的必须讲人话」，把 patch_prd_v3_4_polish.py 通用规则提取成 helper + scan 模块，三道闸接入。规则文件 + 共享扫描 + 自检接入 + push gate 复用 + save_prd 一键 wrapper。
