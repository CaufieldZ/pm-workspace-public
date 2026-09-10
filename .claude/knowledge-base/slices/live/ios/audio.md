---
id: live/audio
platform: ios
---

# 音效管理 — iOS 实现

## 前置条件

**依赖安装（Podfile）**
```ruby
pod 'AtomicXCore', '~> 4.0'
```

**前置状态**：
- `LoginStore.shared.isLogin == true`（登录成功后才可调用音效接口）
- `DeviceStore.shared.openLocalMicrophone` 已成功回调（麦克风打开后音效才生效）
- 耳返功能须插入**有线耳机**；蓝牙耳机**不支持**耳返（见注意事项 1）

## API 调用

```swift
// ── 采集音量（DeviceStore）──────────────────────────────────────
// 设置麦克风采集音量；范围 0–100，默认 100（影响观众收到的音量）
DeviceStore.shared.setCaptureVolume(volume: Int)

// ── 耳返（AudioEffectStore）────────────────────────────────────
// 开启 / 关闭耳返（须插入有线耳机；蓝牙耳机不支持）
AudioEffectStore.shared.setVoiceEarMonitorEnable(enable: Bool)

// 设置耳返音量；范围 0–100，默认 100（仅主播本人通过有线耳机听到）
AudioEffectStore.shared.setVoiceEarMonitorVolume(volume: Int)

// ── 变声（AudioEffectStore）────────────────────────────────────
// 设置变声类型；传 .none 还原原声
AudioEffectStore.shared.setAudioChangerType(type: AudioChangerType)

// ── 混响（AudioEffectStore）────────────────────────────────────
// 设置混响类型；传 .none 还原
AudioEffectStore.shared.setAudioReverbType(type: AudioReverbType)

// ── 重置（AudioEffectStore）────────────────────────────────────
// 离房后效果自动失效；但建议主动调用以保持状态清洁
AudioEffectStore.shared.reset()
```

> ⚠️ **耳返音量范围 0–100，不是 0–150**。超出 100 的值行为未定义。

| 参数 | 类型 | 说明 |
|------|------|------|
| `volume` | `Int` | 音量值，范围 `0–100`，默认 `100` |
| `enable` | `Bool` | `true` 开启耳返，`false` 关闭 |
| `type` (AudioChangerType) | `AudioChangerType` | 变声类型，见下方枚举 |
| `type` (AudioReverbType) | `AudioReverbType` | 混响类型，见下方枚举 |

### AudioChangerType 枚举（完整）

| 值 | 说明 |
|----|------|
| `.none` | 原声（无变声） |
| `.child` | 儿童音 |
| `.littleGirl` | 萝莉音 |
| `.man` | 男声 |
| `.ethereal` | 空灵 |
| `.cold` | 冷酷 |
| `.foreignerr` | 外国腔 |
| `.heavyMachinery` | 重型机械 |
| `.heavyMetal` | 重金属 |
| `.strongCurrent` | 强电流 |
| `.fatso` | 肥仔 |
| `.trappedBeast` | 困兽 |

### AudioReverbType 枚举（完整）

| 值 | 说明 |
|----|------|
| `.none` | 无混响 |
| `.ktv` | KTV |
| `.smallRoom` | 小房间 |
| `.auditorium` | 礼堂 |
| `.loud` | 大型会场 |
| `.deep` | 深沉 |
| `.magnetic` | 磁性 |
| `.metallic` | 金属感 |

## 代码示例

