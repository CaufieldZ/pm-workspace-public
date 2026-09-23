#!/usr/bin/env python3
"""查中转站账户余额 —— user-prompt-warn.sh 报金额时附一行「余额 ¥X」；也可手动跑。

用法：
    python3 scripts/relay_balance.py --provider packyapi            # 一行机器格式：<余额¥> <是否偏低 0/1>
    python3 scripts/relay_balance.py --provider packyapi --verbose  # 人读模式（余额 / 已用 / 请求数 / 取自哪）
    python3 scripts/relay_balance.py --provider packyapi --timeout 2

契约（hook 按这个解析，改动即破坏调用方）：
    stdout 恰好一行 `<余额> <low>`；余额形如 `12` / `12.34`（可带负号，欠费即负）。
    拿不到就非 0 退出且不输出——调用方据「有没有输出」决定省掉这段，不需要看懂错误。
    low = 余额 < 配置 balance.warn_below（默认 30）；「偏低」只换提示里的措辞，不换退出码。

取数：GET `<base_url>/api/user/self`。两个头缺一不可——`Authorization: Bearer <token>` 与
    `New-Api-User: <uid>`（中转站缺后者直接 401，实测）；`quota` ÷ `quota_per_unit` = ¥。

配置：`.claude/hooks/cost-config.json`（`PMWS_COST_CONFIG` 覆盖）的 `providers.<名>`
    —— base_url / token / uid / quota_per_unit；凭据只写 `${VAR}` 引用，值本体在根目录 .env
    （经 scripts/lib/env_refs.py 灌进环境，明文不进配置）。「偏低」阈值在同文件 balance 块。

退出码：0 取到余额 / 1 取不到（没配置 / 令牌失效 / 网络失败 / 返回不合契约）
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from lib.env_refs import apply_env_file, expand_refs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / ".claude" / "hooks" / "cost-config.json"
DEFAULT_TIMEOUT = 6.0
DEFAULT_WARN_BELOW = 30.0
DEFAULT_QUOTA_PER_UNIT = 500000


def load_provider(name: str) -> tuple[dict, dict]:
    """读配置 → (provider 段, 整个配置)。缺配置 / 缺该通道都抛 ValueError。"""
    path = Path(os.environ.get("PMWS_COST_CONFIG") or DEFAULT_CONFIG)
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"配置读不出（{path}）：{e}") from e
    prov = (cfg.get("providers") or {}).get(name)
    if not isinstance(prov, dict):
        raise ValueError(f"配置里没有 providers.{name}")
    apply_env_file(ROOT / ".env")
    prov = expand_refs(prov, warn=False)
    for key in ("token", "uid"):
        if not prov.get(key) or str(prov[key]).startswith("${"):
            raise ValueError(f"providers.{name}.{key} 没解析出值——检查根目录 .env 里的变量名")
    return prov, cfg


def fetch(prov: dict, timeout: float) -> dict:
    url = str(prov.get("base_url") or "").rstrip("/") + "/api/user/self"
    if not url.startswith("http"):
        raise ValueError(f"providers 缺 base_url（拿到 {prov.get('base_url')!r}）")
    req = urllib.request.Request(url, headers={
        "User-Agent": "pm-workspace/1.0",
        "Accept": "application/json",
        "Authorization": f"Bearer {prov['token']}",
        "New-Api-User": str(prov["uid"]),
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            doc = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        raise ValueError(f"站点拒绝（HTTP {e.code}）——检查 .env 里的令牌是否还有效") from e
    except Exception as e:
        raise ValueError(f"取不到余额：{str(e)[:120]}") from e
    data = doc.get("data") or {}
    if data.get("quota") is None:
        raise ValueError(f"返回里没有 quota（success={doc.get('success')!r}）")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="查中转站账户余额（给 hook 的一行机器格式）")
    ap.add_argument("--provider", required=True, help="cost-config.json 里 providers 下的条目名")
    ap.add_argument("--timeout", type=float,
                    default=float(os.environ.get("RELAY_HTTP_TIMEOUT") or DEFAULT_TIMEOUT),
                    help=f"秒（默认 RELAY_HTTP_TIMEOUT 或 {DEFAULT_TIMEOUT}）")
    ap.add_argument("--verbose", action="store_true", help="人读模式（多行）")
    args = ap.parse_args()

    try:
        prov, cfg = load_provider(args.provider)
        data = fetch(prov, args.timeout)
    except ValueError as e:
        print(f"relay_balance: {e}", file=sys.stderr)
        return 1

    per_unit = float(prov.get("quota_per_unit") or DEFAULT_QUOTA_PER_UNIT)
    yuan = int(data["quota"]) / per_unit
    used = int(data.get("used_quota") or 0) / per_unit
    warn_below = float((cfg.get("balance") or {}).get("warn_below") or DEFAULT_WARN_BELOW)
    low = 1 if yuan < warn_below else 0

    if args.verbose:
        print(f"账户：{data.get('username')}（id {data.get('id')}）")
        print(f"余额：¥{yuan:.2f}（阈值 ¥{warn_below:.0f}{'，偏低' if low else ''}）")
        print(f"已用：¥{used:.2f} · 请求数 {data.get('request_count')}")
        print(f"取自：{str(prov.get('base_url')).rstrip('/')}/api/user/self")
    else:
        print(f"{yuan:.2f} {low}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
