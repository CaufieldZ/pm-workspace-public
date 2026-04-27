<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# 交互大图 · 黄金片段参考（从高质量样本提取）

> 填充时如不确定组件写法，直接复制以下片段修改内容即可。

## 1. 完整注释卡（含全部子组件）

**为什么好**：card-title 带 ann-tag 标明优先级，每个 ann-item 有结构化 ann-num + ann-text + ann-tag，末尾 info-box 补充说明。层次清晰，信息密度高。

⚠️ **本 skill 自 2026-04 起不承载变更**：`ann-tag.new/chg/del` 已退役，仅保留 `ann-tag.p0/p1/p2` 优先级标签。下方示例已对齐新规范。

```html
<div class="ann-card" style="align-self:flex-start;margin-top:36px;">
  <div class="card-title">📋 顶部栏与连麦区 <span class="ann-tag p0">P0</span></div>
  <div class="ann-item">
    <div class="ann-num blue">1</div>
    <div class="ann-text"><b>顶部栏</b><br>
      在线入口为头像堆叠 + 人数，点击弹出底部弹层 → <a href="#scene-a" style="color:var(--blue);text-decoration:none;font-weight:700;">见 A ↗</a></div>
  </div>
  <div class="ann-item">
    <div class="ann-num green">2</div>
    <div class="ann-text"><b>连麦嘉宾区</b><br>
      1 主播 + 最多 8 嘉宾横排。头像 + 昵称 + 波纹 + 麦克风角标</div>
  </div>
  <div class="info-box blue"><b>主播 App 端 = 本图</b>（无管理功能，管理走 Web）</div>
</div>
```

## 2. 标注框（包裹屏幕内元素）

**为什么好**：`position:relative` 父容器 + `.anno` 虚线绝对定位 + `.anno-n` 编号圆点，让读者一眼知道注释卡的「1」对应屏幕哪个区域。

⚠️ **anno-n 与 ann-card 的 ann-num 字符样式必须一致**（详见 SKILL.md 规则 4）。默认用阿拉伯数字 `1 2 3`，**不要混用** `①` 和 `1`——读者在屏幕上看到 ① 找不到 ann-card 里的 1，编号无法对应。

```html
<div style="position:relative;margin-top:12px;">
  <div class="anno amber" style="top:-4px;left:-4px;right:-4px;bottom:-4px;">
    <div class="anno-n amber">1</div>  <!-- 阿拉伯数字，与 ann-num 一致 -->
  </div>
  <div style="background:linear-gradient(135deg,var(--blue),#1565C0);border-radius:10px;padding:14px;text-align:center;">
    <div style="font-size:14px;font-weight:800;color:#fff;">核心操作按钮</div>
    <div style="font-size:10px;color:rgba(255,255,255,.6);margin-top:2px;">按钮说明文字</div>
  </div>
</div>
```

## 3. 箭头（屏幕间连接）

**为什么好**：语义化的 `.aw` 容器，箭头线 `.al` + 文案 `.tx` 分离，颜色通过后缀类名控制。

```html
<div class="aw">
  <div class="al g"></div>
  <div class="tx g">点击开通</div>
</div>
```

颜色速查：`.b` 蓝 / `.g` 绿 / `.r` 红 / `.p` 紫 / `.a` 琥珀

## 4. 信息框（3 种颜色）

```html
<!-- 蓝色：未改动说明 / 备注 -->
<div class="info-box blue"><b>未改动：</b>状态栏、主舞台、PiP、关闭按钮</div>

<!-- 琥珀色：注意事项 / 配置依赖 -->
<div class="info-box amber">红包/粉丝群开关在 CMS 后台配置（截图中已有字段）</div>

<!-- 紫色：技术说明 -->
<div class="info-box purple"><b>技术：</b>TRTC Web SDK 全链路（音视频采集 + 连麦混流 + 拉流转推）</div>
```

## 5. 排版层次

```
font-weight:900 → PART 标题、场景标题、关键数字（如价格）
font-weight:700 → 卡片标题(.card-title)、按钮文字、强调关键词(<b>)
font-weight:400 → 正文说明(.ann-text 内非 <b> 部分)、次级信息、备注
```

## 6. 跨场景引用 = 缩略预览 + 锚点超链接

某 phone 引用其他 scene 内容（如「内容 TAB 详见 C」「嵌牛人榜战绩组件」），**禁止纯文字「详见 X」死链**。两条合法路径，按可读性优劣排序：

