#!/usr/bin/env python3
"""当前分支任务进展（只读链，抽象 task-progress.md 的多步查询 + 进展判断）。

从当前 Git 分支提 H 号 → work get + repo current + related-repo + tag history(DEV/TEST/PRD)
+ mr list → 按 task-progress.md「进展判断口径」表输出一句话结论 + 证据。

用法：
    python3 hx_task_progress.py                 # 从当前 git 分支解析 H 号
    python3 hx_task_progress.py H402040         # 指定 H 号/work_id，跳过分支解析
    python3 hx_task_progress.py --json          # 输出结构化 JSON（供 sync 等消费）

只读，不写入。写操作（打 TAG / 建 MR / 合并 / 流转）按 SKILL.md 逐步人工确认，不在此脚本。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hx_client as hx  # noqa: E402

_H_RE = re.compile(r"H(\d+)")


def _current_branch() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "branch", "--show-current"], stderr=subprocess.DEVNULL, text=True
        )
        return out.strip() or None
    except Exception:
        return None


def resolve_work_id(arg: str | None) -> tuple[str, str]:
    """返回 (work_id, 来源说明)。arg 优先；否则从当前分支名提 H 号。"""
    if arg:
        m = _H_RE.search(arg)
        wid = m.group(1) if m else arg.lstrip("Hh")
        if not wid.isdigit():
            raise SystemExit(f"无法从 '{arg}' 解析 work_id（需 H<数字> 或纯数字）")
        return wid, f"参数 {arg}"
    branch = _current_branch()
    if not branch:
        raise SystemExit("当前目录不是 git 仓库或无当前分支；请传 H 号作参数。")
    m = _H_RE.search(branch)
    if not m:
        raise SystemExit(f"分支名 '{branch}' 无 H 号；请传 H 号作参数或改用个人面板（hx_panel.py）。")
    return m.group(1), f"分支 {branch}"


def _safe(fn, default):
    """只读探测：单个子查询失败不炸整个流程，返回 default 并记原因。"""
    try:
        return fn(), None
    except hx.HxError as e:
        return default, str(e)


def gather(work_id: str, token: str | None = None) -> dict:
    """串起 task-progress.md 的只读查询链，返回结构化进展证据。"""
    hx.ensure_auth(token=token)
    result: dict = {"work_id": work_id, "errors": {}}

    work = hx.run(["work", "get", work_id], token=token)
    result["work_name"] = work.get("work_name")
    # work get 返回 current_proc；personal list 返回 current_process。取兼容。
    result["current_process"] = work.get("current_proc") or work.get("current_process")
    result["work"] = work

    repo, err = _safe(lambda: hx.run(["repo", "current"], token=token), {})
    if err:
        result["errors"]["repo_current"] = err
    repo_obj = repo.get("repo", repo) if isinstance(repo, dict) else {}
    repo_id = repo_obj.get("gitlab_repo_id") or repo_obj.get("id")
    result["repo_id"] = repo_id
    result["repo_name"] = repo_obj.get("gitlab_repo_name") or repo_obj.get("name")

    related, err = _safe(lambda: hx.run(["repo", "work", "related-repo", work_id], token=token), {})
    if err:
        result["errors"]["related_repo"] = err
    result["related_repo"] = related

    tags: dict[str, list] = {}
    if repo_id:
        for prefix in ("DEV", "TEST", "PRD"):
            th, err = _safe(
                lambda p=prefix: hx.run(
                    ["repo", "tag", "history", "--work-id", work_id,
                     "--repo-id", str(repo_id), "--prefix", p], token=token),
                {},
            )
            if err:
                result["errors"][f"tag_{prefix}"] = err
            rows = th.get("rows") or th.get("tags") or (th if isinstance(th, list) else [])
            tags[prefix] = rows
        mr, err = _safe(
            lambda: hx.run(["repo", "mr", "list", "--work-id", work_id,
                            "--repo-id", str(repo_id)], token=token),
            {},
        )
        if err:
            result["errors"]["mr_list"] = err
        result["mr"] = mr.get("rows") if isinstance(mr, dict) else mr
    result["tags"] = tags
    return result


def judge(ev: dict) -> str:
    """按 task-progress.md「进展判断口径」表给一句话结论。"""
    tags = ev.get("tags", {})
    has_prd = bool(tags.get("PRD"))
    has_test = bool(tags.get("TEST"))
    has_dev = bool(tags.get("DEV"))
    proc = ev.get("current_process") or ""
    if has_prd:
        return f"已打上线 TAG（PRD），代码已上线链路；火效流程状态「{proc}」。"
    if has_test:
        return f"已打测试 TAG（TEST），通常已提测/测试中；火效流程「{proc}」，尚无上线 TAG。"
    if has_dev:
        return f"已打开发自测 TAG（DEV），开发进行中；火效流程「{proc}」，尚无测试/上线 TAG。"
    if ev.get("related_repo"):
        return f"已关联仓库/分支，代码管理 V2 已开始开发；火效流程「{proc}」，尚无 TAG。"
    if ev.get("repo_id"):
        return f"火效任务存在，当前仓库未见关联分支/TAG；可能还没开始开发或未关联本仓库。火效流程「{proc}」。"
    return f"仅拿到火效工作项（流程「{proc}」）；未匹配到当前 GitLab 仓库，缺代码维度证据。"


def render(ev: dict, source: str) -> str:
    wid = ev["work_id"]
    lines = [
        f"任务：{ev.get('work_name') or '（未取到标题）'}（work_id={wid}，来源：{source}）",
        f"链接：{hx.work_link(wid)}（代码管理 V2 在此页「代码管理」tab）",
        f"火效流程状态：{ev.get('current_process') or '—'}",
    ]
    if ev.get("repo_name"):
        lines.append(f"仓库：{ev['repo_name']}（repo_id={ev.get('repo_id')}）")
    tags = ev.get("tags", {})
    tag_summary = ", ".join(f"{p}×{len(tags.get(p, []))}" for p in ("DEV", "TEST", "PRD"))
    lines.append(f"TAG：{tag_summary or '—'}")
    lines.append("")
    lines.append(f"进展判断：{judge(ev)}")
    if ev.get("errors"):
        lines.append("")
        lines.append("（部分子查询未成功，仅影响对应维度，不代表未发生）：")
        for k, v in ev["errors"].items():
            lines.append(f"  · {k}: {v}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="当前分支任务进展（只读）")
    ap.add_argument("work", nargs="?", help="H 号 / work_id；缺省从当前 git 分支解析")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ap.add_argument("--token", help="覆盖 AIHUB_TOKEN，仅本次")
    args = ap.parse_args()

    try:
        wid, source = resolve_work_id(args.work)
        ev = gather(wid, token=args.token)
    except hx.HxAuthError as e:
        print(f"认证失败：{e}\n下一步：{e.hint}", file=sys.stderr)
        return 2
    except hx.HxError as e:
        print(f"调用失败：{e}", file=sys.stderr)
        return 1

    if args.json:
        ev["_source"] = source
        ev["_judgement"] = judge(ev)
        print(json.dumps(ev, ensure_ascii=False))
    else:
        print(render(ev, source))
    return 0


if __name__ == "__main__":
    sys.exit(main())
