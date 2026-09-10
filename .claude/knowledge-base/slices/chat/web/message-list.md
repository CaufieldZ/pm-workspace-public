---
id: chat/message-list
name: 消息列表
product: chat
platform: web
description: 消息列表（加载 / 上滑加载历史 / 渲染 + 新消息监听 + 滚动状态机）
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: [MessageListStore]
trigger-keywords: [消息列表, message list, 聊天记录, 消息滚动, 内部滚动, 上滑加载历史, 新消息提示, scroll to bottom, MessageListStore]
prerequisites: [login-auth, conversation-list]
tags: ['MessageListStore']
---

## 1. 这个 slice 处理什么

路径 A 基础功能。在 `src/components/chat/MessageList.vue` 通过 `useMessageListStore(conversationID)` 拉取并渲染**当前会话**的消息列表，订阅 `onEvent` 接收新消息，按 `MessageInfo` 渲染气泡，处理**上滑加载历史 + 贴底自动滚动 + 新消息提示徽标**这一组核心交互。

> **本 slice 只覆盖 5 个 API**：`messageList` / `hasOlderMessages` / `loadMessages` / `loadOlderMessages` / `onEvent`。其余 6 个 API 不在 starter 范围：
> - `hasNewerMessages` / `loadNewerMessages` + `MessageLoadOption.cursor/direction` → 见 `features/message-fragment-jump.md`
> - `pinnedMessageList` → 见 `features/pinned-message.md`
> - `sendMessageReadReceipts` → 见 `features/read-receipts.md`
> - `deleteMessages` / `forwardMessages` → 见 `features/recall-edit-reply.md` & `features/forward-message.md`
>
> 写代码时**不要**把这些 API 解构出来，更不要假装实现一半。

## 2. AI 思考清单（写代码前必须想清楚）

- 当前会话 ID（`C2C${userID}` 或 `GROUP${groupID}`）从哪传入——`defineProps` / route / 全局 store？
- MessageList 的高度从哪来：父级 flex 还是固定高度？是否需要 `min-height: 0`？
- 滚动到底部的时机（首次 / 自己发送 / 收到新消息且贴底）+ 用户上翻时如何不被新消息打断
- 上滑加载历史时如何保持视线锚点（高度差补偿 `scrollTop`）
- 头像 / 昵称是否需要展示（从 `msg.from` 取，按兜底链）
- 是否需要时间分组标签（5 分钟阈值）

## 3. SDK API 必读（绝对真理）

### 3.1 引入与初始化

```ts
import { useMessageListStore } from 'tuikit-atomicx-vue3/chat'
import type { MessageInfo, MessageEvent } from 'tuikit-atomicx-vue3/chat'
import { MessageType, MessageStatus } from 'tuikit-atomicx-vue3/chat'

const { messageList, hasOlderMessages, loadMessages, loadOlderMessages, onEvent }
  = useMessageListStore(props.conversationID)
```

| API | 类型 | 作用 |
|---|---|---|
| `messageList` | `ComputedRef<MessageInfo[]>` | 按时间正序（旧→新），直接 `v-for` |
| `hasOlderMessages` | `ComputedRef<boolean>` | 控制"加载更早"入口显隐 |
| `loadMessages` | `(option?) => Promise<void>` | 首次加载最新一页，**starter 不传参** |
| `loadOlderMessages` | `() => Promise<void>` | 上滑拉历史 |
| `onEvent` | `(listener) => unsubscribe` | 订阅事件，**必须存 unsubscribe 并在 onUnmounted 释放** |

### 3.2 MessageInfo 关键字段

#### 顶层字段（`MessageInfoBase`）

