#!/bin/bash
# PreToolUse: Bash 命令前置守卫（多规则聚合 · 5 hook 合并入口）
#
# 本文件内联规则：
#   A：外网下载未设代理 → warn 不阻断（命令照跑，连不通由 proxy-fallback.md 兜底）
#   B：git push/remote 用 HTTPS → 阻断（CLAUDE.md「push 用 SSH」）
#   C：gen_prd_skeleton --force 但目标 scenes 目录有旧文件 → 阻断（LEARNED 2026-05-12 L8）
#
# lib/bash-guards.sh 子函数（原独立 hook 合并，gate 名不变）：
#   risky-op / git-safety / prototype-paradigm-gate
#
# 任一命中 exit 2；跳过：git-safety 支持 SKIP_GIT_SAFETY_GATE=1、prototype-paradigm 支持
# SKIP_PROTOTYPE_PARADIGM_GATE=1（均 env / 命令行前缀双通道）；risky-op 无逃生门（按 block 消息修法走，防绕过安全网）
set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/input.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/guards.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/strip.sh"
source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/bash-guards.sh"

INPUT=$(cat)
hook_parse_all
require_bash

CMD="$HOOK_COMMAND"
[ -n "$CMD" ] || exit 0

CMD_STRIPPED=$(strip_command_literals "$CMD")

# === 合并的 3 个 guard（各自判 trigger / SKIP；命中违规直接 exit 2）===
# 放在内联规则前：内联 proxy 规则在「非下载命令」时会 exit 0，会挡掉后续 guard
guard_risky_op "$CMD" "$CMD_STRIPPED"
guard_git_safety "$CMD" "$CMD_STRIPPED"
guard_prototype_paradigm "$CMD" "$CMD_STRIPPED"

# === 规则 B：git push / git remote (add|set-url) 用 HTTPS 拦截 ===
# case 粗筛：不含 github.com 的命令直接跳过（绝大多数），省 SKIP grep + pattern grep。
# 注：用原始 $CMD 而非 $CMD_STRIPPED——strip_command_literals 会把引号内 URL 整体抹成 ""，
#     导致 git remote add origin "https://github.com/..." 里的 URL 消失，gate 静默 fail-open。
case "$CMD" in
  *github.com*)
    if [ "${SKIP_GIT_HTTPS_GATE:-0}" != "1" ] && [[ "$CMD" != *SKIP_GIT_HTTPS_GATE=1* ]]; then
      # 逐段判：动词看 stripped 段（剥引号字面量，echo "...git remote add..." 不误拦），
      # URL 看原始段（git remote add origin "https://..." 引号内的 URL 仍要拦）。
      # 整行 `.*` 会跨命令误判（git push origin dev && curl https://github.com/... 被当成 push over https），故拆两判。
      while IFS= read -r _seg || [ -n "$_seg" ]; do
        _seg_stripped=$(strip_command_literals "$_seg")
        printf '%s' "$_seg_stripped" | grep -qE '\bgit([[:space:]]+[^[:space:]]+)*[[:space:]]+(push|remote[[:space:]]+(add|set-url))([[:space:]]|$)' || continue
        printf '%s' "$_seg" | grep -q 'https://github\.com' || continue
        echo "" >&2
        echo "🚫 [git-https-gate] git push/remote 应用 SSH，不用 HTTPS" >&2
        echo "   $CMD" >&2
        echo "   改成: 当前仓库的 SSH URL（git remote -v 查，形如 git@github.com:<owner>/<repo>.git）" >&2
        echo "   显式跳过: SKIP_GIT_HTTPS_GATE=1 $CMD" >&2
        log_event gate git-https-gate block "${CMD:0:120}"
        exit 2
      done <<EOF
$(split_command_segments "$CMD")
EOF
    fi
    ;;
esac

# === 规则 C：gen_prd_skeleton --force 前置检查 ===
# case 粗筛：不含 gen_prd_skeleton 的命令直接跳过。
case "$CMD_STRIPPED" in
  *gen_prd_skeleton*)
    if [ "${SKIP_SKELETON_FORCE_GATE:-0}" != "1" ] && [[ "$CMD" != *SKIP_SKELETON_FORCE_GATE=1* ]]; then
      if echo "$CMD_STRIPPED" | grep -qE 'gen_prd_skeleton\.py[[:space:]].*--force'; then
        # 抽 -p / --project 后的项目名，找目标 scenes 目录（先去引号：-p "community" 否则带引号 find 不到 = 门禁失效）
        TARGET=$(strip_quote_chars "$CMD" | grep -oE '(-p|--project)[[:space:]]+[^[:space:]]+' | head -1 | awk '{print $2}')
        if [ -n "$TARGET" ]; then
          SCENES_DIRS=$(find "${CLAUDE_PROJECT_DIR:-$(pwd)}/projects" -type d -name "prd-${TARGET}*-scenes" 2>/dev/null | head -3)
          if [ -n "$SCENES_DIRS" ]; then
            echo "" >&2
            echo "🚫 [skeleton-force-gate] gen_prd_skeleton --force 不清 stale" >&2
            echo "   目标 scenes 目录已存在：" >&2
            echo "$SCENES_DIRS" | sed 's/^/     /' >&2
            echo "   先 rm -rf 旧 scenes 目录 + 主 md，再 --force（LEARNED 2026-05-12）" >&2
            echo "   显式跳过: SKIP_SKELETON_FORCE_GATE=1 $CMD" >&2
            log_event gate skeleton-force-gate block "${CMD:0:120}"
            exit 2
          fi
        fi
      fi
    fi
    ;;
