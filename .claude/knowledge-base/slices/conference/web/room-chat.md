---
id: conference/room-chat
name: 会中聊天
product: conference
platform: web
tags: [chat, message, unread, mute, history]
platforms: [web]
related: [conference/login-auth, conference/room-lifecycle, conference/participant-management, conference/participant-list]
api_docs:
  - title: 会中聊天
    url: https://cloud.tencent.com/document/product/647/126933
---

# 会中聊天

## 功能说明

会中聊天负责把当前会议上下文映射到正确的 IM 群会话，并承接消息展示、发送、历史记录、未读提醒、富媒体消息以及消息权限联动。它解决的是“在当前房间里，消息如何正确收发与展示”，而不是房间创建、成员管理或会控规则本身。

从实现视角看，会中聊天通常由 5 段主链路组成：**会话绑定、消息列表 State、输入 State、历史消息加载、未读与权限联动**。如果业务需要高度自定义的聊天区，优先按这 5 段拆分能力，而不是把聊天理解成单一 UI 面板。

## 典型场景

| 场景 | 主要诉求 | 会中聊天的承接重点 |
|------|----------|--------------------|
| 在线研讨会 | 观众边看边提问 | 低门槛文本互动、未读提醒、禁言联动 |
| 远程协作 | 团队同步讨论与补充资料 | 文本、表情、图片、文件等消息流转 |
| 直播教学 / 培训 | 学员集中提问，老师统一查看 | 历史消息回看、消息列表稳定滚动、输入区禁言控制 |
| 强管控会议 | 房主或管理员可随时禁言 | 输入区状态、发送结果、成员状态三处保持一致 |

## 核心概念

### 集成路径

| 路径 | 适用场景 | 关键特点 |
|------|----------|----------|
| 底层 State 自定义集成 | 已有自定义 UI、抽屉聊天、复杂未读逻辑或高级消息能力 | 自行控制消息渲染、输入框、未读数、历史消息、富媒体消息与发送链路，是最完整的实现路径 |
| 标准聊天区快速封装 | 只需要标准消息区且已有现成组件容器 | 适合低定制场景，但本质上仍依赖同一套会话、消息和输入状态 |

### 能力拆分

| 能力段 | 关键职责 | 常见关键接口 / 状态 |
|--------|----------|---------------------|
| 会话绑定 | 把当前房间映射到正确群会话 | `roomId`、`setActiveConversation()`、`GROUP${roomId}` |
| 消息列表 | 承接当前会话消息流与历史分页 | `messageList`、`hasMoreOlderMessage`、`loadMoreOlderMessage()` |
| 输入与发送 | 维护待发送内容并执行消息发送 | `inputRawValue`、`updateRawValue()`、`sendMessage()` |
| 权限联动 | 同步全体禁言、单独禁言与真实可发消息状态 | `localParticipant.isMessageDisabled` |
| 扩展能力 | 处理图片、文件、已读回执、未读提醒等 | `sendMessage(InputContent[])`、`setEnableReadReceipt(true)`、未读计数 |

### 角色与职责

| 角色 | 关键职责 | 说明 |
|------|----------|------|
| 当前参会人 | 查看和发送消息 | 在当前房间上下文中收发文本、表情、图片、文件等消息 |
| 聊天模块 | 维护当前会话、消息流与输入态 | 承接消息列表、历史加载、未读角标和发送链路 |
| 会控模块 | 控制消息权限 | 全体禁言和单独禁言都会影响输入区和真实发送动作 |
| 成员列表模块 | 展示成员消息相关状态 | 聊天侧与成员侧应对同一成员的禁言状态给出一致表达 |
| 房间生命周期模块 | 提供 roomId 与进退房时机 | 只有进入真实房间后，聊天才能绑定到对应群会话 |

### 事件流

