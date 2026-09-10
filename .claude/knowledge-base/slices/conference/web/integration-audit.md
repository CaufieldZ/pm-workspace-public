---
id: conference/integration-audit
name: Conference Web 集成审计
product: conference
platform: web
tags: [audit, checklist, meta, integration-review, roomkit, online-classroom]
platforms: [web]
related:
  - conference/login-auth
  - conference/prejoin-check
  - conference/room-lifecycle
  - conference/room-schedule
  - conference/device-control
  - conference/official-roomkit-api
related_scenario: general-conference
---

# Conference Web 集成审计

> **Meta slice** — 横切对照清单，供 intent F（集成审计）使用。
> **不要**加入 scenario 的 `slices` / `confirmed_plan`，**不要**走 topic 集成队列或 apply 门禁。

> 当用户问「检查业务流程遗漏」「对照官方接入流程」「在线课堂/会议流程是否正常」时使用本 slice。
> 输出形态：**固定 checklist + slice 引用**；**不要**输出 code review、优缺点列表或「改进建议」段落。

## 如何使用

1. 从 session 读取 `product` / `platform` / `ui_mode` / `scenario`（若有）。
2. 仅 `(product, platform) == (conference, web)` 时走完整清单；其他组合说明当前 skill 集成 fix 仅覆盖 Conference Web，清单仍可作为对照参考。
3. 按角色（学生 / 老师 / 通用）裁剪章节；用户未说明角色时输出「通用骨架 + 在线课堂附录」。
4. 每项标注：**应有** / **常见遗漏** / **对应 slice**。
5. 用户贴了代码时，只核对清单项是否 wired up，不做风格点评。

---

## 1. 通用骨架（所有 Conference Web 项目）

| # | 检查项 | 常见遗漏 | 参考 slice |
|---|--------|----------|------------|
| 1.1 | `conference.login()` / `useLoginState().login()` 先于任何 room/device/chat 调用 | 未登录直接 join | `conference/login-auth` |
| 1.2 | 登录参数含 `scene: 5001`（skill 生成代码） | 缺 scene | `conference/login-auth` |
| 1.3 | 登录成功后 `setSelfInfo({ userName, avatarUrl })` | 列表只显示 userId | `conference/login-auth` |
| 1.4 | UserSig：生产由后端签发；本地可用 config 自动签名（`local-dev`）或控制台粘贴（`console`） | userId 与 userSig 不匹配 | `conference/login-auth` |
| 1.5 | 监听 `LoginEvent.onLoginExpired` / `onKickedOffline` 并收口 | 只打日志 | `conference/login-auth` |
| 1.6 | 监听 `RoomEvent.USER_SIG_EXPIRED` / `KICKED_OUT` / `ROOM_DISMISS` | 被动退出 UI 假在线 | `conference/room-lifecycle` |
| 1.7 | 页面在 **HTTPS** 或 **localhost** 下调试 | 生产 HTTP 无媒体权限 | `conference/device-control` |
| 1.8 | iframe 嵌入时宿主页 `allow="camera; microphone; display-capture; fullscreen"` | iframe 内黑屏/无权限 | `conference/device-control` |
| 1.9 | 刷新/关页时 `leaveRoom()` 或等价清理 | 幽灵参会者 | `conference/room-lifecycle` |
| 1.10 | 房主 `endRoom()` vs 成员 `leaveRoom()` 分支正确 | 老师误用 leave 导致房间未结束 | `conference/room-lifecycle` |

---

## 2. 会前设备检测

| # | 检查项 | 常见遗漏 | 参考 slice |
|---|--------|----------|------------|
| 2.1 | 会前用 `startCameraTest` / `stopCameraTest`，**不用** `openLocalCamera` 做预检 | getUserMedia 与 SDK 双轨冲突 | `conference/prejoin-check` |
| 2.2 | 预检页设备开关用**本地 ref**，不读 `cameraStatus` / `microphoneStatus` | 预检与会中状态串线 | `conference/prejoin-check` |
| 2.3 | 入会前 `stopCameraTest()` 释放采集 | 进房后设备占用 | `conference/prejoin-check` |
| 2.4 | 轻量 `getUserMedia` 仅作**权限门禁**；完整预览走 Atomicx 测试 API | 两套检测职责重叠 | `conference/prejoin-check` |
| 2.5 | 进房后麦克风：先 `openLocalMicrophone()` + 默认 `muteMicrophone()`；摄像头：`open/closeLocalCamera` | 开麦延迟、关摄语义错误 | `conference/device-control` |

---

## 3. 房间生命周期

