#!/usr/bin/env bash
# 共享：PostToolUse Write|Edit 全部 checker 子函数（pc_*，调用序列见 post-writeedit-dispatch.sh）
#
# 被 post-writeedit-dispatch.sh source；前提：已 source log.sh + input.sh + guards.sh + runner.sh + dedup.sh
#                                          且已 INPUT=$(cat); hook_parse_all; require_write_or_edit
#
# 约定：
# - 每个 pc_* 子函数无参数，读全局 $HOOK_FILE_PATH / $INPUT / $PROJECT_DIR
# - block 类：写三段式到 >&2 + log_event block + 置 _PC_BLOCKED=1 + return 0（不 exit，让后续 checker 继续跑）
# - warn 类：写 >&2 + log_event warn + note_add 汇总一句 → return 0
# - skip / 路径不匹配 / 文件缺失：return 0
# - dispatcher 末尾按 _PC_BLOCKED 统一 exit 2 / 0
#
# ⚠️ warn 类为什么必须额外调 note_add：PostToolUse 的 hook 在 exit 0 时，写到 stderr 的内容
#    只进 transcript 里的 hook_success 记录（供界面展示），**不进模型 context**——模型看不到。
#    要送达模型只有两条路：① exit 2（但 warn 类本来就不该阻断）② hookSpecificOutput.additionalContext。
#    dispatcher 末尾把累加内容作为 additionalContext 输出；block 时走 exit 2，不再重复注入。
#    （该通道事实经官方文档 + 本仓实弹核对确认：test-reminder-gate 响过、模型侧无感。）
#    新增 warn 类门时若只写 stderr 而不调 note_add，等于没提醒。
#
# checker 互不依赖（全只读检查同一文件），全跑安全，一次拿全违规优于半路截断
# gate 名 / SKIP env 与原 9 hook 逐字一致（dashboard 聚合键 + settings.json 单测入口契约）
set +e

_PC_BLOCKED=0

# 待送达模型的 warn 说明走 lib/notes.sh 的 note_add / note_emit —— 累加器与发射器单点实现，
# 4 个 hook 入口（两个 PostToolUse + 两个 PreToolUse）共用，不在各入口各抄一份。
# 前置：调用方须已 source lib/notes.sh（见该文件头对通道原因的说明）。

# skip-env 门：统一走 guards.sh 的 check_skip_env（默认 return 版；调用方 `&& return 0`）

