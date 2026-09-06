#!/usr/bin/env python3
"""网易有数（YouData）报告下载 CLI

私有化部署适配 INTERNAL_DOMAIN_REDACTED `.env` 读
（`YOUSHU_BASE` / `YOUSHU_TOKEN_KEY`），token 缓存到 `.youshu_token_cache.json`
（已 gitignore 通过 .env 规则覆盖，单独再加防漏）。

子命令:
  list-reports                    列出有权限的所有报告
  search <关键词>                 在本地列表中过滤
  list-dashboards --report-id X   列报告下页面 ID
  export --report-id X            导出（指定格式）
  download <URL>                  贴 URL 自动解析 rid/did 导出
  async-export --report-id X --component-id Y   异步大导出（>2 万行组件）

导出格式（--format / --export-type）:
  crossTable  交叉表 xlsx（保留视觉样式；若报告中的表本身是一维表则导出也是一维）
  xlsx        一维表 xlsx（每行一条记录，适合二次处理）
  png         单页截图
  pdf         多页报告 PDF（自带分页页码）

crossTable / xlsx 时可附加 4 个布尔选项（对应网页导出弹窗）：
  --use-origin-data   true=保留原始数值（1234567）/ false=保留展示格式（"123万"）
  --enhance           true=带样式（蓝色表头）/ false=不带（推荐 false，体积小）
  --condition-format  true=保留数据/日期格式 / false=不保留（推荐 false）
  --include-title     true=表格上方插标题行（表头被挤到第二行）/ false=不插（推荐 false）

周报场景固定 4 个 component 走 .claude/skills/data-report/scripts/fetch_weekly_youshu.py，
本脚本是「临时下载任意报告」用，和周报互不干扰。
"""

from __future__ import annotations

import pathlib as _pl

# route-log: 调用埋点（scripts/lib/route_log.py）
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("youshu_cli"))

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
TOKEN_CACHE_FILE = ROOT / ".youshu_token_cache.json"
DEFAULT_OUTPUT_DIR = Path("~/Downloads/netease_download").expanduser()
DEFAULT_PROJECT_ID = 2  # Platform C项目
TOKEN_TTL = 7 * 86400


# ============================================================
# 配置加载（.env）
# ============================================================

def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    for k in ("YOUSHU_BASE", "YOUSHU_TOKEN_KEY"):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


def resolve_config(args) -> tuple[str, str, int]:
    env = load_env()
    base_url = args.base_url or env.get("YOUSHU_BASE")
    token_key = args.token_key or env.get("YOUSHU_TOKEN_KEY")
    project_id = args.project_id or DEFAULT_PROJECT_ID
    if not base_url:
        sys.exit("错误：未配置 YOUSHU_BASE（.env 或 --base-url）")
    return base_url.rstrip("/"), token_key or "", project_id


# ============================================================
# Token 管理
# ============================================================

def load_token_cache() -> dict:
    if not TOKEN_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(TOKEN_CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_token_cache(token: str, expire_ts: int) -> None:
    TOKEN_CACHE_FILE.write_text(
        json.dumps({"token": token, "expire_ts": expire_ts}, ensure_ascii=False),
        encoding="utf-8",
    )
    try:
        os.chmod(TOKEN_CACHE_FILE, 0o600)  # bearer token 明文落盘，收紧到仅本人可读写
    except OSError:
        pass  # Windows / 特殊 FS 不支持 POSIX 权限，忽略


def get_token(args) -> str:
    if args.token:
        return args.token

    base_url, token_key, _ = resolve_config(args)
    if not token_key:
        sys.exit("错误：未配置 YOUSHU_TOKEN_KEY（.env 或 --token-key）")

    cache = load_token_cache()
    # 距离过期 > 1 天才复用，避免 API 调用中途过期
    if cache.get("token") and cache.get("expire_ts", 0) - time.time() > 86400:
        return cache["token"]

    print("正在用 TokenKey 换 Token...", file=sys.stderr)
    result = api_request(
        base_url, "POST", "/api/dash/util/genToken",
        payload={"tokenType": "tokenKey", "key": token_key, "expiryTime": TOKEN_TTL},
    )
    if isinstance(result, str):
        token = result
    elif isinstance(result, dict):
        token = result.get("token") or result.get("data", {}).get("token") or str(result)
    else:
        token = str(result)
    save_token_cache(token, int(time.time()) + TOKEN_TTL)
    return token


# ============================================================
# HTTP
# ============================================================

def api_request(base_url: str, method: str, path: str,
                payload=None, params=None) -> dict | str:
    url = f"{base_url}{path}"
    if params:
        url += "?" + urlencode(params)
    body = json.dumps(payload).encode("utf-8") if payload else None
    req = Request(
        url, data=body, method=method,
        headers={"Content-Type": "application/json"} if body else {},
    )
    try:
        with urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"错误：HTTP {e.code} {url}\n{body[:500]}")
    except (URLError, OSError) as e:
        sys.exit(f"错误：请求失败 {e}")

    if isinstance(result, str):
        return result
    if result.get("code") != 200:
        msg = result.get("msg") or result.get("message") or str(result)
        sys.exit(f"错误：API code={result.get('code')} {msg}")
    return result.get("result") or result


