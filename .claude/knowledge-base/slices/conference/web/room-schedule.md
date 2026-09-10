---
id: conference/room-schedule
name: 预约会议
product: conference
platform: web
tags: [schedule, calendar, future-room, scheduledRoomList]
platforms: [web]
related: [conference/room-lifecycle, conference/room-call]
api_docs:
  - title: 预定房间
    url: https://cloud.tencent.com/document/product/647/126931
business_decisions:
  - key: schedule_features
    tier: blocking
    multi_select: true
    baseline: ["list"]   # 始终生成的基础能力，不作为多选项展示（预约会议列表默认提供）
    question: "预约会议需要支持哪些能力？（预约会议列表默认展示，以下为额外能力，可多选）"
    options:
      - { label: "修改或取消已预约的会议", value: "modify" }
      - { label: "为会议设置访问密码", value: "password" }
      - { label: "会议状态变更时发送通知（开始提醒、邀请、取消等）", value: "events" }
---

# 预约会议

## 功能说明

预约会议负责未来时间维度上的会议排期，覆盖预定会议、修改和取消预定、展示预定列表，以及会议临近开始时的提醒和入会入口。它关注的是“未来会议怎么被安排与兑现”，而不是会议真正开始后的房间主链路。

## 核心概念

### 角色与操作

| 角色 | 关键操作 | 说明 |
|------|----------|------|
| 会议组织者 | 创建、修改、取消预约会议 | 负责定义未来会议的时间和基础信息 |
| 被邀请或关注会议的用户 | 查看和进入预约会议 | 在会议临近时感知提醒，并在合适时间进入真实会议 |
| 日历 / 列表模块 | 承载排期展示 | 提供预约会议列表、筛选、更新和取消入口 |
| 房间生命周期模块 | 承接真实入会 | 预约会议到点后，真正进入会议仍需回到 `room-lifecycle` |

### 事件流

| 阶段 | 参与方 | 关键动作 |
|------|--------|----------|
| 创建预约 | 组织者 | 设置开始时间、结束时间、会议基础配置和预约参会人 |
| 列表展示 | 客户端 | 拉取并展示未来会议列表，并把预约结果同步给相关参会人入口 |
| 预约变更 | 组织者 / 系统 | 修改、取消或重排预约会议信息 |
| 即将开始 | 客户端 / 系统 | 触发“会议即将开始”的提醒与进入入口 |
| 真实入会 | 用户 | 到点后从预约会议入口进入真实房间主流程 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| 预约会议 ID / 房间 ID | 用于唯一标识一条未来会议记录以及其对应房间 |
| 开始 / 结束时间 | 定义会议的时间边界 |
| `scheduleAttendees` / 参会人集合 | 表示本次预约会议计划覆盖的目标参会人 |
| 预约状态 | 已预约、已修改、已取消、即将开始、已过期等状态 |
| 预约会议列表与游标 | 用于分页展示和拉取未来会议数据 |
| 提醒与入会入口状态 | 用于触发“即将开始”提示与进入会议动作 |

### 状态机

```text
draft
  → scheduled
  → updated
  → starting-soon
  → joining-room
  → completed

scheduled
  → cancelled
  → expired
```

## 前置条件
**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`

**前置状态**：
- 已阅读 `conference/room-schedule`，明确当前能力的产品边界。
- 已完成 `conference/login-auth`，确保当前页面具备稳定登录态。
- 已根据业务流程接入会议上下文；需要房间状态时，优先通过 `conference/room-lifecycle` 统一承接。

## 最佳实践

### ✅ ALWAYS

1. **把预约信息与真实房间生命周期分开处理** —— 预约会议是未来计划，真正入会要在到点后回到房间主链路。
2. **让即时会议和预约会议复用同一套房间配置模型** —— 会议名称、密码和默认规则最好保持一致语义。
3. **显式处理修改、取消和即将开始提醒** —— 预约会议不是只有“创建成功”一个状态。
4. **在列表与提醒中统一使用同一时间语义** —— 开始时间、结束时间、即将开始阈值要避免前后不一致。

### ❌ NEVER

1. **不要把创建预约会议当成已经创建了正在运行的房间** —— 预约成功不等于用户已经在会议里。
2. **不要忽略取消和过期状态** —— 预约类能力天然带有时间失效和状态变更特征。
3. **不要让预约列表、提醒入口和真实入会入口各自维护不同的会议身份** —— 否则很容易出现跳错会或进错房间。

## 代码示例
### 预约与取消：创建未来会议并分页读取列表

```ts
import { useRoomState } from 'tuikit-atomicx-vue3/room';

const { scheduleRoom, getScheduledRoomList, cancelScheduledRoom } = useRoomState();
const startTime = Math.floor(Date.now() / 1000) + 3600;

await scheduleRoom({
  roomId: 'schedule_room',
  options: {
    roomName: '周会',
    scheduleStartTime: startTime,
    scheduleEndTime: startTime + 1800,
    scheduleAttendees: ['user_a', 'user_b'],
  },
});

