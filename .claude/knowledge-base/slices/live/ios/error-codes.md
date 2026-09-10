---
id: live/error-codes
platform: ios
---

# 错误码参考 — iOS 实现

## 前置条件

AtomicXCore SDK 所有异步接口均通过 Swift `Result<T, ErrorInfo>` 回调返回错误。

**错误类型是 `ErrorInfo` 结构体，不是 Swift `Error` 协议**：

```swift
struct ErrorInfo {
    var code: Int       // 错误码（负数：客户端；正数：服务端）
    var message: String // 错误描述
}

// 所有异步回调的统一签名
typealias CompletionClosure = (Result<Void, ErrorInfo>) -> Void
```

## API 调用（错误码提取方式）

```swift
// ✅ 正确：直接从 ErrorInfo 结构体取字段
LoginStore.shared.login(sdkAppID: 1400000001,
                        userID: "user_001",
                        userSig: userSig) { result in
    switch result {
    case .success:
        break
    case .failure(let errorInfo):   // errorInfo: ErrorInfo（不是 Error）
        let code = errorInfo.code
        let msg  = errorInfo.message
    }
}

// ✅ 返回 LiveInfo 的回调（LiveInfoCompletionClosure）
// typealias LiveInfoCompletionClosure = (Result<LiveInfo, ErrorInfo>) -> Void
LiveListStore.shared.joinLive(liveID: "room_001") { result in
    switch result {
    case .success(let liveInfo):    // liveInfo: LiveInfo
        print("直播间名称: \(liveInfo.liveName)")
    case .failure(let errorInfo):
        print("进房失败, code: \(errorInfo.code)")
    }
}
```

## 代码示例

```swift
import AtomicXCore

// MARK: - 统一错误处理器

final class ErrorHandler {

    // MARK: - 从 ErrorInfo 提取信息

    /// 直接从 ErrorInfo 取 code 和 message
    static func log(_ errorInfo: ErrorInfo, context: String = #function) {
        print("[ErrorHandler] [\(context)] code=\(errorInfo.code), msg=\(errorInfo.message)")
    }

    // MARK: - 分类处理（按 errorInfo.code 分支）

    static func handle(_ errorInfo: ErrorInfo,
                       context: String = #function,
                       retryHandler: (() -> Void)? = nil) {
        log(errorInfo, context: context)

        switch errorInfo.code {
        // ── 通用错误 ──────────────────────────────────────────
        case -1000:
            showAlert(title: "配置错误", message: "SDKAppID 不合法，请检查控制台配置")
        case -1001:
            showAlert(title: "参数错误", message: "UserSig 已过期或参数不合法，请重新获取")
        case -1002:
            showAlert(title: "未登录", message: "请先完成登录后再进行操作")
        case -1003:
            guideToSystemPermissionSettings()

        // ── 限频（可重试）────────────────────────────────────
        case -2:
            retryWithBackoff(handler: retryHandler)

        // ── 设备错误 ──────────────────────────────────────────
        case -1101:
            guideToSystemPermissionSettings(permissionType: .camera)
        case -1102:
            showAlert(title: "摄像头占用", message: "请关闭其他正在使用摄像头的应用后重试")
        case -1103:
            showAlert(title: "无摄像头", message: "当前设备不支持摄像头，请使用真机测试")
        case -1105:
            guideToSystemPermissionSettings(permissionType: .microphone)
        case -1106:
            showAlert(title: "麦克风占用", message: "请结束通话或关闭其他语音应用后重试")
        case -1100, -1104:
            showAlert(title: "设备错误",
                      message: "设备打开失败（code: \(errorInfo.code)），请重启应用后重试")

        // ── 房间错误 ──────────────────────────────────────────
        case -2101:
            showAlert(title: "操作错误", message: "请先进入房间再执行此操作")
        case -2105:
            showAlert(title: "参数错误", message: "直播间 ID 格式非法（须为 ASCII，≤ 48 字节）")
        case -2107:
            showAlert(title: "参数错误", message: "直播间名称非法（UTF-8，≤ 30 字节）")
        case -2108:
            showAlert(title: "已在房间内", message: "您已在其他房间中，请先退出后再加入新房间")

        // ── 权限/信令错误 ─────────────────────────────────────
        case -2380:
            showAlert(title: "全员禁言", message: "当前房间已开启全员禁言，请等待房主解除")
        case -2381:
            showAlert(title: "被禁言", message: "您已被禁言，请联系房主申请解除")

        // ── 服务端错误（可重试）──────────────────────────────
        case 100001:
            retryWithBackoff(handler: retryHandler)

        // ── 未知错误 ──────────────────────────────────────────
        default:
            showAlert(title: "未知错误", message: "错误码：\(errorInfo.code)\n\(errorInfo.message)")
        }
    }

    // MARK: - UI 工具方法

    private static func showAlert(title: String, message: String) {
        DispatchQueue.main.async {
            guard let topVC = UIApplication.shared.topViewController else { return }
            let alert = UIAlertController(title: title, message: message, preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "确定", style: .default))
            topVC.present(alert, animated: true)
        }
    }

    enum PermissionType { case camera, microphone }

    static func guideToSystemPermissionSettings(permissionType: PermissionType? = nil) {
        let message: String
        switch permissionType {
        case .camera:
            message = "请前往「设置 > 隐私与安全 > 摄像头」开启权限"
        case .microphone:
            message = "请前往「设置 > 隐私与安全 > 麦克风」开启权限"
        case nil:
            message = "请前往系统设置开启所需权限"
        }
        DispatchQueue.main.async {
            guard let topVC = UIApplication.shared.topViewController else { return }
            let alert = UIAlertController(title: "权限不足", message: message, preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "去设置", style: .default) { _ in
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            })
            alert.addAction(UIAlertAction(title: "取消", style: .cancel))
            topVC.present(alert, animated: true)
        }
    }

    private static var retryCount = 0
    private static let maxRetries = 3

    private static func retryWithBackoff(handler: (() -> Void)?) {
        guard let handler = handler, retryCount < maxRetries else {
            retryCount = 0
            showAlert(title: "请求失败", message: "多次重试后仍然失败，请稍后再试")
            return
        }
        let delay = pow(2.0, Double(retryCount))
        retryCount += 1
        DispatchQueue.main.asyncAfter(deadline: .now() + delay) {
            handler()
        }
    }
}

// MARK: - UIApplication 顶层 ViewController 扩展

extension UIApplication {
    var topViewController: UIViewController? {
        var topVC = connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow }?
            .rootViewController
        while let presented = topVC?.presentedViewController {
            topVC = presented
        }
        return topVC
    }
}
```

