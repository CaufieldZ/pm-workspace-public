# user — AIHUB token 状态与当前用户

查看 AIHUB token 状态、当前用户、PM staff id。

## 用户可见链接

火效 Web base 见 `SKILL.md`：`https://INTERNAL_URL_REDACTED

| 对象 | 链接模式 | 说明 |
|------|----------|------|
| 当前用户个人资料页 | `https://INTERNAL_URL_REDACTED | 用户明确要打开/查看火效个人资料页时给。 |

不要把 `https://INTERNAL_URL_REDACTED 作为用户可点击的火效页面链接；它是 CLI/API 调用地址。

## 命令

| 目标 | 命令 |
|------|------|
| AIHUB token 状态 | `hx-cli status` |
| AIHUB session 检查 | `hx-cli auth check` |
| GA 认证 session | `hx-cli auth login --ga-code <6位验证码>` |
| 申请绑定 GA | `hx-cli auth ga bindreq` |
| 确认绑定 GA | `hx-cli auth ga bindconfirm --ga-code <6位验证码>` |
| 使用环境变量 token | `AIHUB_TOKEN=<token> hx-cli user` |
| 单次命令指定 token | `hx-cli --token <token> user` |
| 当前用户 | `hx-cli user` |
| 当前用户 staff id | `hx-cli user` 后看 `pm_staff_pk` 或同义 staff 字段 |

## 工作流

1. 写操作前先跑 `hx-cli status`。
2. 如果需要确认 GA session 是否有效，先跑 `hx-cli auth check`。
3. 需要负责人/执行人时跑 `hx-cli user`，使用 PM staff id，不要用用户 id。
4. token 失效时，提示用户刷新 AIHUB token，并设置 `AIHUB_TOKEN` 或使用单次 `--token`。
5. session 过期时，直接向用户索要 TOTP APP 当前 6 位 GA 验证码，执行 `hx-cli auth login --ga-code <code>` 后重试原命令；不要把验证码写进可复用示例里。

## AIHUB Token 流程

所有请求通过 AIHUB connector 代理到 HX：

```bash
https://INTERNAL_URL_REDACTED
```

CLI 请求头固定为：

```text
Authorization: Bearer <AIHUB token>
Content-Type: application/json
```

token 解析优先级：

| 来源 | 示例 | 说明 |
|------|------|------|
| `--token` | `hx-cli --token <token> user` | 只影响当前命令，优先级最高 |
| `AIHUB_TOKEN` | `export AIHUB_TOKEN=<token>` | 推荐给 agent / IDE 会话使用 |

## GA Session 流程

`AIHUB_TOKEN` 只代表 sk 可用；访问 HX 业务接口前还需要 AIHUB 侧 GA session 在有效期内。

### 检查 session

```bash
hx-cli auth check
```

- 成功：`data.session_valid=true`，可继续执行业务命令。
- `code=session_expired`：向用户收集 GA 验证码，再执行认证。
- `code=not_logged_in`：缺少 `AIHUB_TOKEN` 或 `--token`。

### 已绑定 GA：认证 session

```bash
hx-cli auth login --ga-code <6位验证码>
```

成功时返回 AIHUB 的 `domain_user` / `session_id` 等字段；之后 30 分钟内可继续执行业务命令。

### 自动登录（可选，免抄码）

把 GA seed（绑定时 `ga bindreq` 返回的 `secret`）写进 `.env` 的 `HX_GA_SECRET`，session 过期时跑脚本自动算码登录，免去手动去 TOTP app 抄 6 位码：

```bash
source .env && python3 .claude/skills/hx-cli/scripts/hx_login.py
```

seed 是永久密钥（拿到即等同账号）；`.env` 已 gitignore 不进 git，但存了即把 2FA 降级成单因素——自己的风险决策。

### 未绑定 GA：先绑定再认证

申请绑定：

```bash
hx-cli auth ga bindreq
```

返回 `secret`、`qr_uri`、`qr_base64` 后，把 `qr_uri` 或 `secret` 提供给用户，让用户用 Google Authenticator / TOTP APP 绑定。绑定完成后，请用户提供当前 6 位验证码。

确认绑定：

```bash
hx-cli auth ga bindconfirm --ga-code <6位验证码>
```

绑定成功后，再执行 `hx-cli auth login --ga-code <6位验证码>` 获取 session。

## 验证后输出概览

确认 `hx-cli status` 返回 `logged_in=true`，且 `hx-cli auth check` 成功后，agent 必须立即依次执行并把结果以**表格**形式汇总给用户。不要用纯文本列点，必须用 Markdown 表格。

#### 4.1 用户信息（一张表）

执行 `hx-cli user`，输出如下表格：

| 字段 | 值 |
|------|----|
| 姓名 | `name` |
| 邮箱 | `email` |
| PM staff id | `pm_staff_pk` |
| 部门 | `pm_department_name` |
| 拥有项目 id | `own_projects` |
| 管理项目 id | `manage_projects` |
| 参与项目 id | `member_projects`（去重） |

#### 4.2 项目信息（一张表）

对 `own_projects` ∪ `manage_projects` 去重后的每个项目 id 调用 `hx-cli project info <id>`，所有结果合并到**一张**表格：

| 项目 id | 项目名 | 状态 | 负责人 | 管理人 | 角色 |
|---------|--------|------|--------|--------|------|
| `id` | `prj_name` | `prj_status_display` | `own_by.name` | `manage_by.name` | own / manage / both |

- 「角色」列根据该 id 出现在 `own_projects` / `manage_projects` 来填 `own`、`manage` 或 `own+manage`。
- 如果 `own_projects` 与 `manage_projects` 都为空，改对 `member_projects` 去重后每个 id 调 `project info`，「角色」填 `member`。
- 不要输出 token 或敏感字段。
- 项目较多时（>10 个）可只展示前 10 个并提示总数。

## 关键字段

| 字段 | 含义 | 用途 |
|------|------|------|
| `id` | 用户 id | 不用于 `own_by_id` |
| `pm_staff_pk` / staff id | PM staff id | `--owner-id`、`--executor-ids`、`--first-process-item-executor` |
| staff department id | 部门 id | `--owner-dept-id` |

## 常见错误

- 用用户 id 当 `--owner-id`。
- 使用 `--show-token` 让 token 进入上下文。
- 忘记 `--token` 是全局 flag，推荐写成：`hx-cli --token <token> user`。
- session 过期时只刷新 token，不做 GA 认证。
