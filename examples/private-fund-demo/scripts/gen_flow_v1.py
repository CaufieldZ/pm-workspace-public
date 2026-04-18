"""
gen_flow_v1.py · 私募基金流程图(合格投资者校验 + 大额赎回审批)

依赖 .claude/skills/flowchart/references/gen_flow_base.py
"""
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

# 向上查找 .claude/skills/flowchart/references(兼容 private/public 不同层级)
_here = Path(__file__).resolve().parent
for _p in [_here, *_here.parents]:
    _target = _p / ".claude/skills/flowchart/references"
    if _target.exists():
        sys.path.insert(0, str(_target))
        break
else:
    raise RuntimeError("flowchart skill references not found in ancestors")

from gen_flow_base import render_flowchart  # noqa: E402


# ── 图 1:合格投资者校验(branch) ─────────────────────
BRANCH_QI = {
    "type": "branch",
    "short_title": "合格投资者校验",
    "title": "合格投资者认证流程(R1/R2)",
    "subtitle": "用户进入认购前的前后端双重校验,失败分支走引导或拦截",
    "layout": "TB",
    "nodes": [
        {"id": "START", "type": "terminal", "label": "点击「立即认购」"},
        {"id": "FETCH", "type": "process",  "label": "前端请求 QI 状态"},
        {"id": "Q1",    "type": "decision", "label": "QI 已认证?"},
        {"id": "AUTH",  "type": "fail",     "label": "拦截+引导「去认证」"},
        {"id": "READC", "type": "process",  "label": "读取风险等级 C"},
        {"id": "Q2",    "type": "decision", "label": "C 级 ≥ R 级?"},
        {"id": "BLOCK", "type": "fail",     "label": "拦截+提示不匹配"},
        {"id": "BADGE", "type": "success",  "label": "Badge「C3 匹配 R3」"},
        {"id": "NEXT",  "type": "terminal", "label": "进入认购下单"},
    ],
    "edges": [
        {"s": "START", "t": "FETCH"},
        {"s": "FETCH", "t": "Q1"},
        {"s": "Q1",    "t": "AUTH",  "label": "No"},
        {"s": "Q1",    "t": "READC", "label": "Yes"},
        {"s": "READC", "t": "Q2"},
        {"s": "Q2",    "t": "BLOCK", "label": "No"},
        {"s": "Q2",    "t": "BADGE", "label": "Yes"},
        {"s": "BADGE", "t": "NEXT"},
    ],
}


# ── 图 2:大额赎回审批(swimlane) ─────────────────────
SWIMLANE_REDEEM = {
    "type": "swimlane",
    "short_title": "大额赎回审批",
    "title": "大额赎回审批流程(含资料回流 / 风险驳回 / 联席签字)",
    "subtitle": "投资人 / 运营 / 风控 / 基金经理 四泳道 · 14 节点 · 4 判定 · 3 条跨泳道回流",
    "lanes": ["投资人", "运营", "风控", "基金经理"],
    "nodes": [
        {"id": "I1", "lane": "投资人",   "col": 0, "type": "terminal", "label": "发起赎回申请"},
        {"id": "O1", "lane": "运营",     "col": 1, "type": "process",  "label": "接收+资料核验"},
        {"id": "Q1", "lane": "运营",     "col": 2, "type": "decision", "label": "资料完整?"},
        {"id": "I2", "lane": "投资人",   "col": 2, "type": "fail",     "label": "补充资料"},
        {"id": "Q2", "lane": "运营",     "col": 3, "type": "decision", "label": "金额≥300万?"},
        {"id": "I3", "lane": "投资人",   "col": 4, "type": "success",  "label": "普通赎回 T+1"},
        {"id": "R1", "lane": "风控",     "col": 4, "type": "process",  "label": "风险评估"},
        {"id": "Q3", "lane": "风控",     "col": 5, "type": "decision", "label": "风险通过?"},
        {"id": "I4", "lane": "投资人",   "col": 6, "type": "fail",     "label": "收到驳回通知"},
        {"id": "F1", "lane": "基金经理", "col": 6, "type": "process",  "label": "基金经理审批"},
        {"id": "Q4", "lane": "基金经理", "col": 7, "type": "decision", "label": "≥1000万?"},
        {"id": "F2", "lane": "基金经理", "col": 8, "type": "process",  "label": "联席签字"},
        {"id": "F3", "lane": "基金经理", "col": 9, "type": "terminal", "label": "结算完成"},
        {"id": "I5", "lane": "投资人",   "col": 9, "type": "success",  "label": "到账确认"},
    ],
    "edges": [
        {"s": "I1", "t": "O1"},
        {"s": "O1", "t": "Q1"},
        {"s": "Q1", "t": "I2", "label": "No"},
        {"s": "I2", "t": "O1"},
        {"s": "Q1", "t": "Q2", "label": "Yes"},
        {"s": "Q2", "t": "I3", "label": "No"},
        {"s": "Q2", "t": "R1", "label": "Yes"},
        {"s": "R1", "t": "Q3"},
        {"s": "Q3", "t": "I4", "label": "No"},
        {"s": "Q3", "t": "F1", "label": "Yes"},
        {"s": "F1", "t": "Q4"},
        {"s": "Q4", "t": "F2", "label": "Yes"},
        {"s": "Q4", "t": "F3", "label": "No", "sp": "bottom", "tp": "bottom"},
        {"s": "F2", "t": "F3"},
        {"s": "F3", "t": "I5"},
    ],
}


if __name__ == "__main__":
    render_flowchart(
        output_path=str(PROJECT_DIR / "deliverables/flow-demo-qi.html"),
        title="流程图 Demo · 私募",
        subtitle="X6 + dagre(分支)/ 泳道二维定位 · 深色画布 + 浅色白板卡片 · 自动自检",
        charts=[BRANCH_QI, SWIMLANE_REDEEM],
    )
