#!/bin/bash
# MRD 评审报告基本卫生自检
# 只卡评审报告本身的卫生（八维度齐全 / 最终立场 / 找漏 / 圈数字 / 占位符 / CJK 标点）
# 不卡 MRD 输入格式（评的是价值不是格式，参 SKILL.md 核心原则）
#
# 用法: bash scripts/check_mrd.sh <评审报告.md>
set -euo pipefail

FILE="${1:?用法: bash scripts/check_mrd.sh <评审报告.md>}"

if [ ! -f "$FILE" ]; then
    echo "❌ 文件不存在: $FILE"
    exit 2
fi

echo "=========================================="
echo "  MRD 评审报告自检: $(basename "$FILE")"
echo "=========================================="

fail=0

# ── 1. 最终立场必须给出 ────────────────────────
if ! grep -qE '最终立场.*[:：].*(该做|有保留地做|暂不该做|重做)' "$FILE"; then
    echo "❌ 缺「最终立场」一句话结论(该做/有保留地做/暂不该做)"
    echo "   评审报告开头必须给一行立场,决策者 1 分钟内拿结论"
    fail=1
fi

# ── 2. 八维度立场齐全 ──────────────────────────
declare -a DIMS=(
    "市场窗口真伪"
    "用户价值兑现"
    "差异化是否站得住"
    "UE 模型成立性"
    "资源可行性"
    "风险底线"
    "战略契合"
    "成功 / 杀死标准"
)
missing_dims=()
for d in "${DIMS[@]}"; do
    if ! grep -qF "$d" "$FILE"; then
        missing_dims+=("$d")
    fi
