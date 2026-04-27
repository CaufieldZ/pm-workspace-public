#!/bin/bash
# Scene Change Impact Check
# Usage: bash scripts/impact-check.sh <project-name>
# Compares scene-list.md against deliverables/ to find stale outputs.
# Exit: 0 = all in sync, 1 = some need update
set -euo pipefail

PROJECT="${1:?Usage: bash scripts/impact-check.sh <project-name>}"
ROOT="$(git rev-parse --show-toplevel)"
PROJECT_DIR="$ROOT/projects/$PROJECT"
SCENE_LIST="$PROJECT_DIR/scene-list.md"
DELIV_DIR="$PROJECT_DIR/deliverables"

[ -d "$PROJECT_DIR" ] || { echo "ERR: project dir not found: $PROJECT_DIR"; exit 1; }
[ -f "$SCENE_LIST" ] || { echo "ERR: scene-list.md not found"; exit 1; }
[ -d "$DELIV_DIR" ]  || { echo "ERR: deliverables/ not found"; exit 1; }

FAIL=0

# ─── Helpers ───

# Extract scene IDs from scene-list.md (A, B-1, F-0a, M-1, etc.)
extract_scene_ids() {
  grep '^|' "$1" \
    | grep -v '^|[-]' \
    | grep -v '^|.*---' \
    | sed -n 's/^|[[:space:]]*\([A-Z][A-Za-z0-9-]*\)[[:space:]]*|.*/\1/p' \
    | grep -vE '^(View|P[0-9])' \
    | sort -u
}

# Extract scene IDs referenced in a deliverable file
extract_file_ids() {
  local file="$1"
  local ext="${file##*.}"
  case "$ext" in
    html|md)
      # Multi-char IDs: B-1, F-0a, M-2, etc.
      grep -oE '\b[A-Z]-[0-9]+[a-z]?\b' "$file" 2>/dev/null || true
      # Single-letter in context: "Scene A", "scene-A", "PART A", phone-label">A ·
      # 「Scene」keyword case-insensitive, single-letter scene ID 仍要求大写以避免误匹配 (e.g. "an A...")
      grep -oiE '(scene[- ]|PART[- ]|phone-label">[[:space:]]*)([A-Z])\b' "$file" 2>/dev/null \
        | grep -oE '[A-Z]$' || true
      # md 表格首列单字符 anchor：`| E |` `| A |` 等（场景清单第一列惯例）
      if [ "$ext" = "md" ]; then
        grep -oE '^\|[[:space:]]*[A-Z][[:space:]]*\|' "$file" 2>/dev/null \
          | grep -oE '[A-Z]' || true
      fi
      ;;
    docx)
      python3 -c "
import re, sys
try:
    from docx import Document
    doc = Document('$file')
    text = '\n'.join(p.text for p in doc.paragraphs)
    cell_texts = []
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                ct = cell.text
                text += '\n' + ct
                cell_texts.append(ct.strip())
    found = set()
    for m in re.findall(r'\b([A-Z]-[0-9]+[a-z]?)\b', text):
        found.add(m)
    # Scene/PART keyword case-insensitive；single-letter scene ID 仍要求大写
    for m in re.findall(r'(?:scene|PART)[^A-Za-z]*([A-Z])\b', text, re.IGNORECASE):
        found.add(m)
    # 表格首列是惯例 anchor 列（如场景地图 T2 第 0 列）：单字符大写或 X-N 格式直接当 scene ID
    for ct in cell_texts:
        if len(ct) <= 12 and re.fullmatch(r'[A-Z](?:-[0-9]+[a-z]?)?(?:\s*[~～]\s*[A-Z](?:-[0-9]+[a-z]?)?)?', ct):
            for m in re.findall(r'[A-Z](?:-[0-9]+[a-z]?)?', ct):
                found.add(m)
    for m in sorted(found):
        print(m)
except Exception as e:
    print('ERR: ' + str(e), file=sys.stderr)
" 2>/dev/null || true
      ;;
  esac
}

# Check if scene ID is covered (direct match or parent covered by children)
# e.g. scene-list has "A" → HTML has "A-1","A-2" → "A" is covered
id_found_in() {
  local sid="$1"
  local file_ids="$2"
  # Direct match
  echo "$file_ids" | grep -qxF "$sid" && return 0
  # Parent match: single-letter ID covered by children (A → A-*)
  if echo "$sid" | grep -qE '^[A-Z]$'; then
    echo "$file_ids" | grep -qE "^${sid}-" && return 0
  fi
  return 1
}

