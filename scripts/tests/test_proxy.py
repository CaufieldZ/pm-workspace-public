"""lib/proxy.py 的纯函数与环境变量处理。不真连网络、不依赖本机代理开关。

判定顺序里凡是要探口的部分都用 monkeypatch 换掉：断言「探到什么口会得出什么结论」，
而不是断言本机此刻恰好有没有代理在跑（那种测试换台机器就红）。
"""
import os
import socket

import pytest

from lib import proxy

ALL_VARS = proxy.PROXY_ENV_VARS
NO_PROXY_VARS = ("NO_PROXY", "no_proxy", "PROXY_FORCE")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """每个用例从干净的代理环境出发，跑完自动还原。"""
    for var in ALL_VARS + NO_PROXY_VARS:
        monkeypatch.delenv(var, raising=False)
    proxy.clear_cache()
    yield
    proxy.clear_cache()


# ---------------------------------------------------------------- _endpoint / _is_loopback

@pytest.mark.parametrize("url,expected", [
    ("http://本地代理端口", ("127.0.0.1", 7897)),
    ("本地代理端口", ("127.0.0.1", 7897)),          # 不带 scheme 也要认
    ("socks5h://127.0.0.1:7891", ("127.0.0.1", 7891)),
    ("http://[::1]:7897", ("::1", 7897)),
    ("http://localhost:7897", ("localhost", 7897)),
    ("http://10.0.0.1:8080", ("10.0.0.1", 8080)),
    ("http://127.0.0.1", ("127.0.0.1", 80)),          # 缺端口 → 按 scheme 默认
    ("https://127.0.0.1", ("127.0.0.1", 443)),
    ("", None),
    ("http://:7897", None),                            # 没主机
    ("http://127.0.0.1:abc", None),                    # 端口不是数字
])
def test_endpoint(url, expected):
    assert proxy._endpoint(url) == expected


@pytest.mark.parametrize("url,expected", [
    ("http://本地代理端口", True),
    ("127.5.5.5:3128", True),          # 整个 127/8 都是环回，不只是 127.0.0.1
    ("http://localhost:7897", True),
    ("http://[::1]:7897", True),
    ("http://10.0.0.1:8080", False),
    ("http://proxy.corp.example:8080", False),
    ("", False),
])
def test_is_loopback(url, expected):
    assert proxy._is_loopback(url) is expected


# ---------------------------------------------------------------- _pick_port

def test_pick_port_prefers_mixed():
    text = "mixed-port: 7897\nport: 7899\nsocks-port: 7898\n"
    assert proxy._pick_port(text) == 7897


def test_pick_port_falls_back_to_http_port():
    text = "port: 7899\nsocks-port: 7898\n"
    assert proxy._pick_port(text) == 7899


def test_pick_port_ignores_socks_port():
    """socks 口给不出 http:// URL，而且 urllib 根本不支持 socks——不能当出口代理。"""
    assert proxy._pick_port("socks-port: 7898\n") is None


def test_pick_port_ignores_other_scalars():
    text = "external-controller: 127.0.0.1:9097\nsecret: ''\nmode: rule\n"
    assert proxy._pick_port(text) is None


def test_pick_port_handles_quoted_and_crlf():
    assert proxy._pick_port("mixed-port: '7897'\r\n") == 7897


def test_pick_port_handles_inline_comment():
    """行尾注释很常见，别因为它漏读端口。"""
    assert proxy._pick_port("mixed-port: 7897   # 混合口\n") == 7897


def test_pick_port_on_verge_like_config():
    """贴近真实 Verge config.yaml 的形态：三个口并列时取混合口。"""
    text = (
        "mixed-port: 7897\n"
        "socks-port: 7898\n"
        "port: 7899\n"
        "external-controller: 127.0.0.1:9097\n"
        "external-controller-unix: /tmp/verge/verge-mihomo.sock\n"
    )
    assert proxy._pick_port(text) == 7897


# ---------------------------------------------------------------- 判定顺序

