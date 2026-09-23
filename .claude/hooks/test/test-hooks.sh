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

# 误拦白名单（下载类命令一律放行 · commit 1be8b44 曾干掉 ~1300 次假阳性 warn）
# 代理判定已迁至 pre-proxy-check.sh，其命中/排除语义在下方 S2.8 段；这里守的是
# pre-bash-guard 自身（git-safety / git-https-gate 等）不对下载命令越权拦截。
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
# 三句完整的短句（句长够）→ 放行：段落不再数句号，罚的是碎句与长句
printf '# t\n\n目前这条漏斗没有看板。运营每天只能手工拉数。我们想做一张看板。\n' > "$D/projects/bdproj/deliverables/prd-bdshort.md"
BDSH_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/bdproj/deliverables/prd-bdshort.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_no_grep "bullet-density · 三句完整短句放行" "bullet-density-gate" "$BDSH_OUT"
# 单句 ≥100 字（逗号焊成的长枚举）→ block
printf '# t\n\n平仓盈利顶飘的触发要覆盖主动平仓、止盈止损触发、部分平仓三种情况，并且每一笔都要显示本次已实现盈亏与收益率两个数字，以及对应的晒单入口按钮位置说明，和不再显示的勾选逻辑说明，还要区分合约与现货两条链路\n' > "$D/projects/bdproj/deliverables/prd-bdlong.md"
BDL_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/bdproj/deliverables/prd-bdlong.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_grep "bullet-density · 单句 ≥100 字 → block" "bullet-density-gate" "$BDL_OUT"