```swift
import AtomicXCore
import AVFoundation
import Combine

// MARK: - 音效面板 ViewModel

final class AudioEffectPanelViewModel: ObservableObject {

    // MARK: Published 状态（与 UI 双向绑定）

    @Published var captureVolume: Int = 100         // 采集音量 (0–100)
    @Published var earMonitorEnabled: Bool = false  // 耳返开关
    @Published var earMonitorVolume: Int = 100      // 耳返音量 (0–100)
    @Published var changerType: AudioChangerType = .none    // 变声
    @Published var reverbType: AudioReverbType = .none      // 混响
    @Published var isWiredHeadphoneConnected: Bool = false  // 有线耳机连接状态

    private var cancellables = Set<AnyCancellable>()

    init() {
        syncStateFromStore()
        observeAudioRoute()
    }

    // MARK: - 状态同步（从 Store 读取当前值）

    private func syncStateFromStore() {
        // 从 DeviceStore 同步采集音量
        DeviceStore.shared.state
            .map(\.captureVolume)
            .receive(on: DispatchQueue.main)
            .assign(to: &$captureVolume)

        // 从 AudioEffectStore 同步音效状态
        AudioEffectStore.shared.state
            .receive(on: DispatchQueue.main)
            .sink { [weak self] state in
                guard let self else { return }
                self.earMonitorEnabled = state.isEarMonitorOpened
                self.earMonitorVolume  = state.earMonitorVolume   // Int, 0–100
                self.changerType       = state.audioChangerType
                self.reverbType        = state.audioReverbType
            }
            .store(in: &cancellables)
    }

    // MARK: - 耳机路由监听
    // ⚠️ 只检测有线耳机（.headphones），蓝牙耳机不支持耳返

    private func observeAudioRoute() {
        isWiredHeadphoneConnected = checkWiredHeadphoneConnected()

        NotificationCenter.default
            .publisher(for: AVAudioSession.routeChangeNotification)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in
                guard let self else { return }
                self.isWiredHeadphoneConnected = self.checkWiredHeadphoneConnected()
                // 有线耳机断开时自动关闭耳返
                if !self.isWiredHeadphoneConnected && self.earMonitorEnabled {
                    self.setEarMonitorEnabled(false)
                }
            }
            .store(in: &cancellables)
    }

    private func checkWiredHeadphoneConnected() -> Bool {
        let outputs = AVAudioSession.sharedInstance().currentRoute.outputs
        // 仅检测有线耳机（.headphones），蓝牙耳机（.bluetoothA2DP）不支持耳返
        return outputs.contains { $0.portType == .headphones }
    }

    // MARK: - 采集音量控制（范围 0–100）

    func setCaptureVolume(_ volume: Int) {
        let clamped = max(0, min(100, volume))
        DeviceStore.shared.setCaptureVolume(volume: clamped)
    }

    // MARK: - 耳返控制

    func setEarMonitorEnabled(_ enable: Bool) {
        guard !enable || isWiredHeadphoneConnected else {
            // 未接有线耳机时禁止开启，通知 UI 展示提示
            print("[AudioEffect] 耳返需要插入有线耳机，蓝牙耳机不支持")
            return
        }
        AudioEffectStore.shared.setVoiceEarMonitorEnable(enable: enable)
    }

    func setEarMonitorVolume(_ volume: Int) {
        // ⚠️ 范围 0–100，不是 0–150
        let clamped = max(0, min(100, volume))
        AudioEffectStore.shared.setVoiceEarMonitorVolume(volume: clamped)
    }

    // MARK: - 变声控制

    func setChangerType(_ type: AudioChangerType) {
        AudioEffectStore.shared.setAudioChangerType(type: type)
    }

    // MARK: - 混响控制

    func setReverbType(_ type: AudioReverbType) {
        AudioEffectStore.shared.setAudioReverbType(type: type)
    }

    // MARK: - 重置
    // 注意：离房后音效会自动失效，但建议主动调用保持状态干净

    func resetAll() {
        AudioEffectStore.shared.reset()
        // 采集音量也恢复默认
        DeviceStore.shared.setCaptureVolume(volume: 100)
    }
}

// MARK: - 音效面板 ViewController

final class AudioEffectPanelViewController: UIViewController {

    private let viewModel = AudioEffectPanelViewModel()
    private var cancellables = Set<AnyCancellable>()

    // MARK: UI 元素

    private let captureVolumeSlider = UISlider()
    private let earMonitorSwitch    = UISwitch()
    private let earMonitorSlider    = UISlider()
    private let changerSegment      = UISegmentedControl(items: ["原声", "儿童", "萝莉", "男声"])
    private let reverbSegment       = UISegmentedControl(items: ["无", "KTV", "小房间", "金属"])
    private let resetButton         = UIButton(type: .system)

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        bindViewModel()
    }

    // MARK: - UI 绑定

    private func bindViewModel() {
        // 采集音量（0–100）
        viewModel.$captureVolume
            .map { Float($0) }
            .receive(on: DispatchQueue.main)
            .assign(to: \.value, on: captureVolumeSlider)
            .store(in: &cancellables)

        // 耳返开关（仅有线耳机连接时可用）
        viewModel.$earMonitorEnabled
            .receive(on: DispatchQueue.main)
            .assign(to: \.isOn, on: earMonitorSwitch)
            .store(in: &cancellables)

        // 耳返 Switch 启用状态（未连有线耳机时置灰）
        viewModel.$isWiredHeadphoneConnected
            .receive(on: DispatchQueue.main)
            .assign(to: \.isEnabled, on: earMonitorSwitch)
            .store(in: &cancellables)

        // 耳返音量（0–100）
        viewModel.$earMonitorVolume
            .map { Float($0) }
            .receive(on: DispatchQueue.main)
            .assign(to: \.value, on: earMonitorSlider)
            .store(in: &cancellables)
    }

    // MARK: - 控件回调

    @objc private func captureVolumeChanged(_ slider: UISlider) {
        viewModel.setCaptureVolume(Int(slider.value))
    }

    @objc private func earMonitorSwitchChanged(_ sw: UISwitch) {
        viewModel.setEarMonitorEnabled(sw.isOn)
    }

    @objc private func earMonitorVolumeChanged(_ slider: UISlider) {
        viewModel.setEarMonitorVolume(Int(slider.value))
    }

    @objc private func changerSegmentChanged(_ segment: UISegmentedControl) {
        let types: [AudioChangerType] = [.none, .child, .littleGirl, .man]
        guard segment.selectedSegmentIndex < types.count else { return }
        viewModel.setChangerType(types[segment.selectedSegmentIndex])
    }

    @objc private func reverbSegmentChanged(_ segment: UISegmentedControl) {
        let types: [AudioReverbType] = [.none, .ktv, .smallRoom, .metallic]
        guard segment.selectedSegmentIndex < types.count else { return }
        viewModel.setReverbType(types[segment.selectedSegmentIndex])
    }

    @objc private func resetTapped() {
        viewModel.resetAll()
    }

    // MARK: - 基础 UI 搭建

    private func setupUI() {
        view.backgroundColor = .systemBackground

        captureVolumeSlider.minimumValue = 0
        captureVolumeSlider.maximumValue = 100   // ⚠️ 最大值 100，不是 150
        captureVolumeSlider.addTarget(self, action: #selector(captureVolumeChanged), for: .valueChanged)

        earMonitorSwitch.addTarget(self, action: #selector(earMonitorSwitchChanged), for: .valueChanged)

        earMonitorSlider.minimumValue = 0
        earMonitorSlider.maximumValue = 100      // ⚠️ 最大值 100，不是 150
        earMonitorSlider.addTarget(self, action: #selector(earMonitorVolumeChanged), for: .valueChanged)

        changerSegment.selectedSegmentIndex = 0
        changerSegment.addTarget(self, action: #selector(changerSegmentChanged), for: .valueChanged)

        reverbSegment.selectedSegmentIndex = 0
        reverbSegment.addTarget(self, action: #selector(reverbSegmentChanged), for: .valueChanged)

        resetButton.setTitle("重置音效", for: .normal)
        resetButton.addTarget(self, action: #selector(resetTapped), for: .touchUpInside)

        [captureVolumeSlider, earMonitorSwitch, earMonitorSlider,
         changerSegment, reverbSegment, resetButton].forEach { view.addSubview($0) }
    }
}
```

