#!/bin/bash
# 回归测试：post-script-syntax-check.sh + pre-skill-load-gate.sh
#
# 用法：bash .claude/hooks/test/test-hooks.sh
# 退出：0 全过 / 1 任一失败
#
# 加 case：往对应小节追加 assert_*；新增 hook 时整段抄一个小节
# 局限：pipe smoke-test，不验证真实 Edit/Write 流；未覆盖 race / encoding / huge transcript

set +e
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT" || exit 1

# 回归跑触发的是真 hook，log_event 会写进真 usage.jsonl 污染 dashboard 健康统计
# （fixtures bad.py / prd-foo / prd-ll-baseline 被当真实流量）→ 子进程继承此标志后短路埋点
export CLAUDE_HOOK_TEST=1

PASS=0; FAIL=0
D=$(mktemp -d)
SANDBOX=$(mktemp -d)
trap "rm -rf $D ${SANDBOX:-}" EXIT

assert_exit() {
  local label="$1" expected="$2" actual="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  [OK]   $label"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] $label → exit=$actual (expected $expected)"
    FAIL=$((FAIL + 1))
  fi
}

run_post_syntax() {
  echo "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$1\"}}" \
    | bash .claude/hooks/post-writeedit-dispatch.sh 2>/dev/null
}

run_pre_gate() {
  echo "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$1\"},\"transcript_path\":\"$2\"}" \
    | bash .claude/hooks/pre-writeedit-guard.sh 2>/dev/null
}

# ═══════════════════════════════════════════════════════════════
echo "═══ 环境健康检查（hook 运行依赖 · M11：jq 缺失致 dashboard 静默空）═══"
assert_cmd_exists() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  [OK]   $cmd 可用"; PASS=$((PASS + 1))
  else
    echo "  [FAIL] $cmd 缺失 → dashboard 埋点 / checker 静默失效"; FAIL=$((FAIL + 1))
  fi
}
assert_cmd_exists jq
assert_cmd_exists python3

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ post-script-syntax-check.sh ═══"

# fixtures
printf 'def f(\n  pass\n'                 > "$D/bad.py"
printf 'x = 1\nprint(x)\n'                 > "$D/ok.py"
printf 'if true; then\n  echo hi\n'        > "$D/bad.sh"
printf '#!/bin/bash\necho hi\n'             > "$D/ok.sh"
printf 'const x = ;\n'                      > "$D/bad.js"
printf 'const x = 1;\nconsole.log(x);\n'    > "$D/ok.js"
printf '{"a":1,"b":,}\n'                    > "$D/bad.json"
printf '{"a":1,"b":2}\n'                    > "$D/ok.json"
printf 'foo: [1, 2, 3\nbar: {a: 1\n'        > "$D/bad.yaml"
printf 'foo:\n  bar: baz\n'                 > "$D/ok.yaml"
echo hi                                    > "$D/ignore.md"

for ext in py sh js json yaml; do
  run_post_syntax "$D/bad.$ext" >/dev/null; assert_exit "bad.$ext  → block" 2 $?
  run_post_syntax "$D/ok.$ext"  >/dev/null; assert_exit "ok.$ext   → pass"  0 $?
done
run_post_syntax "$D/ignore.md" >/dev/null
assert_exit "ignore.md  → skip"  0 $?
SKIP_SCRIPT_SYNTAX_GATE=1 bash -c "echo '{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$D/bad.py\"}}' | bash .claude/hooks/post-writeedit-dispatch.sh" >/dev/null 2>&1
assert_exit "SKIP_SCRIPT_SYNTAX_GATE bypass" 0 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ pre-skill-load-gate.sh ═══"

# transcript fixtures (synthesized JSONL with Read event(s); 多参数 = 多行 Read)
make_hit() { local out="$1"; shift; : > "$out"; for p in "$@"; do echo "{\"tool_input\":{\"file_path\":\"$p\"}}" >> "$out"; done; }
T_HIT_PRD="$D/t_prd.jsonl"
T_HIT_SL="$D/t_sl.jsonl"
T_HIT_HOOK="$D/t_hook.jsonl"
T_MISS="$D/t_miss.jsonl"
# prd / scene-list 产出物需读 SKILL.md + info-ownership.md（GUIDE2）；prd 另需章节规则速查（GUIDE3）+ 场景模板速查（GUIDE4）
make_hit "$T_HIT_PRD" "/p/.claude/skills/prd/SKILL.md" "/p/.claude/runbooks/info-ownership.md" "/p/.claude/skills/prd/references/prd-chapter-rules-quickref.md" "/p/.claude/skills/prd/references/prd-scene-template-quickref.md"
make_hit "$T_HIT_SL"  "/p/.claude/skills/scene-list/SKILL.md" "/p/.claude/runbooks/info-ownership.md"
make_hit "$T_HIT_HOOK" "/p/.claude/hooks/HOOK_WRITING-quickref.md"
echo '{}' > "$T_MISS"

# 旧 skill-load-gate 规则
run_pre_gate "/p/projects/x/deliverables/prd-foo.md" "$T_HIT_PRD" >/dev/null
assert_exit "old · prd-*.md          HIT " 0 $?
run_pre_gate "/p/projects/x/deliverables/prd-foo.md" "$T_MISS"    >/dev/null
assert_exit "old · prd-*.md          MISS" 2 $?
run_pre_gate "/p/projects/x/scene-list.md"           "$T_HIT_SL"  >/dev/null
assert_exit "old · scene-list.md     HIT " 0 $?
run_pre_gate "/p/projects/x/scene-list.md"           "$T_MISS"    >/dev/null
assert_exit "old · scene-list.md     MISS" 2 $?
run_pre_gate "/p/projects/x/deliverables/prd-foo-scenes/back-G-1-x.md" "$T_HIT_PRD" >/dev/null
assert_exit "old · prd-*-scenes/.md  HIT " 0 $?

# 新 required-read-gate 规则
run_pre_gate "/p/.claude/skills/prd/scripts/foo.py" "$T_HIT_PRD" >/dev/null
assert_exit "new · skill scripts .py HIT " 0 $?
run_pre_gate "/p/.claude/skills/prd/scripts/foo.py" "$T_MISS"    >/dev/null
assert_exit "new · skill scripts .py MISS" 2 $?
run_pre_gate "/p/.claude/hooks/some-new.sh"         "$T_HIT_HOOK" >/dev/null
assert_exit "new · hooks/*.sh        HIT " 0 $?
run_pre_gate "/p/.claude/hooks/some-new.sh"         "$T_MISS"    >/dev/null
assert_exit "new · hooks/*.sh        MISS" 2 $?

