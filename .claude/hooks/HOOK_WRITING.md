# 写新 Hook / 改老 Hook 规范

写新 hook 前必读。改老 hook 前如果当前 hook 还没用 lib/，按本规范一起迁。

> 快速查模板 / 四段式 / 自检清单 → [HOOK_WRITING-quickref.md](HOOK_WRITING-quickref.md)（≤100 行，required-read-gate 强制读）。
> 想查「当前有哪些 hook、各管什么、内含哪些 gate」→ [README.md](README.md)（`gen_hooks_readme.py` 自动生成）。本文件讲「怎么写」，README 讲「现在有啥」。加 / 删 hook 后重跑生成脚本，audit §15 会校验 drift。

---

## 一、最小模板

按事件类型选模板，复制粘贴改：

### Bash 前置门（PreToolUse / Bash）

```bash
#!/bin/bash
# PreToolUse Bash hook: <一句话目的>
#
# 触发：<什么命令 pattern>
# 行为：<命中怎么处理>
# Escape：SKIP_<GATE_NAME>_GATE=1

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"
# 命令字符串里有用户输入 / heredoc / 字符串字面量需要剥 → 加：
# source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/strip.sh"

INPUT=$(cat)
hook_parse_all
require_bash

CMD="$HOOK_COMMAND"

# 触发匹配
echo "$CMD" | grep -qE '<pattern>' || exit 0

# SKIP 旁路（如有）
check_skip_env "<gate-name>" "SKIP_<GATE_NAME>_GATE" "$CMD"

# 字符串字面量剥（如需）
# CMD_STRIPPED=$(strip_command_literals "$CMD")

# ... 业务判断 ...

# 命中（stderr 走三段式，详见 §二）
echo "" >&2
echo "🚫 [<gate-name>] <一句话业务诊断，不报技术细节>" >&2
echo "   <证据 / 文件 / 行号>" >&2
echo "" >&2
echo "   → 修法 1: <具体步骤，给文件 / 命令 / 行号>" >&2
echo "   → 修法 2: <替代方案，如有>" >&2
echo "   → 真不适用 → SKIP_<GATE_NAME>_GATE=1（说明什么场景该绕）" >&2
log_event gate <gate-name> block "${CMD:0:120}"
exit 2
```

### Write/Edit 后置 checker（PostToolUse / Write|Edit）

```bash
#!/bin/bash
# PostToolUse hook: <一句话目的>
#
# 触发：Write/Edit 命中 <什么路径 pattern>
# 检测：<什么规则 / 调什么 checker>
# 行为：strict 命中 → exit 2 阻断 + stderr 报违规

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/runner.sh"

INPUT=$(cat)
hook_parse_all
require_write_or_edit

FILE_PATH="$HOOK_FILE_PATH"
[ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && exit 0

# 路径过滤
case "$FILE_PATH" in
  <你的 pattern>) ;;
  *) exit 0 ;;
esac
is_excluded_path "$FILE_PATH" && exit 0
# 或者
# is_deliverable_path "$FILE_PATH" || exit 0

check_skip_env "<gate-name>" "SKIP_<GATE_NAME>_GATE" "$FILE_PATH"

# 简单路径：调 run_checker_block 一行完成
CHECKER="${CLAUDE_PROJECT_DIR:-$(pwd)}/scripts/check_<your>.py"
[ -f "$CHECKER" ] && run_checker_block "<gate-name>" "$FILE_PATH" python3 "$CHECKER" "$FILE_PATH"

# 或自定义失败处理（带 head -N、额外 hint）：
# run_checker_capture python3 "$CHECKER" "$FILE_PATH"
# if [ "$RC" -ne 0 ]; then
#   head -30 "$TMPOUT" >&2
#   log_event hook <gate-name> block "$FILE_PATH"
#   exit 2
# fi
# log_event hook <gate-name> clean "$FILE_PATH"
```

### Bash 后置 checker（PostToolUse / Bash, 扫近 N 秒动过的文件）

```bash
#!/bin/bash
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/recent.sh"

INPUT=$(cat)
hook_parse_all
require_bash

CMD="$HOOK_COMMAND"
echo "$CMD" | grep -qE '<触发 pattern>' || exit 0
check_skip_env "<gate-name>" "SKIP_<GATE>_GATE" "$CMD"

# 60 秒内动过的 *.md / *.html，排除 scenes/
RECENT=$(find_recent_deliverables 60 --not-path '*-scenes/*' "*.md" "*.html")
[ -z "$RECENT" ] && exit 0

# 逐个跑 checker（业务逻辑省略）
```

### UserPromptSubmit 提醒（UserPromptSubmit / *）

> UserPromptSubmit 与 PreToolUse/PostToolUse 输出语义不同：exit 0 时 **stderr 被静默丢弃**（无 tool result），只有 stdout 被读。
> stdout 纯文本 / `{additionalContext}` 会注入 Claude context；要给**用户看**且不进 context、不阻断，用 `{systemMessage}`。

