---
id: conference/webinar-interaction
name: Webinar 举手、上台与弹幕互动
product: conference
platform: web
tags: [webinar, raise-hand, audience, participant, barrage, requestToOpenDevice]
platforms: [web]
related: [conference/room-lifecycle, conference/participant-management, conference/room-chat]
---

# Webinar 举手、上台与弹幕互动

## 功能说明

Webinar 互动负责研讨会房型中的观众举手、主持人审批、观众上台成为嘉宾、设备申请收口以及弹幕互动。它解决的是“观众如何申请发言、主持人如何处理申请、观众区如何低成本互动”，不是普通 Standard 会议的成员管理入口。

Conference Core 中，观众举手本质上是 `requestToOpenDevice({ device: DeviceType.Microphone })`；主持人侧通过 `pendingDeviceApplications` 展示待处理申请，接受时先 `promoteToParticipant()`，再 `approveOpenDeviceRequest()`。

## 核心概念

| 能力 | 说明 |
|------|------|
| `RoomType.Webinar` | 研讨会房型，区分房主/管理员、嘉宾和观众 |
| 观众举手 | 观众申请打开麦克风，进入待审批队列 |
| `pendingDeviceApplications` | 主持人或管理员侧看到的设备申请列表 |
| 上台 | 观众被提升为嘉宾/参会人后才能参与发言或开设备 |
| 弹幕 | Webinar 低门槛互动入口，通常基于 live barrage 状态和组件 |
| 禁言联动 | 弹幕输入和普通聊天一样需要联动 `localParticipant.isMessageDisabled` |

## 前置条件

**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`
- Webinar 房间应使用 `RoomType.Webinar` 创建或加入。

## 最佳实践

### ✅ ALWAYS

1. **只在 Webinar 房型中启用举手和弹幕入口** —— Standard 会议优先使用成员管理和会中聊天。
2. **观众端举手用 `requestToOpenDevice({ device: DeviceType.Microphone })`** —— 不要让观众直接 `openLocalMicrophone()` 绕过审批。
3. **主持人接受申请时先上台再批准设备** —— 推荐顺序是 `promoteToParticipant()` → `approveOpenDeviceRequest()`。
4. **拒绝、超时、已批准都要清理观众端举手状态** —— 避免按钮一直显示“已举手”。
5. **弹幕输入必须联动禁言状态** —— `localParticipant.isMessageDisabled` 生效时，输入框和发送链路都要禁用。
6. **弹幕未读数只在面板关闭时累积** —— 打开面板应清零，并在切房间时重置。

### ❌ NEVER

1. **不要把 Webinar 观众当作普通会议成员直接开麦/开摄** —— 观众发言必须经过申请和审批。
2. **不要只批准设备而不提升角色** —— 观众仍可能没有上台权限，导致申请看似通过但设备不可用。
3. **不要把 Webinar 弹幕直接套用普通会议 `GROUP${roomId}` 聊天逻辑** —— Webinar 弹幕应使用 live barrage 能力。

## 代码示例

### 观众举手与取消举手

```ts
import { ref, onMounted, onUnmounted } from 'vue';
import {
  DeviceType,
  RoomParticipantEvent,
  useRoomParticipantState,
} from 'tuikit-atomicx-vue3/room';

const {
  requestToOpenDevice,
  cancelOpenDeviceRequest,
  subscribeEvent,
  unsubscribeEvent,
} = useRoomParticipantState();

const isRaised = ref(false);

export async function toggleRaiseHand() {
  if (isRaised.value) {
    await cancelOpenDeviceRequest({ device: DeviceType.Microphone });
    isRaised.value = false;
    return;
  }

  await requestToOpenDevice({ device: DeviceType.Microphone, timeout: 30 });
  isRaised.value = true;
}

const resetRaised = () => {
  isRaised.value = false;
};

onMounted(() => {
  subscribeEvent(RoomParticipantEvent.onDeviceRequestApproved, resetRaised);
  subscribeEvent(RoomParticipantEvent.onDeviceRequestRejected, resetRaised);
  subscribeEvent(RoomParticipantEvent.onDeviceRequestTimeout, resetRaised);
});

onUnmounted(() => {
  unsubscribeEvent(RoomParticipantEvent.onDeviceRequestApproved, resetRaised);
  unsubscribeEvent(RoomParticipantEvent.onDeviceRequestRejected, resetRaised);
  unsubscribeEvent(RoomParticipantEvent.onDeviceRequestTimeout, resetRaised);
});
```

### 主持人处理举手列表

```ts
import { computed } from 'vue';
import { useRoomParticipantState, type DeviceRequestInfo } from 'tuikit-atomicx-vue3/room';

