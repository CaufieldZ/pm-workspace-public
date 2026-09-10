---
id: chat/login-auth
name: SDK 登录鉴权
product: chat
platform: web
description: SDK 登录鉴权（tuikit-atomicx-vue3 useLoginStore 单例 composable）+ UserSig 来源；路径 A 同时覆盖默认登录页
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: [LoginStore]
trigger-keywords: [登录, login, 鉴权, userSig, 初始化, init, sdkAppID, kickedOffline, 被踢下线, logout, 登出, 登录页, login page]
prerequisites: []
tags: ['LoginStore']
---

## 1. 这个 slice 处理什么

路径 A 基础功能之（登录鉴权）。在 `src/im/login.ts`（或项目等价位置）封装 `useLoginStore` 的 `login` / `logout` / `loginStatus` / 被踢下线，给上层 UI 和后续 slice 提供：

- `loginIM({ userID, userSig })` —— 上层登录页调用入口
- `logoutIM()` —— 登出入口
- `useLoginGuard()` —— 路由守卫用的 `loginStatus` ComputedRef 透传
- `setupKickedOfflineHandler()` —— 被踢下线事件订阅

**额外覆盖**：路径 A（0→1 项目）需同时生成最小登录页 `src/views/Login.vue`，见 § 8。

**不在本 slice 处理**：UserSig 后端接口实现；路径 B 的登录页改造（用户主动要求才做）。

## 2. AI 思考清单（写代码前必须想清楚）

- **chatMode = full / direct？**（A.1 用户已选）→ full 含登录页；direct 仅 composable（静默自动登录，无独立登录页）
- `kickedOffline` 提示用什么 UI？优先用 Toast / Dialog；无 UI 库时降级原生 `alert()`（标注 TODO）
- **Direct Chat 额外**：登录失败时就地显示"连接失败 + 返回按钮"（不跳登录页）；被踢下线跳回来源页面（`router.back()`）

## 3. SDK API 必读（绝对真理）

```ts
import { useLoginStore } from 'tuikit-atomicx-vue3/chat'
const {
  loginStatus,    // ComputedRef<'unlogin' | 'logined'>
  loginUserInfo,  // ComputedRef<UserProfile | null>
  login,          // (params: LoginParams) => Promise<void>
  logout,         // () => Promise<void>
  setSelfInfo,    // (profile: Partial<UserProfile>) => Promise<void>
  getChat,        // () => ChatSDK（兜底原生实例）
  onEvent,        // (listener: (e: LoginEvent) => void) => Unsubscribe
} = useLoginStore()
```

`LoginParams` 关键字段（完整见 `_shared/store-types.md`）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `sdkAppID` | `number` | 是 | 腾讯云控制台拿 |
| `userID` | `string` | 是 | 业务侧用户 ID |
| `userSig` | `string` | 是 | 鉴权后端签发 |
| `scene` | `string` | 否 | 默认 `'5000'`，必须传入 |
| `proxyServer` / `fileUploadProxy` / `fileDownloadProxy` | `string` | 否 | 私有化部署专用 |

`LoginEvent`（目前 1 种，监听用 `switch` 预留扩展）：

```ts
type LoginEvent = { type: 'kickedOffline' }
```

## 4. Hard rules（AI 必须遵守）

> ❗ 所有 SDK 异步调用必须遵循 `references/06-a-defensive-coding.md` 防御编程规范（try/catch/finally、formatError、错误反馈形式、状态锁）。本节规则是该规范的专属补充，不替代它。
> ❗ 写 UI 代码前必须先 `read_file _base/style-guide.md`，按其规范生成样式，不准跳过。

### 4.1 实例化

- ❗ 统一使用 `useLoginStore()`，是**单例 composable**，任意位置调用同一实例
  - ❌ `useLoginStore.create(...)` / `LoginStore.create(...)` — 那是多实例 store 的 API
  - ❌ `import { LoginStore } from 'tuikit-atomicx-vue3/chat'`（`LoginStore` 不是 hook，应用 `useLoginStore`）
  - ❌ `onScopeDispose(() => store.destroy())` — 单例由 SDK 管理，不准手动销毁

