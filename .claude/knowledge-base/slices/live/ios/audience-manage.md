---
id: live/audience-manage
platform: ios
---

# 观众管理 — iOS 实现

## 前置条件

**依赖安装（Podfile）**
```ruby
pod 'AtomicXCore', '~> 4.0'
```

**前置状态**：
- `LoginStore.shared.isLogin == true`
- 已成功进入直播间
- 当前用户为房主（执行 `setAdministrator` / `revokeAdministrator`）或管理员（执行 `kickUserOutOfRoom`）

## API 调用

```swift
// 创建观众管理模块（通过 LiveAudienceStore 工厂方法）
let liveAudienceStore = LiveAudienceStore.create(liveID: liveID)

// 踢出观众（需房主或管理员权限）
liveAudienceStore.kickUserOutOfRoom(
    userID: String,
    completion: CompletionClosure?
)
// CompletionClosure = (Result<Void, ErrorInfo>) -> Void

// 设置管理员（仅房主）
liveAudienceStore.setAdministrator(
    userID: String,
    completion: CompletionClosure?
)

// 撤销管理员（仅房主）
liveAudienceStore.revokeAdministrator(
    userID: String,
    completion: CompletionClosure?
)

// 禁言 / 解除禁言（需房主或管理员权限）
liveAudienceStore.disableSendMessage(
    userID: String,
    isDisable: Bool,
    completion: CompletionClosure?
)

// 订阅观众管理事件
liveAudienceStore.liveAudienceEventPublisher  // PassthroughSubject<LiveAudienceEvent, Never>
// 包含：
// .onAudienceMessageDisabled(audience: LiveUserInfo, isDisable: Bool)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `userID` | `String` | 目标用户的唯一标识 |
| `isDisable` | `Bool` | `true` = 禁言，`false` = 解除禁言 |
| `completion` | `CompletionClosure?` | `(Result<Void, ErrorInfo>) -> Void`，`ErrorInfo` 含 `.code` 和 `.message` |

## 代码示例

### 完整管理操作集成

```swift
import AtomicXCore
import Combine

final class AudienceManageManager {

    // MARK: - 属性

    private let audienceStore: LiveAudienceStore
    private var cancellables = Set<AnyCancellable>()

    /// 当前用户角色（从 LiveStore 获取）
    private var currentUserRole: UserRole = .audience

    // MARK: - 初始化

    init(liveID: String) {
        // 通过工厂方法创建，确保每个直播间独立实例
        self.audienceStore = LiveAudienceStore.create(liveID: liveID)
        subscribeAudienceEvents()
    }

    // MARK: - 监听观众管理事件

    private func subscribeAudienceEvents() {
        audienceStore.liveAudienceEventPublisher
            .receive(on: DispatchQueue.main)
            .sink { [weak self] event in
                guard let self else { return }
                switch event {
                case .onAudienceMessageDisabled(let audience, let isDisable):
                    // 某用户禁言状态变更，刷新列表 UI
                    print("[Manage] 用户 \(audience.userID) 禁言状态: \(isDisable)")
                case .onAudienceJoined, .onAudienceLeft:
                    break
                }
            }
            .store(in: &cancellables)
    }

    // MARK: - 权限校验

    /// 校验是否有踢人权限
    private func canKick(targetRole: UserRole) -> Bool {
        switch currentUserRole {
        case .owner:
            // 房主可以踢任何人
            return true
        case .admin:
            // 管理员只能踢普通观众，不能踢其他管理员或房主
            return targetRole == .audience
        case .audience:
            return false
        }
    }

    /// 校验是否有设置/撤销管理员权限
    private func canManageAdmin() -> Bool {
        return currentUserRole == .owner
    }

    // MARK: - 踢出观众