# required-read-gate · scripts（仅工区根 scripts/*.py / lib/*.py 前必读 SCRIPTS_WRITING.md）
T_HIT_SCRIPTS="$D/t_scripts.jsonl"
make_hit "$T_HIT_SCRIPTS" "$ROOT/scripts/SCRIPTS_WRITING.md"
run_pre_gate "$ROOT/scripts/check_new.py" "$T_HIT_SCRIPTS" >/dev/null
assert_exit "req-read · root scripts/*.py     HIT " 0 $?
run_pre_gate "$ROOT/scripts/check_new.py" "$T_MISS"    >/dev/null
assert_exit "req-read · root scripts/*.py     MISS" 2 $?
run_pre_gate "$ROOT/scripts/lib/new_mod.py" "$T_HIT_SCRIPTS" >/dev/null
assert_exit "req-read · root scripts/lib/*.py HIT " 0 $?
run_pre_gate "$ROOT/scripts/lib/new_mod.py" "$T_MISS"    >/dev/null
assert_exit "req-read · root scripts/lib/*.py MISS" 2 $?
# projects/*/scripts/*.py 是产物生成器，不走 SCRIPTS_WRITING.md gate → 无须读任何 guide 也放行
run_pre_gate "$ROOT/projects/livestream/scripts/build_proto_v212.py" "$T_MISS" >/dev/null
assert_exit "exempt · projects/*/scripts/*.py     → skip" 0 $?
run_pre_gate "$ROOT/projects/livestream/scripts/src/crud.py" "$T_MISS" >/dev/null
assert_exit "exempt · projects/*/scripts/src/*.py → skip" 0 $?

# required-read-gate · hub 工具/agent（L1 入口 + L3 过审 + L2 对应公司规范，全部要读）
_MCP="$ROOT/hub/AI中台-规范及帮助文档/AI中台-MCP编写规范.md"
_AGENT="$ROOT/hub/AI中台-规范及帮助文档/AI 中台-Agent 创建规范.md"
_PROMPT="$ROOT/hub/AI中台-规范及帮助文档/AI中台-Prompt编写规范.md"
T_HIT_DIST="$D/t_dist.jsonl"
make_hit "$T_HIT_DIST" "$ROOT/.claude/runbooks/ai-platform-specs.md" "$ROOT/hub/AUTHORING-RULES.md" "$_MCP"
run_pre_gate "$ROOT/hub/confluence-cli/aihub_tool.py" "$T_HIT_DIST" >/dev/null
assert_exit "req-read · aihub_tool 全读   HIT " 0 $?
run_pre_gate "$ROOT/hub/confluence-cli/aihub_tool.py" "$T_MISS"    >/dev/null
assert_exit "req-read · aihub_tool 没读   MISS" 2 $?
# 只读入口+过审没读 L2 MCP 规范 → 仍 MISS（L2 机械强制）
T_NO_L2="$D/t_no_l2.jsonl"
make_hit "$T_NO_L2" "$ROOT/.claude/runbooks/ai-platform-specs.md" "$ROOT/hub/AUTHORING-RULES.md"
run_pre_gate "$ROOT/hub/confluence-cli/aihub_tool.py" "$T_NO_L2" >/dev/null
assert_exit "req-read · 没读 L2 MCP 规范 MISS" 2 $?
# system-prompt.md → L1+L3+Agent+Prompt（4 份）
T_HIT_AGENT="$D/t_agent.jsonl"
make_hit "$T_HIT_AGENT" "$ROOT/.claude/runbooks/ai-platform-specs.md" "$ROOT/hub/AUTHORING-RULES.md" "$_AGENT" "$_PROMPT"
run_pre_gate "$ROOT/hub/promo-agent/system-prompt.md" "$T_HIT_AGENT" >/dev/null
assert_exit "req-read · system-prompt 全读 HIT " 0 $?

# 不命中任何规则
run_pre_gate "/p/projects/x/random.md" "$T_MISS" >/dev/null
assert_exit "unrelated .md            → skip" 0 $?

# SKIP env（两个变量任一都解锁）
SKIP_SKILL_LOAD_GATE=1 bash -c "echo '{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"/p/projects/x/deliverables/prd-foo.md\"},\"transcript_path\":\"$T_MISS\"}' | bash .claude/hooks/pre-writeedit-guard.sh" >/dev/null 2>&1
assert_exit "SKIP_SKILL_LOAD_GATE bypass" 0 $?
SKIP_REQUIRED_READ_GATE=1 bash -c "echo '{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"/p/projects/x/deliverables/prd-foo.md\"},\"transcript_path\":\"$T_MISS\"}' | bash .claude/hooks/pre-writeedit-guard.sh" >/dev/null 2>&1
assert_exit "SKIP_REQUIRED_READ_GATE bypass" 0 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ deliverable-source-gate（TYPE 抽取含数字 · 防 fail-open）═══"
# 数字紧贴 type（build_imap2_）：修前 ([a-zA-Z]+) 抽空 → 静默放行；修后 ([a-zA-Z0-9]+) → imap2 拦截
DS="$D/dsgate"
mkdir -p "$DS/projects/p3/scripts" "$DS/projects/p3/deliverables"
printf 'x=1\n' > "$DS/projects/p3/scripts/build_imap2_skeleton.py"
printf 'x=1\n' > "$DS/projects/p3/scripts/build_imap_skeleton.py"
test_ds() {  # $1=产物文件名 → 返回 pg_deliverable_source 退出码
  ( source .claude/hooks/lib/log.sh
    source .claude/hooks/lib/input.sh
    source .claude/hooks/lib/guards.sh
    source .claude/hooks/lib/pre-writeedit-guards.sh
    PROJECT_DIR="$DS"; HOOK_FILE_PATH="$DS/projects/p3/deliverables/$1"
    pg_deliverable_source )
}
test_ds "imap2-foo.html" >/dev/null 2>&1; assert_exit "ds · 数字 type build_imap2_ → imap2-foo.html → block" 2 $?
test_ds "imap-bar.html"  >/dev/null 2>&1; assert_exit "ds · 纯字母 type build_imap_ → imap-bar.html  → block" 2 $?
test_ds "report-x.html"  >/dev/null 2>&1; assert_exit "ds · 无匹配脚本 report-x.html → pass" 0 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ check_scene_list.py（pipeline 源头护栏 · 重复编号）═══"
SL_CHK=".claude/skills/scene-list/scripts/check_scene_list.py"
SLD="$D/sl"; mkdir -p "$SLD"
printf '| 编号 | 场景 | P |\n|--|--|--|\n| A | x | P0 |\n| A | y | P0 |\n' > "$SLD/scene-list.md"
python3 "$SL_CHK" "$SLD/scene-list.md" --strict >/dev/null 2>&1
assert_exit "scene-list · 重复编号 --strict → block" 2 $?
printf '| 编号 | 场景 | P |\n|--|--|--|\n| A | x | P0 |\n| B | y | P1 |\n' > "$SLD/scene-list.md"
python3 "$SL_CHK" "$SLD/scene-list.md" --strict >/dev/null 2>&1
assert_exit "scene-list · 唯一编号 --strict → pass" 0 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ check_proto_split.py（src/scenes 分场景拆分门）═══"

