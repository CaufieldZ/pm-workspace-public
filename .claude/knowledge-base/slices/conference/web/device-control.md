---
id: conference/device-control
name: 设备控制
product: conference
platform: web
tags: [device, camera, microphone, speaker, resolution, mirror]
platforms: [web]
related: [conference/prejoin-check, conference/participant-management, conference/network-quality, conference/video-layout]
api_docs:
  - title: 设备及网络
    url: https://cloud.tencent.com/document/product/647/126923
---

# 设备控制

## 功能说明

设备控制负责会议中的本地音视频设备使用与设置，覆盖摄像头、麦克风、扬声器的打开关闭、设备切换、音量调节、视频分辨率、本地镜像，以及权限拒绝、设备占用、无设备可用、受会中规则限制等异常处理。它解决的是“本机设备如何被正确使用”“当前为什么不能使用”“当前终端支持哪些设置项”“当前是否需要先做局部检查或预览”这类问题。入会前的完整设备检查主流程归属 `prejoin-check`；而会中设置面板、工具栏或异常恢复场景下的局部摄像头预览、麦克风音量检测、扬声器测试，也属于当前 slice 的能力范围。会中的全体禁用、成员设备关闭、设备申请和设备邀请等约束则与 `participant-management` 联动。

## 核心概念

### 角色与操作

| 角色 | 关键操作 | 说明 |
|------|----------|------|
| 当前参会人 | 开关设备、调整设置并执行局部检查 | 控制自己的摄像头、麦克风、扬声器，以及音量、分辨率、镜像等设置；也可在需要时做局部预览、音量检测和扬声器测试；设备受限时可发起申请或响应邀请 |
| 会控模块 | 限制或恢复设备能力 | 可通过全体禁用、关闭成员设备、设备申请和设备邀请等规则影响本地设备可用态 |
| 浏览器 / 系统 | 提供设备与权限能力 | 决定设备能否被访问，以及是否支持设备枚举、扬声器切换、音量调整、局部预览和测试等能力 |
| 设备设置界面 | 展示设备列表、设置项与能力边界 | 应根据当前终端能力裁剪设置项；能力完整的终端可提供更完整的音频和视频设置，能力受限的终端应只保留核心入口，并同步展示异常和受限原因 |
| 布局模块 | 感知设备开关结果 | 摄像头、麦克风和共享相关状态会进一步影响画面编排和挂件展示 |

### 事件流

| 阶段 | 参与方 | 关键动作 |
|------|--------|----------|
| 设备准备 | 浏览器 / 客户端 | 枚举摄像头、麦克风、扬声器等设备，并确认当前终端支持哪些设置项 |
| 局部检查 | 当前参会人 / 浏览器 | 在会前页或会中设置面板进行摄像头预览、麦克风音量检测或扬声器测试 |
| 权限与约束判断 | 浏览器 / 会控状态 | 判断是否具备浏览器权限、是否受会中规则限制，以及是否需要先申请或等待邀请 |
| 会中控制 | 当前参会人 | 开关、切换和调整设备设置；设备受限时发起申请或响应邀请 |
| 状态同步 | UI / 会控 / 布局 | 设备状态、受限原因和处理结果同步到工具栏、设置面板和画面展示 |
| 异常收口 | 浏览器 / 客户端 | 处理权限拒绝、设备占用、无设备可用、切换失败、不支持等场景 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| 摄像头 / 麦克风 / 扬声器列表 | 当前终端可选择的本地设备集合 |
| 当前设备选择 | 当前实际使用的摄像头、麦克风、扬声器标识 |
| 设备能力边界 | 表示当前终端是否支持设备切换、扬声器选择、音量调节、镜像或分辨率设置 |
| 本地设备开关状态 | 表示摄像头和麦克风当前是否处于开启状态 |
| 麦克风采集与发言状态 | 用于区分“设备已经开始采集”与“当前是否正在向房间发送音频”，也可支撑闭麦说话提醒 |
| 局部检查状态 | 包括摄像头预览状态、麦克风电平检测状态和扬声器测试状态 |
| 音频设置项 | 包括麦克风选择、扬声器选择、采集音量、播放音量和实时音量反馈 |
| 视频设置项 | 包括摄像头选择、前后置切换、视频分辨率、本地镜像和局部预览 |
| 分辨率档位策略 | 用于按弱网、多人成会、默认会议体验或高清场景提供不同清晰度选项 |
| 会中限制状态 | 表示是否被全体禁用、被管理员关闭，或需要先申请开启 |
| 设备异常状态 | 包括权限拒绝、占用冲突、设备不存在、浏览器不支持、切换失败等结果 |

