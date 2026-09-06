---
id: chat/at-mention
name: 群聊 @ 提及
product: chat
platform: web
description: 群聊 @提及成员（成员选择器 + atUserList option + tag 展示）
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: [MessageInputStore, GroupMemberStore]
trigger-keywords: [at, @, 提及, mention, @群成员, @所有人, atUserList, 群成员选择]
prerequisites: [login-auth, message-list, message-input]
tags: ['MessageInputStore', 'GroupMemberStore']
---

## 1. 这个 slice 处理什么

在群聊场景的 MessageInput 中，监听用户输入 `@` 字符唤起成员选择器，选中后将 `@name` 插入输入框，发送时将 userID 列表传入 `sendMessage(payload, { atUserList })`。

> 仅群聊有效（`conversationID.startsWith('GROUP')`），C2C 会话不启用 @ 功能。

## 2. AI 思考清单

- 如何判断当前是群聊？（`conversationID` 前缀判定）
- 成员选择器定位方式？（输入框上方 Popover / 绝对定位到光标附近）

## 3. SDK API 必读

### 3.1 发送侧（sendMessage option）

```ts
import { useMessageInputStore } from 'tuikit-atomicx-vue3/chat'

const { sendMessage } = useMessageInputStore(props.conversationID)

// 发送带 @ 的文本消息
await sendMessage(
  { type: 'textMessage', text: '大家注意一下 @张三 @李四' },
  { atUserList: ['zhangsan_001', 'lisi_002'] }
)
```

`SendMessageInputOption.atUserList`：
- 类型：`string[]`
- 含义：被 @ 的 userID 列表
- 群聊 @ 列表；C2C 会话传入时被 SDK 忽略

### 3.2 成员列表（useGroupMemberStore）

```ts
import { useGroupMemberStore, GroupAtType } from 'tuikit-atomicx-vue3/chat'
import type { GroupMember } from 'tuikit-atomicx-vue3/chat'

// groupID = conversationID.slice(5)（去掉 'GROUP' 前缀）
const {
  memberList,      // ComputedRef<GroupMember[]>
  hasMoreMembers,  // ComputedRef<boolean>
  loadMembers,     // (roleList?) => Promise
  loadMoreMembers, // () => Promise
} = useGroupMemberStore(groupID)
```

`GroupMember` 关键字段：

| 字段 | 类型 | 用途 |
|---|---|---|
| `userID` | `string` | 唯一标识，传入 `atUserList` |
| `nickname` | `string \| undefined` | 昵称 |
| `nameCard` | `string \| undefined` | 群名片（优先于 nickname 展示） |
| `avatarURL` | `string \| undefined` | 头像 |
| `role` | `string \| undefined` | 角色（Owner / Admin / Member） |

### 3.3 展示名兜底链

```ts
function memberDisplayName(m: GroupMember): string {
  return m.nameCard || m.nickname || m.userID
}
```

## 4. Hard rules

### 4.1 群聊判定 + 触发方式

- ❗ 通过 `props.conversationID.startsWith('GROUP')` 判定是否群聊
- ❗ 非群聊时 @ 功能完全不启用（不监听 `@` 输入、不渲染选择器）
- ❗ `groupID` 通过 `conversationID.slice(5)` 取得（去掉 `GROUP` 前缀）
  - ❌ `conversationID.replace('GROUP', '')` — 如果 ID 内含 GROUP 字样会误删
- ❗ 触发方式：用户在输入框中键入 `@` 字符时自动唤起成员选择器
  - 输入框中 `@` 后继续输入的文字不参与成员过滤（搜索仅在选择器内搜索框进行）
  - ❌ 用 toolbar 按钮触发（不需要额外按钮）
