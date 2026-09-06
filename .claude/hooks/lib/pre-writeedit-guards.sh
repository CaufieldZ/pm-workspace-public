#!/usr/bin/env bash
# 共享：PreToolUse Write|Edit 4 个 guard 子函数（原 4 个独立 pre-*.sh 合并）
#
# 被 pre-writeedit-guard.sh source；前提：已 source log.sh + input.sh + guards.sh
#                                        且已 INPUT=$(cat); hook_parse_all
#
# 约定（Pre 侧 = 硬 block，拦住就停）：
# - 每个 pg_* 子函数：路径 / 工具不匹配 → return 0（放行，继续下一 guard）
# - 命中违规 → 写三段式 + log_event block + return 2（dispatcher 见 2 立即 exit 2）
# - SKIP env 命中 → 子函数内 return 0
#
# gate 名 / SKIP env 与原 4 hook 逐字一致。
# scripts-first 仅 Write 触发（非 Edit）；其余 Write|Edit 皆触发。
set +e

# 从 $INPUT 抽 content / new_string（hook_parse_all 不含，单独取）
_pg_content() {
  echo "$INPUT" | python3 -c "import sys,json; t=json.load(sys.stdin).get('tool_input',{}); print(t.get('content','') or t.get('new_string',''))" 2>/dev/null
}

# ── 1. scripts-first（首次大 HTML Write 拦截，仅 Write）──────────────
pg_scripts_first() {
  [ "$HOOK_TOOL_NAME" != "Write" ] && return 0
  local FILE_PATH="$HOOK_FILE_PATH"
  if _pg_skip_block "scripts-first" "SKIP_SCRIPTS_FIRST_GATE" "$FILE_PATH"; then return 0; fi
  echo "$FILE_PATH" | grep -qE 'projects/[^/]+/.*\.html$' || return 0
  echo "$FILE_PATH" | grep -qE '/(archive|inputs|screenshots|scripts|sop-src)/' && return 0

  local CONTENT LINE_COUNT
  CONTENT=$(_pg_content)
  LINE_COUNT=$(echo "$CONTENT" | wc -l | tr -d ' ')
  [ "$LINE_COUNT" -gt 200 ] || return 0

  local PROJECT_DIR_X
  PROJECT_DIR_X=$(echo "$FILE_PATH" | sed -nE 's#(.*projects/[^/]+/[^/]+)/(deliverables|scripts|inputs|screenshots).*#\1#p')
  [ -z "$PROJECT_DIR_X" ] && PROJECT_DIR_X=$(echo "$FILE_PATH" | sed -nE 's#(.*projects/[^/]+)/(deliverables|scripts|inputs|screenshots).*#\1#p')
  [ -z "$PROJECT_DIR_X" ] && PROJECT_DIR_X=$(echo "$FILE_PATH" | sed -E 's#(.*projects/[^/]+)/.*#\1#')

  if [ -d "$PROJECT_DIR_X/scripts" ] && \
     find "$PROJECT_DIR_X/scripts" -maxdepth 2 -type f \
       \( -name 'gen_*.py' -o -name 'gen_*.js' \
          -o -name 'fill_*.py' -o -name 'fill_*.js' \
          -o -name 'patch_*.py' -o -name 'patch_*.js' \
          -o -name 'build_*.py' -o -name 'build_*.js' \
          -o -name 'build.py' -o -name 'build.js' \) 2>/dev/null | grep -q .; then
    return 0
  fi

  echo "" >&2
  echo "🚫 [scripts-first] 首次生成 > 200 行 HTML 禁直接 Write（无可复用脚本则强制走 gen 模式）" >&2
  echo "   文件: ${FILE_PATH}（拟写 ${LINE_COUNT} 行）" >&2
  echo "" >&2
  echo "   → 修法 1: 在 ${PROJECT_DIR_X}/scripts/ 创建 gen_*.py（可参考 .claude/skills/prd/scripts/gen_prd_skeleton.py 模板）" >&2
  echo "   → 修法 2: 用 python3 ${PROJECT_DIR_X}/scripts/gen_*.py 生成 HTML（产物文件不再手 Write）" >&2
  echo "   → 阈值依据: scripts/lib/thresholds.yaml HTML_DIRECT_WRITE_MAX（200 行）" >&2
  echo "   → 真不适用 → 检查文件名是否应改后缀避免误判（hook 仅对 *.html 触发）；或 export SKIP_SCRIPTS_FIRST_GATE=1（仅一次性静态 HTML、确无脚本生成价值时）" >&2
  echo "" >&2
  log_event hook scripts-first block "large first-gen html: $FILE_PATH $LINE_COUNT lines"
  return 2
}

