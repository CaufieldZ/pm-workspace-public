#!/usr/bin/env bash
# 共享：PreToolUse Bash 守卫子函数（被 pre-bash-guard.sh 调度）
#
# 用途：合并 pre-risky-op + pre-git-safety + pre-prototype-paradigm-gate
#       独立 Bash hook 到单一入口，省进程启动 + 共享 hook_parse_all / strip_command_literals
#
# 每个 guard_* fn 约定：
#   - 入参：$1=CMD（原始，含 env 前缀）  $2=CMD_STRIPPED（已剥字面量）
#   - 自检 trigger pattern（不命中 return 0），SKIP 用 check_skip_env（命中会 exit 0 整链放行 = 与原独立 hook 行为一致）
#   - 命中违规 → stderr 三段式 + log_event 原 gate 名 + exit 2
#   - 放行 → log_event triggered/clean（如原 hook 有）+ return 0
#
# gate 名是稳定契约（dashboard 按字符串聚合，HOOK_WRITING §三-A）：
#   risky-op / git-safety / prototype-paradigm-gate —— 保持不变
set +e

# ── Guard 1: 高风险 Bash 操作 warn（原 pre-risky-op.sh，不阻断）──────────────
guard_risky_op() {
  local cmd_stripped="$2"
  local risky_reason=""

  # case 粗筛短路：不含这些关键词的命令（绝大多数）直接 return，零 grep fork。
  # 粗筛词是下方两个 grep pattern 全部命中词的超集 → 不漏判，命中粗筛才精确 grep。
  case "$cmd_stripped" in
    *full_page*|*headless*|*wait_for_*|*render_*) ;;
    *) return 0 ;;
  esac

  if echo "$cmd_stripped" | grep -qE 'full_page=True|headless=False|wait_for_(selector|function|load_state).*timeout=[0-9]{5,}'; then
    risky_reason="长页面截图/长超时等待/非 headless 浏览"
  elif echo "$cmd_stripped" | grep -qE 'python3.*render_.*\.py'; then
    risky_reason="大文件渲染脚本"
  fi

  [ -z "$risky_reason" ] && return 0

  echo "" >&2
  echo "⚠️  [risky-op] 高风险 Bash 操作前建议 checkpoint" >&2
  echo "   触发原因: $risky_reason" >&2
  echo "   → 先 Write .claude/session-state.md 保存当前进度" >&2
  echo "   → 理由: Playwright / 大文件渲染一旦 tool output 超 50K 或 API 挂住，无 compact 触发，状态会丢" >&2
  echo "" >&2
  log_event hook risky-op warn "$risky_reason"
  return 0
}

