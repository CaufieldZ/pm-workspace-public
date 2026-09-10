---
id: live/login-auth
name: 登录与鉴权
product: live
tags: [login, auth, SDKAppID, UserID, UserSig, LoginStore]
platforms: [ios, android, web, flutter]
related: [live/device-control, live/anchor-preview, live/audience-watch]
---

# 登录与鉴权

## 功能说明

`LoginStore` 是所有 Live 功能的前置依赖，负责完成 TRTC SDK 的初始化与用户身份鉴权。所有主播推流、观众拉流、连麦等能力均需在登录成功后才可调用。

核心入口：调用 LoginStore 的 `login` 方法，传入 SDKAppID、UserID、UserSig，通过回调获取登录结果。

登录成功后 LoginStore 作为全局单例持有会话状态，其他 Store（DeviceStore、RoomStore 等）依赖其登录态运行。

## 核心概念

| 概念 | 说明 |
|------|------|
| **SDKAppID** | 腾讯云控制台创建应用后分配的唯一数字 ID，用于区分不同应用的流量与计费 |
| **UserID** | 业务侧自定义的用户唯一标识，仅允许 ASCII 字母、数字、连字符 `-`、下划线 `_`，长度 ≤ 32 字节 |
| **UserSig** | 由业务后端使用 SecretKey 签发的鉴权票据，具有有效期（建议 7 天），过期后需重新签发 |
| **LoginStore** | SDK 全局单例，持有登录态；登录成功后其他 Store 方可使用 |

## 最佳实践

### ✅ ALWAYS

1. **在业务后端生成 UserSig** — 将 SDKSecretKey 保管在服务器端，客户端通过接口获取 UserSig，禁止在客户端直接使用 SecretKey 签发。
2. **登录成功后才调用其他 API** — 在 `login` 的成功回调中再初始化 DeviceStore、进入房间等操作，避免因登录未完成导致 `-1002` 错误。
3. **声明系统权限** — 推流场景需在各平台声明相机与麦克风权限（各平台方式不同 → 见平台文件），否则调用设备接口时会被系统拒绝或崩溃。
4. **监听登录状态变化** — 注册登录状态变更回调，处理后台断连、UserSig 过期等场景，及时触发重新登录或 UI 提示。

### ❌ NEVER

1. **客户端硬编码 SecretKey** — 一旦 App 包被逆向，SecretKey 泄露将导致所有用户的 UserSig 可被伪造，造成安全事故。
2. **使用过期 UserSig** — 过期票据会导致登录失败（`-1001`），需在签发时记录有效期并在到期前刷新。
3. **忽略登录回调错误** — 失败回调必须处理，至少向用户展示提示并上报错误日志，不可静默忽略导致后续所有功能异常。

## 排障指南

### 常见错误码

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| `-1000` | SDKAppID 未找到 / 不合法 | 核对控制台 App 列表中的 SDKAppID，确认传入类型为 `Int` |
| `-1001` | 参数不合法（含 UserSig 过期/格式错误） | 检查 UserID 是否包含非法字符；重新从后端获取最新 UserSig |
| `-1002` | 未登录，调用了需要登录态的 API | 确保在 `login` 成功回调后再调用其他接口 |

### 排障流程

```
登录失败
├── 错误码 -1000
│   ├── 检查 SDKAppID 是否与控制台一致
│   └── 确认 SDKAppID 类型为 Int（非 String）
├── 错误码 -1001
│   ├── UserSig 是否已过期？→ 重新签发
│   ├── UserID 是否含非 ASCII 字符或超过 32 字节？→ 修正
│   └── UserSig 是否由正确 SDKAppID 对应的 SecretKey 签发？→ 核对
├── 错误码 -1002（其他接口返回）
│   ├── 是否在 login 完成前调用了其他接口？→ 移入登录成功回调中
│   └── 登录态是否已失效（后台断连/UserSig 过期）？→ 重新登录
└── 其他
    ├── 检查网络连通性（是否能访问 trtc.io）
    └── 抓取完整 error.code + error.message 上报
```

## 关联知识

- **[live/device-control](live/device-control.md)** — 登录成功后初始化摄像头与麦克风
- **[live/anchor-preview](live/anchor-preview.md)** — 主播预览需先完成登录
- **[live/audience-watch](live/audience-watch.md)** — 观众观看流同样依赖登录态
- **[live/error-codes](live/error-codes.md)** — 完整错误码参考