**直播结束时重置（在主播下播回调中调用）**：
```swift
func onAnchorStopBroadcast() {
    // 离房后音效自动失效，但主动 reset 可保持本地状态干净
    AudioEffectStore.shared.reset()
    DeviceStore.shared.setCaptureVolume(volume: 100)
}
```

## 调用时序

```
主播开播，麦克风打开成功
        │
        ▼
【可选】预设音效
        ├─ DeviceStore.shared.setCaptureVolume(volume: 100)   // 采集音量（0–100）
        ├─ AudioEffectStore.shared.setAudioChangerType(.ktv)  // 变声
        └─ AudioEffectStore.shared.setAudioReverbType(.ktv)   // 混响
        │
        ▼
主播开播中：用户通过面板实时调整
        ├─ 采集音量：setCaptureVolume(volume:)       // 0–100
        ├─ 耳返（有线耳机限定）：setVoiceEarMonitorEnable / setVoiceEarMonitorVolume（0–100）
        ├─ 变声：setAudioChangerType(type:)
        └─ 混响：setAudioReverbType(type:)
        │
        ▼
主播下播 / 退出直播间
        │
        ├─ AudioEffectStore.shared.reset()     ← 主动重置，保持状态干净
        └─ DeviceStore.shared.setCaptureVolume(volume: 100)

有线耳机连接监听（贯穿整个直播生命周期）
        ├─ AVAudioSession.routeChangeNotification 触发
        ├─ 有线耳机拔出 → 自动关闭耳返，置灰耳返开关
        └─ 有线耳机插入 → 允许用户开启耳返
```

## 平台特有注意事项

### 1. 蓝牙耳机不支持耳返
**蓝牙耳机（AirPods 等）不支持耳返功能**。耳返只对有线耳机（`AVAudioSessionPortHeadphones`）有效。检测耳机时只判断 `.headphones` 类型，不要包含 `.bluetoothA2DP`，否则会误判导致用户开启耳返后听不到声音。

### 2. 耳返音量范围 0–100
`setVoiceEarMonitorVolume` 和 `AudioEffectState.earMonitorVolume` 的有效范围是 **0–100**，不是 0–150。UI 滑块的 `maximumValue` 应设为 `100`。

### 3. 离房后音效自动失效
离开直播间后，`AudioEffectStore` 的音效参数自动失效，无需手动 reset 来"清除效果"。但调用 `reset()` 可以将本地 `AudioEffectState` 状态归零，避免下次开播时 UI 显示残留的旧值。

### 4. AVAudioSession 配置
音效功能依赖 SDK 内部的 `AVAudioSession` 配置（通常为 `.playAndRecord`）。若 App 自行修改了 `AVAudioSession.category`，可能导致耳返或混响失效。建议将音频会话管理统一交给 SDK，不要在直播期间手动调用 `AVAudioSession.setCategory`。

### 5. 变声与混响可叠加使用
`setAudioChangerType` 与 `setAudioReverbType` 互不干扰，可同时生效（如"萝莉音 + KTV 混响"）。需要单独还原某一项时，传入对应的 `.none` 即可，不影响另一项设置。
