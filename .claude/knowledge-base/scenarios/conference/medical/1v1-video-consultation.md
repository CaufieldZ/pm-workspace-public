---
id: 1v1-video-consultation
name: 1v1视频问诊
product: conference
room_type: standard
base_scenario: general-conference
industry: medical

trigger:
  intent_keywords:
    - 1v1 视频问诊
    - 远程问诊
    - 互联网医院
    - 医生患者视频
    - 在线问诊
    - 医患视频
    - 问诊系统
    - telemedicine
    - video consultation
    - doctor patient video

template:
  path: skills/trtc-conference/templates/medical-consultation/
  playbook: medical-quickstart
  description: 完整的 1v1 视频问诊项目，含医生端 / 患者端 UI、候诊室和问诊流程

business_traits:
  - waiting-room
  - medical-record
  - prescription
slices:
  - conference/login-auth
  - conference/prejoin-check
  - conference/room-lifecycle
  - conference/room-call
  - conference/participant-list
  - conference/device-control
  - conference/network-quality
  - conference/room-chat
  - conference/video-layout
---

# 1v1视频问诊

## 场景描述

本文描述的是一个完整的 **1v1 视频问诊** 场景。它面向互联网医院、远程复诊、线上问诊等医患一对一沟通流程：患者先进入候诊室等待叫号，医生在首页查看业务后台维护的待接诊列表；当医生进入诊室并呼叫患者后，患者再真正进入问诊房间。问诊过程中，医生一边视频沟通，一边填写病历、处方并查看患者资料；问诊结束后，医生结束本次会诊，患者进入完成页。

## 场景边界

| 需求形态 | 是否直接沿用本文 | 说明 |
|------|------------------|------|
| 1v1 视频问诊 | 是 | 本文的默认目标场景，医生与患者一对一进入问诊房间。 |
| 多人远程会诊 | 否 | 一旦进入多医生 / 多患者 / 家属共同入会，应优先查看 `medical-multidoctor-consultation.md`；它本质仍基于 `general-conference`，但已补齐医疗会诊业务外壳。 |
| 复诊随访 / 术后回访 | 部分适合 | 如果仍是稳定 1v1 视频沟通，可沿用本文；若更像纯呼叫或消息提醒链路，再单独评估。 |

## 前置条件

- TRTC 控制台已创建应用，获取 `SDKAppID`
- 业务后端已实现 `UserSig` 签发接口
- 业务侧已准备待接诊列表、候诊状态、叫号状态、病历 / 处方 / 资料面板等业务数据源
- 问诊房间的 `roomId`、医生 / 患者身份映射和叫号关系由业务层统一生成

## 能力展示

### 展示文案

你选择的是 **1v1 视频问诊（医疗在线咨询）** 场景。这里应优先按“医疗问诊项目”解释，而不是按通用会议模块表解释。

这个场景包含：

- 医生工作台：待接诊列表、患者基础信息、进入诊室、呼叫患者。
- 患者候诊：登录、自检、候诊状态、收到叫号后入诊。
- 问诊房间：医生与患者一对一视频沟通，展示医患身份、音视频状态、弱网提示和基础会控。
- 医疗业务面板：病历、处方、检查资料或客户 EMR / HIS / PACS 插槽。
- 问诊收口：医生结束问诊、释放设备、患者进入完成页。

如果这是 brand-new project 且项目里没有现成 TRTC 依赖，应直接创建完整的医疗问诊模板项目；不要向用户展示原子 slice 清单，也不要把它描述为 `general-conference` 的模块组合。只有在用户明确选择“自定义 UI”或“业务逻辑 only”时，才继续进入 slice-driven topic 流程。

## 主流程

| 步骤 | 参与方 | Slice / 模块 | 核心操作 |
|------|--------|--------------|---------|
| 1. 患者进入候诊室 | 患者 | `login-auth` + `prejoin-check` + 业务候诊室 | 患者完成登录、自检并进入候诊态，等待医生叫号；此时还未真正进入问诊房间 |
| 2. 医生首页查看待接诊列表 | 医生 | 业务接诊列表 + 业务候诊状态 | 医生在工作台查看后台维护的待接诊列表、候诊状态和目标患者基础信息 |
| 3. 医生进入诊室并呼叫患者 | 医生 | `room-lifecycle` + `room-call` | 医生创建 / 进入本次问诊房间，并向目标患者发起叫号 |
| 4. 患者进入诊室 | 患者 | `room-call` + `room-lifecycle` | 患者接到叫号后接受呼叫，真正进入问诊房间 |
| 5. 医生开始问诊并填写病历 / 处方 / 查看资料 | 医生 | `video-layout` + `participant-list` + `participant-management` + `device-control` + `room-chat` + `network-quality` + 业务病历面板 | 医生通过 `RoomView` 与患者进行 1v1 视频问诊，同时在业务面板中填写病历、处方和查看资料；必要时可执行禁麦、禁摄、禁聊等会中控制 |
| 6. 医生结束问诊 | 医生 | `room-lifecycle` + `device-control` | 医生结束本次问诊，统一收口会中状态并释放本地设备 |
| 7. 患者完成本次问诊 | 患者 | `room-lifecycle` + 业务完成页 | 患者离开问诊房间，进入问诊完成页或后续待支付 / 待取药 / 待评价流程 |

