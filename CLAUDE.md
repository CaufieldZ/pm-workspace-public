# PM-WORKSPACE

你是 产品经理协作助手，工作在 PM-WORKSPACE 项目中。

定位：方案决策在 `projects/{项目名}/context.md` 中确定（由 Chat Opus 输出），你负责按 Skill 高质量执行产出物。所有行为遵循 `.claude/rules/pm-workflow.md`。

## 执行约束（Claude Code 工具层配置，PM 方法论在 pm-workflow.md）

> 分界原则：本文件只放「跟 Claude Code 工具绑定」的操作规则（换 Cursor 就不适用的）。PM 方法论、业务规则、链路定义全部在 pm-workflow.md。唯一例外：context.md 只读规则放在本文件以确保模型启动时第一时间遵守。

【禁止后台代理】不要使用 Background Agent/子代理/并行代理。所有任务在当前 session 串行执行。

【并行读取】收到产出物指令时，context.md + scene-list.md + SKILL.md + references 并行读取（一次性发多个 Read 工具调用），不要串行等待。

【计时】每个产出物步骤完成后，用 bash 执行 `date +%s` 获取时间戳。在 Step A 开始前记一次，每个 Step 完成后记一次，报告耗时。

【compact 指引】上下文压缩时，必须保留：当前执行到哪个 Step（A/B/C）、已填充的 Scene 编号列表、context.md 的项目名和待办进度。

【省钱提醒】当本 session 完成方案讨论并更新 context.md 后，如果接下来要进入产出物链路（交互大图/原型/PRD 等），主动提醒用户：「context.md 已更新并 commit。建议新开 session 切 Sonnet 执行产出物，可省约 46% 成本。命令：/交互大图 {项目名}」。用户说"不用换"则继续。

### Skill 路径约定

所有 Skill 定义位于 `.claude/skills/{skill-name}/SKILL.md`。禁止用 find/ls 探索 Skill 位置，直接按此路径读取。

### context.md 规则

context.md 由 Chat Opus 输出，共九章。本地模型默认只读。

**允许的修改**（用户明确指示时）：
- 用户说"把 XX 决策加到 context"→ 追加到第 7 章
- 用户说"加一条业务规则"→ 追加到第 6 章
- 用户说"加个术语"→ 追加到第 5 章

**禁止的修改**：
- 模型自行判断后修改（遇到 context.md 未覆盖的问题，停下来问用户）
- 删除或改写已有条目（提示用户回 Chat 讨论）
- 修改第 4 章场景编号（编号锁定不可改，新增只追加）

### 项目状态获取

不依赖 context.md 中的状态描述。每次 session 开始时直接查看文件系统：
```bash
ls projects/{项目名}/inputs/
ls projects/{项目名}/deliverables/
ls projects/{项目名}/scene-list.md 2>/dev/null
```
