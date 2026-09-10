# Review 维度分工表

> 本文件是**索引不是知识库**——规则原文在 `scripts/SCRIPTS_WRITING.md` 与 `.claude/hooks/HOOK_WRITING.md`，本表只回答「这条谁查、在哪读」。
> Step 3 逐条对着 diff 过表 B；表 A 的维度已有 gate 兜底，报告里只汇总不重述（SKILL.md §硬规则 R4）。

## 表 A：机械层已覆盖（不重复报）

| 维度 | 谁查 |
|---|---|
| Python 语法 / 未定义名 / 重复定义 | `script-syntax-gate`（ruff F，写时即拦）+ 本 skill 第 ② 段补 F401 |
| Shell 语法 / shellcheck error 级 | `script-syntax-gate`（`bash -n`）+ 第 ② 段 shellcheck |
| `open()` 缺 encoding · `mktemp` 后缀模板 · 裸 `sed -i` · GNU-only coreutils | `audit.sh 19`（第 ② 段跑，全仓回归信号） |
| 明文 secret · staged 超大文件 | `.githooks/pre-commit` |
| SKILL.md 结构 / 三件套纯洁性 / 依赖闭环 / 计数对账 | `audit.sh 1,14,16,20`（走 workspace-audit，不归本 skill） |
| 生成脚本 docstring 退化 | `check_generator_docstring.py`（第 ② 段命中 `gen_*` / `build_*` 时跑） |

## 表 B：机械层空白，必须人眼过

### B1 · Python 结构与可测性 — `scripts/SCRIPTS_WRITING.md §三`

| 看 diff 里有没有 | 锚点 |
|---|---|
| 业务判定逻辑写在 `main()` 里，没抽成吃字符串 → 返回结构的纯函数 | §三-C |
| 入口逻辑没包 `if __name__ == "__main__":`，pytest 一 import 就跑 main | §三-A |
| 纯函数里读文件 / 发网络请求，没法单测 | §三-C · §四 |
| `exit 1` 表示「有违规」（语义模糊，hook 只认 0/2） | §三-E |
| `--help` 被参数解析吞掉后静默执行真逻辑；`add_argument` 零 `help=` | §二 · §四 |
| `--stdin` / `--strict` / `--json-out` 接口偏离约定形态 | §二 |

### B2 · 复用与口径一致 — `SCRIPTS_WRITING.md §三-D`

| 看 diff 里有没有 | 锚点 |
|---|---|
| 第二次实现同一逻辑（场景编号匹配 / 章节锚点 / 日期边界 / 哨兵值），没查 `scripts/lib/` 有没有现成的 | §三-D · §四 |
| 改了 `lib/` 的签名 / 常量却只跟了已知调用方 — 对着脚本第 ③ 段消费者清单逐条核 | §三-D |
| 同一口径在姊妹脚本里各写一份，本次只改了一处 | §四 |
| 跑 `ruff --fix` 删掉的符号被别处 `from X import` 引用 | §三-D |

### B3 · 静默错数据（🔴 高发区）

| 看 diff 里有没有 | 锚点 |
|---|---|
| `2>/dev/null` 吞掉 checker 真实错误 → 假绿 | §四 · HOOK_WRITING §三-2 |
| `glob` 该用 `rglob`（漏递归 → 子目录假绿） | §四 |
| 追加式日志取「最近一次」用 `setdefault`（拿到的是最旧） | §四 |
| 非唯一键做 dict 键（摘要 / 裸文件名），跨目录同名静默互相覆盖 | `skill-conventions.md §Checker/Gate 设计踩坑` |
| `--fix` 的改写步骤绕过检测侧保护区（行内代码 / URL 被改坏） | §四 |
| 多文件违规报错指错文件（`head -1` 凑数） | §四 |

**出报告纪律**：🔴 级「会崩 / 静默错数据」结论先实跑复现再上报（SKILL.md §硬规则 R6），复现不了降 🟡 标「未复现」——锚点 `SCRIPTS_WRITING.md §四`「凭内联测试 / 表象反推 bug」。