# ── Guard 2: git 危险操作阻断（原 pre-git-safety.sh）──────────────────────
guard_git_safety() {
  local cmd="$1"
  local cmd_stripped="$2"

  [ "${SKIP_GIT_SAFETY_GATE:-0}" = "1" ] && return 0
  [[ "$cmd" == *SKIP_GIT_SAFETY_GATE=1* ]] && return 0

  # case 粗筛短路：非 git 命令（绝大多数）不可能命中下方 git pattern，直接 return 省逐段 grep。
  case "$cmd_stripped" in
    *git*) ;;
    *) return 0 ;;
  esac

  # 逐段判（按 ; && || | 切）：整行 grep 会让三条件跨命令拼凑假阳
  # （`git push --force origin dev && git checkout main` 误判 force-push-main），
  # 也让 A 漏判无 --force 的 +refspec 强推。逐段后每段是单条命令，判断精确。
  local seg
  while IFS= read -r seg || [ -n "$seg" ]; do
    case "$seg" in *git*) ;; *) continue ;; esac

    # A: git push force 到 main/master（--force/-f + 目标 main/master，或 +refspec 隐式强推）
    # 子命令前允许夹全局选项 token（-C <path> / -c k=v / --git-dir=… 等），否则 git -C x push 全绕过
    if echo "$seg" | grep -qE '(^|[[:space:]])git([[:space:]]+[^[:space:]]+)*[[:space:]]+push([[:space:]]|$)'; then
      local hit=no
      if echo "$seg" | grep -qE '(^|[[:space:]])(--force|-f)([[:space:]]|$)' \
         && echo "$seg" | grep -qE '(^|[[:space:]:/])(main|master)([[:space:]]|$)'; then
        hit=yes
      fi
      # +refspec 强推（无 --force 也覆盖历史）：+main / +HEAD:main / +main:refs/heads/main / +refs/heads/main:refs/heads/main
      # 路径段前缀（refs/heads/ 等）逐段吞掉；右边界不含 - ，+feature/main-fix 这类 feature 分支不误伤
      if echo "$seg" | grep -qE '(^|[[:space:]])\+([^[:space:]:/]*[:/])*(main|master)([[:space:]:/]|$)'; then
        hit=yes
      fi
      if [ "$hit" = yes ]; then
        echo "" >&2
        echo "🚫 [git-safety-gate] force push 会覆盖 main / master 上游历史" >&2
        echo "   $cmd" >&2
        echo "   （+main / +HEAD:main 这类 +refspec 不带 --force 也是强推，同样拦）" >&2
        echo "   → 改用 --force-with-lease，或推 feature 分支开 PR" >&2
        echo "   → 真要覆盖远端（清私有镜像等）→ SKIP_GIT_SAFETY_GATE=1 $cmd" >&2
        log_event gate git-safety block "force-push-main: ${cmd:0:120}"
        exit 2
      fi
    fi

    # B: git commit --amend（子命令前允许夹全局选项 token，与规则 A 同因）
    if echo "$seg" | grep -qE '(^|[[:space:]])git([[:space:]]+[^[:space:]]+)*[[:space:]]+commit[[:space:]].*--amend([[:space:]]|$)'; then
      echo "" >&2
      echo "🚫 [git-safety-gate] git commit --amend 改写上一条 commit，易丢工作" >&2
      echo "   $cmd" >&2
      echo "   理由：amend 改写 last commit，pre-commit hook 失败 / 已 push 时会丢提交" >&2
      echo "   → 直接 git commit 建新提交" >&2
      echo "   → 真要修上一条且未 push → SKIP_GIT_SAFETY_GATE=1 $cmd" >&2
      log_event gate git-safety block "amend: ${cmd:0:120}"
      exit 2
    fi

    # C: git reset --hard（子命令前允许夹全局选项 token，与规则 A 同因）
    if echo "$seg" | grep -qE '(^|[[:space:]])git([[:space:]]+[^[:space:]]+)*[[:space:]]+reset[[:space:]].*--hard([[:space:]]|$)'; then
      echo "" >&2
      echo "🚫 [git-safety-gate] git reset --hard 会丢未提交改动" >&2
      echo "   $cmd" >&2
      echo "   → 先 git stash 存起来（或 git status 确认没有要保留的），再 reset" >&2
      echo "   → 真要丢弃工作区改动 → SKIP_GIT_SAFETY_GATE=1 $cmd" >&2
      log_event gate git-safety block "reset-hard: ${cmd:0:120}"
      exit 2
    fi
  done <<EOF
$(split_command_segments "$cmd_stripped")
EOF

  return 0
}

# ── Guard 3: prototype 范式门（原 pre-prototype-paradigm-gate.sh）──────────
guard_prototype_paradigm() {
  local cmd="$1"
  local cmd_stripped="$2"

  # SKIP 双通道（与 git-safety 同范式手写，不用 check_skip_env——它会 exit 0 放行整条 dispatcher 链）
  [ "${SKIP_PROTOTYPE_PARADIGM_GATE:-0}" = "1" ] && return 0
  [[ "$cmd" == *SKIP_PROTOTYPE_PARADIGM_GATE=1* ]] && return 0

  # case 粗筛短路：不含 build_proto 字样的命令直接 return，省下方 grep + 项目名抽取。
  case "$cmd_stripped" in
    *build_proto*) ;;
    *) return 0 ;;
  esac

  # 触发：build 脚本出现在命令位才算调用——逐段取首 token（剥 ENV= 前缀与 python3/env 包装），
  # basename 匹配 build_proto* 才拦；ruff / grep / diff 命令把它当文件名参数提及不拦
  local seg t first hit_call=0
  while IFS= read -r seg || [ -n "$seg" ]; do
    first=""
    for t in $seg; do
      case "$t" in
        [A-Za-z_]*=*) continue ;;
        python3|python|env) continue ;;
        *) first="$t"; break ;;
      esac
    done
    [ -n "$first" ] || continue
    case "${first##*/}" in
      build_proto_v*.py|build_proto_skeleton.py|build_proto_skeleton) hit_call=1; break ;;
    esac
  done <<EOF
