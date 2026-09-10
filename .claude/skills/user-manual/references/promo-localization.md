# 营销稿多语言 + 图上文字交付

> 写 `promo-` 多语言版本 / 要动 Figma 图上文字前 Read。手册（`user-manual-`）也可复用「图上文字」一节。

## Figma 只读铁律（先认清能力边界，别赌）

工区 figma MCP（`figma-developer-mcp`）+ `fetch_figma.py` 走的都是 Figma **REST API**，**只读**：

- 只有两个能力：`get_figma_data`（读图层结构 / 文字节点）、`download_figma_images`（导 PNG / SVG）。
- **改不了画布**——REST API 官方不提供写画布文字 / 排版的接口。
- 唯一能写 Figma 的路径是 **Plugin API**：需用户本地开着 Figma 客户端 + 装桥接插件 + 连 WebSocket，纯后台 API key 做不到。

结论：**图上的外文，最终一律由设计侧在 Figma 里替换**。模型能做的是把译文给全 + 对齐图层，让替换零思考——即 On-Image String Map。别声称能编辑 Figma。

## On-Image String Map（图上文字译文交付规范）

图上文字（截图里 UI 的中文）翻译，落**字串映射表**交给设计侧照替，不改图：

1. `python3 scripts/call_mcp.py call figma get_figma_data fileKey="<KEY>"` 拉全文字节点（`grep 'text:'` 提取）。
2. 落 `promo-{feature}-{lang}.md` 文末 `## On-Image String Map` 节，**按面板 / frame 分组**（如「交易卡」「闪电下单抽屉」「Feed」各一张表），两列 `| Figma text (ZH) | Replace with (XX) |`。
3. 混合稿常见（一个 Figma 文件混多需求的 frame）：只映射本次 scope 内 frame 的字串，无关 frame 标一句「ignore for this launch」。
4. 术语随品牌：中文「Platform C」→ EN「Platform C」；字段级译法对齐交易所通行叫法（如 本金金额→Amount、可开多→Max long），不硬直译。

## promo- 多语言版本落法

- 命名：主稿 `promo-{feature}.md`，外文版 `promo-{feature}-{lang}.md`（如 `-en`）。同目录并列。
- 单源不分叉仍成立：外文版是主稿的**平行翻译**，卖点 / 结构 / 配图索引一一对应，不擅自增删卖点。
- 调性**按渠道分别本地化**，不是逐句直译（见下）。品牌名全篇统一（Platform C→Platform C）。

## KOL / 营销口吻分档（mock 晒单文案 · 中英语域）

营销稿里的「示例晒单 / KOL 帖」mock 文案，先定**调性档位**（塞官方宣发截图有品牌背书取舍，默认中等）：

| 档位 | 中文 | 英文（CT = Crypto Twitter） |
|---|---|---|
| 官方 clean | 专业克制，不玩梗 | 完整句、正字，不用黑话 |
| **中等（默认）** | 有 KOL 味不脏：吐槽感 / 凡尔赛喊单，保留「家人们 / 回踩上的车 / 让利润奔跑」，去最脏的（梭哈 / 干就完了） | native CT 语感：碎句、`ser` / `fomo` / `NFA` 可留，去掉 `diamond handing` / `wagmi` / 全小写 degen |
| degen 满配 | 大饼 / 梭哈 / 老铁全上 | 全小写 + `wagmi` / `ape` / `rekt` / emoji，最真实但最「不官方」 |

**中英不是翻译关系，是各自母语的原生表达**（关键铁律）：

- 英文 mock **禁「中译英」长句**。真实 CT 是碎句、短、meme 密度高。
  - ❌ 中译英：`while everyone was panic-selling that dip and crying in the group chat, I said it plain`
  - ✅ 原生 CT：`everyone panicking at the dip while i said it plain — trendline held`
- 光挂 `ser` / `NFA` ≠ CT 调性；节奏（碎句 + 全小写感）才是。
- 中文币圈黑话有对应梗则用对应梗，无对应则换 native 表达，不硬造。
