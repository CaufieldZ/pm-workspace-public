---
id: general-conference
name: 通用会议
product: conference
room_type: standard
industry: generic

trigger:
  intent_keywords:
    - 通用会议
    - 标准视频会议
    - 多人会议
    - 在线会议
    - 团队会议
    - 远程协作会议
    - standard meeting
    - general meeting
    - team meeting

slices:
  - conference/login-auth
  - conference/prejoin-check
  - conference/room-lifecycle
  - conference/participant-list
  - conference/video-layout
  - conference/device-control
  - conference/network-quality
  - conference/room-chat
  - conference/screen-share
  - conference/participant-management
  - conference/room-schedule
  - conference/room-call
  - conference/beauty-effects
  - conference/virtual-background
---

# 通用会议 Slice 映射

## 结论

如果客户说的是 **通用会议场景 / 标准视频会议 / 多人会议 / 在线会议 / 团队会议 / 远程协作会议**，那么在当前 `conference` 体系里，优先命中的不应是某一个孤立能力，而应是一组围绕 **会前预览、房间生命周期、参会人状态、画面布局、设备稳定性、会中协作** 展开的默认会议主链路 slices。

与教育、医疗这类行业场景不同，通用会议本身就是 `conference` 的默认问题域，因此更适合按 **“默认骨架先成立，产品外壳再补齐，增强能力按需叠加”** 的方式来理解和命中。

同时要补一条明确的**识别失败兜底规则**：如果需求分析阶段**未能识别出教育场景、医疗场景或 webinar 场景**，但用户描述的仍然是多人实时音视频沟通、多人进房、参会人管理、画面布局、设备控制、网络稳定性、主持控场这类典型会议能力，那么应**统一回落到 `通用会议场景`**，不要让这类需求悬空。

## 从真实产品形态可提炼的结论

基于典型会议产品界面，可以稳定提炼出以下产品形态：

1. **通用会议通常有独立的会前首页，而不是登录后立刻进房**：
   - 首页中间常驻 **本地视频预览**
   - 预览区下方直接提供 **麦克风 / 摄像头控制**
   - 首页主按钮通常是 **新建房间 / 加入房间 / 预定房间**
2. **预约会议列表是通用会议产品的高频外壳，而不是边缘功能**：
   - 首页右侧常见“今日 / 未来会议列表”
   - 用户可直接从预约列表进入会议，因此 `room-schedule` 在完整会议产品里通常是高频增强项
3. **会中页的稳定结构通常是“画面区 + 顶部状态栏 + 右侧面板 + 底部操作栏”**：
   - 画面区承接宫格布局或演讲者布局
   - 顶部通常展示会议主题、时长、语言切换和账号信息
   - 右侧常驻成员 / 聊天等信息面板
   - 底部集中放置设备、共享、邀请、聊天、成员、设置等操作入口
4. **布局切换是通用会议的默认能力，不应只被当成高级定制**：
   - 宫格布局、演讲者布局、共享时主画面切换，都是会议主舞台的基础能力
5. **成员面板不仅是展示区，还是主持治理入口**：
   - 右侧成员列表通常直接承接静音、移除、设管理员、禁画面等操作
   - 这意味着 `participant-list` 和 `participant-management` 在真实产品里是协同出现的
6. **会中邀请和视频效果是通用会议里的高频增强项**：
   - 邀请更多成员入会，通常作为底部工具栏或右侧面板的常驻入口
   - 美颜、虚拟背景、背景替换等视频效果，也常被放进设置或视频效果面板，而不是完全后置能力
7. **主题切换、中英文切换、品牌头部等属于产品外壳，不应误写成 RTC 原子能力**：
   - 它们是会议产品的外层体验模块
   - RTC 主链路仍然聚焦在进会、会中协作、成员状态和稳定性上

> 一句话结论：**真实通用会议产品通常是“会前预览首页 + 预约列表 + 会中宫格/演讲者布局 + 右侧成员面板 + 底部协作工具栏”的组合，而不是只有一个进房页。**

## 为什么这个场景成立

### 1. 通用会议的核心目标是“把一场会稳定地开起来并顺畅地开下去”

多数客户说“做一个会议场景”时，第一反应通常不是白板、考试、会诊台这类行业能力，而是：

- 用户怎么登录进入会议系统
- 发起人怎么创建会议，成员怎么进入会议
- 会前怎么确认摄像头、麦克风、扬声器可用
- 会中界面怎么切宫格 / 演讲者布局，谁在说话、谁是什么角色
- 屏幕共享、聊天、邀请、成员管理如何协同
- 弱网、断线、重连时怎么提示和恢复

