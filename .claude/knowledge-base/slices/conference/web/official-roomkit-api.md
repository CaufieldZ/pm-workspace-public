---
id: conference/official-roomkit-api
platform: web
api_docs:
  - title: 快速接入 Web&H5 (Vue3)
    url: https://cloud.tencent.com/document/product/647/81962
  - title: 快速接入 Web (React)
    url: https://cloud.tencent.com/document/product/647/132839
  - title: 界面微调 (Web)
    url: https://cloud.tencent.com/document/product/647/129842
---

# 官方 RoomKit 适配层 API — Web 实现

> 本 slice 覆盖官方 RoomKit Web 包导出的 `conference` 对象 API。
> Vue3 项目使用 `@tencentcloud/roomkit-web-vue3`，React 项目使用
> `@tencentcloud/roomkit-web-react`。两者的 `conference` API 调用时序保持一致。
> 当 `ui_mode = official-roomkit` 时，业务侧通过此对象操作会议，
> 而不是直接调用 no-UI hooks/composables（no-UI 层见 `conference/web/room-lifecycle.md` 等）。
>
> Vue3 签名基于 `@tencentcloud/roomkit-web-vue3@5.9.0` 源码验证；React
> 签名基于官方 React 快速接入文档与同名导出校验。

## 前置条件

**安装依赖（按项目框架二选一，不要混装）**：

Vue3：
```bash
npm install @tencentcloud/roomkit-web-vue3@5 tuikit-atomicx-vue3 \
  @tencentcloud/uikit-base-component-vue3 @tencentcloud/universal-api
```

React：
```bash
npm install @tencentcloud/roomkit-web-react tuikit-atomicx-react \
  @tencentcloud/uikit-base-component-react @tencentcloud/universal-api
```

**版本要求**：
- Vue3：lockfile 中 `@tencentcloud/roomkit-web-vue3` 解析版本必须 `>=5.4.3`。
- React：使用 `@tencentcloud/roomkit-web-react` 与同版本族的 `tuikit-atomicx-react`。

**导入来源（Vue3）**：
```ts
// 会议组件 + conference API + 事件/枚举
import {
  ConferenceMainView,
  ConferenceMainViewH5,
  conference,
  RoomEvent,
  BuiltinWidget,
  InterceptorAction,
} from '@tencentcloud/roomkit-web-vue3'

// UIKitProvider（包裹组件用）
import { UIKitProvider } from '@tencentcloud/uikit-base-component-vue3'
```

**导入来源（React）**：
```tsx
// 会议组件 + conference API + 事件/枚举
import {
  ConferenceMainView,
  conference,
  RoomEvent,
  BuiltinWidget,
  InterceptorAction,
} from '@tencentcloud/roomkit-web-react'

// UIKitProvider（包裹组件用）
import { UIKitProvider } from '@tencentcloud/uikit-base-component-react'
```

## 枚举定义

```ts
enum RoomEvent {
  ROOM_LEAVE = 'RoomLeave',
  ROOM_DISMISS = 'RoomDismiss',
  ROOM_ERROR = 'RoomError',
  KICKED_OUT = 'KickedOut',
  KICKED_OFFLINE = 'KickedOffline',
  USER_SIG_EXPIRED = 'UserSigExpired',
}

enum BuiltinWidget {
  MicWidget = 'MicWidget',
  CameraWidget = 'CameraWidget',
  ScreenShareWidget = 'ScreenShareWidget',
  RoomChatWidget = 'RoomChatWidget',
  MemberWidget = 'MemberWidget',
  InviteWidget = 'InviteWidget',
  VirtualBackgroundWidget = 'VirtualBackgroundWidget',
  BasicBeautyWidget = 'BasicBeautyWidget',
  AIToolsWidget = 'AIToolsWidget',
  SettingsWidget = 'SettingsWidget',
  ThemeWidget = 'ThemeWidget',
  LayoutWidget = 'LayoutWidget',
  LocalNetworkInfoWidget = 'LocalNetworkInfoWidget',
  LanguageWidget = 'LanguageWidget',
  LoginUserInfoWidget = 'LoginUserInfoWidget',
  CurrentRoomInfoWidget = 'CurrentRoomInfoWidget',
  LeaveRoomWidget = 'LeaveRoomWidget',
  SwitchCameraWidget = 'SwitchCameraWidget',
  BarrageWidget = 'BarrageWidget',
  RaiseHandsWidget = 'RaiseHandsWidget',
  RaiseHandsListWidget = 'RaiseHandsListWidget',
}

enum InterceptorAction {
  OpenMicrophone = 'openMicrophone',
  CloseMicrophone = 'closeMicrophone',
  OpenCamera = 'openCamera',
  CloseCamera = 'closeCamera',
  StartScreenShare = 'startScreenShare',
  StopScreenShare = 'stopScreenShare',
}
```

## API 签名

### 登录与用户信息