echo ""
echo "═══ S2.6b · md-blockquote-gate（项目 md 新增引用墙 block，合批路径）═══"
# 连排两行引用墙 → block（$D 非 git 仓 → untracked 全文即新增）
printf '# t\n\n> 第一行导读\n> 第二行导读\n\n正文\n' > "$D/projects/bdproj/notes-bq.md"
BQ_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/bdproj/notes-bq.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_grep "md-blockquote · 连排引用墙 → block" "md-blockquote-gate" "$BQ_OUT"
# 单行短引用 → 干净（不构成墙）
printf '# t\n\n> 单行短说明\n\n正文\n' > "$D/projects/bdproj/notes-bqc.md"
BQC_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/bdproj/notes-bqc.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_no_grep "md-blockquote · 单行短引用不误报" "md-blockquote-gate" "$BQC_OUT"
# prd 路径豁免（引用墙检查走 check_prd_md，本门不触发）
printf '# t\n\n> 墙一\n> 墙二\n' > "$D/projects/bdproj/deliverables/prd-bqx.md"
BQX_OUT=$(printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/bdproj/deliverables/prd-bqx.md"}}' "$D" | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-writeedit-dispatch.sh 2>&1)
assert_no_grep "md-blockquote · prd 路径豁免" "md-blockquote-gate" "$BQX_OUT"

echo ""
echo "═══ S2.6c · prd-content-gate（PRD 写入新增行内容硬错 block）═══"
# git-init 沙箱：本门 diff-based，「旧账不卡」只有 tracked 文件才测得出
PC_SB="$D/pcsbx"
mkdir -p "$PC_SB/projects/pcproj/deliverables"
ln -s "$ROOT/.claude" "$PC_SB/.claude"; ln -s "$ROOT/scripts" "$PC_SB/scripts"
git -C "$PC_SB" init -q
_pc_run() {  # $1 = 沙箱内 PRD 相对路径
  (cd "$PC_SB" && printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/%s"}}' "$PC_SB" "$1" \
    | TMPDIR="$(mktemp -d)" CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$PC_SB" \
      bash "$ROOT/.claude/hooks/post-writeedit-dispatch.sh" 2>&1)
}
# 新增行含行内版本标签 → block
printf '# t\n\n- 打赏入口（v2.1 新增）\n' > "$PC_SB/projects/pcproj/deliverables/prd-pchit.md"
PCH_OUT=$(_pc_run projects/pcproj/deliverables/prd-pchit.md)
assert_grep "prd-content · 新增违规行 → block" "prd-content-gate" "$PCH_OUT"
# 干净的新 PRD → 不误报
printf '# t\n\n- 打赏入口\n- 用户完成签到后获得奖励\n' > "$PC_SB/projects/pcproj/deliverables/prd-pcclean.md"
PCC_OUT=$(_pc_run projects/pcproj/deliverables/prd-pcclean.md)
assert_no_grep "prd-content · 干净新 PRD 不误报" "prd-content-gate" "$PCC_OUT"
# 已提交的旧账 + 一行干净新增 → 只报新增行，旧账不卡
printf '# t\n\n- 打赏入口（v2.1 新增）\n' > "$PC_SB/projects/pcproj/deliverables/prd-pcold.md"
git -C "$PC_SB" add -A >/dev/null 2>&1
git -C "$PC_SB" -c user.email=t@t -c user.name=t commit -q -m init >/dev/null 2>&1
printf '# t\n\n- 打赏入口（v2.1 新增）\n- 用户完成签到后获得奖励\n' > "$PC_SB/projects/pcproj/deliverables/prd-pcold.md"
PCO_OUT=$(_pc_run projects/pcproj/deliverables/prd-pcold.md)
assert_no_grep "prd-content · 旧账加干净新增行不拦" "prd-content-gate" "$PCO_OUT"
# 同一沙箱里再加一行违规 → 照拦（证明门在该仓真跑，上一条不是被 skip 掉的假绿）
printf '# t\n\n- 打赏入口（v2.1 新增）\n- 用户完成签到后获得奖励\n- 展示 hover 提示\n' > "$PC_SB/projects/pcproj/deliverables/prd-pcold.md"
PCO2_OUT=$(_pc_run projects/pcproj/deliverables/prd-pcold.md)
assert_grep "prd-content · 旧账仓内新增违规行照拦" "prd-content-gate" "$PCO2_OUT"

# 同一 git 沙箱测 plain-language 的 --added-only：旧账（已提交）违规不卡，新增行才判
printf '# t\n\n见 baseline.md 的口径。\n' > "$PC_SB/projects/pcproj/deliverables/report-plain.md"
git -C "$PC_SB" add -A >/dev/null 2>&1
git -C "$PC_SB" -c user.email=t@t -c user.name=t commit -q -m plain >/dev/null 2>&1
printf '# t\n\n见 baseline.md 的口径。\n用户完成签到后获得奖励。\n' > "$PC_SB/projects/pcproj/deliverables/report-plain.md"
PL_OUT=$(_pc_run projects/pcproj/deliverables/report-plain.md)
assert_no_grep "plain-language · 旧账加干净新增行不拦" "plain-language-gate" "$PL_OUT"
printf '# t\n\n见 baseline.md 的口径。\n用户完成签到后获得奖励。\n见 scene-list.md 的口径。\n' > "$PC_SB/projects/pcproj/deliverables/report-plain.md"
PL2_OUT=$(_pc_run projects/pcproj/deliverables/report-plain.md)
assert_grep "plain-language · 新增违规行照拦" "plain-language-gate" "$PL2_OUT"

echo ""
echo "═══ 产品线三查 · campaign 嵌套口径（growth/queen 不再静默 skip）═══"
# git-init 沙箱工区：checker 的 find_root 走 cwd git rev-parse → 锚定沙箱（软链真仓 .claude/scripts）
QSBX="$D/qsbx"
mkdir -p "$QSBX/projects/growth/queen/deliverables/2026Q3/1.0" "$QSBX/projects/liveline/deliverables/2026Q3/2.3"
ln -s "$ROOT/.claude" "$QSBX/.claude"; ln -s "$ROOT/scripts" "$QSBX/scripts"
git -C "$QSBX" init -q && git -C "$QSBX" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
_qsbx_proj() {  # $1=项目路径段（growth/queen | liveline）
  local bn="${1##*/}"  # baseline 文件名取项目 leaf：prd-*-baseline.md 模式要求中间有段
  printf '# 场景清单\n\n| 编号 | 场景 | 描述 |\n| --- | --- | --- |\n| A-1 | 签到 | 用户完成签到后获得奖励 |\n' > "$QSBX/projects/$1/scene-list.md"
  printf '# Baseline\n\n## 1. 现状\n\n用户完成签到后获得奖励。\n\n## 9. 版本历史\n\n| 日期 | 模块 | delta | 状态 |\n| --- | --- | --- | --- |\n' > "$QSBX/projects/$1/prd-${bn}-baseline.md"
}
_qsbx_stale_delta() {  # 已上线但 changelog 无行 → baseline-fresh 🔴
  printf '# Delta\n\n状态：已上线\n\n## 1. 目标\n\n用户完成签到后获得奖励（A-1）。\n' > "$1"
}
# 嵌套项目：delta 写入 → 产线三查必须真跑（此前单段抽取静默 skip），产品线行须是全段
_qsbx_proj growth/queen
_qsbx_stale_delta "$QSBX/projects/growth/queen/deliverables/2026Q3/1.0/prd-queen-1.0.md"
QD_OUT=$(cd "$QSBX" && printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/growth/queen/deliverables/2026Q3/1.0/prd-queen-1.0.md"}}' "$QSBX" \
  | TMPDIR="$(mktemp -d)" CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$QSBX" bash "$ROOT/.claude/hooks/post-writeedit-dispatch.sh" 2>&1)
assert_grep "产线三查 · 嵌套项目不再静默 skip" "baseline-fresh-gate" "$QD_OUT"
assert_grep "产线三查 · 产品线行取全段 growth/queen" "产品线: growth/queen" "$QD_OUT"
# 单段项目回归：口径不变（首段）
_qsbx_proj liveline
_qsbx_stale_delta "$QSBX/projects/liveline/deliverables/2026Q3/2.3/prd-liveline-2.3.md"
QL_OUT=$(cd "$QSBX" && printf '{"tool_name":"Edit","tool_input":{"file_path":"%s/projects/liveline/deliverables/2026Q3/2.3/prd-liveline-2.3.md"}}' "$QSBX" \
  | TMPDIR="$(mktemp -d)" CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$QSBX" bash "$ROOT/.claude/hooks/post-writeedit-dispatch.sh" 2>&1)
assert_grep "产线三查 · 单段项目回归不变" "产品线: liveline" "$QL_OUT"

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
# Skill 工具调用也记 skill triggered（这条路径没有 Read 事件，靠 tool_input.skill 认）
PSL_TOOL=$(printf '{"tool_name":"Skill","tool_input":{"skill":"code-review","args":""}}' | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-skill-load.sh 2>&1; echo "rc=$?")
assert_grep "post-skill-load · Skill 工具调用不早退（exit 0）" "rc=0" "$PSL_TOOL"
PSL_TOOL_EMPTY=$(printf '{"tool_name":"Skill","tool_input":{"args":""}}' | CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash .claude/hooks/post-skill-load.sh 2>&1; echo "rc=$?")
assert_grep "post-skill-load · Skill 无 skill 名不炸（exit 0）" "rc=0" "$PSL_TOOL_EMPTY"
PSL_PARSE=$(INPUT='{"tool_name":"Skill","tool_input":{"skill":"code-review"}}' bash -c 'source .claude/hooks/lib/input.sh; hook_parse_skill; printf "%s|%s" "$HOOK_TOOL_NAME" "$HOOK_SKILL_NAME"')
assert_grep "hook_parse_skill · 取出 Skill 名" "Skill|code-review" "$PSL_PARSE"

# ═══ S2.8 · pre-proxy-check：外网下载命令自动挂代理（注入契约 + 排除表）═══
# 「有没有代理」用 PROXY_FORCE 钉死，否则断言随本机代理开关而变 —— 这是本门唯一需要的逃生口。
# payload 必须带 tool_name：门内 require_bash 靠它早退，缺了就静默 pass（假绿）。
PROXY_HOOK=".claude/hooks/pre-proxy-check.sh"
FAKE_PROXY="http://127.0.0.1:9"      # 不需要真在听：PROXY_FORCE 直接采信
run_proxy() {                        # $1=命令  $2..=额外 env 赋值
  local cmd="$1"; shift
  jq -nc --arg c "$cmd" '{tool_name:"Bash",tool_input:{command:$c}}' \
    | env "$@" CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash "$PROXY_HOOK" 2>/dev/null
}

# 粗筛：下载命令命中（含命令开头的双词 go get），含 "go" 子串的非下载命令不误判
assert_grep "proxy-check · pip install 有代理时注入" "updatedInput" \
  "$(run_proxy 'pip install requests' "PROXY_FORCE=$FAKE_PROXY")"
assert_grep "proxy-check · go get 命中（命令开头双词 glob，粗筛不漏）" "updatedInput" \
  "$(run_proxy 'go get github.com/x/y' "PROXY_FORCE=$FAKE_PROXY")"
assert_eq "proxy-check · 非下载命令（含 go 子串）不注入" "0" \
  "$(run_proxy 'echo django logo' "PROXY_FORCE=$FAKE_PROXY" | wc -c | tr -d ' ')"
assert_eq "proxy-check · 判定不到代理时不注入（境外 / 代理未启动）" "0" \
  "$(run_proxy 'pip install requests' 'PROXY_FORCE=direct' | wc -c | tr -d ' ')"

# 注入产物契约：stdout 单行 JSON；updatedInput 是**整体替换**，其余 tool_input 键必须原样带回
PROXY_OUT=$(jq -nc '{tool_name:"Bash",tool_input:{command:"brew install jq",description:"装 jq",timeout:60000,run_in_background:true}}' \
  | env "PROXY_FORCE=$FAKE_PROXY" CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" bash "$PROXY_HOOK" 2>/dev/null)
assert_eq "proxy-check · 注入 stdout 只有一行" "1" \
  "$(printf '%s' "$PROXY_OUT" | grep -c .)"
assert_eq "proxy-check · hookEventName=PreToolUse" "PreToolUse" \
  "$(printf '%s' "$PROXY_OUT" | jq -r '.hookSpecificOutput.hookEventName // ""' 2>/dev/null)"
assert_eq "proxy-check · permissionDecision=allow（注入后白名单前缀匹配不上）" "allow" \
  "$(printf '%s' "$PROXY_OUT" | jq -r '.hookSpecificOutput.permissionDecision // ""' 2>/dev/null)"
assert_eq "proxy-check · updatedInput 带回其余 tool_input 键" "1" \
  "$(printf '%s' "$PROXY_OUT" | jq -r 'if (.hookSpecificOutput.updatedInput | {description,timeout,run_in_background}) == {description:"装 jq",timeout:60000,run_in_background:true} then 1 else 0 end' 2>/dev/null)"
assert_eq "proxy-check · command 以 export 前置、原命令在尾部" "1" \
  "$(printf '%s' "$PROXY_OUT" | jq -r 'if ((.hookSpecificOutput.updatedInput.command | startswith("export ")) and (.hookSpecificOutput.updatedInput.command | endswith("brew install jq"))) then 1 else 0 end' 2>/dev/null)"
assert_eq "proxy-check · 注入带 NO_PROXY（护本机 webapp / 控制口）" "1" \
  "$(printf '%s' "$PROXY_OUT" | jq -r 'if (.hookSpecificOutput.updatedInput.command | contains("NO_PROXY=")) then 1 else 0 end' 2>/dev/null)"

# 排除表：命中但原样放行（含带引号字面量的形态，走 jq 构造 payload 免转义踩坑）
for _case in 'ALL_PROXY=http://x pip install requests' \
             'curl --proxy http://x https://github.com/u/r' \
             'pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple requests' \
             'SKIP_PROXY_CHECK_GATE=1 brew install jq' \
             'SKIP_PROXY_CHECK=1 brew install jq' \
             'env -u ALL_PROXY brew install jq' \
             'sudo brew install jq' \
             'git clone git@github.com:owner/repo.git' \
             'git commit -m "brew install jq"'; do
  assert_eq "proxy-check · 排除表放行：${_case:0:40}" "0" \
    "$(run_proxy "$_case" "PROXY_FORCE=$FAKE_PROXY" | wc -c | tr -d ' ')"
done

# 静态 deny 锚点守卫：以 deny 开头形态起手的命令不注入（否则前缀一换，deny 就匹配不上了）
for _case in 'rm -rf /tmp/x && pip install requests' \
             'git push origin main && pip install requests' \
             'sudo brew install jq'; do
  assert_eq "proxy-check · deny 锚点不注入：${_case:0:34}" "0" \
    "$(run_proxy "$_case" "PROXY_FORCE=$FAKE_PROXY" | wc -c | tr -d ' ')"
done

# 模式开关：off 整条关；block 退回阻断并 exit 2
assert_eq "proxy-check · PROXY_GATE_MODE=off 整条关" "0" \
  "$(run_proxy 'brew install jq' PROXY_GATE_MODE=off "PROXY_FORCE=$FAKE_PROXY" | wc -c | tr -d ' ')"
jq -nc '{tool_name:"Bash",tool_input:{command:"brew install jq"}}' \
  | env PROXY_GATE_MODE=block "PROXY_FORCE=$FAKE_PROXY" CLAUDE_HOOK_TEST=1 CLAUDE_PROJECT_DIR="$ROOT" \
    bash "$PROXY_HOOK" >/dev/null 2>&1
assert_exit "proxy-check · PROXY_GATE_MODE=block 退回阻断" 2 $?

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
mkdir -p "$SANDBOX/projects/sbx/scripts/src/scenes" "$SANDBOX/projects/sbx/deliverables/fv"
# 沙箱按真实项目形态建 src/scenes：Bash 路径的拆分门要求交付产物背后有分场景源码，
# 缺它会让下面 proto-audit 两条断言被拆分门连带拦下（fixture 不真实，非真误伤）
printf 'def page_fv():\n    return ""\n' > "$SANDBOX/projects/sbx/scripts/src/scenes/s_fv.py"
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

# 触发判定单元表（gate 验意图不验表面）：命令位 python3 直呼 / 脚本即首词 = 执行，
# 必触发（usage.jsonl 反查 46 条真执行全为此形态）；cat/head/wc/grep/find/for/
# 重定向写文件 = 提及不算执行，不触发（111 条误触全来自这类形态）
PDGEN_RC() {  # $1=命令文本 → 0 触发 / 1 不触发
  bash -c 'source "$1/.claude/hooks/lib/checkers.sh"; _proto_cmd_runs_generator "$2"' _ "$ROOT" "$1" >/dev/null 2>&1
  echo $?
}
assert_eq "proto-drift 触发 · 命令位 python3 直呼"          "0" "$(PDGEN_RC 'python3 build_proto_v1.py')"
assert_eq "proto-drift 触发 · && 后带路径与 flag"           "0" "$(PDGEN_RC 'cd projects/x && python3 scripts/build_proto_v25.py --force')"
assert_eq "proto-drift 触发 · env 赋值前缀"                 "0" "$(PDGEN_RC 'FOO=1 python3 projects/livestream/scripts/build_proto_v24.py')"
assert_eq "proto-drift 触发 · 解释器 flag"                  "0" "$(PDGEN_RC 'python3 -u ./build_proto_v10.py')"
assert_eq "proto-drift 触发 · python3.x 版本号"             "0" "$(PDGEN_RC 'python3.11 build_proto_v1.py')"
assert_eq "proto-drift 触发 · nohup 前缀"                   "0" "$(PDGEN_RC 'nohup python3 build_proto_v1.py &')"
assert_eq "proto-drift 触发 · 脚本即首词直执行"             "0" "$(PDGEN_RC './build_proto_v2.py --out x.html')"
assert_eq "proto-drift 触发 · 多行命令的后续行"             "0" "$(PDGEN_RC 'echo hi
python3 build_proto_v1.py')"
assert_eq "proto-drift 不触发 · cat 查看源码"               "1" "$(PDGEN_RC 'cat build_proto_v25.py')"
assert_eq "proto-drift 不触发 · head 看前段"                "1" "$(PDGEN_RC 'head -60 projects/x/scripts/build_proto_v10.py')"
assert_eq "proto-drift 不触发 · wc 统计行数"                "1" "$(PDGEN_RC 'wc -l build_proto_v1.py')"
assert_eq "proto-drift 不触发 · grep 参数提及"              "1" "$(PDGEN_RC 'grep -n build_proto_v24.py README.md')"
assert_eq "proto-drift 不触发 · find -name 检索"            "1" "$(PDGEN_RC 'find projects -name build_proto_v*.py')"
assert_eq "proto-drift 不触发 · for 遍历文件名"             "1" "$(PDGEN_RC 'for f in build_proto_v1.py build_proto_v2.py; do echo "$f"; done')"
assert_eq "proto-drift 不触发 · 重定向写文件本体"           "1" "$(PDGEN_RC 'cat > build_proto_v10.py <<EOF')"
assert_eq "proto-drift 不触发 · git log 路径参数"           "1" "$(PDGEN_RC 'git log --oneline -- build_proto_v1.py')"
assert_eq "proto-drift 不触发 · python3 跑别的脚本仅提及"   "1" "$(PDGEN_RC 'python3 scripts/telemetry.py funnel  # build_proto_v25.py')"

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
cp "$ROOT/projects/community/deliverables/2026Q3/3.4.2/proto-community-3.4.2.html" \
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
# F2 回归：裸提及 session-state（让子代理去读）不是合规——修前「出现即放行」挡不住
echo "{\"tool_name\":\"Agent\",\"tool_input\":{\"prompt\":\"$AG120 请先 read .claude/session-state.md 然后继续\"}}" \
  | bash .claude/hooks/pre-task-prompt-scrub.sh 2>/dev/null
assert_exit "scrub · 裸提及 read session-state（无禁止词）→ block" 2 $?
echo "{\"tool_name\":\"Agent\",\"tool_input\":{\"prompt\":\"$AG120 Do not read or write .claude/session-state.md\"}}" \
  | bash .claude/hooks/pre-task-prompt-scrub.sh 2>/dev/null
assert_exit "scrub · 英文禁止句式（do not）→ pass" 0 $?

echo ""
echo "── user-prompt-warn.sh · 量化目标判定（F1：Q3/v2 顺带数字不算指标）──"
# 提醒走 stdout hookSpecificOutput.additionalContext（注入模型，非 systemMessage）；
# dedup 600s 全局键 stale 即 touch 占配额 → 每个 fire 断言前清缓存
_pmg_clear() { rm -f "${TMPDIR:-/tmp}/pmws_dedup/pm-gate-reminder."* 2>/dev/null; }
run_reqguard() { printf '{"prompt":"%s"}' "$1" | bash .claude/hooks/user-prompt-warn.sh 2>/dev/null; }
_pmg_clear
assert_grep "req · 无数字模糊需求 → 提醒" "pm-gate-reminder" "$(run_reqguard '写需求：优化主播留存率，完善开播流程')"
_pmg_clear
assert_grep "req · Q3 顺带数字仍模糊 → 提醒（F1 修前漏）" "pm-gate-reminder" "$(run_reqguard '写需求：优化主播留存率，目标 Q3 上线')"
_pmg_clear
assert_grep "req · v2 顺带数字仍模糊 → 提醒（F1 修前漏）" "pm-gate-reminder" "$(run_reqguard '写需求：提升 v2 的转化率，改善下单流程')"
_pmg_clear
# 通道断言：内容对了但发错人（写进 systemMessage）时，仅断言内容测不出来——必须锁字段名。
# 该 gate 曾因这个错误自上线起从未被模型收到。
assert_grep "req · 通道 = hookSpecificOutput.additionalContext（非 systemMessage）" "hookSpecificOutput" "$(run_reqguard '写需求：优化主播留存率，完善开播流程')"
_pmg_clear
assert_no_grep "req · 不得落到 systemMessage（发错人 = 失效）" "systemMessage" "$(run_reqguard '写需求：优化主播留存率，完善开播流程')"
assert_no_grep "req · 真实指标 42%→55% → 不提醒" "pm-gate-reminder" "$(run_reqguard '写需求：次日留存从 42% 提升到 55%')"

echo ""
echo "── user-prompt-warn.sh · context 压力切压缩边界（F2：刚 compact 完反被催 compact）──"
# 修前：transcript 追加式写，压缩边界不删旧行，边界已落地而压缩后首条 assistant 消息尚未
# 写进来时，末条缓存读仍是压缩前的旧值 → /compact 后第一条 prompt 照报 460K（真值 ~40K）。
# 每个 case 前清 dedup 缓存（pm-gate-reminder 与 context-warn 同进程，全局键 stale 会占配额）
# BSD 的 mktemp 只替换模板末尾连续 X，带后缀的模板原样返回 → 用 $D 内固定名
CTX_A="$D/ctx-compact-first.jsonl"
CTX_B="$D/ctx-no-boundary.jsonl"
CTX_C="$D/ctx-after-boundary.jsonl"
CTX_D="$D/ctx-quoted-boundary.jsonl"
run_ctxguard() { printf '{"prompt":"继续","transcript_path":"%s"}' "$1" | bash .claude/hooks/user-prompt-warn.sh 2>/dev/null; }
BIG='{"type":"assistant","message":{"model":"deepseek-flash","usage":{"input_tokens":100,"cache_creation_input_tokens":0,"cache_read_input_tokens":460000,"output_tokens":50}},"timestamp":"2026-09-15T08:34:00.000Z"}'
BOUND='{"type":"system","subtype":"compact_boundary","content":"Conversation compacted","timestamp":"2026-09-15T08:36:04.000Z"}'
SMALL='{"type":"assistant","message":{"model":"deepseek-flash","usage":{"input_tokens":29271,"cache_creation_input_tokens":0,"cache_read_input_tokens":10752,"output_tokens":50}},"timestamp":"2026-09-15T08:37:53.000Z"}'
PROMPT='{"type":"user","message":{"role":"user","content":"继续"}}'

printf '%s\n%s\n%s\n' "$BIG" "$BOUND" "$PROMPT" > "$CTX_A"
assert_no_grep "ctx · 压缩后首条 prompt 不报压缩前旧值（F2 修前误报 460K）" "context 缓存读取 460K" "$(run_ctxguard "$CTX_A")"
printf '%s\n%s\n' "$BIG" "$PROMPT" > "$CTX_B"
assert_grep "ctx · 无压缩边界时同值仍报（对照：检查没被关掉）" "context 缓存读取 460K" "$(run_ctxguard "$CTX_B")"
printf '%s\n%s\n%s\n' "$BIG" "$BOUND" "$SMALL" > "$CTX_C"
assert_no_grep "ctx · 边界后有新 assistant → 按边界后 10K 判，不报" "context 缓存读取" "$(run_ctxguard "$CTX_C")"
# 工具结果里引用过 compact_boundary 字样（本工区 grep 源文件即产生）不得误清 → 否则闸静默失灵
QUOTED='{"type":"user","message":{"role":"user","content":[{"type":"tool_result","content":"grep compact_boundary 命中 \"compact_boundary\" 一行"}]}}'
printf '%s\n%s\n' "$BIG" "$QUOTED" > "$CTX_D"
assert_grep "ctx · 旁文提及 compact_boundary 不误清（防闸静默失灵）" "context 缓存读取 460K" "$(run_ctxguard "$CTX_D")"
# 增速子句：边界后 4 条 cache_read（均 +10K/条）→ 距下一档（390K）约 1 条
CTX_E="$D/ctx-pace.jsonl"
P1='{"type":"assistant","message":{"id":"cp1","model":"deepseek-flash","usage":{"input_tokens":100,"cache_creation_input_tokens":0,"cache_read_input_tokens":350000,"output_tokens":50}},"timestamp":"2026-09-15T04:00:00.000Z"}'
P2='{"type":"assistant","message":{"id":"cp2","model":"deepseek-flash","usage":{"input_tokens":100,"cache_creation_input_tokens":0,"cache_read_input_tokens":360000,"output_tokens":50}},"timestamp":"2026-09-15T04:01:00.000Z"}'
P3='{"type":"assistant","message":{"id":"cp3","model":"deepseek-flash","usage":{"input_tokens":100,"cache_creation_input_tokens":0,"cache_read_input_tokens":370000,"output_tokens":50}},"timestamp":"2026-09-15T04:02:00.000Z"}'
P4='{"type":"assistant","message":{"id":"cp4","model":"deepseek-flash","usage":{"input_tokens":100,"cache_creation_input_tokens":0,"cache_read_input_tokens":380000,"output_tokens":50}},"timestamp":"2026-09-15T04:03:00.000Z"}'
printf '%s\n%s\n%s\n%s\n%s\n' "$P1" "$P2" "$P3" "$P4" "$PROMPT" > "$CTX_E"
OUT_CTXE=$(run_ctxguard "$CTX_E")
assert_grep "ctx · 增速子句（中位差分 10K/条）" "均 +10K/条" "$OUT_CTXE"
assert_grep "ctx · 距下一档（390K）估计 1 条" "距 390K 约 1 条" "$OUT_CTXE"
# 档位制：跨档才报、同档不刷屏。默认首档 300K、步长 10K，所以 310K→313K（同档）静默、
# 300K→310K（跨档）报——这两条锁住「越线后每轮刷屏」不再回潮。
ctx_row() {  # $1=id $2=cache_read
  printf '{"type":"assistant","message":{"id":"%s","model":"deepseek-flash","usage":{"input_tokens":100,"cache_creation_input_tokens":0,"cache_read_input_tokens":%s,"output_tokens":50}},"timestamp":"2026-09-15T04:00:00.000Z"}' "$1" "$2"
}
CTX_F="$D/ctx-same-rung.jsonl"
printf '%s\n%s\n%s\n' "$(ctx_row f1 310000)" "$(ctx_row f2 312000)" "$(ctx_row f3 313000)" > "$CTX_F"
printf '%s\n' "$PROMPT" >> "$CTX_F"
assert_no_grep "ctx · 同一档内不重复报（310K→313K 差 < 步长 10K）" "context 缓存读取" "$(run_ctxguard "$CTX_F")"
CTX_G="$D/ctx-cross-rung.jsonl"
printf '%s\n%s\n%s\n' "$(ctx_row g1 300000)" "$(ctx_row g2 305000)" "$(ctx_row g3 310000)" > "$CTX_G"
printf '%s\n' "$PROMPT" >> "$CTX_G"
assert_grep "ctx · 跨档才报（300K→310K 跨一档）" "context 缓存读取 310K" "$(run_ctxguard "$CTX_G")"
CTX_H="$D/ctx-under-start.jsonl"
printf '%s\n%s\n' "$(ctx_row h1 250000)" "$PROMPT" > "$CTX_H"
assert_no_grep "ctx · 未到首档（250K < 300K）不报" "context 缓存读取" "$(run_ctxguard "$CTX_H")"

echo ""
echo "── user-prompt-warn.sh · cost 多通道计费（去重 / 币种 / 档位 / 混合）──"
# 全部走 fixture：PMWS_COST_CONFIG 指向 $D 内配置，PMWS_CCSWITCH_DB 指向 $D 内 sqlite；
# 真配置 / 真 db 不进测试路径（测试文件随公开镜像出，fixture 名一律中性）。
COST_DB="$D/cost-fixture.db"
python3 - "$COST_DB" <<'PY'
import json, sqlite3, sys
con = sqlite3.connect(sys.argv[1])
con.execute("CREATE TABLE providers (name TEXT, app_type TEXT, is_current INTEGER, settings_config TEXT)")
con.execute("CREATE TABLE model_pricing (model_id TEXT, input_cost_per_million TEXT,"
            " output_cost_per_million TEXT, cache_read_cost_per_million TEXT,"
            " cache_creation_cost_per_million TEXT)")
def prov(name, tok, cur=0, base="https://fixture.invalid"):
    con.execute("INSERT INTO providers VALUES (?,?,?,?)", (name, "claude", cur, json.dumps(
        {"env": {"ANTHROPIC_AUTH_TOKEN": tok, "ANTHROPIC_BASE_URL": base}})))
prov("prov-ds", "tok-ds")
prov("prov-sale", "tok-sale")
prov("prov-in", "tok-in")
prov("prov-usd", "tok-usd", cur=1, base="https://usd.fixture.invalid")
con.execute("INSERT INTO model_pricing VALUES ('claude-opus-4-7','5','25','0.5','6.25')")
con.commit()
PY
COST_CFG="$D/cost-fixture.json"
cat > "$COST_CFG" <<'JSON'
{
  "ccswitch_db": "/nonexistent-cfg-db",
  "peak": {"hours": [9, 10, 11, 14, 15, 16, 17], "multiplier": 2, "models": ["deepseek-"]},
  "steps": {"cny_micro": 10000, "usd_micro": 10000},
  "channels": [
    {"id": "chn-ds", "provider": "stub-prov", "provider_names": ["prov-ds"], "legacy_base_url": ["https://legacy.fixture.invalid", "https://legacy2.fixture.invalid"],
     "currency": "CNY",
     "rates_off_peak": {"deepseek-flash": {"in": 0.80, "out": 3.20, "cache_read": 0.016},
                        "deepseek-v4-pro": {"in": 3.60, "out": 10.80, "cache_read": 0.11988},
                        "prov-other": {"in": 2.00, "out": 2.00, "cache_read": 0.0}},
     "cache_write_rate": 1.25},
    {"id": "chn-sale", "provider_names": ["prov-sale"],
     "currency": "CNY",
     "rates_off_peak": {"deepseek-flash": {"in": 0.50, "out": 2.00, "cache_read": 0.010},
                        "deepseek-v4-flash": {"in": 0.50, "out": 2.00, "cache_read": 0.010}},
     "cache_write_rate": "cache_read"},
    {"id": "chn-in", "provider_names": ["prov-in"],
     "currency": "CNY",
     "rates_off_peak": {"deepseek-flash": {"in": 0.80, "out": 3.20, "cache_read": 0.016}},
     "cache_write_rate": "in"},
    {"id": "chn-usd", "provider_names": ["prov-usd"],
     "currency": "USD", "models": ["claude"], "pricing_source": "ccswitch_model_pricing"}
  ]
}
JSON
CST="$D/cost-state"
# 每条 case 前清步进状态目录：同 session-id(global) 复用状态会让后续 case 不触发
run_cost() {  # $1=transcript $2=token $3=base_url，其余=额外 ENV=VAL（覆盖默认桩）
  local tr="$1" tok="$2" url="$3"; shift 3
  rm -rf "$CST"; mkdir -p "$CST"
  # 余额段默认换成不产出任何东西的桩：整份 hook 测试永不触网（真跑会去打中转站，
  # 而且要 .env 里的令牌）。测余额的用例用 HOOK_BALANCE_CMD 注入假命令。
  printf '{"prompt":"继续","transcript_path":"%s"}' "$tr" \
    | env -u ANTHROPIC_API_KEY -u PMWS_COST_STEP_MICRO -u PMWS_COST_STEP_USD_MICRO -u PMWS_CONTEXT_STEP_START -u PMWS_CONTEXT_STEP \
        TMPDIR="$CST" PMWS_COST_CONFIG="$COST_CFG" PMWS_CCSWITCH_DB="$COST_DB" \
        ANTHROPIC_AUTH_TOKEN="$tok" ANTHROPIC_BASE_URL="$url" \
        WARN_BALANCE_CMD="${HOOK_BALANCE_CMD-false}" "$@" \
        bash .claude/hooks/user-prompt-warn.sh 2>/dev/null
}
# 统一用北京 12:00（工作日午休，非高峰）：UTC 04:00
TS_OFF='"timestamp":"2026-09-15T04:00:00.000Z"'
DUP_MSG="{\"type\":\"assistant\",\"message\":{\"id\":\"m1\",\"model\":\"deepseek-flash\",\"usage\":{\"input_tokens\":1000000,\"cache_creation_input_tokens\":0,\"cache_read_input_tokens\":0,\"output_tokens\":0}},$TS_OFF}"

# 1) 去重：同一 message.id 落 3 行 → 只计 1 次（修前 ¥2.40 虚高）
COST_DUP="$D/cost-dup.jsonl"
printf '%s\n%s\n%s\n' "$DUP_MSG" "$DUP_MSG" "$DUP_MSG" > "$COST_DUP"
OUT_DUP=$(run_cost "$COST_DUP" "tok-ds" "https://fixture.invalid")
assert_grep "cost · 同 id 重复行去重（1×¥0.80）" "¥0.80" "$OUT_DUP"
assert_no_grep "cost · 去重后不得出现 3 倍值" "¥2.4" "$OUT_DUP"

# 2) 档位：token 命中 5 折档 → ¥0.50
OUT_SALE=$(run_cost "$COST_DUP" "tok-sale" "https://fixture.invalid")
assert_grep "cost · 5 折档 key 走 0.50 表" "¥0.50" "$OUT_SALE"

# 3) USD 通道：claude 模型按 model_pricing（含缓存写）= 0.2M×5 + 1K×25 + 0.1M×0.5 + 10K×6.25 每 1M → $1.1375
CLAUDE_MSG="{\"type\":\"assistant\",\"message\":{\"id\":\"m2\",\"model\":\"claude-opus-4-7\",\"usage\":{\"input_tokens\":200000,\"cache_creation_input_tokens\":10000,\"cache_read_input_tokens\":100000,\"output_tokens\":1000}},$TS_OFF}"
COST_USD="$D/cost-usd.jsonl"
printf '%s\n' "$CLAUDE_MSG" > "$COST_USD"
OUT_USD=$(run_cost "$COST_USD" "tok-usd" "https://usd.fixture.invalid")
assert_grep "cost · USD 通道金额含缓存写" "1.1375" "$OUT_USD"
assert_grep "cost · USD 段带缓存写分列" "缓存写" "$OUT_USD"

# 4) 混合 session：deepseek 段 ¥ + claude 段 $ 分币种合计
COST_MIX="$D/cost-mix.jsonl"
printf '%s\n%s\n' "$DUP_MSG" "$CLAUDE_MSG" > "$COST_MIX"
OUT_MIX=$(run_cost "$COST_MIX" "tok-ds" "https://fixture.invalid")
assert_grep "cost · 混合 session ¥ 段" "¥0.80" "$OUT_MIX"
assert_grep "cost · 混合 session \$ 段" "1.1375" "$OUT_MIX"

# 5) legacy 兜底：token 未登记 + base_url 命中配置 legacy → 默认 CNY 档
OUT_LEG=$(run_cost "$COST_DUP" "tok-unregistered" "https://legacy.fixture.invalid")
assert_grep "cost · legacy base_url 兜底走默认档（¥0.80）" "¥0.80" "$OUT_LEG"
# 5b) legacy 多值：第二个端点同样兜底（出差换端点场景）
OUT_LEG2=$(run_cost "$COST_DUP" "tok-unregistered" "https://legacy2.fixture.invalid")
assert_grep "cost · legacy 多值第二端点兜底（¥0.80）" "¥0.80" "$OUT_LEG2"

# 6) 不可计价模型（glm）→ 不计费、无输出
GLM_MSG="{\"type\":\"assistant\",\"message\":{\"id\":\"m3\",\"model\":\"glm-5.3\",\"usage\":{\"input_tokens\":1000000,\"cache_creation_input_tokens\":0,\"cache_read_input_tokens\":0,\"output_tokens\":0}},$TS_OFF}"
COST_GLM="$D/cost-glm.jsonl"
printf '%s\n' "$GLM_MSG" > "$COST_GLM"
OUT_GLM=$(run_cost "$COST_GLM" "tok-ds" "https://fixture.invalid")
assert_no_grep "cost · 未计价模型不产生金额" "累计" "$OUT_GLM"

# 7) 通道内多模型价目：deepseek-v4-pro 按表计（¥3.60，非 flash 价）
V4P_MSG="{\"type\":\"assistant\",\"message\":{\"id\":\"m4\",\"model\":\"deepseek-v4-pro\",\"usage\":{\"input_tokens\":1000000,\"cache_creation_input_tokens\":0,\"cache_read_input_tokens\":0,\"output_tokens\":0}},$TS_OFF}"
COST_V4P="$D/cost-v4p.jsonl"
printf '%s\n' "$V4P_MSG" > "$COST_V4P"
assert_grep "cost · v4-pro 走通道内价目表（¥3.60）" "¥3.60" "$(run_cost "$COST_V4P" "tok-ds" "https://fixture.invalid")"

# 8) 未列模型不计：v4-flash 在 ds 档无价目 → 无输出；sale 档有 → ¥0.50
V4F_MSG="{\"type\":\"assistant\",\"message\":{\"id\":\"m5\",\"model\":\"deepseek-v4-flash\",\"usage\":{\"input_tokens\":1000000,\"cache_creation_input_tokens\":0,\"cache_read_input_tokens\":0,\"output_tokens\":0}},$TS_OFF}"
COST_V4F="$D/cost-v4f.jsonl"
printf '%s\n' "$V4F_MSG" > "$COST_V4F"
assert_no_grep "cost · ds 档未列模型不计（无输出）" "累计" "$(run_cost "$COST_V4F" "tok-ds" "https://fixture.invalid")"
assert_grep "cost · sale 档同模型正常计（¥0.50）" "¥0.50" "$(run_cost "$COST_V4F" "tok-sale" "https://fixture.invalid")"

# 9) peak.models 前缀名单：名单内 ×2、名单外原价（工作日 10:00 高峰时刻）
TS_PEAK='"timestamp":"2026-09-15T02:00:00.000Z"'
PK_F="$D/cost-pk-flash.jsonl"; PK_O="$D/cost-pk-other.jsonl"
printf '%s\n' "{\"type\":\"assistant\",\"message\":{\"id\":\"m6\",\"model\":\"deepseek-flash\",\"usage\":{\"input_tokens\":1000000,\"cache_creation_input_tokens\":0,\"cache_read_input_tokens\":0,\"output_tokens\":0}},$TS_PEAK}" > "$PK_F"
printf '%s\n' "{\"type\":\"assistant\",\"message\":{\"id\":\"m7\",\"model\":\"prov-other-x1\",\"usage\":{\"input_tokens\":1000000,\"cache_creation_input_tokens\":0,\"cache_read_input_tokens\":0,\"output_tokens\":0}},$TS_PEAK}" > "$PK_O"
assert_grep "cost · 名单内 deepseek 高峰 ×2（¥1.60）" "¥1.60" "$(run_cost "$PK_F" "tok-ds" "https://fixture.invalid")"
assert_grep "cost · 名单外模型不吃 ×2（¥2.00 原价）" "¥2.00" "$(run_cost "$PK_O" "tok-ds" "https://fixture.invalid")"

# 10) 缓存写倍率三态：数字 = 相对输入价的倍数，'in' / 'cache_read' 两个别名
# 站点按 1.25 × 输入价收缓存写；数字被当成 1.0（旧口径）会少算 20%，而配置里写数字是主用法。
CW_MSG="{\"type\":\"assistant\",\"message\":{\"id\":\"m8\",\"model\":\"deepseek-flash\",\"usage\":{\"input_tokens\":0,\"cache_creation_input_tokens\":1000000,\"cache_read_input_tokens\":0,\"output_tokens\":0}},$TS_OFF}"
COST_CW="$D/cost-cw.jsonl"
printf '%s\n' "$CW_MSG" > "$COST_CW"
OUT_CW=$(run_cost "$COST_CW" "tok-ds" "https://fixture.invalid")
assert_grep "cost · 缓存写按 1.25 × 输入价（1M → ¥1.00）" "¥1.00" "$OUT_CW"
assert_no_grep "cost · 数字倍率不得被当成 1.0（会少算成 ¥0.80）" "¥0.80" "$OUT_CW"
assert_grep "cost · cache_write_rate='cache_read' → 按缓存读价（¥0.01）" "¥0.01" "$(run_cost "$COST_CW" "tok-sale" "https://fixture.invalid")"
assert_grep "cost · cache_write_rate='in' → 按输入价（¥0.80）" "¥0.80" "$(run_cost "$COST_CW" "tok-in" "https://fixture.invalid")"

# 11) 高峰的时段条件含周几：同一天同一时刻，周末不 ×2
# 2026-09-15 是周二（上面两条断言高峰生效），09-19 是周六
TS_SAT='"timestamp":"2026-09-19T02:00:00.000Z"'
PK_SAT="$D/cost-pk-sat.jsonl"
printf '%s\n' "{\"type\":\"assistant\",\"message\":{\"id\":\"m9\",\"model\":\"deepseek-flash\",\"usage\":{\"input_tokens\":1000000,\"cache_creation_input_tokens\":0,\"cache_read_input_tokens\":0,\"output_tokens\":0}},$TS_SAT}" > "$PK_SAT"
OUT_SAT=$(run_cost "$PK_SAT" "tok-ds" "https://fixture.invalid")
assert_grep "cost · 周末同一时刻按原价（¥0.80）" "¥0.80" "$OUT_SAT"
assert_no_grep "cost · 周末不得按高峰计（¥1.60）" "¥1.60" "$OUT_SAT"

# 11b) 放假日表：峰谷判的是「交易所日历」——放假日落在工作日 → 原价；
#      表只排除命中的那一天，不排除整周；表未覆盖的年份退回「只按周几」并自报缺口；
#      表声明了却读不到同样自报缺口，不静默按「没有节假日」判。
HOL_JSON="$D/hol-fixture.json"
printf '%s' '{"off_days": {"2026": ["2026-09-25"]}}' > "$HOL_JSON"
HOL_CFG="$D/cost-hol.json"
python3 - "$HOL_CFG" "$COST_CFG" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[2]))
cfg["peak"]["holidays_file"] = "hol-fixture.json"
cfg["peak"]["holidays_mode"] = "exclude"
json.dump(cfg, open(sys.argv[1], "w"), ensure_ascii=False)
PY
TS_HOL='"timestamp":"2026-09-25T02:00:00.000Z"'
HOL_F="$D/cost-hol-day.jsonl"
printf '%s\n' "{\"type\":\"assistant\",\"message\":{\"id\":\"h1\",\"model\":\"deepseek-flash\",\"usage\":{\"input_tokens\":1000000,\"cache_creation_input_tokens\":0,\"cache_read_input_tokens\":0,\"output_tokens\":0}},$TS_HOL}" > "$HOL_F"
OUT_HOL=$(run_cost "$HOL_F" "tok-ds" "https://fixture.invalid" PMWS_COST_CONFIG="$HOL_CFG")
assert_grep "cost · 放假日高峰窗按原价（¥0.80）" "¥0.80" "$OUT_HOL"
assert_no_grep "cost · 放假日不得按高峰计（¥1.60）" "¥1.60" "$OUT_HOL"
assert_grep "cost · 同配置下非放假日工作日仍 ×2（表只排除命中日）" "¥1.60" \
  "$(run_cost "$PK_F" "tok-ds" "https://fixture.invalid" PMWS_COST_CONFIG="$HOL_CFG")"
# 调休补班的周六日：国务院日历里上班、交易所日历里休息 → 仍原价（表里没有它，靠周几就排除）
assert_grep "cost · 补班周末（表未收录）仍按原价" "¥0.80" \
  "$(run_cost "$PK_SAT" "tok-ds" "https://fixture.invalid" PMWS_COST_CONFIG="$HOL_CFG")"
# 表未覆盖的年份：判定退回「只按周几」，且必须自报缺口
TS_27='"timestamp":"2027-01-05T02:00:00.000Z"'
HOL_27="$D/cost-hol-2027.jsonl"
printf '%s\n' "{\"type\":\"assistant\",\"message\":{\"id\":\"h2\",\"model\":\"deepseek-flash\",\"usage\":{\"input_tokens\":1000000,\"cache_creation_input_tokens\":0,\"cache_read_input_tokens\":0,\"output_tokens\":0}},$TS_27}" > "$HOL_27"
OUT_HOL27=$(run_cost "$HOL_27" "tok-ds" "https://fixture.invalid" PMWS_COST_CONFIG="$HOL_CFG")
assert_grep "cost · 表未覆盖年份按周一~周五判（¥1.60）" "¥1.60" "$OUT_HOL27"
assert_grep "cost · 表未覆盖年份自报缺口" "节假日表未覆盖 2027" "$OUT_HOL27"
# 表声明了但读不到：不静默按「没有节假日」，同样自报
BAD_CFG="$D/cost-hol-bad.json"
python3 - "$BAD_CFG" "$COST_CFG" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[2]))
cfg["peak"]["holidays_file"] = "no-such-hol-file.json"
cfg["peak"]["holidays_mode"] = "exclude"
json.dump(cfg, open(sys.argv[1], "w"), ensure_ascii=False)
PY
OUT_HOLBAD=$(run_cost "$PK_F" "tok-ds" "https://fixture.invalid" PMWS_COST_CONFIG="$BAD_CFG")
assert_grep "cost · 表读不到按周一~周五判（¥1.60）" "¥1.60" "$OUT_HOLBAD"
assert_grep "cost · 表读不到自报缺口（不静默）" "节假日表读不到" "$OUT_HOLBAD"
# 未声明 holidays_file → 完全不查表，也不出缺口标注（无配置不该刷噪音）
OUT_NOHOL=$(run_cost "$PK_F" "tok-ds" "https://fixture.invalid")
assert_no_grep "cost · 未声明节假日表 → 不出缺口标注" "节假日表" "$OUT_NOHOL"

