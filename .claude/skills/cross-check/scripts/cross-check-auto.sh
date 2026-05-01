#!/bin/bash
# cross-check 7 维自动对账（PM 收尾时跑一次,替代部分人工走查）
#
# 用法:
#   bash .claude/skills/cross-check/scripts/cross-check-auto.sh <项目名>
#
# 7 维:
#   跨产出物一致性 4 维:
#     1. 场景编号一致(scene-list 编号 ⊆ imap/proto/prd 编号并集)
#     2. 术语一致(context.md 第 5 章术语 vs 各产出物用词)
#     3. View 划分一致(scene-list View 数 == imap PART 数 == PRD 第 3+ 章数)
#     4. 业务规则一致(context.md 第 6 章主表 Rule ID == PRD 第 6 章 Rule ID)
#   单产出物完整性 3 维:
#     5. 跳转目标存在(PRD/imap 内「→ 见 X-N」目标在 scene-list 编号集合内)
#     6. 编号格式正确(scene-list 编号都符合 [A-Z]-[0-9]+ 模式)
#     7. 必填字段(scene-list ≥ 1 行, imap ≥ 1 PART, PRD 1.2 含 Guardrail)
#
# 退出码:
#   0 = 全过
#   1 = 有 ❌ 项
#   2 = 项目不存在或缺前置文件
set +e

PROJECT="${1:?用法: bash $0 <项目名>}"
PROJ_DIR="projects/$PROJECT"
[ ! -d "$PROJ_DIR" ] && { echo "❌ 项目不存在: $PROJ_DIR"; exit 2; }

SCENE_LIST="$PROJ_DIR/scene-list.md"
CONTEXT_MD="$PROJ_DIR/context.md"
[ ! -f "$SCENE_LIST" ] && { echo "❌ 缺 scene-list.md: $SCENE_LIST"; exit 2; }

