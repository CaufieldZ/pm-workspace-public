# 写新 Script / 改老 Script 规范

写新 script 前 / 改老 script 前必读（`pre-writeedit-guard.sh` 的 `required-read-gate` 强制：改 `scripts/*.py` / `scripts/*.sh` / `scripts/lib/*.py` 前必须 Read 本文件）。

> 想查「当前有哪些 script、各管什么」→ [README.md](README.md)（`gen_scripts_readme.py` 自动生成）。本文件讲「怎么写」，README 讲「现在有啥」。加 / 删 script 后重跑生成脚本，audit §15 会校验 drift。

---

## 一、最小模板

按脚本类型选模板，复制粘贴改：

### CLI 入口脚本（`scripts/*.py`）

```python
#!/usr/bin/env python3
"""<一句话职责>。

用法：
    python3 scripts/<name>.py <file>... [--strict]
    cat foo.md | python3 scripts/<name>.py --stdin [--strict] [--json-out <path>]

退出码：
    0 — clean / warn（未传 --strict）
    2 — 传 --strict 且有违规（hook 用）
"""
from __future__ import annotations

import sys
from pathlib import Path


# 纯逻辑抽成可测函数（pytest 可直接 import，不依赖文件 / 网络）
def check_text(text: str) -> list[tuple]:
    """单行 / 全文扫描，返回 [(行号, 类别, 原文), ...]。"""
    ...


def check_file(path: Path) -> list[tuple]:
    """读文件 → check_text。Path.read_text(encoding='utf-8', errors='replace')。"""
    ...


def main() -> int:
    args = sys.argv[1:]
    strict = "--strict" in args
    use_stdin = "--stdin" in args
    files = [Path(a) for a in args if not a.startswith("-")]
    ...
    return 2 if (strict and hits) else 0


if __name__ == "__main__":
    sys.exit(main())
```

### 共享模块（`scripts/lib/*.py`）

```python
"""<共享职责一句话>。

调用方：
- scripts/check_X.py
- .claude/skills/Y/scripts/Z.py
"""
import re

# 模块级常量（正则 / 词表）—— SSOT，跨脚本共用同一份
PATTERN_X = re.compile(r"...")

# 纯函数：吃字符串 → 返回结构，无文件 / 网络 I/O
def scan_xxx(text: str) -> list[tuple[str, str]]:
    """返回 [(category, match_str), ...]。"""
    ...
```

---

## 二、exit code + 接口约定

### 退出码语义（与 hook 链路对齐）

| 码 | 含义 | 谁用 |
|----|------|------|
| `0` | clean（无违规）/ warn（有违规但未传 `--strict`） | 默认 |
| `2` | 传 `--strict` 且有违规 → hook 阻断 | post-writeedit / post-bash checker |
| `1` | 有违规但非 strict 级（仅 `check_plain_language` 用，warn 不阻断） | 极少用，新脚本别用 |

**hook 一律走 `--strict` 拿 exit 2 阻断**；人手跑不传 `--strict` 拿 warn（exit 0，不阻断）。

`gen_*.py` 生成文案类脚本产出后必过 humanize 复扫一遍（`check_plain_language.py` 等），生成时套用的模板措辞常年久失修带进新 AI 味 / 违规词，脚本产出不能豁免行文检查。

### 标准接口（按需组合）

- `--stdin`：管道输入（`sys.stdin.read()`），免去临时文件
- `--strict`：阻断模式（exit 2）
- `--json-out <path|->`：结构化结果写文件（或 `-` 走 stdout），供 hook 取命中词埋点
- `--fix` / `--dry-run`：可修复类（如 cjk 标点）的改写 + 预览

---

## 三、硬约束

### A. `if __name__ == "__main__":` guard 必须有

所有根脚本 `scripts/*.py` 必须把入口逻辑包进 guard，保证模块可被 pytest import（`from check_X import check_text`），不触发 main。

### B. 显式 `encoding="utf-8"`

所有 `open()` / `Path.read_text()` / `write_text()` 必须传 `encoding="utf-8"`。Python 3.13 默认编码行为变更，不传会在含 CJK 内容时炸。`errors="replace"` 容错读历史脏文件。

### C. 纯逻辑抽函数，main 只做 CLI