# ============================================================
# 报告列表
# ============================================================

def fetch_all_reports(base_url: str, token: str, project_id: int) -> list[tuple]:
    """返回 [(path, id, name, publish_status, permissions), ...]"""
    result = api_request(
        base_url, "GET", "/api/dash/folder/list",
        params={"token": token, "projectId": project_id},
    )
    folders = result.get("folders", [])
    root_items = result.get("items", [])
    all_reports = []

    def report_name(item):
        return item.get("title") or item.get("name") or item.get("text") or "（无名称）"

    def walk(folder_list, parent_path="root"):
        for folder in folder_list:
            current_path = f"{parent_path} > {folder.get('name', '无名称')}"
            for item in folder.get("items", []):
                if item.get("isFolder") == 0:
                    all_reports.append((
                        current_path, item.get("id"), report_name(item),
                        item.get("publishStatus"), item.get("permissions", []),
                    ))
            walk(folder.get("folders", []), current_path)

    walk(folders)
    for item in root_items:
        if item.get("isFolder") == 0:
            all_reports.append((
                "root", item.get("id"), report_name(item),
                item.get("publishStatus"), item.get("permissions", []),
            ))
    return all_reports


def status_tag(publish_status, path: str) -> str:
    if publish_status == 0:
        return "草稿"
    if publish_status == 1:
        return "待下线" if "待下线" in path else "已发布"
    return "未知"


def print_reports(reports: list, title: str | None = None) -> None:
    if not reports:
        print("\n没有匹配的报告")
        return
    print(f"\n{title or f'共 {len(reports)} 个报告'}\n")
    print("-" * 100)
    print(f"  {'报告ID':<10} {'报告名称':<36} {'状态':<10} {'路径'}")
    print("-" * 100)
    for folder_path, rid, rname, pstatus, _ in sorted(reports, key=lambda x: x[1] or 0):
        short_path = folder_path if folder_path != "root" else "根目录"
        rid_str = str(rid) if rid is not None else "?"
        rname_str = (rname or "（无名称）")[:34]
        print(f"  {rid_str:<10} {rname_str:<36} {status_tag(pstatus, folder_path):<10} {short_path}")
    print("-" * 100)


# ============================================================
# 子命令
# ============================================================

def cmd_list_reports(args):
    base_url, _, project_id = resolve_config(args)
    token = get_token(args)
    print("正在获取报告列表...", file=sys.stderr)
    all_reports = fetch_all_reports(base_url, token, project_id)
    print_reports(all_reports, f"共 {len(all_reports)} 个报告" if all_reports else None)
    if all_reports:
        print("\n提示：python3 scripts/youshu_cli.py search <关键词> 过滤；")
        print("      python3 scripts/youshu_cli.py download <URL> 直接拉")


def cmd_search(args):
    base_url, _, project_id = resolve_config(args)
    token = get_token(args)
    keyword = (args.keyword or "").strip()
    if not keyword:
        sys.exit("错误：请输入搜索关键词")
    if args.server:
        print("正在服务端全文搜索...", file=sys.stderr)
        try:
            results = es_search_reports(base_url, token, project_id, keyword,
                                        args.measure, args.dimension)
        except SystemExit as e:
            # 当前域未开通 esSearch（code=742，2026-08-04 实测），给可操作提示而非裸报错
            if "742" in str(e):
                sys.exit("错误：当前域未开通 esSearch 功能（code=742），"
                         "改用本地过滤（去掉 --server）")
            raise
        print_es_results(results, keyword)
        return
    print("正在获取报告列表...", file=sys.stderr)
    all_reports = fetch_all_reports(base_url, token, project_id)
    kw = keyword.lower()
    matched = [r for r in all_reports
               if kw in (r[2] or "").lower() or kw in (r[0] or "").lower()]
    print_reports(matched, f"搜索「{keyword}」匹配 {len(matched)} 个报告")


