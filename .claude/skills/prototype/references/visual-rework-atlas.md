---
name: visual-rework-atlas
description: 原型视觉失分图鉴——症状 / 反例 / 正例逐条对照，Step 2 样板页做完与 Step 3 自评时逐项过
type: reference
---

# 原型视觉失分图鉴

> 这些是评审会指出来、需要返修的具体位置。每条给「反例 → 正例」的可直接替换写法。
> 组件层 `assets/crypto-dark.css` 已把正例做成 `cx-` class，优先用 class，不照抄 CSS。

## 一、补齐顺序（先看这条，它决定其余条目的优先级）

向标杆看齐的补齐顺序：**内容密度 → 动效 → 质感 → 微交互 → 层次**。

**空屏是评审第一眼最大的减分项。** 一屏只有三张卡、大片留白、字段名写「标题 / 描述」，比配色不准严重得多。交易所页面的常态是一屏承载真实字段全集（持仓卡 = 收益 + 收益率 + 持仓量 + 初始保证金 + 保证金率 + 开仓均价 + 最新价 + 预估强平价，八个字段同屏），不是三个卡片撑满。

因此 `anti-ai-slop.md` 的「留白 ≥ 40%」**不适用于本 skill 的对客交易 / 直播页面**，按真品密度走。留白规则仍适用于 ppt / 架构图。

配套：数据用接近真实的示例（`BTCUSDT 永续` / `20X` / `全仓` / `一键平仓`），不用 `示例标题` / Lorem ipsum。

## 二、素材：零 emoji

图标 / 头像 / logo / 走势图 / 状态栏一律走 `scripts/lib/icons.py` 的矢量件，不用 emoji 顶替。

| | 写法 |
|---|---|
| ❌ | `<span>📊</span>` `<span>🔥</span>` `<div class="avatar">👤</div>` `<span>📶</span>` |
| ✅ | `ic('chart', 16)` · `logo_svg(22)` · `avatar_monogram('Edward', 34)` · `signal_svg()` |

`lib/icons.py` 公共件：`ic(name,size,color)` 线性图标 · `avatar_monogram(name,size)` 按名字 hash 分配 6 色盘的字母头像 · `logo_svg(size)` · `_TONE` 涨跌色。业务特有素材（行情封面 / 迷你走势线）建项目 `src/icons.py` 复用 lib 的 token 再补，不另起一套。

**建共享层前先 `ls` 项目 `src/` 看有没有现成的素材工厂**，有就复用。

两个连带坑：

- 头像不要用灰色单色剪影，识别度为零 —— 用 `avatar_monogram()`，同一页多个头像颜色自然分开。
- **多处复用同一个 SVG 字符串变量会撞 `clipPath` / `linearGradient` 的 id**，后出现的那个渲染成空白。素材函数内部要用自增计数器生成 id（`lib/icons.py` 已这么做），别把 SVG 存成模块级常量到处 `+`。

## 三、卡片与圆角

| 症状 | ❌ | ✅ |
|---|---|---|
| 卡片描边显脏 | `border:1px solid #23282F` | 去掉边框，靠底色差分层：`#161A1E` on `#0B0E11`（`.cx-card`）|
| 网页感圆角 | `border-radius:10px` / `11px` 用在卡片 | 卡片 / 面板 `16px`，控件 `8px`，胶囊 `10px`（`.cx-card` / `.cx-btn` / `.cx-tag`）|
| badge 像标签纸 | `border-radius:3px~4px` 的方角 | 全胶囊 `10px`（`.cx-tag` / `.cx-badge-live`）|
| 封面发灰发脏 | `linear-gradient(135deg,#1E2A38,#141A20)` | 饱和蓝调 `linear-gradient(135deg,#1a3a5c,#0d2035)`（`.cx-cover`）|

**无边框规则的例外**：底色亮度差不够时不成立。`#161A1E` on `#0B0E11` 这一级对比 + 密集垂直堆叠的**后台控制台面板**必须保留 hairline 定界，用 `.cx-panel`（12px 圆角 + `1px solid #2B3139`）。对客 App / Web 前台一律 `.cx-card` 无边框。判据看对比度和堆叠密度，不看端。

## 四、悬浮与选中

| 症状 | ❌ | ✅ |
|---|---|---|
| hover 像 2019 年 | `:hover{border-color:#007FFF}` | `transform:translateY(-2px); box-shadow:0 10px 28px rgba(0,0,0,.36)`（`.cx-card.tap`）|
| 列表选中态糊 | 整行换底色或描边 | 2px 蓝色左缘 accent（`.cx-row.on`）|
| 待填充位置像坏了 | 实心灰块 | 虚线占位框（`.cx-slot-empty`）|