# ── 1. cjk-punct（双分支 strict/warn）──────────────────────────────
pc_cjk_punct() {
  local CHECKER="$PROJECT_DIR/scripts/check_cjk_punct.py"
  [ ! -f "$CHECKER" ] && return 0
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] && return 0
  [ ! -f "$FILE_PATH" ] && return 0
  case "$FILE_PATH" in
    *.md|*.html) ;;
    *) return 0 ;;
  esac
  # 仅产物树内的 prose 文档：projects/ 产物+baseline+scene-list、examples/ 样例
  # 排除误报源——.claude 规则文档（YAML frontmatter 冒号 / 内部枚举符 ①②③）、根 CLAUDE.md、代码 docstring、plans
  case "$FILE_PATH" in
    */projects/*|*/examples/*) ;;
    *) return 0 ;;
  esac
  is_excluded_path "$FILE_PATH" && return 0
  # 导入源 / 参考资料非自产产物，原文标点照搬，不跑 strict CJK（与 bullet-density 排除对齐）
  case "$FILE_PATH" in
    */inputs/*|*/references/*) return 0 ;;
  esac

  local IS_DELIVERABLE=0
  if is_deliverable_path "$FILE_PATH" && ! is_excluded_path "$FILE_PATH"; then
    IS_DELIVERABLE=1
  fi

  local TMPOUT RC
  if [ "$IS_DELIVERABLE" -eq 1 ]; then
    TMPOUT=$(mktemp)
    # strict 通过即视为过关：建议级 pangu 空格不喷不记 —— 无人处理的软 warn 是告警疲劳源。
    # 改为静默自动补空格（中英/中数/单位间，autocorrect 思路，机器管空格人不感知）。
    # 全工区唯一「PostToolUse 改盘」的 hook，安全靠三条：① 仅 strict clean 后补（不碰待修脏文件）
    # ② 只改空格且幂等（不与后续编辑打架）③ best-effort 永不 block（失败吞、不动 _PC_BLOCKED）。
    # 脚本自身 fs 写入不经过 Write/Edit 工具，不触发二次 PostToolUse，无递归。
    # --strict-then-fix-spaces 把「判定 + 补空格」收进一个进程：原先连起两个 python3、
    # 同一文件读两遍。补空格阶段的异常在脚本内吞掉，退出码只反映 strict 判定（不改上面第 ③ 条）。
    if [ "${SKIP_CJK_SPACE_FIX:-0}" != "1" ]; then
      python3 "$CHECKER" "$FILE_PATH" --strict-then-fix-spaces > "$TMPOUT" 2>&1
    else
      python3 "$CHECKER" "$FILE_PATH" --strict > "$TMPOUT" 2>&1
    fi
    RC=$?
    if [ "$RC" -ne 0 ]; then
      head -20 "$TMPOUT" >&2
      echo "💡 自动修复：python3 scripts/check_cjk_punct.py --fix \"$FILE_PATH\"（--dry-run 预览不写盘）" >&2
      log_event hook cjk-punct block "$FILE_PATH"
      rm -f "$TMPOUT"
      _PC_BLOCKED=1
      return 0
    fi
    log_event hook cjk-punct clean "$FILE_PATH"
    rm -f "$TMPOUT"
  else
    local STDERR
    STDERR=$(python3 "$CHECKER" "$FILE_PATH" --strict 2>&1 >/dev/null)
    RC=$?
    [ -n "$STDERR" ] && echo "$STDERR" >&2
    if [ "$RC" -ne 0 ]; then
      echo "💡 自动修复：python3 scripts/check_cjk_punct.py --fix \"$FILE_PATH\"（--dry-run 预览不写盘）" >&2
      note_add "工区 cjk-punct 检查：${FILE_PATH#$PROJECT_DIR/} 含 CJK 旁半角标点。该文件不在产物树内故只提示不阻断；修：python3 scripts/check_cjk_punct.py --fix \"$FILE_PATH\"。"
      log_event hook cjk-punct warn "$FILE_PATH"
    else
      log_event hook cjk-punct clean "$FILE_PATH"
    fi
  fi
  return 0
}

# ── 2. plain-language（含 learned-rules 旁路）────────────────────────
# 合批形态（decisions/2026-09-23-pc-batch-mechanism）：本函数只做守卫 + 入队
# （_pc_enqueue，判定在单进程批量 runner 里跑原 argv）；判定结果由 _pcr_plain_language
# 在 dispatcher 的 _pc_flush 之后消费。判定代码 / 文案 / log_event 形态逐字节保持。
# 走 --added-only：living 文档存量违规多，全量扫会让每次编辑都被旧账拦下，门沦为噪音。
# 副作用——hits_words 埋点从此只统计新增行命中，词表死词分析的口径跟着变窄。
# learned rc=2 时原本会跳过 plain 运行——批量下 plain 可能已在批内跑过，report 段
# 以「learned 阻断即返回、丢弃 plain 结果」复刻同一可观测行为（plain 无 side effect，
# --json-out 落临时文件即弃）。
pc_plain_language() {
  local CHECKER="$PROJECT_DIR/scripts/check_plain_language.py"
  [ ! -f "$CHECKER" ] && return 0
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] && return 0
  [ ! -f "$FILE_PATH" ] && return 0
  case "$FILE_PATH" in
    *.md|*.html|*.drawio|*.mmd) ;;
    *) return 0 ;;
  esac
  _PC_PL_LEARNED_QUEUED=0
  _PC_PL_QUEUED=0
  _PC_PL_TMPJSON=""

  # learned-rules 旁路（在 deliverables/ 过滤前跑，scene-list / prd 也覆盖）
  local LEARNED_CHECKER="$PROJECT_DIR/scripts/check_learned_rules.py"
  if [ -f "$LEARNED_CHECKER" ] && [ "${SKIP_LEARNED_RULES_GATE:-0}" != "1" ]; then
    _pc_enqueue learned "$LEARNED_CHECKER" "$FILE_PATH"
    _PC_PL_LEARNED_QUEUED=1
  fi

  echo "$FILE_PATH" | grep -qE '/deliverables/' || return 0

  is_plain_language_exempt "$FILE_PATH" && return 0
  # PRD 由 prd-content-gate 按 PRD 自己的 profile 判（含量 / 锚点口径与本文档不同）
  case "$FILE_PATH" in
    */deliverables/prd-*.md|*/deliverables/prd-*-scenes/*.md) return 0 ;;
    */deliverables/*/prd-*.md|*/deliverables/*/prd-*-scenes/*.md) return 0 ;;
  esac

  check_skip_env "plain-language-gate" "SKIP_PLAIN_LANGUAGE_GATE" "${FILE_PATH:0:120}" && return 0

  _PC_PL_TMPJSON=$(mktemp)
  _pc_enqueue plain "$CHECKER" "$FILE_PATH" --strict --added-only --json-out "$_PC_PL_TMPJSON"
  _PC_PL_QUEUED=1
}

_pcr_plain_language() {
  local FILE_PATH="$HOOK_FILE_PATH"
  if [ "${_PC_PL_LEARNED_QUEUED:-0}" = "1" ]; then
    if [ "${_PC_RC_learned:-1}" = "2" ]; then
      cat "$_PC_ALL_learned" >&2
      log_event hook learned-rules-gate block "$FILE_PATH"
      rm -f "$_PC_ALL_learned" "$_PC_PL_TMPJSON"
      _PC_BLOCKED=1
      return 0
    fi
    [ -s "$_PC_ALL_learned" ] && cat "$_PC_ALL_learned" >&2
    rm -f "$_PC_ALL_learned"
  fi
  [ "${_PC_PL_QUEUED:-0}" = "1" ] || return 0

  local TMPOUT="$_PC_ALL_plain" TMPJSON="$_PC_PL_TMPJSON" RC WORDS
  RC="${_PC_RC_plain:-1}"
  # 命中词明细（词表防腐化埋点，telemetry terms 反查死词用）。
  # 默认 []（零命中也 emit，标记「这次扫了 + 有埋点」）—— analyze 分母只认带 hits_words
  # 字段的事件，埋点上线前的历史扫描无此字段自动排除，不被误算进死词分母。
  WORDS="[]"
  if [ -s "$TMPJSON" ]; then
    local _w
    _w=$(jq -rc '[.hits[].matched] | unique' "$TMPJSON" 2>/dev/null)
    [ -n "$_w" ] && WORDS="$_w"
  fi
  if [ "$RC" -eq 2 ]; then
    echo "" >&2
    echo "🚫 [plain-language-gate] 产物讲人话违规（内部锚点 / [待补充] / FIXME / 决策号 / 翻译腔不应入对外产物）" >&2
    echo "   文件: $(echo "$FILE_PATH" | sed "s#$PROJECT_DIR/##")" >&2
    cat "$TMPOUT" >&2
    echo "" >&2
    echo "   → 修法 1: 按上方行号定位，把内部锚点 / 决策号 / 待补充 改成业务白话（例：A-1 → 「下注弹层」，决策 7 → 删除引用）" >&2
    echo "   → 修法 2: 改源后重 build（若是脚本化产物 prd/imap/proto/arch/ppt）" >&2
    echo "   → 真不适用 → SKIP_PLAIN_LANGUAGE_GATE=1（仅内部审计 / fix-plan 文档，对外产物禁用）" >&2
    echo "" >&2
    log_event hook plain-language-gate block "$FILE_PATH" "" "" "$WORDS"
    rm -f "$TMPOUT" "$TMPJSON"
    _PC_BLOCKED=1
    return 0
  fi
  rm -f "$TMPOUT" "$TMPJSON"
  log_event hook plain-language-gate clean "$FILE_PATH" "" "" "$WORDS"
  return 0
}

# ── 3. context-static-lint（真相源静态章四不，warn 永不 block）──────────
# gate 名 context-static-lint + SKIP_CONTEXT_LINT_GATE 为 dashboard / 白名单稳定契约，保留不改。
pc_static_chapter() {
  [ "${SKIP_CONTEXT_LINT_GATE:-0}" = "1" ] && return 0  # 对齐其余 gate：只有 =1 才跳（=0 不该关）
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] && return 0
  [ ! -f "$FILE_PATH" ] && return 0
  case "$FILE_PATH" in
    */projects/*/prd-*-baseline.md) ;;
    */projects/*/scene-list.md) ;;
    *) return 0 ;;
  esac
  is_excluded_path "$FILE_PATH" && return 0
  local CHECKER="$PROJECT_DIR/scripts/check_static_chapter.py"
  [ ! -f "$CHECKER" ] && return 0

  local TMPJSON WORDS STDERR
  TMPJSON=$(mktemp)
  STDERR=$(python3 "$CHECKER" "$FILE_PATH" --json-out "$TMPJSON" 2>&1 >/dev/null)
  # 命中词明细（词表防腐化埋点，telemetry terms 反查 ui_jargon / tech_jargon 死词用）。
  # 默认 []（零命中也 emit，标记「这次扫了 + 有埋点」）—— analyze 分母只认带 hits_words
  # 字段的事件，埋点上线前的历史扫描无此字段自动排除，不被误算进死词分母。
  WORDS="[]"
  local HAS_HIT=0
  if [ -s "$TMPJSON" ]; then
    local _w
    _w=$(jq -rc '[.hits[].matched] | unique' "$TMPJSON" 2>/dev/null)
    [ -n "$_w" ] && WORDS="$_w"
    # 用 json hits 判违规（不靠 stderr 非空——框架 DeprecationWarning 会污染 stderr 误报）
    jq -e '.hits | length > 0' "$TMPJSON" >/dev/null 2>&1 && HAS_HIT=1
  fi
  rm -f "$TMPJSON"
  if [ "$HAS_HIT" = "1" ]; then
    echo "" >&2
    echo "⚠️  [context-static-lint] 静态章四不违规（流水时间 / 决策号 / 技术栈 / UI 规范不应进静态章）" >&2
    echo "   文件: $FILE_PATH" >&2
    echo "$STDERR" >&2
    echo "" >&2
    echo "   → 按上方每条「修法」改即可（手改 md，或加章节级 <!-- lint-allow: 词 -->）" >&2
    echo "   → 真不适用 → SKIP_CONTEXT_LINT_GATE=1（仅 false positive 时用）" >&2
    echo "" >&2
    note_add "工区 context-static-lint 检查：${FILE_PATH#$PROJECT_DIR/} 的静态章踩了「四不」（流水时间 / 决策号 / 技术栈 / UI 规范不应进静态章；不阻断）。命中词：${WORDS}。修：手改 md，或加章节级 <!-- lint-allow: 词 -->。"
    log_event hook context-static-lint warn "$FILE_PATH" "" "" "$WORDS"
  else
    log_event hook context-static-lint clean "$FILE_PATH" "" "" "$WORDS"
  fi
  return 0
}

# ── 3.5 scene-list 结构自检（warn 级 · pipeline 源头护栏）────────────
pc_scene_list() {
  local CHECKER="$PROJECT_DIR/.claude/skills/scene-list/scripts/check_scene_list.py"
  [ ! -f "$CHECKER" ] && return 0
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] && return 0
  [ ! -f "$FILE_PATH" ] && return 0
  case "$FILE_PATH" in
    */scene-list.md) ;;
    *) return 0 ;;
  esac
  is_excluded_path "$FILE_PATH" && return 0
  check_skip_env "scene-list-gate" "SKIP_SCENE_LIST_GATE" "$FILE_PATH" && return 0

  local OUT EXIT_CODE
  OUT=$(python3 "$CHECKER" "$FILE_PATH" --strict 2>&1)
  EXIT_CODE=$?
  if [ "$EXIT_CODE" -eq 2 ]; then
    echo "" >&2
    echo "🚫 [scene-list-gate] 检测到重复场景编号——下游 IMAP / 原型 / PRD 依赖编号唯一性，阻断保存：" >&2
    echo "$OUT" | head -20 >&2
    echo "" >&2
    echo "   → 修法：删掉重复行，或重新分配编号（A-3a / A-3b 拆子场景）" >&2
    echo "   → 典型误操：复制粘贴表格行时漏改第一列编号" >&2
    echo "   → 紧急绕过：SKIP_SCENE_LIST_GATE=1" >&2
    log_event hook scene-list-gate block "$FILE_PATH"
    _PC_BLOCKED=1
  elif [ -n "$OUT" ]; then
    echo "" >&2
    echo "⚠️  [scene-list-gate] scene-list 结构问题（warn · 不阻断）：" >&2
    echo "$OUT" | head -20 >&2
    echo "   → 修后重存；临时绕过 SKIP_SCENE_LIST_GATE=1" >&2
    note_add "工区 scene-list-gate 检查：scene-list.md 有结构问题（不阻断）。命中：$(printf '%s' "$OUT" | head -3 | tr '\n' ' ' | tr -s ' ')"
    log_event hook scene-list-gate warn "$FILE_PATH"
  else
    log_event hook scene-list-gate clean "$FILE_PATH"
  fi
  return 0
}

