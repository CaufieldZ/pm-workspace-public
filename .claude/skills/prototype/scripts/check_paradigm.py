"""Step 0 范式门 · prototype skill

读真相源（baseline）+ scene-list.md，推断端构成，输出推荐范式 + 标杆 + 必读 references。

用法：
    python3 .claude/skills/prototype/scripts/check_paradigm.py {项目名}

输出 stdout（人读 + 机读）：
    范式: 单 phone + scene chips
    端类型: app
    场景数: 17
    标杆: <PARADIGMS 里对应范式的 baseline 路径>
    骨架模式: single-phone-scenes
    必读 references:
      - .claude/skills/prototype/references/crypto-app-vocabulary.md
      - .claude/skills/prototype/references/baseline-pattern-card.md
      - .claude/skills/prototype/references/prototype-source-discipline.md
      - .claude/skills/interaction-map/references/biz-social.md
      - .claude/skills/interaction-map/references/components-core.md

退出码：
    0 = 推断成功
    1 = 项目不存在 / 缺真相源（baseline / context）/ scene-list.md
    2 = 推断不出范式（要求模型问用户）
"""
import argparse
import atexit
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from lib.truth_source import involved_ends, resolve  # noqa: E402

# skill-log: 完成率埋点（包 sys.exit 按退出码 emit；正常 return 兜底 atexit emit completed）
_SKILL_EMITTED = False


def _emit_skill_end(status):
    global _SKILL_EMITTED
    if _SKILL_EMITTED:
        return
    _SKILL_EMITTED = True
    try:
        import datetime
        import json
        import os
        root = os.environ.get("CLAUDE_PROJECT_DIR")
        root = Path(root) if root else Path(__file__).resolve().parents[4]
        log_path = root / ".claude" / "logs" / "usage.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        tz = datetime.timezone(datetime.timedelta(hours=8))
        ts = datetime.datetime.now(tz).isoformat(timespec="seconds")
        ev = {"ts": ts, "type": "skill", "name": "prototype", "action": status}
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:
        pass


_orig_exit = sys.exit


def _wrapped_exit(code=0):
    rc = code or 0
    _emit_skill_end("completed" if rc == 0 else "failed")
    _orig_exit(code)


sys.exit = _wrapped_exit
atexit.register(lambda: _emit_skill_end("completed"))


ROOT = Path(__file__).resolve().parents[4]


# ── 4 个范式定义 ─────────────────────────────────────
PARADIGMS = {
    "single-phone-scenes": {
        "name": "单 phone + scene chips",
        "baseline": "projects/livestream/archive/2026Q2/q2-update/deliverables/示例_观众端可交互原型_V8.html",
        "alt_baselines": [
            "projects/community/base/deliverables/proto-proj-community-v3.html",
        ],
    },
    "single-phone-no-nav": {
        "name": "单 phone 无 nav",
        "baseline": None,
        "alt_baselines": [],
    },
    "single-view-sidebar": {
        "name": "单 view + sidebar",
        "baseline": None,
        "alt_baselines": [],
    },
    "single-web-front": {
        "name": "单 web 前台 (device=web-front)",
        "baseline": None,
        "alt_baselines": [],
    },
    # 存量 archive 兼容（activity-center 等多 view 合并文件可 rebuild）。
    # 新项目多端走 multi-end-split（每端一独立文件），不再合并进单 HTML。
    "multi-view-gnav": {
        "name": "多 view 切换 (gnav) · 仅存量 archive rebuild",
        "baseline": "projects/growth/archive/activity-center/deliverables/活动中心_可交互原型_v5.3.html",
        "alt_baselines": [],
    },
}

# 多端拆分时，每端各自的单端壳范式（generate_single 一端一文件，device/theme 决定壳）
END_PARADIGM = {
    "app": "single-phone-scenes",       # device=phone dark 壳
    "web-frontend": "single-web-front",  # device=web-front dark 壳 + 顶 nav
    "web-backend": "single-view-sidebar",  # theme=light 后台壳 + sidebar
}
END_LABEL = {"app": "App 端", "web-frontend": "Web 前台", "web-backend": "内部后台"}
_END_SUFFIX = {"app": "app", "web-frontend": "web", "web-backend": "mgt"}


def count_scenes(scene_list_text: str) -> int:
    """数 scene-list.md 顶部表格的场景行数（粗略）"""
    rows = re.findall(r"^\s*\|\s*[A-Za-z]-?\d+", scene_list_text, re.MULTILINE)
    if rows:
        return len(rows)
    rows = re.findall(r"^\s*[#\-]+\s*[A-Za-z]-?\d+", scene_list_text, re.MULTILINE)
    return len(rows)


