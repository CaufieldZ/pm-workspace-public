---
id: live/device-control
platform: ios
---

# 设备管理 — iOS 实现

## 前置条件

**依赖安装（Podfile）**
```ruby
pod 'AtomicXCore', '~> 4.0'
```

**Info.plist 权限声明**（两项均须配置，否则系统拒绝授权或 App 崩溃）
```xml
<key>NSCameraUsageDescription</key>
<string>需要访问摄像头以进行视频直播</string>
<key>NSMicrophoneUsageDescription</key>
<string>需要访问麦克风以进行语音直播</string>
```

**前置状态**：
- `LoginStore.shared` 登录成功（登录成功后才可操作设备）
- 系统权限已授予（AVAuthorizationStatus == .authorized）

## API 调用（真实签名）

```swift
// ── 摄像头 ──────────────────────────────────────────────────────────
DeviceStore.shared.openLocalCamera(isFront: Bool, completion: CompletionClosure?)
DeviceStore.shared.closeLocalCamera()
DeviceStore.shared.switchCamera(isFront: Bool)          // 不中断采集，切换前/后置

// ── 麦克风 ──────────────────────────────────────────────────────────
DeviceStore.shared.openLocalMicrophone(completion: CompletionClosure?)
DeviceStore.shared.closeLocalMicrophone()

// ── 音量控制 ─────────────────────────────────────────────────────────
DeviceStore.shared.setCaptureVolume(volume: Int)         // 采集音量，range [0, 100]
DeviceStore.shared.setOutputVolume(_ volume: Int)        // 播放音量，range [0, 100]

// ── 音频路由 ─────────────────────────────────────────────────────────
DeviceStore.shared.setAudioRoute(_ route: AudioRoute)

// ── 镜像与画质 ───────────────────────────────────────────────────────
DeviceStore.shared.switchMirror(mirrorType: MirrorType)
DeviceStore.shared.updateVideoQuality(_ quality: VideoQuality)

// ── 状态快照 ─────────────────────────────────────────────────────────
DeviceStore.shared.state  // StatePublisher<DeviceState>
```

**DeviceState 关键字段**
```swift
struct DeviceState {
    var microphoneStatus: DeviceStatus
    var captureVolume: Int          // range [0, 100]  ⚠️ 不是 0-150
    var outputVolume: Int           // range [0, 100]
    var cameraStatus: DeviceStatus
    var isFrontCamera: Bool
    var localMirrorType: MirrorType
    var localVideoQuality: VideoQuality
    var currentAudioRoute: AudioRoute
    var networkInfo: NetworkInfo
}
```

**通用回调类型**
```swift
typealias CompletionClosure = (Result<Void, ErrorInfo>) -> Void

struct ErrorInfo {
    var code: Int
    var message: String
}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `isFront` | `Bool` | `true` = 前置摄像头，`false` = 后置摄像头 |
| `completion` | `CompletionClosure?` | 异步回调 `(Result<Void, ErrorInfo>) -> Void`；`nil` 表示不关心结果 |
| `volume` | `Int` | 音量范围 **[0, 100]**（注意不是 0-150） |

## 代码示例

```swift
import AtomicXCore
import AVFoundation

// MARK: - 打开摄像头（含权限检查）

func openCamera(isFront: Bool = true) {
    // 先检查系统权限
    switch AVCaptureDevice.authorizationStatus(for: .video) {
    case .authorized:
        DeviceStore.shared.openLocalCamera(isFront: isFront) { result in
            switch result {
            case .success:
                print("[Device] 摄像头打开成功, 前置: \(isFront)")
            case .failure(let errorInfo):
                print("[Device] 摄像头打开失败, code: \(errorInfo.code), msg: \(errorInfo.message)")
                handleDeviceError(errorInfo)
            }
        }
    case .notDetermined:
        AVCaptureDevice.requestAccess(for: .video) { granted in
            DispatchQueue.main.async {
                if granted { openCamera(isFront: isFront) }
            }
        }
    case .denied, .restricted:
        guideToSettings(message: "请在「设置 > 隐私 > 摄像头」中开启权限")
    @unknown default:
        break
    }
}

// MARK: - 打开麦克风

func openMicrophone() {
    DeviceStore.shared.openLocalMicrophone { result in
        switch result {
        case .success:
            print("[Device] 麦克风打开成功")
        case .failure(let errorInfo):
            print("[Device] 麦克风打开失败, code: \(errorInfo.code)")
            handleDeviceError(errorInfo)
        }
    }
}

// MARK: - 关闭设备

func closeAllDevices() {
    DeviceStore.shared.closeLocalCamera()
    DeviceStore.shared.closeLocalMicrophone()
}

// MARK: - 切换前后摄像头（不中断推流）

func flipCamera(toFront: Bool) {
    DeviceStore.shared.switchCamera(isFront: toFront)
}

// MARK: - 音量调节（range [0, 100]）

func setCaptureVolume(_ volume: Int) {
    // ⚠️ 范围是 [0, 100]，不是 [0, 150]
    let clamped = min(max(volume, 0), 100)
    DeviceStore.shared.setCaptureVolume(volume: clamped)
}

