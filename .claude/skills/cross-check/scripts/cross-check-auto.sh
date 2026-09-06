#!/bin/bash
# cross-check 7 维自动对账（PM 收尾时跑一次,替代部分人工走查）
#
# 用法:
#   bash .claude/skills/cross-check/scripts/cross-check-auto.sh <项目名>
#
# 7 维:
#   跨产出物一致性 4 维:
#     1. 场景编号一致(scene-list 编号 ⊆ imap/proto/prd 编号并集)
#     2. 术语一致(真相源术语表 vs 各产出物用词)
#     3. View 划分一致(scene-list View 数 == imap PART 数 == PRD 第 3+ 章数)
#     4. 业务规则一致(真相源全局规则章主表 Rule ID == PRD Rule ID)
#   单产出物完整性 3 维:
#     5. 跳转目标存在(PRD/imap 内「→ 见 X-N」目标在 scene-list 编号集合内)
#     6. 编号格式正确(scene-list 编号符合 ID_TOKEN / 多 ID 斜杠组 B-1/B-2 模式)
#     7. 必填字段(scene-list ≥ 1 行, imap ≥ 1 PART, PRD 1.2 含 Guardrail)
#
# 退出码:
#   0 = 全过
#   1 = 有 ❌ 项
#   2 = 项目不存在或缺前置文件
set +e

# skill-log: 完成率埋点（trap EXIT 按退出码 emit completed / failed）
# exit 0/1 = 校验跑完（1 = 发现 ❌ 项，属正常产出）→ completed；exit ≥2 = 前置缺失 / 崩溃 → failed
_SL_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
source "$_SL_ROOT/.claude/hooks/lib/log.sh" 2>/dev/null
trap '_rc=$?; log_event skill "cross-check" "$([ $_rc -le 1 ] && echo completed || echo failed)" 2>/dev/null' EXIT

PROJECT="${1:?用法: bash $0 <项目名>}"
PROJ_DIR="projects/$PROJECT"
[ ! -d "$PROJ_DIR" ] && { echo "❌ 项目不存在: $PROJ_DIR"; exit 2; }

SCENE_LIST="$PROJ_DIR/scene-list.md"
[ ! -f "$SCENE_LIST" ] && { echo "❌ 缺 scene-list.md: $SCENE_LIST"; exit 2; }

# 真相源（术语 / 规则维取此处）：产品线根 prd-{线}-baseline.md，或项目自带 prd-*-baseline.md（campaign 变体）
_LINE="${PROJECT%%/*}"
TRUTH_SRC=""
for _cand in "projects/$_LINE/prd-$_LINE-baseline.md" "$PROJ_DIR"/prd-*-baseline.md; do
  [ -f "$_cand" ] && { TRUTH_SRC="$_cand"; break; }
done

