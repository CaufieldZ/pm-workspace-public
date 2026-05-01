---
name: shapes-toolkit
description: PPT 特殊形状 SVG 工具包，补充 X6 节点类型之外的架构图常用形状
type: reference
---

# 特殊形状 SVG 工具包

> 用于 PPT 内嵌架构图 / 系统图，补充 flowchart skill X6 节点（rect/diamond）之外的形状。
> 配色统一用 `currentColor`（跟随主题 `--cd-accent`）+ `var(--cd-bg)`，自动适配 8 套主题。
> 尺寸用 `viewBox` + CSS 控制，不写 `width/height` 像素。

**使用方式**：直接内联 SVG，用 `style="color:var(--cd-accent)"` 驱动颜色：

```html
<svg class="shape shape-cloud" viewBox="0 0 80 50" style="color:var(--cd-accent); width:80px">
  ...
</svg>
```

---

## 1. 云形（cloud）— 第三方服务 / 公网

```html
<svg class="shape shape-cloud" viewBox="0 0 80 52" style="color:var(--cd-accent)">
  <path d="M18,44 C8,44 6,36 6,30 C6,23 10,18 18,17 C16,7 24,4 32,7 C36,2 44,2 50,7 C57,4 65,9 64,18 C72,18 76,24 76,31 C76,38 70,44 62,44 Z"
    stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)" stroke-linejoin="round"/>
</svg>
```

---

## 2. 数据库柱（database）— 存储 / DB / 数据湖

```html
<svg class="shape shape-database" viewBox="0 0 60 72" style="color:var(--cd-accent)">
  <!-- 顶部椭圆 -->
  <ellipse cx="30" cy="14" rx="26" ry="9" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
  <!-- 两侧竖线 -->
  <line x1="4"  y1="14" x2="4"  y2="58" stroke="currentColor" stroke-width="1.5"/>
  <line x1="56" y1="14" x2="56" y2="58" stroke="currentColor" stroke-width="1.5"/>
  <!-- 中间分层弧（2 层） -->
  <path d="M4,30 Q30,40 56,30" stroke="currentColor" stroke-width="1" fill="none" opacity="0.45"/>
  <path d="M4,44 Q30,54 56,44" stroke="currentColor" stroke-width="1" fill="none" opacity="0.45"/>
  <!-- 底部椭圆 -->
  <ellipse cx="30" cy="58" rx="26" ry="9" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
</svg>
```

---

## 3. 服务模块（service）— 微服务 / 后端模块

```html
<svg class="shape shape-service" viewBox="0 0 80 60" style="color:var(--cd-accent)">
  <!-- 圆角矩形主体 -->
  <rect x="4" y="18" width="72" height="38" rx="6" ry="6"
    stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
  <!-- 顶部 icon slot（小圆 + 标题条） -->
  <circle cx="20" cy="9" r="7" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
  <line x1="32" y1="7" x2="68" y2="7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="32" y1="12" x2="56" y2="12" stroke="currentColor" stroke-width="1" stroke-linecap="round" opacity="0.5"/>
</svg>
```

---

## 4. 文档堆叠（doc-stack）— 多文档 / 报表 / 配置

```html
<svg class="shape shape-doc-stack" viewBox="0 0 64 72" style="color:var(--cd-accent)">
  <!-- 第 3 层（最深） -->
  <rect x="12" y="8"  width="46" height="56" rx="3" stroke="currentColor" stroke-width="1" fill="var(--cd-bg)" opacity="0.4"/>
  <!-- 第 2 层 -->
  <rect x="8"  y="12" width="46" height="56" rx="3" stroke="currentColor" stroke-width="1" fill="var(--cd-bg)" opacity="0.65"/>
  <!-- 顶层（完整文档） -->
  <rect x="4"  y="16" width="46" height="56" rx="3" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
  <!-- 折角 -->
  <path d="M38,16 L50,28 L38,28 Z" stroke="currentColor" stroke-width="1" fill="var(--cd-bg)"/>
  <path d="M38,16 L50,28" stroke="currentColor" stroke-width="1.5"/>
  <!-- 内容线 -->
  <line x1="12" y1="36" x2="42" y2="36" stroke="currentColor" stroke-width="1" opacity="0.45"/>
  <line x1="12" y1="44" x2="36" y2="44" stroke="currentColor" stroke-width="1" opacity="0.45"/>
  <line x1="12" y1="52" x2="38" y2="52" stroke="currentColor" stroke-width="1" opacity="0.45"/>
</svg>
```

---

## 5. 用户头像（user）— 人 / 用户 / 角色

```html
<svg class="shape shape-user" viewBox="0 0 60 70" style="color:var(--cd-accent)">
  <!-- 头部 -->
  <circle cx="30" cy="18" r="14" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
  <!-- 身体（圆弧半身） -->
  <path d="M6,70 Q6,46 30,46 Q54,46 54,70"
    stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)" stroke-linejoin="round"/>
</svg>
```

