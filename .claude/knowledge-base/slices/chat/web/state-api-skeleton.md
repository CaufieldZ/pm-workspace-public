---
id: chat/state-api-skeleton
name: State API 集成骨架
product: chat
platform: web
description: 'tuikit-atomicx-vue3 Store 集成通用骨架（兜底分支用）'
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: []
trigger-keywords: []
prerequisites: []
tags: [chat, vue3]
---

## 1. 这个 slice 处理什么

为兜底分支（`chat/references/05-slice-loading.md` § 5.3）提供 `tuikit-atomicx-vue3` Store 通用骨架，让 AI 在没有命中具体 features slice 时仍能基于本骨架自由实现。

> 文件名保留 `state-api-skeleton` 以兼容上层 dispatcher 引用；当前底层依赖统一为 `tuikit-atomicx-vue3` 提供的 Store hooks。

## 2. AI 思考清单

- 项目里 `tuikit-atomicx-vue3` 是否已就位？（路径 B 复用现有实例；路径 A 按平台 pattern 安装）
- 用户功能对应哪个 Store hook？（`useLoginStore` / `useConversationListStore` / `useMessageListStore` / `useMessageInputStore`）
- 该 Store 暴露的响应式状态和命令式 API 各是哪些？是否需要订阅事件？

## 3. SDK API 必读

> 通用骨架口径：参考 `vue3/SKILL.md` § 3 入口骨架 + § 4 事件监听约定。

- 所有 Store hook 必须从 `tuikit-atomicx-vue3` 引
- 类型可从 `tuikit-atomicx-vue3` 引（仅做类型标注用）
- 各 Store 具体 API 详见对应 `_starter/*` slice § 3

## 4. Hard rules

- ❗ Store hooks 只能从 `tuikit-atomicx-vue3` 引
  - ❌ `import { LoginStore } from 'tuikit-atomicx-vue3/chat'`（`LoginStore` 不是 hook，应用 `useLoginStore`）
- ❗ 解构 Store 的 `ComputedRef` 后不准赋给本地 `ref`（会断响应式）
  - ❌ `const list = ref(messageList.value)` — 丢失响应性
- ❗ 业务侧不准手写 `loginStore.destroy()` / `chat.create({...})`，单例 Store 由 SDK 管理
  - ❌ `onUnmounted(() => loginStore.destroy())`
- ❗ 业务侧自己加的 `watch` / `addEventListener` 仍需在 `onUnmounted` 解绑
  - ❌ 第三方事件监听不解绑，组件卸载后内存泄漏
- ❗ 多实例 Store（ConversationList / MessageList / MessageInput）必须传 `conversationID`；单例 Store（Login）直接调
  - ❌ `useMessageListStore()` 不传参（运行时报错）
- ❗ 沿用 `vue3/SKILL.md` 的目录约定与入口骨架

## 5. 反例库

> 见 § 4 各条内联反例。

## 6. UI 自由度

✅ 完全自由：UI 由 AI 按项目风格生成
⚠️ 必须遵循项目现状：UI 库 / CSS 方案 / 命名约定（详见 `_base/detect-style.md`）

## 7. 参考实现

> 兜底场景下，参考最相近的 `_starter/*` slice § 7 骨架（如"消息相关" → `message-list.md` 或 `message-input.md`）。
