import sys, os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/interaction-map/references'))
from gen_imap_skeleton import generate_skeleton

project = {
    "name": "私募基金认申赎",
    "subtitle": "前端交互大图 v1.0",
    "nav_desc": "H5 投资人端 → Web 运营后台 ｜ 分 PART 阅读",
}

legends = [
    {"color": "blue",   "label": "合规校验"},
    {"color": "green",  "label": "新增功能"},
    {"color": "red",    "label": "风控拦截"},
    {"color": "amber",  "label": "流程跳转"},
    {"color": "purple", "label": "运营后台"},
]

parts = [
    {
        "id": "part0",
        "num": "PART 0",
        "name": "📱 H5 投资人端",
        "desc": "合格投资者认购 / 赎回全流程（H5）",
        "theme": "frontend",
        "dot_color": "amber",
        "scenes": [
            {"id": "A-1", "name": "基金详情 + 认购下单",          "trigger": "基金列表点入 → 点「立即认购」",  "device": "phone"},
            {"id": "A-2", "name": "认购协议签署 + 冷静期提示",      "trigger": "A-1 完成下单后",                "device": "phone"},
            {"id": "B-1", "name": "持仓列表 + 赎回入口",           "trigger": "我的 → 持仓",                  "device": "phone"},
            {"id": "B-2", "name": "赎回下单（含大额顺延提示）",      "trigger": "B-1 点「赎回」",               "device": "phone"},
        ],
    },
    {
        "id": "part1",
        "num": "PART 1",
        "name": "🖥️ Web 运营后台",
        "desc": "基金运营人员订单审核（Web）",
        "theme": "admin",
        "dot_color": "blue",
        "scenes": [
            {"id": "C-1", "name": "订单审核队列（认购 + 赎回）",   "trigger": "运营后台 → 订单中心",            "device": "web"},
        ],
    },
]

output_path = os.path.join(
    _ROOT, 'projects/demo-private-fund/deliverables/imap-private-fund-v1.html'
)
generate_skeleton(project, legends, parts, output_path)
print(f"Skeleton written to: {output_path}")
