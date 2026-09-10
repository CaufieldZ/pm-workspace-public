---
id: chat/message-input
name: 消息输入框
product: chat
platform: web
description: 消息输入框（文本输入 + 发送 + toolbar 扩展位 + sending/error 三态）
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: [MessageInputStore]
trigger-keywords: [输入框, 消息输入, message input, 工具栏, toolbar, MessageInputStore, sendMessage, 发消息, 发文本]
prerequisites: [login-auth, message-list]
tags: ['MessageInputStore']
---

## 1. 这个 slice 处理什么

路径 A 基础功能。在 `src/components/chat/MessageInput.vue` 通过 `useMessageInputStore(conversationID)` 拿到 `sendMessage` API。**本 slice 只覆盖文本发送 + toolbar 扩展位 + sending/error 三态**。

> 其余 payload 类型不在 starter 范围：
> - `imageMessage` / `videoMessage` / `fileMessage` / `audioMessage` → `features/send-media.md`
> - `customMessage` → `features/send-custom-message.md`
> - `faceMessage` / `locationMessage` → 对应 feature slice
>
> `SendMessageInputOption` 的字段也按 feature 拆分（`quotedMessage` / `atUserList` / `needReadReceipt` 等），starter 不传。

## 2. AI 思考清单

- `conversationID` 从哪传入？（props / route / 全局 store）
- toolbar 位置？（输入框上方 / 下方）
- 键盘约定？（默认 Enter 发送 / Shift+Enter 换行，跟随项目如有不同）
- 扩展位形式？（`<slot>` / props / 具名按钮组）

## 3. SDK API 必读

```ts
import { useMessageInputStore } from 'tuikit-atomicx-vue3/chat'

const { sendMessage } = useMessageInputStore(props.conversationID)
// sendMessage: (payload: SendMessagePayload, option?: SendMessageInputOption) => Promise<MessageInfo>
```

`SendMessagePayload`（可辨识联合，starter 只用第一种）：

```ts
type SendMessagePayload =
  | { type: 'textMessage'; text: string }                    // ← starter 范围
  | { type: 'customMessage'; customData: string; description?: string; extension?: string }
  | { type: 'imageMessage'; file: File | HTMLInputElement; width?: number; height?: number }
  | { type: 'audioMessage'; file: File | HTMLInputElement; duration: number }
  | { type: 'videoMessage'; file: File | HTMLInputElement; duration: number; ... }
  | { type: 'fileMessage'; file: File | HTMLInputElement }
  | { type: 'locationMessage'; description: string; longitude: number; latitude: number }
  | { type: 'faceMessage'; index: number; data: string }
```

> `payload.type` 用小写驼峰（`textMessage`），不是旧版 `TIMTextElem`。

`SendMessageInputOption`（starter 不传，留给 features）：

```ts
interface SendMessageInputOption {
  atUserList?: string[]
  quotedMessage?: MessageInfo
  needReadReceipt?: boolean
  isExtensionEnabled?: boolean
  onlineUserOnly?: boolean
  offlinePushInfo?: { title?: string; description?: string; extensionInfo?: Record<string, unknown> }
}
```

## 4. Hard rules

> ❗ 所有 SDK 异步调用必须遵循 `references/06-a-defensive-coding.md` 防御编程规范（try/catch/finally、formatError、错误反馈形式、状态锁）。本节规则是该规范的专属补充，不替代它。
> ❗ 写 UI 代码前必须先 `read_file _base/style-guide.md`，按其规范生成样式，不准跳过。

### 4.1 调用范式

- ❗ `useMessageInputStore(props.conversationID)` 必填 conversationID
  - ❌ 不传参（运行时报错）
- ❗ 唯一入口 `sendMessage(payload, option?)`，禁止绕过 store 调旧 API
  - ❌ `chat.createTextMessage(...)` + `chat.sendMessage(...)`
- ❗ `payload.type` 必须用字面量 `'textMessage'`
  - ❌ `'TIMTextElem'` / `'text'` / 大写驼峰
- ❗ 文本 `trim()` 后为空禁止发送（按钮 disabled + 早返回双重拦截）
- ❗ `try/catch/finally`：sending 锁住 → catch 显示 errorMsg → finally 复位
  - ❌ `sending` 没在 finally 复位
  - ❌ catch 里 console.error 但 UI 不显示