```ts
conference.login({ sdkAppId: number, userId: string, userSig: string }): Promise<void>
conference.setSelfInfo({ userName: string, avatarUrl: string }): Promise<void>
conference.logout(): Promise<void>
```

### 房间生命周期

```ts
// 创建并加入房间
conference.createAndJoinRoom({
  roomId: string,
  roomType?: RoomType,
  options?: CreateRoomOptions,
}): Promise<void>

interface CreateRoomOptions {
  roomName?: string;
  password?: string;
  isAllMicrophoneDisabled?: boolean;
  isAllCameraDisabled?: boolean;
  isAllScreenShareDisabled?: boolean;
  isAllMessageDisabled?: boolean;
}

// 加入已有房间
conference.joinRoom({
  roomId: string,
  roomType?: RoomType,
  password?: string,
}): Promise<void>

// 离开（普通成员）
conference.leaveRoom(): Promise<void>

// 结束（主持人）
conference.endRoom(): Promise<void>
```

### 事件

```ts
conference.on(eventType: RoomEvent, callback: (data?: any) => void): void
conference.off(eventType: RoomEvent, callback: (data?: any) => void): void
```

### 界面微调

```ts
// 隐藏/显示内置按钮
conference.setWidgetVisible(config: Partial<Record<BuiltinWidget, boolean>>): void

// 注册自定义按钮（返回注销函数）
conference.registerWidget(config: WidgetConfig): () => void

// 拦截内置操作（返回注销函数）
conference.onWill(action: InterceptorAction, handler: InterceptorHandler): () => void

type InterceptorHandler = (
  action: InterceptorAction,
  proceed: () => void,
  abort: () => void,
) => void | Promise<void>
```

### 特性配置

```ts
conference.setFeatureConfig(config: Partial<FeatureConfig>): void

interface FeatureConfig {
  watermark?: WatermarkConfig;
  shareLink?: string;              // 纯字符串 URL
  contactList?: ContactListProvider;
  virtualBackground?: VirtualBackgroundFeatureConfig;
  aiTools?: AIToolsConfig;
  layoutTemplate?: RoomLayoutTemplate;
  toolbar?: ToolbarConfig;
}
```

## 调用时序

```
1. conference.login()
2. conference.setSelfInfo()
3. conference.setWidgetVisible()      ← login 之后、进房之前
   conference.registerWidget()        ← 同上
   conference.onWill()                ← 同上
4. conference.createAndJoinRoom() 或 conference.joinRoom()
5. conference.setFeatureConfig()      ← 进房成功后（shareLink 依赖最终 roomId）
   ...会中...
6. conference.leaveRoom() 或 conference.endRoom()
7. RoomEvent.ROOM_LEAVE / ROOM_DISMISS 回调 → 清理注销函数
```

## 完整代码示例（Vue3）

```vue
<template>
  <UIKitProvider theme="light" language="zh-CN">
    <ConferenceMainView v-if="isPC" />
    <ConferenceMainViewH5 v-else />
  </UIKitProvider>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ConferenceMainView,
  ConferenceMainViewH5,
  conference,
  RoomEvent,
  BuiltinWidget,
} from '@tencentcloud/roomkit-web-vue3'
import { UIKitProvider } from '@tencentcloud/uikit-base-component-vue3'

const route = useRoute()
const router = useRouter()
const isPC = ref(window.innerWidth > 768)
function onResize() { isPC.value = window.innerWidth > 768 }

const cleanupFns: Array<() => void> = []

onMounted(async () => {
  window.addEventListener('resize', onResize)

  const sdkAppId = Number(route.query.sdkAppId)
  const userId = route.query.userId as string
  const userSig = route.query.userSig as string
  const roomId = route.query.roomId as string

  if (!sdkAppId || !userId || !userSig || !roomId) {
    router.replace('/')
    return
  }

  // 1. 登录
  await conference.login({ sdkAppId, userId, userSig })
  await conference.setSelfInfo({ userName: userId, avatarUrl: '' })

  // 2. 界面微调（login 之后、进房之前）
  conference.setWidgetVisible({
    [BuiltinWidget.InviteWidget]: false,
  })

  // 3. 监听离房
  conference.on(RoomEvent.ROOM_LEAVE, handleLeave)
  conference.on(RoomEvent.ROOM_DISMISS, handleLeave)

  // 4. 创建并加入
  await conference.createAndJoinRoom({
    roomId,
    options: { roomName: `会议-${roomId}` },
  })

  // 5. 进房后设置分享链接
  conference.setFeatureConfig({
    shareLink: `${window.location.origin}/meeting?roomId=${roomId}`,
  })
})

function handleLeave() {
  conference.off(RoomEvent.ROOM_LEAVE, handleLeave)
  conference.off(RoomEvent.ROOM_DISMISS, handleLeave)
  cleanupFns.forEach(fn => fn())
  router.replace('/')
}

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  handleLeave()
})
</script>
```

## 完整代码示例（React）