# ── 2. deliverable-source-gate（已脚本化 HTML 禁直 Write/Edit）────────
pg_deliverable_source() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] && return 0

  if _pg_skip_block "deliverable-source-gate" "SKIP_DELIVERABLE_GATE" "$FILE_PATH"; then return 0; fi

  case "$FILE_PATH" in
    *projects/*/*/deliverables/*.html|*projects/*/deliverables/*.html) ;;
    *) return 0 ;;
  esac
  is_excluded_path "$FILE_PATH" && return 0

  local PROJECT_PATH
  PROJECT_PATH=$(echo "$FILE_PATH" | sed -nE 's|.*projects/([^/]+/[^/]+)/deliverables/.*|\1|p')
  [ -z "$PROJECT_PATH" ] && PROJECT_PATH=$(echo "$FILE_PATH" | sed -nE 's|.*projects/([^/]+)/deliverables/.*|\1|p')
  [ -z "$PROJECT_PATH" ] && return 0

  local SCRIPTS_DIR="$PROJECT_DIR/projects/$PROJECT_PATH/scripts"
  [ ! -d "$SCRIPTS_DIR" ] && return 0

  local EXISTING SRC_BUILDS TSRC_BUILDS
  EXISTING=$(find "$SCRIPTS_DIR" -maxdepth 1 -type f \
    \( -name 'gen_*.py' -o -name 'gen_*.js' \
       -o -name 'fill_*.py' -o -name 'fill_*.js' \
       -o -name 'patch_*.py' -o -name 'patch_*.js' \
       -o -name 'build_*.py' -o -name 'build_*.js' \) 2>/dev/null)

  if [ -d "$SCRIPTS_DIR/src" ]; then
    SRC_BUILDS=$(find "$SCRIPTS_DIR/src" -maxdepth 1 -type f \
      \( -name 'build_*.py' -o -name 'build.py' -o -name 'build_*.js' -o -name 'build.js' \) 2>/dev/null)
    EXISTING="${EXISTING}${SRC_BUILDS:+$'\n'}${SRC_BUILDS}"
  fi

  local tsrc
  for tsrc in "$SCRIPTS_DIR"/*-src; do
    [ -d "$tsrc" ] || continue
    TSRC_BUILDS=$(find "$tsrc" -maxdepth 1 -type f \
      \( -name 'build_*.py' -o -name 'build.py' -o -name 'build_*.js' -o -name 'build.js' \
         -o -name 'gen_*.py' -o -name 'gen_*.js' \) 2>/dev/null)
    EXISTING="${EXISTING}${TSRC_BUILDS:+$'\n'}${TSRC_BUILDS}"
  done

  EXISTING=$(echo "$EXISTING" | sed '/^$/d' | head -5)
  [ -z "$EXISTING" ] && return 0

  local FILE_BASE MATCH_SCRIPT="" script base parent TYPE
  FILE_BASE=$(basename "$FILE_PATH")
  while IFS= read -r script; do
    [ -z "$script" ] && continue
    base=$(basename "$script")
    parent=$(basename "$(dirname "$script")")
    TYPE=$(echo "$base" | sed -nE 's/^(gen|fill|patch|build)_([a-zA-Z0-9]+)_.*/\2/p')
    if [ -z "$TYPE" ]; then
      case "$parent" in
        *-src) TYPE="${parent%-src}" ;;
      esac
    fi
    if [ -z "$TYPE" ] && [ "$parent" = "src" ] && { [ "$base" = "build.py" ] || [ "$base" = "build.js" ]; }; then
      TYPE="__any__"
    fi
    [ -z "$TYPE" ] && continue
    if [ "$TYPE" = "__any__" ]; then
      MATCH_SCRIPT="$script"; break
    fi
    case "$FILE_BASE" in
      *"-${TYPE}-"*|*"_${TYPE}_"*|"${TYPE}-"*|"${TYPE}_"*)
        MATCH_SCRIPT="$script"; break ;;
    esac
  done <<< "$EXISTING"

  [ -z "$MATCH_SCRIPT" ] && return 0

  local MATCH_REL="${MATCH_SCRIPT#${PROJECT_DIR}/}" RUNNER="python3"
  case "$MATCH_SCRIPT" in *.js) RUNNER="node" ;; esac
  echo "" >&2
  echo "🚫 [deliverable-source-gate] 禁止直接 Write/Edit 已脚本化的 HTML 产出物" >&2
  echo "   文件: $FILE_BASE" >&2
  echo "   生成脚本: $MATCH_REL" >&2
  echo "" >&2
  echo "   → 改源：编辑 $MATCH_REL（或其 src/scenes、src/pages 数据），别改 HTML" >&2
  echo "   → 重生：$RUNNER $MATCH_REL" >&2
  echo "   → 真要小幅文案修改且不重生：export SKIP_DELIVERABLE_GATE=1 后重试" >&2
  echo "" >&2
  log_event gate deliverable-source-gate block "$FILE_BASE"
  return 2
}