| 字段 | 类型 | 用途 |
|---|---|---|
| `msgID` | `string` | 业务侧消息 ID，用作 `v-for :key` |
| `messageType` | `MessageType`（枚举数字） | `Text=1` / `Image=2` / `Video=3` / `Audio=4` / `File=5` / `Face=6` / `Tips=7` / `Custom=8` / `Merged=9` / `Stream=10` / `Unknown=0` |
| `messagePayload` | `XxxMessagePayload` | 按 `messageType` discriminated union 收窄 |
| `from` | `MessageSenderInfo`（**对象**） | 含 `userID` / `nickname` / `avatarURL` / `friendRemark` / `nameCard` |
| `to` | `string` | 接收方 |
| `isSentBySelf` | `boolean` | 决定气泡左/右 |
| `timestamp` | `Date \| undefined` | **已是 Date 对象**，不是秒/毫秒数字 |
| `status` | `MessageStatus`（枚举数字） | `InitStatus=0` / `Sending=1` / `SendSuccess=2` / `SendFail=3` / `Recalled=4` / `Deleted=5` / `LocalImported=6` / `Violation=7` |

> starter 只关心 `msgID` / `messageType` / `messagePayload` / `from` / `isSentBySelf` / `timestamp` / `status`。

#### `from: MessageSenderInfo`

| 字段 | 类型 |
|---|---|
| `userID` | `string`（必有） |
| `avatarURL` | `string \| undefined` |
| `nickname` | `string \| undefined` |
| `friendRemark` | `string \| undefined` |
| `nameCard` | `string \| undefined`（仅群聊有意义） |

### 3.3 onEvent 事件类型

```ts
type MessageEvent = { type: 'onReceiveNewMessage'; message: MessageInfo }
```

`event.type` switch 必须保留 default 分支。

## 4. Hard rules（AI 必须遵守）

> ❗ 所有 SDK 异步调用必须遵循 `references/06-a-defensive-coding.md` 防御编程规范（try/catch/finally、formatError、错误反馈形式、状态锁）。本节规则是该规范的专属补充，不替代它。
> ❗ 写 UI 代码前必须先 `read_file _base/style-guide.md`，按其规范生成样式，不准跳过。

### 4.1 数据 / 加载

- ❗ `useMessageListStore(props.conversationID)` 的 `conversationID` **必填**
  - ❌ `useMessageListStore()` 不传参
- ❗ 渲染直接用 `messageList`（`v-for="msg in messageList"`），不准 `.value` 解构后赋给本地 `ref`
  - ❌ `const list = ref(messageList.value)` — 丢失响应性
- ❗ 不准 `chat.on(...)` 手动订阅 / 不准 `setInterval` 轮询（store 已托管）
- ❗ `onEvent` 必须存 `unsubscribe` + `onUnmounted` 释放；`event.type` switch 必须有 default
  - ❌ `onMounted` 订阅但 `onUnmounted` 没释放（页面切换泄漏 + 旧组件还在收消息）
- ❗ 首次加载放 `onMounted`，`try/finally` 控制 `loadingInitial` 态
- ❗ "加载中" / "空列表" / "有数据" 三态显式区分
- ❗ `loadMessages()` **不传参**（传 `cursor`/`direction`/`messageListType` 属于 fragment feature）
  - ❌ `loadMessages({ direction: 'both', cursor: '...' })`
- ❗ 不准解构 `loadNewerMessages` / `hasNewerMessages` / `pinnedMessageList` / `deleteMessages` / `forwardMessages` / `sendMessageReadReceipts`（属于其他 feature）

### 4.2 滚动容器（强约束）

- ❗ **MessageList 必须是「内部滚动」容器**（`overflow-y: auto` + `overflow-x: hidden`），不准把外层页面顶出滚动条，也不准出现水平滚动条
  - ❌ 只写 `overflow-y: auto` 不加 `overflow-x: hidden`，长文本消息撑宽 flex 行导致水平滚动
  - ❌ 没设确定高度，消息一多把外层整体滚动
- ❗ 外层给确定高度（`height: 100%` / `flex: 1` / `calc(100vh - header - input)` 三选一）
- ❗ flex 子项必须 `min-height: 0`（否则内容撑爆 flex 容器）
  - ❌ flex 布局没加 `min-height: 0`，`overflow` 失效
- ❗ 消息行（msg-row）内的气泡必须有宽度上限（如 `max-width: 70%`）**且气泡自身设 `overflow-wrap: break-word`**，防止单行长文本撑破布局
- ❗ 不准对 `body`/`html`/`#app` 做 `overflow: hidden` 兜底
- ❗ 滚到底用 `el.scrollTop = el.scrollHeight`（auto）或 `el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })`，**且要 `await nextTick()`**

