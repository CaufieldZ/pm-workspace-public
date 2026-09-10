# 平台 Slice 模板

> **本文件是平台实现 slice 的标准模板。**
> 复制本文件到 `slices/{product}/{platform}/{ability}.md`,按 `<!-- 指引: ... -->` 批注填写内容,**填完后删除所有批注**。
>
> **三步走**:
> 1. 复制本文件 → 把 `{占位符}` 全部替换为真实内容
> 2. 对照每个 section 批注里的 ✅ 正例 / ❌ 反例自查
> 3. 跑批注里给出的「验证命令」,通过后再提交
> 复制本文件到 `slices/{product}/{platform}/{ability}.md`,按 `<!-- 指引: ... -->` 批注填写内容,**填完后删除所有批注**。
>
> **三步走**:
> 1. 复制本文件 → 把 `{占位符}` 全部替换为真实内容
> 2. 对照每个 section 批注里的 ✅ 正例 / ❌ 反例自查
> 3. 跑批注里给出的「验证命令」,通过后再提交
>
> **填写范例**:请参考 [`slices/live/ios/coguest-apply.md`](slices/live/ios/coguest-apply.md) — 目前最完整的平台 slice,包含所有 section 的真实内容。
> **完整规范**:见 [`slice-spec.md`](slice-spec.md) — 仅在批注不够用时回查。
> **填写范例**:请参考 [`slices/live/ios/coguest-apply.md`](slices/live/ios/coguest-apply.md) — 目前最完整的平台 slice,包含所有 section 的真实内容。
> **完整规范**:见 [`slice-spec.md`](slice-spec.md) — 仅在批注不够用时回查。

---

```yaml
---
id: {product}/{ability}       # [必填] 与对应的 per-product platform index 中的 id 一致
platform: {platform}          # [必填] ios / android / web / flutter / electron
api_docs:                     # [必填] 该平台对应的 API 参考文档链接,至少 1 条
api_docs:                     # [必填] 该平台对应的 API 参考文档链接,至少 1 条
  - title: {API 类名/模块名}
    url: https://...
---
```

<!-- 指引: Frontmatter 字段说明：
     - id: 与对应的 per-product platform index 中的 slice id 完全一致
     - platform: 当前平台标识
     - api_docs: 该功能在该平台的 API 参考文档链接（接口签名、参数类型、返回值等）。
       产品级概览已不再放文档链接，教程/指南类 URL 也不放在 api_docs 里。

1️⃣ 你必须写什么
- id:与 index.yaml 中的 slice id **完全一致**(含连字符大小写)
- platform:当前平台标识(只能是 ios / android / web / flutter / electron 之一)
- api_docs:该功能在该平台的 API 参考文档链接(精确到类/模块,至少 1 条)

2️⃣ 写作模板
api_docs:
  - title: {本 slice 涉及的具体类名,如 CoGuestStore}
    url: https://{平台 SDK 文档站}/.../{类名小写}/

判定 url 是否合格:打开链接,**第一屏**就能看到本 slice 涉及的**具体类的方法签名**(参数名、参数类型、返回值)→ ✅ 合格

3️⃣ ✅ 正例(摘自 live/ios/coguest-apply)
api_docs:
  - title: CoGuestStore
    url: https://tencent-rtc.github.io/TUIKit_iOS/documentation/atomicxcore/cogueststore/
  - title: DeviceStore
    url: https://tencent-rtc.github.io/TUIKit_iOS/documentation/atomicxcore/devicestore/
为什么是正例:
- 链接路径含 /documentation/ → 是 API 参考站
- 路径末尾是具体类名 cogueststore → 精确到类
- slice 涉及两个 Store → 分别列出,不省略

4️⃣ ❌ 反例
- title: TRTC iOS SDK
  url: https://trtc.io/sdk           ← SDK 首页:AI 拿不到类签名,生成不存在的 API
- title: 连麦集成指南
  url: https://trtc.io/zh/document/74598   ← 教程页:API 名常被简化,AI 引用错误
- title: TODO
  url: TODO                          ← 占位:永远不会被替换,半年后就是废 slice

5️⃣ 必填项语义三件套
- 违反后果:链接非类级 → AI 生成不存在的 API 名 → 客户编译报错投诉
- 验证手段:python scripts/validate_api_docs.py {file}
  通过标准:每条 url 返回 200;url 含 /documentation/ 或 /api/;打开链接的页面 H1 必须包含 frontmatter 里的 title
- 绕过条件:该平台官方确实无 API 参考站(如某些早期 Electron 模块)→ 必须填头文件 GitHub 永久链接(含 commit hash),且在 PR 中说明

注:name / tags / platforms / related 在产品级概览中维护,此处不重复。
-->

# {名称} — {平台} 实现

## 前置条件 [必填]

<!-- 指引: 前置条件 [必填]

1️⃣ 你必须写什么
列出本 slice 代码运行前必须满足的状态,**用引用形式**指向其他 slice。
通用依赖(SDK 安装、基础权限)已在 login-auth 中统一描述,**禁止重复**。

本 section 只写两类内容:
- 增量依赖 — 本 slice 额外需要的库/权限(如美颜 SDK、蓝牙权限)
- 前置状态 — 本功能依赖哪些 Store 已初始化/操作已完成,引用对应 slice ID

2️⃣ 写作模板
**通用依赖**:见 [login-auth 平台 slice](../login-auth.md)

**额外依赖**:{无 / 列出本 slice 独有依赖}

**前置状态**:
- `{Store/状态}.{属性} == {期望值}`(→ {产品}/{依赖 slice})
- {跨角色前置:如"主播端已开播"}

3️⃣ ✅ 正例(摘自 live/ios/coguest-apply)
**通用依赖**:见 [login-auth 平台 slice](../login-auth.md)

**额外依赖**:无

**前置状态**:
- 已完成登录(→ live/login-auth),`LoginStore.shared.isLogin == true`
- 已加入房间且角色为观众(→ live/room-lifecycle),`RoomStore.shared.localUser.role == .audience`
- 主播端已开播且开启了"接受连麦申请"开关
为什么是正例:
- 用 → slice-id 标注依赖,不重复说明怎么登录
- 给出可机械验证的状态条件(role == .audience)
- 包含跨角色前置(主播端配置)

4️⃣ ❌ 反例
要先安装 SDK 包 `pod 'TUIKit'`,然后调用 LoginStore.login(userId:userSig:) 登录,
然后调用 RoomStore.joinRoom(roomId:) 加入房间,...
为什么是反例:
- 重复了 base-setup / login-auth 的内容
- 这些内容会随版本变化,这里写一份等于埋雷
- 没用引用形式,信息易漂移
→ 改为 → live/login-auth 引用

5️⃣ 必填项语义三件套
- 违反后果:重复其他 slice 内容 → 信息漂移(版本升级后这里没同步)→ AI 生成过时代码
- 验证手段:全文搜安装关键字应命中 0 次:
  grep -E "pod install|pod 'AtomicXCore'|npm install|implementation 'com.tencent" {file}
- 绕过条件:本 slice 确实需要额外依赖(如美颜 SDK)→ 在「额外依赖」段列出
<!-- 指引: 前置条件 [必填]

1️⃣ 你必须写什么
列出本 slice 代码运行前必须满足的状态,**用引用形式**指向其他 slice。
通用依赖(SDK 安装、基础权限)已在 login-auth 中统一描述,**禁止重复**。