# ── 4. audit-fast（含 scenes/ lite 分支）────────────────────────────
pc_audit_fast() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] && return 0
  is_deliverable_path "$FILE_PATH" || return 0
  is_excluded_path "$FILE_PATH" && return 0
  check_skip_env "audit-fast" "SKIP_AUDIT_FAST" "${FILE_PATH##*/}" && return 0

  case "$FILE_PATH" in
    *-scenes/*)
      # CJK 标点已由 pc_cjk_punct（dispatcher 内先跑、strict block）统一负责，此处只查占位符
      local LITE_FAIL=""
      if grep -qE 'TODO|FIXME|\[待补充\]|\[补充\]|XXX' "$FILE_PATH" 2>/dev/null; then
        LITE_FAIL="${LITE_FAIL}占位符（TODO / FIXME / [待补充] / [补充] / XXX）"$'\n'
      fi
      if [ -n "$LITE_FAIL" ]; then
        echo "" >&2
        echo "🚫 [audit-fast-lite] split scenes/ 子文件轻量自检未通过" >&2
        echo "   文件: $FILE_PATH" >&2
        printf '%s' "$LITE_FAIL" >&2
        echo "   → 修后重试；编号闭环 / 命名前缀闭环仍由主 prd- 文件统一负责" >&2
        echo "   → escape: export SKIP_AUDIT_FAST=1（不推荐）" >&2
        log_event hook audit-fast-lite block "$FILE_PATH"
        _PC_BLOCKED=1
        return 0
      fi
      log_event hook audit-fast-lite clean "$FILE_PATH"
      return 0
      ;;
  esac

  local SCRIPT="$PROJECT_DIR/scripts/audit-fast.sh"
  [ ! -f "$SCRIPT" ] && return 0

  local TMPOUT RC
  TMPOUT=$(mktemp)
  bash "$SCRIPT" "$FILE_PATH" > "$TMPOUT" 2>&1
  RC=$?
  if [ "$RC" -ne 0 ]; then
    echo "" >&2
    echo "🚫 [audit-fast] 产物快速自检未通过（命名前缀 / 编号一致性 / 引用闭合等基础约束）" >&2
    echo "   文件: $FILE_PATH" >&2
    cat "$TMPOUT" >&2
    echo "" >&2
    echo "   → 按上方 audit 报告每条违规修改，重跑 bash scripts/audit-fast.sh $FILE_PATH 确认通过" >&2
    echo "   → 真不适用 → 改 audit-fast.sh 规则或在源产物加 audit-skip 注释（不要逐次绕）" >&2
    echo "" >&2
    log_event hook audit-fast block "$FILE_PATH"
    rm -f "$TMPOUT"
    _PC_BLOCKED=1
    return 0
  fi
  rm -f "$TMPOUT"
  log_event hook audit-fast clean "$FILE_PATH"
  return 0
}

# ── 5. pm-visual-overreach（PRD md 视觉越界）─────────
pc_pm_visual() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && return 0
  case "$FILE_PATH" in
    */deliverables/prd-*.md|*/deliverables/prd-*-scenes/*.md) ;;
    */deliverables/*/prd-*.md|*/deliverables/*/prd-*-scenes/*.md) ;;
    *) return 0 ;;
  esac
  check_skip_env "pm-visual-gate" "SKIP_PM_VISUAL_GATE" "${FILE_PATH##*/}" && return 0

  local PATTERNS_DIR="$PROJECT_DIR/.claude/skills/prd/scripts/humanize"
  local HITS
  HITS=$(python3 -c "
import sys
file_path, patterns_dir = sys.argv[1], sys.argv[2]
sys.path.insert(0, patterns_dir)
from patterns import PM_EMOJI_RE, PM_VISUAL_OVERREACH_RE

visual = []
with open(file_path, encoding='utf-8') as f:
    for i, line in enumerate(f, start=1):
        for m in PM_VISUAL_OVERREACH_RE.finditer(line):
            visual.append(f'L{i}: {m.group()}  ← {line.strip()[:80]}')
        for m in PM_EMOJI_RE.finditer(line):
            visual.append(f'L{i}: 图标 emoji「{m.group()}」（写功能名即可，图标由设计定）  ← {line.strip()[:80]}')

if visual:
    print('VISUAL')
    for h in visual: print(h)
" "$FILE_PATH" "$PATTERNS_DIR" 2>&1)

  local VISUAL_BLOCK FAIL=0
  VISUAL_BLOCK=$(echo "$HITS" | awk '/^VISUAL$/{flag=1; next} flag')

  if [ -n "$VISUAL_BLOCK" ]; then
    FAIL=1
    echo "🚫 [pm-visual-gate] PRD 视觉细节越界（PM 写承载形态 + 业务规则，不定颜色 / 尺寸 / 描边 / 圆角 / ✕ / 图标 emoji 等视觉规格）：" >&2
    echo "   文件: ${FILE_PATH#$PROJECT_DIR/}" >&2
    echo "$VISUAL_BLOCK" | head -10 | sed 's/^/   /' >&2
    echo "   修法：写「按视觉规范」「视觉规范由设计定」「按金融语义色规范（涨绿跌红）」等业务语义" >&2
    echo "" >&2
  fi

  # checker 异常（HITS 含 traceback → awk 不匹配 VISUAL → 原逻辑 FAIL=0 静默放行）不放过
  if [ "$FAIL" -eq 0 ] && echo "$HITS" | grep -qE 'Traceback|Error|Exception|ImportError'; then
    FAIL=1
    echo "🚫 [pm-visual-gate] checker 异常（patterns 加载失败），无法判定视觉越界：" >&2
    echo "$HITS" | head -10 | sed 's/^/   /' >&2
    echo "   修法：检查 .claude/skills/prd/scripts/humanize/patterns.py 是否可 import" >&2
    echo "" >&2
  fi

  if [ "$FAIL" -eq 1 ]; then
    echo "   临时绕过：SKIP_PM_VISUAL_GATE=1 ..." >&2
    log_event hook pm-visual-gate block "${FILE_PATH##*/}"
    _PC_BLOCKED=1
    return 0
  fi
  log_event hook pm-visual-gate clean "${FILE_PATH##*/}"
  return 0
}

# ── 共享：本次新增/修改行清单（bullet / blockquote / prd-content 共用一份 git diff 产物）────
# 原先两 checker 各自跑一遍 git ls-files + git diff -U0 HEAD（同一文件 4 次 git fork）。
# 惰性 + 进程内缓存：首次调用必须发生在 pc_cjk_punct 之后——cjk 是唯一写盘 hook
# （补空格），diff 必须取定型后的文件状态（批量不变量 1 的 bash 侧体现）。
#
# 赋值不 echo：调用方用 `$(...)` 取的话，函数体在子 shell 里跑，_PC_ADDED_FILE 的缓存
# 传不回父 shell —— 每次都重算 git diff，且 mktemp 出来的文件父 shell 不知道，清理漏掉。
_pc_git_added_lines() {  # 设置 _PC_ADDED_FILE（tracked → diff added；untracked → 全文）
  if [ -z "${_PC_ADDED_FILE:-}" ]; then
    _PC_ADDED_FILE=$(mktemp)
    if git -C "$PROJECT_DIR" ls-files --error-unmatch "$HOOK_FILE_PATH" >/dev/null 2>&1; then
      git -C "$PROJECT_DIR" diff -U0 HEAD -- "$HOOK_FILE_PATH" 2>/dev/null \
        | grep '^+' | grep -v '^+++' | sed 's/^+//' > "$_PC_ADDED_FILE"
    else
      cp "$HOOK_FILE_PATH" "$_PC_ADDED_FILE"
    fi
  fi
}

