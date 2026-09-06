# 本地生成 UserSig（仅开发调试）

> 与 `slices/` 平级的通用知识文件，各框架共用。
> dispatcher 在路径 A 的 `login-auth` slice 写代码阶段引用本文件。

## 1. 用途

让开发者在登录页**输入任意 userID 即可登录**，无需：
- 每次去控制台手动生成 UserSig
- 搭建后端签发服务

适用于：本地开发 / 联调 / 多用户模拟测试。

## 2. 文件来源

knowledge-base 中已内置 `debug/` 目录：

```
knowledge-base/debug/
├── GenerateTestUserSig.js       # 调用入口（需填 SDKAPPID + SECRETKEY）
└── lib-generate-test-usersig.min.js  # 官方签名计算库（不可修改）
```

使用时需将整个 `debug/` 目录**拷贝到用户项目的 `public/` 目录下**。

## 3. 集成方式

### 3.1 拷贝目标路径

```
<projectRoot>/public/debug/
├── GenerateTestUserSig.js
└── lib-generate-test-usersig.min.js
```

放在 `public/` 下的原因：
- Vite / webpack-dev-server 都将 `public/` 作为静态资源根目录
- `<script src="/debug/...">` 在两种构建工具下均可直接访问
- 不经过打包器处理，lib 作为全局脚本正确执行

> 路径 A 由 AI 在 login-auth slice 写代码时自动拷贝（`write_to_file`）。

### 3.2 填入凭据

`public/debug/GenerateTestUserSig.js` 中两个常量需替换：

```js
const SDKAPPID = 1400000000;  // ← 用户的 SDKAppID
const SECRETKEY = 'your_secret_key_here';  // ← 用户的 SecretKey
```

> 这两个值在 A.2 凭据收集阶段获取，直接写入此文件。不存放到 `.env.local`。

### 3.3 在 login 逻辑中引用

`lib-generate-test-usersig.min.js` 是 IIFE 全局脚本，**必须通过 `<script>` 标签加载**才能正确挂载 `window.LibGenerateTestUserSig`，不能用 ESM `import`（模块有独立作用域，`window` 上拿不到，会报 `LibGenerateTestUserSig is not a constructor`）。

在 `index.html` 中加两行（放在 `<body>` 末尾、主入口 script 之前）：

```html
<!-- index.html（仅开发期，上线前删除） -->
<script src="/debug/lib-generate-test-usersig.min.js"></script>
<script src="/debug/GenerateTestUserSig.js"></script>
```

在 login 逻辑中通过 `window` 调用：

```ts
// src/im/login.ts

// ⚠️ 上线前将此处替换为真实后端接口地址，并删除 public/debug/ 和 index.html 中的两行 <script>
const TOKEN_ENDPOINT = ''  // 生产期填入，如 'https://your-backend.com/api/im/get-user-sig'

async function resolveCredentials(userID: string): Promise<{ SDKAppID: number; userSig: string }> {
  // 生产期：调后端签发接口
  if (TOKEN_ENDPOINT) {
    const res = await fetch(`${TOKEN_ENDPOINT}?userID=${encodeURIComponent(userID)}`, { credentials: 'include' })
    if (!res.ok) throw new Error(`Token endpoint ${res.status}`)
    return await res.json()  // 后端返回 { SDKAppID, userSig }
  }

  // 开发期：本地生成（依赖 index.html 中的 <script> 加载）
  return (window as any).genTestUserSig(userID)
}
```

**优先级**：`TOKEN_ENDPOINT` 非空时走后端接口 > 否则本地生成

## 4. Hard rules

### ❗ 必须通过 `<script>` 标签加载，不能 ESM import
- ❌ `import { genTestUserSig } from '../debug/GenerateTestUserSig'`（模块作用域内 `window.LibGenerateTestUserSig` 未定义）
- ✅ `index.html` 加两行 `<script src="/debug/...">`，再用 `window.genTestUserSig(userID)` 调用

### ❗ debug 目录必须加入 .gitignore
- `public/debug/` 内含 SecretKey 明文，**绝不可入库**
- AI 写代码时检查 `.gitignore` 是否已有 `public/debug/`，没有则追加

### ❗ SDKAppID + SecretKey 都直接写入 GenerateTestUserSig.js
- ❌ 不要把 SDKAppID / SecretKey 放到 `.env.local`（该文件的设计就是直接内嵌常量）
- ✅ 直接在文件中填写 `SDKAPPID` 和 `SECRETKEY`
- ✅ 登录时通过 `window.genTestUserSig(userID)` 返回的 `SDKAppID` 字段获取

### ❗ lib-generate-test-usersig.min.js 不可修改
- 这是官方签名算法库，原样拷贝

### ❗ 上线前必须删除整个 public/debug/ 目录
- WHAT-TO-DO-NEXT.md 中明确标注
- 生产环境 `resolveCredentials` 只走后端接口分支

## 5. 凭据收集阶段引导

A.2 收集：
1. **SDKAppID** — 必填（写入 `public/debug/GenerateTestUserSig.js`）
2. **SecretKey** — 必填（写入 `public/debug/GenerateTestUserSig.js`）

Direct Chat 追加：
3. 对话对象
4. 入口位置

> SDKAppID 和 SecretKey 都内嵌在 debug 文件中，不使用 `.env.local` 存放。

## 6. 反例

- ❌ 把 `public/debug/` 提交到 git（泄露 SecretKey）
- ❌ 生产环境仍引用 debug 目录中的本地生成（任何人可伪造身份）
- ❌ 修改 `lib-generate-test-usersig.min.js`（破坏签名算法）
- ❌ 把 SDKAppID / SecretKey 写到 `.env.local`（debug 文件是唯一信源）
- ❌ 把文件放在 `src/debug/`（webpack-dev-server 无法通过 `/debug/` 路径直接访问）