### 4.3 滚动状态机（强约束）

| 触发场景 | 是否滚到底 | 是否累加新消息计数 |
|---|---|---|
| 首次加载完成 | ✅ auto 滚（无动画） | — |
| 自己发送（`isSentBySelf`） | ✅ smooth 滚 | 否 |
| 别人发送 + 当前**贴底** | ✅ smooth 滚 | 否 |
| 别人发送 + 当前**没贴底** | ❌ 不滚 | ✅ `newMessageCount++` |

- ❗ "贴底"判定：`scrollHeight - scrollTop - clientHeight < 150px`
- ❗ 没贴底时必须显示"N 条新消息"提示徽标，点击滚到底 + 清零
  - ❌ 没贴底 + 收到新消息时无任何提示
- ❗ 用户手动滚到底时也要清零计数
- ❗ 用户上翻看历史时收到新消息**不准**强制滚到底
  - ❌ 收到消息无条件 `scrollTop = scrollHeight`
- ❗ `watch(messageList)` 兜底——乐观插入不触发 `onReceiveNewMessage` 时，diff 末尾 `isSentBySelf` 补滚
- ❗ `loadingOlder` 期间 `watch` 兜底必须跳过（`if (loadingOlder.value) return`）
  - ❌ 上滑加载期间兜底滚动把用户拽到底

### 4.3.1 活跃会话清未读数（强约束）

> 用户正在看当前会话时收到新消息，应自动清零未读数，但需控制调用频率。

- ❗ `clearConversationUnreadCount` 从 `useConversationListStore()` 解构获取（需在组件顶部额外解构此方法）：
  ```ts
  import { useConversationListStore } from 'tuikit-atomicx-vue3/chat'
  const { clearConversationUnreadCount } = useConversationListStore()
  ```
- ❗ 仅当 `msg.conversationID === props.conversationID` 时才计入清理逻辑
- ❗ 清理策略（条件取 OR，命中任一即调用 `clearConversationUnreadCount`）：
  - 条件 A：本会话累积未读数 ≥ 5 → 立即执行
  - 条件 B：累积未读数 < 5 且距上次清理 ≥ 10s → 执行一次
- ❗ 调用后重置计数器和计时器
- ❗ 组件卸载时如果计数器 > 0，执行一次最终清理（兜底）
  - ❌ 每收到一条新消息就调一次 clearConversationUnreadCount（高频场景打爆接口）
  - ❌ 只靠固定 interval 轮询（低频场景响应慢）
  - ❌ 组件卸载不做兜底清理（残留未读数）
  - ❌ 自行 `import { clearConversationUnreadCount } from 'tuikit-atomicx-vue3/chat'`（不存在此导出）

### 4.4 上滑加载历史（强约束）

- ❗ 入口用 `hasOlderMessages` 控制显隐
- ❗ 调 `loadOlderMessages()`，禁止自己拼 `MessageLoadOption`
- ❗ 视线锚点补偿：拉取前记 `oldScrollHeight`，拉取后 `await nextTick()` → `el.scrollTop = el.scrollHeight - oldScrollHeight`
  - ❌ 不补偿，用户视线被顶到列表顶部
- ❗ `loadingOlder` 独立态，避免重复触发；disabled 期间用 spinner
  - ❌ 没有 `loadingOlder` 节流，连点 N 次

### 4.5 头像 / 昵称兜底链（强约束）

字段从 `msg.from`（`MessageSenderInfo` 对象）取，**不是** `msg.avatar` / `msg.nick` / `msg.from`（当 string）。

- ❗ **头像**：`msg.from.avatarURL` → 昵称首字母（字母头像）→ `msg.from.userID` 首字母
  - 字母头像取首个 Unicode 码点：`[...str][0]?.toUpperCase()`，不准 `str[0]`
  - 配色按 `msg.from.userID` 哈希取固定色，不准随机
  - `<img>` 必须 `@error` 兜底切到字母头像
  - ❌ `msg.from.avatarURL || msg.from.userID[0]` — 跳过昵称首字母档
  - ❌ 字母头像每次渲染随机配色
