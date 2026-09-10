---
id: chat/conversation-list
name: 会话列表
product: chat
platform: web
description: 会话列表（加载 / 渲染 + 置顶 / 删除 / 免打扰 基础操作）
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: []
trigger-keywords: [会话列表, conversation list, 最近联系人, 置顶, pin, 删除会话, 免打扰, mute, do not disturb, 发起单聊, 发起群聊, 创建会话, 创建群组, 冷启动]
prerequisites: [login-auth]
tags: [chat, vue3]
---

## 1. 这个 slice 处理什么

路径 A 基础功能。在 `src/components/chat/ConversationList.vue` 通过 `useConversationListStore()` 拉取并渲染会话列表。**只覆盖：加载 / 渲染 + 置顶 / 删除 / 免打扰**。

> SDK 一次性返回全部会话，不分页。本 slice 不暴露 `hasMoreConversations` / `loadMoreConversations`。
> 其他操作（标星 / 标已读未读 / 草稿 / 清空消息）见 `features/conversation-actions.md`。

## 2. AI 思考清单

- 是否要分组？（默认无分组传 `undefined`，按需传 `conversationGroup` 字符串）
- 点击会话后怎么切换？（`emit('select', id)` / 路由跳转 / 全局 store）
- 是否需要显示草稿提示 / 群标识 / 免打扰图标？
- 操作触发方式？（右键菜单 / 长按 / 侧滑 / 悬浮按钮）

## 3. SDK API 必读

```ts
import { useConversationListStore } from 'tuikit-atomicx-vue3/chat'
import { ReceiveMessageOption, ConversationType, MessageType } from 'tuikit-atomicx-vue3/chat'
import type { ConversationInfo } from 'tuikit-atomicx-vue3/chat'

const {
  conversationList,        // ComputedRef<ConversationInfo[]>
  totalUnreadCount,        // ComputedRef<number>
  loadConversations,       // (option?) => Promise
  getConversationInfo,     // (conversationID: string) => Promise<ConversationInfo> — 获取/创建单条会话
  pinConversation,         // (id, pin: boolean) => Promise
  deleteConversation,      // (id) => Promise
  setReceiveMessageOpt,    // (id, opt: ReceiveMessageOption) => Promise
} = useConversationListStore(/* 可选 conversationGroup?: string */)
```

创建群组（§ 4.7 发起群聊用）：

```ts
import { useGroupStore } from 'tuikit-atomicx-vue3/chat'
import { GroupType } from 'tuikit-atomicx-vue3/chat'

const { createGroup } = useGroupStore()
// createGroup(params: GroupCreateParams) => Promise<string>  // 返回值直接是 groupID
```

`GroupCreateParams` 完整字段：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `groupName` | `string` | ✅ | — | 群名称 |
| `groupType` | `GroupType` | 否 | `GroupType.Work` | 群类型枚举（Work / Public / Meeting / AVChatRoom） |
| `groupID` | `string` | 否 | SDK 自动生成 | 自定义群 ID，不填则由服务端生成 |
| `avatarURL` | `string` | 否 | — | 群头像 URL |
| `memberList` | `string[]` | 否 | `[]` | 初始成员 userID 列表 |

- ❗ `groupType` 必须用 `GroupType` 枚举，不准写字符串
  - ❌ `groupType: 'Public'`
  - ✅ `groupType: GroupType.Public`
- ❗ § 4.7 发起群聊默认使用 `GroupType.Public`（非默认的 Work，因为 Work 群不允许主动加入）

`ConversationInfo` 关键字段：

| 字段 | 类型 | 用途 |
|---|---|---|
| `conversationID` | `string` | 唯一 ID（含 `C2C` / `GROUP` 前缀） |
| `type` | `ConversationType \| undefined` | `Group` / `C2C`，渲染图标 |
| `groupType` | `GroupType \| undefined` | 群类型（Work / Public / Meeting / AVChatRoom），仅群聊有值 |
| `title` | `string \| undefined` | 已合成的会话名 |
| `avatarURL` | `string \| undefined` | 已合成的头像 URL |
| `isPinned` | `boolean` | 是否置顶 |
| `unreadCount` | `number` | 未读数 |
| `draft` | `string \| undefined` | 草稿（非空时优先于 lastMessage 显示） |
| `lastMessage` | `MessageInfo \| undefined` | 最后一条消息 |
| `receiveOption` | `ReceiveMessageOption` | 免打扰状态 |
| `groupAtInfoList` | `GroupAtInfo[] \| undefined` | 群 @ 信息列表（含 @ 自己 / @ 所有人），有值时在徽标旁显示 @ 提示 |
| `conversationMarkList` | `ConversationMarkType[]` | 会话标记列表（Star / Unread 等枚举值）；空数组表示无标记 |
| `conversationGroupList` | `string[]` | 所属会话分组名列表；空数组表示未分组 |

