---
id: conference/screen-share
name: 屏幕分享
product: conference
platform: web
tags: [screen-share, share, screenAudio, participantWithScreen]
platforms: [web]
related: [conference/video-layout, conference/device-control, conference/participant-management]
api_docs:
  - title: 屏幕分享
    url: https://cloud.tencent.com/document/product/647/126925
---

# 屏幕分享

## 功能说明

屏幕分享负责会议中的共享链路，覆盖开始共享、停止共享、是否携带系统音频、谁正在共享，以及共享状态如何驱动画面编排和权限限制。它关注的是共享媒体能力本身，也要处理“当前为什么不能共享、共享被谁中断、共享受限后如何恢复”这些问题，而不是共享后画面如何排布或谁具备角色治理权限。

## 核心概念

### 角色与操作

| 角色 | 关键操作 | 说明 |
|------|----------|------|
| 共享发起人 | 开始 / 停止屏幕共享 | 选择共享窗口、标签页或整个屏幕，并在支持时携带系统音频 |
| 观看方 | 感知共享状态 | 根据共享者变化切换主画面或观看内容 |
| 会控模块 | 约束或恢复共享能力 | 可限制成员发起共享，也可通过设备协作帮助成员恢复共享能力 |
| 浏览器 | 提供原生共享能力 | 控制共享弹窗、系统音频可用性和原生停止事件 |
| 布局模块 | 消费共享结果 | 根据共享开始、结束或中断结果切换主画面和展示模式 |

### 事件流

| 阶段 | 参与方 | 关键动作 |
|------|--------|----------|
| 发起共享 | 共享发起人 / 浏览器 | 用户触发共享，浏览器弹出原生选择窗口 |
| 共享建立 | 客户端 | 共享成功后记录当前共享状态和共享者信息 |
| 权限受限或协作恢复 | 会控模块 / 成员 | 当共享被限制时，限制入口、展示原因，并在需要时进入申请或邀请链路 |
| 共享结束 | 浏览器 / 管理者 / 发起人 | 原生停止、管理员关闭共享或用户主动停止后，客户端同步收口 |
| 布局回退 | 布局模块 | 根据共享结束结果回退主画面和展示模式 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| 共享状态 | 表示当前是否处于共享中、停止中或空闲态 |
| `participantWithScreen` | 当前正在共享屏幕的成员信息 |
| 系统音频选项 | 表示当前共享是否尝试携带系统音频 |
| 浏览器支持能力 | 决定共享范围和系统音频能力是否可用 |
| 共享权限状态 | 表示当前成员是否被允许发起共享 |
| 共享协作状态 | 表示共享是否因会控受限、是否需要申请开启或等待邀请响应 |

### 状态机

```text
idle
  → requesting-share
  → sharing
  → externally-stopped
  → idle

requesting-share
  → restricted
  → denied
  → failed
  → idle
```

## 前置条件
**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`

**前置状态**：
- 已阅读 `conference/screen-share`，明确当前能力的产品边界。
- 已完成 `conference/login-auth`，确保当前页面具备稳定登录态。
- 已根据业务流程接入会议上下文；需要房间状态时，优先通过 `conference/room-lifecycle` 统一承接。
- 当前能力涉及媒体采集、渲染或浏览器权限时，请在 `HTTPS` 或 `localhost` 安全上下文下调试。

## 最佳实践

### ✅ ALWAYS

1. **把浏览器原生停止和管理员关闭共享都当作主流程事件处理** —— 用户不一定通过你的按钮结束共享。
2. **让共享状态与布局编排显式联动** —— 谁在共享、共享何时开始和结束，应该直接驱动画面焦点切换。
3. **把共享受限原因讲清楚** —— 当共享被会控限制、被管理员关闭或需要申请开启时，应给出明确原因和后续动作入口。
4. **把共享权限与房间会控统一设计** —— 当共享能力受限时，不仅要限制入口，还要限制真实共享流程，并在需要时进入申请 / 邀请链路。
5. **针对浏览器差异给出清晰提示** —— 系统音频、共享范围和权限提示在不同环境下会有差异。

### ❌ NEVER

1. **不要把屏幕共享当成普通按钮开关** —— 它受到浏览器原生交互、权限弹窗、会控限制和外部中断事件影响。
2. **不要忽略共享结束后的布局回退** —— 否则主画面会停留在已经不存在的共享状态。
3. **不要把共享失败一律归因到浏览器支持性问题** —— 还要排查是否被当前会控限制、被管理员关闭，或是否需要先申请开启共享。
4. **不要默认系统音频在所有环境都可用** —— 需要根据当前环境能力做提示和降级。

## 代码示例
### 基础接入：开始共享、监听共享者并在结束时收口

```ts
import { watch } from 'vue';
import { useDeviceState, useRoomParticipantState } from 'tuikit-atomicx-vue3/room';

const { startScreenShare, stopScreenShare, screenStatus } = useDeviceState();
const { participantWithScreen } = useRoomParticipantState();

await startScreenShare({ screenAudio: true });
watch(participantWithScreen, (participant) => {
  console.log('当前共享者:', participant?.userId);
});
await stopScreenShare();
```

## 调用时序
```
完成 login-auth 并进入会议
   │
   ▼
调用 startScreenShare({ screenAudio })
   │
   ├─ 浏览器弹出原生共享选择器
   ├─ 用户确认 → 本地开始共享，participantWithScreen 更新
   ├─ 用户取消 → 保持未共享状态
   └─ 浏览器原生停止 → screenStatus / participantWithScreen 变化收口 UI
   │
   ▼