def es_search_reports(base_url: str, token: str, project_id: int,
                      keyword: str, measure: str | None = None,
                      dimension: str | None = None) -> list[dict]:
    """服务端全文搜索（es/searchReport）：报告名 + 度量/维度字段关键字匹配。

    返回 result[]（reportId / reportName / componentHighlights / webLink 等）。
    """
    payload: dict = {"token": token, "projectId": project_id, "reportKeyword": keyword}
    if measure:
        payload["measureKeyword"] = measure
    if dimension:
        payload["dimensionKeyword"] = dimension
    result = api_request(base_url, "POST", "/api/dash/es/searchReport", payload=payload)
    if isinstance(result, dict):
        return result.get("result", []) or []
    return result if isinstance(result, list) else []


def print_es_results(results: list[dict], keyword: str) -> None:
    if not results:
        print(f"\n服务端搜索「{keyword}」命中 0 个报告")
        return
    print(f"\n服务端搜索「{keyword}」命中 {len(results)} 个报告\n")
    print("-" * 110)
    print(f"  {'报告ID':<10} {'报告名称':<32} {'匹配组件'}")
    print("-" * 110)
    for r in results:
        rid = r.get("reportId")
        name = (r.get("reportName") or "（无名称）")[:30]
        highlights = r.get("componentHighlights") or []
        comps = "、".join(
            h.get("componentTitle", "") for h in highlights if h.get("componentTitle")
        )[:40]
        print(f"  {rid:<10} {name:<32} {comps}")
    print("-" * 110)
    print("用 download <URL> 拉取命中报告")


def cmd_flush_cache(args):
    base_url, _, _ = resolve_config(args)
    token = get_token(args)
    payload: dict = {
        "token": token,
        "dataConnectionId": args.data_connection_id,
        "tableName": args.table,
    }
    if args.database:
        payload["database"] = args.database
    print(f"正在刷新表 {args.table} 的图表缓存...", file=sys.stderr)
    result = api_request(base_url, "POST", "/api/dash/cacheTask/flushByTable", payload=payload)
    print(f"缓存刷新完成：{result}")


def cmd_list_dashboards(args):
    base_url, _, project_id = resolve_config(args)
    token = get_token(args)
    # 隐藏接口 getDashboards 直接拿 dashboard 列表（详见 youshu-api.md §二）
    print(f"正在查询报告 {args.report_id} 的页面列表...", file=sys.stderr)
    try:
        result = api_request(
            base_url, "GET", "/api/dash/report/getDashboards",
            params={"token": token, "reportId": args.report_id},
        )
        dashboards = result.get("dashboards", []) if isinstance(result, dict) else []
    except SystemExit:
        dashboards = []

    if dashboards:
        print(f"\n报告 {args.report_id} 下有 {len(dashboards)} 个页面：\n")
        print("-" * 80)
        print(f"  {'页面ID':<12} {'页面名称'}")
        print("-" * 80)
        for d in dashboards:
            print(f"  {str(d.get('id')):<12} {d.get('title', '（无名称）')}")
        print("-" * 80)
        print("\n提示：导出某个页面 →")
        print(f"  python3 scripts/youshu_cli.py export --report-id {args.report_id} "
              f"--type dashboard --dashboard-id <页面ID> --export-type png")
        return

    # getDashboards 不可用时 fallback 到 ext/get
    print("getDashboards 未返回页面列表，fallback 到 report/ext/get：", file=sys.stderr)
    info = api_request(
        base_url, "GET", "/api/dash/report/ext/get",
        params={"token": token, "reportId": args.report_id},
    )
    print(json.dumps(info, ensure_ascii=False, indent=2))
    print("\n提示：页面 ID 也可从浏览器 URL 的 did=xxx 参数读取")


