---
id: conference/room-call
name: 会中呼叫
product: conference
platform: web
tags: [call, callUserToRoom, acceptCall, rejectCall, cancelCall]
platforms: [web]
related: [conference/room-lifecycle, conference/participant-management, conference/participant-list]
api_docs:
  - title: 会中呼叫
    url: https://cloud.tencent.com/document/product/647/126929
business_decisions:
  - key: call_target
    tier: blocking
    question: "会中邀请他人加入时，需要支持批量操作吗？"
    options:
      - { label: "仅支持逐个邀请 —— 适合小规模场景", value: "single" }
      - { label: "需要支持批量邀请 —— 适合大型会议或需要同时通知多人的场景（也能单个邀请）", value: "multi" }
  - key: call_permission
    tier: blocking
    question: "谁可以在会议中邀请他人加入？"
    options:
      - { label: "所有参会者都可邀请 —— 开放式", value: "anyone" }
      - { label: "仅主持人 / 管理员可邀请 —— 受控式", value: "admin-only" }
---

# 会中呼叫

## 功能说明

会中呼叫负责房间内对房外用户发起入会呼叫的信令链路，解决呼叫发送、接收、接受、拒绝、取消、超时以及多设备收口问题。它的核心是"呼叫是否跑通"，而不是"呼叫接受后是否已经真正进入房间"。

## 核心概念

### 角色与操作

| 角色 | 关键操作 | 说明 |
|------|----------|------|
| 呼叫发起方 | 发起入会呼叫、取消呼叫 | 通常是房主、管理员或具备权限的会议成员 |
| 被呼叫方 | 接受或拒绝呼叫 | 接受呼叫后，仍需继续进入真实入会流程 |
| 其他设备 | 收口重复处理 | 同一用户多设备在线时，呼叫结果需要统一收敛 |
| 房间生命周期模块 | 承接真实入会 | `acceptCall` 不是最终入会，仍需衔接 `joinRoom` |

### 事件流

| 阶段 | 参与方 | 关键动作 |
|------|--------|----------|
| 发起呼叫 | 呼叫方 | 向指定用户发送入会呼叫 |
| 接收呼叫 | 被呼叫方 | 在常驻监听处收到会中呼叫通知 |
| 用户响应 | 被呼叫方 | 选择接受、拒绝，或等待超时 |
| 结果回传 | 双方 / 其他设备 | 呼叫成功、拒绝、超时、取消、其他设备已处理等状态回传 |
| 真正入会 | 被呼叫方 | 只有在接受呼叫后继续走入房链路，会议才算真正建立 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| 被呼叫用户集合 | 当前呼叫要覆盖的目标用户 |
| 呼叫结果状态 | 接受、拒绝、超时、取消、其他设备已处理等结果 |
| 呼叫上下文 | 用于标识本次呼叫及其结果收口 |
| 房间标识 | 决定呼叫接受后要进入哪一场会议 |
| 当前用户权限 | 决定是否可以对外发起会中呼叫 |

### 状态机

```text
idle
  → calling
  → pending-response
  → accepted
  → joining-room
  → in-room

pending-response
  → rejected
  → timeout
  → cancelled
  → handled-by-other-device
  → idle
```

## 前置条件
**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`

**前置状态**：
- 已阅读 `conference/room-call`，明确当前能力的产品边界。
- 已完成 `conference/login-auth`，确保当前页面具备稳定登录态。
- 已根据业务流程接入会议上下文；需要房间状态时，优先通过 `conference/room-lifecycle` 统一承接。

## 最佳实践

### ✅ ALWAYS

1. **把呼叫确认与真正入会拆成两步** —— 呼叫被接受后，仍应显式进入房间生命周期。
2. **在常驻组件中监听呼叫事件** —— 不要依赖某个临时页面在前台，避免呼叫到达时无人接收。
3. **处理好多设备并发响应的收口** —— 同一用户一台设备接受后，其它设备应同步结束该次呼叫流程。
4. **让呼叫权限与角色治理保持一致** —— 谁能发起呼叫，应和会议中的治理边界同步设计。

### ❌ NEVER

1. **不要把 `acceptCall` 直接当成已经入会成功** —— 不补 `joinRoom`，用户仍不在真实会议上下文中。
2. **不要只处理单设备单用户的理想路径** —— 取消、超时、其他设备已处理同样是主流程。
3. **不要绕过角色权限直接暴露呼叫能力** —— 呼叫权应受成员治理和产品规则约束。

## 代码示例
### 呼叫链路：发起呼叫、接听并进入会议

```ts
import { useRoomState, RoomEvent } from 'tuikit-atomicx-vue3/room';

const { callUserToRoom, acceptCall, joinRoom, subscribeEvent } = useRoomState();

await callUserToRoom({ roomId: 'demo_room', userIdList: ['user_002'], timeout: 60 });

subscribeEvent(RoomEvent.onCallReceived, async ({ roomInfo }) => {
  await acceptCall({ roomId: roomInfo.roomId });
  await joinRoom({
    roomId: roomInfo.roomId,
    roomType: roomInfo.roomType,
    password: roomInfo.password || undefined,
  });
});