- ❗ 关闭时机（仅以下 3 种）：
  - 确认选择：用户点击"确定"按钮
  - 按 Esc：键盘快捷关闭
  - 输入框内容完全清空：如全选删除，`text.value.length === 0` 时自动关闭
    - ❗ 实现方式：用 `watch(text, ...)` 统一拦截，不准只在单个事件处理函数里判断（否则无法覆盖全选删除、Ctrl+A+Delete、剪切等所有清空路径）
- ❗ 已移除的关闭方式（不准实现）：
  - ❌ 点击外部关闭 — 输入框聚焦会误触发关闭，体验不好
  - ❌ 删除单个 `@` 触发字符时关闭 — 用户诉求是只有输入框完全清空才关闭，删除单个 `@` 不应关闭

### 4.2 成员加载

- ❗ `useGroupMemberStore(groupID)` 必须传 groupID
  - ❌ 不传参（运行时报错）
- ❗ 组件 mount 时调 `loadMembers()` 预加载（`try/catch`）
- ❗ 渲染直接用 `memberList` ComputedRef，不赋给本地 ref
  - ❌ `const list = ref(memberList.value)`
- ❗ 成员列表必须过滤掉当前登录用户自己（`useLoginStore().loginUserInfo.value?.userID`）
  - ❌ 自己出现在选择器列表里，@ 自己无意义
  - ✅ `const filteredMembers = computed(() => memberList.value.filter(m => m.userID !== loginUserInfo.value?.userID))`
- ❗ 列表较长时支持 `loadMoreMembers()`（`hasMoreMembers` 控制）
- ❗ 不准 `chat.getGroupMemberList(...)` 绕过 store
  - ❌ 直接调 SDK 底层 API

### 4.3 发送集成

- ❗ `atUserList` 传入 `sendMessage` 的第二参 option 中
  ```ts
  await sendMessage({ type: 'textMessage', text }, { atUserList: selectedUserIDs })
  ```
- ❗ `atUserList` 为空数组时不传 option（或传 `undefined`），不传空数组
  - ❌ `{ atUserList: [] }` — 无意义开销
- ❗ 发送成功后清空已选成员列表
- ❗ `atUserList` 中的值是 `userID` 字符串，不是 nickname / nameCard
  - ❌ `atUserList: ['张三', '李四']` — 传了显示名

### 4.4 成员选择器 UI

- ❗ 支持多选：用户可勾选多个成员，点击"确定"后一次性把所有 `@name ` 插入光标位置并关闭选择器
  - ❌ 单选即关闭（每次只能 @ 一人，多人需反复操作）

- ❗ **选择器整体布局（从上到下）**：

  ```
  ┌─────────────────────────────────┐
  │ 选择成员           取消  确定    │  ← 顶部操作栏
  ├─────────────────────────────────┤
  │ 🔍 搜索成员                     │  ← 搜索输入框
  ├─────────────────────────────────┤
  │ ☑ 👥 @所有人                    │  ← 固定项
  ├─────────────────────────────────┤
  │ ☐ 🧑 张三                       │  ← 成员列表（可滚动）
  │ ☐ 🧑 李四                       │
  │ ...                             │
  └─────────────────────────────────┘
  ```

- ❗ **顶部操作栏**：左侧标题"选择成员" + 右侧"取消"和"确定"两个按钮
  - "取消"：关闭面板，不插入任何内容
  - "确定"：插入已选成员并关闭
  - 按钮文案固定为"取消"和"确定"，不准用其他文案
  - ❌ 只有"确定"没有"取消"
  - ❌ 按钮放在底部 / 列表内部
  - ❌ 文案用"确认"/"完成"/"OK"等替代

- ❗ **搜索输入框**：位于顶部操作栏下方，列表上方
  - placeholder 文案"搜索成员..."
  - 输入时实时过滤下方成员列表（匹配 `nameCard` / `nickname` / `userID`，不区分大小写）
  - 过滤结果为空时显示"无匹配成员"提示
  - ❌ 不放搜索框（只靠输入框 `@` 后的文字过滤 — 体验不够明显）
  - ❌ 搜索框放在底部或列表内部