const {
  pendingDeviceApplications,
  promoteToParticipant,
  approveOpenDeviceRequest,
  rejectOpenDeviceRequest,
} = useRoomParticipantState();

const pendingCount = computed(() => pendingDeviceApplications.value.length);

export async function approveRaiseHand(invitation: DeviceRequestInfo) {
  await promoteToParticipant({ userId: invitation.senderUserId });
  await approveOpenDeviceRequest({
    device: invitation.deviceType,
    userId: invitation.senderUserId,
  });
}

export async function rejectRaiseHand(invitation: DeviceRequestInfo) {
  await rejectOpenDeviceRequest({
    device: invitation.deviceType,
    userId: invitation.senderUserId,
  });
}
```

### Webinar 弹幕入口

```vue
<template>
  <BarrageList class="message-list" />
  <BarrageInput
    class="message-input"
    :disabled="localParticipant?.isMessageDisabled"
  />
</template>

<script setup lang="ts">
import { BarrageInput, BarrageList } from 'tuikit-atomicx-vue3/live';
import { useRoomParticipantState } from 'tuikit-atomicx-vue3/room';

const { localParticipant } = useRoomParticipantState();
</script>
```

## 平台特有注意事项

### 1. 举手不是直接开麦
观众端只发起 `requestToOpenDevice()`，真实上台和设备批准由主持人/管理员处理。不要在观众点击举手后直接调用 `openLocalMicrophone()`。

### 2. 接受申请要处理错误码
嘉宾人数已满或权限不足时，`promoteToParticipant()` / `approveOpenDeviceRequest()` 可能失败。遇到 `ERR_ALL_SEAT_OCCUPIED` 和 `ERR_NO_PERMISSION` 时应给出明确提示。

### 3. 弹幕和普通会议聊天不同源
普通会议聊天使用 `tuikit-atomicx-vue3/chat` 的 `setActiveConversation(GROUP${roomId})`；Webinar 弹幕使用 `tuikit-atomicx-vue3/live` 的 `BarrageList`、`BarrageInput`、`useBarrageState()`。

## 代码生成约束

### MUST

1. **观众举手使用 `requestToOpenDevice({ device: DeviceType.Microphone })`**。  
   **Verify**: 检查是否存在 `requestToOpenDevice`。
2. **主持人接受申请时先 `promoteToParticipant()` 再 `approveOpenDeviceRequest()`**。  
   **Verify**: 检查接受处理函数里的调用顺序。
3. **监听 approved/rejected/timeout 事件重置举手状态**。  
   **Verify**: 检查 `RoomParticipantEvent.onDeviceRequest*` 监听。
4. **Webinar 弹幕使用 live barrage 组件或状态**。  
   **Verify**: 检查是否从 `tuikit-atomicx-vue3/live` 导入 `BarrageInput` / `BarrageList` / `useBarrageState`。

### MUST NOT

1. **不要让观众举手后直接开麦**。  
   **Verify**: 检查观众举手函数中是否直接调用 `openLocalMicrophone()`。
2. **不要用普通会议聊天会话替代 Webinar 弹幕**。  
   **Verify**: Webinar 弹幕代码中不应只出现 `setActiveConversation(GROUP${roomId})`。

## 验证矩阵

| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | Webinar 相关 API 可解析 | 检查 `DeviceType`、`RoomParticipantEvent`、barrage 导入 | 类型可解析 |
| 2. 静态规则级 | 接受举手顺序正确 | 阅读 `approveRaiseHand()` | 先上台再批准设备 |
| 3. 运行时级 | 观众举手和取消可用 | 双账号 Webinar 联调 | 主持人侧出现待处理申请 |
| 4. 业务行为级 | 弹幕禁言联动正确 | 禁言后尝试发送 | 输入或发送被拦截 |

## 排障指南

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 观众举手后主持人看不到 | 待处理列表为空 | 检查是否在 Webinar 房型、是否调用 `requestToOpenDevice()` |
| 主持人同意后观众仍不能发言 | 申请通过但麦克风不可用 | 检查是否先调用 `promoteToParticipant()` 再批准设备 |
| 举手按钮状态不复位 | 拒绝或超时后仍显示已举手 | 监听 approved/rejected/timeout 事件并重置本地状态 |
| 弹幕被禁言仍可输入 | UI 和真实权限不一致 | 绑定 `localParticipant.isMessageDisabled` 并拦截发送 |

## 关联知识

- **[conference/participant-management](participant-management.md)** —— 角色治理 + 全员禁言 / 禁设备等会控规则。
- **[conference/room-chat](room-chat.md)** —— 普通会议聊天，与 Webinar 弹幕需要区分。