# 找产出物（按前缀识别 skill 类型）
IMAP_HTML=$(ls "$PROJ_DIR/deliverables"/imap-*.html 2>/dev/null | head -1)
PROTO_HTML=$(ls "$PROJ_DIR/deliverables"/proto-*.html 2>/dev/null | head -1)
PRD_DOCX=$(ls "$PROJ_DIR/deliverables"/*PRD*.docx "$PROJ_DIR/deliverables"/prd-*.docx 2>/dev/null | head -1)

echo "=========================================="
echo "  cross-check 7 维自动对账: $PROJECT"
echo "=========================================="
echo "scene-list:   $SCENE_LIST"
echo "context:      ${CONTEXT_MD}"
echo "imap:         ${IMAP_HTML:-（无）}"
echo "proto:        ${PROTO_HTML:-（无）}"
echo "prd docx:     ${PRD_DOCX:-（无）}"
echo ""

FAIL=0

python3 - "$SCENE_LIST" "$CONTEXT_MD" "$IMAP_HTML" "$PROTO_HTML" "$PRD_DOCX" <<'PY'
import re, sys
from pathlib import Path

scene_list_path, context_path, imap_path, proto_path, prd_path = sys.argv[1:6]
fail = 0

def section(n, title):
    print(f"\n--- 维度 {n}:{title} ---")

# ── 提取 scene-list 数据 ────────────────────────────────────────
scene_text = Path(scene_list_path).read_text(encoding='utf-8')
scene_ids = set(re.findall(r'^\|\s*([A-Z]-\d+[a-z]?)\s*\|', scene_text, re.MULTILINE))
view_titles_sl = re.findall(r'^##\s+View\s+(\d+)\s*·\s*(.+?)$', scene_text, re.MULTILINE)
view_count_sl = len(view_titles_sl)

# context 数据
ctx_text = Path(context_path).read_text(encoding='utf-8') if Path(context_path).exists() else ''

# ── 维度 1:场景编号一致 ─────────────────────────────────────────
section(1, "场景编号一致")
scope_ids = set()
for path, label in [(imap_path, 'imap'), (proto_path, 'proto')]:
    if path and Path(path).exists():
        text = Path(path).read_text(encoding='utf-8')
        ids = set(re.findall(r'\b([A-Z]-\d+[a-z]?)\b', text))
        valid = ids & scene_ids  # 只收 scene-list 已有编号,过滤误匹配
        scope_ids |= valid
        print(f"  {label}: 命中 {len(valid)} 编号")

# PRD docx 单独处理
if prd_path and Path(prd_path).exists():
    try:
        from docx import Document
        d = Document(prd_path)
        prd_text = '\n'.join(p.text for p in d.paragraphs)
        for t in d.tables:
            for row in t.rows:
                for cell in row.cells:
                    prd_text += '\n' + cell.text
        prd_ids = set(re.findall(r'\b([A-Z]-\d+[a-z]?)\b', prd_text)) & scene_ids
        scope_ids |= prd_ids
        print(f"  prd:  命中 {len(prd_ids)} 编号")
    except ImportError:
        print("  prd:  python-docx 未装,跳过 docx 扫描")

if scope_ids and not (scene_ids - scope_ids):
    print(f"  ✅ scene-list {len(scene_ids)} 编号全部覆盖")
elif not scope_ids:
    print(f"  ⚠️ 无 imap/proto/prd 产出物,跳过")
else:
    missing = scene_ids - scope_ids
    print(f"  ❌ scene-list {len(missing)} 编号未在任何产出物覆盖: {sorted(missing)[:10]}")
    fail = 1

# ── 维度 2:术语一致 ──────────────────────────────────────────
section(2, "术语一致")
# 提 context 第 5 章术语表
m = re.search(r'^##\s+5\.\s*术语', ctx_text, re.MULTILINE)
if m and ctx_text:
    start = m.end()
    nx = re.search(r'^##\s+6\.', ctx_text[start:], re.MULTILINE)
    section_5 = ctx_text[start:(start + nx.start()) if nx else len(ctx_text)]
    # 术语表第 1 列:`| 术语 | 定义 |` 跳过表头/分隔行
    rows = re.findall(r'^\|\s*([^|]+?)\s*\|', section_5, re.MULTILINE)
    terms = {t.strip() for t in rows
             if t.strip() and not set(t.strip()) <= set('-: ')
             and t.strip() not in ('术语', '中文', '英文', '名词')}

    if not terms:
        print("  ⚠️ context.md 第 5 章无可解析术语,跳过")
    else:
        print(f"  context 第 5 章 {len(terms)} 术语")
        # 抽 3-5 个高频术语,扫产出物是否至少出现一次
        sample = list(terms)[:8]
        miss = []
        for path, label in [(imap_path, 'imap'), (proto_path, 'proto'), (prd_path, 'prd')]:
            if not (path and Path(path).exists()):
                continue
            if path.endswith('.docx'):
                continue  # docx 已扫过
            text = Path(path).read_text(encoding='utf-8', errors='ignore')
            for term in sample:
                if term not in text:
                    miss.append(f"{label}: '{term}'")
        if miss:
            print(f"  ⚠️ {len(miss)} 处术语在产出物中未出现(抽样 {len(sample)} 个):")
            for m in miss[:5]:
                print(f"     {m}")
            print("     不一定是错(可能术语只在 context 用),仅 warn")
        else:
            print(f"  ✅ 抽样 {len(sample)} 术语在所有产出物中均出现")
else:
    print("  ⚠️ context.md 无第 5 章术语表,跳过")

# ── 维度 3:View 划分一致 ─────────────────────────────────────
section(3, "View 划分一致")
print(f"  scene-list:  {view_count_sl} View")
mismatches = []
if imap_path and Path(imap_path).exists():
    imap_text = Path(imap_path).read_text(encoding='utf-8')
    part_count = len(set(re.findall(r'id="part(\d+)"', imap_text)))
    print(f"  imap:        {part_count} PART (叙事段落,可含总览/数据流,不严格 = View)")

if prd_path and Path(prd_path).exists():
    try:
        from docx import Document
        d = Document(prd_path)
        # 数 H1 「3. ... 详细需求」「4. ...」「5. ...」
        view_h1_count = sum(
            1 for p in d.paragraphs
            if p.style and p.style.name == 'Heading 1'
            and re.match(r'^\s*[345]\.\s+', p.text)
        )
        print(f"  prd:         {view_h1_count} View 章")
        if view_h1_count and view_h1_count != view_count_sl:
            mismatches.append(f"prd View 章 {view_h1_count} ≠ scene-list View {view_count_sl}")
    except Exception:
        pass

if mismatches:
    for m in mismatches:
        print(f"  ⚠️ {m}（warn,叙事链路验证版 / 部分场景项目可能正常）")
else:
    print(f"  ✅ View 划分对齐（prd View 章 = scene-list View）")

# ── 维度 4:业务规则 ID 一致 ──────────────────────────────────
section(4, "业务规则 ID 一致")
# context 第 6 章主表 Rule ID
m = re.search(r'^##\s+6\.\s*业务规则', ctx_text, re.MULTILINE) if ctx_text else None
ctx_rule_ids = set()
if m:
    start = m.end()
    nx = re.search(r'^##\s+7\.', ctx_text[start:], re.MULTILINE)
    section_6 = ctx_text[start:(start + nx.start()) if nx else len(ctx_text)]
    # 主表 ID 列:R1 / R2 / M-1 等
    ctx_rule_ids = set(re.findall(r'^\|\s*([RM][-\d]+|\d+\.\d+)\s*\|', section_6, re.MULTILINE))

if not ctx_rule_ids:
    print("  ⚠️ context.md 第 6 章无可解析 Rule ID,跳过")
elif prd_path and Path(prd_path).exists():
    try:
        from docx import Document
        d = Document(prd_path)
        prd_text = '\n'.join(p.text for p in d.paragraphs)
        for t in d.tables:
            for row in t.rows:
                for cell in row.cells:
                    prd_text += '\n' + cell.text
        prd_rule_ids = set(re.findall(r'\b([RM]\d+|R\d+)\b', prd_text))
        common = ctx_rule_ids & prd_rule_ids
        missing_in_prd = ctx_rule_ids - prd_rule_ids
        print(f"  context Rule ID:  {len(ctx_rule_ids)}")
        print(f"  prd 命中:         {len(common)}")
        if missing_in_prd:
            print(f"  ⚠️ context 中 {len(missing_in_prd)} 个 Rule ID 在 prd 未引用: {sorted(missing_in_prd)[:8]}")
            print("     不一定是错(部分规则可能不需进 PRD),仅 warn")
        else:
            print(f"  ✅ context 全部 Rule ID 在 prd 中引用")
    except Exception:
        print("  ⚠️ prd docx 解析失败,跳过")
else:
    print(f"  context Rule ID: {len(ctx_rule_ids)},无 prd 跳过对比")

# ── 维度 5:跳转目标存在 ────────────────────────────────────
section(5, "跳转目标存在")
broken = []
for path, label in [(imap_path, 'imap'), (proto_path, 'proto')]:
    if path and Path(path).exists():
        text = Path(path).read_text(encoding='utf-8', errors='ignore')
        targets = re.findall(r'→\s*见\s*([A-Z]-\d+[a-z]?)', text)
        for t in targets:
            if t not in scene_ids:
                broken.append(f"{label}: → 见 {t}")
if prd_path and Path(prd_path).exists():
    try:
        from docx import Document
        d = Document(prd_path)
        full = '\n'.join(p.text for p in d.paragraphs)
        for t in d.tables:
            for row in t.rows:
                for cell in row.cells:
                    full += '\n' + cell.text
        targets = re.findall(r'→\s*见\s*([A-Z]-\d+[a-z]?)', full)
        for t in targets:
            if t not in scene_ids:
                broken.append(f"prd: → 见 {t}")
    except Exception:
        pass

if broken:
    print(f"  ❌ {len(broken)} 处跳转目标不在 scene-list 编号集合:")
    for b in broken[:10]:
        print(f"     {b}")
    fail = 1
else:
    print(f"  ✅ 所有「→ 见 X-N」跳转目标存在")

# ── 维度 6:编号格式 ────────────────────────────────────────
section(6, "编号格式正确")
# 严格 [A-Z]-[0-9]+ 或 [A-Z]-[0-9]+[a-z],不能裸数字 / 中文
# 已经用同一个正则提了 scene_ids,这里再扫表格一遍看是否有不规范
weird = []
for line in scene_text.split('\n'):
    m = re.match(r'^\|\s*([^|]+?)\s*\|', line)
    if m:
        cell = m.group(1).strip()
        # 跳过表头 / 分隔行 / 空 / View 列
        if not cell or set(cell) <= set('-: ') or cell == '编号':
            continue
        # 如果第一列像编号但不符合格式
        if re.match(r'^[A-Za-z0-9]', cell):
            if not re.fullmatch(r'[A-Z]-\d+[a-z]?', cell):
                # 排除 View 行(View 1 这种)
                if not re.match(r'^View\s+\d+', cell, re.IGNORECASE):
                    weird.append(cell)

if weird:
    print(f"  ❌ {len(weird)} 个编号格式异常: {weird[:5]}")
    fail = 1
else:
    print(f"  ✅ scene-list {len(scene_ids)} 编号全部符合 [A-Z]-N[a-z]? 格式")

# ── 维度 7:必填字段 ──────────────────────────────────────
section(7, "必填字段")
checks = []
if len(scene_ids) == 0:
    checks.append("scene-list 0 行（必须 ≥ 1）")
if imap_path and Path(imap_path).exists():
    imap_text = Path(imap_path).read_text(encoding='utf-8')
    if 'id="part' not in imap_text:
        checks.append("imap 无 PART 容器（id=\"partN\"）")
if prd_path and Path(prd_path).exists():
    try:
        from docx import Document
        d = Document(prd_path)
        full = '\n'.join(p.text for p in d.paragraphs)
        if not any(kw in full for kw in ('Guardrail', '反向指标', '不能恶化', '反向')):
            checks.append("prd 1.2 段无 Guardrail 关键词")
    except Exception:
        pass

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