需要结束共享时调用 stopScreenShare()
```

## 平台特有注意事项
### 1. 系统音频共享受浏览器差异影响明显
`screenAudio` 在 Chrome / Edge 上通常体验更完整，Firefox / Safari 的能力与限制差异更大，联调时要分浏览器验证。

### 2. 必须处理浏览器原生“停止分享”
用户点击浏览器原生停止按钮后，前端不能只依赖业务按钮状态，必须通过共享状态变化主动收口 UI。

### 3. 屏幕分享主要面向桌面浏览器
移动端 Web 对屏幕共享的支持极其有限，产品设计和文档说明都应以桌面场景为主。

### 4. 本地共享 tile 不展示真实预览时，不要让它停留在纯黑屏
部分 Web 环境或产品方案里，本地共享流不会展示真实预览，或者业务上本来就不希望在本地重复渲染共享内容。此时推荐改成“您正在共享屏幕”一类的示意态，并按需提供“结束共享”操作。

这里的图标、文案、按钮布局都只是**示例**，不应被理解为固定 UI 规范；真正需要固定的是：用户一眼能知道自己正在共享，且不会看到无语义的黑底。

如需具体承载方式，优先交给 `conference/web/video-layout` 中的 `participantViewUI` 或页面级 overlay 处理。

## 代码生成约束
### 编译必要条件
- **通用条件**：见 [login-auth 平台 slice](login-auth.md)。
- **额外导入**：至少需要导入 `useDeviceState` 与 `useRoomParticipantState`。
- **运行前提**：浏览器支持屏幕采集，并处于安全上下文。

### 生成规则
#### MUST（生成时必须包含）

1. **通过 `startScreenShare()` / `stopScreenShare()` 控制共享主链路** — 可保证共享状态与房间状态一致。  
   **Verify**: 检查是否存在 `startScreenShare(` 与 `stopScreenShare(`。
2. **根据 `participantWithScreen` 或 `screenStatus` 驱动 UI** — 共享者变化必须能被页面感知。  
   **Verify**: 检查是否读取 `participantWithScreen` 或 `screenStatus`。
3. **如果本地共享流不展示真实预览或表现为黑底，必须补共享中的提示态** —— 可以是状态文案、图标、结束共享入口或它们的组合，但不能只有无语义黑屏。  
   **Verify**: 检查本地共享中的 UI 是否至少向用户表达“正在共享”这一状态。

#### MUST NOT（生成时绝不能出现）

1. **不要假设所有浏览器都等价支持系统音频共享** — 会造成错误的产品承诺。  
   **Verify**: 检查是否有浏览器差异说明或降级策略。
2. **不要忽略浏览器原生停止共享后的状态变化** — UI 会残留“仍在共享”的假状态。  
   **Verify**: 检查是否有基于状态变化的收口逻辑。
3. **不要把共享中的示意态写死成唯一视觉规范** —— 示例可以参考设计稿，但实现必须允许按业务风格调整。  
   **Verify**: 检查说明文字是否把示例样式当作唯一合法 UI。

### 集成检查点
- 当前 slice 常与 `conference/video-layout`、`conference/participant-management` 联动。
- 集成方式通常是新增共享按钮、共享状态提示和主画面切换逻辑。
- 如果业务需要限制谁能共享，应在上层与角色治理或会控规则联合判断。

## 验证矩阵
| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已导入共享相关 Hook | 检查 `import` 语句 | 屏幕共享 API 可解析 |
| 2. 静态规则级 | 共享开始、停止和状态监听都存在 | 搜索 `startScreenShare` / `stopScreenShare` / `participantWithScreen` | 形成完整共享链路 |
| 3. 运行时级 | 浏览器确认后可开始共享 | 在桌面浏览器执行共享 | 页面出现共享状态 |
| 4. 业务行为级 | 原生停止共享后 UI 正确收口 | 点击浏览器原生停止按钮 | 共享按钮与主画面状态恢复正常 |

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 点击共享没有成功开始 | 浏览器无弹窗，或弹窗后没有进入共享状态 | 检查浏览器共享权限、当前环境支持能力，以及共享入口是否被会控限制 |
| 浏览器已停止共享但 UI 仍显示共享中 | 用户通过浏览器原生面板停止后，页面状态未收口 | 检查是否监听并处理了原生停止共享事件 |
| 共享被中断但原因不清楚 | 共享突然结束，用户不知道是自己停了还是被管理者关闭 | 检查是否对管理员关闭共享和浏览器原生停止做了区分提示 |
| 共享开始了但主画面没切换 | 共享画面存在，但布局仍停留在普通成员视图 | 检查共享状态是否真正驱动了 `video-layout` 的焦点切换逻辑 |

### 排障流程

```text
发现 屏幕分享 相关问题
├── 第 1 步：确认问题属于共享媒体能力，而不是布局编排或角色治理本身
├── 第 2 步：检查浏览器共享弹窗、权限和系统音频支持是否符合当前环境
├── 第 3 步：确认当前是否存在禁共享、共享被关闭或申请 / 邀请中的会中限制
└── 第 4 步：若仍异常，再回查 video-layout / device-control / participant-management 的衔接是否正确
```

## 关联知识

- **[conference/video-layout](video-layout.md)** —— 屏幕共享会直接驱动主画面切换与布局重编排。
- **[conference/device-control](device-control.md)** —— 本地媒体控制与共享状态共同构成会中媒体体验。
- **[conference/participant-management](participant-management.md)** —— 禁共享、共享关闭和申请 / 邀请链路会直接约束当前能力；同时谁能发起共享相关协作也由成员角色边界决定。
