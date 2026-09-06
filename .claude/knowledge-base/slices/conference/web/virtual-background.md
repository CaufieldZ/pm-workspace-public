---
id: conference/virtual-background
name: 虚拟背景
product: conference
platform: web
tags: [virtual-background, blur, assetsPath, useVirtualBackgroundState]
platforms: [web]
related: [conference/device-control, conference/video-layout, conference/beauty-effects]
api_docs:
  - title: 虚拟背景
    url: https://cloud.tencent.com/document/product/647/126935
---

# 虚拟背景

## 功能说明

虚拟背景负责会议中本地视频的背景增强能力，包括背景虚化、图片替换、模型资源初始化、浏览器支持性检测以及从预览到正式生效的完整链路。与基础美颜相比，它更依赖模型资源、浏览器能力和初始化流程。

## 核心概念

### 角色与操作

| 角色 | 关键操作 | 说明 |
|------|----------|------|
| 当前参会人 | 选择背景模式 | 可以切换虚化、图片背景或关闭虚拟背景 |
| 虚拟背景面板 | 管理模式与预览 | 承载背景模式选择、资源初始化和确认保存入口 |
| 浏览器 / 模型运行时 | 提供支持能力 | 决定当前环境是否支持虚拟背景以及模型是否可初始化 |
| 本地视频处理链 | 应用背景效果 | 将保存后的背景设置作用到本地视频流 |

### 事件流

| 阶段 | 参与方 | 关键动作 |
|------|--------|----------|
| 支持性检测 | 浏览器 / 客户端 | 先确认当前环境是否支持虚拟背景 |
| 资源初始化 | 客户端 | 依据 `assetsPath` 等条件初始化背景模型资源 |
| 效果预览 | 当前参会人 | 选择虚化或图片背景，并在本地画面上实时预览 |
| 确认保存 | 当前参会人 | 将当前背景设置正式应用到会中视频流 |
| 降级回退 | 客户端 | 不支持或初始化失败时回退到普通视频能力 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| `isSupported` | 表示当前浏览器是否支持虚拟背景能力 |
| 初始化状态 | 标识模型资源是否已成功加载并可用 |
| `assetsPath` | Web 端初始化模型资源时的重要前置条件 |
| 当前背景模式 | 关闭、虚化、图片替换等模式 |
| 预览态 / 已保存态 | 区分当前面板中试用效果与真正对外生效的设置 |

### 状态机

```text
unsupported

idle
  → checking-support
  → initializing
  → previewing
  → saved
  → active
  → cleared
```

## 前置条件
**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`

**前置状态**：
- 已阅读 `conference/virtual-background`，明确当前能力的产品边界。
- 已完成 `conference/login-auth`，确保当前页面具备稳定登录态。
- 已根据业务流程接入会议上下文；需要房间状态时，优先通过 `conference/room-lifecycle` 统一承接。
- 当前能力涉及媒体采集、渲染或浏览器权限时，请在 `HTTPS` 或 `localhost` 安全上下文下调试。

## 最佳实践

### ✅ ALWAYS

1. **先做支持性检测，再开放设置入口** —— 不支持的环境应直接降级，而不是让用户在无效面板里反复尝试。
2. **把资源初始化作为显式前置步骤** —— `assetsPath`、模型资源和初始化结果应被明确管理。
3. **区分预览效果与正式保存结果** —— 让用户确认满意后再真正应用到会中画面。
4. **准备好不支持场景下的降级方案** —— 对不支持的浏览器应回到普通摄像头画面，而不是让视频链路中断。

### ❌ NEVER

1. **不要跳过初始化直接设置虚拟背景** —— 缺少模型资源时，效果很可能无法生效或表现异常。
2. **不要默认所有浏览器都支持相同能力** —— 虚拟背景的兼容性明显强依赖浏览器和环境。
3. **不要把虚拟背景与基础美颜混成同一份无边界的状态** —— 它们都作用于本地视频，但依赖与失败模式不同。

## 代码示例
### 初始化模型资源并保存虚拟背景效果

```ts
import { onMounted } from 'vue';
import { useVirtualBackgroundState } from 'tuikit-atomicx-vue3/room';

const { isSupported, initVirtualBackground, setVirtualBackground, saveVirtualBackground } = useVirtualBackgroundState();

onMounted(async () => {
  if (!isSupported()) return;
  await initVirtualBackground({ assetsPath: 'https://cdn.example.com/assets' });
  await setVirtualBackground({ enable: true, type: 'blur', level: 0.5 });
  await saveVirtualBackground();
});
```

## 调用时序
```
完成 login-auth 并准备本地视频
   │
   ▼