```tsx
import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ConferenceMainView,
  conference,
  RoomEvent,
  BuiltinWidget,
} from '@tencentcloud/roomkit-web-react'
import { UIKitProvider } from '@tencentcloud/uikit-base-component-react'

export function MeetingRoom() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const sdkAppId = Number(searchParams.get('sdkAppId'))
    const userId = searchParams.get('userId') || ''
    const userSig = searchParams.get('userSig') || ''
    const roomId = searchParams.get('roomId') || ''
    const cleanupFns: Array<() => void> = []

    const cleanupRoomListeners = () => {
      conference.off(RoomEvent.ROOM_LEAVE, handleLeave)
      conference.off(RoomEvent.ROOM_DISMISS, handleLeave)
      cleanupFns.forEach((fn) => fn())
    }

    const handleLeave = () => {
      cleanupRoomListeners()
      navigate('/')
    }

    const start = async () => {
      if (!sdkAppId || !userId || !userSig || !roomId) {
        navigate('/')
        return
      }

      await conference.login({ sdkAppId, userId, userSig })
      await conference.setSelfInfo({ userName: userId, avatarUrl: '' })

      conference.setWidgetVisible({
        [BuiltinWidget.InviteWidget]: false,
      })

      conference.on(RoomEvent.ROOM_LEAVE, handleLeave)
      conference.on(RoomEvent.ROOM_DISMISS, handleLeave)

      await conference.createAndJoinRoom({
        roomId,
        options: { roomName: `会议-${roomId}` },
      })

      conference.setFeatureConfig({
        shareLink: `${window.location.origin}/meeting?roomId=${roomId}`,
      })
    }

    start().catch(() => navigate('/'))

    return () => {
      cleanupRoomListeners()
    }
  }, [navigate, searchParams])

  return (
    <UIKitProvider theme="light" language="zh-CN">
      <ConferenceMainView />
    </UIKitProvider>
  )
}
```

## 代码生成约束

### MUST

1. **使用 UIKitProvider 包裹会议组件** — `ConferenceMainView` / `ConferenceMainViewH5` 必须放在 `UIKitProvider` 内。
   - Vue3：`@tencentcloud/uikit-base-component-vue3`
   - React：`@tencentcloud/uikit-base-component-react`
2. **界面微调 API 在 login 之后、进房之前注册** — 避免按钮闪烁或拦截器遗漏。
3. **registerWidget / onWill 返回的注销函数必须收集并在 ROOM_LEAVE + ROOM_DISMISS 时清理** — 防止重复注册。
4. **shareLink 在进房成功后设置** — 依赖最终确定的 roomId。
5. **按项目框架选择包名** — React 项目必须使用 `@tencentcloud/roomkit-web-react` / `tuikit-atomicx-react`，Vue3 项目必须使用 `@tencentcloud/roomkit-web-vue3` / `tuikit-atomicx-vue3`。

### MUST NOT

1. **不要用不存在的枚举值** — `BuiltinWidget.InviteControl` 不存在，正确是 `BuiltinWidget.InviteWidget`。
2. **不要给 createAndJoinRoom 传顶层 roomName / isOpenCamera / isSeatEnabled** — `roomName` 在 `options` 内，其余不存在。
3. **不要给 joinRoom 传 isOpenCamera / isOpenMicrophone** — 只接受 `roomId`、`roomType`、`password`。
4. **不要把 shareLink 写成对象** — `setFeatureConfig({ shareLink: '...' })` 是纯字符串。
5. **不要用 CSS/DOM hack 修改 RoomKit 内部 UI** — 必须用 `setWidgetVisible` / `registerWidget` / `onWill`。
6. **不要在 React 项目中生成 Vue SFC 或 Vue 包导入**；也不要在 Vue3 项目中生成 React JSX / TSX。

## 常见错误速查

| 错误写法 | 正确写法 | 原因 |
|---------|---------|------|
| `BuiltinWidget.InviteControl` | `BuiltinWidget.InviteWidget` | 枚举值不存在 |
| `createAndJoinRoom({ roomId, roomName })` | `createAndJoinRoom({ roomId, options: { roomName } })` | roomName 在 options 内 |
| `joinRoom({ roomId, isOpenCamera: true })` | `joinRoom({ roomId })` | 无 isOpenCamera 参数 |
| `setFeatureConfig({ shareLink: { link, title } })` | `setFeatureConfig({ shareLink: 'url' })` | shareLink 是字符串 |
| `import { UIKitProvider } from '@tencentcloud/roomkit-web-vue3'` | `import { UIKitProvider } from '@tencentcloud/uikit-base-component-vue3'` | UIKitProvider 在 peer 包中 |
| React 项目 `import { ConferenceMainView } from '@tencentcloud/roomkit-web-vue3'` | `import { ConferenceMainView } from '@tencentcloud/roomkit-web-react'` | React 与 Vue3 包名不同 |
| React 项目 `import { useRoomState } from 'tuikit-atomicx-vue3/room'` | `import { useRoomState } from 'tuikit-atomicx-react/room'` | React no-UI hooks 使用 React 包 |
