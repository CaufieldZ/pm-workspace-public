---
id: conference/participant-management
name: 参会人管理与会控
product: conference
platform: web
tags: [participant, role, admin, owner, kick, transfer, moderation, mute, device-control, message-control, device-request]
platforms: [web]
related: [conference/participant-list, conference/room-call, conference/room-lifecycle, conference/room-chat, conference/device-control, conference/screen-share]
api_docs:
  - title: 成员管理
    url: https://cloud.tencent.com/document/product/647/126927
business_decisions:
  - key: management_features
    tier: blocking
    multi_select: true
    baseline: ["list"]   # 始终生成的基础能力，不作为多选项展示（参会人列表默认提供）
    question: "主持人需要哪些会控权限？（参会人列表默认展示，以下为额外管控能力，可多选）"
    options:
      - { label: "管控单个成员 —— 静音 / 关闭摄像头 / 禁止发言 / 邀请开设备", value: "single-control" }
      - { label: "全场管控 —— 全员静音、全员禁画、全员禁言、设备申请审批", value: "all-room" }
      - { label: "成员身份管理 —— 设置 / 撤销管理员、转让主持人、移出成员（含破坏性操作）", value: "role-and-kick" }
---

# 参会人管理与会控

## 功能说明

参会人管理与会控负责会议中所有"针对成员"的治理动作——既包括成员级治理（角色调整、移出、名片维护、单成员关闭设备），也包括房间级会控（全员禁麦、全员禁画、全员禁言、设备申请审批与邀请）。它解决的是"谁可以管理谁、可以做什么、规则如何同步、被治理的人如何感知和响应"这一整套问题。它不负责成员列表的纯展示（归属 `conference/participant-list`），也不等同于成员列表组件本身。

## 核心概念

### 角色与操作

| 角色 | 关键操作 | 说明 |
|------|----------|------|
| 房主 | 设置 / 撤销管理员、转让房主、移出成员、关闭成员设备、全员禁麦 / 禁画 / 禁言、处理设备申请、邀请成员开启设备 | 通用会议中同一时间通常只有一个房主，是成员治理与会控的最高权限角色 |
| 管理员 | 移出成员、关闭成员设备、单独 / 全体禁言、全体禁用设备、处理设备申请、邀请成员开启设备 | 由房主授予；可执行大部分治理动作，但不能设置管理员、撤销管理员或转让房主 |
| 普通成员 | 查看自身角色、维护自身名片、申请开启受限设备、响应管理侧设备邀请 | 不能治理他人，但可维护自己的名片，并在设备受限时发起开启申请或响应邀请 |
| 设备 / 聊天 / 共享模块 | 消费会控结果 | 禁言、禁设备、禁共享等规则最终会作用到输入区、设备按钮和共享入口 |

### 关键治理动作

| 动作 | 谁可以发起 | 结果 |
|------|------------|------|
| `setAdmin` | 仅房主 | 把普通成员设为管理员 |
| `revokeAdmin` | 仅房主 | 撤销管理员身份 |
| `transferOwner` | 仅房主 | 把房主身份转交给其他成员 |
| `kickParticipant` | 房主 / 管理员 | 移出指定成员 |
| `closeParticipantDevice` | 房主 / 管理员 | 关闭指定成员的麦克风、摄像头或屏幕共享 |
| `disableUserMessage` | 房主 / 管理员 | 单独禁言 / 解禁某成员 |
| `disableAllDevices` | 房主 / 管理员 | 全员禁用 / 解除禁用 麦克风、摄像头或屏幕共享 |
| `disableAllMessages` | 房主 / 管理员 | 全体禁言 / 解除禁言 |
| `requestToOpenDevice` | 普通成员 | 申请房主 / 管理员批准开启被禁用的设备 |
| `approveOpenDeviceRequest` / `rejectOpenDeviceRequest` | 房主 / 管理员 | 处理普通成员的设备开启申请 |
| `inviteToOpenDevice` | 房主 / 管理员 | 邀请成员开启麦克风、摄像头或屏幕共享 |
| `acceptOpenDeviceInvitation` / `declineOpenDeviceInvitation` | 普通成员 | 接受 / 拒绝管理侧的设备开启邀请 |
| `updateParticipantNameCard` | 成员本人 / 房主 / 管理员 | 更新成员名片 |
| `updateParticipantMetaData` | 业务层按权限控制 | 更新业务扩展字段 |

### 事件流

