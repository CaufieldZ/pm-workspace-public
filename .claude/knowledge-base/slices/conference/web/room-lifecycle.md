---
id: conference/room-lifecycle
name: 房间创建、加入、离开与结束
product: conference
platform: web
tags: [room, lifecycle, create, join, leave, end]
platforms: [web]
related: [conference/login-auth, conference/participant-list, conference/room-schedule, conference/room-call]
api_docs:
  - title: 房间管理
    url: https://cloud.tencent.com/document/product/647/126919
business_decisions:
  - key: roomid_origin
    tier: blocking
    question: "会议的房间号从哪儿来？建议 onboarding 分两步渐进引导：先问“会议怎么发起”（自己开新会 / 由后台统一管理 / 只能受邀入会），选“后台统一管理”后再追问一句“房间号是后台早建好的，还是进会时现向后台要一个”，据此落到下面四个 value 之一。"
    options:
      - { label: "用户自己开新会 —— 谁发起谁建房，系统当场生成房间号", value: "frontend" }
      - { label: "后台早就建好了 —— 前端拿现成的房间号直接进", value: "backend-precreated" }
      - { label: "后台临时分配 —— 进会时向后台要一个房间号再进", value: "backend-allocated" }
      - { label: "只进别人的会，自己从不建房 —— 比如纯听课/纯参会", value: "join-only" }
  - key: creation_pattern
    tier: blocking
    question: "你的会议是随开随用，还是需要提前预约？（本维度与 roomid_origin 正交：号从哪来 ≠ 现在开还是约将来，两者不要合并）"
    options:
      - { label: "随开随用 —— 点一下马上开会", value: "instant" }
      - { label: "提前预约 —— 先订好时间，到点再进", value: "scheduled" }
      - { label: "两种都要", value: "both" }
  - key: passive_exit_target
    tier: deferrable
    default: lobby
    question: "用户被动离开会议（被请出、会议结束、网络断开重连失败）后，页面默认跳去哪？注意：异地登录顶替（KickedOutOfRoomReason.ReplacedByAnotherDevice）身份态已失效，强制跳登录页，不受此项影响。"
    options:
      - { label: "回会议列表/大厅 —— 方便再进别的会（推荐默认；仅当应用确有大厅/列表页可回时才适用）", value: "lobby" }
      - { label: "回登录页", value: "login" }
      - { label: "弹提示，让用户在【重新入会 / 回首页】之间自己决定", value: "prompt-user" }
decision_constraints:
  - when: { roomid_origin: join-only }
    forbid: { creation_pattern: both }
    reason: "“只进别人的会”意味着前端不具备建房能力，无法支撑“即时+预约都要”；onboarding 选到此组合时应校验拦截，提示改选 instant 或调整 roomid_origin。"
  - when: { roomid_origin: join-only }
    adjust: { passive_exit_target: { disable_option: lobby, prefer: [login, prompt-user] } }
    reason: "纯受邀/链接入会的应用通常没有大厅或会议列表页可回，lobby 不可达；此场景应灰掉 lobby 选项，默认推 login 或 prompt-user。"
---

# 房间创建、加入、离开与结束

## 功能说明

房间生命周期负责一场 Conference 通用会议从"被创建"到"被结束"的主链路，覆盖即时会议发起、加入已有房间、在无法确认房间是否已存在时直接创建并加入、主动离房、房主结束会议以及被动退房后的状态收口。它是会议产品的主干流程，服务端预创建房间或代解散房间时，前端仍需通过同一套生命周期能力完成真实入会和退场。

创建时可通过 `options` 传入房间名称（`roomName`）、密码（`password`）和默认入会规则（`isAllMicrophoneDisabled` 等），这些配置决定了成员进入房间后的初始受限状态。房主在会中也可通过 `updateRoomInfo()` 修改房间名称和密码。

## 核心概念

### 角色与操作