def test_env_non_loopback_trusted_without_probe(monkeypatch):
    """非环回是远程代理，本地探不着也验不准 → 直接采信。"""
    monkeypatch.setenv("ALL_PROXY", "http://10.0.0.1:8080")
    assert proxy.proxy_url() == "http://10.0.0.1:8080"


def test_env_loopback_dead_is_discarded(monkeypatch):
    """残留的死环回代理必须被丢掉，继续往下判——这正是境外场景的常见形态。"""
    monkeypatch.setenv("ALL_PROXY", "http://本地代理端口")
    monkeypatch.setattr(proxy, "_probe", lambda *a, **k: False)
    monkeypatch.setattr(proxy, "_config_ports", lambda: [])
    assert proxy.proxy_url() is None
    assert "未发现" in proxy.describe()


def test_env_loopback_alive_is_used(monkeypatch):
    monkeypatch.setenv("ALL_PROXY", "http://本地代理端口")
    monkeypatch.setattr(proxy, "_probe", lambda host, port, *a, **k: port == 7897)
    assert proxy.proxy_url() == "http://本地代理端口"


def test_config_port_requires_live_probe(monkeypatch):
    """配置文件是生成物不是活状态：代理关掉之后它照样写着 mixed-port。

    少了探口这一步，这里会返回一个没人监听的代理——比不判定更糟。
    """
    monkeypatch.setattr(proxy, "_config_ports", lambda: [(7897, "Clash Verge config.yaml")])
    monkeypatch.setattr(proxy, "_probe", lambda *a, **k: False)
    assert proxy.proxy_url() is None


def test_config_port_used_when_alive(monkeypatch):
    monkeypatch.setattr(proxy, "_config_ports", lambda: [(7897, "Clash Verge config.yaml")])
    monkeypatch.setattr(proxy, "_probe", lambda host, port, *a, **k: port == 7897)
    assert proxy.proxy_url() == "http://本地代理端口"
    assert "config.yaml" in proxy.describe()


def test_fallback_ports_when_nothing_known(monkeypatch):
    monkeypatch.setattr(proxy, "_config_ports", lambda: [])
    monkeypatch.setattr(proxy, "_probe", lambda host, port, *a, **k: port == proxy.FALLBACK_PORTS[0])
    url = proxy.proxy_url()
    assert url == f"http://127.0.0.1:{proxy.FALLBACK_PORTS[0]}"
    assert "兜底" in proxy.describe()


def test_config_ports_read_before_fallback(monkeypatch):
    """自定义端口只在第 2 步能读到——兜底端口表里没有它，顺序不能颠倒。"""
    monkeypatch.setattr(proxy, "_config_ports", lambda: [(7899, "Clash Verge config.yaml")])
    monkeypatch.setattr(proxy, "_probe", lambda host, port, *a, **k: port == 7899)
    assert proxy.proxy_url() == "http://127.0.0.1:7899"


def test_force_direct_short_circuits_everything(monkeypatch):
    monkeypatch.setenv("PROXY_FORCE", "direct")
    monkeypatch.setenv("ALL_PROXY", "http://10.0.0.1:8080")
    monkeypatch.setattr(proxy, "_probe", lambda *a, **k: True)
    assert proxy.proxy_url() is None


def test_no_proxy_star_forces_direct(monkeypatch):
    monkeypatch.setenv("NO_PROXY", "*")
    monkeypatch.setattr(proxy, "_probe", lambda *a, **k: True)
    assert proxy.proxy_url() is None


def test_cache_reused_and_force_reprobes(monkeypatch):
    calls = []

    def fake_probe(*a, **k):
        calls.append(a)
        return False

    monkeypatch.setattr(proxy, "_config_ports", lambda: [])
    monkeypatch.setattr(proxy, "_probe", fake_probe)

    proxy.proxy_url()
    n = len(calls)
    proxy.proxy_url()                       # 吃缓存
    assert len(calls) == n
    proxy.proxy_url(force=True)             # 强制重探
    assert len(calls) > n


