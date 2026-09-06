---
id: conference/video-layout
name: 视频布局
product: conference
platform: web
tags: [layout, RoomView, layoutTemplate, participantViewUI, focus, screen-share, mobile-layout]
platforms: [web]
related: [conference/screen-share, conference/participant-list, conference/room-lifecycle, conference/device-control]
api_docs:
  - title: 视频布局
    url: https://cloud.tencent.com/document/product/647/126921
---

# 视频布局

## 功能说明

视频布局负责会议页面中视频区域的整体编排，核心关注点包括：房间级视频容器如何渲染、布局模板如何切换、谁应该成为主画面、屏幕共享出现时如何突出展示、单画面挂件如何叠加、移动端如何分页和适配，以及用户对画面的双击聚焦如何与默认规则协同。

它消费房间、成员和共享状态，但**不负责**创建或加入房间，也不负责打开摄像头、麦克风或管理成员权限。通用会议里，它通常作为 `room-lifecycle`、`participant-list`、`screen-share`、`device-control` 之上的“画面呈现层”。

## 核心概念

### 角色与操作

| 角色 | 关键操作 | 说明 |
|------|----------|------|
| 当前参会人 | 浏览画面、切换布局、双击聚焦 | 根据会议形态选择宫格或主画面布局，并对当前关注对象做聚焦 |
| 房间级布局容器 | 负责编排整个视频区域 | 决定宫格、主画面、侧边栏、移动端分页等房间级布局结果 |
| 单画面挂件层 | 叠加昵称、角色、设备态等信息 | 基于成员状态和流类型为每一路画面增加业务 UI |
| 共享状态来源 | 驱动主画面切换 | 屏幕共享开始、结束通常是主画面和布局模板变更的关键触发器 |
| 业务页面容器 | 提供实际展示空间 | 视频区域需要与成员列表、底部工具栏、会中聊天等共同组成完整会议页 |

### 布局模板

| 布局类型 | 适用场景 | 典型表现 |
|----------|----------|----------|
| 宫格布局 | 多人讨论、日常会议、面试 | 多路画面均衡展示，适合常规视频会议 |
| 顶部栏布局 | 演示、培训、共享讲解 | 主画面突出，其他成员画面位于顶部 |
| 侧边栏布局 | 主讲人模式、汇报场景 | 主画面突出，其他成员画面位于侧边 |
| 移动端布局 | H5 或小屏终端会议页 | 优先保证主画面可读性，并兼顾分页、滑动和共享场景适配 |

### 标准布局与自定义布局分工

| 方式 | 适用场景 | 说明 |
|------|----------|------|
| 房间级布局容器 | 通用会议、常规会中页面 | 更适合承接房间内所有参与者流的排序、播放、布局排版和缩放处理，并统一消费共享状态和焦点状态 |
| 单路原子播放器 | 完全自定义布局、业务强定制场景 | 更适合按业务需要逐路拼装指定流，由外层决定每一路画面的大小、比例和排布方式 |

### 状态与数据

| 数据 / 状态 | 说明 |
|-------------|------|
| 当前布局模板 | 表示当前使用宫格、顶部栏、侧边栏或移动端布局 |
| 主画面焦点 | 当前被放大的成员画面或屏幕共享画面 |
| `participantList` | 当前房间内可参与布局编排的成员集合 |
| `participantWithScreen` | 当前正在屏幕共享的成员信息 |
| 画面流类型 | 用于区分摄像头流和屏幕共享流，决定挂件展示方式 |
| 挂件状态 | 包括昵称、角色、麦克风、摄像头、业务标签等叠加信息 |
| 可视区域与分页状态 | 决定哪些画面当前可见，以及是否需要分页或懒加载 |
| 布局交互状态 | 例如双击聚焦、共享结束后的回退、切房后的清空 |

### 编排规则