lastMessage 预览取值：

```
draft 非空 → "[Draft] " + draft
否则按 lastMessage.messageType 映射：
  Text → .messagePayload.text | Image → [Image] | Video → [Video]
  Audio → [Audio] | File → [File] | Face → [Sticker]
  Custom → [Custom] | Merged → [Chat Record] | Tips → [Notice]
  Stream → .messagePayload.markdown | 兜底 → [Message]
```

## 4. Hard rules

> ❗ 所有 SDK 异步调用必须遵循 `references/06-a-defensive-coding.md` 防御编程规范（try/catch/finally、formatError、错误反馈形式、状态锁）。本节规则是该规范的专属补充，不替代它。
> ❗ 写 UI 代码前必须先 `read_file _base/style-guide.md`，按其规范生成样式，不准跳过。

### 4.1 数据 / 加载

- ❗ 登录完成后再调 `loadConversations()`（`onMounted` + `try/finally` 控制 loading 态）
- ❗ 直接用 `conversationList` ComputedRef 渲染，不准赋给本地 ref
  - ❌ `const list = ref(conversationList.value)` — 丢响应性
- ❗ 不准手动 `chat.on(...)` / `setInterval` 轮询，store 已自动同步
- ❗ 不准写"加载更多"按钮（不分页）
- ❗ 三态显式区分：loading / empty / 有数据

### 4.2 头像渲染

- ❗ 优先级：`conv.avatarURL` 非空 → `<img>`（必须有 `@error` 兜底）→ 字母头像（取首个 Unicode 码点，背景色按 ID 哈希稳定）
  - ❌ 不做 `@error` 兜底，静默显示破图
  - ❌ 用外网占位图（`placehold.co` / `dicebear`）
  - ❌ `title[0]` 直接切（emoji 会坏），应 `[...title][0]?.toUpperCase()`
  - ❌ 背景色 `Math.random()`（刷新闪烁）

### 4.3 置顶 / 删除

- ❗ `pinConversation(id, !conv.isPinned)` 第二参必须为布尔
  - ❌ 漏传第二参 / 传字符串
- ❗ `deleteConversation(id)` 后不准手动 `splice`，store 自动同步
  - ❌ `conversationList.value.splice(idx, 1)`
- ❗ 删除必须二次确认，按钮做危险态：
  - 有 UI 库 → 用 UI 库的 Dialog 组件
  - 无 UI 库 → 自建最小 Dialog（有 Tailwind/SCSS 复用已有 CSS 方案；无 CSS 方案时用 `confirm()` 并标 `// TODO: 替换为 Dialog 组件`）
- ❗ 已置顶项必须有视觉提示（pin 图标 / 底色变化）
- ❗ 必须暴露至少一种触发入口，不准只写函数不给 UI

### 4.4 选中时清未读数

- ❗ `clearConversationUnreadCount` 从 `useConversationListStore()` 解构（与 § 3 同一个 store 实例，不需要额外 import）
- ❗ 选中会话时内部调用 `clearConversationUnreadCount(conversationID)` 清零未读
- ❗ 相同 conversationID 连续触发需防抖（判断 ID 未变则跳过，不重复调用）
- ❗ 此调用在 `emit('select', conversationID)` 之前完成，父组件不感知
  - ❌ 把 clearConversationUnreadCount 暴露给父组件调用
  - ❌ 不做防抖，快速连点同一会话多次调接口
  - ❌ 从其他 store / 自行 import SDK 方法调用

### 4.5 免打扰

- ❗ 状态判定必须用枚举：`conv.receiveOption !== ReceiveMessageOption.Receive`
  - ❌ 魔法数字 `conv.receiveOption !== 1`
  - ❌ 字符串 `'mute'` / 布尔 `true`
- ❗ 切换传 `ReceiveMessageOption` 枚举值
- ❗ 必须有视觉反馈（铃铛图标 / 菜单文案切换）
- ❗ 免打扰下未读徽标**必须变灰**（不能仍是高饱和主色）
- ❗ 免打扰不改变 `unreadCount` 数字，只是 UI 降级

### 4.6 冷启动（首次会话列表为空）