调用 isSupported() 检查浏览器能力
   │
   ├─ 不支持 → 隐藏入口或走降级文案
   └─ 支持
       │
       ▼
initVirtualBackground({ assetsPath })
       │
       ▼
setVirtualBackground(...) 做预览
       │
       ├─ 用户确认 → saveVirtualBackground()
       └─ 用户取消 / 关闭 → 回退或关闭背景效果
```

## 平台特有注意事项
### 1. `assetsPath` 是虚拟背景能否启动的关键前置条件
必须先成功初始化 `assetsPath` 对应的模型或资源目录，否则虚拟背景功能无法正常工作。

### 2. 兼容性检查必须放在渲染前
浏览器对虚拟背景的支持差异明显，建议在页面入口或打开设置面板前先调用 `isSupported()` 做能力判断。

### 3. 虚拟背景比基础美颜更吃性能
在低性能设备上，虚拟背景更容易带来 CPU / GPU 压力；业务应允许快速关闭，并提供清晰的降级说明。

## 代码生成约束
### 编译必要条件
- **通用条件**：见 [login-auth 平台 slice](login-auth.md)。
- **额外导入**：至少需要导入 `useVirtualBackgroundState`。
- **运行前提**：浏览器支持该能力、页面处于安全上下文，且 `assetsPath` 可访问。

### 生成规则
#### MUST（生成时必须包含）

1. **在启用虚拟背景前先做能力检查与初始化** — 否则会出现入口可见但能力不可用的假状态。  
   **Verify**: 检查是否存在 `isSupported()` 与 `initVirtualBackground(`。
2. **把预览与最终保存分开处理** — 用户需要有确认生效的动作，而不是一改即永久保存。  
   **Verify**: 检查是否同时存在 `setVirtualBackground(` 与 `saveVirtualBackground(`。

#### MUST NOT（生成时绝不能出现）

1. **不要跳过 `assetsPath` 初始化直接启用背景能力** — 功能无法正常启动。  
   **Verify**: 检查是否先调用 `initVirtualBackground({ assetsPath })`。
2. **不要忽略不支持浏览器的降级路径** — 低兼容环境会直接报错或白屏。  
   **Verify**: 检查是否存在 `isSupported()` 判断和降级处理。

### 集成检查点
- 当前 slice 常与 `conference/device-control`、`conference/beauty-effects` 联动。
- 集成方式通常是新增本地效果设置面板，不需要改动房间生命周期逻辑。
- 如果业务同时接入美颜和虚拟背景，建议在 UI 和性能策略上给出统一入口与优先级。

## 验证矩阵
| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已导入 `useVirtualBackgroundState` | 检查 `import` 语句 | 虚拟背景 Hook 可解析 |
| 2. 静态规则级 | 存在能力检查、初始化、保存链路 | 搜索 `isSupported` / `initVirtualBackground` / `saveVirtualBackground` | 形成完整启用流程 |
| 3. 运行时级 | 支持浏览器可成功启用背景效果 | 在支持环境打开虚拟背景功能 | 能看到预览并保存效果 |
| 4. 业务行为级 | 不支持或低性能环境有清晰降级 | 在不支持环境或低性能设备联调 | 页面能正确隐藏入口或提示降级 |

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 面板可打开但效果不可用 | 用户能看到背景设置入口，但切换后画面无变化 | 检查浏览器支持性检测和初始化是否真正成功 |
| 初始化失败 | 选择背景时直接报错或模型资源加载失败 | 检查 `assetsPath`、资源可访问性以及初始化时机是否正确 |
| 保存后效果丢失 | 当前会议里可见，重新进入面板或再次开会后失效 | 检查预览态和已保存态是否区分维护，并确认初始化完成后再恢复设置 |

### 排障流程

```text
发现 虚拟背景 相关问题
├── 第 1 步：确认当前环境是否支持虚拟背景，不支持时应直接走降级路径
├── 第 2 步：检查 assetsPath 和模型初始化流程是否完整且已成功完成
├── 第 3 步：确认当前背景设置是否仍停留在预览态，还是已经正式保存到视频流
└── 第 4 步：若仍异常，再回查 device-control / video-layout / beauty-effects 的衔接是否正确
```

## 关联知识

- **[conference/device-control](device-control.md)** —— 摄像头是否已准备好会直接影响虚拟背景是否具备可视化预览前提。
- **[conference/video-layout](video-layout.md)** —— 背景效果最终体现为布局中的本地画面变化。
- **[conference/beauty-effects](beauty-effects.md)** —— 与虚拟背景同属本地视频前处理，但初始化要求和失败模式不同。