```bash
#!/bin/bash
# UserPromptSubmit hook: <一句话目的>
#
# 触发：每次用户发消息前
# 数据源：transcript JSONL（hook_parse_all → $HOOK_TRANSCRIPT）
# 行为：命中条件 → systemMessage 提醒（用户可见 / 不进 context / 不阻断）

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"

INPUT=$(cat)
hook_parse_all

[ -f "$HOOK_TRANSCRIPT" ] || exit 0

# ... 从 transcript / prompt 取数据判断 ...
# <条件不满足> && exit 0

# stdout 只允许这一行 JSON：多一行（含 shell profile 噪声）→ JSON 校验失败整条被丢
jq -nc --arg msg "<一句话提醒>" '{systemMessage: $msg}'
log_event hook <name> triggered "<detail>"
exit 0
```

要点：
- **提醒走 `systemMessage`，不走 stderr**：UserPromptSubmit exit 0 stderr 被丢弃（§三 B 例外）
- **stdout 只允许这行 JSON**：混入任何额外输出会触发 JSON 校验失败，提醒被吞
- **阻断 prompt** 用 `{decision:"block", reason:"..."}`（exit 2 会忽略 JSON，别用）

---

## 二、stderr 写作三段式（让 Claude 看了就能修）

主旨：hook 的 stderr 是 Claude 唯一能看到的反馈。只报"症状"没用，必须告诉它**为什么 + 怎么修 + 啥时候该绕**。否则 Claude 看到 warn 不知所措会绕过，或瞎修把别的东西改坏。**典型反例是调外部 checker 后只 forward 原始输出**——checker 报「L23 [流水标注]」，Claude 不知道该删行 / 改归章节 / 改写措辞，大概率瞎修或直接 SKIP。

### 标准模板（四段）

```
🚫 [hook-name] 一句话诊断（why，业务语言不报技术细节）
   文件: <相对路径>
   <证据 / 行号 / checker 输出，可多行>

   → 修法 1: <具体步骤，给出文件 / 命令>
   → 修法 2: <替代方案，如有>
   → 真不适用 → SKIP_<NAME>_GATE=1（说明什么场景该绕；warn 类不需要这行）
```

要点：
- **第一行 emoji + [name] + why**。emoji 用 `🚫` (block) / `⚠️` (warn)。why 不是「checker 未通过」，是「**讲人话违规：内部锚点 / 决策号不应入对外产物**」这种业务诊断
- **文件行明示相对路径**，方便 Claude grep / Read 定位
- **修法用 `→` 引导**，给出可执行步骤（文件路径 / 命令 / 行号），不要只说「按规则修」
- **SKIP 说明何时该绕**（「仅 false positive 时」/「仅内部审计文档」），不要只列 env 名让 Claude 凭感觉用

### 黄金范例

`lib/pre-writeedit-guards.sh` `pg_deliverable_source` 末段 —— 四段齐全（文件 + 匹配脚本 + 改源路径 + SKIP env）。新 hook 不确定怎么写时照抄。

### 反例对比

**反例**：
```
项目X/prd-X-baseline.md — warn 3（流水标注 3）
  ⚠️  L23 [流水标注]
     （v3.1 新增）本次新增了 XXX
```
Claude 看到「L23 流水标注」只知有违规，**不知是删行 / 改写 / 改归章节**，大概率瞎修或 SKIP。

**正例**：
```
⚠️  [context-static-lint] 静态章四不违规（流水时间 / 决策号 / 技术栈 / UI 规范不应进静态章）
   文件: 项目X/prd-X-baseline.md
   ⚠️  L23 [流水标注]
        原文: （v3.1 新增）本次新增了 XXX
        修法: 删行内 v3.1 标注，改写到 ## 9. 版本历史 章节
   → 真不适用 → SKIP_CONTEXT_LINT_GATE=1（仅 false positive 时用）
```
Claude 看完 3 秒决定动作，不需要 Read runbook。

### 怎么实施

- **新 hook**：按模板写
- **老 hook 升级**：调 checker 的 hook 改 `cat $TMPOUT >&2` 为「先 echo 诊断 + 文件 + 空行 → cat checker 输出 → echo 空行 + → 修法 → SKIP」
- **复杂场景**（checker 输出本身就需要 per-line 修法）：让 checker 输出「原文 + 修法」双行，参考 `scripts/check_static_chapter.py` FIX_HINTS dict
- **改 stderr 文案时优先核对 Bash 路径 checker（`lib/checkers.sh`）与 Write/Edit 孪生（`lib/post-checks.sh`）是否一致**：`lib/checkers.sh` 常比 `lib/post-checks.sh` 措辞更糙、漂离四段式

---

## 三、硬约束

### A. `log_event "<name>"` 字符串是稳定契约

`scripts/dashboard.py` 按 `log_event` 字符串分组（不按文件名）。