# ── md-blockquote-gate（项目辅助 md 新增 > 导读墙）─────────────────
# diff-based：只看本次新增行（tracked → git diff HEAD；untracked → 全文），存量墙不碰。
# PRD 由 prd-content-gate 管（全禁 >、baseline 豁免）；inputs/ 导入源文档、archive/ 冻结，均放行。
# 合批形态：判定体物化在 scripts/hook_check_md_blockquote.py（逐字节搬运），经
# _pc_enqueue 入批；判定报告在 _pcr_md_blockquote_wall（flush 后跑）。
pc_md_blockquote_wall() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && return 0
  case "$FILE_PATH" in
    */projects/*.md) ;;
    *) return 0 ;;
  esac
  is_excluded_path "$FILE_PATH" && return 0
  case "$FILE_PATH" in
    */prd-*.md|*/prd-*-scenes/*.md) return 0 ;;
    */inputs/*) return 0 ;;
  esac
  check_skip_env "md-blockquote-gate" "SKIP_MD_BLOCKQUOTE_GATE" "${FILE_PATH##*/}" && return 0

  _PC_MBW_QUEUED=0
  local SCRIPT="$PROJECT_DIR/scripts/hook_check_md_blockquote.py"
  [ ! -f "$SCRIPT" ] && return 0
  _pc_git_added_lines
  _pc_enqueue blockquote "$SCRIPT" "$FILE_PATH" --added-file "$_PC_ADDED_FILE"
  _PC_MBW_QUEUED=1
}

_pcr_md_blockquote_wall() {
  [ "${_PC_MBW_QUEUED:-0}" = "1" ] || return 0
  local FILE_PATH="$HOOK_FILE_PATH"
  local HITS
  HITS=$(cat "$_PC_ALL_blockquote")
  rm -f "$_PC_ALL_blockquote"

  local FAIL=0
  if echo "$HITS" | grep -q '^WALL$'; then
    FAIL=1
    echo "🚫 [md-blockquote-gate] 项目 md 本次新增 blockquote 导读墙（> 引用块连排 / 超长，Confluence / 终端渲染丑，破坏文档流）：" >&2
    echo "   文件: ${FILE_PATH#$PROJECT_DIR/}" >&2
    echo "$HITS" | grep -v '^WALL$' | sed 's/^/   /' >&2
    echo "   → 修法: 导读改 **加粗引导**：正文（如「**读表**：…」用粗体 + 普通正文，不用 >）" >&2
    echo "   → 单行短表格说明可留 1 行 >，别连排成墙 / 别单行超 120 字" >&2
    echo "   → 真不适用 → SKIP_MD_BLOCKQUOTE_GATE=1（仅 false positive 时用）" >&2
    echo "" >&2
  elif echo "$HITS" | grep -qE 'Traceback|Error|Exception'; then
    FAIL=1
    echo "🚫 [md-blockquote-gate] checker 异常，无法判定引用墙：" >&2
    echo "$HITS" | head -10 | sed 's/^/   /' >&2
    echo "" >&2
  fi

  if [ "$FAIL" -eq 1 ]; then
    log_event hook md-blockquote-gate block "${FILE_PATH##*/}"
    _PC_BLOCKED=1
    return 0
  fi
  log_event hook md-blockquote-gate clean "${FILE_PATH##*/}"
  return 0
}

# ── 5.5 bullet-density（PRD 单行挤话：句号 ≥3 或 分号 ≥2）─────────
# diff-based：只拦本次新增/修改行（新增行清单与 blockquote 共享 _pc_git_added_lines）。
# 存量 living 文档不卡（分号串渐进消化），章节 / 表格豁免靠 checker 全文状态机。
pc_bullet_density() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && return 0
  # 人读 / 传 Confluence 的 md 产物：projects/ 下全量（PRD / baseline / scene-list / 报告 / 看板需求）+ 根 deliverables/reports/（datareport 周报）
  # 排除 archive（冻结）/ inputs（导入源）/ audits 子目录 / audit-*.md 等内部审计文档（不对外）
  case "$FILE_PATH" in
    */projects/*.md) ;;
    */deliverables/reports/*.md) ;;
    *) return 0 ;;
  esac
  is_excluded_path "$FILE_PATH" && return 0
  case "$FILE_PATH" in
    */inputs/*|*/audits/*) return 0 ;;
  esac
  is_plain_language_exempt "$FILE_PATH" && return 0
  check_skip_env "bullet-density-gate" "SKIP_BULLET_DENSITY_GATE" "${FILE_PATH##*/}" && return 0

  local CHECKER="$PROJECT_DIR/scripts/check_bullet_density.py"
  [ ! -f "$CHECKER" ] && return 0

  _PC_BD_QUEUED=0
  _pc_git_added_lines
  _pc_enqueue bullet "$CHECKER" "$FILE_PATH" --added-file "$_PC_ADDED_FILE" --strict
  _PC_BD_QUEUED=1
}

_pcr_bullet_density() {
  [ "${_PC_BD_QUEUED:-0}" = "1" ] || return 0
  local FILE_PATH="$HOOK_FILE_PATH"
  local RC="${_PC_RC_bullet:-1}" TMPOUT="$_PC_ALL_bullet"
  if [ "$RC" -ne 0 ]; then
    echo "" >&2
    echo "🚫 [bullet-density-gate] PRD 本次改动挤话（bullet 句号 ≥3 / 分号 ≥2 / 单句 ≥100 字 / 段落碎句）" >&2
    echo "   文件: ${FILE_PATH#$PROJECT_DIR/}" >&2
    cat "$TMPOUT" >&2
    echo "" >&2
    echo "   → 修法：挤话拆平级子 bullet（父行只留「标签：」）；长句拆成短句、句号断开；碎句连成完整的话。示例：" >&2
    echo "     改前: - 主播开播：填标题选封面。观众进房看直播。可点赞可打赏。" >&2
    echo "     改后: - 主播开播：" >&2
    echo "             - 填标题、选封面" >&2
    echo "             - 观众进房看直播" >&2
    echo "             - 可点赞、可打赏" >&2
    echo "   → 真不适用 → SKIP_BULLET_DENSITY_GATE=1（仅 false positive）" >&2
    echo "" >&2
    log_event hook bullet-density-gate block "${FILE_PATH##*/}" "" "${_PC_DUR_MS_bullet:-0}"
    _PC_BLOCKED=1
    rm -f "$TMPOUT"
    return 0
  fi
  log_event hook bullet-density-gate clean "${FILE_PATH##*/}" "" "${_PC_DUR_MS_bullet:-0}"
  rm -f "$TMPOUT"
  return 0
}

# ── 5.6 prd-content（PRD 写入时新增行的讲人话 / 结构硬错）─────────
# diff-based：只拦本次新增行。PRD 不在 check_prd_md 的写入路径上，plain-language 与
# md-blockquote 又都以「PRD 走 check_prd_md」为由跳过 PRD —— 写入路径此前整个没门。
# 维度清单与 check_prd_md 同源（humanize/patterns.py prd_fail_keys），去掉别的门已管的
# 圈数字 / 水平线（cjk-punct）与视觉越界（pm-visual-gate）。
pc_prd_content() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && return 0
  case "$FILE_PATH" in
    */deliverables/prd-*.md|*/deliverables/prd-*-scenes/*.md) ;;
    */deliverables/*/prd-*.md|*/deliverables/*/prd-*-scenes/*.md) ;;
    *) return 0 ;;
  esac
  is_excluded_path "$FILE_PATH" && return 0
  check_skip_env "prd-content-gate" "SKIP_PRD_CONTENT_GATE" "${FILE_PATH##*/}" && return 0

  local SCRIPT="$PROJECT_DIR/scripts/hook_check_prd_content.py"
  [ ! -f "$SCRIPT" ] && return 0

  _PC_PRC_QUEUED=0
  _pc_git_added_lines
  _pc_enqueue prd_content "$SCRIPT" "$FILE_PATH" --added-file "$_PC_ADDED_FILE"
  _PC_PRC_QUEUED=1
}

