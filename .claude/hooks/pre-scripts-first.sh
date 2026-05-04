#!/bin/bash
# PreToolUse hook: Skill 微调场景「脚本优先」强制检查
# 命中手写 python-docx / 绕过 skill helper 的操作时 stderr 警告
# 当前覆盖: PRD docx 修改 (.claude/skills/prd/scripts/update_prd_base.py)
# 设计: warn 不 block,误报成本低于漏报

set +e

source "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/lib/log.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

print_prd_warning() {
  echo "" >&2
  echo "⚠️  检测到手写 python-docx 调用,可能绕过 Skill helper" >&2
  echo "   PRD docx 局部修改应优先走 .claude/skills/prd/scripts/update_prd_base.py:" >&2
  echo "     - set_cell_blocks(cell, blocks, numbered=True)  自动生成 1. 2. 3. 编号 + 字体" >&2
  echo "     - replace_para_text(para, new_text)            替换段落文案保字体" >&2
  echo "     - search_replace_para(para, old, new)          段落内 find-replace" >&2
  echo "     - insert_scene_blocks / insert_paragraph_before 插入新块" >&2
  echo "   完整列表: grep -n '^def ' .claude/skills/prd/scripts/update_prd_base.py" >&2
  echo "   如确需手写 (helper 不覆盖的场景),说明理由后继续即可" >&2
  echo "" >&2
}

# 白名单: 在维护 helper 本身 / 已经在用 helper
is_whitelisted() {
  echo "$1" | grep -qE 'update_prd_base|gen_prd_base|\.claude/skills/prd/scripts/'
}

# 检测 python-docx 原生调用 (排除 update_prd_base 这类合法 import)
has_raw_docx_import() {
  echo "$1" | grep -qE '(from docx import|from docx\.|^import docx$|[^_a-zA-Z0-9]import docx[^_a-zA-Z0-9])'
}

case "$TOOL_NAME" in
  Bash)
    CMD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)
    if has_raw_docx_import "$CMD" && ! is_whitelisted "$CMD"; then
      print_prd_warning
      log_event hook scripts-first warn "raw docx import in Bash"
    fi
    ;;
  Write|Edit)
    FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)
    case "$FILE_PATH" in
      *.claude/skills/*) exit 0 ;;
    esac
    CONTENT=$(echo "$INPUT" | python3 -c "import sys,json; t=json.load(sys.stdin).get('tool_input',{}); print(t.get('content','') or t.get('new_string',''))" 2>/dev/null)
    if has_raw_docx_import "$CONTENT" && ! is_whitelisted "$CONTENT"; then
      print_prd_warning
      log_event hook scripts-first warn "raw docx import in Write/Edit: $FILE_PATH"
    fi
    # 首次大 HTML 拦截：projects/ 下 .html 直接 Write > 200 行 → 必须先写 gen 脚本
    # 注：「已脚本化 HTML 拦截」由 pre-deliverable-source-gate 唯一负责（按 type 精准匹配 + 认 SKIP_DELIVERABLE_GATE=1 出口），本 hook 不再重复
    if [ "$TOOL_NAME" = "Write" ] && \
       echo "$FILE_PATH" | grep -qE 'projects/[^/]+/.*\.html$' && \
       ! echo "$FILE_PATH" | grep -qE '/(archive|inputs|screenshots|scripts|sop-src)/'; then
      LINE_COUNT=$(echo "$CONTENT" | wc -l | tr -d ' ')
      if [ "$LINE_COUNT" -gt 200 ]; then
        # 抽项目目录：两层（产品线/项目）→ 一层（顶级）
        PROJECT_DIR=$(echo "$FILE_PATH" | sed -nE 's#(.*projects/[^/]+/[^/]+)/(deliverables|scripts|inputs|screenshots).*#\1#p')
        [ -z "$PROJECT_DIR" ] && PROJECT_DIR=$(echo "$FILE_PATH" | sed -nE 's#(.*projects/[^/]+)/(deliverables|scripts|inputs|screenshots).*#\1#p')
        [ -z "$PROJECT_DIR" ] && PROJECT_DIR=$(echo "$FILE_PATH" | sed -E 's#(.*projects/[^/]+)/.*#\1#')
        echo "❌ 首次生成 >200 行 HTML 禁止直接 Write（${LINE_COUNT} 行）" >&2
        echo "   应先写 gen 脚本到 ${PROJECT_DIR}/scripts/gen_*.py，再 python3 执行生成" >&2
        log_event hook scripts-first block "large first-gen html: $FILE_PATH $LINE_COUNT lines"
        exit 2
      fi
    fi
    ;;
esac

exit 0