SPLIT_CHK=".claude/skills/prototype/scripts/check_proto_split.py"
# 已拆分：项目根 scripts/src/scenes/*.py 存在
mkdir -p "$D/proj/scripts/src/scenes" "$D/proj/deliverables"
printf 'x=1\n' > "$D/proj/scripts/src/scenes/user_view_main.py"
printf '<html></html>\n' > "$D/proj/deliverables/proto-x-v1.html"
python3 "$SPLIT_CHK" "$D/proj/deliverables/proto-x-v1.html" --strict >/dev/null 2>&1
assert_exit "split · 有 src/scenes   → pass" 0 $?
# 未拆分：内联，无 src/scenes
mkdir -p "$D/proj2/scripts" "$D/proj2/deliverables"
printf 'inline\n' > "$D/proj2/scripts/build_proto_v1.py"
printf '<html></html>\n' > "$D/proj2/deliverables/proto-y-v1.html"
python3 "$SPLIT_CHK" "$D/proj2/deliverables/proto-y-v1.html" --strict >/dev/null 2>&1
assert_exit "split · 内联无拆分      → block" 2 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ check_imap_split.py（IMAP src/scenes 分场景拆分门）═══"

IMAP_SPLIT_CHK=".claude/skills/interaction-map/scripts/check_imap_split.py"
# 已拆分：项目根 scripts/src/scenes/*.py 存在
mkdir -p "$D/iproj/scripts/src/scenes" "$D/iproj/deliverables"
printf 'def scene_a(): return ""\n' > "$D/iproj/scripts/src/scenes/a.py"
printf '<html></html>\n' > "$D/iproj/deliverables/imap-x-v1.html"
python3 "$IMAP_SPLIT_CHK" "$D/iproj/deliverables/imap-x-v1.html" --strict >/dev/null 2>&1
assert_exit "imap-split · 有 src/scenes → pass" 0 $?
# 未拆分：内联，无 src/scenes
mkdir -p "$D/iproj2/scripts" "$D/iproj2/deliverables"
printf 'inline\n' > "$D/iproj2/scripts/build_imap_v1.py"
printf '<html></html>\n' > "$D/iproj2/deliverables/imap-y-v1.html"
python3 "$IMAP_SPLIT_CHK" "$D/iproj2/deliverables/imap-y-v1.html" --strict >/dev/null 2>&1
assert_exit "imap-split · 内联无拆分   → block" 2 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ check_ui_annotation.py（渲染 UI 屏内禁开发注解）═══"

UIA_CHK="scripts/check_ui_annotation.py"
mkdir -p "$D/uia/deliverables"
# proto · 渲染壳内含注解 → block
printf '<html><body><div class="app-mock"><div class="card">广告位（灰条占位）</div></div></body></html>\n' \
  > "$D/uia/deliverables/proto-dirty-v1.html"
python3 "$UIA_CHK" "$D/uia/deliverables/proto-dirty-v1.html" --strict >/dev/null 2>&1
assert_exit "uia · proto 壳内注解      → block" 2 $?
# proto · 纯真实文案 → pass
printf '<html><body><div class="app-mock"><div class="card">累计收益（含手续费）</div></div></body></html>\n' \
  > "$D/uia/deliverables/proto-clean-v1.html"
python3 "$UIA_CHK" "$D/uia/deliverables/proto-clean-v1.html" --strict >/dev/null 2>&1
assert_exit "uia · proto 纯真实文案    → pass" 0 $?
# imap · .phone 屏内含注解 → block
printf '<html><body><div class="phone"><div class="card">昵称（动态加载）</div></div></body></html>\n' \
  > "$D/uia/deliverables/imap-dirty-v1.html"
python3 "$UIA_CHK" "$D/uia/deliverables/imap-dirty-v1.html" --strict >/dev/null 2>&1
assert_exit "uia · imap 屏内注解       → block" 2 $?
# imap · 同样注解放 mockup 外的 ann-card → pass（验作用域）
printf '<html><body><div class="phone"><div class="card">张三</div></div><div class="ann-card">昵称（动态加载）</div></body></html>\n' \
  > "$D/uia/deliverables/imap-anncard-v1.html"
python3 "$UIA_CHK" "$D/uia/deliverables/imap-anncard-v1.html" --strict >/dev/null 2>&1
assert_exit "uia · imap 注解在 ann-card → pass" 0 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ check_static_chapter.py（真相源静态章四不 + baseline 豁免）═══"

assert_grep() {
  local label="$1" needle="$2" haystack="$3"
  if echo "$haystack" | grep -q "$needle"; then
    echo "  [OK]   $label"; PASS=$((PASS + 1))
  else
    echo "  [FAIL] $label → 未命中 '$needle'"; FAIL=$((FAIL + 1))
  fi
}
assert_no_grep() {
  local label="$1" needle="$2" haystack="$3"
  if echo "$haystack" | grep -q "$needle"; then
    echo "  [FAIL] $label → 误命中 '$needle'"; FAIL=$((FAIL + 1))
  else
    echo "  [OK]   $label"; PASS=$((PASS + 1))
  fi
}

# 真泄漏：技术实现（infra 通用词 binlog）/ UI hex / 流水标注 应命中
printf '# t\n\n## 1. 现状\n下单触发 binlog 同步。\n按钮 #FF6A00。\n（v5.1 新增）反转决策 #3。\n' > "$D/leak.md"
LEAK_OUT=$(python3 scripts/check_static_chapter.py "$D/leak.md" 2>&1)
assert_grep "leak · 技术实现命中"  "技术实现"  "$LEAK_OUT"
assert_grep "leak · UI 视觉命中"    "UI 视觉"   "$LEAK_OUT"
assert_grep "leak · 流水标注命中"   "流水标注"  "$LEAK_OUT"

# baseline 承重 / 业务常识豁免：本轮 delta 交叉引用 / CDN·SDK / Toast 反馈 / > 导言 应放行
printf '# t\n\n## 1. 现状\n> 静态章。不写本轮变更。\n含卡帖本轮 delta 引入。\n降级 CDN，含 TRTC SDK。\n校验失败 → Toast「请先登录」。\n' > "$D/clean.md"
CLEAN_OUT=$(python3 scripts/check_static_chapter.py "$D/clean.md" 2>&1)
assert_no_grep "clean · 本轮 delta 放行"  "思考过程"  "$CLEAN_OUT"
assert_no_grep "clean · CDN/SDK 放行"      "技术实现"  "$CLEAN_OUT"
assert_no_grep "clean · Toast 反馈放行"    "UI 视觉"   "$CLEAN_OUT"

# dispatcher 路由：编辑 baseline 路径应触发 context-static-lint（gate 名契约保留）
mkdir -p "$D/projects/ll"
printf '# t\n\n## 1. 现状\n下单触发 binlog 同步。\n' > "$D/projects/ll/prd-ll-baseline.md"
ROUTE_OUT=$(CLAUDE_PROJECT_DIR="$ROOT" bash -c "echo '{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$D/projects/ll/prd-ll-baseline.md\"}}' | bash .claude/hooks/post-writeedit-dispatch.sh" 2>&1)
assert_grep "dispatch · baseline 触发 gate"  "context-static-lint"  "$ROUTE_OUT"

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ check_cjk_punct.py --stdin（CJK 标点 exit code 契约 · 防静默漏判）═══"

