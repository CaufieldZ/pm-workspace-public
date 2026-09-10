---
id: live/login-auth
platform: ios
---

# 登录与鉴权 — iOS 实现

## 前置条件

**依赖安装（Podfile）**
```ruby
pod 'AtomicXCore', '~> 4.0'
```

**Info.plist 权限声明**（推流场景必须配置，否则 iOS 14+ 设备调用设备接口时崩溃）
```xml
<key>NSCameraUsageDescription</key>
<string>需要访问摄像头以进行视频直播</string>
<key>NSMicrophoneUsageDescription</key>
<string>需要访问麦克风以进行语音直播</string>
```

**最低系统要求**：iOS 13.0+，Xcode 14.0+

## API 调用（真实签名）

```swift
// 登录
LoginStore.shared.login(
    sdkAppID: Int32,              // ⚠️ Int32，不是 Int
    userID: String,
    userSig: String,
    completion: CompletionClosure? // (Result<Void, ErrorInfo>) -> Void
)

// 登出
LoginStore.shared.logout(completion: CompletionClosure?)

// 更新用户资料
LoginStore.shared.setSelfInfo(userProfile: UserProfile, completion: CompletionClosure?)

// 状态订阅（Combine）
LoginStore.shared.state          // StatePublisher<LoginState>
// LoginState.loginStatus: LoginStatus
// LoginState.loginUserInfo: UserProfile?

// 被动事件订阅
LoginStore.shared.loginEventPublisher  // PassthroughSubject<LoginEvent, Never>
// LoginEvent.kickedOffline    — 被踢下线
// LoginEvent.loginExpired     — 登录票据过期
```

**通用类型**
```swift
typealias CompletionClosure = (Result<Void, ErrorInfo>) -> Void

struct ErrorInfo {
    var code: Int
    var message: String
}

enum LoginEvent {
    case kickedOffline
    case loginExpired
}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `sdkAppID` | `Int32` | 腾讯云控制台的应用 ID（**Int32**，注意不是 Int） |
| `userID` | `String` | 用户唯一标识，ASCII 字母/数字/`-`/`_`，≤ 32 字节 |
| `userSig` | `String` | 后端签发的鉴权票据 |
| `completion` | `CompletionClosure?` | 异步回调 `(Result<Void, ErrorInfo>) -> Void`，在主线程返回 |

## 代码示例

```swift
import AtomicXCore
import Combine

// MARK: - 登录

func login(sdkAppID: Int32,   // ⚠️ Int32
           userID: String,
           userSig: String) {
    LoginStore.shared.login(sdkAppID: sdkAppID,
                            userID: userID,
                            userSig: userSig) { result in
        switch result {
        case .success:
            print("[Login] 登录成功")
            // 登录成功后可操作设备 / 进入房间

        case .failure(let errorInfo):
            // errorInfo 是 ErrorInfo 结构体，不是 Swift Error
            print("[Login] 登录失败, code: \(errorInfo.code), msg: \(errorInfo.message)")
            handleLoginError(errorInfo)
        }
    }
}

// MARK: - 登出

func logout() {
    LoginStore.shared.logout { result in
        switch result {
        case .success:
            print("[Login] 登出成功")
        case .failure(let errorInfo):
            print("[Login] 登出失败, code: \(errorInfo.code)")
        }
    }
}

// MARK: - 错误分类处理

func handleLoginError(_ errorInfo: ErrorInfo) {
    switch errorInfo.code {
    case -1000:
        print("SDKAppID 不合法，请检查控制台配置")
    case -1001:
        print("UserSig 已过期或参数不合法，请重新获取")
    default:
        print("未知登录错误：\(errorInfo.code) - \(errorInfo.message)")
    }
}

// MARK: - 被动事件监听（踢下线 / 票据过期）

var cancellables = Set<AnyCancellable>()

func subscribeLoginEvents() {
    LoginStore.shared.loginEventPublisher
        .receive(on: DispatchQueue.main)
        .sink { event in
            switch event {
            case .kickedOffline:
                print("[Login] 被踢下线，需重新登录")
                // 引导用户重新登录

            case .loginExpired:
                print("[Login] 登录票据已过期，需刷新 UserSig 后重新登录")
                // 从业务后端刷新 UserSig 后重新调用 login
            }
        }
        .store(in: &cancellables)
}