这决定了通用会议的第一层命中，应该始终围绕 **登录 → 会前预览 → 房间生命周期 → 参会人状态 → 视频布局 → 设备与网络稳定性** 展开。

### 2. 通用会议更适合“默认骨架先成立，再叠加产品化外壳和增强能力”

当用户说“做通用会议 / 做一个会议产品”时，最合理的命中方式应理解为：

- 先命中 **接入前提**：`login-auth`
- 再命中 **会前预览与设备确认**：`prejoin-check`、`device-control`
- 再命中 **房间主链路**：`room-lifecycle`
- 再命中 **参会人和画面状态层**：`participant-list`、`video-layout`
- 再命中 **稳定性底座**：`network-quality`
- 如果是完整会议产品，再补 **预约列表 / 到点入会**：`room-schedule`
- 最后再根据是否涉及聊天、共享、主持控制、成员治理、会中呼叫、视觉增强，补命中其他 slices

## 与行业场景的关系

| 需求形态 | 是否仍以标准房间为 RTC 基座 | 说明 |
|------|--------------------------|------|
| 多人医疗会诊 | 是 | 多位医生 / 患者 / 家属在同一房间协作时，本质仍是 `standard` 房型；候诊、病历、会诊单等属于医疗业务外壳。 |
| 互动式小班课 / 双向课堂 | 是 | 如果学生需要频繁上麦、开摄、点名互动，仍应先复用 `standard` 房型骨架，再叠加教育外壳。 |
| 讲授式培训 / 在线宣讲 / 在线研讨会 | 否 | 如果主讲人中心化明显、观众长期以观看 / 聊天 / 问答为主，更应分流到 `webinar-conference.md`。 |

> 一句话边界：`general-conference.md` 解决的是 **标准房间** 的 RTC 基座，不负责吞掉所有教育、医疗、培训行业形态。

## 会议主链路与产品外壳层

### 会议主链路

以下能力属于本文真正要解决的会议骨架：

- `login-auth`
- `prejoin-check`
- `room-lifecycle`
- `participant-list`
- `video-layout`
- `device-control`
- `network-quality`
- `room-chat`
- `screen-share`
- `participant-management`
- `room-schedule`
- `room-call`
- `beauty-effects`
- `virtual-background`

### 产品外壳层

以下内容会出现在通用会议产品中，但默认不是 RTC 原子能力本身：

- 会议首页 / 品牌头部 / 主题切换 / 中英文切换
- 预约会议列表的 UI 容器与筛选交互
- 会中右侧侧栏容器（聊天 / 成员 / 会议信息）
- 设置面板、更多菜单、产品化导航壳层

## 通用会议的默认流程

### 默认主流程

| 步骤 | 阶段目标 | 主要命中 slices | 说明 |
|------|----------|-----------------|------|
| 1. 用户进入会议系统 | 完成账号登录，建立可用会话 | `conference/login-auth` | 所有会议后续动作都依赖稳定登录态。 |
| 2. 进入会前预览首页 | 完成本地视频预览、麦克风 / 摄像头确认 | `conference/prejoin-check`, `conference/device-control`, `conference/beauty-effects`, `conference/virtual-background` | 完整会议产品里，会前预览通常是默认入口；视频效果是高频增强项。 |
| 3. 创建 / 加入 / 预约会议 | 建立会议房间或确认未来会议安排 | `conference/room-lifecycle`, `conference/room-schedule` | 新建、加入、预约列表、到点入会都应在这里收口。 |
| 4. 渲染会议主界面 | 呈现参会人、画面布局和基础状态 | `conference/participant-list`, `conference/video-layout` | 会中主界面通常包含宫格 / 演讲者布局、顶部状态栏和右侧信息面板。 |
| 5. 进行会中协作 | 聊天、共享、主持控场、成员治理、会中呼叫 | `conference/room-chat`, `conference/screen-share`, `conference/participant-management`, `conference/room-call` | 这些能力在正式会议产品里往往组合出现，而不是孤立使用。 |
| 6. 处理设备与网络异常 | 保证会议持续可用 | `conference/device-control`, `conference/network-quality`, `conference/room-lifecycle` | 弱网、断线、设备占用、权限拒绝等问题都应在会中流程里统一处理。 |
| 7. 离会或结束会议 | 退出当前会议并清理会中状态 | `conference/room-lifecycle`, `conference/device-control` | 主持人结束会议与普通成员离会都属于流程收口阶段。 |

### 一个更容易理解的顺序

