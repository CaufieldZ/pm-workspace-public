---
id: conference/ai-tools
name: AI 实时转写与字幕
product: conference
platform: web
tags: [ai, asr, transcription, subtitle, translation, realtime]
platforms: [web]
related: [conference/room-lifecycle, conference/participant-management]
---

# AI 实时转写与字幕

## 功能说明

AI 实时转写与字幕负责会议中的实时语音转文字、字幕展示、翻译语言设置和转写消息列表。业务 UI 可以把它做成工具栏入口、侧栏面板或浮层字幕；房主负责启动和更新转写配置，其他成员主要消费字幕和消息结果。

## 核心概念

| 能力 | 说明 |
|------|------|
| `useAITranscriberState()` | 启停和更新实时转写配置 |
| `startRealtimeTranscriber()` | 启动实时转写，传入源语言和翻译目标语言 |
| `stopRealtimeTranscriber()` | 停止实时转写，离房或角色变化时需要收口 |
| `updateRealTimeTranscriber()` | 转写运行中更新语言配置 |
| `RealtimeTranscriberEvent` | 监听转写启动、停止等状态 |
| `Subtitle` | 字幕展示组件 |
| `RealtimeMessageList` | 实时转写消息列表组件 |
| `SubtitleDisplayMode` | 字幕展示模式，当前是 `'bilingual'` / `'translation'` 这类字符串类型 |

## 前置条件

**通用依赖**：见 [login-auth 平台 slice](login-auth.md)。

**额外依赖**：
- 已安装 `tuikit-atomicx-vue3@latest`
- 已完成会议 UI 入口设计，例如工具栏按钮、侧栏面板或字幕浮层。

## 最佳实践

### ✅ ALWAYS

1. **AI 工具入口应由业务 UI 显式控制** —— 只有在当前会议和用户权限满足条件时才展示入口。
2. **只让房主启动或更新实时转写** —— 推荐用 `currentRoom.roomOwner.userId === localParticipant.userId` 判断管理权。
3. **打开字幕或转写面板前先确保 ASR 已启动** —— 面板消费的是实时转写状态，不应空开。
4. **监听转写停止事件并关闭相关 UI** —— ASR 停止后字幕和实时消息面板应同步收口。
5. **房间切换时重置语言、字幕模式和启动状态** —— 防止跨房间继承旧配置。
6. **处理套餐或权限类错误** —— 启动失败时要给出可理解提示，而不是只打印日志。

### ❌ NEVER

1. **不要让每个成员都尝试启动转写** —— 会造成重复请求、权限失败或状态混乱。
2. **不要在离房后保留字幕浮层** —— 旧房间的实时内容不应残留到下一场会议。
3. **不要只切 UI 语言而不调用 `updateRealTimeTranscriber()`** —— 运行中的转写配置不会自动变化。

## 代码示例

### 启动、停止和更新实时转写

```ts
import { ref, watch } from 'vue';
import {
  RealtimeTranscriberEvent,
  useAITranscriberState,
  useRoomParticipantState,
  useRoomState,
} from 'tuikit-atomicx-vue3/room';
import type { SubtitleDisplayMode } from 'tuikit-atomicx-vue3/room';

const sourceLanguage = ref('auto');
const targetLanguage = ref('');
const subtitleDisplayMode = ref<SubtitleDisplayMode>('translation');
const hasStartedASR = ref(false);

const {
  startRealtimeTranscriber,
  stopRealtimeTranscriber,
  updateRealTimeTranscriber,
  subscribeEvent,
} = useAITranscriberState();

const { currentRoom } = useRoomState();
const { localParticipant } = useRoomParticipantState();

const canManageTranscriber = () =>
  currentRoom.value?.roomOwner?.userId === localParticipant.value?.userId;

subscribeEvent(RealtimeTranscriberEvent.onRealtimeTranscriberStarted, () => {
  hasStartedASR.value = true;
});

subscribeEvent(RealtimeTranscriberEvent.onRealtimeTranscriberStopped, () => {
  hasStartedASR.value = false;
});

export async function ensureASRStarted() {
  if (!canManageTranscriber() || hasStartedASR.value) return;

  await startRealtimeTranscriber({
    sourceLanguage: sourceLanguage.value || 'auto',
    translationLanguages: targetLanguage.value ? [targetLanguage.value] : [],
  });
  hasStartedASR.value = true;
}

export async function saveASRSettings(options: {
  sourceLanguage?: string;
  targetLanguage?: string;
  subtitleDisplayMode?: SubtitleDisplayMode;
}) {
  const nextSourceLanguage = options.sourceLanguage ?? sourceLanguage.value;
  const nextTargetLanguage = options.targetLanguage ?? targetLanguage.value;

  sourceLanguage.value = nextSourceLanguage;
  targetLanguage.value = nextTargetLanguage;
  subtitleDisplayMode.value = options.subtitleDisplayMode ?? subtitleDisplayMode.value;

  if (canManageTranscriber() && hasStartedASR.value) {
    await updateRealTimeTranscriber({
      sourceLanguage: sourceLanguage.value || 'auto',
      translationLanguages: targetLanguage.value ? [targetLanguage.value] : [],
    });
  }
}

export async function stopASR() {
  if (!hasStartedASR.value) return;
  await stopRealtimeTranscriber();
  hasStartedASR.value = false;
}

watch(() => currentRoom.value?.roomId, () => {
  sourceLanguage.value = 'auto';
  targetLanguage.value = '';
  hasStartedASR.value = false;
}, { immediate: true });
```