def pick_paradigm(ends: set, scene_count: int) -> str:
    """范式路由。多端（≥ 2）→ multi-end-split（每端一独立文件），单端走对应单端范式。"""
    real_ends = {e for e in ends if e in END_PARADIGM}
    if len(real_ends) >= 2:
        return "multi-end-split"
    if real_ends == {"web-backend"}:
        return "single-view-sidebar"
    if real_ends == {"web-frontend"}:
        return "single-web-front"  # 对客 Web → dark 前台壳（SKILL.md 范式表 + END_PARADIGM）；原误路由到后台壳
    if "app" in real_ends and scene_count >= 5:
        return "single-phone-scenes"
    if "app" in real_ends and scene_count < 5:
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

    ts = resolve(args.project, ROOT / "projects")
    if ts.kind is None:
        print(f"❌ 缺真相源（无 prd-{ts.line}-baseline.md）: {args.project}", file=sys.stderr)
        sys.exit(1)

    sl_path = proj_dir / "scene-list.md"
    if not sl_path.exists():
        print(f"❌ 缺 scene-list.md: {sl_path}", file=sys.stderr)
        sys.exit(1)

    ctx = ts.path.read_text(encoding="utf-8")
    sl = sl_path.read_text(encoding="utf-8")

    ends = involved_ends(ts)
    scenes = count_scenes(sl)
    paradigm_key = pick_paradigm(ends, scenes)
    biz_refs = biz_vertical(ctx, sl)

    if paradigm_key == "unknown":
        print("⚠️  推断不出范式，请向用户确认端构成（4 选 1）：", file=sys.stderr)
        print("    1. 单 phone + scene chips (纯 App + 多场景 ≥ 5)", file=sys.stderr)
        print("    2. 单 phone 无 nav (纯 App + 简单流 ≤ 3)", file=sys.stderr)
        print("    3. 多端拆分 (Web / App / 后台 任意 ≥ 2 → 每端一独立文件)", file=sys.stderr)
        print("    4. 单 view + sidebar (纯 Web 后台 / CMS)", file=sys.stderr)
        sys.exit(2)

    if paradigm_key == "multi-end-split":
        real_ends = [e for e in ("app", "web-frontend", "web-backend") if e in ends]
        print(f"范式: 多端拆分 — {len(real_ends)} 端各产一个独立文件")
        print(f"端类型: {','.join(sorted(ends)) or '?'}")
        print(f"场景数: {scenes}")
        print("骨架模式: multi-end-split（每端 generate_single 一端一文件，禁合并进单 HTML 顶栏切换）")
        print("各端文件规划:")
        for e in real_ends:
            sub_key = END_PARADIGM[e]
            sub = PARADIGMS[sub_key]
            bl = sub["baseline"] or "（无独立标杆，按 device 壳 + crypto-app-vocabulary 构建）"
            print(f"  - {END_LABEL[e]}: proto-{{产品线}}-{{版本}}-{_END_SUFFIX[e]}.html | 单端范式 {sub_key} | 标杆 {bl}")
        print("必读 references:")
        print("  - .claude/skills/prototype/references/crypto-app-vocabulary.md")
        print("  - .claude/skills/prototype/references/baseline-pattern-card.md")
        print("  - .claude/skills/prototype/references/prototype-source-discipline.md")
        for ref in biz_refs:
            print(f"  - .claude/skills/interaction-map/references/{ref}")
        _print_imap_block(proj_dir)
        return

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

    _print_imap_block(proj_dir)


def _print_imap_block(proj_dir):
    has_imap = list(proj_dir.glob("deliverables/imap-*.html"))
    has_competitors = (proj_dir / "inputs" / "competitors").exists()
    print(f"上游 IMAP: {'✓ ' + has_imap[0].name if has_imap else '✗ 无 → 走无 IMAP 双 anchor 流程'}")
    print(f"竞品截图: {'✓' if has_competitors else '✗ 必须收集到 inputs/competitors/'}")

    if has_imap:
        anchor_re = re.compile(r'→\s*原型「([^」]+)」状态全集')
        anchors = []
        for imap_path in has_imap:
            text = imap_path.read_text(encoding="utf-8")
            for m in anchor_re.finditer(text):
                anchors.append((imap_path.name, m.group(1)))
        if anchors:
            print()
            print(f"IMAP 状态全集锚点: {len(anchors)} 处")
            for fname, target in anchors:
                print(f"  - {fname} → 原型「{target}」")
            print("  → 在 build_proto_v{N}.py 的 page_fns 内为每个锚点提供 state-chip Tab")
            print("    建议 chip：正常态 / 加载中 / 空态 / 错误态 + 业务态 N")
            print("    check_proto.sh 会比对 IMAP 锚点 ↔ prototype state-chip 文案，缺失 FAIL")


if __name__ == "__main__":
    main()
