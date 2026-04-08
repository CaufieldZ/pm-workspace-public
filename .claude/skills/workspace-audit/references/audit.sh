#!/bin/bash
# workspace-audit 统一审计脚本
# 用法: bash audit.sh [类别编号，逗号分隔] 例如: bash audit.sh 1,2,3,4,5,6
# 不传参数 = 全部执行
# macOS + Linux 兼容

set -o pipefail
cd "$(git rev-parse --show-toplevel)"

CATEGORIES="${1:-1,2,3,4,5,6}"
GLOBAL_FAIL=0

# ─── 常量 ───
TOKEN_HEAVY_THRESHOLD=12000   # 单 skill 实际加载超过此值标 ⚠️
WORKFLOW_FILE=".claude/rules/pm-workflow.md"

run_cat() { echo "$CATEGORIES" | tr ',' '\n' | grep -qx "$1"; }

# ─── 从 pm-workflow §三 动态提取规范值 ───
# 设备尺寸：从 "375×812px" 格式提取
SPEC_SIZES=$(grep -oE '[0-9]+×[0-9]+px' "$WORKFLOW_FILE" 2>/dev/null | tr '×' '\n' | sed 's/px//' | sort -un)
# 配色：从 §三 提取，Binance 行和 Arco 行各取一行
BINANCE_COLORS=$(grep 'Binance 深色系' "$WORKFLOW_FILE" 2>/dev/null | grep -oE '#[0-9A-Fa-f]{6}')
ARCO_COLORS=$(grep 'Arco Design 浅色系' "$WORKFLOW_FILE" 2>/dev/null | grep -oE '#[0-9A-Fa-f]{6}')
# 字体：从 §三 提取
SPEC_BODY=$(grep "字体：" "$WORKFLOW_FILE" 2>/dev/null | grep -oE "'[^']+'" | head -1 | tr -d "'")
SPEC_MONO=$(grep "字体：" "$WORKFLOW_FILE" 2>/dev/null | grep -oE "'[^']+'" | tail -1 | tr -d "'")
# 兜底默认值
[ -z "$SPEC_BODY" ] && SPEC_BODY="Noto Sans SC"
[ -z "$SPEC_MONO" ] && SPEC_MONO="IBM Plex Mono"