| 角色 | 关键操作 | 说明 |
|------|----------|------|
| 房主 / 发起人 | 创建并加入房间、结束房间 | 房主通常拥有会议生命周期中的最高控制权 |
| 普通参会人 | 加入已有房间、主动离房 | 普通成员可以进入和离开会议，但不能结束整个房间 |
| 服务端业务系统 | 预创建 / 销毁房间 | 可通过服务端能力提前准备会议，但前端仍负责真正入会与状态收口 |
| 客户端应用 | 监听生命周期变化 | 负责处理房间结束、被踢、异常断开、重进等状态变化 |

### 事件流

| 阶段 | 参与方 | 关键动作 |
|------|--------|----------|
| 登录就绪 | 用户 → 客户端 | 完成登录，确认当前用户已具备可调用房间能力的身份态 |
| 创建或加入 | 客户端 | 已知房间存在时发起 `joinRoom`；若只知道 `roomId` 但不确定房间是否存在，可直接发起 `createAndJoinRoom` |
| 会议建立 | 房间状态 | `currentRoom` 建立，参会人列表和布局开始同步 |
| 退出会议 | 用户 / 系统 | 发生主动离房、房主结束、被踢出、网络异常断开等事件 |
| 状态清理 | 客户端 | 清理房间上下文、会中状态和界面残留，恢复到可再次入会的初始态 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| `roomId` | 当前房间唯一标识，创建和加入都会围绕它展开 |
| `currentRoom` | 当前房间的核心响应式状态入口 |
| 登录就绪状态 | 决定当前是否已经可以安全发起创建、加入、离房或结束动作 |
| 生命周期状态 | 表示当前处于创建中、加入中、会中、离房中或已结束 |
| 房主信息 | 决定谁有权结束会议以及执行部分管理能力 |
| 单用户单房间约束 | 同一用户同一时刻通常只能维持一个有效房间上下文 |
| 被动退房原因 | 用于区分房间结束、被踢、网络异常等不同退出来源 |

### 状态机

```text
idle
  → creating / joining
  → joined
  → leaving / ending
  → idle

joined
  → kicked-out
  → room-ended
  → reconnecting
  → idle
```

### 典型接入场景

| 场景 | 推荐主路径 | 说明 |
|------|------------|------|
| 临时沟通 / 即时会议 | 发起人 `createAndJoinRoom`，其他成员 `joinRoom` | 适合 IM 会话内快速开会或临时拉会 |
| 预约会议到点入会 | 先通过 `room-schedule` 完成预约，真正开会时回到 `joinRoom` 或 `createAndJoinRoom` | 预约成功不等于已经进入会议 |
| 服务端统一创建会议 | 服务端预先生成并维护 `roomId`，客户端在指定入口 `joinRoom` | 适合政务、医疗、企业 OA 等强管控场景 |
| 双向对等发起 | 直接使用 `createAndJoinRoom` | 适合在线问诊、视频面试、1v1 客服等无法预判谁先入会的场景 |
| 邀请链接 / 会议列表入会 | `joinRoom` | 前提是房间已经由发起人、预约系统或服务端准备好 |

### 被动退房与失败分流

| 类型 | 常见来源 | 处理重点 |
|------|----------|----------|
| 房间被结束 | 房主调用结束会议 | 提示会议已结束，并立即收口会中 UI 与状态 |
| 成员被移出 | 房主 / 管理员移出成员 | 给出明确原因提示，不要只停留在旧页面 |
| 账号被顶替 / 异地登录 | 同账号在其他设备进入会议 | 提示当前设备已失效，并回到安全的可重入状态 |
| 断线或重连失败 | 网络超时、离线期间房间状态已变化 | 区分临时重连与最终退房，避免页面假在线 |
| 房间不存在 | 对不存在的房间调用 `joinRoom` | 提示房间不存在；若属于双向对等发起场景，可改走 `createAndJoinRoom` |
| 房间人数已满 | 房间达到成员上限 | 给出明确失败提示，并引导稍后重试或联系房主 |
| `roomId` 已占用 | 创建时使用了已被占用的 `roomId` | 回查 `roomId` 生成策略；若允许“存在则加入”，可改走 `createAndJoinRoom` |