CJK_CHK="scripts/check_cjk_punct.py"
# 脏：中文旁半角逗号/句号 → --strict 必须阻断（防该报不报的静默漏判）
printf '这是测试,含半角逗号.\n' | python3 "$CJK_CHK" --stdin --strict >/dev/null 2>&1
assert_exit "cjk · 脏(半角标点) --strict → block" 2 $?
# 净：全角标点 → pass
printf '这是测试，含全角逗号。\n' | python3 "$CJK_CHK" --stdin --strict >/dev/null 2>&1
assert_exit "cjk · 净(全角标点) --strict → pass"  0 $?
# 不传 --strict：脏也只 warn（exit 0，非阻断）—— 契约：strict 才阻断
printf '这是测试,含半角逗号.\n' | python3 "$CJK_CHK" --stdin >/dev/null 2>&1
assert_exit "cjk · 脏 无 --strict → warn(0)" 0 $?
# HR：水平分割线 --- → --strict 阻断；setext 下划线（紧邻文本行）放行
printf '段落一\n\n---\n\n段落二\n' | python3 "$CJK_CHK" --stdin --strict >/dev/null 2>&1
assert_exit "cjk · 脏(水平分割线 ---) --strict → block" 2 $?
printf '标题文本\n---\n' | python3 "$CJK_CHK" --stdin --strict >/dev/null 2>&1
assert_exit "cjk · 净(setext 标题下划线) → pass" 0 $?

# ── --fix-spaces：自动补空格（幂等，只改空格不碰标点）───────────
printf '用GitHub世界\n' > "$D/sp.md"
python3 "$CJK_CHK" --fix-spaces "$D/sp.md" >/dev/null 2>&1
assert_exit "cjk · --fix-spaces exit 0" 0 $?
grep -q '用 GitHub 世界' "$D/sp.md"; assert_exit "cjk · --fix-spaces 补了空格" 0 $?
# 只改空格不碰标点：半角逗号保留（punct 关）
printf '用GitHub世界,结束\n' > "$D/sp2.md"
python3 "$CJK_CHK" --fix-spaces "$D/sp2.md" >/dev/null 2>&1
grep -q '用 GitHub 世界,结束' "$D/sp2.md"; assert_exit "cjk · --fix-spaces 不碰半角标点" 0 $?
# 单字母保护：D值 不动
printf 'D值分析\n' > "$D/sp3.md"
python3 "$CJK_CHK" --fix-spaces "$D/sp3.md" >/dev/null 2>&1
grep -qx 'D值分析' "$D/sp3.md"; assert_exit "cjk · --fix-spaces 单字母 D值 不动" 0 $?

# ── hook 侧 SKIP_CJK_SPACE_FIX=1 旁路：写脏空格文件跑 hook 内容不变 ──
mkdir -p "$D/projects/ll/deliverables"
DELIV="$D/projects/ll/deliverables/report-ll.md"
printf '# 标题\n\n用GitHub世界做方案\n' > "$DELIV"
SKIP_OUT=$(CLAUDE_PROJECT_DIR="$ROOT" SKIP_CJK_SPACE_FIX=1 bash -c \
  "echo '{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$DELIV\"}}' | bash .claude/hooks/post-writeedit-dispatch.sh" 2>&1)
grep -q '用GitHub世界' "$DELIV"; assert_exit "cjk · SKIP_CJK_SPACE_FIX=1 旁路不补空格" 0 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ check_plain_language.py --stdin（讲人话 exit code 契约 · 防静默漏判）═══"

PLAIN_CHK="scripts/check_plain_language.py"
# 脏：AI slop 收尾煽动词（重塑 / 真相）→ --strict 阻断
printf '我们要重塑行业真相。\n' | python3 "$PLAIN_CHK" --stdin --strict >/dev/null 2>&1
assert_exit "plain · 脏(重塑/真相) --strict → block" 2 $?
# 净：正常业务表达 → pass
printf '用户完成签到后获得奖励。\n' | python3 "$PLAIN_CHK" --stdin --strict >/dev/null 2>&1
assert_exit "plain · 净(正常表达) --strict → pass"  0 $?
# 不传 --strict：脏 exit 1（warn 级，非阻断）—— 契约与 cjk 不同（plain 脏即 1）
printf '我们要重塑行业真相。\n' | python3 "$PLAIN_CHK" --stdin >/dev/null 2>&1
assert_exit "plain · 脏 无 --strict → warn(1)" 1 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ pre-bash-guard.sh（Bash 前置守卫 · 误拦白名单 + 违规拦截）═══"

run_bash_guard() {
  echo "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"$1\"}}" \
    | bash .claude/hooks/pre-bash-guard.sh 2>/dev/null
}

# 误拦白名单（proxy-check 不误报 · commit 1be8b44 曾干掉 ~1300 次假阳性 warn）
run_bash_guard 'ALL_PROXY=http://x pip install requests' >/dev/null; assert_exit "bash · ALL_PROXY 前缀  → 放行" 0 $?
run_bash_guard 'curl --proxy http://x https://github.com/u/r' >/dev/null; assert_exit "bash · curl --proxy    → 放行" 0 $?
run_bash_guard 'curl -x https://p https://github.com/u/r' >/dev/null; assert_exit "bash · curl -x         → 放行" 0 $?
run_bash_guard 'pip install x -i https://pypi.tuna.tsinghua.edu.cn/simple' >/dev/null; assert_exit "bash · 国内镜像      → 放行" 0 $?
run_bash_guard 'curl https://example.com/f' >/dev/null; assert_exit "bash · 非境外 URL     → 放行" 0 $?
run_bash_guard 'grep -rn foo projects/' >/dev/null; assert_exit "bash · 无关命令        → 放行" 0 $?

# 违规拦截（git-safety / git-https-gate）
run_bash_guard 'git push --force origin main' >/dev/null; assert_exit "bash · force push main → block" 2 $?
run_bash_guard 'git commit --amend' >/dev/null; assert_exit "bash · commit --amend   → block" 2 $?
run_bash_guard 'git reset --hard HEAD~1' >/dev/null; assert_exit "bash · reset --hard     → block" 2 $?
run_bash_guard 'git push https://github.com/x/y.git main' >/dev/null; assert_exit "bash · push https       → block" 2 $?

# +refspec 隐式强推到 main/master（无 --force 也覆盖历史 · 曾 fail-open）
run_bash_guard 'git push origin +main' >/dev/null; assert_exit "bash · +main 强推      → block" 2 $?
run_bash_guard 'git push origin +HEAD:master' >/dev/null; assert_exit "bash · +HEAD:master    → block" 2 $?

