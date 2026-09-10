---
id: live/coguest-apply
platform: ios
api_docs:
  - title: CoGuestStore
    url: https://tencent-rtc.github.io/TUIKit_iOS/documentation/atomicxcore/cogueststore/
---

# 观众申请连麦 — iOS 实现

## 前置条件 [必填]

**通用依赖**：见 [login-auth 平台 slice](../login-auth.md)（SDK 安装、Info.plist 权限声明）

**额外依赖**：无

**前置状态**：
- `LoginStore.shared.isLogin == true`（登录成功）（→ live/login-auth）
- 已进入直播间，持有有效的 `liveID`（→ live/audience-watch）
- `CoGuestStore` 已通过 `create(liveID:)` 初始化

## 代码示例 [必填]

### 观众端：申请 → 等待 → 开设备 → 连麦 → 断开

```swift
import AtomicXCore
import Combine

final class AudienceCoGuestViewModel: ObservableObject {

    // MARK: 状态

    enum CoGuestStatus {
        case idle           // 未连麦
        case applying       // 申请中
        case connected      // 连麦中
    }

    @Published var status: CoGuestStatus = .idle
    @Published var errorMessage: String?

    private let coGuestStore: CoGuestStore
    private var cancellables = Set<AnyCancellable>()
    private let applyTimeout: TimeInterval = 30

    init(liveID: String) {
        self.coGuestStore = CoGuestStore.create(liveID: liveID)
        observeGuestEvents()
    }

    // MARK: - 观众端事件订阅

    private func observeGuestEvents() {
        coGuestStore.guestEventPublisher
            .receive(on: DispatchQueue.main)
            .sink { [weak self] event in
                guard let self else { return }
                switch event {
                case .onGuestApplicationResponded(let isAccept, let hostUser):
                    if isAccept {
                        // ✅ 申请通过，立即开启设备
                        print("[CoGuest] 主播 \(hostUser.userName) 已同意申请")
                        self.openDevicesAfterAccepted()
                    } else {
                        // 申请被拒绝
                        self.status = .idle
                        self.errorMessage = "连麦申请被主播拒绝"
                    }

                case .onGuestApplicationNoResponse(let reason):
                    // 超时未响应
                    self.status = .idle
                    self.errorMessage = "申请超时，请重试"
                    print("[CoGuest] 申请超时，原因: \(reason)")

                case .onKickedOffSeat(let seatIndex, let hostUser):
                    // 被主播踢下麦位
                    self.closeDevicesAfterDisconnect()
                    self.status = .idle
                    self.errorMessage = "已被主播移出麦位（座位 \(seatIndex)）"
                    print("[CoGuest] 被 \(hostUser.userName) 踢下麦位 \(seatIndex)")

                case .onHostInvitationReceived(let hostUser):
                    // 收到主播邀请，可展示弹窗供用户选择
                    print("[CoGuest] 收到主播 \(hostUser.userName) 的邀请")

                case .onHostInvitationCancelled(let hostUser):
                    // 主播取消邀请
                    print("[CoGuest] 主播 \(hostUser.userName) 取消了邀请")
                }
            }
            .store(in: &cancellables)
    }

    // MARK: - 申请连麦
    // seatIndex: Int 默认 -1 表示自动分配麦位

    func applyForSeat(seatIndex: Int = -1) {
        guard status == .idle else { return }
        status = .applying

        coGuestStore.applyForSeat(
            seatIndex: seatIndex,
            timeout: applyTimeout,
            extraInfo: nil
        ) { [weak self] result in
            guard let self else { return }
            DispatchQueue.main.async {
                switch result {
                case .success:
                    // 申请发送成功，等待主播响应（通过 guestEventPublisher 回调）
                    print("[CoGuest] 申请已发送，等待主播响应...")
                case .failure(let error):
                    self.status = .idle
                    if error.code == -2340 {
                        self.errorMessage = "当前连麦人数已达上限，请稍后再试"
                    } else {
                        self.errorMessage = "申请失败：\(error.message)"
                    }
                }
            }
        }
    }

    // MARK: - 取消申请

    func cancelApplication() {
        guard status == .applying else { return }
        coGuestStore.cancelApplication { [weak self] _ in
            DispatchQueue.main.async {
                self?.status = .idle
            }
        }
    }

    // MARK: - 接受主播邀请（inviterID 为邀请方主播的 userID）

    func acceptInvitation(inviterID: String) {
        coGuestStore.acceptInvitation(inviterID: inviterID) { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success:
                    self?.openDevicesAfterAccepted()
                case .failure(let error):
                    self?.errorMessage = "接受邀请失败：\(error.message)"
                }
            }
        }
    }

    // MARK: - 拒绝主播邀请

    func rejectInvitation(inviterID: String) {
        coGuestStore.rejectInvitation(inviterID: inviterID) { result in
            if case .failure(let error) = result {
                print("[CoGuest] 拒绝邀请失败 code=\(error.code)")
            }
        }
    }

    // MARK: - 申请通过后开设备

    private func openDevicesAfterAccepted() {
        // 前置：设备控制能力（→ live/device-control）
        // 先开麦克风
        DeviceStore.shared.openLocalMicrophone { [weak self] micResult in
            guard let self else { return }
            switch micResult {
            case .failure(let error):
                print("[CoGuest] 麦克风打开失败 code=\(error.code)")
                self.errorMessage = "麦克风打开失败，请检查权限"
                // 麦克风失败，断开连麦
                self.coGuestStore.disConnect(completion: nil)
                DispatchQueue.main.async { self.status = .idle }
            case .success:
                // 再开摄像头
                DeviceStore.shared.openLocalCamera(isFront: true) { cameraResult in
                    DispatchQueue.main.async {
                        if case .failure(let error) = cameraResult {
                            print("[CoGuest] 摄像头打开失败 code=\(error.code)，以纯音频模式连麦")
                        }
                        self.status = .connected
                    }
                }
            }
        }
    }

    // MARK: - 主动断开连麦

    func disconnect() {
        guard status == .connected else { return }
        coGuestStore.disConnect { [weak self] _ in
            self?.closeDevicesAfterDisconnect()
            DispatchQueue.main.async { self?.status = .idle }
        }
    }

    // MARK: - 断开后关闭设备

    private func closeDevicesAfterDisconnect() {
        // 前置：设备控制能力（→ live/device-control）
        DeviceStore.shared.closeLocalCamera()
        DeviceStore.shared.closeLocalMicrophone()
        print("[CoGuest] 连麦已断开，设备已关闭")
    }
}
```