# 12) 高峰文案门：本 session 没有名单内模型时，不标「当前高峰时段（2 倍价）」
# now_peak 看的是此刻 + 本 session 实际计价的模型，把高峰窗对齐到跑测试的这一刻才能确定性断言
PEAK_NOW_CFG="$D/cost-peak-now.json"
python3 - "$PEAK_NOW_CFG" "$COST_CFG" <<'PY'
import datetime, json, sys
cfg = json.load(open(sys.argv[2]))
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
cfg["peak"] = {"enabled": True, "hours": [now.hour], "weekdays": [now.weekday()],
               "multiplier": 2, "models": ["deepseek-"]}
json.dump(cfg, open(sys.argv[1], "w"), ensure_ascii=False)
PY
assert_grep "cost · 名单内模型 + 此刻在高峰窗 → 标高峰" "当前高峰时段" \
  "$(run_cost "$PK_F" "tok-ds" "https://fixture.invalid" PMWS_COST_CONFIG="$PEAK_NOW_CFG")"
OUT_USD_PK=$(run_cost "$COST_USD" "tok-usd" "https://usd.fixture.invalid" PMWS_COST_CONFIG="$PEAK_NOW_CFG")
assert_grep "cost · 同一时刻 USD 段照报金额" "1.1375" "$OUT_USD_PK"
assert_no_grep "cost · claude 不在高峰名单里 → 不标 2 倍价（会误导改时段）" "当前高峰时段" "$OUT_USD_PK"