// MARK: - 状态查询（通过 state 订阅）

func observeLoginState() {
    LoginStore.shared.state
        .receive(on: DispatchQueue.main)
        .sink { loginState in
            print("[Login] 状态: \(loginState.loginStatus)")
            if let profile = loginState.loginUserInfo {
                print("[Login] 当前用户: \(profile.userID)")
            }
        }
        .store(in: &cancellables)
}
```

**典型调用流程（从业务后端获取 UserSig 后登录）**：
```swift
// Step 1: 从业务后端获取 UserSig（伪代码）
YourAPI.fetchUserSig(userID: "user_001") { userSig in
    guard let userSig = userSig else { return }

    // Step 2: 登录 SDK
    // ⚠️ sdkAppID 必须传 Int32 字面量或显式转换
    LoginStore.shared.login(sdkAppID: 1400000001,
                            userID: "user_001",
                            userSig: userSig) { result in
        switch result {
        case .success:
            // Step 3: 登录成功后才可操作设备 / 进入房间
            setupDevices()
        case .failure(let errorInfo):
            showAlert(message: "登录失败: \(errorInfo.message)")
        }
    }
}
```

## 调用时序

```
App 启动
    │
    ▼
从业务后端获取 UserSig
    │
    ├─ 失败 ──→ 展示网络错误，引导重试
    │
    ▼
LoginStore.shared.login(sdkAppID: Int32, userID:, userSig:)
    │
    ├─ .failure(errorInfo)
    │       ├─ code -1000 → 核查 SDKAppID（Int32）
    │       ├─ code -1001 → 检查 UserSig 有效期 / UserID 格式
    │       └─ 其他      → 上报日志，提示用户
    │
    └─ .success
            │
            ▼
        订阅 loginEventPublisher（监听踢下线/过期）
            │
            ▼
        进入主功能流程
        （设备初始化 / 进入房间 / 开始推流）
```

## 平台特有注意事项

### 1. sdkAppID 类型必须是 Int32
Swift 类型推断会将整数字面量视为 `Int`。传入 `login()` 时若将 `Int` 变量隐式传递给 `Int32` 参数，编译器会报错：
```swift
let appID: Int = 1400000001     // ❌ 编译错误：不能将 Int 赋值给 Int32
let appID: Int32 = 1400000001   // ✅ 正确
// 或直接传字面量（Swift 自动推断 Int32）：
LoginStore.shared.login(sdkAppID: 1400000001, ...)  // ✅ 字面量可自动匹配 Int32
```

### 2. ErrorInfo 是结构体，不是 Error 协议
SDK 回调返回的是 `ErrorInfo` 结构体，**不是** `Swift.Error`。不可将其强转为 `Error` 或使用 `localizedDescription`：
```swift
case .failure(let errorInfo):
    let code = errorInfo.code       // ✅ 直接访问 .code
    let msg  = errorInfo.message    // ✅ 直接访问 .message
    // errorInfo.localizedDescription  // ❌ 不存在此属性
```

### 3. Info.plist 权限缺失导致崩溃
iOS 14+ 系统在首次访问相机/麦克风时，若未在 `Info.plist` 中声明 `NSCameraUsageDescription` 或 `NSMicrophoneUsageDescription`，App **直接崩溃**（不返回错误码）。务必在集成 SDK 时同步添加权限描述。

### 4. 进入后台后网络断连
App 切入后台超过约 30 秒后，iOS 系统可能中断 TCP 长连接，导致登录态失效并触发 `loginEventPublisher` 的 `.loginExpired` 事件。建议：
- 订阅 `UIApplication.willEnterForegroundNotification`
- 前台恢复时通过 `LoginStore.shared.state` 检查 `loginStatus`
- 如已失效，刷新 UserSig 后重新调用 `login`

### 5. UserSig 刷新策略
UserSig 有有效期（建议后端配置 7 天），客户端应：
- 在签发时记录过期时间戳（`exp` 字段）
- App 启动或前台恢复时检查是否在有效期内
- 距离过期 ≤ 1 小时时主动向后端刷新，避免直播中途 UserSig 失效中断推流
