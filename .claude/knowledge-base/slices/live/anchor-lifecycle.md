---
id: live/anchor-lifecycle
name: 主播开播与结束生命周期
product: live
tags: [anchor, start, end, createLive, endLive, lifecycle]
platforms: [ios, android, web, flutter]
related: [live/anchor-room-config, live/anchor-preview, live/device-control]
---

# 主播开播与结束生命周期

## 功能说明

主播的完整生命周期包含两个核心动作：

- **`createLive`**：在服务端创建直播间并开始推流，观众可加入收看。
- **`endLive`**：结束直播、销毁服务端房间、停止推流。

除主动结束外，还需监听 `liveListEventPublisher` 处理**被动结束**场景（如被踢出、网络异常等）。生命周期管理的正确性直接影响房间资源释放和用户体验。

## 核心概念

### createLive

调用 `LiveListStore` 的 `createLive` 方法，传入直播信息对象，通过成功/失败回调获取结果。

| 行为 | 说明 |
|------|------|
| 创建服务端房间 | 以 `liveID` 为唯一标识在服务端创建直播间 |
| 开始推流 | 将本地摄像头/麦克风数据推送到 CDN |
| 生成直播列表条目 | 直播间出现在观众的直播列表中 |

**前置条件**：摄像头已打开（`openLocalCamera` 成功）+ `LiveInfo` 已配置。

### endLive

调用 `LiveListStore` 的 `endLive` 方法，传入直播间 ID，通过成功/失败回调获取结果。

| 行为 | 说明 |
|------|------|
| 通知所有观众直播结束 | 触发观众端 `onLiveEnded` 事件 |
| 销毁服务端房间 | 房间从直播列表消失 |
| 停止推流 | 本地推流通道关闭 |

### 被动结束事件（liveListEventPublisher）

通过订阅 `LiveListStore` 的直播列表事件监听以下事件：

| 事件 | 触发场景 | 处理建议 |
|------|----------|----------|
| `onLiveEnded(liveID:)` | 直播被服务端强制结束 / 主播在其他设备调用 endLive | 清理 UI，提示用户直播已结束 |
| `onKickedOutOfLive(liveID:reason:)` | 主播被管理员踢出直播间 | 显示踢出原因，释放资源，返回首页 |

### 正确的结束顺序

直播中可能存在 PK（跨房连麦）、连线（观众上麦）、连麦等子会话，结束时必须按以下顺序操作，避免资源未释放：

```
1. 结束 PK（如有）         → endPK()
2. 断开连线（如有）        → disconnectLink()
3. 断开连麦（如有）        → stopCoguest()
4. 关闭摄像头/麦克风       → 通过 DeviceStore 关闭本地摄像头和麦克风
5. 结束直播               → 通过 LiveListStore 调用 endLive，传入 liveID
6. 销毁 LiveCoreView       → 仅在 endLive 回调成功后
```

## 最佳实践

### ✅ ALWAYS

1. **严格遵守结束顺序** — 先结束所有子会话（PK → 连线 → 连麦），再关闭设备，最后调 `endLive`。乱序操作会导致远端用户状态异常或推流未真正停止。
2. **监听 `onLiveEnded` 事件** — 直播可能因网络问题、服务端策略或管理员操作而被动结束；监听此事件以保证 UI 和资源的正确清理。
3. **在 `endLive` 回调成功后才释放 `LiveCoreView`** — 回调前释放会导致内部推流管道异常，可能产生残留连接。
4. **`createLive` 成功后再更新 UI 状态** — 创建是异步操作，在回调成功前不应向用户展示「正在直播」状态。

### ❌ NEVER

1. **`endLive` 回调前释放 `LiveCoreView`** — 视图持有底层推流资源；过早释放会导致 crash 或资源泄漏。
2. **忽略 `onKickedOutOfLive` 事件** — 未处理此事件时，被踢出的主播仍停留在「直播中」界面，用户体验极差，且推流资源无法释放。
3. **重复调用 `createLive`** — 同一 `liveID` 已存在直播间时再次调用会返回 `-2108`；用唯一 ID 或先调 `endLive` 销毁后再创建。
4. **在子线程更新 UI** — `createLive` / `endLive` 的回调应在主线程处理 UI 变更；若不确定回调线程，确保切换到主线程再更新 UI。

## 排障指南

### 常见错误码

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| `-2105` | 直播间 ID 非法 | `liveID` 须为 ASCII 字符且长度 ≤ 48 字节 |
| `-2107` | 直播间名称非法 | `liveName` 须为合法 UTF-8 且长度 ≤ 30 字节 |
| `-2108` | 已在其他直播间 | 先调用 `endLive` / `leaveLive` 退出当前房间再重试 |
| `-2300` | 权限不足 | 操作需要房主权限（如 endLive 只有创建者可调用） |

### 排障流程

```
createLive 失败
├── 错误码 -2105 → liveID 含非法字符或超长，修正后重试
├── 错误码 -2107 → liveName 超 30 字节，截短后重试
├── 错误码 -2108 → 已在房间，先 endLive 退出再创建
└── 其他错误    → 检查网络连接；抓取 error.message 上报

endLive 无响应 / 超时
├── 是否已有网络连接？→ 检查网络后重试
├── 是否在子线程调用了 UI 操作？→ 移至主线程
└── LiveCoreView 是否被提前释放？→ 确保在回调后才销毁视图

主播被踢出后推流未停止
└── 检查是否订阅了 onKickedOutOfLive
    └── 订阅后调用正确结束顺序释放资源

观众收不到 onLiveEnded 通知
└── 检查主播是否调用了 endLive（而非直接 kill 进程）
    └── 若 App 被强杀，服务端会在超时后自动触发房间销毁
```

## 关联知识

- **[live/anchor-room-config](live/anchor-room-config.md)** — createLive 所需的 LiveInfo 配置
- **[live/anchor-preview](live/anchor-preview.md)** — createLive 前的摄像头预览准备
- **[live/device-control](live/device-control.md)** — 设备开关与结束顺序
- **[live/error-codes](live/error-codes.md)** — 完整错误码参考
