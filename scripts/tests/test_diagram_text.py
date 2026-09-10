"""lib.diagram_text 的 .mmd / .drawio 文本抽取单测。

锁住：flowchart 三种标签位（节点 / 判定 / 边）+ subgraph 标题 + stateDiagram 状态名
都能被抽出（否则 CJK 标点 / 禁裸编号两道门对 .mmd 形同虚设），
stateDiagram 不引号的边 label 也能抽到，`%%{init}%%` 指令行不误扫，行号对齐。
"""
import pytest

from lib.diagram_text import extract_scan_lines


def _scan(lines):
    return extract_scan_lines(".mmd", lines)


# ── flowchart：三种标签位 ────────────────────────────────
def test_flowchart_node_decision_edge_labels_extracted():
    lines = [
        "flowchart TB",
        '    A(["起点，半角逗号"]) --> B{"决策: 是?"}',
        '    B -->|"否，退回"| C["处理 A-2 步骤"]',
    ]
    out = _scan(lines)
    assert "起点，半角逗号" in out[1]
    assert "决策: 是?" in out[1]
    assert "否，退回" in out[2]
    assert "处理 A-2 步骤" in out[2]


def test_swimlane_subgraph_title_extracted():
    lines = [
        "swimlane-beta TB",
        '    subgraph lane_0 ["投资人"]',
        '        I1(["发起赎回"])',
    ]
    out = _scan(lines)
    assert "投资人" in out[1]
    assert "发起赎回" in out[2]


# ── stateDiagram ─────────────────────────────────────────
def test_state_label_and_unquoted_transition_extracted():
    lines = [
        "stateDiagram-v2",
        '    state "待补全" as s1',
        "    s1 --> s3 : 审核通过点上线",
    ]
    out = _scan(lines)
    assert "待补全" in out[1]
    assert "审核通过点上线" in out[2]


# ── 边界 ─────────────────────────────────────────────────
def test_init_directive_not_scanned():
    lines = ['%%{init: {"theme": "base"}}%%', "flowchart TB"]
    out = _scan(lines)
    assert out[0] == ""


def test_syntax_noise_not_extracted():
    out = _scan(["flowchart TB", "    classDef fail fill:#FEE3E6,stroke:#F6465D"])
    assert out[1] == ""


def test_line_count_preserved():
    lines = ["flowchart TB", "", '    A(["x"]) --> B["y"]', ""]
    assert len(_scan(lines)) == len(lines)


# ── .drawio 分支不回归 ───────────────────────────────────
def test_drawio_value_still_extracted():
    lines = ['<mxCell value="发起赎回" style="rounded=1;" vertex="1">']
    out = extract_scan_lines(".drawio", lines)
    assert out[0] == "发起赎回"


@pytest.mark.parametrize("suffix", [".md", ".html", ".txt"])
def test_other_suffix_returns_none(suffix):
    assert extract_scan_lines(suffix, ["任意内容"]) is None
