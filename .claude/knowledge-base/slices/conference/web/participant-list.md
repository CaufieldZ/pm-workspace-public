---
id: conference/participant-list
name: 参会人列表与状态
product: conference
platform: web
tags: [participant, list, state, speakingUsers, pendingParticipantList]
platforms: [web]
related: [conference/participant-management, conference/video-layout, conference/room-lifecycle, conference/network-quality]
api_docs:
  - title: 成员管理
    url: https://cloud.tencent.com/document/product/647/126927
---

# 参会人列表与状态

## 功能说明

参会人列表与状态负责会议内“谁在房间内、每个人当前是什么状态、这些状态如何被展示”的统一数据基础，覆盖在线成员、待入会成员、角色、音视频设备状态、屏幕共享、发言态、网络质量、禁言态以及业务扩展字段的展示与同步。布局、会控、聊天、网络诊断等能力都可以直接基于这份成员数据组织自己的界面和状态展示。

在产品层，成员面板既要满足基础成员信息展示，也可能承载更强的业务定制诉求；当业务需要自定义成员界面、排序规则、业务身份展示或扩展操作菜单时，应围绕同一份成员状态数据组织列表、分组、排序和状态展示，避免不同模块各自维护一套成员信息。

## 核心概念

### 角色与关注点

| 角色 | 关键关注点 | 说明 |
|------|------------|------|
| 当前参会人 | 查看成员状态 | 关注谁在会里、谁是房主 / 管理员、谁正在发言、谁正在共享或处于弱网 |
| 待入会成员 | 展示入会前状态 | 关注预约、呼叫中、未入会等状态；可展示在独立分区，但不参与在线成员统计、布局和会控判断 |
| 房主 / 管理员 | 查看成员情况 | 可在列表里看成员当前状态；真正的设管理员、踢人、转移房主等操作不在当前 slice 内完成 |
| 布局与挂件模块 | 消费成员读模型 | 使用成员状态驱动画面编排、角标、共享标识、发言高亮与状态挂件 |
| 业务扩展模块 | 投影业务信息 | 可把职务、业务身份、购买状态、标签等信息同步进参会人展示模型 |

> **边界说明：** `participant-list` 负责成员信息展示、状态同步与读模型消费，不负责定义或承接操作码；如果需要踢人、设管理员、转移房主、禁麦、禁聊等治理动作，应交给 `participant-management`。

### 事件流

| 阶段 | 参与方 | 关键动作 |
|------|--------|----------|
| 初始入会 | 客户端 | 建立房间后首次拉取在线成员列表，并初始化本地成员视角 |
| 待入会展示 | 客户端 | 展示预约、呼叫中或尚未进房的成员，但不把它们当作在线成员 |
| 状态同步 | 房间状态 | 成员加入、离开、角色变化、开关设备、屏幕共享、发言、禁言或网络质量变化时刷新读模型 |
| 列表扩展 | 客户端 | 大房间场景下按游标继续分页拉取更多成员，并做好去重与合并 |
| 业务投影 | 业务层 | 将名片、自定义元数据等业务字段映射到成员展示字段 |
| 退出清理 | 客户端 | 离房或房间结束后清理成员列表、待入会列表与相关派生状态 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| `participantList` | 当前已加载的在线成员列表，是判断“谁在房间内”的主来源 |
| `participantListCursor` | 分页继续拉取在线成员时使用的游标；非空表示仍可能有更多成员 |
| `pendingParticipantList` | 待入会、呼叫中、预约等尚未进房的成员集合，不等同于在线成员列表 |
| `localParticipant` | 当前用户在会议中的成员视角数据，可用于展示“我”和判断本地角色 |
| `speakingUsers` | 当前正在发言的成员集合及音量信息，用于发言高亮、音量波纹或闭麦说话提醒 |
| `networkQualities` | 成员网络质量信息，用于展示弱网标识或辅助管理员诊断 |
| `participantListWithVideo` | 当前开启摄像头的成员集合，可用于视频成员筛选和宫格排序 |
| `participantWithScreen` | 当前正在屏幕共享的成员，可用于共享中标识、共享画面置顶和布局切换 |
| `participant.role` / `localParticipant.role` | 成员角色状态，是判断房主、管理员、普通成员的推荐来源 |
| `participant.isMessageDisabled` | 成员是否被单独禁言，可用于展示禁言状态和聊天入口可用态 |
| `participant.metaData` / `nameCard` | 业务自定义数据和成员名片，可用于展示职务、业务身份、等级、购买状态等扩展信息 |

### 成员展示字段