- 一旦某 gate 名进了 `usage.jsonl`（哪怕 1 次），后续 hook 改名 / 合并必须**保留同样的字符串** emit
- gate-name 用 kebab-case，与 SKIP 环境变量同源（`prd-check-gate` ↔ `SKIP_PRD_CHECK_GATE`）
- 一个 hook 文件可以 emit 多个 gate 名（如 `pre-bash-guard.sh` emit `proxy-check` + `git-https-gate` + `skeleton-force-gate`）
- 不要为了"清理"改 gate 名 — dashboard 会出现 ghost 行
- **`lib/log.sh` 的 `log_event` 在非 hook 脚本里 source 用时**，需先 `export CLAUDE_PROJECT_DIR`，否则它按 `BASH_SOURCE` 推断 root 会走偏到 `/Users`。

### B. stderr 是模型唯一能读到的输出通道

Claude Code 只读 stderr 作为 hook 输出注入到 tool result。`2>/dev/null` 静默 checker 输出 = hook 形同虚设。

- 模型需要感知到的所有错误 / 警告必须 `>&2`
- checker 的 stdout / stderr 都要收 → 失败时 `cat / head / tail` 到 `>&2`
- 不要 `2>/dev/null` 静默 checker 真实错误（`command -v _log_skip_gate 2>/dev/null` 这种存在性测试除外）
- **例外 UserPromptSubmit**：exit 0 时无 tool result，stderr 被静默丢弃——给用户的提醒走 stdout `{systemMessage}`（不进 context、不阻断），范例 `user-prompt-context-warn.sh`（§一 模板）

### C. tempfile 用 `mktemp`，不要硬编码

固定名 `/tmp/foo.txt` 并发 race；`/tmp/foo.$$.txt` 风格不统一。

- 简单场景：`source lib/runner.sh` 用 `run_checker_block` / `run_checker_capture`（自动 mktemp + trap cleanup）
- 复杂场景需要自管：`TMPOUT=$(mktemp); ...; rm -f "$TMPOUT"`
- 永远不写 `/tmp/<fixed-name>.txt`
- 需要稳定路径做 TTL / 缓存 key（非一次性 tempfile）：`${TMPDIR:-/tmp}/<name>` 兜底，不裸写 `/tmp/<name>`（Git Bash for Windows 的 TMPDIR 可能指向非 `/tmp`）；范例 `lib/dedup.sh`

### D. SKIP 环境变量统一命名 + 行为

- 命名：`SKIP_<UPPER_KEBAB>_GATE=1`（如 `SKIP_PRD_CHECK_GATE` / `SKIP_DELIVERABLE_GATE`）
- 统一用 `check_skip_env "<gate-name>" "SKIP_<NAME>_GATE" "$DETAIL"` 一句话搞定
- check_skip_env 同时处理：env var + 命令行 inline 前缀（`SKIP_X=1 python3 ...`），并 emit skip 事件到日志
- **例外**：Write/Edit 触发的 hook，命令行 inline 不工作（Edit/Write 不经 Bash 管道），文档里 stderr 提示用户用 env，不要骗用户
- 反例：`pre-writeedit-guard.sh` 的 `pg_skill_load` 在判 transcript 之前先判 `SKIP_SKILL_LOAD_GATE` env — 这是对的，inline 通道对 Write/Edit 工具无效，根本不需要 hook_parse_all 后再判

### E. JSON 解析走 `hook_parse_all`

每个 hook 手写 `python3 -c "import sys,json; ..."` 会让单次 Write/Edit 触发十几个 python3 进程。

- 必须 `INPUT=$(cat); hook_parse_all` 一次性出 `$HOOK_TOOL_NAME` / `$HOOK_FILE_PATH` / `$HOOK_COMMAND` / `$HOOK_TRANSCRIPT`
- 单字段函数 `hook_tool_name` / `hook_file_path` / `hook_command` 仅在不需要其他字段时用（省一个 python3 进程）
- Read 路径专用 `hook_parse_read` 一次出 `$HOOK_FILE_PATH` + `$HOOK_HAS_PAGING`（offset/limit 标志），别 `hook_parse_all` 后再 `jq` 取 paging
- 需要的字段现有 `hook_parse_*` 没覆盖 → 扩函数多输出一个变量（仍单次 jq），不要再 fork 第二次 jq（见 §三 K）
- 内容字段（`tool_input.content` / `new_string` / `old_string`）目前没抽进 lib，写新 hook 需要的话仿照 `lib/pre-writeedit-guards.sh` 的 `_pg_content` 写法

### F. 路径过滤用 helper

- deliverable 判定：`is_deliverable_path "$PATH" || exit 0`
- 通用排除（archive / __pycache__ / node_modules / .git）：`is_excluded_path "$PATH" && exit 0`
- 特殊 pattern（如 prd-*.md / proto-*.html）：case 直接写（不抽 lib）

### G. 命令字符串 grep 前必须剥字面量