- ❗ **@所有人固定项**：位于搜索框下方、成员列表上方，不随搜索过滤消失
  - 选中后 `atUserList` 传 `['__kImSDK_MesssageAtALL__']`
  - 插入输入框的文案为 `@所有人 `
  - 所有群成员均可使用
  - ❌ @所有人被搜索过滤掉

- ❗ **成员列表区域**：可滚动，每项展示头像（兜底字母头像）+ 展示名（nameCard > nickname > userID），不显示成员角色

- ❗ 选择器宽度限制：`max-width: 360px`，不准撑满输入框宽度
  - ❌ 选择器宽度等于输入框宽度（视觉过宽，尤其桌面端）

### 4.5 @ 文案落入输入框

- ❗ 确认选择时，先**删除触发的 `@` 字符及其后的搜索文字**（从 `atTriggerPos` 到当前光标位置），再插入 `@展示名 `
  - 即：`text = text[0..atTriggerPos] + '@name ' + text[cursorPos..]`
  - ❌ 不删除触发字符直接插入，导致出现 `@@name`（双 @ bug）
- ❗ 选中成员后，`@展示名 ` 直接插入到输入框文本的**触发位置**（末尾带一个空格分隔）
  - ❌ 在输入框外部用独立 tag/chip 展示已选成员
  - ❌ 发送时才拼接 @ 文案（用户看不到最终发出的文本）
- ❗ 插入后光标移到 `@name ` 之后，用户可继续输入正文
- ❗ 展示名用 memberDisplayName 兜底链取值
- ❗ 内部维护 `atUsers: Array<{ userID, name }>` 用于发送时提取 atUserList
  - ❌ 不需要存 `startIndex` / `endIndex`（不依赖预存位置索引）

### 4.6 原子删除（基于文本内容动态查找）

- ❗ 每次 Backspace 时，通过 `text.value.indexOf(token)` 实时定位 `@name ` 在文本中的位置，判断光标是否在该 token 范围内
  ```ts
  const hitIndex = atUsers.value.findIndex(u => {
    const token = `@${u.name} `
    const idx = text.value.indexOf(token)
    if (idx === -1) return false
    return pos > idx && pos <= idx + token.length
  })
  ```
- ❗ 光标在 `@name ` 范围内任意位置（含紧贴末尾空格后）按 Backspace → 一次性删除整个 token，同时从 atUsers 数组中移除该条目
- ❗ 删除后光标回到 token 起始位置（`idx`）
- ❗ 删除后若输入框为空（`text.value.length === 0`），触发关闭（同 § 4.1 关闭时机第 3 条）
- ❗ `name` 字段是查找 token 的唯一 key（通过 `` `@${name} ` `` 匹配文本）
  - ❌ 依赖预存的 startIndex/endIndex 判定（文本编辑后索引会漂移，不可靠）
  - ❌ 逐字符删除，留下残缺的 `@张` 或 `@`
  - ❌ 需要先选中再删除（应单次 Backspace 即可）

### 4.7 会话列表 @ 标识

- ❗ 命中本 slice 后，ConversationList 的列表项必须同步增加 @ 标识渲染
- ❗ 数据来源：`ConversationInfo.groupAtInfoList`（`GroupAtInfo[]`）
- ❗ 标识位置：消息预览文案**最前方**，红色高亮
- ❗ 清除时机：用户进入该会话 → `clearConversationUnreadCount(conversationID)` → SDK 自动清除 `groupAtInfoList`，无需前端手动处理
- ❗ `atType` 必须用 `GroupAtType` 枚举，禁止硬编码数字
  - ❌ `item.atType === 1`
- ❗ `groupAtInfoList` 为空时不渲染任何占位元素
  - ❌ 空数组时仍渲染空 `<span>`

**累积规则**（多条 `GroupAtInfo` 合并）：