手机端没有 hover，App 端用 `:active` 的按压缩放（`.cx-tap`），不写 hover。

## 五、数字排版

交易所页面主体是数字，这一条的返修率最高。

| ❌ | ✅ |
|---|---|
| 数值和单位同字号同色 | 数值提亮加粗（`.cx-num`），单位留灰小一号（`.cx-unit`）|
| 比例字体，上下行位数对不齐 | `font-variant-numeric:tabular-nums`（`.cx-num` 自带）|
| 涨跌只靠 `+/-` 号 | 配 `.cx-up` / `.cx-dn` 染色，标签走浅底色字 `.cx-tag.up/.dn`（不用饱和色铺满整块）|
| 可解释字段（开仓均价 / 预估强平价）无提示 | 加虚线下划线 `.cx-dsh` |

## 六、浮层与玻璃

- 深色 UI 上的浮层用暗玻璃 `#1C2636` + `1px solid rgba(255,255,255,.08)`（`.cx-glass`），不用纯白 `#fff` 盖上去。
- **液态玻璃先看背后有没有真画面**：近黑 / 纯色底上 `backdrop-filter` 等于没写，配底比调参数重要。
- 玻璃只给常驻控件（输入栏 / 按钮）。逐条增删的弹幕、列表项不上玻璃 —— 掉帧且字发飘。
- `mask-image` 的祖先会切断后代的 `backdrop-filter` 取样源。

## 七、弹窗与滚动

- 弹窗 `max-height:80vh` 必须配 `overflow-y:auto`，否则底部主按钮被裁掉点不到。
- 底部主按钮保持原位不吸底 —— 用户填完参数才点它，吸底浪费弹窗空间。
- 手机壳内 `.cx-body` 必须 `flex:1; min-height:0; overflow-y:auto`，少了 `min-height:0` 内容会溢出机框。
- 抽屉在手机壳内底部上推，绝对定位在 `.app-mock` 内，不脱出机框。

## 八、动效

- **已有自动轮播 / 自动滚动的组件不要再叠第二层动画**：两个周期不整除，信息可读性退化成随机抽奖。
- 跑马灯：内容重复两遍走 `translateX(-50%)` 无缝循环（`.cx-marquee`），别用 `padding-left:100%` 起手（有一段空转期）。
- 位移作用在**内层 track**，不能作用在 `overflow-x:auto` 的滚动容器自身 —— 整条会被祖先 `overflow:hidden` 裁掉变空白。要么改写 `scrollLeft`，要么位移内层。
- 移动端横滑手势别在 `pointerdown` 就 `setPointerCapture`，会吞掉子元素 click；等移动超过约 6px 判定为拖拽后再捕获。
- 读 `offsetHeight` 做高度自适应的实现，在页面隐藏时会静默跳过赋值 —— 改卡片高度前先确认首屏就生效，否则表现为塌高。

## 九、静默失效（不报错但页面是错的）

- **JS 拼 class 必须确认 CSS 里真有那个类名**：`class="x " + item.tone` 拼出 `x up`，CSS 里没有 `.up` 就是静默无样式。样式类 bug 优先查这一条。
- **改场景 HTML 字符串后必数 div 开闭配平**：少一个闭合会把后续场景重排进当前容器、把壳外标注挤进壳内。`check_proto.sh` 拦不住这类结构错，只能靠数和看截图。
- 克隆场景前先 grep 项目 `crud.py` 查 CSS class 的作用域前缀（`.arow .v` 这种后代选择器，脱离 `.arow` 就裸了）。
- 状态切换靠**叠类**不靠换类：`add('done')` 而不是 `remove('pri')`，否则按钮失去 `flex:1` 宽度跳变。CSS 用复合选择器 `.cx-btn.pri.done{...}` 承接。

## 十、真品对照纪律

素材权威性从高到低：

1. **PM 直接给的矢量 / 源文件**（源码注释标了「PM 给的矢量 / PM 提供」的，权威性最高，别拿事后补的真机截图去覆盖它）
2. Figma 真品（`assets/figma-anchors/`）
3. 竞品 / 线上真机截图

动手画版式前，`inputs/` 里的截图**逐张 Read 完**。页面结构 / Tab 名 / 字段名一律照抄，不推测、不精简。凭印象画出来的假 Tab 假字段，返修时要整屏重排。