字符串字面量里出现命令名会让 grep 假阳（如 commit msg 里的脚本名命中 hook 检测）。

- 任何要 `grep` 命令名 / 关键字的 hook：`source lib/strip.sh` + `CMD_STRIPPED=$(strip_command_literals "$CMD")`，对剥后版本做 grep
- env 变量检测 / SKIP inline 检测对**原始** CMD 做（剥后 `=` 也被剥）

### H. warn vs block 退出码语义

- `exit 0` = 放行 / 静默 / warn（warn：PreToolUse/PostToolUse 走 stderr；**UserPromptSubmit 走 stdout `{systemMessage}`**——那里 exit 0 stderr 被丢弃）
- `exit 2` = 阻断 tool 调用
- `exit 1` = 不要用（语义不明确，混淆）
- post 类 hook（context-static-lint）软 warn 永不 block：`exit 0` after 写完 stderr
- pre 类 hook（deliverable-source-gate）硬 block：`exit 2`
- UserPromptSubmit 提醒：`jq -nc '{systemMessage:$msg}'` + exit 0；要阻断 prompt 用 `{decision:"block",reason:...}` 而非 exit 2（exit 2 忽略 JSON）

### I. warn 类 checker 用 dedup 节流

warn 类（不阻断、`exit 0`）checker 没必要每次 Edit 都同步跑——连续 Edit 同文件
会重复扫同一份内容发热。包 `_dedup_if_fresh` 让同 key 在 TTL 秒内只跑第一次。

用法（dispatcher 包裹调用，须在 log.sh 之后 source）：

```bash
source lib/dedup.sh
_dedup_if_fresh context-static-lint 60 "$FILE_PATH" || pc_static_chapter
# fresh（TTL 内跑过）返回 0 → || 短路 → skip
# stale（该跑了）   返回 1 → || 执行 → run
```

- key 维度：检查具体文件 → 文件路径；检查产品线树 → 产品线名
- TTL 内 emit `dedupe-skip`（action 不在 dashboard 五列，不污染聚合诊断；usage.jsonl 留痕）
- 只对 warn 类用；block 类（cjk_punct / plain_language）阻断要及时，每次都该跑，不节流
- 见 `post-writeedit-dispatch.sh` 4 个 warn checker 的包裹范例

### J. 多操作系统兼容：Unix-like 前提 + BSD/GNU coreutils 分叉

**平台前提**：所有 hook 是 `#!/bin/bash`，跑在 macOS / Linux / Git Bash / WSL。Windows 原生 CMD / PowerShell 没有 bash → hook 链整体不工作（README 已声明此前提）。写 hook 不必考虑 cmd 兼容，但临时路径要兼容 Git Bash 的 TMPDIR（见 §三 C）。

**BSD vs GNU 分叉**：Unix-like 内部仍分叉——macOS 是 BSD userland，Linux / WSL 是 GNU coreutils，同名工具 flag 行为不同。hook 在两类机器都跑，命令取交集或显式双分支（BSD 优先 `||` GNU fallback）：

| 工具 | 陷阱 | 可移植写法 |
|------|------|-----------|
| `sed -i` | GNU 接 `-i`，BSD 须 `-i ''` | `sed -i.bak` 后删 `.bak`（两边通吃）|
| `stat` | BSD `-f`，GNU `-c` | BSD 优先 `\|\|` GNU fallback |
| `date -d` | GNU 有，BSD 无 | 偏移计算交给 `python3` |
| `grep -P` | BSD 无 PCRE | 用 ERE `grep -E`（热路径粗筛见 §三 K）|
| `mktemp` | BSD 只替换模板末尾连续 X | 裸 `mktemp`（§三 C 已要求；别加后缀模板）|
| `readlink -f` | BSD 老版无 `-f` | 用 `python3 -c 'import os;print(os.path.realpath(...))'` |

> 已有 lint：audit §15 的「BSD sed 分隔符冲突 lint」专扫 hook 里 `sed` 分隔符与内容冲突，改 hook 后跑 §15 验证。

### K. 热路径 hook 砍冗余 fork

每次 Read / Bash / Write/Edit 都同步跑对应 hook，串在工具调用前后。瓶颈不是逻辑，是**子进程 fork**：source lib 几乎免费，外部 checker 多为亚秒，真正吃时间的是每条命令都重复启的 `jq` / `grep` / `sed` / `awk` / `python3`。

单 fork 成本（本机量级，定位用）：

| 操作 | 量级 | 操作 | 量级 |
|------|------|------|------|
| bash 启动 + source 6 lib | ~10ms | `python3` 冷启 | ~30ms |
| `jq` / `grep` / `sed` / `awk` 各一次 | ~14ms | bash 内建 `case` / `[[ ]]` / 参数展开 | ≈ 0 |

四条规则：

