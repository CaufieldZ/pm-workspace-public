#!/usr/bin/env bash
# 共享：Bash 路径 sub-checker fn（被 post-bash-deliverable-check.sh 调度）
#
# 用途：cjk / plain-language / prd-check 三个 Bash 路径检查器收口到单一调度入口，
#       共享一次 hook_parse_all 解析。
#
# 每个 sub-checker fn：
#   - 自检 trigger pattern（自己 grep $CMD 决定是否跑），不跑直接 return 0
#   - 跑外部 checker → mktemp 收集 → stderr 报错 → log_event gate 字符串名
#   - fail → exit 2 + stderr 用户消息
#
# 各 gate 行为差异：
#   - script-rebuild-cjk：发射方是 cjk 检查器（half-life 真相源见 .claude/_meta/half-life.md）
#   - plain-language-gate：唯一含根 deliverables/ 的检查器（--include-root-deliverables）
#   - prd-check-gate：排除 *-scenes/* + 支持 --skeleton flag（split PRD 父 PRD 兼容）
set +e
_check_block() {
  local gate="$1"
  local detail="$2"
  log_event hook "$gate" block "$detail"
  exit 2
}

_check_warn() {
  log_event hook "$1" warn "$2"
}

_check_clean() {
  log_event hook "$1" clean "$2"
}

# SKIP 门（return 版，对齐 post-checks _pc_skip）：命中 env 或 inline → _log_skip_gate + return 0
_check_skip() {
  local gate="$1" var="$2" cmd="$3" val
  eval "val=\${${var}:-0}"
  if [ "$val" = "1" ]; then
    _log_skip_gate "$gate" "env  ${cmd:0:120}"
    return 0
  fi
  if echo "$cmd" | grep -qE "\b${var}=1\b"; then
    _log_skip_gate "$gate" "inline  ${cmd:0:120}"
    return 0
  fi
  return 1
}

# ── Sub-checker 1: CJK 标点（gen|fill|patch|update|render_*.{py,js} 后扫近 30s）─────

check_cjk_for_bash_recent() {
  local cmd="$1"
  echo "$cmd" | grep -qE '\b(gen|fill|patch|update|render)_[a-zA-Z0-9_-]+\.(py|js)\b' || return 0

  if [ "${SKIP_SCRIPT_REBUILD_CJK_GATE:-0}" = "1" ]; then
    _log_skip_gate script-rebuild-cjk "env  ${cmd:0:120}"
    return 0
  fi
  if echo "$cmd" | grep -qE '\bSKIP_SCRIPT_REBUILD_CJK_GATE=1\b'; then
    _log_skip_gate script-rebuild-cjk "inline  ${cmd:0:120}"
    return 0
  fi

  local proj="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  local checker="$proj/scripts/check_cjk_punct.py"
  [ ! -f "$checker" ] && return 0

  local recent
  recent=$(find_recent_deliverables 30 '*.html' '*.md' '*.drawio')
  [ -z "$recent" ] && return 0

  local tmpout
  tmpout=$(mktemp)
  # NUL 分隔避免含空格的文件名被 xargs 按空格拆错参数（-0 两端 BSD/GNU 通吃）
  echo "$recent" | tr '\n' '\0' | xargs -0 python3 "$checker" --strict > "$tmpout" 2>&1
  local rc=$?
  local first
  # 多文件 xargs 聚合 rc，head -1 会指错文件 → 从 checker 输出解析首个违规文件
  first=$(grep -m1 -E '^[^[:space:]]+ — ' "$tmpout" 2>/dev/null | sed 's/ —.*//')
  [ -z "$first" ] && first=$(echo "$recent" | head -1)

  if [ "$rc" -ne 0 ]; then
    echo "" >&2
    echo "🚫 [script-rebuild-cjk] 脚本重生的产物含 CJK 旁半角标点（中文旁夹半角逗号 / 句号 / 括号，渲染丑）" >&2
    echo "   文件: $(echo "$first" | sed "s#$proj/##")" >&2
    head -30 "$tmpout" >&2
    echo "" >&2
    echo "   → 修法 1: 改源脚本里的字符串字面量（把半角标点改全角），重跑 gen/fill/patch 脚本重生" >&2
    echo "   → 修法 2: 只想快速修产物 → python3 scripts/check_cjk_punct.py --fix \"$first\"（--dry-run 先预览；注意下次重跑脚本会覆盖，最终仍要改源）" >&2
    echo "   → 真不适用 → SKIP_SCRIPT_REBUILD_CJK_GATE=1（仅 false positive，如外部引入非自产产物）" >&2
    echo "" >&2
    rm -f "$tmpout"
    _check_block script-rebuild-cjk "$first"
    return 0
  fi

  if grep -q '⚠️' "$tmpout" 2>/dev/null; then
    echo "" >&2
    echo "⚠️  [script-rebuild-cjk] 脚本重生的产物含 CJK 排版 warn（不阻断，但会带进下次重生）" >&2
    echo "   文件: $(echo "$first" | sed "s#$proj/##")" >&2
    head -30 "$tmpout" >&2
    echo "" >&2
    echo "   → 收尾前改源脚本字符串字面量修掉，避免每次重生都复现" >&2
    echo "" >&2
    _check_warn script-rebuild-cjk "$first"
    rm -f "$tmpout"
    return 0
  fi

  _check_clean script-rebuild-cjk "$first"
  rm -f "$tmpout"
}