| 字段 | 说明 | 展示建议 |
|------|------|----------|
| `userId` | 用户 ID | 作为列表 key 和成员定位标识；若后续进入治理链路，也可作为目标用户标识 |
| `userName` | 用户昵称 | 优先展示昵称；为空时可兜底展示 `userId` |
| `avatarUrl` | 头像地址 | 用于展示成员头像；在摄像头关闭时，也应作为视频挂件占位层的首选素材 |
| `role` | 成员角色 | 展示房主、管理员、普通成员等角色标签 |
| `roomStatus` | 成员在房间内状态 | 区分在房、呼叫中、预约等状态 |
| `microphoneStatus` | 麦克风状态 | 展示开麦、闭麦或被关闭状态 |
| `cameraStatus` | 摄像头状态 | 展示开摄像头、关摄像头或被关闭状态 |
| `screenShareStatus` | 屏幕分享状态 | 展示屏幕分享中标识 |
| `isMessageDisabled` | 消息禁用状态 | 展示禁言标识或禁用聊天入口 |
| `metaData` | 业务自定义数据 | 展示职务、部门、会员等级、购买状态等业务信息 |

### 成员排序建议

| 排序维度 | 推荐处理 |
|----------|----------|
| 本地用户 | 通常置顶，并展示“我”标识 |
| 房主和管理员 | 优先展示，便于用户识别管理者 |
| 屏幕共享成员 | 可置顶或展示“共享中”标识 |
| 正在发言成员 | 可短暂前置或高亮展示 |
| 开启摄像头成员 | 视频会议场景可优先展示 |
| 开启麦克风成员 | 可优先展示 |
| 普通成员 | 可按昵称、入会时间或业务字段排序 |

### 状态机

```text
empty
  → initial-loading
  → synced
  → paginating
  → synced
  → cleared
```

## 前置条件
**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`

**前置状态**：
- 已阅读 `conference/participant-list`，明确当前能力的产品边界。
- 已完成 `conference/login-auth`，确保当前页面具备稳定登录态。
- 已根据业务流程接入会议上下文；需要房间状态时，优先通过 `conference/room-lifecycle` 统一承接。

## 最佳实践

### ✅ ALWAYS

1. **把参会人列表当作会议读模型，而不是管理指令入口** —— 它负责展示和同步，不负责定义权限本身。
2. **在大房间场景中显式处理分页与游标** —— 首次拉取不应默认视为全量，首次最多可能只自动获取约 300 名成员，需要根据 `participantListCursor` 继续分页。
3. **区分在线成员和待入会成员** —— `participantList` 表示在线成员，`pendingParticipantList` 只适合展示“未入会”“呼叫中”“预约”等成员区。
4. **用真实角色字段判断房主和管理员** —— 通用会议中应优先使用 `participant.role` 或 `localParticipant.role`，不要依赖 `adminList`。
5. **把发言态、角色态、设备态、共享态和网络态同时投影到 UI** —— 成员列表、画面挂件、侧栏和诊断入口最好消费同一份成员状态来源。
6. **给成员展示信息准备稳定兜底字段** —— 昵称优先用 `nameCard` / `userName`，头像优先用 `avatarUrl`，缺失时至少要能回退到 `userId` 首字母，供成员列表和“关摄像头占位层”共用。
7. **把成员排序交给业务层明确生成** —— 按本地用户、房主/管理员、屏幕共享、发言、开摄像头和业务字段组合排序，避免不同模块顺序不一致。
8. **离房时清空成员列表及其派生状态** —— 防止下一场会议仍看到上一场会议的成员、发言态、共享态或弱网标识。

### ❌ NEVER

1. **不要直接根据显示文案推断权限** —— 房主、管理员等身份应来自真实成员状态，而不是列表上的文本。
2. **不要依赖 `adminList` 判断通用会议管理员身份** —— 通用会议不单独维护管理员列表，该状态通常为空数组。
3. **不要把 `pendingParticipantList` 当作在线成员列表** —— 待入会、呼叫中或预约成员不能直接参与在线成员统计、布局和会控判断。
4. **不要把成员列表的展示操作误当成权限修改成功** —— 真正的角色治理和踢人动作应回到 `participant-management`。
5. **不要忽略分页去重与离房清理** —— 否则很容易出现成员重复、幽灵成员或跨房间残留。
6. **不要使用旧版 `hasAudioStream` / `hasVideoStream` 字段判断设备状态** —— 当前 AtomicX `RoomParticipant` 类型没有这些字段。成员列表、远端画面挂件等成员读模型应读取 `participant.microphoneStatus`、`participant.cameraStatus`、`participant.screenShareStatus`；本地工具栏、会前预览和本地设备开关按钮应优先从 `useDeviceState().microphoneStatus` / `cameraStatus` / `screenStatus` 派生，避免本地设备状态与成员读模型短暂不同步。

## 代码示例
### 基础接入：拉取参会人列表并按游标分页

```ts
import { useRoomParticipantState } from 'tuikit-atomicx-vue3/room';

const { participantList, participantListCursor, getParticipantList, speakingUsers } = useRoomParticipantState();

await getParticipantList({ cursor: '' });
if (participantListCursor.value) {
  await getParticipantList({ cursor: participantListCursor.value });
}
console.log(participantList.value, speakingUsers.value);
```

## 调用时序
```
完成 login-auth 并进入会议
   │
   ▼
调用 getParticipantList({ cursor: '' })
   │
   ├─ 首次成功 → 渲染 participantList
   ├─ 存在下一页 → 使用 participantListCursor 继续拉取
   └─ 失败 → 提示加载失败并允许重试
   │
   ▼
