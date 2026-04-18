#!/usr/bin/env bash
# sync_colleague.sh — 把 pm-workspace 框架层同步给公司内部同事试用
# 用法: ./sync_colleague.sh [colleague_repo_path]
# 默认路径: ~/pm-workspace-for-colleague
#
# 与 sync_public.sh 区别：
#   - sync_public: 对外脱敏（HTX→Platform），用于 GitHub 公开 repo
#   - sync_colleague: 内部同事用，保留公司术语，仅去掉凭证/业务/个人内容
set -euo pipefail

PRIVATE_ROOT="$(cd "$(dirname "$0")" && pwd)"
COLLEAGUE_ROOT="${1:-$HOME/pm-workspace-for-colleague}"

echo "=== pm-workspace → colleague sync ==="
echo "  Source:  $PRIVATE_ROOT"
echo "  Target:  $COLLEAGUE_ROOT"
echo ""

# ── 0. 初始化目标目录 ──────────────────────────────────────────
FIRST_RUN=false
if [ ! -d "$COLLEAGUE_ROOT" ]; then
    mkdir -p "$COLLEAGUE_ROOT"
    FIRST_RUN=true
    echo "[init] Created $COLLEAGUE_ROOT"
fi

# ── 1. rsync 框架文件（排除凭证/业务/个人）────────────────────
echo "[rsync] Syncing framework files..."
rsync -a --delete \
    --exclude='.git/' \
    --exclude='.DS_Store' \
    --exclude='.env' \
    --exclude='.mcp.json' \
    --exclude='.claude/settings.local.json' \
    --exclude='.claude/projects/' \
    --exclude='.claude/skills/intel-collector/references/auth/' \
    --exclude='.claude/rules/soul.md' \
    --exclude='projects/' \
    --exclude='/references/' \
    --exclude='/deliverables/' \
    --exclude='**/.private/' \
    --exclude='.public/' \
    --exclude='node_modules/' \
    --exclude='package-lock.json' \
    --exclude='__pycache__/' \
    --exclude='*.bak' \
    --exclude='/tmp/' \
    --exclude='sync_public.sh' \
    --exclude='sync_colleague.sh' \
    "$PRIVATE_ROOT/" "$COLLEAGUE_ROOT/"

# ── 2. 生成 .env.example（脱敏模板）───────────────────────────
cat > "$COLLEAGUE_ROOT/.env.example" <<'EOF'
# Slack 通知机器人 token（intel-collector skill 用到，不需要可留空）
SLACK_BOT_TOKEN=
EOF
echo "[template] .env.example"

# ── 3. 生成 .mcp.json.example（凭证替换成占位符）──────────────
cat > "$COLLEAGUE_ROOT/.mcp.json.example" <<'EOF'
{
  "mcpServers": {
    "figma-local": {
      "command": "npx",
      "args": ["-y", "figma-developer-mcp", "--stdio"],
      "env": {
        "FIGMA_API_KEY": "YOUR_FIGMA_API_KEY_HERE"
      }
    },
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "YOUR_FIRECRAWL_API_KEY_HERE"
      }
    },
    "confluence": {
      "command": "npx",
      "args": ["-y", "confluence-mcp-server"],
      "env": {
        "CONF_MODE": "server",
        "CONF_BASE_URL": "https://INTERNAL_URL_REDACTED",
        "CONF_AUTH_MODE": "bearer",
        "CONF_TOKEN": "YOUR_CONFLUENCE_BEARER_TOKEN_HERE"
      }
    },
    "sensors": {
      "command": "node",
      "args": ["/PATH/TO/SensorsMCPServer/dist/index.js"],
      "env": {
        "SA_URL": "https://INTERNAL_URL_REDACTED",
        "SA_PROJECT": "production",
        "SA_API_KEY": "YOUR_SENSORS_API_KEY_HERE",
        "SA_API_SECRET": "YOUR_SENSORS_API_SECRET_HERE"
      }
    }
  }
}
EOF
echo "[template] .mcp.json.example"

# ── 4. 拷贝 SETUP.md（从模板）────────────────────────────────────
SETUP_SRC="$PRIVATE_ROOT/.public/overrides/SETUP.md"
if [ -f "$SETUP_SRC" ]; then
    cp "$SETUP_SRC" "$COLLEAGUE_ROOT/SETUP.md"
    echo "[template] SETUP.md"
else
    echo "[WARN] $SETUP_SRC not found"
fi

# ── 4.5. 注入版权水印头 ──────────────────────────────────────────
echo "[watermark] Injecting protection headers..."
HEADER_MD='<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->'
HEADER_HTML='<!-- PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->'
HEADER_CSS='/* PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 */'
HEADER_PY='# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction'
HEADER_JS='// PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏'
HEADER_SH='# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction'

# .md (skip README/AI-TRAINING which have their own notices)
find "$COLLEAGUE_ROOT" -name '*.md' -not -name 'README.md' -not -name 'AI-TRAINING-RESTRICTION.md' -not -path '*/.git/*' | while read f; do
    grep -q 'PM-Workspace.*AI Training' "$f" 2>/dev/null || sed -i '' "1i\\
$HEADER_MD
" "$f"
done
# .css
find "$COLLEAGUE_ROOT" -name '*.css' -not -path '*/.git/*' | while read f; do
    grep -q 'PM-Workspace.*AI Training' "$f" 2>/dev/null || sed -i '' "1i\\
