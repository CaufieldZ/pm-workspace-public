#!/bin/bash
# PreToolUse Bash hook: 外网下载命令自动挂代理后放行
#
# 触发：HARD 组（brew / pip / npm / pnpm / yarn / bun / cargo / composer 的安装类子命令、
#       go get|install|mod download、gh api|clone|run|repo clone）命中即触发；
#       SOFT 组 curl / wget / git clone 仅在命令里出现境外 URL 时触发
# 行为：判定到可用代理 → updatedInput 给命令前置 `export …;` 后放行（其余 tool_input 键原样带回）；
#       判定不到 → 原样放行，绝不注入没人监听的代理
# Escape：SKIP_PROXY_CHECK_GATE=1（旧名 SKIP_PROXY_CHECK=1 仍认）；PROXY_GATE_MODE=off 关整条、
#         =block 退回「命中即 exit 2 阻断」的旧行为
#
# 判定源是 scripts/lib/proxy.py：它**探口验活**，代理没在跑就判直连，端口与候选规则都在那边，
# 本文件不重复实现，也不写死任何端口。
#
# 为什么是注入而不是阻断：命中就阻断、让人重发一次带代理的命令，白付一轮往返——判定的活
# 本来就该 hook 干。注入点统一用「命令最前面加 export …;」，不在管道里找位置插前缀：前者对
# `cd /x && brew install jq`、`FOO=1 cmd`、多行、管道起手一律语义完整。
#
# 性能：判定（import lib.proxy + 探口）只在**正则命中之后**才做，未命中的绝大多数调用不付。
set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/strip.sh"

# 仓根从 hook 自身位置推，不用 $CLAUDE_PROJECT_DIR：后者是「被检查的工区」，测试 fixture /
# 跨工区调用时会指向别处，而判定源必须是本仓自己的 scripts/lib/proxy.py。
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$HOOK_DIR/../.." && pwd)"

INPUT=$(cat)
hook_parse_bash_input
require_bash

CMD="$HOOK_COMMAND"
[ -n "$CMD" ] || exit 0

# 粗筛短路（bash 内建，零 fork）：不含任何下载命令关键词的命令（绝大多数，如 git status / ls / cat）
# 直接退出，省下方几条复杂 grep 与 python3。
# 词取 HARD/SOFT pattern 全部命令名的**超集**——宁可 over-match 回落到精确 grep，绝不 under-match 漏判。
# `go` / `gh` 用双词 glob：`*go*` 会误命中 django / logo，`*" go "*` 会漏命令开头的 `go get`。
case "$CMD" in
  *brew*|*pip*|*npm*|*pnpm*|*yarn*|*bun*|*cargo*|*composer*|*curl*|*wget*|*clone*) ;;
  *go\ get*|*go\ install*|*go\ mod*|*gh\ api*|*gh\ clone*|*gh\ run*|*gh\ repo*) ;;
  *) exit 0 ;;
esac

# 模式开关用 bash 内建匹配（大小写不敏感），零 fork——热路径上不为它起子进程
GATE_MODE="${PROXY_GATE_MODE:-inject}"
case "$GATE_MODE" in [Oo][Ff][Ff]) exit 0 ;; esac

# 剥掉字符串字面量 / heredoc 内容，避免 `git commit -m "...brew install..."` 与
# `cat <<EOF ... EOF` 误判（只匹配剥后版本）
CMD_STRIPPED=$(strip_command_literals "$CMD")

# 静态 deny 里这几条以**命令开头**为准（settings.json：Bash(rm -rf /Users/*) / Bash(rm -rf .*) /
# Bash(sudo:*) / Bash(git push --force:*) …）。注入会在开头加 export，它们就匹配不上原始命令了 ——
# 等于替这条命令绕过 deny。故这类命令一律不改写，原样放行，让权限判定仍以原始命令为准。
case "$CMD_STRIPPED" in
  rm\ -rf*|sudo\ *|git\ push*) exit 0 ;;
esac