| 阶段 | 参与方 | 关键动作 |
|------|--------|----------|
| 权限确认 | 当前用户 | 根据本地角色决定治理 / 会控入口的展示与可执行动作 |
| 发起操作 | 房主 / 管理员 / 普通成员 | 角色调整、移出、关闭设备、全员规则、设备协作或资料维护 |
| 规则同步 | 房间状态 | 角色变化、成员去留、设备 / 消息禁用结果、待处理申请与邀请同步到所有端 |
| 成员响应 | 普通成员 | 根据当前限制调整输入和设备操作；必要时发起设备申请或响应邀请 |
| 结果反馈 | 客户端 / 业务层 | 申请被批准 / 拒绝 / 超时 / 已被他人处理等结果回流到界面 |
| 规则解除 | 房主 / 管理员 | 取消或调整当前会控状态，并收口相关提示和入口 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| `localParticipant.role` | 当前用户角色，是治理和会控入口显隐的唯一可信来源 |
| `participant.role` | 成员角色，用于判断房主、管理员、普通成员 |
| `participant.microphoneStatus` / `cameraStatus` / `screenShareStatus` | 成员当前设备状态，会控生效后会自动同步 |
| `participant.isMessageDisabled` | 成员单独禁言状态 |
| 全员设备禁用状态 | 控制普通成员是否还能自行开启麦克风、摄像头或屏幕共享；房主和管理员通常不受该限制 |
| 全员消息禁用状态 | 控制普通成员聊天输入区是否可用 |
| 管理端房间级会控读模型 | 供房主 / 管理员按钮、菜单文案和二次确认提示回显当前全员静音 / 禁画 / 禁言状态；不应只存在于一次点击的临时变量中 |
| `pendingDeviceApplications` | 当前仍待管理员处理的设备开启申请 |
| `pendingDeviceInvitations` | 当前仍待成员响应的设备开启邀请 |
| `nameCard` / `metaData` | 成员名片 / 业务扩展信息 |
| 当前治理动作结果 | 表示成功、失败、无权限、目标已离会等结果 |
| 管理员数量限制 | 应以产品配置或服务端规则为准，业务层不要写死 |

### 角色能力矩阵

| 能力 | 房主 | 管理员 | 普通成员 |
|------|------|--------|----------|
| 查看成员列表 | 支持 | 支持 | 支持 |
| 修改自己的名片 | 支持 | 支持 | 支持 |
| 修改任意成员名片 | 支持 | 支持 | 不支持 |
| 设置 / 撤销管理员 | 支持 | 不支持 | 不支持 |
| 转让房主 | 支持 | 不支持 | 不支持 |
| 解散房间 | 支持 | 不支持 | 不支持 |
| 移出成员 | 支持 | 支持 | 不支持 |
| 关闭指定成员设备 | 支持 | 支持 | 不支持 |
| 全员禁用设备 | 支持 | 支持 | 不支持 |
| 单独禁言 | 支持 | 支持 | 不支持 |
| 全体禁言 | 支持 | 支持 | 不支持 |
| 处理设备开启申请 | 支持 | 支持 | 不支持 |
| 邀请成员开启设备 | 支持 | 支持 | 不支持 |
| 申请开启受限设备 | 不需要 | 不需要 | 支持 |

### 状态机

```text
idle
  → role-checked
  → applying-action
  → waiting-sync
  → synced
  → idle

applying-action
  → denied
  → failed
  → idle

room-default
  → moderation-applied
  → participant-restricted
  → request-or-invitation-pending
  → result-synced
  → moderation-released
  → room-default
```