- ❗ **昵称**：`msg.from.friendRemark` → `msg.from.nameCard`（仅群聊）→ `msg.from.nickname` → `msg.from.userID`
  - 单聊 `nameCard` 跳过
- ❗ 头像与昵称**独立兜底**，不准强制绑定
- ❗ `MessageType.Tips` 系统提示不走头像/昵称

### 4.6 渲染分支（强约束）

- ❗ 按 `msg.messageType` **枚举**判断，必须给下表每个主流 type 单独 `v-else-if` 分支
  - ❌ 只写 `Text` 一个分支 + default 全员 `[Unsupported]`
- ❗ 比较用 `MessageType` 枚举常量，不准用字符串（旧 TIM 字符串全表见 § 5）
  - ❌ `msg.messageType === 'TIMTextElem'` / `'text'`
- ❗ 字段名是 `messageType` / `messagePayload`，不准写成 `type` / `payload`
- ❗ 兜底文案必须带 type：`[Unsupported: {{ msg.messageType }}]`
  - ❌ `[未知消息类型]` / `[Unknown]`

**分支表（写代码时逐行对照）**：

| `msg.messageType` | 取字段（`msg.messagePayload.*`） | 模板要求 |
|---|---|---|
| `MessageType.Text` (1) | `text` | 普通气泡 |
| `MessageType.Image` (2) | `thumbImageUrl` / `originalImageUrl` / `largeImageUrl` | 普通气泡 |
| `MessageType.Video` (3) | `videoUrl` / `videoSnapshotUrl` / `videoDuration` | 普通气泡 |
| `MessageType.Audio` (4) | `audioUrl` / `audioDuration` | 普通气泡 |
| `MessageType.File` (5) | `fileName` / `fileSize` / `fileUrl` | 普通气泡 |
| `MessageType.Face` (6) | `faceIndex` / `faceData` | 普通气泡 |
| `MessageType.Tips` (7) | `groupTips: GroupTipsInfo[]` | ⚠️ **居中系统提示**，不走气泡/头像/左右分列 |
| `MessageType.Custom` (8) | `customData` / `description` / `extensionInfo` | ⚠️ **卡片形态**，在 `msg-bubble` 外部独立存在 |
| `MessageType.Merged` (9) | `title` / `abstractList` | 普通气泡 |
| `MessageType.Stream` (10) | `markdown` / `isStreamEnded` | 普通气泡 |
| 其它 / `Unknown` (0) | — | `[Unsupported: {{ msg.messageType }}]` |

- ❗ **Tips 特殊处理**：居中灰色提示，默认文案 `[System Notice]`
  - ❌ Tips 走普通用户气泡 / `JSON.stringify(messagePayload)` 当文案
- ❗ **撤回消息渲染**：撤回后该消息的 `status` 更新为 `MessageStatus.Recalled`（4），前端需在渲染时判断：
  - `msg.status === MessageStatus.Recalled` → 居中灰色提示（不走普通气泡）
  - 自己撤回（`msg.isSentBySelf`）→ `"你撤回了一条消息"`
  - 对方撤回 → `"{对方昵称}撤回了一条消息"`（昵称取 msg.from 兜底链）
  - ❌ 撤回后仍显示原消息内容
  - ❌ 撤回提示走普通气泡（应居中展示，类似 Tips）
- ❗ **删除消息渲染**：删除后该消息的 `status` 更新为 `MessageStatus.Deleted`（5），前端渲染时需过滤掉 `status === 5` 的消息，不显示任何内容
  - ❌ 删除后仍然渲染该消息
  - ❌ 显示"此消息已删除"占位
  - ❌ 手动 `messageList.value.splice(...)` 移除
- ❗ **Custom 特殊处理**：`v-else-if` 分支在 `msg-bubble` 外部（无气泡包裹）；`customData` 若是 string 需 `try/catch JSON.parse`
  - ❌ `messagePayload.businessID`（SDK 没有此字段，业务约定塞在 `customData` 内嵌 JSON）

### 4.7 时间分组标签（可选）

