#!/usr/bin/env bash
# inject-canary.sh — 给核心 IP 文件注入/更新 canary token
# 用法: bash scripts/inject-canary.sh [canary-string]
# 不传参数则自动生成
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

CANARY="${1:-pm-ws-canary-$(openssl rand -hex 4)}"
echo "=== Canary Token Injection ==="
echo "  Token: $CANARY"
echo ""

COUNT=0

# ── SKILL.md 文件：在 frontmatter 结束标记 --- 后插入 HTML 注释 ──
for f in .claude/skills/*/SKILL.md; do
    [ -f "$f" ] || continue
    # 移除已有 canary
    sed -i '' '/<!-- pm-ws-canary-/d' "$f"
    # 在第二个 --- 后插入（frontmatter 结束位置）
    awk -v canary="$CANARY" '
        BEGIN { dash_count=0; inserted=0 }
        /^---$/ { dash_count++ }
        { print }
        dash_count==2 && !inserted { print "<!-- " canary " -->"; inserted=1 }
    ' "$f" > "${f}.tmp" && mv "${f}.tmp" "$f"
    COUNT=$((COUNT + 1))
done

# ── pm-workflow.md：末尾插入 ──
WF=".claude/rules/pm-workflow.md"
if [ -f "$WF" ]; then
    sed -i '' '/<!-- pm-ws-canary-/d' "$WF"
    echo "" >> "$WF"
    echo "<!-- $CANARY -->" >> "$WF"
    COUNT=$((COUNT + 1))
fi

# ── CSS 文件：顶部插入 ──
for f in .claude/skills/*/references/*.css; do
    [ -f "$f" ] || continue
    sed -i '' '/\/\* pm-ws-canary-/d' "$f"
    sed -i '' "1i\\
/* $CANARY */
" "$f"
    COUNT=$((COUNT + 1))
done

# ── JS 文件：顶部插入 ──
for f in .claude/skills/*/references/*.js; do
    [ -f "$f" ] || continue
    sed -i '' '/\/\/ pm-ws-canary-/d' "$f"
    sed -i '' "1i\\
// $CANARY
" "$f"
    COUNT=$((COUNT + 1))
done

# ── HTML 模板：DOCTYPE 后插入 ──
for f in .claude/chat-templates/*.html .claude/skills/*/references/*.html; do
    [ -f "$f" ] || continue
    sed -i '' '/<!-- pm-ws-canary-/d' "$f"
    if grep -q '<!DOCTYPE' "$f" 2>/dev/null; then
        sed -i '' "/<!DOCTYPE/a\\
<!-- $CANARY -->
" "$f"
    else
        sed -i '' "1i\\
<!-- $CANARY -->
" "$f"
    fi
    COUNT=$((COUNT + 1))
done

# ── Python 骨架脚本：shebang 后或顶部插入 ──
for f in .claude/skills/*/references/*.py scripts/*.py; do
    [ -f "$f" ] || continue
    sed -i '' '/# pm-ws-canary-/d' "$f"
    if head -1 "$f" | grep -q '^#!'; then
        sed -i '' "1a\\
# $CANARY
" "$f"
    else
        sed -i '' "1i\\
# $CANARY
" "$f"
    fi
    COUNT=$((COUNT + 1))
done

echo "=== Done: $COUNT files injected with $CANARY ==="
echo ""
echo "Verify: grep -rl '$CANARY' .claude/ scripts/"