### 4.2 调用顺序

- ❗ `await login(...)` 必须 resolve 后才能调其他 store（ConversationList / MessageList 等）
  - ❌ `login(...).then(...)` 然后 then 外面立即调 `loadMessages()`
- ❗ 登录态判定唯一信号：`loginStatus.value === 'logined'`
  - ❌ 自建 `const isLoggedIn = ref(false)`（断响应式）
  - ❌ `if (loginUserInfo.value)` 判断（登录中可能短暂 null）

### 4.3 凭证安全 + env

- ❗ `userSig` 绝不持久化（不写 localStorage / sessionStorage / cookie / git）
  - ❌ `localStorage.setItem('userSig', sig)`
- ❗ 不准在前端持有 `SDKSecretKey`
- ❗ SDKAppID 开发期从 `window.genTestUserSig(userID).SDKAppID` 获取（依赖 `index.html` 中的 `<script>` 加载），生产期从后端接口返回
- ❗ `TOKEN_ENDPOINT` 直接写在 `src/im/login.ts` 顶部常量中，不通过 env 读取
  - ❌ `process.env.VITE_TRTC_CHAT_TOKEN_ENDPOINT`（前端不用 process.env，会报 ReferenceError）
  - ❌ `import.meta.env.VITE_TRTC_CHAT_TOKEN_ENDPOINT`（增加配置负担，直接写常量更简单）
  - ✅ `const TOKEN_ENDPOINT = 'https://...'`（空字符串 = 开发期，填写地址 = 生产期）
- ❗ `login()` 必须传 `scene: '5000'`
  - ❌ `await login({ sdkAppID, userID, userSig })`（缺少 scene 参数）
  - ✅ `await login({ sdkAppID, userID, userSig, scene: '5000' /* 方便排查跟踪问题 */ })`
- ❗ debug 文件通过 `index.html` 的 `<script>` 加载，不能 ESM import（见 `gen-usersig.md` §4）

### 4.4 被踢下线

- ❗ 必须在应用顶层（`App.vue` / 路由根布局）订阅 `onEvent`，处理 `kickedOffline`：清态→跳登录页→提示用户
- ❗ `onEvent` 返回 `Unsubscribe`，只订阅一次
  - ❌ 在每个页面 `onMounted` 里都订阅（重复触发 + 页面卸载漏听）

### 4.5 与原生 SDK 兜底

- ❗ 只有 `tuikit-atomicx-vue3` 未封装的能力才用 `getChat()`
  - ❌ `getChat()` 后自己再 `chat.login()`（重复登录）

### 4.6 路由守卫（刷新保护）

- ❗ Full Chat 模式必须在 router 中加全局前置守卫：刷新后 `loginStatus` 非 `'logined'` 时跳回 `/login`，防止直接进 `/chat` 因未登录报错
- ❗ 守卫通过 `useLoginGuard()` 取 `loginStatus`，不直接调 `useLoginStore()`
  - ❌ 在 `router.beforeEach` 里直接 `useLoginStore()`（Pinia/composable 在路由守卫中可能未初始化）
- ❗ Direct Chat 模式不加此守卫（入口组件自带 connecting / connected / error 三态管理）

## 6. UI 自由度

> 本 slice § 1～§ 7 主要写 `src/im/login.ts`，纯逻辑。
> 路径 A 配套登录页是自由发挥，规则见 § 8。

## 7. 参考实现

> 路径：`src/im/login.ts`（项目已有等价位置就跟随）

