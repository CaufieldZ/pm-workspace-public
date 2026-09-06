#!/usr/bin/env python3
"""GA 自动登录（可选）：读 HX_GA_SECRET 算当前 TOTP 6 位码 → hx-cli auth login。

session 过期（错误码 40102）时手动跑一次本脚本，免去去 TOTP app 抄码。
seed 只从环境变量读，不硬编码、不进日志。纯标准库实现 TOTP（RFC 6238），无第三方依赖。

用法：
    source .env && python3 hx_login.py

前置：.env 写一行 HX_GA_SECRET=<auth ga bindreq 返回的 secret>。
安全权衡：seed 是永久密钥（拿到即等同账号），存 .env 即把 2FA 降级成单因素——
自己的风险决策。.env 已 gitignore 不进 git。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hx_client as hx  # noqa: E402


def _totp(secret: str, t: int | None = None) -> str:
    """RFC 6238 TOTP：base32 secret → 当前 30s 窗口的 6 位码。"""
    raw = secret.strip().replace(" ", "").upper()
    raw += "=" * (-len(raw) % 8)          # base32 padding 补齐到 8 的倍数
    key = base64.b32decode(raw)
    counter = (t if t is not None else int(time.time())) // 30
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return f"{binary % 1_000_000:06d}"


def main() -> int:
    secret = os.environ.get("HX_GA_SECRET", "").strip()
    if not secret:
        print(
            "未设 HX_GA_SECRET。在 .env 写一行：\n"
            "  HX_GA_SECRET=<auth ga bindreq 返回的 secret>\n"
            "然后 source .env 再跑本脚本。",
            file=sys.stderr,
        )
        return 2

    code = _totp(secret)
    remain = 30 - int(time.time()) % 30
    print(f"GA 码已生成（{remain}s 后刷新），正在登录…")

    try:
        data = hx.run(["auth", "login", "--ga-code", code])
    except hx.HxAuthError as e:
        print(f"认证失败：{e}\n下一步：{e.hint}", file=sys.stderr)
        return 2
    except hx.HxError as e:
        print(f"调用失败：{e}", file=sys.stderr)
        return 1

    sid = data.get("session_id") or data.get("domain_user") or ""
    print(f"登录成功，session 已续期（30min）{('— ' + str(sid)) if sid else ''}。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
