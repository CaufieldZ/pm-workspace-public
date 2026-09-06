# troubleshooting — 排障

hx-cli 常见错误和定位顺序。

## 链接生成排障

火效 Web base 固定是 `https://INTERNAL_URL_REDACTED connector base `https://INTERNAL_URL_REDACTED 只用于 API，不是给用户点击的页面地址。

常见修正：

- 工作项详情：用 `https://INTERNAL_URL_REDACTED<work_id>`，不要用项目 id、`work_type_id`、`work_manager.id` 或 `checker_id`。
- 代码管理 V2（只读查看时）：仍给 `https://INTERNAL_URL_REDACTED<work_id>`，并说明打开「代码管理」tab；不要拼 `?tab=8` 或独立 V2 path。
- 提测单：只有提测历史记录 id 才能生成 `https://INTERNAL_URL_REDACTED<history_id>`；只有 `checker_id` 时给工作项链接和 `/pre-test-checker` 列表入口。
- GitLab（只读查看时）：只使用返回的 `web_url`、`http_url_to_repo`、MR URL，不从 SSH 地址猜域名。

## 错误码

| code | 含义 | 处理 |
|------|------|------|
| `not_logged_in` | 没有可用 AIHUB token | 提示用户设置 `AIHUB_TOKEN`，或对单次命令传 `--token <token>` |
| `unauthorized` | AIHUB token 错误、过期、无权限，或 AIHUB 到 HX 的代理鉴权失败 | 让用户刷新 AIHUB token 后重试；若新 token 仍失败，检查 AIHUB connector `hx` 配置、HX 后端 AKSK、域账号透传与权限 |
| `session_expired` | AIHUB GA session 不存在或已过期 | 请用户提供 TOTP APP 6 位验证码，执行 `hx-cli auth login --ga-code <code>` 后重试 |
| `40103` | GA 验证码错误或过期 | 让用户重新给当前码（30s 一变），不复用旧码 |
| `40104` | 未绑定 GA | 走下方「GA 绑定」流程 |
| `42901` | 绑定请求过于频繁 | 等 1 小时后再试 bindreq |
| `http_error` | 二进制收到非 JSON 4xx，响应体被吞 | 用 curl 直调同一路径复核，拿真实错误码（见「GA 绑定」节） |
| `network_error` | 网络/DNS/超时 | 重试或检查环境 |
| `decode_error` | AIHUB connector 返回的不是 HX JSON，例如 `text/html` 前端页面 | 检查 connector 路由是否命中；若 curl 同一路径也是 HTML，说明问题在 AIHUB 路由/connector 配置，不是 CLI JSON 解析 |
| `api_error` | 后端业务错误 | 看 `msg`，必要时用查询命令缩小范围 |
| `flag_error` | CLI 参数错误 | 读 `hx-cli <command> --help` |

## AIHUB 鉴权问题

所有 API 都通过 AIHUB 代理：

```bash
https://INTERNAL_URL_REDACTED
```

请求头固定是：

```text
Authorization: Bearer <AIHUB token>
Content-Type: application/json
```

处理顺序：

1. 先执行 `hx-cli status`，确认 `data.logged_in=true` 且 `data.source` 是 `env` 或 `flag`。
2. 如果是 `not_logged_in`，让用户设置 `AIHUB_TOKEN`，或改用 `hx-cli --token <token> user` 验证单次 token。
3. 如果是 `session_expired` 或消息含 `40102` / `Session 已过期`，请用户给 GA 验证码，执行 `hx-cli auth login --ga-code <code>`。
4. 如果返回 `40104` 或提示未绑定 GA，走下方「GA 绑定」流程。
5. 如果是 `unauthorized` / 401 / 403 且不是 session 过期，让用户在 AIHUB 刷新 token。
6. 如果是 `decode_error` 且提示 `non-json response` / `text/html`，用 curl 复核同一路径；若仍是 AIHUB 前端 HTML，检查 `/ai-connector/hx/...` 是否被正确路由到 connector。
7. 如果新 token 和 GA session 都仍失败，记录接口、时间、错误码，检查 AIHUB 的 `hx` connector 是否仍带 HX 后端 AKSK 签名和当前用户域账号。
8. 不要把 token 或 GA 验证码原文写进对话、日志或排障说明里。

## GA 绑定（curl 直调）

GA 认证 / 绑定接口路径是 `https://INTERNAL_URL_REDACTED `/hx` 段**），与业务 API（`/ai-connector/hx/...`）不同，别混用——打错路径（多带 `/hx`）会收到包着 nginx 405 页面的 `code:0` 响应。二进制 `auth ga bindreq` 已知返回无响应体的 400（`http_error`），绑定时用 curl 直调：

```bash
# 申请绑定：body 必须为 {}（平台官方口径）；返回 qr_uri / secret 给用户扫 TOTP APP
curl -sS -X POST "https://INTERNAL_URL_REDACTED" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $AIHUB_TOKEN" \
  -d '{}'

# 确认绑定：用户扫完给当前 6 位码
curl -sS -X POST "https://INTERNAL_URL_REDACTED" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $AIHUB_TOKEN" \
  -d '{"ga_code":"<6位码>"}'
```

登录续 session 的 curl 等价形式（排障复核用，日常仍走二进制）：

```bash
curl -sS -X POST "https://INTERNAL_URL_REDACTED" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $AIHUB_TOKEN" \
  -d '{"ga_code":"<6位码>"}'
```

`42901 绑定请求过于频繁` = 频控，等 1 小时再试。

## `work create` 失败

按顺序检查：

1. `--owner-id` 是否 PM staff id，而不是 user id。
2. 是否传了当前项目的 `work_type_id`。
3. 创建研发任务是否传 leaf `--new-work-type-id`。
4. 首流程无默认执行人时是否传 `--first-process-item-executor`。
5. 是否需要 `--owner-dept-id`。

## 代码管理 V2 / repo 写操作排障

本 skill 不含代码管理 V2 / repo 写操作（开始开发、打 TAG、发起评审、合回、建分支、提测单创建、安全提测）的排障——这些属于研发发布链路。如遇 `repo flow ...` / `safe submit` 等命令失败，建议联系研发同事在火效 Web 端处理，或参考完整版 hx-cli 文档。