    func kickUser(_ userID: String,
                  targetRole: UserRole,
                  completion: ((Result<Void, ErrorInfo>) -> Void)? = nil) {
        // 步骤1: 调用前校验权限
        guard canKick(targetRole: targetRole) else {
            print("[Manage] 权限不足，无法踢出用户: \(userID)")
            completion?(.failure(ErrorInfo(code: -1, message: "权限不足，无法执行此操作")))
            return
        }

        // 步骤2: 踢出用户
        audienceStore.kickUserOutOfRoom(userID: userID) { result in
            DispatchQueue.main.async {
                switch result {
                case .success:
                    print("[Manage] 已踢出用户: \(userID)")
                    completion?(.success(()))
                case .failure(let error):
                    print("[Manage] 踢出失败 code=\(error.code) msg=\(error.message)")
                    completion?(.failure(error))
                }
            }
        }
    }

    // MARK: - 管理员设置（仅房主）

    func setAdministrator(_ userID: String,
                          completion: ((Result<Void, ErrorInfo>) -> Void)? = nil) {
        // 步骤3: 校验房主权限
        guard canManageAdmin() else {
            completion?(.failure(ErrorInfo(code: -1, message: "权限不足，无法执行此操作")))
            return
        }

        audienceStore.setAdministrator(userID: userID) { result in
            DispatchQueue.main.async {
                switch result {
                case .success:
                    print("[Manage] 已设置管理员: \(userID)")
                    completion?(.success(()))
                case .failure(let error):
                    print("[Manage] 设置管理员失败 code=\(error.code) msg=\(error.message)")
                    completion?(.failure(error))
                }
            }
        }
    }

    func revokeAdministrator(_ userID: String,
                             completion: ((Result<Void, ErrorInfo>) -> Void)? = nil) {
        guard canManageAdmin() else {
            completion?(.failure(ErrorInfo(code: -1, message: "权限不足，无法执行此操作")))
            return
        }

        audienceStore.revokeAdministrator(userID: userID) { result in
            DispatchQueue.main.async {
                switch result {
                case .success:
                    print("[Manage] 已撤销管理员: \(userID)")
                    completion?(.success(()))
                case .failure(let error):
                    print("[Manage] 撤销管理员失败 code=\(error.code) msg=\(error.message)")
                    completion?(.failure(error))
                }
            }
        }
    }

    // MARK: - 禁言管理

    func muteUser(_ userID: String,
                  completion: ((Result<Void, ErrorInfo>) -> Void)? = nil) {
        audienceStore.disableSendMessage(userID: userID, isDisable: true) { result in
            DispatchQueue.main.async {
                switch result {
                case .success:
                    print("[Manage] 已禁言用户: \(userID)")
                    completion?(.success(()))
                case .failure(let error):
                    print("[Manage] 禁言失败 code=\(error.code) msg=\(error.message)")
                    completion?(.failure(error))
                }
            }
        }
    }

    func unmuteUser(_ userID: String,
                    completion: ((Result<Void, ErrorInfo>) -> Void)? = nil) {
        audienceStore.disableSendMessage(userID: userID, isDisable: false) { result in
            DispatchQueue.main.async {
                completion?(result)
            }
        }
    }

    // MARK: - 错误处理

    func handleManageError(_ error: ErrorInfo, for operation: String) {
        switch error.code {
        case -2300:
            showAlert(title: "权限不足", message: "该操作仅房主可执行")
        case -2301:
            showAlert(title: "权限不足", message: "该操作需要管理员或房主权限")
        case -2302:
            showToast("该用户已不在直播间")
        default:
            showToast("\(operation)失败：\(error.message)")
        }
    }
}

// MARK: - 用户角色