## 前置条件
**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`

**前置状态**：
- 已阅读 `conference/room-lifecycle`，明确当前能力的产品边界。
- 已完成 `conference/login-auth`，确保当前页面具备稳定登录态。
- 已根据业务流程接入会议上下文；需要房间状态时，优先通过当前 slice 统一承接。

## 最佳实践

### ✅ ALWAYS

1. **把创建、加入、离开、结束视为同一条生命周期链路** —— 不要只写“进房成功”的快乐路径，退场和异常分支同样是主流程的一部分。
2. **登录真正就绪后再触发房间生命周期动作** —— 未确认登录态时抢跑调用，很容易导致入房失败或状态漂移。
3. **根据是否确定房间已存在选择 `joinRoom` 或 `createAndJoinRoom`** —— 已知房间存在就直接加入；无法确认存在性时再走“存在则加入，不存在则创建”的路径。
4. **把服务端预创建房间与端上即时入会统一收口到前端生命周期管理** —— 即使房间由服务端准备，前端仍要显式处理入房与离房状态。
5. **对被动退房做明确原因区分** —— 房间结束、被踢、网络断连需要不同的 UI 提示与状态恢复方式。
6. **离房或结束后立即清理会中上下文** —— 包括当前房间状态、局部面板、聊天上下文和布局焦点，避免残留到下一场会议。
7. **让 `options` 模型集中维护房间配置，让生命周期负责流程切换** —— `roomName`、`password`、默认规则属于配置语义，建议收口到一个 `baseRoomOptions` 对象；创建 / 加入 / 离开 / 结束才属于生命周期语义。

### ❌ NEVER

1. **不要把接受邀请等同于已经入会** —— 邀请只是前置信令，真正进入会议仍应回到房间生命周期执行。
2. **不要只处理主动离房，不处理被动退房** —— 房间主链路必须覆盖被踢、被结束、重连失败等异常分支。
3. **不要在旧房间状态未清理前直接复用下一场会议上下文** —— 很容易造成房间号错乱、成员状态串场或 UI 残留。
4. **不要在 `room-lifecycle` 里把预约时间、参会人等排期字段当成房间配置主语义** —— 这些是 `room-schedule` 的时间维度能力。

## 代码示例
### 场景一：房主 / 发起人直接创建并进入快速会议

```ts
import { useRoomState } from 'tuikit-atomicx-vue3/room';

const { createAndJoinRoom, currentRoom } = useRoomState();

await createAndJoinRoom({
  roomId: 'demo_room',
  options: { roomName: '演示会议' },
});

console.log(currentRoom.value?.roomId);
```

### 场景二：已知房间已经存在，直接加入

```ts
import { useRoomState } from 'tuikit-atomicx-vue3/room';

const { joinRoom, currentRoom } = useRoomState();

await joinRoom({
  roomId: 'demo_room',
});

console.log(currentRoom.value?.roomId);
```

### 场景三：只知道 `roomId`，但不确定房间是否已经存在

```ts
import { useRoomState } from 'tuikit-atomicx-vue3/room';

const { createAndJoinRoom, currentRoom } = useRoomState();

await createAndJoinRoom({
  roomId: 'demo_room',
  options: { roomName: '业务沟通房间' },
});

console.log(currentRoom.value?.roomId);
```

### 场景四：会议结束前正确收口

```ts
import { useRoomState } from 'tuikit-atomicx-vue3/room';

const { leaveRoom, endRoom } = useRoomState();

