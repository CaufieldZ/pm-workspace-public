---
id: chat/send-custom-message
name: 自定义消息
product: chat
platform: web
description: 通用自定义消息（订单/商品/优惠券/投票/红包等业务卡片，自定义 businessID）
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: [MessageInputStore]
trigger-keywords: [自定义消息, custom message, customMessage, 订单, 商品卡片, 优惠券, 红包, 投票, 卡片消息, 业务卡片, 评价, 评分, rating]
prerequisites: [login-auth, message-list, message-input]
tags: ['MessageInputStore']
---

## 1. 这个 slice 处理什么

所有业务卡片消息（订单 / 商品 / 优惠券 / 投票 / 红包 / 评价 / 任意业务类型）共用本 slice。SDK 调用 100% 一致——`useMessageInputStore(conversationID).sendMessage({ type: 'customMessage', customData, description?, extension? })`——区别仅在 `businessID` 命名、`customData` JSON 字段结构、卡片 Bubble UI。

> ❗ **不要为每种业务类型新建 slice**。新业务卡片：起 `businessID` + 起 Bubble 组件 + 在 message-list 加 `v-else-if` 分支即可。
>
> ⚠️ **发送口径锁死**：通过 store 的 `sendMessage(payload)` 出栈，不准调底层 `chat.createCustomMessage(...)` / `chat.sendMessage(...)`。

## 2. AI 思考清单（写代码前必须想清楚）

- 业务类型决定 `businessID`（如 `order` / `product` / `coupon` / `red-packet`）
- 关键字段（扁平 + 稳定，接收端字段缺失时能容错）
- 谁发（客户 / 客服 / 系统）
- 卡片点击行为（路由 / Modal / 不跳）——写在父组件，不在 Bubble
- `description` 文案（离线推送 / 列表预览兜底）
- 接收端版本兼容：新增字段时旧版本不 throw

## 3. SDK API 必读（绝对真理）

### 3.1 引入

```ts
import { useMessageInputStore } from 'tuikit-atomicx-vue3/chat'
const { sendMessage } = useMessageInputStore(props.conversationID)
```

> store 实例按 `conversationID` 多实例。发送动作建议放在已持有该会话 store 的父组件，不要在每个业务表单里重新起 `useMessageInputStore(...)`。

### 3.2 customMessage payload

```ts
type CustomMessagePayload = {
  type: 'customMessage'
  customData: string         // 业务 JSON 必须 JSON.stringify 后塞这里
  description?: string       // 离线推送 / 列表预览兜底
  extension?: string         // 业务扩展字段
}
```

推荐 `customData` 内嵌结构：

```ts
{ businessID: string; version?: number; data: T }
```

调用形态：