- ❗ 登录成功 + `loadConversations()` 后 `conversationList.length === 0` → 自动与 `administrator` 创建一条 C2C 会话
- ❗ 使用 `useConversationListStore().getConversationInfo('C2Cadministrator')` 触发会话创建
- ❗ 仅当列表确实为空时触发，已有会话不重复创建
- ❗ 不发消息，仅建立会话关系（让用户看到非空列表即可）
  - ❌ 自动发一条"欢迎消息"（侵入用户数据）

### 4.7 创建会话入口（列表头部）

- ❗ 会话列表顶部必须有两个创建入口：**发起单聊** + **发起群聊**
- ❗ 这是基础件套的一部分，不需要额外命中 feature slice

#### 发起单聊

- ❗ **必须以 Dialog 弹窗形式呈现**，不准 inline 展开在列表区域内——inline 表单破坏会话列表布局
- 弹窗内容：userID 输入框 + 确定按钮 + 取消按钮
- 用户点确定 → 调 `useConversationListStore().getConversationInfo('C2C' + userID)` → 创建/获取会话 → emit select 跳转
- ❗ **失败时用 Toast 提示**（居中/偏上），不准在列表区域内 inline 显示 errorMsg——errorMsg 会遮挡会话列表
  - ❌ 没有取消按钮
  - ❌ inline 展开在列表顶部
  - ❌ 没有输入入口，只能等别人先发消息

#### 发起群聊

- ❗ **必须以 Dialog 弹窗形式呈现**，不准 inline 展开在列表区域内
- 调 `useGroupStore().createGroup(params)` 创建群组
- 参数默认值：
  - `groupType`: `GroupType.Public`
  - `groupName`: `'group_test'`（用户可修改）
  - `groupID`: 不填（IM 后台自动生成）
  - `memberList`: 由用户输入（内容可以不填，不填则群内只有群主自己）
- ❗ `groupType` 必须传 `GroupType` 枚举值
  - ❌ `groupType: 'Public'`（字符串会报错）
- 创建成功后自动跳转到该群会话（`emit('select', 'GROUP' + groupID)`）
- UI 形式：Dialog 弹窗，包含：
  - 群名输入框（默认值 `group_test`，用户可修改）
  - 成员 userID 输入框（**UI 必须有此输入框**；多个 userID 英文逗号分隔；内容可以不填，不填则群内只有群主自己）
  - 确认按钮 → 调 `createGroup` → 跳转到群会话
  - ❌ 没有创建群聊入口

## 5. 反例库

> § 4 各条已内联主要反例。本节补充跨规则复合错误：

- ❌ 顶部 `const list = (await loadConversations()).data` 赋给本地 ref → 同时违反 4.1（丢响应性）+ 后续操作（pin/delete/mute）不会反映到 UI
- ❌ 切换免打扰时顺手清了 `unreadCount`（免打扰只是 UI 降级，不改数据）

## 6. UI 自由度

> 样式由 AI 自由发挥，遵循项目已有 CSS 方案（见 `_base/detect-style.md`）。

✅ 完全自由：列表样式 / 头像形状 / 字母头像配色 / 触发方式 / 徽标位置 / 加载态插画
⚠️ 必须遵循项目现状：UI 库 / CSS 方案 / 同类组件命名
⚠️ § 4 强约束不可放宽

## 7. 参考实现

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useConversationListStore, useGroupStore } from 'tuikit-atomicx-vue3/chat'
import { ConversationType, ReceiveMessageOption, MessageType, GroupType } from 'tuikit-atomicx-vue3/chat'
import type { ConversationInfo } from 'tuikit-atomicx-vue3/chat'

const emit = defineEmits<{ select: [id: string] }>()

const {
  conversationList,
  loadConversations,
  getConversationInfo,
  pinConversation,
  deleteConversation,
  setReceiveMessageOpt,
} = useConversationListStore()

const { createGroup } = useGroupStore()

const loading = ref(true)

onMounted(async () => {
  try {
    await loadConversations()
    // § 4.6 冷启动：列表为空时自动创建 administrator 会话
    if (conversationList.value.length === 0) {
      await getConversationInfo('C2Cadministrator')
    }
  } finally { loading.value = false }
})

// ── 创建会话入口（§ 4.7） ──

async function startC2C(userID: string) {
  if (!userID.trim()) return
  await getConversationInfo('C2C' + userID)
  emit('select', 'C2C' + userID)
}

async function startGroup(groupName = 'group_test', memberList: string[] = []) {
  const groupID = await createGroup({
    groupType: GroupType.Public,
    groupName,
    ...(memberList.length ? { memberList } : {}),
  })
  emit('select', 'GROUP' + groupID)
}