await leaveRoom();
// 房主结束会议：await endRoom();
```

### 场景五：创建带配置的会议（房间名称、密码、默认规则）

创建会议时可通过 `options` 传入房间名称、密码和默认入会规则（全员禁麦/禁画/禁共享/禁消息），这些配置会决定成员进入房间后的初始受限状态。

```ts
import { reactive, computed } from 'vue';
import { useRoomState } from 'tuikit-atomicx-vue3/room';

const { createAndJoinRoom } = useRoomState();

const roomDraft = reactive({
  roomId: 'room_20260507_001',
  roomName: '产品评审会',
  password: '123456',
  isAllMicrophoneDisabled: true,
  isAllCameraDisabled: true,
  isAllScreenShareDisabled: true,
  isAllMessageDisabled: true,
});

const baseRoomOptions = computed(() => ({
  roomName: roomDraft.roomName.trim(),
  password: roomDraft.password || undefined,
  isAllMicrophoneDisabled: roomDraft.isAllMicrophoneDisabled,
  isAllCameraDisabled: roomDraft.isAllCameraDisabled,
  isAllScreenShareDisabled: roomDraft.isAllScreenShareDisabled,
  isAllMessageDisabled: roomDraft.isAllMessageDisabled,
}));

async function createConfiguredRoom() {
  await createAndJoinRoom({
    roomId: roomDraft.roomId,
    options: baseRoomOptions.value,
  });
}
```

> **说明：**
> - `baseRoomOptions` 可以在即时会议和预约会议中复用；预约会议时额外补充 `scheduleStartTime`、`scheduleEndTime`、`scheduleAttendees` 等字段（由 `room-schedule` 承接）。
> - 默认规则字段映射（Web）：`isAllMicrophoneDisabled` / `isAllCameraDisabled` / `isAllScreenShareDisabled` / `isAllMessageDisabled`，对应全员禁麦、禁画、禁共享、禁消息。
> - 当默认规则为 `true` 时，前端不应只在接口侧生效，还应同步让对应按钮切到禁用图标和禁用提示态（见下方 UI 状态派生）。

### 默认规则驱动 UI 状态派生

```ts
const toolbarUiState = computed(() => ({
  microphone: {
    disabled: baseRoomOptions.value.isAllMicrophoneDisabled,
    icon: baseRoomOptions.value.isAllMicrophoneDisabled ? 'mic-off-disabled' : 'mic-on',
    tooltip: baseRoomOptions.value.isAllMicrophoneDisabled ? '房主已开启全员静音' : '打开麦克风',
  },
  camera: {
    disabled: baseRoomOptions.value.isAllCameraDisabled,
    icon: baseRoomOptions.value.isAllCameraDisabled ? 'cam-off-disabled' : 'cam-on',
    tooltip: baseRoomOptions.value.isAllCameraDisabled ? '房主已禁用摄像头' : '打开摄像头',
  },
}));
```

### 场景六：会中修改房间名称或密码

房主在会议中可调用 `updateRoomInfo()` 修改房间基础信息，但必须确认仍在当前房间内。

```ts
import { useRoomState } from 'tuikit-atomicx-vue3/room';

const { updateRoomInfo, currentRoom } = useRoomState();

async function updateRoomNameOrPassword(newName: string, newPassword?: string) {
  if (!currentRoom.value) {
    console.warn('当前不在任何房间内，不能更新房间信息');
    return;
  }

  await updateRoomInfo({
    roomId: currentRoom.value.roomId,
    options: {
      roomName: newName.trim(),
      password: newPassword || undefined,
    },
  });
}
```

### 处理房间结束与被动退房：监听房间被解散、被踢和异常退出

```ts
import { onMounted, onUnmounted } from 'vue';
import {
  useRoomParticipantState,
  useRoomState,
  RoomEvent,
  RoomParticipantEvent,
  KickedOutOfRoomReason,
} from 'tuikit-atomicx-vue3/room';

const { subscribeEvent, unsubscribeEvent } = useRoomState();
const {
  subscribeEvent: subscribeParticipantEvent,
  unsubscribeEvent: unsubscribeParticipantEvent,
} = useRoomParticipantState();