### 状态机

```text
idle
  → enumerating-devices
  → ready
  → opening-device
  → active

active
  → changing-settings
  → muted-but-capturing
  → active

opening-device / changing-settings
  → restricted
  → blocked
  → failed
  → ready
```

## 前置条件
**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`

**前置状态**：
- 已阅读 `conference/device-control`，明确当前能力的产品边界。
- 已完成 `conference/login-auth`，确保当前页面具备稳定登录态。
- 已根据业务流程接入会议上下文；需要房间状态时，优先通过 `conference/room-lifecycle` 统一承接。
- 当前能力涉及媒体采集、渲染或浏览器权限时，请在 `HTTPS` 或 `localhost` 安全上下文下调试。

## 最佳实践

### ✅ ALWAYS

1. **把会前完整检查流程和会中设备控制拆成两段主链路** —— 会前主流程负责入会准备；会中仍可在设置面板、工具栏或异常恢复时做局部检查、预览和测试。
2. **区分麦克风采集状态和发言状态** —— 会议场景更推荐在用户成功进房后先完成本地麦克风采集准备，并默认保持静音；之后“开麦 / 闭麦”主要控制音频是否上行，而不是频繁打开和关闭物理麦克风采集。这样既能减少开麦时重新处理设备采集带来的延迟，也便于结合实时音量反馈实现闭麦说话提醒。
3. **根据当前终端能力裁剪设备设置项** —— 能力完整的终端可提供设备列表、扬声器切换、音量、分辨率和镜像设置；能力受限的终端只保留开关、前后置切换和少量分辨率等核心入口。
4. **按音频设置和视频设置组织面板** —— 音频侧重点是设备选择、音量和音量反馈；视频侧重点是摄像头选择、分辨率、镜像和局部预览。
5. **把设备列表、当前选择和工具栏状态放在同一份状态里维护** —— 切换设备、调节音量或修改分辨率后，设置面板和会中入口应看到一致结果；切换失败时应保留原设备并给出提示。
6. **按场景提供清晰度档位** —— 弱网、多人成会或小窗场景可优先低档位；默认会议体验可使用中高档位；高清主讲场景再提供更高分辨率选项。
7. **把设备受限原因和恢复路径一起展示** —— 当设备因 `disableAllDevices` 触发的房间级禁用而不可开时，这类限制通常只作用于普通成员；设备 icon 应表现为 disabled，并在用户点击时按产品需要提供申请开启入口。若设备只是被房主或管理员单独关闭，则应通过 toast 等方式明确告知结果，但只要没有房间级禁用，成员仍可再次主动开启本地设备。
8. **把设备异常直接映射成可执行提示** —— 权限拒绝、设备占用、无设备可用、浏览器不支持、切换失败等情况都应告诉用户下一步该怎么做。

### ❌ NEVER

1. **不要把会中的“开麦 / 闭麦”直接等同于频繁开关物理麦克风** —— 释放物理设备更适合离房、结束会议或明确需要停止采集的场景。
2. **不要在能力受限的终端强行展示完整设备设置** —— 麦克风列表、扬声器切换或复杂设置项在部分终端上可能并不成立。
3. **不要把“打不开设备”一律解释成浏览器或系统问题** —— 还应排查是否被全体禁用、被管理员关闭，或需要先发起设备申请。
4. **不要假设设备列表和设备切换永远可用** —— 浏览器兼容性、热插拔、系统限制和切换失败都需要单独收口。
5. **不要把网络波动、设备异常和会控限制混成同一类问题** —— 设备权限、设备状态和网络质量应分别判断，避免误导排障方向。
6. **不要在离房、结束会议或页面销毁后遗留采集状态** —— 避免摄像头常亮、麦克风仍被占用或下一场会议沿用脏状态。

### 会议中的麦克风控制推荐采用"进房后预静音 + 建立采集"
- 用户成功进入房间后，先调用 `muteMicrophone()`，先把本地音频上行状态收口为静音。
- 随后调用 `openLocalMicrophone()` 建立本地麦克风采集，保持本地已采集但默认不向远端发送音频。
- 用户点击"打开麦克风"时，调用 `unmuteMicrophone()` 恢复音频上行。
- 用户点击"关闭麦克风"时，调用 `muteMicrophone()` 停止音频上行。
- 只有在离房、结束会议或明确要释放设备时，再调用 `closeLocalMicrophone()`。

这里要特别区分：**麦克风需要把"是否采集"和"是否上行"拆开处理，但摄像头通常不需要照搬这套模型。**
- 摄像头在大多数会议产品里，直接用 `openLocalCamera()` / `closeLocalCamera()` 控制开启与关闭即可。
- 如果业务要求"入会默认不开摄"，应明确调用 `closeLocalCamera()` 收口摄像头关闭状态；当用户点击开摄时再调用 `openLocalCamera()`。
- 如果用户点击关摄，直接调用 `closeLocalCamera()` 释放本地摄像头采集即可，不需要类比成 `muteMicrophone()` / `unmuteMicrophone()` 这类"保留采集但停止上行"的用法。
- 只有在客户明确要求"摄像头预热但默认不展示 / 不上屏"这类特殊策略时，才需要单独评估是否做更复杂的摄像头状态编排；默认文档口径不要把摄像头推断成和麦克风同一套控制链路。

这样设计有两个直接收益：
- 用户开麦时无需重新处理物理设备采集，响应速度更快。
- 业务层可以持续结合 `currentMicVolume` 检测闭麦说话，并在合适时提示"您正在说话，是否打开麦克风？"。

## 代码示例
### 基础接入：打开摄像头、切换设备并在离场前关闭

```ts
import { useDeviceState, DeviceStatus } from 'tuikit-atomicx-vue3/room';

