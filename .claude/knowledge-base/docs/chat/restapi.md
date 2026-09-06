# 服务端 REST API — 官方文档 URL 映射

### 通用技术

| 子问题 | 目标文档 |
|--------|---------|
| UserSig 生成方法（登录鉴权） | `https://cloud.tencent.com/document/product/269/32688` |
| 服务端错误码表 | `https://cloud.tencent.com/document/product/269/1671` |
| 服务端消息格式 | `https://cloud.tencent.com/document/product/269/2720` |

## 消息相关 REST API

### 发送消息

| 子问题 | 目标文档 |
|--------|---------|
| 单发单聊消息 | `https://cloud.tencent.com/document/product/269/2282` |
| 批量发单聊消息 | `https://cloud.tencent.com/document/product/269/1612` |
| 在群组中发送普通消息 | `https://cloud.tencent.com/document/product/269/1629` |
| 发送 C2C 流式消息 | `https://cloud.tencent.com/document/product/269/128596` |
| 发送群流式消息 | `https://cloud.tencent.com/document/product/269/128597` |
| 直播群广播消息 | `https://cloud.tencent.com/document/product/269/77402` |
| 导入群消息 | `https://cloud.tencent.com/document/product/269/1635` |
| 导入单聊消息 | `https://cloud.tencent.com/document/product/269/2568` |
| 公众号用户发送广播消息 | `https://cloud.tencent.com/document/product/269/102298` |

### 历史消息

| 子问题 | 目标文档 |
|--------|---------|
| 修改单聊历史消息 | `https://cloud.tencent.com/document/product/269/74740` |
| 修改群聊历史消息 | `https://cloud.tencent.com/document/product/269/74741` |
| 拉取单聊历史消息 | `https://cloud.tencent.com/document/product/269/42794` |
| 拉取群聊历史消息 | `https://cloud.tencent.com/document/product/269/2738` |
| 拉取公众号用户历史消息 | `https://cloud.tencent.com/document/product/269/102299` |

### 删除消息

| 子问题 | 目标文档 |
|--------|---------|
| 单向删除单聊历史消息 | `https://cloud.tencent.com/document/product/269/101439` |
| 清空群聊历史消息 | `https://cloud.tencent.com/document/product/269/95617` |
| 删除指定用户发送的消息 | `https://cloud.tencent.com/document/product/269/2359` |

### 撤回消息

| 子问题 | 目标文档 |
|--------|---------|
| 撤回单聊消息 | `https://cloud.tencent.com/document/product/269/38980` |
| 撤回群消息 | `https://cloud.tencent.com/document/product/269/12341` |
| 撤回公众号消息 | `https://cloud.tencent.com/document/product/269/102327` |

### 已读回执

| 子问题 | 目标文档 |
|--------|---------|
| 群消息已读回执 | `https://cloud.tencent.com/document/product/269/107478` |
| 发送单聊消息已读回执 | `https://cloud.tencent.com/document/product/269/104121` |
| 拉取群消息已读回执详情 | `https://cloud.tencent.com/document/product/269/77693` |
| 拉取群消息已读回执信息 | `https://cloud.tencent.com/document/product/269/77694` |

### 消息扩展

| 子问题 | 目标文档 |
|--------|---------|
| 拉取单聊消息扩展 | `https://cloud.tencent.com/document/product/269/82029` |
| 设置单聊消息扩展 | `https://cloud.tencent.com/document/product/269/82030` |
| 拉取群消息扩展 | `https://cloud.tencent.com/document/product/269/82031` |
| 设置群消息扩展 | `https://cloud.tencent.com/document/product/269/82032` |

## 会话相关 REST API

### 会话基础能力

| 子问题 | 目标文档 |
|--------|---------|
| 拉取会话列表 | `https://cloud.tencent.com/document/product/269/62118` |
| 设置群成员未读消息计数 | `https://cloud.tencent.com/document/product/269/1637` |
| 清理单聊会话的未读消息计数 | `https://cloud.tencent.com/document/product/269/50349` |
| 设置置顶会话 | `https://cloud.tencent.com/document/product/269/103772` |
| 删除单个会话 | `https://cloud.tencent.com/document/product/269/62119` |

### 会话分组标记

| 子问题 | 目标文档 |
|--------|---------|
| 创建会话分组数据 | `https://cloud.tencent.com/document/product/269/85791` |
| 更新会话分组数据 | `https://cloud.tencent.com/document/product/269/85793` |
| 删除会话分组数据 | `https://cloud.tencent.com/document/product/269/85795` |
| 创建或更新会话标记数据 | `https://cloud.tencent.com/document/product/269/85792` |
| 搜索会话分组标记 | `https://cloud.tencent.com/document/product/269/85796` |
| 拉取会话分组标记数据 | `https://cloud.tencent.com/document/product/269/85794` |

## 群组相关 REST API

### 群组管理

| 子问题 | 目标文档 |
|--------|---------|
| 创建群组 | `https://cloud.tencent.com/document/product/269/1615` |
| 解散群组 | `https://cloud.tencent.com/document/product/269/1624` |
| 获取用户所加入的群组 | `https://cloud.tencent.com/document/product/269/1625` |
| 获取 App 中的所有群组 | `https://cloud.tencent.com/document/product/269/1614` |

### 群资料

| 子问题 | 目标文档 |
|--------|---------|
| 获取群详细资料 | `https://cloud.tencent.com/document/product/269/1616` |
| 修改群基础资料 | `https://cloud.tencent.com/document/product/269/1620` |
| 导入群基础资料 | `https://cloud.tencent.com/document/product/269/1634` |

### 群成员管理

