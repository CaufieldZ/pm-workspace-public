#!/usr/bin/env python3
"""Confluence REST 透传原语：任意端点直接调，不写专用脚本。

- endpoint：/rest/api/... 相对路径自动拼 base_url；完整 URL 须同源（异源 exit 2）
- body：--input（JSON 文件或 - 读 stdin）优先，其次 -f key=value 键值对
- --jq：迷你求值器（.a.b[0].c / .a[] 展开 / | length），不引外部 jq 依赖
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

from lib.confluence import base_url, request_raw


def normalize_endpoint(endpoint: str, base: str) -> str:
    """相对路径拼 base；绝对 URL 须同源（scheme+netloc 一致）。非法输入 raise ValueError。"""
    if endpoint.startswith(("http://", "https://")):
        e = urllib.parse.urlparse(endpoint)
        b = urllib.parse.urlparse(base)
        if (e.scheme, e.netloc) != (b.scheme, b.netloc):
            raise ValueError(f"异源 URL 拒绝：{endpoint}（base={base}）")
        return endpoint
    if endpoint.startswith("/"):
        return base + endpoint
    raise ValueError(f"endpoint 必须是 /rest/api/... 相对路径或同源完整 URL：{endpoint!r}")


def parse_kv_args(fields: list[str]) -> dict:
    """-f key=value 解析：value 尝试 JSON 字面量（数字/布尔/嵌套），失败保留字符串；
    dotted key（a.b=v）展开嵌套 dict（Confluence REST 常见 space.key / body.storage.value）。"""
    result: dict = {}
    for item in fields:
        if "=" not in item:
            raise ValueError(f"-f 参数必须是 key=value，收到: {item!r}")
        k, v = item.split("=", 1)
        try:
            v = json.loads(v)
        except json.JSONDecodeError:
            pass
        if "." in k:
            node = result
            parts = k.split(".")
            for p in parts[:-1]:
                if not isinstance(node.get(p), dict):
                    node[p] = {}
                node = node[p]
            node[parts[-1]] = v
        else:
            result[k] = v
    return result


def build_body(input_path: str | None, fields: list[str]) -> bytes | None:
    """body 组装：--input 优先于 -f 键值对，都没有返回 None。"""
    if input_path:
        if input_path == "-":
            return sys.stdin.buffer.read()
        return Path(input_path).read_bytes()
    if fields:
        return json.dumps(parse_kv_args(fields), ensure_ascii=False).encode("utf-8")
    return None


def _walk_path(current: object, segs: list[str]) -> object:
    """逐段走路径；[] 段对列表每个元素递归走剩余路径（map 语义，如 .results[].id）。"""
    if not segs:
        return current
    m = re.fullmatch(r"([^\[\]]*)(\[(\d*)\])?", segs[0])
    if not m:
        raise ValueError(f"无法解析路径段: {segs[0]!r}")
    key, _, idx = m.groups()
    if key:
        current = current[key]  # KeyError → 键不存在
    if idx == "":
        if not isinstance(current, list):
            raise ValueError("[] 只能用于列表")
        return [_walk_path(item, segs[1:]) for item in current]
    if idx:
        current = current[int(idx)]
    return _walk_path(current, segs[1:])


def evaluate_jq(expr: str, data) -> object:
    """迷你 jq 求值：.a.b[0].c（点路径+数字索引）、.a[]（展开列表）、`| length`。

    求值失败（键不存在 / 类型不符 / 非法表达式）raise KeyError/TypeError/ValueError。
    """
    if "|" in expr:
        base, pipe = expr.split("|", 1)
        result = evaluate_jq(base.strip(), data)
        if pipe.strip() == "length":
            return len(result)
        raise ValueError(f"仅支持 | length，收到: {pipe.strip()!r}")
    if not expr.startswith("."):
        raise ValueError(f"仅支持点路径表达式（如 .results[0].id），收到: {expr!r}")
    return _walk_path(data, [s for s in expr[1:].split(".") if s])


def _dump(item: object) -> str:
    if isinstance(item, (dict, list)):
        return json.dumps(item, ensure_ascii=False)
    return str(item)


def render_output(raw: bytes, jq: str | None, silent: bool) -> int:
    """输出：--jq 求值结果（列表逐行）> pretty JSON > 非 JSON 原文。失败 exit 2。"""
    text = raw.decode("utf-8", errors="replace")
    if jq:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            if not silent:
                sys.stderr.write("错误：--jq 需要 JSON 响应，但响应不是 JSON\n")
            return 2
        try:
            result = evaluate_jq(jq, data)
        except (KeyError, TypeError, ValueError) as e:
            if not silent:
                sys.stderr.write(f"错误：--jq 求值失败：{e}\n")
            return 2
        if isinstance(result, list):
            for item in result:
                print(_dump(item))
        else:
            print(_dump(result) if isinstance(result, (dict, list)) else result)
        return 0
    if not text:
        return 0
    try:
        print(json.dumps(json.loads(text), ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        sys.stdout.write(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="直接调 Confluence REST API（透传/调试/临时 CQL），凭据同 fetch_confluence",
        epilog="""示例：
  # 当前用户
  python3 confluence_api.py /rest/api/user/current --jq '.displayName'
  # CQL 搜页面取 ID 列表
  python3 confluence_api.py '/rest/api/content/search?cql=type=page+and+space=jituankejizhongxin&limit=5' --jq '.results[].id'
  # 带 body 的 POST（-f 值支持 JSON 字面量）
  python3 confluence_api.py /rest/api/content -X POST -f 'type=page' -f 'space.key=jituankejizhongxin' -f 'title=测试'
  # 从文件读 body（- 读 stdin）
  python3 confluence_api.py /rest/api/content -X PUT --input body.json""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("endpoint", help="/rest/api/... 相对路径或同源完整 URL")
    parser.add_argument("-X", "--method", default="GET", choices=["GET", "POST", "PUT", "DELETE"],
                        help="HTTP 方法（默认 GET）")
    parser.add_argument("-H", "--header", action="append", default=[], metavar="K: V",
                        help="额外请求头，可多次")
    parser.add_argument("-f", "--field", action="append", default=[], metavar="key=value",
                        help="body 键值对（值支持 JSON 字面量），可多次")
    parser.add_argument("--input", metavar="FILE", help="body 从文件读取（- 读 stdin），优先于 -f")
    parser.add_argument("--jq", metavar="EXPR", help="迷你 jq 过滤：.a.b[0] / .a[] / | length")
    parser.add_argument("-i", "--include", action="store_true", help="打印 HTTP 状态行与关键响应头")
    parser.add_argument("--silent", action="store_true", help="静默 stderr 输出")
    args = parser.parse_args(argv)

    try:
        endpoint = normalize_endpoint(args.endpoint, base_url())
    except ValueError as e:
        sys.stderr.write(f"错误：{e}\n")
        return 2

    headers = {}
    for h in args.header:
        k, _, v = h.partition(":")
        headers[k.strip()] = v.strip()

    try:
        body = build_body(args.input, args.field)
        if body is not None and "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
        status, resp_headers, raw = request_raw(args.method, endpoint, body, headers)
    except Exception as e:
        if not args.silent:
            sys.stderr.write(f"Confluence 请求失败 ({e})\n")
        return 2

    if args.include:
        sys.stderr.write(f"HTTP {status}\n")
        for h in ("content-type", "location", "etag"):
            v = resp_headers.get(h)
            if v:
                sys.stderr.write(f"{h}: {v}\n")
    return render_output(raw, args.jq, args.silent)


if __name__ == "__main__":
    sys.exit(main())
