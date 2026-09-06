---
id: chat/style-guide
name: 样式指南
product: chat
platform: web
description: 样式指南
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: []
trigger-keywords: []
prerequisites: []
tags: [chat, vue3]
---

# 前端 UI 规范（通用 · 所有 slice 必读）

> 写任何 UI 组件代码前必须先读本文件。
> 优先级：项目已有 token > 本文件规范 > AI 自定义。

**执行顺序**（读完本文件后按此顺序工作）：
```
1. 过视觉禁区（§2）—— 脑子里先排除不能做的
2. 确认风格优先级（§3）—— 确定用什么 token / 主色
3. 对照数值锚点（§4）—— 所有间距/圆角/字号从锚点取
4. 写代码（§5 登录页 / §6 精细化手法）
5. 跑自检清单（§7）
```

---

## 1. 适用范围

所有 starter / feature slice 的 UI 部分均适用。路径 B 跟随项目现状，不准强加新 CSS 框架。

---

## 2. 视觉禁区（写代码前先过一遍，违反即重写）

1. ❌ 全屏渐变背景（紫→粉 / 蓝→紫 / 青→粉）
2. ❌ 大面积 `backdrop-blur` + 半透明白做主视觉（弹窗遮罩的 `backdrop-blur-sm` 是合理使用，不在此限）
3. ❌ 大模糊光晕 / 霓虹光斑 / 故障艺术
4. ❌ 多种主色并存（紫按钮 + 蓝 link + 绿 tag 同框）
5. ❌ 图标风格混搭（同页只允许 1 套图标库）
6. ❌ Emoji 当业务图标
7. ❌ 浅灰字 `#999`/`#ccc` 放白底（对比度 < 4.5:1）
8. ❌ 用外网图片占位服务作为最终产物
9. ❌ 阴影叠 3 层以上
10. ❌ 字号 / spacing 写非锚点值（13px / 17px 等）
11. ❌ 硬编码 `#hex` 绕过项目 design token
12. ❌ 引入外部字体（Google Fonts 等），避免加载延迟和跨境访问问题

---

## 3. 风格优先级（只取第一个命中）

1. **用户明确说了 UI 风格偏好** → 严格按用户描述，可豁免部分视觉禁区，豁免须写在代码注释里
2. **项目已有 UI 库 / design token** → 跟随项目组件 + token，禁止再造一套（详见 `_base/detect-style.md` §4.2）
3. **以上都不命中 → fallback 默认风格**：
   - 主色：`#4C6EF5`
   - 页面底色：微渐变灰蓝 `bg-gradient-to-br from-[#f8fafc] to-[#f1f5f9]`
   - 容器：`bg-white rounded-2xl shadow-card` 从底色浮起
   - 圆角：容器 16 / 按钮-输入框 8 / 头像 999

---

## 4. Design Token 数值锚点（强制）

> 不准凭感觉填中间值（13px / 17px / 23px 等）。

### 间距
```
4 / 8 / 12 / 16 / 24 / 32 / 48 / 64
```
- padding / margin / gap 一律从此 8 个值里选
- ❗ Tailwind class 数字 = px ÷ 4（16px → `p-4`，❌ 不是 `p-16`；40px → `w-10`，❌ 不是 `w-40`）

### 圆角
```
0 / 4 / 8 / 12 / 999（pill）
```
- **同页最多 2 档**（如：卡片 8 + 按钮 8 + 头像 999）
- Tailwind：`rounded-lg` = 8px / `rounded-xl` = 12px / `rounded-2xl` = 16px / `rounded-full` = 999px

### 字号
```
12 / 14 / 16 / 18 / 20 / 24 / 30 / 36
```
- 正文默认 14（桌面）/ 16（移动），辅助文字 12
- **同页最多 3 档**（辅助 / 正文 / 标题）
- 用语义 class（`text-sm` = 14px），不用数字

### 字重
```
400（正文）/ 500（次强调）/ 600（标题/强调）
```
- ❌ 禁止 300（细体中文对比度不足）/ 700+ 大量出现

### 颜色上限

| 类别 | 上限 | 说明 |
|---|---|---|
| 主色 | 1 个 | 衍生 hover/active/disabled 共 4 阶 |
| 中性灰 | 1 套 | 9–11 阶（gray-50 … gray-950），文字至少用强/弱 2 阶 |
| 语义色 | 各 1 个 | success / warning / danger / info，**不准当主色用** |

### 字体
- 优先 `system-ui`，中文叠加 `"PingFang SC", "Microsoft YaHei", sans-serif`