# ─────────────────────────────────────────────
# 类别 1：文件完整性
# ─────────────────────────────────────────────
if run_cat 1; then
  echo "===== 1. 文件完整性 ====="
  echo ""

  # 1.1 SKILL.md 存在性
  FAIL=0
  for d in .claude/skills/*/; do
    skill=$(basename "$d")
    if [ ! -f "$d/SKILL.md" ]; then
      echo "  ❌ $skill 缺少 SKILL.md"
      FAIL=1; GLOBAL_FAIL=1
    fi
  done
  [ "$FAIL" -eq 0 ] && echo "  ✅ 所有 skill 有 SKILL.md"

  # 1.2 frontmatter 完整性
  echo ""
  echo "--- frontmatter ---"
  FM_OK=true
  for f in .claude/skills/*/SKILL.md; do
    skill=$(basename "$(dirname "$f")")
    for field in name description type; do
      grep -q "^${field}:" "$f" || { echo "  ❌ $skill 缺少 frontmatter 字段: $field"; FM_OK=false; GLOBAL_FAIL=1; }
    done
  done
  $FM_OK && echo "  ✅ 所有 skill frontmatter 完整"

  # 1.3 references 引用检查
  echo ""
  echo "--- references 引用 ---"
  REF_FAIL_FILE=$(mktemp)
  echo "0" > "$REF_FAIL_FILE"
  for f in .claude/skills/*/SKILL.md; do
    skill_dir=$(dirname "$f")
    grep -oE 'references/[A-Za-z0-9_.-]+\.[A-Za-z]+' "$f" 2>/dev/null | sort -u | while read -r ref; do
      if [ ! -f "$skill_dir/$ref" ]; then
        echo "  ❌ $skill_dir/$ref 不存在（被 SKILL.md 引用）"
        echo "1" > "$REF_FAIL_FILE"
      fi
    done
  done
  if [ "$(cat "$REF_FAIL_FILE")" = "0" ]; then
    echo "  ✅ references 引用全部有效"
  else
    GLOBAL_FAIL=1
  fi
  rm -f "$REF_FAIL_FILE"

  # 1.4 核心配置文件
  echo ""
  echo "--- 核心配置 ---"
  for f in CLAUDE.md "$WORKFLOW_FILE" .claude/chat-templates/context-template.md; do
    [ -f "$f" ] && echo "  ✅ $f" || { echo "  ❌ $f 缺失"; GLOBAL_FAIL=1; }
  done

  # 1.5 context-template 章节
  echo ""
  CHAPTERS=$(grep -cE '^## ' .claude/chat-templates/context-template.md 2>/dev/null || echo 0)
  echo "  context-template 实际 $CHAPTERS 章："
  grep '^## ' .claude/chat-templates/context-template.md 2>/dev/null | sed 's/^/    /'

  # 1.6 "九章"引用与实际章数一致性
  NINE_REF=$(grep -rl '九章' CLAUDE.md "$WORKFLOW_FILE" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$NINE_REF" -gt 0 ] && [ "$CHAPTERS" -ne 9 ]; then
    echo "  ⚠️  CLAUDE.md/pm-workflow 引用「九章」，但 context-template 实际 $CHAPTERS 章"
    GLOBAL_FAIL=1
  fi

  # 1.7 Skill 计数一致性（README 等文档中的硬编码数字 vs 实际）
  ACTUAL_SKILL_COUNT=$(find .claude/skills/ -maxdepth 1 -type d | tail -n +2 | wc -l | tr -d ' ')
  ACTUAL_PIPELINE=$(grep -rl '^type: *pipeline' .claude/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d ' ')
  ACTUAL_OTHER=$((ACTUAL_SKILL_COUNT - ACTUAL_PIPELINE))
  echo ""
  echo "--- Skill 计数 ---"
  echo "  实际: $ACTUAL_SKILL_COUNT 个 skill（$ACTUAL_PIPELINE pipeline + $ACTUAL_OTHER 其他）"
  # 检查 README 中的硬编码数字
  if [ -f README.md ]; then
    README_COUNT=$(grep -oE 'Skills-[0-9]+' README.md 2>/dev/null | grep -oE '[0-9]+' | head -1)
    if [ -n "$README_COUNT" ] && [ "$README_COUNT" -ne "$ACTUAL_SKILL_COUNT" ]; then
      echo "  ⚠️  README.md badge 写 $README_COUNT 个，实际 $ACTUAL_SKILL_COUNT 个"
      GLOBAL_FAIL=1
    else
      echo "  ✅ README badge 计数一致"
    fi
  fi
  echo ""
fi

# ─────────────────────────────────────────────
# 类别 2：数值与格式一致
# ─────────────────────────────────────────────
if run_cat 2; then
  echo "===== 2. 数值与格式一致 ====="
  echo ""

  # 2.1 设备尺寸（从 pm-workflow §三 动态提取）
  echo "--- 设备尺寸（来源: pm-workflow §三）---"
  if [ -n "$SPEC_SIZES" ]; then
    echo "$SPEC_SIZES" | while read -r size; do
      [ -z "$size" ] && continue
      count=$(grep -rl "$size" .claude/skills/ .claude/rules/ --include='*.md' --include='*.css' --include='*.html' 2>/dev/null | wc -l | tr -d ' ')
      echo "  ${size}px 出现在 $count 个文件"
    done
  else
    echo "  ⚠️  pm-workflow §三 未找到设备尺寸定义"
  fi

  # 2.2 配色 token（从 pm-workflow §三 动态提取）
  echo ""
  echo "--- 配色 token（来源: pm-workflow §三）---"
  echo "  [Binance 深色系 - 前台]"
  if [ -n "$BINANCE_COLORS" ]; then
    echo "$BINANCE_COLORS" | while read -r color; do
      [ -z "$color" ] && continue
      count=$(grep -rl "$color" .claude/skills/*/references/ 2>/dev/null | wc -l | tr -d ' ')
      echo "    $color → $count 个 ref 文件"
    done
  else
    echo "    ⚠️  未从 pm-workflow 提取到 Binance 色值"
  fi
  echo "  [Arco 浅色系 - 后台]"
  if [ -n "$ARCO_COLORS" ]; then
    echo "$ARCO_COLORS" | while read -r color; do
      [ -z "$color" ] && continue
      count=$(grep -rl "$color" .claude/skills/*/references/ 2>/dev/null | wc -l | tr -d ' ')
      echo "    $color → $count 个 ref 文件"
    done
  else
    echo "    ⚠️  未从 pm-workflow 提取到 Arco 色值"
  fi

  # 混用检查（prototype 白名单）
  echo ""
  echo "  [混用检查]"
  MIXED=false
  BINANCE_PATTERN=$(echo "$BINANCE_COLORS" | tr '\n' '|' | sed 's/|$//' | sed 's/#/\\#/g')
  ARCO_PATTERN=$(echo "$ARCO_COLORS" | tr '\n' '|' | sed 's/|$//' | sed 's/#/\\#/g')
  if [ -n "$BINANCE_PATTERN" ] && [ -n "$ARCO_PATTERN" ]; then
    for f in .claude/skills/*/references/*.css .claude/skills/*/references/*.html; do
      [ -f "$f" ] || continue
      case "$f" in *prototype*) continue ;; esac
      has_binance=$(grep -cE "$BINANCE_PATTERN" "$f" 2>/dev/null || true)
      has_arco=$(grep -cE "$ARCO_PATTERN" "$f" 2>/dev/null || true)
      if [ "$has_binance" -gt 0 ] && [ "$has_arco" -gt 0 ]; then
        echo "    ⚠️  $(echo "$f" | sed 's|.claude/skills/||') 混用了 Binance + Arco 色值"
        MIXED=true
      fi
    done
  fi
  $MIXED || echo "    ✅ 无混用（prototype 双色系已白名单）"

  # 2.3 命名前缀（从 SKILL.md frontmatter 动态读取）
  echo ""
  echo "--- 命名前缀 ---"
  for f in .claude/skills/*/SKILL.md; do
    prefix=$(sed -n 's/^output_prefix: *//p' "$f")
    name=$(sed -n 's/^name: *//p' "$f")
    [ -n "$prefix" ] && echo "  $name → $prefix"
  done

  # 2.4 字体（从 pm-workflow §三 动态提取规范值）
  echo ""
  echo "--- 字体 ---"
  echo "  规范值：正文 '$SPEC_BODY'  等宽 '$SPEC_MONO'（pm-workflow §三）"
  echo ""
  FONT_ISSUES=0
  for f in .claude/skills/*/references/*.css .claude/skills/*/references/*.html; do
    [ -f "$f" ] || continue
    short=$(echo "$f" | sed 's|.claude/skills/||')
    body_fonts=$(grep -oE "font-family:[^;]+" "$f" 2>/dev/null | grep -v monospace | grep -v 'IBM Plex\|JetBrains' || true)
    if [ -n "$body_fonts" ]; then
      if ! echo "$body_fonts" | grep -q "$SPEC_BODY"; then
        echo "    ⚠️  $short 正文字体缺少 $SPEC_BODY"
        echo "       实际: $(echo "$body_fonts" | head -1 | sed 's/font-family://')"
        FONT_ISSUES=$((FONT_ISSUES + 1))
      fi
    fi
    mono_fonts=$(grep -oE "font-family:[^;]+" "$f" 2>/dev/null | grep -E 'monospace|Mono' || true)
    if [ -n "$mono_fonts" ]; then
      if echo "$mono_fonts" | grep -q 'JetBrains' && ! echo "$mono_fonts" | grep -q "$SPEC_MONO"; then
        echo "    ℹ️  $short 等宽用 JetBrains Mono（规范为 $SPEC_MONO）"
        FONT_ISSUES=$((FONT_ISSUES + 1))
      fi
    fi
  done
  [ "$FONT_ISSUES" -eq 0 ] && echo "    ✅ 字体声明与规范一致"

  # 2.5 字体栈顺序（CJK 优先）
  echo ""
  echo "--- 字体栈顺序（CJK 优先）---"
  ORDER_FAIL=0
  for f in .claude/skills/*/references/*.css; do
    [ -f "$f" ] || continue
    short=$(echo "$f" | sed 's|.claude/skills/||')
    # 检查 body font-family 中英文字体是否排在 CJK 前面
    if grep -q "font-family:.*'DM Sans'.*'Noto Sans SC'" "$f" 2>/dev/null; then
      echo "    ❌ $short: DM Sans 在 Noto Sans SC 前面（违反 CJK 优先）"
      ORDER_FAIL=1; GLOBAL_FAIL=1
    fi
    if grep -q "font-family:.*-apple-system.*'Noto Sans SC'" "$f" 2>/dev/null; then
      echo "    ❌ $short: -apple-system 在 Noto Sans SC 前面（违反 CJK 优先）"
      ORDER_FAIL=1; GLOBAL_FAIL=1
    fi
    if grep -q "font-family:.*'Helvetica Neue'.*'Noto Sans SC'" "$f" 2>/dev/null; then
      echo "    ❌ $short: Helvetica Neue 在 Noto Sans SC 前面（违反 CJK 优先）"
      ORDER_FAIL=1; GLOBAL_FAIL=1
    fi
  done
  [ "$ORDER_FAIL" -eq 0 ] && echo "    ✅ 字体栈顺序正确（CJK 优先）"
  echo ""
fi

# ─────────────────────────────────────────────
# 类别 3：依赖与链路
# ─────────────────────────────────────────────
if run_cat 3; then
  echo "===== 3. 依赖与链路 ====="
  echo ""

  # 3.1 构建 registry
  REGISTRY_FILE=$(mktemp)
  for f in .claude/skills/*/SKILL.md; do
    fm=$(awk '/^---$/{n++; next} n==1{print} n>=2{exit}' "$f")
    name=$(echo "$fm" | sed -n 's/^name: *//p')
    type=$(echo "$fm" | sed -n 's/^type: *//p')
    deps=$(echo "$fm" | sed -n 's/^depends_on: *//p')
    consumed=$(echo "$fm" | sed -n 's/^consumed_by: *//p')
    pos=$(echo "$fm" | sed -n 's/^pipeline_position: *//p')
    [ -n "$name" ] && echo "$name|$type|$deps|$consumed|$pos" >> "$REGISTRY_FILE"
  done

  echo "--- Registry ---"
  column -t -s'|' < "$REGISTRY_FILE"

  # 3.2 依赖闭环
  echo ""
  echo "--- 依赖闭环检查 ---"
  DEP_FAIL_FILE=$(mktemp)
  echo "0" > "$DEP_FAIL_FILE"
  while IFS='|' read -r name type deps consumed pos; do
    echo "$deps" | tr -d '[]' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | while read -r dep; do
      [ -z "$dep" ] && continue
      dep_consumed=$(grep "^${dep}|" "$REGISTRY_FILE" | cut -d'|' -f4)
      if ! echo "$dep_consumed" | grep -q "$name"; then
        echo "  ⚠️  $name depends_on $dep，但 $dep 的 consumed_by 不包含 $name"
        echo "1" > "$DEP_FAIL_FILE"
      fi
    done
  done < "$REGISTRY_FILE"
  if [ "$(cat "$DEP_FAIL_FILE")" = "0" ]; then
    echo "  ✅ 依赖闭环完整"
  fi
  rm -f "$DEP_FAIL_FILE"

  # 3.3 pipeline 排序
  echo ""
  echo "--- Pipeline 排序 ---"
  grep '|pipeline|' "$REGISTRY_FILE" | sort -t'|' -k5 -n | while IFS='|' read -r name type deps consumed pos; do
    echo "  $pos → $name"
  done

  # 3.4 孤立 skill
  echo ""
  echo "--- 孤立 skill ---"
  ORPHAN=0
  while IFS='|' read -r name type deps consumed pos; do
    [ "$type" != "pipeline" ] && continue
    [ "$name" = "scene-list" ] && continue
    deps_clean=$(echo "$deps" | tr -d '[] ')
    consumed_clean=$(echo "$consumed" | tr -d '[] ')
    if [ -z "$deps_clean" ] && [ -z "$consumed_clean" ]; then
      echo "  ⚠️  $name 是 pipeline 型但无依赖也无消费者"
      ORPHAN=1
    fi
  done < "$REGISTRY_FILE"
  [ "$ORPHAN" -eq 0 ] && echo "  ✅ 无孤立 pipeline skill"

  rm -f "$REGISTRY_FILE"
  echo ""
fi

# ─────────────────────────────────────────────
# 类别 4：规则冲突
# ─────────────────────────────────────────────
if run_cat 4; then
  echo "===== 4. 规则冲突 ====="
  echo ""

  # 4.1 context.md 章节引用一致性
  echo "--- context.md 章节引用一致性 ---"
  echo "[CLAUDE.md]："
  grep -oE '第 *[0-9一二三四五六七八九十]+ *章' CLAUDE.md 2>/dev/null | sort -u | sed 's/^/  /' || echo "  （无引用）"
  echo "[pm-workflow]："
  grep -oE '第 *[0-9一二三四五六七八九十]+ *章' "$WORKFLOW_FILE" 2>/dev/null | sort -u | sed 's/^/  /' || echo "  （无引用）"
  echo "[context-template 实际章节]："
  grep '^## ' .claude/chat-templates/context-template.md 2>/dev/null | sed 's/^/  /'

  # 4.2 触发词重叠
  echo ""
  echo "--- 触发词重叠 ---"
  for f in .claude/skills/*/SKILL.md; do
    name=$(sed -n 's/^name: *//p' "$f")
    desc=$(awk '/^---$/{n++; next} n==1 && /^description:/{sub(/^description: *>/,""); p=1; print; next} n==1 && p && /^  /{print; next} {p=0} n>=2{exit}' "$f" | head -3 | tr '\n' ' ' | sed 's/  */ /g')
    echo "  [$name] $desc"
  done
  echo ""
  echo "  >> 人工检查：是否有两个 skill 被同一个指令同时触发"

  # 4.3 术语一致性
  echo ""
  echo "--- 术语一致性 ---"
  check_term() {
    local label="$1"
    local count
    count=$(grep -rl "$label" CLAUDE.md .claude/rules/ .claude/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d ' ')
    printf '  「%s」→ %s 个文件\n' "$label" "$count"
  }
  check_term "交互大图"
  check_term "可交互原型"
  check_term "行为规格"
  check_term "场景清单"
  check_term "拉通自检"
  echo ""
fi

# ─────────────────────────────────────────────
# 类别 5：Token 预算
# ─────────────────────────────────────────────
if run_cat 5; then
  echo "===== 5. Token 预算 ====="
  echo ""

  # 5.1 规则层
  echo "--- 规则层（每 session 必加载）---"
  RULE_TOTAL=0
  for f in CLAUDE.md "$WORKFLOW_FILE" .claude/rules/soul.md; do
    if [ -f "$f" ]; then
      bytes=$(wc -c < "$f" | tr -d ' ')
      tokens=$((bytes / 2))
      echo "  $f — ~${tokens}t"
      RULE_TOTAL=$((RULE_TOTAL + tokens))
    fi
  done
  echo "  规则层合计: ~${RULE_TOTAL}t"

  # 5.2 单 skill 加载成本
  echo ""
  echo "--- 单 Skill 加载成本 ---"
  echo "  （必读 = 模型必须读 | 按需 = 条件读取 | 执行 = Python/拼接，模型不读）"
  echo ""
  for d in .claude/skills/*/; do
    skill=$(basename "$d")
    skill_file="$d/SKILL.md"
    skill_bytes=$(wc -c < "$skill_file" 2>/dev/null | tr -d ' ')
    skill_tokens=$((skill_bytes / 2))

    must_bytes=0
    ondemand_bytes=0
    exec_bytes=0

    if [ -d "${d}references" ]; then
      for f in "${d}references/"*; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        fbytes=$(wc -c < "$f" | tr -d ' ')

        # 分类：骨架脚本/CSS/JS → 执行类（模型不读）
        case "$fname" in
          gen_*_skeleton.py|*.css|*.js)
            exec_bytes=$((exec_bytes + fbytes))
            continue
            ;;
        esac

        # 分类：SKILL.md 中标记为"执行类"或"模型无需读取"的文件（双向匹配）
        if grep -q "${fname}.*执行类\|${fname}.*模型无需读取\|${fname}.*模型不读\|执行类.*${fname}\|模型无需读取.*${fname}\|模型不读.*${fname}" "$skill_file" 2>/dev/null; then
          exec_bytes=$((exec_bytes + fbytes))
          continue
        fi

        # 分类：检查 SKILL.md 是否标记为按需
        is_ondemand=false
        if grep -A5 '按需' "$skill_file" 2>/dev/null | grep -q "$fname"; then
          is_ondemand=true
        elif grep -q "仅.*${fname}\|才读.*${fname}" "$skill_file" 2>/dev/null; then
          is_ondemand=true
        fi
        if $is_ondemand; then
          ondemand_bytes=$((ondemand_bytes + fbytes))
        else
          must_bytes=$((must_bytes + fbytes))
        fi
      done
    fi

    must_tokens=$((must_bytes / 2))
    ondemand_tokens=$((ondemand_bytes / 2))
    exec_tokens=$((exec_bytes / 2))

    actual=$((skill_tokens + must_tokens))

    flag=""
    [ "$actual" -gt "$TOKEN_HEAVY_THRESHOLD" ] && flag=" ⚠️ 偏重"

    echo "  $skill — SKILL.md ~${skill_tokens}t | 必读 ~${must_tokens}t | 按需 ~${ondemand_tokens}t | 执行 ~${exec_tokens}t | 实际≈${actual}t${flag}"
  done

  # 5.3 全链路预算估算（从实际项目文件测量）
  echo ""
  echo "--- 全链路 session 预算估算 ---"
  # 尝试从实际项目测量 context.md 和 scene-list.md 大小
  CTX_TOKENS=0
  SL_TOKENS=0
  for proj_dir in projects/*/; do
    [ -d "$proj_dir" ] || continue
    if [ -f "${proj_dir}context.md" ]; then
      b=$(wc -c < "${proj_dir}context.md" | tr -d ' ')
      t=$((b / 2))
      [ "$t" -gt "$CTX_TOKENS" ] && CTX_TOKENS=$t
    fi
    if [ -f "${proj_dir}scene-list.md" ]; then
      b=$(wc -c < "${proj_dir}scene-list.md" | tr -d ' ')
      t=$((b / 2))
      [ "$t" -gt "$SL_TOKENS" ] && SL_TOKENS=$t
    fi
  done
  # 无项目时给兜底估值
  [ "$CTX_TOKENS" -eq 0 ] && CTX_TOKENS=2000
  [ "$SL_TOKENS" -eq 0 ] && SL_TOKENS=500
  BASELINE=$((RULE_TOTAL + CTX_TOKENS + SL_TOKENS))
  echo "  基础开销 ≈ 规则层(${RULE_TOTAL}) + context(~${CTX_TOKENS}) + scene-list(~${SL_TOKENS}) = ~${BASELINE}t"
  if [ "$CTX_TOKENS" -gt 2000 ] || [ "$SL_TOKENS" -gt 500 ]; then
    echo "  （以上 context/scene-list 数值为当前项目实测最大值）"
  fi
  echo "  单步 = 基础开销 + skill 实际加载（见上表）"
  echo "  Opus/Sonnet (1M) → 全链路无压力"
  echo "  GLM 5.1/Kimi K2.5 (200K) → 建议单 session ≤ $((200000 / BASELINE)) 步"
  echo "  ≤128K 模型 → 每个产出物独立 session"
  echo ""
fi

# ─────────────────────────────────────────────
# 类别 6：产出物一致性
# ─────────────────────────────────────────────
if run_cat 6; then
  echo "===== 6. 产出物一致性 ====="
  echo ""

  # 从 SKILL.md frontmatter 动态构建合法前缀列表
  VALID_PREFIXES=""
  for f in .claude/skills/*/SKILL.md; do
    prefix=$(sed -n 's/^output_prefix: *//p' "$f" | tr -d ' ')
    [ -n "$prefix" ] && VALID_PREFIXES="$VALID_PREFIXES $prefix"
  done
  # 加上 audit- 前缀（workspace-audit 产出）
  VALID_PREFIXES="$VALID_PREFIXES audit-"

  # 6.0 context.md 九章结构验证
  EXPECTED_CHAPTERS="1 2 3 4 5 6 7 8 9"
  for proj_dir in projects/*/; do
    [ -d "$proj_dir" ] || continue
    ctx="${proj_dir}context.md"
    [ -f "$ctx" ] || continue
    proj=$(basename "$proj_dir")
    chapters=$(grep -oE '^## [0-9]+' "$ctx" 2>/dev/null | grep -oE '[0-9]+' | sort -n | tr '\n' ' ' | sed 's/ $//')
    expected=$(echo $EXPECTED_CHAPTERS)
    if [ "$chapters" = "$expected" ]; then
      echo "  ✅ $proj/context.md 九章完整"
    else
      echo "  ⚠️  $proj/context.md 章节: [$chapters] 期望: [$expected]"
    fi
  done
  echo ""

  HAS_PROJECT=false
  for proj_dir in projects/*/; do
    [ -d "${proj_dir}deliverables" ] || continue
    HAS_PROJECT=true
    proj=$(basename "$proj_dir")
    echo "--- 项目: $proj ---"

    # 6.1 场景编号
    if [ -f "${proj_dir}scene-list.md" ]; then
      echo "[场景编号]："
      scene_ids=$(grep -oE '[A-Z]-[0-9]+[a-z]?' "${proj_dir}scene-list.md" | sort -u)
      scene_count=$(echo "$scene_ids" | grep -c '.' || echo 0)
      echo "  scene-list.md 中有 $scene_count 个编号"

      for f in "${proj_dir}deliverables/"*.html "${proj_dir}deliverables/"*.md; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        missing=""
        while read -r sid; do
          [ -z "$sid" ] && continue
          grep -q "$sid" "$f" || missing="$missing $sid"
        done <<< "$scene_ids"
        if [ -n "$missing" ]; then
          echo "  ⚠️  $fname 缺少编号:$missing"
        else
          echo "  ✅ $fname 编号完整"
        fi
      done
    fi

    # 6.2 文件命名规范（从 frontmatter 动态构建合法前缀）
    echo "[命名规范]："
    for f in "${proj_dir}deliverables/"*; do
      [ -f "$f" ] || continue
      fname=$(basename "$f")
      case "$fname" in .*) continue ;; esac
      matched=false
      for prefix in $VALID_PREFIXES; do
        case "$fname" in "${prefix}"*) matched=true; break ;; esac
      done
      if $matched; then
        echo "  ✅ $fname"
      else
        echo "  ⚠️  $fname 不符合 {prefix}-{project}-v{N} 规范（合法前缀: $VALID_PREFIXES）"
      fi
    done
    echo ""
  done

  if ! $HAS_PROJECT; then
    echo "  ⏭️ 无活跃项目，跳过产出物一致性检查"
    echo ""
  fi
