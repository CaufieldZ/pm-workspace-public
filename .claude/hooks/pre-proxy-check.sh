#!/bin/bash
# PreToolUse: 外网下载命令自动检查代理
# 命中高风险命令且未设代理 → exit 2 阻断
# 已设代理 / 国内源 / 不匹配 / 显式跳过 → exit 0

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
[ "$TOOL_NAME" = "Bash" ] || exit 0

CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)
[ -n "$CMD" ] || exit 0

# 剥掉字符串字面量 / heredoc 内容，避免 commit -m "...brew install..." / cat <<EOF ... EOF 误拦
CMD_STRIPPED=$(CMD_RAW="$CMD" python3 <<'PY'
import os, re, sys
cmd = os.environ.get("CMD_RAW", "")
# heredoc 体：<<EOF ... EOF / <<'EOF' ... EOF / <<-EOF ... EOF
cmd = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?[\s\S]*?\n\1", "", cmd)
# 双引号 / 单引号字符串字面量（不处理嵌套，够用）
cmd = re.sub(r'"(?:\\.|[^"\\])*"', '""', cmd)
cmd = re.sub(r"'[^']*'", "''", cmd)
sys.stdout.write(cmd)
PY
)

# 左边界 = 行首 / 管道分隔符 / 可选 ENV=val 前缀
# 只匹配剥字符串后的版本
HARD_HIT=no
echo "$CMD_STRIPPED" | grep -qE '(^|[;&|`\n])[[:space:]]*([A-Z_][A-Z0-9_]*=[^[:space:]]*[[:space:]]+)*(brew[[:space:]]+(install|tap|upgrade|reinstall|update)|pip3?[[:space:]]+install|npm[[:space:]]+(install|i|add|ci)|pnpm[[:space:]]+(install|i|add)|yarn[[:space:]]+(add|install)|bun[[:space:]]+(add|install)|cargo[[:space:]]+install|go[[:space:]]+(get|install|mod[[:space:]]+download)|gh[[:space:]]+(api|clone|run|repo[[:space:]]+clone)|composer[[:space:]]+(install|require|update))([[:space:]]|$)' && HARD_HIT=yes

# 条件拦组：curl / wget / git clone 仅在境外 URL 时拦
SOFT_HIT=no
if [ "$HARD_HIT" = "no" ]; then
  echo "$CMD_STRIPPED" | grep -qE '(^|[;&|`\n])[[:space:]]*([A-Z_][A-Z0-9_]*=[^[:space:]]*[[:space:]]+)*(curl|wget|git[[:space:]]+clone)([[:space:]]|$)' \
    && echo "$CMD_STRIPPED" | grep -qE '(https?://|git@)(github\.com|raw\.githubusercontent|gist\.github|pypi\.org|registry\.npmjs|crates\.io|rubygems\.org|proxy\.golang\.org|packagist\.org|go\.googlesource|googleapis|gcr\.io|ghcr\.io|docker\.io|quay\.io|huggingface\.co|anaconda\.org|objects\.githubusercontent)' \
    && SOFT_HIT=yes
fi

[ "$HARD_HIT" = "no" ] && [ "$SOFT_HIT" = "no" ] && exit 0

# 已设代理 → 放
echo "$CMD" | grep -qiE '(ALL_PROXY|HTTPS?_PROXY|all_proxy|https?_proxy)=' && exit 0

# 国内镜像 → 放
echo "$CMD" | grep -qE '(pypi\.tuna\.tsinghua|npmmirror|mirrors\.(aliyun|tencent|ustc|163)|registry\.npm\.taobao|goproxy\.cn|\.cn[/:])' && exit 0

# 显式跳过 → 放
echo "$CMD" | grep -q 'SKIP_PROXY_CHECK=1' && exit 0

# 命中
echo "" >&2
echo "[proxy-gate] 外网下载命令未设代理" >&2
echo "   $CMD" >&2
echo "   请改为: ALL_PROXY=http://127.0.0.1:7897 $CMD" >&2
echo "   国内源或确认不需代理: SKIP_PROXY_CHECK=1 $CMD" >&2
echo "" >&2
log_event gate proxy-check block "${CMD:0:120}"
exit 2
