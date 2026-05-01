# Crypto APP 视觉词汇库 · prototype skill

> 本文件薄。重头戏：① interaction-map/references/biz-*.md（Figma 真品 992 行业务组件） ② 本文 § B 真品组件代码（HTX Figma 直抽，直接 copy-paste 级）。
>
> **硬底线**：所有 Crypto 元素必须先查本文件 / 上述 references / Figma 真品。凭印象画 = 红线。

## A. 业务垂直 → imap references 路由表

| 项目业务 | 必读 imap references |
|----------|---------------------|
| 社区 / Feed / 牛人榜 / 个人主页 | `biz-social.md` + `components-core.md` |
| 交易 / 合约 / 跟单 / 现货 | `biz-trading.md` + `components-core.md` |
| 直播 / 礼物 / 弹幕 | `biz-livestream.md` + `components-core.md` |
| 通用 / 设置 / 资料类 | `components-core.md` + `templates-quickref.md` |

`check_paradigm.py` 输出建议清单，Step 1 按清单加载。

## B. prototype-only 真品组件（imap reference 没覆盖的）

每条带 ① Figma node ② 本地 anchor PNG ③ 直接 copy-paste 级 HTML/CSS。

### B1. iOS 状态栏 · 浅色 · iPhone 11/标准（375×44）

