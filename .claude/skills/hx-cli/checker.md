# checker — 提测单 / 过程文档（只读查询）

本模块只保留提测单的**只读查询**能力：列提测单、查提测单详情、查提测历史、QA 提测列表。创建提测单、重新提测、撤回、QA 审核/测试通过/打回等写操作不在本 skill 范围——需要时让研发或 QA 在火效 Web 端操作，或用完整版 hx-cli。

字段传参原则：agent 优先使用明确 flags；`--body-json` 只作为兜底。

## 用户可见链接

火效 Web base 见 `SKILL.md`：`https://INTERNAL_URL_REDACTED `work_id`、`checker_id` 和提测历史记录 id：

| 对象 | 链接模式 | 使用条件 |
|------|----------|----------|
| 提测所属工作项 | `https://INTERNAL_URL_REDACTED<work_id>` | 查询提测单时只要知道工作项数字 id，就给工作项详情链接。过程文档入口在工作项详情内。 |
| QA 提测列表 | `https://INTERNAL_URL_REDACTED | 用户需要进入 QA 提测单列表、按项目/状态筛选时给。 |
| 提测历史详情 | `https://INTERNAL_URL_REDACTED<history_id>` | 只有 `checker history` 或后端返回里明确拿到提测历史记录 id 时才生成。前端这个路由会先用 history id 查出 checker id。 |

不要把 `checker_id` 拼成 `/process/release/<checker_id>`；这是错的。只有 `checker_id` 时，给工作项详情链接和 QA 提测列表入口，并说明当前 CLI 结果没有返回可直接打开单个提测历史详情的 history id。

## 查询与验证

```bash
# 任务详情里拿 work_manager.id；或先 work list 取完整字段
hx-cli checker list --work-manager-id <work_manager_id>

hx-cli checker get <checker_id>

hx-cli checker history <checker_id>

# QA 列表
hx-cli checker pre-test-list --project-id <project_id> --status SUBMITTED --page 1 --page-size 20
```

只读查询时重点看的字段：

- `name` 是 `提测模板`
- `validate_status.name_code` 是 `SUBMITTED` / `TESTING` / `ACCEPT` / `FAILED` / `REJECT` 之一
- `executor.id` 是目标测试人员
- `base_content.release_list` / `detail` 等内容

权限口径（仅了解，本 skill 不执行写操作）：

- `TESTING` / `REJECT` / `ACCEPT` / `FAILED` 只能由提测单测试人员执行。
- `withdraw` / `resubmit` 只能由提测单创建人执行。
- 已通过 `ACCEPT` 的提测单不允许普通修改。

## 注意事项

- 用户说“提测了没”“提测单状态”“查提测”时走本模块只读查询；说“提测”“提提测单”“重新提测”时，说明创建/流转写操作不在本 skill，建议在火效 Web 端或由研发/QA 操作。
- 代码管理 V2 测试步骤里的 `repo flow tag-test` 只负责创建 TEST Tag，与本 skill 无关；提测是否真正进入 QA 跟进以 `checker` 记录为准。