结合 speakingUsers / metaData / 角色态更新列表 UI
```

## 平台特有注意事项
### 1. 成员列表与管理动作应分层
成员列表负责展示“谁在会里、状态如何”；踢人、设管理员、转移房主等动作应继续交给 `conference/participant-management`。

### 2. 分页游标需要持续复用
当参会人数较多时，列表不应假设一次性全量返回；应根据 `participantListCursor` 持续分页拉取。

### 3. 业务扩展字段建议走 `metaData`
如果要展示身份标签、业务等级或组织信息，建议通过 `metaData` 同步，而不是在 UI 层拼接一套旁路数据源。

## 代码生成约束
### 编译必要条件
- **通用条件**：见 [login-auth 平台 slice](login-auth.md)。
- **额外导入**：至少需要导入 `useRoomParticipantState`。
- **运行前提**：已进入会议，房间上下文可用。

### 生成规则
#### MUST（生成时必须包含）

1. **通过 `useRoomParticipantState` 承接成员列表数据** — 可以保持列表、发言态与角色信息同源。  
   **Verify**: 检查是否存在 `useRoomParticipantState()`。
2. **支持首屏加载与游标续拉** — 成员列表在多人场景下不能只写死首屏一次调用。  
   **Verify**: 检查是否存在 `getParticipantList({ cursor })` 与 `participantListCursor` 逻辑。

#### MUST NOT（生成时绝不能出现）

1. **不要把成员列表组件直接耦合管理操作权限** — 会让展示层和治理层边界混乱。  
   **Verify**: 检查踢人/转移房主逻辑是否放在独立治理能力中。
2. **不要忽略分页游标** — 在大房间场景会导致成员显示不完整。  
   **Verify**: 检查是否读取 `participantListCursor` 或提供加载更多逻辑。

### 集成检查点
- 当前 slice 常与 `conference/participant-management`、`conference/video-layout` 联动。
- 集成侵入性较低，通常新增一个侧栏、抽屉或列表区域即可。
- 若业务已有企业通讯录或组织树，需要明确“在线成员列表”和“组织架构列表”的来源边界。

## 验证矩阵
| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已导入 `useRoomParticipantState` | 检查 `import` 语句 | 成员状态 Hook 可解析 |
| 2. 静态规则级 | 存在首屏加载与分页逻辑 | 搜索 `getParticipantList` 与 `participantListCursor` | 形成分页加载链路 |
| 3. 运行时级 | 成员列表能正常展示与刷新 | 进房后打开成员列表 | 可看到参会人和状态信息 |
| 4. 业务行为级 | 人数增多时列表仍完整 | 多人会议中滚动加载更多 | 列表可持续补齐更多成员 |

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 成员列表不完整 | 房间里明明有成员，但列表只显示部分数据 | 检查首次拉取后是否继续基于 `participantListCursor` 分页获取更多成员 |
| 首次拉取后仍有游标 | 调用首屏加载后 `participantListCursor` 仍非空 | 这是大房间正常现象，不要把首次拉取当作全量，按需继续加载 |
| 管理员判断错误 | 通用会议中 `adminList` 为空，导致管理员入口不显示 | 改用 `participant.role` 或 `localParticipant.role` 判断角色 |
| 待入会成员被当作在线成员 | 呼叫中或预约成员进入在线人数、布局或会控判断 | 检查是否误用 `pendingParticipantList`，在线成员应以 `participantList` 为准 |
| 发言态显示异常 | 成员正在发言，但列表角标或布局挂件没有变化 | 检查 `speakingUsers` 是否与成员读模型联动，而不是独立维护另一份状态 |
| 网络或共享状态异常 | 弱网标识、共享中标识和实际状态不一致 | 检查 `networkQualities`、`participantWithScreen`、`participantListWithVideo` 是否与成员列表使用同一份状态源 |
| 离房后仍看到旧成员 | 切换到新房间后，列表残留上一场会议成员 | 检查离房和房间结束时是否统一清空成员列表与派生缓存 |

### 排障流程

```text
发现 参会人列表与状态 相关问题
├── 第 1 步：确认问题属于成员展示读模型，而不是权限治理或会控动作
├── 第 2 步：检查首屏加载、游标分页、成员去重和待入会成员分区是否完整
├── 第 3 步：确认 speakingUsers、角色态、设备态、共享态、网络态是否从同一份成员状态源派生
├── 第 4 步：检查角色判断是否使用 participant.role / localParticipant.role，而不是 adminList 或展示文案
└── 第 5 步：若仍异常，再回查 participant-management / video-layout / room-lifecycle / network-quality 的衔接是否正确
```

## 关联知识

- **[conference/participant-management](participant-management.md)** —— 成员角色治理、踢人和房主转移等写操作入口。
- **[conference/video-layout](video-layout.md)** —— 成员状态会驱动画面布局与单元挂件展示。
- **[conference/room-lifecycle](room-lifecycle.md)** —— 成员列表随入房、离房和房间结束而建立或清空。
- **[conference/network-quality](network-quality.md)** —— 成员网络质量可投影到成员列表和诊断入口。
