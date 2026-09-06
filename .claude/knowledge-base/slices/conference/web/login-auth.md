---
id: conference/login-auth
name: 登录与鉴权
product: conference
platform: web
tags: [login, auth, sdkappid, usersig, useLoginState]
platforms: [web]
related: [conference/room-lifecycle, conference/device-control, conference/prejoin-check]
api_docs:
  - title: 接入概览
    url: https://cloud.tencent.com/document/product/647/126917
business_decisions:
  - key: usersig_source
    tier: blocking
    question: "您的项目当前处于哪个阶段？这决定鉴权凭证（UserSig）的生成方式。"
    tier: blocking
    question: "您的项目当前处于哪个阶段？这决定鉴权凭证（UserSig）的生成方式。"
    options:
      - { label: "本地开发 —— config 配置 SDKAppID+SecretKey，登录时按 UserID 自动签名（推荐，最快）", value: "local-dev" }
      - { label: "本地开发 / 调试 —— 到控制台生成 UserSig，复制粘贴到登录页（不配置 SecretKey）", value: "console" }
      - { label: "对接生产 —— 由后端接口签发，安全合规（推荐）", value: "backend" }
  - key: userid_strategy
    tier: blocking
    question: "参会用户的身份需要绑定您现有的账号体系吗？"
    tier: blocking
    question: "参会用户的身份需要绑定您现有的账号体系吗？"
    options:
      - { label: "需要，直接使用现有账号的用户 ID —— 最常见，如员工工号、手机号等", value: "direct" }
      - { label: "需要，但不能暴露真实 ID —— 转换为会议专用身份，后台维护映射关系", value: "uuid-mapping" }
      - { label: "不需要，允许无账号匿名入会 —— 生成临时 ID，用完即弃", value: "anonymous" }
      - { label: "需要，直接使用现有账号的用户 ID —— 最常见，如员工工号、手机号等", value: "direct" }
      - { label: "需要，但不能暴露真实 ID —— 转换为会议专用身份，后台维护映射关系", value: "uuid-mapping" }
      - { label: "不需要，允许无账号匿名入会 —— 生成临时 ID，用完即弃", value: "anonymous" }
  - key: on_session_lost
    tier: deferrable
    default: redirect-login
    question: "如果用户登录态失效了（凭证过期，或在别处登录把这台顶下线），页面应如何处理？"
    tier: deferrable
    default: redirect-login
    question: "如果用户登录态失效了（凭证过期，或在别处登录把这台顶下线），页面应如何处理？"
    options:
      - { label: "跳回登录页，让用户重新登录 —— 最稳妥（推荐默认）", value: "redirect-login" }
      - { label: "后台静默换新凭证、自动重连 —— 用户无感，但需后端配合", value: "auto-refresh" }
      - { label: "弹窗提示，由用户决定重连或退出", value: "prompt-user" }
      - { label: "跳回登录页，让用户重新登录 —— 最稳妥（推荐默认）", value: "redirect-login" }
      - { label: "后台静默换新凭证、自动重连 —— 用户无感，但需后端配合", value: "auto-refresh" }
      - { label: "弹窗提示，由用户决定重连或退出", value: "prompt-user" }
---

# 登录与鉴权

## 功能说明

登录与鉴权是 Conference 通用会议所有能力的共同入口，负责把业务身份映射成可被 Room UIKit 使用的登录态。它解决“用户是谁、凭什么入会、资料如何同步”这三个基础问题；创建房间、加入房间、采集设备、会中聊天等后续能力都应建立在稳定登录态之上。

## 核心概念

### 角色与操作

| 角色 | 关键操作 | 说明 |
|------|----------|------|
| 业务后端 | 签发 `UserSig` | 正式环境下由服务端签发登录凭证，不在前端硬编码长期有效凭证 |
| 客户端应用 | 调用 `login` | 使用 `SDKAppID / userId / userSig` 建立会议登录态 |
| 当前用户 | 设置资料 | 通过 `setSelfInfo` 同步昵称、头像等会中展示信息 |
| 后续会议能力 | 消费登录态 | `room-lifecycle`、`device-control`、`prejoin-check` 等能力都依赖已登录状态 |

### 事件流

| 阶段 | 参与方 | 关键动作 |
|------|--------|----------|
| 凭证准备 | 后端 → 客户端 | 后端根据业务身份生成 `userSig` 并下发给客户端 |
| 登录建链 | 客户端 | 客户端调用登录接口，建立 SDK 登录态 |
| 资料同步 | 客户端 | 登录成功后补充昵称、头像等用户展示信息 |
| 能力放行 | 客户端 → 会议能力 | 只有登录完成后，房间、设备、聊天等能力才开始工作 |
| 退出登录 | 客户端 | 登出或切换用户时清理旧会话，避免把旧状态带入下一场会议 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| `sdkAppId` | 当前会议应用的 SDK 应用标识 |
| `userId` | 当前登录用户的唯一身份标识 |
| `userSig` | 用于完成鉴权的动态签名，正式环境应由服务端签发 |
| `selfInfo` | 当前用户昵称、头像等会中展示信息 |
| 登录态 | 表示当前用户是否已可安全执行房间与设备相关操作 |