# 逐段判：复合命令不跨命令拼凑假阳（曾误拦）
run_bash_guard 'git push --force origin dev && git checkout main' >/dev/null; assert_exit "bash · force dev&&co main → 放行" 0 $?
run_bash_guard 'git push origin dev && curl https://github.com/a/b' >/dev/null; assert_exit "bash · push dev&&curl gh  → 放行" 0 $?
run_bash_guard 'git push --force-with-lease origin main' >/dev/null; assert_exit "bash · force-with-lease   → 放行" 0 $?

# bypass（SKIP env · 显式跳过链路放行）
run_bash_guard 'SKIP_GIT_SAFETY_GATE=1 git push --force origin main' >/dev/null; assert_exit "bash · SKIP_GIT_SAFETY → bypass" 0 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ pre-read-bigfile.sh（> 500 行禁全量 Read · 补 huge 盲区）═══"

run_read_guard() {
  # $1=file_path  $2=额外 tool_input 字段（如 ,"offset":100）
  echo "{\"tool_name\":\"Read\",\"tool_input\":{\"file_path\":\"$1\"$2}}" \
    | bash .claude/hooks/pre-read-bigfile.sh 2>/dev/null
}
seq 1 600 > "$D/big.txt"          # 600 行 > 阈值 500
echo hi    > "$D/small.txt"
cp "$D/big.txt" "$D/big.png"      # 图片后缀走 Read 自身机制（不看内容）

# 大文件无分页 → block（防 token 爆 / compact 丢状态）
run_read_guard "$D/big.txt" "" >/dev/null; assert_exit "read · 大文件无分页   → block" 2 $?
# 大文件带 offset → 放行（模型已知分页）
run_read_guard "$D/big.txt" ',"offset":100' >/dev/null; assert_exit "read · 大文件带 offset → 放行" 0 $?
# 大文件带 limit → 放行
run_read_guard "$D/big.txt" ',"limit":50' >/dev/null; assert_exit "read · 大文件带 limit  → 放行" 0 $?
# 小文件 → 放行
run_read_guard "$D/small.txt" "" >/dev/null; assert_exit "read · 小文件          → 放行" 0 $?
# 图片 / PDF 走 Read 自身机制 → 放行（即便行数多）
run_read_guard "$D/big.png" "" >/dev/null; assert_exit "read · .png 走自身机制 → 放行" 0 $?
# SKIP env（Read 不经 Bash 管道，只 env 生效）
SKIP_READ_BIGFILE_GATE=1 bash -c "echo '{\"tool_name\":\"Read\",\"tool_input\":{\"file_path\":\"$D/big.txt\"}}' | bash .claude/hooks/pre-read-bigfile.sh" >/dev/null 2>&1
assert_exit "read · SKIP_READ_BIGFILE → bypass" 0 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ pre-read-image-check.sh（Bedrock 网关特征下图片 Read 限制预检）═══"

run_read_img_guard() {
  # $1=file_path  $2=ANTHROPIC_BASE_URL（假域名：含 aihub 特征但非真实内部域名，测试文件同步 public 也安全）
  echo "{\"tool_name\":\"Read\",\"tool_input\":{\"file_path\":\"$1\"}}" \
    | ANTHROPIC_BASE_URL="$2" CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/pre-read-image-check.sh 2>/dev/null
}
python3 -c "
from PIL import Image
Image.new('RGB', (3000, 2000), color=(100,150,200)).save('$D/over.png')   # 超维度
Image.new('RGB', (1800, 900), color=(100,150,200)).save('$D/ok.png')      # 满足
" 2>/dev/null
printf 'hi' > "$D/note.md"

# Bedrock 网关（aihub 特征）+ 超维度 → block
run_read_img_guard "$D/over.png" "https://aihub.fakegw.com/api/cc" >/dev/null; assert_exit "img · 网关特征+超维度 → block" 2 $?
# Bedrock 网关 + 满足 → 放行
run_read_img_guard "$D/ok.png" "https://aihub.fakegw.com/api/cc" >/dev/null; assert_exit "img · 网关特征+满足   → 放行" 0 $?
# 非 Bedrock 网关（中转站支持大图）→ 放行
run_read_img_guard "$D/over.png" "https://api.othergw.com" >/dev/null; assert_exit "img · 非网关特征+超维度 → 放行" 0 $?
# 网关特征 + 非图片文件 → 放行
run_read_img_guard "$D/note.md" "https://aihub.fakegw.com/api/cc" >/dev/null; assert_exit "img · 网关特征+非图片 → 放行" 0 $?
# SKIP env → 放行
SKIP_READ_IMAGE_CHECK_GATE=1 bash -c "echo '{\"tool_name\":\"Read\",\"tool_input\":{\"file_path\":\"$D/over.png\"}}' | ANTHROPIC_BASE_URL='https://aihub.fakegw.com/api/cc' CLAUDE_PROJECT_DIR='$ROOT' bash .claude/hooks/pre-read-image-check.sh" >/dev/null 2>&1
assert_exit "img · SKIP_READ_IMAGE_CHECK → bypass" 0 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ pc_pm_visual（PRD 视觉越界 · 覆盖 S1 argv 改造 + L14 clean 路径）═══"

mkdir -p "$D/pvproj/deliverables"
# 视觉越界：颜色 + UI 元素（红色描边）→ pm-visual-gate block
printf '# t\n\n按钮用红色描边。\n' > "$D/pvproj/deliverables/prd-pvtest.md"
PV_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/pvproj/deliverables/prd-pvtest.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_grep "pm-visual · 颜色+UI 越界 → block" "pm-visual-gate" "$PV_OUT"
# clean：无视觉越界 → 不触发 pm-visual-gate
printf '# t\n\n用户完成签到后获得奖励。\n' > "$D/pvproj/deliverables/prd-pvclean.md"
PVC_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/pvproj/deliverables/prd-pvclean.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_no_grep "pm-visual · clean 不误报" "pm-visual-gate" "$PVC_OUT"

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ S2.6 · bullet-density-gate（md 产物单行挤话 block）═══"

