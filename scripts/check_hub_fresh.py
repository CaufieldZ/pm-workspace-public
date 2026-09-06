#!/usr/bin/env python3
"""hub 分发物新鲜度校验（改完源码忘重打 zip / 忘重贴 OWUI 的机械检出）。

zip 才是真正传上 SkillHub 的东西，OWUI 上贴着的才是同事真正在用的 Agent——
两者都会悄悄落后于 hub/ 里的源码。本脚本把这两种漂移变成可算的红黄灯。

三层判据：

第一层 · zip 新鲜度（机械可算，红灯）：
  包目录里有文件比 zips/{包}.zip 新 ⇒ 源码改了没重打，发出去的是旧版。
  修：bash hub/_repack.sh {包}

第二层 · zip 缺失（黄灯）：
  包无 zip 且不在豁免名单 ⇒ 要么该打包，要么该登记豁免。

第三层 · 部署态漂移（黄灯）：
  对照 hub/deployed.json（人工登记「OWUI 上真正贴着的版本 + 日期」，平台无 API
  不自动拉）。Tool 包比 aihub_tool.py 头部 version；Agent 包比 system-prompt.md /
  agent-model.json 的改动时间是否晚于登记的部署日期。未登记的包只提示，不报错。

豁免走登记制（EXEMPT_NO_ZIP）：agent 组装包 raw 分发不打 zip，规范文档非包。

用法：
    python3 scripts/check_hub_fresh.py
    python3 scripts/check_hub_fresh.py --strict     # 有红灯 exit 2（pre-commit / audit 用）

退出码：
    0 — clean / warn（未传 --strict）
    2 — 传 --strict 且有红灯（zip 过期）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.repo import find_root  # noqa: E402

# 不打 zip 的包（登记制豁免）：agent 组装包走 raw 分发，规范文档 / 参考资料非包
EXEMPT_NO_ZIP = {
    "confluence-archaeology-agent",
    "data-agent",
    "file-parse-agent",
    "hx-agent",
    "mrd-review-agent",
    "promo-agent",
    "proto-sketch-agent",
    "tracking-agent",
    "AI中台-规范及帮助文档",
    "references",
}
SKIP_DIRS = {"zips"}

# aihub_tool.py 头部 docstring 里的 `version: 1.3.1`
_TOOL_VERSION = re.compile(r"^\s*version:\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$", re.MULTILINE)
# Agent 包里「改了就得重贴 OWUI」的文件
_AGENT_DEPLOY_FILES = ("system-prompt.md", "agent-model.json")


def parse_tool_version(text: str) -> str | None:
    """从 aihub_tool.py 正文提 `version: X.Y.Z`，取不到返回 None。"""
    m = _TOOL_VERSION.search(text)
    return m.group(1) if m else None


def stale_files(pkg_dir: Path, zip_path: Path) -> list[Path]:
    """包目录里比 zip 新的文件。zip 排除清单内的文件不算（对齐 _repack.sh 的 -x 参数）。"""
    if not zip_path.exists():
        return []
    zip_mtime = zip_path.stat().st_mtime
    out: list[Path] = []
    for p in pkg_dir.rglob("*"):
        if not p.is_file():
            continue
        if ("__pycache__" in p.parts or p.suffix == ".pyc"
                or p.name in (".DS_Store", "Thumbs.db", ".skillignore-secrets")):
            continue
        if p.stat().st_mtime > zip_mtime:
            out.append(p)
    return sorted(out)


def load_deployed(path: Path) -> dict[str, dict]:
    """读部署态登记表；不存在 / 解析失败 → 空表（第三层降级为「全部未登记」）。"""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data.get("packages", {}) if isinstance(data, dict) else {}


def _newest_mtime(pkg_dir: Path, names: tuple[str, ...]) -> float | None:
    times = [(pkg_dir / n).stat().st_mtime for n in names if (pkg_dir / n).exists()]
    return max(times) if times else None


def deploy_drift(pkg_dir: Path, entry: dict | None) -> str | None:
    """返回部署态漂移的一句话描述；无漂移 / 无从判断 → None。

    Tool 包（有 aihub_tool.py）比版本号；Agent 包（有 agent-model.json）比改动日期；
    双形态包两者都查（tool 版本一致 / 缺登记不提前返回，继续查 agent 文件漂移）。
    """
    if entry is None:
        return None
    tool = pkg_dir / "aihub_tool.py"
    if tool.exists():
        local = parse_tool_version(tool.read_text(encoding="utf-8", errors="replace"))
        remote = str(entry.get("version", "")).lstrip("v")
        if local and remote and local != remote:
            return f"本地 aihub_tool v{local} ≠ OWUI 已部署 v{remote}（{entry.get('deployed_at', '?')}）"
    if (pkg_dir / "agent-model.json").exists():
        raw = entry.get("deployed_at")
        if not raw:
            return None
        try:
            deployed_on = datetime.strptime(str(raw), "%Y-%m-%d").date()
        except ValueError:
            return None
        newest = _newest_mtime(pkg_dir, _AGENT_DEPLOY_FILES)
        if newest is None:
            return None
        changed_on = date.fromtimestamp(newest)
        if changed_on > deployed_on:
            return f"system-prompt / agent-model {changed_on} 改过，晚于登记的部署日 {raw}（需重贴 OWUI 生效）"
    return None


def check(hub_dir: Path) -> dict:
    """扫全 hub，返回 {red: [...], yellow: [...], unregistered: [...], ok: [...]}。"""
    deployed = load_deployed(hub_dir / "deployed.json")
    red: list[dict] = []
    yellow: list[dict] = []
    unregistered: list[str] = []
    registered: list[str] = []
    green: list[str] = []

    for pkg in sorted(p for p in hub_dir.iterdir() if p.is_dir()):
        name = pkg.name
        if name in SKIP_DIRS or name.startswith((".", "__")):
            continue

        if name not in EXEMPT_NO_ZIP:
            zip_path = hub_dir / "zips" / f"{name}.zip"
            if not zip_path.exists():
                yellow.append({"pkg": name, "kind": "zip-missing",
                               "msg": f"无 zips/{name}.zip —— 该打包，或加进 EXEMPT_NO_ZIP 登记豁免"})
            else:
                stale = stale_files(pkg, zip_path)
                if stale:
                    rel = [str(p.relative_to(pkg)) for p in stale[:5]]
                    more = f" 等 {len(stale)} 个" if len(stale) > 5 else ""
                    red.append({"pkg": name, "kind": "zip-stale", "count": len(stale),
                                "msg": f"{', '.join(rel)}{more} 比 zip 新 —— 跑 bash hub/_repack.sh {name}"})
                else:
                    green.append(name)

        entry = deployed.get(name)
        if entry is None:
            if (pkg / "aihub_tool.py").exists() or (pkg / "agent-model.json").exists():
                unregistered.append(name)
            continue
        registered.append(name)
        drift = deploy_drift(pkg, entry)
        if drift:
            yellow.append({"pkg": name, "kind": "deploy-drift", "msg": drift})

    return {"red": red, "yellow": yellow, "unregistered": unregistered,
            "registered": registered, "ok": green}


def report(result: dict) -> None:
    red, yellow, unreg, green = result["red"], result["yellow"], result["unregistered"], result["ok"]
    reg = result.get("registered", [])

    if red:
        print(f"🔴 第一层 · zip 过期（{len(red)}）—— 发出去的是旧版，必须重打：")
        for r in red:
            print(f"  ❌ {r['pkg']}：{r['msg']}")
    else:
        print(f"🟢 第一层 · zip 新鲜度：{len(green)} 个包的 zip 均不比源码旧")

    zip_missing = [y for y in yellow if y["kind"] == "zip-missing"]
    drift = [y for y in yellow if y["kind"] == "deploy-drift"]

    if zip_missing:
        print(f"\n🟡 第二层 · zip 缺失（{len(zip_missing)}）：")
        for y in zip_missing:
            print(f"  · {y['pkg']}：{y['msg']}")
    else:
        print("🟢 第二层 · zip 缺失：无（未豁免的包都有 zip）")

    if drift:
        print(f"\n🟡 第三层 · 部署态漂移（{len(drift)}）—— 本地领先 OWUI，同事用的还是旧的：")
        for y in drift:
            print(f"  · {y['pkg']}：{y['msg']}")
    elif not reg:
        # 登记表空时「无漂移」恒真 —— 报绿等于谎称已核对，覆盖率为 0 必须显式说结论不可用
        print(f"\n🟡 第三层 · 部署态漂移：登记覆盖率 0/{len(unreg)}，本层结论不可用"
              "（hub/deployed.json 的 packages 为空，无从比对）")
    else:
        print(f"🟢 第三层 · 部署态漂移：已登记的 {len(reg)}/{len(reg) + len(unreg)} 个包"
              "本地与 OWUI 一致")

    if unreg:
        print(f"\n🟡 未登记部署态（{len(unreg)}）—— 在 hub/deployed.json 补一行才能查漂移：")
        print(f"  · {', '.join(unreg)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="hub 分发物新鲜度校验")
    ap.add_argument("--strict", action="store_true", help="有红灯（zip 过期）时 exit 2")
    args = ap.parse_args()

    hub_dir = find_root() / "hub"
    if not hub_dir.is_dir():
        print("⚠ 无 hub/ 目录，skip")
        return 0

    result = check(hub_dir)
    report(result)
    return 2 if (args.strict and result["red"]) else 0


if __name__ == "__main__":
    sys.exit(main())
