---
id: chat/conversation-actions
name: 会话增强操作
product: chat
platform: web
description: 会话增强操作（标星收藏 / 标已读未读 / 草稿 / 清空消息）
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: [ConversationListStore]
trigger-keywords: [标星, 收藏, star, 标未读, 标已读, mark unread, mark read, 草稿, draft, 清空消息, clear messages]
prerequisites: [conversation-list]
tags: ['ConversationListStore']
---

## 1. 这个 slice 处理什么

在 starter `conversation-list`（已覆盖加载 / 渲染 + 置顶 / 删除 / 免打扰）之上，叠加 `useConversationListStore()` 的**其余 4 个会话级操作**：

1. **标星 / 收藏** — `markConversation` + `ConversationMarkType.Star`
2. **标已读 / 标未读** — `clearConversationUnreadCount` + `markConversation` + `ConversationMarkType.Unread`
3. **草稿** — `setConversationDraft`
4. **清空消息** — `clearConversationMessages`

> 不重复 starter 已讲过的「加载 / 渲染 / 头像兜底 / 置顶 / 删除 / 免打扰」。

## 2. AI 思考清单（写代码前必须想清楚）

- 操作放哪里：右键菜单 / 长按 / 侧滑？（建议复用 starter 已搭好的菜单入口）
- 是否需要在列表项上视觉化这些状态（星标 / 红点 / 草稿前缀）
- "清空消息"是否需要二次确认（强烈建议与"删除会话"一致）
- 草稿何时同步：失焦？还是输入停顿 500ms 去抖？

## 3. SDK API 必读（绝对真理）

### 3.1 引入

```ts
import { useConversationListStore } from 'tuikit-atomicx-vue3/chat'
import { ConversationMarkType } from 'tuikit-atomicx-vue3/chat'
import type { ConversationInfo } from 'tuikit-atomicx-vue3/chat'

const {
  markConversation,             // (idList: string[], markType, enable: boolean) => Promise
  clearConversationUnreadCount, // (id) => Promise
  setConversationDraft,         // (id, draft: string) => Promise
  clearConversationMessages,    // (id) => Promise
} = useConversationListStore()
```

### 3.2 状态判定（统一工具函数）

```ts
const isStarred = (c: ConversationInfo) => c.conversationMarkList.includes(ConversationMarkType.Star)
const isMarkedUnread = (c: ConversationInfo) => c.conversationMarkList.includes(ConversationMarkType.Unread)
```

### 3.3 操作语义对照表

| 场景 | 调用 |
|---|---|
| 收藏 | `markConversation([id], ConversationMarkType.Star, true)` |
| 取消收藏 | `markConversation([id], ConversationMarkType.Star, false)` |
| 标已读 | `clearConversationUnreadCount(id)` + 条件性 `markConversation([id], Unread, false)` |
| 标未读 | `markConversation([id], ConversationMarkType.Unread, true)` |
| 设草稿 | `setConversationDraft(id, text)` — 空串 `''` 清除草稿 |
| 清空消息 | `clearConversationMessages(id)` — 不删会话，仅清消息 |

### 3.4 未读数 vs 标未读

- `unreadCount: number` — 真实未读消息数，`clearConversationUnreadCount` 后归 0
- `ConversationMarkType.Unread` — 用户手动标的"未读旗"，与 `unreadCount` 互不相干

UI 渲染：`unreadCount > 0` → 数字徽标；`unreadCount === 0 && isMarkedUnread` → 纯色小红点。

## 4. Hard rules（AI 必须遵守）

> ❗ 所有 SDK 异步调用必须遵循 `references/06-a-defensive-coding.md` 防御编程规范（try/catch/finally、formatError、错误反馈形式、状态锁）。本节规则是该规范的专属补充，不替代它。

- ❗ `markConversation` 第一参必须是 `string[]`（即便单条也要数组）
  - ❌ `markConversation(id, ConversationMarkType.Star, true)` — 漏 `[]`
- ❗ "标已读"必须**两步**：`clearConversationUnreadCount` + 条件性 `markConversation([id], Unread, false)`
  - ❌ 只调 `clearConversationUnreadCount` — 手动标的红点擦不掉
  - ❌ 只调 `markConversation([id], Unread, false)` — `unreadCount` 数字还在