# Infer skill type from filename (supports both prefix and Chinese naming)
infer_skill() {
  local f="$1"
  # Check common patterns (English prefix first, then Chinese keywords)
  if echo "$f" | grep -qiE 'imap|interaction|交互大图'; then echo "3:interaction-map"
  elif echo "$f" | grep -qiE 'proto|原型'; then echo "4:prototype"
  elif echo "$f" | grep -qiE 'prd|PRD'; then echo "5:prd"
  elif echo "$f" | grep -qiE '^rf-|需求框架|requirement'; then echo "2:requirement-framework"
  elif echo "$f" | grep -qiE 'arch|diagrams|架构'; then echo "2.5:architecture-diagrams"
  elif echo "$f" | grep -qiE 'bspec|行为规格'; then echo "6:behavior-spec"
  elif echo "$f" | grep -qiE 'pspec|页面结构'; then echo "6:page-structure"
  elif echo "$f" | grep -qiE '^tc-|测试用例'; then echo "7:test-cases"
  elif echo "$f" | grep -qiE 'ppt'; then echo "0:ppt"
  else echo "9:unknown"
  fi
}

# ─── Step 1: Extract IDs ───

echo "=========================================="
echo "  Scene Change Impact Check"
echo "=========================================="
echo ""

VERSION=$(grep -oE 'V[0-9]+\.[0-9]+' "$SCENE_LIST" | head -1 || echo "?")
ALL_IDS=$(extract_scene_ids "$SCENE_LIST")
TOTAL=$(echo "$ALL_IDS" | grep -c . 2>/dev/null || echo 0)

printf "Project: %s\n" "$PROJECT"
printf "Scene-List: %s (%s scenes)\n" "$VERSION" "$TOTAL"
echo ""

# ─── Version sync check (context.md vs scene-list.md) ───
CONTEXT_FILE="$PROJECT_DIR/context.md"
if [ -f "$CONTEXT_FILE" ]; then
  CTX_VER=$(grep -oE '[Vv][0-9]+(\.[0-9]+)?' "$CONTEXT_FILE" | head -1 || echo "")
  SL_VER=$(grep -oE '[Vv][0-9]+(\.[0-9]+)?' "$SCENE_LIST" | head -1 || echo "")
  if [ -n "$CTX_VER" ] && [ -n "$SL_VER" ]; then
    if [ "$CTX_VER" != "$SL_VER" ]; then
      printf "!! Version mismatch: context.md=%s  scene-list=%s\n" "$CTX_VER" "$SL_VER"
      FAIL=1
    else
      printf "Version sync: %s (OK)\n" "$SL_VER"
    fi
  fi
fi
echo ""

# Try git diff for incremental detection
DIFF_MODE="full"
ADDED_IDS=""
REMOVED_IDS=""
MODIFIED_IDS=""

if git -C "$ROOT" log --oneline -1 -- "$SCENE_LIST" >/dev/null 2>&1; then
  DIFF_OUTPUT=$(git -C "$ROOT" diff HEAD -- "$SCENE_LIST" 2>/dev/null || true)
  if [ -n "$DIFF_OUTPUT" ]; then
    DIFF_MODE="diff"
    ADDED_IDS=$(echo "$DIFF_OUTPUT" | grep '^+|' | grep -v '^+++' | grep -v '^+|[-]' \
      | sed -n 's/^+|[[:space:]]*\([A-Z][A-Za-z0-9-]*\)[[:space:]]*|.*/\1/p' \
      | sort -u || true)
    REMOVED_IDS=$(echo "$DIFF_OUTPUT" | grep '^-|' | grep -v '^---' | grep -v '^-|[-]' \
      | sed -n 's/^-|[[:space:]]*\([A-Z][A-Za-z0-9-]*\)[[:space:]]*|.*/\1/p' \
      | sort -u || true)
    if [ -n "$ADDED_IDS" ] && [ -n "$REMOVED_IDS" ]; then
      MODIFIED_IDS=$(comm -12 <(echo "$ADDED_IDS") <(echo "$REMOVED_IDS") || true)
      ADDED_IDS=$(comm -23 <(echo "$ADDED_IDS") <(echo "$REMOVED_IDS") || true)
      REMOVED_IDS=$(comm -23 <(echo "$REMOVED_IDS") <(echo "$ADDED_IDS") || true)
    fi
  fi
fi

printf -- "--- Change Detection (mode: %s) ---\n" "$DIFF_MODE"
if [ "$DIFF_MODE" = "diff" ]; then
  [ -n "$ADDED_IDS" ]    && echo "$ADDED_IDS"    | while read -r id; do echo "  + $id  (added)"; done || true
  [ -n "$MODIFIED_IDS" ] && echo "$MODIFIED_IDS" | while read -r id; do echo "  ~ $id  (modified)"; done || true
  [ -n "$REMOVED_IDS" ]  && echo "$REMOVED_IDS"  | while read -r id; do echo "  - $id  (removed)"; done || true
  if [ -z "$ADDED_IDS" ] && [ -z "$MODIFIED_IDS" ] && [ -z "$REMOVED_IDS" ]; then
    echo "  (no scene ID changes in diff, text-only)"
    echo "  falling back to full comparison"
    DIFF_MODE="full"
  fi
