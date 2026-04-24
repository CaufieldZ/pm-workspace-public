#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""Push a Markdown file to Confluence as a child page, wrapped in the Markdown macro.

Reads Confluence creds from .mcp.json or .mcp-disabled.json (toggle-mcp.sh
parks the env block in the latter when the server is disabled — REST calls
still work since no live MCP server is needed).

Usage:
    python3 scripts/md_to_confluence.py <md_path> --parent-id <id> [--title <title>] [--space <key>] [--update-id <id>]

Examples:
    # Create new child page under parent
    python3 scripts/md_to_confluence.py projects/foo/deliverables/pspec.md --parent-id 151429067

    # Overwrite an existing page by ID
    python3 scripts/md_to_confluence.py projects/foo/deliverables/pspec.md --update-id 164481003
"""
import argparse
import re
import sys
from pathlib import Path

from lib.confluence import base_url, create_page, update_page


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

    if args.update_id:
        res = update_page(args.update_id, title, body)
    else:
        if not args.parent_id:
            sys.exit("need --parent-id for create, or --update-id to overwrite")
        res = create_page(args.space, title, body, args.parent_id)

    page_id = res["id"]
    print(f"✓ {title}")
    print(f"  {base_url()}/pages/viewpage.action?pageId={page_id}")


if __name__ == "__main__":
    main()
