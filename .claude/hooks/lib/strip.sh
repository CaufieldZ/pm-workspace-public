#!/usr/bin/env bash
# 共享：剥 shell 命令里的字符串字面量 / heredoc 内容
#
# 用途：在用 grep 检测命令名前清掉字符串里出现的关键字
# 典型场景：避免 `git commit -m "...md_to_confluence.py..."` 让命令检测假阳
#          避免 `echo "ALL_PROXY=..."` 让 proxy-check 假阳
#
# 用法：
#   source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/strip.sh"
#   CMD_STRIPPED=$(strip_command_literals "$CMD")
#
# 实现：删 heredoc 块；双引号串变 ""；单引号串变 ''
set +e

strip_command_literals() {
  # 无引号 / 无 heredoc 的命令（git status / ls / python3 x.py 等绝大多数）无字面量可剥，
  # case 原样返回跳过 python3（省 ~30ms fork）。含 " ' << 才走 python3 精确剥。
  # 等价性：无字面量时 python 三个 re.sub 都不匹配，输出本就 == 输入。
  case "$1" in
    *\"*|*\'*|*'<<'*) ;;
    *) printf '%s' "$1"; return 0 ;;
  esac
  CMD_RAW="$1" python3 <<'PY'
import os, re, sys
cmd = os.environ.get("CMD_RAW", "")
cmd = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?[\s\S]*?\n\1", "", cmd)
cmd = re.sub(r'"(?:\\.|[^"\\])*"', '""', cmd)
cmd = re.sub(r"'[^']*'", "''", cmd)
sys.stdout.write(cmd)
PY
}

# 把命令按 shell 连接符（; && || |）+ 换行切成段，每段一行输出。
# 用途：逐条命令判 git 安全 / https，避免整行 grep 让 `.*` 跨命令拼凑假阳
# （`git push --force origin dev && git checkout main` 被误判 force-push-main）或漏判。
split_command_segments() {
  # 反斜杠续行先并回单行再切段：跨行命令拆两段会让逐段判定漏拦（--force 与目标分居两段即绕过 git-safety）
  local cmd="${1:-}"
  printf '%s' "${cmd//'\'$'\n'/}" | tr ';&|' '\n\n\n'
}

# 只删引号字符本身、保留被引内容（供安全门抽路径 / 项目名）。
# 与 strip_command_literals 相对：那个把整个引号串抹成 ""（防命令名在字符串里假阳）；
# 安全门抽「被引号包住的真实路径 / 项目名」必须用本函数，否则引号一包路径就抹没了 = 门禁 fail-open。
strip_quote_chars() {
  printf '%s' "${1:-}" | tr -d "\"'"
}