业务规则（扫描 / 解析 / 判定）抽成纯函数（吃字符串 → 返回结构），`main()` 只负责 argparse + 文件读写 + exit code。这样 pytest 直接测函数，不必 subprocess + 造文件。可测性是回归测试的前提。

### D. 复用 `scripts/lib/`，不重造

第二次出现的逻辑立即抽进 `scripts/lib/`。现有 lib 模块（检测类 `banned_terms` / `scene_match` / `ui_visual` / `truth_source` / `md_to_html` / `changelog_residue`；通用基元 `repo`(仓库根定位) / `path_skip`(lint 跳过判定 + `is_skipped`) / `lint_exempt`(行文 lint 产物豁免 + `is_lint_exempt`，规则表 `lint_exempt.txt` 与 bash 侧 `hooks/lib/guards.sh` 共读) / `json_out`(命中明细导出) / `diagram_text`(drawio·mmd 文本抽取) …）是跨脚本 SSOT。写新 checker 前先 `grep` lib 看有没有现成的。

import 路径：lib 模块走 `from lib.X import`（需 `scripts/` 在 `sys.path`，`scripts/tests/conftest.py` 已注入）；根脚本走 `import check_X`。

**改 lib 模块（加 header / 改签名 / 改常量）前必全仓 grep 所有消费者**：`grep -rn "from lib.X import\|from \.modname import"` + bash heredoc 形态 `grep -rn "X" --include='*.sh'`（`python3 << 'PY' from lib.X ... PY` 常规 `--include='*.py'` 抓不到）——不能只信已知调用方，漏消费者就破坏跨 skill 链路。

**跑 `ruff --fix` 清 F401 未用 import 前必反查被删符号是否被跨模块 import**：ruff 只看单文件视角，删掉的符号若被别处 `from this_module import symbol` 引用，`--fix` 会静默破坏跨模块调用，删前先 grep 符号名全仓引用。

### E. exit code 走 0/2，慎用 1

`exit 2` = hook 阻断；`exit 0` = 放行 / warn。`exit 1` 语义模糊（既非 clean 也非 strict block），新脚本别用。warn 类 checker（永不阻断）一律 `exit 0` 后写 stderr。

### F. 加 / 删脚本后跑 `gen_scripts_readme.py`

`scripts/README.md` 自动生成（列脚本名 + 职责）。加 / 删 / 改脚本 docstring 后跑 `python3 scripts/gen_scripts_readme.py`，audit §15.8 校验是否 drift。

同模式可复用给任何「源文件 → 清单」场景（hooks README 已用 `gen_hooks_readme.py`，未来给 `projects/` 等做清单）：ast 提取 docstring + 解析源文档表 / 配置 + `--check` drift（exit code 驱动）+ audit 接入（镜像 §15 加并列小节，`GLOBAL_FAIL` 上抛）。

### G. 测试落 `scripts/tests/test_*.py`

新 checker 的纯函数必须有对应 `test_*.py`（pytest，`@pytest.mark.parametrize` 覆盖正 / 负 / 边界）。exit code 契约走 `test-hooks.sh`（`--stdin` 喂脏 / 净断言 exit 2 / 0）。自动修复类脚本（空格插入 / 标点修复等）的测试必须断言「跑两次输出一致」（幂等性）——`\b` 边界后接 CJK 等场景跑两次会差。

### H. 临时路径跨平台：用 `tempfile`，禁裸 `/tmp`

`Path("/tmp/foo")` 在 Windows 原生 Python 是字面路径（落到当前盘符 `C:\tmp`），Git Bash 的 `/tmp → %TEMP%` 映射对原生 Python 无效 → `FileNotFoundError`。临时目录 / 文件一律走标准库：

- 目录：`Path(tempfile.gettempdir(), "prefix-xxx")` 或 `tempfile.mkdtemp(prefix="xxx-")`
- 文件：`tempfile.NamedTemporaryFile` / `mkstemp`
- 跨平台解析：macOS → `$TMPDIR`（`/var/folders/...`）、Linux → `/tmp`、Windows → `%TEMP%`
- 禁 `Path("/tmp/...")` 字面写死（含 dry-run 预览 / 中间产物 / 缓存目录）

### I. 多操作系统兼容（macOS / Linux / Windows）

**目标平台矩阵**：