| 子问题 | 目标文档 |
|--------|---------|
| 增加群成员 | `https://cloud.tencent.com/document/product/269/1621` |
| 删除群成员 | `https://cloud.tencent.com/document/product/269/1622` |
| 群成员封禁 | `https://cloud.tencent.com/document/product/269/79249` |
| 群成员解封 | `https://cloud.tencent.com/document/product/269/79250` |
| 获取封禁群成员列表 | `https://cloud.tencent.com/document/product/269/79248` |
| 批量禁言和取消禁言 | `https://cloud.tencent.com/document/product/269/1627` |
| 获取被禁言群成员列表 | `https://cloud.tencent.com/document/product/269/2925` |
| 转让群主 | `https://cloud.tencent.com/document/product/269/1633` |
| 查询用户在群组中的身份 | `https://cloud.tencent.com/document/product/269/1626` |
| 导入群成员 | `https://cloud.tencent.com/document/product/269/1636` |

### 群成员资料

| 子问题 | 目标文档 |
|--------|---------|
| 获取群成员详细资料 | `https://cloud.tencent.com/document/product/269/1617` |
| 获取指定群成员详细资料 | `https://cloud.tencent.com/document/product/269/112002` |
| 修改群成员资料 | `https://cloud.tencent.com/document/product/269/1623` |

### 群自定义属性

| 子问题 | 目标文档 |
|--------|---------|
| 获取群自定义属性 | `https://cloud.tencent.com/document/product/269/67012` |
| 修改群自定义属性 | `https://cloud.tencent.com/document/product/269/67010` |
| 清空群自定义属性 | `https://cloud.tencent.com/document/product/269/67009` |
| 重置群自定义属性 | `https://cloud.tencent.com/document/product/269/67011` |
| 删除群自定义属性 | `https://cloud.tencent.com/document/product/269/104440` |

### 直播群管理

| 子问题 | 目标文档 |
|--------|---------|
| 设置直播群机器人 | `https://cloud.tencent.com/document/product/269/103784` |
| 取消直播群机器人 | `https://cloud.tencent.com/document/product/269/103785` |
| 设置/取消直播群管理员 | `https://cloud.tencent.com/document/product/269/102857` |
| 获取直播群管理员列表 | `https://cloud.tencent.com/document/product/269/102858` |
| 获取直播群在线人数 | `https://cloud.tencent.com/document/product/269/49180` |
| 获取直播群在线成员列表 | `https://cloud.tencent.com/document/product/269/77266` |
| 设置直播群成员标记 | `https://cloud.tencent.com/document/product/269/79267` |

### 社群管理

| 子问题 | 目标文档 |
|--------|---------|
| 创建话题 | `https://cloud.tencent.com/document/product/269/78203` |
| 解散话题 | `https://cloud.tencent.com/document/product/269/78202` |
| 获取话题资料 | `https://cloud.tencent.com/document/product/269/78204` |
| 修改话题资料 | `https://cloud.tencent.com/document/product/269/78205` |
| 导入话题基础资料 | `https://cloud.tencent.com/document/product/269/85313` |
| 获取社群在线人数 | `https://cloud.tencent.com/document/product/269/102707` |

### 群计数器

| 子问题 | 目标文档 |
|--------|---------|
| 获取群计数器 | `https://cloud.tencent.com/document/product/269/85953` |
| 更新群计数器 | `https://cloud.tencent.com/document/product/269/85952` |
| 删除群计数器 | `https://cloud.tencent.com/document/product/269/85954` |

## 用户相关 REST API

### 账号管理

| 子问题 | 目标文档 |
|--------|---------|
| 导入单个账号 | `https://cloud.tencent.com/document/product/269/1608` |
| 导入多个账号 | `https://cloud.tencent.com/document/product/269/4919` |
| 查询账号 | `https://cloud.tencent.com/document/product/269/38417` |
| 删除账号 | `https://cloud.tencent.com/document/product/269/36443` |

### 用户资料管理

| 子问题 | 目标文档 |
|--------|---------|
| 获取用户资料 | `https://cloud.tencent.com/document/product/269/1639` |
| 设置用户资料 | `https://cloud.tencent.com/document/product/269/1640` |

### 用户在线状态

| 子问题 | 目标文档 |
|--------|---------|
| 查询账号在线状态 | `https://cloud.tencent.com/document/product/269/2566` |
| 失效账号登录状态 | `https://cloud.tencent.com/document/product/269/3853` |


### 全局禁言管理

| 子问题 | 目标文档 |
|--------|---------|
| 设置全局禁言 | `https://cloud.tencent.com/document/product/269/4230` |
| 查询全局禁言 | `https://cloud.tencent.com/document/product/269/4229` |

### 云端搜索

| 子问题 | 目标文档 |
|--------|---------|
| 用户搜索 | `https://cloud.tencent.com/document/product/269/114547` |
| 群成员搜索 | `https://cloud.tencent.com/document/product/269/114548` |
| 群组搜索 | `https://cloud.tencent.com/document/product/269/114549` |
| 隐藏搜索对象 | `https://cloud.tencent.com/document/product/269/114550` |
| 查询隐藏搜索对象 | `https://cloud.tencent.com/document/product/269/114551` |

### 机器人

| 子问题 | 目标文档 |
|--------|---------|
| 发送流式响应消息 | `https://cloud.tencent.com/document/product/269/104537` |
| 创建机器人 | `https://cloud.tencent.com/document/product/269/89991` |
| 删除机器人 | `https://cloud.tencent.com/document/product/269/89992` |
| 获取取所有机器人 | `https://cloud.tencent.com/document/product/269/89993` |