---

### 主播端：监听申请 → 同意 / 拒绝 → 邀请 → 管理连麦

```swift
import AtomicXCore
import Combine

final class HostCoGuestViewModel: ObservableObject {

    // MARK: 状态

    @Published var pendingApplicants: [LiveUserInfo] = []   // 待审批申请列表
    @Published var connectedGuests: [SeatUserInfo]  = []    // 当前连麦列表

    private let coGuestStore: CoGuestStore
    private var cancellables = Set<AnyCancellable>()

    init(liveID: String) {
        self.coGuestStore = CoGuestStore.create(liveID: liveID)
        observeHostEvents()
        observeState()
    }

    // MARK: - 主播端事件订阅

    private func observeHostEvents() {
        coGuestStore.hostEventPublisher
            .receive(on: DispatchQueue.main)
            .sink { [weak self] event in
                guard let self else { return }
                switch event {
                case .onGuestApplicationReceived(let guestUser):
                    // 新收到观众申请，添加到待审批列表
                    if !self.pendingApplicants.contains(where: { $0.userID == guestUser.userID }) {
                        self.pendingApplicants.append(guestUser)
                    }

                case .onGuestApplicationCancelled(let guestUser):
                    // 观众撤回了申请
                    self.pendingApplicants.removeAll { $0.userID == guestUser.userID }

                case .onGuestApplicationProcessedByOtherHost(let guestUser, let hostUser):
                    // 申请被其他主播处理（多主播场景）
                    self.pendingApplicants.removeAll { $0.userID == guestUser.userID }
                    print("[Host] \(guestUser.userName) 的申请已被 \(hostUser.userName) 处理")

                case .onHostInvitationResponded(let isAccept, let guestUser):
                    if isAccept {
                        print("[Host] \(guestUser.userName) 接受了邀请")
                    } else {
                        print("[Host] \(guestUser.userName) 拒绝了邀请")
                    }

                case .onHostInvitationNoResponse(let guestUser, let reason):
                    print("[Host] \(guestUser.userName) 未响应邀请，原因: \(reason)")
                }
            }
            .store(in: &cancellables)
    }

    // MARK: - 状态订阅（实时同步连麦列表）

    private func observeState() {
        coGuestStore.state
            .map(\.connected)
            .receive(on: DispatchQueue.main)
            .assign(to: &$connectedGuests)
    }

    // MARK: - 同意申请

    func acceptApplication(userID: String) {
        coGuestStore.acceptApplication(userID: userID) { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success:
                    self?.pendingApplicants.removeAll { $0.userID == userID }
                    print("[Host] 已同意 \(userID) 的连麦申请")
                case .failure(let error):
                    print("[Host] 同意申请失败 code=\(error.code) msg=\(error.message)")
                }
            }
        }
    }

    // MARK: - 拒绝申请

    func rejectApplication(userID: String) {
        coGuestStore.rejectApplication(userID: userID) { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success:
                    self?.pendingApplicants.removeAll { $0.userID == userID }
                    print("[Host] 已拒绝 \(userID) 的连麦申请")
                case .failure(let error):
                    print("[Host] 拒绝申请失败 code=\(error.code) msg=\(error.message)")
                }
            }
        }
    }

    // MARK: - 主播邀请观众上麦

    func inviteToSeat(userID: String, seatIndex: Int = -1) {
        coGuestStore.inviteToSeat(
            userID: userID,
            seatIndex: seatIndex,
            timeout: 30,
            extraInfo: nil
        ) { result in
            if case .failure(let error) = result {
                print("[Host] 邀请失败 code=\(error.code) msg=\(error.message)")
            }
        }
    }

    // MARK: - 主播踢出已连麦观众

    func disconnectGuest() {
        coGuestStore.disConnect { result in
            DispatchQueue.main.async {
                if case .failure(let error) = result {
                    print("[Host] 断开失败 code=\(error.code) msg=\(error.message)")
                }
            }
        }
    }
}
```

