---
id: chat/direct-chat-entry
name: 直连对话入口
product: chat
platform: web
description: Direct Chat 入口组件（静默登录 + 固定会话 + 三态管理 + 返回行为 + 集成方式）
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: [LoginStore, MessageListStore, MessageInputStore]
trigger-keywords: [直连对话, direct chat, 客服入口, 在线客服页, 单点对话, 固定会话]
prerequisites: [login-auth, message-list, message-input]
tags: ['LoginStore', 'MessageListStore', 'MessageInputStore']
---

## 1. 这个 slice 处理什么

Direct Chat 模式的**入口组件**。用户点击入口（Footer 按钮 / 悬浮按钮 / 路由跳转）→ 本组件自动登录 → 直接渲染指定会话的消息列表 + 输入框。

> 本 slice 是 Direct Chat 模式的**组装层**——内部复用 `login-auth` 的 `loginIM` composable + `message-list` 的 `MessageList` 组件 + `message-input` 的 `MessageInput` 组件，不重复它们的逻辑。

**不在本 slice 处理**：多会话列表（那是 Full Chat 模式的 `conversation-list`）；登录页 UI（Direct Chat 没有独立登录页）。

## 2. AI 思考清单（写代码前必须想清楚）

- 对话对象是谁？（从 `directChatConfig.targetID` + `targetType` 取，拼出 `C2C${id}` 或 `GROUP${id}`）
- 入口集成方式？（独立路由页 / 右下角悬浮弹窗 / 底部 Sheet / 嵌入侧边栏）
- 登录凭据从哪来？（业务 token 换 userSig 接口 / `.env.local` 开发期直接用）
- Header 需要什么？（返回按钮 + 标题 + 在线状态？）
- 登录失败 / 网络断开时的 UX？（就地提示 + 返回按钮，不跳登录页）

## 3. SDK API 必读（绝对真理）

本 slice 不引入新 API，复用已有 slice 的 API：

- `loginIM` / `loginStatus` / `onEvent` → 来自 `login-auth.md` § 3
- `useMessageListStore(conversationID)` → 来自 `message-list.md` § 3
- `useMessageInputStore(conversationID)` → 来自 `message-input.md` § 3

唯一新增的是 **conversationID 拼接逻辑**：

```ts
// targetID 直接写在文件顶部常量，不通过 env 管理（减少配置负担）
// ⚠️ 替换为实际客服 userID 或 groupID（用户在 A.2 Q.3b 中填写的值）
const TARGET_ID = 'administrator'
const targetType = directChatConfig.targetType  // 'C2C' | 'GROUP'
const conversationID = `${targetType}${TARGET_ID}`
```

## 4. Hard rules（AI 必须遵守）

### 4.1 静默登录

- ❗ `onMounted` 自动调 `loginIM()`，不等用户手动触发
  - ❌ 弹出登录表单让用户输入
- ❗ 登录凭据从业务登录态获取（生产）或 `.env.local`（开发期），不准让用户在这个界面手动输入 userSig
- ❗ 登录过程中显示 `connecting` 态（loading spinner + "正在连接..."）

### 4.2 固定 conversationID

- ❗ conversationID 从 `directChatConfig` 拼出，不准让用户选
  - ❌ 弹出会话选择器
- ❗ `C2C` 前缀 + `targetID`（单聊）或 `GROUP` 前缀 + `targetID`（群聊），不准拼错
  - ❌ `conversationID = targetID`（缺少 C2C/GROUP 前缀）

### 4.3 三态管理

- ❗ 必须显式区分三态：`connecting` → `connected` → `error`

| 状态 | UI |
|---|---|
| `connecting` | 居中 loading + "正在连接..." |
| `connected` | MessageList + MessageInput |
| `error` | 错误提示 + 重试按钮 + 返回按钮 |

  - ❌ 没有 loading 态，白屏后突然出现消息
  - ❌ 登录失败白屏无反馈

### 4.4 返回行为

- ❗ 必须有返回按钮（Header 左侧）
- ❗ 点击返回：路由页 → `router.back()`；弹窗 → `emit('close')`
  - ❌ 无返回按钮，用户被困在对话页

### 4.5 被踢下线

- ❗ 被踢下线时跳回来源页面（`router.back()` 或 `emit('close')`），不跳登录页
  - ❌ `router.push('/login')`（Direct Chat 没有登录页）