_pcr_prd_content() {
  [ "${_PC_PRC_QUEUED:-0}" = "1" ] || return 0
  local FILE_PATH="$HOOK_FILE_PATH"
  local HITS
  HITS=$(cat "$_PC_ALL_prd_content")
  rm -f "$_PC_ALL_prd_content"

  local FAIL=0
  if echo "$HITS" | grep -q '^HITS$'; then
    FAIL=1
    echo "" >&2
    echo "🚫 [prd-content-gate] PRD 本次改动有讲人话 / 结构硬错（流水账 / 技术字段 / 越界禁词 / 场景正文串句等）：" >&2
    echo "   文件: ${FILE_PATH#$PROJECT_DIR/}" >&2
    echo "$HITS" | grep -v '^HITS$' | sed 's/^/   /' >&2
    echo "" >&2
    echo "   → 修法：按方括号里的维度名逐条改，示例：" >&2
    echo "     改前: 打赏入口（v2.1 新增）  →  改后: 打赏入口（版本变更集中写 §2 本轮需求）" >&2
    echo "     改前: hover 时显示           →  改后: 悬停时显示" >&2
    echo "     改前: - **现状**：A。B。C。   →  改后: 一 bullet 一原子事实，多阶段用 → 串成一行" >&2
    echo "   → 真不适用 → SKIP_PRD_CONTENT_GATE=1（仅 false positive；场景正文叙事确需保留时先用 SKIP_SCENE_PROSE_GATE=1）" >&2
    echo "" >&2
  elif echo "$HITS" | grep -qE 'Traceback|Error|Exception'; then
    FAIL=1
    echo "🚫 [prd-content-gate] checker 异常，无法判定 PRD 内容：" >&2
    echo "$HITS" | head -10 | sed 's/^/   /' >&2
    echo "" >&2
  fi

  if [ "$FAIL" -eq 1 ]; then
    log_event hook prd-content-gate block "${FILE_PATH##*/}"
    _PC_BLOCKED=1
    return 0
  fi
  log_event hook prd-content-gate clean "${FILE_PATH##*/}"
  return 0
}

