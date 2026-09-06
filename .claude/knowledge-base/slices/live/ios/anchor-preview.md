---
id: live/anchor-preview
platform: ios
---

# 主播预览 — iOS 实现

## 前置条件

**依赖安装（Podfile）**
```ruby
pod 'AtomicXCore', '~> 4.0'
```

**Info.plist 权限声明**
```xml
<key>NSCameraUsageDescription</key>
<string>需要访问摄像头以进行视频直播</string>
<key>NSMicrophoneUsageDescription</key>
<string>需要访问麦克风以进行语音直播</string>
```

**前置状态**：
- `LoginStore.shared` 登录成功（须完成登录）
- 摄像头/麦克风系统权限已授予

## API 调用（真实签名）

```swift
// LiveCoreView 初始化：主播端用 .pushView（推流模式）
// ⚠️ 参数名是 viewType（不是 liveScene）
LiveCoreView(viewType: .pushView, frame: CGRect = .zero)

// 绑定直播间 ID（创建后必须立即调用，否则黑屏）
liveCoreView.setLiveID(_ liveID: String)

// 1. 打开前/后置摄像头（含 completion 回调）
DeviceStore.shared.openLocalCamera(isFront: Bool, completion: CompletionClosure?)
// CompletionClosure = (Result<Void, ErrorInfo>) -> Void

// 2. 打开麦克风
DeviceStore.shared.openLocalMicrophone(completion: CompletionClosure?)

// 3. 不中断采集情况下切换前后摄像头
DeviceStore.shared.switchCamera(isFront: Bool)

// 4. 退出预览时关闭设备
DeviceStore.shared.closeLocalCamera()
DeviceStore.shared.closeLocalMicrophone()
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `isFront` | `Bool` | `true` = 前置摄像头（默认），`false` = 后置 |
| `completion` | `CompletionClosure?` | `(Result<Void, ErrorInfo>) -> Void`；`nil` 表示不关心结果 |

## 代码示例

```swift
import UIKit
import AtomicXCore
import AVFoundation
import Combine

// MARK: - 主播预览核心逻辑（SDK API 使用为主）

// Step 1: 检查摄像头权限，通过后打开设备
func setupPreview() {
    switch AVCaptureDevice.authorizationStatus(for: .video) {
    case .authorized:
        openCameraAndMic()
    case .notDetermined:
        AVCaptureDevice.requestAccess(for: .video) { granted in
            DispatchQueue.main.async {
                if granted { openCameraAndMic() }
            }
        }
    case .denied, .restricted:
        showPermissionAlert(for: .video)
    @unknown default:
        break
    }
}

// Step 2: 先打开摄像头，成功后再打开麦克风
func openCameraAndMic() {
    DeviceStore.shared.openLocalCamera(isFront: true) { result in
        switch result {
        case .success:
            print("[Preview] 摄像头打开成功")
            openMicrophone()

        case .failure(let errorInfo):
            // errorInfo: ErrorInfo（.code + .message）
            print("[Preview] 摄像头打开失败, code: \(errorInfo.code), msg: \(errorInfo.message)")
            handleDeviceError(errorInfo)
        }
    }
}

func openMicrophone() {
    DeviceStore.shared.openLocalMicrophone { result in
        switch result {
        case .success:
            print("[Preview] 麦克风打开成功，预览就绪")
        case .failure(let errorInfo):
            print("[Preview] 麦克风打开失败, code: \(errorInfo.code)")
            handleDeviceError(errorInfo)
        }
    }
}

// Step 3: 退出预览时关闭设备
func teardownPreview() {
    DeviceStore.shared.closeLocalCamera()
    DeviceStore.shared.closeLocalMicrophone()
}

// Step 4: 不中断预览切换前后置摄像头
func flipCamera(toFront: Bool) {
    DeviceStore.shared.switchCamera(isFront: toFront)
}

// MARK: - 错误处理（使用 ErrorInfo 的 .code 字段）

