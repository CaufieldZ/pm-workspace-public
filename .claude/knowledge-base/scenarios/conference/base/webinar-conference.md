---
id: webinar-conference
name: 研讨会 / 宣讲会
product: conference
room_type: webinar
industry: generic

trigger:
  intent_keywords:
    - 研讨会
    - 宣讲会
    - 在线讲座
    - 主讲人
    - 嘉宾上台
    - 大型会议
    - 单向广播
    - webinar
    - lecture
    - town hall

slices:
  - conference/login-auth
  - conference/prejoin-check
  - conference/room-lifecycle
  - conference/participant-list
  - conference/video-layout
  - conference/device-control
  - conference/network-quality
  - conference/room-chat
  - conference/screen-share
  - conference/participant-management
  - conference/room-schedule
  - conference/room-call
---

# 研讨会 / 宣讲会 Slice 映射

## 结论

如果客户描述的是 **研讨会房间 / webinar / 在线宣讲 / 线上发布会 / 全员大会 / 培训讲座 / 老师主讲型课堂**，并且其核心特征是 **主讲人中心化、观众多数以观看和聊天为主、开麦或上台受到明显控制**，那么在当前 `conference` 体系里，应优先命中的不是 `general-conference`，而是一组围绕 **主舞台、受控互动、聊天问答、主持秩序和宣讲型流程** 展开的 `webinar` 房型骨架 slices。

它和标准会议最大的区别，不是有没有聊天、共享或成员管理，而是 **互动权是否天然对称**。只要互动权长期集中在主持人 / 主讲人一侧，就更适合落到 `webinar` 房型。

## 为什么这个场景成立

### 1. 研讨会的核心不是“多人平权协作”，而是“主讲人驱动的一对多传播”

多数 webinar / 宣讲会产品里，真正长期占据主舞台的是主讲人、主持人或少量嘉宾；观众更多承担观看、聊天、提问、等待上台的角色。也就是说，这类场景虽然仍属于多人实时音视频，但**参与关系天然不对称**。

### 2. 研讨会常见的是“主舞台 + 观众侧栏 + 受控互动”

典型形态通常包括：

- 主舞台长期展示主讲人视频或屏幕共享
- 观众成员默认不与主讲人平权并列展示
- 互动入口集中在聊天、问答、举手、申请上台
- 管理员对发言权、共享权、上台权有更强控制

### 3. 培训、公开课、宣讲并不天然等于“在线教育课堂”

如果是 **双向互动课堂**，学生频繁上麦、开摄、点名互动，那么更接近 `standard` 房型上的教育外壳；如果是 **讲授式培训 / 在线宣讲 / 在线研讨会**，则更接近本文定义的 `webinar` 房型，教育或培训只是行业标签。

## 与相邻场景的区别

| 相邻场景 | 主要差异 | 推荐判断 |
|------|----------|---------|
| `general-conference` | 参会人更平权，更多人默认可上麦开摄并并列协作 | 如果多人长期平等协作，优先回到 `general-conference` |
| `online-education-classroom` | 更强调老师与学生的双向互动、点名发言和课堂秩序 | 如果学生主要看 / 聊 / 问答，而非频繁音视频互动，优先落到本文 |
| `1v1-video-consultation` | 天然双人，不存在一对多观众关系 | 一旦角色变成主讲人对大量观众，就不应再看 1v1 |

## 默认流程

| 步骤 | 阶段目标 | 主要命中 slices | 说明 |
|------|----------|-----------------|------|
| 1. 用户登录进入系统 | 建立稳定会话与身份 | `conference/login-auth` | 主讲人、主持人、嘉宾、观众都依赖统一登录态。 |
| 2. 主讲人会前准备 | 完成设备检查、画面效果和共享准备 | `conference/prejoin-check`, `conference/device-control`, `conference/screen-share` | 主讲人通常在开讲前完成音视频和演示内容准备。 |
| 3. 创建 / 加入 / 预约研讨会 | 建立 webinar 房间或确认排期 | `conference/room-lifecycle`, `conference/room-schedule` | 宣讲会、培训讲座、线上发布会通常更依赖预约和定时开始。 |
| 4. 渲染主舞台与观众侧信息 | 呈现主讲画面、共享内容、观众名单和聊天区 | `conference/video-layout`, `conference/participant-list`, `conference/room-chat` | 画面编排以主舞台优先，不应默认所有观众与主讲人平权展示。 |
| 5. 进行受控互动 | 聊天、问答、举手、申请上台、临时呼叫嘉宾 | `conference/room-chat`, `conference/participant-management`, `conference/room-call` | 研讨会的互动通常是受控开放，而不是默认全量平权。 |
| 6. 处理设备与网络异常 | 保证主讲链路稳定 | `conference/device-control`, `conference/network-quality`, `conference/room-lifecycle` | 主讲人的音视频和共享链路优先级通常更高。 |
| 7. 结束研讨会或观众离场 | 统一收口状态 | `conference/room-lifecycle`, `conference/device-control` | 主持人结束和观众离场都应有清晰收口。 |