| 阶段 | 参与方 | 关键动作 |
|------|--------|----------|
| 登录并进房 | 客户端 | 拿到有效登录态和当前房间 `roomId` |
| 会话绑定 | 聊天模块 | 把当前活跃会话切到会议对应的群会话 |
| 消息初始化 | 消息列表 State | 读取当前会话消息、判断是否还有历史消息、按需开启已读回执 |
| 输入初始化 | 输入 State | 维护输入内容、监听禁言状态、准备发送链路 |
| 消息流转 | 参会人 | 发送、接收、分页加载历史消息、按类型渲染消息 |
| 提醒联动 | 聊天入口 / 抽屉状态 | 根据聊天窗口开关态维护未读计数与提示 |
| 退出清理 | 客户端 | 房间切换、退房或结束会议后收口旧会话上下文和未读状态 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| 房间会话标识 | 当前会议对应的唯一会话标识，通常由固定前缀和 `roomId` 组合而成 |
| 活跃会话 | 当前聊天面板实际绑定的会话 |
| 消息列表 | 当前会话已加载与正在展示的消息集合 |
| 历史消息状态 | 是否还有更早消息、是否正在分页加载 |
| 输入区原始内容 | 当前待发送的文本或组合输入内容 |
| 输入 API 绑定方式 | 原生输入框通常直接使用 `updateRawValue()`，不依赖富文本编辑器实例 |
| 未读数 | 用于聊天入口角标与消息提醒 |
| 房间级消息权限 | 表示当前会议是否处于全体禁言状态 |
| 当前成员消息权限 | 表示当前成员是否被单独禁言 |
| 输入区可用态 | 由房间级与成员级消息权限共同决定 |
| 高级消息能力 | 包括图片、文件、已读回执等扩展能力 |

### 状态机

```text
idle
  → binding-conversation
  → ready
  → sending / receiving
  → loading-history
  → ready
  → muted
  → ready
  → cleared
```

## 前置条件
**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`
- 若采用富文本编辑器集成，可按需接入 `@tiptap/vue-3`；若只使用原生 `<input>` / `<textarea>`，不需要依赖编辑器实例。

**前置状态**：
- 已阅读 `conference/room-chat`，明确当前能力的产品边界。
- 已完成 `conference/login-auth`，确保当前页面具备稳定登录态。
- 已根据业务流程接入会议上下文，并能从 `useRoomState()` 获取有效 `currentRoom.roomId`。

## 最佳实践

### ✅ ALWAYS

1. **把聊天上下文与当前房间一一绑定** —— 会议切换后，活跃会话也必须同步切换，避免串房间消息。
2. **在进房成功后尽快完成会话绑定** —— 让历史消息、未读数和新消息都围绕同一个房间上下文流转。
3. **把消息列表、输入态和发送链路拆开管理** —— 这样业务才能独立控制消息渲染、输入框和未读逻辑。
4. **让输入区状态和真实发送结果都受消息权限控制** —— 不仅输入框要禁用，发送链路也必须拦截禁言用户。
5. **原生输入框优先使用 `updateRawValue()`** —— 没有绑定编辑器实例时，不要把 `setContent()` 当成普通输入框更新手段。
6. **把历史消息加载和滚动位置当成聊天主链路的一部分** —— 否则自定义聊天面板很容易出现跳屏或重复拉取。
7. **把未读数设计成“聊天窗口开关态”的伴生状态** —— 抽屉关闭时累计，打开时清零，避免提醒漂移。
8. **为文本和富媒体消息预留统一渲染策略** —— 图片、文件、表情等消息不应混入纯文本分支里硬编码处理。
9. **让成员列表、聊天区和会控规则共享同一套禁言事实来源** —— 避免一个地方显示可发言、另一个地方显示已禁言。

### ❌ NEVER

1. **不要在会话未绑定前直接发送消息** —— 否则很容易把消息发到错误会话或丢失当前房间上下文。
2. **不要把房间聊天绑定成裸 `roomId` 或业务私聊会话** —— 会导致消息进错会话。
3. **不要只改输入框样式而不阻止真实发送** —— 禁言必须落到真实发送路径。
4. **不要在原生输入场景下依赖富文本编辑器 API** —— 没有 editor 实例时，这些 API 往往不会按预期生效。
5. **不要忽略房间切换时的会话、未读和消息流清理** —— 否则会出现消息串场和角标错误。
6. **不要把历史消息加载后的滚动跳动当成纯 UI 小问题** —— 这会直接影响会中阅读体验。
7. **不要默认所有聊天场景都只发纯文本** —— 远程协作和教学类场景往往需要图片、文件等富媒体能力。

## 接入方式
当前文档仅覆盖**无 UI 集成**：聊天列表、输入区、抽屉 / 侧栏样式均由业务自己实现，`tuikit-atomicx-vue3` 负责提供房间聊天相关 Hook、State 与发送能力。以下内容以 `会中聊天（Web）.md` 中 **“方案二：使用底层 API 自定义集成”** 为主。

> **注意**：
> `MessageInputState` 默认支持与 `@tiptap/vue-3` 编辑器集成。如果您仅需要简单的文本输入框（例如 `<input>` 或 `<textarea>`），请忽略 `setEditorInstance()`、`setContent()` 等与编辑器实例绑定的 API，直接使用 `updateRawValue()` 和 `sendMessage()` 即可。

## 代码示例
### 步骤一：数据初始化

在用户加入房间成功后，需要调用 `setActiveConversation()` 初始化聊天数据。建议监听 `currentRoom` 的变化来自动处理。

```ts
import { onUnmounted, watch } from 'vue';
import { useConversationListState } from 'tuikit-atomicx-vue3/chat';
import { useRoomState } from 'tuikit-atomicx-vue3/room';

