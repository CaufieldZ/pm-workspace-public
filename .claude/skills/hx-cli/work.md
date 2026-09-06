# work — 工作项创建与查询

创建/查询/更新需求、研发任务、后端任务等。所有工作项都是 `work`，用项目 `work_type_id` 和标准 leaf `new_work_type_id` 区分。

`work create`、`work delete`、`work transition`、`work update-progress` 都会真实写入。执行前必须按 `SKILL.md` 的后果确认协议，在对话里确认会创建/删除/流转/更新哪个工作项、归属项目、类型、父子关系、负责人/执行人、状态或字段变化和可见影响；不要让用户确认内部 CLI 命令。

当你通过代码管理 V2、提测单、安全提测、MR、TAG、分支比较、上线/合并结果发现当前需求或任务的火效状态可能落后于实际进展时，要随时提醒用户更新对应需求/任务状态，并说明建议流转到哪个状态以及依据。提醒不等于写入；只有用户明确确认后，才执行 `work transition`。

创建需求、研发任务、后端任务、事务任务、Bug 或拆分子任务时，必须主动推荐开始日期、结束日期和预估工时（人天）。这些字段默认推荐填写：`--start-date` / `--end-date` 记录任务排期日期，`--expected-start` / `--expected-done` 记录预期开始/完成时间，`--work-time` 记录预估工时，必要时 `--tech-work-time` 记录技术预估工时。用户明确要求不填时可以不填，但确认消息里要说明留空字段。

如果在日常开发交流中发现逾期、依赖阻塞、返工、范围扩大、测试/上线窗口错过、实际进展和计划不一致等风险，要主动提醒用户更新风险字段。用户确认后，用 `work update-progress` 同步风险状态、风险描述，并视情况同步日期、工时和进度百分比。

## 用户可见链接

火效 Web base 见 `SKILL.md`：`https://INTERNAL_URL_REDACTED

| 对象 | 链接模式 | 说明 |
|------|----------|------|
| 任意工作项详情 | `https://INTERNAL_URL_REDACTED<work_id>` | `<work_id>` 是数字 id。链接文本优先用标题、H 号或 `work_name`，例如 `[H402111]`、`[Market-7418]`。 |
| 父需求 / 父任务 | `https://INTERNAL_URL_REDACTED<parent_work_id>` | 只有确认父级数字 id 后才给。 |
| 子任务 | `https://INTERNAL_URL_REDACTED<child_work_id>` | 创建子任务或验证父子关系后逐条给。 |

不要把项目 id、`work_type_id`、`work_manager.id`、`checker_id` 当成工作项详情 id。前端复制任务链接的实际格式是 `https://INTERNAL_URL_REDACTED<work_id>`；`/project/task/:taskId` 只是兼容路由，不作为默认输出。

## 创建需求

```bash
hx-cli work create \
  --project <project_id> \
  --type-id <demand_work_type_id> \
  --title "需求标题" \
  --description "需求描述" \
  --owner-id <staff_id> \
  --priority <priority> \
  --start-date "2026-06-18" \
  --end-date "2026-06-20" \
  --expected-start "2026-06-18 09:00:00" \
  --expected-done "2026-06-20 18:00:00" \
  --work-time 3 \
  --executor-ids <staff_id>
```

`work create` 会自动从项目工作类型第一个流程节点补 `current_proc`；特殊流程可手动传 `--current-proc`。

## 创建研发子任务 / 后端任务

```bash
hx-cli work create \
  --project <project_id> \
  --type-id <dev_task_work_type_id> \
  --new-work-type-id <leaf_new_work_type_id> \
  --parent-id <parent_work_id> \
  --title "后端任务标题" \
  --description "任务描述" \
  --owner-id <staff_id> \
  --owner-dept-id <department_id> \
  --priority <priority> \
  --start-date "2026-06-18" \
  --end-date "2026-06-19" \
  --expected-start "2026-06-18 09:00:00" \
  --expected-done "2026-06-19 18:00:00" \
  --work-time 2 \
  --tech-work-time 2 \
  --time-scale <time_scale> \
  --executor-ids <staff_id> \
  --first-process-item-executor <staff_id>
```

推荐值口径：

- 简单配置/文案/脚本任务：通常 0.5~1 人天，开始日期可用今天，结束日期可用今天或下一个工作日。
- 常规后端/前端开发子任务：通常 1~3 人天，按范围、联调和自测复杂度调整。
- 跨系统联调、数据迁移、权限/安全/发布链路任务：通常 3~5 人天或更高，并在描述里说明依赖和风险。
- 父需求的工时应覆盖需求分析、开发、联调、测试跟进和发布协调；拆分子任务后，要提醒用户是否需要用子任务汇总结果回填父需求工时和结束日期。

## 查询验证