| 规则 | 说明 |
|------|------|
| 默认排序参考 | 多数会议布局会优先考虑：屏幕共享流、房主、本地用户、管理员、音视频都开启的成员、仅开启摄像头的成员、仅开启麦克风的成员 |
| 双击聚焦优先 | 用户主动双击某一路画面后，该画面通常应优先成为当前关注对象 |
| 默认主画面回退 | 当聚焦对象失效、共享结束或成员离开时，需要回退到“共享优先、再看普通视频画面、最后兜底本地用户”的默认规则 |
| 摄像头流与共享流分治 | 摄像头画面适合展示成员挂件；共享画面更适合展示“正在共享”类信息 |
| 非可视区域按需渲染 | 多路画面场景下，非当前可视区域通常不需要持续高成本渲染 |
| 小画面优先轻量策略 | 多数布局会优先保障主画面和共享画面的清晰度，小画面采用更轻量的展示策略 |

## 前置条件
**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`

**前置状态**：
- 已阅读 `conference/video-layout`，明确当前能力的产品边界。
- 已完成 `conference/login-auth`，确保当前页面具备稳定登录态。
- 已根据业务流程接入会议上下文；需要进房状态时，优先通过 `conference/room-lifecycle` 统一承接。
- 承载 `RoomView` 的父容器必须具备明确宽高，否则视频区域无法正确计算布局。

## 最佳实践

### ✅ ALWAYS

1. **把房间级布局和单画面挂件分层设计** —— 房间级容器负责整体编排，挂件层只负责单路信息叠加。
2. **让布局由状态驱动，而不是由零散 DOM 操作驱动** —— 成员列表、共享状态、焦点状态和平台能力都应该成为布局切换依据。
3. **通用会议优先使用房间级布局容器，自定义布局再下沉到单路播放器** —— 通用会议更适合复用内置排序、播放、缩放和布局编排；只有在布局自由度明显超出通用会议能力时，再采用逐路播放器自行拼装。
4. **为屏幕共享保留明确优先级和回退规则** —— 通用会议通常在有共享时切到主画面布局，无共享或房间内仅一人时回到宫格，避免主画面悬空。
5. **区分摄像头流与屏幕共享流的展示语义** —— 共享画面不应机械复用摄像头挂件。
6. **显式处理用户主动聚焦与系统默认排序的关系** —— 双击聚焦、共享优先、成员离场三者之间需要清晰优先级。
7. **针对移动端单独考虑布局策略** —— 小屏场景更关注主画面可读性、分页体验和共享可视性，而不是照搬桌面端布局。
8. **接受布局容器的懒加载和画质分层特性** —— 不要把“非可视区域不持续播放”或“小画面优先轻量策略”误判为异常。
9. **在离房、切房和页面销毁时清空布局态** —— 避免上一场会议的聚焦对象、共享状态和布局模板残留。

### ❌ NEVER

1. **不要把完整会议页与视频布局容器混为一体** —— 视频布局只是一层能力，不应吞掉成员列表、会控、聊天等其他模块。
2. **不要把共享状态、成员状态和布局状态塞进同一份不可追踪的本地变量** —— 这些状态来源不同，应该保持边界清晰。
3. **不要忽略用户主动聚焦后的失效回退** —— 被聚焦成员离场、关摄像头或共享结束后，主画面必须能回退。
4. **不要把所有挂件都当成可点击覆盖层默认铺满画面** —— 这会破坏布局容器原有交互和展示语义。
5. **不要跨平台硬套同一套布局策略** —— 桌面端的宫格 / 主画面逻辑和移动端分页逻辑应分别设计。

### 1. 没给布局要求时直接用 `RoomView`，超出支持范围再切 `RoomParticipantView`
如果客户没有明确给到布局信息，或者只是提出常规会议布局诉求，最佳实践就是直接使用 `RoomView` 作为视频区域主容器。它已经承接了房间内参与者流的排序、播放、布局排版和缩放处理，成员列表、底部工具栏、聊天面板、业务弹窗等仍应由业务页面自行组合。

以下诉求通常**仍属于 `RoomView` 可覆盖范围**：
- 只是在 `GridLayout`、`CinemaLayout`、`SidebarLayout`、`MobileLayout` 之间选择或切换。
- 只是在画面上叠加昵称、角色、共享标识等挂件 UI。
- 只需要响应双击聚焦，或者根据共享状态、人数变化自动切换布局。

以下诉求通常可以判断为**超出 `RoomView` 支持范围**：
- 客户明确指定某一路流必须固定在某个区域，或要求每一路画面的大小、位置、层级都由业务自己决定。
- 视频区需要和白板、文档、字幕、AI 面板等业务模块做深度交错排版，而不是只在 `RoomView` 外围组合页面。
- 需要非标准布局编排，无法落在 `GridLayout`、`CinemaLayout`、`SidebarLayout`、`MobileLayout` 这些既有模板内。
- 需要业务侧自己接管主画面选择、排序或分区编排逻辑，而不是沿用 `RoomView` 的内置规则。

只有当客户明确提出了这类 `RoomView` 无法承接的布局诉求时，才建议切到 `RoomParticipantView` 这类单路播放原子组件逐路拼装。此时组件尺寸由外层布局决定，通常建议外层优先保持接近 `16:9` 的宽高比例，避免出现过度裁切或留白。

如果最终选择 `RoomParticipantView`，就需要在方案、文档或生成代码说明里**明确指明超出点**：至少写清楚是哪一条布局诉求超出了内置模板、挂件扩展或默认交互能力；如果说不清，默认就先用 `RoomView`。

### 2. 通用会议中让布局切换跟随共享和人数变化
- 有屏幕分享时，推荐自动切到 `RoomLayoutTemplate.SidebarLayout`，突出共享主画面。
- 没有屏幕分享，或者房间内仅有一个人的时候，推荐自动切回 `RoomLayoutTemplate.GridLayout`。
- 如果业务还提供手动切布局入口，建议让手动选择和这套默认回退规则保持一致。

### 3. PC 与 H5 使用不同布局策略
- PC Web 通用会议的常用布局主要是 `GridLayout`、`CinemaLayout`、`SidebarLayout`。
- H5 页面优先使用 `MobileLayout`，不要直接照搬桌面端布局。
- 屏幕共享开始时，PC 常见做法是切到 `SidebarLayout`；H5 通常继续使用 `MobileLayout`。

### 4. 把挂件定制放到 `participantViewUI`，并区分摄像头流与共享流
同一个挂件模板不应该机械复用于所有画面。共享流更适合展示“正在共享屏幕”等信息，摄像头流更适合展示昵称、角色和设备状态。

当成员关闭摄像头时，**不要让摄像头画面只剩纯黑底**。推荐继续复用 `participantViewUI` 在挂件层叠加“头像 + 用户名”的占位态，让关闭摄像头后的 tile 仍然可识别。这个占位态只应用在摄像头流上，不要覆盖共享流。

如果**本地用户已经开启屏幕分享，但本地共享 tile 不展示真实预览或表现为黑底**，也推荐在共享流上给一个居中的“正在共享屏幕”示例态，例如：图标 + 状态文案 + “结束共享”操作。这里的视觉样式只是示例，不是固定 UI 规范；业务可以替换成更轻的提示条、品牌化插画或其他表达方式，关键是不要让本地共享态只剩无语义的黑屏。

另外要注意本地用户和远端用户的判断口径不同：
- **远端用户摄像头流**：可以用 `participant.cameraStatus !== DeviceStatus.On` 判断是否显示占位层。
- **本地用户摄像头流**：不要直接依赖成员列表里的本地摄像头字段，应读取 `useDeviceState().cameraStatus` 判断本地摄像头是否关闭。
- **本地用户共享流**：可结合 `participantWithScreen` 与 `localParticipant` 判断当前共享者是否是自己，再决定是否展示本地共享提示态。

### 5. 避免挂件层拦截默认交互
如果挂件只是展示信息，优先给挂件容器设置 `pointer-events: none`，避免影响默认双击、拖拽或移动端手势。

## 布局能力矩阵

| 布局 | 枚举值 | 适用端 | 推荐场景 | 关键说明 |
|------|--------|--------|----------|----------|
| 宫格布局 | `RoomLayoutTemplate.GridLayout` | PC Web | 多人讨论、常规会议、视频面试 | 默认布局；单页通常最多展示 9 路，超过后通过翻页查看 |
| 顶部栏布局 | `RoomLayoutTemplate.CinemaLayout` | PC Web | 培训、演示、共享讲解 | 主画面居中突出，其他成员画面位于顶部 |
| 侧边栏布局 | `RoomLayoutTemplate.SidebarLayout` | PC Web | 主讲人模式、汇报场景 | 主画面居中突出，其他成员画面位于侧边 |
| 移动端布局 | `RoomLayoutTemplate.MobileLayout` | H5 | 移动端会议页 | 更强调主画面、滑动分页；共享场景下通常继续沿用该布局 |

## 代码示例
### 基础接入：渲染 `RoomView` 并选择布局模板

```vue
<template>
  <div class="room-view-wrapper">
    <RoomView :layout-template="currentLayout" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { RoomLayoutTemplate, RoomView } from 'tuikit-atomicx-vue3/room';

