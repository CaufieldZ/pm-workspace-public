#!/bin/bash
# workspace-audit 统一审计脚本
# 用法: bash audit.sh [类别编号，逗号分隔] 例如: bash audit.sh 1,2,3,4,5,6
# 不传参数 = 默认类别（1,2,3,4,7,12,13,14,15,16,17,19,20,21,23,25，缺 5/6/18/22/24）
# 全部 21 类：bash audit.sh 1,2,3,4,5,6,7,12,13,14,15,16,17,18,19,20,21,22,23,24,25
#   （编号跳 8-11，那四类是 Phase 2 模型推理，不在本脚本内）
# macOS + Linux 兼容

set -o pipefail
ROOT="$(git rev-parse --show-toplevel)" || { echo "错误：不在 git 仓库内，无法定位工区根目录" >&2; exit 1; }
cd "$ROOT" || { echo "错误：无法进入工区根目录 $ROOT" >&2; exit 1; }

# skill-log: 完成率埋点（trap EXIT 按退出码 emit completed / failed）
source ".claude/hooks/lib/log.sh" 2>/dev/null
trap '_rc=$?; log_event skill "workspace-audit" "$([ $_rc -eq 0 ] && echo completed || echo failed)" 2>/dev/null' EXIT

CATEGORIES="${1:-1,2,3,4,7,12,13,14,15,16,17,19,20,21,23,25}"
GLOBAL_FAIL=0

# ─── 常量 ───
TOKEN_HEAVY_THRESHOLD=20000   # 单 skill 实际加载超过此值标 ⚠️（SKILL.md 本体 + 真必读 references）
WORKFLOW_FILE=".claude/runbooks/pm-methodology.md"
ARTIFACT_FILE=".claude/runbooks/artifact-conventions.md"
TOKENS_FILE=".claude/skills/_shared/claude-design/tokens.css"

run_cat() { echo "$CATEGORIES" | tr ',' '\n' | grep -qx "$1"; }