本 section 只写两类内容:
- 增量依赖 — 本 slice 额外需要的库/权限(如美颜 SDK、蓝牙权限)
- 前置状态 — 本功能依赖哪些 Store 已初始化/操作已完成,引用对应 slice ID

2️⃣ 写作模板
**通用依赖**:见 [login-auth 平台 slice](../login-auth.md)

**额外依赖**:{无 / 列出本 slice 独有依赖}

**前置状态**:
- `{Store/状态}.{属性} == {期望值}`(→ {产品}/{依赖 slice})
- {跨角色前置:如"主播端已开播"}

3️⃣ ✅ 正例(摘自 live/ios/coguest-apply)
**通用依赖**:见 [login-auth 平台 slice](../login-auth.md)

**额外依赖**:无

**前置状态**:
- 已完成登录(→ live/login-auth),`LoginStore.shared.isLogin == true`
- 已加入房间且角色为观众(→ live/room-lifecycle),`RoomStore.shared.localUser.role == .audience`
- 主播端已开播且开启了"接受连麦申请"开关
为什么是正例:
- 用 → slice-id 标注依赖,不重复说明怎么登录
- 给出可机械验证的状态条件(role == .audience)
- 包含跨角色前置(主播端配置)

4️⃣ ❌ 反例
要先安装 SDK 包 `pod 'TUIKit'`,然后调用 LoginStore.login(userId:userSig:) 登录,
然后调用 RoomStore.joinRoom(roomId:) 加入房间,...
为什么是反例:
- 重复了 base-setup / login-auth 的内容
- 这些内容会随版本变化,这里写一份等于埋雷
- 没用引用形式,信息易漂移
→ 改为 → live/login-auth 引用

5️⃣ 必填项语义三件套
- 违反后果:重复其他 slice 内容 → 信息漂移(版本升级后这里没同步)→ AI 生成过时代码
- 验证手段:全文搜安装关键字应命中 0 次:
  grep -E "pod install|pod 'AtomicXCore'|npm install|implementation 'com.tencent" {file}
- 绕过条件:本 slice 确实需要额外依赖(如美颜 SDK)→ 在「额外依赖」段列出
-->

**通用依赖**:见 [login-auth 平台 slice](../login-auth.md)
**通用依赖**:见 [login-auth 平台 slice](../login-auth.md)

**额外依赖**:
<!-- 如有本 slice 独有依赖,在此列出;没有则写「无」 -->
**额外依赖**:
<!-- 如有本 slice 独有依赖,在此列出;没有则写「无」 -->

**前置状态**:
<!-- 列出必须满足的前置条件,引用 slice ID -->
**前置状态**:
<!-- 列出必须满足的前置条件,引用 slice ID -->

## 代码示例 [必填]

<!-- 指引: 代码示例 [必填]

1️⃣ 你必须写什么
能让 AI 直接学习并产出**可编译、可运行**的代码块。
代码示例 = 这份 slice 给 AI 的"训练数据",每个细节都会被复制放大。

定位是「零件」— 单个功能的完整实现。多个零件如何组装成完整场景,由 scenario 的平台实现文件负责。
<!-- 指引: 代码示例 [必填]

1️⃣ 你必须写什么
能让 AI 直接学习并产出**可编译、可运行**的代码块。
代码示例 = 这份 slice 给 AI 的"训练数据",每个细节都会被复制放大。

定位是「零件」— 单个功能的完整实现。多个零件如何组装成完整场景,由 scenario 的平台实现文件负责。

2️⃣ 6 条最低标准(必须全部满足)

| 维度 | 最低标准 |
|------|---------|
| 可编译 | 含完整 import、完整类/函数闭包,**严禁** ... 省略任何逻辑分支 |
| 可运行 | 补充业务参数后可直接跑通;业务参数用 {TODO: 填入 xxx} 占位 |
| 有日志锚点 | 关键路径必须有 print/console.log/Log.d,带模块前缀如 [CoGuest] |
| 有错误处理 | 每个 .failure / catch / error 分支必须有面向用户的处理(UI 可见的 errorMessage / alert),不允许只 print |
| 多角色分开写 | 主播端 / 观众端必须拆成独立代码块,不耦合 |
| 可组合性 | 前置依赖通过注释声明 // 前置:登录完成(→ live/login-auth),不硬编码其他 slice 调用 |

组织方式:按用户操作流程,用 MARK / region / 注释分隔各步骤(初始化 → 核心操作 → 事件监听 → 错误处理 → 清理)

3️⃣ ✅ 正例(摘自 live/ios/coguest-apply)
```swift
// 前置:登录完成(→ chat/login-auth)
// 前置:已加入房间(→ live/room-lifecycle)

import TencentImSDKPlugin
import Combine

class CoGuestApplyViewModel: ObservableObject {
    @Published var errorMessage: String?       // ← UI 必需,展示给用户
    private var cancellables = Set<AnyCancellable>()

    func applyForSeat() {
        print("[CoGuest] 开始发起连麦申请")  // ← 日志锚点

        CoGuestStore.shared.applyForSeat(timeout: 30)
            .sink { [weak self] completion in   // ← [weak self] 必需
                if case .failure(let error) = completion {
                    print("[CoGuest] 申请失败: \(error)")
                    self?.errorMessage = "连麦申请失败,请重试"  // ← 用户可见
                }
            } receiveValue: { [weak self] _ in
                print("[CoGuest] 申请已发送")
                self?.errorMessage = nil
            }
            .store(in: &cancellables)
    }
}
```
为什么是正例:
- 顶部 // 前置 注释声明依赖 slice,不耦合调用
- import 完整,可直接编译
- 业务参数(timeout)用真实值不是 xxx
- 关键路径有 print 锚点,带 [CoGuest] 模块前缀
- 每个 failure 分支都设置 errorMessage(UI 可见),不是只 print
- [weak self] 防循环引用

4️⃣ ❌ 反例
反例 1:用 ... 省略
func applyForSeat() {
    CoGuestStore.shared.applyForSeat(...) { result in
        // 处理结果
        ...
    }
}
→ "..." 跳过了失败处理,AI 学到这个模式后到处省略

反例 2:仅 print 错误
.sink { completion in
    if case .failure(let error) = completion {
        print("error: \(error)")   // ← 用户看不到!
    }
}
→ 客户线上故障时用户只看到无反应

反例 3:省略 import
class XXX {
    var cancellables = Set<AnyCancellable>()
    // ↑ 没 import Combine,代码贴出来不能编译
}

反例 4:业务参数瞎编
applyForSeat(seatIndex: 1, timeout: 60, reason: "我想连麦")
→ "我想连麦" 应该用 {TODO: 填入业务申请理由} 占位

反例 5:多角色塞一个类里
class CoGuestManager {
    func audienceApply() { ... }
    func hostApprove() { ... }
}
→ 主播观众职责混合,AI 生成时随机抽方法

5️⃣ 必填项语义三件套
- 违反后果:含 ... / 仅 print 错误 / 省略 import → AI 学坏 → 跨 slice 蔓延错误模式 → slice 不可合并,**已合并的批量回退**(2025-03 真实事故,2 周返工)
- 验证手段:
  # 1. 抽取代码块编译
  python scripts/extract_code.py {file} | xcodebuild build ...
  # 2. 静态扫描
  grep -E "\\.\\.\\.|//\\s*处理结果|//\\s*TODO[^:]" {file}   # 必须命中 0 次
  grep -E "errorMessage|alert|toast" {file}                # 每个 .failure 块至少 1 处