const currentLayout = ref(RoomLayoutTemplate.GridLayout);
</script>

<style scoped>
.room-view-wrapper {
  width: 100%;
  height: 100%;
}
</style>
```

### 自定义挂件：通过 `participantViewUI` 展示昵称、角色和“关摄像头占位层”

```vue
<template>
  <div class="room-view-wrapper">
    <RoomView :layout-template="currentLayout">
      <template #participantViewUI="{ participant, streamType }">
        <div class="participant-view-ui">
          <div
            v-if="showCameraPlaceholder(participant, streamType)"
            class="camera-placeholder"
          >
            <span
              class="camera-placeholder__avatar"
              :style="participant.avatarUrl ? { backgroundImage: `url(${participant.avatarUrl})` } : {}"
            >
              {{ getDisplayName(participant).charAt(0) }}
            </span>
            <span class="camera-placeholder__name">{{ getDisplayName(participant) }}</span>
          </div>

          <div class="participant-view-ui__footer">
            <span class="name">{{ getDisplayName(participant) }}</span>
            <span v-if="streamType === VideoStreamType.Screen" class="tag">正在共享屏幕</span>
            <span v-else class="tag">{{ participant.role }}</span>
          </div>
        </div>
      </template>
    </RoomView>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import {
  DeviceStatus,
  RoomLayoutTemplate,
  RoomView,
  VideoStreamType,
  useDeviceState,
  useRoomParticipantState,
  type RoomParticipant,
} from 'tuikit-atomicx-vue3/room';