mkdir -p "$D/projects/bdproj/deliverables" "$D/deliverables/reports/weekly-0624"
# 挤话：正文段落 4 句 → block（projects 内 PRD 路径）
printf '# t\n\n补丁包。表单缺校验。推流加白锁死。假重开。两处 bug。\n' > "$D/projects/bdproj/deliverables/prd-bdtest.md"
BD_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/bdproj/deliverables/prd-bdtest.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_grep "bullet-density · 段落 4 句 → block" "bullet-density-gate" "$BD_OUT"
# 决策章无豁免：3 句焊一行照样 block（决策流水也配写好看，拆标签 bullet 更清晰）
printf '# t\n\n# 6. 决策记录（WHY）\n取舍：选 A。因为 X。所以 Y。\n' > "$D/projects/bdproj/deliverables/prd-bddec.md"
BDD_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/bdproj/deliverables/prd-bddec.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_grep "bullet-density · 决策章 3 句照样 block（无章节豁免）" "bullet-density-gate" "$BDD_OUT"
# 决策章 2 句（论点。论据。）不到阈值 → 干净：证明拦的是句数不是章
printf '# t\n\n# 6. 决策记录（WHY）\n取舍：选 A。因为成本更低。\n' > "$D/projects/bdproj/deliverables/prd-bdclean.md"
BDC_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/bdproj/deliverables/prd-bdclean.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_no_grep "bullet-density · 决策章 2 句不误报（≤2 句号天然过）" "bullet-density-gate" "$BDC_OUT"
# datareport 根 deliverables/reports/ 路径也覆盖 → block
printf '# 周报\n\n归因落环境。共现率假象。真实转化低。\n' > "$D/deliverables/reports/weekly-0624/report.md"
BDR_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/deliverables/reports/weekly-0624/report.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_grep "bullet-density · 根 deliverables/reports/ datareport → block" "bullet-density-gate" "$BDR_OUT"
# 根 deliverables/audit-*.md 内部审计 → trigger 不覆盖，不触发
printf '# t\n\n审计 A。审计 B。审计 C。\n' > "$D/deliverables/audit-fake.md"
BDA_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/deliverables/audit-fake.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_no_grep "bullet-density · 根 deliverables/audit 内部文档不触发" "bullet-density-gate" "$BDA_OUT"
# 分号 ≥2 → block（分号串该拆嵌套 bullet；句号不足 3 也拦）
printf '# t\n\n- 显示逻辑：默认自动通过；运营可驳回；通过前校验冲突\n' > "$D/projects/bdproj/deliverables/prd-bdsemi.md"
BDS_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/bdproj/deliverables/prd-bdsemi.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_grep "bullet-density · 分号 ≥2 → block" "bullet-density-gate" "$BDS_OUT"
# 表格行内分号（md_to_confluence 切 bullet 约定分隔符）→ 豁免不触发
printf '# t\n\n| 规则 | A；B；C；D |\n' > "$D/projects/bdproj/deliverables/prd-bdtable.md"
BDT_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/bdproj/deliverables/prd-bdtable.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_no_grep "bullet-density · 表格行分号豁免" "bullet-density-gate" "$BDT_OUT"

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ S3 · check_cjk 多文件 first 解析（防指错文件循环）═══"

# 模拟 check_cjk_punct 多文件输出：recent 有 clean+dirty，checker 只输出 dirty 段
printf '/p/proj/deliverables/clean.md\n/p/proj/deliverables/dirty.md\n' > "$D/s3_recent.txt"
printf '\n/p/proj/deliverables/dirty.md — strict 1\n  L1 脏,的.\n' > "$D/s3_out.txt"
S3_FIRST=$(grep -m1 -E '^[^[:space:]]+ — ' "$D/s3_out.txt" 2>/dev/null | sed 's/ —.*//')
assert_grep "S3 · first 解析出违规文件 dirty" "dirty.md" "$S3_FIRST"
assert_no_grep "S3 · first 不误指 clean 文件" "clean.md" "$S3_FIRST"
# 无违规（checker 无输出）→ fallback recent head -1（不 worse 于原行为）
printf '' > "$D/s3_clean.txt"
S3_FB=$(grep -m1 -E '^[^[:space:]]+ — ' "$D/s3_clean.txt" 2>/dev/null | sed 's/ —.*//')
[ -z "$S3_FB" ] && S3_FB=$(head -1 "$D/s3_recent.txt")
assert_grep "S3 · 无违规 fallback head -1" "clean.md" "$S3_FB"

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ 热路径 fork 优化等价性（case 粗筛 / 短路不改变拦截行为）═══"

# strip_command_literals 短路：无引号原样返回，含引号仍剥
source .claude/hooks/lib/strip.sh
assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [ "$actual" = "$expected" ]; then echo "  [OK]   $label"; PASS=$((PASS + 1))
  else echo "  [FAIL] $label → '$actual' (expected '$expected')"; FAIL=$((FAIL + 1)); fi
}
assert_eq "strip · 无引号命令原样返回" "git status -s" "$(strip_command_literals 'git status -s')"
assert_eq "strip · 双引号串剥成空" 'echo ""' "$(strip_command_literals 'echo "secret"')"
assert_eq "strip · 单引号串剥成空" "echo ''" "$(strip_command_literals "echo 'secret'")"

# post-skill-load case 早退：非 SKILL.md 输入不再记录 skill triggered
PSL_SKILL=$(printf '{"tool_name":"Read","tool_input":{"file_path":"%s/.claude/skills/prd/SKILL.md"}}' "$ROOT" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-skill-load.sh 2>&1; echo "rc=$?")
assert_grep "post-skill-load · SKILL.md 不早退（exit 0 正常）" "rc=0" "$PSL_SKILL"
PSL_NORMAL=$(printf '{"tool_name":"Read","tool_input":{"file_path":"%s/scripts/README.md"}}' "$ROOT" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-skill-load.sh 2>&1; echo "rc=$?")
assert_grep "post-skill-load · 非 SKILL.md case 早退（exit 0）" "rc=0" "$PSL_NORMAL"

# proxy-check 粗筛：下载命令仍 warn，含 "go" 子串的非下载命令不误判
PROXY_PIP=$(printf '{"tool_name":"Bash","tool_input":{"command":"pip install requests"}}' | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/pre-bash-guard.sh 2>&1)
assert_grep "proxy-check · pip install 仍 warn（粗筛不漏）" "proxy-check" "$PROXY_PIP"
PROXY_GOGET=$(printf '{"tool_name":"Bash","tool_input":{"command":"go get github.com/x/y"}}' | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/pre-bash-guard.sh 2>&1)
assert_grep "proxy-check · go get 仍 warn（命令开头双词 glob）" "proxy-check" "$PROXY_GOGET"
PROXY_ECHO=$(printf '{"tool_name":"Bash","tool_input":{"command":"echo django logo"}}' | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/pre-bash-guard.sh 2>&1)
assert_no_grep "proxy-check · echo 含 go 子串不误 warn" "proxy-check" "$PROXY_ECHO"

