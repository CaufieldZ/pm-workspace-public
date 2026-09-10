---
id: live/gift
name: 礼物
product: live
tags: [gift, send, receive, GiftStore, reward]
platforms: [ios, android, web, flutter]
related: [live/audience-watch, live/barrage]
---

# 礼物

## 功能说明

`GiftStore` 负责礼物面板数据拉取、礼物发送与接收事件处理。礼物列表从服务端拉取（含分类和价格），发送通过 `sendGift` 触发，接收端通过 `giftEventPublisher` 订阅 `.onReceiveGift` 事件驱动动画展示。

**重要**：礼物扣费逻辑必须在**服务端回调**中完成，客户端仅负责 UI 展示，不可在客户端实现扣费。

## 核心概念

| 方法 / 属性 | 说明 |
|-------------|------|
| `GiftStore.create(liveID)` | 创建或获取与指定直播间绑定的单例实例 |
| `refreshUsableGifts` | 从服务端拉取礼物面板所需数据（分类列表 + 礼物详情）；建议在面板展示前调用 |
| `sendGift(giftID, count)` | 发送指定数量的礼物；`count` 为正整数；成功时触发全房间的 `onReceiveGift` 广播 |
| `giftEventPublisher` | 礼物事件发布器；订阅后接收房间内所有礼物事件（含自己发出的） |
| `onReceiveGift` | 礼物事件类型；携带 `liveID`（字符串）、`gift`（Gift 对象）、`count`（正整数）、`sender`（发送者信息） |
| `Gift` | 单个礼物数据模型；含 `giftID`、`name`、`desc`、`iconURL`、`resourceURL`（动画资源）、`level`、`coins`（价格） |
| `GiftCategory` | 礼物分类模型；含 `categoryID`、`name`、`giftList`（Gift 数组） |
| `GiftState` | 礼物模块状态容器；`usableGifts` 为服务端返回的可用礼物分类列表 |
| `setLanguage` | 设置礼物名称/描述的语言（如 `"zh-CN"`、`"en"`）；需在 `refreshUsableGifts` 前调用 |

## 最佳实践

### ✅ ALWAYS

1. **通过 `giftEventPublisher` 处理所有礼物 UI** — 礼物动画、连击计数、弹幕通知等所有 UI 逻辑都应订阅 `giftEventPublisher`。这是唯一能保证接收到所有礼物事件（包括他人发送的）的方式。
2. **`sendGift` 回调仅处理错误** — `sendGift` 的 `completion` 只用于处理发送失败（如余额不足、网络错误）。成功后的礼物展示通过 `giftEventPublisher` 驱动，不要在 `completion` 成功分支里直接更新动画 UI。
3. **面板展示前调用 `refreshUsableGifts`** — 礼物面板打开前先确保数据已拉取。可在进房时预加载，或在面板打开时懒加载，避免面板空白。
4. **多语言场景先调用 `setLanguage`** — 国际化应用中，在 `refreshUsableGifts` 之前调用 `setLanguage`，否则礼物名称显示为默认语言。
5. **礼物扣费通过服务端回调验证** — 客户端 `sendGift` 成功仅表示消息送达，实际扣费和到账须在服务端监听腾讯云礼物回调事件后处理。

### ❌ NEVER

1. **客户端实现扣费逻辑** — 不在客户端直接修改用户余额或金币数量，防止刷礼物作弊。扣费必须通过服务端回调处理。
2. **在 `sendGift` 成功回调中展示动画** — 发送方的 UI 应与接收方保持一致，统一从 `giftEventPublisher` 消费，避免发送方和接收方动画时序不同步。
3. **重复订阅 `giftEventPublisher`** — 每次进房只订阅一次；不要在页面显示等生命周期回调中重复订阅，否则同一礼物会触发多次动画。

## 排障指南

### 常见错误码

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| `-4001` | 余额不足 | 引导用户充值；在 UI 上展示充值入口 |
| `-4002` | 礼物 ID 不存在 | 检查 `giftID` 是否来自 `refreshUsableGifts` 返回的列表 |
| `-1002` | 未登录 | 确保登录成功后再操作 `GiftStore` |
| 网络超时 | 发送超时无回调 | 展示重试按钮；不要自动重试以防重复扣费 |

### 排障流程

```
发送失败
├── -4001 余额不足 → 弹出充值引导
├── -4002 礼物不存在 → 重新调用 refreshUsableGifts 刷新列表
├── 网络错误 → 提示重试；避免自动重发
└── completion 不回调
    └── 检查 GiftStore 对应的 liveID 与当前房间是否一致

giftEventPublisher 不触发
├── 是否建立了订阅？ → 检查事件订阅是否已注册且订阅对象未被释放
├── 发送成功但接收方没收到？
│   ├── 接收方是否在同一房间？
│   └── 订阅时机是否在发送之后？ → 确保进房后立即订阅
└── 发送方自己也没收到？ → 核查 giftEventPublisher 订阅是否正确

余额显示异常
└── 客户端不维护余额，请检查服务端扣费回调逻辑
```

## 关联知识

- **[live/audience-watch](live/audience-watch.md)** — 观众进房后初始化 GiftStore 订阅礼物事件
- **[live/barrage](live/barrage.md)** — 礼物通知可通过弹幕区文本消息展示（BarrageStore 互补）
- **[live/error-codes](live/error-codes.md)** — 完整错误码参考
