---
id: chat/send-media
name: 发送多媒体
product: chat
platform: web
description: 发送图片、视频、文件消息（toolbar 按钮 + 文件选择 + 上传发送）
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: [MessageInputStore]
trigger-keywords: [发图片, 发视频, 发文件, 图片消息, 视频消息, 文件消息, send image, send video, send file, imageMessage, videoMessage, fileMessage, 上传, upload, 多媒体, media]
prerequisites: [login-auth, message-list, message-input]
tags: ['MessageInputStore']
---

## 1. 这个 slice 处理什么

在 MessageInput 的 toolbar 扩展位追加**图片 / 视频 / 文件**三个发送按钮，通过隐藏 `<input type="file">` 选择文件后调用 `sendMessage(payload)` 发送。三者共享完全相同的调用模式，仅 `payload.type` 和 `accept` 不同。

> 本 slice 不覆盖：
> - `audioMessage`（录音交互复杂度高，见未来 `features/send-audio.md`）
> - `customMessage` → `features/send-custom-message.md`

## 2. AI 思考清单

❗ **本 slice 包含图片 / 视频 / 文件三种媒体类型，读取后禁止默认全部实现。**
- 根据用户原始需求判断需要哪几种，只实现对应类型
- 用户只说"图片" → 只加图片按钮和 `imageMessage` 逻辑，不附带视频 / 文件
- 用户说"图片和视频" → 只加这两种，不加文件
- 用户说"媒体" / "多媒体" / 表述模糊 → 在 B.3 确认阶段询问具体类型，再实现
  - ❌ 读完 slice 直接把三种类型全部写进代码

- toolbar 按钮放在哪？（追加到 MessageInput 的 `<slot name="toolbar-actions">` / 直接在 MessageInput 组件内追加）
- 图标库用哪个？（跟随项目已有 / lucide / heroicons）
- 是否需要上传进度提示？（SDK 内部处理，前端只需 sending 态）
- 视频 duration 如何获取？（传 0 即可，前端获取不到 duration）
- 文件大小前端校验：默认限制——图片 ≤ 20MB / 视频 ≤ 100MB / 文件 ≤ 100MB（SDK 服务端也有此限制，前端拦截提升体验）

## 3. SDK API 必读

```ts
import { useMessageInputStore } from 'tuikit-atomicx-vue3/chat'

const { sendMessage } = useMessageInputStore(props.conversationID)
```

三种 payload 的完整类型：

```ts
// 图片
{ type: 'imageMessage'; file: File | HTMLInputElement; width?: number; height?: number }

// 视频
{ type: 'videoMessage'; file: File | HTMLInputElement; duration: number; snapshotFile?: File | HTMLInputElement; snapshotWidth?: number; snapshotHeight?: number }

// 文件
{ type: 'fileMessage'; file: File | HTMLInputElement }
```

> `file` 字段传 `File` 对象（从 `<input>` 的 `files[0]` 取）。不传 `HTMLInputElement`（Web 端推荐 File）。

`SendMessageInputOption`（可选，与 starter 相同的 option）：

```ts
interface SendMessageInputOption {
  needReadReceipt?: boolean     // 已读回执（需 read-receipts feature）
  // ... 其余字段见 message-input.md § 3
}
```

## 4. Hard rules

### 4.1 调用范式

- ❗ 复用 `useMessageInputStore(props.conversationID)` 的 `sendMessage`（与文本发送同一个 store 实例）
  - ❌ 另起一个 `useMessageInputStore` 实例
  - ❌ 绕过 store 调旧 API `chat.createImageMessage(...)` + `chat.sendMessage(...)`
- ❗ `payload.type` 必须用字面量：`'imageMessage'` / `'videoMessage'` / `'fileMessage'`
  - ❌ `'TIMImageElem'` / `'image'` / 大写驼峰
- ❗ `file` 传 `File` 对象（`input.files[0]`），不传 DOM element
  - ❌ `{ type: 'imageMessage', file: imageInputEl }` — 传了 HTMLInputElement ref
- ❗ videoMessage 的 `duration` 字段必填，前端不做视频解析时传 `0`
  - ❌ 不传 duration（TS 报错）
  - ❌ 费力用 `<video>` 预加载获取 duration（非必要复杂度）

### 4.2 文件选择

- ❗ 每种类型用独立的隐藏 `<input type="file">`，通过 `accept` 限制：
  - 图片：`accept="image/*"`
  - 视频：`accept="video/*"`
  - 文件：不设 accept（接受所有类型）
- ❗ 选择后立即重置 input value（`(e.target as HTMLInputElement).value = ''`），否则同一文件无法再次选择
  - ❌ 不重置，用户选同一张图第二次无反应
- ❗ `files[0]` 为空时直接 return，不调 sendMessage
- ❗ 隐藏 input 用 `class="hidden"` 或 `display:none`，不放在 toolbar 可视区

### 4.3 发送状态