subscribeEvent(RoomEvent.onCallTimeout, ({ roomInfo }) => {
  // 收口呼叫弹层或本地呼叫中状态；超时本身不需要再 rejectCall。
  console.info('room call timeout', roomInfo.roomId);
});
```

## 调用时序
```
【呼叫端】
在会议中调用 callUserToRoom({ roomId, userIdList, timeout })
   │
   ▼
被呼叫人收到 RoomEvent.onCallReceived
   │
   ├─ 接受 → acceptCall({ roomId }) → 由当前回调或外层生命周期继续 joinRoom({ roomId, roomType, password })
   ├─ 拒绝 → rejectCall({ roomId })
   ├─ 超时 → onCallTimeout 收口 UI
   └─ 其他设备已处理 → onCallHandledByOtherDevice 收口 UI
```

## 平台特有注意事项
### 1. `acceptCall()` 不等于已经进入会议
接受呼叫只是信令确认；真正进入房间仍需要继续调用 `joinRoom()`。业务可以在 `acceptCall({ roomId })` 后通过自定义回调把 `roomId`、`password`、`roomType` 交给外层入会流程，也可以在同一个事件回调里直接接续 `joinRoom()`。关键是不要把 `acceptCall()` 本身当作"已经进房"。

### 2. 呼叫弹层应统一监听取消、超时与多设备收口
如果只处理收到呼叫和接受，不处理 `onCallCancelled`、`onCallTimeout`、`onCallHandledByOtherDevice`，呼叫 UI 很容易残留。

### 3. `extensionInfo` 适合透传业务字段
呼叫原因、来源场景、优先级、会议主题摘要等字段建议统一放在 `extensionInfo` 或业务补充结构中，而不是在 UI 层硬编码。

## 代码生成约束
### 编译必要条件
- **通用条件**：见 [login-auth 平台 slice](login-auth.md)。
- **额外导入**：至少需要导入 `useRoomState`；如需事件监听，还需导入 `RoomEvent`。
- **运行前提**：当前用户已在会中，且被邀请方具备有效登录态。

### 生成规则
#### MUST（生成时必须包含）

1. **把呼叫确认与真正入会拆成两个阶段** — 才能正确覆盖呼叫确认与实际进房。两阶段可以在同一个回调内串联，也可以通过自定义回调 / 外层生命周期衔接。  
   **Verify**: 检查是否存在 `acceptCall(`，且接受后有继续触发 `joinRoom({ roomId, roomType, password })` 或等价入会流程。
2. **在常驻层监听呼叫事件并收口状态** — 任何页面都应能响应呼叫。  
   **Verify**: 检查是否存在 `subscribeEvent(RoomEvent.onCallReceived, ...)` 或等价监听逻辑。

#### MUST NOT（生成时绝不能出现）

1. **不要把 `acceptCall()` 当作最终进房动作** — 会造成"已接听但未进房"的悬空状态。
2. **不要忽略取消、超时和多设备处理事件** — 呼叫弹窗容易残留。  
   **Verify**: 检查是否存在对应事件或兜底清理说明。

### 集成检查点
- 当前 slice 常与 `conference/room-lifecycle`、`conference/participant-management` 联动。
- 集成通常表现为会中呼叫弹层和常驻呼叫监听组件。
- 若业务侧还有站内信或电话提醒，需要明确多种通知渠道之间的优先级和收口策略。

## 验证矩阵
| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已导入 `useRoomState` 与 `RoomEvent` | 检查 `import` 语句 | 呼叫相关 API 与事件可解析 |
| 2. 静态规则级 | 接受呼叫后继续进房 | 搜索 `acceptCall` 与 `joinRoom` 或外层入会回调 | 存在两阶段链路 |
| 3. 运行时级 | 收到呼叫后可接受并进入会议 | 双账号联调呼叫流程 | 接收端可成功进房 |
| 4. 业务行为级 | 取消 / 超时 / 多设备处理时 UI 正确收口 | 模拟各种呼叫结果 | 呼叫弹层不会残留 |

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 接受呼叫后未真正入会 | 用户点击接受，但页面没有进入会议 | 检查是否在接受呼叫后继续衔接 `joinRoom` 主链路 |
| 呼叫通知收不到 | 房外用户在线，但没有弹出呼叫提示 | 检查呼叫监听是否放在常驻位置，避免页面切换后监听被释放 |
| 多设备状态不一致 | 一台设备已接受，另一台仍显示待处理 | 检查是否处理了“其他设备已处理”这类收口事件 |

### 排障流程

```text
发现 会中呼叫 相关问题
├── 第 1 步：确认问题属于呼叫信令链路，而不是房间生命周期本身
├── 第 2 步：检查呼叫监听是否常驻，并能接收接受、拒绝、超时、取消等结果
├── 第 3 步：确认 acceptCall 之后是否继续触发 joinRoom，完成真实入会
└── 第 4 步：若仍异常，再回查 room-lifecycle / participant-management / participant-list 的衔接是否正确```

## 关联知识

- **[conference/room-lifecycle](room-lifecycle.md)** —— 呼叫接受后，真正的入会仍由房间生命周期承接。
- **[conference/participant-management](participant-management.md)** —— 谁有权发起呼叫，通常受会议角色治理约束。
- **[conference/participant-list](participant-list.md)** —— 被呼叫人真正进房后，才会进入成员列表读模型。