# 13) 余额段：只在真要报金额时取一次；取到的内容过了正则才准进提示
# 默认桩（run_cost 里的 WARN_BALANCE_CMD=false）保证上面所有 case 都不触网
OUT_BAL=$(HOOK_BALANCE_CMD='echo "104.47 0"' run_cost "$COST_DUP" "tok-ds" "https://fixture.invalid")
assert_grep "余额 · 正常 → 显示余额" "余额 ¥104.47" "$OUT_BAL"
assert_no_grep "余额 · 正常 → 不标偏低" "偏低" "$OUT_BAL"
OUT_BAL_LOW=$(HOOK_BALANCE_CMD='echo "28.10 1"' run_cost "$COST_DUP" "tok-ds" "https://fixture.invalid")
assert_grep "余额 · 偏低 → 显示金额" "余额 ¥28.10" "$OUT_BAL_LOW"
assert_grep "余额 · 偏低 → 带警示" "偏低" "$OUT_BAL_LOW"
# 余额内容不合契约（1.2.3 既不是金额也不是 low）→ 整段丢弃，不能污染 stdout
OUT_BAL_BAD=$(HOOK_BALANCE_CMD='echo "1.2.3 1"' run_cost "$COST_DUP" "tok-ds" "https://fixture.invalid")
assert_no_grep "余额 · 脏值 → 整段丢弃" "余额" "$OUT_BAL_BAD"
if printf '%s' "$OUT_BAL_BAD" | jq -e '.systemMessage' >/dev/null 2>&1; then
  echo "  [OK]   余额 · 脏值不影响 stdout 一行 JSON 契约"
  PASS=$((PASS + 1))