# 左边界 = 行首 / 管道分隔符 / 可选 ENV=val 前缀
HARD_HIT=no
printf '%s' "$CMD_STRIPPED" | grep -qE '(^|[;&|`\n])[[:space:]]*([A-Z_][A-Z0-9_]*=[^[:space:]]*[[:space:]]+)*(brew[[:space:]]+(install|tap|upgrade|reinstall|update)|pip3?[[:space:]]+install|npm[[:space:]]+(install|i|add|ci)|pnpm[[:space:]]+(install|i|add)|yarn[[:space:]]+(add|install)|bun[[:space:]]+(add|install)|cargo[[:space:]]+install|go[[:space:]]+(get|install|mod[[:space:]]+download)|gh[[:space:]]+(api|clone|run|repo[[:space:]]+clone)|composer[[:space:]]+(install|require|update))([[:space:]]|$)' && HARD_HIT=yes

# 条件拦组：curl / wget / git clone 仅在境外 URL 时拦。
# 只认 https?:// —— git@github.com:… 走 SSH 传输，代理对它毫无作用，注入了也是空转。
SOFT_HIT=no
if [ "$HARD_HIT" = "no" ]; then
  printf '%s' "$CMD_STRIPPED" | grep -qE '(^|[;&|`\n])[[:space:]]*([A-Z_][A-Z0-9_]*=[^[:space:]]*[[:space:]]+)*(curl|wget|git[[:space:]]+clone)([[:space:]]|$)' \
    && printf '%s' "$CMD_STRIPPED" | grep -qE 'https?://(github\.com|raw\.githubusercontent|gist\.github|pypi\.org|registry\.npmjs|crates\.io|rubygems\.org|proxy\.golang\.org|packagist\.org|go\.googlesource|googleapis|gcr\.io|ghcr\.io|docker\.io|quay\.io|huggingface\.co|anaconda\.org|objects\.githubusercontent)' \
    && SOFT_HIT=yes
fi

[ "$HARD_HIT" = "no" ] && [ "$SOFT_HIT" = "no" ] && exit 0

# 命令里已自带代理（含 curl --proxy / -x 的显式指定）→ 放行，不叠加
printf '%s' "$CMD" | grep -qiE '(ALL_PROXY|HTTPS?_PROXY|all_proxy|https?_proxy)=|--proxy[[:space:]]|-x[[:space:]]*https?://' && exit 0

# 国内镜像 / 直连可达的源 → 放行（这些端点挂代理反而绕路）
printf '%s' "$CMD" | grep -qE '(pypi\.tuna\.tsinghua|npmmirror|mirrors\.(aliyun|tencent|ustc|163)|registry\.npm\.taobao|goproxy\.cn|\.cn[/:])' && exit 0

# 与注入语义冲突（要的就是不走代理 / 环境被清空）→ 放行
printf '%s' "$CMD_STRIPPED" | grep -qiE '--noproxy|env[[:space:]]+-i([[:space:]]|$)|env[[:space:]]+-u[[:space:]]+[^[:space:]]*PROXY|unset[^\n]*PROXY' && exit 0

# sudo 开头 → 放行：sudo 默认重置环境，注入的变量递不进子进程，注了也是空转
printf '%s' "$CMD_STRIPPED" | grep -qE '(^|[;&|][[:space:]]*)sudo([[:space:]]|$)' && exit 0

# 显式跳过
check_skip_env "proxy-check" "SKIP_PROXY_CHECK_GATE" "${CMD:0:120}" --exit
printf '%s' "$CMD" | grep -q 'SKIP_PROXY_CHECK=1' && {
  _log_skip_gate "proxy-check" "inline-legacy  ${CMD:0:120}"
  exit 0
}

# 到这一步才判定代理：探活端口，代理没在跑就判直连（人在境外），不注入。
# 候选端口与验活规则全在 lib/proxy.py，这里不重复实现。同进程 import，不再起第二个解释器干解析。
# stderr 单独收着：空结论有两种来源——「判直连」（正常）与「判定源 import 失败」（异常），
# 吞掉 stderr 会让后者在日志里伪装成前者。
PROXY_ERRFILE=$(mktemp)
PREFIX=$(PROXY_ROOT="$ROOT_DIR" python3 - 2>"$PROXY_ERRFILE" <<'PY'
import os, sys
root = os.environ.get("PROXY_ROOT", "")
if root:
    sys.path.insert(0, os.path.join(root, "scripts"))
try:
    from lib.proxy import shell_prefix
except Exception:
    print("__LIB_ERROR__")          # 与「判直连」的空串区分开
else:
    print(shell_prefix() or "")
PY
)

