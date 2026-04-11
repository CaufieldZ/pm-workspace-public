#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
"""
scheduled-scrape.py — 定时采集竞品公告 & Crypto 媒体内容
用法:
  python3 scheduled-scrape.py --all          # 全部采集
  python3 scheduled-scrape.py --platforms binance,okx  # 指定交易所
  python3 scheduled-scrape.py --media        # 仅媒体
  python3 scheduled-scrape.py --platforms binance --media  # 交易所+媒体

零 AI Token 消耗：纯 Playwright headless 抓取 + 本地文件存储。
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parents[3]  # .claude/skills/intel-collector/references -> root
REGISTRY_PATH = SCRIPT_DIR / "url-registry.json"
AUTH_DIR = SCRIPT_DIR / "auth"
COMPETITORS_DIR = WORKSPACE_ROOT / "references" / "competitors"
TODAY = datetime.now().strftime("%Y-%m-%d")


def load_registry():
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def get_scrape_targets(registry, platforms=None, media=False):
    """Filter registry to announcement/news URLs only."""
    targets = []

    # Exchange announcements
    if platforms is not None:
        for platform in platforms:
            if platform not in registry:
                continue
            for key, urls in registry[platform].items():
                if "announcement" in key or "news" in key:
                    for url in urls:
                        targets.append({
                            "platform": platform,
                            "key": key,
                            "url": url,
                            "type": "exchange",
                        })

    # Media sources
    if media and "_media" in registry:
        for key, urls in registry["_media"].items():
            # Only scrape -news / -article keys, skip homepage duplicates
            if any(suffix in key for suffix in ["-news", "-article", "-markets", "-tech", "-policy", "-latest"]):
                media_name = key.split("-")[0]
                for url in urls:
                    targets.append({
                        "platform": media_name,
                        "key": key,
                        "url": url,
                        "type": "media",
                    })

    return targets


def get_output_path(target):
    if target["type"] == "media":
        return COMPETITORS_DIR / "_media" / target["platform"] / f"{TODAY}.md"
    else:
        return COMPETITORS_DIR / target["platform"] / "announcements" / f"{TODAY}.md"


def content_is_new(output_path, new_content):
    """Check if content differs from the most recent file in the same directory."""
    directory = output_path.parent
    if not directory.exists():
        return True

    existing = sorted(directory.glob("*.md"), reverse=True)
    if not existing:
        return True

    # Compare with latest file (could be today's or older)
    latest = existing[0]
    if not latest.exists():
        return True

    old_content = latest.read_text(encoding="utf-8").strip()
    # Normalize whitespace for comparison
    old_norm = re.sub(r"\s+", " ", old_content)
    new_norm = re.sub(r"\s+", " ", new_content.strip())

    return old_norm != new_norm


NOISE_PATTERNS = [
    "cookie", "sign up", "log in", "download app", "© 20",
    "all rights reserved", "terms of service", "privacy policy",
    "footer", "consent", "legitimate interests", "personalised advertising",
    "switch label", "view illustrations", "partners can use this purpose",
    "object to", "googletag", "window.ads", "gtm-", "googletagmanager",
]


def clean_body_text(raw_text):
    """Remove nav/footer/consent noise, collapse whitespace."""
    lines = raw_text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        lower = line.lower()
        if any(skip in lower for skip in NOISE_PATTERNS):
            continue
        # Skip lines that look like JS code or CSS
        if line.startswith(("var ", "function ", "window.", "{", "}", "//", "/*")):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

# Preferred content selectors, tried in order (first match wins)
CONTENT_SELECTORS = ["main", "article", "[role='main']", "#content", ".content"]


async def extract_jsonld(page):
    """Extract article info from JSON-LD structured data if available."""
    try:
        scripts = await page.query_selector_all('script[type="application/ld+json"]')
        articles = []
        for script in scripts:
            text = await script.text_content()
            data = json.loads(text)
            items = []
            # Handle ItemList (CoinDesk style)
            if isinstance(data, dict) and "mainEntity" in data:
                entity = data["mainEntity"]
                if isinstance(entity, dict) and "itemListElement" in entity:
                    items = entity["itemListElement"]
            # Handle direct array
            elif isinstance(data, list):
                items = [{"item": d} for d in data if isinstance(d, dict)]

            for item in items:
                art = item.get("item", item)
                headline = art.get("headline", "")
                url = art.get("url", "")
                date = art.get("datePublished", "")
                if headline:
                    line = f"- **{headline}**"
                    if date:
                        line += f" ({date[:10]})"
                    if url:
                        line += f"\n  {url}"
                    articles.append(line)
        return "\n".join(articles) if articles else None
    except Exception:
        return None


async def scrape_page(browser, target):
    """Scrape a single page, return cleaned text or None on error."""
    auth_file = AUTH_DIR / f"{target['platform']}.json"
    context_opts = {"user_agent": USER_AGENT}
    if auth_file.exists():
        context_opts["storage_state"] = str(auth_file)

    context = await browser.new_context(
        viewport={"width": 1440, "height": 900},
        **context_opts,
    )

    try:
        page = await context.new_page()
        await page.goto(target["url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        # 1. Try JSON-LD structured data first (cleanest)
        jsonld = await extract_jsonld(page)

        # 2. Try focused content selectors (skip nav/footer)
        body_text = None
        if not jsonld:
            for selector in CONTENT_SELECTORS:
                el = await page.query_selector(selector)
                if el:
                    body_text = await el.inner_text()
                    if body_text and len(body_text.strip()) > 100:
                        break
                    body_text = None

        # 3. Fallback to body inner_text (respects CSS visibility, skips script/style)
        if not jsonld and not body_text:
            body_text = await page.inner_text("body")

        if not jsonld and (not body_text or len(body_text.strip()) < 50):
            return None

        content = jsonld if jsonld else clean_body_text(body_text)
        if not content or len(content) < 30:
            return None

        header = f"# {target['platform']} — {target['key']}\n"
        header += f"> Source: {target['url']}\n"
        header += f"> Scraped: {TODAY}\n\n"
        return header + content

    except Exception as e:
        raise e
    finally:
        await context.close()


async def main():
    parser = argparse.ArgumentParser(description="Scheduled competitor content scraper")
    parser.add_argument("--platforms", type=str, help="Comma-separated platform names")
    parser.add_argument("--media", action="store_true", help="Scrape media sources")
    parser.add_argument("--all", action="store_true", help="Scrape all exchanges + media")
    args = parser.parse_args()

    if not any([args.platforms, args.media, args.all]):
        parser.error("Specify --platforms, --media, or --all")

    registry = load_registry()

    # Determine which platforms to scrape
    if args.all:
        platforms = [k for k in registry.keys() if not k.startswith("_")]
        media = True
    else:
        platforms = args.platforms.split(",") if args.platforms else []
        media = args.media

    targets = get_scrape_targets(registry, platforms if platforms else None, media)

    if not targets:
        print(json.dumps({"scraped": 0, "new": 0, "errors": 0, "details": [], "msg": "No matching targets"}))
        return

    # Import playwright here so the script can parse args without it installed
    from playwright.async_api import async_playwright

    results = {"scraped": 0, "new": 0, "errors": 0, "details": []}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for target in targets:
            detail = {"platform": target["platform"], "key": target["key"], "status": ""}
            try:
                content = await scrape_page(browser, target)
                results["scraped"] += 1

                if content is None:
                    detail["status"] = "empty"
                    results["details"].append(detail)
                    continue

                output_path = get_output_path(target)

                if content_is_new(output_path, content):
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    # Append to today's file if multiple keys for same platform
                    if output_path.exists():
                        with open(output_path, "a", encoding="utf-8") as f:
                            f.write("\n\n---\n\n" + content)
                    else:
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(content)
                    detail["status"] = "new"
                    results["new"] += 1
                else:
                    detail["status"] = "unchanged"

            except Exception as e:
                detail["status"] = f"error: {str(e)[:100]}"
                results["errors"] += 1

            results["details"].append(detail)

        await browser.close()

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