const currentLayout = ref(RoomLayoutTemplate.GridLayout);
const { cameraStatus } = useDeviceState();
const { localParticipant } = useRoomParticipantState();

function getDisplayName(participant: RoomParticipant) {
  return participant.nameCard || participant.userName || participant.userId;
}

function showCameraPlaceholder(participant: RoomParticipant, streamType: VideoStreamType) {
  if (streamType === VideoStreamType.Screen) {
    return false;
  }

  if (participant.userId === localParticipant.value?.userId) {
    return cameraStatus.value !== DeviceStatus.On;
  }

  return participant.cameraStatus !== DeviceStatus.On;
}
</script>

<style scoped>
.room-view-wrapper {
  width: 100%;
  height: 100%;
}

.participant-view-ui {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 12px;
  color: #fff;
  pointer-events: none;
}

.camera-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.camera-placeholder__avatar {
  width: 56px;
  height: 56px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgb(255 255 255 / 20%);
  background-position: center;
  background-size: cover;
  font-size: 20px;
  font-weight: 600;
}

.camera-placeholder__name,
.name {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.participant-view-ui__footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgb(0 0 0 / 50%);
}
</style>
```

> 如果业务不需要大面积占位层，也可以只保留底部昵称条；但只要产品要求“关闭摄像头后不要黑块”，就应该至少补一个可识别的头像 / 名称占位态。

### 本地共享提示：共享流本地预览为黑底时，用示例化状态面板替代裸黑屏

```vue
<template>
  <div class="room-view-wrapper">
    <RoomView :layout-template="currentLayout">
      <template #participantViewUI="{ participant, streamType }">
        <div class="participant-view-ui">
          <div
            v-if="showLocalScreenSharePlaceholder(participant.userId, streamType)"
            class="screen-share-placeholder"
          >
            <div class="screen-share-placeholder__icon" aria-hidden="true"></div>
            <div class="screen-share-placeholder__title">您正在共享屏幕…</div>
            <button
              class="screen-share-placeholder__action"
              type="button"
              @click.stop="handleStopScreenShare"
            >
              结束共享
            </button>
          </div>
        </div>
      </template>
    </RoomView>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import {
  RoomLayoutTemplate,
  RoomView,
  VideoStreamType,
  useDeviceState,
  useRoomParticipantState,
} from 'tuikit-atomicx-vue3/room';

