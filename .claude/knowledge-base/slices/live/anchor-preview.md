---
id: live/anchor-preview
name: 主播预览
product: live
tags: [anchor, preview, LiveCoreView, pushView, camera]
platforms: [ios, android, web, flutter]
related: [live/device-control, live/anchor-room-config, live/beauty, live/audio]
---

# 主播预览

## 功能说明

主播预览是开播前的关键准备步骤。`LiveCoreView` 是专为直播场景设计的轻量级视图组件，通过指定推流模式（pushView）将摄像头采集的本地画面渲染到屏幕上，让主播在正式开播前确认画面效果。

预览阶段**不会**推流到观众端，仅在本地渲染画面，直到调用 `createLive` 后才开始向外推流。

## 核心概念

| 概念 / 方法 | 说明 |
|------------|------|
| LiveCoreView（推流模式） | 创建主播推流视图；推流模式表示该视图用于采集和预览本地画面 |
| `setLiveID` | 将视图绑定到指定直播间 ID；**必须在开启摄像头之前调用** |
| DeviceStore `openLocalCamera` | 打开本地摄像头并将预览帧渲染到已绑定的 LiveCoreView；可指定前置/后置 |
| DeviceStore `openLocalMicrophone` | 打开本地麦克风，采集音频（预览阶段可选，开播前必须打开）|

### 预览 vs 推流

```
[预览阶段]  LiveCoreView(推流模式) + setLiveID + openLocalCamera
               ↓ 仅本地渲染，不推流
[开播阶段]  LiveListStore.createLive(liveInfo) 之后
               ↓ 本地画面开始向观众推流
```

## 最佳实践

### ✅ ALWAYS

1. **创建 LiveCoreView 后必须立即调用 `setLiveID`** — 视图内部通过 liveID 关联底层推流通道；若跳过此步骤，摄像头画面无法渲染（出现黑屏）。
2. **先打开设备，再依赖预览** — 调用 `openLocalCamera` 的成功回调确认后，再进行 UI 更新（如移除加载遮罩）。
3. **提前申请系统权限** — 进入预览页面前通过系统权限检查 API 确认摄像头/麦克风权限（各平台方式不同 → 见平台文件），避免在 `openLocalCamera` 回调中才发现权限被拒导致用户体验差。
4. **将 LiveCoreView 正确加入视图层级** — 将 LiveCoreView 添加到视图层级后设置好布局，否则视图不可见。

### ❌ NEVER

1. **忘记调用 `setLiveID`** — 这是最常见的黑屏原因；`LiveCoreView` 没有 liveID 绑定时摄像头数据无处渲染。
2. **预览阶段调用 `createLive`** — `createLive` 会立即向服务端创建房间并开始推流，应在用户确认开播后才调用，不可在预览配置页面调用。
3. **在 `openLocalCamera` completion 之前就调用 `createLive`** — 设备未就绪时开播会导致推流无画面。
4. **跳过设备关闭直接销毁 LiveCoreView** — 退出预览页面时须先关闭摄像头与麦克风，再移除视图，否则可能出现资源泄漏。

## 排障指南

### 常见错误码

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| `-1101` | 摄像头缺少系统授权 | 引导用户在「设置 > 隐私 > 摄像头」中开启权限 |
| `-1105` | 麦克风缺少系统授权 | 引导用户在「设置 > 隐私 > 麦克风」中开启权限 |
| `-1100` | 打开摄像头失败 | 重启 App 重试；持续失败则上报错误日志 |
| `-1102` | 摄像头被其他进程占用 | 提示用户关闭 FaceTime / 系统相机等应用 |

### 排障流程

```
预览黑屏
├── setLiveID 是否已调用？
│   └─ 否 → 在将 LiveCoreView 添加到视图层级之后、openLocalCamera 之前调用 setLiveID
├── openLocalCamera 是否成功（成功回调）？
│   ├─ 失败(-1101) → 摄像头权限被拒，引导用户去系统设置
│   ├─ 失败(-1102) → 摄像头被占用，提示关闭其他应用
│   └─ 失败(-1100) → 硬件失败，重试或上报
├── LiveCoreView 是否已添加到视图层级并设置正确布局？
│   └─ 否 → 检查视图层级，确认视图可见
└── 模拟器/无摄像头设备？
    └─ 是 → 部分平台模拟器不支持摄像头，切换真机测试

预览有画面但没声音
├── openLocalMicrophone 是否已调用？
├── 麦克风权限是否已授予（-1105）？
└── 是否被其他音频应用占用（-1106）？
```

## 关联知识

- **[live/device-control](live/device-control.md)** — DeviceStore 设备管理完整 API
- **[live/anchor-room-config](live/anchor-room-config.md)** — 直播间配置（setLiveID 所需的 liveID 来源）
- **[live/anchor-lifecycle](live/anchor-lifecycle.md)** — 从预览到 createLive 开播的完整生命周期
- **[live/beauty](live/beauty.md)** — 预览阶段启用美颜效果
- **[live/audio](live/audio.md)** — 音频采集与配置