## 调用时序 [条件必填：多角色异步交互 或 回调嵌套 ≥3 层]

```
【观众端】
用户点击"申请连麦"
        │
        ▼
coGuestStore.applyForSeat(seatIndex: -1, timeout: 30, extraInfo: nil)
        │
        ├─ .failure(code: -2340) → 麦位满，提示用户
        ├─ .failure(ErrorInfo) → 展示 error.message
        │
        └─ .success（申请发出，等待主播响应）
                │
                ▼（guestEventPublisher 回调）
        .onGuestApplicationResponded(isAccept:hostUser:)
                │
                ├─ isAccept == false → 提示被拒，status = .idle
                │
                └─ isAccept == true
                        │
                        ▼
                openLocalMicrophone()
                        │
                        ├─ .failure → disConnect，提示权限问题
                        └─ .success
                                │
                                ▼
                        openLocalCamera(isFront: true)
                                └─ status = .connected（连麦中）

        .onKickedOffSeat(seatIndex:hostUser:) → closeDevices() → status = .idle
        .onGuestApplicationNoResponse(reason:) → status = .idle，提示超时

【主播端（并行）】
订阅 hostEventPublisher
        │
        ▼
.onGuestApplicationReceived(guestUser:) → 加入待审批列表
        │
        ├─ 主播点击"同意" → acceptApplication(userID:)
        │       └─ 从 pendingApplicants 移除
        └─ 主播点击"拒绝" → rejectApplication(userID:)
                └─ 从 pendingApplicants 移除

.onGuestApplicationCancelled(guestUser:) → 从待审批列表移除
```

## 平台特有注意事项 [必填：至少 1 条]

### 1. seatIndex 参数
`applyForSeat` 包含 `seatIndex: Int` 参数（默认值 `-1`），`-1` 表示由系统自动分配麦位。若业务有固定麦位布局（如卡拉 OK 多人），可传具体的麦位索引（从 0 开始）。
```swift
// ✅ 自动分配麦位
coGuestStore.applyForSeat(seatIndex: -1, timeout: 30, extraInfo: nil)

// ✅ 指定麦位（如卡拉 OK 场景，固定 6 个座位）
coGuestStore.applyForSeat(seatIndex: 2, timeout: 30, extraInfo: nil)
```

### 2. acceptInvitation / rejectInvitation 参数为 inviterID
观众接受/拒绝主播邀请时，参数名为 `inviterID`（邀请方），不是 `userID`。不要与 `acceptApplication(userID:)` 混淆，两者语义不同。
```swift
// ✅ 正确：传主播的 userID 作为 inviterID
coGuestStore.acceptInvitation(inviterID: hostUserID, completion: nil)

// ❌ 错误：传了观众自己的 userID，接受邀请永远失败
coGuestStore.acceptInvitation(inviterID: selfUserID, completion: nil)
```

### 3. Combine cancellable 生命周期管理
`hostEventPublisher` 和 `guestEventPublisher` 是 Combine Publisher。订阅时返回的 `AnyCancellable` 必须存储到 ViewModel/ViewController 的属性中（如 `Set<AnyCancellable>`），否则订阅会立即被释放，导致主播收不到任何申请事件。