## 前置条件
**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`

**前置状态**：
- 已阅读 `conference/participant-management`，明确当前能力的产品边界。
- 已完成 `conference/login-auth`，确保当前页面具备稳定登录态。
- 已根据业务流程接入会议上下文；需要房间状态时，优先通过 `conference/room-lifecycle` 统一承接。

## 最佳实践

### ✅ ALWAYS

1. **同时在界面层和调用层做权限校验** —— 普通成员不可见的治理 / 会控入口应在界面层隐藏；接口调用仍要处理无权限、目标已离会、申请或邀请超时等失败情况。
2. **统一通过 `participant.role` 或 `localParticipant.role` 判断角色** —— 不要依赖 `adminList`、缓存字段或展示文案。
3. **把成员级治理与房间级会控分层处理** —— 设置管理员、转让房主、移出成员、关闭单成员设备属于成员级；全员禁麦 / 禁画 / 禁言属于房间级；两者表达方式和恢复路径不同，但同属于本 slice。
4. **把创建期默认规则与会中动态会控分开** —— 创建期默认禁麦 / 禁画 / 禁聊归属 `conference/room-lifecycle`；会中动态调整归属本 slice。
5. **让房主 / 管理员的房间级会控按钮体现当前状态并支持 toggle** —— "全员静音 / 解除全员静音"、"全员禁言 / 解除全员禁言"应围绕当前状态成对出现，不要只提供单向"开启限制"。
6. **让管理端按钮状态从可恢复的房间级状态源初始化** —— 页面刷新、重进房或管理面板重新挂载后，应从房间状态、`roomInfo` 映射或业务侧会控快照中恢复，而不是默认回到未禁用态。
7. **让会控结果直接作用到真实交互路径** —— 禁言要禁用输入区、禁设备要限制真实开启动作、禁共享要限制共享入口，而不是只改文案。
8. **让治理与会控结果都回流到界面** —— 角色变化、成员离会、设备被关闭、申请被处理、邀请被接受 / 拒绝后，成员列表、入口显隐、待处理列表和提示信息都应同步更新。
9. **明确 `disableAllDevices` 的作用范围** —— 房间级规则，可作用于麦克风、摄像头和屏幕分享；通常只约束普通成员，房主和管理员不受该限制。
10. **明确 `disableAllMessages` 的作用范围** —— 通常只约束普通成员；房主和管理员仍需保留必要的会中管理与沟通能力。
11. **区分房间级禁用与单成员关闭的恢复路径** —— 房间级禁用期间，普通成员入口表现为 disabled，按产品需要走申请开启链路；单成员关闭只是一次"纠正当前状态"的动作，没有叠加房间级禁用时，成员获得提示后仍可再次主动开启。
12. **对设备申请和邀请做好超时、取消和重复处理收口** —— 多管理员协作时，申请或邀请可能已被他人处理，界面应及时关闭无效入口。
13. **管理员数量限制和业务字段规则来自产品配置或服务端约束** —— 不要在客户端写死上限；`metaData` 字段含义和展示规则应提前约定。

### ❌ NEVER

1. **不要把成员级治理和房间级会控看成两个完全不同的系统** —— 它们应统一在一个治理面板里被设计和使用，但要清楚标注每个动作影响的是单成员还是全房间。
2. **不要依赖 `adminList`、本地缓存或展示文案判断角色** —— 通用会议不单独维护管理员列表，角色判断应回到成员状态本身。
3. **不要把全员会控按钮做成只有"开启"没有"解除"的单向动作** —— 真实产品中的全员静音 / 禁画 / 禁言都应支持回退。
4. **不要只在管理端成功提示，不处理成员端反馈** —— 被治理 / 被会控的用户必须看到清晰反馈，否则会误以为是本地故障。
5. **不要把全员规则状态只存在当前页面内存中** —— 页面刷新后会导致管理端 UI 与真实房间规则脱节。
6. **不要在房间级禁用仍生效时让普通成员直接调用开启能力** —— 这会绕开会控语义，并产生"点了没反应"的混乱体验。
7. **不要让普通成员暴露房间级会控入口** —— 会控能力应严格受房主 / 管理员权限边界约束。
8. **不要把一次点击或一次接口返回当成最终结果** —— 仍需等待角色变化、成员去留、设备协作结果等真实状态回流。
9. **不要把 `metaData` 当成无结构字符串自由拼接** —— 业务侧应提前约定字段含义和展示方式。

## 业务决策与代码生成的对应关系

`business_decisions.management_features` 的多选结果直接决定生成代码的范围。`list` 是 **baseline（基础项）**：始终生成，不作为多选项让用户勾选；`single-control` / `all-room` / `role-and-kick` 是用户多选的额外管控能力。

| 档位 | 生成的 API 与 UI |
|---|---|
| `list`（baseline，始终生成） | `participantList` / `getParticipantList` (含 cursor 分页) / `localParticipant` / `speakingUsers` / `participantWithScreen`；只读列表 + 角色 / 设备状态展示 |
| `single-control` | `closeParticipantDevice` (Mic/Camera/Screen) / `inviteToOpenDevice` / `disableUserMessage`；成员行右侧"⋯"菜单出现"关 TA 设备 / 邀请打开 / 单独禁言"等条目 |
| `all-room` | `disableAllDevices` (Mic/Camera) / `disableAllMessages` / `pendingDeviceApplications` / `approveOpenDeviceRequest` / `rejectOpenDeviceRequest`；面板顶部出现全员控制 toggle 与待审批列表 |
| `role-and-kick` | `setAdmin` / `revokeAdmin` / `transferOwner` / `kickParticipant`；成员菜单出现高风险条目，移出 / 转让需二次确认 |

`list` 因为是 baseline，始终生成；其余三档中未勾选的，对应 API 不导出、不导入、对应 UI 入口不渲染（按 topic G8 规则）。

## 角色权限速览

| 角色 | 枚举值 | 可执行 |
|------|--------|--------|
| 房主 | `RoomParticipantRole.Owner` | 所有治理与会控动作 |
| 管理员 | `RoomParticipantRole.Admin` | 移出成员、关闭成员设备、单独 / 全体禁言、全体禁用设备、处理设备申请、邀请成员开启设备；不可设管理员、撤销管理员、转让房主 |
| 普通成员 | `RoomParticipantRole.GeneralUser` | 查看成员列表、修改自己的名片、申请开启被禁用的设备 |

> 详细能力矩阵见产品级 slice。前端权限校验只用于 UI 显隐；接口调用仍要 `try/catch` 处理无权限错误。

## 代码示例

### 成员列表加载与渲染（`list` 档基础）

```ts
import { onMounted, watch } from 'vue';
import { useRoomParticipantState, useRoomState } from 'tuikit-atomicx-vue3/room';