交易页组件尤其要逐字段核对 —— 真品的合约持仓卡含保证金三列 + 强平价 + 已实现盈亏条 + 四按钮，凭印象画会漏掉一半。缺实拍截图就向 PM 要，不要先画了再说。

## 十一、文案

原型里的文字给用户看，不是给评审看规格。

- 留删判据：**使用者在这个页面做决定时需要知道的才留**。解释系统内部机制、「本轮 / 取代原先」这类版本语言、研发算法口径一律不进原型（那些属于 PRD）。
- 渲染壳内禁开发注解：`（此处占位）` / `（灰条占位）` / `注：` / `TODO` 会被开发误读成真实产品文案。
- 禁裸场景编号（`A-1`）/ 决策号（`见决策 3`）。
- 评审用的 devbar / 场景 chip 不是用户路径，不写进 PRD 验收。

## 十二、整页示例（照抄改字段即可）

下面这页零自写 CSS，`audit_against_baseline.py` 16 项全绿。config.py 里给足 project 字段，
壳上的 logo / 状态栏 / 顶导按钮就都不是 emoji：

```python
from lib.icons import ic, avatar_monogram, logo_svg

project = {"name": "Platform C", "version": "3.4",
           "css_packs": ["crypto-dark"],
           "logo_html": logo_svg(20),
           "status_html": ic("signal", 12) + ic("wifi-off", 12),
           "nav_right_html": ic("wallet", 13)}

def page_app_pos():
    return f'''
<div class="cx-pagehead"><span class="t">持仓</span><span class="cx-ib">{ic('more-h',18)}</span></div>
<div class="cx-tabs">
  <div class="cx-tab" onclick="cxTab(this,'pos','order')">全部委托</div>
  <div class="cx-tab on" onclick="cxTab(this,'pos','hold')">持仓 (3)</div>
  <div class="cx-tab" onclick="cxTab(this,'pos','bot')">交易机器人</div>
</div>
<div class="cx-pills">
  <div class="cx-pill on" onclick="cxPill(this)">全部</div>
  <div class="cx-pill" onclick="cxPill(this)">永续</div>
  <div class="cx-pill" onclick="cxPill(this)">现货</div>
</div>
<div class="cx-body" style="padding:10px 16px" id="pos-hold">
  <div class="cx-card tap">
    <div style="display:flex;align-items:center;gap:6px">
      {avatar_monogram('Edward', 22)}
      <b style="font-size:13.5px">BTCUSDT 永续</b>
      <span class="cx-tag up">多</span><span class="cx-tag mut">全仓</span><span class="cx-tag mut">20X</span>
    </div>
    <div class="cx-grid">
      <div><span class="k">收益(USDT)</span><span class="vb cx-up">+1,240.00</span></div>
      <div><span class="k">收益率</span><span class="vb cx-up">+8.00%</span></div>
    </div>
    <div class="cx-grid">
      <div><span class="k">持仓量(BTC)</span><span class="v">0.500</span></div>
      <div><span class="k">初始保证金</span><span class="v">1,500.00</span></div>
      <div><span class="k">保证金率</span><span class="v">182.66%</span></div>
    </div>
    <div class="cx-grid">
      <div><span class="k cx-dsh">开仓均价</span><span class="v">60,000.0</span></div>
      <div><span class="k">最新价</span><span class="v">64,800.0</span></div>
      <div><span class="k">预估强平价</span><span class="v">57,320.0</span></div>
    </div>
    <div class="cx-btns" style="margin-top:10px">
      <button class="cx-btn">平仓</button><button class="cx-btn">反手</button>
      <button class="cx-btn pri" onclick="openShare()">分享</button>
    </div>
  </div>
</div>'''
```

三行字段网格是**故意的**：真品持仓卡就是八个字段同屏，别为了「干净」删成两行。

交互函数随组件层一起拼入（`crypto-dark.js`）：`cxTab(el,group,tab)` 切 Tab 并显隐 `#{group}-{tab}` 面板 ·
`cxPill(el)` 胶囊单选 · `cxRow(el)` 列表行单选 · `cxSheet(id,show)` 底部弹层（自动建遮罩、点遮罩关）·
`cxToggle(el,onText)` 叠类式状态切换 · `cxToast(msg)`。**别用骨架的 `switchTab`** —— 它绑的是
`.p-tab` 和固定的 `ongoing/upcoming/ended` 面板 id，形状对不上 cx- 组件，点了没反应。

列表项的次要信息（观看数 / 时长 / 播放键）同样不用 emoji 顶替 —— `👁 12.4万` / `▶` 要换成
`ic('eye',11)` / `ic('play',18)`，这是壳内 emoji 最常见的漏网处。
