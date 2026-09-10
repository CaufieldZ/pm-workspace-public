---
id: conference/prejoin-check
name: 入会前设备检查
product: conference
platform: web
tags: [prejoin, camera-test, microphone-test, speaker-test, device-check]
platforms: [web]
related: [conference/login-auth, conference/device-control, conference/network-quality]
api_docs:
  - title: 设备检测
    url: https://cloud.tencent.com/document/product/647/126939
---

# 入会前设备检查

## 功能说明

入会前设备检查负责用户真正加入会议前的本地自检流程，帮助确认摄像头、麦克风、扬声器是否可用，并让用户在入会前完成设备选择、权限确认和异常兜底。它解决的是“进房之前先把设备准备好”这条主流程。会中设置面板、工具栏或异常恢复场景下也可能出现局部设备检查、预览和测试，但那属于 `device-control` 的会中能力延伸，而不是当前 slice 关注的主流程。

## 核心概念

### 角色与操作

| 角色 | 关键操作 | 说明 |
|------|----------|------|
| 准备入会的用户 | 预览和测试设备 | 在不真正入房的前提下完成摄像头、麦克风、扬声器检查 |
| 浏览器 / 系统 | 授予测试权限 | 控制会前是否允许访问摄像头和麦克风 |
| 会前检测页 | 聚合测试流程 | 承载设备选择、音量反馈、测试音频播放和异常提示 |
| 入房主流程 | 消费测试结果 | 把用户在会前选好的设备延续到真实会议里 |

### 事件流

| 阶段 | 参与方 | 关键动作 |
|------|--------|----------|
| 打开会前页 | 用户 | 进入会前检测流程 |
| 摄像头测试 | 浏览器 / 客户端 | 启动本地画面预览，确认摄像头工作正常 |
| 麦克风测试 | 浏览器 / 客户端 | 检测麦克风采集并反馈实时音量 |
| 扬声器测试 | 浏览器 / 客户端 | 播放测试音并确认输出设备是否正确 |
| 入会衔接 | 用户 / 客户端 | 结束测试，把当前设备选择带入真实入会流程 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| 当前选择的摄像头 / 麦克风 / 扬声器 | 用户准备带入会议的设备偏好 |
| 摄像头预览状态 | 表示当前是否已经启动会前画面预览 |
| 麦克风测试电平 | 用于反馈当前麦克风是否正在采集声音 |
| 扬声器测试状态 | 用于判断测试音是否成功播放到目标设备 |
| 会前异常状态 | 包括权限拒绝、设备不可用、测试未启动等情况 |

### 状态机

```text
idle
  → camera-testing
  → microphone-testing
  → speaker-testing
  → confirmed
  → entering-room

camera-testing / microphone-testing / speaker-testing
  → blocked
  → failed
  → idle
```

## 前置条件
**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`

**前置状态**：
- 已阅读 `conference/prejoin-check`，明确当前能力的产品边界。
- 已完成 `conference/login-auth`，确保当前页面具备稳定登录态。
- 已根据业务流程接入会议上下文；需要房间状态时，优先通过 `conference/room-lifecycle` 统一承接。
- 当前能力涉及媒体采集、渲染或浏览器权限时，请在 `HTTPS` 或 `localhost` 安全上下文下调试。

## 最佳实践

### ✅ ALWAYS

1. **把入会前完整检查流程与真实入会控制拆成两段主链路** —— 用户先完成会前自检，再进入房间主链路；会中如需局部检查，应由会中设备能力单独承接。
2. **把用户选定的设备延续到会中** —— 会前选好的摄像头、麦克风和扬声器应直接复用于会中控制。
3. **在页面卸载、路由离开或进入会议前停止全部测试** —— 必须调用 `stopCameraTest()` 与 `stopSpeakerTest()`（若 SDK 暴露），避免会前测试与会中真实采集冲突，以及扬声器测试音贯穿整场会议。
4. **把权限拒绝和设备缺失写成可执行提示** —— 告诉用户下一步该切浏览器权限、换设备，还是直接降级进入。

### ❌ NEVER

1. **不要把会前测试残留到会中流程里** —— 测试流和真实采集流应在入会时完成切换；`startSpeakerTest` 后未 `stopSpeakerTest` 会导致测试音循环播放至会议结束。
2. **不要只测试摄像头而忽略麦克风和扬声器** —— 用户真实会议体验依赖完整的音视频链路。
3. **不要在测试失败时静默继续入会** —— 如果关键设备不可用，应给出明确风险提示或修复建议。

## 代码示例
### 会前自检：摄像头、麦克风、扬声器测试

```ts
import { ref } from 'vue';
import { useDeviceState } from 'tuikit-atomicx-vue3/room';

const {
  startCameraTest,
  stopCameraTest,
  startMicrophoneTest,
  startSpeakerTest,
  stopSpeakerTest,
  currentMicVolume,
} = useDeviceState();