# ── 6. prototype-audit（proto-*.html E1-E6 视觉铁律）─────────────────
pc_prototype_audit() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] && return 0
  case "$FILE_PATH" in
    */deliverables/proto-*.html|*/deliverables/*/proto-*.html) ;;
    *) return 0 ;;
  esac
  is_excluded_path "$FILE_PATH" && return 0
  local SCRIPT="$PROJECT_DIR/.claude/skills/prototype/scripts/audit_against_baseline.py"
  [ ! -f "$SCRIPT" ] && return 0

  run_checker_capture python3 "$SCRIPT" "$FILE_PATH"
  if [ "$RC" -ne 0 ]; then
    echo "═══ prototype audit fail (post-prototype-audit) ═══" >&2
    cat "$TMPOUT" >&2
    echo "" >&2
    echo "→ 修复方案：改 src/scenes/*.py 重 build。E 组见 references/prototype-components.md § E（Fill 视觉铁律）；V 组（数字排版 / 素材 / 悬浮 / 交互态）见 references/visual-rework-atlas.md，多数可直接换用 crypto-dark.css 的 cx- 组件" >&2
    log_event hook prototype-audit block "$FILE_PATH" "" "$DUR_MS"
    _PC_BLOCKED=1
    return 0
  fi
  log_event hook prototype-audit clean "$FILE_PATH" "" "$DUR_MS"
  return 0
}

# ── block 类 checker 的统一骨架 ──────────────────────────────────────
# 各 wrapper 自理「路径 glob case」（逐 gate 可读），其余骨架全收在此：
# 守卫 → is_excluded_path → SKIP 门 → checker 存在性 → 跑 checker → rc 判定
# → 四段式 stderr → log_event block/clean → _PC_BLOCKED（不 exit，由 dispatcher 统一收口）
#
# 用法：_pc_strict_block GATE SKIP_VAR CHECKER EXTRA_ARGS RC_TEST TITLE 修法行...
#   GATE        gate 字符串名（log_event 用，稳定契约，不许改）
#   SKIP_VAR    SKIP 环境变量名
#   CHECKER     checker 相对 PROJECT_DIR 的路径
#   EXTRA_ARGS  额外参数；"" = 无
#   RC_TEST     ne0 = 非 0 即违规；eq2 = 仅退出码 2 违规（checker 有三态时用）
#   TITLE       🚫 行正文（模板自动补 "🚫 [GATE] " 前缀与「文件:」行）
#   修法行...    TITLE 之后逐行输出（每行一个参数，含前导缩进）
_pc_strict_block() {
  local gate="$1" skip_var="$2" checker="$3" extra="$4" rc_test="$5" title="$6"
  shift 6
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && return 0
  is_excluded_path "$FILE_PATH" && return 0
  check_skip_env "$gate" "$skip_var" "$FILE_PATH" && return 0

  local SCRIPT="$PROJECT_DIR/$checker"
  [ ! -f "$SCRIPT" ] && return 0

  # shellcheck disable=SC2086  # extra 需按空格拆成多个参数（只传固定 flag）
  run_checker_capture python3 "$SCRIPT" "$FILE_PATH" $extra
  local hit=0
  case "$rc_test" in
    eq2) [ "$RC" -eq 2 ] && hit=1 ;;
    ne0) [ "$RC" -ne 0 ] && hit=1 ;;
  esac
  if [ "$hit" = "1" ]; then
    local line
    echo "" >&2
    echo "🚫 [$gate] $title" >&2
    echo "   文件: $FILE_PATH" >&2
    cat "$TMPOUT" >&2
    echo "" >&2
    for line in "$@"; do echo "$line" >&2; done
    echo "" >&2
    log_event hook "$gate" block "$FILE_PATH" "" "$DUR_MS"
    _PC_BLOCKED=1
    return 0
  fi
  log_event hook "$gate" clean "$FILE_PATH" "" "$DUR_MS"
  return 0
}

# ── 7. prototype-source（scenes_*.py page_fns 设备壳越界）────────────
pc_prototype_source() {
  case "$HOOK_FILE_PATH" in
    */projects/*/scripts/proto_v*/scenes_*.py) ;;
    */projects/*/scripts/proto_v*/page_fns*.py) ;;
    */projects/*/scripts/*scenes_*.py) ;;
    */projects/*/scripts/src/scenes/*.py) ;;
    *) return 0 ;;
  esac
  _pc_strict_block "prototype-shell-gate" "SKIP_PROTOTYPE_SHELL_GATE" \
    ".claude/skills/prototype/scripts/check_page_fns_shell.py" "--strict" ne0 \
    "page_fns 生成超出设备壳范围（应仅产页内容，外壳由模板提供）" \
    "   → 修法: 从 page_fns 函数体里移除 .app-mock / .layout / .p-nav / .phone / .status-bar / <aside> 等外壳元素，只留页面内 UI" \
    "   → 规则源: .claude/skills/prototype/SKILL.md §设备壳门（L254 / L304）" \
    "   → 真不适用 → SKIP_PROTOTYPE_SHELL_GATE=1（极少数特殊壳设计，需在源文件 head 注释说明）"
}

# ── 7b. prototype-split（proto-*.html 必须有 src/scenes 分场景拆分）──
pc_prototype_split() {
  case "$HOOK_FILE_PATH" in
    */deliverables/proto-*.html|*/deliverables/*/proto-*.html) ;;
    *) return 0 ;;
  esac
  _pc_strict_block "prototype-split-gate" "SKIP_PROTOTYPE_SPLIT_GATE" \
    ".claude/skills/prototype/scripts/check_proto_split.py" "--strict" ne0 \
    "原型 page_fns 未拆分到 src/scenes（疑似内联在 orchestrator 单文件）" \
    "   → 修法: 拆 projects/{项目}/scripts/src/scenes/{view_id}_{page_id}.py 一文件一页面，build_proto_v{N}.py import 收口后重 build" \
    "   → 规则源: .claude/skills/prototype/SKILL.md §硬规则 11（src/scenes 分场景拆分）+ .claude/runbooks/html-build-split.md §二" \
    "   → 真不适用 → SKIP_PROTOTYPE_SPLIT_GATE=1（极少数单页极简原型，需说明）"
}

# ── 7c. imap-split（imap-*.html 必须有 src/scenes 分场景拆分）────────
pc_imap_split() {
  case "$HOOK_FILE_PATH" in
    */deliverables/imap-*.html|*/deliverables/*/imap-*.html) ;;
    *) return 0 ;;
  esac
  _pc_strict_block "imap-split-gate" "SKIP_IMAP_SPLIT_GATE" \
    ".claude/skills/interaction-map/scripts/check_imap_split.py" "--strict" ne0 \
    "IMAP scene_fns 未拆分到 src/scenes（疑似内联在 orchestrator 单文件）" \
    "   → 修法: 拆 projects/{项目}/scripts/src/scenes/{scene_id}.py 一文件一主场景，build_imap_v{N}.py import 收口后重 build" \
    "   → 规则源: .claude/skills/interaction-map/SKILL.md §硬规则 11（src/scenes 分场景拆分）+ .claude/runbooks/html-build-split.md §二" \
    "   → 真不适用 → SKIP_IMAP_SPLIT_GATE=1（极少数单场景极简 IMAP，需说明）"
}

# ── 7d. ui-annotation（proto/imap mockup 渲染屏内禁开发注解）─────────
# 防御纵深：正常 build 走 Bash 路径（checkers.sh），此处兜直接 Write/Edit HTML 的情况。
pc_ui_annotation() {
  case "$HOOK_FILE_PATH" in
    */deliverables/proto-*.html|*/deliverables/*/proto-*.html) ;;
    */deliverables/imap-*.html|*/deliverables/*/imap-*.html) ;;
    *) return 0 ;;
  esac
  _pc_strict_block "ui-annotation-gate" "SKIP_UI_ANNOTATION_GATE" \
    "scripts/check_ui_annotation.py" "--strict" eq2 \
    "渲染 UI 屏内写了开发注解，开发会误读为真实产品文案" \
    "   → 原型: 删掉注解，屏内只放真实文案；IMAP: 注解移到 mockup 外的 ann-card / flow-note" \
    "   → 改源 scene_fns / page_fns 后重 build（禁直改 HTML）" \
    "   → 规则源: prototype/SKILL.md + interaction-map/SKILL.md §硬规则（渲染 UI 内禁注解）" \
    "   → 真不适用（极少数 false positive）→ SKIP_UI_ANNOTATION_GATE=1"
}

# ── 8. prd-cross-check（PRD md 7 维一致性，warn 永不 block）──────────
pc_prd_cross_check() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] && return 0
  case "$FILE_PATH" in
    */deliverables/prd-*.md|*/deliverables/*/prd-*.md) ;;
    *) return 0 ;;
  esac
  is_excluded_path "$FILE_PATH" && return 0
  check_skip_env "prd-cross-check-gate" "SKIP_PRD_CROSS_CHECK_GATE" "$FILE_PATH" && return 0

  local PROJECT
  PROJECT=$(echo "$FILE_PATH" | sed -nE 's|.*/projects/(.*)/deliverables/.*|\1|p')
  [ -z "$PROJECT" ] && return 0

  local SCRIPT="$PROJECT_DIR/.claude/skills/cross-check/scripts/cross-check-auto.sh"
  [ ! -f "$SCRIPT" ] && return 0

  # argv 传参（$1=PROJECT_DIR $2=SCRIPT $3=PROJECT），路径含单引号也安全
  run_checker_capture bash -c 'cd "$1" && bash "$2" "$3"' _ "$PROJECT_DIR" "$SCRIPT" "$PROJECT"
  local REL="${FILE_PATH#${PROJECT_DIR}/}"

  case "$RC" in
    0)
      log_event hook prd-cross-check-gate clean "$REL" "" "$DUR_MS"
      ;;
    2)
      echo "" >&2
      echo "⚠️  [prd-cross-check-gate] PRD 已写入但前置文件缺失，跨产出物 7 维校验跳过" >&2
      echo "   文件: $REL" >&2
      echo "   项目: $PROJECT" >&2
      head -10 "$TMPOUT" >&2
      echo "" >&2
      echo "   → 修法: 检查 projects/$PROJECT/ 是否缺 scene-list.md 或 deliverables/ 子目录" >&2
      echo "   → 真不适用 → SKIP_PRD_CROSS_CHECK_GATE=1（仅项目骨架未到位时）" >&2
      note_add "工区 prd-cross-check-gate 检查：${REL} 所在项目的骨架未到位（缺 scene-list.md 或 deliverables/），跨产出物 7 维校验被跳过（不阻断）。项目：${PROJECT}。"
      log_event hook prd-cross-check-gate skip-noprereq "$REL"
      ;;
    *)
      echo "" >&2
      echo "⚠️  [prd-cross-check-gate] PRD 与已有产出物存在跨文件一致性问题（编号 / 术语 / View / 跳转 / 字段）" >&2
      echo "   文件: $REL" >&2
      echo "   项目: $PROJECT" >&2
      echo "" >&2
      head -40 "$TMPOUT" >&2
      echo "" >&2
      echo "   → 修法 1: 按上面 ❌ 项定位，对照典型错误模式改写：" >&2
      echo "     ① 场景编号错位：PRD 写「A-3 开播流程」→ 应核对 scene-list.md 第一列，编号+描述一字不差" >&2
      echo "     ② 术语漂移：PRD 写「房间」→ 应 Read prd-{产品线}-baseline.md §术语表，复制标准词「直播间」" >&2
      echo "     ③ View ID 脱节：IMAP 里 V03，PRD §4.3 写的 V04 → View ID 从 imap-*.html 来源复制，不手写" >&2
      echo "   → 修法 2: 手动重跑校验定位完整问题清单：" >&2
      echo "     bash .claude/skills/cross-check/scripts/cross-check-auto.sh $PROJECT" >&2
      echo "   → 真不适用 → SKIP_PRD_CROSS_CHECK_GATE=1（仅 false positive 或老项目兼容时）" >&2
      note_add "工区 prd-cross-check-gate 检查：${REL} 与已有产出物存在跨文件一致性问题（编号 / 术语 / View / 跳转 / 字段，不阻断）。项目：${PROJECT}。完整清单：bash .claude/skills/cross-check/scripts/cross-check-auto.sh ${PROJECT}。"
      log_event hook prd-cross-check-gate block "$REL" "" "$DUR_MS"
      ;;
  esac
  return 0  # warn 类恒不 block
}