const currentLayout = ref(RoomLayoutTemplate.SidebarLayout);
const { stopScreenShare } = useDeviceState();
const { localParticipant, participantWithScreen } = useRoomParticipantState();

function showLocalScreenSharePlaceholder(
  participantUserId: string,
  streamType: VideoStreamType,
) {
  return (
    streamType === VideoStreamType.Screen &&
    participantUserId === localParticipant.value?.userId &&
    participantWithScreen.value?.userId === localParticipant.value?.userId
  );
}

async function handleStopScreenShare() {
  await stopScreenShare();
}
</script>

<style scoped>
.room-view-wrapper {
  width: 100%;
  height: 100%;
}

.participant-view-ui {
  position: absolute;
  inset: 0;
  display: flex;
  pointer-events: none;
}

.screen-share-placeholder {
  margin: auto;
  min-width: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 20px;
  border-radius: 20px;
  background: rgb(255 255 255 / 82%);
  color: #666;
  text-align: center;
  pointer-events: auto;
}

.screen-share-placeholder__icon {
  width: 48px;
  height: 32px;
  border: 2px solid currentColor;
  border-radius: 6px;
  position: relative;
}

.screen-share-placeholder__icon::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -10px;
  width: 12px;
  height: 8px;
  border: 2px solid currentColor;
  border-top: 0;
  border-left: 0;
  transform: translateX(-50%) rotate(45deg);
}

.screen-share-placeholder__title {
  font-size: 16px;
  font-weight: 500;
}

.screen-share-placeholder__action {
  border: 0;
  border-radius: 999px;
  padding: 8px 16px;
  background: #e65b4e;
  color: #fff;
}
</style>
```

> 这个面板只是示例化占位，不要求所有项目都做成同样的灰底居中卡片；你可以只保留文案，也可以把“结束共享”留在工具栏，只要让本地共享态不再是无语义黑屏即可。

### 状态驱动：共享开始时切到侧边栏，无共享或单人时回到宫格

```ts
import { computed, ref, watch } from 'vue';
import {
  RoomLayoutTemplate,
  useRoomParticipantState,
} from 'tuikit-atomicx-vue3/room';

const currentLayout = ref(RoomLayoutTemplate.GridLayout);
const { participantList, participantWithScreen } = useRoomParticipantState();

const participantCount = computed(() => participantList.value.length);

watch(
  [participantWithScreen, participantCount],
  ([screenParticipant, count]) => {
    if (screenParticipant) {
      currentLayout.value = RoomLayoutTemplate.SidebarLayout;
      return;
    }

    if (count <= 1) {
      currentLayout.value = RoomLayoutTemplate.GridLayout;
      return;
    }

    currentLayout.value = RoomLayoutTemplate.GridLayout;
  },
  { immediate: true },
);
```

### 交互回调：监听 `stream-double-click` 同步业务 UI 状态

```vue
<template>
  <div class="room-view-wrapper">
    <RoomView
      :layout-template="currentLayout"
      @stream-double-click="handleStreamDoubleClick"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import {
  RoomLayoutTemplate,
  RoomView,
  type VideoStreamType,
  type RoomParticipant,
} from 'tuikit-atomicx-vue3/room';

const currentLayout = ref(RoomLayoutTemplate.SidebarLayout);
const focusedStream = ref<string>('');

function handleStreamDoubleClick(payload: {
  participant: RoomParticipant;
  streamType: VideoStreamType;
}) {
  focusedStream.value = `${payload.participant.userId}:${payload.streamType}`;
}
</script>

<style scoped>
.room-view-wrapper {
  width: 100%;
  height: 100%;
}
</style>
```

## 调用时序
```
完成 login-auth 并进入会议
   │
   ▼
为 RoomView 准备有明确宽高的父容器
   │
   ▼
根据当前平台选择初始 layoutTemplate
   │
   ├─ PC 常规会议 → GridLayout
   ├─ PC 共享 / 主讲场景 → SidebarLayout / CinemaLayout
   └─ H5 页面 → MobileLayout
   │
   ▼