- **登录进入系统** → `conference/login-auth`
- **会前预览与设备确认** → `conference/prejoin-check`, `conference/device-control`
- **创建 / 加入 / 预约会议** → `conference/room-lifecycle`, `conference/room-schedule`
- **渲染成员与画面布局** → `conference/participant-list`, `conference/video-layout`
- **按需叠加聊天、共享、会控、成员治理、会中呼叫** → `conference/room-chat`, `conference/screen-share`, `conference/participant-management`, `conference/room-call`
- **处理弱网、断线、设备异常** → `conference/network-quality`, `conference/room-lifecycle`, `conference/device-control`
- **离会 / 结束并释放资源** → `conference/room-lifecycle`, `conference/device-control`

## 需求点到 Slice 的映射

| 通用会议需求点 | 主要命中 slices | 判断原因 |
|------|------------------|---------|
| 用户登录并进入会议系统 | `conference/login-auth` | 所有会议能力都建立在统一鉴权和会话有效性的前提上。 |
| 会前首页本地视频预览、麦克风 / 摄像头控制 | `conference/prejoin-check`, `conference/device-control` | 这是通用会议产品的高频入口形态。 |
| 新建会议、加入会议、离开会议、结束会议 | `conference/room-lifecycle` | 通用会议最核心的主链路就是房间生命周期；它统一覆盖创建、加入、离开、恢复和结束。 |
| 设置会议主题、密码、默认禁麦等初始规则 | `conference/room-lifecycle` | 会议创建时的配置选项已整合到房间生命周期 slice 中。 |
| 首页显示预约会议列表、会议排期、到点提醒 | `conference/room-schedule`, `conference/room-lifecycle` | 排期属于未来时间维度；到点后真正进房和结束仍回到房间生命周期。 |
| 显示参会人列表、角色、发言态、设备态 | `conference/participant-list` | 会议内“谁在场、谁是什么状态”都汇总在这里。 |
| 宫格布局、演讲者布局、共享时主画面切换 | `conference/video-layout`, `conference/screen-share` | 画面呈现由 `video-layout` 承担，共享状态由 `screen-share` 提供并驱动画面切换。 |
| 右侧成员面板和更多成员操作 | `conference/participant-list`, `conference/participant-management` | 成员面板不仅展示名单，也承接静音、移除、设管理员、禁画面等治理动作。 |
| 摄像头、麦克风、扬声器的开关、切换和异常恢复 | `conference/device-control` | 会中设备控制属于通用会议的基础底座能力。 |
| 弱网提示、超时告警、断线恢复建议 | `conference/network-quality`, `conference/room-lifecycle` | 一个负责网络稳定性观测，一个负责真正的离房收口和重入恢复。 |
| 会中聊天、消息互动、历史消息和禁聊联动 | `conference/room-chat` | 会议里的文本协作入口落在这里。 |
| 屏幕共享、演示文档、汇报讲解 | `conference/screen-share`, `conference/video-layout`, `conference/participant-management` | 共享是媒体能力，布局负责响应，会控负责约束共享权限。 |
| 会中临时呼叫、拉人入会 | `conference/room-call`, `conference/participant-management`, `conference/room-lifecycle` | 呼叫是信令链路，谁有权发起由成员治理约束，真正进房回到房间生命周期。 |
| 美颜、虚化、背景替换等视频效果 | `conference/beauty-effects`, `conference/virtual-background`, `conference/device-control` | 这些是通用会议里的常见增强项，通常出现在会前预览或会中设置面板。 |
| 中英文切换、黑白主题、品牌头部等产品壳层 | 业务会议外壳 + `conference/video-layout` | 这些能力会影响产品体验，但不应误拆成 RTC 原子能力。 |
| 白板 / 画布 / 共创区与会议同屏展示 | `conference/video-layout`, `conference/screen-share` + 业务白板 / 画布模块 | 通用会议可以承接这类增强诉求；画布本身通常由业务模块实现，会议侧重点仍是视频区与共享区如何协同展示。 |
| 未识别出教育、医疗或 webinar 专属场景，但需求仍是多人音视频会议 | `conference/login-auth`, `conference/prejoin-check`, `conference/room-lifecycle`, `conference/participant-list`, `conference/video-layout`, `conference/device-control`, `conference/network-quality` | 这类需求本质仍是通用会议主链路，只是上层场景分类没有命中，应统一回落到通用会议骨架。 |

## 主命中分层建议

### P0 默认会议骨架

这些 slice 基本覆盖了大多数“通用会议产品”的第一层理解，通常都应作为 `P0` 默认能力一起考虑：

- `conference/login-auth`
- `conference/prejoin-check`
- `conference/room-lifecycle`
- `conference/participant-list`
- `conference/video-layout`
- `conference/device-control`
- `conference/network-quality`
- `conference/room-chat`
- `conference/screen-share`
- `conference/participant-management`
- `conference/room-schedule`
- `conference/room-call`