# ═══ S2.7 · git-safety 绕过形态 + paradigm 命令位锚定（双探针）═══
# 安全门正则改动后必跑：绕过形态必 block、无害近似形态必放行（HOOK_WRITING §三 K）
# block 用例选 moderation：无 scene-anchors 范式 / 无 proto-*.html / session-state 无「范式」
run_pre_bash_rc() {
  printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$1" \
    | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" \
      bash .claude/hooks/pre-bash-guard.sh >/dev/null 2>&1
  echo $?
}
RC=$(run_pre_bash_rc 'git -C /tmp/xx push --force origin main')
assert_exit "git-safety · -C 全局选项前缀 force-push main → block" 2 "$RC"
RC=$(run_pre_bash_rc 'git push origin +refs/heads/main:refs/heads/main')
assert_exit "git-safety · 完整 refspec +refs/heads/main → block" 2 "$RC"
RC=$(run_pre_bash_rc 'git push origin +main:refs/heads/main')
assert_exit "git-safety · +main:refs/heads/main → block" 2 "$RC"
RC=$(run_pre_bash_rc 'git -C repo commit --amend -m x')
assert_exit "git-safety · -C 前缀 commit --amend → block" 2 "$RC"
RC=$(run_pre_bash_rc 'git --git-dir=x/.git reset --hard')
assert_exit "git-safety · --git-dir 前缀 reset --hard → block" 2 "$RC"
RC=$(run_pre_bash_rc 'git push origin dev')
assert_exit "git-safety · push feature 分支 → pass" 0 "$RC"
RC=$(run_pre_bash_rc 'git push origin +feature/main-fix')
assert_exit "git-safety · +feature/main-fix（含 main 子串分支）→ pass" 0 "$RC"
RC=$(run_pre_bash_rc 'git push origin main')
assert_exit "git-safety · 无 --force push main → pass" 0 "$RC"
RC=$(run_pre_bash_rc 'git commit -m "git push --force origin main"')
assert_exit "git-safety · commit msg 提及（引号剥除）→ pass" 0 "$RC"
RC=$(run_pre_bash_rc 'ruff check x.py .claude/skills/prototype/scripts/build_proto_skeleton.py')
assert_exit "paradigm · ruff 文件列表提及 build_proto（参数≠调用）→ pass" 0 "$RC"
RC=$(run_pre_bash_rc 'grep -n anno .claude/skills/prototype/scripts/build_proto_skeleton.py')
assert_exit "paradigm · grep 提及 build_proto（参数≠调用）→ pass" 0 "$RC"
RC=$(run_pre_bash_rc 'python3 projects/moderation/scripts/build_proto_v1.py --end app')
assert_exit "paradigm · 命令位真调用（moderation 无范式）→ block" 2 "$RC"
RC=$(run_pre_bash_rc 'cd projects/moderation/scripts && python3 build_proto_v2.py')
assert_exit "paradigm · cd 后真调用 → block" 2 "$RC"
RC=$(run_pre_bash_rc 'python3 .claude/skills/prototype/scripts/build_proto_skeleton.py -p moderation')
assert_exit "paradigm · -p 空格式真调用（无 projects/ 路径）→ block" 2 "$RC"
RC=$(run_pre_bash_rc 'python3 .claude/skills/prototype/scripts/build_proto_skeleton.py -pmoderation')
assert_exit "paradigm · -p 连写式真调用 → block" 2 "$RC"
RC=$(run_pre_bash_rc 'SKIP_PROTOTYPE_PARADIGM_GATE=1 python3 projects/moderation/scripts/build_proto_v1.py')
assert_exit "paradigm · SKIP inline 前缀 → bypass" 0 "$RC"
SKIP_ENV_RC=$(printf '{"tool_name":"Bash","tool_input":{"command":"python3 projects/moderation/scripts/build_proto_v1.py"}}' \
  | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" SKIP_PROTOTYPE_PARADIGM_GATE=1 \
  bash .claude/hooks/pre-bash-guard.sh >/dev/null 2>&1; echo $?)
assert_exit "paradigm · SKIP env 通道 → bypass" 0 "$SKIP_ENV_RC"
RC=$(run_pre_bash_rc 'python3 projects/livestream/scripts/build_proto_v23.py')
assert_exit "paradigm · 尾段归一化（livestream/scripts → livestream 顶层 anchors 有范式）→ pass" 0 "$RC"

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ required-read-gate · 提示与判定同源（照提示做要能解锁）═══"

# 改 prd 产物但只读了 SKILL.md：轻量提示只教读 SKILL.md，照做仍被拦 → 必须改列显式缺失清单
run_pre_gate_err() {
  echo "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$1\"},\"transcript_path\":\"$2\"}" \
    | bash .claude/hooks/pre-writeedit-guard.sh 2>&1 >/dev/null
}
T_PARTIAL="$D/t_partial.jsonl"
make_hit "$T_PARTIAL" "/p/.claude/skills/prd/SKILL.md"
ERR_PARTIAL=$(run_pre_gate_err "/p/projects/x/deliverables/prd-foo.md" "$T_PARTIAL")
assert_grep "req-read · 部分已读 → 列出未读的 info-ownership" "Read.*info-ownership" "$ERR_PARTIAL"
assert_no_grep "req-read · 部分已读 → 不给「只读 SKILL.md 就够」的轻量提示" "limit=120" "$ERR_PARTIAL"

# 一个 guide 都没读且该产物只有单一 guide：轻量提示成立（提示 = 判定，照做即解锁）
ERR_SINGLE=$(run_pre_gate_err "$ROOT/scripts/check_new.py" "$T_MISS")
assert_grep "req-read · 单 guide 缺失 → 显式给 Read 命令" "Read.*SCRIPTS_WRITING" "$ERR_SINGLE"

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ proto-drift-warn · 共享场景库跨版本漂移提示 ═══"
run_post_bash() {
  local proj="${PROJ:-$ROOT}"
  echo "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"$1\"}}" \
    | CLAUDE_PROJECT_DIR="$proj" bash .claude/hooks/post-bash-deliverable-check.sh 2>&1 >/dev/null
}
# 确定性 fixture 沙箱（不依赖真实工区干净度）：干净 / 真漂移 / frozen 三态
mkdir -p "$SANDBOX/projects/sbx/scripts/src" "$SANDBOX/projects/sbx/deliverables/fv"
ln -s "$ROOT/.claude" "$SANDBOX/.claude"  # hook 自身 lib 从真实 .claude 读，漂移扫描根 = 沙箱
printf 'x' > "$SANDBOX/projects/sbx/scripts/src/f.py"
sbx_lock() { # $1 = frozen 标志（true/false，JSON 字面量）
  local h
  h=$(python3 -c "import hashlib;print(hashlib.sha256(open('$SANDBOX/projects/sbx/scripts/src/f.py','rb').read()).hexdigest()[:16])")
  printf '{"version": "fv", "frozen": %s, "inputs": {"app": {"f.py": "%s"}}}\n' "$1" "$h" \
    > "$SANDBOX/projects/sbx/deliverables/fv/.proto-lock.json"
}
sbx_lock false
PROJ="$SANDBOX" DRIFT_CLEAN=$(run_post_bash 'python3 projects/sbx/scripts/build_proto_v1.py')
assert_no_grep "proto-drift · 干净库不吵（沙箱 fixture）" "proto-drift-warn" "$DRIFT_CLEAN"
printf 'y' > "$SANDBOX/projects/sbx/scripts/src/f.py"
PROJ="$SANDBOX" DRIFT_DIRTY=$(run_post_bash 'python3 projects/sbx/scripts/build_proto_v1.py')
assert_grep "proto-drift · 真漂移要吵" "proto-drift-warn" "$DRIFT_DIRTY"
sbx_lock true
PROJ="$SANDBOX" DRIFT_FROZEN=$(run_post_bash 'python3 projects/sbx/scripts/build_proto_v1.py')
assert_no_grep "proto-drift · frozen 脏库豁免不吵" "proto-drift-warn" "$DRIFT_FROZEN"
DRIFT_CLEAN_REAL=$(run_post_bash 'python3 projects/livestream/scripts/build_proto_v24.py')
assert_no_grep "proto-drift · 真实工区封版 2.3 豁免不吵" "proto-drift-warn" "$DRIFT_CLEAN_REAL"
DRIFT_OFF=$(SKIP_PROTO_DRIFT_WARN=1 run_post_bash 'python3 projects/livestream/scripts/build_proto_v24.py')
assert_no_grep "proto-drift · SKIP env → bypass" "proto-drift-warn" "$DRIFT_OFF"
DRIFT_NOTRIG=$(run_post_bash 'python3 scripts/dashboard.py')
assert_no_grep "proto-drift · 非 build 命令不触发" "proto-drift-warn" "$DRIFT_NOTRIG"

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ prototype-audit · Bash build 路径可达（Write/Edit 被 deliverable-source-gate 挡死）═══"
# 同名 gate 也挂在 Write|Edit dispatcher 上，但脚本化 HTML 禁直 Write/Edit，
# 那条路径物理不可达 → 正常产出流必须由本条 Bash 路径捕获。
run_post_bash_rc() {
  local proj="${PROJ:-$ROOT}"
  echo "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"$1\"}}" \
    | CLAUDE_PROJECT_DIR="$proj" bash .claude/hooks/post-bash-deliverable-check.sh >/dev/null 2>&1
  echo $?
}
sbx_lock true   # 借上节沙箱，冻掉 drift 噪音，只看 audit 结论
printf '<html><body><div class="app-mock"><div class="phone">x</div></div></body></html>' \
  > "$SANDBOX/projects/sbx/deliverables/fv/proto-sbx-bad.html"
PROJ="$SANDBOX" AUDIT_BAD=$(run_post_bash 'python3 projects/sbx/scripts/build_proto_v1.py')
assert_grep "proto-audit · 失分产物 → 报 gate 名" "prototype-audit" "$AUDIT_BAD"
assert_grep "proto-audit · 提示指向 V 组图鉴" "visual-rework-atlas" "$AUDIT_BAD"
PROJ="$SANDBOX" RC=$(run_post_bash_rc 'python3 projects/sbx/scripts/build_proto_v1.py')
assert_exit "proto-audit · 失分产物 → block" 2 "$RC"
PROJ="$SANDBOX" RC=$(run_post_bash_rc 'SKIP_PROTOTYPE_AUDIT=1 python3 projects/sbx/scripts/build_proto_v1.py')
assert_exit "proto-audit · SKIP inline → bypass" 0 "$RC"
PROJ="$SANDBOX" RC=$(run_post_bash_rc 'python3 scripts/dashboard.py')
assert_exit "proto-audit · 非 build 命令不触发" 0 "$RC"
# 已交付标杆必须全绿，否则新门会把正常重建全拦下
cp "$ROOT/projects/community/deliverables/2026Q3/3.4/proto-community-3.4.html" \
   "$SANDBOX/projects/sbx/deliverables/fv/proto-sbx-good.html" 2>/dev/null
rm -f "$SANDBOX/projects/sbx/deliverables/fv/proto-sbx-bad.html"
PROJ="$SANDBOX" RC=$(run_post_bash_rc 'python3 projects/sbx/scripts/build_proto_v1.py')
assert_exit "proto-audit · 标杆产物 → pass（新门不误伤已交付）" 0 "$RC"

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ script-syntax-gate · F401 不当阻断闸（两步 Edit 中间态假阳）═══"
if python3 -m ruff --version >/dev/null 2>&1; then
  printf 'import os\n\n\ndef f():\n    return 1\n'   > "$D/unused_import.py"
  printf 'def f():\n    return undefined_name\n'      > "$D/undef_name.py"
  run_post_syntax "$D/unused_import.py" >/dev/null
  assert_exit "syntax · 仅 F401 未用 import → pass（中间态不误拦）" 0 $?
  run_post_syntax "$D/undef_name.py" >/dev/null
  assert_exit "syntax · F821 未定义名 → block（真崩项仍拦）" 2 $?
else
  echo "  [SKIP] 未装 ruff（当前走 py_compile 降级，F 类检查不生效）"
fi

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ pre-task-prompt-scrub.sh · tool_name 兼容 Agent/Task ═══"
# 回归防线：Agent 工具现名必须拦/放行，旧名 Task 一并兼容（matcher 失配事故复发即红）
AG120="$(printf 'x%.0s' {1..120})"   # 过 <100 短路阈值的超长 prompt
echo "{\"tool_name\":\"Agent\",\"tool_input\":{\"prompt\":\"$AG120\"}}" \
  | bash .claude/hooks/pre-task-prompt-scrub.sh 2>/dev/null
assert_exit "scrub · Agent 无 session-state → block" 2 $?
echo "{\"tool_name\":\"Agent\",\"tool_input\":{\"prompt\":\"$AG120 禁读写 .claude/session-state.md\"}}" \
  | bash .claude/hooks/pre-task-prompt-scrub.sh 2>/dev/null
assert_exit "scrub · Agent 含 session-state → pass" 0 $?
echo "{\"tool_name\":\"Task\",\"tool_input\":{\"prompt\":\"$AG120\"}}" \
  | bash .claude/hooks/pre-task-prompt-scrub.sh 2>/dev/null
assert_exit "scrub · 旧名 Task 无 phrase → block" 2 $?

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ session-start.sh · resume 成本注入 ═══"
# 沙箱 PROJECT_DIR（$D 内，trap 自清）：真 lib 经 symlink 载入；STATE/DASHBOARD 缺席
# → 只剩 resume 成本行 + 尾注，绝不触碰真 .claude/session-state.md（72h auto-clear 误删防线）
SS_SB="$D/ss-proj"
mkdir -p "$SS_SB/.claude/hooks"
ln -s "$ROOT/.claude/hooks/lib" "$SS_SB/.claude/hooks/lib"
run_ss() {
  CLAUDE_PROJECT_DIR="$SS_SB" CLAUDE_HOOK_TEST=1 bash "$ROOT/.claude/hooks/session-start.sh" 2>/dev/null
}
SS_RESUME=$(echo '{"source":"resume","seconds_since_last_response":246656,"context_tokens":23443,"estimated_cache_write_usd":0.1465}' | run_ss)
assert_grep "ss · resume+字段齐 → 注入成本行" "resume 成本（session 已闲置 68h · context 23443 tok · re-cache ≈ \$0.1465" "$SS_RESUME"
SS_STARTUP=$(echo '{"source":"startup"}' | run_ss)
assert_no_grep "ss · startup → 零成本行" "resume 成本" "$SS_STARTUP"
SS_EMPTY=$(run_ss < /dev/null)
assert_no_grep "ss · 裸跑空 stdin → 零成本行不卡死" "resume 成本" "$SS_EMPTY"

# ═══════════════════════════════════════════════════════════════
echo ""
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -gt 0 ]; then
  echo "❌ $FAIL / $TOTAL failed"
  exit 1
fi
echo "✅ $PASS / $TOTAL passed"
exit 0
