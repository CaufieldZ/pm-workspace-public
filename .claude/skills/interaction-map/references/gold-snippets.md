<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# 交互大图 · 黄金片段参考（从高质量样本提取）

> 填充时如不确定组件写法，直接复制以下片段修改内容即可。

## 1. 完整注释卡（含全部子组件）

**为什么好**：card-title 带 ann-tag 标明优先级，每个 ann-item 有结构化 ann-num + ann-text + ann-tag，末尾 info-box 补充说明。层次清晰，信息密度高。

```html
<div class="ann-card" style="align-self:flex-start;margin-top:36px;">
  <div class="card-title">改动标注</div>
  <div class="ann-item">
    <div class="ann-num blue">1</div>
    <div class="ann-text"><b>顶部栏</b> <span class="ann-tag chg">改动</span> <span class="ann-tag p1">P1</span><br>
      在线入口改为头像堆叠 + 人数，点击弹出底部弹层 → <b>见 A-2</b></div>
  </div>
  <div class="ann-item">
    <div class="ann-num green">2</div>
    <div class="ann-text"><b>连麦嘉宾区</b> <span class="ann-tag new">NEW</span> <span class="ann-tag p0">P0</span><br>
      1 主播 + 最多 8 嘉宾横排。头像 + 昵称 + 波纹 + 麦克风角标</div>
  </div>
  <div class="info-box blue"><b>未改动：</b>状态栏、主舞台、PiP、关闭按钮<br><b>主播 App 端 = 本图</b>（无管理功能，管理走 Web）</div>
</div>
```

## 2. 标注框（包裹屏幕内元素）

**为什么好**：`position:relative` 父容器 + `.anno` 虚线绝对定位 + `.anno-n` 编号圆点，让读者一眼知道注释卡的 ① 对应屏幕哪个区域。

```html
<div style="position:relative;margin-top:12px;">
  <div class="anno amber" style="top:-4px;left:-4px;right:-4px;bottom:-4px;">
    <div class="anno-n amber">①</div>
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

## 6. 反模式 vs 正确写法

| 反模式（❌） | 正确写法（✅） |
|-------------|--------------|
| `<div class="ann-card"><div class="ann-num">①</div>说明文字</div>` | 完整结构：ann-card > card-title + ann-item > ann-num + ann-text（见 §1） |
| 无 `.anno` 框，注释卡悬空无对应 | 屏幕内目标元素用 `.anno.{色}` 包裹 + `.anno-n` 编号（见 §2） |
| 屏幕间无 `.aw` 箭头 | 每两个有流向关系的屏幕间必须有 `.aw`（见 §3） |
| 注释卡无 `.ann-tag`，不知道优先级 | card-title 和 ann-text 内加 `.ann-tag.{new/chg/p0/p1}`（见 §1） |
| 全文 font-weight:700，无层次 | 3 级层次：900 / 700 / 400（见 §5） |
| 无 `.info-box`，补充说明写在 ann-item 里 | 独立 `.info-box.{色}` 放在 ann-card 底部（见 §4） |
| 无 `.flow-note`，屏幕无状态说明 | 每个 `.flow-col` 末尾加 `<div class="flow-note">状态描述</div>` |