- ❗ 复用 MessageInput 已有的 `sending` + `errorMsg` 机制（同一组 ref）
- ❗ `try/catch/finally` 闭环：sending 锁住所有按钮 → catch 显示 errorMsg → finally 复位
  - ❌ 图片/视频/文件各自独立 sending 态（用户困惑哪个在发）
- ❗ 发送中禁用所有 toolbar 按钮（含文本发送按钮）
- ❗ 成功后不手动 push 到 messageList（store 自动同步）

### 4.4 toolbar 集成

- ❗ 按钮放在 MessageInput toolbar 的扩展位内（slot 或直接追加）
- ❗ 按钮顺序：图片 → 视频 → 文件（约定固定，避免每次生成不一样）
- ❗ 每个按钮必须有 `title` / `aria-label` 属性（可访问性）
- ❗ 按钮触发方式：`@click="xxxInputEl?.click()"`
  - ❌ 用 `<label for="xxx">` 包裹（跨组件 id 冲突风险）

### 4.5 前端文件校验

- ❗ 选择文件后、调 `sendMessage` 前校验文件大小（阈值见 § 2 思考清单：图片 ≤ 20MB / 视频 ≤ 100MB / 文件 ≤ 100MB）
- ❗ 超限时设置 `errorMsg` 提示用户，不调 sendMessage
  - ❌ 不做前端校验，等 SDK 超时报错（体验差）

## 5. 反例库

> § 4 已内联主要反例。本节补充跨规则复合错误：

- ❌ 把文件选择逻辑写在父组件 ChatPage 里，通过 props 传 File 给 MessageInput — 违反封装
- ❌ 用全局 event bus 传 File — 过度设计
- ❌ 三个 input 共用一个，运行时动态改 accept — 竞态风险 + UX 差

## 6. UI 自由度

> 样式由 AI 自由发挥，遵循项目已有 CSS 方案（见 `_base/detect-style.md`）。

✅ 完全自由：按钮图标 / 按钮形态（icon-only / icon+text）/ tooltip 样式 / 文件大小校验阈值 / 错误提示措辞
⚠️ 必须遵循项目现状：图标库 / CSS 方案 / toolbar 风格保持一致
⚠️ § 4 强约束不可放宽

## 7. 参考实现

```vue
<script setup lang="ts">
import { ref, useTemplateRef } from 'vue'
import { useMessageInputStore } from 'tuikit-atomicx-vue3/chat'

const props = defineProps<{ conversationID: string }>()
const { sendMessage } = useMessageInputStore(props.conversationID)

const sending = ref(false)
const errorMsg = ref<string | null>(null)

const imageInputEl = useTemplateRef<HTMLInputElement>('imageInputEl')
const videoInputEl = useTemplateRef<HTMLInputElement>('videoInputEl')
const fileInputEl = useTemplateRef<HTMLInputElement>('fileInputEl')

async function sendMediaFile(payload: Parameters<typeof sendMessage>[0]) {
  errorMsg.value = null
  sending.value = true
  try {
    await sendMessage(payload)
  } catch (err: any) {
    errorMsg.value = err?.message ?? String(err)
  } finally {
    sending.value = false
  }
}

function onImageSelect(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  sendMediaFile({ type: 'imageMessage', file })
  ;(e.target as HTMLInputElement).value = ''
}

function onVideoSelect(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  sendMediaFile({ type: 'videoMessage', file, duration: 0 })
  ;(e.target as HTMLInputElement).value = ''
}

function onFileSelect(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  sendMediaFile({ type: 'fileMessage', file })
  ;(e.target as HTMLInputElement).value = ''
}
</script>

<template>
  <!-- toolbar 按钮（注入 MessageInput 的扩展位） -->
  <button :disabled="sending" title="Send image" @click="imageInputEl?.click()">📷</button>
  <button :disabled="sending" title="Send video" @click="videoInputEl?.click()">🎬</button>
  <button :disabled="sending" title="Send file" @click="fileInputEl?.click()">📎</button>

  <!-- 隐藏 file inputs -->
  <input ref="imageInputEl" type="file" accept="image/*" class="hidden" @change="onImageSelect" />
  <input ref="videoInputEl" type="file" accept="video/*" class="hidden" @change="onVideoSelect" />
  <input ref="fileInputEl" type="file" class="hidden" @change="onFileSelect" />
</template>
```

> ⚠️ 实际实现时，上述逻辑应与 MessageInput 组件合并（共享 `sending` / `errorMsg`），而非独立组件。参考实现仅展示逻辑骨架。

### 可改

- 图标（emoji 只是占位，应替换为项目图标库）
- 按钮样式 / 布局
- 是否加文件大小前端校验
- 是否加上传进度 UI（SDK 暂未暴露进度回调）

### 不可改

- `sendMessage` 从 `useMessageInputStore(conversationID)` 取（同一实例）
- payload type 字面量（`'imageMessage'` / `'videoMessage'` / `'fileMessage'`）
- `file` 传 File 对象（不传 HTMLInputElement）
- videoMessage 必须带 `duration`（传 0）
- 选择后重置 input value
- 三个独立隐藏 input（不共用）