# ── Sub-checker 2: 讲人话（gen|fill_*.{py,sh} 后扫近 60s，含根 deliverables/）─────

check_plain_language_for_bash_recent() {
  local cmd="$1"
  echo "$cmd" | grep -qE '\b(gen|fill)_[a-zA-Z0-9_-]+\.(py|sh)\b' || return 0

  local proj="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  local checker="$proj/scripts/check_plain_language.py"
  [ ! -f "$checker" ] && return 0

  _check_skip plain-language-gate SKIP_PLAIN_LANGUAGE_GATE "$cmd" && return 0

  local recent
  recent=$(find_recent_deliverables 60 --include-root-deliverables '*.md' '*.html' '*.drawio' '*.mmd')
  [ -z "$recent" ] && return 0

  local fail=0
  local fail_output=""

  while IFS= read -r f; do
    [ -z "$f" ] && continue
    is_plain_language_exempt "$f" && continue

    local tmpout
    tmpout=$(mktemp)
    python3 "$checker" "$f" --strict > "$tmpout" 2>&1
    local rc=$?
    if [ "$rc" -eq 2 ]; then
      fail=1
      fail_output="${fail_output}
=== $(echo "$f" | sed "s#$proj/##") ===
$(cat "$tmpout")
"
    fi
    rm -f "$tmpout"
  done <<< "$recent"

  if [ "$fail" -eq 1 ]; then
    echo "" >&2
    echo "🚫 [plain-language-gate] 产物讲人话违规（gen/fill 脚本重生后自动二闸；内部锚点 / [待补充] / 决策号 / 翻译腔不应入对外产物）" >&2
    echo "$fail_output" | head -80 >&2
    echo "" >&2
    echo "   → 修法 1: 按上方行号定位，把内部锚点（文件名 / 决策 N / 第 N 章 / PART / 占位符）改成业务白话（例：A-1 → 「下注弹层」，决策 7 → 删引用）" >&2
    echo "   → 修法 2: 改的是源脚本里的字符串字面量，改完重跑 gen/fill 脚本重生（别直接改产物，下次重生会覆盖）" >&2
    echo "   → 真不适用 → SKIP_PLAIN_LANGUAGE_GATE=1 python3 ...（仅内部审计 / fix-plan 文档，对外产物禁用）" >&2
    echo "" >&2
    _check_block plain-language-gate "${cmd:0:80}"
    return 0
  fi

  _check_clean plain-language-gate "${cmd:0:80}"
}

# ── Sub-checker 3: PRD 自检（gen|update|patch_prd*.py 后扫近 60s，排除 *-scenes/*）─

