---
id: live/audience-list
platform: ios
---

# 观众列表 — iOS 实现

## 前置条件

**依赖安装（Podfile）**
```ruby
pod 'AtomicXCore', '~> 4.0'
```

**最低系统要求**：iOS 13.0+，Xcode 14.0+

**前置登录与进房**：必须在 `LoginStore.shared.login` 成功且 `liveCoreView.joinLive` 成功后才可调用 `fetchAudienceList`。

## API 调用

```swift
// 创建观众列表模块（每个直播间独立实例）
let audienceStore = LiveAudienceStore.create(liveID: String)

// 拉取当前观众列表快照
audienceStore.fetchAudienceList(completion: CompletionClosure?)
// CompletionClosure = (Result<Void, ErrorInfo>) -> Void
// ErrorInfo: .code: Int, .message: String

// 订阅观众实时事件（Combine）
audienceStore.liveAudienceEventPublisher  // PassthroughSubject<LiveAudienceEvent, Never>

// 订阅状态变化（包含 audienceList 和 audienceCount）
audienceStore.state  // StatePublisher<LiveAudienceState>
```

**LiveUserInfo 字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| `userID` | `String` | 用户唯一 ID |
| `userName` | `String` | 显示名称 |
| `avatarURL` | `String` | 头像 URL |

**LiveAudienceState 字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| `audienceList` | `[LiveUserInfo]` | 当前观众数组快照 |
| `audienceCount` | `UInt` | 观众总数（近似值，受频控影响） |
| `messageBannedUserList` | `[LiveUserInfo]` | 已被禁言的用户列表 |

**LiveAudienceEvent 枚举**

| 事件 | 说明 |
|------|------|
| `.onAudienceJoined(audience: LiveUserInfo)` | 有观众进入直播间 |
| `.onAudienceLeft(audience: LiveUserInfo)` | 有观众离开直播间 |
| `.onAudienceMessageDisabled(audience: LiveUserInfo, isDisable: Bool)` | 某观众禁言状态变更 |
| `.onOwnerJoined(owner: LiveUserInfo)` | 房主进入直播间（4.1.0+） |
| `.onOwnerLeft(owner: LiveUserInfo)` | 房主离开直播间（4.1.0+） |
| `.onAdminJoined(admin: LiveUserInfo)` | 管理员进入直播间（4.1.0+） |
| `.onAdminLeft(admin: LiveUserInfo)` | 管理员离开直播间（4.1.0+） |

> **MUST**: switch LiveAudienceEvent 时必须添加 `default` 分支，因为枚举可能在后续版本继续扩展。

## 代码示例

### 1. 创建、拉取列表与订阅事件

