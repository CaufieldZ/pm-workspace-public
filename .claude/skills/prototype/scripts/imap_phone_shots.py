"""IMAP 单截每张 phone · prototype skill 硬看流程配套

用 playwright 找 IMAP HTML 里所有 .phone / .app-mock，每张独立截 PNG，按场景编号命名。

用法：
    python3 .claude/skills/prototype/scripts/imap_phone_shots.py <imap.html> -o <out_dir>

每张图保存到 <out_dir>/{编号}.png（编号从最近的 .phone-label / .st h2 / data-scene 抽）。
"""
import argparse
import re
import sys
from pathlib import Path
from urllib.parse import quote


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("imap", help="IMAP HTML 文件路径")
    ap.add_argument("-o", "--out", required=True, help="输出目录")
    args = ap.parse_args()

    imap_path = Path(args.imap).resolve()
    if not imap_path.exists():
        print(f"❌ IMAP 不存在: {imap_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 缺 playwright，先 pip install playwright && playwright install chromium", file=sys.stderr)
        sys.exit(1)

    file_url = "file://" + quote(str(imap_path), safe="/:")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(file_url, wait_until="networkidle")

        phones = page.query_selector_all(".phone, .app-mock")
        if not phones:
            print("⚠️ 没找到 .phone / .app-mock 元素", file=sys.stderr)
            sys.exit(2)

        saved = 0
        used_names = set()
        for i, ph in enumerate(phones):
            name = ph.evaluate("""el => {
                let id = el.id || '';
                if (id) return id;
                let lbl = el.querySelector('.phone-label, .st h2, .scene-label');
                if (lbl) return (lbl.textContent || '').trim();
                let parent = el.closest('.flow-col, .st');
                if (parent) {
                    let plbl = parent.querySelector('.phone-label, h2');
                    if (plbl) return (plbl.textContent || '').trim();
                }
                return '';
            }""")
            slug = re.sub(r"\s+", "-", (name or f"phone-{i+1:02d}").strip())
            slug = re.sub(r"[^\w\-·]", "", slug) or f"phone-{i+1:02d}"
            if slug in used_names:
                slug = f"{slug}-{i+1:02d}"
            used_names.add(slug)

            target = out_dir / f"{slug}.png"
            try:
                ph.screenshot(path=str(target))
                saved += 1
                print(f"  ✓ {target.name}")
            except Exception as e:
                print(f"  ✗ {slug}: {e}", file=sys.stderr)

        browser.close()
        print(f"\n完成：{saved}/{len(phones)} 张保存到 {out_dir}")


if __name__ == "__main__":
    main()