else
  echo "  [FAIL] 余额 · 脏值破坏了 stdout：$OUT_BAL_BAD"
  FAIL=$((FAIL + 1))
fi
OUT_BAL_OFF=$(WARN_BALANCE=0 HOOK_BALANCE_CMD='echo "104.47 0"' run_cost "$COST_DUP" "tok-ds" "https://fixture.invalid")
assert_no_grep "余额 · WARN_BALANCE=0 → 关掉本段" "余额" "$OUT_BAL_OFF"
assert_grep "余额 · 关掉不影响金额" "¥0.80" "$OUT_BAL_OFF"
# 通道没写 provider（chn-sale）→ 取不到余额，即使注入的桩有值也不显示
assert_no_grep "余额 · 通道无 provider → 不取也不显示" "余额" \
  "$(HOOK_BALANCE_CMD='echo "999.99 0"' run_cost "$COST_DUP" "tok-sale" "https://fixture.invalid")"
# 只命中 context、不报金额时不该去取余额（热路径上不付这个成本）
# 档位抬到 ¥100：本 fixture 的 460K 缓存读在高峰价下会自己越过 ¥0.01 档，得先让它不报金额
OUT_BAL_CTX=$(HOOK_BALANCE_CMD='echo "999.99 0"' run_cost "$CTX_B" "tok-ds" "https://fixture.invalid" \
  PMWS_COST_STEP_MICRO=100000000)