# ── 9. script-syntax（.py/.sh/.js/.json/.yaml 语法自检）──────────────
pc_script_syntax() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && return 0
  is_excluded_path "$FILE_PATH" && return 0
  local SYNTAX_LANG
  case "$FILE_PATH" in
    *.py)              SYNTAX_LANG=py ;;
    *.sh)              SYNTAX_LANG=sh ;;
    *.js|*.mjs|*.cjs)  SYNTAX_LANG=js ;;
    *.json)            SYNTAX_LANG=json ;;
    *.yaml|*.yml)      SYNTAX_LANG=yaml ;;
    *) return 0 ;;
  esac
  check_skip_env "script-syntax-gate" "SKIP_SCRIPT_SYNTAX_GATE" "$FILE_PATH" && return 0

  local REL="${FILE_PATH#${PROJECT_DIR}/}" EXTRA_HINT="" CHECKER MSG FIX SELFCHECK
  case "$SYNTAX_LANG" in
    py)
      # ruff F 类 = pyflakes 超集（漏 import / 未定义名 / 未用变量），比 py_compile 多抓一层。
      # 只 --select F：E/I 格式类存量 285 条，当阻断闸会淹没真 bug（全量走人手 `ruff check .`）。
      # 排除 F401：本闸跑每次 Edit 的中间态，「先加 import 再加使用」两步编辑必然在中间态
      # 报未用 import —— 假阳会诱导删掉真在用的 import。F401 交给收尾自检与 audit cat22；
      # F821 未定义名 / F811 重复定义等真崩项全部保留阻断。
      if python3 -m ruff --version >/dev/null 2>&1; then
        run_checker_capture python3 -m ruff check --select F --ignore F401 --no-cache "$FILE_PATH"
        CHECKER="ruff(F 除 F401)"
        SELFCHECK="python3 -m ruff check --select F $REL"
        EXTRA_HINT="   → F401（import 未使用）本闸不拦（两步 Edit 中间态会假阳）；改完跑上面自检收尾"
      elif python3 -c "import pyflakes" 2>/dev/null; then
        run_checker_capture python3 -m pyflakes "$FILE_PATH"
        CHECKER="pyflakes"
        SELFCHECK="python3 -m pyflakes $REL"
      else
        run_checker_capture python3 -m py_compile "$FILE_PATH"
        CHECKER="py_compile"
        EXTRA_HINT="   → 升级: \`python3 -m pip install ruff\` 装上能多抓「漏 import / 未定义名」"
        SELFCHECK="python3 -m py_compile $REL"
      fi
      MSG="Python 脚本语法/引用错误（改完没自检会让下游 import 直接挂）"
      FIX="按上面行号定位，修语法 / 补 import / 改错变量名"
      ;;
    sh)
      # bash -n 只抓语法；shellcheck -S error 补一层「语法过但必然跑挂」（全仓存量 0，纯防未来）。
      # warning 级不接（存量 59 条多为风格偏好），人手跑 `shellcheck -S warning <file>` 看。
      if command -v shellcheck >/dev/null 2>&1; then
        run_checker_capture shellcheck -S error "$FILE_PATH"
        CHECKER="shellcheck(error)"
        SELFCHECK="shellcheck -S error $REL"
      else
        run_checker_capture bash -n "$FILE_PATH"
        CHECKER="bash -n"
        EXTRA_HINT="   → 升级: \`brew install shellcheck\` 装上能多抓「语法过但必然跑挂」"
        SELFCHECK="bash -n $REL"
      fi
      MSG="Shell 脚本语法错误（hook 链或子进程跑会直接挂）"
      FIX="按报错行号修语法"
      ;;
    js)
      run_checker_capture node --check "$FILE_PATH"
      CHECKER="node --check"; MSG="JS 脚本语法错误"
      FIX="按报错行号修语法"; SELFCHECK="node --check $REL"
      ;;
    json)
      run_checker_capture python3 -c "import json, sys; json.load(open(sys.argv[1]))" "$FILE_PATH"
      CHECKER="python3 json.load"; MSG="JSON 解析失败（settings.json / 配置文件 / jq pipeline 会直接挂）"
      FIX="按报错位置修，常见: 缺/多逗号、错引号、未闭合括号"; SELFCHECK="jq empty $REL"
      ;;
    yaml)
      run_checker_capture python3 -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]))" "$FILE_PATH"
      CHECKER="python3 yaml.safe_load"; MSG="YAML 解析失败"
      FIX="按报错位置修，常见: 缩进不一致 / 冒号后缺空格 / tab 混 space"
      SELFCHECK="python3 -c \"import yaml; yaml.safe_load(open('$REL'))\""
      ;;
  esac

  if [ "$RC" -ne 0 ]; then
    echo "" >&2
    echo "🚫 [script-syntax-gate] $MSG" >&2
    echo "   文件: $REL" >&2
    echo "   检测: $CHECKER" >&2
    echo "" >&2
    head -40 "$TMPOUT" >&2
    echo "" >&2
    echo "   → 修法: $FIX" >&2
    echo "   → 自检: $SELFCHECK" >&2
    [ -n "$EXTRA_HINT" ] && echo "$EXTRA_HINT" >&2
    echo "   → 真不适用 → SKIP_SCRIPT_SYNTAX_GATE=1（仅 false positive，如动态 import / 模板片段 / 草稿）" >&2
    log_event hook script-syntax-gate block "$FILE_PATH" "" "$DUR_MS"
    _PC_BLOCKED=1
    return 0
  fi
  log_event hook script-syntax-gate clean "$FILE_PATH" "" "$DUR_MS"
  return 0
}

# ── 产品线路径段抽取（campaign 嵌套取全段，单段项目取首段）─────────────────
# 对齐 dashboard.py（**/prd-*-baseline.md 认嵌套）与 audit-fast.sh（(.+) 贪婪）的口径；
# 原单段抽取把 growth/queen 类嵌套项目的产线三查静默 skip（baseline 在嵌套层 ls 不到）。
# 三个 checker 均接受路径片段（repo_root / "projects" / <本函数输出>）。
_pc_product_line_of() {  # $1 = 产物路径 → 产品线路径段（growth/queen 或 liveline；无 /projects/ 前缀则空）
  local seg
  case "$1" in
    */projects/*) ;;
    *) return 0 ;;
  esac
  seg="${1#*/projects/}"
  case "$1" in
    */deliverables/*) printf '%s' "${seg%%/deliverables/*}" ;;
    */prd-*-baseline.md) printf '%s' "${seg%/*}" ;;
    *) printf '%s' "${seg%%/*}" ;;
  esac
}

# ── 10-11. 产品线级 warn checker 公共骨架（合批形态）──────────────────
# 抽产品线 → 入队（_pc_line_enqueue）→ flush 后 grep 红灯标记判定（_pcr_line_warn）。
# 触发 case 留在各自 wrapper（触发面不同）；checker / 标记 / 文案 / 报告命令走参数。
# TTL 节流完全留在 bash（dispatcher _dedup_if_fresh，fresh 的 gate 根本不入队）；
# hash 抑制作用于该槽 .all（与单跑 stdout 逐字节相等 → hash 不变 → 抑制行为不变）。
_pc_line_enqueue() {
  # $1 gate 名（字面量，gen_hooks_readme 提取源） $2 SKIP env 名  $3 checker 相对路径
  local gate="$1" skip_var="$2" checker="$3"
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && return 0
  is_excluded_path "$FILE_PATH" && return 0
  check_skip_env "$gate" "$skip_var" "$FILE_PATH" && return 0

  local CHECKER="$PROJECT_DIR/$checker"
  [ ! -f "$CHECKER" ] && return 0

  # 抽产品线（campaign 嵌套取全段 growth/queen；baseline 取所在目录；delta 取 deliverables 前全段）
  local PRODUCT_LINE
  PRODUCT_LINE=$(_pc_product_line_of "$FILE_PATH")
  [ -z "$PRODUCT_LINE" ] && return 0
  # 仅当该项目根存在 baseline 时才查（否则非 baseline 项目，skip）
  ls "$PROJECT_DIR/projects/$PRODUCT_LINE"/prd-*-baseline.md >/dev/null 2>&1 || return 0

  local slot="${gate//-/_}"
  _pc_enqueue "$slot" "$CHECKER" "$PRODUCT_LINE"
  eval "_PC_LW_QUEUED_${slot}=1"
}