const { currentRoom } = useRoomState();
const {
  participantList,
  participantListCursor,
  localParticipant,
  getParticipantList,
} = useRoomParticipantState();

onMounted(() => {
  watch(
    () => currentRoom.value?.roomId,
    async (roomId) => {
      if (!roomId) return;
      try {
        await getParticipantList({ cursor: '' });
      } catch (error) {
        console.error('获取成员列表失败:', error);
      }
    },
    { immediate: true },
  );
});

async function loadMoreParticipants() {
  if (!participantListCursor.value) return;
  try {
    await getParticipantList({ cursor: participantListCursor.value });
  } catch (error) {
    console.error('加载更多成员失败:', error);
  }
}
```

### 角色与设备状态展示

```ts
import {
  DeviceStatus,
  RoomParticipant,
  RoomParticipantRole,
  useRoomParticipantState,
} from 'tuikit-atomicx-vue3/room';

const { localParticipant } = useRoomParticipantState();

function getRoleText(role: RoomParticipantRole) {
  if (role === RoomParticipantRole.Owner) return '房主';
  if (role === RoomParticipantRole.Admin) return '管理员';
  return '成员';
}

function isCameraOn(participant: RoomParticipant) {
  return participant.cameraStatus === DeviceStatus.On;
}

function isMicrophoneOn(participant: RoomParticipant) {
  return participant.microphoneStatus === DeviceStatus.On;
}

function isLocalUser(userId: string) {
  return userId === localParticipant.value?.userId;
}
```

### 发言态、屏幕共享态

```ts
import { useRoomParticipantState } from 'tuikit-atomicx-vue3/room';

const {
  speakingUsers,
  participantListWithVideo,
  participantWithScreen,
} = useRoomParticipantState();

function isSpeaking(userId: string) {
  return speakingUsers.value.has(userId);
}

function getVolume(userId: string) {
  return speakingUsers.value.get(userId) || 0;
}

function isSharingScreen(userId: string) {
  return participantWithScreen.value?.userId === userId;
}
```

### 名片与扩展字段

```ts
import { useRoomParticipantState } from 'tuikit-atomicx-vue3/room';

const {
  updateParticipantNameCard,
  updateParticipantMetaData,
} = useRoomParticipantState();

async function updateUserNameCard(userId: string, nameCard: string) {
  try {
    await updateParticipantNameCard({ userId, nameCard });
  } catch (error) {
    console.error('修改成员名片失败:', error);
  }
}

async function updateUserMetaData(userId: string, metaData: Record<string, string>) {
  try {
    await updateParticipantMetaData({ userId, metaData });
  } catch (error) {
    console.error('更新成员扩展信息失败:', error);
  }
}
```

### 角色管理（`role-and-kick` 档，仅房主可调用）

```ts
import { computed } from 'vue';
import { RoomParticipantRole, useRoomParticipantState } from 'tuikit-atomicx-vue3/room';

const {
  localParticipant,
  setAdmin,
  revokeAdmin,
  transferOwner,
  kickParticipant,
} = useRoomParticipantState();

const hasOwnerPermission = computed(
  () => localParticipant.value?.role === RoomParticipantRole.Owner,
);

const hasAdminPermission = computed(() => {
  const role = localParticipant.value?.role;
  return role === RoomParticipantRole.Owner || role === RoomParticipantRole.Admin;
});

async function setUserAsAdmin(userId: string) {
  if (!hasOwnerPermission.value) return;
  await setAdmin({ userId });
}

async function revokeUserAdmin(userId: string) {
  if (!hasOwnerPermission.value) return;
  await revokeAdmin({ userId });
}

async function transferRoomOwner(userId: string) {
  if (!hasOwnerPermission.value) return;
  await transferOwner({ userId });
}

async function kickUser(userId: string) {
  if (!hasAdminPermission.value) return;
  await kickParticipant({ userId });
}
```

### 单成员设备 / 消息控制（`single-control` 档）

```ts
import { DeviceType, useRoomParticipantState } from 'tuikit-atomicx-vue3/room';

const {
  closeParticipantDevice,
  inviteToOpenDevice,
  disableUserMessage,
} = useRoomParticipantState();

// 关闭指定成员的麦克风 / 摄像头 / 屏幕共享
async function closeUserMicrophone(userId: string) {
  await closeParticipantDevice({ userId, deviceType: DeviceType.Microphone });
}