- ❗ 相邻消息间隔 > 5 分钟才显示一次
- ❗ `timestamp` 是 `Date` 对象，相减用 `getTime()`，阈值 `5 * 60 * 1000`（毫秒）
  - ❌ `new Date(msg.timestamp * 1000)` / 阈值 `5 * 60`（秒）
- ❗ 首条消息（`prev === undefined`）必须显示时间标签
- ❗ `timestamp` 为 `undefined` 时跳过（返回 `false`）

## 5. 反例库

> § 4 各条已内联主要反例。本节补充**旧字段名幻觉对照表**（旧 TIM v2 → 当前 SDK）。

| ❌ 旧写法 | ✅ 正确写法 |
|---|---|
| `msg.type === 'TIMTextElem'` | `msg.messageType === MessageType.Text` |
| `msg.payload.text` | `msg.messagePayload.text` |
| `msg.from`（当 string） | `msg.from.userID` |
| `msg.nick` / `msg.avatar` | `msg.from.nickname` / `msg.from.avatarURL` |
| `new Date(msg.timestamp * 1000)` | 直接用 `msg.timestamp`（Date 对象） |
| `msg.status === 'sendSuccess'` | `msg.status === MessageStatus.SendSuccess` |
| `messagePayload.imageInfoArray[0].url` | `messagePayload.thumbImageUrl` / `originalImageUrl`（扁平字段） |
| `messagePayload.url`（音频） | `messagePayload.audioUrl` |
| `messagePayload.second`（音频） | `messagePayload.audioDuration` |
| `messagePayload.snapshotUrl`（视频） | `messagePayload.videoSnapshotUrl` |
| `messagePayload.data`（表情） | `messagePayload.faceIndex` / `faceData` |
| `messagePayload.data`（自定义） | `messagePayload.customData` / `description` / `extensionInfo` |
| `messagePayload.text`（Stream） | `messagePayload.markdown` |

## 6. UI 自由度

> 样式由 AI 自由发挥，遵循项目已有 CSS 方案（见 `_base/detect-style.md`）。

✅ 完全自由：气泡形状 / 头像位置形状 / 时间显示位置 / 系统消息样式 / 字母头像配色板 / 新消息徽标位置样式 / 加载触发方式（按钮 / 滚顶自动）/ 时间标签样式 / loading 与 empty 插画
⚠️ 必须遵循项目现状：UI 库 / CSS 方案；自定义消息分支保留对应业务卡片组件
⚠️ § 4.2–4.5 是强约束不可放宽

## 7. 参考实现（明确哪些可改）

> ⚠️ **写代码前必须回看 § 4.6 分支表逐行核对字段名，不要凭记忆写。** Tips / Custom 的模板结构约束也在 § 4.6。

### 最小骨架

