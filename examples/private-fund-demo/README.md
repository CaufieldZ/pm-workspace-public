# Private Fund Subscription & Redemption — Demo

> **虚构项目** — 本 demo 业务场景为 PM Workspace 能力展示而虚构，不对应任何真实公司或产品。

选私募证券基金认申赎是因为它的合规链条足够典型（合格投资者 / 冷静期 / 大额赎回 / 净值披露），能完整展示 PM 工作流的「从模糊需求到 PRD 交付」全流程。

---

## 交付物速览

| 产出物 | 文件 | 规模 |
|---|---|---|
| 产品 Context | [`context.md`](context.md) | 9 章，5 个场景锁定 |
| 场景清单 | [`scene-list.md`](scene-list.md) | 2 个 View / 5 个场景 / P0 × 5 |
| 交互大图 | [`deliverables/imap-private-fund-v1.html`](deliverables/imap-private-fund-v1.html) | 单文件 HTML / 1173 行 / 9 个手机 mockup + 1 个 Web 后台 + 跨端数据流表 |
| PRD 文档 | [`deliverables/prd-private-fund-v1.docx`](deliverables/prd-private-fund-v1.docx) | Landscape 横版 / 8 个 H1 章 / 20 个表格 / 5 张 Scene 截图自动插入 |

## 生成耗时

Sonnet 4.6 模型，跟着 Skill 流水线跑：

| 阶段 | 时间 |
|---|---|
| context.md（Opus 决策产出） | 5 分钟 |
| scene-list.md | 1 分钟 |
| 交互大图 V1（Step A 骨架 + Step B fill + Step C 跨端表） | 10 分钟 |
| PRD V1（gen + 截图 + 插入） | 5 分钟 |
| **合计** | **~20 分钟** |

---

## 怎么看 demo

**交互大图**（浏览器打开 HTML）：

```bash
open deliverables/imap-private-fund-v1.html
```

5 个场景按 PART 分组：
- **PART 0 · H5 投资人端**：A-1 基金详情+认购 → A-2 协议签署+冷静期 → B-1 持仓+赎回入口 → B-2 赎回下单+大额顺延
- **PART 1 · Web 运营后台**：C-1 订单审核队列（认购/赎回双 Tab + 大额双签）

**PRD 文档**（Word/WPS 打开）：

```bash
open deliverables/prd-private-fund-v1.docx
```

8 章结构（挂原生 Heading style，自动生成目录）：
1. 项目背景与目标
2. 场景地图
3. H5 投资人端详细需求（4 个 Scene 表，左截图右需求）
4. Web 运营后台详细需求
5. 业务规则（R1-R5 合规 + B1-B6 业务）
6. 订单状态机（认购 10 步 + 赎回 8 步）
7. 非功能性需求（性能 / 可用性 / 兼容性）
8. 埋点与监控（H5 10 事件 + 后台 5 事件 + 漏斗 + 报警）

---

## 生成过程可复现

所有脚本都在 [`scripts/`](scripts/) 目录，拷贝到你自己的项目 `projects/{你的项目}/scripts/` 下，修改数据即可。

| 脚本 | 作用 |
|---|---|
| `gen_imap_v1.py` | 生成交互大图骨架（调 Skill 的 `generate_skeleton`）|
| `scenes_part0a/b.py` / `scenes_part1.py` | 每个 Scene 的 fill 函数，≤ 80 行 HTML/函数 |
| `fill_imap_v1.py` | 串联 fill 函数，填充骨架占位 |
| `step_c_imap_v1.py` | 插入跨端数据流表 + 底部 Callout |
| `gen_prd_v1.py` | 生成 PRD docx（调 Skill 的 `scene_table` / `make_table`）|
| `screenshot_for_prd.py` | Playwright 从交互大图截取 5 张 Scene 截图 |
| `insert_screenshots_to_prd.py` | 把 PNG 插入 docx 左列（`fix_dpi()` 防虚化）|

---

## 设计取舍

几个典型的「本 demo 跳了什么 / 保留了什么」：

- **跳掉原型**（`prototype` Skill）— 交互大图 + PRD 已能展示完整闭环，demo 项目不做原型避免重复
- **跳掉 bspec / pspec / test-cases** — 这三者是给下游 AI Agent 消费的，需要配套的研发/设计/QA 环境才有价值
- **保留合规章节**（R1-R5）和**埋点章节**（8 章）— 金融产品 PRD 没有这两章就不成立，宁可重也不省
- **跨端数据流表** — 交互大图内嵌表格展示 H5 ↔ Web 后台的数据契约，补足"图像看不出字段"的缺失