渲染 RoomView，并按需接入 participantViewUI / stream-double-click
   │
   ▼
监听 participantWithScreen、成员状态和业务焦点变化
   │
   ├─ 共享开始 → 切主画面布局
   ├─ 共享结束 → 回退到默认布局
   └─ 双击画面 → 同步业务侧焦点态或辅助 UI
   │
   ▼
离房或销毁页面时清理布局相关本地状态
```

## 平台特有注意事项
### 1. 父容器尺寸是 `RoomView` 正常工作的前提
如果外层容器宽高为 `0`，布局和画面渲染都会异常；这通常不是 SDK 本身的问题，而是页面容器没有被正确撑开。

### 2. `RoomView` 不负责进房和开关设备
如果页面没有画面，先检查是否已经进房，以及本地 / 远端是否真的存在可展示的视频或共享流，而不是只盯着布局组件本身。

### 3. 布局切换必须使用 `RoomLayoutTemplate` 枚举
不要手写字符串，也不要让 PC 使用 `MobileLayout`，或让 H5 强行复用桌面端宫格 / 顶部栏 / 侧边栏布局。

### 4. 共享画面和摄像头画面的挂件语义不同
共享流更适合展示“正在共享屏幕”等状态；摄像头流更适合展示昵称、角色、设备态和业务标签。

### 5. 只有明确超出 `RoomView` 能力边界时，才改用 `RoomParticipantView`
如果客户没有提出特殊布局要求，或者需求本身仍可落在 `RoomView` 的既有布局能力里，就不要过早切到单路播放器方案。只有在业务明确要求自己决定每一路流放在哪里、占多大区域、如何与其他业务模块交错排布时，才更适合使用 `RoomParticipantView` 这类单路播放组件逐路拼装。此时建议优先由外层容器控制宽高比例，通常保持接近 `16:9` 更利于常规摄像头和共享画面的展示。

### 6. 不要破坏 `RoomView` 的可视区域判断
多路画面场景下，非可视区域通常按需渲染，小画面也会采用更轻量的展示策略；自定义样式不应破坏其容器尺寸和可视区域计算。

### 7. H5 重点关注移动端手势和分页体验
`MobileLayout` 更关注主画面可读性、滑动分页和共享场景适配；移动端页面不建议强行复用桌面端的宫格或主讲布局思路。

## RoomView 内置行为

### 默认排序参考

| 优先级 | 排序因素 | 说明 |
|--------|----------|------|
| 1 | 屏幕共享流 | 有共享时，共享画面通常优先进入视频流列表 |
| 2 | 房主 | 房主画面优先级较高 |
| 3 | 本地用户 | 本地用户通常具有较高展示优先级 |
| 4 | 管理员 | 管理员画面优先于普通成员 |
| 5 | 摄像头和麦克风都开启 | 音视频都活跃的成员优先 |
| 6 | 仅开启摄像头 | 有视频画面的成员优先于仅音频成员 |
| 7 | 仅开启麦克风 | 只有音频状态的成员次之 |

> `RoomView` 会基于这些规则继续处理房间内参与者流的播放、布局排版和缩放。通用会议通常不需要业务侧自行重排；如果客户没有明确提出超出其能力边界的布局诉求，就应优先继续使用 `RoomView`。只有布局要求已经超出其支持范围时，才更适合改用 `RoomParticipantView` 一类单路组件自行组织。

### 主画面选择参考

| 场景 | 选择规则 |
|------|----------|
| 宫格布局 | 通常不强调单独主画面，而是按分页展示当前页画面 |
| 顶部栏 / 侧边栏布局 | 优先展示用户双击聚焦的画面；否则展示屏幕共享；再否则展示首个适合放大的视频画面；最后兜底本地用户 |
| 移动端布局 | 优先保障共享或主要画面的可读性，多人场景通过分页组织其余画面 |

### 渲染策略
- 非可视区域的远端画面通常按需渲染，不需要误判为播放异常。
- 小窗口和边栏画面通常会采用更轻量的展示策略，主画面和共享画面优先保证体验。

## 代码生成约束
### 编译必要条件
- **通用条件**：见 [login-auth 平台 slice](login-auth.md)。
- **额外导入**：常规场景至少需要导入 `RoomView` 与 `RoomLayoutTemplate`；按需导入 `VideoStreamType`、`useRoomParticipantState`；只有在明确超出 `RoomView` 布局能力时，才额外导入 `RoomParticipantView`。
- **运行前提**：页面已经进入会议流程，且 `RoomView` 父容器具备明确宽高。

### 生成规则
#### MUST（生成时必须包含）

1. **客户未明确提出特殊布局时，默认以 `RoomView` 作为视频区域主容器** — 这是通用会议和常规布局诉求的最佳实践。  
   **Verify**: 检查常规会议场景是否优先存在 `RoomView` 渲染节点。
2. **显式为 `RoomView` 的父容器设置宽高** — 否则布局无法正常计算。  
   **Verify**: 检查外层容器是否存在 `width` / `height` 样式。
3. **使用 `RoomLayoutTemplate` 枚举管理布局模板** — 这样 PC 与 H5 的布局策略才可控。  
   **Verify**: 检查是否存在 `RoomLayoutTemplate.GridLayout` / `SidebarLayout` / `CinemaLayout` / `MobileLayout`。
4. **挂件扩展优先走 `participantViewUI` 插槽** — 这样挂件能跟随成员和流类型状态同步更新。  
   **Verify**: 检查是否存在 `participantViewUI` 插槽或等价扩展点。
5. **需要响应画面交互时，优先监听 `stream-double-click`** — 用于同步业务侧焦点态或辅助交互。  
   **Verify**: 检查是否绑定了 `@stream-double-click` 或等价处理逻辑。
6. **共享场景下通过 `participantWithScreen`、成员人数等状态驱动布局切换** — 不要用硬编码定时器或手工 DOM 调整主画面。  
   **Verify**: 检查是否读取共享状态和成员数量，并在共享时切到 `SidebarLayout`、无共享或单人时回到 `GridLayout`。
7. **只有明确超出 `RoomView` 支持范围时，才切到单路播放组件** — 当业务不再采用通用会议布局容器，而是要自行决定每一路画面的尺寸、比例和排布时，再由外层接管布局。  
   **Verify**: 检查自定义布局方案是否先说明了 `RoomView` 不能满足的点，并补充单路组件的尺寸约束，且优先保持接近 `16:9` 的画面比例。

#### MUST NOT（生成时绝不能出现）

1. **不要把 `RoomView` 当成完整会议页面组件** — 它不承载成员列表、会控面板或聊天区域。  
   **Verify**: 检查实现是否仍保留页面装配层。
2. **不要手写布局枚举字符串或跨平台误用布局模板** — 会直接导致布局行为偏离官方能力。  
   **Verify**: 检查模板切换是否全部基于 `RoomLayoutTemplate`。
3. **不要让纯展示型挂件默认拦截交互** — 会影响双击、拖拽或移动端手势。  
   **Verify**: 检查挂件层是否使用 `pointer-events: none` 或把点击区限制在局部元素上。
4. **不要直接用本地成员列表字段判断摄像头关闭** —— 本地设备开关状态应读取 `useDeviceState().cameraStatus`；远端占位可使用 `participant.cameraStatus`。  
   **Verify**: 检查本地 tile 的关闭态是否来自设备状态而不是本地 participant 流字段。
5. **不要把本地共享流的黑底直接当作可接受默认态** —— 如果本地共享 tile 不展示真实预览，就应补共享中的语义化提示。  
   **Verify**: 检查本地共享流在无预览时是否仍只有空白 / 黑底且没有任何状态说明。
6. **不要把“共享中提示面板”的视觉样式固化成唯一规范** —— 图标、文案、按钮位置都应允许按业务风格调整；真正需要固定的是语义，而不是灰底卡片本身。  
   **Verify**: 检查文档或生成说明是否把示例写成“仅能这样做”的硬编码样式约束。
7. **不要在客户没提特殊布局时绕开 `RoomView` 自己手工编排全部视频 DOM** — 除非业务明确提出 `RoomView` 无法覆盖的布局诉求，并接受逐路管理播放区域和尺寸约束。  
   **Verify**: 检查通用会议或常规布局场景是否仍以 `RoomView` 作为主容器。
8. **不要在自定义单路布局里放任画面比例失控** — 过窄、过高或随内容抖动的容器会明显影响播放体验。  
   **Verify**: 检查单路播放器外层是否具备稳定尺寸，且优先保持接近 `16:9`。
9. **不要把“非可视区域按需渲染”误判为流异常** — 先确认是否属于布局容器的正常策略。  
   **Verify**: 检查排障说明是否区分布局策略与真实故障。

### 集成检查点
- 当前 slice 常与 `conference/room-lifecycle`、`conference/screen-share`、`conference/participant-list`、`conference/device-control` 联动。
- 集成方式通常是在会议主页面中先新增一个 `RoomView` 容器，再按需扩展挂件和布局切换逻辑；只有当客户明确提出 `RoomView` 之外的布局诉求时，再切到 `RoomParticipantView` 逐路拼装。
- 如果业务已有完整自定义会议 UI，仍建议优先保留“页面装配层 / RoomView 布局层 / 挂件层”三层分工；只有布局能力明确不匹配时，再升级为单路播放器方案。

## 验证矩阵
| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | 已导入 `RoomView`、`RoomLayoutTemplate` 等核心依赖 | 检查 `import` 语句 | 布局组件与枚举可正常解析 |
| 2. 静态规则级 | 组件选型、布局模板、父容器尺寸、插槽与事件都配置完整 | 搜索 `RoomView`、`RoomParticipantView`、`participantViewUI`、`stream-double-click`、容器样式 | 常规场景优先使用 `RoomView`，超出能力边界时才切单路组件 |
| 3. 运行时级 | 共享开始、布局切换、双击交互都能生效 | 在会议中触发共享和双击画面 | 主画面与布局行为符合预期 |
| 4. 业务行为级 | 会议页面画面层清晰、挂件不挡交互、移动端策略正确 | 在 PC / H5 页面分别验证 | 视频区域可读、可控且与官方能力一致 |

## 排障指南

### 常见问题

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 视频区域没有正常渲染 | 页面已进房，但画面为空或尺寸异常 | 检查房间是否已建立、视频区域父容器是否具备有效尺寸，以及当前是否存在可展示画面 |
| 屏幕共享没有成为主画面 | 共享已经开始，但主画面仍停留在普通成员 | 检查共享状态是否真正驱动布局切换，以及共享结束后的回退逻辑是否和默认聚焦冲突 |
| 双击某路画面后主画面行为异常 | 聚焦后无法回退，或成员离场后焦点残留 | 检查用户主动聚焦状态是否有清晰失效条件 |
| 多路画面中部分远端不持续播放 | 翻页后某些画面才开始更新，或不可视区域没有持续渲染 | 先确认是否属于布局容器的懒加载与按需渲染特性 |
| 小窗口清晰度看起来偏低 | 主画面清晰，但侧边栏或宫格小窗较模糊 | 先确认是否属于大画面 / 小画面的画质分层策略，而不是错误订阅 |
| 移动端布局体验不佳 | 直接复用桌面端布局，导致主画面过小或交互拥挤 | 改为独立的移动端布局策略，突出主画面和分页体验 |

### 排障流程

```text
发现 视频布局 相关问题
├── 第 1 步：确认问题属于画面编排与挂件展示，而不是进房、设备或成员状态来源本身
├── 第 2 步：检查当前布局模板、共享状态、主画面焦点和平台策略是否由统一状态驱动
├── 第 3 步：确认挂件层是否正确区分摄像头流与共享流，并避免覆盖默认交互
└── 第 4 步：若仍异常，再回查 room-lifecycle / participant-list / screen-share / device-control 的衔接是否正确
```

## 关联知识

- **[conference/room-lifecycle](room-lifecycle.md)** —— 布局的前提是用户已稳定进入房间，离房后也需要同步收口布局状态。
- **[conference/participant-list](participant-list.md)** —— 成员角色、设备状态和名称等信息会投影到视频挂件和排序逻辑里。
- **[conference/screen-share](screen-share.md)** —— 屏幕共享是驱动主画面切换和布局重编排的关键状态来源。
- **[conference/device-control](device-control.md)** —— 摄像头、麦克风开关结果会影响哪些成员进入可视画面以及挂件如何展示。