esac

# === 规则 D：delta PRD 推 Confluence 前未见冷读产物 ===
# case 粗筛：不含 md_to_confluence 的命令直接跳过。
case "$CMD_STRIPPED" in
  *md_to_confluence*)
    if [ "${SKIP_COLD_READ_GATE:-0}" != "1" ] && [[ "$CMD" != *SKIP_COLD_READ_GATE=1* ]]; then
      # 抽 delta PRD md 路径：deliverables/{季}Q{N}/{版}/prd-*.md（季度段避开 baseline / 普通 PRD）
      # 用去引号版而非 CMD_STRIPPED：引号包住的路径会被 strip_command_literals 抹成 ""，门禁 fail-open
      DELTA_MD=$(strip_quote_chars "$CMD" | grep -oE '[^[:space:]]*deliverables/[0-9]{4}Q[1-4]/[^[:space:]/]+/prd-[^[:space:]]+\.md' | head -1)
      if [ -n "$DELTA_MD" ]; then
        MD_DIR=$(dirname "$DELTA_MD")
        if ! ls "$MD_DIR"/cold-read-*.md >/dev/null 2>&1; then
          echo "" >&2
          echo "🚫 [cold-read-gate] delta PRD 推 Confluence 前未见冷读产物" >&2
          echo "   $DELTA_MD" >&2
          echo "   交付前冷读是推 wiki 前必跑工序（抓机械自检漏掉的语义盲点）：" >&2
          echo "   python3 .claude/skills/prd/scripts/cold_read.py --prepare $DELTA_MD → 派干净子代理逐 target 跑 → 盲点 triage" >&2
          echo "   已跑过冷读 / 本次确无需要 → 显式跳过：SKIP_COLD_READ_GATE=1 $CMD" >&2
          log_event gate cold-read-gate block "${CMD:0:120}"
          exit 2
        fi
      fi
    fi
    ;;
esac

# === 规则 A：外网下载未设代理（原有逻辑，复用上方 CMD_STRIPPED）===
# case 粗筛短路：不含任何下载命令关键词的命令（绝大多数，如 git status / ls / cat）
# 直接 exit 0，省下方 4~6 个复杂 grep。粗筛是 HARD/SOFT pattern 全部命令名的超集
# （宁可 over-match 回落到精确 grep，绝不 under-match 漏拦）。go/gh 用双词 glob 覆盖命令开头。
case "$CMD_STRIPPED" in
  *brew*|*pip*|*npm*|*pnpm*|*yarn*|*bun*|*cargo*|*composer*|*curl*|*wget*|*clone*) ;;
  *go\ get*|*go\ install*|*go\ mod*|*gh\ api*|*gh\ clone*|*gh\ run*|*gh\ repo*) ;;
  *) exit 0 ;;
esac

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
echo "$CMD" | grep -qiE '(ALL_PROXY|HTTPS?_PROXY|all_proxy|https?_proxy)=|--proxy[[:space:]]|-x[[:space:]]*https?://' && exit 0

# 国内镜像 → 放
echo "$CMD" | grep -qE '(pypi\.tuna\.tsinghua|npmmirror|mirrors\.(aliyun|tencent|ustc|163)|registry\.npm\.taobao|goproxy\.cn|\.cn[/:])' && exit 0

# 显式跳过 → 放
echo "$CMD" | grep -q 'SKIP_PROXY_CHECK=1' && exit 0

# 命中：warn 不阻断（命令照跑，连不通由 proxy-fallback.md runbook 事后兜底）
# 事前无法预判直连通不通（海外直连正常 / 墙内才需代理），所以只提示不拦
PROXY_HINT="${ALL_PROXY:-http://127.0.0.1:7897}"
echo "" >&2
echo "⚠️  [proxy-check] 外网下载未设代理（海外直连正常则忽略本提示）" >&2
echo "   $CMD" >&2
echo "   自动降级: bash scripts/net_retry.sh <cmd>（直连失败自动加代理重试）" >&2
echo "   含管道/重定向时手动: ALL_PROXY=$PROXY_HINT $CMD" >&2
echo "" >&2
log_event gate proxy-check warn "${CMD:0:120}"
exit 0