来源：[Figma App-Sparkle node 282-5797](https://www.figma.com/design/ewHDBGMTwKVgzcNW3B4FM0/?node-id=282-5797) · 本地：[figma-anchors/ios-statusbar-light.png](../assets/figma-anchors/ios-statusbar-light.png) · 节点 spec：[figma-anchors/ios-statusbar-light.spec.txt](../assets/figma-anchors/ios-statusbar-light.spec.txt)

- 总尺寸 375×44，bg `#FFFFFF`
- 时间「9:41」黑色 SF Pro，容器 54×21 r=32（圆角胶囊）
- 右侧状态区 67×11：信号 17×11 + WiFi 15×11 + 电池 24×11，全黑色 `#000000`，wifi/信号弱化填色 `#D9D9D9`
- 电池：外壳 22×11 r=2.68 + 接头 1×4 + 内填 18×7 r=1.34

### B2. iOS 状态栏 · 深色 · iPhone Pro（390×44）

来源：[Figma 社区交易卡片 node 1116-25679](https://www.figma.com/design/DUxCewcwzc5GKoP01K4TJy/?node-id=1116-25679) · 本地：[figma-anchors/ios-statusbar-dark.png](../assets/figma-anchors/ios-statusbar-dark.png) · spec：[../assets/figma-anchors/ios-statusbar-dark.spec.txt](../assets/figma-anchors/ios-statusbar-dark.spec.txt)

- 总尺寸 **390×44**（iPhone 15 Pro 宽 390 ≠ iPhone 11 的 375）
- bg `#000000`，时间 + 状态图标 `#FFFFFF`，wifi/信号弱化 `#DADADA`
- 其它结构与 B1 同

### B3. 状态栏 HTML 真品片段（深 / 浅可切）

```html
<div class="sbar" data-theme="dark">
  <span class="sbar-time">9:41</span>
  <div class="sbar-status">
    <span class="sig">●●●●</span>
    <svg class="wifi" viewBox="0 0 15 11" width="15" height="11">
      <!-- 三条弧 path 见 ../assets/figma-anchors/ios-statusbar-dark.spec.txt 第 14-17 行 -->
    </svg>
    <div class="bat"><div class="bat-fill"></div></div>
  </div>
</div>
```

```css
.sbar{display:flex;align-items:center;justify-content:space-between;padding:0 16px;height:44px;font-family:'HarmonyOS Sans SC','SF Pro Display',-apple-system;}
.sbar[data-theme="light"]{background:#FFFFFF;color:#000;}
.sbar[data-theme="dark"]{background:#000;color:#FFF;}
.sbar-time{font-size:17px;font-weight:600;letter-spacing:-0.3px;}
.sbar-status{display:flex;align-items:center;gap:5px;}
.sbar .bat{width:24px;height:11px;border:1.2px solid currentColor;border-radius:2.7px;position:relative;}
.sbar .bat::after{content:'';position:absolute;right:-3px;top:3.5px;width:1.5px;height:4px;background:currentColor;border-radius:0 1px 1px 0;}
.sbar .bat-fill{position:absolute;inset:1.5px;background:currentColor;border-radius:1.3px;width:18px;height:7px;}
```

### B4. HTX App 底部导航 · 双层结构（375×134）

来源：[Figma App-Sparkle node 12547-22326](https://www.figma.com/design/ewHDBGMTwKVgzcNW3B4FM0/?node-id=12547-22326) · 本地：[figma-anchors/htx-bottom-nav.png](../assets/figma-anchors/htx-bottom-nav.png) · spec：[figma-anchors/htx-bottom-nav.spec.txt](../assets/figma-anchors/htx-bottom-nav.spec.txt)

**关键反 v2 错觉**：HTX 底部导航不是单层 5-tab，是**双层 + 圆形交易主按钮**：

- 总尺寸 375×134，外圆角 r=20，bg `#191919`（暗灰）
- **上层 56px**「发现 / 关注 / 快讯 / 直播 / 公告」横向浮层 + 右侧 ^ 上拉展开
  - 字号 16px / weight 500 / line-height 20px / HarmonyOS Sans SC
  - 选中 `#FFFFFF` 白 + 下方 16×3 蓝色 `#007FFF` indicator
  - 未选 `#828282` 灰
- **下层 44px** 5 个 tab：home / market / trade / futures(探索) / assects(资产)
  - 每个 button 72×44，icon 区 64×28，label 字号 10px / weight 400
  - 「交易」中间是**圆形白底突出按钮 44×44 r=100**（FAB 样式），里面 ↔ 双向箭头
  - 选中态 `#FFFFFF` + 蓝色 `#007FFF` 高亮（首页选中时图标内部蓝色）
  - 未选 icon 全 `#828282`
- Home Indicator 区 34px，白条 134×5 r=100

```html
<nav class="htx-tbar">
  <!-- 上层浮层 tabs -->
  <div class="htx-tbar-top">
    <span class="t on">发现</span><span class="t">关注</span>
    <span class="t">快讯</span><span class="t">直播</span><span class="t">公告</span>
    <span class="caret-up">︿</span>
  </div>
  <!-- 下层主 nav -->
  <div class="htx-tbar-main">
    <div class="tab on"><i class="ic-home"></i><span>首页</span></div>
    <div class="tab"><i class="ic-market"></i><span>行情</span></div>
    <div class="tab tab-fab"><i class="ic-trade"></i><span>交易</span></div>
    <div class="tab"><i class="ic-explore"></i><span>探索</span></div>
    <div class="tab"><i class="ic-assets"></i><span>资产</span></div>
  </div>
  <div class="home-ind"><div></div></div>
</nav>
```

```css
.htx-tbar{position:absolute;left:0;right:0;bottom:0;background:#191919;border-radius:20px 20px 0 0;font-family:'HarmonyOS Sans SC',-apple-system,sans-serif;}
.htx-tbar-top{display:flex;align-items:center;height:56px;padding:0 16px;gap:18px;}
.htx-tbar-top .t{font-size:16px;font-weight:500;line-height:20px;color:#828282;position:relative;padding:8px 0;}
.htx-tbar-top .t.on{color:#FFFFFF;}
.htx-tbar-top .t.on::after{content:'';position:absolute;left:50%;transform:translateX(-50%);bottom:6px;width:16px;height:3px;background:#007FFF;border-radius:1.5px;}
.htx-tbar-top .caret-up{margin-left:auto;color:#FFFFFF;font-size:14px;cursor:pointer;}
.htx-tbar-main{display:flex;height:44px;border-top:1px solid rgba(0,0,0,.1);}
.htx-tbar-main .tab{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#828282;}
.htx-tbar-main .tab.on{color:#FFFFFF;}
.htx-tbar-main .tab span{font-size:10px;font-weight:400;line-height:14px;}
.htx-tbar-main .tab-fab{position:relative;}
.htx-tbar-main .tab-fab i{width:44px;height:44px;border-radius:50%;background:#FFFFFF;display:flex;align-items:center;justify-content:center;position:absolute;top:-12px;}
.htx-tbar-main .tab-fab span{margin-top:32px;}
.home-ind{height:34px;display:flex;align-items:center;justify-content:center;}
.home-ind div{width:134px;height:5px;background:#FFFFFF;border-radius:2.5px;}
```

### B5. Scene chips 顶部 nav（多 .scr 切换的核心导航）

来源：抽自 V8 / community v3 HTML（不是 Figma — Figma 没这种 prototype 工具栏）

```html
<div class="nav">
  <button data-s="a-1" class="on">A-1 Feed</button>
  <button data-s="a-2">A-2 落 TAB</button>
  <span class="sep"></span>
  <button data-s="b-1">B-1 主页</button>
  <!-- ... -->
</div>
```

```css
.nav{display:flex;flex-wrap:wrap;gap:3px;justify-content:center;max-width:480px;margin-bottom:14px;}
.nav button{font-family:inherit;font-size:9.5px;font-weight:700;padding:4px 7px;border-radius:4px;border:1px solid #334155;background:#1e293b;color:#94a3b8;cursor:pointer;transition:.12s;}
.nav button.on{background:#2979FF;border-color:#2979FF;color:#fff;}
.nav .sep{width:1px;background:#334155;margin:0 2px;}
```

### B6. Sticky CTA bar（订阅 + 铃铛 · v2 踩坑沉淀）

来源：v2 C-3 实战（[scenes_bc.py 208-211](../../../../projects/community/leaderboard/scripts/proto_v2/scenes_bc.py)）

```html
<div class="cta-bar">
  <button id="bellToggle" class="bell-btn" style="display:none;">🔔</button>
  <button class="cta-blue" onclick="_subscribe(this)">订阅<div class="cta-sub">45,927 位订阅用户</div></button>
</div>
```

```css
.cta-bar{position:absolute;left:0;right:0;bottom:24px;background:var(--bg);border-top:1px solid var(--border);padding:10px 14px;display:flex;align-items:center;gap:8px;z-index:30;}
.cta-blue{flex:1;background:var(--accent);color:#fff;border:none;padding:9px 0;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer;line-height:1.2;}
.cta-grey{background:var(--bg3);color:var(--text2);}  /* 订阅后追加，不 remove cta-blue 保留 flex:1 */
.bell-btn{background:var(--bg2);border:1px solid var(--border);color:var(--gold);width:42px;height:42px;border-radius:8px;font-size:16px;flex-shrink:0;}
.bell-btn.muted{color:var(--text3);}
```

⚠ JS 切换状态时**只 add `cta-grey,subscribed`，不 remove `cta-blue`**（否则 flex:1 丢失，按钮缩窄 — v2 第二轮 bug）。

### B7. 多 .scr 切换机制

来源：v2 [styles.py:26-29](../../../../projects/community/leaderboard/scripts/proto_v2/styles.py) + [js_helpers.py:4-17](../../../../projects/community/leaderboard/scripts/proto_v2/js_helpers.py)

```css
.scr{position:absolute;top:0;left:0;right:0;bottom:0;display:none;flex-direction:column;}
.scr.on{display:flex;}
```

```js
function go(id){
  document.querySelectorAll('.scr').forEach(s => s.classList.remove('on'));
  var t = document.getElementById('s-'+id);
  if (t) t.classList.add('on');
  document.querySelectorAll('.nav button').forEach(b => b.classList.toggle('on', b.dataset.s === id));
  if (t){ var bd = t.querySelector('.body'); if (bd) bd.scrollTop = 0; }
}
```

### B8. 抽屉 visibility 模式（防 paint 盖底部 nav）

来源：v2 styles.py 实战教训

```css
.app-mock .p-drawer:not(.show){visibility:hidden;pointer-events:none;}
```

`display:none` 太重（动画消失），但 z-index:501 不加 visibility 会 paint 盖底部 nav。`visibility:hidden` 是正确折中。

### B9. 全局滚动条隐藏（双引擎覆盖）

来源：v2 styles.py:118-119

```css
.phone *::-webkit-scrollbar{display:none;width:0;height:0;}
.phone *{scrollbar-width:none;-ms-overflow-style:none;}
```

需双引擎：webkit （Chrome/Safari）+ Firefox `scrollbar-width`。单一引擎在另一浏览器还会出滚动条 — v2 第二轮被嘲讽点。

## C. 反向抽取来源声明纪律

新增 prototype-only 条目时，每条必须标注来源（三类任一）：

1. **Figma node X-Y · 本地 ../assets/figma-anchors/xxx.png · spec：xxx.spec.txt**（最高权威 — HTX 自家真品）
2. **抽自 V8 / community v3 / activity-center v5.1 第 X 行**（标杆 HTML 反向抽）
3. **v2 踩坑沉淀**（实战教训）

无来源条目禁止合入 — 这是「不准凭印象」的形式化兜底。

## D. 字体栈纪律（HTX 钦定）

**所有 HTX prototype 必须**：

```css
font-family:'HarmonyOS Sans SC','Noto Sans SC',-apple-system,sans-serif;
```

HarmonyOS Sans SC 是 HTX 官方 Figma 全栈用的中文字体（确认见所有节点 `style.fontFamily`）。Noto Sans SC 是 fallback。把 HarmonyOS Sans SC 漏掉 = 视觉差一档。

数字字体走 'IBM Plex Mono' / 'JetBrains Mono'，与 HarmonyOS Sans SC 配合。

## E. Figma 真品扩展规则

后续遇到本文件未覆盖的 HTX UI 组件（卡片 / 抽屉 / chip / 下拉），同样规则：

1. 要 Figma 链接（用户提供 / 项目 inputs/figma-links.md）
2. `python3 scripts/fetch_figma.py <url> --image --batch ... --out-dir .claude/skills/prototype/assets/figma-anchors/`
3. `python3 .claude/skills/prototype/assets/figma-anchors/_extract.py <node>.json > <node>.spec.txt`
4. Read PNG（多模态）+ Read spec.txt 后写真品 HTML/CSS
5. 追加条目到本文 § B，标来源

不准跳过 1-3 步直接写 — 模型对 HTX 视觉的「印象」永远比真品差一档。