# 判定报告（flush 后由各 _pcr_* wrapper 以字面量参数调用；判定代码与原 _pc_line_warn 逐字节同源）
_pcr_line_warn() {
  # $1 gate 名  $2 红灯标记（grep -q 判定）  $3 明细子过滤词（grep -A20 后按词过滤）
  # $4 warn 首行标题  $5 提示行  $6 报告命令前缀
  # $7 hash 抑制 TTL 秒（可选，0 = 不抑制）：checker 输出 hash 未变则 TTL 内只 warn 一次
  local gate="$1" mark="$2" subfilter="$3" title="$4" hint="$5" report_cmd="$6"
  local hash_ttl="${7:-0}"
  local slot="${gate//-/_}"
  local queued=0
  eval "queued=\${_PC_LW_QUEUED_${slot}:-0}"
  [ "$queued" = "1" ] || return 0

  local PRODUCT_LINE
  PRODUCT_LINE=$(_pc_product_line_of "$HOOK_FILE_PATH")
  local TMPOUT RC
  eval "TMPOUT=\$_PC_ALL_${slot}"
  eval "RC=\$_PC_RC_${slot}"

  if grep -q "$mark" "$TMPOUT" 2>/dev/null; then
    # 状态不变抑制：checker 输出 hash 与上次相同 + TTL 内 → 跳过 warn（emit dedupe-skip）
    if [ "$hash_ttl" -gt 0 ] 2>/dev/null; then
      local out_hash cache_file prev_hash prev_ts now
      out_hash=$(shasum "$TMPOUT" 2>/dev/null | cut -c1-16)
      cache_file="${TMPDIR:-/tmp}/pmws_warn_hash/${gate}.${PRODUCT_LINE}"
      if [ -f "$cache_file" ]; then
        prev_hash=$(head -1 "$cache_file" 2>/dev/null)
        prev_ts=$(tail -1 "$cache_file" 2>/dev/null)
        now=$(date +%s)
        if [ "$out_hash" = "$prev_hash" ] && [ -n "$prev_ts" ] && [ $((now - prev_ts)) -lt "$hash_ttl" ]; then
          log_event hook "$gate" dedupe-skip "$PRODUCT_LINE (state unchanged, $((hash_ttl - (now - prev_ts)))s left)"
          rm -f "$TMPOUT"
          return 0
        fi
      fi
      mkdir -p "$(dirname "$cache_file")" 2>/dev/null
      printf '%s\n%s\n' "$out_hash" "$now" > "$cache_file"
    fi
    echo "" >&2
    echo "⚠️  [$gate] $title" >&2
    echo "   产品线: $PRODUCT_LINE" >&2
    grep -A20 "$mark" "$TMPOUT" | grep "$subfilter" | head -8 | sed 's/^/   /' >&2
    echo "" >&2
    [ -n "$hint" ] && echo "   → $hint" >&2
    echo "   → 完整报告：$report_cmd $PRODUCT_LINE" >&2
    echo "" >&2
    local NOTE_HINT=""
    [ -n "$hint" ] && NOTE_HINT="相关约定：${hint}。"
    note_add "工区 ${gate} 检查发现：产品线 ${PRODUCT_LINE} ${title}。命中：$(grep -A20 "$mark" "$TMPOUT" | grep "$subfilter" | head -3 | tr '\n' ' ' | tr -s ' ')。${NOTE_HINT}完整报告：${report_cmd} ${PRODUCT_LINE}。"
    log_event hook "$gate" warn "$PRODUCT_LINE"
  else
    log_event hook "$gate" clean "$PRODUCT_LINE"
  fi
  rm -f "$TMPOUT"
  return 0  # warn 类恒不 block
}

# ── 10. baseline-fresh（编辑 baseline / delta 后查反向合并新鲜度，warn 永不 block）──
pc_baseline_fresh() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && return 0
  # 触发：产品线根 baseline，或 deliverables/ 下的 delta（迭代 PRD）
  case "$FILE_PATH" in
    */projects/*/prd-*-baseline.md) ;;
    */projects/*/deliverables/prd-*.md|*/projects/*/*/deliverables/prd-*.md) ;;
    */projects/*/deliverables/*/prd-*.md) ;;
    *) return 0 ;;
  esac
  _pc_line_enqueue "baseline-fresh-gate" "SKIP_BASELINE_FRESH_GATE" "scripts/check_baseline_fresh.py"
}
_pcr_baseline_fresh() {
  _pcr_line_warn "baseline-fresh-gate" '🔴' '❌' \
    'baseline 流程新鲜度 STALE —— 有已上线 delta 未反向合并进 baseline' \
    '承重不变量：delta 上线后必须 ① 补 changelog 行（状态=已合并）② 反向合并进 baseline 对应模块章' \
    'python3 scripts/check_baseline_fresh.py'
}

# ── 10b. delta-conflict（并行在途 delta 反向合并目标重叠，warn 永不 block）──
pc_delta_conflict() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && return 0
  # 触发：仅 delta 路径（冲突是 delta 间的事，不含 baseline 本身）
  case "$FILE_PATH" in
    */projects/*/deliverables/prd-*.md|*/projects/*/*/deliverables/prd-*.md) ;;
    */projects/*/deliverables/*/prd-*.md) ;;
    *) return 0 ;;
  esac
  _pc_line_enqueue "delta-conflict-gate" "SKIP_DELTA_CONFLICT_GATE" "scripts/check_delta_conflict.py"
}
_pcr_delta_conflict() {
  _pcr_line_warn "delta-conflict-gate" '🟡' '∩' \
    '并行在途 delta 反向合并目标重叠 —— 多个 delta 改同一 baseline 目标' \
    '反向合并前核对合并顺序与是否矛盾（脚本只报目标重叠，不判真矛盾）' \
    'python3 scripts/check_delta_conflict.py'
}

# ── 11. rule-version-drift（产物骨架版本落后校验，warn 永不 block）──
pc_rule_version_drift() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && return 0
  # 触发：产品线根 baseline，或 deliverables/ 树下 md / html 产物（深度 ≤ 3）
  case "$FILE_PATH" in
    */projects/*/prd-*-baseline.md) ;;
    */projects/*/deliverables/*.md|*/projects/*/deliverables/*/*.md|*/projects/*/deliverables/*/*/*.md) ;;
    */projects/*/deliverables/*.html|*/projects/*/deliverables/*/*.html|*/projects/*/deliverables/*/*/*.html) ;;
    *) return 0 ;;
  esac
  _pc_line_enqueue "rule-version-drift-gate" "SKIP_RULE_VERSION_DRIFT_GATE" "scripts/check_rule_version_drift.py"
}
_pcr_rule_version_drift() {
  # 只报红灯（版本落后）；黄灯（遗留产物缺戳）不喷——现存产物全无戳会噪音
  _pcr_line_warn "rule-version-drift-gate" '🔴' '❌' \
    '产物骨架版本落后 —— 有产物按旧规则生成，规则源已升级需重生成' \
    '重生成产物（骨架脚本自动打当前版本戳）或确认仍适用后忽略' \
    'python3 scripts/check_rule_version_drift.py' \
    86400
}

# ── 12. test-reminder（改规则层/脚本/hook 后提醒跑测试，warn 永不 block）──
pc_test_reminder() {
  local FILE_PATH="$HOOK_FILE_PATH"
  [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ] && return 0
  is_excluded_path "$FILE_PATH" && return 0

  local KIND
  case "$FILE_PATH" in
    */CLAUDE.md|*/.claude/skills/*/SKILL.md|*/.claude/runbooks/*.md|*/.claude/output-styles/*.md) KIND="规则层" ;;
    */scripts/*.py|*/scripts/*/*.py|*/scripts/*.sh|*/scripts/*/*.sh|*/.claude/skills/*/scripts/*.py|*/.claude/skills/*/scripts/*/*.py|*/.claude/skills/*/scripts/*.sh|*/.claude/skills/*/scripts/*/*.sh) KIND="脚本" ;;
    */.claude/hooks/*.sh|*/.claude/hooks/*/*.sh|*/.claude/settings.json) KIND="hook" ;;
    *) return 0 ;;
  esac

  check_skip_env "test-reminder-gate" "SKIP_TEST_REMINDER_GATE" "$FILE_PATH" && return 0

  # 固定 key dedup：10min 内只提醒一次（跨文件），防连续改多文件刷屏
  # 放路径匹配 + SKIP 之后 → 改产物文件 / SKIP 命中不消耗配额
  _dedup_if_fresh test-reminder-gate 600 "global" && return 0

  local REL="${FILE_PATH#${PROJECT_DIR}/}"
  echo "" >&2
  echo "⚠️  [test-reminder-gate] 改了${KIND}资产，收尾前跑单元 + 回归测试" >&2
  echo "   文件: ${REL}（${KIND}）" >&2
  echo "   未跑就推 / 切 session，hook 链 / 脚本回归风险会漏到线上" >&2
  echo "" >&2
  echo "   → 单元测试: python3 -m pytest scripts/tests/ -q" >&2
  echo "   → 回归测试: bash .claude/hooks/test/test-hooks.sh" >&2
  echo "   → 真不适用（纯文档 / 注释微调）→ SKIP_TEST_REMINDER_GATE=1" >&2
  note_add "本轮改动落在工区的${KIND}资产（${REL}）。按工区约定，这三类改动收尾前要跑 python3 -m pytest scripts/tests/ -q 与 bash .claude/hooks/test/test-hooks.sh。（本条来自工区 test-reminder-gate 检查）"
  log_event hook test-reminder-gate warn "$FILE_PATH"
  return 0  # warn 类恒不 block
}