const {
  cameraStatus,
  openLocalCamera,
  closeLocalCamera,
  getCameraList,
  setCurrentCamera,
} = useDeviceState();

if (cameraStatus.value !== DeviceStatus.On) await openLocalCamera();
await getCameraList();
await setCurrentCamera({ deviceId: 'camera_device_id' });
await closeLocalCamera();
```

### 会议推荐：用 `cameraStatus` 驱动摄像头开关按钮

> ⚠️ 重要：`localParticipant.isCameraDisabled` 是管理员/会控禁用状态，**不**反映本地设备的实际开关。会中摄像头开关按钮状态必须来自 `cameraStatus`。

```ts
import { computed } from 'vue';
import { useDeviceState, useRoomParticipantState, DeviceStatus } from 'tuikit-atomicx-vue3/room';

const { cameraStatus, openLocalCamera, closeLocalCamera } = useDeviceState();

// ✅ 正确：用 cameraStatus 反映本地设备实际开关状态
const isCameraOff = computed(() => cameraStatus.value !== DeviceStatus.On);

// ❌ 错误示例（切勿使用）：
// const { localParticipant } = useRoomParticipantState();
// const isCameraOff = computed(() => Boolean(localParticipant.value?.isCameraDisabled));
// → isCameraDisabled 是管理员远程禁用标志，不跟随 openLocalCamera/closeLocalCamera 更新

