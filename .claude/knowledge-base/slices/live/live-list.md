---
id: live/live-list
name: 直播列表
product: live
tags: [list, fetch, category, slide-play, LiveListStore]
platforms: [ios, android, web, flutter]
related: [live/audience-watch, live/login-auth]
---

# 直播列表

## 功能说明

`LiveListStore` 是负责查询直播间列表的全局单例，观众端通过它拉取当前正在开播的直播列表、支持分页加载与分类筛选，并可根据 `seatLayoutTemplateID` 区分语聊房（1–199）与视频直播（200–999）。

核心入口：调用 `LiveListStore` 的 `fetchLiveList` 方法，传入分页游标（cursor）和拉取数量（count），通过成功/失败回调获取结果。

拉取到列表后，将 `liveID` 传给 `LiveCoreView` 实现滑动播放。**每个列表 Cell 必须持有独立的 `LiveCoreView` 实例**，严禁跨 Cell 复用同一实例。

## 核心概念

| 概念 | 说明 |
|------|------|
| **LiveListStore** | 全局单例，负责列表拉取与直播状态监听 |
| **LiveListState** | 当前状态快照；`liveList` 保存已拉取的 `LiveInfo` 列表，`currentLive` 保存正在观看的直播信息 |
| **LiveListEvent** | 异步事件；`onLiveEnded` 表示直播结束，`onKickedOutOfLive` 表示被移出直播间 |
| **LiveInfo** | 单条直播数据；含 `liveID`、`categoryList`、`seatLayoutTemplateID`、`metaData` 等字段 |
| **cursor** | 分页游标字符串；首次请求传空字符串 `""`，后续传上一次返回值；返回空字符串表示已到末页 |
| **count** | 单次拉取数量，推荐值 20，不宜超过 50 |
| **categoryList** | 直播分类标签数组，用于客户端筛选，不参与服务端过滤 |
| **seatLayoutTemplateID** | 房间类型标识；1–199 为语聊房，200–999 为视频直播 |

## 最佳实践

### ✅ ALWAYS

1. **使用 cursor 分页加载** — 首次传 `""`, 每次成功回调后保存返回的新 cursor；当返回 cursor 为空字符串时停止加载更多。
2. **每个滑动列表 Cell 持有独立 LiveCoreView** — 在列表 Cell 初始化时创建 `LiveCoreView` 并添加到视图层级，Cell 间绝不共享实例。
3. **在 Cell 可见/不可见时管理播放生命周期** — Cell 可见时调用 `setLiveID` + 预加载，Cell 不可见时立即停止播放并释放资源，防止内存堆积。
4. **客户端按 seatLayoutTemplateID 或 liveID 前缀过滤** — 服务端不按类型过滤，需在回调中对 `liveList` 做本地筛选再渲染。
5. **订阅 LiveListEvent.onLiveEnded** — 直播结束时及时从列表中移除对应条目并刷新 UI，避免用户点击已结束的直播间。

### ❌ NEVER

1. **一次性拉取全部列表** — 直播间数量可能很大，无分页地全量请求会导致超时与内存压力。
2. **复用同一个 LiveCoreView 给多个 Cell** — 内部状态不可共享，复用会导致画面撕裂、音频冲突或崩溃。
3. **在列表页同时播放多路流** — 滑动列表场景下同时解码多路视频会大幅消耗 CPU/GPU，应确保任意时刻只有当前可见 Cell 在播放。
4. **忽略 onKickedOutOfLive 事件** — 用户被踢出后若不处理，UI 会停留在空播放状态且无任何提示。

## 排障指南

### 常见错误码

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| `-1002` | 未登录 | 确保 `LoginStore` 的 `login` 成功后再调用 `fetchLiveList` |
| 列表返回空 | 正常情况：当前无开播直播 | 展示"暂无直播"空态 UI；检查 categoryList 筛选条件是否过严 |
| 列表卡顿/内存增长 | Cell 复用时 LiveCoreView 未释放 | 在 Cell 不可见时调用停播接口；确认每个 Cell 使用独立实例 |

### 排障流程

```
fetchLiveList 拉不到数据
├── 是否已登录？ → 否 → 先完成 LoginStore.login
├── cursor 是否正确传递？ → 检查首次是否传 ""
├── 网络是否可用？ → 检查连接与防火墙
└── 返回空列表（非错误）→ 当前确实无开播直播，展示空态

列表显示后滑动卡顿
├── 检查每个 Cell 是否独立持有 LiveCoreView
├── 检查 Cell 不可见时是否停播
└── 检查是否在主线程刷新 UI

收到 onLiveEnded / onKickedOutOfLive 后 UI 无变化
└── 确认已订阅 LiveListEvent 并在回调中刷新列表
```

## 关联知识

- **[live/audience-watch](live/audience-watch.md)** — 从列表选中直播间后进房观看
- **[live/login-auth](live/login-auth.md)** — fetchLiveList 需登录态，必须先完成鉴权
- **[live/error-codes](live/error-codes.md)** — 完整错误码参考