- 绕过条件:无。"先占位以后补"的代码示例 = 永远不会补的代码示例
2️⃣ 6 条最低标准(必须全部满足)

| 维度 | 最低标准 |
|------|---------|
| 可编译 | 含完整 import、完整类/函数闭包,**严禁** ... 省略任何逻辑分支 |
| 可运行 | 补充业务参数后可直接跑通;业务参数用 {TODO: 填入 xxx} 占位 |
| 有日志锚点 | 关键路径必须有 print/console.log/Log.d,带模块前缀如 [CoGuest] |
| 有错误处理 | 每个 .failure / catch / error 分支必须有面向用户的处理(UI 可见的 errorMessage / alert),不允许只 print |
| 多角色分开写 | 主播端 / 观众端必须拆成独立代码块,不耦合 |
| 可组合性 | 前置依赖通过注释声明 // 前置:登录完成(→ live/login-auth),不硬编码其他 slice 调用 |

组织方式:按用户操作流程,用 MARK / region / 注释分隔各步骤(初始化 → 核心操作 → 事件监听 → 错误处理 → 清理)

3️⃣ ✅ 正例(摘自 live/ios/coguest-apply)
```swift
// 前置:登录完成(→ chat/login-auth)
// 前置:已加入房间(→ live/room-lifecycle)

import TencentImSDKPlugin
import Combine

class CoGuestApplyViewModel: ObservableObject {
    @Published var errorMessage: String?       // ← UI 必需,展示给用户
    private var cancellables = Set<AnyCancellable>()

    func applyForSeat() {
        print("[CoGuest] 开始发起连麦申请")  // ← 日志锚点

        CoGuestStore.shared.applyForSeat(timeout: 30)
            .sink { [weak self] completion in   // ← [weak self] 必需
                if case .failure(let error) = completion {
                    print("[CoGuest] 申请失败: \(error)")
                    self?.errorMessage = "连麦申请失败,请重试"  // ← 用户可见
                }
            } receiveValue: { [weak self] _ in
                print("[CoGuest] 申请已发送")
                self?.errorMessage = nil
            }
            .store(in: &cancellables)
    }
}
```
为什么是正例:
- 顶部 // 前置 注释声明依赖 slice,不耦合调用
- import 完整,可直接编译
- 业务参数(timeout)用真实值不是 xxx
- 关键路径有 print 锚点,带 [CoGuest] 模块前缀
- 每个 failure 分支都设置 errorMessage(UI 可见),不是只 print
- [weak self] 防循环引用

4️⃣ ❌ 反例
反例 1:用 ... 省略
func applyForSeat() {
    CoGuestStore.shared.applyForSeat(...) { result in
        // 处理结果
        ...
    }
}
→ "..." 跳过了失败处理,AI 学到这个模式后到处省略

反例 2:仅 print 错误
.sink { completion in
    if case .failure(let error) = completion {
        print("error: \(error)")   // ← 用户看不到!
    }
}
→ 客户线上故障时用户只看到无反应

反例 3:省略 import
class XXX {
    var cancellables = Set<AnyCancellable>()
    // ↑ 没 import Combine,代码贴出来不能编译
}

反例 4:业务参数瞎编
applyForSeat(seatIndex: 1, timeout: 60, reason: "我想连麦")
→ "我想连麦" 应该用 {TODO: 填入业务申请理由} 占位

反例 5:多角色塞一个类里
class CoGuestManager {
    func audienceApply() { ... }
    func hostApprove() { ... }
}
→ 主播观众职责混合,AI 生成时随机抽方法

5️⃣ 必填项语义三件套
- 违反后果:含 ... / 仅 print 错误 / 省略 import → AI 学坏 → 跨 slice 蔓延错误模式 → slice 不可合并,**已合并的批量回退**(2025-03 真实事故,2 周返工)
- 验证手段:
  # 1. 抽取代码块编译
  python scripts/extract_code.py {file} | xcodebuild build ...
  # 2. 静态扫描
  grep -E "\\.\\.\\.|//\\s*处理结果|//\\s*TODO[^:]" {file}   # 必须命中 0 次
  grep -E "errorMessage|alert|toast" {file}                # 每个 .failure 块至少 1 处
- 绕过条件:无。"先占位以后补"的代码示例 = 永远不会补的代码示例
-->

## 调用时序 [条件必填:多角色异步交互 或 回调嵌套 ≥3 层]
## 调用时序 [条件必填:多角色异步交互 或 回调嵌套 ≥3 层]

<!-- 指引: 调用时序 [条件必填]

1️⃣ 触发条件(任一满足即必须画)
- 多角色交互(主播/观众/服务端三方时序不容易从单段代码看出)
- 异步回调链路特别深(3 层以上嵌套回调)
- 状态机分支 ≥3 个

不满足 → **整段删除**,不要留空。

2️⃣ 写作模板(ASCII 时序图)
```
{角色 A}        {SDK / 中介}      {角色 B}
   │                │              │
   ├─ {操作} ──→    │              │
   │                ├─ {事件} ──→  │
   │                │              ├─ {响应}
   │                ←─ {回调} ─────┤
```

3️⃣ ✅ 正例(摘自 live/ios/coguest-apply)
```
观众端           SDK              主播端
  │                                │
  ├─ applyForSeat ──→               │
  │                                │
  │              ←─ onApplication ─┤
  │                                │
  │              ←─ approve  ──────┤
  │                                │
  ├─ {打开摄像头/麦克风}            │
  │                                │
```
为什么是正例:
- 三列对应三方角色(观众/SDK/主播),清晰
- 每条箭头标注具体方法名/事件名,可对应到代码
- 顺序贴近真实业务时序

4️⃣ ❌ 反例
观众发起申请,主播收到后处理,然后通知观众。
→ 不是图,只是一句散文,无法体现并行/异步

或者画图但没标方法名:
观众  →  服务器  →  主播
→ 无法对应代码,AI 拿不到信息

5️⃣ 必填项语义三件套
- 违反后果:多角色交互无时序图 → AI 生成代码角色行为错位 → 上线后双方互相听不到
- 验证手段:人工 review,触发条件命中即必有;时序图覆盖所有角色和关键事件
- 绕过条件:不满足触发条件 → 可省(整段删除)
<!-- 指引: 调用时序 [条件必填]

1️⃣ 触发条件(任一满足即必须画)
- 多角色交互(主播/观众/服务端三方时序不容易从单段代码看出)
- 异步回调链路特别深(3 层以上嵌套回调)
- 状态机分支 ≥3 个

不满足 → **整段删除**,不要留空。

2️⃣ 写作模板(ASCII 时序图)
```
{角色 A}        {SDK / 中介}      {角色 B}
   │                │              │
   ├─ {操作} ──→    │              │
   │                ├─ {事件} ──→  │
   │                │              ├─ {响应}
   │                ←─ {回调} ─────┤
```

3️⃣ ✅ 正例(摘自 live/ios/coguest-apply)
```
观众端           SDK              主播端
  │                                │
  ├─ applyForSeat ──→               │
  │                                │
  │              ←─ onApplication ─┤
  │                                │
  │              ←─ approve  ──────┤
  │                                │
  ├─ {打开摄像头/麦克风}            │
  │                                │
```
为什么是正例:
- 三列对应三方角色(观众/SDK/主播),清晰
- 每条箭头标注具体方法名/事件名,可对应到代码
- 顺序贴近真实业务时序

