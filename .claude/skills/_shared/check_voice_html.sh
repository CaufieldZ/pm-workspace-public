#!/usr/bin/env bash
# 共享：IMAP / prototype HTML 综合自检外壳（check_imap.sh + check_proto.sh 合并）
#
# 用法: bash check_voice_html.sh <kind> <html> [<scene-list.md>]
#   kind ∈ {imap, proto}
#
# 业务逻辑全在 scripts/lib/run_voice_checks.py（kind 参数化）；
# imap 额外跑 _validators.validate_ann_card_four_bans（§9 ann-card 四禁）。
# 本文件只做参数解析 + scene-list 自动推断 + 日志埋点。
#
# 退出码:
#   0 = 通过（含 warn 也算过）
#   1 = FAIL（结构 / 编号 / 组件 / 内部代号 / ann-card 四禁违规）
#   2 = 共享 lib 加载失败 / 参数错误

set +e

KIND="$1"
HTML="$2"
SCENE_LIST="${3:-}"

case "$KIND" in
  imap)  SKILL_NAME="interaction-map"; LABEL="IMAP" ;;
  proto) SKILL_NAME="prototype";       LABEL="prototype" ;;
  *) echo "❌ 未知 kind: '$KIND'（应为 imap / proto）" >&2; exit 2 ;;
esac

_SL_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
source "$_SL_ROOT/.claude/hooks/lib/log.sh" 2>/dev/null
trap '_rc=$?; log_event skill "'"$SKILL_NAME"'" "$([ $_rc -eq 0 ] && echo completed || echo failed)" 2>/dev/null' EXIT

if [ -z "$HTML" ]; then
  echo "用法: bash $0 $KIND <html> [<scene-list.md>]" >&2
  exit 2
fi
[ ! -f "$HTML" ] && { echo "❌ 文件不存在: $HTML" >&2; exit 2; }

if [ -z "$SCENE_LIST" ]; then
  PROJ_DIR=$(echo "$HTML" | sed -E 's|.*(projects/[^/]+/[^/]+)/deliverables/.*|\1|; s|.*(projects/[^/]+)/deliverables/.*|\1|')
  if [ -n "$PROJ_DIR" ] && [ -f "$_SL_ROOT/$PROJ_DIR/scene-list.md" ]; then
    SCENE_LIST="$_SL_ROOT/$PROJ_DIR/scene-list.md"
  fi
fi

echo "=========================================="
echo "  $LABEL 自检: $(basename "$HTML")"
echo "=========================================="
[ -n "$SCENE_LIST" ] && echo "  对照 scene-list: $SCENE_LIST"

python3 - "$KIND" "$HTML" "$SCENE_LIST" "$_SL_ROOT" "$SKILL_NAME" <<'PY'
import sys, os
kind = sys.argv[1]
html_path = sys.argv[2]
scene_list_path = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
proj_root = sys.argv[4] if len(sys.argv) > 4 else os.environ.get('CLAUDE_PROJECT_DIR', '.')
skill_name = sys.argv[5]

sys.path.insert(0, os.path.join(proj_root, 'scripts'))
sys.path.insert(0, os.path.join(proj_root, '.claude/skills', skill_name, 'scripts'))

try:
    from lib.run_voice_checks import run_voice_checks
except ImportError as e:
    print(f'❌ 共享 lib 加载失败，自检不可信: {e}', file=sys.stderr)
    print('   修法：检查 scripts/lib/ 路径与 __init__.py，重启 session', file=sys.stderr)
    sys.exit(2)

voice_rc = run_voice_checks(
    kind=kind,
    html_path=html_path,
    scene_list_path=scene_list_path,
)

if kind != 'imap':
    sys.exit(voice_rc)

# imap 额外：§9 ann-card 四禁 + §10 anno-n ↔ ann-num 对应
try:
    from _validators import validate_ann_card_four_bans, validate_anno_correspondence
except ImportError as e:
    print(f'❌ _validators 加载失败: {e}', file=sys.stderr)
    sys.exit(2)

print()
print('--- §9. ann-card 四禁 ---')
findings = validate_ann_card_four_bans(html_path)
fail_findings = [m for s, m in findings if s == 'FAIL']
warn_findings = [m for s, m in findings if s == 'WARN']

if not findings:
    print('  ✅ ann-card 四禁全过')
else:
    for msg in fail_findings:
        print(f'  ❌ {msg}')
    for msg in warn_findings:
        print(f'  ⚠️  {msg}')
    print(f'  汇总：{len(fail_findings)} FAIL · {len(warn_findings)} WARN')

print()
print('--- §10. anno-n ↔ ann-num 对应（规则 2/4）---')
anno_findings = validate_anno_correspondence(html_path)
anno_fail = [m for s, m in anno_findings if s == 'FAIL']
if not anno_fail:
    print('  ✅ anno-n / ann-num 编号对应一致')
else:
    for msg in anno_fail:
        print(f'  ❌ {msg}')
    print(f'  汇总：{len(anno_fail)} FAIL')

sys.exit(1 if (voice_rc == 1 or fail_findings or anno_fail) else voice_rc)
PY