// ⚠️ 关键：会前测试 API（startCameraTest / startMicrophoneTest）运行在测试模式下，
// **不会** 改变 cameraStatus / microphoneStatus。
// 预检页的设备开关状态必须使用独立的本地 ref 管理。
const isCameraOn = ref(true);
const isMicrophoneOn = ref(true);

await startCameraTest({ view: document.getElementById('preview')! });
await startMicrophoneTest({ interval: 200 });
await startSpeakerTest({
  filePath: 'https://web.sdk.qcloud.com/trtc/electron/download/resources/media/TestSpeaker.mp3',
  // TODO: 上线前建议替换为客户自己维护的 HTTPS mp3 资源，避免外部测试资源变更或不可用。
});

// 切换摄像头预览：停止/重启测试，同时翻转本地状态
async function toggleCameraPreview(view: HTMLElement) {
  if (isCameraOn.value) {
    await stopCameraTest();
    isCameraOn.value = false;
  } else {
    await startCameraTest({ view });
    isCameraOn.value = true;
  }
}

// 入会前停止测试释放设备资源（扬声器测试音必须停止，否则会贯穿整场会议）
await stopSpeakerTest?.();
await stopCameraTest();
```

### 会前检测完整组件示例（Vue 3 Composition API）

```ts
import { ref, onMounted, onUnmounted } from 'vue';
import { useDeviceState } from 'tuikit-atomicx-vue3/room';

// ⚠️ 如果业务层封装了统一的 composable（如 useConferenceDevice），
// 必须确保 useDeviceState() 在模块级缓存为单例（只调用一次），
// 否则不同组件拿到的 currentMicVolume 可能来自不同实例，导致音量数据不同步。
const {
  startCameraTest,
  stopCameraTest,
  startMicrophoneTest,
  currentMicVolume, // 由 startMicrophoneTest 按 interval 周期更新
} = useDeviceState();

// 本地状态：预检页 UI 开关（不依赖 cameraStatus / microphoneStatus）
const isCameraOn = ref(true);
const isMicrophoneOn = ref(true);
const previewRef = ref<HTMLElement | null>(null);

onMounted(async () => {
  if (previewRef.value) {
    await startCameraTest({ view: previewRef.value });
    await startMicrophoneTest({ interval: 200 });
  }
});

onUnmounted(async () => {
  await stopSpeakerTest?.();
  await stopCameraTest();
});

// 入会时将本地预设状态透传给会中逻辑
function getDevicePreset() {
  return { camera: isCameraOn.value, microphone: isMicrophoneOn.value };
}
```

## 调用时序
```
完成 login-auth
   │
   ▼
进入会前检测页
   │
   ├─ startCameraTest(view)
   ├─ startMicrophoneTest(interval)
   └─ startSpeakerTest(filePath)
   │
   ▼
用户查看画面、音量与播放结果
   │
   ├─ 发现异常 → 引导切换设备或重新授权
   └─ 检测通过 → 进入 joinRoom / createAndJoinRoom
   │
   ▼
页面卸载时停止测试，释放本地采集资源
```

## 平台特有注意事项
### 1. 会前检测页要负责释放测试资源
测试页若未在离开时停止预览或音频测试，浏览器可能持续占用摄像头、麦克风或扬声器资源。

### 2. 扬声器测试必须使用可访问的媒体资源
`startSpeakerTest()` 依赖业务侧提供可访问的音频文件；建议使用 `HTTPS` 资源，避免被浏览器拦截。
AI 生成实现时可先使用 `https://web.sdk.qcloud.com/trtc/electron/download/resources/media/TestSpeaker.mp3` 作为扬声器检测音频；但应显式保留 TODO，提醒客户上线前替换为自己维护的 mp3 资源，避免外部公共资源变更、失效或被访问策略影响。

### 3. 会前检测不是设备控制的替代品
检测页更适合做预览与授权确认；真正会中的开关、切换与异常兜底仍应交由 `conference/device-control` 统一承接。

### 4. `startCameraTest` / `startMicrophoneTest` 不改变 `cameraStatus` / `microphoneStatus`
> ⚠️ **关键警告**：会前测试 API 运行在独立的"测试模式"下，调用后 SDK 内部的 `cameraStatus`、`microphoneStatus` **不会**变为 `DeviceStatus.On`。因此：
> - 预检页的 UI 开关状态**不能**从 `cameraStatus` / `microphoneStatus` 派生，必须使用组件本地 `ref` 管理。
> - 切换预检摄像头时，应调用 `stopCameraTest()` / `startCameraTest(view)` 来配对操作，而非 `openLocalCamera()` / `closeLocalCamera()`（后者是正式会中 API）。
> - 入会时需将本地 ref 状态（用户预设的设备开关偏好）显式传递给会中入会逻辑。