```vue
<script setup lang="ts">
import { onMounted, onUnmounted, ref, nextTick, watch } from 'vue'
import { useMessageListStore } from 'tuikit-atomicx-vue3/chat'
import type { MessageInfo, MessageEvent } from 'tuikit-atomicx-vue3/chat'
import { MessageType, MessageStatus } from 'tuikit-atomicx-vue3/chat'

const props = defineProps<{ conversationID: string }>()

const {
  messageList,
  hasOlderMessages,
  loadMessages,
  loadOlderMessages,
  onEvent,
} = useMessageListStore(props.conversationID)

// ── 三态 ──
const loadingInitial = ref(true)
const loadingOlder = ref(false)

// ── 滚动状态机 ──
const scrollContainer = ref<HTMLElement | null>(null)
const isNearBottom = ref(true)
const newMessageCount = ref(0)
const didInitialScroll = ref(false)
const NEAR_BOTTOM_THRESHOLD = 150

async function scrollToBottom(behavior: ScrollBehavior = 'auto') {
  await nextTick()
  const el = scrollContainer.value
  if (!el) return
  if (behavior === 'smooth') {
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  } else {
    el.scrollTop = el.scrollHeight
  }
}

function checkNearBottom() {
  const el = scrollContainer.value
  if (!el) return
  isNearBottom.value =
    el.scrollHeight - el.scrollTop - el.clientHeight < NEAR_BOTTOM_THRESHOLD
}

function handleScroll() {
  checkNearBottom()
  if (isNearBottom.value && newMessageCount.value > 0) {
    newMessageCount.value = 0
  }
}

// ── 新消息分支决策 ──
function handleNewMessage(message: MessageInfo) {
  if (message.isSentBySelf) {
    nextTick(() => scrollToBottom('smooth'))
    return
  }
  if (isNearBottom.value) {
    nextTick(() => scrollToBottom('smooth'))
  } else {
    newMessageCount.value++
  }
}

// ── 兜底：乐观插入可能不触发 onEvent ──
watch(messageList, (newList, oldList) => {
  if (!didInitialScroll.value) return
  if (loadingOlder.value) return
  if (newList.length > (oldList?.length ?? 0)) {
    const last = newList[newList.length - 1]
    if (last?.isSentBySelf) {
      nextTick(() => scrollToBottom('smooth'))
    }
  }
})

// ── 生命周期 ──
let unsubscribe: (() => void) | null = null

onMounted(async () => {
  try {
    await loadMessages()
  } finally {
    loadingInitial.value = false
    await nextTick()
    await scrollToBottom('auto')
    didInitialScroll.value = true
  }

  scrollContainer.value?.addEventListener('scroll', handleScroll, { passive: true })

  unsubscribe = onEvent((event: MessageEvent) => {
    switch (event.type) {
      case 'onReceiveNewMessage':
        handleNewMessage(event.message)
        break
      default:
        console.warn('[MessageList] unknown event', event)
    }
  })
})

onUnmounted(() => {
  scrollContainer.value?.removeEventListener('scroll', handleScroll)
  unsubscribe?.()
  unsubscribe = null
})

// ── 上滑加载历史 ──
async function handleLoadOlder() {
  if (loadingOlder.value) return
  const el = scrollContainer.value
  const oldScrollHeight = el?.scrollHeight ?? 0
  loadingOlder.value = true
  try {
    await loadOlderMessages()
    await nextTick()
    if (el) el.scrollTop = el.scrollHeight - oldScrollHeight
  } finally {
    loadingOlder.value = false
  }
}

// ── 时间分组标签 ──
function shouldShowTimeLabel(curr: MessageInfo, prev: MessageInfo | undefined): boolean {
  if (!prev) return true
  if (!curr.timestamp || !prev.timestamp) return false
  return Math.abs(curr.timestamp.getTime() - prev.timestamp.getTime()) > 5 * 60 * 1000
}

function formatTimeLabel(ts: Date): string {
  const now = new Date()
  const sameDay = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  const yesterday = new Date(now); yesterday.setDate(now.getDate() - 1)
  const hhmm = `${String(ts.getHours()).padStart(2, '0')}:${String(ts.getMinutes()).padStart(2, '0')}`
  if (sameDay(ts, now)) return hhmm
  if (sameDay(ts, yesterday)) return `Yesterday ${hhmm}`
  return ts.toLocaleDateString()
}

// ── 头像 / 昵称兜底 ──
function displayName(msg: MessageInfo): string {
  const f = msg.from
  return f.friendRemark || f.nameCard || f.nickname || f.userID
}

function handleBadgeClick() {
  newMessageCount.value = 0
  scrollToBottom('smooth')
}
</script>

<template>
  <div class="msg-list-wrapper">
    <div ref="scrollContainer" class="msg-list">
      <div v-if="loadingInitial" class="state-loading">Loading messages...</div>

      <template v-else>
        <div v-if="hasOlderMessages" class="load-older">
          <button :disabled="loadingOlder" @click="handleLoadOlder">
            {{ loadingOlder ? 'Loading…' : 'Load earlier messages' }}
          </button>
        </div>

        <div v-if="messageList.length === 0" class="state-empty">No messages yet</div>

        <template v-for="(msg, idx) in messageList" :key="msg.msgID">
          <div v-if="shouldShowTimeLabel(msg, messageList[idx - 1])" class="time-label">
            <template v-if="msg.timestamp">{{ formatTimeLabel(msg.timestamp) }}</template>
          </div>

          <!-- ═══ Tips：居中系统提示 ═══ -->
          <div v-if="msg.messageType === MessageType.Tips" class="system-tip">
            [System Notice]
          </div>

          <!-- ═══ Custom：独立卡片形态（无 msg-bubble 包裹） ═══ -->
          <div
            v-else-if="msg.messageType === MessageType.Custom"
            class="msg-row msg-row--card"
            :class="{ 'is-self': msg.isSentBySelf }"
          >
            <!-- Avatar + CustomMessageBubble 由项目自行实现 -->
          </div>

          <!-- ═══ 普通消息气泡 ═══ -->
          <div v-else class="msg-row" :class="{ 'is-self': msg.isSentBySelf }">
            <div class="msg-bubble">
              <div v-if="msg.messageType === MessageType.Text" class="msg-text">
                {{ msg.messagePayload.text }}
              </div>
              <img v-else-if="msg.messageType === MessageType.Image"
                :src="msg.messagePayload.thumbImageUrl ?? msg.messagePayload.originalImageUrl"
              />
              <!-- Audio: audioUrl / audioDuration -->
              <div v-else-if="msg.messageType === MessageType.Audio">
                🔊 {{ msg.messagePayload.audioDuration }}s
              </div>
              <!-- Video: videoUrl / videoSnapshotUrl / videoDuration -->
              <video v-else-if="msg.messageType === MessageType.Video"
                :src="msg.messagePayload.videoUrl"
                :poster="msg.messagePayload.videoSnapshotUrl" controls
              />
              <!-- File: fileUrl / fileName / fileSize -->
              <a v-else-if="msg.messageType === MessageType.File"
                :href="msg.messagePayload.fileUrl" :download="msg.messagePayload.fileName">
                {{ msg.messagePayload.fileName }}
              </a>
              <!-- Face: faceIndex / faceData -->
              <span v-else-if="msg.messageType === MessageType.Face">
                [Sticker: {{ msg.messagePayload.faceIndex }}]
              </span>
              <!-- Merged: title / abstractList -->
              <div v-else-if="msg.messageType === MessageType.Merged">
                {{ msg.messagePayload.title }}
              </div>
              <!-- Stream: markdown / isStreamEnded -->
              <div v-else-if="msg.messageType === MessageType.Stream">
                {{ msg.messagePayload.markdown }}
              </div>
              <div v-else>[Unsupported: {{ msg.messageType }}]</div>

              <span v-if="msg.isSentBySelf && msg.status === MessageStatus.Sending">⏳</span>
              <span v-if="msg.isSentBySelf && msg.status === MessageStatus.SendFail">❗</span>
            </div>
          </div>
        </template>
      </template>
    </div>

    <button v-if="newMessageCount > 0 && !isNearBottom" class="new-msg-badge" @click="handleBadgeClick">
      {{ newMessageCount }} new messages
    </button>
  </div>
</template>
```