**1. 判断按成本排序**：bash 内建（`case` / `[[ ]]`）粗筛在前，复杂 `grep` 居中，外部 checker（python3）最后。让最便宜的判断先把绝大多数输入挡掉。

**2. 跑复杂 `grep` / 外部进程前先 `case` 粗筛短路**。粗筛词必须是精确 pattern 命中集的**超集**——over-match 回落到精确判断（安全，只损失一点性能）；**under-match 漏判（bug）**。短词陷阱：`go get` 别用 `*go*`（误命中 django/logo）也别用 `*" go "*`（漏命令开头的 `go get`），用双词 glob `*go\ get*`（`*` 含空，覆盖开头）。

```bash
guard_git_safety() {
  # 非 git 命令（绝大多数）不可能命中下方 git pattern，case 粗筛直接 return 省 3 段 grep
  case "$2" in *git*) ;; *) return 0 ;; esac
  echo "$2" | grep -qE '(^|[[:space:]])git[[:space:]]+push...' && ...   # 罕见命中才精确判
}
```

**3. 固定串 / 简单择一用 bash 内建替 fork**（语义等价、零进程）：

| fork 写法 | bash 内建 |
|-----------|-----------|
| `echo "$x" \| grep -q 'FIXED'` | `[[ "$x" == *FIXED* ]]` |
| `echo "$x" \| grep -qE 'a\|b\|c'` | `case "$x" in *a*\|*b*\|*c*) ;; esac` |
| `sed -nE 's\|.*/projects/([^/]+)/.*\|\1\|p'` 抽段 | `t="${x#*/projects/}"; echo "${t%%/*}"` |
| `wc -l <f \| tr -d ' '` | `n=$(wc -l <f); n="${n//[[:space:]]/}"` |

**4. 保留 `grep` 的边界**：复杂 ERE（`\b` 词边界 / `{n,}` / `\.` 转义 / 含 `-i`）别硬翻成 `[[ =~ ]]`——bash `[[ =~ ]]` 用 ERE，**不支持 GNU `\b`**，改写易出静默错判。**收益让位正确性**：把这类 grep 放 `case` 粗筛之后，只在罕见命中时跑即可。

配套：① 同一份 JSON 不重复 `jq`，需要多字段就扩 `hook_parse_*`（如 Read 路径 `hook_parse_read` 一次出 file_path + paging），别二次 fork。② 外部 python3 checker 只处理特定标记时，先 `grep -q '<标记>' || exit 0` 预筛（如 `stop-learn-capture` 无 `[LEARN]` 跳过整个 python3）。③ 读 yaml / config 后移到「确需精确值」时——如「文件 ≤ 下界直接放行，> 下界才 awk 取精确阈值」。

> ⚠️ 改 PreToolUse 安全门（git-safety / proxy-check / paradigm-gate）的粗筛时：粗筛词宁可 over-match，改完**必跑 `test/test-hooks.sh` 确认拦截行为逐字不变**，正向（该 block 仍 block）+ 边界（含子串的无害命令不误判）都要测。
> 正则 / 匹配逻辑类改动另跑**双探针**（绕过形态必 exit 2、无害近似形态必 exit 0）：`printf '{"tool_name":"Bash","tool_input":{"command":"<cmd>"}}' | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR=<根> bash .claude/hooks/pre-bash-guard.sh` 逐条断言退出码——套件锁的是已知形态，探针补的是「你以为改对了的」新形态。
>
> 亚秒性能回归：`$SECONDS` 整秒分辨率对亚秒 hook 计时无效——`analyze_gate_funnel` 的 `d>0` 过滤会让 < 1s 的 dur_ms 落空；亚秒级回归走 pytest `perf_counter`，dur_ms 埋点只对定位「多秒慢闸」有意义。

### L. 变量紧邻非 ASCII 字符必须 `${var}`

bash 3.2 解析 `$var` 按字节贪婪匹配变量名。若 `$var` 两侧任一侧紧贴非 ASCII 字节（中文 / 全角标点 / emoji / `×` 等），相邻 UTF-8 续字节被误吞进变量名 → 变量值丢失 + 紧邻字符损坏（如阈值数字变乱码）。echo / printf / 双引号串 / heredoc **都中招**，不是 heredoc 独有。

`${var}` 花括号显式划定边界，所有场景安全。`printf '%s' "$var"` 也安全但非必须——heredoc 可继续用，只需把其中裸 `$var` 换成 `${var}`。

```bash
# ❌ 全角（紧贴 $pipeline → $pipeline 求值空 + 相邻字符损坏
echo "  skill（$pipeline pipeline）"
FAIL="... ×$BAD"                     # × 紧贴 $BAD 同样损坏

# ✅ 花括号划定边界
echo "  skill（${pipeline} pipeline）"
FAIL="... ×${BAD}"
```

边界：`$var` 两侧是 ASCII（空格 / 半角标点 / 字母）无需花括号；特殊参数 `$#` `$?` `$@` 是定长单字符，紧邻全角也不触发，不必加花括号。

