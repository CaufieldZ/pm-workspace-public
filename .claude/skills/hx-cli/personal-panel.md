# personal-panel — 个人面板 / 我的任务概览

当用户问「看看我手头的任务」「我在做什么」「我有哪些待处理/逾期」「最近改了哪些火效任务」时，优先用本页流程。它复刻火效前端 `/project/personal-panel` 的只读信息，帮助用户快速了解自己的任务，不做任何写入。

## 用户可见链接

火效 Web base 见 `SKILL.md`：`https://INTERNAL_URL_REDACTED

| 对象 | 链接模式 | 说明 |
|------|----------|------|
| 个人面板总入口 | `https://INTERNAL_URL_REDACTED | 回答“我的任务/个人面板”概览时给。 |
| 列表里的工作项 | `https://INTERNAL_URL_REDACTED<work_id>` | `personal list` / `personal records` 返回 `work_id` 时，每条重要任务都给工作项链接。 |

不要把 personal 接口里的统计字段、筛选名或 `pha_id` 拼成页面路径；只有数字 `work_id` 能生成工作项详情链接。

## 页面口径

前端入口：

- 路由：`/project/personal-panel`
- 页面：`cd-platform-fed/src/views/project/personagePanel/index.vue`
- 列表：复用 `Kanborad` / `personalWorkList`
- 动态：`cd-platform-fed/src/views/project/personagePanel/dynamic.vue`

后端主接口：

| 页面区块 | CLI | 后端接口 | 说明 |
|----------|-----|----------|------|
| 统计卡片 | `hx-cli personal stats` | `GET /api/v1/pm/workbench/personal-stats` | 返回 `future_me`、`current_me`、`past_me`、`overdue_me` |
| 任务列表 | `hx-cli personal list` | `GET /api/v1/pm/workbench/personal-worklist` | 按个人面板筛选列出任务 |
| 右侧动态 | `hx-cli personal records` | `GET /api/v1/pm/workbench/personal-records` | 当前用户在时间段内的字段变更和流程流转记录 |

前端 API 文件里还有 `personal-pre-check`、`personal-todo-works`、`personal-estimate-works`、`personal-time-check`、`personal-check-works`、`personal-check-done`、`personal-unpack-works`、`personal-unpack-detail` 等封装；当前后端 `apps/pm_core/urls.py` 只登记了上表三个个人面板主接口。不要把未登记接口当成可稳定调用能力。

## 快速工作流

1. 先确认认证：

```bash
hx-cli status
hx-cli auth check
```

2. 拉个人面板统计：

```bash
hx-cli personal stats
```

统计字段口径：

| 字段 | 页面文案 | 后端筛选口径 |
|------|----------|--------------|
| `future_me` | 待处理 | 当前人为执行人，当前流程带「待处理标志」 |
| `current_me` | 进行中 | 当前人为执行人，排除「终结标志」「暂停」「待处理标志」 |
| `past_me` | 已完成 | 当前人为执行人，当前流程属于完成节点 |
| `overdue_me` | 已逾期 | 当前人为执行人，`end_time <= 今天` 且未完成 |

3. 按用户关心的分组拉任务列表。默认看进行中：

```bash
hx-cli personal list --filter current --page 1 --page-size 20
```

常用筛选：

```bash
hx-cli personal list --filter future --page 1 --page-size 20
hx-cli personal list --filter overdue --page 1 --page-size 20
hx-cli personal list --filter past --page 1 --page-size 20 --order-by work_manager__created_at --order-seq desc
hx-cli personal list --filter create --page 1 --page-size 20
hx-cli personal list --filter all --work-type-name "需求,研发任务,BUG" --page 1 --page-size 50
```

`personal list` 输出的 `data` 是 `{ "rows": [...], "total": N }`，回答用户时用 `total` 说明当前筛选总数，用 `rows` 展示本页明细。

`--filter` 与页面「展示内容」一致：

| `--filter` | 页面文案 | 含义 |
|------------|----------|------|
| `all` | 全部 | 我参与的：创建人、业务 Owner、产品 Owner、测试 Owner、执行人、技术 Owner 任一命中 |
| `future` | 待处理 | 当前人为执行人，处于待处理节点 |
| `current` | 进行中 | 当前人为执行人，处于非完成、非暂停、非待处理节点 |
| `past` | 已完成 | 当前人为执行人，处于完成节点 |
| `overdue` | 已逾期 | 当前人为执行人，结束日期已到且未完成 |
| `create` | 我创建的 | 当前人为创建人 |

4. 拉最近动态，默认最近 7 天：

```bash
hx-cli personal records
```

指定时间段：

```bash
hx-cli personal records --start-at "2026-07-01 00:00:00" --end-at "2026-07-03 23:59:59"
```

动态返回字段常见为 `work_id`、`pha_id`、`work_type`、`field_name`、`old_value`、`new_value`、`rcd_time`。回答用户时把它整理成「什么任务、什么字段/流程、从什么变成什么、什么时候」。

## 回答用户的默认摘要格式

只读查询不用确认。查完后优先输出一段短结论，再用表格展示最值得看的任务：

```text
你当前个人面板是：待处理 X、进行中 Y、已完成 Z、已逾期 N。优先看 N 个逾期和 Y 个进行中任务。
```

任务表推荐列：

| 优先级 | 工作项 | 类型 | 项目 | 状态 | 执行人 | 截止/预期 | 进度/风险 |
|--------|--------|------|------|------|--------|-----------|-----------|

排序建议：

- 先展示 `overdue`，再展示 `current`，最后按需要展示 `future`。
- 如果用户问「最近做了什么」，补充 `personal records` 的最近动态。
- 如果列表里有 `end_time` 已过、`expected_done_at` 临近、风险字段为空但明显阻塞，提醒用户是否要同步火效进度/风险；不要擅自写入。

## 注意事项

- `personal stats/list/records` 都是只读命令，不需要写入确认。
- 这些命令按当前登录用户计算，不需要手填 staff id。
- `personal list` 只看激活项目，后端会排除停用项目。
- `personal stats` 的后端统计包含 `INTERNAL_需求池`，`personal list` 只取激活项目；如果卡片数量和列表总数有小差异，先说明这是后端口径差异，再按列表里的明细回答。
- 当用户需要修改状态、进度、风险、时间或工时，切回 `work.md` 的写入流程，先查目标工作项并按确认协议执行。
