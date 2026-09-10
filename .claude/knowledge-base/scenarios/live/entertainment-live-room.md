---
id: entertainment-live-room
name: 秀场直播间
product: live

trigger:
  intent_keywords:
    - 秀场直播
    - 直播间
    - 主播开播
    - 观众刷礼物
    - 连麦直播
    - entertainment live
    - live room
    - gift live stream

slices:
  - live/login-auth
  - live/device-control
  - live/anchor-preview
  - live/anchor-room-config
  - live/anchor-lifecycle
  - live/live-list
  - live/audience-watch
  - live/audience-list
  - live/barrage
  - live/gift
  - live/audience-manage
  - live/beauty
  - live/audio
  - live/coguest-apply
  - live/error-codes
---

# 秀场直播间

## 场景描述

搭建一个完整的秀场直播间。主播开播后，观众可以从列表进入，在房间里发弹幕、刷礼物、申请连麦。主播可以管理观众（踢人/禁言），也可以邀请观众上麦。连麦观众需要有美颜。

## 前置条件

- TRTC 控制台已创建应用，获取 SDKAppID
- 业务后端已实现 UserSig 签发接口
- iOS 项目已集成 `pod 'AtomicXCore', '~> 4.0'`

## 主播端流程

### 阶段一：开播准备

| 步骤 | Slice | 核心操作 |
|------|-------|---------|
| 1. 登录 | login-auth | LoginStore.shared.login() |
| 2. 打开设备 | device-control | DeviceStore.shared.openLocalCamera() + openLocalMicrophone() |
| 3. 预览画面 | anchor-preview | LiveCoreView(viewType: .pushView) + setLiveID |
| 4. 调整美颜 | beauty | BaseBeautyStore.shared.setSmoothLevel() 等 |
| 5. 调整音效 | audio | AudioEffectStore.shared.setAudioChangerType() 等 |
| 6. 配置房间 | anchor-room-config | 设置房间名、封面、MetaData |
| 7. 开播 | anchor-lifecycle | LiveListStore.shared.createLive() |

### 阶段二：直播中互动

| 功能 | Slice | 核心操作 |
|------|-------|---------|
| 查看弹幕 | barrage | BarrageStore 状态订阅 |
| 收到礼物 | gift | giftEventPublisher 订阅 |
| 查看观众 | audience-list | LiveAudienceStore.fetchAudienceList() |
| 管理观众 | audience-manage | kickUserOutOfRoom / setAdministrator |
| 禁言 | barrage | disableSendMessage() |

### 阶段三：连麦管理

| 操作 | Slice | 核心操作 |
|------|-------|---------|
| 收到连麦申请 | coguest-apply | hostEventPublisher 监听 |
| 同意/拒绝 | coguest-apply | acceptApplication / rejectApplication |
| 断开连麦 | coguest-apply | disConnect() |

### 结束直播

| 步骤 | Slice | 核心操作 |
|------|-------|---------|
| 1. 断开所有连麦 | coguest-apply | disConnect() |
| 2. 结束直播 | anchor-lifecycle | LiveListStore.shared.endLive() |
| 3. 重置音效 | audio | AudioEffectStore.shared.reset() |
| 4. 关闭设备 | device-control | closeLocalCamera() + closeLocalMicrophone() |

## 观众端流程

### 进入观看

| 步骤 | Slice | 核心操作 |
|------|-------|---------|
| 1. 登录 | login-auth | LoginStore.shared.login() |
| 2. 浏览列表 | live-list | fetchLiveList() |
| 3. 进入直播间 | audience-watch | LiveCoreView(playView) + joinLive() |
| 4. 查看观众 | audience-list | LiveAudienceStore |
| 5. 发弹幕 | barrage | sendTextMessage() |
| 6. 送礼物 | gift | sendGift() |

### 申请连麦（可选）

| 步骤 | Slice | 核心操作 |
|------|-------|---------|
| 1. 发起申请 | coguest-apply | applyForSeat(timeout: 30) |
| 2. 等待审批 | coguest-apply | guestEventPublisher 监听 |
| 3. 通过后开设备 | device-control | openLocalCamera + openLocalMicrophone |
| 4. 开启美颜 | beauty | BaseBeautyStore 设置 |
| 5. 下麦 | coguest-apply | disConnect() → 关闭设备 → 回到普通观看 |

### 退出直播间

| 步骤 | Slice | 核心操作 |
|------|-------|---------|
| 1. 如在连麦，先下麦 | coguest-apply | disConnect() |
| 2. 退出房间 | audience-watch | leaveLive() |

## 排障速查

遇到问题时，根据现象查找对应 slice 的排障指南：

| 现象 | 可能原因 | 参考 Slice |
|------|---------|-----------|
| 所有功能不可用 | 未登录或登录失败 | login-auth |
| 黑屏无画面 | 设备未打开 / setLiveID 缺失 | device-control / anchor-preview |
| 弹幕不显示 | BarrageStore 未创建或未订阅 | barrage |
| 礼物发送失败 | 余额不足或网络问题 | gift |
| 连麦申请无响应 | 主播未监听事件 | coguest-apply |
| 操作被拒绝（权限） | 非房主/管理员 | audience-manage + error-codes |
| 任何错误码 | 查错误码表 | error-codes |