| 脚本类型 | macOS（BSD userland）| Linux / WSL（GNU）| Windows 原生 |
|---------|------|------|------|
| `*.py` | ✅ | ✅ | ✅（须照本节写）|
| `*.sh` | ✅ | ✅ | ❌ CMD/PowerShell 无 bash；走 Git Bash / WSL |

Python 脚本必须三平台原生可跑；shell 脚本只保证 Unix-like（含 Git Bash / WSL），不为 Windows 原生 CMD/PS 兼容。

**Python（三平台）**：

- 文件 I/O 一律 `encoding="utf-8"`（§B），临时路径走 `tempfile`（§H）——这两条是 Windows 翻车高发区
- 路径用 `pathlib.Path` / `os.path.join` 拼，禁字面量 `/` 拼接、禁硬编码盘符；分隔符差异交给标准库
- 探测外部命令用 `shutil.which("x")`，不 `subprocess.run(["which", "x"])`（Windows 无 `which`）
- 调 macOS 专属命令（`open` / `pbcopy` / `sips` / `osascript`）前必按 `platform.system()` 分支，给 Windows（`startfile` / `start`）+ Linux（`xdg-open`）兜底；范例 [pack_for_opus.py:232](pack_for_opus.py#L232)
- 子进程别假设 shell 内建（`rm` / `cp` / `cat`）存在——用 `pathlib` / `shutil` 等价 API

**Shell（macOS BSD vs Linux/WSL GNU coreutils 分叉）**：同名工具 flag 行为分叉，取交集或显式双分支（BSD 优先 + GNU fallback）：

| 工具 | 陷阱 | 可移植写法 |
|------|------|-----------|
| `mktemp` | BSD 只替换模板**末尾**连续 X，`mktemp x.XXXXXX.md` 不随机化生成字面名 | 裸 `mktemp` 或 `"$(mktemp).md"` 加后缀 |
| `sed -i` | GNU 接 `-i`，BSD 须 `-i ''`（或带后缀）| `sed -i.bak`（两边通吃）后删 `.bak` |
| `stat` | BSD `-f '%Sm'`，GNU `-c '%y'` | BSD 优先 `\|\|` GNU fallback；范例 [publish.sh:86](publish.sh#L86) |
| `date -d` | GNU 有 `-d`/`--date`，BSD 无（用 `-v` / `-j -f`）| 偏移计算交给 `python3` |
| `readlink -f` | BSD 老版无 `-f` | 用 `python3 -c 'import os;print(os.path.realpath(...))'` |
| `grep -P` | BSD 无 PCRE | 用 ERE `grep -E` |
| `find -printf` | GNU 专属 | `find ... -exec stat ...` 或 `-print0` + 管道 |

CLI 缺失走 `command -v x >/dev/null 2>&1` 守卫静默降级（范例 `pbcopy` [publish.sh:208](publish.sh#L208)），不让缺命令把脚本拖崩。

**被 `set -u` 脚本 source 的共享库，内部所有环境变量引用必须写 `${VAR:-}`**：调用方开着 `set -u` 时，共享库里裸 `$VAR` 一旦变量未设置就直接中断调用方，加默认值兜底才不会连带炸主脚本。

### J. 生成脚本必须自证（换 session 定位得到）

产物生成脚本（`gen_*` / `build_*`，含 `projects/**/scripts/` 项目侧）要让「换 session 后第一次看到产物 / 脚本的人」双向定位得到源头：

- **产物 → 脚本**：生成的 HTML 顶部带 provenance 注释（走 `lib.html_builder.render_head` 的 proto/imap/arch 自动注入 `<!-- 源脚本 -->`；hand-roll HTML 的 deck 自己在输出串顶部加同款注释）。
- **脚本 → 用法**：脚本头部 docstring/注释不能只回显文件名，至少含「怎么跑 + 产物落哪 + 改哪重生」任一线索。`check_generator_docstring.py --scan` 扫退化 docstring（只回显文件名 = 抓瞎），可挂 audit / 手动跑。

### K. checker 声明的检查维度必须自证能命中（检查器健康度）

`check_*.py` / `check_*.sh` 的 fail_keys / 声明维度必须有断言「真能命中」——防「承诺检查了实际恒 0」的名存实亡（先例：missing_story_intro 声明后从未 append，检查形同虚设；check_mrd.sh 五问 `\|` 死模式永不命中）。

- 新增 fail_key / 新检查维度时，同步补 `scripts/tests/test_<name>.py` 正例断言（喂含该违规的文本 → 该 key 非空）
- 已有 fail_key 无测试的，先补测试再改动
- 无法构造违规样本的维度 → 从 fail_keys 删除（0 命中的规则是维护负担不是价值）；设计变更后不再适用的 fail_key 必须同步删（先例：H1 引言检查在设计改为「骨架章不查引言」后残留 2 轮迭代）

### L. > 300 行必读 references 必须配 ≤ 100 行 quickref（省 token）

SKILL.md References「必读」清单里的 md 文件 > 300 行时，必须同目录配 `<原名>-quickref.md`（≤ 100 行，只留必守硬规则 + 全量指针）。References 必读指向 quickref、全量降为按需读；skill-load-gate 的 GUIDE 清单同步指向 quickref。先例：prd-scene-templates 300 行 → quickref 67 行；prd-chapter-rules 561 行 → quickref ~100 行（每 PRD session 省 ~15K token）。

---

## 四、反模式清单（写 script 时禁犯）

| 反模式 | 正确做法 |
|--------|---------|
| 业务逻辑全塞 `main()` 里，没法 import 测 | 抽 `check_text` / `parse_*` 纯函数，main 只 CLI |
| `open(path)` / `read_text()` 不传 encoding | `encoding="utf-8"`（3.13 默认编码会炸 CJK） |
| `exit 1` 表示「有违规」 | `exit 2 if strict else 0`，1 留给 plain_language warn 级 |
| `2>/dev/null` 吞 checker 真实错误（静默漏判） | 输出收 tmpout，失败时展示给用户 |
| glob 漏递归（`glob` 不递归，季度子目录假绿） | 要递归用 `rglob` / `Path.rglob()` |
| 第 N 次重写「场景编号匹配」「章节锚点」 | 复用 `lib/scene_match`；锚点类先全仓 grep 现成实现再新建（新建即登记消费方，防死模块） |
| 根脚本裸写 `print(...); sys.exit(2)` 无 guard | 包 `if __name__ == "__main__":` |
| 多文件违规报错指错文件（`head -1` 凑数） | 从 checker 输出解析真违规文件 |
| 加了脚本没跑 `gen_scripts_readme.py` | 加 / 删 / 改 docstring 后必跑，audit §15 校验 |
| 纯函数依赖文件 / 网络（没法单测） | I/O 注入路径 / mock，逻辑保持纯 |
| `Path("/tmp/foo")` 硬编码临时路径 | `Path(tempfile.gettempdir(), "foo")` / `tempfile.mkdtemp()`（Windows 原生 Python 落到 `C:\tmp` 失败）|
| `mktemp x.XXXXXX.md`（带后缀模板，BSD 不随机化生成字面名）| 裸 `mktemp` 或 `"$(mktemp).md"`（§I）|
| shell 直用 `sed -i` / `stat -c` / `date -d` / `readlink -f` / `grep -P`（BSD/GNU 分叉）| 取交集或 BSD 优先 + GNU fallback（§I 表）|
| Python `subprocess(["which", x])` / 直调 `open`·`pbcopy`（Windows / Linux 无）| `shutil.which` 探测；macOS 专属命令按 `platform.system()` 分支兜底（§I）|
| 凭内联测试 / 表象反推 bug（把好代码误判成坏代码）| 先逐行读源码确认逻辑，再用脚本本身跑单事件验证脚本对不对，再下结论 |
| `set -u` 下裸 `$var` 后紧跟全角符号 / 中文（贪婪吞多字节进变量名报 unbound variable）| 变量后跟非 ASCII 一律 `${var}` 显式定界 |
| 给已有 `set +e` / `test && action` 惯用法的脚本机械加 `set -euo pipefail` | 加之前实跑一遍确认（无匹配 grep / false test 会触发中止，破坏退出码驱动控制流）|
| shell 函数末尾 `[ cond ] && cmd`（条件假时返回 1 冒泡成函数 / 脚本退出码）| 干跑类分支显式 `return 0` |
| `trap '_rc=$?; log_event ... "$([ $_rc -eq 0 ] && echo ok || echo fail)"' EXIT`（trap 埋点内用命令替换判断状态）| trap 内先预判变量：`trap '_rc=$?; _s="failed"; [ "$_rc" -eq 0 ] && _s="completed"; log_event ... "$_s"'`——脚本被管道截断（`\| head` / `\| grep`）SIGPIPE 中断后，trap eval 的 `$(...)` 会捕获 echo 残留（含换行 / ANSI 转义），污染 log_dir 等下游参数，mkdir 生成怪目录树；hub/ 5 脚本同构问题即此 |
| 跑生成器回归对真实产物路径加 `--force` | 生成到一次性测试路径，或用 `git diff` 证明该代码路径未被改动 |
| 在 zsh 里 source bash 共享库做验证 | 必须真 bash 下跑（`bash -c` 或临时脚本），zsh 数组展开 / glob 语义静默失真 |
| 改脚本生成的产物（周报 / HTML / README）只改产物不改源码 | 改生成脚本源码字面量，只改产物会被下次 gen 覆盖；改完 dry-run 重生验证 |
| `--fix` 修复路径某步绕过检测侧保护区（逐字符替换查 span，收敛 `re.sub` 裸跑整行）→ 行内代码 / URL 里的 `!!` `??` 被改坏 | 检测剥掉什么，修复就不得触碰什么：每个改写步骤走同一保护区判定（先例：check_cjk_punct fix_line 的收敛 sub 无视 span，`sudo !!` 被写成 `sudo ！`） |
| 按时间正序的追加式日志（usage.jsonl）取「最近一次」用 `setdefault` → 拿到**最旧**时间戳 | 正序遍历直接覆盖赋值 `dict[key] = ts`；setdefault 是「首见即冻结」（先例：dashboard 4 处最近一次列全显示最旧，活跃项被误判 dead） |
| 同一口径（哨兵值 / 多词分隔符 / 日期边界）多处实现只改一处 → 姊妹脚本口径分叉 | 口径出现第二处即抽 lib 纯函数或注释互指，改前 grep 全部同类实现（先例：神策 -1 哨兵 3 处只实现 2 处；命中内容逗号拆分姊妹脚本只实现 1 处，额度回收候选整批误判） |

---

## 五、改动 / 退役 script 清单

### 改名 / 改职责

1. 改文件名 + 改 docstring 一句话职责
2. `grep -rn` 旧名（CLAUDE.md / runbook / 别的脚本 import / hook 调用）全跟
3. 跑 `gen_scripts_readme.py` 更新 README

### 删 script

1. `grep -rn <name>` 确认零引用（含 `from <name>` / `from lib.<name>` / **`from .<name>`（lib 内相对导入）** / bash heredoc `python3 << 'PY' from lib.X`）
2. 删文件 + 删所有调用方
3. 跑 `gen_scripts_readme.py`

---

## 六、自检清单（写完新 script 前过一遍）

- [ ] `if __name__ == "__main__":` guard 有
- [ ] 所有 `open` / `read_text` / `write_text` 传了 `encoding="utf-8"`
- [ ] 业务逻辑抽成纯函数（吃字符串 → 返回结构），main 只 CLI
- [ ] 复用了 lib（没重造已有逻辑）
- [ ] exit code 0/2（hook 用 `--strict` 拿 2），没用 1
- [ ] `--stdin` / `--strict` / `--json-out` 接口按约定（如需）
- [ ] 错误不 `2>/dev/null` 吞（收 tmpout，失败展示）
- [ ] `scripts/tests/test_<name>.py` 有对应纯函数测试
- [ ] 改 `scripts/lib/*.py` 后 `mypy scripts/lib/` 通过（类型标注兑现；根 scripts 暂不强制）
- [ ] `test-hooks.sh` 有 `--stdin` exit code 契约断言（如是 hook 调的 checker）
- [ ] 临时路径用 `tempfile`（`gettempdir()` / `mkdtemp()`），无裸 `Path("/tmp/...")`
- [ ] 多 OS 兼容（§I）：Python 三平台（路径 `pathlib`、`shutil.which` 探命令、macOS 专属命令按 `platform.system()` 分支）；shell `mktemp`/`sed -i`/`stat`/`date` 取 BSD∩GNU 交集或双分支
- [ ] 跑过 `gen_scripts_readme.py`，README 无 drift
