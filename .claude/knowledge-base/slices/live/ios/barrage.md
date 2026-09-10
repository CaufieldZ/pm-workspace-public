---
id: live/barrage
platform: ios
---

# 弹幕 — iOS 实现

## 前置条件

**依赖安装（Podfile）**
```ruby
pod 'AtomicXCore', '~> 4.0'
```

**前置状态**：
- `LoginStore.shared.isLogin == true`（弹幕依赖登录态）
- 已成功加入直播间（房间 ID 即 `liveID`）

## API 调用

```swift
// 创建弹幕实例（与直播间绑定）
let barrageStore = BarrageStore.create(liveID: liveID)

// 发送文本弹幕
// ⚠️ extensionInfo 类型为 [String: String]?，不是 [String: Any]?
barrageStore.sendTextMessage(
    text: String,
    extensionInfo: [String: String]?,
    completion: CompletionClosure?
)
// CompletionClosure = (Result<Void, ErrorInfo>) -> Void

// 发送自定义消息
barrageStore.sendCustomMessage(
    businessID: String,
    data: String,          // JSON 字符串
    completion: CompletionClosure?
)

// 插入本地提示（不广播，仅当前客户端可见）
barrageStore.appendLocalTip(message: Barrage)

// 订阅消息列表状态变化
// BarrageStore 上没有 eventPublisher，只通过 state 订阅
barrageStore.state  // StatePublisher<BarrageState>
// BarrageState.messageList: [Barrage]
```

> ⚠️ **注意**：`BarrageStore` 上没有独立的 `eventPublisher`，消息通过 `state.messageList` 分发。
> ⚠️ **注意**：`disableSendMessage` 属于 `LiveAudienceStore`，不属于 `BarrageStore`，见 [live/audience-manage](live/audience-manage.md)。

| 参数 | 类型 | 说明 |
|------|------|------|
| `liveID` | `String` | 直播间唯一标识，与进房 ID 保持一致 |
| `text` | `String` | 消息文本内容 |
| `extensionInfo` | `[String: String]?` | 扩展信息字典（值必须为 String，不支持嵌套） |
| `businessID` | `String` | 自定义消息类型标识，如 `"gift_notify"` |
| `data` | `String` | JSON 格式的自定义消息体 |

## 代码示例

### 完整弹幕集成

```swift
import AtomicXCore
import Combine

final class BarrageManager {

    // MARK: - 属性

    private let barrageStore: BarrageStore
    private var cancellables = Set<AnyCancellable>()

    /// 经节流后供 UI 使用的消息列表（最多 500 条）
    @Published private(set) var displayMessages: [Barrage] = []

    // 节流定时器
    private var throttleTimer: Timer?
    private let throttleInterval: TimeInterval = 0.3   // 300ms

    // MARK: - 初始化

    init(liveID: String) {
        // 步骤1: 创建与直播间绑定的 BarrageStore
        self.barrageStore = BarrageStore.create(liveID: liveID)

        // 步骤2: 订阅消息列表变化（通过 state，不是 eventPublisher）
        subscribeMessageList()
    }

    // MARK: - 订阅

    private func subscribeMessageList() {
        barrageStore.state
            .map(\.messageList)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] messages in
                // 步骤3: 节流处理，避免高频刷新
                self?.scheduleThrottledUpdate(messages: messages)
            }
            .store(in: &cancellables)
    }

    // MARK: - 节流 + 循环缓冲

    private func scheduleThrottledUpdate(messages: [Barrage]) {
        // 取消上一个待执行的 timer
        throttleTimer?.invalidate()
        throttleTimer = Timer.scheduledTimer(
            withTimeInterval: throttleInterval,
            repeats: false
        ) { [weak self] _ in
            guard let self else { return }
            // 循环缓冲：超过 500 条时截取最新 500 条
            let capped = messages.count > 500
                ? Array(messages.suffix(500))
                : messages
            self.displayMessages = capped
        }
    }

    // MARK: - 展示层（TableView 配置建议）

    /// 配置弹幕 Cell 的异步渲染
    func configureBarrageCell(_ cell: UITableViewCell) {
        // 步骤4: 异步渲染降低主线程压力
        cell.layer.drawsAsynchronously = true
    }

    // MARK: - 发送文本弹幕

    func sendText(_ text: String,
                  completion: ((Result<Void, ErrorInfo>) -> Void)? = nil) {
        // 步骤5: 发送文本消息
        // extensionInfo 类型为 [String: String]?，值只能是字符串
        barrageStore.sendTextMessage(
            text: text,
            extensionInfo: nil
        ) { result in
            switch result {
            case .success:
                // 成功时 messageList 会自动更新，无需手动插入
                completion?(.success(()))
            case .failure(let error):
                print("[Barrage] 发送失败 code=\(error.code) msg=\(error.message)")
                completion?(.failure(error))
            }
        }
    }

    // MARK: - 发送自定义弹幕（如礼物通知）

    func sendGiftNotification(giftName: String, count: Int) {
        // 步骤6: 自定义消息示例（JSON 格式）
        let payload: [String: Any] = [
            "gift_name": giftName,
            "count": count,
            "timestamp": Date().timeIntervalSince1970
        ]

        guard let jsonData = try? JSONSerialization.data(withJSONObject: payload),
              let jsonString = String(data: jsonData, encoding: .utf8) else {
            return
        }

        barrageStore.sendCustomMessage(
            businessID: "gift_notify",   // 接收端通过此 ID 识别消息类型
            data: jsonString
        ) { result in
            if case .failure(let error) = result {
                print("[Barrage] 自定义消息发送失败 code=\(error.code) msg=\(error.message)")
            }
        }
    }

    // MARK: - 本地提示（不广播）

    func appendSystemTip(_ text: String) {
        // 步骤7: 插入仅本端可见的系统提示
        var tip = Barrage()
        tip.textContent = text
        barrageStore.appendLocalTip(message: tip)
    }
}
```