# ── 3. deliverable-img-path-gate（PRD md 图片路径约束）───────────────
pg_deliverable_img_path() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] && return 0

  if _pg_skip_block "deliverable-img-path-gate" "SKIP_IMG_PATH_GATE" "$FILE_PATH"; then return 0; fi

  case "$FILE_PATH" in
    *projects/*/deliverables/prd-*.md|*projects/*/*/deliverables/prd-*.md) ;;
    *projects/*/deliverables/*/prd-*.md) ;;
    *) return 0 ;;
  esac
  is_excluded_path "$FILE_PATH" && return 0

  local CONTENT
  CONTENT=$(_pg_content)
  [ -z "$CONTENT" ] && return 0

  local PATHS PARSE_ERR
  PARSE_ERR=$(mktemp)
  PATHS=$(echo "$CONTENT" | python3 -c "
import sys, re
text = sys.stdin.read()
md_paths = re.findall(r'!\[[^\]]*\]\(([^)\s]+)', text)
html_paths = re.findall(r'<img[^>]+src=[\"\\'](.*?)[\"\\']', text)
for p in md_paths + html_paths:
    print(p)
" 2>"$PARSE_ERR")
  # 解析出错 ≠ 没有图片：fail-loud（warn + 可见 log）而非静默放行，避免漏掉真违规
  if [ -s "$PARSE_ERR" ]; then
    echo "⚠️  [deliverable-img-path-gate] 图片路径解析异常，跳过本次检测（请人工核对 PRD 图片引用路径）：" >&2
    head -3 "$PARSE_ERR" >&2
    log_event gate deliverable-img-path-gate warn "parse-error: $(basename "$FILE_PATH")"
    rm -f "$PARSE_ERR"
    return 0
  fi
  rm -f "$PARSE_ERR"
  [ -z "$PATHS" ] && return 0

  local VIOLATIONS="" p
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    case "$p" in
      http://*|https://*) continue ;;
    esac
    case "$p" in
      assets/*|./assets/*|../assets/*) continue ;;
    esac
    case "$p" in
      ../inputs/competitors/*) continue ;;
    esac
    VIOLATIONS="$VIOLATIONS\n   ❌ $p"
  done <<< "$PATHS"
  [ -z "$VIOLATIONS" ] && return 0

  echo "" >&2
  echo "🚫 [deliverable-img-path-gate] PRD md 图片引用路径违规" >&2
  echo "   文件: $(basename "$FILE_PATH")" >&2
  echo -e "$VIOLATIONS" >&2
  echo "" >&2
  echo "   规则: PRD 截图应放 deliverables/assets/prd/，md 引用形如 assets/prd/xxx.png" >&2
  echo "         竞品对比可引用 ../inputs/competitors/{平台}/xxx.png" >&2
  echo "         禁止从 inputs/raw/ inputs/figma/ screenshots/ 或绝对路径引用" >&2
  echo "" >&2
  echo "   → 把图迁到 deliverables/assets/prd/ 后改路径" >&2
  echo "   → 真要绕过: export SKIP_IMG_PATH_GATE=1 后重试" >&2
  echo "" >&2
  log_event gate deliverable-img-path-gate block "$(basename "$FILE_PATH")"
  return 2
}

# ── 4. skill-load-gate / required-read-gate（改关键文件前必读 guide）──
pg_skill_load() {
  if [ "${SKIP_SKILL_LOAD_GATE:-0}" = "1" ] || [ "${SKIP_REQUIRED_READ_GATE:-0}" = "1" ]; then
    command -v _log_skip_gate >/dev/null && _log_skip_gate skill-load-gate "env"
    return 0
  fi

  local FILE_PATH="$HOOK_FILE_PATH"
  local TRANSCRIPT_PATH="$HOOK_TRANSCRIPT"
  [ -z "$FILE_PATH" ] && return 0

  local BASENAME GUIDE="" GATE="" GUIDE2="" GUIDE3="" GUIDE4="" SKILL=""
  BASENAME=$(basename "$FILE_PATH")

  case "$BASENAME" in
    prd-*.md)                                    SKILL=prd ;;
    scene-list*.md|scene-list*.html)             SKILL=scene-list ;;
    imap-*.html|interaction-*.html|imap-*-skeleton.html) SKILL=interaction-map ;;
    proto-*.html|prototype-*.html)               SKILL=prototype ;;
    arch-*.html|architecture-*.html)             SKILL=architecture-diagrams ;;
    ppt-*.html)                                  SKILL=ppt ;;
  esac
  if [ -z "$SKILL" ]; then
    case "$FILE_PATH" in
      */prd-*-scenes/*.md) SKILL=prd ;;
    esac
  fi
  if [ -n "$SKILL" ]; then
    GUIDE=".claude/skills/$SKILL/SKILL.md"
    GATE="skill-load-gate"
    case "$SKILL" in
      scene-list|interaction-map|prototype|prd)
        GUIDE2=".claude/runbooks/info-ownership.md" ;;
    esac
    # prd 追加：章节规则速查（写 PRD 前必读，chapter-rules 561 行精华 ~100 行，全量按需）+ 场景模板速查
    if [ "$SKILL" = "prd" ]; then
      GUIDE3=".claude/skills/prd/references/prd-chapter-rules-quickref.md"
      GUIDE4=".claude/skills/prd/references/prd-scene-template-quickref.md"
    fi
  fi

  if [ -z "$GUIDE" ]; then
    local SKILL_FROM_SCRIPT
    SKILL_FROM_SCRIPT=$(echo "$FILE_PATH" | sed -nE 's|.*/\.claude/skills/([^/]+)/scripts/.+\.py$|\1|p')
    if [ -n "$SKILL_FROM_SCRIPT" ]; then
      GUIDE=".claude/skills/$SKILL_FROM_SCRIPT/SKILL.md"; GATE="required-read-gate"
    fi
  fi

  if [ -z "$GUIDE" ]; then
    case "$FILE_PATH" in
      */.claude/hooks/*.sh)
        GUIDE=".claude/hooks/HOOK_WRITING-quickref.md"; GATE="required-read-gate" ;;
      # 仅工区根 scripts/ 走 SCRIPTS_WRITING.md；projects/*/scripts/ 是产物生成器，规则在对应 SKILL，不强制读
      "$PROJECT_DIR"/scripts/*.py|"$PROJECT_DIR"/scripts/*.sh|"$PROJECT_DIR"/scripts/lib/*.py)
        GUIDE="scripts/SCRIPTS_WRITING.md"; GATE="required-read-gate" ;;
    esac
  fi

  # hub 对外抽象产物 → 必读 L1 入口 + L3 过审 + 按产物类型必读对应 L2 公司编写规范
  # L2 机械强制（不只指路）：aihub_tool→MCP / system-prompt→Agent+Prompt / agent-model→Agent
  if [ -z "$GUIDE" ]; then
    case "$BASENAME" in
      aihub_tool.py)
        case "$FILE_PATH" in */hub/*)
          GUIDE=".claude/runbooks/ai-platform-specs.md"; GATE="required-read-gate"
          GUIDE2="hub/AUTHORING-RULES.md"
          GUIDE3="hub/AI中台-规范及帮助文档/AI中台-MCP编写规范.md" ;;
        esac ;;
      system-prompt.md)
        case "$FILE_PATH" in */hub/*)
          GUIDE=".claude/runbooks/ai-platform-specs.md"; GATE="required-read-gate"
          GUIDE2="hub/AUTHORING-RULES.md"
          GUIDE3="hub/AI中台-规范及帮助文档/AI 中台-Agent 创建规范.md"
          GUIDE4="hub/AI中台-规范及帮助文档/AI中台-Prompt编写规范.md" ;;
        esac ;;
      agent-model.json)
        case "$FILE_PATH" in */hub/*)
          GUIDE=".claude/runbooks/ai-platform-specs.md"; GATE="required-read-gate"
          GUIDE2="hub/AUTHORING-RULES.md"
          GUIDE3="hub/AI中台-规范及帮助文档/AI 中台-Agent 创建规范.md" ;;
        esac ;;
    esac
  fi

  [ -z "$GUIDE" ] && return 0

  _pg_check_read() {
    local guide="$1"
    [ -z "$guide" ] && return 0
    # ① 当前 transcript 读过 → 命中（最强信号，本会话内）
    if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
      # 全正则转义（不只 `.`）：guide 路径含 [ ] + ? 等字符时 grep -E 会错配。
      # 用 re.escape 而非 sed：BRE 字符类转义 [ / ] / \ 组合易错；本路径低频（改产物文件才跑），30ms 可接受。
      local esc
      esc=$(printf '%s' "$guide" | python3 -c 'import re, sys; print(re.escape(sys.stdin.read().strip()))')
      grep -qE "\"file_path\"[[:space:]]*:[[:space:]]*\"[^\"]*${esc}\"" "$TRANSCRIPT_PATH" 2>/dev/null && return 0
    fi
    # ② 跨 session fallback：usage.jsonl 近 6h 有这份 guide 的 guide-read 记录 → 命中。
    # 解决 compact / 换 session 后 transcript 清零导致的失忆误报；隔时段（>6h）仍要求重读。
    # 测试态（CLAUDE_HOOK_TEST=1）跳过 fallback，保持回归只验 transcript 语义、不读真 usage.jsonl。
    [ -n "$CLAUDE_HOOK_TEST" ] && return 1
    _pg_guide_read_recent "$guide" 21600 && return 0
    return 1
  }

  # usage.jsonl 倒序扫 guide-read 事件：detail 以 $guide 结尾且 ts 在 window_sec 内 → return 0
  _pg_guide_read_recent() {
    local guide="$1" window="$2"
    local logf="$PROJECT_DIR/.claude/logs/usage.jsonl"
    [ -f "$logf" ] || return 1
    GUIDE="$guide" WINDOW="$window" python3 - "$logf" <<'PY' 2>/dev/null
import sys, os, json
from datetime import datetime, timedelta
guide, window = os.environ["GUIDE"], int(os.environ["WINDOW"])
cutoff = datetime.now().astimezone() - timedelta(seconds=window)
hit = False
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        lines = f.readlines()
except Exception:
    sys.exit(1)
for ln in reversed(lines):
    try:
        d = json.loads(ln)
    except Exception:
        continue
    if d.get("name") != "guide-read":
        continue
    det = d.get("detail", "")
    if not (det == guide or det.endswith(guide) or det.endswith("/" + guide)):
        continue
    try:
        ts = datetime.fromisoformat(d["ts"])
    except Exception:
        continue
    if ts >= cutoff:
        hit = True
    break
sys.exit(0 if hit else 1)
PY
  }

  local MISSING=()
  _pg_check_read "$GUIDE" || MISSING+=("$GUIDE")
  local _g
  for _g in "$GUIDE2" "$GUIDE3" "$GUIDE4"; do
    [ -n "$_g" ] && { _pg_check_read "$_g" || MISSING+=("$_g"); }
  done
  [ "${#MISSING[@]}" -eq 0 ] && return 0

  local REL="${FILE_PATH#${PROJECT_DIR}/}" HINT_LIGHT="" g
  case "$FILE_PATH" in
    */.claude/skills/*/scripts/*.py|*/.claude/skills/*/scripts/*.sh)
      if [[ "$GUIDE" == *SKILL.md ]] && [ -z "$GUIDE2" ]; then
        HINT_LIGHT="   → 修法（轻量·改 scripts/*）: Read $GUIDE limit=80（§1 触发与定位 + §2 改脚本前 30 秒 即够·见 skill-conventions.md）"
      fi ;;
    */projects/*/prd-*.md|*/projects/*/*/prd-*.md|*/projects/*/prd-*-baseline.md|*/projects/*/prd-*-scenes/*.md)
      # 只在「缺的就是 GUIDE 本身」时给轻量提示；还缺别的文件就落到下面的显式清单分支。
      # 否则提示只教读 GUIDE、判定却要求读全部缺失项，照提示做仍被拦 → 反复撞墙。
      if [ "${#MISSING[@]}" -eq 1 ] && [ "${MISSING[0]}" = "$GUIDE" ]; then
        HINT_LIGHT="   → 修法（轻量·改 prd 产物）: Read $GUIDE limit=120（前两节 §触发与定位 + §硬规则 即够）"
      fi ;;
  esac

  echo "" >&2
  echo "🚫 [$GATE] 改 $REL 前必读以下文件" >&2
  echo "   文件: $REL" >&2
  for g in "${MISSING[@]}"; do
    echo "   缺失: $g" >&2
  done
  echo "" >&2
  if [ -n "$HINT_LIGHT" ]; then
    echo "$HINT_LIGHT" >&2
    echo "   → 修法（完整·改产出物 / 改业务规则）: Read $GUIDE 全文" >&2
  else
    for g in "${MISSING[@]}"; do
      echo "   → Read $g" >&2
    done
    echo "   → 全部读完按规则自检后，再 $HOOK_TOOL_NAME 此文件" >&2
  fi
  echo "   → 事前 10 行 guide > 事后 hook 抓 N 处 fail 来回返工" >&2
  echo "   → 真不适用 → outer shell \`export SKIP_SKILL_LOAD_GATE=1\` 或 SKIP_REQUIRED_READ_GATE=1（仅 PM 手动开；Claude inline 旁路无效）" >&2
  command -v log_event >/dev/null && log_event hook "$GATE" block "$REL"
  return 2
}

# 共享：SKIP env 命中 → _log_skip_gate + return 0；不命中 → return 1
# （Write/Edit 不经 Bash 管道，inline 旁路无效，只判 env）
_pg_skip_block() {
  local gate="$1" var="$2" detail="${3:-}" val
  eval "val=\${${var}:-0}"
  if [ "$val" = "1" ]; then
    _log_skip_gate "$gate" "env  ${detail:0:120}"
    return 0
  fi
  return 1
}