4️⃣ ❌ 反例
观众发起申请,主播收到后处理,然后通知观众。
→ 不是图,只是一句散文,无法体现并行/异步

或者画图但没标方法名:
观众  →  服务器  →  主播
→ 无法对应代码,AI 拿不到信息

5️⃣ 必填项语义三件套
- 违反后果:多角色交互无时序图 → AI 生成代码角色行为错位 → 上线后双方互相听不到
- 验证手段:人工 review,触发条件命中即必有;时序图覆盖所有角色和关键事件
- 绕过条件:不满足触发条件 → 可省(整段删除)
-->

## 平台特有注意事项 [必填:至少 1 条]
## 平台特有注意事项 [必填:至少 1 条]

<!-- 指引: 平台特有注意事项 [必填,至少 1 条]

1️⃣ 你必须写什么
仅在该平台才会踩的坑。每条标准:**该平台独有 + 不写出来研发会踩**。
跨平台通用的注意事项 → 上移到产品级概览的 ALWAYS/NEVER。

2️⃣ 写作模板
### {编号}. {一句话标题}
**现象**:{开发者会遇到什么具体表现}
**原因**:{为什么会这样,SDK / 平台机制层面}
**必须做**:{具体动作,可机械执行}

3️⃣ ✅ 正例(iOS)
### 1. AnyCancellable 必须存为实例属性
**现象**:.sink 闭包永远不触发,日志没有任何输出
**原因**:局部变量 cancellable 出作用域后被释放,Combine 自动解除订阅
**必须做**:声明 `private var cancellables = Set<AnyCancellable>()` 实例属性,
所有 sink 后接 `.store(in: &cancellables)`

### 2. sink 闭包必须显式 [weak self]
**现象**:VC dismiss 后 ViewModel 不释放,Memory Graph 显示循环引用
**原因**:sink 闭包对 self 强引用,publisher 又被 self 持有
**必须做**:所有 .sink { } 闭包第一行加 [weak self]

### 3. 首次申请麦克风权限的弹窗在异步线程触发会被忽略
**现象**:点击连麦按钮后,系统不弹权限对话框,SDK 直接返回权限拒绝
**原因**:iOS 权限弹窗必须在主线程触发,异步线程调用静默失败
**必须做**:`DispatchQueue.main.async { applyForSeat() }`

为什么这些是正例:
- 每条都是 iOS 独有(Android/Web 无 Combine、无 [weak self]、权限机制不同)
- 三段式结构(现象/原因/必须做)清晰,新人能快速 get
- "必须做" 是具体动作,不是"注意一下"

4️⃣ ❌ 反例
### 1. 注意内存管理
内存管理很重要,要避免泄漏。
→ "注意""很重要" = 软词;"内存管理"跨平台都有 → 不是平台特有

### 2. iOS 上需要权限
iOS 应用要在 Info.plist 声明权限。
→ 这是基础常识,不写也不会踩;且 base-setup 已覆盖

### 3. 异步代码要小心
处理异步代码时要注意时序问题。
→ 全是模糊形容词,无具体动作

5️⃣ 必填项语义三件套
- 违反后果:平台特有坑没写 → AI 生成代码在该平台报错 / 行为异常 / 内存泄漏
- 验证手段:每条必须含"必须做:{具体动作}";描述的现象其他平台不会出现;不出现"注意""小心""很重要"等软词
- 绕过条件:无(每个平台 slice 都至少要有 1 条)
<!-- 指引: 平台特有注意事项 [必填,至少 1 条]

1️⃣ 你必须写什么
仅在该平台才会踩的坑。每条标准:**该平台独有 + 不写出来研发会踩**。
跨平台通用的注意事项 → 上移到产品级概览的 ALWAYS/NEVER。

2️⃣ 写作模板
### {编号}. {一句话标题}
**现象**:{开发者会遇到什么具体表现}
**原因**:{为什么会这样,SDK / 平台机制层面}
**必须做**:{具体动作,可机械执行}

3️⃣ ✅ 正例(iOS)
### 1. AnyCancellable 必须存为实例属性
**现象**:.sink 闭包永远不触发,日志没有任何输出
**原因**:局部变量 cancellable 出作用域后被释放,Combine 自动解除订阅
**必须做**:声明 `private var cancellables = Set<AnyCancellable>()` 实例属性,
所有 sink 后接 `.store(in: &cancellables)`

### 2. sink 闭包必须显式 [weak self]
**现象**:VC dismiss 后 ViewModel 不释放,Memory Graph 显示循环引用
**原因**:sink 闭包对 self 强引用,publisher 又被 self 持有
**必须做**:所有 .sink { } 闭包第一行加 [weak self]

### 3. 首次申请麦克风权限的弹窗在异步线程触发会被忽略
**现象**:点击连麦按钮后,系统不弹权限对话框,SDK 直接返回权限拒绝
**原因**:iOS 权限弹窗必须在主线程触发,异步线程调用静默失败
**必须做**:`DispatchQueue.main.async { applyForSeat() }`

为什么这些是正例:
- 每条都是 iOS 独有(Android/Web 无 Combine、无 [weak self]、权限机制不同)
- 三段式结构(现象/原因/必须做)清晰,新人能快速 get
- "必须做" 是具体动作,不是"注意一下"

4️⃣ ❌ 反例
### 1. 注意内存管理
内存管理很重要,要避免泄漏。
→ "注意""很重要" = 软词;"内存管理"跨平台都有 → 不是平台特有

### 2. iOS 上需要权限
iOS 应用要在 Info.plist 声明权限。
→ 这是基础常识,不写也不会踩;且 base-setup 已覆盖

### 3. 异步代码要小心
处理异步代码时要注意时序问题。
→ 全是模糊形容词,无具体动作

5️⃣ 必填项语义三件套
- 违反后果:平台特有坑没写 → AI 生成代码在该平台报错 / 行为异常 / 内存泄漏
- 验证手段:每条必须含"必须做:{具体动作}";描述的现象其他平台不会出现;不出现"注意""小心""很重要"等软词
- 绕过条件:无(每个平台 slice 都至少要有 1 条)
-->

## 代码生成约束 [必填]

<!-- 指引: 代码生成约束 [必填]

本 section 是给 AI 读的硬性规则,与「平台特有注意事项」互补:
- 注意事项 = 给人读的经验提醒(描述性)
- 代码生成约束 = 给 AI 读的可机械验证规则(结构化)

⚠️ 核心原则
**MUST 的语义 = 它的 backtick 符号能验的语义。**
规则文字承诺得比 backtick 多 → 维度溢出 → AI 写对了 grep 不到,写错了也 grep 不到 → verifier 反向变成攻击面。

完整原则与红旗词表见 slice-spec.md「MUST 规则的维度对齐原则」,但你**不需要先读它**——按下方批注的模板和正反例即可。
<!-- 指引: 代码生成约束 [必填]

本 section 是给 AI 读的硬性规则,与「平台特有注意事项」互补:
- 注意事项 = 给人读的经验提醒(描述性)
- 代码生成约束 = 给 AI 读的可机械验证规则(结构化)

⚠️ 核心原则
**MUST 的语义 = 它的 backtick 符号能验的语义。**
规则文字承诺得比 backtick 多 → 维度溢出 → AI 写对了 grep 不到,写错了也 grep 不到 → verifier 反向变成攻击面。