assert_grep "余额 · 只报 context 时 context 照报" "context" "$OUT_BAL_CTX"
assert_no_grep "余额 · 只报 context → 不取也不显示余额" "余额" "$OUT_BAL_CTX"

# 14) 口径标注：推定档（价是猜的）与未计价条数，都得自己说出来
assert_grep "cost · legacy 兜底标「key 未登记」" "key 未登记" "$OUT_LEG"
COST_SKIP="$D/cost-skip.jsonl"
printf '%s\n%s\n' "$DUP_MSG" "$GLM_MSG" > "$COST_SKIP"
assert_grep "cost · 未计价条目如实报数（不冒充全量）" "另有 1 条未计价" "$(run_cost "$COST_SKIP" "tok-ds" "https://fixture.invalid")"

echo ""
echo "── required-read-gate · 缺席 guide 降级（F3：gitignored L2 不死锁）──"
# 修前：gitignored 的 hub L2 公司规范在全新 clone 缺席 → 无满足路径仍 block（死锁，只能 SKIP env 绕）
HB="$D/hubgate"
mkdir -p "$HB/.claude/runbooks" "$HB/hub/confluence-cli"
printf 'x\n' > "$HB/.claude/runbooks/ai-platform-specs.md"
printf 'x\n' > "$HB/hub/AUTHORING-RULES.md"
# 故意不建 hub/AI中台-规范及帮助文档/（模拟全新 clone：L2 规范 gitignored 缺席）
T_HUB_HIT="$D/t_hub_hit.jsonl"
make_hit "$T_HUB_HIT" "$HB/.claude/runbooks/ai-platform-specs.md" "$HB/hub/AUTHORING-RULES.md"
test_hub_gate() {  # $1=transcript → pg_skill_load 退出码
  ( source .claude/hooks/lib/log.sh
    source .claude/hooks/lib/input.sh
    source .claude/hooks/lib/guards.sh
    source .claude/hooks/lib/pre-writeedit-guards.sh
    PROJECT_DIR="$HB"; HOOK_FILE_PATH="$HB/hub/confluence-cli/aihub_tool.py"; HOOK_TRANSCRIPT="$1"
    pg_skill_load )
}
test_hub_gate "$T_HUB_HIT" >/dev/null 2>&1
assert_exit "hub · L2 缺席 + L1/L3 已读 → 降级 pass（F3 修前死锁）" 0 $?
# 对照：L2 存在但没读 → 仍 block（降级不削弱真·必读）
mkdir -p "$HB/hub/AI中台-规范及帮助文档"
printf 'x\n' > "$HB/hub/AI中台-规范及帮助文档/AI中台-MCP编写规范.md"
test_hub_gate "$T_HUB_HIT" >/dev/null 2>&1
assert_exit "hub · L2 存在但没读 → 仍 block" 2 $?

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
echo "═══ find_recent_deliverables 契约（挂着 5 条检查链路，此前零覆盖）═══"

# 该函数的调用方靠三件事活着：真·空串短路、绝对路径、sort -u 顺序。
# 本次把「每文件 fork 一个 stat」换成 bash 内建 -nt，语义必须逐条不变。
fr_recent() {  # $1=project dir, 其余=函数参数
  local proj="$1"; shift
  ( export CLAUDE_PROJECT_DIR="$proj"; source "$ROOT/.claude/hooks/lib/recent.sh"; find_recent_deliverables "$@" )
}

FR=$(mktemp -d)
mkdir -p "$FR"/projects/demo/deliverables/prd-demo-scenes "$FR"/projects/demo/deliverables/1.0 "$FR"/deliverables
: > "$FR/projects/demo/deliverables/fresh.md"
: > "$FR/projects/demo/deliverables/1.0/proto-demo.html"
: > "$FR/projects/demo/deliverables/prd-demo-scenes/prd-demo-scenes.md"
: > "$FR/deliverables/root.md"
FR_OLD=$(date -v-2d +%Y%m%d%H%M.%S 2>/dev/null || date -d '-2 days' +%Y%m%d%H%M.%S)
: > "$FR/projects/demo/deliverables/stale.md"
touch -t "$FR_OLD" "$FR/projects/demo/deliverables/stale.md"