const { currentRoom } = useRoomState();
const { setActiveConversation } = useConversationListState();

watch(() => currentRoom.value?.roomId, (roomId) => {
  if (!roomId) {
    setActiveConversation('');
    return;
  }

  setActiveConversation(`GROUP${roomId}`);
}, { immediate: true });

onUnmounted(() => {
  setActiveConversation('');
});
```

> **说明**：
> - `GROUP` 为固定前缀，`setActiveConversation()` 参数必须为 `GROUP${roomId}`，否则无法正常收发消息。
> - 在房间切换、退房或聊天按钮组件卸载时，应同步 `setActiveConversation('')` 清空旧会话，避免消息错发至错误会话。

### 步骤二：获取消息列表

使用 `useMessageListState()` 获取当前会话的消息列表，`messageList` 是响应式数据，会自动更新新收到的消息。

```ts
import { useMessageListState } from 'tuikit-atomicx-vue3/chat';

const {
  messageList,
  loadMoreOlderMessage,
  hasMoreOlderMessage,
} = useMessageListState();

console.log(messageList.value);
console.log(hasMoreOlderMessage.value);
```

### 步骤三：发送消息

使用 `useMessageInputState()` 管理输入框内容并发送消息。

```ts
import { computed } from 'vue';
import { useMessageInputState } from 'tuikit-atomicx-vue3/chat';
import { useRoomParticipantState } from 'tuikit-atomicx-vue3/room';

const {
  inputRawValue,
  updateRawValue,
  sendMessage,
} = useMessageInputState();

const { localParticipant } = useRoomParticipantState();
const isMessageDisabled = computed(() => Boolean(localParticipant.value?.isMessageDisabled));
const hasTextInput = computed(() => (
  typeof inputRawValue.value === 'string'
    ? inputRawValue.value.trim().length > 0
    : inputRawValue.value.length > 0
));

const handleSend = async () => {
  if (isMessageDisabled.value) return;
  if (!hasTextInput.value) return;

  try {
    await sendMessage();
    updateRawValue('');
  } catch (error) {
    console.error('发送失败', error);
  }
};

// 原生输入框示例
// <input
//   :value="inputRawValue"
//   @input="(e) => updateRawValue((e.target as HTMLInputElement).value)"
//   @keyup.enter="handleSend"
// />
```

> **说明**：
> - 非富文本模式下，发送成功后请使用 `updateRawValue('')` 清空输入框。
> - 若当前成员已被禁言，除了输入框应禁用外，发送链路也需要一起拦截。
> - 若需要直接发送富媒体消息，可通过 `sendMessage(InputContent[])` 传入图片、文件等内容。

### 步骤四：加载历史消息

通过 `loadMoreOlderMessage()` 分页拉取历史消息，通常在滚动到列表顶部时触发。

```ts
import { nextTick } from 'vue';
import { useMessageListState } from 'tuikit-atomicx-vue3/chat';

