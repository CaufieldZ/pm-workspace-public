#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""Push a Markdown file to Confluence as a child page, wrapped in the Markdown macro.

Reads Confluence creds from .mcp.json so nothing sensitive lives in this script.

Usage:
    python3 scripts/md_to_confluence.py <md_path> --parent-id <id> [--title <title>] [--space <key>] [--update-id <id>]

Examples:
    # Create new child page under parent
    python3 scripts/md_to_confluence.py projects/foo/deliverables/pspec.md --parent-id 151429067

    # Overwrite an existing page by ID
    python3 scripts/md_to_confluence.py projects/foo/deliverables/pspec.md --update-id 164481003
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib import request, error

ROOT = Path(__file__).resolve().parent.parent
MCP_CONFIG = ROOT / ".mcp.json"


def load_creds():
    cfg = json.loads(MCP_CONFIG.read_text())
    env = cfg["mcpServers"]["confluence"]["env"]
    return env["CONF_BASE_URL"].rstrip("/"), env["CONF_TOKEN"]


def wrap_markdown(md: str) -> str:
    if "]]>" in md:
        md = md.replace("]]>", "]]]]><![CDATA[>")
    return (
        '<ac:structured-macro ac:name="markdown">'
        "<ac:plain-text-body><![CDATA["
        f"{md}"
        "]]></ac:plain-text-body></ac:structured-macro>"
    )


def extract_title(md: str) -> str:
    for line in md.splitlines():
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    raise ValueError("No H1 title found in markdown; pass --title explicitly")


def api(base: str, token: str, method: str, path: str, body: dict | None = None):
    url = f"{base}{path}"
    data = json.dumps(body).encode() if body else None
    req = request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read())
    except error.HTTPError as e:
        sys.stderr.write(f"HTTP {e.code}: {e.read().decode()}\n")
        raise


def create_page(base, token, space, title, body, parent_id):
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space},
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    if parent_id:
        payload["ancestors"] = [{"id": str(parent_id)}]
    return api(base, token, "POST", "/rest/api/content", payload)


def update_page(base, token, page_id, title, body):
    current = api(base, token, "GET", f"/rest/api/content/{page_id}?expand=version,space")
    payload = {
        "type": "page",
        "title": title or current["title"],
        "space": {"key": current["space"]["key"]},
        "version": {"number": current["version"]["number"] + 1},
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    return api(base, token, "PUT", f"/rest/api/content/{page_id}", payload)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("md_path")
    p.add_argument("--parent-id", help="parent page id (for create)")
    p.add_argument("--update-id", help="existing page id to overwrite (skips create)")
    p.add_argument("--space", default="jituankejizhongxin")
    p.add_argument("--title", help="override page title (default: first H1 of md)")
    args = p.parse_args()

    md = Path(args.md_path).read_text()
    title = args.title or extract_title(md)
    body = wrap_markdown(md)

    base, token = load_creds()

    if args.update_id:
        res = update_page(base, token, args.update_id, title, body)
    else:
        if not args.parent_id:
            sys.exit("need --parent-id for create, or --update-id to overwrite")
        res = create_page(base, token, args.space, title, body, args.parent_id)

    page_id = res["id"]
    print(f"✓ {title}")
    print(f"  https://INTERNAL_URL_REDACTED")


if __name__ == "__main__":
    main()
