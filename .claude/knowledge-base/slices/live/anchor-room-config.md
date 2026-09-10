---
id: live/anchor-room-config
name: 直播间配置
product: live
tags: [room, config, metadata, LiveListStore, room-name, cover]
platforms: [ios, android, web, flutter]
related: [live/anchor-preview, live/anchor-lifecycle]
---

# 直播间配置

## 功能说明

在主播调用 `createLive` 开播之前，需要通过 `LiveInfo` 配置直播间的基本信息（房间名称、封面图、座位模板等）以及扩展的自定义元数据（MetaData）。配置完成后将 `LiveInfo` 传入 `LiveListStore` 的 `createLive` 方法完成直播间创建。

开播后仍可通过 `updateLiveMetaData` 动态更新 MetaData，但仅限**房主和管理员**操作。

## 核心概念

### LiveInfo 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `liveID` | 字符串 | ✅ | 直播间唯一标识；ASCII 字符，长度 ≤ 48 字节 |
| `liveName` | 字符串 | ❌ | 直播间名称；UTF-8 编码，长度 ≤ 30 字节（约 10 个汉字） |
| `coverURL` | 字符串 | ❌ | 封面图 URL；建议宽高比 9:16，大小 ≤ 500KB |
| `seatTemplate` | 枚举 `SeatTemplate` | ✅ | 连麦座位布局模板（如 `videoDynamicGrid9Seats`） |
| `notice` | 字符串 | ❌ | 直播间公告文本 |
| `isGiftEnabled` | 布尔值 | ❌ | 是否开启礼物功能，默认 `false` |

### MetaData 约束

MetaData 是附加在直播间上的键值对扩展信息，常用于存储自定义标签、分类、活动 ID 等。

| 限制项 | 上限 | 超出时的错误 |
|--------|------|-------------|
| 键的数量 | 10 个 | 超出则更新失败 |
| 单个键长度 | 50 字节 | 键过长则写入被拒绝 |
| 单个值大小 | 2 KB | 超出则写入被拒绝 |
| 所有值总大小 | 16 KB | 超出则更新失败 |

### updateLiveMetaData 权限

```
房主（创建者）    ✅ 可调用
管理员            ✅ 可调用
普通成员/观众     ❌ 返回 -2300（权限不足）
```

## 最佳实践

### ✅ ALWAYS

1. **`createLive` 之前完成所有配置** — `LiveInfo` 中的 `liveID`、`liveName`、`seatTemplate` 在创建后无法通过普通接口修改；需修改时必须结束本场直播重新创建。
2. **key 数量控制在 10 个以内** — 超过限制会导致 `updateLiveMetaData` 失败；定期清理不再使用的 key。
3. **MetaData 值做大小校验** — 写入前在客户端侧计算 UTF-8 字节数，超过 2 KB 时截断或拆分存储，避免请求到达服务端才失败。
4. **使用语义化 key 命名** — 如 `category`、`activityId`，避免使用随机字符串，便于维护和调试。

### ❌ NEVER

1. **单值超过 2 KB** — 如大段 JSON、Base64 图片数据不应存入 MetaData；应上传到 CDN 后存 URL。
2. **非房主调用 `updateLiveMetaData`** — 观众或普通成员调用会返回 `-2300` 权限不足；须在 UI 层限制此操作入口。
3. **将敏感信息存入 MetaData** — MetaData 对房间内所有成员可见，不应存储 token、密码等敏感字段。
4. **在 `createLive` 回调成功之前使用 liveID 进行其他操作** — 房间创建是异步操作，回调成功前房间尚不存在于服务端。

## 排障指南

### 常见错误码

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| `-2105` | 直播间 ID 非法 | `liveID` 须为 ASCII 字符且长度 ≤ 48 字节；检查是否含非法字符（如中文、空格） |
| `-2107` | 直播间名称非法 | `liveName` 须为合法 UTF-8 字符串且长度 ≤ 30 字节（约 10 个汉字）；超长时截断处理 |
| `-2300` | 权限不足 | 仅房主/管理员可调用 `updateLiveMetaData`；检查当前用户角色 |
| `-2108` | 已在其他直播间 | 当前用户已在另一个房间中；需先调用 `endLive` 或 `leaveLive` 退出后再创建 |

### 排障流程

```
createLive 失败
├── 错误码 -2105（liveID 非法）
│   ├── 检查 liveID 是否为纯 ASCII 字符
│   ├── 检查长度是否 ≤ 48 字节
│   └── 常见问题：含空格、中文、特殊符号
├── 错误码 -2107（liveName 非法）
│   ├── 检查 liveName UTF-8 编码后字节数是否 ≤ 30
│   └── 1 个汉字 = 3 字节；10 个汉字 = 30 字节（恰好达到上限）
└── 错误码 -2108（已在其他房间）
    └── 调用 endLive / leaveLive 退出当前房间后重试

updateLiveMetaData 失败
├── 错误码 -2300（权限不足）
│   └── 当前用户非房主/管理员，不可更新 MetaData
├── MetaData 超出大小限制
│   ├── 单值 > 2 KB → 减小值大小或改存 CDN URL
│   └── 总大小 > 16 KB → 清理不必要的 key
└── key 数量超过 10 个 → 删除旧 key 后再添加新 key
```

## 关联知识

- **[live/anchor-preview](live/anchor-preview.md)** — 预览阶段获取 liveID，传入 LiveInfo
- **[live/anchor-lifecycle](live/anchor-lifecycle.md)** — createLive 完整调用流程
- **[live/error-codes](live/error-codes.md)** — 完整错误码参考
