---
id: live/audience-list
name: 观众列表
product: live
tags: [audience, list, count, LiveAudienceStore]
platforms: [ios, android, web, flutter]
related: [live/audience-watch, live/audience-manage]
---

# 观众列表

## 功能说明

`LiveAudienceStore` 是管理直播间实时观众信息的模块，提供观众列表快照拉取、实时进离场事件订阅以及观众人数展示功能。开发者可用它构建完整的观众列表与人数展示 UI。

核心入口：
- 通过 `LiveAudienceStore` 的 `create` 方法传入 liveID 创建实例
- 调用 `fetchAudienceList` 拉取观众列表快照（通过成功/失败回调获取结果）
- 订阅观众事件获取实时进离场通知

**注意**：`audienceCount` 受每秒 40 条消息的频控限制，高并发场景下人数变更消息可能被丢弃，**仅用于 UI 展示，不可用于精确统计或计费**。

## 核心概念

| 概念 | 说明 |
|------|------|
| **LiveAudienceStore** | 观众信息管理模块，每个直播间通过 `create` 方法传入 liveID 创建独立实例 |
| **LiveUserInfo** | 单个观众数据结构；含 `userID`、`userName`、`avatarURL` 字段 |
| **LiveAudienceState** | 当前状态快照；`audienceList` 为观众数组，`audienceCount` 为总人数 |
| **LiveAudienceEvent** | 实时事件枚举；`.onAudienceJoined` 观众进场，`.onAudienceLeft` 观众离场 |
| **fetchAudienceList** | 主动拉取当前观众列表快照，进房后调用一次获取初始数据 |
| **audienceCount** | 当前观众总数，受频控影响可能不精确，仅用于 UI 展示 |
| **频控 40 条/秒** | 每个直播间每秒最多处理 40 条消息；高并发时人数变更消息优先级低，可能被丢弃 |

## 最佳实践

### ✅ ALWAYS

1. **进房成功后立即调用 fetchAudienceList** — 获取当前观众列表快照作为初始数据，之后通过事件增量更新，避免列表长时间为空。
2. **订阅 LiveAudienceEvent 实时更新列表** — `onAudienceJoined` 时在列表头部插入新观众，`onAudienceLeft` 时移除，保持列表与实际状态同步。
3. **audienceCount 仅用于 UI 展示** — 在观众人数标签上显示近似值可接受；不可将此值用于计费、权限判断或精确统计场景。
4. **直播结束或退出时销毁 audienceStore** — 销毁/释放 `audienceStore` 实例，释放订阅和内部资源，防止内存泄漏。

### ❌ NEVER

1. **依赖 audienceCount 的精确值** — 频控策略（40条/秒）会丢弃低优先级消息，高并发时人数可能滞后或跳变，切勿用此值做业务逻辑判断。
2. **不订阅事件只依赖轮询** — `LiveAudienceStore` 提供推送事件，轮询方式浪费带宽且延迟更高；应通过 `liveAudienceEventPublisher` 订阅增量变化。
3. **进房前调用 fetchAudienceList** — 未进房时调用会返回错误或空数据，必须在 `joinLive` 成功后才可调用。
4. **持有多个相同 liveID 的 LiveAudienceStore 实例** — 重复 `create` 同一 liveID 会导致重复订阅和事件重复处理；每个直播间只创建一个实例。

## 排障指南

### 常见错误码

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| `-1002` | 未登录 | 确保通过 `LoginStore` 登录成功后再操作 |
| 列表返回空 | 正常情况：当前直播间无观众 / 未进房就调用 | 确认已进房；检查是否在 `joinLive.success` 后调用 |
| 人数显示不准确 | 频控丢弃消息（正常现象） | 仅展示，不依赖精确值；可提示"约 X 人在看" |
| 观众列表不更新 | 未订阅观众事件 | 检查事件订阅是否被正确持有（未持有则会立即释放） |

### 排障流程

```
观众列表为空
├── 是否已进房（joinLive.success）？ → 否 → 先进房
├── 是否调用了 fetchAudienceList？ → 否 → 补充调用
├── 调用后仍为空 → 直播间确实无其他观众（正常）
└── 网络问题 → 检查连接

观众进离场后列表不刷新
├── 是否订阅了观众事件？
│       → 否 → 添加订阅
│       → 是 → 检查事件订阅是否被正确持有（未持有则立即释放）
└── 事件回调是否在主线程刷新 UI？ → 否 → 确保切换到主线程再更新 UI

人数跳变 / 不准
└── 正常现象（频控 40 条/秒）
    └── 加"约"字前缀展示即可；不可用于精确业务逻辑
```

## 关联知识

- **[live/audience-watch](live/audience-watch.md)** — 进房观看，是使用观众列表的前提
- **[live/audience-manage](live/audience-manage.md)** — 踢人、设置管理员等管理操作
- **[live/error-codes](live/error-codes.md)** — 完整错误码参考
