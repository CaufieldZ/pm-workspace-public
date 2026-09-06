---
id: live/barrage
name: 弹幕
product: live
tags: [barrage, message, chat, mute, BarrageStore, danmu]
platforms: [ios, android, web, flutter]
related: [live/audience-watch, live/audience-manage]
---

# 弹幕

## 功能说明

`BarrageStore` 是直播间弹幕/聊天的核心模块，负责文本消息与自定义消息的收发、本地提示插入，以及用户禁言管理。所有弹幕消息通过 `BarrageState.messageList` 统一分发，UI 层订阅该状态进行渲染。

`BarrageStore` 实例与直播间 `liveID` 绑定，相同 `liveID` 的多次 `create` 调用返回同一实例。

## 核心概念

| 方法 / 属性 | 说明 |
|-------------|------|
| `BarrageStore.create(liveID)` | 创建或获取与指定直播间绑定的单例实例 |
| `sendTextMessage(text, extensionInfo)` | 向房间内所有用户广播纯文本弹幕；`extensionInfo` 可附加扩展字段；通过成功/失败回调返回结果 |
| `sendCustomMessage(businessID, data)` | 发送自定义业务消息；`data` 为 JSON 格式字符串，`businessID` 区分消息类型；通过成功/失败回调返回结果 |
| `appendLocalTip(message)` | 向本地消息列表插入仅本端可见的系统提示，不广播给其他用户 |
| `disableSendMessage(userID, isDisable)` | 对指定用户单独禁言（`true`）或解除禁言（`false`）；状态在用户重新进房后仍生效；通过成功/失败回调返回结果 |
| `Barrage` | 单条弹幕数据模型；包含发送者信息、`textContent` / `data` 内容、`messageType` 分类 |
| `BarrageState` | 弹幕模块状态容器；`messageList` 是 UI 渲染的唯一数据源 |
| `BarrageState.messageList` | 按时间排序的完整消息数组；SDK 每次更新时下发完整列表 |

> **全员禁言**：通过 `LiveListStore` 的 `updateLiveInfo` 方法（设置 `modifyFlag` 为 `isMessageDisable`）控制，与 `disableSendMessage` 是不同接口，作用范围不同。

## 最佳实践

### ✅ ALWAYS

1. **批处理更新（300ms 节流）** — 高并发弹幕场景下 SDK 可能以 30+ 次/秒的频率下发更新。务必对 `messageList` 变化做 300ms 节流处理，将刷新频率降至 3~4 次/秒，避免主线程过载。
2. **循环缓冲限制消息上限（500 条）** — 长时间直播中 `messageList` 会持续增长。在 UI 层维护一个固定大小（推荐 500 条）的循环缓冲区，超出后丢弃最旧消息，防止内存无限膨胀。
3. **启用异步渲染优化** — 弹幕 Cell 开启异步渲染，将绘制工作移至后台线程，主线程只做布局，显著降低掉帧率。
4. **`appendLocalTip` 用于系统通知** — 用户进入/离开直播间、礼物特效等本地通知使用 `appendLocalTip` 插入，无需走网络，也不污染其他用户视图。
5. **`sendCustomMessage` 携带 businessID** — 自定义消息务必设置清晰的 `businessID`（如 `"gift_notify"`、`"like_action"`），接收端通过 `businessID` 过滤处理，避免业务逻辑混淆。

### ❌ NEVER

1. **每条弹幕到达立即刷新 UI** — 不做节流直接刷新列表，高峰期会造成 UI 卡顿甚至 ANR。
2. **无限累积消息到内存** — 不对 `messageList` 做截断，长播场景下内存占用会线性增长直至被系统终止。
3. **在非主线程直接操作 UI** — 订阅 `messageList` 变化后，确保所有 UI 操作切换到主线程执行。
4. **用 `appendLocalTip` 替代网络消息** — `appendLocalTip` 只在本地生效，不要用它发送需要其他用户看到的消息。

## 排障指南

### 常见错误码

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| `-2380` | 全员禁言（房主已开启全局禁言） | UI 提示"直播间已开启全员禁言"，隐藏发送入口 |
| `-2381` | 当前用户已被单独禁言 | UI 提示"您已被禁止发言"，隐藏发送入口 |
| `-2382` | 消息内容违规（敏感词过滤） | 提示用户修改内容后重试 |
| `-1002` | 未登录即调用 | 确保 `LoginStore` 登录成功后再初始化 `BarrageStore` |

### 排障流程

```
弹幕不显示
├── messageList 有数据但 UI 不更新
│   ├── 是否在主线程更新 UI？ → 确保 UI 操作在主线程执行
│   └── 是否未订阅 BarrageState？ → 检查状态订阅是否建立
├── messageList 始终为空
│   ├── BarrageStore.create(liveID) 的 liveID 是否与进房 ID 一致？
│   └── 登录态是否正常？ → 检查 LoginStore 的 isLogin 状态
└── 历史消息不显示
    └── BarrageStore 创建时机太晚 → 在进房前创建实例以接收历史消息

发送失败
├── -2380 全员禁言 → 检查 LiveListStore.liveInfo.isMessageDisable
├── -2381 已被禁言 → 检查当前用户禁言状态
├── -2382 内容违规 → 提示用户修改内容
├── 网络错误 → 检查网络连接，retry 1次
└── completion 一直不回调
    └── 检查 liveID 对应的房间是否存在且已加入
```

## 关联知识

- **[live/audience-watch](live/audience-watch.md)** — 观众进房后需初始化 BarrageStore 接收弹幕
- **[live/audience-manage](live/audience-manage.md)** — 禁言用户依赖管理员/房主权限
- **[live/gift](live/gift.md)** — 礼物通知常通过弹幕区展示
- **[live/error-codes](live/error-codes.md)** — 完整消息错误码参考