const {
  hasMoreOlderMessage,
  loadMoreOlderMessage,
} = useMessageListState();

const loadHistory = async (scrollContainer: HTMLElement) => {
  if (!hasMoreOlderMessage.value) return;

  const previousHeight = scrollContainer.scrollHeight;
  await loadMoreOlderMessage();

  await nextTick();
  const currentHeight = scrollContainer.scrollHeight;
  scrollContainer.scrollTop += currentHeight - previousHeight;
};
```

> **注意**：
> 加载历史消息后，通常需要手动调整滚动条位置，以保持当前浏览视角不发生跳变。

### 步骤五：高级功能（已读回执）

如果业务需要已读回执功能，可以通过 `setEnableReadReceipt()` 开启。

```ts
import { useMessageListState } from 'tuikit-atomicx-vue3/chat';

const {
  setEnableReadReceipt,
} = useMessageListState();

setEnableReadReceipt(true);
```

## 调用时序
```
完成 login-auth
   │
   ▼
进入 room-lifecycle，拿到 currentRoom.roomId
   │
   ▼
调用 setActiveConversation(`GROUP${roomId}`)
   │
   ├─ 成功 → 获取 messageList / inputRawValue 等状态并渲染业务自定义聊天 UI
   ├─ 房间切换 → 重新绑定新的 GROUP 会话
   └─ 失败 → 提示会话初始化异常并阻止发言入口
   │
   ▼
结合 localParticipant.isMessageDisabled 控制输入区与发送链路
   │
   ▼
处理发送、历史消息、可选已读回执与富媒体消息
   │
   ▼
