# Web — SDK 官方文档 URL 映射

> 知识咨询时 `read_file` 本文件，按问题匹配领域和子问题，获取目标 URL。检索方式和兜底策略见 `references/14-official-docs.md`。

## A — SDK 集成和初始化（Flutter）

| 子问题 | 目标文档 |
|--------|---------|
| Flutter SDK 集成 | `https://cloud.tencent.com/document/product/269/75286` |
| Flutter SDK 初始化 | `https://cloud.tencent.com/document/product/269/75293` |

## B — 多端登录配置与 UserSig 鉴权

| 子问题 | 目标文档 |
|--------|---------|
| 登录（`login` API） | `https://cloud.tencent.com/document/product/269/75296` |
| 登出（`logout` API） | `https://cloud.tencent.com/document/product/269/75296` |

## C — SDK API 使用

| 子问题 | 目标文档 |
|--------|---------|
| SDK 消息类型介绍 | `https://cloud.tencent.com/document/product/269/75674` |
| 文本消息（createTextMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75317` |
| 群 @ 消息（createTextAtMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75350` |
| 图片消息（createImageMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75317` |
| 语音消息（createSoundMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75317` |
| 视频消息（createVideoMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75317` |
| 文件消息（createFileMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75317` |
| 自定义消息（createCustomMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75317` |
| 表情消息（createFaceMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75315` |
| 地理位置消息（createLocationMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75315` |
| 合并消息（createMergerMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75326` |
| 逐条转发消息（createForwardMessage → sendMessage） | `https://cloud.tencent.com/document/product/269/75326` |
| 发送消息参数配置（sendMessage 参数） | `https://cloud.tencent.com/document/product/269/75317` |
| 接收消息（addAdvancedMsgListener） | `https://cloud.tencent.com/document/product/269/75320` |
| 获取历史消息（getC2CHistoryMessageList/getGroupHistoryMessageList/getHistoryMessageList） | `https://cloud.tencent.com/document/product/269/75323` |
| 修改消息（modifyMessage） | `https://cloud.tencent.com/document/product/269/75329` |
| 插入消息（insertC2CMessageToLocalStorage/insertGroupMessageToLocalStorage） | `https://cloud.tencent.com/document/product/269/75331` |
| 删除消息（deleteMessageFromLocalStorage/deleteMessages） | `https://cloud.tencent.com/document/product/269/75334` |
| 清空消息（clearC2CHistoryMessage/clearGroupHistoryMessage） | `https://cloud.tencent.com/document/product/269/75336` |
| 撤回消息（revokeMessage） | `https://cloud.tencent.com/document/product/269/75339` |
| 在线消息 | `https://cloud.tencent.com/document/product/269/75342` |
| 已读回执（单聊/群聊） | `https://cloud.tencent.com/document/product/269/75345` |
| 查询消息（findMessages） | `https://cloud.tencent.com/document/product/269/75347` |
| 群定向消息(createXXXMessage -> createTargetedGroupMessage -> sendMessage) | `https://cloud.tencent.com/document/product/269/75352` |
| 消息免打扰（setC2CReceiveMessageOpt/setGroupReceiveMessageOpt） | `https://cloud.tencent.com/document/product/269/75355` |
| 消息扩展（投票/接龙场景） | `https://cloud.tencent.com/document/product/269/83722` |
| 会话存储限制 | `https://cloud.tencent.com/document/product/269/75365` |
| 会话列表（getConversationList） | `https://cloud.tencent.com/document/product/269/75368` |
| 会话资料（getConversation） | `https://cloud.tencent.com/document/product/269/75371` |
| 会话未读数（getTotalUnreadMessageCount） | `https://cloud.tencent.com/document/product/269/75374` |
| 置顶会话（pinConversation） | `https://cloud.tencent.com/document/product/269/75377` |
| 删除会话（deleteConversation） | `https://cloud.tencent.com/document/product/269/75380` |
| 会话草稿（setConversationDraft） | `https://cloud.tencent.com/document/product/269/75382` |
| 会话标记（markConversation） | `https://cloud.tencent.com/document/product/269/79694` |
| 会话分组 | `https://cloud.tencent.com/document/product/269/79695` |
| 群组类型和不同群类型能力介绍 | `https://cloud.tencent.com/document/product/269/75697` |
| 普通群管理 | `https://cloud.tencent.com/document/product/269/75396` |
| 群资料（getGroupsInfo / setGroupInfo） | `https://cloud.tencent.com/document/product/269/75399` |
| 群成员管理 | `https://cloud.tencent.com/document/product/269/75402` |
| 群成员资料 | `https://cloud.tencent.com/document/product/269/75405` |
| 群自定义属性 | `https://cloud.tencent.com/document/product/269/75408` |
| 社群（Community / 话题） | `https://cloud.tencent.com/document/product/269/75411` |
| 社群（权限组） | `https://cloud.tencent.com/document/product/269/127846` |
| 用户资料（getUsersInfo / setSelfInfo） | `https://cloud.tencent.com/document/product/269/75418` |
| 用户状态（getUserStatus / subscribeUserStatus） | `https://cloud.tencent.com/document/product/269/105469` |
| 好友管理 | `https://cloud.tencent.com/document/product/269/75421` |
| 好友分组 | `https://cloud.tencent.com/document/product/269/75424` |
| 用户黑名单 | `https://cloud.tencent.com/document/product/269/75427` |
| 关注和粉丝 | `https://cloud.tencent.com/document/product/269/110774` |
| 本地搜索消息（searchLocalMessages） | `https://cloud.tencent.com/document/product/269/75438` |
| 本地搜索好友（searchFriends） | `https://cloud.tencent.com/document/product/269/75440` |
| 本地搜索群组（searchGroups） | `https://cloud.tencent.com/document/product/269/75442` |
| 本地搜索群成员（searchGroupMembers） | `https://cloud.tencent.com/document/product/269/75444` |

## D — 错误码（SDK 错误码）

> 错误码查询策略见 `references/14-official-docs.md §14.4`

| 子问题 | 目标文档 |
|--------|---------|
| Flutter SDK 错误码表 | `https://cloud.tencent.com/document/product/269/1671` |
