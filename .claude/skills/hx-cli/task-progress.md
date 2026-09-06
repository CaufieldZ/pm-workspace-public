# task-progress — 从当前分支判断任务进展

当用户在某个代码仓库里问「这个任务状态」「任务进展」「做到哪一步了」「这个分支对应什么需求」时，默认先从当前 Git 分支解析 H 号，再查询火效工作项和代码管理 V2 状态。这个流程只读，不需要用户确认；只有后续要流转工作项、创建/关联分支、打 TAG、发起评审、合并代码时，才按 `SKILL.md` 的写入确认协议，在对话里暂停并确认后果。

## 适用场景

- 当前仓库分支名形如 `develop_H00000`、`release_H00000`、`feature_H00000_xxx`。这里的 `H00000` 是代码管理 V2 分支命名里的工作项数字 id 形态，去掉 `H` 后当作 `work_id` 使用。
- 用户没有给 work id，但在仓库上下文里问任务、需求、进度、代码管理 V2 状态。
- 用户给了一个 H 号，也可以跳过分支解析，直接查工作项。

## 用户可见链接

火效 Web base 见 `SKILL.md`：`https://INTERNAL_URL_REDACTED

| 对象 | 链接模式 | 说明 |
|------|----------|------|
| 当前分支对应工作项 | `https://INTERNAL_URL_REDACTED<work_id>` | 从 `H<work_id>` 去掉 H 后生成；链接文本可用 H 号、标题或任务名。 |
| 上级需求 / 父任务 | `https://INTERNAL_URL_REDACTED<parent_work_id>` | 只有查到父级数字 id 时给。 |
| 代码管理 V2 | `https://INTERNAL_URL_REDACTED<work_id>` | V2 在工作项详情的「代码管理」tab；不要生成独立 V2 URL。 |
| GitLab 仓库 / MR | 使用 CLI 返回的完整 GitLab URL | `repo current`、MR 历史、`new_mr_address` 有完整 URL 时才给。 |

