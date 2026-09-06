---
id: medical-multidoctor-consultation
name: 医疗会诊
product: conference
room_type: standard
base_scenario: general-conference
industry: medical

trigger:
  intent_keywords:
    - 多方会诊
    - 医疗会诊
    - 专家会诊
    - 多医生讨论
    - 远程会诊
    - MDT 会议
    - 多学科会诊
    - multi-doctor consultation
    - medical consultation

business_traits:
  - mdt
  - medical-record
  - consultation-sheet
slices:
  - conference/login-auth
  - conference/prejoin-check
  - conference/room-schedule
  - conference/room-lifecycle
  - conference/room-call
  - conference/participant-list
  - conference/participant-management
  - conference/device-control
  - conference/network-quality
  - conference/room-chat
  - conference/video-layout
  - conference/screen-share
---

# 医疗会诊

## 场景描述

本文描述的是一个完整的 **医疗会诊** 场景，它属于 **`general-conference` 的医疗派生场景**。典型形态是：围绕同一患者病例，由主诊医生发起会诊，邀请院内外专家、多学科医生或助理共同进入会诊房间；会中一边进行多人视频讨论，一边查看病历、检查结果、影像资料和会诊单，必要时可让患者或家属在特定阶段进入房间补充沟通；会诊结束后，由主诊医生统一收口会议并沉淀会诊结论。

## 场景边界

| 需求形态 | 是否直接沿用本文 | 说明 |
|------|------------------|------|
| 多医生远程会诊 / MDT 会诊 | 是 | 本文的默认目标场景，多位医生围绕同一病例进行实时讨论与决策。 |
| 1v1 视频问诊 | 否 | 如果主要是医生与患者一对一沟通，应优先查看 `1v1-video-consultation.md`。 |
| 医疗培训讲座 / 学术直播 | 否 | 如果主讲人中心化明显、听众弱互动，应优先分流到 `webinar-conference.md` 再叠加医疗培训外壳。 |
| 科室晨会 / 病例讨论会 | 部分适合 | 如果仍以多人实时音视频协作为主，可沿用本文；若没有患者参与且更偏内部日常会议，也可直接回落到 `general-conference.md`。 |

## 前置条件

- TRTC 控制台已创建应用，获取 `SDKAppID`
- 业务后端已实现 `UserSig` 签发接口
- 业务侧已准备会诊预约、专家列表、病例资料、影像链接、会诊单与结论记录等数据源
- 本次会诊的 `roomId`、参会角色、邀请关系和患者绑定关系由业务层统一生成

## 主流程

| 步骤 | 参与方 | Slice / 模块 | 核心操作 |
|------|--------|--------------|---------|
| 1. 主诊医生发起会诊并预约时间 | 主诊医生 / 后台 | `login-auth` + `room-schedule` + 业务会诊单 | 医生创建会诊单、选择时间并配置参与专家与患者信息 |
| 2. 医生与专家会前准备 | 医生 / 专家 | `prejoin-check` + `device-control` | 各参会医生在入会前完成摄像头、麦克风、扬声器检查 |
| 3. 主诊医生创建并进入会诊房间 | 主诊医生 | `room-lifecycle` | 由主诊医生配置并进入本次会诊房间，建立主持角色和房间规则 |
| 4. 邀请专家和相关参与方进入 | 主诊医生 / 系统 | `room-call` + `room-lifecycle` + `participant-list` | 按会诊单邀请院内外专家、助理，必要时控制患者 / 家属进入时机 |
| 5. 多人视频讨论病例 | 医生 / 专家 | `video-layout` + `participant-list` + `room-chat` + `network-quality` | 多位医生基于病例进行实时音视频讨论，查看在场状态、发言态和网络状态 |
| 6. 共享影像和病例资料 | 医生 / 专家 | `screen-share` + `video-layout` + 业务病历面板 | 共享 CT、检查单、PPT 或病例资料，并保持主舞台与成员画面的协同展示 |
| 7. 主诊医生控场与结论收敛 | 主诊医生 | `participant-management` + 业务会诊单 | 控制发言秩序、静音、移除或指定发言人，并沉淀会诊结论 |
| 8. 结束会诊并归档 | 主诊医生 / 后台 | `room-lifecycle` + `device-control` + 业务归档模块 | 结束会诊、释放本地设备，并把结论、建议和会诊记录归档 |