```swift
import AtomicXCore
import Combine
import UIKit

final class AudienceListViewModel {

    // MARK: - Properties

    private(set) var audienceList: [LiveUserInfo] = []
    private(set) var audienceCount: UInt = 0

    private var audienceStore: LiveAudienceStore?
    private var cancellables = Set<AnyCancellable>()

    // UI 刷新回调（通知 ViewController）
    var onListUpdated: (() -> Void)?
    var onCountUpdated: ((UInt) -> Void)?

    // MARK: - 初始化（进房成功后调用）

    func setup(liveID: String) {
        // Step 1: 创建 LiveAudienceStore 实例
        audienceStore = LiveAudienceStore.create(liveID: liveID)

        // Step 2: 订阅实时事件
        subscribeEvents()

        // Step 3: 拉取初始列表快照
        fetchInitialList()
    }

    // MARK: - 销毁（退出直播间时调用）

    func teardown() {
        cancellables.removeAll()
        audienceStore = nil
        audienceList = []
        audienceCount = 0
    }

    // MARK: - 订阅实时进离场事件

    private func subscribeEvents() {
        audienceStore?.liveAudienceEventPublisher
            .receive(on: DispatchQueue.main)
            .sink { [weak self] event in
                guard let self = self else { return }
                switch event {
                case .onAudienceJoined(let audience):
                    self.handleAudienceJoined(audience)
                case .onAudienceLeft(let audience):
                    self.handleAudienceLeft(audience)
                case .onAudienceMessageDisabled(let audience, let isDisable):
                    // 禁言状态变更，可在此刷新 UI 标记
                    print("[AudienceList] 用户 \(audience.userID) 禁言状态变更: \(isDisable)")
                default:
                    break  // 兼容 4.1.0+ 新增 case（onOwnerJoined/Left, onAdminJoined/Left）
                }
            }
            .store(in: &cancellables)
    }

    // MARK: - 拉取初始列表

    private func fetchInitialList() {
        audienceStore?.fetchAudienceList { [weak self] result in
            DispatchQueue.main.async {
                guard let self = self else { return }
                switch result {
                case .success:
                    // 从 state.value 中取最新快照（state 是 StatePublisher，必须通过 .value 访问）
                    self.audienceList = self.audienceStore?.state.value.audienceList ?? []
                    self.audienceCount = self.audienceStore?.state.value.audienceCount ?? 0
                    self.onListUpdated?()
                    self.onCountUpdated?(self.audienceCount)
                case .failure(let error):
                    print("[AudienceList] fetchAudienceList failed code=\(error.code) msg=\(error.message)")
                }
            }
        }
    }

    // MARK: - 事件处理

    private func handleAudienceJoined(_ audience: LiveUserInfo) {
        // 避免重复插入
        guard !audienceList.contains(where: { $0.userID == audience.userID }) else { return }
        audienceList.insert(audience, at: 0)   // 新观众插入列表头部
        audienceCount = audienceStore?.state.value.audienceCount ?? audienceCount + 1
        onListUpdated?()
        onCountUpdated?(audienceCount)
    }

    private func handleAudienceLeft(_ audience: LiveUserInfo) {
        audienceList.removeAll { $0.userID == audience.userID }
        audienceCount = audienceStore?.state.value.audienceCount ?? (audienceCount > 0 ? audienceCount - 1 : 0)
        onListUpdated?()
        onCountUpdated?(audienceCount)
    }
}
```

### 2. 单列 UICollectionView 展示

```swift
import UIKit

final class AudienceListViewController: UIViewController {

    private let viewModel = AudienceListViewModel()

    // MARK: - UI

    private lazy var countLabel: UILabel = {
        let label = UILabel()
        label.font = .systemFont(ofSize: 14, weight: .medium)
        label.textColor = .white
        return label
    }()

    private lazy var collectionView: UICollectionView = {
        let layout = UICollectionViewFlowLayout()
        layout.scrollDirection = .vertical
        layout.itemSize = CGSize(width: UIScreen.main.bounds.width, height: 60)
        layout.minimumLineSpacing = 0
        let cv = UICollectionView(frame: .zero, collectionViewLayout: layout)
        cv.register(AudienceCell.self, forCellWithReuseIdentifier: "AudienceCell")
        cv.dataSource = self
        cv.backgroundColor = .clear
        return cv
    }()

    // MARK: - Setup

    init(liveID: String) {
        super.init(nibName: nil, bundle: nil)
        viewModel.setup(liveID: liveID)
    }

    required init?(coder: NSCoder) { fatalError() }

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        bindViewModel()
    }

    deinit {
        viewModel.teardown()
    }

    private func setupUI() {
        view.addSubview(countLabel)
        view.addSubview(collectionView)
        // 布局代码省略
    }

    private func bindViewModel() {
        viewModel.onListUpdated = { [weak self] in
            self?.collectionView.reloadData()
        }
        viewModel.onCountUpdated = { [weak self] count in
            // ⚠️ 人数仅展示，加"约"字说明非精确值
            self?.countLabel.text = "约 \(count) 人在看"
        }
    }
}

extension AudienceListViewController: UICollectionViewDataSource {
    func collectionView(_ cv: UICollectionView,
                        numberOfItemsInSection section: Int) -> Int {
        viewModel.audienceList.count
    }

    func collectionView(_ cv: UICollectionView,
                        cellForItemAt indexPath: IndexPath) -> UICollectionViewCell {
        let cell = cv.dequeueReusableCell(withReuseIdentifier: "AudienceCell",
                                          for: indexPath) as! AudienceCell
        cell.configure(with: viewModel.audienceList[indexPath.item])
        return cell
    }
}

// MARK: - 双列布局（可选）

extension AudienceListViewController {
    /// 切换为双列显示（适合大观众列表）
    func switchToDoubleColumnLayout() {
        guard let layout = collectionView.collectionViewLayout
                as? UICollectionViewFlowLayout else { return }
        let padding: CGFloat = 8
        let itemWidth = (UIScreen.main.bounds.width - padding * 3) / 2
        layout.itemSize = CGSize(width: itemWidth, height: 56)
        layout.minimumInteritemSpacing = padding
        layout.minimumLineSpacing = padding
        layout.sectionInset = UIEdgeInsets(top: padding, left: padding,
                                           bottom: padding, right: padding)
        collectionView.reloadData()
    }
}

// MARK: - Cell

final class AudienceCell: UICollectionViewCell {

    private let avatarImageView = UIImageView()
    private let nameLabel = UILabel()

    override init(frame: CGRect) {
        super.init(frame: frame)
        setupUI()
    }

    required init?(coder: NSCoder) { fatalError() }

    private func setupUI() {
        avatarImageView.layer.cornerRadius = 20
        avatarImageView.clipsToBounds = true
        contentView.addSubview(avatarImageView)
        contentView.addSubview(nameLabel)
        // 布局代码省略
    }

    func configure(with user: LiveUserInfo) {
        nameLabel.text = user.userName
        // 加载头像（使用业务图片加载框架）
        if let url = URL(string: user.avatarURL) {
            // e.g. avatarImageView.sd_setImage(with: url)
            _ = url  // 占位
        }
    }
}
```

