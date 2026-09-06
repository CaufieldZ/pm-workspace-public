"""`.env` 加载 + `${VAR}` 引用展开。

MCP 配置（.mcp.json / .mcp-disabled.json）里的凭据值统一收敛到 `.env`，
配置只留 `${VAR}` 引用——密钥唯一值源，轮换密钥只改 .env 一处。
消费方（call_mcp.py / fetch_figma.py / probe_* / fetch_weekly_sensors.py）
读配置前先 apply_env_file 再 expand_refs。
"""

import os
import re
import sys

_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def apply_env_file(path, override=False):
    """把 .env 的 KEY=VALUE 灌进 os.environ；默认不覆盖已存在的变量。

    只认整行注释；值去首尾引号。重复调用幂等。
    """
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            if key and (override or key not in os.environ):
                os.environ[key] = value.strip().strip('"').strip("'")


def expand_refs(obj, warn=True):
    """递归把字符串值里的 ${VAR} 展开为 os.environ 值；变量缺失保留原样并警告。"""
    if isinstance(obj, dict):
        return {k: expand_refs(v, warn) for k, v in obj.items()}
    if isinstance(obj, list):
        return [expand_refs(x, warn) for x in obj]
    if isinstance(obj, str):
        def _sub(m):
            name = m.group(1)
            value = os.environ.get(name)
            if value is None:
                if warn:
                    print(f"警告：环境变量 {name} 未设置，{m.group(0)} 保持原样", file=sys.stderr)
                return m.group(0)
            return value
        return _REF_RE.sub(_sub, obj)
    return obj