check_prd_for_bash_recent() {
  local cmd="$1"
  echo "$cmd" | grep -qE '\b(gen|update|patch)_prd[a-zA-Z0-9_-]*\.py\b' || return 0

  _check_skip prd-check-gate SKIP_PRD_CHECK_GATE "$cmd" && return 0

  local skeleton_flag=""
  echo "$cmd" | grep -q 'gen_prd_skeleton\.py' && skeleton_flag="--skeleton"

  local proj="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  local checker="$proj/.claude/skills/prd/scripts/check_prd_md.sh"
  [ ! -f "$checker" ] && return 0

  local recent
  recent=$(find_recent_deliverables 60 --not-path '*-scenes/*' "prd-*.md")
  [ -z "$recent" ] && return 0

  local fail=0
  local fail_output=""

  while IFS= read -r md; do
    [ -z "$md" ] && continue
    local tmpout
    tmpout=$(mktemp)
    if [ -n "$skeleton_flag" ]; then
      bash "$checker" "$md" "$skeleton_flag" > "$tmpout" 2>&1
    else
      bash "$checker" "$md" > "$tmpout" 2>&1
    fi
    local rc=$?
    if [ "$rc" -ne 0 ]; then
      fail=1
      fail_output="${fail_output}
=== $(echo "$md" | sed "s#$proj/##") ===
$(cat "$tmpout")
"
    fi
    rm -f "$tmpout"
  done <<< "$recent"

  if [ "$fail" -eq 1 ]; then
    echo "" >&2
    echo "🚫 [prd-check-gate] PRD 结构自检未通过（gen/update 脚本重生后自动二闸；命名前缀 / 编号闭环 / 占位符残留等基础约束）" >&2
    echo "$fail_output" | head -60 >&2
    echo "" >&2
    if echo "$fail_output" | grep -q "残留占位符"; then
      echo "   💡 占位符残留 = 截图还没回填。截图直接放 deliverables/assets/，md 里写 ![](./assets/xxx.png)" >&2
      echo "      原型截图走 prototype skill 截图脚本（projects/{项目}/scripts/screenshot_*.py）" >&2
      echo "" >&2
    fi
    echo "   → 修法 1: 按上方每条违规定位，修对应内容（补占位截图 / 对齐编号 / 改命名前缀）" >&2
    echo "   → 修法 2: 修完重跑 gen_prd_skeleton.py 重生，或手动 bash .claude/skills/prd/scripts/check_prd_md.sh <prd.md> 确认通过" >&2
    echo "   → 真不适用 → SKIP_PRD_CHECK_GATE=1 ...（仅 false positive，如草稿骨架）" >&2
    echo "" >&2
    _check_block prd-check-gate "${cmd:0:80}"
    return 0
  fi

  _check_clean prd-check-gate "${cmd:0:80}"
}

# ── Sub-checker 4: 渲染 UI 屏内禁注解（build_proto_*/build_imap_*.py 后扫近 60s）─
# 开发注解写进 mockup 渲染屏，开发误读为真实文案。proto/imap 经 build 脚本产出，
# 直接 Write/Edit 被拦，故只有 Bash build 路径能捕到正常产出流。

check_ui_annotation_for_bash_recent() {
  local cmd="$1"
  echo "$cmd" | grep -qE '\bbuild_(proto|imap)_[a-zA-Z0-9_-]*\.py\b' || return 0

  local proj="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  local checker="$proj/scripts/check_ui_annotation.py"
  [ ! -f "$checker" ] && return 0

  _check_skip ui-annotation-gate SKIP_UI_ANNOTATION_GATE "$cmd" && return 0

  local recent
  recent=$(find_recent_deliverables 60 "proto-*.html" "imap-*.html")
  [ -z "$recent" ] && return 0

  local fail=0
  local fail_output=""

  while IFS= read -r f; do
    [ -z "$f" ] && continue
    local tmpout
    tmpout=$(mktemp)
    python3 "$checker" "$f" --strict > "$tmpout" 2>&1
    if [ "$?" -eq 2 ]; then
      fail=1
      fail_output="${fail_output}
=== $(echo "$f" | sed "s#$proj/##") ===
$(cat "$tmpout")
"
    fi
    rm -f "$tmpout"
  done <<< "$recent"

  if [ "$fail" -eq 1 ]; then
    echo "🚫 [ui-annotation-gate] 渲染 UI 屏内写了开发注解，开发会误读为真实产品文案：" >&2
    echo "$fail_output" | head -80 >&2
    echo "" >&2
    echo "   → 原型：删掉注解，屏内只放真实文案" >&2
    echo "   → IMAP：注解移到 mockup 外的 ann-card / flow-note，手机/Web 屏内只放真实文案" >&2
    echo "   → 改源 scene_fns / page_fns 后重 build" >&2
    echo "   → 真不适用（极少数 false positive）：SKIP_UI_ANNOTATION_GATE=1 python3 ..." >&2
    _check_block ui-annotation-gate "${cmd:0:80}"
    return 0
  fi

  _check_clean ui-annotation-gate "${cmd:0:80}"
}

