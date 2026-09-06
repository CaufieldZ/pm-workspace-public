---
id: live/anchor-room-config
platform: ios
---

# 直播间配置 — iOS 实现

## 前置条件

**依赖安装（Podfile）**
```ruby
pod 'AtomicXCore', '~> 4.0'
```

**前置状态**：
- `LoginStore.shared` 登录成功（须完成登录）
- 摄像头/麦克风设备已打开（`DeviceStore.shared.openLocalCamera` 成功）

## API 调用（真实签名）

```swift
// 构建直播间配置
// ⚠️ LiveInfo 必须通过 init(seatTemplate:) 初始化，不是 LiveInfo()
var liveInfo = LiveInfo(seatTemplate: .videoDynamicGrid9Seats)
liveInfo.liveID       = "your-live-id"
liveInfo.liveName     = "直播间名称"
liveInfo.coverURL     = "https://cdn.example.com/cover.jpg"
liveInfo.notice       = "欢迎来到我的直播间"
liveInfo.isPublicVisible = true

// 创建直播间
// ⚠️ 第一参数无标签（unnamed），completion 返回 LiveInfo
LiveListStore.shared.createLive(_ liveInfo: LiveInfo,
                                completion: LiveInfoCompletionClosure?)
// LiveInfoCompletionClosure = (Result<LiveInfo, ErrorInfo>) -> Void

// 更新直播间元数据（仅房主/管理员可调用）
LiveListStore.shared.updateLiveMetaData(_ metaData: [String: String],
                                        completion: CompletionClosure?)

// 更新直播间基础信息
LiveListStore.shared.updateLiveInfo(_ liveInfo: LiveInfo,
                                    modifyFlag: LiveInfo.ModifyFlag,
                                    completion: CompletionClosure?)
```

**LiveInfo 初始化与关键字段**
```swift
struct LiveInfo {
    // ⚠️ 正确初始化方式：必须传 seatTemplate
    init(seatTemplate: SeatLayoutTemplate)

    var liveID: String
    var liveName: String
    var coverURL: String
    var backgroundURL: String
    var notice: String
    var seatTemplate: SeatLayoutTemplate  // 座位布局模板
    var seatMode: TakeSeatMode           // .apply 或 .free
    var isPublicVisible: Bool
    var isGiftEnabled: Bool
    var isMessageDisable: Bool
    var categoryList: [NSNumber]
    var metaData: [String: String]
}

enum SeatLayoutTemplate {
    case videoDynamicGrid9Seats   // 9格视频动态布局（最常用）
    case videoDynamicFloat7Seats  // 7格视频浮动布局
    case videoFixedGrid9Seats
    case videoFixedFloat7Seats
    case videoLandscape4Seats
    case audioSalon(seatCount: Int)
    case karaoke(seatCount: Int)
}

// createLive 的回调类型
typealias LiveInfoCompletionClosure = (Result<LiveInfo, ErrorInfo>) -> Void
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `liveInfo.seatTemplate` | `SeatLayoutTemplate` | 必须通过 `init(seatTemplate:)` 传入，不可省略 |
| `liveID` | `String` | 直播间唯一 ID；仅含 ASCII，长度 ≤ 48 字节 |
| `liveName` | `String` | 显示名称；UTF-8，长度 ≤ 30 字节（约 10 个汉字） |
| `metaData` | `[String: String]` | 键值对扩展信息；最多 10 key，单值 ≤ 2 KB，总 ≤ 16 KB |

## 代码示例

```swift
import AtomicXCore

// MARK: - 创建直播间

func createLive(liveID: String, liveName: String, coverURL: String) {
    // ✅ 正确：使用 init(seatTemplate:) 初始化
    var liveInfo = LiveInfo(seatTemplate: .videoDynamicGrid9Seats)
    liveInfo.liveID       = liveID
    liveInfo.liveName     = liveName.isEmpty ? "我的直播间" : liveName
    liveInfo.coverURL     = coverURL
    liveInfo.isPublicVisible = true

    // ⚠️ createLive 第一参数无标签，completion 返回 LiveInfo（不是 Void）
    LiveListStore.shared.createLive(liveInfo) { result in
        switch result {
        case .success(let createdLiveInfo):
            // 回调返回完整 LiveInfo（含服务端写入的字段，如 createTime）
            print("[RoomConfig] 直播间创建成功, liveID: \(createdLiveInfo.liveID)")
            print("[RoomConfig] 创建时间: \(createdLiveInfo.createTime)")
            // 跳转直播中页面

        case .failure(let errorInfo):
            handleCreateLiveError(errorInfo)
        }
    }
}

// MARK: - 参数校验

func validateLiveName(_ name: String) -> Bool {
    // liveName 限制：UTF-8 字节数 ≤ 30
    let byteCount = name.utf8.count
    guard byteCount <= 30 else {
        print("[RoomConfig] 名称超过 30 字节（约 10 个汉字），当前 \(byteCount) 字节")
        return false
    }
    return true
}