func setOutputVolume(_ volume: Int) {
    let clamped = min(max(volume, 0), 100)
    DeviceStore.shared.setOutputVolume(clamped)
}

// MARK: - 音频路由切换（扬声器 / 听筒）

func switchToSpeaker() {
    DeviceStore.shared.setAudioRoute(.speaker)
}

func switchToEarpiece() {
    DeviceStore.shared.setAudioRoute(.earpiece)
}

// MARK: - 错误处理

func handleDeviceError(_ errorInfo: ErrorInfo) {
    switch errorInfo.code {
    case -1101:
        guideToSettings(message: "摄像头权限被拒，请前往系统设置开启")
    case -1102:
        print("摄像头被其他应用占用，请关闭后重试")
    case -1103:
        print("当前设备不支持摄像头（请使用真机测试）")
    case -1105:
        guideToSettings(message: "麦克风权限被拒，请前往系统设置开启")
    case -1106:
        print("麦克风被其他应用占用，请结束通话后重试")
    default:
        print("设备错误 code: \(errorInfo.code), msg: \(errorInfo.message)")
    }
}

func guideToSettings(message: String) {
    DispatchQueue.main.async {
        // 引导用户跳转到系统设置（业务自行实现 Alert UI）
        if let url = URL(string: UIApplication.openSettingsURLString) {
            UIApplication.shared.open(url)
        }
    }
}
```

**主播开播：同时打开摄像头和麦克风**：
```swift
func openAllDevicesForAnchor() {
    openCamera(isFront: true)   // 先打开摄像头
    openMicrophone()            // 再打开麦克风
    // 注意：如需串行等待，请在 openCamera 的 completion .success 分支内调用 openMicrophone
}

// 主播下播：关闭所有设备
func closeAllDevicesOnStop() {
    DeviceStore.shared.closeLocalCamera()
    DeviceStore.shared.closeLocalMicrophone()
}
```

## 调用时序

```
权限检查
    │
    ├─ 未确定（notDetermined）
    │       └─ 系统弹窗 → 用户授权/拒绝
    │
    ├─ 已拒绝（denied）
    │       └─ 展示引导弹窗 → 跳转系统设置
    │
    └─ 已授权（authorized）
            │
            ▼
    DeviceStore.shared.openLocalCamera(isFront: true, completion:)
            │
            ├─ .failure(errorInfo)
            │       ├─ code -1100 → 重试或上报
            │       ├─ code -1101 → 系统授权异常（引导去设置）
            │       ├─ code -1102 → 提示关闭其他应用
            │       └─ code -1103 → 模拟器，提示换真机
            │
            └─ .success
                    │
                    ▼
            DeviceStore.shared.openLocalMicrophone(completion:)
                    │
                    ├─ .failure(errorInfo) → 同上处理
                    │
                    └─ .success
                            │
                            ▼
                    设备就绪，进行推流/预览
                            │
                    [使用中]
                    switchCamera(isFront:)         ← 切换前后置（无黑屏）
                    setCaptureVolume(volume:)      ← 调节采集音量 [0, 100]
                    setAudioRoute(.speaker)        ← 切换音频路由
                            │
                            ▼
                    DeviceStore.shared.closeLocalCamera()
                    DeviceStore.shared.closeLocalMicrophone()
                    （下播 / 退房 / App 进入后台）
```

## 平台特有注意事项

### 1. captureVolume 范围是 [0, 100]，不是 [0, 150]
`setCaptureVolume(volume:)` 和 `setOutputVolume(_:)` 的有效范围均为 **[0, 100]**。传入超过 100 的值会被 SDK 忽略或截断。不要将范围设为 0-150。

### 2. iOS 权限弹窗时机
系统权限弹窗**只会弹出一次**（首次请求时）。若用户拒绝后，后续调用 `requestAccess` 不再弹窗，必须引导用户手动前往系统设置开启。建议在开播前明确告知用户权限用途，提高授权通过率。

### 3. 后台摄像头自动关闭
iOS 系统在 App 进入后台时会**自动挂起摄像头采集**。主播场景中若需要后台推流，须在 `Info.plist` 中开启后台音视频模式：
```xml
<key>UIBackgroundModes</key>
<array>
    <string>audio</string>
</array>
```
即使开启后台模式，摄像头视频帧在后台仍会停止推送，建议切后台时向观众提示"主播暂时离开"。

### 4. 摄像头被其他进程占用（-1102）
iOS 系统级应用（如 FaceTime、系统相机）在前台时会独占摄像头。当 App 从后台切回前台并重新打开摄像头时，若系统摄像头仍被其他应用持有，会触发 `-1102`。解决方案：监听 `UIApplication.didBecomeActiveNotification`，延迟 0.5~1 秒后重试打开摄像头。

### 5. ErrorInfo 不是 Swift Error
回调中的 `errorInfo` 是 `ErrorInfo` 结构体，直接用 `.code` 和 `.message` 访问，不可当作 `Error` 使用：
```swift
case .failure(let errorInfo):
    let code = errorInfo.code       // ✅
    let msg  = errorInfo.message    // ✅
    // errorInfo as? Error          // ❌ 不适用
```