fi

# ─────────────────────────────────────────────
# 类别 7：SKILL_TABLE 一致性
# ─────────────────────────────────────────────
if run_cat 7; then
  echo "===== 7. SKILL_TABLE 一致性 ====="
  echo ""

  WC_FILE="workspace-context.md"
  if [ ! -f "$WC_FILE" ]; then
    echo "  ⚠️  workspace-context.md 不存在，跳过"
  else
    TABLE_FAIL=0

    # 提取 SKILL_TABLE 区域（从 "| Skill | 类型" 到下一个 "---" 或 "###"）
    TABLE_SECTION=$(sed -n '/^| Skill.*类型/,/^[#-]/p' "$WC_FILE" | grep '^|' | grep -v '^| Skill' | grep -v '^|[-]')

    for f in .claude/skills/*/SKILL.md; do
      fm=$(awk '/^---$/{n++; next} n==1{print} n>=2{exit}' "$f")
      name=$(echo "$fm" | sed -n 's/^name: *//p' | head -1)
      type=$(echo "$fm" | sed -n 's/^type: *//p')
      fmt=$(echo "$fm" | sed -n 's/^output_format: *//p')

      [ -z "$name" ] && continue
      # skill-creator 的 name 含模板占位符，取目录名
      case "$name" in *"{"*) name=$(basename "$(dirname "$f")") ;; esac

      table_line=$(echo "$TABLE_SECTION" | grep "| *${name} " | head -1)
      if [ -z "$table_line" ]; then
        echo "  ❌ $name 在 SKILL.md 中存在但 SKILL_TABLE 中缺失"
        TABLE_FAIL=1; GLOBAL_FAIL=1
        continue
      fi

      # 比对 type
      if [ -n "$type" ] && ! echo "$table_line" | grep -q "$type"; then
        echo "  ❌ $name type: frontmatter=$type vs table"
        TABLE_FAIL=1; GLOBAL_FAIL=1
      fi
      # 比对 output_format（跳过 对话内/.md 这类多模式 skill）
      if [ -n "$fmt" ] && [ "$fmt" != ".md" ] || [ "$type" != "tool" ]; then
        if [ -n "$fmt" ] && ! echo "$table_line" | grep -q "$fmt"; then
          # 允许 .md 和 对话内 互换（workspace-audit 等）
          if ! echo "$table_line" | grep -q '对话内'; then
            echo "  ⚠️  $name output_format: frontmatter=$fmt"
            TABLE_FAIL=1
          fi
        fi
      fi
    done

    # 反向检查：仅在 SKILL_TABLE 范围内
    echo "$TABLE_SECTION" | while IFS='|' read -r _ tname _rest; do
      tname=$(echo "$tname" | tr -d ' ')
      [ -z "$tname" ] && continue
      if [ ! -f ".claude/skills/$tname/SKILL.md" ]; then
        echo "  ❌ SKILL_TABLE 有 $tname 但 SKILL.md 不存在"
        echo "1" > /tmp/audit_table_fail 2>/dev/null
      fi
    done
    [ -f /tmp/audit_table_fail ] && { TABLE_FAIL=1; GLOBAL_FAIL=1; rm -f /tmp/audit_table_fail; }

    [ "$TABLE_FAIL" -eq 0 ] && echo "  ✅ SKILL_TABLE 与 frontmatter 一致"
  fi
  echo ""
fi

echo "===== 审计完成 ====="
exit $GLOBAL_FAIL
