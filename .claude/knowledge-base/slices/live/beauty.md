---
id: live/beauty
name: 美颜
product: live
tags: [beauty, smooth, whiten, ruddy, BaseBeautyStore, filter]
platforms: [ios, android, web, flutter]
related: [live/anchor-preview, live/coguest-apply, live/device-control]
---

# 美颜

## 功能说明

`BaseBeautyStore` 是全局单例，提供磨皮、美白、红润三种基础美颜效果。通过调整 0–9 的强度参数作用于本地摄像头采集的视频流，效果实时生效。所有美颜参数通过 `BaseBeautyState` 统一管理，UI 订阅状态变化实现滑块与实际效果的同步。

`BaseBeautyStore` 适用于主播开播和连麦观众两个场景，复用同一套接口。

## 核心概念

| 方法 / 属性 | 说明 |
|-------------|------|
| `BaseBeautyStore` | 全局单例，整个 App 生命周期内唯一实例 |
| `setSmoothLevel` | 设置磨皮强度；参数为浮点数，范围 0–9，0 为关闭，9 为最强 |
| `setWhitenessLevel` | 设置美白强度；参数为浮点数，范围 0–9 |
| `setRuddyLevel` | 设置红润强度；参数为浮点数，范围 0–9 |
| `reset()` | 将所有美颜参数恢复为默认值（通常为 0） |
| `BaseBeautyState` | 美颜状态容器；包含 `smoothLevel`、`whitenessLevel`、`ruddyLevel` 三个浮点数属性 |
| `state` | 可订阅的状态属性，变化时通知 UI 更新滑块位置 |

### UI 参数映射

UI 控件（滑块）通常使用 `0.0–1.0` 的浮点范围，调用 SDK 前需乘以 9 转换：

```
SDK 参数 = UI 滑块值 × 9.0
UI 滑块值 = SDK 参数 ÷ 9.0
```

> ⚠️ SDK 参数类型为浮点数，不是整数。传入 `4.5` 与传入 `4`（整数截断）效果不同。

| UI 值 | SDK 参数值 | 效果 |
|-------|--------|------|
| 0.0 | 0.0 | 关闭效果 |
| 0.5 | 4.5 | 中等强度 |
| 1.0 | 9.0 | 最强效果 |

## 最佳实践

### ✅ ALWAYS

1. **摄像头打开后再设置美颜** — `BaseBeautyStore` 作用于摄像头采集的视频流，必须在 `DeviceStore.openLocalCamera` 成功后调用美颜接口，否则设置不会生效。
2. **订阅 `state` 更新 UI** — 订阅 `BaseBeautyStore` 的 `state` 状态变化，在状态变化时同步更新滑块位置，保证 UI 与实际效果一致。特别是调用 `reset()` 后需刷新所有滑块到初始值。
3. **参数乘以 9.0 后传入浮点数** — UI 滑块值（0.0–1.0）必须映射到 SDK 参数范围（0.0–9.0），不要直接传 0.0–1.0 的值（实际效果几乎为 0）。参数类型是浮点数，不要转换为整数。
4. **连麦观众复用同一单例** — 连麦场景中观众打开摄像头后，直接使用 `BaseBeautyStore` 即可，无需额外初始化。

### ❌ NEVER

1. **参数超过 9.0** — 传入大于 9.0 的值行为未定义，可能导致效果异常或崩溃。UI 层应做数值截断保护。
2. **在摄像头关闭时调用美颜接口** — 无法作用于视频流，调用也不会报错，但下次摄像头打开时不会自动恢复上次设置，需重新赋值。
3. **不做参数映射直接传 UI 值** — 直接将 0.0–1.0 的 UI 滑块值传给 SDK，实际强度极低（9 分之一），用户感知不到美颜效果。且参数类型是浮点数，不要转换为整数传入。

## 排障指南

### 常见错误码

美颜接口本身无业务错误码，问题通常表现为效果不生效：

| 现象 | 可能原因 | 处理建议 |
|------|----------|----------|
| 美颜无效果 | 摄像头未打开 | 确保 `openLocalCamera` 成功后再调用 |
| 美颜无效果 | 参数传值错误（忘记 ×9） | 检查传入值是否在 1–9 范围内 |
| 美颜无效果 | 授权问题 | 确认 AtomicXCore 授权包含美颜功能 |
| 滑块与效果不同步 | 未订阅 `state` | 订阅状态变化，从 `state` 读取参数更新 UI |
| `reset()` 后滑块未归零 | UI 未监听状态变化 | 订阅 `state` 变化，在 `reset()` 后自动刷新 UI |

### 排障流程

```
美颜无效果
├── 摄像头是否已打开？
│   └─ 否 → 等待 openLocalCamera completion 回调后再设置美颜
├── 参数是否正确？
│   ├─ 打印 smoothLevel/whitenessLevel/ruddyLevel 值
│   └─ 若值 < 1.0 → 确认是否做了 ×9 转换
├── 授权是否包含美颜？
│   └─ 检查 AtomicXCore 授权配置，联系腾讯云确认
└── 真机测试
    └─ 模拟器摄像头不支持，美颜效果只能在真机上验证

reset() 后 UI 未更新
└── 检查是否订阅了 BaseBeautyStore 的 state 变化
    └── 在状态回调中更新所有滑块的值
```

## 关联知识

- **[live/anchor-preview](live/anchor-preview.md)** — 主播预览时即可开启美颜
- **[live/device-control](live/device-control.md)** — 摄像头打开是美颜生效的前提
- **[live/coguest-apply](live/coguest-apply.md)** — 连麦观众打开摄像头后同样可使用美颜
