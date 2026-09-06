---
id: chat/message-base-actions
name: 消息基础操作
product: chat
platform: web
description: 消息基础操作（复制 / 撤回 / 删除 / 下载媒体）
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: [MessageActionStore]
trigger-keywords: [消息操作, 复制消息, 撤回, 删除消息, 下载, copy, revoke, recall, delete message, download, 右键菜单, 长按菜单, context menu, message actions]
prerequisites: [login-auth, message-list]
tags: ['MessageActionStore']
---

## 1. 这个 slice 处理什么

对**单条消息**的轻量操作集：复制文本、撤回、删除、下载媒体。四个操作共享同一触发入口（长按 / 右键菜单 / ActionSheet），每个操作是"菜单项 → 一次调用 → 反馈"的简单链路。

> 不覆盖：
> - 表情回应 → `features/message-reaction.md`
> - 消息置顶 → 未来 `features/pinned-message.md`
> - 转发 → 未来 `features/forward-message.md`
> - 引用回复 → 未来 `features/quote-reply.md`

## 2. AI 思考清单

- 操作菜单触发方式？（桌面右键 / 移动端长按 / 消息悬浮按钮）
- 菜单用什么组件？（项目 UI 库 Dropdown / 自建 Popover / BottomSheet）
- 撤回时限？（默认 2 分钟，由服务端控制，前端不做倒计时）
- 删除是否需二次确认？（建议需要）
- 哪些消息类型显示哪些菜单项？（文本 → 复制可用；媒体 → 下载可用）
- 下载在 Web 端是否可用？（SDK `downloadMedia` web 端不支持，改用 `<a download>` 直接下载 URL）

## 3. SDK API 必读

```ts
import { useMessageActionStore } from 'tuikit-atomicx-vue3/chat'
import type { MessageInfo } from 'tuikit-atomicx-vue3/chat'

// 针对单条消息创建 action store
const actionStore = useMessageActionStore(message)

// 可用方法（本 slice 范围）
actionStore.revoke()        // () => Promise<void> — 撤回
actionStore.delete()        // () => Promise<void> — 删除（仅本地）
actionStore.downloadMedia() // (quality?: MediaQuality) => Promise<void> — ⚠️ Web 端不支持
```

> ⚠️ `useMessageActionStore(message)` 的 `message` 是 `MessageInfo` 对象（必填），不是 msgID 字符串。

`MediaQuality` 枚举（Web 端无实际作用）：

```ts
enum MediaQuality {
  Thumbnail = 'thumbnail',
  Standard = 'standard',
  Original = 'original',
}
```

### 3.1 Store 生命周期

- `useMessageActionStore` 内部 `onScopeDispose` 自动销毁，**不需要**手动调 `destroy()`
- ❗ **store 在菜单组件 `setup()` 顶层创建一次，菜单关闭时随组件销毁**——不需要每次操作重新创建
- ❗ **操作顺序约束**：必须在 store 的操作（`revoke()`/`delete()`）**完全执行完毕后**，才能 `emit('close')` 或卸载菜单组件
  - 原因：`emit('close')` 触发父组件卸载菜单 → `onScopeDispose` 销毁 store；如果先 close 再用 store，抛 `MessageActionStore has been destroyed`
  - ❌ 先 `emit('close')` 再通过 callback 调 `actionStore.delete()`
  - ✅ 先 `await actionStore.delete()` 完成，再 `emit('close')`

### 3.2 复制（纯前端，无 SDK API）

```ts
await navigator.clipboard.writeText(text)
```

## 4. Hard rules

> ❗ 所有 SDK 异步调用必须遵循 `references/06-a-defensive-coding.md` 防御编程规范（try/catch/finally、formatError、错误反馈形式、状态锁）。本节规则是该规范的专属补充，不替代它。

### 4.1 Store 创建

- ❗ `useMessageActionStore(message)` 的 `message` 必须是完整 `MessageInfo` 对象
  - ❌ 传 `msgID` 字符串
  - ❌ 传 `{ msgID: '...' }` 不完整对象
- ❗ 不需要手动调 `destroy()`（`onScopeDispose` 已接管）
  - ❌ 在 `onUnmounted` 里手动 `actionStore.destroy()`
- ❗ 不准 `chat.revokeMessage(...)` 等旧 API 绕过 store