---

## 6a. 设备框 — PC 显示器

```html
<svg class="shape shape-device-pc" viewBox="0 0 80 68" style="color:var(--cd-accent)">
  <!-- 显示器 -->
  <rect x="4" y="4" width="72" height="48" rx="4" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
  <!-- 屏幕内区 -->
  <rect x="10" y="10" width="60" height="36" rx="2" stroke="currentColor" stroke-width="1" fill="none" opacity="0.35"/>
  <!-- 支架 -->
  <line x1="40" y1="52" x2="40" y2="62" stroke="currentColor" stroke-width="2"/>
  <!-- 底座 -->
  <line x1="26" y1="62" x2="54" y2="62" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
</svg>
```

---

## 6b. 设备框 — 手机

```html
<svg class="shape shape-device-mobile" viewBox="0 0 40 70" style="color:var(--cd-accent)">
  <rect x="4" y="4" width="32" height="62" rx="6" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
  <!-- 刘海 -->
  <line x1="14" y1="10" x2="26" y2="10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  <!-- 屏幕区 -->
  <rect x="9" y="16" width="22" height="38" rx="2" stroke="currentColor" stroke-width="1" fill="none" opacity="0.35"/>
  <!-- Home 键 -->
  <circle cx="20" cy="60" r="3" stroke="currentColor" stroke-width="1" fill="none"/>
</svg>
```

---

## 7. 防火墙（firewall）— 安全边界 / WAF

```html
<svg class="shape shape-firewall" viewBox="0 0 72 60" style="color:var(--cd-accent)">
  <!-- 外框 -->
  <rect x="2" y="2" width="68" height="56" rx="4" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
  <!-- 砖块纹路（3 行，错位） -->
  <!-- 行 1 -->
  <rect x="8"  y="12" width="24" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
  <rect x="36" y="12" width="28" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
  <!-- 行 2（错位） -->
  <rect x="8"  y="26" width="16" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
  <rect x="28" y="26" width="24" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
  <rect x="56" y="26" width="8"  height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
  <!-- 行 3 -->
  <rect x="8"  y="40" width="24" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
  <rect x="36" y="40" width="28" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
</svg>
```

---

## 8. 地球（globe）— 网络 / 公网 / 全球化

```html
<svg class="shape shape-globe" viewBox="0 0 64 64" style="color:var(--cd-accent)">
  <!-- 外圆 -->
  <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
  <!-- 经线（3 条） -->
  <ellipse cx="32" cy="32" rx="12" ry="28" stroke="currentColor" stroke-width="1" fill="none" opacity="0.4"/>
  <line x1="4" y1="32" x2="60" y2="32" stroke="currentColor" stroke-width="1" opacity="0.4"/>
  <!-- 纬线（2 条） -->
  <path d="M10,20 Q32,26 54,20" stroke="currentColor" stroke-width="1" fill="none" opacity="0.4"/>
  <path d="M10,44 Q32,38 54,44" stroke="currentColor" stroke-width="1" fill="none" opacity="0.4"/>
</svg>
```

---

## 9. 锁（lock）— 安全 / 加密 / 权限

```html
<svg class="shape shape-lock" viewBox="0 0 52 66" style="color:var(--cd-accent)">
  <!-- 锁体 -->
  <rect x="4" y="30" width="44" height="32" rx="6" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
  <!-- 锁梁（U形） -->
  <path d="M14,30 L14,18 Q14,6 26,6 Q38,6 38,18 L38,30"
    stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
  <!-- 锁眼 -->
  <circle cx="26" cy="46" r="6" stroke="currentColor" stroke-width="1.5" fill="none"/>
  <line x1="26" y1="52" x2="26" y2="58" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg>
```

---

## 10. 齿轮（gear）— 配置 / 处理 / 运行时

```html
<svg class="shape shape-gear" viewBox="0 0 64 64" style="color:var(--cd-accent)">
  <!-- 齿轮主体（8 齿，简化为圆 + 外凸矩形） -->
  <circle cx="32" cy="32" r="14" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
  <!-- 8 个齿（外凸小矩形，旋转） -->
  <rect x="29" y="4"  width="6" height="10" rx="2" transform="rotate(0   32 32)" stroke="currentColor" stroke-width="1.2" fill="var(--cd-bg)"/>
  <rect x="29" y="4"  width="6" height="10" rx="2" transform="rotate(45  32 32)" stroke="currentColor" stroke-width="1.2" fill="var(--cd-bg)"/>
  <rect x="29" y="4"  width="6" height="10" rx="2" transform="rotate(90  32 32)" stroke="currentColor" stroke-width="1.2" fill="var(--cd-bg)"/>
  <rect x="29" y="4"  width="6" height="10" rx="2" transform="rotate(135 32 32)" stroke="currentColor" stroke-width="1.2" fill="var(--cd-bg)"/>
  <rect x="29" y="4"  width="6" height="10" rx="2" transform="rotate(180 32 32)" stroke="currentColor" stroke-width="1.2" fill="var(--cd-bg)"/>
  <rect x="29" y="4"  width="6" height="10" rx="2" transform="rotate(225 32 32)" stroke="currentColor" stroke-width="1.2" fill="var(--cd-bg)"/>
  <rect x="29" y="4"  width="6" height="10" rx="2" transform="rotate(270 32 32)" stroke="currentColor" stroke-width="1.2" fill="var(--cd-bg)"/>
  <rect x="29" y="4"  width="6" height="10" rx="2" transform="rotate(315 32 32)" stroke="currentColor" stroke-width="1.2" fill="var(--cd-bg)"/>
  <!-- 中心轴孔 -->
  <circle cx="32" cy="32" r="5" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
</svg>
```