def cmd_export(args):
    base_url, _, project_id = resolve_config(args)
    token = get_token(args)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 格式
    export_type = args.export_type
    if not export_type:
        print("请选择导出格式：")
        print("  1) crossTable — 交叉表 xlsx（保留样式）")
        print("  2) xlsx       — 一维表 xlsx（每行一条记录）")
        print("  3) png        — 截图")
        print("  4) pdf        — PDF（多页）")
        ans = input("[1/2/3/4]: ").strip()
        export_type = {"1": "crossTable", "2": "xlsx", "3": "png", "4": "pdf"}.get(ans, ans)

    export_config = {
        "crossTable": ("/api/dash/report/exportExcel", ".xlsx"),
        "xlsx":       ("/api/dash/report/exportExcel", ".xlsx"),
        "png":        ("/api/dash/report/exportCapture", ".png"),
        "pdf":        ("/api/dash/report/exportCapture", ".pdf"),
    }
    if export_type not in export_config:
        sys.exit(f"错误：未知格式 {export_type}（支持 crossTable/xlsx/png/pdf）")
    api_path, ext = export_config[export_type]

    # 输出文件名
    if args.output:
        base = args.output.rsplit(".", 1)[0]
        output_file = Path(f"{base}_{now_str}{ext}")
    else:
        all_reports = fetch_all_reports(base_url, token, project_id)
        title = "report"
        for _, rid, rname, *_rest in all_reports:
            if rid == args.report_id and rname:
                title = rname.strip().replace("/", "_").replace(" ", "_")
                break
        if args.dashboard_id:
            output_file = Path(f"{title}_did{args.dashboard_id}_{now_str}{ext}")
        else:
            output_file = Path(f"{title}_{now_str}{ext}")

    if not output_file.is_absolute():
        out_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        output_file = out_dir / output_file

    # crossTable/xlsx 才询问 4 个布尔选项
    use_origin_data = enhance = condition_format = include_title = None
    if export_type in ("crossTable", "xlsx"):
        use_origin_data = ask_bool(
            args.use_origin_data, "是否导出原始数值（不转成展示格式）？", default=True,
        )
        enhance = ask_bool(
            args.enhance, "是否导出样式（蓝色表头等）？", default=False,
        )
        condition_format = ask_bool(
            args.condition_format, "是否导出数据格式及日期格式？", default=False,
        )
        include_title = ask_bool(
            args.include_title, "是否导出图表标题？", default=False,
        )

    api_export_type = {"png": "picture", "pdf": "pdf"}.get(export_type, export_type)
    params = {
        "token": token,
        "reportId": args.report_id,
        "type": args.type,
        "exportType": api_export_type,
        "pid": project_id,
    }
    if use_origin_data is not None:
        params["useOriginData"] = use_origin_data
    if enhance is not None:
        params["enhance"] = enhance
    if condition_format is not None:
        params["conditionFormat"] = condition_format
    if include_title is not None:
        params["includeTitle"] = include_title
    if args.type == "dashboard" and args.dashboard_id:
        params["dashboardId"] = args.dashboard_id
    if args.type == "component" and args.component_id:
        params["componentId"] = args.component_id
    if args.title:
        params["title"] = args.title

    print(f"正在导出（reportId={args.report_id}, format={export_type}）...", file=sys.stderr)
    url = f"{base_url}{api_path}?{urlencode(params)}"
    try:
        with urlopen(Request(url, method="GET"), timeout=180) as resp:
            content = resp.read()
            try:
                obj = json.loads(content.decode("utf-8"))
                if obj.get("code") != 200:
                    sys.exit(f"错误：导出失败 {obj.get('msg', obj)}")
                result_obj = obj.get("result", {}) or obj.get("data", {})
                download_url = result_obj.get("link") or result_obj.get("url")
                if not download_url:
                    sys.exit(f"错误：导出返回 JSON 但无文件链接 {obj}")
                print("拿到下载链接，开始下载...", file=sys.stderr)
                with urlopen(Request(download_url, method="GET"), timeout=180) as r2:
                    content = r2.read()
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass  # 二进制直接落盘

        output_file.write_bytes(content)
        print(f"导出成功 → {output_file} ({len(content)/1024:.1f} KB)")
    except HTTPError as e:
        sys.exit(f"错误：HTTP {e.code} {e.read().decode('utf-8', errors='replace')[:500]}")