FR_HIT=$(fr_recent "$FR" 3600 '*.md' '*.html')
assert_grep "recent · 窗口内文件命中" "fresh.md" "$FR_HIT"
assert_no_grep "recent · 窗口外文件不命中" "stale.md" "$FR_HIT"
assert_grep "recent · 输出绝对路径（下游 sed 剥前缀靠它）" "$FR/" "$FR_HIT"
assert_grep "recent · 递归进 {季度}/{版本} 子目录" "proto-demo.html" "$FR_HIT"
assert_no_grep "recent · --not-path 排除 scenes（默认调用形态）" "prd-demo-scenes.md" \
  "$(fr_recent "$FR" 3600 --not-path '*-scenes/*' '*.md')"
assert_no_grep "recent · 根 deliverables/ 默认不扫" "root.md" "$FR_HIT"
assert_grep "recent · --include-root-deliverables 才扫根 deliverables/" "root.md" \
  "$(fr_recent "$FR" 3600 --include-root-deliverables '*.md')"

# 空值契约：必须是 0 字节的真空串。多一个换行会让 5 个调用点的 [ -z ] 短路失效，
# 变成「拿空文件列表去跑检查器」= 白付一次 fork + 空报告块。
FR_STALE=$(mktemp -d)
mkdir -p "$FR_STALE/projects/demo/deliverables"
: > "$FR_STALE/projects/demo/deliverables/old.md"
touch -t "$FR_OLD" "$FR_STALE/projects/demo/deliverables/old.md"
assert_eq "recent · 无命中返回真·空串（0 字节）" "0" "$(fr_recent "$FR_STALE" 60 '*.md' | wc -c | tr -d ' ')"
assert_eq "recent · 宽窗口下同一棵树有命中" "1" "$(fr_recent "$FR_STALE" 604800 '*.md' | grep -c .)"
assert_eq "recent · 无 glob 参数直接返回空" "0" "$(fr_recent "$FR" 60 | wc -c | tr -d ' ')"
assert_eq "recent · 项目根不存在返回空" "0" "$(fr_recent /nonexistent-xyz 60 '*.md' | wc -c | tr -d ' ')"

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ cjk --strict-then-fix-spaces（写盘热路径双跑合一）═══"

CJKD=$(mktemp -d)
# 干净但有空格可补 → 补空格、exit 0
printf '用GitHub世界做20TB的活\n' > "$CJKD/sp.md"
python3 "$CJK_CHK" "$CJKD/sp.md" --strict-then-fix-spaces >/dev/null 2>&1
assert_exit "cjk-merge · 无可改标点时 exit 0" 0 $?
assert_grep "cjk-merge · 仍会静默补空格" "用 GitHub 世界" "$(cat "$CJKD/sp.md")"
# 幂等：再跑一次不得再改
CJK_A=$(md5 -q "$CJKD/sp.md" 2>/dev/null || md5sum "$CJKD/sp.md" | cut -d' ' -f1)
python3 "$CJK_CHK" "$CJKD/sp.md" --strict-then-fix-spaces >/dev/null 2>&1
CJK_B=$(md5 -q "$CJKD/sp.md" 2>/dev/null || md5sum "$CJKD/sp.md" | cut -d' ' -f1)
assert_eq "cjk-merge · 幂等（二次运行不再改盘）" "$CJK_A" "$CJK_B"
# 脏文件不碰：strict 命中 → exit 2 且一字不改（补空格必须在判定之后）
printf '中文,半角 和English\n' > "$CJKD/dirty.md"
CJK_DIRTY_BEFORE=$(cat "$CJKD/dirty.md")
python3 "$CJK_CHK" "$CJKD/dirty.md" --strict-then-fix-spaces >/dev/null 2>&1
assert_exit "cjk-merge · strict 命中 exit 2" 2 $?
assert_eq "cjk-merge · strict 命中时文件一字不改（脏文件不碰）" "$CJK_DIRTY_BEFORE" "$(cat "$CJKD/dirty.md")"
# 干净路径必须静默：hook 靠「无输出 + exit 0」判过关
assert_eq "cjk-merge · 干净路径无 stderr 输出" "0" \
  "$(python3 "$CJK_CHK" "$CJKD/sp.md" --strict-then-fix-spaces 2>&1 >/dev/null | wc -c | tr -d ' ')"
# 原有 flag 不受影响
printf '用GitHub世界\n' > "$CJKD/legacy.md"
python3 "$CJK_CHK" "$CJKD/legacy.md" --fix-spaces >/dev/null 2>&1
assert_grep "cjk-merge · 原 --fix-spaces 仍可用" "用 GitHub 世界" "$(cat "$CJKD/legacy.md")"

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ warn 通道（exit 0 时 stderr 模型看不到 → 必须走 additionalContext）═══"

# 背景：PostToolUse 的 hook 在 exit 0 时，写到 stderr 的内容只进 transcript 的 hook_success
# 记录（供界面展示），不进模型 context —— 模型看不到。warn 类提醒必须经
# hookSpecificOutput.additionalContext 才能送达。下面几条锁住该契约，防被改回 stderr。
# TMPDIR 指向一次性目录：dedup 缓存随之隔离，warn 门必触发，测试不受 600s TTL 影响。
run_post_json() {   # $1=file  $2=TMPDIR
  echo "{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"$1\"}}" \
    | TMPDIR="$2" bash .claude/hooks/post-writeedit-dispatch.sh 2>/dev/null
}

CH_WARN_DIR=$(mktemp -d)
CH_WARN=$(run_post_json "$ROOT/scripts/check_cjk_punct.py" "$CH_WARN_DIR")
assert_grep "warn-channel · 命中 warn 时 stdout 是 hookSpecificOutput JSON" "hookSpecificOutput" "$CH_WARN"
assert_grep "warn-channel · hookEventName 必须为 PostToolUse" '"hookEventName":"PostToolUse"' "$CH_WARN"
assert_grep "warn-channel · additionalContext 带上门名（可溯源）" "test-reminder-gate" "$CH_WARN"
# 放顶层会被静默忽略 —— 发了等于没发，这条专防那种改写
assert_eq "warn-channel · additionalContext 嵌在 hookSpecificOutput 内（非顶层）" "1" \
  "$(printf '%s' "$CH_WARN" | jq -r 'if (.hookSpecificOutput.additionalContext // "") != "" and (.additionalContext // "") == "" then 1 else 0 end' 2>/dev/null)"

CH_CLEAN_DIR=$(mktemp -d)
assert_eq "warn-channel · 无 warn 时 stdout 为空（多余输出会让整条被丢）" "0" \
  "$(run_post_json "$ROOT/LEARNED.md" "$CH_CLEAN_DIR" | wc -c | tr -d ' ')"
# block 路径走 exit 2，stderr 本就可达模型，不得再叠一份 additionalContext
# 样例是仓内既有脏产物（strict 命中）；它若被修好，本断言会失败——那正是该有人看一眼的信号
CH_BLOCK_DIR=$(mktemp -d)
CH_BLOCK_FILE="$ROOT/projects/livestream/deliverables/2026Q3/2.3/proto-livestream-2.3-app.html"
CH_BLOCK=$(run_post_json "$CH_BLOCK_FILE" "$CH_BLOCK_DIR")
assert_eq "warn-channel · block 路径不重复注入（stdout 为空）" "0" \
  "$(printf '%s' "$CH_BLOCK" | wc -c | tr -d ' ')"

# Pre 侧：Bash 路径的 warn 门（risky-op）也要发射，且 hookEventName 不能写错
CH_BASH_DIR=$(mktemp -d)
CH_BASH=$(printf '{"tool_name":"Bash","tool_input":{"command":"python3 shot.py --headless=False"}}' \
  | TMPDIR="$CH_BASH_DIR" bash .claude/hooks/pre-bash-guard.sh 2>/dev/null)
assert_grep "warn-channel · PreToolUse 侧也发射 JSON" "hookSpecificOutput" "$CH_BASH"
assert_grep "warn-channel · PreToolUse 的 hookEventName 正确（非 PostToolUse）" '"hookEventName":"PreToolUse"' "$CH_BASH"
assert_grep "warn-channel · PreToolUse 说明带上门名" "risky-op" "$CH_BASH"
# Pre 侧用 EXIT trap 兜多出口：exit 2（阻断）时不得再叠一份 additionalContext
CH_PREBLOCK=$(printf '{"tool_name":"Bash","tool_input":{"command":"git push https://github.com/x/y.git main"}}' \
  | TMPDIR="$(mktemp -d)" bash .claude/hooks/pre-bash-guard.sh 2>/dev/null)
assert_eq "warn-channel · PreToolUse block 路径不重复注入（stdout 为空）" "0" \
  "$(printf '%s' "$CH_PREBLOCK" | wc -c | tr -d ' ')"

# 发射器本体：无内容时不得输出任何东西（多余 stdout 会让整条 JSON 校验失败被丢）
NOTES_LIB=".claude/hooks/lib/notes.sh"
assert_eq "warn-channel · note_emit 无内容时不输出" "0" \
  "$(bash -c "source $NOTES_LIB; note_emit PostToolUse" | wc -c | tr -d ' ')"