### P1 按需补命中

这些 slice 更依赖视觉体验诉求或设备性能是否明确：

- `conference/beauty-effects`：本地美颜增强
- `conference/virtual-background`：背景虚化与替换

## 能力展示与 coverage 选择

> **这是 topic Step 1.5 直接照抄并执行的章节**(coverage 多选变体,见 `scenario-spec.md`)。
> 通用会议**不是**"全部 slice 一起装"的 Form A;它是"骨架必装 + 其他按显式需求补命中"。
> 不要把整张 `slices:` 清单当成默认全集——那正是"用户没要美颜却被装上美颜"的根因。

### 必装骨架(always on,不向用户提问)

最小可开会的主链路,始终包含:

- `conference/login-auth`
- `conference/prejoin-check`
- `conference/room-lifecycle`
- `conference/participant-list`
- `conference/video-layout`
- `conference/device-control`
- `conference/network-quality`

### 可选模块(多选,默认只勾选命中用户需求的项)

- `conference/room-chat` —— 会中聊天
- `conference/screen-share` —— 屏幕共享 / 演示
- `conference/participant-management` —— 成员治理(禁麦禁画、移除、设管理员、角色控制)
- `conference/room-schedule` —— 预约会议 / 排期 / 到点入会
- `conference/room-call` —— 会中呼叫 / 拉人入会
- `conference/beauty-effects` —— 本地美颜
- `conference/virtual-background` —— 背景虚化 / 替换

### 执行规则(topic 必须遵守)