完整原则与红旗词表见 slice-spec.md「MUST 规则的维度对齐原则」,但你**不需要先读它**——按下方批注的模板和正反例即可。
-->

### 编译必要条件 [必填]

<!-- 指引: 编译必要条件 [必填]

1️⃣ 你必须写什么
本 slice 代码能编译通过的最小条件。**只写增量条件**(通用条件见 login-auth)。

2️⃣ 写作模板
- **必须导入** `{包名 1}` / `{包名 2}` —— SDK 类型不可用则编译失败。
- **最低 SDK 版本**:`{version}`(若高于 base-setup 中的版本)
- **必须的权限声明**:
  - {平台}: {key/permission} —— {用途}

3️⃣ ✅ 正例(摘自 live/ios/coguest-apply)
- **必须导入** `import TencentImSDKPlugin` 与 `import Combine`
- **最低 iOS 版本**:`13.0`(Combine 最低要求)
- **必须的权限声明**:
  - Info.plist `NSMicrophoneUsageDescription` —— 连麦需要麦克风
  - Info.plist `NSCameraUsageDescription` —— 连麦需要摄像头

4️⃣ ❌ 反例
- 需要导入相关的包。
- 最低版本参见官方文档。
- 注意申请权限。
→ 模糊、不可机械验证、"参见官方文档" = 等于没写

5️⃣ 必填项语义三件套
- 违反后果:编译条件不明 → AI 生成代码编译失败 → 客户接入第一步就卡住
- 验证手段:每条都有 backtick 包裹的具体包名/版本号/权限 key
- 绕过条件:同 login-auth,无额外要求 → 写"同 login-auth,无额外要求"
<!-- 指引: 编译必要条件 [必填]

1️⃣ 你必须写什么
本 slice 代码能编译通过的最小条件。**只写增量条件**(通用条件见 login-auth)。

2️⃣ 写作模板
- **必须导入** `{包名 1}` / `{包名 2}` —— SDK 类型不可用则编译失败。
- **最低 SDK 版本**:`{version}`(若高于 base-setup 中的版本)
- **必须的权限声明**:
  - {平台}: {key/permission} —— {用途}

3️⃣ ✅ 正例(摘自 live/ios/coguest-apply)
- **必须导入** `import TencentImSDKPlugin` 与 `import Combine`
- **最低 iOS 版本**:`13.0`(Combine 最低要求)
- **必须的权限声明**:
  - Info.plist `NSMicrophoneUsageDescription` —— 连麦需要麦克风
  - Info.plist `NSCameraUsageDescription` —— 连麦需要摄像头

4️⃣ ❌ 反例
- 需要导入相关的包。
- 最低版本参见官方文档。
- 注意申请权限。
→ 模糊、不可机械验证、"参见官方文档" = 等于没写

5️⃣ 必填项语义三件套
- 违反后果:编译条件不明 → AI 生成代码编译失败 → 客户接入第一步就卡住
- 验证手段:每条都有 backtick 包裹的具体包名/版本号/权限 key
- 绕过条件:同 login-auth,无额外要求 → 写"同 login-auth,无额外要求"
-->

### 生成规则 [必填]

#### MUST(生成时必须包含)

<!-- 指引: MUST [必填,至少 3 条]

1️⃣ 你必须写什么
AI 生成代码时**机械验证**的硬约束,**只写 apply 能用 grep 验的规则**。

2️⃣ 写作模板
1. **必须 {强动词} `{可 grep 的符号}`** —— {不这样做的具体后果}。
   **Verify**: 检查 `{符号}` 出现 ≥1 次。

2. **必须 {强动词} `{符号 A}` 与 `{符号 B}`** —— {后果}。
   **Verify**: 检查 `{符号 A}` 与 `{符号 B}` 各出现 ≥1 次。

3. **必须在 {场景} 时调用 `{符号}`** —— {后果}。
   **Verify**: 检查 `{符号}` 出现 ≥1 次。

⚠️ 「在 X 时调用 Y」中的 X 语义 apply **不验**,只验 Y 出现。
这是有意的——调用时机属于软规则,放到「调用时序」section 引导 AI。

3️⃣ ✅ 正例(摘自 chat/ios/multi-instance)
1. **必须导入 `import TencentImSDKPlugin`** —— 否则 SDK 类型不可用,编译报错。
   **Verify**: 检查 `import TencentImSDKPlugin` 出现 ≥1 次。

2. **必须注册互踢监听 `addSimpleMsgListener`** —— 不注册则用户被踢后无感知。
   **Verify**: 检查 `addSimpleMsgListener` 出现 ≥1 次。

3. **必须在 `onKickedOffline` 回调里展示 UI 反馈 `errorMessage`** ——
   仅 print 不算,用户看不到。
   **Verify**: 检查 `onKickedOffline` 与 `errorMessage` 各出现 ≥1 次。

为什么是正例:
- 每条用强动词("必须导入""必须注册"),不用"应该""建议"
- backtick 内是**精确的可 grep 字符串**(类名/方法名)
- 规则文字承诺的范围 ≤ Verify 能验的范围(无维度溢出)
- 每条都有"违反后果"

4️⃣ ❌ 反例(及红旗词诊断)
1. **应该正确处理互踢回调** —— 否则用户体验不好。
   **Verify**: 检查互踢逻辑是否完整。
   ↑ 软词"应该" + 模糊动词"处理" + Verify 不可机械化

2. **必须调用 `login()` 或 `loginWithSig()`** —— 没登录无法用 SDK。
   **Verify**: 检查 `login` 出现。
   ↑ "或" = 红旗词;只 grep 一个 ≠ 验了选择

3. **必须按业务场景选择互踢策略** —— 业务决定。
   **Verify**: 检查策略配置是否合理。
   ↑ "按业务""合理" = 不可机械验证,应下沉到「最佳实践」软规则

🚩 红旗词表(出现任一即重写)
- 「或 / 任一」 → 拆两条 MUST 各管一个分支
- 「等价 / 或类似」 → 显式枚举所有可接受写法
- 「按业务 / 根据场景」 → 完全移出 MUST,移到「代码示例」按场景给完整 demo
- 「留给 / 负责」 → 移到「集成检查点」,作为 AI 读但 apply 不验的引导
- 「多 backtick 但 Verify 只提一个」 → 拆原子规则;调用顺序写到「调用时序」

✍️ 自查三问(写完每条 MUST 之前问自己)
1. backtick 里的符号是不是 verify 唯一会做的事?规则文字其他词能不能删?
2. 如果 AI 写**等价但不同写法**的代码,verify 会不会误杀?误杀 = 规则太死。
3. 如果 AI 写**只满足 backtick 字符串但语义错**的代码,verify 会不会放过?放过 = 规则太松。

5️⃣ 必填项语义三件套
- 违反后果:MUST 含红旗词 → apply 误杀正确代码 + 训练 AI 凑字符串 → slice 不可合并(2024-12 真实事故:room-lifecycle 写"调 A 或 B",apply 验过却生成错误混合代码)
- 验证手段:python scripts/check_must_rules.py {file}
  通过标准:红旗词命中 0 次;每条 MUST 都有 Verify;Verify 内有 backtick
- 绕过条件:**无**。MUST 是硬约束区,不接受任何豁免。需要"或/按业务"语义 → 拆原子规则,或下沉到「最佳实践」软规则区
#### MUST(生成时必须包含)