```bash
hx-cli work get <work_id_or_H>
hx-cli work children <parent_work_id_or_H>
hx-cli work parents <child_work_id_or_H>
hx-cli work list --project <project_id> --work-type-id <demand_work_type_id> --search "标题" --page 1 --page-size 10
hx-cli work list --project <project_id> --work-type-id <dev_task_work_type_id> --parent-id <parent_work_id> --page 1 --page-size 10
```

`work get` 直接调用工作项详情接口 `GET /api/v1/pm/work/<work_id_or_H>`，参数可以是数字 id，也可以是 `H403914` 这类 `pha_id` / `work_serial`。
`work children` / `work parents` 会先调用专门关系接口确认父子关系，再自动补查每个关联工作项详情；输出中 `data.rows` 是可直接展示的工作项详情列表，`data.relations` 是关系接口原始返回，`data.relation_ids` 是关系接口确认的关联工作项 id。

父子关系不要用工作项详情里的 `has_dmd_father` / `hasDMDFather` 判断。这个字段是详情页派生字段，容易让 agent 误判需求和任务是否已经关联。验证父子关系时，以 `work children` / `work parents` 为准，它们封装的是专门关系接口：

```text
GET /api/v1/pm/work/child/<parent_work_id>
GET /api/v1/pm/work/parent/<child_work_id>
```

判断口径：

- `hx-cli work children <parent_work_id_or_H>` 返回的列表里包含子任务 id，才说明父需求下有这个子任务。
- `hx-cli work parents <child_work_id_or_H>` 返回的列表里包含父需求 id，才说明这个任务已关联父需求。
- 即使详情里出现 `has_dmd_father=false` 或 `has_dmd_father=true`，也不要单独用它作为父子关联是否存在的结论。

## 工作流：创建需求 + 子任务

1. `hx-cli user` 获取当前 PM staff id 和部门 id。
2. `hx-cli project work-types <project_id>` 获取项目 `work_type_id`。
3. `hx-cli work-type list --show-all` 获取 leaf `new_work_type_id`。
4. 创建父需求，记录返回的 `id` / `pha_id`。
5. 用父需求 `id` 创建子任务。
6. 用 `GET /api/v1/pm/work/child/<parent_work_id>` 和 `GET /api/v1/pm/work/parent/<child_work_id>` 验证父子关系；不要看 `has_dmd_father` / `hasDMDFather` 字段来判断关联是否存在。再查询子任务详情，确认类型和负责人。

## 删除工作项

```bash
hx-cli work delete <work_id>
```

不可逆操作。会级联向翻译子任务发通知。`work_id` 必须是数字 id；不要用项目序号或泛化搜索结果代替数字 id。

删除前必须二次确认具体 `work_id`、标题和影响范围。

## 流转工作项状态（完成/进行中/暂停 等）

```bash
# 用流程节点 id（推荐，最稳）
hx-cli work transition <work_id> --proc-id <proc_id>

# 或者用流程节点名称（后端会按 work 当前 work_type 解析 name 到 id）
hx-cli work transition <work_id> --proc-name "已完成"

# 复杂场景：透传 PATCH body
hx-cli work transition <work_id> --body-json '{"current_proc":<proc_id>,"notice_tech_own_change":false}'
```

`--proc-id` 与 `--proc-name` 互斥。

### 如何拿到 `--proc-id`

```bash
hx-cli project work-types <project_id>
```

返回里 `children[].id` 就是各 work_type 下可用的流程节点 id。不同项目的同名节点 id 不同；用前必须实时查表，不要复用历史项目里的固定 id。

## 更新任务进度 / 风险 / 时间工时字段

当用户要修改任务或需求的「进度百分比」「风险状态」「进度详情」「风险描述」「变更描述」「开始/结束日期」「预期开始/完成时间」「预估工时」时，必须使用专门命令 `work update-progress`，不要使用 `work transition --body-json` 或其他兜底 PATCH。

这些字段对应火效任务详情页「更多设置」里的业务字段，后端接口是 `PATCH /api/v1/pm/work/<work_id>`：

