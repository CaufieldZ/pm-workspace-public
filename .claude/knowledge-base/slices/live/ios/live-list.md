---
id: live/live-list
platform: ios
---

# 直播列表 — iOS 实现

## 前置条件

**依赖安装（Podfile）**
```ruby
pod 'AtomicXCore', '~> 4.0'
```

**最低系统要求**：iOS 13.0+，Xcode 14.0+

**前置登录**：必须在 `LoginStore.shared.login` 成功回调后才可调用 `fetchLiveList`。

## API 调用（真实签名）

```swift
// 拉取直播列表（分页）
// ⚠️ completion 是 CompletionClosure（Result<Void, ErrorInfo>），列表通过 state 读取
LiveListStore.shared.fetchLiveList(
    cursor: String,            // 首次传 ""，后续传 liveListCursor
    count: Int,                // 每页数量，推荐 20
    completion: CompletionClosure?  // (Result<Void, ErrorInfo>) -> Void
)

// 读取状态快照（Combine）
LiveListStore.shared.state  // StatePublisher<LiveListState>

// 订阅异步事件
LiveListStore.shared.liveListEventPublisher  // PassthroughSubject<LiveListEvent, Never>

// 加入直播间（观众）
// ⚠️ completion 返回 LiveInfo（不是 Void）
LiveListStore.shared.joinLive(liveID: String,
                              completion: LiveInfoCompletionClosure?)
// LiveInfoCompletionClosure = (Result<LiveInfo, ErrorInfo>) -> Void
```

**LiveListState 关键字段**
```swift
struct LiveListState {
    var liveList: [LiveInfo]        // 当前已拉取的直播列表
    var liveListCursor: String      // 下一页游标；"" 表示已到末页
    var currentLive: LiveInfo       // 当前所在直播间的信息
}
```

**LiveListEvent 完整签名**
```swift
enum LiveListEvent {
    case onLiveEnded(liveID: String, reason: LiveEndedReason, message: String)
    case onKickedOutOfLive(liveID: String, reason: LiveKickedOutReason, message: String)
}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `cursor` | `String` | 分页游标；首次传 `""`，末页时 `liveListCursor` 返回 `""` |
| `count` | `Int` | 单次返回条数，建议 20，最大 50 |

**LiveInfo 关键字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| `liveID` | `String` | 直播间唯一 ID |
| `liveName` | `String` | 直播间名称 |
| `coverURL` | `String` | 封面 URL |
| `liveOwner` | `LiveUserInfo` | 主播信息 |
| `seatTemplate` | `SeatLayoutTemplate` | 座位布局模板 |
| `categoryList` | `[NSNumber]` | 分类标签（NSNumber，不是 String） |
| `metaData` | `[String: String]` | 自定义扩展数据 |
| `totalViewerCount` | `Int` | 当前观看人数 |
| `isEmpty` | `Bool` | 直播间是否为空（可用于过滤） |

## 代码示例

```swift
import AtomicXCore
import Combine

var cancellables = Set<AnyCancellable>()

// MARK: - 分页拉取直播列表
// ⚠️ fetchLiveList completion 是 Result<Void, ErrorInfo>
//    列表数据通过 state 读取，不是通过 completion 参数返回

func fetchFirstPage() {
    LiveListStore.shared.fetchLiveList(cursor: "", count: 20) { result in
        switch result {
        case .success:
            // ✅ 拉取成功后，从 state 读取列表
            // （state 是 StatePublisher，可订阅也可直接读当前值）
            observeLiveListState()

        case .failure(let errorInfo):
            print("[LiveList] 拉取失败, code: \(errorInfo.code), msg: \(errorInfo.message)")
        }
    }
}

func fetchMorePages() {
    // 通过 state 读取当前 cursor
    // （StatePublisher 读当前值的方式取决于具体 SDK 实现，此处以 .value 示意）
    // TODO: 待验证 — StatePublisher 读取当前值的具体方式
    let currentCursor = "..." // 从 state.liveListCursor 获取
    guard !currentCursor.isEmpty else {
        print("[LiveList] 已到末页")
        return
    }

    LiveListStore.shared.fetchLiveList(cursor: currentCursor, count: 20) { result in
        switch result {
        case .success:
            print("[LiveList] 更多页拉取成功")
        case .failure(let errorInfo):
            print("[LiveList] 拉取更多失败, code: \(errorInfo.code)")
        }
    }
}

// MARK: - 订阅状态（Combine）

func observeLiveListState() {
    LiveListStore.shared.state
        .receive(on: DispatchQueue.main)
        .sink { liveListState in
            let list   = liveListState.liveList       // [LiveInfo]
            let cursor = liveListState.liveListCursor // String（"" = 末页）
            print("[LiveList] 当前列表数量: \(list.count), 下一页 cursor: \(cursor)")
            // 刷新 UI
        }
        .store(in: &cancellables)
}

