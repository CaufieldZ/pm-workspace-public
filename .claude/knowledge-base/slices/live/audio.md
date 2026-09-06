---
id: live/audio
name: 音效管理
product: live
tags: [audio, voice, effect, changer, reverb, ear-monitor, AudioEffectStore]
platforms: [ios, android, web, flutter]
related: [live/anchor-preview, live/device-control]
---

# 音效管理

## 功能说明

`AudioEffectStore` 是全局单例，统一管理主播端的音效能力，包括采集音量、耳返、变声、混响四大功能模块。所有音效设置在整个直播生命周期内持续生效，直播结束后须调用 `reset()` 恢复默认值。

采集音量（`setCaptureVolume`）通过 `DeviceStore` 控制，影响观众收到的音量；耳返音量（`setVoiceEarMonitorVolume`）仅影响主播本人通过耳机听到的声音，两者相互独立。

## 核心概念

| 方法 / 属性 | 归属 | 说明 |
|-------------|------|------|
| `AudioEffectStore` | `AudioEffectStore` | 全局单例，整个 App 生命周期内唯一实例 |
| `DeviceStore` | `DeviceStore` | 全局单例；采集音量由此控制 |
| `setCaptureVolume` | `DeviceStore` | 设置麦克风采集音量；范围 `0–100`，默认 `100` |
| `setVoiceEarMonitorEnable` | `AudioEffectStore` | 开启 / 关闭耳返；须插入**有线耳机**才有效（蓝牙耳机不支持） |
| `setVoiceEarMonitorVolume` | `AudioEffectStore` | 设置耳返音量；范围 `0–100`，默认 `100` |
| `setAudioChangerType` | `AudioEffectStore` | 设置变声效果；传 `none` 还原 |
| `setAudioReverbType` | `AudioEffectStore` | 设置混响效果；传 `none` 还原 |
| `reset()` | `AudioEffectStore` | 重置所有音效参数为默认值 |

### AudioChangerType 枚举

| 值 | 说明 |
|----|------|
| `none` | 原声（无变声） |
| `child` | 儿童音 |
| `littleGirl` | 萝莉音 |
| `man` | 男声 |
| `ethereal` | 空灵 |
| `cold` | 冷酷 |
| `foreignerr` | 外国腔 |
| `heavyMachinery` | 重型机械 |
| `heavyMetal` | 重金属 |
| `strongCurrent` | 强电流 |
| `fatso` | 肥仔 |
| `trappedBeast` | 困兽 |

### AudioReverbType 枚举

| 值 | 说明 |
|----|------|
| `none` | 无混响 |
| `ktv` | KTV |
| `smallRoom` | 小房间 |
| `auditorium` | 礼堂 |
| `loud` | 大型会场 |
| `deep` | 深沉 |
| `magnetic` | 磁性 |
| `metallic` | 金属感 |

## 最佳实践

### ✅ ALWAYS

1. **直播结束后调用 `reset()`** — `AudioEffectStore` 是全局单例，音效参数在 App 整个生命周期内持久存在。离房后音效虽自动失效，但本地 `AudioEffectState` 不会重置；主动调用 `reset()` 可保持状态干净，避免下次开播时 UI 显示残留旧值。
2. **两个 Store 都是全局单例，各司其职** — 采集音量走 `DeviceStore.setCaptureVolume`，其余音效走 `AudioEffectStore`。不要混淆两个单例的职责。
3. **耳返仅支持有线耳机** — 蓝牙耳机（AirPods 等）**不支持**耳返。开启耳返时，先通过系统音频路由 API 确认当前输出路由包含有线耳机，否则开启后无声音。应向用户提示"请插入有线耳机"，不要基于蓝牙耳机判断。
4. **音量范围 0–100，超出范围截断** — `setCaptureVolume` 和 `setVoiceEarMonitorVolume` 的有效范围均为 `0–100`；默认值为 `100`（即原始音量）。UI 滑块的 `maximumValue` 应设为 `100`，不是 `150`。

### ❌ NEVER

1. **直播结束不调 `reset()`** — 遗漏重置不影响实际音效（离房后自动失效），但会导致 `AudioEffectState` 保持上次的值，下次开播时 UI 面板显示残留状态，造成困惑。
2. **在未插有线耳机时向用户展示耳返开关** — 蓝牙耳机不支持耳返；有线耳机未插入时耳返无效，应先通过系统音频路由 API 检测有线耳机再决定是否展示该控件，避免用户困惑。
3. **将采集音量和耳返音量混用** — 两个音量控制的是不同端点（观众听到的 vs 主播自己听到的），不要用同一个 Slider 同时控制两者。

## 排障指南

### 常见错误码

音效模块通常不返回业务错误码，异常表现为效果不生效。常见排障场景：

| 现象 | 可能原因 | 处理建议 |
|------|----------|----------|
| 耳返无声 | 未插入有线耳机 / 使用了蓝牙耳机 | 蓝牙耳机不支持耳返；通过系统音频路由 API 检查当前输出设备，确认包含有线耳机 |
| 采集音量异常（观众听到音量过大/过小） | `setCaptureVolume` 值偏差或未调用 | 检查是否已调用 `DeviceStore.setCaptureVolume`，有效范围 0–100，默认值 100 |
| 变声/混响在新一场直播中意外生效 | 直播结束时未调 `reset()` | 在直播结束（下播/退房）时调用 `AudioEffectStore.reset()` |
| 变声效果不生效 | 麦克风未打开 | 确保 `DeviceStore.openLocalMicrophone` 已成功回调 |

### 排障流程

```
耳返无声
├── 是否已调用 setVoiceEarMonitorEnable(true)？
│       └─ 否 → 补充调用
├── 是否使用有线耳机？
│       ├─ 蓝牙耳机 → 不支持耳返，提示用户换有线耳机
│       └─ 通过系统音频路由 API 检查当前输出设备
│               ├─ 无有线耳机输出 → 提示用户插入有线耳机
│               └─ 有耳机但仍无声 → 检查 earMonitorVolume 是否为 0
└── 重置后重新开启
        └─ reset() → setVoiceEarMonitorEnable(true) → setVoiceEarMonitorVolume(100)

变声/混响上次直播残留
├── 确认直播结束时未调 reset()
└─ 在下播/退房回调中补充 AudioEffectStore.reset()

采集音量过大/过小
├── 检查 DeviceStore 的 state.captureVolume 当前值
├── 调用 setCaptureVolume(100) 恢复默认
└── 若仍异常 → 检查是否有其他地方覆盖写入了 captureVolume
```

## 关联知识

- **[live/device-control](live/device-control.md)** — `DeviceStore` 管理麦克风开关，音效须在麦克风打开后才生效
- **[live/anchor-preview](live/anchor-preview.md)** — 主播预览阶段可预设音效，开播后立即生效
