#!/usr/bin/env python3
"""Test paired reader mode with full text splitting."""
import subprocess, sys, os, time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8767
proc = subprocess.Popen(
    [sys.executable, "-m", "http.server", str(PORT)],
    cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(2)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        for pid in ["2.4", "31.3"]:
            print(f"\n=== Paper {pid} ===")
            page.goto(f"http://localhost:{PORT}/site/index.html?private=1#paper/{pid}")
            page.wait_for_selector(".detail-page", timeout=10000)
            page.wait_for_timeout(3000)  # Wait for text.md to load

            # Check slides
            slide = page.query_selector(".reader-slide")
            print(f"  reader-slide: {slide is not None}")

            # Check text content (should be full paragraphs, not just captions)
            reader_text = page.query_selector(".reader-text")
            if reader_text:
                t = reader_text.text_content()
                print(f"  text length: {len(t)} chars")
                print(f"  first 200: {t[:200]}...")

            # Count paragraphs
            paras = page.query_selector_all(".reader-paragraph")
            print(f"  paragraphs: {len(paras)}")

            # Check dots count
            dots = page.query_selector_all(".reader-dot")
            print(f"  slides (dots): {len(dots)}")

            # Screenshot
            page.screenshot(
                path=os.path.join(BASE_DIR, "screenshots", f"reader_{pid.replace('.','_')}.png"),
                full_page=True
            )

            # Navigate to slide 2 and check
            next_btn = page.query_selector("#reader-next")
            if next_btn:
                next_btn.click()
                page.wait_for_timeout(500)
                reader_text2 = page.query_selector(".reader-text")
                if reader_text2:
                    t2 = reader_text2.text_content()
                    print(f"  slide 2 text length: {len(t2)} chars")
                    print(f"  slide 2 first 150: {t2[:150]}...")

            page.screenshot(
                path=os.path.join(BASE_DIR, "screenshots", f"reader_{pid.replace('.','_')}_s2.png"),
                full_page=True
            )

        if errors:
            print(f"\nConsole errors: {errors[:5]}")

        browser.close()
finally:
    proc.terminate()
    proc.wait()

print("\nDone.")