# ── Sub-checker 5: 原型 audit（build_proto_*.py 后扫近 60s）──────────────────
# E 组交互机制 + V 组视觉底线 + slop 三条。与 post-checks 的 pc_prototype_audit 同一 gate，
# 但那条挂在 Write|Edit 上，而 deliverable-source-gate 恰好禁止直接 Write/Edit 脚本化 HTML
# —— 正常产出流只经 Bash build，故本条才是实际触发路径。
check_proto_audit_for_bash() {
  local cmd="$1"
  echo "$cmd" | grep -qE '\bbuild_proto_[a-zA-Z0-9_-]*\.py\b' || return 0

  local proj="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  local checker="$proj/.claude/skills/prototype/scripts/audit_against_baseline.py"
  [ ! -f "$checker" ] && return 0

  _check_skip prototype-audit SKIP_PROTOTYPE_AUDIT "$cmd" && return 0

  local recent
  recent=$(find_recent_deliverables 60 "proto-*.html")
  [ -z "$recent" ] && return 0

  local fail=0
  local fail_output=""

  while IFS= read -r f; do
    [ -z "$f" ] && continue
    local tmpout
    tmpout=$(mktemp)
    python3 "$checker" "$f" > "$tmpout" 2>&1
    if [ "$?" -ne 0 ]; then
      fail=1
      fail_output="${fail_output}
=== $(echo "$f" | sed "s#$proj/##") ===
$(cat "$tmpout")
"
    fi
    rm -f "$tmpout"
  done <<< "$recent"

  if [ "$fail" -eq 1 ]; then
    echo "🚫 [prototype-audit] 原型自检未通过：" >&2
    echo "$fail_output" | head -80 >&2
    echo "" >&2
    echo "   → 改 src/scenes/*.py 或 page_fns 重 build，不直接改 HTML" >&2
    echo "   → E 组（交互机制 / Fill 视觉铁律）见 references/prototype-components.md § E" >&2
    echo "   → V 组（数字排版 / 素材 / 悬浮 / 交互态）见 references/visual-rework-atlas.md，多数可直接换用 crypto-dark.css 的 cx- 组件" >&2
    echo "   → 真不适用 → SKIP_PROTOTYPE_AUDIT=1 python3 ..." >&2
    _check_block prototype-audit "${cmd:0:80}"
    return 0
  fi

  _check_clean prototype-audit "${cmd:0:80}"
}

# ── proto-drift-warn（共享场景库：其他版本产物是否已被本次改动带脏）────────
# warn 不阻断：污染发生在「改共享 src」那一刻，build X 不触碰 Y 的文件，损害是潜伏的，
# build 时没有可精确阻断的时刻。这里按 .proto-lock.json 记的「本版真用到的 src 文件」
# 指纹秒级比对，精确结论走 check_proto_repro.py（全量重建，约 10s）。
# 封版豁免：.proto-lock.json 带 frozen=true 的版本不再比对（已决策不重建，见
# .claude/decisions/implemented/2026-08-25-proto-drift-frozen.md）。
check_proto_drift_for_bash() {
  local cmd="$1"
  echo "$cmd" | grep -qE '\bbuild_proto_v[a-zA-Z0-9_-]*\.py\b' || return 0

  local proj="${CLAUDE_PROJECT_DIR:-$(pwd)}"
  _check_skip proto-drift-warn SKIP_PROTO_DRIFT_WARN "$cmd" && return 0

  local out
  out=$(cd "$proj" && python3 - <<'PY' 2>/dev/null
import hashlib, json, sys
from pathlib import Path

stale = []
for lock in sorted(Path("projects").rglob("deliverables/**/.proto-lock.json")):
    src = None
    for anc in lock.parents:
        cand = anc / "scripts" / "src"
        if cand.is_dir():
            src = cand
            break
    if src is None:
        continue
    try:
        data = json.loads(lock.read_text(encoding="utf-8"))
    except Exception:
        continue
    if data.get("frozen"):
        continue
    changed = set()
    for files in data.get("inputs", {}).values():
        for rel, want in files.items():
            f = src / rel
            if not f.is_file():
                changed.add(rel)
                continue
            got = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
            if got != want:
                changed.add(rel)
    if changed:
        stale.append((data.get("version", lock.parent.name), sorted(changed)[:4]))

for ver, files in stale:
    print(f"{ver}\t{', '.join(files)}")
PY
)
  [ -z "$out" ] && { _check_clean proto-drift-warn "${cmd:0:80}"; return 0; }

  local n
  n=$(echo "$out" | wc -l | tr -d ' ')
  {
    echo ""
    echo "⚠️  [proto-drift-warn] ${n} 个版本的产物可能已不可原样重建"
    echo "$out" | while IFS=$'\t' read -r ver files; do
      echo "   ${ver}：用到的 ${files} 已变，但该版产物是旧的"
    done
    echo ""
    echo "   → 确认是否真漂移: python3 .claude/skills/prototype/scripts/check_proto_repro.py"
    echo "   → 漂移是有意的 → 重建那些版本；无意的 → 按 prototype SKILL §硬规则 14 收窄装配范围"
    echo "   → 真不适用 → SKIP_PROTO_DRIFT_WARN=1"
  } >&2
  command -v log_event >/dev/null && log_event hook proto-drift-warn warn "${cmd:0:80}"
  return 0
}