---

## 组合示例：架构图片段

```html
<div style="display:flex; gap:32px; align-items:center; color:var(--cd-accent)">
  <!-- 用户 -->
  <div style="text-align:center">
    <svg viewBox="0 0 60 70" style="width:48px; color:var(--cd-accent)">
      <circle cx="30" cy="18" r="14" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
      <path d="M6,70 Q6,46 30,46 Q54,46 54,70" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
    </svg>
    <div style="font:500 11px var(--cd-mono); color:var(--cd-ink-58); margin-top:4px">用户</div>
  </div>

  <!-- 箭头 -->
  <div style="color:var(--cd-ink-40); font-size:20px">→</div>

  <!-- 防火墙 -->
  <div style="text-align:center">
    <svg viewBox="0 0 72 60" style="width:56px; color:var(--cd-accent)">
      <rect x="2" y="2" width="68" height="56" rx="4" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
      <rect x="8"  y="12" width="24" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
      <rect x="36" y="12" width="28" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
      <rect x="8"  y="26" width="16" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
      <rect x="28" y="26" width="24" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
      <rect x="8"  y="40" width="24" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
      <rect x="36" y="40" width="28" height="10" rx="1" stroke="currentColor" stroke-width="1" fill="none" opacity="0.55"/>
    </svg>
    <div style="font:500 11px var(--cd-mono); color:var(--cd-ink-58); margin-top:4px">WAF</div>
  </div>

  <!-- 箭头 -->
  <div style="color:var(--cd-ink-40); font-size:20px">→</div>

  <!-- 服务 -->
  <div style="text-align:center">
    <svg viewBox="0 0 80 60" style="width:60px; color:var(--cd-accent)">
      <rect x="4" y="18" width="72" height="38" rx="6" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
      <circle cx="20" cy="9" r="7" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
      <line x1="32" y1="7" x2="68" y2="7" stroke="currentColor" stroke-width="1.5"/>
    </svg>
    <div style="font:500 11px var(--cd-mono); color:var(--cd-ink-58); margin-top:4px">API 服务</div>
  </div>

  <!-- 箭头 -->
  <div style="color:var(--cd-ink-40); font-size:20px">→</div>

  <!-- 数据库 -->
  <div style="text-align:center">
    <svg viewBox="0 0 60 72" style="width:44px; color:var(--cd-accent)">
      <ellipse cx="30" cy="14" rx="26" ry="9" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
      <line x1="4"  y1="14" x2="4"  y2="58" stroke="currentColor" stroke-width="1.5"/>
      <line x1="56" y1="14" x2="56" y2="58" stroke="currentColor" stroke-width="1.5"/>
      <path d="M4,30 Q30,40 56,30" stroke="currentColor" stroke-width="1" fill="none" opacity="0.45"/>
      <path d="M4,44 Q30,54 56,44" stroke="currentColor" stroke-width="1" fill="none" opacity="0.45"/>
      <ellipse cx="30" cy="58" rx="26" ry="9" stroke="currentColor" stroke-width="1.5" fill="var(--cd-bg)"/>
    </svg>
    <div style="font:500 11px var(--cd-mono); color:var(--cd-ink-58); margin-top:4px">DB</div>
  </div>
</div>
```

---

## 约束清单

- 配色：只用 `currentColor`（跟随 `--cd-accent`）和 `var(--cd-bg)`，不写死 hex
- 尺寸：用 `viewBox` 定义比例，inline `style="width:Npx"` 控制实际尺寸
- 线条：`stroke-width` 统一 1.5px（主线）/ 1px（次要线）/ 2px（加粗强调）
- 填充：主体内部 `fill="var(--cd-bg)"` 或 `fill="none"`，不用 `fill="white"`（暗色主题会穿帮）
- 复杂分支流程图 / 决策树用 flowchart skill 独立产出 → 截图嵌入 PPT（PPT 内嵌 X6 已 rolled back，黑底主题视觉不对齐）