assert_eq "warn-channel · note_emit 有内容时输出一行 JSON" "1" \
  "$(bash -c "source $NOTES_LIB; note_add '测试'; note_emit PostToolUse" | grep -c .)"

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══ block 类 gate 骨架（_pc_strict_block · 4 个 wrapper 的共享模板）═══"
# 沙箱 + stub checker 驾驭 rc 分支：锁住 路径判定 → 排除 → SKIP 门 → checker 存在性
# → rc 判定 → _PC_BLOCKED 整条骨架。改模板或 wrapper 时这组断言即回归网。
PCSB="$D/pcsb"
pcsb_stub() {  # $1=相对路径 $2=退出码 $3=输出
  mkdir -p "$PCSB/$(dirname "$1")"
  printf 'import sys\nprint(%s)\nsys.exit(%s)\n' "\"$3\"" "$2" > "$PCSB/$1"
}
pcsb_run() {  # $1=函数名 $2=相对文件路径(空=空 HOOK_FILE_PATH) $3=SKIP env 名或空 → _PC_BLOCKED
  ( source .claude/hooks/lib/log.sh; source .claude/hooks/lib/guards.sh
    source .claude/hooks/lib/runner.sh; source .claude/hooks/lib/notes.sh
    source .claude/hooks/lib/post-checks.sh
    PROJECT_DIR="$PCSB"; HOOK_FILE_PATH="${2:+$PCSB/$2}"; _PC_BLOCKED=""
    [ -n "$3" ] && export "$3=1"
    "$1" >/dev/null 2>&1
    printf '%s' "${_PC_BLOCKED:-0}" )
}
pcsb_err() {  # 同 pcsb_run 参数 → stderr 前 3 行（验四段式标题行；崩溃时 stderr 非空，可与「真放行」区分）
  ( source .claude/hooks/lib/log.sh; source .claude/hooks/lib/guards.sh
    source .claude/hooks/lib/runner.sh; source .claude/hooks/lib/notes.sh
    source .claude/hooks/lib/post-checks.sh
    PROJECT_DIR="$PCSB"; HOOK_FILE_PATH="${2:+$PCSB/$2}"
    [ -n "$3" ] && export "$3=1"
    "$1" 2>&1 >/dev/null | head -3 )
}
PHTML="projects/x/deliverables/proto-x.html"
IHTML="projects/x/deliverables/imap-x.html"
PYSRC="projects/x/scripts/proto_v1/scenes_a.py"
mkdir -p "$PCSB/projects/x/deliverables" "$PCSB/projects/x/scripts/proto_v1"
: > "$PCSB/$PHTML"; : > "$PCSB/$IHTML"; : > "$PCSB/$PYSRC"

pcsb_stub ".claude/skills/prototype/scripts/check_page_fns_shell.py" 1 "hit"
assert_eq "shell-gate · rc=1 → block" "1" "$(pcsb_run pc_prototype_source "$PYSRC" "")"
pcsb_stub ".claude/skills/prototype/scripts/check_page_fns_shell.py" 0 "ok"
assert_eq "shell-gate · rc=0 → 放行" "0" "$(pcsb_run pc_prototype_source "$PYSRC" "")"
pcsb_stub ".claude/skills/prototype/scripts/check_page_fns_shell.py" 1 "hit"
assert_eq "shell-gate · SKIP env → 放行" "0" "$(pcsb_run pc_prototype_source "$PYSRC" SKIP_PROTOTYPE_SHELL_GATE)"
assert_eq "shell-gate · 路径不匹配 → 不触发" "0" "$(pcsb_run pc_prototype_source "$PHTML" "")"
assert_eq "shell-gate · 空 FILE_PATH → 放行" "0" "$(pcsb_run pc_prototype_source "" "")"

pcsb_stub ".claude/skills/prototype/scripts/check_proto_split.py" 1 "hit"
assert_eq "proto-split · rc=1 → block" "1" "$(pcsb_run pc_prototype_split "$PHTML" "")"
pcsb_stub ".claude/skills/prototype/scripts/check_proto_split.py" 0 "ok"
assert_eq "proto-split · rc=0 → 放行" "0" "$(pcsb_run pc_prototype_split "$PHTML" "")"
pcsb_stub ".claude/skills/prototype/scripts/check_proto_split.py" 1 "hit"
assert_eq "proto-split · SKIP env → 放行" "0" "$(pcsb_run pc_prototype_split "$PHTML" SKIP_PROTOTYPE_SPLIT_GATE)"
assert_eq "proto-split · imap 路径不匹配 → 不触发" "0" "$(pcsb_run pc_prototype_split "$IHTML" "")"

pcsb_stub ".claude/skills/interaction-map/scripts/check_imap_split.py" 1 "hit"
assert_eq "imap-split · rc=1 → block" "1" "$(pcsb_run pc_imap_split "$IHTML" "")"
pcsb_stub ".claude/skills/interaction-map/scripts/check_imap_split.py" 0 "ok"
assert_eq "imap-split · rc=0 → 放行" "0" "$(pcsb_run pc_imap_split "$IHTML" "")"
pcsb_stub ".claude/skills/interaction-map/scripts/check_imap_split.py" 1 "hit"
assert_eq "imap-split · SKIP env → 放行" "0" "$(pcsb_run pc_imap_split "$IHTML" SKIP_IMAP_SPLIT_GATE)"
assert_eq "imap-split · proto 路径不匹配 → 不触发" "0" "$(pcsb_run pc_imap_split "$PHTML" "")"

# ui-annotation 的 rc 判定是 eq2（三态 checker），与上面三个 ne0 不同 —— 专项锁住
pcsb_stub "scripts/check_ui_annotation.py" 2 "hit"
assert_eq "ui-annotation · rc=2 → block" "1" "$(pcsb_run pc_ui_annotation "$PHTML" "")"
pcsb_stub "scripts/check_ui_annotation.py" 1 "warn-only"
assert_eq "ui-annotation · rc=1 → 不阻断（eq2 语义，非 ne0）" "0" "$(pcsb_run pc_ui_annotation "$PHTML" "")"
pcsb_stub "scripts/check_ui_annotation.py" 2 "hit"
assert_eq "ui-annotation · imap 路径同样触发" "1" "$(pcsb_run pc_ui_annotation "$IHTML" "")"
assert_eq "ui-annotation · SKIP env → 放行" "0" "$(pcsb_run pc_ui_annotation "$PHTML" SKIP_UI_ANNOTATION_GATE)"

# stderr 四段式锁定：模板把 banner 参数化，文案必须逐字不变（HOOK_WRITING §二 是模型唯一反馈通道）。
# 同时判「放行」的断言若只看 _PC_BLOCKED，函数中途崩溃也输出 0（假绿）——clean 路径另验 stderr 为空。
# needle 必须锁**整行标题**（含 gate 名之后的诊断文案）——assert_grep 是子串匹配，只锁 `🚫 [gate]`
# 前缀的话，文案被改坏仍会通过。方括号要转义：grep 走 BRE，裸 [ 会被当字符类报 invalid character range。
pcsb_stub ".claude/skills/prototype/scripts/check_page_fns_shell.py" 1 "hit"
assert_grep "shell-gate · block 标题行未漂移" "🚫 \[prototype-shell-gate\] page_fns 生成超出设备壳范围（应仅产页内容，外壳由模板提供）" "$(pcsb_err pc_prototype_source "$PYSRC" "")"
pcsb_stub ".claude/skills/prototype/scripts/check_page_fns_shell.py" 0 "ok"
assert_eq "shell-gate · clean 时 stderr 为空（区分崩溃假绿）" "" "$(pcsb_err pc_prototype_source "$PYSRC" "")"

pcsb_stub ".claude/skills/prototype/scripts/check_proto_split.py" 1 "hit"
assert_grep "proto-split · block 标题行未漂移" "🚫 \[prototype-split-gate\] 原型 page_fns 未拆分到 src/scenes（疑似内联在 orchestrator 单文件）" "$(pcsb_err pc_prototype_split "$PHTML" "")"
pcsb_stub ".claude/skills/prototype/scripts/check_proto_split.py" 0 "ok"
assert_eq "proto-split · clean 时 stderr 为空（区分崩溃假绿）" "" "$(pcsb_err pc_prototype_split "$PHTML" "")"

pcsb_stub ".claude/skills/interaction-map/scripts/check_imap_split.py" 1 "hit"
assert_grep "imap-split · block 标题行未漂移" "🚫 \[imap-split-gate\] IMAP scene_fns 未拆分到 src/scenes（疑似内联在 orchestrator 单文件）" "$(pcsb_err pc_imap_split "$IHTML" "")"
pcsb_stub ".claude/skills/interaction-map/scripts/check_imap_split.py" 0 "ok"
assert_eq "imap-split · clean 时 stderr 为空（区分崩溃假绿）" "" "$(pcsb_err pc_imap_split "$IHTML" "")"

pcsb_stub "scripts/check_ui_annotation.py" 2 "hit"
assert_grep "ui-annotation · block 标题行未漂移" "🚫 \[ui-annotation-gate\] 渲染 UI 屏内写了开发注解，开发会误读为真实产品文案" "$(pcsb_err pc_ui_annotation "$PHTML" "")"
pcsb_stub "scripts/check_ui_annotation.py" 0 "ok"
assert_eq "ui-annotation · clean 时 stderr 为空（区分崩溃假绿）" "" "$(pcsb_err pc_ui_annotation "$PHTML" "")"

# SKIP 环境变量门（guards.sh check_skip_env）—— 全工区唯一实现，三侧共用
source .claude/hooks/lib/guards.sh
assert_eq "check_skip_env · 未命中 → return 1" "1" "$(SKIP_X_GATE=0; check_skip_env g SKIP_X_GATE d; echo $?)"
assert_eq "check_skip_env · env=1 → return 0" "0" "$(SKIP_X_GATE=1; check_skip_env g SKIP_X_GATE d >/dev/null 2>&1; echo $?)"
assert_eq "check_skip_env · --exit → exit 0（子 shell 截获）" "0" "$(SKIP_X_GATE=1; ( check_skip_env g SKIP_X_GATE d --exit ); echo $?)"

# ═══════════════════════════════════════════════════════════════
echo ""
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -gt 0 ]; then
  echo "❌ $FAIL / $TOTAL failed"
  exit 1
fi
echo "✅ $PASS / $TOTAL passed"
exit 0