| 用户说法 | CLI flag | 后端字段 | 说明 |
|----------|----------|----------|------|
| 进度百分比 | `--percent <0-100>` | `percentage_progress` | 数字，允许小数，范围 0~100；传 `0` 表示 0% |
| 风险状态 | `--risk-state-id <id>` | `risk_state_id` | 推荐在已知枚举 id 时使用 |
| 风险状态 | `--risk-state-name "<名称>"` | `risk_state_id` | CLI 会查 `RISK_STATE` 枚举并按 `enum_name` / `key_str` 解析 |
| 清空风险状态 | `--clear-risk-state` | `risk_state_id=null` | 与 `--risk-state-id` / `--risk-state-name` 互斥 |
| 进度详情 | `--progress-detail "<内容>"` | `memo` | 火效字段名是 `memo`，页面展示为「进度详情」 |
| 风险描述 | `--risk-description "<内容>"` | `risk_description` | 最大 1024 字符，传空字符串可清空 |
| 变更描述 | `--change-description "<内容>"` | `change_description` | 最大 1024 字符，传空字符串可清空 |
| 规模 | `--time-scale <id>` | `time_scale` | 后端规模枚举；通常随 `work_time` 一起维护 |
| 预估工时 | `--work-time <人天>` | `work_time` | 可传小数；例如 `0.5`、`2`、`3.5` |
| 技术预估工时 | `--tech-work-time <人天>` | `tech_work_time` | 技术侧估算；没有单独口径时可与 `work_time` 一致 |
| 预期开始时间 | `--expected-start "YYYY-MM-DD HH:mm:ss"` | `expected_start_at` | 可用 `--clear-expected-start` 清空 |
| 预期完成时间 | `--expected-done "YYYY-MM-DD HH:mm:ss"` | `expected_done_at` | 可用 `--clear-expected-done` 清空 |
| 开始日期 | `--start-date "YYYY-MM-DD"` | `start_time` | 可用 `--clear-start-date` 清空 |
| 结束日期 | `--end-date "YYYY-MM-DD"` | `end_time` | 可用 `--clear-end-date` 清空 |

查询风险状态枚举：

```bash
hx-cli work risk-states
```

更新示例：

```bash
hx-cli work update-progress <work_id> \
  --percent 80 \
  --risk-state-name "正常" \
  --progress-detail "已完成开发和自测，等待 QA 回归" \
  --start-date "2026-06-18" \
  --end-date "2026-06-20" \
  --expected-done "2026-06-20 18:00:00" \
  --work-time 3 \
  --risk-description "" \
  --change-description "接口返回字段按评审意见补充"
```

只改一个字段也使用同一命令：

```bash
hx-cli work update-progress <work_id> --percent 100
hx-cli work update-progress <work_id> --risk-state-id <risk_state_id>
hx-cli work update-progress <work_id> --progress-detail "今日完成联调"
hx-cli work update-progress <work_id> --risk-description "依赖上游接口验收"
hx-cli work update-progress <work_id> --change-description "范围从 A 扩展到 A+B"
hx-cli work update-progress <work_id> --work-time 2.5 --end-date "2026-06-21"
hx-cli work update-progress <work_id> --clear-expected-done --clear-end-date
```

写入前必须先查出目标 work 的标题、项目、当前负责人、当前进度/风险字段，并向用户确认具体变化。例如：

```text
我准备更新这个工作项的进度/风险/时间工时字段：
- 工作项：<标题 / id>
- 将修改：进度百分比 <旧值> -> <新值>；风险状态 <旧值> -> <新值>；开始/结束日期、预期完成时间、预估工时按本次推荐值更新；进度详情/风险描述/变更描述按本次内容更新
- 用户可见影响：火效任务详情和列表里的进度、风险、排期、工时列会立即变化

然后询问用户：`确认并更新`、`先调整字段`，还是`取消`。
```

写后用 `work list` 验证，至少带上这些字段：

```bash
hx-cli work list \
  --search <work_id_or_title> \
  --need-field id,work_name,percentage_progress,risk_state,risk_state_id,memo,risk_description,change_description,work_time,tech_work_time,time_scale,time_scale_display,expected_start_at,expected_done_at,start_time,end_time \
  --page 1 \
  --page-size 10
```

## 字段口径

| flag | 后端字段 | 说明 |
|------|----------|------|
| `--project` | `project_id` | 项目 id |
| `--type-id` | `work_type_id` | 项目内工作项类型 |
| `--new-work-type-id` | `new_work_type_id` | 标准 leaf 类型 |
| `--work-time` | `work_time` | 预估工时，单位人天 |
| `--tech-work-time` | `tech_work_time` | 技术预估工时，单位人天 |
| `--expected-start` | `expected_start_at` | 预期开始时间，格式 `YYYY-MM-DD HH:mm:ss` |
| `--expected-done` | `expected_done_at` | 预期完成时间，格式 `YYYY-MM-DD HH:mm:ss` |
| `--start-date` | `start_time` | 开始日期，格式 `YYYY-MM-DD` |
| `--end-date` | `end_time` | 结束日期，格式 `YYYY-MM-DD` |
| `--current-proc` | `current_proc` | 流程原型 id；通常自动补 |
| `--first-process-item-executor` | `first_process_item_executor` | 首流程执行人 staff ids |
| `--owner-id` | `own_by_id` | PM staff id，不是 user id |

## 常见错误

- 后端返回 `Server Internal Error`：优先检查是否缺 `current_proc`、`new_work_type_id`、`first_process_item_executor`。
- 创建研发任务时不要省略 leaf `new_work_type_id`；具体值必须查询当前项目/平台配置。