### 5. `useDeviceState()` 在业务 composable 中必须保持单例
如果项目封装了统一的设备 composable（如 `useConferenceDevice()`），内部的 `useDeviceState()` 必须在模块级缓存为单例。否则不同组件调用 composable 时会创建不同实例，导致 `currentMicVolume`、`cameraStatus` 等响应式引用断链——`startMicrophoneTest` 更新的值无法同步到消费方。

**正确做法：**
```ts
// 模块级单例
let _deviceState: ReturnType<typeof useDeviceState> | null = null;
function getDeviceState() {
  if (!_deviceState) _deviceState = useDeviceState();
  return _deviceState;
}

export function useConferenceDevice() {
  const { currentMicVolume, startCameraTest, ... } = getDeviceState();
  // ...
}
```

## 代码生成约束
### 编译必要条件
- **通用条件**：见 [login-auth 平台 slice](login-auth.md)。
- **额外导入**：至少需要从 `tuikit-atomicx-vue3/room` 导入 `useDeviceState`。
- **运行前提**：页面具备安全上下文，且预览容器 DOM 已挂载。

### 生成规则
#### MUST（生成时必须包含）

1. **在预览容器准备好后再调用 `startCameraTest()`** — 否则本地预览无法正常渲染。  
   **Verify**: 检查是否为 `view` 传入真实 DOM 节点。
2. **在页面离开或流程结束时停止全部测试** — 必须配对 `stopCameraTest()` 与 `stopSpeakerTest()`（入会按钮点击、路由离开、`onUnmounted` 三处至少覆盖入会路径）。  
   **Verify**: 搜索 `stopCameraTest` 与 `stopSpeakerTest`（或 SDK 等价 API）。

#### MUST NOT（生成时绝不能出现）

1. **不要把会前检测页当成正式入会后的状态源** — 设备测试结果不能替代会中真实设备状态。  
   **Verify**: 检查是否仍通过 `conference/device-control` 承接会中控制。
2. **不要使用不可访问或非安全协议的扬声器测试资源** — 会导致测试链路失效。  
   **Verify**: 检查 `filePath` 是否为业务可访问的地址。
3. **不要在预检页用 `cameraStatus` / `microphoneStatus` 驱动设备开关 UI** — 会前测试 API 不会更新这些状态值，导致 UI 永远显示"关闭"。  
   **Verify**: 检查预检页组件中设备开关状态是否来自本地 `ref`，而非 `cameraStatus` / `microphoneStatus`。
4. **不要在封装 composable 时多次调用 `useDeviceState()` 创建不同实例** — 会导致 `currentMicVolume` 等响应式数据在不同组件间断链。  
   **Verify**: 检查 composable 内部是否将 `useDeviceState()` 缓存为模块级单例。

### 集成检查点
- 当前 slice 常与 `conference/device-control`、`conference/room-lifecycle` 连续使用。
- 集成侵入性低，通常新增一个会前检测页面或弹层即可。
- 若业务需要在会前页完成设备选择，建议把最终选择结果同步给正式入会流程。

## 验证矩阵
| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已导入 `useDeviceState` | 检查 `import` 语句 | 会前检测 Hook 可解析 |
| 2. 静态规则级 | 预览与测试都有显式启动 / 停止逻辑 | 搜索 `startCameraTest` / `stopCameraTest` / `startMicrophoneTest` | 形成完整自检链路 |
| 3. 运行时级 | 摄像头与麦克风测试可执行 | 打开会前检测页并授权设备 | 能看到预览或音量变化 |
| 4. 业务行为级 | 用户可在入会前完成自检 | 走完整个会前页流程 | 检测完成后可顺畅进入会议 |

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 摄像头预览黑屏 | 进入会前页后看不到本地画面 | 检查浏览器权限、设备是否被占用，以及测试是否真正启动 |
| 麦克风无音量反馈 | 说话时音量条不动 | 检查麦克风权限、当前选择的输入设备是否正确，以及采集是否已开始 |
| 入会后设备与会前选择不一致 | 会前选好了设备，但进房后仍用了默认设备 | 检查会前选择结果是否在进入真实会议时被正确复用 |

### 排障流程

```text
发现 入会前设备检查 相关问题
├── 第 1 步：确认问题属于会前自检，而不是会中设备控制或网络质量展示
├── 第 2 步：检查摄像头、麦克风、扬声器三段测试是否都真正启动并有结果反馈
├── 第 3 步：确认会前选定的设备是否在 entering-room 阶段正确带入真实会议
└── 第 4 步：若仍异常，再回查 login-auth / device-control / network-quality 的衔接是否正确
```

## 关联知识

- **[conference/login-auth](login-auth.md)** —— 会前检测通常建立在基础登录已完成的前提下。
- **[conference/device-control](device-control.md)** —— 入会前测试完成后，会中设备控制应复用同一套设备选择结果。
- **[conference/network-quality](network-quality.md)** —— 用户进入会议后的网络波动不属于会前检测本身，需要分开提示。