## 角色流程

### 阶段一：主诊医生

| 步骤 | Slice / 模块 | 核心操作 |
|------|--------------|---------|
| 1. 登录医生工作台 | login-auth | 完成 `SDKAppID / UserID / UserSig` 鉴权登录 |
| 2. 发起会诊并设置议题 | 业务会诊单 + room-schedule | 选择病例、时间、参与专家和会诊目标 |
| 3. 创建会诊房间 | room-lifecycle | 配置房间名称、入会规则、默认禁麦或角色权限 |
| 4. 邀请专家 / 患者 / 家属 | room-call + participant-management | 定向邀请参会人，并根据阶段控制谁可以入会 |
| 5. 组织讨论与总结结论 | participant-management + room-chat + 业务会诊单 | 控制发言秩序、同步文字结论并最终收口 |

### 阶段二：专家医生

| 步骤 | Slice / 模块 | 核心操作 |
|------|--------------|---------|
| 1. 接收会诊通知 | room-schedule / room-call | 从预约列表或即时邀请进入会诊 |
| 2. 会前设备检查 | prejoin-check + device-control | 检查设备状态并处理权限 / 占用问题 |
| 3. 进入会诊房间 | room-lifecycle | 进入多人讨论房间，加载音视频上下文 |
| 4. 查看参会状态与资料 | participant-list + 业务病历面板 | 识别当前发言人、角色和病例资料 |
| 5. 参与讨论与资料共享 | video-layout + screen-share + room-chat | 发言、共享资料或通过聊天补充建议 |

### 阶段三：患者 / 家属（可选）

| 步骤 | Slice / 模块 | 核心操作 |
|------|--------------|---------|
| 1. 等待进入通知 | 业务会诊单 / room-call | 只在需要直接沟通时接收进入提醒 |
| 2. 完成入会前检查 | prejoin-check + device-control | 检查本地设备和网络状态 |
| 3. 在指定阶段进入房间 | room-lifecycle + participant-list | 进入会诊房间，与医生 / 专家进行补充沟通 |
| 4. 退出会诊并等待结果 | room-lifecycle | 沟通结束后退出房间，回到业务结果页 |

## 关键能力拆分

| 能力点 | 对应 Slice / 模块 | 说明 |
|------|------------------|------|
| 会诊预约与时间管理 | `room-schedule` + 业务会诊单 | 预约列表与到点提醒属于高频入口 |
| 房间规则与角色权限 | `room-lifecycle` + `participant-management` | 会诊通常有明确主持人和受控发言秩序 |
| 多专家入会与状态展示 | `participant-list` + `participant-management` | 需要清楚看到各专家身份、设备态和发言状态 |
| 病例讨论主舞台 | `video-layout` + `screen-share` | 影像或病例资料共享时，需要兼顾主舞台和人员画面 |
| 会中沟通与结论同步 | `room-chat` + 业务会诊单 | 聊天用于补充文字信息，正式结论仍落业务模块 |
| 稳定性与异常恢复 | `network-quality` + `room-lifecycle` + `device-control` | 处理弱网、断线、设备异常和重入恢复 |

## 排障速查

| 现象 | 可能原因 | 参考 Slice / 模块 |
|------|---------|------------------|
| 专家收不到会诊通知 | 邀请未送达、预约数据未同步或用户不在线 | room-call / room-schedule |
| 部分医生进入后看不到其他参会人 | 角色映射错误或成员状态未正确同步 | participant-list / participant-management |
| 共享影像后主画面切换异常 | 共享状态、布局逻辑或主舞台策略未处理好 | screen-share / video-layout |
| 会中无法发言或被错误静音 | 会控规则配置不一致或主持操作未同步 | participant-management |
| 外院专家音视频异常 | 本地设备权限、浏览器兼容性或网络质量问题 | prejoin-check / device-control / network-quality |
| 会诊结束后仍占用摄像头麦克风 | 房间收口后未正确释放本地设备 | room-lifecycle / device-control |