# ─── 从 tokens.css @audit-spec 注释块提取规范值（机器可解析 SSOT）───
AUDIT_SPEC=$(awk '/@audit-spec/,/\*\//' "$TOKENS_FILE" 2>/dev/null)
# 设备尺寸：mobile-device: 375x812
SPEC_SIZES=$(echo "$AUDIT_SPEC" | grep -oE 'mobile-device: *[0-9]+x[0-9]+' | head -1 | grep -oE '[0-9]+' | sort -un)
# 配色：Binance / Arco / Claude Design 三系
BINANCE_COLORS=$(echo "$AUDIT_SPEC" | grep -E '^\s*\*?\s*theme-ex:' | grep -oE '#[0-9A-Fa-f]{6}')
SEMANTIC_COLORS=$(echo "$AUDIT_SPEC" | grep -E '^\s*\*?\s*theme-semantic:' | grep -oE '#[0-9A-Fa-f]{6}')
CD_COLORS=$(echo "$AUDIT_SPEC" | grep -E '^\s*\*?\s*theme-cd:' | grep -oE '#[0-9A-Fa-f]{6}' | head -3)
# 字体：全 skill 统一一套，取 sans body + mono
SPEC_BODY=$(echo "$AUDIT_SPEC" | grep -oE 'font-body: *"[^"]+"' | grep -oE '"[^"]+"' | tr -d '"')
SPEC_MONO=$(echo "$AUDIT_SPEC" | grep -oE 'font-mono: *"[^"]+"' | grep -oE '"[^"]+"' | tr -d '"')
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
  # 进程替换喂 while，循环跑在主 shell，REF_FAIL 直接传出（免 mktemp flag-file 子壳传值绕路）
  REF_FAIL=0
  for f in .claude/skills/*/SKILL.md; do
    skill_dir=$(dirname "$f")
    while read -r ref; do
      if [ ! -f "$skill_dir/$ref" ]; then
        echo "  ❌ $skill_dir/$ref 不存在（被 SKILL.md 引用）"
        REF_FAIL=1
      fi
    done < <(grep -oE '(^|[^/A-Za-z0-9_-])references/[A-Za-z0-9_.-]+\.[A-Za-z]+' "$f" 2>/dev/null | sed -E 's|^[^r]*||' | sort -u)
    while read -r ref; do
      target=".claude/skills/$ref"
      if [ ! -f "$target" ]; then
        echo "  ❌ $target 不存在（被 $skill_dir/SKILL.md 引用）"
        REF_FAIL=1
      fi
    done < <(grep -oE '_shared/claude-design/[A-Za-z0-9_./-]+\.[A-Za-z]+' "$f" 2>/dev/null | sort -u)
  done
  if [ "$REF_FAIL" -eq 0 ]; then
    echo "  ✅ references 引用全部有效（含 _shared/claude-design/ 跨目录）"
  else
    GLOBAL_FAIL=1
  fi

  # 1.4 核心配置文件
  echo ""
  echo "--- 核心配置 ---"
  for f in CLAUDE.md "$WORKFLOW_FILE"; do
    [ -f "$f" ] && echo "  ✅ $f" || { echo "  ❌ $f 缺失"; GLOBAL_FAIL=1; }
  done

  # 1.7 Skill 计数一致性（README 等文档中的硬编码数字 vs 实际，排除 _shared 共享资产目录）
  ACTUAL_SKILL_COUNT=$(find .claude/skills/ -maxdepth 1 -type d | tail -n +2 | grep -v '/_shared$' | wc -l | tr -d ' ')
  ACTUAL_PIPELINE=$(grep -rl '^type: *pipeline' .claude/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d ' ')
  ACTUAL_OTHER=$((ACTUAL_SKILL_COUNT - ACTUAL_PIPELINE))
  echo ""
  echo "--- Skill 计数 ---"
  echo "  实际: $ACTUAL_SKILL_COUNT 个 skill（${ACTUAL_PIPELINE} pipeline + $ACTUAL_OTHER 其他，_shared 不计入）"
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

  # 三个扫描 scope 各预扫一次（替代每个 token 一次全树 grep -rl，N 遍 → 3 遍）
  SCOPE_SIZES=$(find .claude/skills .claude/runbooks -type f \( -name '*.md' -o -name '*.css' -o -name '*.html' \) 2>/dev/null)
  SCOPE_REFS=$(find .claude/skills/*/references -type f 2>/dev/null)
  SCOPE_SKILLS=$(find .claude/skills -type f 2>/dev/null)
  # 含子串的文件数（保留原 grep -rl 子串语义）；0 命中 → 规范值无人引用，warn（spec 漂了）
  # 用法：spec_count <token> <scope-filelist>
  spec_count() { echo "$2" | xargs grep -l "$1" 2>/dev/null | wc -l | tr -d ' '; }

  # 2.1 设备尺寸（从 tokens.css @audit-spec 提取）
  echo "--- 设备尺寸（来源: tokens.css @audit-spec）---"
  if [ -n "$SPEC_SIZES" ]; then
    echo "$SPEC_SIZES" | while read -r size; do
      [ -z "$size" ] && continue
      count=$(spec_count "$size" "$SCOPE_SIZES")
      echo "  ${size}px 出现在 $count 个文件"
      [ "$count" -eq 0 ] && echo "    ⚠️  规范尺寸 ${size}px 无任何文件引用（@audit-spec 可能已漂）"
    done
  else
    echo "  ⚠️  tokens.css @audit-spec 未找到设备尺寸定义"
  fi

  # 2.2 配色 token（从 tokens.css @audit-spec 提取）
  echo ""
  echo "--- 配色 token（来源: tokens.css @audit-spec）---"
  echo "  [Binance 深色系 - 前台]"
  if [ -n "$BINANCE_COLORS" ]; then
    echo "$BINANCE_COLORS" | while read -r color; do
      [ -z "$color" ] && continue
      count=$(spec_count "$color" "$SCOPE_REFS")
      echo "    $color → $count 个 ref 文件"
    done
  else
    echo "    ⚠️  未从 tokens.css @audit-spec 提取到 Binance 色值"
  fi
  echo "  [语义色 - 成功/失败，跨主题通用]"
  if [ -n "$SEMANTIC_COLORS" ]; then
    echo "$SEMANTIC_COLORS" | while read -r color; do
      [ -z "$color" ] && continue
      count=$(spec_count "$color" "$SCOPE_REFS")
      echo "    $color → $count 个 ref 文件"
    done
  else
    echo "    ⚠️  未从 tokens.css @audit-spec 提取到语义色值"
  fi
  echo "  [Claude Design 系 - ppt/flowchart/arch/Web 后台]"
  if [ -n "$CD_COLORS" ]; then
    echo "$CD_COLORS" | while read -r color; do
      [ -z "$color" ] && continue
      count=$(spec_count "$color" "$SCOPE_SKILLS")
      echo "    $color → $count 个文件"
    done
    # 额外扫 --cd-accent 变量使用（不算色值）
    cd_accent_count=$(spec_count 'var(--cd-accent)' "$SCOPE_REFS")
    echo "    var(--cd-accent) → $cd_accent_count 个 ref 文件"
  else
    echo "    ⚠️  未从 tokens.css @audit-spec 提取到 Claude Design 色值"
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

  # 2.4 字体（从 tokens.css @audit-spec 提取规范值，单套 Claude Design 套装）
  echo ""
  echo "--- 字体 ---"
  echo "  规范值：正文 '$SPEC_BODY'  等宽 '$SPEC_MONO'（tokens.css @audit-spec）"
  echo ""
  FONT_ISSUES=0
  LEGACY_FONTS='HarmonyOS Sans SC\|Plus Jakarta Sans\|IBM Plex Mono\|DM Sans'
  # ppt 纯 deck 三字体规范：元信息栈用 IBM Plex Mono（SKILL.md §纯 deck 默认三字体），非遗留 → 从其检查中剔除
  LEGACY_FONTS_PPT='HarmonyOS Sans SC\|Plus Jakarta Sans\|DM Sans'
  for f in .claude/skills/*/assets/*.css .claude/skills/*/assets/*.html; do
    [ -f "$f" ] || continue
    short=$(echo "$f" | sed 's|.claude/skills/||')
    # 检查遗留字体名（已统一到 Claude Design 套装后应清零）
    case "$short" in
      ppt/*) legacy_pat="$LEGACY_FONTS_PPT"; legacy_label="HarmonyOS/Plus Jakarta/DM Sans" ;;
      *)     legacy_pat="$LEGACY_FONTS";     legacy_label="HarmonyOS/Plus Jakarta/IBM Plex/DM Sans" ;;
    esac
    if grep -q "$legacy_pat" "$f" 2>/dev/null; then
      echo "    ⚠️  $short 仍引用遗留字体（$legacy_label）"
      FONT_ISSUES=$((FONT_ISSUES + 1))
    fi
    body_fonts=$(grep -oE "font-family:[^;]+" "$f" 2>/dev/null | grep -v monospace | grep -v 'JetBrains' | grep -vE 'var\(--(cd-|font-|fc-|arch-)?mono\)' || true)
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
  for f in .claude/skills/*/assets/*.css .claude/skills/_shared/claude-design/*.css; do
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

  # 2.6 同文件字体栈一致性（focus 英文 fallback：焕新时遗漏会导致一处 Inter 一处 Poppins）
  echo ""
  echo "--- 同文件字体栈一致性 ---"
  INCON_FAIL=0
  for f in .claude/skills/*/assets/*.css; do
    [ -f "$f" ] || continue
    short=$(echo "$f" | sed 's|.claude/skills/||')
    # 提取所有 font-family 声明里的英文 sans fallback（匹配单引号和双引号两种写法）
    en_fonts=$(grep -oE "font-family:[^;]+" "$f" 2>/dev/null | \
      grep -oE "['\"](Inter|Poppins|Plus Jakarta Sans|DM Sans|HarmonyOS Sans SC|Roboto|Space Grotesk|Fraunces)['\"]" | \
      tr -d '"'"'" | sort -u)
    [ -z "$en_fonts" ] && continue
    n=$(echo "$en_fonts" | wc -l | tr -d ' ')
    if [ "$n" -gt 1 ]; then
      echo "    ❌ $short 混用 $n 种英文 fallback：$(echo "$en_fonts" | tr '\n' ' ')"
      INCON_FAIL=1; GLOBAL_FAIL=1
    fi
  done
  [ "$INCON_FAIL" -eq 0 ] && echo "    ✅ 各 CSS 同文件内英文 fallback 一致"
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
        echo "  ⚠️  $name depends_on ${dep}，但 ${dep} 的 consumed_by 不包含 $name"
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

  # 4.1 章节引用扫描（规则文件里的「第 N 章」裸引用，信息性）
  echo "--- 章节引用扫描 ---"
  echo "[CLAUDE.md]："
  grep -oE '第 *[0-9一二三四五六七八九十]+ *章' CLAUDE.md 2>/dev/null | sort -u | sed 's/^/  /' || echo "  （无引用）"
  echo "[pm-methodology + artifact-conventions]："
  grep -oE '第 *[0-9一二三四五六七八九十]+ *章' "$WORKFLOW_FILE" "$ARTIFACT_FILE" 2>/dev/null | grep -oE '第 *[0-9一二三四五六七八九十]+ *章' | sort -u | sed 's/^/  /' || echo "  （无引用）"

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

  # 4.3 术语一致性（从 skill name + artifact-conventions 核心术语动态提取）
  echo ""
  echo "--- 术语一致性 ---"
  TERMS_FILE=$(mktemp)
  # 来源 1：各 skill 的 name 字段中的中文名
  for f in .claude/skills/*/SKILL.md; do
    sname=$(sed -n 's/^name: *//p' "$f")
    # 只取含中文的名称（LC_ALL=C 把任意非 ASCII 字节判为「含中文」，跨 BSD/GNU grep 一致；
    # 避免 \x{} ERE / \p{Han} PCRE —— BSD grep 两者都不支持）
    if echo "$sname" | LC_ALL=C grep -q '[^ -~]' 2>/dev/null; then
      echo "$sname" >> "$TERMS_FILE"
    fi
  done
  # 来源 2：artifact-conventions.md 中定义的核心术语
  for term in "交互大图" "可交互原型" "行为规格" "页面结构" "场景清单" "拉通自检" "架构图"; do
    echo "$term" >> "$TERMS_FILE"
  done
  sort -u "$TERMS_FILE" -o "$TERMS_FILE"
  while read -r term; do
    [ -z "$term" ] && continue
    count=$(grep -rl "$term" CLAUDE.md .claude/runbooks/ .claude/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d ' ')
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
  for f in CLAUDE.md "$WORKFLOW_FILE"; do
    if [ -f "$f" ]; then
      bytes=$(wc -c < "$f" | tr -d ' ')
      tokens=$((bytes / 2))
      echo "  $f — ~${tokens}t"
      RULE_TOTAL=$((RULE_TOTAL + tokens))
    fi
  done
  echo "  规则层合计: ~${RULE_TOTAL}t"
  echo ""

  # 5.1b 体积棘轮（逐文件上限，红灯）—— 上限清单 scripts/rule-budgets.manifest.json
  echo "--- 体积棘轮 ---"
  if python3 scripts/check_rule_volume.py --strict; then
    :
  else
    echo "  ❌ 规则层体积破棘轮上限（上方红灯）"
    GLOBAL_FAIL=1
  fi

  # 5.2 单 skill 加载成本
  echo ""
  echo "--- 单 Skill 加载成本 ---"
  echo "  （必读 = 模型必须读 | 按需 = 条件读取 | 执行 = Python/拼接，模型不读）"
  echo ""
  for d in .claude/skills/*/; do
    skill=$(basename "$d")
    [ "$skill" = "_shared" ] && continue
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
        # 「按需」section 边界识别：
        #   起点：`### 按需...` H3 / `**按需...**` bold 段头
        #   终点：下一个 H1-H3 / 下一个 `**必读|执行类|可选...**` bold 段头 / EOF
        # 段内提到 fname = 按需。
        # 备用：「仅.../才读...」措辞 / SKILL.md 全文 0 引用 = 按需
        is_ondemand=false
        ondemand_section=$(awk '
          /^### *按需/ || /^\*\*按需[^*]*\*\*/ { flag=1; next }
          /^#{1,3} / { flag=0 }
          /^\*\*(必读|执行类|可选|强制)/ { flag=0 }
          flag
        ' "$skill_file" 2>/dev/null)
        if [ -n "$ondemand_section" ] && echo "$ondemand_section" | grep -q "$fname"; then
          is_ondemand=true
        elif grep -q "仅.*${fname}\|才读.*${fname}" "$skill_file" 2>/dev/null; then
          is_ondemand=true
        elif ! grep -q "$fname" "$skill_file" 2>/dev/null; then
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
  # 检测 read_prd_section.py 路由是否生效
  HAS_ROUTER=false
  if [ -f ".claude/skills/prd/scripts/read_prd_section.py" ] && grep -q 'read_prd_section' CLAUDE.md 2>/dev/null; then
    HAS_ROUTER=true
  fi
  BASE_TOKENS=0
  BASE_FULL=0
  SL_TOKENS=0
  for base in projects/*/prd-*-baseline.md projects/*/*/prd-*-baseline.md; do
    [ -f "$base" ] || continue
    proj_dir="$(dirname "$base")/"
    [ -d "$proj_dir" ] || continue
    b=$(wc -c < "$base" | tr -d ' ')
    t=$((b / 2))
    [ "$t" -gt "$BASE_FULL" ] && BASE_FULL=$t
    if $HAS_ROUTER && [ "$t" -gt 600 ]; then
      # 按需读取：章节平均 token × 3 次选读
      chapters=$(grep -c '^## ' "$base" 2>/dev/null || echo 1)
      [ "$chapters" -eq 0 ] && chapters=1
      avg_chapter=$((t / chapters))
      routed=$((avg_chapter * 3))
      [ "$routed" -gt "$BASE_TOKENS" ] && BASE_TOKENS=$routed
    else
      [ "$t" -gt "$BASE_TOKENS" ] && BASE_TOKENS=$t
    fi
    if [ -f "${proj_dir}scene-list.md" ]; then
      b=$(wc -c < "${proj_dir}scene-list.md" | tr -d ' ')
      t=$((b / 2))
      [ "$t" -gt "$SL_TOKENS" ] && SL_TOKENS=$t
    fi
  done
  [ "$BASE_TOKENS" -eq 0 ] && BASE_TOKENS=2000
  [ "$SL_TOKENS" -eq 0 ] && SL_TOKENS=500
  BASELINE=$((RULE_TOTAL + BASE_TOKENS + SL_TOKENS))
  if $HAS_ROUTER && [ "$BASE_FULL" -gt 600 ]; then
    echo "  基础开销 ≈ 规则层(${RULE_TOTAL}) + baseline(~${BASE_TOKENS}，按需读取) + scene-list(~${SL_TOKENS}) = ~${BASELINE}t"
    echo "  （路由生效：read_prd_section.py + CLAUDE.md 规则；全文上限 ${BASE_FULL}t）"
  else
    echo "  基础开销 ≈ 规则层(${RULE_TOTAL}) + baseline(~${BASE_TOKENS}) + scene-list(~${SL_TOKENS}) = ~${BASELINE}t"
    if [ "$BASE_TOKENS" -gt 2000 ] || [ "$SL_TOKENS" -gt 500 ]; then
      echo "  （以上 baseline/scene-list 数值为当前项目实测最大值）"
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

  HAS_PROJECT=false
  # 项目发现：以 scene-list.md 为标记（单模型下每个非 EXEMPT 项目都有 scene-list）
  for sl in projects/*/scene-list.md projects/*/*/scene-list.md; do
    [ -f "$sl" ] || continue
    proj_dir="$(dirname "$sl")/"
    [ -d "${proj_dir}deliverables" ] || continue
    HAS_PROJECT=true
    proj=$(basename "$proj_dir")
    echo "--- 项目: $proj ---"

    # 6.1 场景编号
    # 只对需要铺全场景的产出物前缀做全覆盖校验：scene-list / imap / proto / prd / tc
    # 其他前缀（mrd-review / flow 子流程 / comp / report / ppt / handbook / arch / `_*` 研究预览）
    # 本就不该铺全场景，跳过报告（避免 liquidity 研究材料、queen mrd、leaderboard flow 等误报）
    # bspec / pspec 前缀已废弃（行为规格 / 页面结构并入 PRD），老项目历史文件不再做覆盖校验
    SCENE_COVER_RE='^(scene-list|imap|proto|prd|tc)-'
    if [ -f "${proj_dir}scene-list.md" ]; then
      echo "[场景编号]："
      # 只从 markdown 表格第一列提取编号，避免正文里的 WEB / Platform C / API / URL 等大写词被误当编号
      # 支持的格式：A / A-1 / A-1a / M0 / F-0a / B-1a/b/c（斜杠展开为多条）
      scene_ids=$(awk -F'|' '
        /^\| / {
          s=$2; gsub(/^ +| +$/, "", s)
          if (s ~ /^[A-Z][0-9]*(-[0-9]+)?[a-z]\/[a-z](\/[a-z])*$/) {
            # 展开 B-1a/b/c 形式
            n=split(s, parts, "/")
            head=parts[1]; sub(/[a-z]$/, "", head)
            for (i=1;i<=n;i++) print head parts[i]
          } else {
            print s
          }
        }' "${proj_dir}scene-list.md" \
        | grep -E '^[A-Z][0-9]*(-[0-9]+[a-z]?)?$' \
        | sort -u)
      scene_count=$(echo "$scene_ids" | grep -c '.' || echo 0)
      echo "  scene-list.md 中有 $scene_count 个编号"

      for f in "${proj_dir}deliverables/"*.html "${proj_dir}deliverables/"*.md; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        # 文件头 audit-skip 注释豁免（独立工具规格等不走 pipeline 的产物在头部声明）
        if head -5 "$f" 2>/dev/null | grep -q 'audit-skip'; then
          echo "  ↪️  ${fname}（头部 audit-skip 豁免）"
          continue
        fi
        # 类别豁免：只校验 pipeline 主路径产出物
        if ! echo "$fname" | grep -qE "$SCENE_COVER_RE"; then
          continue
        fi
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

      # 文件头 audit-skip 注释豁免（独立工具规格等不走 pipeline 的产物在头部声明）
      if [ -f "$f" ] && head -5 "$f" 2>/dev/null | grep -q 'audit-skip'; then
        echo "  ↪️  ${fname}（头部 audit-skip 豁免）"
        continue
      fi

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
      # frontmatter name 含模板占位符（如 `{skill-name}`）时回退取目录名
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

    # 反向检查：仅在 SKILL_TABLE 范围内。进程替换喂 while → 循环在主 shell，
    # TABLE_FAIL 直接传出（替代固定名 /tmp/audit_table_fail 跨进程传 flag：并发 race + 裸 /tmp 不跨平台）
    while IFS='|' read -r _ tname _rest; do
      tname=$(echo "$tname" | tr -d ' ')
      [ -z "$tname" ] && continue
      if [ ! -f ".claude/skills/$tname/SKILL.md" ]; then
        echo "  ❌ SKILL_TABLE 有 $tname 但 SKILL.md 不存在"
        TABLE_FAIL=1; GLOBAL_FAIL=1
      fi
    done < <(echo "$TABLE_SECTION")

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
      # 1) 按原样（处理形如 scripts/xxx.py 或 assets/xxx.css 这种已带路径的）
      # 2) skill references / skill scripts / skill assets / 项目根 scripts
      # 用 -e 同时接受文件和目录（Python 子包形式如 humanize/ 也算合法 script）
      found=false
      for path in "${script_name}" \
                  "${skill_dir}/references/${script_name}" \
                  "${skill_dir}/scripts/${script_name}" \
                  "${skill_dir}/assets/${script_name}" \
                  "scripts/${script_name}"; do
        [ -e "$path" ] && { found=true; break; }
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

# ─────────────────────────────────────────────
# 类别 13：scripts/lib/ import 链路冒烟测试
# 共享模块能被 skill 脚本正确 import
# ─────────────────────────────────────────────
if run_cat 13; then
  echo "===== 13. scripts/lib/ import 链路 ====="
  echo ""
  LIB_FAIL=0

  # 13.1 __init__.py 存在
  if [ ! -f scripts/lib/__init__.py ]; then
    echo "  ❌ scripts/lib/__init__.py 缺失（Python 包标记）"
    LIB_FAIL=1; GLOBAL_FAIL=1
  else
    echo "  ✅ scripts/lib/__init__.py 存在"
  fi

  # 13.2 各 lib 模块独立 import
  for mod in confluence html_builder; do
    if [ ! -f "scripts/lib/${mod}.py" ]; then
      continue
    fi
    if python3 -c "import sys; sys.path.insert(0,'scripts'); from lib.${mod} import *" 2>/dev/null; then
      echo "  ✅ lib.${mod} import OK"
    else
      echo "  ❌ lib.${mod} import 失败"
      LIB_FAIL=1; GLOBAL_FAIL=1
    fi
  done

  # 13.3 skill update base 继承链
  # （所有 update_*_base 已删；HtmlPatcher / update_proto_base / update_ppt_base 已死）

  # 13.4 gen 脚本 import 链路（改了 import 后还能跑）
  for gen in \
    ".claude/skills/flowchart/scripts/gen_flow_base.py:render_flowchart"; do
    gpath="${gen%%:*}"
    gfunc="${gen##*:}"
    [ -f "$gpath" ] || continue
    gdir=$(dirname "$gpath")
    if python3 -c "
import sys; sys.path.insert(0,'$gdir')
mod = __import__('$(basename "${gpath}" .py)')
assert hasattr(mod, '$gfunc'), 'missing $gfunc'
" 2>/dev/null; then
      echo "  ✅ $(basename "$gpath"):${gfunc} import OK"
    else
      echo "  ❌ $(basename "$gpath"):${gfunc} import 失败"
      LIB_FAIL=1; GLOBAL_FAIL=1
    fi
  done

  echo ""
fi

# ─────────────────────────────────────────────
# 类别 14：三件套纯洁性（Anthropic Progressive Disclosure 规范）
# scripts/ 仅 .py/.sh/.js · references/ 仅 .md · assets/ 不含 .md
# ─────────────────────────────────────────────
if run_cat 14; then
  echo "===== 14. 三件套纯洁性 ====="
  echo ""
  TIER_FAIL=0

  # references/ 不允许非 .md（_shared/ 排除：跨 skill 共享资产，不是 skill）
  bad_refs=$(find .claude/skills -path '*/references/*' -type f -not -name '*.md' -not -path '*/_shared/*' 2>/dev/null)
  if [ -n "$bad_refs" ]; then
    echo "  ❌ references/ 混入非 .md 文件（应去 scripts/ 或 assets/）："
    echo "$bad_refs" | sed 's/^/     /'
    TIER_FAIL=1; GLOBAL_FAIL=1
  else
    echo "  ✅ references/ 纯净（仅 .md）"
  fi

  # assets/ 不允许 .md
  bad_assets=$(find .claude/skills -path '*/assets/*.md' -not -path '*/_shared/*' 2>/dev/null)
  if [ -n "$bad_assets" ]; then
    echo "  ❌ assets/ 混入 .md 文件（应去 references/）："
    echo "$bad_assets" | sed 's/^/     /'
    TIER_FAIL=1; GLOBAL_FAIL=1
  else
    echo "  ✅ assets/ 纯净（无 .md）"
  fi

  # scripts/ 不允许 .md（lib/ 子目录排除：__init__.py 等基础设施）
  bad_scripts=$(find .claude/skills -path '*/scripts/*.md' -not -path '*/_shared/*' 2>/dev/null)
  if [ -n "$bad_scripts" ]; then
    echo "  ❌ scripts/ 混入 .md 文件（应去 references/）："
    echo "$bad_scripts" | sed 's/^/     /'
    TIER_FAIL=1; GLOBAL_FAIL=1
  else
    echo "  ✅ scripts/ 纯净（无 .md）"
  fi

  echo ""
fi

# ─────────────────────────────────────────────
# 类别 16：SKILL.md 内部结构合规（skill-conventions.md §SKILL.md 内部章节标准）
# 章节顺序 + 命名 + 行数约束 + 同义词禁用
# ─────────────────────────────────────────────
if run_cat 16; then
  echo "===== 16. SKILL.md 内部结构合规 ====="
  echo ""
  STRUCT_FAIL=0
  SKILL_MAX_LINES=500

  # 标准章节名（命中 = 合规）
  REQUIRED_SECTIONS=(
    "## 触发与定位"
    "## 硬规则（FAIL 即拦）"
    "## 核心输出规范"
    "## 执行步骤"
    "## 自检清单"
  )
  # 同义词黑名单（pattern|建议，命中 pattern 行 = 警告）
  # 注意：grep -E 后单独成行的 ## 标题才算（避免误伤正文）
  FORBIDDEN_ALIASES=(
    "^## 定位$|改为 ## 触发与定位"
    "^## 作用$|改为 ## 触发与定位"
    "^## 何时用|改为 ## 触发与定位"
    "^## API 速查表$|改为 ## API 速查"
    "^## 踩坑速查|改为 ## API 速查"
    "^## 自检$|改为 ## 自检清单"
    "^## 输出格式$|改为 ## 核心输出规范"
    "^## 注意$|改为 ## 注意事项"
  )
  # 8 条 alias 合并成一个 ERE，per-skill 先一次粗筛；命中（罕见）才展开逐条定位
  ALIAS_COMBINED=$(IFS='|'; printf '%s' "${FORBIDDEN_ALIASES[*]%%|*}")

  for d in .claude/skills/*/; do
    skill=$(basename "$d")
    [ "$skill" = "_shared" ] && continue
    skillmd="$d/SKILL.md"
    [ ! -f "$skillmd" ] && continue

    # 跳过 deprecated 类型
    grep -qE '^type:\s*deprecated\s*$' "$skillmd" && continue

    # 一次性读入内存，固定串章节检查走 bash 内建（零 fork），替代每章一次 grep
    content=$(<"$skillmd")
    skill_header_printed=0
    lines=$(wc -l < "$skillmd" | tr -d ' ')
    type_val=$(awk '/^type:/{print $2}' "$skillmd")

    print_skill_header() {
      [ "$skill_header_printed" -eq 0 ] && echo "  ⚠️  $skill ($lines 行):" && skill_header_printed=1
    }

    # A. 行数上限
    if [ "$lines" -gt "$SKILL_MAX_LINES" ]; then
      print_skill_header
      echo "     ⚠️  $lines 行 > ${SKILL_MAX_LINES}（应拆 references/{skill}-{topic}.md）"
      STRUCT_FAIL=1
    fi

    # B. 必需章节缺失（tool 类放宽）
    if [ "$type_val" = "tool" ]; then
      check_sections=("## 触发与定位" "## 执行步骤")
    else
      check_sections=("${REQUIRED_SECTIONS[@]}")
    fi
    for sec in "${check_sections[@]}"; do
      if [[ "$content" != *"$sec"* ]]; then
        print_skill_header
        echo "     ⚠️  缺章节: $sec"
        STRUCT_FAIL=1
      fi
    done

    # C. § 2「改脚本前 30 秒」（有 scripts/ 才要求）
    scripts_count=$(find "$d/scripts" -maxdepth 1 -type f \( -name "*.py" -o -name "*.sh" \) 2>/dev/null | wc -l | tr -d ' ')
    if [ "$scripts_count" -gt 0 ] && [[ "$content" != *"## 改脚本前 30 秒"* ]]; then
      print_skill_header
      echo "     ⚠️  有 scripts/ 但缺章节: ## 改脚本前 30 秒（hook 轻量入口）"
      STRUCT_FAIL=1
    fi

    # D. 同义词黑名单（合并粗筛，命中才逐条定位）
    if grep -qE "$ALIAS_COMBINED" "$skillmd"; then
      for entry in "${FORBIDDEN_ALIASES[@]}"; do
        pat="${entry%%|*}"
        hint="${entry##*|}"
        if grep -qE "$pat" "$skillmd"; then
          hit=$(grep -E "$pat" "$skillmd" | head -1)
          print_skill_header
          echo "     ⚠️  禁用同义词 \"$hit\" → $hint"
          STRUCT_FAIL=1
        fi
      done
    fi
  done

  if [ "$STRUCT_FAIL" -eq 0 ]; then
    echo "  ✅ 所有 SKILL.md 结构合规（章节齐全 / 命名标准 / 行数达标）"
  else
    echo ""
    echo "  参考：.claude/runbooks/skill-conventions.md §SKILL.md 内部章节标准"
  fi

  echo ""
fi

# ─────────────────────────────────────────────
# 类别 15：Hooks 健康度
# bash 语法 + BSD sed 兼容性 + 引用脚本存在性 + settings.json 登记一致
# ─────────────────────────────────────────────
if run_cat 15; then
  echo "===== 15. Hooks 健康度 ====="
  echo ""
  HOOKS_FAIL=0

  HOOK_DIR=".claude/hooks"
  if [ ! -d "$HOOK_DIR" ]; then
    echo "  ⏭️  $HOOK_DIR 不存在，跳过"
    echo ""
  else
    # 15.1 bash -n 语法
    echo "--- bash -n 语法 ---"
    SYNTAX_FAIL=0
    for f in "$HOOK_DIR"/*.sh "$HOOK_DIR"/lib/*.sh; do
      [ -f "$f" ] || continue
      if ! bash -n "$f" 2>/dev/null; then
        echo "  ❌ $(echo "$f" | sed "s|$HOOK_DIR/||") 语法错误"
        bash -n "$f" 2>&1 | head -2 | sed 's/^/      /'
        SYNTAX_FAIL=1; HOOKS_FAIL=1; GLOBAL_FAIL=1
      fi
    done
    [ "$SYNTAX_FAIL" -eq 0 ] && echo "  ✅ 所有 hook 脚本语法通过"

    # 15.2 BSD sed 分隔符/alternation 冲突
    # 匹配 `'s|...(a|b|c)...|' ` — 分隔符 | 与 alternation | 打架
    # 2026-05-01 pre-scripts-first.sh 翻车同款 bug
    echo ""
    echo "--- BSD sed 分隔符冲突 lint ---"
    SED_FAIL=0
    SED_HITS=$(grep -nE "sed[^'\"]*['\"]s\|[^'\"]*\([^)|]+\|[^)|]+(\|[^)|]+)*\)" "$HOOK_DIR"/*.sh "$HOOK_DIR"/lib/*.sh 2>/dev/null)
    if [ -n "$SED_HITS" ]; then
      echo "  ❌ 发现 sed 用 | 做分隔符且 pattern 含 (a|b|c) alternation（BSD sed 会报 'parentheses not balanced'）："
      echo "$SED_HITS" | sed 's/^/     /'
      echo "     修法：换分隔符，如 sed 's#...(a|b|c)...#\\1#'"
      SED_FAIL=1; HOOKS_FAIL=1; GLOBAL_FAIL=1
    fi
    [ "$SED_FAIL" -eq 0 ] && echo "  ✅ 无 BSD sed 分隔符冲突"

    # 15.3 引用脚本存在性
    # 用 python3 抽更稳：捕获 ${PROJECT_DIR}/path 或 $VAR/path 或裸 .claude/... / scripts/... 路径
    echo ""
    echo "--- 引用脚本存在性 ---"
    REF_FAIL=0
    REFS=$(python3 - "$HOOK_DIR" <<'PYEOF'
import os, re, sys, glob
sys.stdout.reconfigure(newline='\n')  # Windows: 防 \r 残留导致 bash [ -f ] 误判
hook_dir = sys.argv[1]
refs = set()
# 捕获：${VAR[:-default]}/relpath  或  $VAR/relpath  或  裸 .claude/.../.sh|.py|.js  或  scripts/xxx.sh|py|js
patterns = [
    re.compile(r'\$\{(?:CLAUDE_PROJECT_DIR|PROJECT_DIR|ROOT)(?::-[^}]*)?\}/([A-Za-z0-9_./-]+\.(?:sh|py|js))'),
    re.compile(r'\$(?:CLAUDE_PROJECT_DIR|PROJECT_DIR|ROOT)/([A-Za-z0-9_./-]+\.(?:sh|py|js))'),
    re.compile(r'(?<![A-Za-z0-9_/-])(\.claude/(?:skills|hooks)/[A-Za-z0-9_./-]+\.(?:sh|py|js))'),
    re.compile(r'(?<![A-Za-z0-9_/-])(scripts/[A-Za-z0-9_./-]+\.(?:sh|py|js))'),
]
for f in sorted(glob.glob(f'{hook_dir}/*.sh')):
    src = open(f, encoding='utf-8', errors='ignore').read()
    for p in patterns:
        for m in p.findall(src):
            # 过滤含通配符 / 路径拼接占位 / tmp 的
            if any(c in m for c in ['*', '${', '$(', '$']): continue
            if m.startswith('tmp/') or '/tmp/' in m: continue
            refs.add(m)
for r in sorted(refs):
    print(r)
PYEOF
)
    for ref in $REFS; do
      if [ ! -f "$ref" ]; then
        echo "  ❌ hook 引用但文件不存在：${ref}"
        REF_FAIL=1; HOOKS_FAIL=1; GLOBAL_FAIL=1
      fi
    done
    [ "$REF_FAIL" -eq 0 ] && echo "  ✅ hook 引用的脚本均存在（$(echo "$REFS" | wc -l | tr -d ' ') 条）"

    # 15.4 settings.json hooks 节注册一致性（路径式 + 外部命令式）
    echo ""
    echo "--- settings.json 注册一致性 ---"
    SETTINGS=".claude/settings.json"
    REG_FAIL=0
    if [ -f "$SETTINGS" ] && command -v python3 >/dev/null 2>&1; then
      # 路径式 hook：抽 .claude/hooks/*.sh 引用
      # 外部命令式 hook：抽首个 token 非路径的命令名（如 "dippy --claude" → dippy）
      REG_OUTPUT=$(python3 -c "
import json, re, sys
sys.stdout.reconfigure(newline='\n')
try:
    data = json.load(open('$SETTINGS', encoding='utf-8'))
except Exception: raise SystemExit
paths = set()
ext_cmds = set()
hooks = data.get('hooks', {})
for events in hooks.values():
    for entry in events:
        for h in entry.get('hooks', []):
            cmd = h.get('command', '').strip()
            if not cmd: continue
            m = re.search(r'\.claude/hooks/[a-zA-Z0-9_.-]+\.sh', cmd)
            if m:
                paths.add(m.group(0))
                continue
            # 非路径式：取首 token；含 / 或 \$ 视为路径式（跳过 — 已被上面 .claude/hooks 抓或属其他类型）
            first = cmd.split()[0]
            if first and '/' not in first and '\$' not in first:
                ext_cmds.add(first)
for p in sorted(paths):
    print('PATH:' + p)
for c in sorted(ext_cmds):
    print('CMD:' + c)
")
      REGISTERED=$(echo "$REG_OUTPUT" | grep '^PATH:' | sed 's/^PATH://')
      EXT_CMDS=$(echo "$REG_OUTPUT" | grep '^CMD:' | sed 's/^CMD://')

      # 注册的路径式 hook 都该存在
      for r in $REGISTERED; do
        if [ ! -f "$r" ]; then
          echo "  ❌ settings.json 注册了 $r 但文件不存在"
          REG_FAIL=1; HOOKS_FAIL=1; GLOBAL_FAIL=1
        fi
      done
      # 注册的外部命令都该在 PATH 中可执行
      EXT_OK=0
      EXT_FAIL_CMDS=""
      for c in $EXT_CMDS; do
        if command -v "$c" >/dev/null 2>&1; then
          EXT_OK=$((EXT_OK + 1))
        else
          echo "  ❌ settings.json 注册了外部命令 '$c' 但 PATH 中找不到"
          EXT_FAIL_CMDS="$EXT_FAIL_CMDS $c"
          REG_FAIL=1; HOOKS_FAIL=1; GLOBAL_FAIL=1
        fi
      done
      # 存在的都该注册（孤儿 hook 检测）
      # 豁免：pre-commit-* 前缀属于 git pre-commit 显式调用，非 Claude PreToolUse/PostToolUse
      for f in "$HOOK_DIR"/*.sh; do
        base=$(basename "$f")
        rel=".claude/hooks/$base"
        case "$base" in
          pre-commit-*) continue ;;
        esac
        if ! echo "$REGISTERED" | grep -qx "$rel"; then
          echo "  ⚠️  $rel 存在但 settings.json 未注册（孤儿 hook）"
          # warn 不 fail（可能是主动禁用的 hook）
        fi
      done

      # 三方对账表
      PATH_COUNT=$(echo "$REGISTERED" | grep -c '\.sh$' || true)
      EXT_COUNT=$(echo "$EXT_CMDS" | grep -c '.' || true)
      PHY_COUNT=$(ls "$HOOK_DIR"/*.sh 2>/dev/null | wc -l | tr -d ' ')
      echo ""
      echo "  📊 settings × 物理文件 × 外部命令 对账："
      echo "     settings 注册：${PATH_COUNT} 路径式 + ${EXT_COUNT} 外部命令"
      echo "     物理 hook 文件：${PHY_COUNT} 个 .sh"
      echo "     外部命令可执行：${EXT_OK}/${EXT_COUNT}"
      [ "$REG_FAIL" -eq 0 ] && echo "  ✅ 三方一致"
    else
      echo "  ⏭️  settings.json 或 python3 不可用，跳过"
    fi

    # 15.5 pre-commit trigger 覆盖 hooks 层
    echo ""
    echo "--- pre-commit trigger 覆盖 ---"
    if [ -f .githooks/pre-commit ]; then
      if grep -q '\\.claude/hooks/' .githooks/pre-commit; then
        echo "  ✅ .githooks/pre-commit 已覆盖 .claude/hooks/ 变更"
      else
        echo "  ❌ .githooks/pre-commit trigger 未包含 ^\\.claude/hooks/，改 hook 不会触发防腐审计"
        HOOKS_FAIL=1; GLOBAL_FAIL=1
      fi
    fi

    # 15.6 hook 产出物 glob 与 SKILL.md output_prefix 一致性
    # SSOT：SKILL.md frontmatter output_prefix。消费方：hook case glob / find -name 模式。
    # 防 SKILL.md 改 output_prefix 后 hook 里 case 分支没跟着改的 SSOT 漂移。
    # 已知合法豁免：旧前缀别名（向后兼容）+ 非产出物用途前缀
    echo ""
    echo "--- hook 产出物 glob vs SKILL.md output_prefix ---"
    GLOB_FAIL=0
    # 合法前缀 stem（从 SKILL.md 派生 + 去尾 -）
    VALID_PREFIX_STEMS=""
    for f in .claude/skills/*/SKILL.md; do
      prefix=$(sed -n 's/^output_prefix: *//p' "$f" | tr -d ' ')
      case "$prefix" in
        none|—|-|"") continue ;;
      esac
      stem=$(echo "$prefix" | sed 's/-$//')
      VALID_PREFIX_STEMS="$VALID_PREFIX_STEMS $stem"
    done
    # 豁免：① 旧前缀别名（hook 同时认新旧做向后兼容，如 architecture-*.html 别名 arch-*.html）
    #       ② 非产出物前缀（audit- = workspace-audit 产出但 SKILL.md output_prefix 为 none；fix-plan- = 修复方案豁免类；
    #          cold-read- = cold_read.py 产出的冷读盲点清单，cold-read-gate hook 只 glob 查存在，非 hook 自身产出）
    EXEMPT_STEMS="architecture interaction prototype audit fix-plan cold-read"
    # 抽 hook 里产出物 glob 前缀（形如 xxx-*.md / xxx-*.html），跳过注释行
    HOOK_GLOB_STEMS=$(grep -hE "^[^#]*[a-z][a-z0-9-]+-\*+[a-z0-9-]*\.(md|html)" "$HOOK_DIR"/*.sh 2>/dev/null \
      | grep -oE "[a-z][a-z0-9-]+-\*+[a-z0-9-]*\.(md|html)" \
      | sed -E 's/-\*.*//' \
      | sort -u)
    ORPHAN_PREFIXES=""
    for stem in $HOOK_GLOB_STEMS; do
      [ -z "$stem" ] && continue
      # 跳过豁免
      if echo "$EXEMPT_STEMS" | grep -qw "$stem"; then continue; fi
      # 跳过合法
      if echo "$VALID_PREFIX_STEMS" | grep -qw "$stem"; then continue; fi
      ORPHAN_PREFIXES="$ORPHAN_PREFIXES $stem"
    done
    if [ -z "$ORPHAN_PREFIXES" ]; then
      hook_count=$(echo "$HOOK_GLOB_STEMS" | tr ' ' '\n' | grep -v '^$' | wc -l | tr -d ' ')
      exempt_count=$(echo "$EXEMPT_STEMS" | tr ' ' '\n' | wc -l | tr -d ' ')
      echo "  ✅ hook 产出物 glob 前缀全部合法（${hook_count} 类前缀，含 $exempt_count 类已知豁免）"
    else
      echo "  ❌ 发现 hook 用了 SKILL.md 未声明且非已知豁免的产出物前缀（SSOT 漂移）："
      for p in $ORPHAN_PREFIXES; do
        matching=$(grep -lE "\\b$p-\\*+[a-z0-9-]*\\.(md|html)" "$HOOK_DIR"/*.sh 2>/dev/null \
          | xargs -I {} basename {} | tr '\n' ',' | sed 's/,$//')
        echo "     $p- → $matching"
      done
      echo "     → 修法：① SKILL.md 加 output_prefix 声明，或 ② audit.sh §15.6 EXEMPT_STEMS 加豁免"
      GLOB_FAIL=1; HOOKS_FAIL=1; GLOBAL_FAIL=1
    fi

    # 15.7 hooks/README.md 清单 drift（gen_hooks_readme.py 自动生成，须与当前 hooks 一致）
    echo ""
    echo "--- hooks/README.md 清单 drift ---"
    if [ -f scripts/gen_hooks_readme.py ] && command -v python3 >/dev/null 2>&1; then
      if python3 scripts/gen_hooks_readme.py --check >/dev/null 2>&1; then
        echo "  ✅ hooks/README.md 与当前 hooks 一致"
      else
        echo "  ❌ hooks/README.md 与当前 hooks 不一致（drift）"
        echo "     → 修法：python3 scripts/gen_hooks_readme.py 重新生成后提交"
        HOOKS_FAIL=1; GLOBAL_FAIL=1
      fi
    fi

    # 15.8 scripts/README.md 清单 drift（gen_scripts_readme.py 自动生成，须与当前 scripts 一致）
    echo ""
    echo "--- scripts/README.md 清单 drift ---"
    if [ -f scripts/gen_scripts_readme.py ] && command -v python3 >/dev/null 2>&1; then
      if python3 scripts/gen_scripts_readme.py --check >/dev/null 2>&1; then
        echo "  ✅ scripts/README.md 与当前 scripts 一致"
      else
        echo "  ❌ scripts/README.md 与当前 scripts 不一致（drift）"
        echo "     → 修法：python3 scripts/gen_scripts_readme.py 重新生成后提交"
        HOOKS_FAIL=1; GLOBAL_FAIL=1
      fi
    fi

    # 15.9 规范承诺一致性（md 推荐的 SKIP 变量 / lib.* 模块 / 工具路径必须有实现或消费方）
    # 先例：dur_ms 埋点半接 / anchor_patterns 零消费 / SKIP_AUDIT_FAST 幽灵门 / .venv mypy 不存在。
    # cat 22 管脚本语法层，本条管规范文件的「承诺层」。豁免清单就地注理由——豁免是干跑清零的结果，不是预设。
    echo ""
    echo "--- 规范承诺一致性（SKIP / lib.* / 工具路径）---"
    PROMISE_OUT=$(python3 - <<'PYEOF'
import os, re, sys
from pathlib import Path
sys.stdout.reconfigure(newline='\n')

# 语料：runbooks + SKILL.md + CLAUDE.md + hooks 两 md
corpus = sorted(Path('.claude/runbooks').glob('*.md'))
corpus += sorted(Path('.claude/skills').glob('*/SKILL.md'))
corpus += [p for p in (Path('CLAUDE.md'), Path('.claude/hooks/README.md'),
                       Path('.claude/hooks/HOOK_WRITING.md')) if p.exists()]

SKIP_RE = re.compile(r'\bSKIP_[A-Z0-9_]+_GATE\b')  # <GATE> 模板形 / 无 _GATE 尾缀的杂项天然不匹配
LIB_RE = re.compile(r'\blib\.([a-z][a-z0-9_]+)\b')
TICK_RE = re.compile(r'`([^`\n]+)`')
EXTS = ('.py', '.sh', '.js', '.yaml', '.yml', '.json')
BAD_CHARS = set('{}*$<>')  # 占位 / glob / 变量拼接形不作数

# 豁免清单（每个条目注明出处理由）
EXEMPT_LIB = {'modname'}  # git-and-hooks.md「from .modname import」行文占位符，无实现属有意
EXEMPT_PATH_STEM = set()  # 暂空；出现真占位（如 xxx/bin/yyy）时按 stem 加并注出处

# SKIP / lib 消费方搜索面：hooks + skill scripts + 根 scripts（含 .sh/.py；SKIP_SCENE_PROSE_GATE
# 消费方在 check_prd_md.sh 不在 hooks——只扫 hooks 必误报）
chunks = []
for root in ('.claude/hooks', '.claude/skills', 'scripts'):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ('__pycache__', 'assets', 'archive')]
        for fn in filenames:
            if fn.endswith(('.sh', '.py')):
                try:
                    chunks.append(Path(dirpath, fn).read_text(encoding='utf-8', errors='ignore'))
                except OSError:
                    pass
CONSUMERS = '\n'.join(chunks)

# 工具路径 basename 索引（shorthand 兜底：md 写 scripts/audit.sh 实际在 .claude/skills/*/scripts/；
# lib/pre-writeedit-guards.sh 这类 hooks lib 简写也走 basename）
skill_script_names = set()
for pat in ('.claude/skills/*/scripts/*.py', '.claude/skills/*/scripts/*.sh',
            '.claude/skills/*/scripts/**/*.py', '.claude/skills/*/scripts/**/*.sh',
            '.claude/hooks/lib/*.sh'):
    for p in Path('.').glob(pat):
        skill_script_names.add(p.name)

def path_ok(rel, extra_bases):
    candidates = [rel, f'scripts/{rel}', f'.claude/{rel}'] + [str(b / rel) for b in extra_bases]
    for c in candidates:
        if Path(c).is_file():
            return True
    if any(Path(p, rel).is_file() for p in Path('projects').glob('*') if p.is_dir()):
        return True  # 项目相对路径（如 scripts/screenshot_proto.py 只在 projects/*/scripts/）
    return Path(rel).name in skill_script_names

findings = []
n_skip = n_lib = n_path = n_exempt = 0
for f in corpus:
    # 文档相对路径以文档自身目录为解析基之一（ppt SKILL.md 的 assets/xx.js、
    # HOOK_WRITING.md 的 test/test-hooks.sh）
    bases = [f.parent]
    for ln, line in enumerate(f.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
        loc = f'{f}:{ln}'
        for var in set(SKIP_RE.findall(line)):
            n_skip += 1
            if var not in CONSUMERS:
                findings.append(f'  ❌ {loc} 承诺 SKIP 变量 `{var}` 但 hooks / skill scripts / scripts 均无消费方')
        for mod in set(LIB_RE.findall(line)):
            if mod in EXEMPT_LIB:
                n_exempt += 1
                continue
            n_lib += 1
            if not (Path(f'scripts/lib/{mod}.py').exists()
                    or Path(f'scripts/lib/{mod}.yaml').exists()
                    or Path(f'scripts/lib/{mod}').is_dir()
                    or list(Path('.claude/skills').glob(f'*/scripts/lib/{mod}.py'))):
                findings.append(f'  ❌ {loc} 承诺 `lib.{mod}` 但 scripts/lib/ 与 skill scripts/lib/ 均无实现')
        for span in TICK_RE.findall(line):
            for word in span.split():
                if '/' not in word:
                    continue
                w = word.rstrip('.,;:)）」』')
                if not w.endswith(EXTS) or any(c in w for c in BAD_CHARS):
                    continue
                if w.startswith(('http', '-', '/', '~/', 'src/')):
                    # ~/ 家目录在仓外；src/ 是 runbook 里项目产物结构的示例段（非框架工具路径）
                    continue
                if Path(w).name in EXEMPT_PATH_STEM:
                    n_exempt += 1
                    continue
                n_path += 1
                if not path_ok(w, bases):
                    findings.append(f'  ❌ {loc} 承诺工具路径 `{w}` 但根 / scripts/ / .claude/ / projects/*/ / skills basename 均未命中')

if findings:
    print('\n'.join(findings))
print(f'STATS: SKIP {n_skip} · lib {n_lib} · path {n_path} · 豁免 {n_exempt} · fail {len(findings)}')
PYEOF
)
    if echo "$PROMISE_OUT" | grep -q '^  ❌'; then
      echo "$PROMISE_OUT" | grep '^  ❌' | head -15
      echo "     → 修法：删 md 里的幽灵承诺，或补实现 / 消费方；确属行文占位 → 本节 EXEMPT_LIB / EXEMPT_PATH_STEM 加豁免并注理由"
      HOOKS_FAIL=1; GLOBAL_FAIL=1
    else
      echo "  ✅ 承诺一致（$(echo "$PROMISE_OUT" | sed -n 's/^STATS: //p')）"
    fi

    # 15.10 SKILL.md 提及的 gate 名必须在 README gate 索引里
    # 防 SKILL.md 写老 hook 文件名（pre/post-*-check）或拼写错误的 gate 名
    echo ""
    echo "--- SKILL.md gate 名与 README 索引一致 ---"
    GATE_DRIFT_OUT=$(python3 - <<'PYEOF'
import re, sys
from pathlib import Path
sys.stdout.reconfigure(newline='\n')
sys.path.insert(0, str(Path.cwd() / "scripts"))
from gen_hooks_readme import hook_gates, HOOK_DIR
canonical = set()
for f in sorted(HOOK_DIR.glob("*.sh")):
    canonical |= set(hook_gates(f))
# 脚本级 gate（在 skill scripts/*.py 里 print + exit，非 hook log_event，不在 README 索引）
SCRIPT_LEVEL_GATES = {"screenshot-route-gate"}
canonical |= SCRIPT_LEVEL_GATES
old_name_re = re.compile(r'`(pre|post)-[a-z][a-z0-9-]*-check`')
gate_re = re.compile(r'`([a-z][a-z0-9-]*-gate)`')
findings = []
for md in sorted(Path(".claude/skills").glob("*/SKILL.md")):
    text = md.read_text(encoding="utf-8")
    for m in old_name_re.finditer(text):
        name = m.group(0).strip('`')
        findings.append(f"  ❌ {md}: 老名 `{name}` 不在 gate 索引")
    for m in gate_re.finditer(text):
        name = m.group(1)
        if name not in canonical:
            findings.append(f"  ❌ {md}: `{name}` 不在 gate 索引")
n = len(list(Path(".claude/skills").glob("*/SKILL.md")))
print('\n'.join(findings))
print(f'STATS: skills {n} · canonical {len(canonical)} · fail {len(findings)}')
PYEOF
)
    if echo "$GATE_DRIFT_OUT" | grep -q '^  ❌'; then
      echo "$GATE_DRIFT_OUT" | grep '^  ❌' | head -15
      echo "     → 修法：SKILL.md「会拦你的 hook」段的 gate 名与 .claude/hooks/README.md 索引对齐"
      HOOKS_FAIL=1; GLOBAL_FAIL=1
    else
      echo "  ✅ SKILL.md gate 名与索引一致（$(echo "$GATE_DRIFT_OUT" | sed -n 's/^STATS: //p')）"
    fi

    [ "$HOOKS_FAIL" -eq 0 ] && echo ""
    echo ""
  fi
fi

# ─────────────────────────────────────────────
# 类别 17：内链断链（.md 相对链接目标存在性，红灯 block）
# ─────────────────────────────────────────────
if run_cat 17; then
  echo "===== 17. 内链断链 ====="
  echo ""
  LINK_FAIL=0
  LINK_SCANNED=0
  LINK_CHECKED=0

  MD_SET=$(ls CLAUDE.md README.md 2>/dev/null; ls .claude/skills/*/SKILL.md .claude/skills/*/references/*.md .claude/runbooks/*.md .claude/hooks/*.md 2>/dev/null)
  for md in $MD_SET; do
    [ -f "$md" ] || continue
    LINK_SCANNED=$((LINK_SCANNED + 1))
    dir=$(dirname "$md")
    # 先剥行内图片嵌入 ![alt](src)（规则文档里多是示意截图，非可导航链接），再抽 [text](target)
    while IFS= read -r tgt; do
      [ -z "$tgt" ] && continue
      case "$tgt" in
        http://*|https://*|mailto:*|\#*) continue ;;
        # 占位/模板路径（文档示例，非真实链接）
        *'{'*|*'}'*|*'*'*|*xxx*|*XXX*|*XX*|*'...'*|*YYYY*|*mmdd*) continue ;;
        # 指向 projects/（gitignore 易变内容，跨边界引用）不进 block 集
        *projects/*) continue ;;
      esac
      path="${tgt%%#*}"
      [ -z "$path" ] && continue
      LINK_CHECKED=$((LINK_CHECKED + 1))
      if [ -e "$dir/$path" ] || [ -e "$path" ]; then
        :
      else
        printf '  ❌ %s → %s（目标不存在）\n' "$md" "$tgt"
        LINK_FAIL=1; GLOBAL_FAIL=1
      fi
    done < <(sed -E 's/!\[[^]]*\]\([^)]*\)//g' "$md" 2>/dev/null | grep -oE '\]\([^)]+\)' | sed -E 's/^\]\(//; s/\)$//')
  done

  if [ "$LINK_FAIL" -eq 0 ]; then
    echo "  ✅ 内链全部有效（扫描 $LINK_SCANNED 文件 / 校验 $LINK_CHECKED 条相对链接）"
  fi
  echo ""
fi

# ─────────────────────────────────────────────
# 类别 18：场景编号悬空（baseline 引用 scene-list 未定义编号，黄灯 warn）
# 字母族收敛：只校验「字母族在 scene-list 真定义过」的引用，自动滤除决议号 / M-N 项目
# 项目级豁免：项目根 .audit-ignore-scene（每行一编号或 glob，# 注释）
# ─────────────────────────────────────────────
if run_cat 18; then
  echo "===== 18. 场景编号悬空 ====="
  echo ""
  HAS_SCENE_PROJECT=false

  for sl in projects/*/scene-list.md projects/*/*/scene-list.md; do
    [ -f "$sl" ] || continue
    proj_dir="$(dirname "$sl")/"
    baseline=$(ls "${proj_dir}"prd-*-baseline.md 2>/dev/null | head -1)
    [ -n "$baseline" ] || continue
    HAS_SCENE_PROJECT=true
    proj=$(basename "$proj_dir")

    # scene-list 定义编号（表格首列，X-N / X-Na 形式）
    defined=$(awk -F'|' '/^\| / {s=$2; gsub(/^ +| +$/, "", s); if (s ~ /^[A-Z][0-9]*-[0-9]+[a-z]?$/) print s}' "$sl" | sort -u)
    # 定义过的字母族
    families=$(echo "$defined" | sed -E 's/-.*//; s/[0-9]+$//' | sort -u | grep .)

    # 项目豁免列表
    ignore_file="${proj_dir}.audit-ignore-scene"
    ignore_patterns=""
    [ -f "$ignore_file" ] && ignore_patterns=$(grep -v '^#' "$ignore_file" 2>/dev/null | grep -v '^$')

    # baseline 引用编号
    refd=$(grep -oE '\b[A-Z][0-9]*-[0-9]+[a-z]?\b' "$baseline" | sort -u)
    dangling=""
    while read -r r; do
      [ -z "$r" ] && continue
      fam=$(echo "$r" | sed -E 's/-.*//; s/[0-9]+$//')
      # 族收敛：族未在 scene-list 定义过 → 不是场景编号，跳过
      echo "$families" | grep -qx "$fam" || continue
      # 已定义 → 合法
      echo "$defined" | grep -qx "$r" && continue
      # 项目豁免匹配
      skip=false
      if [ -n "$ignore_patterns" ]; then
        while IFS= read -r pat; do
          [ -z "$pat" ] && continue
          case "$r" in $pat) skip=true; break ;; esac
        done <<< "$ignore_patterns"
      fi
      $skip && continue
      dangling="$dangling $r"
    done <<< "$refd"

    if [ -n "$dangling" ]; then
      echo "  ⚠️  $proj baseline 引用了 scene-list 未定义的编号:$dangling"
      echo "       → 修法：① scene-list 补登该编号，或 ② 改 baseline 引用，或 ③ ${ignore_file} 加豁免（forward-reference / 开放问题）"
    else
      echo "  ✅ $proj baseline 场景引用全部有定义"
    fi
  done

  if ! $HAS_SCENE_PROJECT; then
    echo "  ⏭️ 无 baseline + scene-list 项目，跳过"
  fi
  echo ""
fi

# ─────────────────────────────────────────────
# 类别 19：跨平台兼容（macOS BSD / Linux·WSL GNU / Windows 原生 Python）
# 规则源：scripts/SCRIPTS_WRITING.md §三.I + .claude/hooks/HOOK_WRITING.md §三.J
# 扫描面：维护中的 .py/.sh（scripts + hooks + skill scripts），排除 tests / archive / figma-anchors（第三方源码）
# ─────────────────────────────────────────────
if run_cat 19; then
  echo "===== 19. 跨平台兼容 ====="
  echo ""
  COMPAT_FAIL=0

  # 扫描面：维护中的脚本。排除 tests / archive / figma-anchors（第三方源码）；
  # 排除本文件 audit.sh —— 它含各 lint 的 pattern / 提示串，会自命中（同 §15 只扫 HOOK_DIR 不扫自己）
  COMPAT_SH=$(find scripts .claude/hooks .claude/skills -type f -name '*.sh' 2>/dev/null \
    | grep -vE '/(tests|archive)/' | grep -v '/assets/figma-anchors/' | grep -v '/workspace-audit/scripts/audit.sh$')
  COMPAT_PY=$(find scripts .claude/hooks .claude/skills -type f -name '*.py' 2>/dev/null \
    | grep -vE '/(tests|archive)/' | grep -v '/assets/figma-anchors/')

  # 19.1 mktemp 带后缀模板（BSD 只替换末尾连续 X，x.XXXXXX.md 不随机化生成字面名）
  echo "--- mktemp 后缀模板（BSD 不随机化）---"
  M_HITS=$(echo "$COMPAT_SH" | xargs grep -nE 'mktemp[^|;&<>`]*X{3,}\.' 2>/dev/null)
  if [ -n "$M_HITS" ]; then
    echo "  ❌ mktemp 模板在 X 后接后缀，BSD（macOS）不替换 → 生成字面名 / 并发撞车："
    echo "$M_HITS" | sed 's/^/     /'
    echo "     修法：裸 mktemp 或 \"\$(mktemp).md\"（SCRIPTS_WRITING §三.I）"
    COMPAT_FAIL=1; GLOBAL_FAIL=1
  else
    echo "  ✅ 无 mktemp 后缀模板"
  fi

  # 19.2 Python open() 文本模式缺 encoding=（Windows 默认非 UTF-8，写 CJK 炸）
  echo ""
  echo "--- Python open() 缺 encoding ---"
  O_HITS=$(echo "$COMPAT_PY" | xargs grep -nE "(^|[^.A-Za-z_])open\([^)]*,[[:space:]]*['\"][rwa]t?[+]?['\"]" 2>/dev/null | grep -v 'encoding')
  if [ -n "$O_HITS" ]; then
    echo "  ❌ open() 文本模式未传 encoding=（Windows 原生 Python 默认 cp1252，写 CJK UnicodeEncodeError）："
    echo "$O_HITS" | sed 's/^/     /'
    echo "     修法：open(path, \"w\", encoding=\"utf-8\")（SCRIPTS_WRITING §三.B）"
    COMPAT_FAIL=1; GLOBAL_FAIL=1
  else
    echo "  ✅ Python open() 文本模式均带 encoding"
  fi

  # 19.3 sed -i 裸用（GNU 接 -i，BSD 须 -i '' 或带后缀；sed -i.bak 两边通吃）
  echo ""
  echo "--- sed -i 裸用（BSD/GNU 分叉）---"
  S_HITS=$(echo "$COMPAT_SH" | xargs grep -nE "(^|[^A-Za-z0-9_.-])sed([[:space:]]+-[a-zA-Z]+)*[[:space:]]+-i([[:space:]]|$)" 2>/dev/null \
    | grep -vE "sed -i(\.[a-zA-Z]+| +(''|\"\"))")
  if [ -n "$S_HITS" ]; then
    echo "  ❌ sed -i 未带备份后缀（GNU-only，BSD 会把下一参数当后缀吞掉）："
    echo "$S_HITS" | sed 's/^/     /'
    echo "     修法：sed -i.bak 's/../../' 后 rm .bak（两边通吃，SCRIPTS_WRITING §三.I）"
    COMPAT_FAIL=1; GLOBAL_FAIL=1
  else
    echo "  ✅ 无 sed -i 裸用"
  fi

  # 19.4 GNU-only coreutils 无 BSD fallback（文件级：stat -c / date -d 同文件无 BSD 形 → 风险；grep -P / readlink -f 行级直判）
  echo ""
  echo "--- GNU-only coreutils（无 BSD fallback）---"
  G_HITS=""
  while IFS= read -r fl; do
    [ -f "$fl" ] || continue
    # stat -c 无同文件 stat -f
    if grep -qE '(^|[^A-Za-z0-9_-])stat -c' "$fl" && ! grep -qE 'stat -f' "$fl"; then
      G_HITS="$G_HITS$(grep -nE '(^|[^A-Za-z0-9_-])stat -c' "$fl" | sed "s|^|     $fl:|")"$'\n'
    fi
    # date -d / --date 无同文件 date -v / -j（BSD 形）
    if grep -qE '(^|[^A-Za-z0-9_-])date (-d|--date)' "$fl" && ! grep -qE 'date (-v|-j)' "$fl"; then
      G_HITS="$G_HITS$(grep -nE '(^|[^A-Za-z0-9_-])date (-d|--date)' "$fl" | sed "s|^|     $fl:|")"$'\n'
    fi
    # grep -P（PCRE，BSD 无）/ readlink -f（BSD 老版无）—— 行级无条件非可移植
    if grep -qE '(grep -[a-zA-Z]*P|readlink -f)' "$fl"; then
      G_HITS="$G_HITS$(grep -nE '(grep -[a-zA-Z]*P|readlink -f)' "$fl" | sed "s|^|     $fl:|")"$'\n'
    fi
  done <<< "$COMPAT_SH"
  G_HITS=$(echo "$G_HITS" | grep -v '^$')
  if [ -n "$G_HITS" ]; then
    echo "  ❌ GNU-only coreutils 用法缺 BSD fallback（macOS 静默失败）："
    echo "$G_HITS"
    echo "     修法：stat -f||stat -c / date 偏移交 python3 / grep -P 换 -E / readlink -f 换 python3 realpath（SCRIPTS_WRITING §三.I）"
    COMPAT_FAIL=1; GLOBAL_FAIL=1
  else
    echo "  ✅ 无 GNU-only coreutils 裸用"
  fi

  [ "$COMPAT_FAIL" -eq 0 ] && { echo ""; echo "  ✅ 跨平台兼容全部通过"; }
  echo ""
fi

# ─────────────────────────────────────────────
# 类别 20：计数对账（门面文档 N 个 skill/hook/runbook 手写计数 vs 文件系统真实数）
# 真相源 = 文件系统。文档只允许写真实值，漂移即红灯。
# ─────────────────────────────────────────────
if run_cat 20; then
  echo "===== 20. 计数对账 ====="
  echo ""
  COUNT_FAIL=0

  # 真实值（文件系统权威）
  REAL_SKILLS=$(ls -d .claude/skills/*/ 2>/dev/null | grep -v '_shared' | wc -l | tr -d ' ')
  REAL_HOOKS=$(ls .claude/hooks/*.sh 2>/dev/null | grep -v '/lib/' | wc -l | tr -d ' ')
  REAL_RUNBOOKS=$(ls .claude/runbooks/*.md 2>/dev/null | wc -l | tr -d ' ')
  REAL_CATS=$(grep -cE '^if run_cat [0-9]+; then' .claude/skills/workspace-audit/scripts/audit.sh)

  echo "  文件系统真实值：skill=$REAL_SKILLS  hook=$REAL_HOOKS  runbook=$REAL_RUNBOOKS  audit类别=$REAL_CATS"
  echo ""

  # 待校验门面文档：正文/目录树/章节标题里手写的 "N 个 skill/hook/runbook" 与 badge
  # 用法：check_count <文件> <正则(捕获组1=数字)> <真实值> <标签>
  check_count() {
    local file="$1" re="$2" real="$3" label="$4"
    [ -f "$file" ] || return 0
    while IFS= read -r line; do
      local lineno="${line%%:*}"
      local num=$(echo "${line#*:}" | grep -oE "$re" | grep -oE '[0-9]+' | head -1)
      [ -z "$num" ] && continue
      if [ "$num" != "$real" ]; then
        echo "  ❌ $file:$lineno — $label 写 ${num}，真实 ${real}"
        COUNT_FAIL=1; GLOBAL_FAIL=1
      fi
    done < <(grep -nE "$re" "$file" 2>/dev/null)
  }

  # skill 计数
  check_count "README.md"           '[0-9]+ 个 Skill'          "$REAL_SKILLS" "skill 数"
  check_count "README.md"           'skills/                  # [0-9]+ 个 Skill' "$REAL_SKILLS" "skill 数(目录树)"
  check_count "README.md"           'badge/skills-[0-9]+'      "$REAL_SKILLS" "skill badge"
  check_count "README-EN.md"        '[0-9]+ Skills'            "$REAL_SKILLS" "skill 数"
  check_count "README-EN.md"        'badge/skills-[0-9]+'      "$REAL_SKILLS" "skill badge"
  check_count "workspace-context.md" '[0-9]+ 个标准化 Skill'   "$REAL_SKILLS" "skill 数"
  check_count "workspace-context.md" 'Skill 体系（[0-9]+ 个'   "$REAL_SKILLS" "skill 数(章节标题)"

  # hook 计数（物理 .sh 口径；演进注历史段不校验——带 > 引用块，正则不命中当前态表述）
  check_count "README.md"           'badge/hooks-[0-9]+'       "$REAL_HOOKS" "hook badge"
  check_count "workspace-context.md" 'Hook 矩阵（[0-9]+ 个'    "$REAL_HOOKS" "hook 数(章节标题)"
  check_count "workspace-context.md" '[0-9]+ 个 runtime hook'  "$REAL_HOOKS" "hook 数"

  # runbook 计数
  check_count "README.md"           '# [0-9]+ 个按需'          "$REAL_RUNBOOKS" "runbook 数(目录树)"
  check_count "README-EN.md"        '# [0-9]+ on-demand'       "$REAL_RUNBOOKS" "runbook 数(目录树)"
  check_count "README-EN.md"        '[0-9]+ runbooks'          "$REAL_RUNBOOKS" "runbook 数"

  # audit 类别数
  check_count "README.md"           'badge/audit-[0-9]+'       "$REAL_CATS" "audit 类别 badge"
  check_count "README-EN.md"        'badge/audit-[0-9]+'       "$REAL_CATS" "audit 类别 badge"

  [ "$COUNT_FAIL" -eq 0 ] && echo "  ✅ 门面文档计数与文件系统一致"
  echo ""
fi

# ─────────────────────────────────────────────
# 类别 21：hub 分发物健康（AIHUB 包生产线）
# 判据与 hub/gen_index.py 的自动分类逻辑同源：Agent 要 agent-model.json +
# system-prompt.md / Tool 要 aihub_tool.py / Skill 要 SKILL.md。
# ─────────────────────────────────────────────
if run_cat 21; then
  echo "===== 21. hub 分发物健康 ====="
  echo ""

  if [ ! -d hub ]; then
    echo "  · 无 hub/ 目录，skip"
    echo ""
  else
    # 21.1 zip 新鲜度 / 缺失 / 部署态漂移（红灯 exit 2）
    echo "--- 分发物新鲜度 ---"
    if python3 scripts/check_hub_fresh.py --strict; then
      :
    else
      echo "  ❌ hub 分发物有过期 zip（上方红灯）"
      GLOBAL_FAIL=1
    fi
    echo ""

    # 21.2 INDEX.md 与目录树一致性
    echo "--- INDEX.md drift ---"
    if python3 hub/gen_index.py --check >/dev/null 2>&1; then
      echo "  ✅ INDEX.md 与当前包目录一致"
    else
      echo "  ❌ INDEX.md drift — 跑 python3 hub/gen_index.py 刷新"
      GLOBAL_FAIL=1
    fi
    echo ""

    # 21.3 每包必备文件齐全
    echo "--- 包必备文件 ---"
    HUB_FAIL=0
    for d in hub/*/; do
      pkg=$(basename "$d")
      case "$pkg" in zips|references|AI中台-规范及帮助文档|.*|__*) continue ;; esac
      if [ -f "$d/agent-model.json" ]; then
        [ -f "$d/system-prompt.md" ] || { echo "  ❌ $pkg（Agent）缺 system-prompt.md"; HUB_FAIL=1; GLOBAL_FAIL=1; }
      elif [ -f "$d/aihub_tool.py" ] || [ -f "$d/SKILL.md" ]; then
        :
      else
        echo "  ❌ $pkg 无 SKILL.md / aihub_tool.py / agent-model.json，形态无法判定"
        HUB_FAIL=1; GLOBAL_FAIL=1
      fi
    done
    [ "$HUB_FAIL" -eq 0 ] && echo "  ✅ 各包按形态的必备文件齐全"
    echo ""

    # 21.4 同源脚本副本漂移（warn-only：脱敏是有意分叉，只登记不阻断）
    echo "--- 同源副本漂移登记 ---"
    python3 scripts/check_fork_drift.py | sed 's/^/  /'
    echo ""
  fi
fi

# ─────────────────────────────────────────────
# 类别 22：脚本健康度（语法层机械检查，深审固化 — 按需跑，不进 pre-commit 默认）
# ─────────────────────────────────────────────
if run_cat 22; then
  echo "===== 22. 脚本健康度 ====="
  echo ""

  # 清单：生产脚本（排除 archive / __pycache__ / .venv / 中台规范文档 / assets 示例固件 / examples / _demos）
  PY_LIST=$(mktemp); SH_LIST=$(mktemp)
  find scripts .claude/skills .claude/hooks projects hub -type f -name "*.py" \
    -not -path "*/archive/*" -not -path "*/__pycache__/*" -not -path "*/.venv/*" \
    -not -path "*/AI中台-规范及帮助文档/*" -not -path "*/assets/*" \
    -not -path "*/examples/*" -not -path "*/_demos/*" > "$PY_LIST" 2>/dev/null
  find scripts .claude/skills .claude/hooks projects hub -type f -name "*.sh" \
    -not -path "*/archive/*" -not -path "*/.venv/*" \
    -not -path "*/AI中台-规范及帮助文档/*" -not -path "*/assets/*" \
    -not -path "*/examples/*" -not -path "*/_demos/*" > "$SH_LIST" 2>/dev/null

  # 22.1 Python：语法错（E9）+ 未定义名（F821）— 单次 ruff 全量；格式 / 未用 import 类不阻断
  echo "--- Python 语法 / 未定义名 ---"
  PY_N=$(wc -l < "$PY_LIST" | tr -d ' ')
  PY_FAIL=0
  if python3 -m ruff --version >/dev/null 2>&1; then
    RUFF_OUT=$(xargs python3 -m ruff check --select E9,F821 --no-cache --output-format concise < "$PY_LIST" 2>&1)
    if [ -n "$RUFF_OUT" ] && ! echo "$RUFF_OUT" | grep -q "All checks passed"; then
      echo "$RUFF_OUT" | sed 's/^/  ❌ /'
      PY_FAIL=1; GLOBAL_FAIL=1
    fi
  else
    echo "  ⚠ 未装 ruff，跳过（brew install ruff）"
  fi
  [ "$PY_FAIL" -eq 0 ] && echo "  ✅ ${PY_N} 个 py 无语法错 / 未定义名"

  # 22.2 Shell：bash -n 双版本（PATH bash 5.x + /bin/bash 3.2 兼容）
  echo "--- Shell 双版本语法 ---"
  SH_N=$(wc -l < "$SH_LIST" | tr -d ' ')
  SH_FAIL=0
  while IFS= read -r f; do
    err=$(bash -n "$f" 2>&1) || { echo "  ❌ [bash5] $f: $err"; SH_FAIL=1; GLOBAL_FAIL=1; }
    if [ -x /bin/bash ] && [ "/bin/bash" != "$(command -v bash)" ]; then
      err=$(/bin/bash -n "$f" 2>&1) || { echo "  ❌ [bash3.2] $f: $err"; SH_FAIL=1; GLOBAL_FAIL=1; }
    fi
  done < "$SH_LIST"
  [ "$SH_FAIL" -eq 0 ] && echo "  ✅ ${SH_N} 个 sh 双版本语法全过"

  # 22.3 shellcheck error 级（语法过但必然跑挂；warning 级人手跑 shellcheck -S warning）
  echo "--- shellcheck error 级 ---"
  SC_FAIL=0
  if command -v shellcheck >/dev/null 2>&1; then
    SC_OUT=$(xargs shellcheck -S error --format=gcc < "$SH_LIST" 2>&1)
    if [ -n "$SC_OUT" ]; then
      echo "$SC_OUT" | sed 's/^/  ❌ /'
      SC_FAIL=1; GLOBAL_FAIL=1
    fi
  else
    echo "  ⚠ 未装 shellcheck，跳过（brew install shellcheck）"
  fi
  [ "$SC_FAIL" -eq 0 ] && echo "  ✅ shellcheck error 级零命中"
  echo ""
  rm -f "$PY_LIST" "$SH_LIST"
fi

# ─────────────────────────────────────────────
# 类别 23：阈值分布报告
# ─────────────────────────────────────────────
if run_cat 23; then
  echo "===== 23. 阈值分布报告 ====="
  echo ""

  # 23.1 thresholds.yaml 消费者覆盖
  echo "--- thresholds.yaml 键与消费者 ---"
  THRESHOLD_OUT=$(python3 - <<'PYEOF'
import re, sys
from pathlib import Path
sys.stdout.reconfigure(newline='\n')
yaml = Path("scripts/lib/thresholds.yaml")
if not yaml.is_file():
    print("  ⚠ thresholds.yaml 不存在")
    sys.exit(0)
text = yaml.read_text(encoding="utf-8")
keys = re.findall(r'^([a-z_]+)\.([a-z_]+):', text, re.MULTILINE)
consumers = {}
for cat, key in keys:
    full = f"{cat}.{key}"
    # grep 消费者
    found = []
    for py in Path("scripts").rglob("*.py"):
        if "archive" in str(py):
            continue
        try:
            t = py.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if full in t or key.upper() in t:
            found.append(str(py))
    for sh in Path(".claude/hooks").rglob("*.sh"):
        try:
            t = sh.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if key.upper() in t:
            found.append(str(sh))
    consumers[full] = found
    status = "✅" if found else "⚠ 无消费者"
    loc = f" ← {', '.join(found[:2])}" if found else ""
    print(f"  {status} {full}{loc}")
print(f"STATS: keys {len(consumers)} · consumed {sum(1 for v in consumers.values() if v)}")
PYEOF
)
  echo "$THRESHOLD_OUT" | grep -v '^STATS:'

  # 23.2 硬编码阈值登记
  echo ""
  echo "--- 硬编码阈值登记 ---"
  echo "  以下阈值硬编码在脚本中，未进 thresholds.yaml（应登记）："
  echo "  - prd.long_sentence=100     ← .claude/skills/prd/scripts/humanize/patterns.py:75"
  echo "  - prd.story_chars=30        ← .claude/skills/prd/scripts/core/md_renderer.py:140"
  echo "  - prd.scene_split=10       ← .claude/skills/prd/scripts/gen_prd_skeleton.py:269"
  echo "  - baseline.stale_days=60   ← scripts/check_baseline_fresh.py:381"
  echo "  - rule_volume.*            ← scripts/rule-budgets.manifest.json（逐文件上限是名册非标量，"
  echo "                                另立 manifest，消费者 scripts/check_rule_volume.py）"
  echo ""

  # 23.3 阈值命中分布（拿真实产物跑 check_bullet_density）
  echo "--- bullet-density 命中分布 ---"
  BD_SAMPLE=$(find projects -name "prd-*-baseline.md" -not -path "*/archive/*" | head -3)
  if [ -n "$BD_SAMPLE" ]; then
    for f in $BD_SAMPLE; do
      [ -f "$f" ] || continue
      HITS=$(python3 scripts/check_bullet_density.py "$f" --json-out - 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    hits = d.get('hits', [])
    print(f'  {len(hits)} hits')
except: print('  (parse error)')
" 2>/dev/null)
      echo "  $(basename "$f"): ${HITS:- 0 hits}"
    done
  else
    echo "  ⏭️ 无 baseline 产物可采样"
  fi
  echo ""
fi

# ─────────────────────────────────────────────
# 类别 24：原型可复现性（共享场景库产线）
# ─────────────────────────────────────────────
if run_cat 24; then
  echo "===== 24. 原型可复现性 ====="
  echo ""

  # 共享场景库让多版本复用同一份场景实现，代价是改共享层会静默改掉其他版本的产物。
  # 逐版本重建到临时目录做字节比对（不碰已交付产物），漂移报黄不阻断 commit。
  REPRO=".claude/skills/prototype/scripts/check_proto_repro.py"
  if [ -f "$REPRO" ]; then
    python3 "$REPRO" 2>&1 | sed 's/^/  /'
  else
    echo "  ⚠ check_proto_repro.py 不存在，跳过"
  fi
  echo ""
fi

# ─────────────────────────────────────────────
# 类别 25：Gate 健康度（遥测回路）
# ─────────────────────────────────────────────
if run_cat 25; then
  echo "===== 25. Gate 健康度 ====="
  echo ""

  # usage.jsonl 反过来管 gate 名册：日志有名字而注册表没有 = 死 gate；
  # 退役名册登记了却零事件 = 死豁免。两者红灯，零触发 / skip 失衡只报黄。
  if python3 scripts/gate_health.py --strict; then
    :
  else
    echo "  ❌ gate 名册与遥测漂移（上方红灯）"
    GLOBAL_FAIL=1
  fi
  echo ""
fi

echo "===== 审计完成 ====="
exit $GLOBAL_FAIL
