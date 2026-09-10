# mermaid 语法坑对照表

> `gen_flow_base.py` 生成的 `.mmd` 已由 `_q()` 处理掉大部分坑。本表用于两类场景：
> ① mmdc 报 parse error 时定位；② 手改 / 手写 `.mmd` 片段时自查。
> 报错原文来自 mermaid 11.x parser，行号指 `.mmd` 里的行。

## 一、报错 → 原因 → 修法

> 下表每条都在本机 mermaid 11.16 上实测复现过；同含义的坑若下文没有，说明实测**不成立**，别照抄别处的说法。

| 报错 / 现象 | 原因 | 修法 |
|---|---|---|
| `Parse error … Expecting 'SQE', 'DOUBLECIRCLEEND', … got 'STR'` | label 里出现半角 `"`。mermaid **不支持 `\"` 转义**，引号一开一合就断 | 标签里的双引号换单引号 `'`（`_q()` 已自动处理）|
| `Lexical error … Unrecognized text` | 未加引号的 label 里出现 `/`，被当平行四边形语法 `[/text/]` | 加引号：`A["/plan-ceo-review"]` |
| `Parse error on line 1`（节点声明行）| 节点 id 撞了保留字：`class` `classDef` `click` `direction` `end` `graph` `linkStyle` `style` `subgraph` | 换 id，如 `end` → `finish` / `end_node` |
| stateDiagram 状态名带特殊字符 | 状态名未加引号 | `state "显示名" as id` |

## 二、引号规则（最容易搞混的一条）

| 位置 | 要不要引号 | 说明 |
|---|---|---|
| flowchart 节点 label `A["x"]` | ✅ 要 | 引号内是字面量，渲染时脱掉 |
| flowchart 边 label `A -->\|"x"\| B` | ✅ 要 | 同上 |
| stateDiagram 状态名 `state "x" as id` | ✅ 要 | 这是状态名的**语法本身** |
| **stateDiagram 边 label `A --> B : x`** | ❌ **禁** | mermaid 不脱这里的引号，会原文渲染成 `"业务系统同步入库"` |

状态机的边 label 用 `:` 分隔，所以 label 里不能再出现半角 `:`——`gen_flow_base._state_to_mermaid()` 会自动换成全角 `：`。

## 三、换行与排版

- `\n`（或写 `<br/>`）→ 多行。`_q()` 会把 Python 里的 `\n` 转成 `<br/>`。
- 自动换行由 `flowchart.wrappingWidth`（当前 220px）控制；**单行过长且没有可断点**（如一长串英文 / 路径）时不会换行，节点会被撑爆 → 显式用 `\n` 断行，或拆成两个节点。
- 中文没有空格，mermaid 按宽度断行，通常正常；遇到断得难看的句子用 `\n` 指定断点。

## 四、neo look 的两个副作用（都不报错）

### 4.1 描边渐变

`look: neo` 默认给**每个节点描边**挂 SVG 渐变，而不是纯色：

```js
gradientStart = primaryBorderColor      // 我们设成 #1F2329
gradientStop  = secondaryBorderColor    // 没设 → mermaid 自派，会落到浅绿 hsl(99,52%,85%)
stroke = useGradient ? "url(#<svgId>-gradient)" : nodeBorder
```

`secondaryBorderColor` 不设时，端点色由 mermaid 自己算，实测出 `hsl(99.13, 52%, 85.1%)` 的浅绿——表现是「节点边框一半深、一半泛绿」，像渲染坏了。

**修法：`themeVariables.useGradient: false`**，描边即退回 `nodeBorder` 纯色。作用域干净（实测只改 `.node rect / polygon / circle / path` 与 `.icon-shape .icon` 的描边，连线规则一条不动），且 `classDef` 的语义色带 `!important`，不受影响。

### 4.2 渲染不可复现（每次字节都不同）

neo look 的节点是 `<path>` 而非 `<rect>`，路径的控制点**每次渲染随机抖动**——同一条直线会写成不同的贝塞尔参数。几何等价、肉眼无差，但 SVG / PNG 字节每跑一次都变。产出的 `.svg` 要进 git，这会让每次重跑都产生无意义 diff。

```
A: path d="M-79.375 -22.5 C-24.325476607544076 -22.5, 30.72404678491185 -22.5, 79.375 -22.5 …"
B: path d="M-79.375 -22.5 C-20.82318981459545 -22.5, 37.7286203708091 -22.5, 79.375 -22.5 …"
                                        ^^^^^^^^^^^^^^^ 只有控制点 x 变，y 全等 → 直线不变
```

**修法：顶层 `"handDrawnSeed": 42`**（`0` = 随机，是默认值）。名字叫 handDrawn 但它同样管住 neo 的路径抖动——实测钉死后 SVG 与 PNG 双双可复现，尺寸与观感不变。`look: classic` 同样受影响，一并钉住。

## 五、渲染产物的两个已知限制

- **subgraph 标题永远是 `foreignObject`**：mermaid 的 cluster label 不走 `htmlLabels: false` 那条路径。影响面 = 泳道图的泳道名 + 普通流程图里的分组名。浏览器嵌 SVG 正常渲染；Inkscape / 印刷等非浏览器消费者会丢标题 → 这类场景出 PNG。
- **SVG 里的字体靠环境**：`themeVariables.fontFamily` 只声明字体名，不内嵌字体文件。渲染机装了 PingFang SC / Noto Sans SC 才好看；PNG 由 Chromium 在本机渲染，字体正确。

## 六、图型可用性

| 图型 | 需要 mermaid 版本 | 备注 |
|---|---|---|
| `flowchart` | 任意 10+ | |
| `stateDiagram-v2` | 任意 10+ | |
| `swimlane-beta` | **≥ 11.16** | 官方仍标 beta，语法后续可能变；本工区 mmdc 已 11.16+ |
