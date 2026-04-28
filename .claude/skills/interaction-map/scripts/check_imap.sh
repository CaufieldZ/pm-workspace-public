#!/usr/bin/env bash
# IMAP 文案讲人话自检（pm-workflow.md「人读产物讲人话」强制）
# 用法: bash check_imap.sh <imap.html>
#
# 检查规则:
#   1. .flow-note / .ann-text / .card-title / .gd-desc / .part-story / .aw .tx
#      正文里禁止裸 PM 内部代号: A-N / B-N / M-N / 决策 N / context 第 N 章
#   2. 编号锚点合法位置（.st h2 / .phone-label）不扫,允许 "B-1 · 业务白话" 格式
#
# 退出码: 0=pass, 1=fail

set -e

if [ -z "$1" ]; then
  echo "用法: bash $0 <imap.html>" >&2
  exit 2
fi

HTML="$1"
if [ ! -f "$HTML" ]; then
  echo "❌ 文件不存在: $HTML" >&2
  exit 2
fi

python3 - "$HTML" <<'PY'
import sys, re
from bs4 import BeautifulSoup

html_path = sys.argv[1]
with open(html_path, encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# 编号锚点合法容器(class 命中即跳过):允许 "B-1 · xxx" 这种 anchor 格式
ANCHOR_CLASSES = {'phone-label', 'gd-num', 'gd-num-cd'}
ANCHOR_PARENT_TAGS_WITH_CLASS = [('h2', 'st-h2-skip')]  # 不实际跳过 h2 全部，st 内部 h2 单独处理

# 正文目标 class(必扫):
BODY_CLASSES = ['flow-note', 'ann-text', 'card-title', 'gd-desc', 'part-story', 'tx']

# 内部代号正则
SCENE_RE = re.compile(r'(?<![A-Za-z0-9])[A-Z]-\d+(?![一-鿿·\-\d])')  # 裸 A-1 / B-2(后面不能紧跟中文/·避免 anchor 误伤)
DECISION_RE = re.compile(r'决策\s*\d+')
CONTEXT_RE = re.compile(r'context\s*第\s*\d+\s*章', re.I)

violations = []

def scan_text(text, location):
    bad = []
    for m in DECISION_RE.finditer(text):
        bad.append(('决策编号', m.group()))
    for m in CONTEXT_RE.finditer(text):
        bad.append(('context 引用', m.group()))
    # 裸场景编号(允许"B-1 · xxx"格式,即编号后紧跟「 · 」)
    for m in re.finditer(r'(?<![A-Za-z0-9\-])([A-Z]-\d+)', text):
        end = m.end()
        # anchor 格式: B-1 · xxx 或 B-1·xxx,紧跟 · 视为合法 anchor
        rest = text[end:end+3]
        if rest.lstrip().startswith('·'):
            continue
        bad.append(('场景编号', m.group()))
    if bad:
        violations.append((location, text.strip()[:80], bad))

def is_in_anchor(node):
    """节点是否在 anchor 容器内(.phone-label / .gd-num / 或 .st > h2)"""
    cur = node
    while cur is not None and cur.name is not None:
        cls = cur.get('class') or []
        if any(c in ANCHOR_CLASSES for c in cls):
            return True
        # .st > h2 是 Scene 标题 anchor
        if cur.name == 'h2' and cur.parent is not None:
            parent_cls = cur.parent.get('class') or []
            if 'st' in parent_cls:
                return True
        cur = cur.parent
    return False

# 扫所有 BODY_CLASSES 元素的纯文本
for cls in BODY_CLASSES:
    for el in soup.find_all(class_=cls):
        # 跳过被 anchor 容器包裹的(理论上 BODY_CLASSES 不应该在 anchor 里,但保险)
        if is_in_anchor(el):
            continue
        text = el.get_text(' ', strip=True)
        if text:
            scan_text(text, f'.{cls}')

if violations:
    print(f'❌ IMAP 文案讲人话自检失败 ({len(violations)} 处): {html_path}')
    print('   规则源: pm-workflow.md「人读产物讲人话」')
    print('   编号锚点(.phone-label / .st h2)允许 "B-1 · 业务白话",正文位置禁裸代号')
    print()
    for loc, snippet, bads in violations[:20]:
        bad_str = ', '.join(f'{t}={v}' for t, v in bads)
        print(f'   [{loc}] {snippet!r}')
        print(f'      → 命中: {bad_str}')
    if len(violations) > 20:
        print(f'   ... 还有 {len(violations) - 20} 处')
    sys.exit(1)
else:
    print(f'✅ IMAP 文案讲人话自检通过: {html_path}')
    sys.exit(0)
PY