### UI 绑定（UIKit）

```swift
// UIKit: 订阅 displayMessages 刷新 TableView
barrageManager.$displayMessages
    .receive(on: DispatchQueue.main)
    .sink { [weak self] messages in
        self?.tableView.reloadData()
        // 自动滚动到最新消息
        if !messages.isEmpty {
            let lastIndex = IndexPath(row: messages.count - 1, section: 0)
            self?.tableView.scrollToRow(at: lastIndex, at: .bottom, animated: true)
        }
    }
    .store(in: &cancellables)
```

### 自定义消息接收解析

```swift
// 接收端解析自定义弹幕
func parseCustomBarrage(_ barrage: Barrage) {
    guard barrage.messageType == .custom else { return }

    switch barrage.businessID {
    case "gift_notify":
        // 解析礼物通知
        if let data = barrage.data?.data(using: .utf8),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let giftName = json["gift_name"] as? String,
           let count = json["count"] as? Int {
            showGiftAnimation(giftName: giftName, count: count)
        }

    case "like_action":
        // 解析点赞动效
        showLikeAnimation()

    default:
        break
    }
}
```

## 调用时序

```
进房成功
    │
    ▼
BarrageStore.create(liveID:)          // 创建实例
    │
    ▼
订阅 barrageStore.state.messageList   // 建立状态监听（无独立 eventPublisher）
    │
    ├─ 收到消息更新
    │       │
    │       ▼
    │   节流处理（300ms Timer）
    │       │
    │       ▼
    │   循环缓冲截取（max 500）
    │       │
    │       ▼
    │   主线程刷新 UI
    │
    ├─ 用户发送弹幕
    │       │
    │       ▼
    │   sendTextMessage / sendCustomMessage
    │       ├─ .success → messageList 自动更新，无需手动插入
    │       └─ .failure(ErrorInfo) → 展示错误提示
    │               ├─ code -2380 全员禁言
    │               └─ code -2381 已被禁言
    │
    └─ 退出直播间
            │
            ▼
        cancellables.removeAll()      // 取消所有订阅
```

## 平台特有注意事项

### 1. Combine 订阅生命周期
`cancellables` 需与 ViewController / ViewModel 的生命周期保持一致。在 `deinit` 或 `viewDidDisappear` 时调用 `cancellables.removeAll()`，防止在直播间退出后仍收到回调。

### 2. extensionInfo 类型为 `[String: String]?`
`sendTextMessage` 的 `extensionInfo` 参数类型是 `[String: String]?`，不是 `[String: Any]?`。若需要传递复杂结构，请先将值 JSON 序列化为字符串再放入字典。

### 3. 键盘遮挡弹幕列表
iOS 上键盘弹出会遮盖底部弹幕输入框。监听 `UIResponder.keyboardWillShowNotification` 动态调整 `tableView` 的 `contentInset.bottom`，确保最新弹幕可见。

### 4. 模拟器限制
模拟器网络行为与真机存在差异，建议在真机上测试弹幕高并发场景（弹幕风暴）以验证节流效果。

### 5. 自定义消息 data 大小限制
`sendCustomMessage` 的 `data` 字段建议不超过 **4KB**，超出可能导致消息发送失败或被截断。礼物动画资源等大内容应使用 URL 而非内嵌数据。