func handleDeviceError(_ errorInfo: ErrorInfo) {
    let message: String
    switch errorInfo.code {
    case -1101: message = "摄像头权限被拒，请前往系统设置开启"
    case -1102: message = "摄像头被其他应用占用，请关闭后重试"
    case -1103: message = "当前设备不支持摄像头（请使用真机测试）"
    case -1105: message = "麦克风权限被拒，请前往系统设置开启"
    default:    message = "设备打开失败（错误码 \(errorInfo.code)），请重试"
    }
    // 业务自行展示 Alert
    print("[Preview] 设备错误：\(message)")
}

func showPermissionAlert(for mediaType: AVMediaType) {
    let message = mediaType == .video
        ? "请在「设置 > 隐私 > 摄像头」中允许本应用访问摄像头"
        : "请在「设置 > 隐私 > 麦克风」中允许本应用访问麦克风"
    // 业务自行展示 Alert + 跳转设置
    if let url = URL(string: UIApplication.openSettingsURLString) {
        UIApplication.shared.open(url)
    }
}
```

**App 生命周期处理（后台暂停/前台恢复）**：
```swift
import Combine

var cancellables = Set<AnyCancellable>()

func observeAppLifecycle() {
    NotificationCenter.default.publisher(for: UIApplication.didEnterBackgroundNotification)
        .sink { [weak self] _ in
            // 进后台时释放设备，避免摄像头指示灯常亮
            DeviceStore.shared.closeLocalCamera()
            DeviceStore.shared.closeLocalMicrophone()
        }
        .store(in: &cancellables)

    NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)
        .sink { [weak self] _ in
            // 回到前台时重新打开（注意：需要重新检查权限）
            openCameraAndMic()
        }
        .store(in: &cancellables)
}
```

## 调用时序

```
进入预览界面
        │
        ▼
checkCameraPermission()
        │
        ├─ denied  → showPermissionAlert → 用户跳转系统设置
        │
        └─ authorized
                │
                ▼
        DeviceStore.shared.openLocalCamera(isFront: true, completion:)
                │
                ├─ .failure(errorInfo) → handleDeviceError（显示错误提示）
                │
                └─ .success
                        │
                        ▼
                DeviceStore.shared.openLocalMicrophone(completion:)
                        │
                        ├─ .failure(errorInfo) → handleDeviceError
                        │
                        └─ .success → 预览画面出现，等待用户点击「开始直播」
                                │
                        [用户点击开始直播]
                                │
                                ▼
                        导航到房间配置页
                        由配置页调用 createLive（参见 anchor-room-config）
        │
退出预览界面
        │
        ▼
DeviceStore.shared.closeLocalCamera()
DeviceStore.shared.closeLocalMicrophone()   ← 退出预览时释放设备
```

## 平台特有注意事项

### 1. openLocalCamera 有 completion 参数，不可忽略
`DeviceStore.shared.openLocalCamera(isFront: Bool, completion: CompletionClosure?)` 包含 completion 参数。必须在 `.success` 回调中再打开麦克风，避免设备尚未就绪时即执行后续逻辑。

### 2. iOS 模拟器不支持摄像头
所有摄像头相关功能必须在**真实设备**上测试。模拟器调用 `openLocalCamera` 会返回 code `-1103`。

### 3. 进入后台时摄像头自动暂停
iOS 系统在 App 进入后台时会自动挂起摄像头采集。监听 `UIApplication.didEnterBackgroundNotification` 主动关闭设备，再在 `didBecomeActiveNotification` 时重新打开，避免 `-1102` 被占用错误。

### 4. 前后摄像头切换（不中断预览）
预览阶段可直接调用 `DeviceStore.shared.switchCamera(isFront:)` 切换前后摄像头，无需重新调用 `openLocalCamera`，画面切换无黑屏。

### 5. ErrorInfo 不是 Swift Error
设备回调的 `.failure` 分支中，错误对象是 `ErrorInfo` 结构体（`.code: Int` + `.message: String`），不是 `Swift.Error`，不可调用 `localizedDescription`。
