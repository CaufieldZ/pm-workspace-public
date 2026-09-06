---
id: live/audience-watch
platform: ios
---

# 观众观看 — iOS 实现

## 前置条件

**依赖安装（Podfile）**
```ruby
pod 'AtomicXCore', '~> 4.0'
```

**最低系统要求**：iOS 13.0+，Xcode 14.0+

**前置登录**：必须在 `LoginStore.shared.login` 成功后才可调用 `joinLive`。

**权限说明**：观众使用 `.playView` 仅拉流，**无需**申请摄像头/麦克风权限。若观众发起连麦则需相机与麦克风权限（参见 live/device-control）。

## API 调用（真实签名）

```swift
// LiveCoreView 初始化：观众端用 .playView（拉流模式）
// 参数名是 viewType（不是 liveScene）
LiveCoreView(viewType: .playView, frame: CGRect = .zero)

// 加入直播间并开始拉流
// ⚠️ completion 返回 LiveInfo（不是 Void）
LiveListStore.shared.joinLive(liveID: String,
                              completion: LiveInfoCompletionClosure?)
// LiveInfoCompletionClosure = (Result<LiveInfo, ErrorInfo>) -> Void

// 离开直播间并释放媒体资源
LiveListStore.shared.leaveLive(completion: CompletionClosure?)
// CompletionClosure = (Result<Void, ErrorInfo>) -> Void

// 订阅直播事件（Combine）
LiveListStore.shared.liveListEventPublisher  // PassthroughSubject<LiveListEvent, Never>
```

**LiveListEvent 完整签名**
```swift
enum LiveListEvent {
    // 直播结束（主播主动结束 / 服务端强制终止）
    case onLiveEnded(liveID: String, reason: LiveEndedReason, message: String)

    // 被踢出直播间（管理员操作）
    case onKickedOutOfLive(liveID: String, reason: LiveKickedOutReason, message: String)
}
```

**通用类型**
```swift
typealias CompletionClosure         = (Result<Void, ErrorInfo>) -> Void
typealias LiveInfoCompletionClosure = (Result<LiveInfo, ErrorInfo>) -> Void

struct ErrorInfo {
    var code: Int
    var message: String
}
```

## 代码示例

```swift
import AtomicXCore
import Combine

var cancellables = Set<AnyCancellable>()
var isInLive = false

// MARK: - 进入直播间（joinLive）

func joinLive(liveID: String) {
    // ⚠️ joinLive completion 是 LiveInfoCompletionClosure，成功时返回 LiveInfo
    LiveListStore.shared.joinLive(liveID: liveID) { result in
        switch result {
        case .success(let liveInfo):
            isInLive = true
            print("[AudienceWatch] 进房成功: \(liveID)")
            print("[AudienceWatch] 直播间名称: \(liveInfo.liveName)")
            print("[AudienceWatch] 主播: \(liveInfo.liveOwner.userID)")
            // 进房成功后启用弹幕/礼物等功能

        case .failure(let errorInfo):
            // errorInfo: ErrorInfo（.code + .message）
            print("[AudienceWatch] 进房失败, code: \(errorInfo.code), msg: \(errorInfo.message)")
            handleJoinError(errorInfo)
        }
    }
}

// MARK: - 离开直播间（leaveLive）

func leaveLive() {
    guard isInLive else { return }
    isInLive = false

    // ⚠️ leaveLive completion 是 CompletionClosure（Result<Void, ErrorInfo>）
    LiveListStore.shared.leaveLive { result in
        switch result {
        case .success:
            print("[AudienceWatch] 退出直播间成功")
        case .failure(let errorInfo):
            // 即使失败也清理本地状态，避免残留
            print("[AudienceWatch] 退出直播间失败, code: \(errorInfo.code)")
        }
        cleanupSubscriptions()
    }
}

// MARK: - 订阅直播事件（先订阅再 joinLive，防止事件丢失）

func subscribeLiveEvents(currentLiveID: String) {
    LiveListStore.shared.liveListEventPublisher
        .receive(on: DispatchQueue.main)
        .sink { event in
            switch event {
            // ⚠️ onLiveEnded 有三个关联值：liveID, reason, message
            case .onLiveEnded(let liveID, _, let message)
                where liveID == currentLiveID:
                print("[AudienceWatch] 直播已结束: \(message)")
                handleLiveEnded()

            // ⚠️ onKickedOutOfLive 有三个关联值：liveID, reason, message
            case .onKickedOutOfLive(let liveID, _, let message)
                where liveID == currentLiveID:
                print("[AudienceWatch] 被踢出直播间: \(message)")
                handleKickedOut()

            default:
                break
            }
        }
        .store(in: &cancellables)
}

// MARK: - 事件处理

func handleLiveEnded() {
    isInLive = false
    cleanupSubscriptions()
    print("[AudienceWatch] 直播已结束，返回列表")
}

func handleKickedOut() {
    isInLive = false
    cleanupSubscriptions()
    print("[AudienceWatch] 您已被移出直播间")
}

// MARK: - 进房错误处理

func handleJoinError(_ errorInfo: ErrorInfo) {
    switch errorInfo.code {
    case -1002: print("请先登录后再进入直播间")
    case -2001: print("直播间不存在或已结束")
    default:    print("进房失败（code: \(errorInfo.code)）: \(errorInfo.message)")
    }
}

// MARK: - 清理订阅

func cleanupSubscriptions() {
    cancellables.removeAll()
}
```