## 调用时序

```
LoginStore.login 成功
    │
    ▼
liveCoreView.joinLive 成功
    │
    ▼
LiveAudienceStore.create(liveID:)       ← 每个直播间独立实例
    │
    ▼
audienceStore.liveAudienceEventPublisher 订阅（PassthroughSubject）
    │
    ▼
audienceStore.fetchAudienceList          ← 获取初始快照
    │
    ├─ .failure(ErrorInfo) → 检查登录态 / 进房状态（error.code / error.message）
    └─ .success → 读取 state.audienceList → reloadData
            │
            ▼
        实时事件推送
        ├─ .onAudienceJoined(audience:) → 插入列表头 → reloadData
        ├─ .onAudienceLeft(audience:)   → 移除列表项 → reloadData
        └─ .onAudienceMessageDisabled(audience:isDisable:) → 更新禁言标记
            │
            ▼
        退出直播间
        └─ audienceStore = nil（释放订阅与资源）
```

## 平台特有注意事项

### 1. AnyCancellable 必须存储在实例变量中

若将 `liveAudienceEventPublisher.sink` 返回的 `AnyCancellable` 存在局部变量而非 `Set<AnyCancellable>` 实例变量中，订阅会在函数返回后立即释放，导致后续所有事件静默丢弃。务必使用 `.store(in: &cancellables)` 持久化订阅。

### 2. 主线程刷新 UI

`liveAudienceEventPublisher` 的事件可能在后台线程分发。始终使用 `.receive(on: DispatchQueue.main)` 切换到主线程再更新 `audienceList` 和 `collectionView`，否则会触发 `UIKit` 主线程访问警告或崩溃。

### 3. audienceCount 类型为 UInt

`LiveAudienceState.audienceCount` 是 `UInt` 类型（非 `Int`）。UI 展示时建议显示"约 X 人在看"，而非精确数字。由于频控（40条/秒），在万人以上直播间中 `audienceCount` 可能与实际值相差数百，不要用它做业务逻辑判断（如活动奖励门槛）。

### 4. 离场延迟：90 秒心跳窗口

观众因网络断开（非主动退出）时，系统需等待约 90 秒心跳超时后才会触发 `onAudienceLeft`。UI 上观众头像可能在对方已断网后仍显示数分钟，属正常现象，无需特殊处理。