## 需求点到 Slice 的映射

| 需求点 | 主要命中 slices | 判断原因 |
|------|------------------|---------|
| 主讲人 / 主持人 / 嘉宾 / 观众角色分层 | `conference/participant-list`, `conference/participant-management` | 研讨会高度依赖角色分层和受控授权。 |
| 主舞台长期突出主讲人或共享内容 | `conference/video-layout`, `conference/screen-share` | `webinar` 的核心就是主舞台中心化。 |
| 观众通过聊天区提问 | `conference/room-chat` | 聊天 / 问答通常是观众最稳定的互动入口。 |
| 主持人控制谁能发言、共享、聊天 | `conference/participant-management` | 这类房型最关键的是互动权治理。 |
| 临时呼叫嘉宾上台或补叫入会 | `conference/room-call`, `conference/participant-management`, `conference/room-lifecycle` | 呼叫、授权和真正入会是两段链路。 |
| 培训讲座、发布会、town hall 的预约和到点开讲 | `conference/room-schedule`, `conference/room-lifecycle` | 这类场景通常强依赖排期。 |
| 主讲人会前预览与设备确认 | `conference/prejoin-check`, `conference/device-control` | 主讲链路必须在开讲前稳定。 |
| 演示课件、产品发布、屏幕共享讲解 | `conference/screen-share`, `conference/video-layout` | 主讲内容通常由共享驱动主舞台。 |
| 观众弱互动、主讲强中心 | `conference/video-layout`, `conference/room-chat`, `conference/participant-management` | 这是 `webinar` 场景的典型命中特征。 |

## 主命中分层建议

### P0 默认骨架

这些 slice 基本覆盖了大多数 `webinar` / 研讨会产品的第一阶段默认能力，通常都应作为 `P0` 一起考虑：

- `conference/login-auth`
- `conference/prejoin-check`
- `conference/room-lifecycle`
- `conference/video-layout`
- `conference/participant-list`
- `conference/device-control`
- `conference/network-quality`
- `conference/room-chat`
- `conference/screen-share`
- `conference/participant-management`
- `conference/room-schedule`
- `conference/room-call`

### P1 按需补命中

- 行业培训壳层：报名、课表、课后回放、Q&A 面板
- 行业教育壳层：课件目录、签到、作业、白板
- 行业营销壳层：发布会页、嘉宾介绍、表单留资

## 推荐命中策略

### 用户出现以下意图时，优先命中本文

- 在线研讨会 / webinar
- 在线宣讲 / 发布会 / town hall
- 培训讲座 / 老师主讲、学员弱互动
- 大规模观看 + 受控开麦 / 上台
- 主讲人中心、观众主要聊天 / 问答

### 与在线教育的分流规则

- 如果描述是 **互动小班课 / 学生频繁上麦开摄 / 老师与学生双向互动**，优先看 `online-education-classroom.md`
- 如果描述是 **培训讲座 / 老师主讲 / 学员主要看和提问 / 上台受控**，优先看 `webinar-conference.md`

### 与标准会议的分流规则

- 如果多数成员天然平权、都可能并列开麦开摄和参与协作，优先看 `general-conference.md`
- 如果互动权明显集中在主持人 / 主讲人一侧，优先看本文

## 一句话判断

**只要场景的核心是“主讲人中心化 + 观众弱互动 + 受控发言 / 上台”，即使它外层是教育培训、企业宣讲或公开课，也应优先命中 `webinar-conference.md` 这一 `webinar` 房型基座。**
