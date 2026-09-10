# Interaction-map Skill Eval 集

## 任务 1：ann-card 四禁（硬规则 10）

**输入**：给一段 ann-card HTML 含字段表 + 状态全集 + Top N + 埋点事件名。
**判 rubric**：
- [ ] 无 ≥ 2 列 ≥ 3 行 `<table>`（跨端 6 列 `.cross-grid` 例外）
- [ ] 无 `loading / 空态 / 错误态` 状态全集列举（改 `<span class="ref">→ 原型...`）
- [ ] 无 `Top \d+` / 权重数池策略参数
- [ ] 无 snake_case 埋点事件名

## 任务 2：anno-n ↔ ann-num 对应 + 字符一致（硬规则 2/4）

**输入**：给一段 anno overlay 编号 `①②` 但 ann-card 编号 `1 2`。
**判 rubric**：
- [ ] anno-n 与 ann-num 1↔1 对应
- [ ] 字符样式一致（都阿拉伯或都圆圈，不混用）

## 任务 3：零改动叙事（硬规则 3）

**输入**：给一段含 `V2.1 NEW / 变更 / 改动` 的 ann-tag。
**判 rubric**：
- [ ] 无 `ann-tag.new/chg/del`
- [ ] 无 `V\d+\.\d+` / `NEW` / `变更` / `新增` 文案
- [ ] 只保留 `.p0/.p1/.p2`

## 任务 4：src/scenes 拆分（硬规则 11）

**输入**：给一个内联 scene_fns 的 orchestrator 文件。
**判 rubric**：
- [ ] 拆成 `src/scenes/{id}.py` 一文件一主场景
- [ ] orchestrator 只 import + 收口，不内联 scene_fns