// MARK: - 订阅直播事件

func subscribeLiveListEvents() {
    LiveListStore.shared.liveListEventPublisher
        .receive(on: DispatchQueue.main)
        .sink { event in
            switch event {
            // ⚠️ onLiveEnded 三个关联值
            case .onLiveEnded(let liveID, _, _):
                print("[LiveList] 直播 \(liveID) 已结束，从列表移除")

            // ⚠️ onKickedOutOfLive 三个关联值
            case .onKickedOutOfLive(let liveID, let reason, let message):
                print("[LiveList] 被踢出 \(liveID), reason: \(reason), msg: \(message)")
            }
        }
        .store(in: &cancellables)
}

// MARK: - 加入直播间（joinLive 返回 LiveInfo，不是 Void）

func joinLive(liveID: String) {
    // ⚠️ joinLive completion 是 LiveInfoCompletionClosure，返回 LiveInfo
    LiveListStore.shared.joinLive(liveID: liveID) { result in
        switch result {
        case .success(let liveInfo):
            // 成功时回调携带完整 LiveInfo
            print("[LiveList] 进房成功")
            print("[LiveList] 直播间名称: \(liveInfo.liveName)")
            print("[LiveList] 主播: \(liveInfo.liveOwner.userID)")
            // 进房成功后启用弹幕/礼物等功能

        case .failure(let errorInfo):
            print("[LiveList] 进房失败, code: \(errorInfo.code)")
            handleJoinError(errorInfo)
        }
    }
}

// MARK: - 进房错误处理

func handleJoinError(_ errorInfo: ErrorInfo) {
    switch errorInfo.code {
    case -1002: print("请先登录")
    case -2001: print("直播间不存在或已结束")
    default:    print("进房失败（code: \(errorInfo.code)）: \(errorInfo.message)")
    }
}
```

## 调用时序

```
LoginStore.login 成功
    │
    ▼
LiveListStore.shared.fetchLiveList(cursor: "", count: 20) { result in ... }
    │
    ├─ .failure(errorInfo) → 检查登录态 / 网络
    │
    └─ .success
            │
            ▼
    LiveListStore.shared.state 订阅
    读取 liveListState.liveList        ← [LiveInfo]
    读取 liveListState.liveListCursor  ← 下一页游标
            │
            ├─ 渲染列表（reloadData）
            │
            ▼
        用户滑动到底部 → fetchLiveList(cursor: cursor, count: 20)
            │
            └─ .success → state 更新 liveList 和 liveListCursor
            │
            ▼
        用户点击某个直播间
            │
            ▼
        LiveListStore.shared.joinLive(liveID:) { result in ... }
            │
            ├─ .failure(errorInfo) → 展示错误
            └─ .success(liveInfo)  → 进入直播间（启用弹幕/礼物等）
```

## 平台特有注意事项

### 1. fetchLiveList completion 是 `Result<Void, ErrorInfo>`，列表从 state 读取
`fetchLiveList` 的 completion 只表示「请求是否成功」，实际列表数据通过 `LiveListStore.shared.state` 订阅获取：
```swift
// ✅ 正确流程
LiveListStore.shared.fetchLiveList(cursor: "", count: 20) { result in
    if case .success = result {
        // 从 state 读取列表
        subscribeToState()
    }
}

// ❌ 错误：completion 没有 list 参数
LiveListStore.shared.fetchLiveList(cursor: "", count: 20) { result in
    if case .success(let list) = result { ... }  // 编译错误
}
```

### 2. joinLive completion 返回 LiveInfo，不是 Void
`joinLive` 的回调类型是 `LiveInfoCompletionClosure = (Result<LiveInfo, ErrorInfo>) -> Void`，成功时携带直播间完整信息：
```swift
case .success(let liveInfo):  // ✅ liveInfo: LiveInfo
    let ownerID = liveInfo.liveOwner.userID
```

### 3. LiveListEvent 关联值有三个字段
```swift
// ✅ 正确（三个关联值）
case .onLiveEnded(let liveID, let reason, let message):
case .onKickedOutOfLive(let liveID, let reason, let message):

// ❌ 错误（缺少 reason 和 message）
case .onLiveEnded(let liveID):
```

### 4. categoryList 类型是 `[NSNumber]`，不是 `[String]`
```swift
// ✅ 正确
let categories: [NSNumber] = liveInfo.categoryList

// ❌ 错误
let categories: [String] = liveInfo.categoryList  // 类型不匹配
```

### 5. 内存管理：Cell 离屏必须退出直播间
iOS UICollectionView 会缓存离屏 Cell，若不在 `didEndDisplaying` 中调用 `leaveLive`，旧 Cell 的 `LiveCoreView` 会继续解码、占用解码器硬件资源，在直播列表页快速滑动时极易触发内存警告甚至 OOM。