### 4.2 操作菜单

- ❗ 必须有操作菜单 UI（不准只写函数不给入口）
- ❗ 菜单项根据消息类型 + 状态动态过滤：

| 菜单项 | 条件 |
|---|---|
| 复制 | `messageType === MessageType.Text` |
| 撤回 | `isSentBySelf === true`（时限由服务端判，前端不拦） |
| 删除 | 始终显示 |
| 下载 | `messageType in [Image, Video, Audio, File]` |

- ❗ 菜单至少渲染满足条件的项，不准全部隐藏只剩空菜单
  - ❌ 某类消息打开菜单一片空白
- ❗ 菜单弹出位置必须做边界检测，不准溢出视口：
  - 自建 Popover：计算触发元素的 `getBoundingClientRect()`，靠右边缘时向左弹出，靠底部时向上弹出
  - 使用 UI 库 Dropdown/Popover 组件：启用其内置的 `placement` 自动翻转（如 `flip: true` / `placement="auto"`）
  - ❌ 固定弹出方向（如始终 `right` / 始终 `bottom`）不做边界判断

### 4.2.1 操作反馈（通用规则）

- ❗ 所有操作（复制 / 撤回 / 删除 / 下载）必须 `try/catch`，失败时给用户 **可见的错误提示**（Toast）
  - ❌ 操作失败静默吞掉错误，用户无感知
  - ❌ 只 `console.error` 不给 UI 反馈
- ❗ 操作成功也应有轻反馈（复制 → "已复制" / 撤回 → 消息变为撤回提示 / 删除 → 消息消失 / 下载 → 浏览器开始下载）
- ❗ 错误信息用 `formatError(err)`（来自 `@/im/error-map`），不准直接用 `err?.message ?? String(err)` 原始暴露

### 4.3 复制

- ❗ 仅 Text 消息可复制（取 `msg.messagePayload.text`）
- ❗ 使用 `navigator.clipboard.writeText()`
- ❗ 复制成功后给用户轻反馈（toast / 短暂提示 "Copied"）
  - ❌ 无反馈，用户不知道是否成功
- ❗ `clipboard.writeText` 需 `try/catch`（部分浏览器无权限时会 reject）

### 4.4 撤回

- ❗ 调 `actionStore.revoke()`
- ❗ 仅对 `isSentBySelf === true` 的消息显示撤回选项
  - ❌ 对别人消息也显示撤回
- ❗ 撤回失败（超时限）时展示 errorMsg（SDK 会抛错）
- ❗ 撤回成功后 messageList 自动更新为 Tips 消息（store 内部处理），前端不手动 splice
  - ❌ 手动从 messageList 中删除该消息

### 4.5 删除

- ❗ 调 `actionStore.delete()`
- ❗ 必须二次确认，按钮做危险态：
  - 有 UI 库 → 用 UI 库的 Dialog 组件
  - 无 UI 库 + 有 Tailwind/SCSS → 自建最小 Dialog 复用已有 CSS 方案
  - 无 UI 库 + 空项目 → 原生 `confirm()`，标注 `// TODO: 替换为 Dialog 组件`
  - ❌ 点击直接删除无确认
- ❗ 删除是**仅本地**，不影响对方——需在确认弹窗中明确告知
- ❗ 删除成功后 messageList 自动同步，不手动 splice

### 4.6 下载媒体

- ❗ Web 端 `downloadMedia()` 不可用（SDK throw "not supported on web"）
- ❗ Web 端替代方案：用 `<a>` 标签 + `download` 属性，href 取 payload 中的 URL：
  - Image: `msg.messagePayload.originalImageUrl`
  - Video: `msg.messagePayload.videoUrl`
  - Audio: `msg.messagePayload.audioUrl`
  - File: `msg.messagePayload.fileUrl`
- ❗ 不准调 `downloadMedia()` 后不 catch（会 throw）
  - ❌ 无 try/catch 直接调 `downloadMedia()`
- ❗ 下载按钮仅对媒体类型消息显示

## 5. 反例库

> § 4 已内联主要反例。本节补充跨规则复合错误：