### B4 · Shell 与 hook — `.claude/hooks/HOOK_WRITING-quickref.md`

| 看 diff 里有没有 | 锚点 |
|---|---|
| `$var` 紧邻中文 / 全角符号没写 `${var}`（`set -u` 下贪婪吞多字节报 unbound） | §四 · quickref §五 |
| 函数末尾 `[ cond ] && cmd`（条件假返回 1 冒泡成函数退出码） | §四 |
| `trap` 埋点内用 `$(...)` 判断状态（SIGPIPE 后捕获 echo 残留污染下游） | §四 |
| 给已有 `set +e` / `test && action` 惯用法的脚本机械加 `set -euo pipefail` | §四 |
| 被 `set -u` 脚本 source 的共享库里裸 `$VAR` 没写 `${VAR:-}` | §三-I |
| 新 gate 名与 `SKIP_<UPPER>_GATE` 不同源；改了已有 gate 名（dashboard 会断） | quickref §三-1 |
| stderr 只 forward checker 原始输出，没走四段式 | quickref §二 |
| 热路径新增 fork（`echo \| grep` / `sed -nE` 抽段 / 多次 `jq`） | quickref §四 |
| warn 类 checker 没包 `_dedup_if_fresh` 节流 | quickref §五 |

### B5 · 检查器健康度 — `SCRIPTS_WRITING.md §三-K`

| 看 diff 里有没有 | 锚点 |
|---|---|
| 新增 fail_key / 检查维度，但没有正例断言证明真能命中（承诺检查了实际恒 0） | §三-K |
| 设计变更后不再适用的 fail_key 残留没删 | §三-K |
| warn 级检查形同虚设（常被忽略的规则该直接上 block） | `skill-conventions.md §Checker/Gate 设计踩坑` |
| 存量违规多的新规则没做 diff-based（只拦新行），会把 living 文档卡死 | 同上 |
| 给行文检测器加了豁免，没核对与同族 block gate 是否分叉 | 同上 |

### B6 · 跨平台 — `SCRIPTS_WRITING.md §三-I`（audit 19 之外的部分）

| 看 diff 里有没有 | 锚点 |
|---|---|
| `subprocess(["which", x])` 探命令（Windows 无 `which`），该用 `shutil.which` | §三-I |
| 调 macOS 专属命令（`open` / `pbcopy` / `sips` / `osascript`）没按 `platform.system()` 分支兜底 | §三-I |
| 路径用字面 `/` 拼接 / 硬编码盘符，没走 `pathlib` | §三-I |
| 子进程假设 shell 内建（`rm` / `cp` / `cat`）存在 | §三-I |

### B7 · 产物与源码同步

| 看 diff 里有没有 | 锚点 |
|---|---|
| 改了脚本生成的产物（周报 / HTML / README）却没改生成脚本源码字面量 | §四 |
| 跑生成器回归时对真实产物路径加了 `--force` | §四 |
| 生成脚本 docstring 只回显文件名，看不出「怎么跑 + 产物落哪 + 改哪重生」 | §三-J |
| 加 / 删根 script 后没跑 `gen_scripts_readme.py` | §三-F |

### B8 · 工程纪律（CLAUDE.md §代码与工程纪律）

| 看 diff 里有没有 | 锚点 |
|---|---|
| 改动追溯不到用户请求（顺手「改进」无关代码 / 格式 / 注释） | CLAUDE.md |
| 本次改动让 import / 变量 / 函数变 unused 却没删 | CLAUDE.md |
| 一次性 fixture / 半成品脚本跑完没删 | CLAUDE.md |
| 给单次使用的代码加抽象 / configurability / impossible 场景的 error handling | CLAUDE.md |
| 数据结构变更没一次做完链路（上游产出 → 下游消费 → 老数据降级） | CLAUDE.md |
| 脚本注释 / docstring 写了时间向量与因果叙述（沿革该进 git log） | CLAUDE.md |