- ❗ "清空消息"是不可逆操作，UI 必须二次确认
  - ❌ 不弹确认框
- ❗ 清空消息 ≠ 删除会话，不准用 `deleteConversation` 替代
- ❗ 草稿同步不准对每个 keystroke 调用（频控风险），推荐失焦 / 500ms 去抖
  - ❌ `@input="setConversationDraft(id, $event.target.value)"`
- ❗ 状态判定用 § 3.2 工具函数（导入枚举），不准模板内硬编码魔法数字
  - ❌ `conv.conversationMarkList.includes(0)`
- ❗ 草稿在列表预览的 `[Draft]` 前缀由 starter `getLastMessagePreview` 处理，feature 层不重复实现
- ❗ 操作后不准手动 `conversationList.value = [...]` 强制刷新（store 响应式自动同步）
- ❗ 操作必须有视觉反馈（状态图标 / 菜单文案切换）

## 5. 反例库

> § 4 各条已内联主要反例。本节补充跨规则复合错误：

- ❌ 切换免打扰时顺手清了 `unreadCount`（免打扰只是 UI 降级，不改数据）—— 跨越 starter § 4.4 + 本 slice § 3.4
- ❌ feature 层重写 `getLastMessagePreview` 加 `[Draft]` 前缀 —— 与 starter 不一致

## 6. UI 自由度

> 样式由 AI 自由发挥，遵循项目已有 CSS 方案（见 `_base/detect-style.md`）。

✅ 完全自由：操作菜单触发方式 / 菜单图标选型 / 状态指示样式 / 草稿去抖时机 / 清空确认框样式
⚠️ 必须遵循项目现状：UI 库 / 现有 ContextMenu / Dialog 组件
⚠️ § 4 强约束不可放宽

## 7. 参考实现（明确哪些可改）

```vue
<script setup lang="ts">
import { useConversationListStore } from 'tuikit-atomicx-vue3/chat'
import { ConversationMarkType } from 'tuikit-atomicx-vue3/chat'
import type { ConversationInfo } from 'tuikit-atomicx-vue3/chat'

const {
  markConversation,
  clearConversationUnreadCount,
  setConversationDraft,
  clearConversationMessages,
} = useConversationListStore()

const isStarred = (c: ConversationInfo) => c.conversationMarkList.includes(ConversationMarkType.Star)
const isMarkedUnread = (c: ConversationInfo) => c.conversationMarkList.includes(ConversationMarkType.Unread)

async function handleStar(conv: ConversationInfo) {
  await markConversation([conv.conversationID], ConversationMarkType.Star, !isStarred(conv))
}

async function handleMarkRead(conv: ConversationInfo) {
  await clearConversationUnreadCount(conv.conversationID)
  if (isMarkedUnread(conv)) {
    await markConversation([conv.conversationID], ConversationMarkType.Unread, false)
  }
}

async function handleMarkUnread(conv: ConversationInfo) {
  await markConversation([conv.conversationID], ConversationMarkType.Unread, true)
}

async function handleClear(conv: ConversationInfo) {
  if (!confirm(`Clear all messages in "${conv.conversationID}"?`)) return  // TODO: 替换为 UI 库 Dialog 或自建最小 Dialog
  await clearConversationMessages(conv.conversationID)
}

// 草稿去抖（500ms）
let draftTimer: ReturnType<typeof setTimeout> | null = null
function syncDraft(conv: ConversationInfo, text: string) {
  if (draftTimer) clearTimeout(draftTimer)
  draftTimer = setTimeout(() => setConversationDraft(conv.conversationID, text), 500)
}
</script>
```

列表项视觉提示（推荐）：

```vue
<StarIcon v-if="isStarred(conv)" />
<span v-if="conv.unreadCount > 0" class="badge">{{ conv.unreadCount > 99 ? '99+' : conv.unreadCount }}</span>
<span v-else-if="isMarkedUnread(conv)" class="dot" />
```

### 可改

- 触发入口（右键 / 长按 / 侧滑 / 悬浮按钮）
- 确认框组件（项目 Dialog）
- 草稿去抖时机（500ms / 失焦）
- 图标库选型

### 不可改

- `markConversation` 第一参 `[]` 数组形态
- "标已读"两步操作
- 清空消息必须二次确认
- 状态判定用枚举工具函数，禁止模板硬编码
- 不手动刷新 `conversationList`