- ❗ 跳回前 Toast 提示"您的账号在其他设备登录"

### 4.6 集成方式

- ❗ 按 `directChatConfig.entryPosition` 决定组件形态：
  - `route` → 独立路由页（`/customer-service` 等）
  - `floating` → 右下角 fixed 弹窗
  - `sidebar` → 右侧 Drawer
  - `footer-button` → 替换/改造 Footer 中的按钮，点击后展开对话区
- ❗ 非 `route` 方式时，组件必须支持 `v-if` 控制显隐 + 关闭后 cleanup（logout 或保持连接由业务决定）

## 5. 反例库

> § 4 各条已内联反例。本节补充跨规则复合错误：

- ❌ 静默登录写在组件外（`App.vue` onMounted 全局登录）+ conversationID 写死在 message-list 里 → 导致切换对话对象时需要改两处，且全局登录会在不需要聊天的页面也触发
- ❌ 用 `conversation-list` 的 `loadConversations()` 拉会话再取第一条的 ID → 违反 Direct Chat "不需要会话列表"的核心约束

## 6. UI 自由度

> 样式由 AI 自由发挥，遵循项目已有 CSS 方案（见 `_base/detect-style.md`）。

✅ 完全自由：Header 样式 / loading 动画 / 错误提示样式 / 弹窗形态 / 返回按钮图标
⚠️ 必须遵循项目现状：UI 库 / CSS 方案 / 已有 Dialog/Drawer 组件
⚠️ § 4 强约束不可放宽

## 7. 参考实现（明确哪些可改）

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useLoginStore } from 'tuikit-atomicx-vue3/chat'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/chat/MessageInput.vue'

const props = defineProps<{
  targetID: string        // 对话对象 userID 或 groupID
  targetType: 'C2C' | 'GROUP'
}>()

const emit = defineEmits<{ close: [] }>()

const { login, loginStatus, onEvent } = useLoginStore()

// ── 三态 ──
type ConnectionState = 'connecting' | 'connected' | 'error'
const state = ref<ConnectionState>('connecting')
const errorMsg = ref('')

// ── conversationID ──
const conversationID = `${props.targetType}${props.targetID}`

// ── 静默登录 ──
onMounted(async () => {
  try {
    const userID = props.userID  // Direct Chat 由父组件传入或从业务上下文获取
    const { SDKAppID, userSig } = (window as any).genTestUserSig(userID)
    await login({ sdkAppID: SDKAppID, userID, userSig })
    state.value = 'connected'
  } catch (err: any) {
    state.value = 'error'
    errorMsg.value = err?.message ?? '连接失败'
  }
})

// ── 被踢下线 ──
let unsubscribe: (() => void) | null = null
onMounted(() => {
  unsubscribe = onEvent((event) => {
    if (event.type === 'kickedOffline') {
      emit('close')  // 或 router.back()
    }
  })
})
onUnmounted(() => { unsubscribe?.() })

function handleRetry() {
  state.value = 'connecting'
  // 重新调 login...
}
</script>

<template>
  <div class="direct-chat">
    <header class="direct-chat-header">
      <button @click="emit('close')">← 返回</button>
      <span>在线客服</span>
    </header>

    <div v-if="state === 'connecting'" class="state-connecting">
      正在连接...
    </div>

    <div v-else-if="state === 'error'" class="state-error">
      <p>{{ errorMsg }}</p>
      <button @click="handleRetry">重试</button>
      <button @click="emit('close')">返回</button>
    </div>

    <template v-else>
      <MessageList :conversationID="conversationID" />
      <MessageInput :conversationID="conversationID" />
    </template>
  </div>
</template>
```

### 可改

- Header 样式 / 标题文案 / 在线状态展示
- loading / error 的 UI 形态
- 集成方式（route / floating / sidebar / sheet）
- 登录凭据获取方式（env / 后端接口）
- 关闭后是否 logout（业务决定）

### 不可改

- `onMounted` 静默登录（不准弹登录表单）
- conversationID 从 `targetType + targetID` 拼出
- 三态显式区分（connecting / connected / error）
- 必须有返回按钮
- 被踢下线跳回来源（不跳登录页）
- `onEvent` 必须存 unsubscribe + `onUnmounted` 释放