await getScheduledRoomList({ cursor: '' });
await cancelScheduledRoom({ roomId: 'schedule_room' });
```

### 读取预约列表：响应字段与「请求 / 响应」字段名不一致（高频踩坑）

```ts
import { useRoomState } from 'tuikit-atomicx-vue3/room';

const { getScheduledRoomList } = useRoomState();

// 返回 { scheduledRoomList: RoomInfo[]; cursor: string }
const res = await getScheduledRoomList({ cursor: '' });

const rooms = res.scheduledRoomList.map((room) => ({
  roomId: room.roomId,
  roomName: room.roomName,
  // ⚠️ 响应字段是 scheduledStartTime / scheduledEndTime（带 "d"），
  //    与「创建」请求里的 scheduleStartTime / scheduleEndTime（不带 "d"）拼写不同！
  //    用错名字会取到 undefined → 时间为 0 → 列表显示空 / 状态恒为「已结束」。
  startTimeMs: (room.scheduledStartTime ?? 0) * 1000, // 服务端秒级，展示前 *1000 转毫秒
  endTimeMs: (room.scheduledEndTime ?? 0) * 1000,
  // ⚠️ 响应里 scheduleAttendees 是 RoomUser[]（对象数组），不是创建请求里的 string[]
  attendees: (room.scheduleAttendees ?? []).map((u) => u.userId),
}));

const nextCursor = res.cursor; // 续拉下一页
```


## 调用时序
```
完成 login-auth
   │
   ▼
准备预约时间与房间信息
   │
   ▼
scheduleRoom({ roomId, options })
   │
   ├─ 成功 → 写入预约列表
   ├─ 需要查看更多 → getScheduledRoomList({ cursor })
   └─ 用户取消预约 → cancelScheduledRoom({ roomId })
   │
   ▼