// ── 列表操作 ──

function getAvatarFallback(conv: ConversationInfo): string {
  const title = conv.title ?? conv.conversationID
  return [...title][0]?.toUpperCase() ?? '?'
}

function getLastMessagePreview(conv: ConversationInfo): string {
  if (conv.draft) return `[Draft] ${conv.draft}`
  const msg = conv.lastMessage
  if (!msg) return ''
  switch (msg.messageType) {
    case MessageType.Text:   return msg.messagePayload.text
    case MessageType.Image:  return '[Image]'
    case MessageType.Video:  return '[Video]'
    case MessageType.Audio:  return '[Audio]'
    case MessageType.File:   return '[File]'
    case MessageType.Face:   return '[Sticker]'
    case MessageType.Custom: return '[Custom]'
    case MessageType.Merged: return '[Chat Record]'
    case MessageType.Tips:   return '[Notice]'
    case MessageType.Stream: return msg.messagePayload.markdown || '[Stream]'
    default: return '[Message]'
  }
}

const isMuted = (c: ConversationInfo) => c.receiveOption !== ReceiveMessageOption.Receive

async function handlePin(conv: ConversationInfo) {
  await pinConversation(conv.conversationID, !conv.isPinned)
}

async function handleDelete(conv: ConversationInfo) {
  // 有 UI 库 → 用 UI 库 Dialog；有 Tailwind → 自建最小 Dialog（见 style-guide.md §3 弹窗规范）
  // 无任何 CSS 方案（极少情况）→ confirm() 并标 TODO
  const confirmed = await showConfirmDialog(`确认删除会话「${conv.title ?? conv.conversationID}」？`)
  if (!confirmed) return
  await deleteConversation(conv.conversationID)
}

async function handleMute(conv: ConversationInfo) {
  await setReceiveMessageOpt(
    conv.conversationID,
    isMuted(conv) ? ReceiveMessageOption.Receive : ReceiveMessageOption.NotNotify,
  )
}
</script>

<template>
  <div class="conv-list">
    <!-- § 4.7 创建会话入口 -->
    <div class="conv-list-header">
      <!-- AI 自由选择 UI 形态：按钮 / icon / dropdown -->
      <!-- startC2C: 弹出输入 userID 的 Dialog -->
      <!-- startGroup: 弹出填写群名（默认 group_test）+ 成员 userID 的 Dialog -->
    </div>

    <div v-if="loading">Loading...</div>
    <div v-else-if="conversationList.length === 0">No conversations yet</div>
    <template v-else>
      <div
        v-for="conv in conversationList"
        :key="conv.conversationID"
        class="conv-item"
        :class="{ pinned: conv.isPinned, muted: isMuted(conv) }"
        @click="emit('select', conv.conversationID)"
      >
        <img v-if="conv.avatarURL" :src="conv.avatarURL" @error="($event.target as HTMLImageElement).style.display='none'" />
        <span v-else class="avatar-fallback">{{ getAvatarFallback(conv) }}</span>

        <div class="conv-body">
          <span class="conv-title">{{ conv.title ?? conv.conversationID }}</span>
          <p class="conv-preview">{{ getLastMessagePreview(conv) }}</p>
        </div>

        <span v-if="conv.unreadCount > 0" class="badge" :class="{ 'badge-muted': isMuted(conv) }">
          {{ conv.unreadCount > 99 ? '99+' : conv.unreadCount }}
        </span>
      </div>
    </template>
  </div>
</template>
```

### 可改

- 样式 / class 名 / Tailwind / 项目 CSS 方案
- 触发方式（右键 / 长按 / 侧滑 / 悬浮按钮）
- 二次确认形式（Dialog 组件的样式和触发方式）
- 字母头像配色板
- 图标库选型（铃铛 / pin 图标）
- 创建会话入口的 UI 形态（按钮 / icon / dropdown / Dialog）
- 创建群聊表单的布局和样式

### 不可改

- `useConversationListStore()` 解构出的 API 名
- `useGroupStore().createGroup()` 创建群聊的 API 名
- 冷启动目标为 `C2Cadministrator`（§ 4.6）
- 创建单聊用 `getConversationInfo('C2C' + userID)`（§ 4.7）
- 创建群聊默认 `GroupType.Public`（§ 4.7）
- 头像兜底链顺序（§ 4.2）
- 删除二次确认（§ 4.3）
- `pinConversation` 第二参为布尔
- `setReceiveMessageOpt` 传枚举（§ 4.5）
- 免打扰下徽标变灰
- 不加 `chat.on(...)` / 不 `setInterval`
