# Web — SDK 官方文档 URL 映射

> 知识咨询时 `read_file` 本文件，按问题匹配领域和子问题，获取目标 URL。检索方式和兜底策略见 `references/14-official-docs.md`。

## A — SDK 集成和初始化（iOS）

| 子问题 | 目标文档 |
|--------|---------|
| iOS SDK 集成 | `https://cloud.tencent.com/document/product/269/75284` |
| iOS SDK 初始化 | `https://cloud.tencent.com/document/product/269/75291` |

## B — 登录

| 子问题 | 目标文档 |
|--------|---------|
| 登录（`login` API） | `https://cloud.tencent.com/document/product/269/75294` |
| 登出（`logout` API） | `https://cloud.tencent.com/document/product/269/75294` |

## C — SDK API 使用

| 子问题 | 目标文档 |
|--------|---------|
| SDK 消息类型介绍 | `https://cloud.tencent.com/document/product/269/75313` |
| 文本消息（sendC2CMessage/sendGroupTextMessage） | `https://cloud.tencent.com/document/product/269/75315` |
| 群 @ 消息（createAtSignedGroupMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75349` |
| 图片消息（createImageMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75315` |
| 语音消息（createSoundMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75315` |
| 视频消息（createVideoMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75315` |
| 文件消息（createFileMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75315` |
| 自定义消息（sendC2CCustomMessage/sendGroupCustomMessage） | `https://cloud.tencent.com/document/product/269/75315` |
| 表情消息（createFaceMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75315` |
| 地理位置消息（createLocationMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75315` |
| 合并消息（createMergerMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75324` |
| 逐条转发消息（createForwardMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75324` |
| 发送消息参数配置（sendMessage 参数） | `https://cloud.tencent.com/document/product/269/75315` |
| 接收消息（addSimpleMsgListener/addAdvancedMsgListener） | `https://cloud.tencent.com/document/product/269/75318` |
| 获取历史消息（getC2CHistoryMessageList/getGroupHistoryMessageList/getHistoryMessageList） | `https://cloud.tencent.com/document/product/269/75321` |
| 修改消息（modifyMessage） | `https://cloud.tencent.com/document/product/269/75327` |
| 插入消息（insertC2CMessageToLocalStorage/insertGroupMessageToLocalStorage） | `https://cloud.tencent.com/document/product/269/75330` |
| 删除消息（deleteMessageFromLocalStorage/deleteMessages） | `https://cloud.tencent.com/document/product/269/75332` |
| 清空消息（clearC2CHistoryMessage/clearGroupHistoryMessage） | `https://cloud.tencent.com/document/product/269/75335` |
| 撤回消息（revokeMessage） | `https://cloud.tencent.com/document/product/269/75337` |
| 在线消息 | `https://cloud.tencent.com/document/product/269/75340` |
| 已读回执（单聊/群聊） | `https://cloud.tencent.com/document/product/269/75343` |
| 查询消息（findMessages） | `https://cloud.tencent.com/document/product/269/75346` |
| 群定向消息 | `https://cloud.tencent.com/document/product/269/75351` |
| 消息免打扰（setC2CReceiveMessageOpt/setGroupReceiveMessageOpt/setAllReceiveMessageOpt） | `https://cloud.tencent.com/document/product/269/75353` |
| 消息扩展（投票/接龙场景） | `https://cloud.tencent.com/document/product/269/81038` |
| 消息回应（表情回应） | `https://cloud.tencent.com/document/product/269/96241` |
| 消息翻译（translateText） | `https://cloud.tencent.com/document/product/269/85380` |
| 语音转文字（convertVoiceToText） | `https://cloud.tencent.com/document/product/269/96280` |
| 消息置顶（pinGroupMessage） | `https://cloud.tencent.com/document/product/269/106050` |
| 流式消息（V2TIM_ELEM_TYPE_STREAM） | `https://cloud.tencent.com/document/product/269/129557` |
| 文字转语音 | `https://cloud.tencent.com/document/product/269/131939` |
| 会话存储限制 | `https://cloud.tencent.com/document/product/269/75363` |
| 会话列表（getConversationList） | `https://cloud.tencent.com/document/product/269/75366` |
| 会话资料（getConversation） | `https://cloud.tencent.com/document/product/269/75369` |
| 会话未读数（getTotalUnreadMessageCount） | `https://cloud.tencent.com/document/product/269/75372` |
| 置顶会话（pinConversation） | `https://cloud.tencent.com/document/product/269/75375` |
| 删除会话（deleteConversation） | `https://cloud.tencent.com/document/product/269/75378` |
| 会话草稿（setConversationDraft） | `https://cloud.tencent.com/document/product/269/75381` |
| 会话标记（markConversation） | `https://cloud.tencent.com/document/product/269/77389` |
| 会话分组 | `https://cloud.tencent.com/document/product/269/77392` |
| 群组类型和不同群类型能力介绍 | `https://cloud.tencent.com/document/product/269/75697` |
| 普通群管理 | `https://cloud.tencent.com/document/product/269/75395` |
| 群资料（getGroupsInfo / setGroupInfo） | `https://cloud.tencent.com/document/product/269/75397` |
| 群成员管理 | `https://cloud.tencent.com/document/product/269/75400` |
| 群成员资料 | `https://cloud.tencent.com/document/product/269/75403` |
| 群自定义属性 | `https://cloud.tencent.com/document/product/269/75406` |
| 群计数器（groupCounter） | `https://cloud.tencent.com/document/product/269/85676` |
| 社群（Community / 话题） | `https://cloud.tencent.com/document/product/269/75409` |
| 社群（权限组） | `https://cloud.tencent.com/document/product/269/104417` |
| 用户资料（getUsersInfo / setSelfInfo） | `https://cloud.tencent.com/document/product/269/75416` |
| 用户状态（getUserStatus / subscribeUserStatus） | `https://cloud.tencent.com/document/product/269/75511` |
| 好友管理 | `https://cloud.tencent.com/document/product/269/75419` |
| 好友分组 | `https://cloud.tencent.com/document/product/269/75422` |
| 用户黑名单 | `https://cloud.tencent.com/document/product/269/75425` |
| 关注和粉丝 | `https://cloud.tencent.com/document/product/269/105494` |
| 云端搜索消息（searchCloudMessages） | `https://cloud.tencent.com/document/product/269/115824` |
| 云端搜索用户（searchUsers） | `https://cloud.tencent.com/document/product/269/115825` |
| 云端搜索群组（searchGroups） | `https://cloud.tencent.com/document/product/269/115826` |
| 云端搜索群成员（searchGroupMembers） | `https://cloud.tencent.com/document/product/269/115827` |
| 本地搜索消息（searchLocalMessages） | `https://cloud.tencent.com/document/product/269/75436` |
| 本地搜索好友（searchFriends） | `https://cloud.tencent.com/document/product/269/75439` |
| 本地搜索群组（searchGroups） | `https://cloud.tencent.com/document/product/269/75441` |
| 本地搜索群成员（searchGroupMembers） | `https://cloud.tencent.com/document/product/269/75443` |

## D — 错误码（SDK 错误码）

> 错误码查询策略见 `references/14-official-docs.md §14.4`

| 子问题 | 目标文档 |
|--------|---------|
| iOS SDK 错误码表 | `https://cloud.tencent.com/document/product/269/1671` |
