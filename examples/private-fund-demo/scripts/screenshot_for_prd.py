"""从交互大图截取各 Scene 第一个设备框作为 PRD 截图"""
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
import time, os


def round_phone_corners(png_path, radius_px=72):
    """给 phone 截图的 4 个角加透明蒙版。
    CSS 圆角 36px × deviceScaleFactor 2 = 72px 像素半径。
    截图在深色主题（如 GitHub README dark mode）下不再露白边。"""
    img = Image.open(png_path).convert("RGBA")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), img.size], radius=radius_px, fill=255)
    img.putalpha(mask)
    img.save(png_path, "PNG")

IMAP = "file:///Users/felix.zhi/pm-workspace/projects/demo-private-fund/deliverables/imap-private-fund-v1.html"
OUT_DIR = "/Users/felix.zhi/pm-workspace/projects/demo-private-fund/screenshots/prd"
os.makedirs(OUT_DIR, exist_ok=True)

# scene_id -> output filename
SCENES = [
    ("scene-a-1", "a1.png", "phone"),
    ("scene-a-2", "a2.png", "phone"),
    ("scene-b-1", "b1.png", "phone"),
    ("scene-b-2", "b2.png", "phone"),
    ("scene-c-1", "c1.png", "web"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    page.goto(IMAP)
    page.wait_for_load_state("networkidle")
    # 让所有 fade-section 可见 + 隐藏标注/导航（避免叠加到设备框里被截进去）
    page.evaluate("""
        document.querySelectorAll('.fade-section').forEach(el=>el.classList.add('visible'));
        document.querySelectorAll(
          '.anno, .anno-n, .ann-card, .ann-tag, .aw, .flow-note, .side-nav'
        ).forEach(el => el.style.display = 'none');
    """)
    time.sleep(0.6)

    for scene_id, fname, device_type in SCENES:
        # 找到 scene 容器
        scene = page.locator(f"#{scene_id}").first
        scene.scroll_into_view_if_needed()
        time.sleep(0.3)

        # 截第一个 .phone 或 .webframe
        selector = ".phone" if device_type == "phone" else ".webframe"
        device = scene.locator(selector).first
        out_path = os.path.join(OUT_DIR, fname)
        device.screenshot(path=out_path, omit_background=True)
        # phone 截图需要圆角透明化（webframe 是矩形，不处理）
        if device_type == "phone":
            round_phone_corners(out_path)
        print(f"  captured: {fname}")

    browser.close()
print("screenshots done")
