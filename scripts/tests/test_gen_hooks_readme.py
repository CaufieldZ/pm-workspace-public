"""gen_hooks_readme.py 提取器测试 —— gate 名提取六类调用 + 误抓防护。

验证点：
1. 三类原有调用（log_event / _check_block / _log_skip_gate）仍提取
2. 三类新增调用（_pc_line_enqueue / _pc_strict_block / check_skip_env / GATE= 赋值）正确提取
3. 变量引用形式（$gate / "$gate"）不误抓
4. 小写 local gate 变量不误抓（仅大写 GATE 字面量赋值才提取）
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from gen_hooks_readme import GATE_RE, gates_in


def test_literal_log_event():
    """log_event hook <gate> / log_event gate <gate> 提取。"""
    text = 'log_event hook script-syntax-gate block "$CMD"'
    assert "script-syntax-gate" in GATE_RE.findall(text)


def test_check_block():
    """_check_block|clean|warn <gate> 提取。"""
    text = '_check_block my-gate "$FILE_PATH"'
    assert "my-gate" in GATE_RE.findall(text)


def test_log_skip_gate():
    """_log_skip_gate <gate> 提取。"""
    text = '_log_skip_gate some-gate'
    assert "some-gate" in GATE_RE.findall(text)


def test_pc_line_enqueue_quoted():
    """_pc_line_enqueue "<gate>" 提取（带引号；产线三查入队段持有 gate 字面量）。"""
    text = '_pc_line_enqueue "rule-version-drift-gate" "SKIP_RULE_VERSION_DRIFT_GATE" "scripts/check_x.py"'
    assert "rule-version-drift-gate" in GATE_RE.findall(text)


def test_pc_strict_block_quoted():
    """_pc_strict_block "<gate>" 提取（block 类 gate 的共享骨架模板）。"""
    text = '_pc_strict_block "prototype-split-gate" "SKIP_PROTOTYPE_SPLIT_GATE" "a.py" "--strict" ne0'
    assert "prototype-split-gate" in GATE_RE.findall(text)


def test_check_skip_env_quoted():
    """check_skip_env "<gate>" 提取（全工区唯一 SKIP 门，部分 gate 名只在此出现）。"""
    text = 'check_skip_env "scripts-first" "SKIP_SCRIPTS_FIRST_GATE" "$FILE_PATH"'
    assert "scripts-first" in GATE_RE.findall(text)


def test_gate_assignment():
    """GATE="<gate>" 赋值提取。"""
    text = 'GUIDE="some.md"; GATE="required-read-gate"'
    assert "required-read-gate" in GATE_RE.findall(text)


def test_no_false_positive_variable_ref():
    """变量引用 $gate / "$gate" 不误抓。"""
    text = 'log_event hook "$gate" warn "$DETAIL"'
    matches = GATE_RE.findall(text)
    assert "gate" not in matches, f"变量名 'gate' 被误抓: {matches}"
    assert "warn" not in matches


def test_no_false_positive_lowercase_local():
    """小写 local gate 变量不误抓（仅大写 GATE 才提取）。"""
    text = 'local gate="$1"\nlocal GATE="real-gate"'
    matches = GATE_RE.findall(text)
    assert "real-gate" in matches, "大写 GATE 赋值应提取"
    # local gate="$1" — $1 不是 kebab 字面量，不应被抓
    assert "$1" not in matches


def test_no_false_positive_gateway():
    """GATEWAY= 不误抓（GATE 后非 =）。"""
    text = 'GATEWAY="something"'
    matches = GATE_RE.findall(text)
    assert "something" not in matches


def test_gates_in_file(tmp_path):
    """gates_in() 对完整 .sh 文件提取。"""
    f = tmp_path / "test_hook.sh"
    f.write_text(
        '#!/bin/bash\n'
        'source lib/log.sh\n'
        'GATE="my-cool-gate"\n'
        '_pc_line_enqueue "my-cool-gate" "SKIP_MY_COOL_GATE" "scripts/check_x.py"\n'
        'log_event hook my-cool-gate warn "detail"\n'
        '# comment: log_event hook not-a-real-gate\n',  # 注释里的也应提取（grep 式扫描不区分注释）
        encoding="utf-8",
    )
    gates = gates_in(f)
    assert "my-cool-gate" in gates


def test_real_hook_files_extract_known_gates():
    """对真实 pre-writeedit-guards.sh 提取 required-read-gate（回归 P0-2 核心问题）。"""
    p = ROOT / ".claude/hooks/lib/pre-writeedit-guards.sh"
    if not p.is_file():
        return  # 非本工区环境跳过
    gates = gates_in(p)
    assert "required-read-gate" in gates, f"required-read-gate 未提取到！提取结果: {sorted(gates)}"
    assert "skill-load-gate" in gates, f"skill-load-gate 未提取到！提取结果: {sorted(gates)}"


def test_real_post_checks_extract_known_gates():
    """对真实 post-checks.sh 提取 rule-version-drift-gate / delta-conflict-gate。"""
    p = ROOT / ".claude/hooks/lib/post-checks.sh"
    if not p.is_file():
        return
    gates = gates_in(p)
    assert "rule-version-drift-gate" in gates, "rule-version-drift-gate 未提取到！"
    assert "delta-conflict-gate" in gates, "delta-conflict-gate 未提取到！"
    # 模板化后这些 gate 的字面量**只**出现在 _pc_strict_block 调用里（不再是 log_event 行）。
    # 提取器漏认该形态 → 它们从 README 索引静默消失（44→41），只有 audit §15.10 会报。
    for g in ("prototype-shell-gate", "prototype-split-gate", "imap-split-gate", "ui-annotation-gate"):
        assert g in gates, f"{g} 未提取到！提取结果: {sorted(gates)}"