else
  echo "  no uncommitted diff, using full comparison"
fi
echo ""

# ─── Step 2: Scan deliverables ───

echo "--- Deliverable Impact ---"

AFFECTED=0
CLEAN=0
# temp file for results (bash 3 compat, no associative arrays)
RESULT_FILE=$(mktemp)
trap "rm -f $RESULT_FILE" EXIT

for f in "$DELIV_DIR"/*; do
  [ -f "$f" ] || continue
  filename=$(basename "$f")
  ext="${filename##*.}"
  [ -d "$f" ] && continue

  case "$ext" in
    html|md|docx) ;;
    *) continue ;;
  esac

  FILE_IDS=$(extract_file_ids "$f" | sort -u)
  SKILL_INFO=$(infer_skill "$filename")
  PIPELINE_POS="${SKILL_INFO%%:*}"
  SKILL_NAME="${SKILL_INFO##*:}"

  # Prototypes don't embed scene IDs — skip ID check, flag as manual review
  if [ "$SKILL_NAME" = "prototype" ]; then
    printf "  --  %-44s (prototype: manual review needed)\n" "$filename"
    echo "$PIPELINE_POS|$SKILL_NAME|skip" >> "$RESULT_FILE"
    continue
  fi

  MISSING=""
  STALE=""

  for sid in $ALL_IDS; do
    if ! id_found_in "$sid" "$FILE_IDS"; then
      MISSING="$MISSING $sid"
    fi
  done

  if [ "$DIFF_MODE" = "diff" ] && [ -n "$REMOVED_IDS" ]; then
    for rid in $REMOVED_IDS; do
      if echo "$FILE_IDS" | grep -qxF "$rid"; then STALE="$STALE $rid"; fi
    done
  fi

  DETAIL=""
  STATUS="OK"
  if [ -n "$MISSING" ]; then
    MISSING_LIST=$(echo "$MISSING" | xargs | tr ' ' ',')
    DETAIL="missing: $MISSING_LIST"
    STATUS="MISS"
  fi
  if [ -n "$STALE" ]; then
    [ -n "$DETAIL" ] && DETAIL="$DETAIL | " || true
    STALE_LIST=$(echo "$STALE" | xargs | tr ' ' ',')
    DETAIL="${DETAIL}stale: $STALE_LIST"
    STATUS="STALE"
  fi

  # Full mode: high missing count likely means partial View coverage (not a real problem)
  if [ "$DIFF_MODE" = "full" ] && [ -n "$MISSING" ] && [ -z "$STALE" ]; then
    MISSING_COUNT=$(echo "$MISSING" | wc -w | tr -d ' ')
    if [ "$MISSING_COUNT" -gt $((TOTAL / 2)) ]; then
      STATUS="INFO"
      DETAIL="partial coverage ($MISSING_COUNT/$TOTAL missing, may only cover some Views)"
    fi
  fi

  case "$STATUS" in
    OK)
      ICON="✅"; DETAIL="OK"; CLEAN=$((CLEAN + 1))
      ;;
    INFO)
      ICON="ℹ️"; CLEAN=$((CLEAN + 1))
      ;;
    *)
      ICON="⚠️"; AFFECTED=$((AFFECTED + 1)); FAIL=1
      ;;
  esac

  SHORT="$filename"
  [ ${#SHORT} -gt 42 ] && SHORT="${SHORT:0:39}..." || true

  printf "  %s  %-44s %s\n" "$ICON" "$SHORT" "$DETAIL"
  echo "$PIPELINE_POS|$SKILL_NAME|$STATUS|$DETAIL" >> "$RESULT_FILE"
done

echo ""

# ─── Step 3: Upgrade suggestions ───

echo "--- Upgrade Suggestions ---"

# Collect affected skills from result file (bash 3 compat)
UPGRADE_LIST=$(grep -v '|OK|' "$RESULT_FILE" | grep -v '|INFO|' | grep -v '|skip' \
  | cut -d'|' -f1-2 | sort -t'|' -k1 -n | uniq || true)

if [ -z "$UPGRADE_LIST" ]; then
  echo "  No upgrades needed"
else
  echo "  By pipeline order:"
  echo "$UPGRADE_LIST" | while IFS='|' read -r pos skill; do
    printf "  #%-4s %-24s -> upgrade needed\n" "$pos" "$skill"
  done
fi

echo ""

# ─── Summary ───

echo "=========================================="
TOTAL_FILES=$((AFFECTED + CLEAN))
if [ "$AFFECTED" -eq 0 ]; then
  printf "All %s deliverables in sync with scene-list\n" "$TOTAL_FILES"
else
  printf "%s need update, %s OK (total %s)\n" "$AFFECTED" "$CLEAN" "$TOTAL_FILES"
fi
echo "=========================================="

exit $FAIL
