---
id: live/beauty
platform: ios
---

# 美颜 — iOS 实现

## 前置条件

**依赖安装（Podfile）**
```ruby
pod 'AtomicXCore', '~> 4.0'
```

**前置状态**：
- `DeviceStore.shared.openLocalCamera` 已成功回调（摄像头已打开）
- AtomicXCore 授权包含基础美颜功能

## API 调用

```swift
// 获取单例
let beautyStore = BaseBeautyStore.shared

// 设置磨皮强度（0–9，类型为 Float）
beautyStore.setSmoothLevel(smoothLevel: Float)

// 设置美白强度（0–9，类型为 Float）
beautyStore.setWhitenessLevel(whitenessLevel: Float)

// 设置红润强度（0–9，类型为 Float）
beautyStore.setRuddyLevel(ruddyLevel: Float)

// 重置所有美颜参数
beautyStore.reset()

// 订阅状态变化
beautyStore.state  // StatePublisher<BaseBeautyState>
// BaseBeautyState.smoothLevel: Float
// BaseBeautyState.whitenessLevel: Float
// BaseBeautyState.ruddyLevel: Float
```

> ⚠️ **参数类型为 `Float`，不是 `Int`**。范围 0–9，0 表示关闭，9 为最强。

| 参数 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `smoothLevel` | `Float` | 0–9 | 磨皮强度，0 = 关闭 |
| `whitenessLevel` | `Float` | 0–9 | 美白强度，0 = 关闭 |
| `ruddyLevel` | `Float` | 0–9 | 红润强度，0 = 关闭 |

**UI 值映射**：UI 滑块通常范围 `0.0–1.0`，调用 SDK 前需乘以 9：
```
SDK Float 参数 = UISlider.value（0.0–1.0）× 9.0
```

## 代码示例

### 完整美颜集成

```swift
import AtomicXCore
import Combine

final class BeautyPanelViewModel {

    // MARK: - 属性

    private let beautyStore = BaseBeautyStore.shared
    private var cancellables = Set<AnyCancellable>()

    /// UI 滑块值（0.0-1.0），通过映射驱动 SDK
    @Published var smoothSlider: Float = 0.0
    @Published var whitenessSlider: Float = 0.0
    @Published var ruddySlider: Float = 0.0

    // MARK: - 初始化

    init() {
        // 步骤1: 订阅 SDK 状态，同步到 UI 滑块
        subscribeBeautyState()

        // 步骤2: 订阅 UI 滑块变化，映射后调用 SDK
        bindSliderToSDK()
    }

    // MARK: - 状态订阅（SDK → UI）

    private func subscribeBeautyState() {
        // BaseBeautyState 的属性均为 Float
        beautyStore.state
            .receive(on: DispatchQueue.main)
            .sink { [weak self] state in
                // 将 SDK 参数（Float，0-9）转换为 UI 滑块值（0.0-1.0）
                self?.smoothSlider = state.smoothLevel / 9.0
                self?.whitenessSlider = state.whitenessLevel / 9.0
                self?.ruddySlider = state.ruddyLevel / 9.0
            }
            .store(in: &cancellables)
    }

    // MARK: - UI 绑定（UI → SDK）

    private func bindSliderToSDK() {
        // 磨皮滑块变化 → 调用 SDK
        $smoothSlider
            .dropFirst()  // 跳过初始值，避免重复设置
            .sink { [weak self] value in
                self?.setSmoothLevel(sliderValue: value)
            }
            .store(in: &cancellables)

        // 美白滑块变化 → 调用 SDK
        $whitenessSlider
            .dropFirst()
            .sink { [weak self] value in
                self?.setWhitenessLevel(sliderValue: value)
            }
            .store(in: &cancellables)

        // 红润滑块变化 → 调用 SDK
        $ruddySlider
            .dropFirst()
            .sink { [weak self] value in
                self?.setRuddyLevel(sliderValue: value)
            }
            .store(in: &cancellables)
    }

    // MARK: - 美颜参数设置（含 UI→SDK 值映射）

    /// 设置磨皮（UI 滑块值 0.0-1.0 → SDK Float 0-9）
    func setSmoothLevel(sliderValue: Float) {
        // 步骤3: UI 值 ×9 转换为 SDK Float 参数
        let sdkValue = clamp(sliderValue * 9.0)
        beautyStore.setSmoothLevel(smoothLevel: sdkValue)
    }

    /// 设置美白（UI 滑块值 0.0-1.0 → SDK Float 0-9）
    func setWhitenessLevel(sliderValue: Float) {
        let sdkValue = clamp(sliderValue * 9.0)
        beautyStore.setWhitenessLevel(whitenessLevel: sdkValue)
    }

    /// 设置红润（UI 滑块值 0.0-1.0 → SDK Float 0-9）
    func setRuddyLevel(sliderValue: Float) {
        let sdkValue = clamp(sliderValue * 9.0)
        beautyStore.setRuddyLevel(ruddyLevel: sdkValue)
    }

    /// 重置所有美颜参数（步骤4）
    func resetBeauty() {
        beautyStore.reset()
        // $state 订阅会自动将滑块归零，无需手动设置
    }

    // MARK: - 工具方法

    /// 参数截断，防止超出 0–9 范围
    private func clamp(_ value: Float) -> Float {
        return min(max(value, 0.0), 9.0)
    }
}
```

### UI 滑块绑定（UIKit）