退房或结束会议后收口聊天入口、旧会话上下文与本地状态
```

## 平台特有注意事项
### 1. 会议聊天依赖 `GROUP${roomId}` 规则
会中聊天基于 IM 群组会话，`setActiveConversation()` 必须使用 `GROUP${roomId}`，不能只传裸 `roomId`。

### 2. 使用原生输入框时优先走 `updateRawValue()`
若没有接入富文本编辑器，请直接使用 `updateRawValue()` 和 `sendMessage()`；不要依赖 `setContent()`、`setEditorInstance()` 这类编辑器绑定 API 来维护普通输入框内容。

### 3. 输入区应直接绑定会控禁言状态
若 `localParticipant.isMessageDisabled` 已经生效，聊天输入框必须立即转为禁用或只读；自定义输入框同样需要在发送前再次拦截。

### 4. 自定义消息列表容器必须具备稳定高度
聊天区通常需要独立滚动容器；如果父容器没有固定高度并且缺少 `overflow: hidden` 或等价约束，消息区容易无限拉长、无法滚动。

### 5. 历史消息加载后要恢复滚动位置
自定义聊天面板调用 `loadMoreOlderMessage()` 后，通常需要在 DOM 更新后修正 `scrollTop`，避免阅读位置跳变。

### 6. 抽屉式聊天需要维护未读累积与清零
如果聊天面板平时折叠或关闭，应在关闭时累计未读、打开时清零；首次初始化消息列表时不要误计入未读。

### 7. 富媒体消息和已读回执属于可选高级能力
图片、文件等消息可通过 `sendMessage(InputContent[])` 发送；如有消息确认诉求，可结合 `setEnableReadReceipt(true)` 开启已读回执。

### 8. 自定义渲染时要覆盖不同消息类型分支
`messageList` 中通常会出现文本、图片、文件等不同类型消息；自定义聊天 UI 需要按消息类型分别渲染，不要只按纯文本分支处理。

## 常见错误与场景对照

| 错误 / 场景 | 常见触发时机 | 建议处理方式 |
|-------------|--------------|--------------|
| 会话绑定成裸 `roomId` | 只拿到房间号就直接调用 `setActiveConversation(roomId)` | 改为固定用 `setActiveConversation()` 绑定 `GROUP${roomId}` |
| 进房前就切会话 | 登录或进房尚未完成时初始化聊天 | 等 `currentRoom.roomId` 有值后再绑定会话 |
| 原生输入框改了值但发送仍为空 | 直接操作输入框值，没有调用 `updateRawValue()` | 使用 `updateRawValue()` 维护输入内容，再调用 `sendMessage()` |
| 输入框禁用了但代码仍能发送 | 只做 UI 禁用，没有拦截发送函数 | 发送前再次校验禁言状态，保持 UI 与真实行为一致 |
| 自定义聊天区没有稳定高度 | 侧栏 / 抽屉只渲染了内容，没有约束滚动区域 | 为消息列表父容器提供固定高度、滚动区或等价布局约束 |
| 聊天抽屉首次打开就显示未读 | 初次拉取历史消息被误算成新消息 | 仅在窗口关闭且新消息长度增长时累计未读 |
| 历史消息加载后界面跳动 | 上滑加载更早消息时滚动位置漂移 | 记录加载前高度，加载后按高度差恢复滚动位置 |
| 富媒体消息显示异常 | 自定义 UI 只按文本消息渲染 | 按消息类型拆分渲染逻辑，覆盖文本、图片、文件等分支 |

## 代码生成约束
### 编译必要条件
- **通用条件**：见 [login-auth 平台 slice](login-auth.md)。
- **额外导入**：至少需要从 `tuikit-atomicx-vue3/chat` 导入 `useConversationListState`；自定义聊天通常还需要 `useMessageListState` 与 `useMessageInputState`；若输入区需要联动禁言态，通常还需要 `useRoomParticipantState`。
- **运行前提**：当前用户已完成登录，且已拿到有效 `roomId`。
- **容器前提**：业务自定义消息列表时，应提供稳定高度与独立滚动区域。

### 生成规则
#### MUST（生成时必须包含）

1. **用 `currentRoom.roomId` 驱动当前聊天会话** — 这样会议切换时会话才能同步收口。  
   **Verify**: 检查是否从 `useRoomState()` 读取 `currentRoom`。
2. **通过 `setActiveConversation()` 绑定 `GROUP${roomId}` 群会话** — 这是会中聊天的关键映射关系。  
   **Verify**: 搜索是否存在 `GROUP${roomId}` 或等价拼接逻辑。
3. **用 `useMessageListState()` 驱动消息列表和历史消息加载** — 保持当前会话数据源一致。  
   **Verify**: 检查是否读取 `messageList`，并按需使用 `loadMoreOlderMessage()`。
4. **自定义原生输入框时使用 `updateRawValue()` 与 `sendMessage()`** — 保持状态同步和发送行为一致。  
   **Verify**: 检查是否通过 `updateRawValue()` 维护输入内容，并在发送后清空。
5. **把禁言状态同时接到输入区和真实发送链路** — 不能只做视觉禁用。  
   **Verify**: 检查输入区是否联动 `isMessageDisabled`，且发送前有同源校验。
6. **为自定义消息列表提供稳定滚动容器** — 否则聊天区很容易出现拉伸和滚动异常。  
   **Verify**: 检查聊天区父容器是否具备固定高度、滚动区或等价布局约束。

#### MUST NOT（生成时绝不能出现）

1. **不要把房间聊天直接绑定为裸 `roomId` 或私聊会话** — 会导致消息进错会话。  
   **Verify**: 检查会话 ID 是否符合 `GROUP${roomId}` 规则。
2. **不要忽略禁言状态继续开放输入框或发送动作** — UI 与真实可发言状态会不一致。  
   **Verify**: 检查输入区和发送函数是否都联动禁言状态。
3. **不要在没有高度约束的容器里渲染自定义消息列表** — 很容易导致列表无法正常滚动。  
   **Verify**: 检查父容器是否具备固定高度或 `height: 100%` 等稳定布局。
4. **不要把首次历史消息加载误算成未读消息** — 会让角标在初始化后立刻脏掉。  
   **Verify**: 检查未读逻辑是否区分初始化加载与真实新消息。
5. **不要在原生输入场景下依赖富文本编辑器 API 清空内容** — 没绑定编辑器时不会按预期生效。  
   **Verify**: 检查普通输入框场景是否使用 `updateRawValue('')` 而不是 `setContent('')`。

### 集成检查点
- 当前 slice 强依赖 `conference/room-lifecycle` 与 `conference/login-auth`。
- 聊天接入通常是新增侧栏、抽屉或右侧协作区，不需要修改 SDK 内部 IM 实现。
- 如果业务已经有独立 IM 会话体系，需要明确会议群会话与业务私聊的切换边界。
- 如果产品需要图片、文件、已读回执等高级能力，优先在自定义聊天方案里统一规划消息类型和渲染分支。

## 验证矩阵
| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已导入房间与聊天相关 Hook | 检查 `import` 语句 | Room / Chat Hook 可解析 |
| 2. 静态规则级 | 会话 ID 符合 `GROUP${roomId}` 规则 | 搜索 `setActiveConversation` 调用 | 存在群会话绑定逻辑 |
| 3. 数据流级 | 已读取消息列表、输入内容与禁言状态 | 检查 `useMessageListState`、`useMessageInputState`、`useRoomParticipantState` 调用 | 聊天数据源与权限源清晰 |
| 4. 结构级 | 自定义聊天列表具备稳定高度容器与滚动区域 | 检查模板结构与样式容器 | 消息列表具备稳定滚动空间 |
| 5. 运行时级 | 进入会议后聊天面板可展示正确会话 | 进房并打开聊天面板 | 消息收发落在当前会议会话 |
| 6. 业务行为级 | 禁言、历史消息、富媒体渲染表现正确 | 切换禁言、上滑加载历史、发送图片文件 | 输入区、滚动位置和不同消息类型表现符合预期 |

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 聊天面板没有消息 | 已在会议中，但列表为空或不刷新 | 检查是否已切到当前房间对应的群会话，以及是否在登录和进房完成后再绑定 |
| 消息发错会话 | 在 A 房间发送的消息出现在 B 房间 | 检查房间切换时是否重新绑定并清理旧会话上下文 |
| 原生输入框有值但发送为空 | 输入框显示正常，发送后内容丢失或为空 | 检查是否通过 `updateRawValue()` 维护输入内容，而不是只改本地变量 |
| 已禁言但仍能尝试发送 | 输入框变灰了，但代码路径仍可触发发送 | 检查输入区禁用和真实发送拦截是否共用同一套权限判断 |
| 加载历史消息后页面跳动 | 回看历史时滚动位置丢失 | 加载前记录高度，加载后恢复滚动位置 |
| 未读数不准确 | 聊天抽屉打开后仍显示旧未读 | 检查聊天窗口开关态与未读清零逻辑是否绑定 |
| 富媒体消息显示异常 | 图片、文件消息展示为空白或格式错乱 | 检查消息类型分支是否覆盖文本、图片、文件等不同 `payload` |

### 排障流程

```text
发现 会中聊天 相关问题
├── 第 1 步：确认当前问题属于房间聊天上下文，而不是房间生命周期或会控规则本身
├── 第 2 步：检查当前活跃会话是否已与当前 roomId 正确绑定
├── 第 3 步：确认消息列表 State、输入 State 与禁言状态是否来自同一房间上下文
├── 第 4 步：检查历史消息、未读数、富媒体分支和滚动策略是否符合当前聊天入口形态
└── 第 5 步：若仍异常，再回查 login-auth / room-lifecycle / participant-management / participant-list 的衔接
```

## 关联知识

- **[conference/login-auth](login-auth.md)** —— 未登录或登录态异常时，聊天会话无法正确建立。
- **[conference/room-lifecycle](room-lifecycle.md)** —— 只有真正进入房间后，聊天上下文才具备正确的会中绑定基础。
- **[conference/participant-management](participant-management.md)** —— 全体禁言、单独禁言等消息权限由这里驱动。
- **[conference/participant-list](participant-list.md)** —— 成员身份、昵称和禁言状态会同步影响聊天侧展示。