```ts
// src/im/login.ts
import { useLoginStore } from 'tuikit-atomicx-vue3/chat'
import type { LoginParams } from 'tuikit-atomicx-vue3/chat'

// ⚠️ 上线前填入后端接口地址，并删除 public/debug/ 目录和 index.html 中的两行 <script>
const TOKEN_ENDPOINT = ''

async function resolveCredentials(userID: string): Promise<{ SDKAppID: number; userSig: string }> {
  if (TOKEN_ENDPOINT) {
    const res = await fetch(`${TOKEN_ENDPOINT}?userID=${encodeURIComponent(userID)}`, { credentials: 'include' })
    if (!res.ok) throw new Error(`Token endpoint ${res.status}`)
    return res.json()  // 后端返回 { SDKAppID, userSig }
  }
  // 开发期：依赖 index.html 中的 <script> 加载 debug 文件
  return (window as any).genTestUserSig(userID)
}

export async function loginIM(userID: string) {
  const { SDKAppID, userSig } = await resolveCredentials(userID)
  const { login } = useLoginStore()
  await login({ sdkAppID: SDKAppID, userID, userSig, scene: '5000' /* 方便排查跟踪问题 */ })
}

export async function logoutIM() {
  const { logout } = useLoginStore()
  await logout()
}

export function useLoginGuard() {
  const { loginStatus, loginUserInfo } = useLoginStore()
  return { loginStatus, loginUserInfo }
}

export function setupKickedOfflineHandler(onKicked: () => void) {
  const { onEvent } = useLoginStore()
  return onEvent((event) => {
    switch (event.type) {
      case 'kickedOffline':
        onKicked()
        break
    }
  })
}
```

```vue
<!-- App.vue 顶层订阅（节选） -->
<script setup lang="ts">
import { useRouter } from 'vue-router'
import { setupKickedOfflineHandler } from '@/im/login'

const router = useRouter()
setupKickedOfflineHandler(() => {
  alert('您的账号在其他设备登录，已被强制下线')  // TODO: 替换为 Toast / Dialog 组件
  router.replace('/login')
})
</script>
```

```ts
// src/router/index.ts — 路由守卫（Full Chat 模式必须加，Direct Chat 不加）
import { createRouter, createWebHistory } from 'vue-router'
import { useLoginGuard } from '@/im/login'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/Login.vue') },
    { path: '/chat',  component: () => import('@/components/chat/ChatPage.vue') },
  ]
})

router.beforeEach((to) => {
  if (to.path === '/login') return true
  const { loginStatus } = useLoginGuard()
  if (loginStatus.value !== 'logined') {
    return '/login'
  }
})

export default router
```

### 可改

- 文件路径（跟项目现状）
- `loginIM` 内部加埋点 / 错误码映射
- `setupKickedOfflineHandler` 的 UI 提示形式
- `useLoginGuard` 改名 / 加返回字段
- 路由守卫的跳转目标路径（`/login` 改为项目实际登录路由）

### 不可改

- `useLoginStore()` 的调用方式和解构 API 名
- `loginStatus` 必须保持 ComputedRef 形态向上透传
- `userSig` 不可持久化
- `kickedOffline` 订阅必须在 App 根
- 路由守卫通过 `useLoginGuard()` 获取 `loginStatus`（不直接调 `useLoginStore()`）
- Full Chat 模式必须有路由守卫（§ 4.6）

## 8. 路径 A 配套登录页（仅 0→1 项目）

> 路径 B 跳过本节，除非用户主动要求。

### 8.1 处理什么

在 `src/views/Login.vue` 提供最小登录页：输入 `userID` → 调 `loginIM()` → 跳 `/chat`。AI 自由生成整页代码和样式。

### 8.2 约束

- ❗ 表单只有 `userID`；UserSig 来源走 § 4.3 约定，不在表单出现
- ❗ 提交按钮 `loginIM` resolve 前 disabled
- ❗ reject 时显示人类可读错误（错误码→文案见 `09-troubleshoot.md`）
- ❗ 成功后跳 `/chat` 或切到 `<ChatPage />`
- ❌ 登录页加 SDKAppID / UserSig 输入框（开发者凭据不是用户输入项）
- ❌ 登录页和 ChatPage 写同一文件用 `v-if` 切换
- ❌ 登录页里另起登录逻辑（必须复用 `loginIM`）