enum UserRole {
    case owner      // 房主
    case admin      // 管理员
    case audience   // 普通观众
}
```

### 观众列表操作菜单

```swift
// 观众列表 Cell 上的操作菜单（权限判断）
func showAudienceActionMenu(for audience: LiveUserInfo,
                            audienceRole: UserRole,
                            currentRole: UserRole) {
    var actions: [UIAlertAction] = []

    // 仅房主或管理员可踢人（管理员只能踢普通观众）
    let canKick = (currentRole == .owner) ||
                  (currentRole == .admin && audienceRole == .audience)
    if canKick {
        actions.append(UIAlertAction(title: "踢出直播间", style: .destructive) { [weak self] _ in
            self?.confirmKick(userID: audience.userID)
        })
    }

    // 仅房主可禁言/设置管理员
    if currentRole == .owner {
        actions.append(UIAlertAction(title: "禁言", style: .default) { [weak self] _ in
            self?.manageManager.muteUser(audience.userID) { result in
                if case .failure(let error) = result {
                    self?.manageManager.handleManageError(error, for: "禁言")
                }
            }
        })

        if audienceRole == .audience {
            actions.append(UIAlertAction(title: "设为管理员", style: .default) { [weak self] _ in
                self?.manageManager.setAdministrator(audience.userID) { result in
                    if case .failure(let error) = result {
                        self?.manageManager.handleManageError(error, for: "设为管理员")
                    }
                }
            })
        } else if audienceRole == .admin {
            actions.append(UIAlertAction(title: "撤销管理员", style: .default) { [weak self] _ in
                self?.manageManager.revokeAdministrator(audience.userID) { result in
                    if case .failure(let error) = result {
                        self?.manageManager.handleManageError(error, for: "撤销管理员")
                    }
                }
            })
        }
    }

    guard !actions.isEmpty else { return }

    let sheet = UIAlertController(
        title: audience.userName,
        message: nil,
        preferredStyle: .actionSheet
    )
    actions.forEach { sheet.addAction($0) }
    sheet.addAction(UIAlertAction(title: "取消", style: .cancel))
    present(sheet, animated: true)
}

private func confirmKick(userID: String) {
    let alert = UIAlertController(
        title: "踢出直播间",
        message: "确定要将该用户移出直播间吗？",
        preferredStyle: .alert
    )
    alert.addAction(UIAlertAction(title: "确定", style: .destructive) { [weak self] _ in
        self?.manageManager.kickUser(userID, targetRole: .audience) { result in
            if case .failure(let error) = result {
                self?.manageManager.handleManageError(error, for: "踢出用户")
            }
        }
    })
    alert.addAction(UIAlertAction(title: "取消", style: .cancel))
    present(alert, animated: true)
}
```

## 调用时序

```
进入直播间
    │
    ▼
LiveAudienceStore.create(liveID:)
    │
    ▼
订阅 liveAudienceEventPublisher        // 监听禁言状态变更等事件
    │
    ├─ 房主操作流程
    │       │
    │       ├─ setAdministrator(userID:)
    │       │       ├─ .success → 更新观众列表角色标记
    │       │       └─ .failure(code: -2300) → 非房主，隐藏入口
    │       │
    │       ├─ revokeAdministrator(userID:)
    │       │       ├─ .success → 更新观众列表角色标记
    │       │       └─ .failure(code: -2300) → 非房主，隐藏入口
    │       │
    │       └─ disableSendMessage(userID:isDisable:)
    │               ├─ .success → onAudienceMessageDisabled 事件推送
    │               └─ .failure(ErrorInfo) → 展示 error.message
    │
    └─ 房主/管理员踢人流程
            │
            ├─ 权限校验（canKick）
            ├─ 二次确认弹窗
            └─ kickUserOutOfRoom(userID:)
                    ├─ .success → 刷新观众列表
                    ├─ .failure(code: -2301) → 权限不足
                    └─ .failure(code: -2302) → 用户已离开，刷新列表
```

## 平台特有注意事项

### 1. ErrorInfo 替代 Error
所有 completion 使用 `(Result<Void, ErrorInfo>) -> Void`，不是 `Result<Void, Error>`。错误信息通过 `error.code`（Int）和 `error.message`（String）访问，不要调用 `localizedDescription`。

### 2. 管理员权限 UI 实时刷新
当房主撤销某用户的管理员权限时，该用户应立即看到操作按钮的变化（如隐藏踢人按钮）。通过订阅观众列表状态变化来驱动 UI 更新，不要依赖本地缓存的角色信息。

### 3. iPad 上的 ActionSheet
在 iPad 上，`UIAlertController` 的 `.actionSheet` 样式需要设置 `popoverPresentationController` 的 `sourceView` 和 `sourceRect`，否则会崩溃。

```swift
if let popover = sheet.popoverPresentationController {
    popover.sourceView = cell
    popover.sourceRect = cell.bounds
}
```
