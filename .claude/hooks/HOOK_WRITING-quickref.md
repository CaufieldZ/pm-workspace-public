# Hook 速查（quickref）

> 改 hook / 写新 hook 前 30 秒读这页。全量规则见 [HOOK_WRITING.md](HOOK_WRITING.md)。
> required-read-gate 改 `hooks/*.sh` 时强制读本文件。

## 一、选哪个模板（按事件类型）

| 事件 | 模板 | 核心要点 |
|------|------|---------|
| PreToolUse Bash | §一 Bash 前置门 | `set +e` → source log/input/guards → `hook_parse_all` → `require_bash` → case 粗筛 → grep 精确 |
| PostToolUse Write\|Edit | §一 Write/Edit 后置 checker | source log/input/guards/runner → `require_write_or_edit` → 路径 case → `run_checker_block` |
| UserPromptSubmit | §一 提醒 | exit 0 stdout `{systemMessage}`（stderr 被丢）；阻断用 `{decision:"block"}` 非 exit 2 |

## 二、stderr 四段式（让模型 3 秒定位修法）

```
🚫 [gate-name] 一句话业务诊断（why，不报技术细节）
   文件: <相对路径>
   <证据 / 行号 / checker 输出>

   → 修法 1: <具体步骤，给文件 / 命令 / 行号>
   → 修法 2: <替代方案，如有>
   → 真不适用 → SKIP_<NAME>_GATE=1（说明什么场景该绕）
```

- emoji：🚫 block / ⚠️ warn
- 禁只 forward checker 原始输出——模型看不懂 L23 [流水标注] 该怎么修

## 三、六条硬约束（违反即出问题）

1. **`log_event` gate 名是稳定契约**——不改已有名（dashboard 会断），gate 名 = `SKIP_<UPPER>_GATE` 同源
2. **stderr 是模型唯一通道**——不 `2>/dev/null` 吞 checker 真实错误；UserPromptSubmit 例外走 stdout
3. **tempfile 用 `mktemp`**——禁裸 `/tmp/fixed.txt`；稳定路径用 `${TMPDIR:-/tmp}/<name>`
4. **SKIP 统一 `check_skip_env`**——禁手写 if-grep；Write/Edit 无 inline 通道
5. **JSON 解析走 `hook_parse_all`**——禁手写 `python3 -c "import json..."`，省 fork
6. **`set +e`**——hook 不因子命令失败崩溃

## 四、热路径砍 fork（每次 Read/Bash/Write 都跑）

| 禁 | 改 |
|----|-----|
| `echo "$x" \| grep -q 'FIXED'` | `[[ "$x" == *FIXED* ]]` |
| `echo "$x" \| grep -qE 'a\|b\|c'` | `case "$x" in *a*\|*b*\|*c*) ;; esac` |
| `sed -nE` 抽段 | bash 参数展开 `${t%%/*}` |
| 同一 JSON 多次 `jq` | 一次 `hook_parse_all` 出全 |
| 跑 python3 前不粗筛 | 先 `case` 粗筛（超集，宁 over 勿 under） |

## 五、自检清单

- [ ] source log.sh + input.sh（至少）
- [ ] `hook_parse_all` 不手写 python3
- [ ] 路径过滤用 `is_deliverable_path` / `is_excluded_path`
- [ ] SKIP 用 `check_skip_env`
- [ ] tempfile 用 `mktemp` 或 `lib/runner.sh`
- [ ] BSD/GNU 分叉命令取交集（`sed -i.bak` / `stat` 双分支）
- [ ] gate 名 = SKIP env 同源 kebab-case
- [ ] 退出码 0/2（不用 1）
- [ ] stderr 走四段式
- [ ] warn 类 checker 包 `_dedup_if_fresh` 节流
- [ ] `$var` 紧邻中文/全角写 `${var}`
- [ ] 改完跑 `bash .claude/hooks/test/test-hooks.sh` + `audit.sh 15`
