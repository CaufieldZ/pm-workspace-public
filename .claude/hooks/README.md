# Hooks 清单

> 本文件由 `python3 scripts/gen_hooks_readme.py` 自动生成，**勿手改**。
> 怎么写 / 改 hook → [HOOK_WRITING.md](HOOK_WRITING.md)；本文件只回答「当前有哪些 hook、各管什么」。
> 加 / 删 hook 后重跑生成脚本；audit §15 会校验是否 drift。

| 事件 | matcher | hook 文件 | 职责 | 内含 gate |
|------|---------|-----------|------|-----------|
| SessionStart | `startup\|resume\|compact` | `session-start.sh` | 新 session / resume / compact 后，把项目视图 / resume 成本行 / session-state.md 注入新 conversation | `session-start` |
| UserPromptSubmit | `*` | `user-prompt-warn.sh` | session 健康度 + 需求质量提醒（三项检查合一进程） | `context-warn` · `cost-warn` · `pm-gate-reminder` |
| PreToolUse | `Agent\|Task` | `pre-agent-log.sh` | Agent tool 调用 → 记录 sub-agent 调度（type=agent） | —（纯观测 / 无埋点） |
| PreToolUse | `Bash` | `pre-bash-guard.sh` | Bash 命令前置守卫（多规则聚合 · 5 hook 合并入口） | `cold-read-gate` · `git-https-gate` · `git-safety` · `prototype-paradigm-gate` · `risky-op` · `skeleton-force-gate` |
| PreToolUse | `Bash` | `pre-proxy-check.sh` | 外网下载命令自动挂代理后放行 | `proxy-check` |
| PreToolUse | `Read` | `pre-read-bigfile.sh` | 阻断 > 500 行文件的全量 Read（必须用 offset/limit） | `read-bigfile` |
| PreToolUse | `Read` | `pre-read-image-check.sh` | 图片 Read 前多图限制预检（> 2000px / > 5MB 先压缩） | `read-image-check` |
| PreToolUse | `Agent\|Task` | `pre-task-prompt-scrub.sh` | sub-agent prompt 必须显式禁读写 session-state.md | `task-prompt-scrub` |
| PreToolUse | `Write\|Edit` | `pre-writeedit-guard.sh` | Write\|Edit 统一 guard dispatcher（原 4 个独立 pre-*.sh 合并入口） | `deliverable-img-path-gate` · `deliverable-source-gate` · `required-read-gate` · `scripts-first` · `skill-load-gate` |
| PostToolUse | `Bash` | `post-bash-deliverable-check.sh` | 调度 cjk / plain-language / prd-check / ui-annotation / proto-audit / prototype-split / imap-split / proto-drift 八个 Bash 路径 sub-checker | `imap-split-gate` · `plain-language-gate` · `prd-check-gate` · `proto-drift-warn` · `prototype-audit` · `prototype-split-gate` · `script-rebuild-cjk` · `ui-annotation-gate` |
| PostToolUse | `Read\|Skill` | `post-skill-load.sh` | 监听 Read .claude/skills/{name}/SKILL.md 与 Skill 工具调用 → 记录 skill 触发 | —（纯观测 / 无埋点） |
| PostToolUse | `Write\|Edit` | `post-writeedit-dispatch.sh` | Write\|Edit 统一 dispatcher | `audit-fast` · `audit-fast-lite` · `baseline-fresh-gate` · `bullet-density-gate` · `cjk-punct` · `context-static-lint` · `delta-conflict-gate` · `imap-split-gate` · `learned-rules-gate` · `md-blockquote-gate` · `plain-language-gate` · `pm-visual-gate` · `prd-content-gate` · `prd-cross-check-gate` · `prototype-audit` · `prototype-shell-gate` · `prototype-split-gate` · `rule-version-drift-gate` · `scene-list-gate` · `script-syntax-gate` · `test-reminder-gate` · `ui-annotation-gate` |
| Stop | `*` | `stop-dashboard-refresh.sh` | 每次 session 结束后刷新 workspace-dashboard.md | —（纯观测 / 无埋点） |
| Stop | `*` | `stop-learn-capture.sh` | 从对话 transcript 提取 [LEARN] 标记 → 持锁去重追加到 LEARNED.md | —（纯观测 / 无埋点） |
| Stop | `*` | `stop-pycache-clean.sh` | 每次 session 结束后清理 Python 工具链缓存（__pycache__ / .pytest_cache / .hypothesis） | —（纯观测 / 无埋点） |
| PreCompact | `*` | `pre-compact.sh` | 在上下文压缩前注入 session-state.md + git 动态快照 | `pre-compact` |

## gate 名索引

共 45 个 gate（`log_event` 字符串 = dashboard 聚合键 = `SKIP_<UPPER>_GATE` 同源）：

`audit-fast`，`audit-fast-lite`，`baseline-fresh-gate`，`bullet-density-gate`，`cjk-punct`，`cold-read-gate`，`context-static-lint`，`context-warn`，`cost-warn`，`deliverable-img-path-gate`，`deliverable-source-gate`，`delta-conflict-gate`，`git-https-gate`，`git-safety`，`imap-split-gate`，`learned-rules-gate`，`md-blockquote-gate`，`plain-language-gate`，`pm-gate-reminder`，`pm-visual-gate`，`prd-check-gate`，`prd-content-gate`，`prd-cross-check-gate`，`pre-compact`，`proto-drift-warn`，`prototype-audit`，`prototype-paradigm-gate`，`prototype-shell-gate`，`prototype-split-gate`，`proxy-check`，`read-bigfile`，`read-image-check`，`required-read-gate`，`risky-op`，`rule-version-drift-gate`，`scene-list-gate`，`script-rebuild-cjk`，`script-syntax-gate`，`scripts-first`，`session-start`，`skeleton-force-gate`，`skill-load-gate`，`task-prompt-scrub`，`test-reminder-gate`，`ui-annotation-gate`