### 状态机

```text
idle
  → credential-ready
  → logging-in
  → logged-in
  → profile-synced
  → logged-out

logging-in
  → login-failed
  → credential-ready
```

## 前置条件
**通用依赖**：已准备 `SDKAppID / UserID / UserSig`，并确认正式环境的 `UserSig` 由业务后端签发。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`

**前置状态**：
- 已阅读 `conference/login-auth`，明确当前能力的产品边界。
- 若后续需要采集摄像头、麦克风或屏幕，请直接在 `HTTPS` 或 `localhost` 环境联调。

## 最佳实践

### ✅ ALWAYS

1. **由业务后端签发正式环境 `UserSig`** —— 前端只负责消费凭证，不负责生成生产可用签名。
2. **把登录放在应用启动或进入会议主流程之前完成** —— 避免房间创建、设备采集、聊天绑定与登录竞态交错。
3. **登录成功后立即同步用户资料** —— 参会人列表、聊天头像、会控面板都依赖一致的用户展示信息。
4. **在切换账号或退出会议体系时显式清理旧登录态** —— 防止上一位用户的资料和房间上下文泄漏到下一次会话。

### ❌ NEVER

1. **不要在前端硬编码长期有效的生产 `UserSig`** —— 这会破坏鉴权边界，也不利于后续风控和吊销。
2. **不要在未登录完成前直接创建或加入房间** —— 很容易出现入房失败、资料缺失或后续状态无法收口的问题。
3. **不要让多个页面各自重复触发登录** —— 登录应尽量收敛到统一入口，避免并发登录与状态覆盖。

## 代码示例
### 基础接入：启动时完成登录并写入用户资料

```ts
import { onMounted } from 'vue';
import { useLoginState } from 'tuikit-atomicx-vue3/room';

const { login, setSelfInfo } = useLoginState();

onMounted(async () => {
  await login({
    sdkAppId: 1400000000,
    userId: 'user_001',
    userSig: 'YOUR_USERSIG',
    scene: 5001,
  });
  await setSelfInfo({ userName: 'Alice', avatarUrl: '' });
});
```

### 事件处理：登录过期与被强制下线后收口登录态

```ts
import { LoginEvent, useLoginState } from 'tuikit-atomicx-vue3';

const { subscribeEvent } = useLoginState();

subscribeEvent(LoginEvent.onLoginExpired, () => {
  console.log('登录已过期，请重新登录');
  // 跳转到登录页面或刷新 userSig
});

subscribeEvent(LoginEvent.onKickedOffline, () => {
  console.log('账号在其他设备登录，已被强制下线');
  // 提示用户重新登录
});
```

## 调用时序
```
应用启动
   │
   ▼
准备 SDKAppID / UserID / UserSig
   │
   ▼
初始化全局上下文提供者
   │
   ▼
调用 login(...)
   │
   ├─ 失败 → 提示鉴权或签名错误，停止后续房间 / 设备初始化
   │
   └─ 成功
       │
       ▼
调用 setSelfInfo(...)
       │
       ▼
订阅 LoginEvent.onLoginExpired / LoginEvent.onKickedOffline
       │
       ├─ 触发过期事件 → 跳转登录页或刷新 userSig 后重新登录
       │
       ├─ 触发被踢下线事件 → 提示账号异地登录并收口当前登录态
       │
       ▼
