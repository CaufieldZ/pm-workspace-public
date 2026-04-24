#!/bin/bash
# workspace-audit 统一审计脚本
# 用法: bash audit.sh [类别编号，逗号分隔] 例如: bash audit.sh 1,2,3,4,5,6
# 不传参数 = 全部执行
# macOS + Linux 兼容

set -o pipefail
cd "$(git rev-parse --show-toplevel)"

CATEGORIES="${1:-1,2,3,4,7}"
GLOBAL_FAIL=0

# ─── 常量 ───
TOKEN_HEAVY_THRESHOLD=12000   # 单 skill 实际加载超过此值标 ⚠️
WORKFLOW_FILE=".claude/rules/pm-workflow.md"

run_cat() { echo "$CATEGORIES" | tr ',' '\n' | grep -qx "$1"; }

# ─── 从 pm-workflow §三 动态提取规范值 ───
# 设备尺寸：从 "375×812px" 格式提取
SPEC_SIZES=$(grep -oE '[0-9]+×[0-9]+px' "$WORKFLOW_FILE" 2>/dev/null | tr '×' '\n' | sed 's/px//' | sort -un)
# 配色：Binance / Arco / Claude Design 三系并存
BINANCE_COLORS=$(grep 'Binance 深色系' "$WORKFLOW_FILE" 2>/dev/null | grep -oE '#[0-9A-Fa-f]{6}')
SEMANTIC_COLORS=$(grep '语义色' "$WORKFLOW_FILE" 2>/dev/null | grep -oE '#[0-9A-Fa-f]{6}')
CD_COLORS=$(grep 'Claude Design 系' "$WORKFLOW_FILE" 2>/dev/null | grep -oE '#[0-9A-Fa-f]{3,6}|#[0-9A-Fa-f]{6}' | head -3)
# 字体：全 skill 统一一套，取 sans body + mono（display serif 不必硬校验）
SPEC_BODY=$(grep -E "^- 正文 sans[：:]" "$WORKFLOW_FILE" 2>/dev/null | grep -oE "'[^']+'" | head -1 | tr -d "'")
SPEC_MONO=$(grep -E "^- 等宽[：:]" "$WORKFLOW_FILE" 2>/dev/null | grep -oE "'[^']+'" | head -1 | tr -d "'")
# 兜底默认值（Claude Design 单套规范）
[ -z "$SPEC_BODY" ] && SPEC_BODY="Noto Sans SC"
[ -z "$SPEC_MONO" ] && SPEC_MONO="JetBrains Mono"