| # | 检查项 | 常见遗漏 | 参考 slice |
|---|--------|----------|------------|
| 3.1 | 即时会议：发起人 `createAndJoinRoom`，他人 `joinRoom` | roomId 来源混乱 | `conference/room-lifecycle` |
| 3.2 | 预约会议：`scheduleRoom` 成功后，到点仍须 `joinRoom`（预约≠已入会） | 预约后直接认为在会中 | `conference/room-schedule` |
| 3.3 | `joinRoom` 失败区分：未登录 / 房间不存在 / 密码错误 / 已结束 | 统一提示「进房失败」 | `conference/room-lifecycle` |
| 3.4 | 被动退出后清理 `currentRoom`、聊天、布局、widget 注册 | 再次入会残留上一场状态 | `conference/room-lifecycle` |
| 3.5 | `passive_exit_target`：被踢/解散后跳转大厅或登录（业务决策） | 停留在空白会中页 | `conference/room-lifecycle` |

---

## 4. 官方 RoomKit 模式（`ui_mode = official-roomkit`）

| # | 检查项 | 常见遗漏 | 参考 slice |
|---|--------|----------|------------|
| 4.1 | 根节点 `UIKitProvider` 包裹 `PreConferenceView` / `ConferenceMainView(H5)` | Provider 缺失 | `conference/official-roomkit-api` |
| 4.2 | `setWidgetVisible` / `registerWidget` / `onWill` 在 **login 之后、join 之前** | 按钮闪烁、拦截失效 | `conference/official-roomkit-api` |
| 4.3 | `createAndJoinRoom` / `joinRoom` 成功后立即 `setFeatureConfig({ shareLink })` | 分享链接 roomId 不对 | `conference/official-roomkit-api` |
| 4.4 | 收集 `registerWidget` / `onWill` 返回的 cleanup；在 `ROOM_LEAVE` 与 `ROOM_DISMISS` 都执行 | 重复注册、泄漏 | `conference/official-roomkit-api` |
| 4.5 | UI 显隐用 `setWidgetVisible`，**不用** CSS/DOM hack | 升级 SDK 即碎 | `conference/official-roomkit-api` |
| 4.6 | lockfile 中 `@tencentcloud/roomkit-web-vue3 >= 5.4.3` | 定制 API 不可用 | `conference/official-roomkit-api` |

---

## 5. 在线课堂角色附录

### 学生链路

```text
登录 → setSelfInfo → 预约列表(room-schedule) → 会前检测(prejoin-check)
  → joinRoom → 会中（默认禁麦策略）→ 主动 leaveRoom / 被动 ROOM_DISMISS
```

| 常见遗漏 | 说明 |
|----------|------|
| 预约后直接进房未做设备检测 | 应用 prejoin-check 页或等价流程 |
| 被房主结束会议无提示 | 监听 `RoomEvent.ROOM_DISMISS` |
| 与「只 join 不 create」的 roomid_origin 不一致 | session 业务决策应对齐 |

### 老师链路

```text
登录 → setSelfInfo → createAndJoinRoom → 会中开启 AI 字幕(ai-tools) / 录制(控制台+套餐)
  → endRoom（非 leaveRoom）
```

| 常见遗漏 | 说明 |
|----------|------|
| AI 字幕非房主也调 `startRealtimeTranscriber` | 仅房主应启动 |
| 结束会议用 `leaveRoom` 而非 `endRoom` | 其他成员仍留在已结束房间上下文 |
| 录制能力未在控制台开通 | 预制 UI 按钮灰显或启动失败 |

---

## 6. 高频运行时问题速查（审计时顺带提及）

| 现象 / 错误码 | 结论 | 下一步 |
|---------------|------|--------|
| **6206** / UserSig expired | 鉴权失败 | 后端刷新 UserSig；监听 `USER_SIG_EXPIRED` |
| **100211** take-seat not enabled | 非麦位房间内部 seat 同步 | Standard 会议通常**可忽略**；确认未调用上麦/连麦 API |
| **100006** only open to live room | 在 Standard 房间调了 Live 接口 | 检查 roomType；隐藏 Live 工具栏 widget |
| 双设备检测冲突 | 职责未分层 | 见 §2 |
| iframe 无画面 | 缺 allow 权限 | 见 §1.8 |
| 刷新后幽灵在线 | 未 beforeunload leave | 见 §1.9 |

---

## 7. 推荐输出模板（给 AI）

```markdown
## Conference Web 集成对照结果

**场景**：{scenario 或「通用会议」} · **UI 模式**：{official-roomkit | headless | 未知}

### 已覆盖（对照官方流程）
- …

### 可能遗漏（按优先级）
1. … → 参考 `conference/xxx`
2. …

### 环境/权限门禁
- HTTPS / iframe / UserSig：…

### 官方文档
- [Web RoomKit 快速接入](https://cloud.tencent.com/document/product/647/81962)
- [设备检测](https://cloud.tencent.com/document/product/647/126939)
```

**禁止**使用的标题：Critical Review Checklist、改进建议、✅正确 vs ❌错误 对比表（作为主结构）。