# 找产出物（按前缀识别 skill 类型）
IMAP_HTML=$(ls "$PROJ_DIR/deliverables"/imap-*.html 2>/dev/null | sort -V | tail -1)
PROTO_HTML=$(ls "$PROJ_DIR/deliverables"/proto-*.html 2>/dev/null | sort -V | tail -1)
# PRD：工区 md-first，优先取 md（含 deliverables/{季度}/{版本}/ 子目录，排除 scenes/ 拆分页 + archive）；无 md 再 fallback docx
# 优先 deliverables/{季度}/{版本}/ 下的 delta（迭代模型当前态），其次版本目录、最后根层；
# 同层优先三段主 delta（prd-{产品线}-{版本}.md，排除 -app/-web-tracking 等端拆分 / 补充文档），
# 无三段名再全量兜底；sort -V 防 v9 > v10 的字典序误选
_pick_prd() {  # $1=mindepth $2=maxdepth
  local picks
  picks=$(find "$PROJ_DIR/deliverables" -mindepth "$1" -maxdepth "$2" -type f -name 'prd-*.md' \
    -not -path '*/archive/*' -not -path '*-scenes/*' 2>/dev/null | awk -F/ 'split($NF,a,"-")==3' | sort -V)
  [ -z "$picks" ] && picks=$(find "$PROJ_DIR/deliverables" -mindepth "$1" -maxdepth "$2" -type f -name 'prd-*.md' \
    -not -path '*/archive/*' -not -path '*-scenes/*' 2>/dev/null | sort -V)
  echo "$picks" | tail -1
}
PRD_DOC=$(_pick_prd 3 3)
[ -z "$PRD_DOC" ] && PRD_DOC=$(_pick_prd 2 2)
[ -z "$PRD_DOC" ] && PRD_DOC=$(_pick_prd 1 1)
[ -z "$PRD_DOC" ] && PRD_DOC=$(ls "$PROJ_DIR/deliverables"/*PRD*.docx "$PROJ_DIR/deliverables"/prd-*.docx 2>/dev/null | head -1)

echo "=========================================="
echo "  cross-check 7 维自动对账: $PROJECT"
echo "=========================================="
echo "scene-list:   $SCENE_LIST"
echo "truth-src:    ${TRUTH_SRC:-（无）}"
echo "imap:         ${IMAP_HTML:-（无）}"
echo "proto:        ${PROTO_HTML:-（无）}"
echo "prd:          ${PRD_DOC:-（无）}"
echo ""

FAIL=0

python3 - "$SCENE_LIST" "$TRUTH_SRC" "$IMAP_HTML" "$PROTO_HTML" "$PRD_DOC" <<'PY'
import re, sys
from pathlib import Path

scene_list_path, truth_path, imap_path, proto_path, prd_path = sys.argv[1:6]
fail = 0

# 编号契约：与 gen_prd_skeleton._ID_PAT 对齐（多字母前缀 + 多 ID 斜杠组 B-1/B-2）。
# ID_TOKEN 用 ASCII 显式集而非 \w+（\w 含 CJK，自由文本里 "B-1月" 会被吞成一个 token）。
ID_TOKEN = r"[A-Z]+-[0-9A-Za-z]+"
ID_CELL = rf"{ID_TOKEN}(?:/{ID_TOKEN})*"

def section(n, title):
    print(f"\n--- 维度 {n}:{title} ---")

# PRD 全文读取：md 直接读文本；docx 走 python-docx（段落 + 表格单元格）。
# 返回 None 表示无 PRD 或解析失败（docx 缺 python-docx）。各维统一用此函数，不再各自 import docx。
def prd_fulltext(path):
    if not (path and Path(path).exists()):
        return None
    if path.endswith('.docx'):
        try:
            from docx import Document
            d = Document(path)
            parts = [p.text for p in d.paragraphs]
            for t in d.tables:
                for row in t.rows:
                    for cell in row.cells:
                        parts.append(cell.text)
            return '\n'.join(parts)
        except ImportError:
            return None
        except Exception:
            return None
    return Path(path).read_text(encoding='utf-8', errors='ignore')

PRD_TEXT = prd_fulltext(prd_path)

# delta PRD 识别：带「# 9. 反向合并指引」章 = 本轮迭代 delta（只触及部分场景 + 增量章而非详细需求 View）。
# delta 与 full PRD 在维度 1（场景全覆盖）/ 维度 3（View 章数 = scene-list View）的判定逻辑不同。
PRD_IS_DELTA = bool(PRD_TEXT and re.search(r'^#{1,3}\s+\d+\.\s*反向合并指引', PRD_TEXT, re.MULTILINE))

# ── 提取 scene-list 数据 ────────────────────────────────────────
scene_text = Path(scene_list_path).read_text(encoding='utf-8')
scene_ids = set()
for m in re.finditer(rf'^\|\s*({ID_CELL})\s*\|', scene_text, re.MULTILINE):
    scene_ids.update(m.group(1).split('/'))  # 多 ID 单元格 B-1/B-2 拆开入集合
view_titles_sl = re.findall(r'^##\s+View\s+(\d+)\s*·\s*(.+?)$', scene_text, re.MULTILINE)
view_count_sl = len(view_titles_sl)

# 真相源数据
truth_text = Path(truth_path).read_text(encoding='utf-8') if truth_path and Path(truth_path).exists() else ''

# ── 维度 1:场景编号一致 ─────────────────────────────────────────
section(1, "场景编号一致")
scope_ids = set()
for path, label in [(imap_path, 'imap'), (proto_path, 'proto')]:
    if path and Path(path).exists():
        text = Path(path).read_text(encoding='utf-8')
        ids = set(re.findall(rf'\b({ID_TOKEN})\b', text))
        valid = ids & scene_ids  # 只收 scene-list 已有编号,过滤误匹配
        scope_ids |= valid
        print(f"  {label}: 命中 {len(valid)} 编号")

# PRD（md 或 docx，统一走 PRD_TEXT）
prd_ids_raw = set()
if PRD_TEXT is not None:
    prd_ids_raw = set(re.findall(rf'\b({ID_TOKEN})\b', PRD_TEXT))
    prd_ids = prd_ids_raw & scene_ids  # 过滤误匹配（非 scene-list 编号）
    scope_ids |= prd_ids
    print(f"  prd:  命中 {len(prd_ids)} 编号")
elif prd_path and prd_path.endswith('.docx') and Path(prd_path).exists():
    print("  prd:  python-docx 未装,跳过 docx 扫描")

# delta PRD：本轮只触及部分场景，不要求全覆盖；改判「PRD 引用的编号都在 scene-list 内」（孤儿检测）。
# 有无配套 imap/proto 均同判——delta 整包自带 imap/proto 是标准形态，全量覆盖校验对 delta 恒假阳。
if PRD_IS_DELTA:
    orphans = sorted(
        e for e in (prd_ids_raw - scene_ids)
        # delta 增量章可能引用业务对象 / 状态 ID（非场景编号），仅校验形如 X-N 且看似场景的
        if re.fullmatch(ID_TOKEN, e)
    )
    # 真孤儿 = scene-list 完全没有该字母前缀分组（有分组只是本轮没列该号，属正常）
    sl_prefixes = {e.split('-')[0] for e in scene_ids}
    real_orphans = [e for e in orphans if e.split('-')[0] in sl_prefixes and e not in scene_ids]
    if real_orphans:
        print(f"  ❌ delta PRD 引用 {len(real_orphans)} 个 scene-list 不存在的编号: {real_orphans[:10]}")
        fail = 1
    else:
        print(f"  ✅ delta PRD 触及 {len(scope_ids)} 场景，引用编号均在 scene-list 内（delta 不要求全覆盖）")
elif scope_ids and not (scene_ids - scope_ids):
    print(f"  ✅ scene-list {len(scene_ids)} 编号全部覆盖")
elif not scope_ids:
    print(f"  ⚠️ 无 imap/proto/prd 产出物,跳过")
else:
    missing = scene_ids - scope_ids
    print(f"  ❌ scene-list {len(missing)} 编号未在任何产出物覆盖: {sorted(missing)[:10]}")
    fail = 1

# ── 维度 2:术语一致 ──────────────────────────────────────────
section(2, "术语一致")
# 提术语表：baseline「# 2. 术语词典」或 campaign 变体「## 5. 术语表」
m = re.search(r'^#{1,2}\s+(?:2\.\s*术语词典|5\.\s*术语)', truth_text, re.MULTILINE)
if m and truth_text:
    start = m.end()
    nx = re.search(r'^#{1,2}\s+\d+\.', truth_text[start:], re.MULTILINE)
    section_5 = truth_text[start:(start + nx.start()) if nx else len(truth_text)]
    # 术语表第 1 列:`| 术语 | 定义 |` 跳过表头/分隔行
    rows = re.findall(r'^\|\s*([^|]+?)\s*\|', section_5, re.MULTILINE)
    terms = {t.strip() for t in rows
             if t.strip() and not set(t.strip()) <= set('-: ')
             and t.strip() not in ('术语', '中文', '英文', '名词')}

    if not terms:
        print("  ⚠️ 真相源术语表无可解析术语,跳过")
    else:
        print(f"  真相源术语表 {len(terms)} 术语")
        # 抽 3-5 个高频术语,扫产出物是否至少出现一次
        sample = list(terms)[:8]
        miss = []
        scan_targets = []
        for path, label in [(imap_path, 'imap'), (proto_path, 'proto')]:
            if path and Path(path).exists():
                scan_targets.append((Path(path).read_text(encoding='utf-8', errors='ignore'), label))
        if PRD_TEXT is not None:
            scan_targets.append((PRD_TEXT, 'prd'))
        for text, label in scan_targets:
            for term in sample:
                if term not in text:
                    miss.append(f"{label}: '{term}'")
        if miss:
            print(f"  ⚠️ {len(miss)} 处术语在产出物中未出现(抽样 {len(sample)} 个):")
            for m in miss[:5]:
                print(f"     {m}")
            print("     不一定是错(可能术语只在真相源用),仅 warn")
        else:
            print(f"  ✅ 抽样 {len(sample)} 术语在所有产出物中均出现")
else:
    print("  ⚠️ 真相源无术语表,跳过")

# ── 维度 3:View 划分一致 ─────────────────────────────────────
section(3, "View 划分一致")
print(f"  scene-list:  {view_count_sl} View")
mismatches = []
if imap_path and Path(imap_path).exists():
    imap_text = Path(imap_path).read_text(encoding='utf-8')
    part_count = len(set(re.findall(r'id="part(\d+)"', imap_text)))
    print(f"  imap:        {part_count} PART (叙事段落,可含总览/数据流,不严格 = View)")

# View 章 = PRD「3. / 4. / 5. 详细需求」级标题。docx 数 Heading 1 段落；md 数 H1「# 3.」。
# delta PRD（# 2. 本轮需求 为主体，无 3/4/5 章）→ 0 章，跳过不误报。
view_h1_count = 0
if PRD_IS_DELTA:
    print(f"  prd:         delta PRD（3/4/5 章为增量而非详细需求 View），View 数比对不适用，跳过")
    view_h1_count = -1
elif prd_path and prd_path.endswith('.docx') and Path(prd_path).exists():
    try:
        from docx import Document
        d = Document(prd_path)
        view_h1_count = sum(
            1 for p in d.paragraphs
            if p.style and p.style.name == 'Heading 1'
            and re.match(r'^\s*[345]\.\s+', p.text)
        )
    except Exception:
        view_h1_count = -1  # 解析失败,标记跳过
elif PRD_TEXT is not None:
    view_h1_count = len(re.findall(r'^#\s+[345]\.\s+', PRD_TEXT, re.MULTILINE))

if view_h1_count > 0:
    print(f"  prd:         {view_h1_count} View 章")
    if view_h1_count != view_count_sl:
        mismatches.append(f"prd View 章 {view_h1_count} ≠ scene-list View {view_count_sl}")
elif view_h1_count == 0 and PRD_TEXT is not None:
    print(f"  prd:         无 3/4/5 详细需求章（full PRD 以「本轮需求」为主体），跳过")

if mismatches:
    for m in mismatches:
        print(f"  ⚠️ {m}（warn,叙事链路验证版 / 部分场景项目可能正常）")
else:
    print(f"  ✅ View 划分对齐（prd View 章 = scene-list View）")

# ── 维度 4:业务规则 ID 一致 ──────────────────────────────────
section(4, "业务规则 ID 一致")
# 真相源全局规则章主表 Rule ID：baseline「# 4. 全局业务规则」或 campaign 变体「## 6. 业务规则」
m = re.search(r'^#{1,2}\s+(?:4\.\s*全局业务规则|6\.\s*业务规则)', truth_text, re.MULTILINE) if truth_text else None
ctx_rule_ids = set()
if m:
    start = m.end()
    nx = re.search(r'^#{1,2}\s+\d+\.', truth_text[start:], re.MULTILINE)
    section_6 = truth_text[start:(start + nx.start()) if nx else len(truth_text)]
    # 主表 ID 列:R1 / R2 / M-1 等
    ctx_rule_ids = set(re.findall(r'^\|\s*([RM][-\d]+|\d+\.\d+)\s*\|', section_6, re.MULTILINE))

if not ctx_rule_ids:
    print("  ⚠️ 真相源全局规则章无可解析 Rule ID,跳过")
elif PRD_TEXT is not None:
    prd_rule_ids = set(re.findall(r'\b([RM]\d+|R\d+)\b', PRD_TEXT))
    common = ctx_rule_ids & prd_rule_ids
    missing_in_prd = ctx_rule_ids - prd_rule_ids
    print(f"  真相源 Rule ID:   {len(ctx_rule_ids)}")
    print(f"  prd 命中:         {len(common)}")
    if missing_in_prd:
        print(f"  ⚠️ 真相源中 {len(missing_in_prd)} 个 Rule ID 在 prd 未引用: {sorted(missing_in_prd)[:8]}")
        print("     不一定是错(部分规则可能不需进 PRD),仅 warn")
    else:
        print(f"  ✅ 真相源全部 Rule ID 在 prd 中引用")
else:
    print(f"  真相源 Rule ID: {len(ctx_rule_ids)},无 prd 跳过对比")

# ── 维度 5:跳转目标存在 ────────────────────────────────────
section(5, "跳转目标存在")
broken = []
for path, label in [(imap_path, 'imap'), (proto_path, 'proto')]:
    if path and Path(path).exists():
        text = Path(path).read_text(encoding='utf-8', errors='ignore')
        targets = re.findall(rf'→\s*见\s*({ID_CELL})', text)
        for t in targets:
            for tid in t.split('/'):
                if tid not in scene_ids:
                    broken.append(f"{label}: → 见 {tid}")
if PRD_TEXT is not None:
    targets = re.findall(rf'→\s*见\s*({ID_CELL})', PRD_TEXT)
    for t in targets:
        for tid in t.split('/'):
            if tid not in scene_ids:
                broken.append(f"prd: → 见 {tid}")

if broken:
    print(f"  ❌ {len(broken)} 处跳转目标不在 scene-list 编号集合:")
    for b in broken[:10]:
        print(f"     {b}")
    fail = 1
else:
    print(f"  ✅ 所有「→ 见 X-N」跳转目标存在")

# ── 维度 6:编号格式 ────────────────────────────────────────
section(6, "编号格式正确")
# 编号契约同头部 ID_TOKEN/ID_CELL（与 gen_prd_skeleton._ID_PAT 对齐，多 ID 斜杠组 B-1/B-2 合法）。
# 只校验「场景主表」第一列：
# 表头第一格 == '编号' 才纳入。跳转 / 影响关系表（表头「触发」「动作」等）首列是
# 「A-1 主播认证通过」这种「编号+描述」同格，不是场景定义，扫了纯误报。
weird = []
in_scene_table = False  # 当前数据行是否属于 header 第一格为「编号」的表
lines = scene_text.split('\n')
for i, line in enumerate(lines):
    m = re.match(r'^\|\s*([^|]*?)\s*\|', line)
    if not m:
        in_scene_table = False
        continue
    cell = m.group(1).strip()
    # 分隔行（|---|）：上一行是表头，据其首格判定本表是否场景主表
    if set(cell) <= set('-: ') and cell:
        hm = re.match(r'^\|\s*([^|]*?)\s*\|', lines[i - 1]) if i > 0 else None
        in_scene_table = bool(hm and hm.group(1).strip() == '编号')
        continue
    if not in_scene_table or not cell or cell == '编号':
        continue
    if re.match(r'^View\s+\d+', cell, re.IGNORECASE):
        continue
    if not re.fullmatch(ID_CELL, cell):
        weird.append(cell)

if weird:
    print(f"  ❌ {len(weird)} 个编号格式异常: {weird[:5]}")
    fail = 1
else:
    print(f"  ✅ scene-list {len(scene_ids)} 编号全部符合 ID_TOKEN / 多 ID 斜杠组格式")

# ── 维度 7:必填字段 ──────────────────────────────────────
section(7, "必填字段")
checks = []
if len(scene_ids) == 0:
    checks.append("scene-list 0 行（必须 ≥ 1）")
if imap_path and Path(imap_path).exists():
    imap_text = Path(imap_path).read_text(encoding='utf-8')
    if 'id="part' not in imap_text:
        checks.append("imap 无 PART 容器（id=\"partN\"）")
if PRD_TEXT is not None:
    if not any(kw in PRD_TEXT for kw in ('Guardrail', '反向指标', '不能恶化', '反向')):
        checks.append("prd 1.2 段无 Guardrail 关键词")

if checks:
    for c in checks:
        print(f"  ❌ {c}")
    fail = 1
else:
    print(f"  ✅ 必填字段齐全")

print("\n==========================================")
if fail:
    print("❌ cross-check 自动对账未通过（见上方 ❌ 项）")
    sys.exit(1)
else:
    print("✅ cross-check 7 维全部通过")
PY
EXIT=$?

echo "=========================================="
exit $EXIT
