"""Step 0 范式门 · prototype skill

读 context.md 第 2 章 + scene-list.md，推断端构成，输出推荐范式 + 标杆 + 必读 references。

用法：
    python3 .claude/skills/prototype/scripts/check_paradigm.py {项目名}

输出 stdout（人读 + 机读）：
    范式: 单 phone + scene chips
    端类型: app
    场景数: 17
    标杆: projects/htx-live-streaming-updateQ2/deliverables/HTX_观众端可交互原型_V8.html
    骨架模式: single-phone-scenes
    必读 references:
      - .claude/skills/prototype/references/crypto-app-vocabulary.md
      - .claude/skills/prototype/references/baseline-pattern-card.md
      - .claude/skills/prototype/references/prototype-source-discipline.md
      - .claude/skills/interaction-map/references/biz-social.md
      - .claude/skills/interaction-map/references/components-core.md

退出码：
    0 = 推断成功
    1 = 项目不存在 / 缺 context.md / scene-list.md
    2 = 推断不出范式（要求模型问用户）
"""
import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


# ── 4 个范式定义 ─────────────────────────────────────
PARADIGMS = {
    "single-phone-scenes": {
        "name": "单 phone + scene chips",
        "baseline": "projects/livestream/q2-update/deliverables/HTX_观众端可交互原型_V8.html",
        "alt_baselines": [
            "projects/community/base/deliverables/proto-htx-community-v3.html",
        ],
    },
    "single-phone-no-nav": {
        "name": "单 phone 无 nav",
        "baseline": None,
        "alt_baselines": [],
    },
    "multi-view-gnav": {
        "name": "多 view 切换 (gnav)",
        "baseline": "projects/growth/activity-center/deliverables/活动中心_可交互原型_v5.1.html",
        "alt_baselines": [],
    },
    "single-view-sidebar": {
        "name": "单 view + sidebar",
        "baseline": None,
        "alt_baselines": [],
    },
}


def infer_end_type(ctx_text: str) -> set:
    """从 context.md 第 2 章关键词推断端类型集合"""
    ends = set()
    text = ctx_text.lower()
    if any(k in ctx_text for k in ("App 端", "客户端", "iOS", "Android", "移动端", "前台 App")):
        ends.add("app")
    if any(k in ctx_text for k in ("Web 前台", "PC 前台", "网页前台", "H5")):
        ends.add("web-frontend")
    if any(k in ctx_text for k in ("后台", "管理端", "CMS", "后台管理", "运营端")):
        ends.add("web-backend")
    return ends


def count_scenes(scene_list_text: str) -> int:
    """数 scene-list.md 顶部表格的场景行数（粗略）"""
    rows = re.findall(r"^\s*\|\s*[A-Za-z]-?\d+", scene_list_text, re.MULTILINE)
    if rows:
        return len(rows)
    rows = re.findall(r"^\s*[#\-]+\s*[A-Za-z]-?\d+", scene_list_text, re.MULTILINE)
    return len(rows)


def pick_paradigm(ends: set, scene_count: int) -> str:
    """4 个范式路由"""
    if "web-backend" in ends and "web-frontend" not in ends and "app" not in ends:
        return "single-view-sidebar"
    if "web-frontend" in ends and "web-backend" in ends:
        return "multi-view-gnav"
    if "app" in ends and "web-backend" in ends:
        return "multi-view-gnav"
    if "app" in ends and scene_count >= 5:
        return "single-phone-scenes"
    if "app" in ends and scene_count < 5:
        return "single-phone-no-nav"
    return "unknown"


def biz_vertical(ctx_text: str, scene_text: str) -> list:
    """从关键词推断业务垂直，返回必读 imap references 列表"""
    blob = ctx_text + scene_text
    hits = []
    if any(k in blob for k in ("社区", "Feed", "牛人榜", "个人主页", "动态", "关注")):
        hits.extend(["biz-social.md", "components-core.md"])
    if any(k in blob for k in ("交易", "合约", "现货", "跟单", "下单", "K 线")):
        hits.extend(["biz-trading.md", "components-core.md"])
    if any(k in blob for k in ("直播", "弹幕", "礼物", "连麦")):
        hits.extend(["biz-livestream.md", "components-core.md"])
    if not hits:
        hits = ["components-core.md", "templates-quickref.md"]
    seen = set()
    return [x for x in hits if not (x in seen or seen.add(x))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    args = ap.parse_args()

    proj_dir = ROOT / "projects" / args.project
    if not proj_dir.exists():
        print(f"❌ 项目目录不存在: {proj_dir}", file=sys.stderr)
        sys.exit(1)

    ctx_path = proj_dir / "context.md"
    sl_path = proj_dir / "scene-list.md"
    if not ctx_path.exists():
        print(f"❌ 缺 context.md: {ctx_path}", file=sys.stderr)
        sys.exit(1)
    if not sl_path.exists():
        print(f"❌ 缺 scene-list.md: {sl_path}", file=sys.stderr)
        sys.exit(1)

    ctx = ctx_path.read_text(encoding="utf-8")
    sl = sl_path.read_text(encoding="utf-8")

    ends = infer_end_type(ctx)
    scenes = count_scenes(sl)
    paradigm_key = pick_paradigm(ends, scenes)
    biz_refs = biz_vertical(ctx, sl)

    if paradigm_key == "unknown":
        print("⚠️  推断不出范式，请向用户确认端构成（4 选 1）：", file=sys.stderr)
        print("    1. 单 phone + scene chips (纯 App + 多场景 ≥ 5)", file=sys.stderr)
        print("    2. 单 phone 无 nav (纯 App + 简单流 ≤ 3)", file=sys.stderr)
        print("    3. 多 view 切换 gnav (Web + App + 后台)", file=sys.stderr)
        print("    4. 单 view + sidebar (纯 Web 后台 / CMS)", file=sys.stderr)
        sys.exit(2)

    p = PARADIGMS[paradigm_key]
    print(f"范式: {p['name']}")
    print(f"端类型: {','.join(sorted(ends)) or '?'}")
    print(f"场景数: {scenes}")
    if p["baseline"]:
        print(f"标杆: {p['baseline']}")
    if p["alt_baselines"]:
        print(f"备选标杆: {', '.join(p['alt_baselines'])}")
    print(f"骨架模式: {paradigm_key}")
    print("必读 references:")
    print("  - .claude/skills/prototype/references/crypto-app-vocabulary.md")
    print("  - .claude/skills/prototype/references/baseline-pattern-card.md")
    print("  - .claude/skills/prototype/references/prototype-source-discipline.md")
    for ref in biz_refs:
        print(f"  - .claude/skills/interaction-map/references/{ref}")

    has_imap = list(proj_dir.glob("deliverables/imap-*.html"))
    has_competitors = (proj_dir / "inputs" / "competitors").exists()
    print(f"上游 IMAP: {'✓ ' + has_imap[0].name if has_imap else '✗ 无 → 走无 IMAP 双 anchor 流程'}")
    print(f"竞品截图: {'✓' if has_competitors else '✗ 必须收集到 inputs/competitors/'}")


if __name__ == "__main__":
    main()