heredoc 特例：bash 3.2 + UTF-8 locale 下，heredoc 里变量紧邻全角字符仍可能字节错位（阈值数字变乱码）——hook 的阻断 / 提示消息若含全角 + 变量，一律用 `printf '%s' "$var"` 注入、不用 heredoc，全 bash 版本安全。

---

## 四、反模式清单（写 hook 时禁犯）

| 反模式 | 正确做法 |
|--------|---------|
| `python3 -c "import sys,json; print(...)"` 在 hook 里 | `hook_parse_all` 或单字段函数 |
| `/tmp/<fixed-name>.txt` / `/tmp/...$$.txt` | `mktemp` / `lib/runner.sh` |
| 需要稳定路径却裸写 `/tmp/pmws_xxx` | `${TMPDIR:-/tmp}/pmws_xxx`（Git Bash TMPDIR 可能非 `/tmp`）|
| `mktemp x.XXXXXX.suffix` 带后缀模板（BSD 不随机化）/ 直用 `sed -i`·`stat -c`·`date -d`（BSD/GNU 分叉）| 裸 `mktemp`；分叉命令取交集或 BSD 优先 + GNU fallback（§三 J）|
| 重写 `if SKIP_X=1...; then; if echo $CMD grep SKIP_X; ...` | `check_skip_env` |
| `python3 ... 2>/dev/null` 静默 checker 真实错误 | `>"$TMPOUT" 2>&1`，失败时 `cat "$TMPOUT" >&2` |
| `case "$FILE" in */projects/*/*/deliverables/*) ...` 三段 glob | `is_deliverable_path` |
| `grep -E '(archive\|__pycache__\|node_modules)/' "$FILE"` | `is_excluded_path` |
| 直接 `grep 'gen_prd' "$CMD"` 不剥字面量 | `strip_command_literals` |
| 为「美观」改 `log_event` 的 gate 字符串名 | 不改，dashboard 历史断 |
| 改 hook 文件名但忘改 settings.json | audit §15.4 会 ❌ fail；两侧同 commit |
| 把跨 hook 共用的判断写进单个 hook（"以后再抽 lib"）| 第二次出现立即抽 lib |
| 不写 `set +e` 导致管道里某步失败整个 hook 中断 | 默认加 `set +e`（hook 不应因子命令失败而崩溃）|
| 删除「过时」 gate 的 `.sh` 但留 `log_event` emit | 同时删 .sh + 删 emit + 跑 audit §15 验证 |
| 加行文类校验（的字链 / 空泛动词 / 长句 / 分号）不先标定命中数 | 先拿真实语料跑命中数：0 命中的规则是维护负担不是价值，只加命中显著的 |
| 改 SKILL / prompt 里**塑形模型行为**的措辞（非检测器），凭「肯定有用」直接上 | 先 micro-test：无指引对照组确认失败真存在 → 同措辞跑 5+ 次看是否收敛（方差 = 措辞没绑住）。方法见 skill-conventions.md「行为塑形规则改动前先 micro-test」|
| 标点 / 分号类校验对 PRD 区块表行不豁免 | 表格 cell 内 `；` 是 `md_to_confluence` 切 bullet 的约定分隔符，标点类校验对表格行必须豁免，否则与渲染约定冲突 |
| warn 类 checker 每次 Edit 全量跑（连续 Edit 同文件重复扫发热）| 包 `_dedup_if_fresh GATE TTL KEY \|\| pc_xxx` 做同 key TTL 节流 |
| 热路径上 `echo \| grep` 匹配固定串 / `sed`·`tr` 做字符串截取 | bash 内建 `[[ == ]]` / `case` / 参数展开（§三 K）|
| 跑复杂 grep / python3 checker 前不做 `case` 粗筛短路 | 先 `case` 粗筛（词取精确 pattern 超集，宁 over 勿 under），罕见命中才精确判（§三 K）|
| 同一份 JSON 多次 `jq` 取不同字段 | 一次 `hook_parse_all` / `hook_parse_read` 出全（§三 E / K）|
| UserPromptSubmit 提醒写 `echo ... >&2`（exit 0 stderr 被丢，用户看不到）| `jq -nc '{systemMessage:$msg}'`（stdout JSON，§一 模板 / §三 B）|
| 改治理规则（CJK / UI 正则 / SKIP 清单 / repo-root 定位）只改一处 | 治理代码自身无 info-ownership SSOT，多处重复且已漂移——改前 `grep -rn` 全实现处一并改（audit §15 也查 drift）。**讲人话豁免已收口**：规则表 `scripts/lib/lint_exempt.txt` 是 bash + Python 单一真相源，只改那张表，别在 `guards.sh` / checker 里另写 case |
| 安全门（paradigm / deliverable-source / img-path）正则抽项目名 / TYPE 失败时 `return 0` | fail-loud（exit 2 + stderr）或 fail-closed——项目名含中文 / 脚本名含数字即静默放行 = 安全门自身失效 |
| 加 Confluence 渲染约束（禁 `>` / 禁 `---`）只补一两层 | 须补全五层：md_renderer 产 `>` 方法 → sections_md 骨架 → humanize / md_scan 扫描器 → check_prd_md FAIL key → SKILL + chapter-rules 规则文，任一层漏即漏网 |
| 加行文 / 标点校验，注释声明「冒号领起不扫」「表格行豁免」但代码漏实现 | 注释承诺的豁免必须在代码兑现（漏实现 = 误报）；数分支条件只数起始词（若 / 如果 / 否则 / 超过）不数 consequent 连接词「则」，否则每条「若 X 则 Y」都误报 |
| 想 hook 化 AI 味三维度（挤话 / 反复讲 / 夸夸其谈）全上规则 | 只有「挤话」（单行句号 ≥ 3）能规则化；「反复讲」是语义重复归 cross-check LLM；「夸夸其谈」包装词在 Platform C 语境多实义、词表误伤高，留写作指引 |
| 安全门正则要求子命令紧跟程序名（`git[[:space:]]+push`）→ 全局选项前缀（`git -C <path>` / `-c k=v` / `--git-dir=…`）整体绕过；+refspec 只匹配短形式 | 子命令前允许夹选项 token（`git([[:space:]]+[^[:space:]]+)*[[:space:]]+push`）；+refspec 逐段吞 `refs/heads/` 类路径前缀、右边界含 `:` `/`——完整 refspec（`+refs/heads/main:refs/heads/main`）也拦，`+feature/main-fix` 不误伤 |
| block 消息（或头注释）承诺 `SKIP_<X>_GATE` 逃生门但函数内无 `_pc_skip` / `check_skip_env` 消费 | stderr / 注释写出的每个 SKIP 变量必须有对应消费（grep 变量名确认消费方）；无逃生门就在消息里不写、注释里注明「无逃生门」——用户照提示 export 仍被拦 = 承诺失信（先例：SKIP_AUDIT_FAST 只存在于消息） |
| 新增 `hook_parse_*` 只写 jq 分支 | 与 `hook_parse_all` 同构带 python3 兜底——jq 缺失时 eval 空 → 该门静默 fail-open（先例：hook_parse_read 缺兜底，Read 门全灭） |
| 命令名精确判用无锚定 grep（`build_proto` 子串命中即拦）→ ruff / grep 把脚本路径当**参数提及**被误当调用 | 精确判锚定命令位：逐段取首 token（剥 `ENV=` 前缀与 python3 / env 包装）后 basename 匹配；参数位置的文件名提及不算调用 |