- ❌ 把 `useMessageActionStore` 在 MessageList 级别创建一个长期实例（应该是按消息按需创建）
- ❌ 撤回 + 删除写在同一个函数里一起调（二者是独立操作，不应耦合）
- ❌ 复制非 Text 消息时 `JSON.stringify(messagePayload)` 给用户（无意义）
- ❌ 先 `emit('close')` 再通过 callback 使用 store（操作顺序错误导致 `MessageActionStore has been destroyed`）：
  ```ts
  // ❌ 先 close → store 被 onScopeDispose 销毁 → callback 里 store 已死
  function handleDelete() {
    emit('close')
    emit('request-delete', { confirm: async () => actionStore.delete() })
  }

  // ✅ 先操作完成，再 close
  async function handleDelete() {
    const confirmed = await showConfirmDialog('确认删除？')
    if (!confirmed) return
    await actionStore.delete()  // store 还活着
    emit('close')               // 操作完成后再销毁
  }
  ```

## 6. UI 自由度

> 样式由 AI 自由发挥，遵循项目已有 CSS 方案（见 `_base/detect-style.md`）。

✅ 完全自由：菜单形态（Dropdown / Popover / BottomSheet）/ 触发方式（右键 / 长按 / 悬浮按钮）/ 图标 / 动画 / toast 样式
⚠️ 必须遵循项目现状：UI 库 / CSS 方案
⚠️ § 4 强约束不可放宽

## 7. 参考实现

```vue
<script setup lang="ts">
import { useMessageActionStore } from 'tuikit-atomicx-vue3/chat'
import { MessageType } from 'tuikit-atomicx-vue3/chat'
import type { MessageInfo } from 'tuikit-atomicx-vue3/chat'

const props = defineProps<{ message: MessageInfo }>()

// setup 顶层创建一次，菜单关闭时随组件 onScopeDispose 自动销毁
const actionStore = useMessageActionStore(props.message)

const canCopy = props.message.messageType === MessageType.Text
const canRevoke = props.message.isSentBySelf
const canDownload = [MessageType.Image, MessageType.Video, MessageType.Audio, MessageType.File]
  .includes(props.message.messageType)

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(props.message.messagePayload.text)
    // 展示 "Copied" 提示
  } catch { /* clipboard 权限失败兜底 */ }
}

async function handleRevoke() {
  try {
    await actionStore.revoke()   // 先操作
    emit('close')                // 操作完成后再关闭菜单
  } catch (err: any) {
    // 展示错误（如"撤回超时"）
  }
}

async function handleDelete() {
  // 有 UI 库 → 用 UI 库 Dialog；有 Tailwind → 自建最小 Dialog
  const confirmed = await showConfirmDialog(`确认删除该消息？（仅删除本地）`)
  if (!confirmed) return
  await actionStore.delete()   // 先操作
  emit('close')                // 操作完成后再关闭菜单
}

function handleDownload() {
  const payload = props.message.messagePayload as any
  let url = ''
  switch (props.message.messageType) {
    case MessageType.Image: url = payload.originalImageUrl; break
    case MessageType.Video: url = payload.videoUrl; break
    case MessageType.Audio: url = payload.audioUrl; break
    case MessageType.File: url = payload.fileUrl; break
  }
  if (!url) return
  const a = document.createElement('a')
  a.href = url
  a.download = payload.fileName || 'download'
  a.click()
}
</script>

<template>
  <!-- 菜单 UI（Dropdown / Popover / BottomSheet，按项目实现） -->
  <div class="action-menu">
    <button v-if="canCopy" @click="handleCopy">Copy</button>
    <button v-if="canRevoke" @click="handleRevoke">Revoke</button>
    <button @click="handleDelete" class="danger">Delete</button>
    <button v-if="canDownload" @click="handleDownload">Download</button>
  </div>
</template>
```

### 可改

- 菜单形态 / 触发方式 / 图标 / 动画
- 确认弹窗形式（confirm / Dialog 组件）
- 复制成功反馈形式（toast / inline 提示）
- 下载实现（a 标签 / window.open）

### 不可改

- `useMessageActionStore(message)` 传完整 MessageInfo
- 不手动 destroy
- 不绕过 store 调旧 API
- 菜单项按类型/状态动态过滤
- 撤回仅 isSentBySelf
- 删除必须二次确认
- Web 端下载不调 `downloadMedia()`（改用 URL 直接下载）
