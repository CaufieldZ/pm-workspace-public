# project — 项目、成员、工作类型

查询项目、项目成员、项目工作项类型、标准 NewWorkType 目录。

## 用户可见链接

火效 Web base 见 `SKILL.md`：`https://INTERNAL_URL_REDACTED

| 对象 | 链接模式 | 使用条件 |
|------|----------|----------|
| 项目总入口 | `https://INTERNAL_URL_REDACTED<project_id>` | 只知道项目 id、不知道用户关心哪个工作项类型时，默认给项目需求页入口，并说明可在项目总览切换 tab。 |
| 需求列表 | `https://INTERNAL_URL_REDACTED<project_id>` | 用户查需求、需求类型、需求列表。 |
| 研发任务列表 | `https://INTERNAL_URL_REDACTED<project_id>` | 用户查研发任务、后端任务、前端任务、任务类型包。 |
| Bug 列表 | `https://INTERNAL_URL_REDACTED<project_id>` | 用户查 Bug / 缺陷。 |
| 上线任务列表 | `https://INTERNAL_URL_REDACTED<project_id>` | 用户查上线任务。 |
| 事务任务列表 | `https://INTERNAL_URL_REDACTED<project_id>` | 用户查事务任务 / 离线任务。 |
| 设计任务列表 | `https://INTERNAL_URL_REDACTED<project_id>` | 用户查设计任务。 |

不要用项目 id 生成 `/<project_id>` 链接；裸 `/<id>` 是工作项详情，不是项目详情。

## 命令

| 目标 | 命令 |
|------|------|
| 项目列表 | `hx-cli project list --name <project_keyword>` |
| 项目详情 | `hx-cli project info <project_id>` |
| 项目成员 | `hx-cli project members <project_id>` |
| 项目工作类型 | `hx-cli project work-types <project_id>` |
| 标准类型 leaf | `hx-cli work-type list --show-all` |
| 标准父类型 | `hx-cli work-type list --is-parent 1 --show-all` |
| 人员搜索 | `hx-cli staff list --name <name>` |

## 工作流

1. 按项目名查 `project_id`。
2. 用 `project work-types` 查该项目实际使用的 `work_type_id`。
3. 创建研发子任务前，用 `work-type list --show-all` 查 leaf `new_work_type_id`。
4. 用项目成员或 staff 搜索确认负责人/执行人是有效 PM staff。

## 常见错误

- 把标准 `NewWorkType` id 当作项目 `work_type_id`。
- 复用其他项目的固定 id；不同项目的类型包可能不同。
- `project list` 返回字段名是 `prj_name`（不是 project_name / name）。
- `--name` 按业务词（直播 / 社区 / 合约）常查不到——项目名多是组织名（如「商业增长-内容生态」）。改用该产品线任一已有需求的 `work get <H号>` 取 `project_id` + `work_type_id`，比按名搜稳。