$(split_command_segments "$cmd_stripped")
EOF
  [ "$hit_call" = "1" ] || return 0

  # 抽项目名：① 命令里的 projects/ 路径（两层优先回退一层）② -p 参数（空格式 / 连写式，
  # 与 gen_prd_skeleton -p / check_paradigm 位置参数同语义：相对 projects/ 的路径片段）
  local project
  project=$(echo "$cmd" | grep -oE 'projects/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+' | head -1 | sed 's|projects/||')
  if [ -z "$project" ]; then
    project=$(echo "$cmd" | grep -oE 'projects/[a-zA-Z0-9_-]+' | head -1 | sed 's|projects/||')
  fi
  if [ -z "$project" ]; then
    project=$(echo "$cmd" | grep -oE '(^|[[:space:]])-p[[:space:]]+[a-zA-Z0-9_][a-zA-Z0-9_/-]+' | awk '{print $NF}')
  fi
  if [ -z "$project" ]; then
    project=$(echo "$cmd" | grep -oE '(^|[[:space:]])-p[a-zA-Z0-9_][a-zA-Z0-9_/-]*' | sed -E 's/(^|[[:space:]])-p//' | head -1)
  fi

  # 尾段归一化：路径式调用常抽到 projects/{项目}/scripts 这类带非项目尾段的值
  # （livestream/scripts → livestream）。显式剥已知非根尾段——判「像项目根」不可靠：
  # livestream 的 scripts/inputs/ 恰好存在，会把 livestream/scripts 误当项目根。
  # 剥空（如 projects/scripts/...）走 no-project warn，与既有 fail-open 语义一致。
  case "${project##*/}" in
    scripts|inputs|deliverables|assets|references) project="${project%/*}" ;;
  esac

  if [ -z "$project" ]; then
    echo "⚠️  pre-prototype-paradigm-gate: 命中 build_proto_skeleton 但未识别项目名，跳过范式门检测（请确认命令含 projects/{项目} 路径或 -p {项目} 参数）" >&2
    log_event gate prototype-paradigm-gate warn "no-project: ${cmd:0:80}"
    return 0
  fi

  local root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  local proj_dir="$root/projects/$project"
  local anchors="$proj_dir/inputs/scene-anchors.md"
  local session="$root/.claude/session-state.md"

  # 跳过条件：anchors 含「范式」 / session 含「范式:」 / deliverables 已有 proto-*.html
  local has_paradigm=0
  if [ -f "$anchors" ] && grep -q "范式" "$anchors" 2>/dev/null; then
    has_paradigm=1
  fi
  if [ -f "$session" ] && grep -qE "范式[:：]" "$session" 2>/dev/null; then
    has_paradigm=1
  fi
  if ls "$proj_dir/deliverables/proto-"*.html >/dev/null 2>&1; then
    has_paradigm=1
  fi

  if [ "$has_paradigm" -eq 0 ]; then
    printf '═══ pre-prototype-paradigm-gate fail ═══\n\n' >&2
    printf '❌ 检测到 build_proto_skeleton / build_proto_v* 调用，但项目 [%s] 未跑 Step 0 范式门\n\n' "$project" >&2
    printf '→ 先跑：python3 .claude/skills/prototype/scripts/check_paradigm.py %s\n' "$project" >&2
    printf '→ 推断结果记到 projects/%s/inputs/scene-anchors.md（含「范式: xxx」一行）\n' "$project" >&2
    printf '→ 或更新 .claude/session-state.md 含「范式: xxx」\n' >&2
    printf '→ 用户口头确认范式后才允许跑 build_proto_skeleton\n' >&2
    printf '→ 真不适用（临时演示 / 已口头确认但未落盘）→ SKIP_PROTOTYPE_PARADIGM_GATE=1 %s\n\n' "$cmd" >&2
    printf '（v1 翻车根因：跳过范式门默认 view-page，推倒重来。本 hook 防同款）\n' >&2
    log_event gate prototype-paradigm-gate block "$project"
    exit 2
  fi

  log_event gate prototype-paradigm-gate triggered "$project"
  return 0
}