### 可改

- 样式 / class / Tailwind / 项目 token
- 上滑触发方式（按钮 / 滚到顶自动）
- 新消息徽标位置样式
- 时间标签格式化（i18n）
- 各 type 具体 UI（图片预览 lib / audio 播放器 / 表情映射表）
- `MessageType.Custom` 的业务卡片组件
- `MessageType.Tips` 的具体翻译文案

### 不可改

- `useMessageListStore(props.conversationID)` 解构 5 个 API
- 不解构 `loadNewerMessages` / `pinnedMessageList` / `deleteMessages` / `forwardMessages` / `sendMessageReadReceipts`
- `loadMessages()` 不传参
- 滚动状态机分支（§ 4.3）+ 视线锚点补偿（§ 4.4）+ 头像昵称兜底链（§ 4.5）
- `onEvent` 存 `unsubscribe` + `onUnmounted` 释放 + default 分支
- 不加 `chat.on(...)` / 不 `setInterval`
- 渲染分支表所有主流 type 必须有单独分支，Tips 居中不走气泡
- 兜底文案带 type（`[Unsupported: {{ msg.messageType }}]`）
- 真实字段名：`msg.msgID` / `msg.messageType` / `msg.messagePayload` / `msg.from.avatarURL` / `msg.from.nickname` / `msg.timestamp`（Date）