- ❗ 成功后不手动 push 到 messageList（store 自动同步）
- ❗ 不准手动调 `destroy()`（已由 onScopeDispose 自动接管）
- ❗ starter 不传 option（`quotedMessage` / `atUserList` 等属于 features）

### 4.2 输入与键盘

- ❗ textarea 用 `v-model`，不准 `ref="el"` + `el.value.value` 取 DOM 值
- ❗ Enter 发送 + Shift+Enter 换行（跟随项目如有不同）
- ❗ Enter 发送时 `e.preventDefault()`
  - ❌ 发送同时插入换行
- ❗ 成功后清空 `text = ''`，并在 `sending` 复位后 `nextTick()` 再 `focus()` 回 textarea
  - ❌ 在 `try` 块内直接 `focus()`（此时 `sending=true`，textarea 处于 disabled 状态，focus 无效）
  - ✅ `focus()` 必须在 `finally` 里 `sending.value = false` 之后，配合 `await nextTick()`

### 4.3 toolbar 扩展位

- ❗ 必须渲染 toolbar，不准默认隐藏
- ❗ 必须暴露扩展位（slot / props / 具名按钮组三选一），后续 features 能追加按钮而不改源码
- ❗ 基础 4 件套阶段 toolbar 不挂任何业务按钮
  - ❌ starter 里硬塞评价 / 订单 / 优惠券按钮

### 4.4 错误反馈

- ❗ errorMsg 就近显示（输入框附近小字），不用 alert / 顶部 toast
- ❗ 用户开始输入时清空 errorMsg
- ❗ catch 读 `err?.message ?? String(err)`

## 5. 反例库

> § 4 已内联主要反例。本节补充跨规则复合错误：

- ❌ `useMessageInputStore()` 不传 ID + 解构 `destroy` 手动调 + 绕过 store 调旧 API — 三重错误组合
- ❌ starter 阶段传 `option = { quotedMessage, atUserList }` — 会和未来 feature 打架

## 6. UI 自由度

> 样式由 AI 自由发挥，遵循项目已有 CSS 方案（见 `_base/detect-style.md`）。

✅ 完全自由：输入框形状 / toolbar 位置 / 按钮图标 / 发送按钮形态 / textarea 行数 / 错误提示位置
⚠️ 必须遵循项目现状：UI 库 / 同类组件 / CSS 方案
⚠️ § 4 强约束不可放宽

## 7. 参考实现

```vue
<script setup lang="ts">
import { ref, useTemplateRef, watch, nextTick } from 'vue'
import { useMessageInputStore } from 'tuikit-atomicx-vue3/chat'

const props = defineProps<{ conversationID: string }>()
const { sendMessage } = useMessageInputStore(props.conversationID)

const text = ref('')
const sending = ref(false)
const errorMsg = ref<string | null>(null)
const textareaEl = useTemplateRef<HTMLTextAreaElement>('textareaEl')

watch(text, (v) => { if (v.length > 0 && errorMsg.value) errorMsg.value = null })

async function handleSend() {
  const trimmed = text.value.trim()
  if (!trimmed || sending.value) return
  errorMsg.value = null
  sending.value = true
  try {
    await sendMessage({ type: 'textMessage', text: trimmed })
    text.value = ''
  } catch (err: any) {
    errorMsg.value = err?.message ?? String(err)
  } finally {
    sending.value = false
    await nextTick()
    textareaEl.value?.focus()
  }
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="msg-input-wrapper">
    <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

    <textarea
      ref="textareaEl"
      v-model="text"
      :disabled="sending"
      placeholder="Type a message..."
      rows="3"
      @keydown="onKeyDown"
    />

    <div class="toolbar">
      <slot name="toolbar-actions" />
      <div class="spacer" />
      <button type="button" :disabled="sending || !text.trim()" @click="handleSend">
        {{ sending ? 'Sending…' : 'Send' }}
      </button>
    </div>
  </div>
</template>
```

### 可改

- 样式 / class / Tailwind / 项目 token
- toolbar 位置、按钮图标库、发送按钮形态
- 错误提示位置（上/下/内嵌）
- 扩展位形式（slot / props / 按钮组）

### 不可改

- `useMessageInputStore(conversationID)` 解构 `sendMessage`
- 唯一调用 `await sendMessage({ type: 'textMessage', text })`
- 三态闭环（disabled + try/catch/finally + errorMsg 就近）
- Enter 发送 preventDefault + 清空 + finally 里 nextTick + focus
- toolbar 必须存在 + 必须留扩展位 + 不挂业务按钮