会议临近时结合提醒事件与 room-lifecycle 引导入会
```

## 平台特有注意事项
### 1. 时间参数为「秒级」时间戳（注意：SDK 的 .d.ts 注释会误导）
预约接口（创建与列表响应）的时间单位是**秒级** UNIX 时间戳。
⚠️ `tuikit-atomicx-vue3` 的 TypeScript 声明（`.d.ts`）把这些字段注释成「毫秒时间戳」、
示例也写成 `Date.now() + 3600000`，但服务端实际收 / 发的是**秒**。**以秒为准**：
- 创建：`scheduleStartTime: Math.floor(Date.now() / 1000) + 3600`
- 读取：响应里的 `scheduledStartTime / scheduledEndTime` 也是秒；前端要和 `Date.now()`（毫秒）
  比较或交给 `new Date()` 展示时，需先 `* 1000`。

建议应用内部统一用毫秒，只在「调用 / 解析 SDK」这一层做秒↔毫秒转换，避免单位散落各处。

### 2. 「创建请求」与「列表响应」的字段名不一致
这是最容易静默出错的点：
| 含义 | 创建请求 `ScheduleRoomOptions` | 列表响应 `RoomInfo` |
|------|------|------|
| 开始时间 | `scheduleStartTime` | `scheduledStartTime`（多一个 "d"） |
| 结束时间 | `scheduleEndTime` | `scheduledEndTime`（多一个 "d"） |
| 参会人 | `scheduleAttendees: string[]` | `scheduleAttendees: RoomUser[]`（对象数组） |

读取列表时若沿用创建请求的字段名，会取到 `undefined` → 时间为 0 → 列表为空或状态恒为「已结束」。

### 3. `roomId` 更适合由业务后台生成并保证唯一性
预约会议的 `roomId` 最好由业务后台统一生成或分配，避免未来会议与即时会议在不同入口下发生标识冲突。

### 4. 预约时可同步写入 `scheduleAttendees`
如果业务希望把会议信息同步到参会人的会议列表或提醒入口，应在预约阶段明确传入受邀参会人集合，而不是依赖后续临时补录。

### 5. 预约列表通常需要分页拉取
不要默认一次返回所有预约记录；应根据返回的 `cursor` 持续拉取后续列表数据。

### 6. 预约会议最终仍要回到房间生命周期
无论预约由前端创建还是后端排期系统预生成，临近开会时都应回到 `conference/room-lifecycle` 的真实入会链路。

## 代码生成约束

### 业务决策与代码生成的对应关系

`business_decisions.schedule_features` 的多选结果决定生成代码的范围。`list` 是 **baseline（基础项）**：始终生成、不作为多选项让用户勾选；`modify` / `password` / `events` 是用户多选的额外能力。

| 档位 | 生成的 API 与 UI |
|---|---|
| `list`（baseline，始终生成） | `getScheduledRoomList`（含 cursor 分页）+ 预约列表展示 |
| `modify` | 修改预约时间 / 取消预约的 API + 列表项操作入口 |
| `password` | 预约创建表单的密码字段 + 入会密码校验 |
| `events` | 会议开始提醒 / 被邀请 / 被取消等事件订阅与通知 UI |

`list` 因为是 baseline，始终生成；其余三档中未勾选的，对应 API 不导出、不导入、对应 UI 入口不渲染（按 topic G8 规则）。

### 编译必要条件
- **通用条件**：见 [login-auth 平台 slice](login-auth.md)。
- **额外导入**：至少需要导入 `useRoomState`。
- **运行前提**：当前用户具备预约会议权限，且时间参数经过单位校验。

### 生成规则
#### MUST（生成时必须包含）

1. **在预约创建时显式传入秒级时间戳** — 时间单位错误会直接导致会议时间错位。  
   **Verify**: 检查是否存在 `Math.floor(Date.now() / 1000)` 或等价转换。
2. **在预约场景中明确会议标识与参会人集合** — 未来会议记录应能稳定映射到唯一房间和对应参会人入口。  
   **Verify**: 检查是否提供稳定 `roomId`，并在需要时传入 `scheduleAttendees`。
3. **支持预约列表分页读取** — 长列表场景不能只写死第一页。  
   **Verify**: 检查是否存在 `getScheduledRoomList({ cursor })` 调用。
4. **读取列表必须用响应字段名 `scheduledStartTime` / `scheduledEndTime`（带 "d"）** — 与创建请求的 `scheduleStartTime` / `scheduleEndTime` 拼写不同，用错会取到 0。  
   **Verify**: 检查列表映射代码读取的是 `scheduledStartTime` / `scheduledEndTime`，且 `scheduleAttendees` 按 `RoomUser[]` 取 `.userId`。

#### MUST NOT（生成时绝不能出现）

1. **不要把毫秒时间戳直接传给预约接口** — 服务端为秒级，传毫秒会让会议时间漂移到错误年份。  
   **Verify**: 检查创建时是否 `Math.floor(ms / 1000)` 转秒；不要轻信 `.d.ts` 的「毫秒」注释。
2. **不要把预约成功等价为已经进入会议** — 预约与真实入会是两条不同链路。  
   **Verify**: 检查是否仍通过 `room-lifecycle` 承接正式开会。
3. **不要在读取列表时复用创建请求的字段名 / 类型** — `scheduleStartTime`（无 d）、`scheduleAttendees: string[]` 是创建侧的写法，套到响应上会取空。  
   **Verify**: 检查读取侧未出现 `room.scheduleStartTime` / 把 `scheduleAttendees` 当字符串数组直接用。

### 集成检查点
- 当前 slice 常与 `conference/room-lifecycle`、业务提醒系统联动。
- 集成方式通常是新增日程表单、预约列表和提醒入口。
- 如果业务已有企业日历或排期系统，需要提前约定字段映射与同步策略。

## 验证矩阵
| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已导入 `useRoomState` | 检查 `import` 语句 | 预约相关 API 可解析 |
| 2. 静态规则级 | 时间参数、`roomId` 与参会人集合处理正确 | 搜索 `Date.now()`、`roomId`、`scheduleAttendees` | 传参为秒级时间戳，会议标识稳定 |
| 2.1 字段名级 | 创建用 `scheduleStartTime`、读取用 `scheduledStartTime`（带 "d"）；时间按秒↔毫秒正确转换 | 搜索 `scheduledStartTime` / `scheduledEndTime` 与 `* 1000` / `/ 1000` | 列表能读出真实时间，状态不再恒为「已结束」 |
| 3. 运行时级 | 可创建、读取和取消预约会议 | 在预约页面走完整流程 | 预约列表与取消结果正确 |
| 4. 业务行为级 | 临近会议时可顺畅跳转入会 | 从预约记录点击进入会议 | 进入正式入会链路而非停留在预约状态 |

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 预约列表不完整或更新不及时 | 新建、修改、取消后列表没有同步变化 | 检查预约列表拉取、分页和本地状态刷新逻辑 |
| 提醒出现了但无法入会 | 会议即将开始通知已到，但点击后不能进入会议 | 检查提醒入口是否正确衔接到 `room-lifecycle` 的真实入会流程 |
| 取消后仍能看到旧预约 | 会议已取消，但列表和入口仍保留 | 检查取消后的本地状态清理与列表刷新是否统一收口 |

### 排障流程

```text
发现 预约会议 相关问题
├── 第 1 步：确认问题属于未来会议排期，而不是会议已经开始后的房间主链路
├── 第 2 步：检查预约会议的创建、修改、取消和列表刷新是否共用同一会议身份
├── 第 3 步：确认 starting-soon 提醒是否正确连接到 join-room 的真实入会动作
└── 第 4 步：若仍异常，再回查 room-lifecycle / room-call 的衔接是否正确
```

## 关联知识

- **[conference/room-lifecycle](room-lifecycle.md)** —— 预约会议到点后，真正的入会和退场仍由房间生命周期负责；会议配置（名称、密码、默认规则）也已整合到此 slice。
- **[conference/room-call](room-call.md)** —— 预约会议场景下的提醒或召回，可能与会中呼叫形成协同。