---

## 五、改动 / 退役 hook 的清单

### 改名 .sh 文件（如 `post-X.sh` → `post-Y.sh`）

1. 改文件名
2. 改 settings.json 注册路径
3. **保留 `log_event` 字符串名不动**（dashboard 不断）
4. 改外部引用：`.claude/runbooks/*.md`、`.claude/_meta/half-life.md`、`.claude/skills/*/SKILL.md`、`CLAUDE.md`、`README.md` 等（grep 老名字找命中）
5. `python3 scripts/gen_hooks_readme.py` 重生 README 清单
6. `bash .claude/skills/workspace-audit/scripts/audit.sh 15` 验证

### 删 hook（彻底退役）

1. 删 .sh 文件
2. 删 settings.json 注册
3. 删 `log_event` 调用 — 否则 ghost gate 又出现
4. 修 `scripts/dashboard.py` 派生逻辑：把退役 gate 名加进 `GHOST_GATES` deny-list（dashboard 不再渲染，usage.jsonl 历史仍保留）
5. 归档旧日志 `.claude/logs/skip-gates.log`、修剪 `usage.jsonl` 里这个 gate 名（可选）
6. 改外部引用同上
7. `python3 scripts/gen_hooks_readme.py` 重生 README 清单
8. audit §15

### 合并 hook（如 N 个合到 1 个）

1. 新 hook 内每个 sub-checker 显式 emit **原 gate 名**（dashboard 不断）
2. 影子并跑 1 周：settings.json 同时注册新旧，新 hook emit 字符串临时加 `-shadow` 后缀
3. 跑脚本对比 `jq -r '[.name,.action] | @csv' usage.jsonl | sort | uniq -c` 新旧分布 ±5%
4. 切 settings.json 删旧入口，去 `-shadow` 后缀
5. 旧 hook 留 5-line shim 1 周观察期后删
6. `python3 scripts/gen_hooks_readme.py` 重生 README 清单 + audit §15

---

## 六、参考资料