def cmd_download(args):
    parsed = urlparse(args.url)
    qs = parse_qs(parsed.query)
    rid = qs.get("rid", [None])[0]
    did = qs.get("did", [None])[0]
    if not rid:
        sys.exit("错误：URL 中找不到 rid（期望格式 .../dash/folder/2?rid=3965&did=6216）")

    ns = argparse.Namespace(
        token_key=args.token_key, token=args.token,
        base_url=args.base_url, project_id=args.project_id,
        report_id=int(rid), dashboard_id=int(did) if did else None,
        type="dashboard" if did else "report",
        export_type=args.format,
        use_origin_data=args.use_origin_data, enhance=args.enhance,
        condition_format=args.condition_format, include_title=args.include_title,
        component_id=None, title=None, output=args.output, output_dir=args.output_dir,
    )
    print(f"解析 URL：rid={rid}" + (f", did={did}" if did else ""), file=sys.stderr)
    cmd_export(ns)


def cmd_async_export(args):
    """异步大导出：建任务 → 轮询 → 下载 zip。

    解决 getData 2 万行上限 / 同步 exportExcel 体积限制（见 youshu-api.md §三之三）。
    端点：POST /api/dash/report/asyncExportExcel + GET exportExcelTask/get + download。
    """
    base_url, _, _ = resolve_config(args)
    token = get_token(args)

    print(f"正在创建异步导出任务（reportId={args.report_id}, {args.export_type}）...", file=sys.stderr)
    result = api_request(base_url, "POST", "/api/dash/report/asyncExportExcel", payload={
        "token": token,
        "reportId": args.report_id,
        "componentId": args.component_id,
        "exportType": args.export_type,
        "excelSplitLimit": args.split,
    })
    if isinstance(result, dict):
        task_id = result.get("id") or result.get("taskId") or result.get("result")
    else:
        task_id = result
    if not task_id:
        sys.exit(f"错误：asyncExportExcel 未返回任务 ID：{result}")

    print(f"任务 {task_id} 已创建，轮询状态（超时 {args.timeout}s）...", file=sys.stderr)
    deadline = time.time() + args.timeout
    status = None
    while time.time() < deadline:
        info = api_request(base_url, "GET", "/api/dash/exportExcelTask/get",
                           params={"token": token, "id": task_id})
        status = info.get("status") if isinstance(info, dict) else None
        if status in ("success", "fail", "expired"):
            break
        time.sleep(2)
    if status != "success":
        sys.exit(f"错误：导出任务未成功（status={status}）")

    print("任务完成，下载中...", file=sys.stderr)
    url = f"{base_url}/api/dash/exportExcelTask/download?token={token}&id={task_id}"
    try:
        with urlopen(Request(url, method="GET"), timeout=180) as resp:
            content = resp.read()
    except HTTPError as e:
        sys.exit(f"错误：HTTP {e.code} {e.read().decode('utf-8', errors='replace')[:500]}")

    out_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".zip" if not args.output or not args.output.lower().endswith((".zip", ".csv", ".xlsx")) else ""
    name = args.output or f"async_export_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out = out_dir / f"{name}{suffix}"
    out.write_bytes(content)
    print(f"导出成功 → {out} ({len(content)/1024:.1f} KB)")


# ============================================================
# 工具
# ============================================================

def ask_bool(cli_value: str | None, prompt: str, default: bool) -> str:
    """CLI 传值优先，否则交互询问。返回 'true' / 'false'。"""
    if cli_value is not None:
        return cli_value
    suffix = "[Y/n]" if default else "[y/N]"
    ans = input(f"{prompt} {suffix} ").strip().lower()
    if not ans:
        return "true" if default else "false"
    return "true" if ans == "y" else "false"


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="网易有数报告下载 CLI（凭证读 .env 的 YOUSHU_BASE / YOUSHU_TOKEN_KEY）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 scripts/youshu_cli.py list-reports
  python3 scripts/youshu_cli.py search 合约
  python3 scripts/youshu_cli.py search 合约 --server           # 服务端全文搜索
  python3 scripts/youshu_cli.py search 收益 --server --measure 利润
  python3 scripts/youshu_cli.py flush-cache --data-connection-id 700310511 --table bigviz_user --database dev_netease
  python3 scripts/youshu_cli.py download "https://INTERNAL_URL_REDACTED"
  python3 scripts/youshu_cli.py download "URL" --format pdf
  python3 scripts/youshu_cli.py export --report-id 3965 --type dashboard --dashboard-id 6216 --export-type png