**模板 A · 缩略预览 + 锚点（推荐）**：占位区画 2-3 行真实结构化内容，底部加可点击锚点。

```html
<div style="background:var(--dark2);border-radius:6px;padding:8px;display:flex;flex-direction:column;gap:6px;">
  <div style="background:var(--dark);border-radius:4px;padding:6px 8px;">
    <div style="font-size:10px;color:var(--dark-text);font-weight:700;">BTC 突破 71000…</div>
    <div style="font-size:8px;color:var(--dark-text3);">3h · 124 阅读</div>
  </div>
  <div style="background:var(--dark);border-radius:4px;padding:6px 8px;">
    <div style="font-size:10px;color:var(--dark-text);font-weight:700;">现货长线策略复盘</div>
  </div>
  <a href="#scene-c" style="font-size:9px;color:var(--blue);text-align:center;padding:2px;text-decoration:none;font-weight:700;">查看完整 → C ↗</a>
</div>
```

**模板 B · 嵌入战绩组件迷你卡**（数据型场景）：

```html
<div style="background:linear-gradient(135deg,rgba(14,203,129,0.10),transparent);border:1px solid rgba(14,203,129,0.25);border-radius:8px;padding:10px;">
  <div style="font-size:9px;color:var(--dark-text3);">累计收益率（30d）</div>
  <div style="font-size:20px;color:var(--green);font-weight:900;font-family:'JetBrains Mono',monospace;">+173.12%</div>
  <div style="height:24px;margin:4px 0;">
    <svg width="100%" height="24" viewBox="0 0 100 24"><polyline points="0,20 12,18 28,14 45,16 60,10 75,5 90,3 100,1" stroke="#0ECB81" stroke-width="1.5" fill="none"/></svg>
  </div>
  <a href="#scene-c" style="display:block;font-size:9px;color:var(--blue);text-align:center;text-decoration:none;font-weight:700;">查看完整战绩 → C ↗</a>
</div>
```

**TAB bar 整体可点击**（每个 TAB 标签都设锚点）：

```html
<div style="display:flex;gap:14px;border-bottom:1px solid var(--dark2);padding:8px 0;">
  <a href="#scene-c" style="font-size:12px;color:var(--dark-text);font-weight:700;border-bottom:2px solid var(--blue);padding-bottom:6px;text-decoration:none;">内容</a>
  <a href="#scene-c" style="font-size:12px;color:var(--dark-text3);text-decoration:none;">交易战绩</a>
  <a href="#scene-c" style="font-size:12px;color:var(--dark-text3);text-decoration:none;">带单战绩</a>
</div>
```

**锚点 id 来源**：骨架的 `<div class="fade-section" id="scene-{a-g}">`（小写主场景字母），所以 `href="#scene-c"` 跳到主场景 C 开头。子场景级别 anchor 当前骨架不区分，跳到主场景已够。

## 7. 反模式 vs 正确写法

| 反模式（❌） | 正确写法（✅） |
|-------------|--------------|
| `<div class="ann-card"><div class="ann-num">1</div>说明文字</div>` | 完整结构：ann-card > card-title + ann-item > ann-num + ann-text（见 §1） |
| 无 `.anno` 框，注释卡悬空无对应 | 屏幕内目标元素用 `.anno.{色}` 包裹 + `.anno-n` 编号（见 §2） |
| **anno-n 用 `①` 但 ann-num 用 `1`** | 字符样式必须一致，默认阿拉伯数字（见 §2 + SKILL 规则 4） |
| 屏幕间无 `.aw` 箭头 | 每两个有流向关系的屏幕间必须有 `.aw`（见 §3） |
| 注释卡无 `.ann-tag`，不知道优先级 | card-title 和 ann-text 内加 `.ann-tag.{p0/p1/p2}`（见 §1）。`new/chg/del` 已退役 |
| **「内容 TAB 详见 C-1」纯文字** | 缩略预览 + `<a href="#scene-c">` 锚点（见 §6） |
| 全文 font-weight:700，无层次 | 3 级层次：900 / 700 / 400（见 §5） |
| 无 `.info-box`，补充说明写在 ann-item 里 | 独立 `.info-box.{色}` 放在 ann-card 底部（见 §4） |
| 无 `.flow-note`，屏幕无状态说明 | 每个 `.flow-col` 末尾加 `<div class="flow-note">状态描述</div>` |