# 判定源自己坏了（库缺失 / 导入异常）→ 原样放行，但日志里与「无代理」分开记
# 记 warn 不记 skip：skip 是「用户主动绕过」的语义（telemetry gate-health 按它判门槛是否被绕），
# 这里 gate 是想跑而跑不了，混进去会让健康度误报
if [ "$PREFIX" = "__LIB_ERROR__" ]; then
  log_event gate proxy-check warn "lib-error  $(head -1 "$PROXY_ERRFILE" 2>/dev/null | cut -c1-60)"
  rm -f "$PROXY_ERRFILE"
  exit 0
fi
rm -f "$PROXY_ERRFILE"

# 判定不到可用代理（境外 / 代理未启动）→ 原样放行。这是本门的正常结论（工作就是「判有没有」），
# 记 clean 而非 skip，理由同上
if [ -z "$PREFIX" ]; then
  log_event gate proxy-check clean "no-proxy  ${CMD:0:120}"
  exit 0
fi

# 从 `export ALL_PROXY=<url> …;` 里取 url 只为写进放行理由，零 fork
rest="${PREFIX#export ALL_PROXY=}"
PROXY_HINT="${rest%% *}"

case "$GATE_MODE" in
  [Bb][Ll][Oo][Cc][Kk])
    echo "" >&2
    echo "🚫 [proxy-check] 外网下载命令未设代理" >&2
    echo "   ${CMD:0:120}" >&2
    echo "" >&2
    echo "   → 修法 1: 跑 eval \"\$(python3 scripts/lib/proxy.py --export)\" 后重发本条命令" >&2
    echo "   → 修法 2: 确认本条不需代理（国内源 / 已自有代理）→ SKIP_PROXY_CHECK_GATE=1" >&2
    echo "" >&2
    log_event gate proxy-check block "${CMD:0:120}"
    exit 2
    ;;
esac

NEW_CMD="${PREFIX} ${CMD}"

# updatedInput 是**整个 tool_input 的替换、不是补丁**：用 jq 的对象合并把 command 换掉，
# 其余键（description / timeout / run_in_background …）原样带回。合并失败就不注入——
# 宁可少挂一次代理，也不丢 tool_input 的其余键。
JSON_OUT=$(jq -nc \
  --argjson ti "${HOOK_TOOL_INPUT:-{\}}" \
  --arg cmd "$NEW_CMD" \
  --arg url "$PROXY_HINT" \
  '{hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: ("[proxy-gate] 已自动挂上代理 " + $url + "（判定见 scripts/lib/proxy.py）"),
      updatedInput: ($ti + {command: $cmd})
    }}' 2>/dev/null)

if [ -z "$JSON_OUT" ]; then
  # jq 缺失 / tool_input 非法 → 不改写（宁可少挂一次代理，也不丢 tool_input 其余键）。记 warn
  log_event gate proxy-check warn "no-toolinput  ${CMD:0:120}"
  exit 0
fi

# 带 permissionDecision: allow —— 改写后命令以 `export ` 开头，settings.json 里原本锚在
# 命令开头的白名单前缀（Bash(brew install:*) 之类）都匹配不上，不显式放行就会每次注入都弹框。
# （allow 清单里已有 Bash(export:*) / Bash(source *) / Bash(ALL_PROXY=* *)，所以这一步
#  对多数注入可能是冗余的；显式带上是为了不依赖那条规则的匹配细节。）
#
# ⚠️ 改写本身会改变「命令开头」，锚在开头判定的一切规则都受影响。注入路径因此**不碰**
# 以静态 deny 起手的命令（见上方 deny 锚点守卫）；真要退回旧行为用 PROXY_GATE_MODE=block，
# 整条关用 =off。
printf '%s\n' "$JSON_OUT"
log_event gate proxy-check inject "${CMD:0:120}"
exit 0
