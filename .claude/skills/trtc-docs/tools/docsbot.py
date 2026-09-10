"""
tools/docsbot.py
================

DocsBot REST API wrapper for TRTC documentation retrieval.

Calls the DocsBot chat API with full_source=true, returns a structured
JSON result that trtc-docs/SKILL.md can consume directly.

The answer field from DocsBot is already markdown-formatted and
language-matched to the query — no post-processing needed.

Usage:
    python3 -m tools.docsbot ask --query "<question>" [--product <p>] [--platform <pl>]

Output (stdout, JSON):
    {
      "status": "resolved" | "not_found" | "fetch_failed",
      "answer": "<markdown answer from DocsBot>",
      "sources": [{"title": "...", "url": "...", "content": "..."}],
      "could_answer": true | false
    }

TODO: Move API key to @tencent-rtc/skill-tool MCP server so end users
      don't need to configure DocsBot credentials.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DOCSBOT_TEAM_ID = "kWE3LJmKAa1tOWunDswD"
DOCSBOT_BOT_ID  = "eqiBblNdkm6R7wmRuXCL"
DOCSBOT_API_KEY = os.environ.get(
    "DOCSBOT_API_KEY",
    "ba25f6f95c196d017919b550539a2cf863657d220345133aba40f86a3969d623",
)
CHAT_URL = (
    f"https://api.docsbot.ai/teams/{DOCSBOT_TEAM_ID}"
    f"/bots/{DOCSBOT_BOT_ID}/chat"
)
TIMEOUT = 20.0


class DocsBotError(Exception):
    pass


def ask(query: str, product: Optional[str] = None, platform: Optional[str] = None) -> dict[str, Any]:
    """Call DocsBot chat API and return a structured result."""
    # Prepend product/platform so DocsBot can scope retrieval
    parts = ["TRTC"]
    if product:
        parts.append(product.capitalize())
    if platform:
        parts.append(platform.capitalize())
    parts.append(query)
    scoped_query = " ".join(parts)

    payload = json.dumps({
        "question": scoped_query,
        "full_source": True,
    }).encode("utf-8")

    req = Request(
        CHAT_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {DOCSBOT_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return {
            "status": "fetch_failed",
            "answer": "",
            "sources": [],
            "could_answer": False,
            "_error": f"HTTP {exc.code}",
        }
    except URLError as exc:
        return {
            "status": "fetch_failed",
            "answer": "",
            "sources": [],
            "could_answer": False,
            "_error": str(exc.reason),
        }

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        return {
            "status": "fetch_failed",
            "answer": "",
            "sources": [],
            "could_answer": False,
            "_error": f"JSON parse error: {exc}",
        }

    could_answer: bool = bool(data.get("couldAnswer", False))
    answer: str = data.get("answer") or ""

    # Only keep sources that DocsBot actually used in the answer
    raw_sources = data.get("sources") or []
    used_sources = [
        {"title": s.get("title", ""), "url": s.get("url", ""), "content": s.get("content", "")}
        for s in raw_sources
        if s.get("used") is True
    ]
    # De-duplicate by URL while preserving order
    seen: set[str] = set()
    sources: list[dict[str, str]] = []
    for s in used_sources:
        if s["url"] and s["url"] not in seen:
            seen.add(s["url"])
            sources.append(s)

    if not could_answer:
        return {
            "status": "not_found",
            "answer": answer,
            "sources": sources,
            "could_answer": False,
        }

    return {
        "status": "resolved",
        "answer": answer,
        "sources": sources,
        "could_answer": True,
    }


def _parse_args(argv: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--") and i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            out[arg[2:]] = argv[i + 1]
            i += 2
        else:
            i += 1
    return out


def main() -> int:
    argv = sys.argv[1:]
    if not argv or argv[0] != "ask":
        print(__doc__, file=sys.stderr)
        return 1

    kv = _parse_args(argv[1:])
    query = kv.get("query")
    if not query:
        print("ERROR: --query is required", file=sys.stderr)
        return 1

    result = ask(
        query=str(query),
        product=kv.get("product"),
        platform=kv.get("platform"),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "resolved" else 1


if __name__ == "__main__":
    raise SystemExit(main())