```ts
await sendMessage({
  type: 'customMessage',
  customData: JSON.stringify({ businessID: 'order', version: 1, data: { orderId, items, total } }),
  description: `Order #${orderId}`,
})
```

### 3.3 SendMessageInputOption（按需）

- `offlinePushInfo` —— 自定义推送标题
- `onlineUserOnly` —— 直播间临时卡片（不入历史）
- `needReadReceipt` —— 需要已读回执

## 4. Hard rules（AI 必须遵守）

### 4.1 调用范式

- ❗ 必须通过 `sendMessage(...)` 出栈
  - ❌ `chat.createCustomMessage(...)` + `chat.sendMessage(...)`
- ❗ `payload.type` 必须是字面量 `'customMessage'`
  - ❌ `'TIMCustomElem'` / `'custom'`
- ❗ 业务 JSON 放 `customData` 字段
  - ❌ `sendMessage({ type: 'customMessage', data: '...' })`（字段名不是 `data`）
- ❗ `customData` 必须 `JSON.stringify(...)`
  - ❌ `customData: { businessID: 'order', orderId: 1 }`（传了对象）
- ❗ 发送必须 `try/catch`，错误就近显示（不 `alert` / 不静默吞）
- ❗ `submitting = true` 锁按钮，`finally` 复位
  - ❌ `submitting` 没在 `finally` 复位
- ❗ 发送成功后不手动 push 到 message-list（store 自动同步）

### 4.2 业务字段命名

- ❗ `businessID` 必须与卡片业务强相关、有可读语义
  - ❌ `'1'` / `'123'` / `'custom'` / `'card'` / `'msg'`（无语义裸值）
- ❗ 外层包 `{ businessID, version, data }` 便于字段演进

### 4.3 接收端解析

- ❗ `JSON.parse(msg.messagePayload.customData)` 必须 `try/catch`，失败降级渲染
  - ❌ 不 try/catch 直接 parse
- ❗ 必须先校验 `businessID === '<本卡片 ID>'` 再走对应 Bubble
  - ❌ 不校验 businessID 直接渲染（会和其他卡片混）
- ❗ 字段读取容错（缺字段给默认值）
  - ❌ `obj.data.items.map(...)` 无防护链式调用

### 4.4 卡片 Bubble 与交互

- ❗ Bubble 只展示，不发请求 / 不跳路由；通过 `emit('action', payload)` 抛意图
  - ❌ Bubble 里 `axios.post(...)` / `router.push(...)`
- ❗ Bubble 对所有字段缺失做兜底渲染（"—" / 占位），不白屏
- ❗ 业务跳转写在父组件 / store 层
- ❗ **默认点击行为**：卡片必须可点击（`cursor-pointer` + hover 态），点击后弹窗展示卡片详情（用项目已有的 Dialog/Drawer 组件）。具体行为由父组件通过 `emit('action')` 响应决定，但 **AI 生成时必须给一个默认实现**（弹窗展示 JSON 格式化的完整数据），不准生成完全不可交互的静态卡片
  - ❌ 卡片无 hover 态、无 cursor-pointer、点击无反应
  - ❌ 只写了 `emit('action')` 但父组件没有任何响应（等于用户点了没反馈）

### 4.5 触发入口

- ❗ 挂在 `MessageInput` toolbar `<slot name="toolbar-actions" />` 或父页面业务按钮，禁止修改 `MessageInput.vue` 源码
  - ❌ 直接改 `MessageInput.vue` 加业务按钮
- ❗ 同会话不要在每个表单都重新 `useMessageInputStore(...)`

## 5. 反例库

> § 4 各条已内联主要反例。本节补充跨规则复合错误：

- ❌ 在每个业务表单里都 `useMessageInputStore(...)` 起新实例 + 发送后手动 `messageList.push(...)` → 同时违反 4.1（冗余实例）+ 4.1（手动 push）
- ❌ 接收端用 `msg.messagePayload.data`（旧字段）—— 正确是 `msg.messagePayload.customData`

## 6. UI 自由度

> 样式由 AI 自由发挥，遵循项目已有 CSS 方案（见 `_base/detect-style.md`）。

✅ 完全自由：卡片视觉 / 字段排版 / 状态指示形式 / 点击交互 / 工具栏入口位置 / 触发表单形态
⚠️ 必须遵循项目现状：UI 库 / CSS 方案 / 同类组件命名
⚠️ § 4 强约束不可放宽

## 7. 参考实现（明确哪些可改）

### 发送侧核心调用

```ts
const { sendMessage } = useMessageInputStore(props.conversationID)

const submitting = ref(false)
const errorMsg = ref<string | null>(null)

async function handleSend() {
  if (submitting.value) return
  submitting.value = true
  errorMsg.value = null
  try {
    await sendMessage({
      type: 'customMessage',
      customData: JSON.stringify({ businessID: 'order', version: 1, data: { orderId, items, total } }),
      description: `Order #${orderId}`,
    })
  } catch (err: any) {
    errorMsg.value = err?.message ?? String(err)
  } finally {
    submitting.value = false
  }
}
```

### 接收侧解析模式（message-list Custom 分支内）

```ts
function parseCustomCard(msg: MessageInfo) {
  if (msg.messageType !== MessageType.Custom) return null
  try {
    const obj = JSON.parse(msg.messagePayload.customData ?? '{}')
    if (obj?.businessID !== 'order') return null  // 换成你的 businessID
    const d = obj.data ?? {}
    return { orderId: String(d.orderId ?? ''), items: Array.isArray(d.items) ? d.items : [], total: Number(d.total) || 0 }
  } catch { return null }
}
```

### 可改 / 不可改

| 可改 | 不可改 |
|---|---|
| `businessID` 名称 / `data` 字段结构 / Bubble 视觉 / 触发入口位置 / 点击行为 | `sendMessage({ type: 'customMessage', customData: JSON.stringify(...) })` 调用形态 |
| | `customData` 字段名（不是 `data`）+ 必须 stringify |
| | 接收端 `try/catch` + 校验 `businessID` + 字段容错 |
| | Bubble 只展示不发请求 / 不改 `MessageInput.vue` 源码 |
| | `submitting` + try/catch/finally 三态闭环 |