```ts
import { GroupAtType } from 'tuikit-atomicx-vue3/chat'
import type { ConversationInfo } from 'tuikit-atomicx-vue3/chat'

function getAtLabel(c: ConversationInfo): string {
  if (!c.groupAtInfoList || c.groupAtInfoList.length === 0) return ''
  let text = ''
  c.groupAtInfoList.forEach((item) => {
    if (item.atType === GroupAtType.AtMe) {
      text = text.indexOf('[@所有人]') !== -1 ? '[有人@我][@所有人]' : '[有人@我]'
    }
    if (item.atType === GroupAtType.AtAll) {
      text = text.indexOf('[有人@我]') !== -1 ? '[有人@我][@所有人]' : '[@所有人]'
    }
    if (item.atType === GroupAtType.AtAllAtMe) {
      text = '[有人@我][@所有人]'
    }
  })
  return text
}
```

模板中使用：

```vue
<span v-if="getAtLabel(conv)" class="at-label">{{ getAtLabel(conv) }}</span>
<span class="conv-preview">{{ getLastMessagePreview(conv) }}</span>
```

## 5. 反例库

> § 4 已内联主要反例。本节补充跨规则复合错误：

- ❌ 在 C2C 场景渲染 @ 按钮 + 打开空成员列表 — 判定缺失
- ❌ `useGroupMemberStore` 写在 MessageInput 外部（ChatPage），通过 props 传 memberList — 违反封装
- ❌ 选中成员后在输入框外部用 tag/chip 展示，发送时才拼接 — 用户看不到最终文本
- ❌ Backspace 时逐字符删除 `@name`，留下残缺的 `@张` — 应原子删除

## 6. UI 自由度

> 样式由 AI 自由发挥，遵循项目已有 CSS 方案（见 `_base/detect-style.md`）。

✅ 完全自由：选择器容器形态（Popover / floating panel）/ 成员列表排序 / 勾选样式 / 头像形状 / 搜索框样式
⚠️ 必须遵循项目现状：UI 库组件 / CSS 方案
⚠️ § 4.4 布局结构 + § 4.5/4.6 交互行为不可放宽

## 7. 参考实现

