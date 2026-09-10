# Platform C Square（WordPress）API 画像 — 一次探测长期引用

> 2026-09-08 全量实测（鉴权 / 网络 / 语言 / 分类 / 块结构 / 互链 / 节流）。发布相关事实以本文件为准，**不用重新 probe**；站点改版或脚本报错与本文不符时，按文末「重新探测」重跑并更新本文件。

## 站点基本盘

- 站点：https://square.example.com（Platform C Square；WordPress.com 托管 + Jetpack；AIOSEO / Elementor / Polylang 在跑）
- 鉴权：Application Password（Basic auth；`.env` 三件套 WP_SITE / WP_USER / WP_APP_PASSWORD）
- **匿名 REST 全关**（`rest_login_required`）——一切请求带鉴权，含只读
- 网络：本机直连被墙，必须走 Clash（`scripts/proxy_env.sh` 判定）
- 账号：jacky.lau（editor；publish_posts + upload_files 可，**装插件 / 管理员操作不可**）
- 节流：连续建帖过快 → HTTP 429，等 30～60s（wp_publish.py 已内建 45s 自动重试）

## 语言（Polylang · GET /wp-json/pll/v1/languages）

| slug | 名称 | locale |
|---|---|---|
| zh | 中文（中国） | zh_CN |
| en | English（**站点默认**） | en_US |
| ru | Русский | ru_RU |
| ur | اردو | ur |

**铁律**：建帖必须带 `?lang={slug}` query。缺省按 en 落库，Polylang 把非英文分类**重映射成英文**（实测：发「产品更新」ID 落库变 Product Updates ID）。

## 宣发常用分类（按名精确解析 · 禁自建）

| 语境 | zh | en | ru |
|---|---|---|---|
| 产品更新 | 产品更新 (762487135) | Product Updates (762487137) | Обновления продукта (762487202) |
| 活动运营 | 平台活动 (762486953) | Events Hub (762486967) | Центр мероприятий (762486969) |
| 市场内容 | 市场观察 (762485460) | Market Watch (762484459) | Обзор Рынка (762485469) |
| 教程 | 学习教程 (762485456) | Tutorials (2932) | Руководства (762485457) |

（名称后括号为 term ID，信息性；脚本按名解析不依赖 ID。全量：`GET /wp/v2/categories?per_page=100` 带鉴权）

## 文章格式（三语各抽 3 篇已发布实证）

- 纯 Gutenberg 块标记、零 Markdown、**零 emoji（9/9，连 ✅ 都无）**；标题可带感叹号
- 公告体块序列：头图 → 导语段 → 卖点列表（3～4 条裸列表）→ CTA 段；**无小标题**；300～800 字
- 头图必有（featured_media + 正文顶部 image 块；文件名 CN- / RU- 前缀惯例）；标签 0～1 个；摘要可选
- 速递体（多功能合集）：导语 →（段落 + 配图）×N → 结尾

## 三语互链（Polylang translations）— 走不了 REST（实测）

- `meta._translations` 为 protected meta：写入被静默忽略
- `translations` body 字段未注册；`pll/v1` 只有 languages / settings 路由
- **结论**：三语三帖 REST 各自独立发布（各归各语言分类，语言树内正常展示）；要互链 → wp-admin 编辑页 Polylang 语言面板手动关联，或升级 Polylang Pro

## 端点速查（全部带 Basic auth）

| 操作 | 端点 |
|---|---|
| 建帖 | `POST /wp-json/wp/v2/posts?lang=zh` body `{title, content, status, excerpt, categories[], tags[], featured_media}` → 201 |
| 回读 | `GET /wp-json/wp/v2/posts/{id}?context=edit`（content.raw 即存储原文） |
| 传图 | `POST /wp-json/wp/v2/media`（二进制 body + `Content-Type` + `Content-Disposition: attachment; filename=`）→ 201 `{id, source_url}` |
| 分类/标签查 ID | `GET /wp-json/wp/v2/{categories\|tags}?search={名}&per_page=100`（**写操作只收 term ID 不收名**） |
| 删帖 | `DELETE /wp-json/wp/v2/posts/{id}`（进回收站，30 天可恢复） |
| 语言表 | `GET /wp-json/pll/v1/languages` |
| 路由总表 | `GET /wp-json/`（需鉴权） |

## 重新探测（漂移时）

```bash
source .env && source scripts/proxy_env.sh
curl -u "$WP_USER:$WP_APP_PASSWORD" "$WP_SITE/wp-json/wp/v2/categories?per_page=100&_fields=id,name,count"   # 分类
curl -u "$WP_USER:$WP_APP_PASSWORD" "$WP_SITE/wp-json/pll/v1/languages"                                        # 语言
curl -u "$WP_USER:$WP_APP_PASSWORD" "$WP_SITE/wp-json/wp/v2/posts?status=publish&per_page=3&context=edit"      # 块结构抽样
```

探测结论更新回本文件（分类表 / 语言表 / 格式规律），不要只留在会话里。