<!-- 指引: MUST [必填,至少 3 条]

1️⃣ 你必须写什么
AI 生成代码时**机械验证**的硬约束,**只写 apply 能用 grep 验的规则**。

2️⃣ 写作模板
1. **必须 {强动词} `{可 grep 的符号}`** —— {不这样做的具体后果}。
   **Verify**: 检查 `{符号}` 出现 ≥1 次。

2. **必须 {强动词} `{符号 A}` 与 `{符号 B}`** —— {后果}。
   **Verify**: 检查 `{符号 A}` 与 `{符号 B}` 各出现 ≥1 次。

3. **必须在 {场景} 时调用 `{符号}`** —— {后果}。
   **Verify**: 检查 `{符号}` 出现 ≥1 次。

⚠️ 「在 X 时调用 Y」中的 X 语义 apply **不验**,只验 Y 出现。
这是有意的——调用时机属于软规则,放到「调用时序」section 引导 AI。

3️⃣ ✅ 正例(摘自 chat/ios/multi-instance)
1. **必须导入 `import TencentImSDKPlugin`** —— 否则 SDK 类型不可用,编译报错。
   **Verify**: 检查 `import TencentImSDKPlugin` 出现 ≥1 次。

2. **必须注册互踢监听 `addSimpleMsgListener`** —— 不注册则用户被踢后无感知。
   **Verify**: 检查 `addSimpleMsgListener` 出现 ≥1 次。

3. **必须在 `onKickedOffline` 回调里展示 UI 反馈 `errorMessage`** ——
   仅 print 不算,用户看不到。
   **Verify**: 检查 `onKickedOffline` 与 `errorMessage` 各出现 ≥1 次。

为什么是正例:
- 每条用强动词("必须导入""必须注册"),不用"应该""建议"
- backtick 内是**精确的可 grep 字符串**(类名/方法名)
- 规则文字承诺的范围 ≤ Verify 能验的范围(无维度溢出)
- 每条都有"违反后果"

4️⃣ ❌ 反例(及红旗词诊断)
1. **应该正确处理互踢回调** —— 否则用户体验不好。
   **Verify**: 检查互踢逻辑是否完整。
   ↑ 软词"应该" + 模糊动词"处理" + Verify 不可机械化

2. **必须调用 `login()` 或 `loginWithSig()`** —— 没登录无法用 SDK。
   **Verify**: 检查 `login` 出现。
   ↑ "或" = 红旗词;只 grep 一个 ≠ 验了选择

3. **必须按业务场景选择互踢策略** —— 业务决定。
   **Verify**: 检查策略配置是否合理。
   ↑ "按业务""合理" = 不可机械验证,应下沉到「最佳实践」软规则

🚩 红旗词表(出现任一即重写)
- 「或 / 任一」 → 拆两条 MUST 各管一个分支
- 「等价 / 或类似」 → 显式枚举所有可接受写法
- 「按业务 / 根据场景」 → 完全移出 MUST,移到「代码示例」按场景给完整 demo
- 「留给 / 负责」 → 移到「集成检查点」,作为 AI 读但 apply 不验的引导
- 「多 backtick 但 Verify 只提一个」 → 拆原子规则;调用顺序写到「调用时序」

✍️ 自查三问(写完每条 MUST 之前问自己)
1. backtick 里的符号是不是 verify 唯一会做的事?规则文字其他词能不能删?
2. 如果 AI 写**等价但不同写法**的代码,verify 会不会误杀?误杀 = 规则太死。
3. 如果 AI 写**只满足 backtick 字符串但语义错**的代码,verify 会不会放过?放过 = 规则太松。

5️⃣ 必填项语义三件套
- 违反后果:MUST 含红旗词 → apply 误杀正确代码 + 训练 AI 凑字符串 → slice 不可合并(2024-12 真实事故:room-lifecycle 写"调 A 或 B",apply 验过却生成错误混合代码)
- 验证手段:python scripts/check_must_rules.py {file}
  通过标准:红旗词命中 0 次;每条 MUST 都有 Verify;Verify 内有 backtick
- 绕过条件:**无**。MUST 是硬约束区,不接受任何豁免。需要"或/按业务"语义 → 拆原子规则,或下沉到「最佳实践」软规则区
-->

#### MUST NOT(生成时绝不能出现)

<!-- 指引: MUST NOT [必填,至少 2 条]

1️⃣ 你必须写什么
列出**绝不允许出现**的代码模式。重点写「看起来能跑但逻辑错误」的写法 —— 编译器抓不到,只有了解业务语义才能避免。

2️⃣ 写作模板
1. **不要 {动作} `{符号}`** —— {违反后果}。
   **Verify**: 检查 `{符号}` 出现 0 次(或在特定上下文中出现 0 次)。

3️⃣ ✅ 正例
1. **不要在 `onKickedOffline` 回调里调用 `login()`** —— 自动重登形成两端死循环互踢,
   最终两端都登不上。
   **Verify**: 在 `onKickedOffline` 函数体内,`login` 出现 0 次。

2. **不要在客户端代码里硬编码 `SecretKey`** —— 密钥泄露后可签发任意 UserSig。
   **Verify**: 全文 `SecretKey` 出现 0 次。

3. **不要把 `leaveRoom()` 当成解散会议** —— 房主离开后房间仍在,其他成员卡死。
   **Verify**: 房主代码路径中,房主收口必须用 `endRoom`,不能用 `leaveRoom`。

4. **不要用 `try?` 吞掉 `loginWithSig` 的错误** —— 静默失败导致后续 API 全失败但无日志可查。
   **Verify**: `try?\\s+.*loginWithSig` 出现 0 次(grep -E)。

为什么是正例:
- 每条精确到"哪个上下文里不能出现哪个符号"
- Verify 是 0 次匹配,机械可验

4️⃣ ❌ 反例
1. 不要写不安全的代码。
2. 避免循环引用。
3. 不要忽略错误。
→ 全部模糊,无 backtick,无 Verify,grep 不到

5️⃣ 必填项语义三件套
- 违反后果:MUST NOT 缺失或模糊 → AI 生成代码引入安全/性能/稳定性问题
- 验证手段:同 MUST,跑 python scripts/check_must_rules.py
- 绕过条件:无
#### MUST NOT(生成时绝不能出现)

<!-- 指引: MUST NOT [必填,至少 2 条]

1️⃣ 你必须写什么
列出**绝不允许出现**的代码模式。重点写「看起来能跑但逻辑错误」的写法 —— 编译器抓不到,只有了解业务语义才能避免。

2️⃣ 写作模板
1. **不要 {动作} `{符号}`** —— {违反后果}。
   **Verify**: 检查 `{符号}` 出现 0 次(或在特定上下文中出现 0 次)。

3️⃣ ✅ 正例
1. **不要在 `onKickedOffline` 回调里调用 `login()`** —— 自动重登形成两端死循环互踢,
   最终两端都登不上。
   **Verify**: 在 `onKickedOffline` 函数体内,`login` 出现 0 次。

2. **不要在客户端代码里硬编码 `SecretKey`** —— 密钥泄露后可签发任意 UserSig。
   **Verify**: 全文 `SecretKey` 出现 0 次。

3. **不要把 `leaveRoom()` 当成解散会议** —— 房主离开后房间仍在,其他成员卡死。
   **Verify**: 房主代码路径中,房主收口必须用 `endRoom`,不能用 `leaveRoom`。