```vue
<script setup lang="ts">
import { ref, computed, onMounted, useTemplateRef } from 'vue'
import { useMessageInputStore, useGroupMemberStore } from 'tuikit-atomicx-vue3/chat'
import type { GroupMember } from 'tuikit-atomicx-vue3/chat'

const props = defineProps<{ conversationID: string }>()
const { sendMessage } = useMessageInputStore(props.conversationID)

const isGroup = computed(() => props.conversationID.startsWith('GROUP'))
const groupID = computed(() => isGroup.value ? props.conversationID.slice(5) : '')

const memberStore = isGroup.value ? useGroupMemberStore(groupID.value) : null

onMounted(() => {
  if (memberStore) {
    memberStore.loadMembers().catch(() => {})
  }
})

// ── @ 状态 ──
interface AtUser { userID: string; name: string }
const atUsers = ref<AtUser[]>([])
const pickerOpen = ref(false)
const text = ref('')
const textareaEl = useTemplateRef<HTMLTextAreaElement>('textareaEl')

function memberDisplayName(m: GroupMember): string {
  return m.nameCard || m.nickname || m.userID
}

// 选中成员后插入输入框（替换触发的 @ + 搜索文字）
function handleConfirm(selected: GroupMember[]) {
  const el = textareaEl.value
  const cursorPos = el?.selectionStart ?? text.value.length

  const insertions = selected.map(m => `@${memberDisplayName(m)} `)
  const insertText = insertions.join('')

  // 删除触发的 @ 及搜索文字，再插入 @name
  const start = atTriggerPos.value >= 0 ? atTriggerPos.value : cursorPos
  text.value = text.value.slice(0, start) + insertText + text.value.slice(cursorPos)

  // 记录成员（仅 userID + name，不存位置索引）
  for (const m of selected) {
    atUsers.value.push({ userID: m.userID, name: memberDisplayName(m) })
  }

  pickerOpen.value = false
  atTriggerPos.value = -1

  // 光标移到插入内容之后
  const newPos = start + insertText.length
  requestAnimationFrame(() => {
    el?.setSelectionRange(newPos, newPos)
    el?.focus()
  })
}

// 监听输入 @ 字符唤起选择器
const atTriggerPos = ref(-1)

function handleInput(e: Event) {
  if (!isGroup.value) return
  const el = textareaEl.value
  const pos = el?.selectionStart ?? 0
  const inputEvent = e as InputEvent
  if (inputEvent.data === '@') {
    pickerOpen.value = true
    atTriggerPos.value = pos - 1 // @ 字符的位置
  }
}

// Backspace 原子删除：基于文本内容动态查找
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Backspace') {
    const el = textareaEl.value
    const pos = el?.selectionStart ?? 0
    const hitIndex = atUsers.value.findIndex(u => {
      const token = `@${u.name} `
      const idx = text.value.indexOf(token)
      if (idx === -1) return false
      return pos > idx && pos <= idx + token.length
    })
    if (hitIndex !== -1) {
      e.preventDefault()
      const hit = atUsers.value[hitIndex]
      const token = `@${hit.name} `
      const idx = text.value.indexOf(token)
      text.value = text.value.slice(0, idx) + text.value.slice(idx + token.length)
      atUsers.value.splice(hitIndex, 1)
      // 光标回到 token 起始位置
      requestAnimationFrame(() => el?.setSelectionRange(idx, idx))
      // 删除后若输入框为空，关闭成员面板
      if (text.value.length === 0) {
        pickerOpen.value = false
      }
    }
  }
}

// 发送
async function handleSend() {
  const trimmed = text.value.trim()
  if (!trimmed) return
  const atUserList = atUsers.value.map(u => u.userID)
  const option = atUserList.length > 0 ? { atUserList } : undefined
  await sendMessage({ type: 'textMessage', text: trimmed }, option)
  text.value = ''
  atUsers.value = []
}
</script>

<template>
  <textarea
    ref="textareaEl"
    v-model="text"
    @keydown="handleKeydown"
    @input="handleInput"
  />

  <!-- 成员选择器（Popover / Dropdown，定位到 @ 光标位置） -->
  <!-- 显示条件：pickerOpen && isGroup -->
  <!-- 列表数据：memberStore.memberList（按 searchQuery 过滤） -->
  <!-- 确认回调：handleConfirm -->
</template>
```

> ⚠️ 实际实现时，@ 逻辑与 MessageInput 组件合并（共享 `sending` / `text` / `sendMessage`）。上述代码仅展示核心逻辑骨架。

### 可改

- 选择器容器形态（Popover / floating panel / 绝对定位面板）
- 成员列表排序方式
- 勾选框 / 头像 / 列表项样式
- 搜索框 UI 细节（图标位置、清除按钮）

### 不可改

- `useGroupMemberStore(groupID)` 取成员列表（不绕过 store）
- `atUserList` 传 userID 数组到 `sendMessage` option
- 群聊判定用 `conversationID.startsWith('GROUP')`
- groupID 用 `conversationID.slice(5)`
- 非群聊不启用 @ 功能
- 触发方式：输入 `@` 字符唤起选择器（不用 toolbar 按钮）
- 选择器布局：顶部操作栏 → 搜索框 → @所有人固定项 → 成员列表
- 搜索框必须存在于选择器内部，实时过滤成员列表
- @所有人固定置顶，所有群成员可用
- 选中后 `@name ` 直接插入输入框光标位置（不用外部 tag）
- Backspace 原子删除整个 `@name`（基于 indexOf 动态查找）
- 关闭时机仅 3 种（确定 / Esc / 输入框清空）
- 发送成功后清空 atUsers