不要把分支名里的 H 号直接拼成 `https://INTERNAL_URL_REDACTED path 用数字 `work_id`。Markdown 链接文本可以写 `[Hxxxxx]`，目标 URL 必须是 `/<数字id>`。

## 查询顺序

1. 在当前目录读 Git 分支名：

```bash
git branch --show-current
```

2. 从分支名提取第一个 `H` 开头的编号，大小写按原样保留；常见正则是 `H[0-9]+`。如果分支名没有 H 号，先看用户消息里有没有 H 号；仍没有就说明无法从当前分支定位任务，改用 `work.md` 的「我的任务」查询。

3. 把 `H<work_id>` / `<work_id>` 按工作项数字 id 处理，去掉 `H` 得到 `work_id=<work_id>`。不要用 `work list --search H<work_id>` 或 `--search <work_id>` 当作精确查询；`search` 是泛化搜索，返回列表不能直接作为当前任务命中。

4. 用数字 `work_id` 查当前仓库和 V2 证据：

```bash
hx-cli repo current
hx-cli repo info <repo_id>
hx-cli repo work related-repo <work_id>
hx-cli repo work code-history <work_id> --repo-id <repo_id>
hx-cli repo mr list --work-id <work_id> --repo-id <repo_id>
hx-cli repo tag history --work-id <work_id> --repo-id <repo_id> --prefix DEV
hx-cli repo tag history --work-id <work_id> --repo-id <repo_id> --prefix TEST
hx-cli repo tag history --work-id <work_id> --repo-id <repo_id> --prefix PRD
```

从 `related-repo`、`code-history`、TAG / MR 返回里提取 `work_id`、分支名、TAG、MR URL、最近动态等。如果这些接口能稳定证明任务身份，不要再用泛化 `search` 结果覆盖它。

5. 查上级任务 / 需求：

- 如果当前任务返回里已经包含 `parent`、`parent_work`、`requirement`、`demand` 等内嵌上级对象，直接使用。
- 如果只有上级 H 号 / 数字 id，按数字 `work_id` 口径查 V2 证据。
- 如果只有数字 `parent_id` 且当前 CLI 返回里没有父任务详情，不要编造父任务；说明「当前 CLI 响应只暴露了 parent_id，未带父任务详情」，再用当前任务标题、项目、子任务列表辅助判断，或提示需要补一个按 work id 查询的 CLI 能力。

6. 如果前面还没有匹配当前 Git 仓库到火效 GitLab repo，再执行：

```bash
hx-cli repo current
```

从返回里的 `repo.gitlab_repo_id` / `repo.gitlab_repo_name` 取 repo id/name。若当前目录没有 remote 或匹配失败，可以只汇报工作项状态；代码管理 V2 进度会缺仓库维度。

7. 如果前面还没有查询代码管理 V2 关联分支、动态、发布配置，再执行：

```bash
hx-cli repo info <repo_id>
hx-cli repo work related-repo <work_id>
hx-cli repo work code-history <work_id> --repo-id <repo_id>
hx-cli repo mr list --work-id <work_id> --repo-id <repo_id>
hx-cli repo tag history --work-id <work_id> --repo-id <repo_id> --prefix DEV
hx-cli repo tag history --work-id <work_id> --repo-id <repo_id> --prefix TEST
hx-cli repo tag history --work-id <work_id> --repo-id <repo_id> --prefix PRD
```

如果已知 `related-repo` 里的 develop/release/base 分支名，可以按发布模式做只读 compare：

```bash
hx-cli repo branch compare <repo_id> --source <develop_branch> --target <review_target_branch>
hx-cli repo branch compare <repo_id> --source <release_branch> --target <base_branch>
```

对 `BRANCH_PUBLISH` 的上线后判断还要补一组方向相反的 compare：

```bash
hx-cli repo branch compare <repo_id> --source <base_branch> --target <release_branch>
hx-cli repo branch compare <repo_id> --source <release_branch> --target <base_branch>
```

如果 `base -> release` 无差异而 `release -> base` 仍有待合并代码，说明 release 不落后于 base，且 release 上有需要合回 base 的上线代码。此时下一步是代码管理 V2 的「自动Merge代码 / 合并代码」（把 release 合回 base）——合回属写操作，不在本 skill 范围，向用户说明该状态并建议联系研发在火效 Web 端走代码管理 V2 合回流程即可，不要给出手工 MR / 手动合并的具体命令。

## 进展判断口径

用工作项流程状态 + 代码管理 V2 证据一起判断，不要只看分支名：

| 证据 | 可表述的进展 |
|------|--------------|
| 工作项存在，但 `related-repo` 没有当前 repo 的 BASE/DEVELOP 记录 | 火效任务存在，代码管理 V2 还没开始开发或未关联当前仓库 |
| 有 BASE + DEVELOP 关联分支 | 已开始开发，V2 Step 1 已完成 |
| 有 RELEASE 分支（通常 `BRANCH_PUBLISH`） | 已进入分支发布链路，后续测试/上线会围绕 release |
| `DEV` TAG 历史有记录 | 已打开发自测 TAG |
| MR 历史有 develop -> release/base 记录，或 develop -> review target compare 显示 `need_merge=true` | 已进入/需要代码评审；结合 MR 状态说明是待创建、已创建、已合并还是无差异 |
| `TEST` TAG 历史有记录 | 已打测试 TAG，通常已提测或经过测试阶段 |
| `PRD` TAG 历史有记录 | 已打上线 TAG |
| `BRANCH_PUBLISH` 下已有 PRD TAG，base -> release 无差异，且 release -> base compare 显示 `need_merge=true` | release 有需合回 base 的上线代码；下一步是代码管理 V2「合并代码」（合回 base），本 skill 不含该写操作，建议联系研发在火效 Web 端处理 |
| `BRANCH_PUBLISH` 下 release -> base compare 无差异，且有 PRD TAG / 合回动态 | 基本可判断代码已上线并合回 base |
| 工作项 `current_process` / `stat_filter_name` 是已完成 | 火效流程已完成；如果代码证据缺失，要说明是「任务流转完成」，不是自动等同于代码已上线 |

发布模式影响步骤解释：

| 发布模式 | 评审方向 | 测试/上线目标 |
|----------|----------|---------------|
| `BRANCH_PUBLISH` | develop -> release | 测试/上线 TAG 通常在 release；最后 release 合回已核实的 base |
| `MASTER_PUBLISH` | develop -> 已核实的 base | 测试 TAG 通常在 develop，上线 TAG 在 base |
| `SPECIFIC_BRANCH_PUBLISH` | develop -> 指定 base | 同 master 发布，但 base 是配置的指定分支 |

注意：`base` 必须来自 `repo info` 的明确返回、已关联的 `BASE` 记录或真实远端分支核实结果。不要把缺失的 base 自动表述成 `master`；如果仓库实际只有 `main`，而 flow 错用 `master`，这属于 hx-cli / 发布配置问题，不代表当前代码或 TAG 失败。

## 回答模板

回答用户时优先给结论，再列证据：

```text
当前分支解析到 V2 分支标识：<H号>（work_id=<数字>）。

任务：<work_name>（<work_type_name>，id=<id>）
链接：<工作项链接>（代码管理 V2 也在这个页面的「代码管理」tab）
上级需求/任务：<parent_serial> <parent_name>（如果查到）
火效状态：<current_process/stat_filter_name>，负责人 <own_by>，执行人 <executor>，迭代 <sprint>

代码管理 V2：<repo_name>/<repo_id>，发布模式 <dev_mode>，base <base>
当前进展判断：<一句话，例如“已开始开发并打过 DEV TAG，还没有测试 TAG / PRD TAG”>
依据：分支关联 <BASE/DEVELOP/RELEASE>，TAG <DEV/TEST/PRD>，MR/compare <摘要>，最近代码动态 <摘要>
```

不要把未查到的信息说成没有发生。区分：

- 「没有查到」= 接口返回为空、权限不足、repo 未匹配或 CLI 能力不足。
- 「没有发生」= 在对应 repo/work 下明确查到关联/TAG/MR/compare 为空，并且接口成功。
- 「search 返回了很多项」= 泛化搜索结果，不能当作精确任务命中；必须用 `id`、`related-repo`、分支名或代码动态交叉确认。

## 注意事项

- H 号来自分支名时，当作代码管理 V2 的工作项数字 id。仍要用 `repo current` 确认当前 Git 仓库对应的 repo id。
- 同一个工作项可能关联多个 repo。用户问“当前仓库”时优先看 `repo current` 匹配到的 repo；汇总任务全貌时再看 `related-repo` 的全部仓库。
- 只读查询失败时，把失败的环节讲清楚，例如缺少 AIHUB token、repo 无权限、当前目录不是 Git 仓库、分支名无 H 号。
- 代码管理 V2 状态是代码流程进展；火效 `current_process` 是工作项流程进展。两者不一致时同时报告，不要强行合并成一个状态。
