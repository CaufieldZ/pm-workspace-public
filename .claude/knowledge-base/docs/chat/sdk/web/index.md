# Web — SDK 官方文档 URL 映射

> 知识咨询时 `read_file` 本文件，按问题匹配领域和子问题，获取目标 URL。检索方式和兜底策略见 `references/14-official-docs.md`。

## A — SDK 集成和初始化（Web & 小程序）

| 子问题 | 目标文档 |
|--------|---------|
| Web 端集成和初始化（V4） | `https://cloud.tencent.com/document/product/269/75285` |
| 小程序端集成和初始化（V4） | `https://cloud.tencent.com/document/product/269/117335` |

## B — 登录

| 子问题 | 目标文档 |
|--------|---------|
| 登录（`login` API） | `https://cloud.tencent.com/document/product/269/75295` |
| 登出（`logout` API） | `https://cloud.tencent.com/document/product/269/75295` |

## C — SDK API 使用

| 子问题 | 目标文档 |
|--------|---------|
| SDK 消息类型介绍 | `https://cloud.tencent.com/document/product/269/75314` |
| 文本消息（createTextMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75316` |
| 群 @ 消息（createTextAtMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75316` |
| 图片消息（createImageMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75316` |
| 语音消息（createVoiceMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75316` |
| 视频消息（createVideoMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75316` |
| 文件消息（createFileMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75316` |
| 自定义消息（createCustomMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75316` |
| 表情消息（createFaceMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75316` |
| 地理位置消息（createLocationMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75316` |
| 合并消息（createMergerMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75316` |
| 逐条转发消息（createForwardMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75316` |
| 发送消息参数配置（sendMessage 参数） | `https://cloud.tencent.com/document/product/269/75316` |
| 接收消息（EVENT.MESSAGE_RECEIVED） | `https://cloud.tencent.com/document/product/269/75319` |
| 获取历史消息（getMessageList） | `https://cloud.tencent.com/document/product/269/75322` |
| 修改消息（modifyMessage） | `https://cloud.tencent.com/document/product/269/75328` |
| 删除消息（deleteMessage） | `https://cloud.tencent.com/document/product/269/75333` |
| 清空消息（clearHistoryMessage） | `https://cloud.tencent.com/document/product/269/84438` |
| 撤回消息（revokeMessage） | `https://cloud.tencent.com/document/product/269/75338` |
| 在线消息 | `https://cloud.tencent.com/document/product/269/75341` |
| 已读回执（单聊/群聊） | `https://cloud.tencent.com/document/product/269/75344` |
| 查询消息（findMessage） | `https://cloud.tencent.com/document/product/269/75348` |
| 群定向消息 | `https://cloud.tencent.com/document/product/269/82987` |
| 消息免打扰（setMessageRemindType） | `https://cloud.tencent.com/document/product/269/75354` |
| 消息扩展（投票/接龙场景） | `https://cloud.tencent.com/document/product/269/84439` |
| 消息回应（表情回应） | `https://cloud.tencent.com/document/product/269/98758` |
| 消息翻译（translateText） | `https://cloud.tencent.com/document/product/269/95414` |
| 语音转文字（convertVoiceToText） | `https://cloud.tencent.com/document/product/269/106622` |
| 流式消息（TYPES.MSG_STREAM） | `https://cloud.tencent.com/document/product/269/131979` |
| 会话存储限制 | `https://cloud.tencent.com/document/product/269/75364` |
| 会话列表（getConversationList） | `https://cloud.tencent.com/document/product/269/75367` |
| 会话资料（getConversationProfile） | `https://cloud.tencent.com/document/product/269/75370` |
| 会话未读数（getTotalUnreadMessageCount） | `https://cloud.tencent.com/document/product/269/75373` |
| 置顶会话（pinConversation） | `https://cloud.tencent.com/document/product/269/75376` |
| 删除会话（deleteConversation） | `https://cloud.tencent.com/document/product/269/75379` |
| 会话草稿（setConversationDraft） | `https://cloud.tencent.com/document/product/269/95424` |
| 会话标记（markConversation） | `https://cloud.tencent.com/document/product/269/79378` |
| 会话分组 | `https://cloud.tencent.com/document/product/269/79379` |
| 群组类型和不同群类型能力介绍 | `https://cloud.tencent.com/document/product/269/75697` |
| 普通群管理 | `https://cloud.tencent.com/document/product/269/75395` |
| 群资料（getGroupProfile / updateGroupProfile） | `https://cloud.tencent.com/document/product/269/75398` |
| 群成员管理 | `https://cloud.tencent.com/document/product/269/75401` |
| 群成员资料 | `https://cloud.tencent.com/document/product/269/75404` |
| 群自定义属性 | `https://cloud.tencent.com/document/product/269/75407` |
| 群计数器（groupCounter） | `https://cloud.tencent.com/document/product/269/86617` |
| 社群（Community / 话题） | `https://cloud.tencent.com/document/product/269/75410` |
| 用户资料（getMyProfile / getUserProfile / updateMyProfile） | `https://cloud.tencent.com/document/product/269/75417` |
| 用户状态（getUserStatus / subscribeUserStatus） | `https://cloud.tencent.com/document/product/269/78125` |
| 好友管理 | `https://cloud.tencent.com/document/product/269/75420` |
| 好友分组 | `https://cloud.tencent.com/document/product/269/75423` |
| 用户黑名单 | `https://cloud.tencent.com/document/product/269/75426` |
| 关注和粉丝 | `https://cloud.tencent.com/document/product/269/105307` |
| 云端搜索消息（searchCloudMessages） | `https://cloud.tencent.com/document/product/269/114754` |
| 云端搜索用户（searchUsers） | `https://cloud.tencent.com/document/product/269/114757` |
| 云端搜索群组（searchGroups） | `https://cloud.tencent.com/document/product/269/114760` |
| 云端搜索群成员（searchGroupMembers） | `https://cloud.tencent.com/document/product/269/114763` |

## D — 版本升级指南

| 子问题 | 目标文档 |
|--------|---------|
| V4 版本日志 / Changelog | `https://cloud.tencent.com/document/product/269/38492` |
| V3 → V4 版本迁移 | `https://web.sdk.qcloud.com/im/doc/v3/zh-cn/tutorial-04-comparison-v4.html` |
| V3 → V4 破坏性变更 | `https://web.sdk.qcloud.com/im/doc/v3/zh-cn/tutorial-04-comparison-v4.html` |
| V3 版本日志 / Changelog | `https://cloud.tencent.com/document/product/269/124855` |
| V2 → V3 版本迁移 | `https://web.sdk.qcloud.com/im/doc/v3/zh-cn/tutorial-06-comparison.html` |
| V2 → V3 破坏性变更 | `https://web.sdk.qcloud.com/im/doc/v3/zh-cn/tutorial-07-breakingchanges.html` |

## E — 错误码（SDK 错误码）

> 错误码查询策略见 `references/14-official-docs.md §14.4`

| 子问题 | 目标文档 |
|--------|---------|
| Web SDK 错误码表（1xxx-8xxx 范围） | `https://web.sdk.qcloud.com/im/doc/v3/zh-cn/module-ERROR_CODE.html` |