4. **不要用 `try?` 吞掉 `loginWithSig` 的错误** —— 静默失败导致后续 API 全失败但无日志可查。
   **Verify**: `try?\\s+.*loginWithSig` 出现 0 次(grep -E)。

为什么是正例:
- 每条精确到"哪个上下文里不能出现哪个符号"
- Verify 是 0 次匹配,机械可验

4️⃣ ❌ 反例
1. 不要写不安全的代码。
2. 避免循环引用。
3. 不要忽略错误。
→ 全部模糊,无 backtick,无 Verify,grep 不到

5️⃣ 必填项语义三件套
- 违反后果:MUST NOT 缺失或模糊 → AI 生成代码引入安全/性能/稳定性问题
- 验证手段:同 MUST,跑 python scripts/check_must_rules.py
- 绕过条件:无
-->

### 集成检查点 [必填]

<!-- 指引: 集成检查点 [必填,至少 3 条]

1️⃣ 你必须写什么
假设目标是已有项目(不是从零开始的 demo),列出集成时需要确认的事项。
本 section 是软规则区(apply 不验),AI 阅读后自行判断。

2️⃣ 写作模板
- 是否与项目已有 SDK 初始化冲突?(检查 `{初始化函数}` 是否已在别处调用)
- 是否依赖其他 slice 的前置状态?(本 slice 依赖 → `{slice-id}`)
- 对已有代码的侵入性:`{新增 X 个文件 / 修改 Y 个文件}`
- {本 slice 特有的集成关注点}

3️⃣ ✅ 正例
- 是否与项目已有 SDK 初始化冲突?检查项目中 `V2TIMManager.sharedInstance().initSDK()`
  是否已被调用,若是则不要重复调用
- 是否依赖其他 slice?依赖 `chat/login-auth` 完成登录,依赖 `live/room-lifecycle` 已进房
- 对已有代码的侵入性:新增 1 个 ViewModel 文件,无需修改现有代码
- 是否在已有的 RoomEvent 监听基础上叠加?如已注册 `onUserSigExpired` 监听,本 slice 注册的是不同事件,可叠加;若已注册 `onKickedOffline`,需合并而非新增

4️⃣ ❌ 反例
- 集成时注意一下 SDK 冲突。
- 看看有没有依赖。
- 影响应该不大。
→ "注意一下""看看""应该不大" = 软词,无可操作信息

5️⃣ 必填项语义三件套
- 违反后果:不写检查点 → 集成时与已有代码冲突(双重初始化、状态污染)→ 客户报"按文档接但跑不起来"
- 验证手段:必须有 ≥3 条;每条引用具体函数/slice/文件数
- 绕过条件:无
<!-- 指引: 集成检查点 [必填,至少 3 条]

1️⃣ 你必须写什么
假设目标是已有项目(不是从零开始的 demo),列出集成时需要确认的事项。
本 section 是软规则区(apply 不验),AI 阅读后自行判断。

2️⃣ 写作模板
- 是否与项目已有 SDK 初始化冲突?(检查 `{初始化函数}` 是否已在别处调用)
- 是否依赖其他 slice 的前置状态?(本 slice 依赖 → `{slice-id}`)
- 对已有代码的侵入性:`{新增 X 个文件 / 修改 Y 个文件}`
- {本 slice 特有的集成关注点}

3️⃣ ✅ 正例
- 是否与项目已有 SDK 初始化冲突?检查项目中 `V2TIMManager.sharedInstance().initSDK()`
  是否已被调用,若是则不要重复调用
- 是否依赖其他 slice?依赖 `chat/login-auth` 完成登录,依赖 `live/room-lifecycle` 已进房
- 对已有代码的侵入性:新增 1 个 ViewModel 文件,无需修改现有代码
- 是否在已有的 RoomEvent 监听基础上叠加?如已注册 `onUserSigExpired` 监听,本 slice 注册的是不同事件,可叠加;若已注册 `onKickedOffline`,需合并而非新增

4️⃣ ❌ 反例
- 集成时注意一下 SDK 冲突。
- 看看有没有依赖。
- 影响应该不大。
→ "注意一下""看看""应该不大" = 软词,无可操作信息

5️⃣ 必填项语义三件套
- 违反后果:不写检查点 → 集成时与已有代码冲突(双重初始化、状态污染)→ 客户报"按文档接但跑不起来"
- 验证手段:必须有 ≥3 条;每条引用具体函数/slice/文件数
- 绕过条件:无
-->

## 验证矩阵 [必填]

<!-- 指引: 验证矩阵 [必填]

1️⃣ 你必须写什么
平台 slice 末尾的**统一验收出口**。AI 生成代码后或人工 review 时,自上而下跑一遍即可完成验收。
这是 SuperPowers「验证门」机制在 slice 层的落地——**禁止在没跑过验证矩阵的情况下声称完成**。

2️⃣ 4 个层级
- 1. 编译级:能编译、依赖齐全(CI / AI 自动)
- 2. 静态规则级:纯静态扫描 / grep 可查(CI / AI 自动)
- 3. 运行时级:跑起来通过日志锚点可观察(AI 半自动 / 人工)
- 4. 业务行为级:人眼看 UI / 硬件状态(人工)

要求(不可省):
- 每条「代码生成约束」MUST/MUST NOT 都要在矩阵中有对应行(层级 1 或 2)
- 至少 1 条层级 3 的检查,证明代码真能跑
- 至少 1 条层级 4 的检查,证明业务语义正确

3️⃣ ✅ 正例(摘自 live/ios/coguest-apply)

| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 模块导入齐全 | xcodebuild build -scheme Demo | exit code 0 |
| 1. 编译级 | iOS 最低版本 ≥ 13.0 | 查 Podfile/project.pbxproj | IPHONEOS_DEPLOYMENT_TARGET = 13.0 |
| 2. 静态规则级 | 所有 sink 都 [weak self] | grep -E "sink\\s*\\{\\s*\\[weak self\\]" | 匹配数 == sink 总数 |
| 2. 静态规则级 | AnyCancellable 是实例属性 | grep "var cancellables: Set<AnyCancellable>" | 至少 1 处 |
| 2. 静态规则级 | 每个 .failure 有 errorMessage | grep -B 5 "case .failure" \| grep errorMessage | 无裸 print |
| 3. 运行时级 | 申请发送成功 | 观众点申请 → 查日志 | [CoGuest] 申请已发送 |
| 3. 运行时级 | 主播收到事件 | 主播端查日志 | onGuestApplicationReceived |
| 3. 运行时级 | 超时 UI 反馈 | 主播不响应,等 30s | UI 展示"申请超时" |
| 4. 业务行为级 | 通过前设备未开 | 点申请但未同意 | 摄像头指示灯不亮 |
| 4. 业务行为级 | 断开后设备关闭 | 连麦中主动断开 | 摄像头指示灯熄灭 |

为什么是正例:
- 4 层各有 ≥2 行,覆盖完整
- 「检查项」都对应代码生成约束的 MUST/MUST NOT
- 「验证手段」都是可执行命令或具体操作
- 「预期结果」精确到字符串/状态/数值

4️⃣ ❌ 反例

| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1 | 能编译 | 编译看看 | 没报错 |
| 2 | 代码规范 | 看一下代码 | 没问题 |

→ "看看""没问题" = 不可机械验证;层级 3、4 缺失;无对应 MUST