**完整进房 + 退房流程**：
```swift
// ① 先订阅事件（防止进房前的事件丢失）
subscribeLiveEvents(currentLiveID: liveID)

// ② 进入直播间
joinLive(liveID: liveID)

// ③ 退出时（页面消失、收到 onLiveEnded / onKickedOutOfLive）
leaveLive()
```

**App 生命周期处理**：
```swift
import Combine

func observeAppLifecycle(liveID: String) {
    // 进入后台：停止拉流，避免后台占用解码资源
    NotificationCenter.default.publisher(for: UIApplication.didEnterBackgroundNotification)
        .sink { _ in
            // 若业务要求后台不能播放，调用 leaveLive 并在前台重新 joinLive
            // leaveLive()
        }
        .store(in: &cancellables)

    // 回到前台：恢复播放
    NotificationCenter.default.publisher(for: UIApplication.willEnterForegroundNotification)
        .sink { _ in
            // 如已调用 leaveLive，需重新 joinLive
            // joinLive(liveID: liveID)
        }
        .store(in: &cancellables)
}
```

## 调用时序

```
LoginStore.login 成功
    │
    ▼
subscribeLiveEvents(currentLiveID:)    ← ① 先订阅，防止事件丢失
    │
    ▼
LiveListStore.shared.joinLive(liveID: String, completion: LiveInfoCompletionClosure?)
    │
    ├─ .failure(errorInfo)
    │       ├─ code -1002 → 先登录
    │       ├─ code -2001 → 直播已结束 → 返回列表
    │       └─ 其他       → showAlert（code + message）
    │
    └─ .success(liveInfo)   ← 携带完整 LiveInfo
            │
            isInLive = true
            启用弹幕/礼物功能
            │
            ▼
        ┌──────────────────────────────────┐
        │         直播进行中               │
        │  onLiveEnded(liveID,reason,msg)  │
        │  onKickedOutOfLive(liveID,r,msg) │
        └──────────────────────────────────┘
            │
            [用户退出 / 收到事件]
            │
            ▼
LiveListStore.shared.leaveLive(completion: CompletionClosure?)
    │
    ├─ .success / .failure  → 清理本地状态（无论成功失败都 cleanup）
    │
    ▼
cancellables.removeAll()
```

## 平台特有注意事项

### 1. joinLive completion 返回 LiveInfo，不是 Void
```swift
// ✅ 正确
LiveListStore.shared.joinLive(liveID: liveID) { result in
    if case .success(let liveInfo) = result {
        print(liveInfo.liveName)  // 使用服务端返回的 LiveInfo
    }
}

// ❌ 错误：completion 没有直接的 list/room 参数
```

### 2. leaveLive completion 是 `Result<Void, ErrorInfo>`
`leaveLive` 回调是 `CompletionClosure`（`Result<Void, ErrorInfo>`），即使失败也应清理本地状态：
```swift
LiveListStore.shared.leaveLive { result in
    // 无论 .success 还是 .failure，都需要清理本地状态
    isInLive = false
    cancellables.removeAll()
}
```

### 3. LiveListEvent 关联值有三个字段
```swift
// ✅ 正确
case .onLiveEnded(let liveID, let reason, let message):
case .onKickedOutOfLive(let liveID, let reason, let message):

// ❌ 错误（只有一个关联值）
case .onLiveEnded(let liveID):
case .onKickedOutOfLive(let liveID):
```

### 4. viewDidDisappear vs deinit 中调用 leaveLive
建议在 `viewDidDisappear` 中调用而非 `deinit`，原因：iOS push/pop 导航栈时，上级页面不会被销毁（`deinit` 不调用），但 `viewDidDisappear` 会触发。如在 `deinit` 中释放，可能导致用户返回列表后资源未释放直到页面从栈中弹出。

### 5. 强引用导致 LiveCoreView 无法释放
若闭包中捕获 `self` 导致循环引用，`leaveLive` 的回调永远不执行。始终使用 `[weak self]` 捕获 ViewController 引用。

### 6. 后台播放与 App Store 合规
若 App 允许后台音频播放，需在 `Info.plist` 的 `UIBackgroundModes` 中声明 `audio`，否则 App 进入后台后音频会被系统静音，且审核可能被拒。若不支持后台播放，进后台时调用 `leaveLive` 是更安全的选择。