""",
    )
    parser.add_argument("-k", "--token-key", default=None, help="覆盖 .env 的 TokenKey")
    parser.add_argument("-t", "--token", default=None, help="临时 Token，跳过 genToken")
    parser.add_argument("--base-url", default=None, help="覆盖 .env 的 YOUSHU_BASE")
    parser.add_argument("--project-id", type=int, default=None, help="覆盖默认 projectId（=2）")

    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("list-reports", help="列出有权限的报告")
    p.set_defaults(func=cmd_list_reports)

    p = sub.add_parser("search", help="按关键词过滤报告（--server 走服务端全文搜索）")
    p.add_argument("keyword", help="搜索关键词")
    p.add_argument("--server", action="store_true",
                   help="服务端全文搜索（es/searchReport）：报告名 + 字段关键字，分页外也能命中")
    p.add_argument("--measure", default=None, help="--server 时：度量字段关键字")
    p.add_argument("--dimension", default=None, help="--server 时：维度字段关键字")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("flush-cache", help="按表刷新图表缓存（需项目管理员权限）")
    p.add_argument("--data-connection-id", type=int, required=True, help="数据连接 ID")
    p.add_argument("--table", required=True, help="数据库下的表名")
    p.add_argument("--database", default=None, help="数据库名（可选）")
    p.set_defaults(func=cmd_flush_cache)

    p = sub.add_parser("list-dashboards", help="列报告下的页面 ID")
    p.add_argument("--report-id", type=int, required=True)
    p.set_defaults(func=cmd_list_dashboards)

    p = sub.add_parser("download", help="贴 URL 自动解析下载（推荐）")
    p.add_argument("url", help="报告 URL（含 rid，可选 did）")
    p.add_argument("--format", choices=["crossTable", "xlsx", "png", "pdf"], default=None)
    p.add_argument("--use-origin-data", choices=["true", "false"], default=None)
    p.add_argument("--enhance", choices=["true", "false"], default=None)
    p.add_argument("--condition-format", choices=["true", "false"], default=None)
    p.add_argument("--include-title", choices=["true", "false"], default=None)
    p.add_argument("--output", "-o", default=None, help="文件名前缀（不含扩展名）")
    p.add_argument("--output-dir", default=None, help=f"输出目录（默认 {DEFAULT_OUTPUT_DIR}）")
    p.set_defaults(func=cmd_download)

    p = sub.add_parser("export", help="指定 report-id 导出")
    p.add_argument("--report-id", type=int, required=True)
    p.add_argument("--type", choices=["report", "dashboard", "component"], default="report")
    p.add_argument("--export-type", choices=["crossTable", "xlsx", "png", "pdf"], default=None)
    p.add_argument("--dashboard-id", type=int, default=None, help="type=dashboard 必传")
    p.add_argument("--component-id", default=None, help="type=component 必传")
    p.add_argument("--use-origin-data", choices=["true", "false"], default=None)
    p.add_argument("--enhance", choices=["true", "false"], default=None)
    p.add_argument("--condition-format", choices=["true", "false"], default=None)
    p.add_argument("--include-title", choices=["true", "false"], default=None)
    p.add_argument("--title", default=None, help="服务端文件标题")
    p.add_argument("--output", "-o", default=None, help="文件名前缀（不含扩展名）")
    p.add_argument("--output-dir", default=None, help=f"输出目录（默认 {DEFAULT_OUTPUT_DIR}）")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("async-export",
                       help="异步大导出（>2 万行组件）：建任务→轮询→下载 zip")
    p.add_argument("--report-id", type=int, required=True)
    p.add_argument("--component-id", required=True)
    p.add_argument("--export-type", choices=["csv", "xlsx"], default="csv")
    p.add_argument("--split", type=int, default=1000000, help="excelSplitLimit 每文件行数，默认 100 万")
    p.add_argument("--timeout", type=int, default=300, help="轮询超时秒")
    p.add_argument("--output", "-o", default=None, help="输出文件名（可带 .zip/.csv/.xlsx）")
    p.add_argument("--output-dir", default=None, help=f"输出目录（默认 {DEFAULT_OUTPUT_DIR}）")
    p.set_defaults(func=cmd_async_export)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