- `.claude/hooks/lib/*.sh` 自己看实现（含完整签名注释 + 用法示例）
- `lib/log.sh:1-67` — `log_event` / `_log_skip_gate` 用法
- `lib/input.sh` — `hook_parse_all`（全字段）/ `hook_parse_read`（Read 路径 file_path + paging，单次 jq）/ 单字段函数
- `lib/guards.sh` — `require_bash` / `require_write_or_edit` / `is_deliverable_path` / `is_excluded_path` / `is_plain_language_exempt`（规则表 `scripts/lib/lint_exempt.txt`，与 Python 侧 `lib/lint_exempt.py` 共读）/ `check_skip_env`
- `lib/recent.sh:1-78` — `find_recent_deliverables`
- `lib/runner.sh:1-55` — `run_checker_block` / `run_checker_capture`
- `lib/strip.sh` — `strip_command_literals`（无引号 / 无 heredoc 命令 case 短路跳过 python3）
- `lib/dedup.sh` — `_dedup_if_fresh` warn 类 checker 同 key TTL 节流

实际工作中范例（按事件类型查）：

| 事件 | 推荐参考 hook |
|------|-------------|
| PreToolUse Bash 多规则聚合 | `pre-bash-guard.sh` + `lib/bash-guards.sh` |
| PreToolUse Write/Edit 多 guard 聚合 | `pre-writeedit-guard.sh` + `lib/pre-writeedit-guards.sh` |
| PreToolUse Write/Edit 路径门 | `lib/pre-writeedit-guards.sh` `pg_deliverable_source` |
| PreToolUse Write/Edit 配 transcript 反扫 | `lib/pre-writeedit-guards.sh` `pg_skill_load` |
| PostToolUse Write/Edit 多 checker 聚合 | `post-writeedit-dispatch.sh` + `lib/post-checks.sh` |
| PostToolUse Write/Edit 调 checker block | `lib/post-checks.sh` `pc_audit_fast` |
| PostToolUse Write/Edit 软 warn 永不 block | `lib/post-checks.sh` `pc_static_chapter` |
| PostToolUse Write/Edit warn 类 checker dedup 节流 | `post-writeedit-dispatch.sh` + `lib/dedup.sh` |
| PostToolUse Write/Edit 双分支（strict / warn 按路径分）| `lib/post-checks.sh` `pc_cjk_punct` |
| PostToolUse Bash 扫近 N 秒动过的文件 | `post-bash-deliverable-check.sh` |
| PostToolUse Read 纯观测 | `post-skill-load.sh` |
| PreCompact 注入状态 | `pre-compact.sh` |
| Stop 收尾任务 | `stop-dashboard-refresh.sh`（带 6h 鲜度 + 后台 fork）|
| Stop 抓 transcript | `stop-learn-capture.sh`（带去重 / 自引用过滤 / 双 schema 兼容）|

---

## 七、自检清单（写完新 hook 前过一遍）

- [ ] source 了 `lib/log.sh` + `lib/input.sh`（至少）
- [ ] `INPUT=$(cat); hook_parse_all` 而不是手写 python3
- [ ] 早退用 `require_bash` / `require_write_or_edit` 而不是 case
- [ ] 路径过滤用 `is_deliverable_path` / `is_excluded_path` 而不是 verbatim glob
- [ ] SKIP 用 `check_skip_env` 而不是手写 if-grep
- [ ] 命令名 grep 前 `strip_command_literals`（如适用）
- [ ] tempfile 用 `mktemp`（裸用，不加后缀模板）或 `lib/runner.sh`
- [ ] 稳定路径（TTL / 缓存）用 `${TMPDIR:-/tmp}/<name>`，一次性 tempfile 用 `mktemp`
- [ ] BSD/GNU 分叉命令（`sed -i` / `stat` / `date -d` / `grep -P` / `readlink -f`）取交集或双分支（§三 J）
- [ ] `log_event` 字符串名 = SKIP 环境变量名同源 kebab-case
- [ ] 退出码：0 / 2（不要 1）
- [ ] 失败时 stderr `>&2`，不要 stdout 也不要 /dev/null
- [ ] `set +e`（hook 不因子命令失败而崩溃）
- [ ] settings.json 注册了（如适用）
- [ ] `bash -n hook.sh` 语法过
- [ ] 喂非匹配 JSON 早退 RC=0
- [ ] 喂匹配 + 触发 JSON RC=2
- [ ] `bash .claude/skills/workspace-audit/scripts/audit.sh 15` 全绿
- [ ] stderr 走 §二 三段式（诊断 + 证据 + 修法 + SKIP 说明），不要只 forward checker 原始输出
- [ ] warn 类 checker（不阻断）用 `_dedup_if_fresh` 节流；block 类每次都跑不节流
- [ ] 热路径无冗余 fork：固定串判断用 bash 内建、复杂 grep / python3 前有 `case` 粗筛、同 JSON 不二次 jq（§三 K）
- [ ] `$var` 紧邻中文 / 全角标点 / emoji 已写 `${var}`（§三 L）
- [ ] UserPromptSubmit 提醒走 stdout `{systemMessage}`，不走 stderr（exit 0 stderr 被丢，§三 B / §一 模板）