```swift
import UIKit
import Combine

final class BeautyPanelViewController: UIViewController {

    // MARK: - UI 元素

    @IBOutlet weak var smoothSlider: UISlider!          // 磨皮
    @IBOutlet weak var whitenessSlider: UISlider!       // 美白
    @IBOutlet weak var ruddySlider: UISlider!           // 红润
    @IBOutlet weak var resetButton: UIButton!

    private let viewModel = BeautyPanelViewModel()
    private var cancellables = Set<AnyCancellable>()

    // MARK: - 生命周期

    override func viewDidLoad() {
        super.viewDidLoad()
        setupSliders()
        bindViewModel()
    }

    private func setupSliders() {
        [smoothSlider, whitenessSlider, ruddySlider].forEach {
            $0?.minimumValue = 0.0
            $0?.maximumValue = 1.0
        }
    }

    // MARK: - ViewModel 绑定

    private func bindViewModel() {
        // ViewModel → UI：SDK 状态变化驱动滑块位置
        viewModel.$smoothSlider
            .receive(on: DispatchQueue.main)
            .assign(to: \.value, on: smoothSlider)
            .store(in: &cancellables)

        viewModel.$whitenessSlider
            .receive(on: DispatchQueue.main)
            .assign(to: \.value, on: whitenessSlider)
            .store(in: &cancellables)

        viewModel.$ruddySlider
            .receive(on: DispatchQueue.main)
            .assign(to: \.value, on: ruddySlider)
            .store(in: &cancellables)
    }

    // MARK: - 用户交互

    @IBAction func smoothSliderChanged(_ sender: UISlider) {
        viewModel.smoothSlider = sender.value
    }

    @IBAction func whitenessSliderChanged(_ sender: UISlider) {
        viewModel.whitenessSlider = sender.value
    }

    @IBAction func ruddySliderChanged(_ sender: UISlider) {
        viewModel.ruddySlider = sender.value
    }

    @IBAction func resetTapped(_ sender: UIButton) {
        viewModel.resetBeauty()
        // 滑块会通过 $state 订阅自动归零
    }
}
```

### 连麦观众场景复用

```swift
// 连麦观众打开摄像头后，直接复用同一单例
func onCoGuestCameraOpened() {
    // DeviceStore.openLocalCamera 成功后即可设置美颜
    // BaseBeautyStore.shared 持有上次的 Float 参数，无需重新配置
    let currentState = BaseBeautyStore.shared.state
    print("[Beauty] 当前磨皮: \(currentState.smoothLevel), 美白: \(currentState.whitenessLevel)")

    // 若需要重置（连麦场景可能不需要美颜）
    // BaseBeautyStore.shared.reset()
}
```

## 调用时序

```
摄像头打开成功（openLocalCamera .success）
    │
    ▼
BaseBeautyStore.shared                 // 获取单例（无需初始化）
    │
    ▼
订阅 state                             // 建立状态监听，驱动 UI 同步
    │
    ├─ 用户调整磨皮滑块
    │       │
    │       ▼
    │   UISlider.value × 9.0 → setSmoothLevel(smoothLevel: Float)
    │       │
    │       └─ state 更新 → UI 滑块位置同步确认
    │
    ├─ 用户调整美白滑块
    │       │
    │       └─ setWhitenessLevel(whitenessLevel: Float)
    │
    ├─ 用户调整红润滑块
    │       │
    │       └─ setRuddyLevel(ruddyLevel: Float)
    │
    ├─ 用户点击重置
    │       │
    │       ▼
    │   reset()
    │       │
    │       └─ state 更新（所有 Float 值归 0）→ UI 滑块自动归零
    │
    └─ 关闭摄像头 / 退出直播间
            │
            ▼
        cancellables.removeAll()      // 清理订阅
```

## 平台特有注意事项

### 1. 参数类型为 Float
`setSmoothLevel`、`setWhitenessLevel`、`setRuddyLevel` 的参数和 `BaseBeautyState` 的所有属性均为 `Float`，不是 `Int`。不要对参数做 `Int()` 截断，否则会丢失精度（如 4.5 会变成 4）。

### 2. 真机测试
iOS 模拟器不支持摄像头采集，美颜效果**必须在真机上验证**。模拟器上调用美颜接口不会报错，但无法看到实际效果。

### 3. 滑块防抖
用户拖动滑块时会高频触发 `valueChanged`，建议对 SDK 调用做 100ms 防抖，避免过高的调用频率影响性能：

```swift
private var beautyDebounceTimer: Timer?

func setSmoothLevelDebounced(sliderValue: Float) {
    beautyDebounceTimer?.invalidate()
    beautyDebounceTimer = Timer.scheduledTimer(
        withTimeInterval: 0.1,
        repeats: false
    ) { [weak self] _ in
        self?.viewModel.setSmoothLevel(sliderValue: sliderValue)
    }
}
```

### 4. App 进入后台
iOS 后台时摄像头采集暂停，美颜效果自动停止作用。App 重新进入前台且摄像头恢复采集后，美颜参数会自动继续生效（单例保留了上次的 Float 参数设置），无需重新调用。

### 5. 与滤镜功能的关系
`BaseBeautyStore` 仅提供基础美颜（磨皮/美白/红润）。如需高级美颜（瘦脸、大眼等）或滤镜功能，需要接入腾讯特效 SDK（XMagic），配置不同的授权。