// passive_exit_target 决定“被动离开后默认跳哪”：'lobby' | 'login' | 'prompt-user'
// 由 business_decisions 注入；这里以 'lobby' 为例
const passiveExitTarget: 'lobby' | 'login' | 'prompt-user' = 'lobby';

// 关键：跳转前必须先清理会中上下文，否则下一场会议会串场（聊天/布局/成员残留）
function cleanupRoomContext() {
  // 清理 currentRoom 派生状态、聊天上下文、布局焦点、局部面板等
}

function routeAfterPassiveExit(target: 'lobby' | 'login' | 'prompt-user') {
  cleanupRoomContext();
  switch (target) {
    case 'login':
      // router.replace('/login')
      break;
    case 'prompt-user':
      // 弹窗，提供【重新入会 / 回首页】两个动作，由用户决定
      break;
    case 'lobby':
    default:
      // router.replace('/meeting/lobby') —— 前提是应用确有大厅/列表页
      break;
  }
}

function onRoomEnded() {
  console.log('房主已结束会议');
  routeAfterPassiveExit(passiveExitTarget);
}

function onKickedFromRoom({ reason }: { reason: KickedOutOfRoomReason; message: string }) {
  switch (reason) {
    case KickedOutOfRoomReason.KickedByAdmin:
      console.log('当前用户被房主或管理员移出房间');
      routeAfterPassiveExit(passiveExitTarget);
      break;
    case KickedOutOfRoomReason.ReplacedByAnotherDevice:
      // 异地登录顶替：当前设备身份态已失效，强制回登录页，覆盖 passiveExitTarget
      console.log('当前账号已在其他设备进入会议');
      routeAfterPassiveExit('login');
      break;
    case KickedOutOfRoomReason.ConnectionTimeout:
      console.log('网络连接超时，当前会议状态需要重新确认');
      routeAfterPassiveExit(passiveExitTarget);
      break;
    default:
      console.log('当前用户已退出房间');
      routeAfterPassiveExit(passiveExitTarget);
      break;
  }
}

onMounted(() => {
  subscribeEvent(RoomEvent.onRoomEnded, onRoomEnded);
  subscribeParticipantEvent(RoomParticipantEvent.onKickedFromRoom, onKickedFromRoom);
});

onUnmounted(() => {
  unsubscribeEvent(RoomEvent.onRoomEnded, onRoomEnded);
  unsubscribeParticipantEvent(RoomParticipantEvent.onKickedFromRoom, onKickedFromRoom);
});
```

## 调用时序
```
完成 login-auth
   │
   ▼
决定当前路径：创建会议 或 加入已有会议
   │
   ├─ 房主端 → createAndJoinRoom({ roomId, options })
   └─ 成员端 → joinRoom({ roomId })
   │
   ▼
以 currentRoom 作为会议内真实状态来源
   │
   ├─ 普通离开 → leaveRoom()
   ├─ 房主结束 → endRoom()
   └─ 会议被结束 → 通过事件和 currentRoom 变化收口 UI
