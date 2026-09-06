---
id: live/audience-watch
name: 观众观看
product: live
tags: [audience, watch, join, leave, playView, LiveCoreView]
platforms: [ios, android, web, flutter]
related: [live/live-list, live/login-auth, live/barrage, live/gift]
---

# 观众观看

## 功能说明

观众通过 `LiveCoreView` 进入直播间并拉流观看。整个流程围绕三个核心 API：`setLiveID` 绑定直播间、`joinLive` 进房拉流、`leaveLive` 退出释放资源。

核心入口：依次调用 `LiveCoreView` 的 `setLiveID` 绑定直播间、`joinLive` 进房拉流、`leaveLive` 退出释放资源。每个方法通过成功/失败回调返回结果。

观众使用 `.playView` 视图类型，只拉流不推流，不会触发摄像头/麦克风权限申请。被踢出直播间时会收到 `onKickedOutOfLive` 事件，必须监听并处理。

## 核心概念

| 概念 | 说明 |
|------|------|
| **LiveCoreView** | 直播核心视图组件，封装了拉流、连麦、礼物等所有 UI 与逻辑 |
| **.playView** | 观众视图类型，仅拉取主播视频流，不启用摄像头或麦克风 |
| **setLiveID** | 绑定目标直播间 ID，必须在 `joinLive` 之前调用 |
| **joinLive** | 进入直播间并开始拉流；成功回调后才可使用弹幕、礼物等功能 |
| **leaveLive** | 退出直播间并释放所有媒体资源；页面销毁时必须调用 |
| **onKickedOutOfLive** | 观众被主播或管理员移出直播间时触发的事件 |

## 最佳实践

### ✅ ALWAYS

1. **joinLive 之前必须调用 setLiveID** — `LiveCoreView` 需要先知道目标直播间才能建立连接，顺序错误会导致进房失败或黑屏。
2. **在 joinLive 成功回调后再启用其他功能** — 弹幕发送、礼物、连麦申请等均依赖进房成功的会话上下文，提前调用会报未进房错误。
3. **退出时先断开连麦再 leaveLive** — 若观众正处于连麦状态，直接调用 `leaveLive` 会残留上行流；应先调用连麦断开接口（`disConnect`），待回调后再 `leaveLive`。
4. **处理 onKickedOutOfLive 事件** — 收到此事件后立即退出播放页、清理 `LiveCoreView`，并向用户展示提示（如"您已被移出直播间"）。
5. **App 进入后台时清理播放资源** — 系统在 App 后台时间过长后可能回收媒体资源，应在 App 切到后台时停播，切回前台时重新进房或恢复。

### ❌ NEVER

1. **在 joinLive 成功前操作直播功能** — 弹幕、礼物、连麦等功能必须等待 `joinLive` 的成功回调，不可在进房请求未完成时调用。
2. **忘记调用 leaveLive** — 若页面销毁时未调用 `leaveLive`，媒体流不会释放，占用带宽与解码资源，还会导致后续进房冲突。
3. **将同一个 LiveCoreView 复用给不同直播间** — 应在每次进新直播间前销毁旧实例，或在 `leaveLive` 成功后重新 `setLiveID`，不可不退房直接绑定新 ID。
4. **忽略进房失败** — 网络抖动、直播间已结束等原因均可导致 `joinLive` 失败，必须在失败回调中处理并给用户反馈。

## 排障指南

### 常见错误码

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| `-1002` | 未登录 | 确保 `LoginStore` 的 `login` 成功后再进房 |
| `-2001` | 直播间不存在 / 已结束 | 直播已下播，返回列表页并刷新 |
| `-2003` | 重复进房 | 调用 `leaveLive` 后再重新 `joinLive` |
| 黑屏但无错误码 | `setLiveID` 未在 `joinLive` 前调用 | 检查调用顺序：setLiveID → joinLive |
| 被踢后 UI 无响应 | 未订阅 `onKickedOutOfLive` | 注册事件监听，收到事件后执行退出逻辑 |

### 排障流程

```
进房后黑屏
├── 是否先调用了 setLiveID？ → 否 → 补充调用，重新进房
├── joinLive 是否返回成功？ → 否 → 查看错误码
│       ├─ -1002 → 先登录
│       ├─ -2001 → 直播已结束，返回列表
│       └─ -2003 → 先 leaveLive 再 joinLive
└── 成功但画面黑 → 检查 .playView 是否已添加到视图层级且尺寸非零

被踢出后没有提示
└── 确认已订阅 onKickedOutOfLive 并在回调中执行退出 + Toast

退出页面后内存/CPU 未下降
└── 确认页面销毁时已调用 leaveLive
    └── 若处于连麦状态 → 先 disConnect → 再 leaveLive
```

## 关联知识

- **[live/live-list](live/live-list.md)** — 从直播列表获取 liveID 后进入观看
- **[live/login-auth](live/login-auth.md)** — 进房前必须完成登录鉴权
- **[live/barrage](live/barrage.md)** — 进房成功后可使用弹幕功能
- **[live/gift](live/gift.md)** — 进房成功后可发送礼物
- **[live/error-codes](live/error-codes.md)** — 完整错误码参考