### 字幕浮层与实时转写消息列表

```vue
<template>
  <Subtitle
    v-if="isSubtitlesVisible"
    :target-language="targetLanguage"
    :display-mode="subtitleDisplayMode"
  />

  <RealtimeMessageList
    v-if="isRealtimeMessageListVisible"
    :target-language="targetLanguage"
    :display-mode="subtitleDisplayMode"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue';
import {
  RealtimeMessageList,
  Subtitle,
} from 'tuikit-atomicx-vue3/room';
import type { SubtitleDisplayMode } from 'tuikit-atomicx-vue3/room';

const isSubtitlesVisible = ref(false);
const isRealtimeMessageListVisible = ref(false);
const targetLanguage = ref('');
const subtitleDisplayMode = ref<SubtitleDisplayMode>('translation');
</script>
```

## 平台特有注意事项

### 1. 管理权以房主为准
推荐只让房主启动或更新 ASR 配置。如果业务要放开给管理员，需要明确权限规则，并处理多人同时更新配置的冲突。

### 2. 打开 UI 前先启动 ASR
字幕浮层和转写消息列表只是展示层。点击入口时应先调用 `ensureASRStarted()`，成功后再打开字幕或侧栏。

### 3. 停止后同步关闭 UI
监听 `RealtimeTranscriberEvent.onRealtimeTranscriberStopped`，转写停止后关闭字幕、实时消息面板和设置弹层，避免残留。

### 4. 套餐错误要显式提示
启动实时转写可能返回套餐未开通、权限不足或频控类错误。遇到 `ERR_REQUIRE_PAYMENT` 时应提示需要开通对应套餐。

## 代码生成约束

### MUST

1. **通过 `useAITranscriberState()` 启停和更新转写**。  
   **Verify**: 检查是否存在 `startRealtimeTranscriber()` / `stopRealtimeTranscriber()`。
2. **打开字幕或转写面板前确保 ASR 已启动**。  
   **Verify**: 检查入口点击前是否调用 `ensureASRStarted()` 或等价逻辑。
3. **房间切换或转写停止时清理 UI 状态**。  
   **Verify**: 检查 `currentRoom.roomId` watch 或 `onRealtimeTranscriberStopped` 监听。
4. **运行中改语言时调用 `updateRealTimeTranscriber()`**。  
   **Verify**: 检查保存设置逻辑中是否调用更新接口。

### MUST NOT

1. **不要让每个参会人都启动 ASR**。  
   **Verify**: 检查是否有房主或业务权限判断。
2. **不要只渲染 `Subtitle` 而没有转写启动链路**。  
   **Verify**: 检查字幕入口是否能触发启动。

## 验证矩阵

| 层级 | 检查项 | 验证手段 | 预期结果 |
|------|--------|----------|---------|
| 1. 编译级 | AI 转写 API 可解析 | 检查 `useAITranscriberState`、`Subtitle` 导入 | 类型可解析 |
| 2. 静态规则级 | 启动、更新、停止链路完整 | 搜索 `startRealtimeTranscriber` / `updateRealTimeTranscriber` / `stopRealtimeTranscriber` | 三段链路存在 |
| 3. 运行时级 | 房主可打开字幕和转写列表 | 房主账号点击 AI 工具 | ASR 启动并展示内容 |
| 4. 业务行为级 | 切房间或停止后 UI 收口 | 离房或停止 ASR | 字幕和转写面板关闭 |

## 排障指南

| 问题 | 表现 | 处理建议 |
|------|------|----------|
| 点击字幕后没有内容 | 字幕浮层打开但无文本 | 检查是否已调用 `startRealtimeTranscriber()` |
| 非房主启动失败 | 普通成员打开 AI 工具报错 | 只允许房主启动，其他成员消费已有转写结果 |
| 切换语言不生效 | 设置面板保存后字幕仍旧语言 | 转写已启动时调用 `updateRealTimeTranscriber()` |
| 离房后字幕残留 | 下一场会议仍显示旧字幕 | 监听 roomId 变化和 stopped 事件，清理 UI 状态 |

## 关联知识

- **[conference/room-lifecycle](room-lifecycle.md)** —— 进退房决定 AI 状态的初始化与清理时机。
- **[conference/participant-management](participant-management.md)** —— 房主身份和角色变化会影响 AI 管理权。