```

## 平台特有注意事项
### 1. 登录真正就绪后再调用房间生命周期接口
`login()` 是异步动作。单页应用里更适合监听 `loginUserInfo.value?.userId` 或等价登录完成信号，确认用户身份已就绪后再调用 `createAndJoinRoom()`、`joinRoom()`、`leaveRoom()`、`endRoom()`。

### 2. `useRoomState` 是单例，同一时刻只承接一个房间上下文
同一用户同一时间通常只能处于一个有效房间内。切房前应先完成上一场会议的离房或结束收口，避免多个房间状态并存。

### 3. 按业务目标区分 `createAndJoinRoom()` 与 `joinRoom()`
如果当前用户就是房主 / 发起人，需要立即创建并进入一场新会议，应使用 `createAndJoinRoom()`；如果房间已经由发起人、会议列表、预约系统或服务端预先创建好，应使用 `joinRoom()`；如果双方只知道同一个 `roomId`，但无法预先判断房间是否存在，也更适合使用 `createAndJoinRoom()` 承接“存在则加入，不存在则创建”的场景。

调用 `joinRoom()` 时只需要传入 `roomId`；如果是密码房，再额外传入顶层 `password` 字段，例如 `joinRoom({ roomId, password })`。不要把密码或空对象包进 `options`，当前 Web API 的加入房间签名并不接收 `options`。

### 4. `leaveRoom()` 与 `endRoom()` 是两类不同动作
普通成员离开会议应调用 `leaveRoom()`；房主若要真正解散会议，需要调用 `endRoom()`，两者语义不能混用。

### 5. `currentRoom` 是会中真实状态源
即使房间由服务端预创建、预销毁或通过其他链路调度，前端仍要以 `currentRoom` 和实际入会流程作为最终真实状态来源。

### 6. 密码房和入会错误需要业务侧自行承接
加入密码房时，要准备好对 `ERR_NEED_PASSWORD`、`ERR_WRONG_PASSWORD` 等结果做输入与重试处理；若出现房间不存在、人数已满等错误，也应给出明确反馈，而不是只在控制台报错。

### 7. 被动退房最好通过事件与页面收口统一处理
房主结束会议、成员被踢、异地登录顶替、网络超时等情况，本质上都属于“被动离开当前房间”。业务层最好统一监听房间事件并收口页面，而不是分别在多个组件里零散兜底。

被动退房后的跳转目标由 `passive_exit_target` 决策驱动，但**跳转目标不是一刀切**，要按退出原因分层：

| 退出原因 | 来源 | 跳转目标 |
|----------|------|----------|
| 房主结束 / 被移出 / 重连失败 | `onRoomEnded`、`KickedByAdmin`、`ConnectionTimeout` | 用 `passive_exit_target` 的选择（`lobby` / `login` / `prompt-user`） |
| 异地登录顶替 | `KickedOutOfRoomReason.ReplacedByAnotherDevice` | **强制 `login`**，覆盖 `passive_exit_target` —— 当前设备身份态已失效，跳大厅会立刻再次失败 |

两条额外约束：

- **跳转前必须先清理会中上下文**（`currentRoom` 派生状态、聊天、布局、局部面板），否则跳回大厅再进下一场会议会串场。
- **`lobby` 可达性依赖应用形态**：纯受邀 / 邀请链接直接入会（`roomid_origin = join-only`）的应用通常没有大厅或会议列表页，此时 `lobby` 不可达，应在 onboarding 灰掉该选项，默认推 `login` 或 `prompt-user`。
- **`prompt-user` 必须定义弹窗动作集合**：约定提供【重新入会 / 回首页】两个动作，否则生成代码时无从决定按钮。

### 8. `roomId` 应由业务侧保证唯一性
建议由业务后端生成全局唯一 `roomId`，避免测试环境与正式环境、不同会议之间发生 ID 冲突或复用歧义。

### 9. 建房时把配置收口到一个 `baseRoomOptions` 对象
`roomName`、`password`、默认规则等字段的维护与解释，建议收口到一个 `baseRoomOptions` / `roomDraft` 对象，避免散落在多个分支里。默认规则字段在 Web 侧对应 `isAllMicrophoneDisabled`、`isAllCameraDisabled`、`isAllScreenShareDisabled`、`isAllMessageDisabled`，它们同时决定了按钮图标、禁用态和提示文案。

### 10. 默认规则生效后，按钮图标和禁用态也要同步
例如 `isAllMicrophoneDisabled` 为 `true` 时，麦克风按钮不应继续显示为"可开麦"图标；更合理的做法是同步切换到禁用态图标、禁用点击并展示"房主已开启全员静音"之类的提示。`isAllCameraDisabled`、`isAllScreenShareDisabled`、`isAllMessageDisabled` 也应同理映射到对应入口的禁用态。

### 11. `updateRoomInfo()` 仅适合房主在会中执行
更新房间名称或密码前，应确认操作者仍在当前房间内；如果房主已经离房，通常需要重新入会后再修改。

### 12. 创建期默认规则与会中动态治理要分层
默认禁麦、禁画、禁共享、禁消息等规则适合在 `options` 中一次性声明。会中临时禁言、关闭单成员设备等动作仍应由 `conference/participant-management` 承接。

### 13. 密码字段属于配置语义，但密码交互属于入会流程语义
创建时写入 `password`；加入密码房时，密码输入、错误提示和重试逻辑，应由本 slice 的加入流程承接。

## 常见错误与场景对照

| 错误 / 场景 | 常见触发时机 | 建议处理方式 |
|-------------|--------------|--------------|
| `ERR_NEED_PASSWORD` | 加入密码房但未传密码 | 弹出密码输入框，输入后再次调用 `joinRoom({ roomId, password })` |
| `ERR_WRONG_PASSWORD` | 输入的入会密码错误 | 提示密码错误，并允许用户修正顶层 `password` 后重试 |
| `ERR_ROOM_ID_NOT_EXIST` | 对不存在的房间调用 `joinRoom({ roomId })` | 提示房间不存在；若属于对等发起场景可改走 `createAndJoinRoom()` |
| `ERR_ROOM_USER_FULL` | 房间人数达到上限 | 提示房间已满，引导稍后重试或联系房主 |
| `ERR_ROOM_ID_OCCUPIED` | 创建时 `roomId` 已被占用 | 检查 `roomId` 生成策略；若允许“存在则加入”，优先使用 `createAndJoinRoom()` |
| `RoomEvent.onRoomEnded` | 房主结束当前会议 | 提示会议已结束，并退出会中页面 |
| `RoomParticipantEvent.onKickedFromRoom` | 当前用户被移出、被顶替或重连失败 | 根据 `reason` 区分提示文案，并回收当前会中状态 |

## 代码生成约束
### 编译必要条件
- **通用条件**：见 [login-auth 平台 slice](login-auth.md)。
- **额外导入**：至少需要导入 `useRoomState`。
- **运行前提**：页面已具备有效登录态，且拿到可用的 `roomId`。

### 生成规则
#### MUST（生成时必须包含）

1. **通过 `useRoomState` 承接创建、加入、离开和结束会议的主链路** — 才能让状态与 UI 从同一来源收口。  
   **Verify**: 检查是否存在 `useRoomState()` 与生命周期 API 调用。
2. **在登录真正就绪后再触发房间生命周期动作** — 未确认登录完成时抢跑调用很容易导致状态异常。  
   **Verify**: 检查是否存在登录完成判断，例如监听 `loginUserInfo.value?.userId` 或等价登录完成信号。
3. **按业务目标选择 `createAndJoinRoom()` 或 `joinRoom()`** — 房主快速创建并入会、以及无法确认房间是否存在时，都更适合 `createAndJoinRoom()`；只有已知房间已存在时才直接使用 `joinRoom()`。  
   **Verify**: 检查是否把“房主创建并入会”“已知房间存在直接加入”“存在性未知时尝试进入”这三类路径明确区分。
4. **把 `currentRoom` 作为会中状态锚点** — 能避免页面层与房间真实状态漂移。  
   **Verify**: 检查是否读取 `currentRoom` 或围绕其变化更新页面。
5. **为密码房和常见入会错误预留业务反馈** — 无 UI 接入时，密码输入、重试和错误提示都需要页面自行承接。  
   **Verify**: 检查加入流程是否处理 `ERR_NEED_PASSWORD`、`ERR_WRONG_PASSWORD` 或等价失败提示。
6. **被动退房后按 `passive_exit_target` 决策收口路由，且跳转前先清理会中上下文** — 房主结束、被移出、重连失败走该决策选定目标；`ReplacedByAnotherDevice` 强制跳登录页，覆盖该决策。  
   **Verify**: 检查 `onRoomEnded` / `onKickedFromRoom` 中是否存在按 `reason` 分层的跳转，且跳转前调用了上下文清理；`creation_pattern` / `roomid_origin` 的代码分支与决策值一致。

#### MUST NOT（生成时绝不能出现）

1. **不要把 `leaveRoom()` 当成解散会议** — 会导致房主离开后房间仍在。  
   **Verify**: 检查房主结束逻辑是否明确调用 `endRoom()`。
2. **不要只信任服务端预创建结果而跳过前端真实入会状态判断** — 页面可能显示“已在会中”但底层并未入房。  
   **Verify**: 检查是否仍通过 `joinRoom()` / `createAndJoinRoom()` 与 `currentRoom` 收口。

### 集成检查点
- 当前 slice 是 `conference/web` 大多数能力的房间状态基座。
- 集成方式通常是新增页面路由状态或 ViewModel，不需要改 SDK 底层。
- 若业务同时存在预约会议、呼叫入会或服务端预创建房间，需要统一约定 `roomId` 和入会入口。

## 验证矩阵
| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已导入 `useRoomState` | 检查 `import` 语句 | 房间生命周期 Hook 可解析 |
| 2. 静态规则级 | 进房路径、离开与结束动作分层明确 | 搜索 `joinRoom` / `createAndJoinRoom` / `leaveRoom` / `endRoom` | 进入、离开、结束职责清晰 |
| 3. 运行时级 | 创建 / 加入会议后 `currentRoom` 可用 | 进房并查看调试状态 | 可读取有效 `roomId` |
| 4. 业务行为级 | 密码房与错误提示、离开与结束后的页面状态正确收口 | 分别测试密码入会、离会与结束会议 | UI 与房间真实状态一致，失败时有明确反馈 |

---

> **official-roomkit 模式用户注意**：如果 `ui_mode = official-roomkit`，
> 房间操作通过 `conference` 对象而非直接 composable。
> 完整的 `conference` API 签名、枚举定义和代码示例见
> **[`conference/web/official-roomkit-api.md`](./official-roomkit-api.md)**。

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 进房失败 | 创建或加入调用后未能进入会中态 | 先检查登录是否完成，再确认房间配置参数、房间号和调用时机是否正确 |
| 房间已结束但 UI 未退出 | 房主结束会议后，部分参会人页面仍停留在会中 | 检查是否监听并处理了房间结束、被动退房与清理逻辑 |
| 离房后状态残留 | 再次入会时看到上一场会议的聊天、布局或成员数据 | 检查离房和结束路径是否统一清理 `currentRoom` 及相关派生状态 |

### 排障流程

```text
发现 房间创建、加入、离开与结束 相关问题
├── 第 1 步：确认登录是否已完成，并且 roomId / roomName / options 使用的是当前会议上下文
├── 第 2 步：检查当前流程属于创建、加入、主动离房还是被动退房，不要混淆处理分支
├── 第 3 步：确认 currentRoom 建立与销毁时，参会人列表、布局、聊天等派生状态是否同步收口
└── 第 4 步：若仍异常，再回查 login-auth / participant-list / room-schedule 的衔接是否正确
```

## 关联知识

- **[conference/login-auth](login-auth.md)** —— 房间生命周期开始前的统一身份鉴权入口。
- **[conference/room-schedule](room-schedule.md)** —— 预约会议复用房间配置模型，并补充时间与参会人维度。
- **[conference/room-call](room-call.md)** —— 会中呼叫房外用户入会，呼叫接受后仍需回到本 slice 执行入房。
- **[conference/participant-list](participant-list.md)** —— 进房成功后开始同步的成员读模型与状态展示。