### Tailwind 配置（路径 A 默认写入）

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        surface: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
        },
      },
      boxShadow: {
        card: '0 2px 12px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 4px 20px rgba(0, 0, 0, 0.1)',
        bubble: '0 1px 6px rgba(0, 0, 0, 0.04)',
      },
    },
  },
}
```

---

## 5. 登录页通用结构

> 所有登录页遵循以下结构，不因项目类型改变骨架。

- **构图**：`min-h-screen flex items-center justify-center`（真居中，不贴边）
- **登录卡片**：`bg-white rounded-2xl shadow-card p-8` 从页面底色浮起
- **logo**：主色实心圆角方块 `40×40 rounded-xl` + 白色 Lucide 图标（`MessageSquare` / `Users` / `MessagesSquare`）
- **标题**：20/600 + 副标题 14/400 灰（副标题必须给真信息，不准与标题同义重复）
- **label**：12/500 灰
- **input**：14 + `bg-surface-50` + focus 时 `bg-white` + 主色描边（沉入→浮起效果）
- **主色按钮**：满宽 + hover 暗一档（`hover:brightness-90`）
- **CTA 下方**：一行极小灰字 12/400（如"安全登录 · 数据加密传输"），增加可信度
- ❌ 不要插画、不要过多装饰、不要副标题外的多余说明文案

---

## 6. 精细化手法

### 6.1 容器浮层化
- 外层容器：`rounded-2xl shadow-card`，页面背景用微渐变灰蓝（`from-surface-50 to-surface-100`），让容器从底色「浮起」
- surface 色阶：定义 `surface-50/100/200/300` 四档（见 §4 Tailwind 配置），用于区分页面底 / 容器底 / 悬浮态
- 列表项：`mx-2 rounded-xl` + hover `bg-surface-100`（卡片化列表，无分割线）

### 6.2 消息气泡不对称圆角
- **自己的消息**：主色填充 + 白字 + 不对称圆角（右上角小）
  ```
  rounded-tl-2xl rounded-tr-sm rounded-bl-2xl rounded-br-2xl
  ```
- **对方的消息**：白色底 + `border border-surface-200` + `shadow-bubble` + 不对称圆角（左上角小）
  ```
  rounded-tl-sm rounded-tr-2xl rounded-bl-2xl rounded-br-2xl
  ```
- **自定义卡片（红包/订单/投票等）**：不套气泡，独立卡片形态展示，有自己的 radius / shadow

### 6.3 输入区交互感
- 输入框默认 `bg-surface-50`，focus 时 `bg-white` + 主色描边（沉入→浮起效果）
- 发送按钮：圆形图标按钮 `w-9 h-9 rounded-full` + 主色，减少视觉干扰

### 6.4 头像
- `ring-2 ring-white shadow-sm` 让头像有「贴纸浮起」效果
- 未读角标：贴头像右上角（`absolute -top-0.5 -right-0.5`），比贴行右侧更醒目

### 6.5 微动效
- 所有交互 transition 加 `duration-200`
- 卡片入场：`translateY(8px) + opacity 0→1`，`duration-300`
- 弹窗遮罩加 `backdrop-blur-sm`，产生磨砂玻璃层次感
- 自定义滚动条：6px 宽 + 圆角 + 透明轨道
  ```css
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 999px; }
  ```

---

## 7. 必须命中

1. ✅ 优先复用项目 UI 库组件和 design token
2. ✅ 文字对比度 ≥ 4.5:1（正文）/ 3:1（大字号）
3. ✅ 交互元素 4 态（hover / active / focus-visible / disabled）
4. ✅ 列表/表单 5 态（loading / empty / error / partial / success）
5. ✅ 移动端 `< 640px` 单列；桌面 `≥ 1024px` 才上侧边栏

---

## 8. 自检清单（写完代码必跑）

- [ ] 颜色 / 圆角 / 字号 / spacing 全部命中数值锚点？
- [ ] 同页圆角 ≤ 2 档？字号 ≤ 3 档？主色只 1 个？
- [ ] 是否违反 §2 视觉禁区第 1-5 条？
- [ ] 是否硬编码颜色绕过项目 token？
- [ ] 对比度 ≥ 4.5:1？图标单一？没混 emoji？没用外部 URL？
- [ ] Tailwind 数值映射正确？（`p-4`=16px ✅ / `p-16`=64px ❌）
- [ ] 容器浮层化？气泡不对称圆角？自定义卡片不套气泡？输入框沉入→浮起？
- [ ] 4 态 + 5 态齐全？