async function closeUserCamera(userId: string) {
  await closeParticipantDevice({ userId, deviceType: DeviceType.Camera });
}

async function closeUserScreenShare(userId: string) {
  await closeParticipantDevice({ userId, deviceType: DeviceType.ScreenShare });
}

// 邀请成员开启麦克风 / 摄像头 / 屏幕共享
async function inviteUserToOpenCamera(userId: string) {
  await inviteToOpenDevice({
    userId,
    device: DeviceType.Camera,
    timeout: 60,
  });
}

// 单独禁言 / 解禁
async function disableUserChat(userId: string, disable: boolean) {
  await disableUserMessage({ userId, disable });
}
```

### 全员会控（`all-room` 档，房主 / 管理员 toggle）

```ts
import { reactive, watch } from 'vue';
import { DeviceType, useRoomParticipantState, useRoomState } from 'tuikit-atomicx-vue3/room';

const { currentRoom } = useRoomState();
const { disableAllDevices, disableAllMessages } = useRoomParticipantState();

// 管理端按钮状态：必须支持回显，否则刷新后丢失
const moderation = reactive({
  allMicrophoneDisabled: false,
  allCameraDisabled: false,
  allMessagesDisabled: false,
});

watch(
  () => currentRoom.value?.roomId,
  async (roomId) => {
    if (!roomId) {
      moderation.allMicrophoneDisabled = false;
      moderation.allCameraDisabled = false;
      moderation.allMessagesDisabled = false;
      return;
    }
    await hydrateModerationFromBackend(roomId);
  },
  { immediate: true },
);

async function hydrateModerationFromBackend(_roomId: string) {
  // TODO: 从当前房间状态、roomInfo 映射或业务后端 moderation snapshot 恢复三个布尔值。
  // 没有这一步，刷新后管理端按钮会错误显示为"未禁用"，与真实房间规则脱节。
}

async function toggleAllMicrophone() {
  const next = !moderation.allMicrophoneDisabled;
  try {
    await disableAllDevices({ deviceType: DeviceType.Microphone, disable: next });
    moderation.allMicrophoneDisabled = next;
  } catch (error) {
    console.error('切换全员静音失败', error);
  }
}

async function toggleAllCamera() {
  const next = !moderation.allCameraDisabled;
  try {
    await disableAllDevices({ deviceType: DeviceType.Camera, disable: next });
    moderation.allCameraDisabled = next;
  } catch (error) {
    console.error('切换全员禁画失败', error);
  }
}

async function toggleAllMessages() {
  const next = !moderation.allMessagesDisabled;
  try {
    await disableAllMessages({ disable: next });
    moderation.allMessagesDisabled = next;
  } catch (error) {
    console.error('切换全员禁言失败', error);
  }
}
```

### 设备申请审批（`all-room` 档，管理侧）

```ts
import {
  type DeviceRequestInfo,
  DeviceType,
  RoomParticipantEvent,
  useRoomParticipantState,
} from 'tuikit-atomicx-vue3/room';
import { onMounted, onUnmounted } from 'vue';

const {
  pendingDeviceApplications,
  approveOpenDeviceRequest,
  rejectOpenDeviceRequest,
  subscribeEvent,
  unsubscribeEvent,
} = useRoomParticipantState();

function getDeviceName(deviceType: DeviceType) {
  if (deviceType === DeviceType.Microphone) return '麦克风';
  if (deviceType === DeviceType.Camera) return '摄像头';
  return '屏幕分享';
}

async function approveDeviceApplication(application: DeviceRequestInfo) {
  await approveOpenDeviceRequest({
    userId: application.senderUserId,
    device: application.deviceType,
  });
}

async function rejectDeviceApplication(application: DeviceRequestInfo) {
  await rejectOpenDeviceRequest({
    userId: application.senderUserId,
    device: application.deviceType,
  });
}

function onDeviceRequestReceived(info: { request: DeviceRequestInfo }) {
  console.log('收到新的设备申请:', getDeviceName(info.request.deviceType));
}

onMounted(() => {
  subscribeEvent(RoomParticipantEvent.onDeviceRequestReceived, onDeviceRequestReceived);
});

onUnmounted(() => {
  unsubscribeEvent(RoomParticipantEvent.onDeviceRequestReceived, onDeviceRequestReceived);
});
```

### 普通成员申请开启被禁用的设备

```ts
import { DeviceType, useRoomParticipantState } from 'tuikit-atomicx-vue3/room';

const { requestToOpenDevice, cancelOpenDeviceRequest } = useRoomParticipantState();

async function requestToOpenMicrophone() {
  await requestToOpenDevice({ device: DeviceType.Microphone, timeout: 60 });
}