# ─────────────────────────────────────────────
# 类别 1：文件完整性
# ─────────────────────────────────────────────
if run_cat 1; then
  echo "===== 1. 文件完整性 ====="
  echo ""

  # 1.1 SKILL.md 存在性（_shared 白名单：共享资产目录，用 README.md）
  FAIL=0
  for d in .claude/skills/*/; do
    skill=$(basename "$d")
    [ "$skill" = "_shared" ] && continue
    if [ ! -f "$d/SKILL.md" ]; then
      echo "  ❌ $skill 缺少 SKILL.md"
      FAIL=1; GLOBAL_FAIL=1
    fi
  done
  [ -f .claude/skills/_shared/README.md ] || { echo "  ❌ _shared 缺少 README.md"; GLOBAL_FAIL=1; }
  [ "$FAIL" -eq 0 ] && echo "  ✅ 所有 skill 有 SKILL.md（_shared 用 README.md）"

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

  # 1.3 references 引用检查（本地 references/ + _shared/claude-design/ 跨目录）
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
    grep -oE '_shared/claude-design/[A-Za-z0-9_./-]+\.[A-Za-z]+' "$f" 2>/dev/null | sort -u | while read -r ref; do
      target=".claude/skills/$ref"
      if [ ! -f "$target" ]; then
        echo "  ❌ $target 不存在（被 $skill_dir/SKILL.md 引用）"
        echo "1" > "$REF_FAIL_FILE"
      fi
    done
  done
  if [ "$(cat "$REF_FAIL_FILE")" = "0" ]; then
    echo "  ✅ references 引用全部有效（含 _shared/claude-design/ 跨目录）"
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

  # 1.7 Skill 计数一致性（README 等文档中的硬编码数字 vs 实际，排除 _shared 共享资产目录）
  ACTUAL_SKILL_COUNT=$(find .claude/skills/ -maxdepth 1 -type d | tail -n +2 | grep -v '/_shared$' | wc -l | tr -d ' ')
  ACTUAL_PIPELINE=$(grep -rl '^type: *pipeline' .claude/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d ' ')
  ACTUAL_OTHER=$((ACTUAL_SKILL_COUNT - ACTUAL_PIPELINE))
  echo ""
  echo "--- Skill 计数 ---"
  echo "  实际: $ACTUAL_SKILL_COUNT 个 skill（$ACTUAL_PIPELINE pipeline + $ACTUAL_OTHER 其他，_shared 不计入）"
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
  echo "  [语义色 - 成功/失败，跨主题通用]"
  if [ -n "$SEMANTIC_COLORS" ]; then
    echo "$SEMANTIC_COLORS" | while read -r color; do
      [ -z "$color" ] && continue
      count=$(grep -rl "$color" .claude/skills/*/references/ 2>/dev/null | wc -l | tr -d ' ')
      echo "    $color → $count 个 ref 文件"
    done
  else
    echo "    ⚠️  未从 pm-workflow 提取到语义色值"
  fi
  echo "  [Claude Design 系 - ppt/flowchart/arch/Web 后台]"
  if [ -n "$CD_COLORS" ]; then
    echo "$CD_COLORS" | while read -r color; do
      [ -z "$color" ] && continue
      count=$(grep -rl "$color" .claude/skills/ 2>/dev/null | wc -l | tr -d ' ')
      echo "    $color → $count 个文件"
    done
    # 额外扫 --cd-accent 变量使用（不算色值）
    cd_accent_count=$(grep -rl 'var(--cd-accent)' .claude/skills/*/references/ 2>/dev/null | wc -l | tr -d ' ')
    echo "    var(--cd-accent) → $cd_accent_count 个 ref 文件"
  else
    echo "    ⚠️  未从 pm-workflow 提取到 Claude Design 色值"
  fi

  # 语义色（#00B42A 成功 / #F53F3F 失败）允许跨主题使用，不再做主题混用检查

  # 2.3 命名前缀（从 SKILL.md frontmatter 动态读取）
  echo ""
  echo "--- 命名前缀 ---"
  for f in .claude/skills/*/SKILL.md; do
    prefix=$(sed -n 's/^output_prefix: *//p' "$f")
    name=$(sed -n 's/^name: *//p' "$f")
    [ -n "$prefix" ] && echo "  $name → $prefix"
  done

  # 2.4 字体（从 pm-workflow §三 动态提取规范值，单套 Claude Design 套装）
  echo ""
  echo "--- 字体 ---"
  echo "  规范值：正文 '$SPEC_BODY'  等宽 '$SPEC_MONO'（pm-workflow §三）"
  echo ""
  FONT_ISSUES=0
  LEGACY_FONTS='HarmonyOS Sans SC\|Plus Jakarta Sans\|IBM Plex Mono\|DM Sans'
  for f in .claude/skills/*/references/*.css .claude/skills/*/references/*.html; do
    [ -f "$f" ] || continue
    short=$(echo "$f" | sed 's|.claude/skills/||')
    # 检查遗留字体名（已统一到 Claude Design 套装后应清零）
    if grep -q "$LEGACY_FONTS" "$f" 2>/dev/null; then
      echo "    ⚠️  $short 仍引用遗留字体（HarmonyOS/Plus Jakarta/IBM Plex/DM Sans）"
      FONT_ISSUES=$((FONT_ISSUES + 1))
    fi
    body_fonts=$(grep -oE "font-family:[^;]+" "$f" 2>/dev/null | grep -v monospace | grep -v 'JetBrains' || true)
    if [ -n "$body_fonts" ]; then
      # 正文至少带一个 CJK 字体（Noto Sans SC / Noto Serif SC 都算）
      if ! echo "$body_fonts" | grep -qE "Noto (Sans|Serif) SC"; then
        echo "    ⚠️  $short 正文字体缺少 Noto Sans SC / Noto Serif SC"
        echo "       实际: $(echo "$body_fonts" | head -1 | sed 's/font-family://')"
        FONT_ISSUES=$((FONT_ISSUES + 1))
      fi
    fi
  done
  [ "$FONT_ISSUES" -eq 0 ] && echo "    ✅ 字体声明与 Claude Design 规范一致"

  # 2.5 字体栈顺序（CJK 优先）
  echo ""
  echo "--- 字体栈顺序（CJK 优先）---"
  ORDER_FAIL=0
  for f in .claude/skills/*/references/*.css .claude/skills/_shared/claude-design/*.css; do
    [ -f "$f" ] || continue
    short=$(echo "$f" | sed 's|.claude/skills/||')
    # 检查英文字体排在 CJK 前面
    if grep -qE "font-family:.*'Inter'.*'Noto Sans SC'" "$f" 2>/dev/null; then
      echo "    ❌ $short: Inter 在 Noto Sans SC 前面（违反 CJK 优先）"
      ORDER_FAIL=1; GLOBAL_FAIL=1
    fi
    if grep -qE "font-family:.*'Source Serif 4'.*'Noto Serif SC'" "$f" 2>/dev/null; then
      echo "    ❌ $short: Source Serif 4 在 Noto Serif SC 前面（违反 CJK 优先）"
      ORDER_FAIL=1; GLOBAL_FAIL=1
    fi
    if grep -qE "font-family:.*-apple-system.*'Noto Sans SC'" "$f" 2>/dev/null; then
      echo "    ❌ $short: -apple-system 在 Noto Sans SC 前面（违反 CJK 优先）"
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

  # 4.2 触发词重叠（自动检测，Python 处理中文避免 macOS sed/grep 编码问题）
  echo ""
  echo "--- 触发词重叠 ---"
  python3 -c "
import re, os, glob
from collections import defaultdict
trigger_map = defaultdict(list)
for f in sorted(glob.glob('.claude/skills/*/SKILL.md')):
    lines = open(f, encoding='utf-8').readlines()
    name = ''
    in_fm = 0
    desc_lines = []
    for line in lines:
        if line.strip() == '---':
            in_fm += 1
            continue
        if in_fm == 1:
            if line.startswith('name:'):
                name = line.split(':', 1)[1].strip()
            if line.startswith('description:'):
                desc_lines.append(line.split(':', 1)[1])
            elif desc_lines and line.startswith('  '):
                desc_lines.append(line)
        if in_fm >= 2:
            break
    desc = ' '.join(desc_lines)
    triggers = re.findall(r'「([^」]+)」', desc)
    for t in set(triggers):
        trigger_map[t].append(name)
overlap = False
for trigger, owners in sorted(trigger_map.items()):
    if len(owners) > 1:
        print(f'  ⚠️  「{trigger}」被多个 skill 使用: {\", \".join(owners)}')
        overlap = True
if not overlap:
    print('  ✅ 无触发词重叠')
"

  # 4.3 术语一致性（从 context-template 第 5 章 + skill name 动态提取）
  echo ""
  echo "--- 术语一致性 ---"
  TERMS_FILE=$(mktemp)
  # 来源 1：各 skill 的 name 字段中的中文名
  for f in .claude/skills/*/SKILL.md; do
    sname=$(sed -n 's/^name: *//p' "$f")
    # 只取含中文的名称
    if echo "$sname" | grep -qE '[\x{4e00}-\x{9fff}]' 2>/dev/null || echo "$sname" | grep -qP '[\p{Han}]' 2>/dev/null; then
      echo "$sname" >> "$TERMS_FILE"
    fi
  done
  # 来源 2：pm-workflow 中定义的核心术语
  for term in "交互大图" "可交互原型" "行为规格" "页面结构" "场景清单" "需求框架" "拉通自检" "架构图"; do
    echo "$term" >> "$TERMS_FILE"
  done
  sort -u "$TERMS_FILE" -o "$TERMS_FILE"
  while read -r term; do
    [ -z "$term" ] && continue
    count=$(grep -rl "$term" CLAUDE.md .claude/rules/ .claude/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d ' ')
    printf '  「%s」→ %s 个文件\n' "$term" "$count"
  done < "$TERMS_FILE"
  rm -f "$TERMS_FILE"
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
  # 检测 read_context_section.py 路由是否生效
  HAS_CTX_ROUTER=false
  if [ -f "scripts/read_context_section.py" ] && grep -q 'read_context_section' CLAUDE.md 2>/dev/null; then
    HAS_CTX_ROUTER=true
  fi
  CTX_TOKENS=0
  CTX_FULL=0
  SL_TOKENS=0
  for proj_dir in projects/*/; do
    [ -d "$proj_dir" ] || continue
    if [ -f "${proj_dir}context.md" ]; then
      b=$(wc -c < "${proj_dir}context.md" | tr -d ' ')
      t=$((b / 2))
      [ "$t" -gt "$CTX_FULL" ] && CTX_FULL=$t
      if $HAS_CTX_ROUTER && [ "$t" -gt 600 ]; then
        # 按需读取：章节平均 token × 3 次选读
        chapters=$(grep -c '^## ' "${proj_dir}context.md" 2>/dev/null || echo 1)
        [ "$chapters" -eq 0 ] && chapters=1
        avg_chapter=$((t / chapters))
        routed=$((avg_chapter * 3))
        [ "$routed" -gt "$CTX_TOKENS" ] && CTX_TOKENS=$routed
      else
        [ "$t" -gt "$CTX_TOKENS" ] && CTX_TOKENS=$t
      fi
    fi
    if [ -f "${proj_dir}scene-list.md" ]; then
      b=$(wc -c < "${proj_dir}scene-list.md" | tr -d ' ')
      t=$((b / 2))
      [ "$t" -gt "$SL_TOKENS" ] && SL_TOKENS=$t
    fi
  done
  [ "$CTX_TOKENS" -eq 0 ] && CTX_TOKENS=2000
  [ "$SL_TOKENS" -eq 0 ] && SL_TOKENS=500
  BASELINE=$((RULE_TOTAL + CTX_TOKENS + SL_TOKENS))
  if $HAS_CTX_ROUTER && [ "$CTX_FULL" -gt 600 ]; then
    echo "  基础开销 ≈ 规则层(${RULE_TOTAL}) + context(~${CTX_TOKENS}，按需读取) + scene-list(~${SL_TOKENS}) = ~${BASELINE}t"
    echo "  （路由生效：read_context_section.py + CLAUDE.md 规则；全文上限 ${CTX_FULL}t）"
  else
    echo "  基础开销 ≈ 规则层(${RULE_TOTAL}) + context(~${CTX_TOKENS}) + scene-list(~${SL_TOKENS}) = ~${BASELINE}t"
    if [ "$CTX_TOKENS" -gt 2000 ] || [ "$SL_TOKENS" -gt 500 ]; then
      echo "  （以上 context/scene-list 数值为当前项目实测最大值）"
    fi
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
    [ -n "$prefix" ] && [ "$prefix" != "—" ] && [ "$prefix" != "-" ] && VALID_PREFIXES="$VALID_PREFIXES $prefix"
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
      scene_ids=$(grep -oE '[A-Z](-[0-9]+[a-z]?)?' "${proj_dir}scene-list.md" | sort -u)
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
    # 读取项目级豁免列表（.audit-ignore-naming，每行一个 glob）
    ignore_file="${proj_dir}.audit-ignore-naming"
    ignore_patterns=""
    [ -f "$ignore_file" ] && ignore_patterns=$(grep -v '^#' "$ignore_file" 2>/dev/null | grep -v '^$')

    echo "[命名规范]："
    for f in "${proj_dir}deliverables/"*; do
      [ -f "$f" ] || continue
      fname=$(basename "$f")
      case "$fname" in .*) continue ;; esac

      # 项目豁免匹配
      skip=false
      if [ -n "$ignore_patterns" ]; then
        while IFS= read -r pat; do
          [ -z "$pat" ] && continue
          case "$fname" in $pat) skip=true; break ;; esac
        done <<< "$ignore_patterns"
      fi
      $skip && continue

      matched=false
      for prefix in $VALID_PREFIXES; do
        case "$fname" in "${prefix}"*) matched=true; break ;; esac
      done
      if $matched; then
        echo "  ✅ $fname"
      else
        echo "  ⚠️  $fname 不符合 {prefix}-{project}-v{N} 规范（合法前缀: ${VALID_PREFIXES}）"
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

# ─────────────────────────────────────────────
# 类别 12：Scripts 字段存在性
# frontmatter 的 scripts: 映射声明的每个脚本必须在 references/ 或 scripts/ 中存在
# ─────────────────────────────────────────────
if run_cat 12; then
  echo "===== 12. Scripts 字段存在性 ====="
  echo ""
  SCRIPTS_FAIL=0
  for f in .claude/skills/*/SKILL.md; do
    skill_dir=$(dirname "$f")
    skill_name=$(basename "$skill_dir")
    # 提取 frontmatter 内 scripts: 映射块（scripts: 到下一个顶级字段或 ---）
    scripts_block=$(awk '
      /^---$/ { n++; next }
      n==1 && /^scripts:/ { in_scripts=1; next }
      n==1 && in_scripts && /^[a-zA-Z_]+:/ { in_scripts=0 }
      n==1 && in_scripts && /^  [^ ]/ { print }
      n>=2 { exit }
    ' "$f")
    [ -z "$scripts_block" ] && continue

    while IFS= read -r line; do
      # 匹配 "  name.ext: 描述" 提取 name.ext
      script_name=$(echo "$line" | sed -n 's/^  *\([^:]*\):.*/\1/p' | tr -d ' ')
      [ -z "$script_name" ] && continue

      # 按优先级查找：
      # 1) 按原样（处理形如 scripts/xxx.py 这种已带路径的）
      # 2) skill references / skill scripts / 项目根 scripts
      found=false
      for path in "${script_name}" \
                  "${skill_dir}/references/${script_name}" \
                  "${skill_dir}/scripts/${script_name}" \
                  "scripts/${script_name}"; do
        [ -f "$path" ] && { found=true; break; }
      done

      if $found; then
        echo "  ✅ $skill_name → $script_name"
      else
        echo "  ❌ $skill_name 声明了 $script_name 但文件不存在"
        SCRIPTS_FAIL=1
        GLOBAL_FAIL=1
      fi
    done <<< "$scripts_block"
  done
  [ "$SCRIPTS_FAIL" -eq 0 ] && echo ""
  echo ""
fi

echo "===== 审计完成 ====="
exit $GLOBAL_FAIL