$HEADER_CSS
" "$f"
done
# .html (after DOCTYPE if present)
find "$COLLEAGUE_ROOT" -name '*.html' -not -path '*/.git/*' | while read f; do
    grep -q 'PM-Workspace.*AI Training' "$f" 2>/dev/null || {
        if grep -q '<!DOCTYPE' "$f" 2>/dev/null; then
            sed -i '' "/<!DOCTYPE/a\\
$HEADER_HTML
" "$f"
        else
            sed -i '' "1i\\
$HEADER_HTML
" "$f"
        fi
    }
done
# .py (after shebang if present; handle empty files)
find "$COLLEAGUE_ROOT" -name '*.py' -not -path '*/.git/*' | while read f; do
    grep -q 'PM-Workspace.*AI Training' "$f" 2>/dev/null || {
        if [ ! -s "$f" ]; then
            echo "$HEADER_PY" > "$f"
        elif head -1 "$f" | grep -q '^#!'; then
            sed -i '' "1a\\
$HEADER_PY
" "$f"
        else
            sed -i '' "1i\\
$HEADER_PY
" "$f"
        fi
    }
done
# .js
find "$COLLEAGUE_ROOT" -name '*.js' -not -path '*/.git/*' -not -path '*/node_modules/*' | while read f; do
    grep -q 'PM-Workspace.*AI Training' "$f" 2>/dev/null || sed -i '' "1i\\
$HEADER_JS
" "$f"
done
# .sh (after shebang if present)
find "$COLLEAGUE_ROOT" -name '*.sh' -not -path '*/.git/*' | while read f; do
    grep -q 'PM-Workspace.*AI Training' "$f" 2>/dev/null || {
        if head -1 "$f" | grep -q '^#!'; then
            sed -i '' "1a\\
$HEADER_SH
" "$f"
        else
            sed -i '' "1i\\
$HEADER_SH
" "$f"
        fi
    }
done
echo "[watermark] Done"

# ── 5. 扫描残留凭证 ────────────────────────────────────────────
echo ""
echo "=== Scanning for residual credentials... ==="
LEAK=$(grep -rn -E '(xoxb-[0-9]+|figd_[A-Za-z0-9_-]+|fc-[a-f0-9]{32}|MjE0Njk|ef08fd170940)' "$COLLEAGUE_ROOT" \
    --include='*.json' --include='*.md' --include='*.sh' --include='*.py' --include='*.env' 2>/dev/null | grep -v '.example' | grep -v '.git/' || true)
if [ -n "$LEAK" ]; then
    echo "[FAIL] Credential leak detected:"
    echo "$LEAK"
    echo ""
    echo "Fix these before sharing!"
    exit 1
fi
echo "[OK] No credentials found in output"

# ── 5.5. 扫描个人信息（用户名/路径/邮箱/Git 身份）────────────
echo ""
echo "=== Scanning for personal info... ==="
PII=$(grep -rn -iE '(felix\.zhi|felixzhi|CaufieldZ|huajiangxiashu|/Users/felix)' "$COLLEAGUE_ROOT" \
    --include='*.md' --include='*.json' --include='*.sh' --include='*.py' --include='*.js' --include='*.css' --include='*.html' --include='*.txt' 2>/dev/null | grep -v '.git/' || true)
if [ -n "$PII" ]; then
    echo "[WARN] Personal identifiers found:"
    echo "$PII"
    echo ""
    echo "Review these before sharing — may just be harmless references."
else
    echo "[OK] No personal identifiers found"
fi

# ── 6. git 初始化 + 首次 commit ───────────────────────────────
cd "$COLLEAGUE_ROOT"
if [ ! -d .git ]; then
    git init -q
    git add -A
    git -c user.name="pm-workspace" -c user.email="pm-workspace@local" \
        commit -q -m "Initial import from pm-workspace framework

Source: pm-workspace (internal framework)
Excluded: credentials, business projects, personal preferences
See SETUP.md for configuration steps."
    echo "[git] Initialized new repo with initial commit"
else
    CHANGES=$(git status --porcelain | wc -l | tr -d ' ')
    if [ "$CHANGES" -gt 0 ]; then
        git add -A
        git -c user.name="pm-workspace" -c user.email="pm-workspace@local" \
            commit -q -m "sync: update framework from upstream ($CHANGES files)"
        echo "[git] Committed $CHANGES file changes"
    else
        echo "[git] No changes"
    fi
fi

# ── 7. 汇总 ────────────────────────────────────────────────────
echo ""
echo "=== Done ==="
echo "  Location: $COLLEAGUE_ROOT"
echo "  Skills:   $(ls "$COLLEAGUE_ROOT/.claude/skills/" | wc -l | tr -d ' ') 个"
echo "  Size:     $(du -sh "$COLLEAGUE_ROOT" | cut -f1)"
echo ""
echo "下一步："
echo "  1. 目录压包发给同事：tar czf pm-workspace-for-colleague.tgz -C $HOME pm-workspace-for-colleague"
echo "  2. 或直接让同事 rsync 拷贝：rsync -av $COLLEAGUE_ROOT/ ~/pm-workspace/"
echo "  3. 同事按 SETUP.md 配置"