// MARK: - 更新直播间元数据（开播后动态更新）

func updateMetaData(_ updates: [String: String]) {
    LiveListStore.shared.updateLiveMetaData(updates) { result in
        switch result {
        case .success:
            print("[RoomConfig] MetaData 更新成功")
        case .failure(let errorInfo):
            if errorInfo.code == -2300 {
                print("[RoomConfig] 权限不足，仅房主/管理员可更新 MetaData")
            } else {
                print("[RoomConfig] MetaData 更新失败, code: \(errorInfo.code)")
            }
        }
    }
}

// MARK: - MetaData 校验（最多 10 key，单值 ≤ 2KB，总 ≤ 16KB）

func buildValidatedMetaData(_ raw: [String: String]) -> [String: String] {
    var validated: [String: String] = [:]
    let maxKeyCount  = 10
    let maxValueBytes = 2 * 1024    // 2 KB
    let maxTotalBytes = 16 * 1024   // 16 KB
    var totalBytes    = 0

    for (key, value) in raw.prefix(maxKeyCount) {
        let valueBytes = value.utf8.count
        guard valueBytes <= maxValueBytes else {
            print("[RoomConfig] key '\(key)' 值超过 2KB，已跳过")
            continue
        }
        guard totalBytes + valueBytes <= maxTotalBytes else {
            print("[RoomConfig] MetaData 总大小超过 16KB，已停止添加")
            break
        }
        validated[key] = value
        totalBytes += valueBytes
    }
    return validated
}

// MARK: - 错误处理

func handleCreateLiveError(_ errorInfo: ErrorInfo) {
    switch errorInfo.code {
    case -2105: print("直播间 ID 格式非法（须为 ASCII，≤ 48 字节）")
    case -2107: print("直播间名称非法（UTF-8，≤ 30 字节）")
    case -2108: print("您已在其他直播间，请先退出后再试")
    default:    print("创建失败（code: \(errorInfo.code)）: \(errorInfo.message)")
    }
}
```

## 调用时序

```
设备已就绪（openLocalCamera + openLocalMicrophone 成功）
        │
        ▼
构建 LiveInfo
// ⚠️ 必须：LiveInfo(seatTemplate: .videoDynamicGrid9Seats)
// 设置 liveID / liveName / coverURL 等字段
        │
        ▼
客户端校验
├── liveName UTF-8 字节数 ≤ 30？
├── MetaData 单值 ≤ 2KB？
└── MetaData 总大小 ≤ 16KB？
        │
        ▼
// ⚠️ 第一参数无标签
LiveListStore.shared.createLive(liveInfo) { result in ... }
        │
        ├─ .failure(errorInfo)
        │       ├─ code -2105 → liveID 格式错误
        │       ├─ code -2107 → liveName 超长/非法
        │       └─ code -2108 → 已在其他房间
        │
        └─ .success(createdLiveInfo)   ← 包含服务端写入字段
                │
                ▼
        进入直播中状态
        （监听 liveListEventPublisher 生命周期事件）
```

## 平台特有注意事项

### 1. LiveInfo 必须用 `init(seatTemplate:)` 初始化
`LiveInfo` **没有无参初始化方法**（`LiveInfo()` 不正确）。必须传入 `SeatLayoutTemplate`：
```swift
// ✅ 正确
var liveInfo = LiveInfo(seatTemplate: .videoDynamicGrid9Seats)

// ❌ 错误：LiveInfo() 无此初始化方法
var liveInfo = LiveInfo()
```

### 2. createLive 第一参数无标签
`createLive` 签名为 `createLive(_ liveInfo: LiveInfo, completion:)`，第一参数**无标签**：
```swift
// ✅ 正确（无标签）
LiveListStore.shared.createLive(liveInfo) { result in ... }

// ❌ 错误（带标签）
LiveListStore.shared.createLive(liveInfo: liveInfo) { ... }
```

### 3. createLive completion 返回 LiveInfo，不是 Void
`LiveInfoCompletionClosure = (Result<LiveInfo, ErrorInfo>) -> Void`，成功时回调携带服务端确认后的 `LiveInfo`（含 `createTime` 等服务端字段），应使用该对象而非本地构建的对象：
```swift
case .success(let createdLiveInfo):  // ✅ 使用服务端返回的 LiveInfo
    navigateToLiveRoom(liveInfo: createdLiveInfo)
```

### 4. liveName 字节数计算
Swift 中汉字使用 UTF-8 编码，每个汉字占 3 字节：
```swift
let byteCount = liveName.utf8.count  // ✅ 字节数（正确）
let charCount = liveName.count       // ❌ 字符数不等于字节数
```
30 字节 ≈ 10 个汉字 = 30 个英文字母。

### 5. liveID 生成建议
建议在服务端生成 liveID 并下发：
- 仅含字母、数字、下划线、连字符
- 长度控制在 8~32 字节
- 示例：`live_10001_1711593600`
