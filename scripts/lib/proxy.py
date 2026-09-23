"""当前环境有没有代理、在哪个口——工区唯一判定源。

调用方：
- .claude/hooks/pre-proxy-check.sh（从仓根注入 sys.path 后 import lib.proxy）
- scripts/net_retry.sh、scripts/upscale.py、scripts/pack_for_opus.py
- .claude/skills/data-report/scripts/fetch_market_context.py
- .claude/skills/promo-kit/scripts/wp_publish.py

用法：
    python3 scripts/lib/proxy.py --describe        # 人话结论 + 依据（默认行为）
    python3 scripts/lib/proxy.py --url             # 只打印代理 URL（无代理打印空行）
    eval "$(python3 scripts/lib/proxy.py --export)"  # 给当前 shell 挂上代理（或清残留）
    python3 scripts/lib/proxy.py --json            # {"proxy": …, "source": …}

前置：无（只读本机代理配置与环境变量；`--help` 本身不探测）。

退出码：
    0 — 判定完成。「判不出来」也是 0，结论是「直连」（见判定顺序第 4 步）。

判定必须是**运行时**的：把「外网一律走某个本机端口」当默认前提写死，只在「人在大陆 + 代理在跑」
时成立；人在境外时那是一个没人监听的死口，会把本来直连能通的请求弄失败。判定只有这一处，
判不出来就直连。

判定顺序（每一步都实测过，别按直觉改）：

  0. PROXY_FORCE=direct|<url> 逃生口；NO_PROXY 含 * → 直连
  1. 环境变量（ALL_PROXY/all_proxy/HTTPS_PROXY/https_proxy/HTTP_PROXY/http_proxy）
     非环回 → 直接采信（远程代理，本地探不着也验不准）
     环回   → **探口验活**；不通即残留配置，丢弃后继续往下
  2. Clash Verge config.yaml / verge.yaml 的 mixed-port（回落 port，**忽略 socks-port**）
     → **探口验活后才采信**
  3. 兜底端口 7897 → 7890
  4. 全不通 → None（境外 / 直连环境）

第 1 步「环回也验活」与第 2 步「先探口再采信」是整套逻辑的要害：**config.yaml 是生成物，
不是活状态**——代理关掉之后它照样写着 mixed-port: 7897。少了探口，境外会判定出一个没人
监听的代理，比不判定更糟。

不做跨进程缓存：省下的只有零点几毫秒，而缓存失效的方向恰好命中这套逻辑要消灭的两类故障——
缓存了活端口而代理退出 → 注入死代理；缓存了 None 而代理起来 → 漏注入。代理开关是随手点的、
无预告，正是最不该缓存的状态。进程内缓存 + force= 足够。
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
import shlex
import socket
import sys
import urllib.parse
from pathlib import Path

# argparse 故意留到 main() 里 import：hook 每次命中都要 import 本模块，而 argparse
# 是这里最重的一个（约 10ms），探测路径上一行都用不到。

# 判定顺序即优先级：ALL_PROXY 在前只是惯例，任一命中即返回
PROXY_ENV_VARS = (
    "ALL_PROXY", "all_proxy",
    "HTTPS_PROXY", "https_proxy",
    "HTTP_PROXY", "http_proxy",
)

# 探口超时必须小：Windows 上被 Hyper-V / WSL 保留的动态端口段可能不是 RST 而是静默丢包，
# 超时大了会拖死每次命中的 hook。环回正常路径是 RST，0.1ms 级返回。
PROBE_TIMEOUT = 0.25

# 兜底端口只留 Clash 的两个默认口。再往下列（1080 / 6152）就没意义了：探口只能证明
# 「有东西在听」，证明不了「那是 HTTP 代理」，而 1080 恰恰是最常见的 SOCKS 口——
# 给不出 http:// URL，urllib 也不支持 socks。
FALLBACK_PORTS = (7897, 7890)

# 注入代理时必须一起 bypass 的本地地址：本机 webapp 与代理控制口都走 urllib，
# 而 urllib 默认**不** bypass 环回（实测 proxy_bypass("127.0.0.1") == False，
# 不加 NO_PROXY 就会被塞进代理）。
BYPASS_HOSTS = ("localhost", "127.0.0.1", "::1")

_UNSET = object()
_cache: object = _UNSET  # (url, source) 或 _UNSET


# ---------------------------------------------------------------- 基础工具

def _endpoint(url: str) -> tuple[str, int] | None:
    """'http://本地代理端口' / '本地代理端口' → ('127.0.0.1', 7897)。解析不出来返回 None。"""
    spec = url if "://" in url else "http://" + url
    try:
        u = urllib.parse.urlparse(spec)
    except ValueError:
        return None
    host = (u.hostname or "").strip()
    if not host:
        return None
    try:
        port = u.port
    except ValueError:      # 端口不是数字，如 http://host:abc
        return None
    if port is None:
        port = {"http": 80, "https": 443}.get(u.scheme, 0)
    return (host, port) if port else None


def _is_loopback(url: str) -> bool:
    """指向本机的代理地址。用 ipaddress 判，覆盖整个 127/8 与 ::1。"""
    ep = _endpoint(url)
    if not ep:
        return False
    host = ep[0]
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _probe(host: str, port: int, timeout: float = PROBE_TIMEOUT) -> bool:
    """本机 host:port 有没有在监听。用 connect_ex 而非 connect：拒绝连接不抛异常。"""
    s = socket.socket()
    s.settimeout(timeout)
    try:
        return s.connect_ex((host, port)) == 0
    except OSError:
        return False
    finally:
        s.close()


def _coerce_port(value: object) -> int | None:
    try:
        port = int(str(value).strip().strip("'\""))
    except (TypeError, ValueError):
        return None
    return port if 0 < port < 65536 else None


# 标量行 `key: value`。行尾不收锚——配置里常跟行内注释（`mixed-port: 7897 # 混合口`）。
# 注释行以 # 开头，天然不会命中。
_RE_SCALAR = re.compile(r"^\s*([A-Za-z][\w-]*)\s*:\s*(\S+)", re.MULTILINE)


def _pick_port(text: str) -> int | None:
    """从代理配置文本里取出口端口：混合口优先，其次 HTTP 口。

    **不取 socks-port**：它给不出 http:// URL，urllib 也不支持 socks。
    """
    found: dict[str, str] = {}
    for m in _RE_SCALAR.finditer(text):
        found.setdefault(m.group(1), m.group(2))
    for key in ("mixed-port", "port"):
        port = _coerce_port(found.get(key))
        if port:
            return port
    return None


def _verge_dirs() -> list[Path]:
    """Clash Verge Rev 配置目录候选（版本间在 APPDATA / LOCALAPPDATA 间迁移过）。"""
    home = Path.home()
    if sys.platform == "win32":
        bases = [os.environ.get("APPDATA"), os.environ.get("LOCALAPPDATA")]
        return [Path(b) / "io.github.clash-verge-rev.clash-verge-rev" for b in bases if b]
    if sys.platform == "darwin":
        return [home / "Library/Application Support/io.github.clash-verge-rev.clash-verge-rev"]
    return [home / ".config/io.github.clash-verge-rev.clash-verge-rev",
            home / ".local/share/io.github.clash-verge-rev.clash-verge-rev"]


def _config_ports() -> list[tuple[int, str]]:
    """配置目录里的候选端口。读不到就返回空表（不当成错误）。"""
    out: list[tuple[int, str]] = []
    for d in _verge_dirs():
        for name in ("config.yaml", "verge.yaml"):
            f = d / name
            if not f.is_file():
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            port = _pick_port(text)
            if port:
                out.append((port, f"Clash Verge {name}"))
    return out


# ---------------------------------------------------------------- 判定

def _detect() -> tuple[str | None, str]:
    forced = os.environ.get("PROXY_FORCE", "").strip()
    if forced:
        if forced.lower() in ("direct", "none", "off"):
            return None, "PROXY_FORCE=direct"
        return forced, "PROXY_FORCE"

    if any(v.strip() == "*" for v in _no_proxy_values()):
        return None, "NO_PROXY=*"

    for var in PROXY_ENV_VARS:
        raw = os.environ.get(var, "").strip()
        if not raw:
            continue
        if not _is_loopback(raw):
            return raw, f"环境变量 {var}"
        ep = _endpoint(raw)
        if ep and _probe(*ep):
            return raw, f"环境变量 {var}（本机 {ep[0]}:{ep[1]} 在听）"
        # 环回但不通 = 残留配置，继续往下找

    for port, src in _config_ports():
        if _probe("127.0.0.1", port):
            return f"http://127.0.0.1:{port}", src

    for port in FALLBACK_PORTS:
        if _probe("127.0.0.1", port):
            return f"http://127.0.0.1:{port}", "端口兜底"

    return None, "未发现本机代理"


def _resolve(force: bool = False) -> tuple[str | None, str]:
    """缓存 (url, source)。哨兵区分「算过，结果是 None」与「没算过」——
    少了它，None 结果会被反复重探，且 force=True 落不了地。"""
    global _cache
    if force or _cache is _UNSET:
        _cache = _detect()
    return _cache  # type: ignore[return-value]


def clear_cache() -> None:
    global _cache
    _cache = _UNSET


# ---------------------------------------------------------------- 对外接口

def proxy_url(*, force: bool = False) -> str | None:
    """可用的本机代理 URL；没有就 None（直连）。判定唯一入口。"""
    return _resolve(force)[0]


def describe(*, force: bool = False) -> str:
    """人话结论 + 依据，给排查与报错文案用。"""
    url, source = _resolve(force)
    return f"经 {url}（{source}）" if url else f"直连（{source}）"


def proxies(*, force: bool = False) -> dict[str, str]:
    """给 urllib ProxyHandler 用。只给 http/https 两个键——ALL_PROXY 对应的 'all'
    键在 urllib 里永不派发（实测 ProxyHandler.proxies == {'all': …} 而请求照走直连）。"""
    url = proxy_url(force=force)
    return {"http": url, "https": url} if url else {}


def _no_proxy_values() -> list[str]:
    return [os.environ.get(v, "") for v in ("NO_PROXY", "no_proxy")]


def merged_no_proxy() -> str:
    """已有 NO_PROXY 与必须 bypass 的本地地址合并（去重、保序）。"""
    parts: list[str] = []
    for raw in _no_proxy_values():
        parts.extend(p.strip() for p in raw.split(",") if p.strip())
    for host in BYPASS_HOSTS:
        if host not in parts:
            parts.append(host)
    return ",".join(parts)


def apply_env(*, force: bool = False) -> str | None:
    """把判定结果写进 os.environ，并清掉指向环回死口的残留代理变量。

    清理这半步不能省：shell 里常留着 `export ALL_PROXY=…:7897`，代理没在跑时它被判为残留，
    但**变量本身还在**——不删掉，同进程里的 httpx / urllib 照样往上撞，等于没判定。
    非环回变量是用户的显式意图，一律不动。

    返回最终生效的代理 URL（None = 直连）。
    """
    url, _source = _resolve(force)

    for var in PROXY_ENV_VARS:
        cur = os.environ.get(var, "").strip()
        if not url:
            # 判定为直连：死环回变量留着只会让 httpx / urllib 继续往上撞
            if cur and _is_loopback(cur):
                os.environ.pop(var, None)
        elif not cur or (_is_loopback(cur) and cur != url):
            # 补齐 / 替换。**必须补齐**：只给 ALL_PROXY 时 urllib 完全不走代理
            # （'all' 键永不派发），同进程里 urllib 类调用会静默直连。
            # 不动用户另外设的、活的非环回变量——那是显式意图，可能是另一条链路的代理。
            os.environ[var] = url

    if url:
        merged = merged_no_proxy()
        os.environ["NO_PROXY"] = merged
        os.environ["no_proxy"] = merged
    return url


def shell_prefix(*, force: bool = False) -> str | None:
    """给 bash 命令用的一行前置：`export A=… B=…;`。无代理返回 None。

    只导出 4 个变量。urllib 的 getproxies_environment() 会把变量名转小写再取键，
    所以大写 HTTP_PROXY / HTTPS_PROXY 对它同样有效；ALL_PROXY 是给 curl / httpx 的
    （urllib 忽略它：'all' 键永不派发）。NO_PROXY 必带，否则本机 webapp / 控制口会被塞进代理。
    """
    url = proxy_url(force=force)
    if not url:
        return None
    pairs = [
        ("ALL_PROXY", url),
        ("HTTP_PROXY", url),
        ("HTTPS_PROXY", url),
        ("NO_PROXY", merged_no_proxy()),
    ]
    return "export " + " ".join(f"{k}={shlex.quote(v)}" for k, v in pairs) + ";"


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="判定当前环境要不要走本机代理（工区唯一判定源）。默认打印人话结论。",
        epilog='示例：\n'
               '  python3 scripts/lib/proxy.py --describe\n'
               '  eval "$(python3 scripts/lib/proxy.py --export)"\n'
               '  PROXY_FORCE=direct python3 scripts/lib/proxy.py --url',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--describe", action="store_true", help="人话结论 + 依据（默认行为）")
    group.add_argument("--url", action="store_true", help="只打印代理 URL（无代理打印空行）")
    group.add_argument("--export", action="store_true",
                       help="打印可直接 eval 的 export / unset 行")
    group.add_argument("--json", action="store_true", help="打印 {proxy, source}")
    group.add_argument("--prefix", action="store_true", help="打印 bash 命令前置（export …;），无代理打印空行")
    parser.add_argument("--force", action="store_true", help="忽略进程内缓存，重新探测（默认 false）")
    args = parser.parse_args(argv)

    url, source = _resolve(force=True)

    # 上面已经 force 过一次，后面全部吃缓存，别重复探测
    if args.url:
        print(url or "")
    elif args.prefix:
        print(shell_prefix() or "")
    elif args.export:
        print(shell_prefix() if url else "unset " + " ".join(PROXY_ENV_VARS))
    elif args.json:
        print(json.dumps({"proxy": url, "source": source}, ensure_ascii=False))
    else:
        print(describe())
    return 0


if __name__ == "__main__":
    sys.exit(main())