done
if [ ${#missing_dims[@]} -gt 0 ]; then
    echo "❌ 缺维度小标题(${#missing_dims[@]}/8): ${missing_dims[*]}"
    fail=1
fi

# ── 3. 投票表存在(8 行立场行) ─────────────────
# 立场标识用 ✅ / ⚠️ / ❌
stance_count=$(grep -cE '(✅|⚠️|❌)' "$FILE" || true)
if [ "$stance_count" -lt 8 ]; then
    echo "❌ 立场标识(✅/⚠️/❌)不足 8 处: 实际 $stance_count 处,八维度未全部打立场"
    fail=1
fi

# ── 4. 找漏章节存在 ────────────────────────────
if ! grep -qE '找漏|没写但|没识别|MRD 没说|缺失的判断' "$FILE"; then
    echo "❌ 缺「找漏」章节(MRD 没写但应该有的判断,评审者核心价值之一)"
    fail=1
fi

# ── 4.5 Sources 章节存在 + 至少 1 个外部 URL ──
if ! grep -qE '^#+ +Sources|^#+ +.*外部数据来源|^#+ +.*数据来源' "$FILE"; then
    echo "❌ 缺「Sources」章节(所有外部数据 / 竞品 / 法律先例必须附 URL,凭印象写 = 重写)"
    fail=1
else
    # 检查 Sources 章节后至少有 3 个 markdown URL (排除 Anthropic/Claude 自身的提及)
    url_count=$(awk '/^#+ +Sources|^#+ +.*外部数据来源|^#+ +.*数据来源/,/^---|^#+ +评审局限|^#+ +评审者签名/' "$FILE" \
        | grep -cE '\[.+\]\(https?://[^)]+\)' || true)
    if [ "$url_count" -lt 3 ]; then
        echo "⚠️  Sources 章节 markdown URL 数量 < 3 ($url_count): 八维度评审至少应有 3 个外部参考"
    fi
fi

# ── 4.6 评审局限声明 ──
if ! grep -qE '评审局限|能力边界|不可核实|LLM 可信' "$FILE"; then
    echo "❌ 缺「评审局限声明」(明示 LLM 可信判断 vs 必须 PM 内部数据补的判断)"
    fail=1
fi

# ── 4.7 关键计算列等式（CAC / ROI / LTV）──
# 命中 CAC/ROI/LTV 关键词时，应有「= 数字」或「÷」或显式分子/分母
if grep -qE 'CAC|ROI|LTV|UE 模型' "$FILE"; then
    # 简单启发式：CAC/ROI/LTV 上下文有 = 号或 / 号即视为有等式
    eq_lines=$(grep -cE '(CAC|ROI|LTV)[^|]*=[^|]*[0-9]|=[ ]*[0-9.]+[ ]*(U|USD|RMB|美金)' "$FILE" 2>/dev/null || echo 0)
    eq_lines=$(echo "$eq_lines" | tr -d '\n ')
    if [ "${eq_lines:-0}" -lt 1 ]; then
        echo "⚠️  评审报告提到 CAC/ROI/LTV 但未列等式(单位 + 分子分母 + 结果),易藏算术错误"
    fi
fi

# ── 5. 评审会议程: Top 3 必改 + Top 3 待讨论 + Go/No-Go ──
if ! grep -qE '必须拍板|必改|Top 3 必|Top3 必' "$FILE"; then
    echo "⚠️  缺「必须拍板的 Top 3」(评审会议程要点)"
fi
if ! grep -qE '待讨论|Top 3 待|Top3 待' "$FILE"; then
    echo "⚠️  缺「待讨论的 Top 3」(评审会议程要点)"
fi
if ! grep -qE 'Go.*/.*No-Go|Go / No-Go|No-Go 阈值|Go 条件' "$FILE"; then
    echo "❌ 缺「Go / No-Go 阈值」量化标准(否则验证期没有杀死条件)"
    fail=1
fi

# ── 6. 反 PM 偷懒五问穿透检查 ─────────────────
five_q_count=0
for kw in '真需求' '切过来' '不会做.*看不上\|看不上.*不会做' 'UE 算' '最坏结果'; do
    if grep -qE "$kw" "$FILE"; then
        five_q_count=$((five_q_count + 1))
    fi
done
if [ "$five_q_count" -lt 4 ]; then
    echo "⚠️  「反 PM 偷懒五问」覆盖不足($five_q_count/5),评审深度可能不够"
fi

# ── 7. 圈数字 ①②③ 残留(soul.md 2026-04-28 红线) ──
if grep -qE '[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]' "$FILE"; then
    samples=$(grep -oE '[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]' "$FILE" | sort -u | tr -d '\n')
    echo "❌ 圈数字残留: $samples (CLAUDE.md 禁,统一 1./2./3.)"
    fail=1
fi

# ── 8. 占位符残留 ──────────────────────────────
for kw in 'TBD' 'TODO' 'FIXME' '待填' '{slug}' '{项目}' '{你的名字}' '{YYYY-MM-DD}'; do
    if grep -qF "$kw" "$FILE"; then
        echo "❌ 占位符残留: $kw"
        fail=1
    fi
done

# ── 9. 评审意见空洞检测(避免「请补充」「需完善」式格式党评审) ──
hollow_count=$(grep -cE '^[^|]*(请补充|需完善|建议补充|需要补充).*$' "$FILE" 2>/dev/null || echo 0)
hollow_count=$(echo "$hollow_count" | tr -d '\n ')
if [ "${hollow_count:-0}" -gt 5 ]; then
    echo "⚠️  「请补充/需完善」类空洞建议出现 $hollow_count 次,评审太礼貌不穿透"
    echo "   修法: 每条建议要给具体改法(例『重做市场规模测算,链上口径 × 第三方口径双交叉』)"
fi

# ── 10. CJK 半角标点(soul.md 2026-04-23 红线) ─
PROJ_ROOT=$(cd "$(dirname "$0")/../../../.." && pwd)
if [ -f "$PROJ_ROOT/scripts/check_cjk_punct.py" ]; then
    if ! python3 "$PROJ_ROOT/scripts/check_cjk_punct.py" "$FILE" >/dev/null 2>&1; then
        echo "⚠️  CJK 半角标点违规(详见 scripts/check_cjk_punct.py 输出)"
        python3 "$PROJ_ROOT/scripts/check_cjk_punct.py" "$FILE" 2>&1 | head -10 | sed 's/^/   /'
    fi
fi

# ── 11. 评审者签名 ─────────────────────────────
if ! grep -qE '评审人.*[:：]|评审日期.*[:：]' "$FILE"; then
    echo "⚠️  缺评审者签名(评审人 / 评审日期),归档后无法追溯"
fi

# ── 总结 ───────────────────────────────────────
echo "=========================================="
if [ "$fail" -eq 0 ]; then
    echo "✅ 评审报告自检通过"
    exit 0
else
    echo "❌ 评审报告自检未通过"
    exit 1
fi