5️⃣ 必填项语义三件套
- 违反后果:验证矩阵不全 → AI/人工无法系统性自验 → "应该没问题"上线 → 线上事故
- 验证手段:python scripts/check_verify_matrix.py {file}
  通过标准:4 层各 ≥1 行;每条 MUST/MUST NOT 都能在层级 1 或 2 找到对应行;至少 1 条层级 3、1 条层级 4
- 绕过条件:无
<!-- 指引: 验证矩阵 [必填]

1️⃣ 你必须写什么
平台 slice 末尾的**统一验收出口**。AI 生成代码后或人工 review 时,自上而下跑一遍即可完成验收。
这是 SuperPowers「验证门」机制在 slice 层的落地——**禁止在没跑过验证矩阵的情况下声称完成**。

2️⃣ 4 个层级
- 1. 编译级:能编译、依赖齐全(CI / AI 自动)
- 2. 静态规则级:纯静态扫描 / grep 可查(CI / AI 自动)
- 3. 运行时级:跑起来通过日志锚点可观察(AI 半自动 / 人工)
- 4. 业务行为级:人眼看 UI / 硬件状态(人工)

要求(不可省):
- 每条「代码生成约束」MUST/MUST NOT 都要在矩阵中有对应行(层级 1 或 2)
- 至少 1 条层级 3 的检查,证明代码真能跑
- 至少 1 条层级 4 的检查,证明业务语义正确

3️⃣ ✅ 正例(摘自 live/ios/coguest-apply)

| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 模块导入齐全 | xcodebuild build -scheme Demo | exit code 0 |
| 1. 编译级 | iOS 最低版本 ≥ 13.0 | 查 Podfile/project.pbxproj | IPHONEOS_DEPLOYMENT_TARGET = 13.0 |
| 2. 静态规则级 | 所有 sink 都 [weak self] | grep -E "sink\\s*\\{\\s*\\[weak self\\]" | 匹配数 == sink 总数 |
| 2. 静态规则级 | AnyCancellable 是实例属性 | grep "var cancellables: Set<AnyCancellable>" | 至少 1 处 |
| 2. 静态规则级 | 每个 .failure 有 errorMessage | grep -B 5 "case .failure" \| grep errorMessage | 无裸 print |
| 3. 运行时级 | 申请发送成功 | 观众点申请 → 查日志 | [CoGuest] 申请已发送 |
| 3. 运行时级 | 主播收到事件 | 主播端查日志 | onGuestApplicationReceived |
| 3. 运行时级 | 超时 UI 反馈 | 主播不响应,等 30s | UI 展示"申请超时" |
| 4. 业务行为级 | 通过前设备未开 | 点申请但未同意 | 摄像头指示灯不亮 |
| 4. 业务行为级 | 断开后设备关闭 | 连麦中主动断开 | 摄像头指示灯熄灭 |

为什么是正例:
- 4 层各有 ≥2 行,覆盖完整
- 「检查项」都对应代码生成约束的 MUST/MUST NOT
- 「验证手段」都是可执行命令或具体操作
- 「预期结果」精确到字符串/状态/数值

4️⃣ ❌ 反例

| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1 | 能编译 | 编译看看 | 没报错 |
| 2 | 代码规范 | 看一下代码 | 没问题 |

→ "看看""没问题" = 不可机械验证;层级 3、4 缺失;无对应 MUST

5️⃣ 必填项语义三件套
- 违反后果:验证矩阵不全 → AI/人工无法系统性自验 → "应该没问题"上线 → 线上事故
- 验证手段:python scripts/check_verify_matrix.py {file}
  通过标准:4 层各 ≥1 行;每条 MUST/MUST NOT 都能在层级 1 或 2 找到对应行;至少 1 条层级 3、1 条层级 4
- 绕过条件:无
-->

| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | {模块导入齐全} | {xcodebuild build / ./gradlew assembleDebug / tsc --noEmit} | exit code 0 |
| 1. 编译级 | {最低版本达标} | {查项目 deployment target} | ≥ {版本} |
| 2. 静态规则级 | {对应 MUST 规则 1} | {grep 正则} | {匹配条件} |
| 2. 静态规则级 | {对应 MUST NOT 规则 1} | {grep 正则} | {不应匹配} |
| 3. 运行时级 | {关键路径日志} | {触发操作 → 查日志} | {日志内容} |
| 4. 业务行为级 | {业务语义观察} | {操作步骤} | {UI / 硬件状态} |

---

## DoD 自查(提交前删除此 section)

<!-- 指引: 提交前对照 slice-spec.md 第五节「平台实现文件 DoD」逐条打勾。
**任何一项未满足 = 未完成,不允许提 PR**。

⚠️ 仅打勾不跑命令 = 视为未验证。每条标了"验证命令"的项,必须在 PR 描述粘贴命令输出。

最关键的 5 个一票否决项:
- [ ] api_docs 链接精确到类/模块级
      验证:python scripts/validate_api_docs.py {file}
- [ ] 代码示例无 ... 省略,每个 .failure 有 errorMessage
      验证:grep -E "\\.\\.\\." {file} 命中 0 次
- [ ] 代码生成约束 MUST 不含红旗词
      验证:python scripts/check_must_rules.py {file}
- [ ] 验证矩阵 4 层齐全,覆盖所有 MUST/MUST NOT
      验证:python scripts/check_verify_matrix.py {file}
- [ ] 平台特有注意事项 ≥ 1 条,每条含"必须做:"
-->
## DoD 自查(提交前删除此 section)

<!-- 指引: 提交前对照 slice-spec.md 第五节「平台实现文件 DoD」逐条打勾。
**任何一项未满足 = 未完成,不允许提 PR**。

⚠️ 仅打勾不跑命令 = 视为未验证。每条标了"验证命令"的项,必须在 PR 描述粘贴命令输出。

最关键的 5 个一票否决项:
- [ ] api_docs 链接精确到类/模块级
      验证:python scripts/validate_api_docs.py {file}
- [ ] 代码示例无 ... 省略,每个 .failure 有 errorMessage
      验证:grep -E "\\.\\.\\." {file} 命中 0 次
- [ ] 代码生成约束 MUST 不含红旗词
      验证:python scripts/check_must_rules.py {file}
- [ ] 验证矩阵 4 层齐全,覆盖所有 MUST/MUST NOT
      验证:python scripts/check_verify_matrix.py {file}
- [ ] 平台特有注意事项 ≥ 1 条,每条含"必须做:"
-->

提交前对照 `slice-spec.md` 第五节「平台实现文件 DoD」逐条打勾。任何一项未满足 = 未完成。
提交前对照 `slice-spec.md` 第五节「平台实现文件 DoD」逐条打勾。任何一项未满足 = 未完成。

---

> **填写范例**:请参考 [`slices/live/ios/coguest-apply.md`](slices/live/ios/coguest-apply.md) — 这是目前最完整的平台 slice 实现,包含所有 section 的真实内容。
> **完整规范**:见 [`slice-spec.md`](slice-spec.md) — 仅在批注不够用时回查。
> **填写范例**:请参考 [`slices/live/ios/coguest-apply.md`](slices/live/ios/coguest-apply.md) — 这是目前最完整的平台 slice 实现,包含所有 section 的真实内容。
> **完整规范**:见 [`slice-spec.md`](slice-spec.md) — 仅在批注不够用时回查。