async function cancelMicrophoneRequest() {
  await cancelOpenDeviceRequest({ device: DeviceType.Microphone });
}
```

### 事件监听

```ts
import { onMounted, onUnmounted } from 'vue';
import { RoomParticipantEvent, useRoomParticipantState } from 'tuikit-atomicx-vue3/room';

const { subscribeEvent, unsubscribeEvent } = useRoomParticipantState();

function onKickedFromRoom({ reason, message }) {
  console.warn('当前用户已被移出房间:', reason, message);
}

function onParticipantDeviceClosed({ device, operator }) {
  console.warn('设备已被管理员关闭:', device, operator);
}

onMounted(() => {
  subscribeEvent(RoomParticipantEvent.onKickedFromRoom, onKickedFromRoom);
  subscribeEvent(RoomParticipantEvent.onParticipantDeviceClosed, onParticipantDeviceClosed);
});

onUnmounted(() => {
  unsubscribeEvent(RoomParticipantEvent.onKickedFromRoom, onKickedFromRoom);
  unsubscribeEvent(RoomParticipantEvent.onParticipantDeviceClosed, onParticipantDeviceClosed);
});
```

| **状态 / 事件** | **触发时机** | **处理建议** |
|---|---|---|
| `RoomParticipantEvent.onKickedFromRoom` | 当前用户被移出房间 | 跳转回大厅 / 登录页，并清理会中状态 |
| `RoomParticipantEvent.onParticipantDeviceClosed` | 成员被管理员关闭设备 | toast 告知用户"麦克风 / 摄像头已被管理员关闭" |
| `RoomParticipantEvent.onDeviceRequestReceived` | 管理员收到成员申请 | 展示审批弹窗或申请入口提醒 |
| `RoomParticipantEvent.onDeviceRequestCancelled` | 申请者取消申请 | 移除待处理申请 |
| `RoomParticipantEvent.onDeviceRequestTimeout` | 申请超时 | 提示申请已失效，刷新申请列表 |
| `RoomParticipantEvent.onDeviceRequestApproved` | 申请被批准 | 申请者可继续打开对应设备 |
| `RoomParticipantEvent.onDeviceRequestRejected` | 申请被拒绝 | 申请者展示拒绝提示 |
| `RoomParticipantEvent.onDeviceRequestProcessed` | 申请已被其他管理员处理 | 关闭本地审批入口避免重复处理 |
| `RoomParticipantEvent.onDeviceInvitationReceived` | 成员收到管理员邀请 | 展示接受 / 拒绝入口 |

## 调用时序

```
完成 login-auth 并进入会议
   │
   ▼
读取 localParticipant.role 判断当前用户权限
   │
   ├─ 房主 / 管理员 → 展示治理 + 会控入口（按 management_features 决定哪些档）
   │     │
   │     ├─ list 档（baseline，始终生成）→ 拉成员列表 + 分页 + 排序
   │     ├─ single-control 档 → 关 TA 设备 / 邀请打开 / 单独禁言
   │     ├─ all-room 档 → 全员 toggle + 设备申请审批
   │     └─ role-and-kick 档 → 设管理员 / 转让房主 / 移出成员（带二次确认）
   │
   └─ 普通成员 → 只展示成员列表 + 自己的名片维护 + 设备申请入口
   │
   ▼
所有动作的失败结果（无权限 / 目标已离会 / 申请超时）需要 try/catch 兜底
   │
   ▼
