# promo-kit 多语言 + 品牌 Tag + 图上文字交付

> 做多语言宣发版本 / 配品牌 Tag / 要动截图里的图上文字前 Read。

## 品牌 Tag（短文案必加）

宣发短文案结尾必带品牌活动 Tag，按团队配置。Platform C 示例：

| 语言 | Tag |
|---|---|
| 中文 | `#Platform C进化论` |
| 英文 | `#Platform CEVOLVE` |
| 俄语 | `#Platform CEVOLVE` |

其他团队替换成自家品牌活动标签即可（一个中文标 + 一个拉丁字母标覆盖多数语种是常见做法）。Tag 是结尾 CTA 的一部分，不单独成行漂在文外。

## 多语言版本落法

- 命名：主稿 `launch-{feature}-{形态}.md`，外文版加语言后缀 `launch-{feature}-{形态}-{lang}.md`（如 `-en` / `-ru`）。同目录并列。
- **平行翻译不分叉**：外文版是主稿的平行版本，卖点 / 结构 / 分镜 / 配图一一对应，不擅自增删卖点。
- 语言列表**可配 N 语言**：视频分镜表的「截图（{语言}）」列按本次宣发投放语种增减，官方默认中/英/俄三列，不投的语种删列。
- 品牌名全篇统一（如 Platform C → Platform C）。

## 调性按语种本地化，不逐句直译（铁律）

**中英不是翻译关系，是各自母语的原生表达**：

- 英文宣发禁「中译英」长句。母语英文宣发是短句、节奏快、动词前置。
  - ❌ 中译英：`This feature lets you see your real spot cost and calculate your actual profit accurately`
  - ✅ 原生：`See your real cost. Know your true P&L.`
- 卖点句的「≤20 字」是中文约束，英文换算成**一行读得完**（约 8–12 词），不硬套字数。
- CTA 动词按语种习惯：中文「立即打开」，英文 `Open Platform C now` / `Try it`。

## 图上文字：On-Image String Map（不改图）

截图里 UI 的文字（多为源语言）需要出外文版时，**图一律由设计侧在设计工具里替换**，模型交付字串映射表，不声称能改图：

1. 从设计稿 / 截图列出本次 scope 内每个画面的图上文字（源语言）。
2. 落外文版 md 文末 `## On-Image String Map` 节，**按画面 / frame 分组**（如「资产页」「盈亏卡」各一张表），两列 `| 图上文字（源语言） | 替换为（目标语言） |`。
3. 混合稿常见（一个设计文件混多个需求的画面）：只映射本次宣发用到的画面，无关画面标「本次不涉及」。
4. 术语对齐行业通行叫法，不硬直译（如 现货盈亏 → Spot P&L，不逐字 spot profit and loss）。

> 若团队用 Figma：REST API 只读（读图层 / 导图），改不了画布文字，写画布需 Plugin API（本地开客户端 + 插件）。所以图上文字最终由设计侧替换，模型只给 String Map。