1. **预勾选 = 仅命中用户显式需求。** 读 session 的 `target_features` 和用户原始 prompt,用本文件「再按显式词补命中增强 slices」一节的关键词映射,把命中的可选模块预勾选。**没被点名的可选模块一律默认不勾选**(尤其美颜 / 虚拟背景 / 预约 —— 不要因为"通用会议产品常见"就默认装上)。
2. **展示文案**(translate to user's language):

   ```
   我帮你定位到「通用会议」场景。会议骨架(登录、会前预览、房间生命周期、成员列表、画面布局、设备控制、网络质量)会默认集成。

   你的需求里我识别到要这些增强能力:{命中的可选模块中文名}
   你的需求里我识别到要这些增强能力:{命中的可选模块中文名}

   以上无误吗？
   以上无误吗？
   ```

3. **确认 / 选择可选模块**（二选一，不得混用）：

   **3a. 确认优先（当 `target_features` 已非空且无歧义）**：展示命中的可选模块列表，用 `AskUserQuestion` 提一个确认问题（"以上增强能力无误，继续？"），选项：(1) 确认，按此集成；(2) 需要调整能力范围。选 (1) 直接进入步骤 4；选 (2) 走 3b。不要重复让用户从头选择他们已经说清楚的功能。

   **3b. 多选（仅当 `target_features` 为空 / 模糊，或用户选了「需要调整」）**：
   ```
   还要加别的吗？(可多选，不需要的就不用勾)
   ```
   对「可选模块」做一次多选（`multiSelect: true`），选项 label 用上面的中文名，**预勾选第 1 步命中的项**。一次超过 4 项时按"会中协作 / 视频效果 / 预约邀请"分组拆成多次问（遵守 4 选项上限）。
4. **写 `confirmed_plan`**:`confirmed_plan = 必装骨架 + 用户最终选中的可选模块`(去重,保持上面声明的顺序)。这是 `init_slice_queue.py` 的唯一输入,后续 A2-Q1.5 业务决策、slice 循环、apply 都以它为准。
5. **不要**把未选中的可选模块写进 `confirmed_plan`,也不要在生成代码时"顺手"加它们的按钮 / composable。
6. `enhancement_level` 仅为兼容旧字段:全部可选模块都选 → `complete`,否则 → `minimal`。真正的范围以 `confirmed_plan` 为准。

> **边界澄清**:如果用户原始 prompt 就是"做一个完整的通用会议产品 / 给我全套 / 完整版",则可选模块全选(等价 `complete`)。只有当用户点名了具体功能子集时,才按"骨架 + 命中项"收敛。

## 典型通用会议子场景的命中差异

### 1. 会前预览首页型会议产品

优先命中：

- `conference/login-auth`
- `conference/prejoin-check`
- `conference/device-control`
- `conference/room-lifecycle`
- `conference/room-schedule`

这类场景更强调“进入系统后先预览设备，再决定新建 / 加入 / 预约会议”。

### 2. 日常团队会议

优先命中：

- `conference/login-auth`
- `conference/prejoin-check`
- `conference/room-lifecycle`
- `conference/participant-list`
- `conference/video-layout`
- `conference/device-control`
- `conference/network-quality`
- `conference/room-chat`

这类场景更强调默认主链路、稳定性和轻协作。

### 3. 主持型宣讲 / 培训会议

在默认会议骨架基础上补命中：

- `conference/room-lifecycle`
- `conference/screen-share`
- `conference/participant-management`

这类场景更依赖主持秩序、共享展示和参会人治理。

### 4. 预约式正式会议

在默认会议骨架之外补命中：

- `conference/room-schedule`
- `conference/room-lifecycle`

如果业务由后台通过 REST API 先建房、到点后用户再进入，这仍然属于 `room-schedule + room-lifecycle` 的组合，不需要单独再拆服务端 slice。

### 5. 会中呼叫的协作会议

补命中：

- `conference/room-call`
- `conference/participant-management`
- `conference/room-lifecycle`

这类场景强调"呼叫确认"和"真正进房"是两段链路。

### 6. 对视觉体验要求较高的会议

补命中：

- `conference/beauty-effects`
- `conference/virtual-background`
- `conference/device-control`

这类场景更关注本地视频前处理与展示体验，而不是会议骨架本身。

## 当前体系判断

通用会议场景基本就是当前 `conference` 目录的默认落点，因此：

- 不需要再单独补一个“通用会议专属底层 slice”
- 更重要的是把默认命中顺序排清楚，并把会前首页、预约列表、会中成员侧栏这些真实产品形态收束到正确边界
- 如果未来要增强“通用会议产品感”，更适合补的是装配层、样板工程或产品壳层，而不是重新拆分底层问题域

## 触发“通用会议场景”时的推荐命中策略

### 用户出现以下意图时，优先命中 P0 默认会议骨架

- 通用会议场景
- 标准视频会议
- 多人会议
- 在线会议
- 团队会议
- 远程协作会议
- 做一个会议产品
- 创建会议并加入
- 开一个多人视频会
- 实现会议功能

### 未识别出教育 / 医疗 / webinar 场景时的兜底处理

- 如果场景识别阶段没有稳定命中教育场景、医疗场景或 webinar 场景，不要直接丢失这类需求。
- 只要用户描述仍然落在“多人实时音视频开会”这条主线上，就应统一回落到 `通用会议场景`。
- 这里的“多人实时音视频开会”可包含：会前预览、多人进房、主持控场、参会人列表、宫格 / 演讲者布局、设备切换、网络质量、会中聊天、共享演示、预约会议、会中呼叫等通用会议能力。

### 再按显式词补命中增强 slices

- 提到“会前检测 / 麦克风测试 / 摄像头测试 / 本地预览” → `conference/prejoin-check`
- 提到"密码会议 / 默认禁麦 / 会议主题 / 初始规则" → `conference/room-lifecycle`
- 提到“踢人 / 设管理员 / 成员管理 / 成员列表更多操作” → `conference/participant-management`
- 提到"禁麦 / 禁摄 / 禁聊 / 主持人控场" → `conference/participant-management`
- 提到“聊天 / 会中消息 / 文本协作 / 右侧聊天面板” → `conference/room-chat`
- 提到“共享屏幕 / 演示 / 汇报” → `conference/screen-share`, `conference/video-layout`
- 提到“宫格布局 / 演讲者布局 / 主讲模式” → `conference/video-layout`
- 提到“预约 / 排期 / 到点入会 / 会议列表” → `conference/room-schedule`
- 提到"呼叫入会 / 拉人入会 / 呼叫在线用户 / 会中呼叫" → `conference/room-call`
- 提到“美颜 / 背景虚化 / 背景替换 / 视频效果” → `conference/beauty-effects`, `conference/virtual-background`
- 提到“主题切换 / 中英文切换 / 品牌头部” → 业务会议外壳
- 提到“后台创建房间 / 服务端解散房间 / REST API 建房” → `conference/room-lifecycle`, `conference/room-schedule`

## 一句话判断

**如果客户说要做通用会议场景，或者需求本来属于教育、医疗、 webinar 等上层场景但当前没有被稳定识别出来，只要核心诉求仍是多人实时音视频会议，就应优先回落到一组以 `login-auth`、`prejoin-check`、`room-lifecycle`、`participant-list`、`video-layout`、`device-control`、`network-quality` 为中心的默认会议骨架 slices；其他如聊天、共享、成员治理、预约会议、会中呼叫、美颜、虚拟背景和产品外壳等能力，再按显式需求补命中即可。**