房间级会控状态需要在刷新 / 重进房后从后端 / 房间状态恢复
```

## 平台特有注意事项

### 1. 权限判断要前后端双重收口
前端应先隐藏无权限操作提升体验，但真正的权限校验仍要依赖 SDK / 服务端结果，不能只信任页面按钮状态。

### 2. 房主转移会影响后续治理边界
一旦执行 `transferOwner()`，结束会议、修改规则、全员会控等权限边界都会变化，页面状态必须同步切换。

### 3. 创建期规则与会中会控要分层
默认禁麦、禁聊等会议初始规则属于 `conference/room-lifecycle`；会中动态控制才属于本 slice。

### 4. 房主 / 管理员端的会控按钮必须是 toggle，而不是单向动作
`disableAllDevices()` 与 `disableAllMessages()` 都支持通过 `disable: true / false` 在"开启限制"和"解除限制"之间切换。管理端按钮文案、icon 和二次确认文案应围绕当前状态成对出现。

### 5. 页面刷新或重进房后，要从房间级状态恢复管理端按钮态
本地 `ref` 只适合作为当前页面的 UI cache，不适合作为房间级会控状态的唯一来源。进入会议、管理面板重新挂载或页面刷新后，应从当前房间状态、`roomInfo` 映射或业务后端保存的会控快照中恢复管理端按钮态。

### 6. 被控制方必须得到清晰反馈
远程关闭麦克风、摄像头或禁言后，被控制成员需要在本端看到明确提示，否则很容易误以为是本地故障。

### 7. 设备与共享入口要同时表达"不可用原因"和"恢复方式"
普通成员遇到 `disableAllDevices()` 触发的房间级禁用时，设备或共享按钮不应只做成不可点击的灰态而没有解释；至少应给出 toast 或等价提示，并根据产品需求决定是否在点击时调用 `requestToOpenDevice()`。

### 8. 单成员关闭与房间级禁用的恢复路径不同
`closeParticipantDevice()` 是一次"纠正当前状态"的动作，没有叠加房间级禁用时，成员获得提示后可再次主动开启；房间级禁用期间成员入口应表现为 disabled，按需走申请链路。

### 9. 成员管理适合与业务角色标签联动
若业务有"主持人 / 嘉宾 / 观察员"等角色，建议通过 `metaData` 与会议治理能力协同，而不是在 UI 上维护一套脱节状态。

## 代码生成约束

### 编译必要条件
- **通用条件**：见 [login-auth 平台 slice](login-auth.md)。
- **额外导入**：至少需要导入 `useRoomParticipantState`，按需导入 `DeviceType`、`RoomParticipantRole`、`DeviceStatus`、`RoomParticipantEvent`。
- **运行前提**：当前用户已在会议内，且具备相应角色权限。

### 生成规则

#### MUST（生成时必须包含）

1. **通过 `useRoomParticipantState` 承接所有治理与会控动作** — 成员状态与角色变化才能统一收口。
   **Verify**: 检查是否存在 `useRoomParticipantState()`。
2. **在展示治理 / 会控入口前先读取本地角色状态** — UI 才能与权限边界一致。
   **Verify**: 检查是否存在基于 `localParticipant.role` / `RoomParticipantRole` 的显示判断。
3. **角色管理动作（setAdmin / revokeAdmin / transferOwner）只对房主可见可调** — 严格限定。
   **Verify**: 检查是否存在 `localParticipant.role === RoomParticipantRole.Owner` 的前置判断。
4. **房主 / 管理员端的全员会控按钮必须 toggle，并支持解除** — 不能只展示"全员静音"这类单向动作。
   **Verify**: 检查管理端是否根据当前状态生成"开启限制 / 解除限制"两种文案，且 `disable` 参数会在 `true / false` 之间切换。
5. **管理端会控按钮状态必须从可恢复的房间级状态源初始化或回填** — 页面刷新、重进房后，管理端仍应能回显当前全员规则。
   **Verify**: 检查是否存在初始化 / 恢复房间级会控状态的逻辑（例如基于 `currentRoom` 的 watch + hydrate 函数）。
6. **会控结果要联动到聊天 / 设备 / 共享真实入口** — 否则页面会出现"按钮可点但实际被禁用"的错觉。
   **Verify**: 检查聊天输入区、设备开关按钮、共享入口是否消费了对应禁用状态。
7. **失败兜底处理要覆盖无权限、目标已离会、申请超时等情况** — 接口调用必须 try/catch，不能只信任 UI 显隐。
   **Verify**: 检查是否存在 try/catch + 失败提示。

#### MUST NOT（生成时绝不能出现）

1. **不要把角色治理动作（setAdmin 等）混进纯展示型成员列表组件** — 会破坏列表层与治理层边界。
   **Verify**: 检查治理逻辑是否独立于只读展示层。
2. **不要把全员会控按钮做成只下发 `disable: true` 的单向动作** — 真实产品中的全员静音 / 禁画 / 禁言都应支持解除。
   **Verify**: 检查是否缺少 `disable: false` 的解除路径或等价 toggle 分支。
3. **不要把全员规则状态只存在当前页面内存中** — 页面刷新后会导致管理端 UI 与真实房间规则脱节。
   **Verify**: 检查是否没有任何房间级状态恢复逻辑。
4. **不要在房间级禁用仍生效时让普通成员直接调用开启能力** — 这会绕开会控语义。
   **Verify**: 检查普通成员在全员禁设备 / 禁共享时是否优先走提示或申请链路，而不是直接 `open*` / `unmuteMicrophone()` / `startScreenShare()`。
5. **不要依赖 adminList、本地缓存或展示文案判断角色** — 角色判断应回到 `participant.role` / `localParticipant.role`。
   **Verify**: 检查角色判断是否使用 `RoomParticipantRole` 枚举。
6. **不要把成员级治理和房间级会控写成互不感知的两个模块** — 它们同源、应共享一个治理面板的入口体系。
   **Verify**: 检查 UI 组织是否将"对单成员"与"对全员"清晰分组在同一面板。

### 集成检查点
- 当前 slice 与 `conference/participant-list`、`conference/room-lifecycle`、`conference/room-chat`、`conference/device-control`、`conference/screen-share`、`conference/room-call`、`conference/room-lifecycle` 联动。
- 集成方式通常为新增治理面板（含角色管理、单成员控制、全员会控、设备申请审批四类入口），不需要修改底层会控实现。
- 如果业务存在企业组织权限体系或合规审计要求，建议把重要治理动作同步记录到业务日志系统。

## 验证矩阵

| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已导入 `useRoomParticipantState` / `RoomParticipantRole` / `DeviceType` 等核心依赖 | 检查 `import` 语句 | 治理 + 会控相关 API 与枚举可解析 |
| 2. 静态规则级 | 角色判断、toggle 文案、状态回显与失败兜底齐全 | 搜索角色枚举判断、`disable` toggle 分支、try/catch、`hydrate*` 类恢复逻辑 | 形成"控制 + 感知 + 管理端回显 + 失败处理"闭环 |
| 3. 运行时级 | 治理与会控动作可执行并反馈结果 | 在房主 / 管理员账号下执行操作 | 成功后成员状态刷新；失败时有提示；toggle 可解除 |
| 4. 业务行为级 | 刷新后管理端与被控成员都能看到一致状态 | 刷新管理端页面并用被控制账号观察页面 | 房间级规则不因页面刷新丢失，设备 / 聊天 / 共享入口状态持续正确 |

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 管理入口展示错误 | 普通成员看到了管理员或房主操作入口 | 检查本地角色判断是否基于 `participant.role` / `localParticipant.role`，而不是缓存或展示文案 |
| 设置 / 撤销管理员后标签未更新 | 操作成功后，成员列表仍显示旧角色 | 检查角色变化是否已回流到成员列表与入口显隐逻辑 |
| 房主转移后权限混乱 | 新旧房主的可执行操作没有及时切换 | 检查房主变更后的本地角色刷新和按钮显隐是否同步更新 |
| 移出成员后仍显示在列表中 | 成员已被移出会议，但列表里还存在 | 检查成员离会结果是否已同步到 `participant-list` 和 `room-lifecycle` |
| 成员重新入会后角色异常 | 用户重新进入会议后仍沿用上次角色 | 检查是否错误缓存了临时角色，重新入会应以最新同步角色为准 |
| 会控生效但成员侧无变化 | 已开启全员禁言 / 禁设备 / 禁共享，但成员侧入口仍可用 | 检查聊天、设备、共享模块是否直接消费了会控状态 |
| 单独禁言判定错误 | 房间未全体禁言但某成员不能发消息 | 检查是否存在单独禁言（`disableUserMessage`），不要误判为聊天模块异常 |
| 设备申请长期不收口 | 申请已取消、超时或被他人处理，但界面仍显示待处理 | 检查申请状态是否和超时、取消、已处理结果同步更新 |
| 刷新后管理端按钮状态丢失 | 房间里其实仍处于全员静音 / 禁画 / 禁聊，但房主端按钮又显示成初始态 | 检查管理端按钮是否从房间状态同步结果或业务侧会控快照恢复 |
| 规则与默认配置混淆 | 创建前配置的默认禁麦被误当成会中临时会控 | 检查 `room-lifecycle` 与本 slice 是否做了清晰分层 |

### 排障流程

```text
发现 参会人管理与会控 相关问题
├── 第 1 步：确认问题属于成员级治理、房间级会控、还是创建前默认配置
├── 第 2 步：检查当前用户角色和目标成员角色是否已正确同步
├── 第 3 步：确认设置管理员、移出成员、关闭设备、全员规则、申请 / 邀请等动作的结果是否已回流到成员列表、设备 / 聊天 / 共享入口和提示信息
├── 第 4 步：检查是否错误依赖 adminList、缓存角色或本地写死的管理员数量限制
└── 第 5 步：若仍异常，再回查 participant-list / room-lifecycle / room-chat / device-control / screen-share / room-call / room-lifecycle 的衔接是否正确
```

## 关联知识

- **[conference/participant-list](participant-list.md)** —— 成员治理结果最终会体现在成员列表、角色标签和状态展示上。
- **[conference/room-lifecycle](room-lifecycle.md)** —— 创建前默认规则与会中动态会控应分层。
- **[conference/room-chat](room-chat.md)** —— 消息权限会直接影响聊天输入区和发送链路。
- **[conference/device-control](device-control.md)** —— 设备按钮可用态、管理员关闭设备和申请开启链路与本 slice 联动。
- **[conference/screen-share](screen-share.md)** —— 禁共享、共享关闭和申请 / 邀请链路会直接约束共享能力。
- **[conference/room-call](room-call.md)** —— 谁可以发起邀请、邀请哪些人，往往与角色边界有关。
- **[conference/room-lifecycle](room-lifecycle.md)** —— 移出成员、主动离会和房间结束等结果都会影响成员去留。