**调用示例**：
```swift
// 登录错误处理
LoginStore.shared.login(sdkAppID: 1400000001,
                        userID: "user_001",
                        userSig: userSig) { result in
    switch result {
    case .success:
        print("登录成功")
    case .failure(let errorInfo):
        ErrorHandler.handle(errorInfo, context: "login")
    }
}

// 设备错误处理（含重试）
DeviceStore.shared.openLocalCamera(isFront: true) { result in
    switch result {
    case .success:
        print("摄像头打开成功")
    case .failure(let errorInfo):
        ErrorHandler.handle(errorInfo, context: "openLocalCamera") {
            // 重试逻辑
            DeviceStore.shared.openLocalCamera(isFront: true, completion: nil)
        }
    }
}
```

## iOS 特有：权限错误与系统权限对应

iOS 系统权限与 SDK 错误码的对应关系：

| SDK 错误码 | AVFoundation 权限状态 | 系统设置路径 | 处理方式 |
|------------|----------------------|-------------|---------|
| `-1101` | `AVAuthorizationStatus.denied`（摄像头） | 设置 > 隐私与安全 > 摄像头 | 弹窗引导跳转 `UIApplication.openSettingsURLString` |
| `-1105` | `AVAuthorizationStatus.denied`（麦克风） | 设置 > 隐私与安全 > 麦克风 | 弹窗引导跳转 `UIApplication.openSettingsURLString` |
| `-1003` | 系统级权限被拒 | 设置 > 隐私与安全 | 通用权限引导 |

**权限状态主动检测**（在调用 SDK 前预检，避免先触发错误码再处理）：

```swift
import AVFoundation

func checkAndRequestCameraPermission(completion: @escaping (Bool) -> Void) {
    let status = AVCaptureDevice.authorizationStatus(for: .video)
    switch status {
    case .authorized:
        completion(true)
    case .notDetermined:
        // 首次询问 — 系统弹窗只弹一次
        AVCaptureDevice.requestAccess(for: .video) { granted in
            DispatchQueue.main.async { completion(granted) }
        }
    case .denied, .restricted:
        // 已拒绝 — 引导前往系统设置（requestAccess 不再弹窗）
        DispatchQueue.main.async {
            ErrorHandler.guideToSystemPermissionSettings(permissionType: .camera)
            completion(false)
        }
    @unknown default:
        completion(false)
    }
}
```

**注意事项**：
- `Result<Void, ErrorInfo>` 的失败分支中，`errorInfo` 是 `ErrorInfo` 结构体，**不是** `Swift.Error`，无法调用 `localizedDescription`。
- `AVCaptureDevice.requestAccess` 只触发**一次**系统弹窗。用户拒绝后，再次调用不会弹窗，需手动引导前往设置。
- iOS 模拟器不支持摄像头，`AVAuthorizationStatus` 始终返回 `.authorized` 但打开后会收到 `-1103`，请在真机上测试设备功能。
- 权限状态缓存在 App 沙盒中，卸载重装后会重置。测试时需注意。