### 4. 连麦中 App 进入后台
iOS 系统进入后台时会挂起摄像头采集，但麦克风仍可持续（需在 `Info.plist` 开启 `audio` 后台模式）。连麦场景建议在 App 进入后台时关闭摄像头（`closeLocalCamera()`），避免观众看到定格画面。
```swift
// ✅ 监听进入后台，主动关闭摄像头
NotificationCenter.default.addObserver(
    forName: UIApplication.didEnterBackgroundNotification,
    object: nil, queue: .main
) { _ in
    DeviceStore.shared.closeLocalCamera()
}

// ❌ 不处理后台切换，观众看到定格黑屏画面
```

### 5. `-2340` 麦位超限
错误码 `-2340` 由服务端返回，表示当前直播间连麦人数已达上限。此时应禁用"申请连麦"按钮，并订阅 `CoGuestState.connected` 列表变化：当连麦人数减少时，自动重新启用按钮。
```swift
// ✅ 区分 -2340 给出有意义的提示
case .failure(let error):
    if error.code == -2340 {
        self.errorMessage = "当前连麦人数已达上限，请稍后再试"
        self.isApplyButtonDisabled = true
    }

// ❌ 所有错误统一提示，用户不知道为什么失败
case .failure(let error):
    self.errorMessage = "操作失败"
```

## 代码生成约束 [必填]

本 section 供 AI 在生成/验证代码时使用，定义了此 slice 在 iOS 平台上的硬性约束。
所有规则必须基于实际 SDK 行为核实后填入，不允许凭经验推测。

### 编译必要条件 [必填]

- **通用条件**：见 [login-auth 平台 slice](login-auth.md)（pod 安装、Info.plist 权限）
- **额外导入**: `TODO: 列出本 slice 相对 login-auth 额外需要的 import（例如 Combine）`
- **最低平台版本**: `TODO: 若高于 login-auth 基线（iOS 13.0+），填入具体版本并说明原因`

### 生成规则 [必填]

#### MUST（生成时必须包含）

<!-- TODO: 基于实际 SDK 行为填入本 slice 独有的 MUST 规则。
     每条格式：**规则** — 违反后果。**Verify**: 可检查手段
     规则必须来自 SDK 文档 / 实测 / 研发明确约定，不要凭经验推测。
-->

1. `TODO: 规则 1` — `TODO: 违反后果`
   **Verify**: `TODO: grep 正则 / 编译报错 / 运行时日志 / 人工观察`
2. `TODO: 规则 2 ...`

#### MUST NOT（生成时绝不能出现）

<!-- TODO: 基于实际 SDK 行为填入本 slice 独有的 MUST NOT 规则。
     重点是「看起来能跑但逻辑错误」的写法 — 需要 SDK 语义支撑才能列出。
-->

1. `TODO: 规则 1` — `TODO: 违反后果`
   **Verify**: `TODO: 可检查手段`
2. `TODO: 规则 2 ...`

### 集成检查点 [必填]

<!-- TODO: 结合本 slice 在已有 iOS 项目中的集成经验填入，例如：
     - 是否与项目已有的 SDK 初始化冲突
     - 是否依赖其他 slice 的前置状态（引用具体 slice ID）
     - 对已有代码的侵入性（新增文件 vs 修改已有文件）
-->

- `TODO: 集成检查点 1`
- `TODO: 集成检查点 2`

## 验证矩阵 [必填]

AI 生成代码后或人工 review 时，自上而下跑一遍即可完成验收。

<!-- TODO: 基于本 slice 实际填好的 MUST / MUST NOT 规则，逐条映射到矩阵的层级 1/2。
     另外补充：
     - 至少 1 条层级 3（运行时日志锚点），基于代码示例中实际的 print 语句填入
     - 至少 1 条层级 4（业务行为），基于产品级 ALWAYS / NEVER 的运行时体现填入
-->

| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | `TODO: 模块导入齐全` | `xcodebuild build -workspace {Project}.xcworkspace -scheme {Scheme} -destination 'platform=iOS Simulator,name=iPhone 16' -quiet` | exit code 0 |
| 1. 编译级 | `TODO: 最低平台版本达标` | 查 `IPHONEOS_DEPLOYMENT_TARGET` | `TODO: ≥ 版本` |
| 2. 静态规则级 | `TODO: 对应 MUST 规则 1` | `TODO: grep 正则` | `TODO: 匹配条件` |
| 2. 静态规则级 | `TODO: 对应 MUST NOT 规则 1` | `TODO: grep 正则` | `TODO: 不应匹配` |
| 3. 运行时级 | `TODO: 关键路径日志` | `TODO: 触发操作 → 查 Xcode 控制台` | `TODO: 日志内容` |
| 4. 业务行为级 | `TODO: 业务语义观察` | `TODO: 操作步骤` | `TODO: UI / 硬件状态` |