def test_describe_reuses_cached_detection(monkeypatch):
    """describe() 不能为了拿 source 再探一遍。"""
    calls = []

    def fake_probe(*a, **k):
        calls.append(a)
        return False

    monkeypatch.setattr(proxy, "_config_ports", lambda: [])
    monkeypatch.setattr(proxy, "_probe", fake_probe)

    proxy.proxy_url()
    n = len(calls)
    proxy.describe()
    assert len(calls) == n


# ---------------------------------------------------------------- apply_env

def test_apply_env_sets_all_variants_and_no_proxy(monkeypatch):
    monkeypatch.setenv("ALL_PROXY", "http://10.0.0.1:8080")
    assert proxy.apply_env() == "http://10.0.0.1:8080"
    # urllib 的 getproxies_environment() 只把 *_proxy 转成键，ALL_PROXY 对应的 'all'
    # 键永不派发 —— 所以 http/https 两个变量必须一并给足
    assert os.environ["HTTP_PROXY"] == "http://10.0.0.1:8080"
    assert os.environ["https_proxy"] == "http://10.0.0.1:8080"
    # 不给 NO_PROXY，urllib 会把环回上的本机服务也一并塞进代理
    assert "127.0.0.1" in os.environ["NO_PROXY"]
    assert urllib_bypasses_loopback()


def test_apply_env_keeps_existing_no_proxy_entries(monkeypatch):
    monkeypatch.setenv("NO_PROXY", "example.com")
    monkeypatch.setenv("ALL_PROXY", "http://10.0.0.1:8080")
    proxy.apply_env()
    assert os.environ["NO_PROXY"].startswith("example.com,")


def test_apply_env_clears_dead_loopback_vars(monkeypatch):
    """判定为直连时，残留的死环回变量必须从进程里删掉，否则 httpx/urllib 照样撞上去。"""
    monkeypatch.setenv("ALL_PROXY", "http://本地代理端口")
    monkeypatch.setenv("http_proxy", "http://本地代理端口")
    monkeypatch.setattr(proxy, "_probe", lambda *a, **k: False)
    monkeypatch.setattr(proxy, "_config_ports", lambda: [])

    assert proxy.apply_env() is None
    assert "ALL_PROXY" not in os.environ
    assert "http_proxy" not in os.environ


def test_apply_env_leaves_non_loopback_alone_when_direct(monkeypatch):
    """非环回是用户的显式意图，判定为直连也不许动它。"""
    monkeypatch.setenv("PROXY_FORCE", "direct")
    monkeypatch.setenv("ALL_PROXY", "http://10.0.0.1:8080")
    proxy.apply_env()
    assert os.environ["ALL_PROXY"] == "http://10.0.0.1:8080"


# ---------------------------------------------------------------- shell_prefix / proxies

def test_shell_prefix_none_without_proxy(monkeypatch):
    monkeypatch.setenv("PROXY_FORCE", "direct")
    assert proxy.shell_prefix() is None
    assert proxy.proxies() == {}


def test_shell_prefix_shape(monkeypatch):
    monkeypatch.setenv("ALL_PROXY", "http://10.0.0.1:8080")
    prefix = proxy.shell_prefix()
    assert prefix.startswith("export ")
    assert prefix.endswith(";")
    for var in ("ALL_PROXY=", "HTTP_PROXY=", "HTTPS_PROXY=", "NO_PROXY="):
        assert var in prefix


def test_proxies_only_http_and_https(monkeypatch):
    """不给 'all' 键：urllib 对它的处理是永不派发，给了只会让人误以为生效。"""
    monkeypatch.setenv("ALL_PROXY", "http://10.0.0.1:8080")
    assert set(proxy.proxies()) == {"http", "https"}


# ---------------------------------------------------------------- _probe 本体

def test_probe_true_for_listening_socket():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    try:
        assert proxy._probe("127.0.0.1", s.getsockname()[1]) is True
    finally:
        s.close()


def test_probe_false_for_closed_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()                                # 关掉 → 该口现在没人听
    assert proxy._probe("127.0.0.1", port) is False


def urllib_bypasses_loopback() -> bool:
    """注入的 NO_PROXY 是否真的让 urllib 放过环回（本机 webapp / 控制口的保命符）。"""
    import urllib.request
    return urllib.request.proxy_bypass("127.0.0.1")