## 医生端流程

### 阶段一：接诊前准备

| 步骤 | Slice / 模块 | 核心操作 |
|------|--------------|---------|
| 1. 登录医生工作台 | login-auth | 完成 `SDKAppID / UserID / UserSig` 鉴权登录 |
| 2. 查看待接诊列表 | 业务接诊列表 + 业务候诊状态 | 查看后台维护的待接诊顺序、候诊状态和目标患者信息 |
| 3. 创建 / 进入诊室 | room-lifecycle | 生成本次问诊房间并进入医生侧诊室 |
| 4. 打开设备并确认状态 | device-control | 进入诊室后开启摄像头、麦克风，并处理权限拒绝、设备占用等异常 |
| 5. 呼叫患者 | room-call | 向指定患者发起叫号 / 入诊呼叫 |

### 阶段二：问诊进行中

| 功能 | Slice / 模块 | 核心操作 |
|------|--------------|---------|
| 1v1 视频承载 | video-layout | 使用 `RoomView` 承载医生与患者双画面 |
| 医患身份与状态展示 | participant-list | 展示医生 / 患者标签、接诊状态、音视频状态 |
| 会中控制 | participant-management | 医生可按问诊秩序执行禁麦、禁摄、禁聊等控制，并把规则状态同步到设备和输入区 |
| 本地设备控制 | device-control | 控制摄像头、麦克风、扬声器，并处理权限或占用异常 |
| 弱网提示与恢复建议 | network-quality | 展示弱网、重连中、超时告警，并提示是否降级互动强度 |
| 图文提醒 / 补充说明 | room-chat | 发送文字提醒、检查说明或注意事项 |
| 病历 / 处方 / 资料查看 | 业务病历面板 | 在视频外壳层旁路展示病历、处方和影像资料，不改变会议主链路 |

### 阶段三：结束问诊

| 步骤 | Slice / 模块 | 核心操作 |
|------|--------------|---------|
| 1. 完成病历 / 处方填写 | 业务病历面板 | 确认病历、处方和资料处理完成 |
| 2. 结束会议 | room-lifecycle | 结束本次问诊并触发统一收口 |
| 3. 释放本地设备 | device-control | 关闭摄像头、麦克风并释放本地资源 |

## 患者端流程

### 阶段一：候诊

| 步骤 | Slice / 模块 | 核心操作 |
|------|--------------|---------|
| 1. 登录 | login-auth | 完成患者账号登录 |
| 2. 设备自检 | prejoin-check | 检查摄像头、麦克风、扬声器是否可用，必要时降级 |
| 3. 进入候诊室 | 业务候诊室 | 进入候诊态，查看排队中 / 即将接诊等状态 |

### 阶段二：进入问诊

| 步骤 | Slice / 模块 | 核心操作 |
|------|--------------|---------|
| 1. 接收医生叫号 | room-call | 接收问诊呼叫或叫号提醒 |
| 2. 真正进入诊室 | room-lifecycle | 接受呼叫后进入已有问诊房间 |
| 3. 打开本地设备 | device-control | 按权限和设备状态开启摄像头 / 麦克风 |
| 4. 渲染患者问诊页 | video-layout + participant-list | 呈现医生主画面、患者自视图和身份状态 |

### 阶段三：完成问诊

| 步骤 | Slice / 模块 | 核心操作 |
|------|--------------|---------|
| 1. 响应弱网 / 断线恢复 | network-quality + room-lifecycle | 弱网时提示重连或重新加入，超时后恢复会中上下文 |
| 2. 离开问诊房间 | room-lifecycle | 医生结束问诊后退出当前会议 |
| 3. 进入完成页 | 业务完成页 | 展示本次问诊已完成，并进入后续业务流程 |

## 排障速查

遇到问题时，根据现象查找对应 slice 的排障指南：

| 现象 | 可能原因 | 参考 Slice / 模块 |
|------|---------|------------------|
| 患者无法进入候诊室 | 登录失败或业务候诊状态异常 | login-auth / 业务候诊室 |
| 医生首页看不到待接诊列表 | 业务后台列表未同步或候诊状态数据缺失 | 业务接诊列表 / 业务候诊状态 |
| 医生发起叫号后患者无响应 | 呼叫未送达、用户不在线或状态未切换 | room-call |
| 患者接到叫号但进不了诊室 | `roomId` 无效、密码错误或加入主链路失败 | room-lifecycle |
| 问诊中无法开麦 / 开摄 | 设备占用、权限拒绝或本地设备异常 | device-control |
| 视频画面正常但身份 / 状态不对 | 挂件层未正确绑定角色或状态字段 | participant-list / video-layout |
| 问诊中频繁断线 | 网络抖动、弱网或超时离会 | network-quality / room-lifecycle |
| 医生结束问诊后仍残留摄像头占用 | 结束后未正确释放本地设备 | room-lifecycle / device-control |