再进入 room-lifecycle / device-control / room-chat 等后续能力
```

## 平台特有注意事项
### 1. `userSig` 只能由业务后端在正式环境签发
开发联调时可以临时生成 `userSig`，但线上不能把签名逻辑放在前端，否则会直接破坏账号安全边界。

### 2. 登录应早于房间与设备能力初始化
`room-lifecycle`、`device-control`、`room-chat` 等能力都依赖稳定登录态；未登录就先调房间或聊天接口，通常会导致调用失败或状态异常。

### 3. 需要显式处理登录过期与被强制下线事件
当登录凭证过期时，会触发 `LoginEvent.onLoginExpired`；收到此事件后应立即跳转登录页，或先刷新 `userSig` 再重新执行登录流程，不能只在控制台打印日志。

当账号在其他设备登录导致当前设备被强制下线时，会触发 `LoginEvent.onKickedOffline`；收到此事件后应立即提示用户当前登录态已失效，并引导重新登录，避免页面继续停留在失效会中状态。

### 4. Web 端媒体能力依赖安全上下文
如果页面后续需要摄像头、麦克风、屏幕共享或本地特效，部署环境必须满足 `HTTPS`、`localhost` 或浏览器认可的其他安全上下文条件。

## 代码生成约束
### 编译必要条件
- **通用条件**：当前 slice 是 Web 会议所有后续能力的统一登录入口。
- **额外导入**：至少需要从 `tuikit-atomicx-vue3/room` 导入 `useLoginState`；若需订阅登录事件，还应从 `tuikit-atomicx-vue3` 导入 `LoginEvent`。
- **运行前提**：页面必须能拿到有效的 `SDKAppID / UserID / UserSig`；若要承接 UI Kit 组件，还需在根节点挂载全局上下文。

### 生成规则
#### MUST（生成时必须包含）

1. **先完成 `login()`，再初始化其他会议能力** — 否则后续 room / device / chat 调用缺少基础登录态。  
   **Verify**: 检查代码中是否存在 `await login(`，且后续房间或设备逻辑位于其后。
2. **登录参数必须包含 `scene: 5001`** — 用于标识由 skill 生成的场景接入来源，所有 useLoginState().login 生成代码都必须带上该参数。  
   **Verify**: 检查 `login(` 参数对象中是否包含 `scene: 5001`。
3. **把用户资料写入 `setSelfInfo()` 或等价链路** — 否则远端成员列表与会中 UI 可能只显示默认 ID。  
   **Verify**: 检查是否存在 `setSelfInfo(` 或明确的资料同步逻辑。
4. **订阅登录过期与被强制下线事件并收口恢复逻辑** — 登录成功后仍要处理 `LoginEvent.onLoginExpired` 与 `LoginEvent.onKickedOffline`，避免后续房间与聊天状态静默失效。  
   **Verify**: 检查是否存在 `subscribeEvent(LoginEvent.onLoginExpired, ...)`、`subscribeEvent(LoginEvent.onKickedOffline, ...)` 或等价恢复逻辑。

#### MUST NOT（生成时绝不能出现）

1. **不要把正式环境 `UserSig` 生成逻辑写在前端** — 会直接泄露签名能力。  
   **Verify**: 搜索是否存在前端本地生成正式 `UserSig` 的实现。
2. **不要在未登录态下直接调用房间、聊天或设备接口** — 会造成初始化顺序错误。  
   **Verify**: 检查房间 / 设备 / 聊天逻辑是否依赖已完成登录的状态。
3. **不要在收到登录过期或被强制下线事件后只打印日志、不做恢复处理** — 这会让后续能力停留在失效登录态。  
   **Verify**: 检查 `onLoginExpired` 与 `onKickedOffline` 处理逻辑是否真正跳转登录页、刷新 `userSig` 或提示用户重新登录。

### 集成检查点
- 当前 slice 是 `conference/web` 目录下其他所有能力 slice 的公共前置条件。
- 集成方式通常是新增启动逻辑或根级状态管理，不应修改 SDK 内部实现。
- 若业务项目已有独立账号体系，应把用户登录与 TRTC/IM 登录桥接清楚，而不是直接复用匿名测试账号。

## 验证矩阵
| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已正确导入 `useLoginState`、`LoginEvent` 与登录事件相关依赖 | 检查 `import` 语句 | 可解析登录 Hook 与 `LoginEvent` |
| 2. 静态规则级 | 登录先于其他会议能力初始化，登录参数包含 `scene: 5001`，且已监听过期与被踢下线事件 | 搜索 `await login(`、`scene: 5001`、`setSelfInfo(`、`subscribeEvent(LoginEvent.onLoginExpired`、`subscribeEvent(LoginEvent.onKickedOffline` | 先登录、写入资料，并具备完整的登录态恢复入口 |
| 3. 运行时级 | 登录成功后可继续设置资料，并能响应过期或被强制下线事件 | 触发启动流程并观察日志或调试状态 | 登录成功且用户资料更新完成；过期时进入重登或刷新票据流程；被踢下线时提示重新登录 |
| 4. 业务行为级 | 后续会议能力可正常承接 | 完成登录后继续进入会议页面，并模拟异地登录顶替场景 | 房间、设备、聊天入口不再因未登录失败；登录过期或被强制下线后都能被及时收口 |

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 登录失败 | 调用登录后报错，后续房间与设备能力都无法使用 | 检查 `sdkAppId`、`userId`、`userSig` 是否匹配，确认 `UserSig` 未过期且由正确环境签发 |
| 用户资料未同步 | 已登录，但参会人列表或聊天区域昵称、头像不对 | 确认登录成功后已调用资料同步接口，并检查是否被旧本地缓存覆盖 |
| 后续能力报未鉴权 | 创建房间、设备采集或聊天初始化时报未登录 | 检查业务流程是否在登录完成前提前触发了 `room-lifecycle` 或 `device-control` |

### 排障流程

```text
发现 登录与鉴权 相关问题
├── 第 1 步：确认当前使用的 sdkAppId / userId / userSig 是否同属一个环境
├── 第 2 步：检查 userSig 是否过期、是否由后端按当前 userId 重新签发
├── 第 3 步：确认登录成功后是否立即同步了昵称、头像等 selfInfo
└── 第 4 步：若房间或设备能力仍异常，再回查 room-lifecycle / device-control 是否在登录前被提前触发
```

## 关联知识

- **[conference/room-lifecycle](room-lifecycle.md)** —— 登录完成后，真正承接创建房间、加入房间、离房和结束会议。
- **[conference/device-control](device-control.md)** —— 摄像头、麦克风等本地设备能力依赖稳定登录态。
- **[conference/prejoin-check](prejoin-check.md)** —— 会前检测通常在登录完成后进入，确保设备信息可被统一管理。