export async function toggleCamera() {
  if (isCameraOff.value) {
    await openLocalCamera();   // 重新开启摄像头采集
  } else {
    await closeLocalCamera();  // 停止摄像头采集（离场时也应调用）
  }
}
```

### 会议推荐：进房后先静音，再建立麦克风采集

```ts
import { computed } from 'vue';
import { DeviceStatus, useDeviceState, useRoomParticipantState } from 'tuikit-atomicx-vue3/room';

const { microphoneStatus, openLocalMicrophone, currentMicVolume } = useDeviceState();
const { muteMicrophone, unmuteMicrophone } = useRoomParticipantState();

const isMicrophoneOn = computed(() => microphoneStatus.value === DeviceStatus.On);

export async function prepareMicrophoneAfterJoin() {
  await muteMicrophone();
  await openLocalMicrophone();
}

export async function handleClickOpenMicrophone() {
  await unmuteMicrophone();
}

export async function handleClickCloseMicrophone() {
  await muteMicrophone();
}

export function shouldPromptSpeakingWhileMuted() {
  return !isMicrophoneOn.value && currentMicVolume.value > 30;
}
```

## 调用时序
```
完成 login-auth 并进入会议
   │
   ▼
根据页面状态初始化本地设备
   │
   ├─ 摄像头需要开启 → openLocalCamera()
   ├─ 麦克风需要预采集 → muteMicrophone() → openLocalMicrophone()
   ├─ 需切换设备 → getCameraList() / getMicrophoneList() → setCurrent*(...)
   └─ 权限失败 → 展示错误并提示检查浏览器授权
   │
   ▼
用户点击"开麦" → unmuteMicrophone()
   │
   ├─ 检测到闭麦说话 → 可结合 currentMicVolume 给出提醒
   └─ 用户点击"闭麦" → muteMicrophone()
   │
   ▼
离场或明确释放设备时调用 closeLocalCamera() / closeLocalMicrophone()
```

## 平台特有注意事项
### 1. Web 采集设备必须运行在安全上下文
线上环境未启用 `HTTPS` 时，浏览器会直接拦截摄像头和麦克风采集；本地联调可使用 `localhost`。

### 2. 设备切换属于异步动作
切换摄像头、麦克风或扬声器时，建议在 UI 层提供 loading 或"切换中"反馈，避免用户连续点击造成状态错乱。

### 3. 设备错误应直接投射到 UI
摄像头或麦克风异常时，应把 `cameraLastError`、`microphoneLastError` 等状态及时映射成提示，而不是只在控制台打印。

### 4. 工具栏状态应以 AtomicX 状态为准
麦克风按钮应直接用 `useDeviceState().microphoneStatus === DeviceStatus.On` 判断当前是否开麦，再分别调用 `muteMicrophone()` / `unmuteMicrophone()`。自定义工具栏不要额外维护一个容易漂移的本地 `isMuted` 作为唯一事实源；如果业务需要本地 UI 状态，也应从 `microphoneStatus` 派生。

> ⚠️ **注意**：上述规则仅适用于**正式入会后**的会中场景。会前检测页（prejoin）使用的是 `startCameraTest` / `startMicrophoneTest`，这些测试模式 API **不会**更新 `cameraStatus` / `microphoneStatus`，因此预检页的设备 UI 状态必须用本地 `ref` 管理。详见 `conference/prejoin-check`。

### 5. `useDeviceState()` 在业务 composable 中必须保持单例
如果项目将设备操作封装为统一的 composable（如 `useConferenceDevice`），内部的 `useDeviceState()` 必须在模块级缓存为单例，**不能**在每次 composable 调用时重复执行 `useDeviceState()`。

**原因**：`useDeviceState()` 每次调用返回一组独立的响应式引用；如果在不同组件中通过 composable 各自创建了不同实例，`startMicrophoneTest` 更新的 `currentMicVolume` 只会写入调用发起方的实例，其他实例的 `currentMicVolume` 始终为 0。

**正确模式**：
```ts
let _state: ReturnType<typeof useDeviceState> | null = null;
function getDeviceState() {
  if (!_state) _state = useDeviceState();
  return _state;
}
export function useConferenceDevice() {
  const { currentMicVolume, cameraStatus, ... } = getDeviceState();
  // 所有消费方共享同一个响应式实例
}
```

### 5. 设备入口要区分"房间级禁用"和"成员级关闭"
如果当前是 `disableAllDevices` 触发的房间级禁用，这类限制通常只作用于普通成员；普通成员的设备 icon 应表现为 disabled，并在点击时通过 toast 或等价提示说明原因。是否继续允许用户通过 `requestToOpenDevice()` 申请开启，需要结合客户需求决定。若只是被房主或管理员单独关闭设备，则更适合提示"设备已被管理员关闭"，并允许用户在没有房间级禁用的前提下再次调用 `openLocalCamera()` 或 `unmuteMicrophone()` 主动恢复。

### 6. `iframe` 集成要显式放开媒体权限
如果会议页面运行在 `iframe` 内，宿主页面需要通过 `allow` 放开麦克风、摄像头、屏幕共享和全屏权限；否则即使业务代码正确，浏览器也可能直接拦截媒体采集或共享能力。

## 代码生成约束
### 编译必要条件
- **通用条件**：见 [login-auth 平台 slice](login-auth.md)。
- **额外导入**：至少需要从 `tuikit-atomicx-vue3/room` 导入 `useDeviceState`，按需导入 `DeviceStatus`、`DeviceError`。
- **运行前提**：浏览器具备设备权限，页面处于安全上下文。

### 生成规则
#### MUST（生成时必须包含）

1. **通过 `useDeviceState` 承接本地设备状态与操作** — 这样设备列表、状态与异常才能保持同源。  
   **Verify**: 检查是否存在 `useDeviceState()`。
2. **在切换设备前先获取设备列表或当前状态** — 否则 UI 容易对不存在的设备执行切换。  
   **Verify**: 检查是否存在 `getCameraList()` / `getMicrophoneList()` / 状态读取逻辑。
3. **会议场景下把"麦克风采集"与"音频上行"拆开处理，但不要把这套规则直接套到摄像头上** — 推荐进房后先 `muteMicrophone()`，再 `openLocalMicrophone()`；后续通过 `unmuteMicrophone()` / `muteMicrophone()` 响应开麦与闭麦。摄像头统一按 `openLocalCamera()` / `closeLocalCamera()` 直接控制开关。  
   **Verify**: 检查会议工具栏或入会初始化逻辑中，麦克风是否存在上述调用链，同时摄像头是否统一使用 `openLocalCamera()` / `closeLocalCamera()` 控制。

#### MUST NOT（生成时绝不能出现）

1. **不要在不满足安全上下文时默认开启媒体采集** — 浏览器会直接拒绝访问。  
   **Verify**: 检查代码或说明中是否明确 `HTTPS` / `localhost` 前提。
2. **不要只改 UI 开关，不调用真实设备接口** — 会出现按钮已开但本地流未变化的假状态。  
   **Verify**: 检查交互处理函数中是否实际调用 `open*` / `close*` / `setCurrent*`。
3. **不要把会中的"开麦 / 闭麦"实现成反复 `openLocalMicrophone()` / `closeLocalMicrophone()`** — 这样会增加重新采集延迟，也不利于闭麦说话提醒。  
   **Verify**: 检查工具栏开关逻辑是否优先使用 `muteMicrophone()` / `unmuteMicrophone()`。
4. **不要在封装 composable 时多次调用 `useDeviceState()` 创建独立实例** — 多实例会导致 `currentMicVolume`、`cameraStatus` 等响应式数据在组件间断链、无法同步。  
   **Verify**: 检查 composable 是否将 `useDeviceState()` 返回值缓存为模块级单例。
5. **不要在预检页（prejoin）用 `cameraStatus` / `microphoneStatus` 判断设备是否开启** — 会前测试 API 不更新这些字段。  
   **Verify**: 预检页组件中的设备 UI 状态是否来自独立的本地 `ref`。

### 集成检查点
- 当前 slice 常与 `conference/prejoin-check`、`conference/screen-share`、`conference/beauty-effects` 联动。
- 一般只需要新增设备面板或工具栏逻辑，不应侵入 SDK 内部采集实现。
- 如果业务已存在独立媒体层，需要明确由哪一层负责最终设备开关，避免双写状态。

## 验证矩阵
| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已导入 `useDeviceState` | 检查 `import` 语句 | 可正常解析设备 Hook |
| 2. 静态规则级 | UI 操作真实调用设备接口 | 搜索 `openLocalCamera` / `openLocalMicrophone` / `muteMicrophone` / `unmuteMicrophone` / `setCurrentCamera` | 至少一条真实设备调用链存在 |
| 3. 运行时级 | 设备开关与切换可执行 | 在浏览器授权后触发操作 | 摄像头状态可切换，麦克风可在静音与上行之间切换 |
| 4. 业务行为级 | 用户能感知权限、切换与闭麦说话提醒 | 在设置面板或工具栏执行操作 | UI 与实际设备状态保持一致，必要时可提示闭麦说话 |

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 麦克风已打开但别人听不到 | 本地看起来已开麦，但远端没有声音 | 检查当前是“已采集但未上行”还是设备根本未开启，并确认是否受会中禁言或设备限制 |
| 权限正常但设备仍打不开 | 浏览器已授权，按钮仍不可用或开启后立即失败 | 检查是否被全体禁用、被管理员关闭，或是否需要先发起设备申请 |
| 切换设备不生效 | 设置面板已选中新设备，但实际采集仍来自旧设备 | 检查当前设备选择是否真正更新，并确认切换失败时是否保留原设备和提示用户 |
| 扬声器测试或切换无效 | 听不到测试音，或切换输出设备后播放路径未变化 | 检查当前浏览器是否支持扬声器列表与切换；不支持时应引导用户使用系统声音设置 |
| 某些设置项缺失或不可用 | 看不到扬声器切换、完整设备列表或高级设置 | 先确认这是当前终端的能力边界，避免把兼容性差异误判为功能异常 |
| 离房后设备仍在运行 | 会议退出后摄像头灯仍亮或麦克风仍被占用 | 检查离房、结束房间和页面销毁路径是否统一关闭本地采集 |

### 排障流程

```text
发现 设备控制 相关问题
├── 第 1 步：确认问题属于会中设备控制或会中局部检查，而不是独立的会前检查主流程
├── 第 2 步：检查浏览器权限、设备可用性以及当前终端是否支持对应设置项
├── 第 3 步：确认当前是否存在全体禁用、管理员关闭、设备申请或设备邀请等会中限制
└── 第 4 步：若仍异常，再回查 prejoin-check / participant-management / network-quality / video-layout 的衔接是否正确
```

## 关联知识

- **[conference/prejoin-check](prejoin-check.md)** —— 入会前的完整设备检查主流程在这里定义；会中也可能存在局部检查和预览。
- **[conference/participant-management](participant-management.md)** —— 设备按钮可用态、管理员关闭设备和申请开启链路由这里约束。
- **[conference/network-quality](network-quality.md)** —— 网络问题和设备问题常被用户混淆，需要分层排查。
- **[conference/video-layout](video-layout.md)** —— 摄像头开关结果最终会影响画面布局和成员挂件展示。
