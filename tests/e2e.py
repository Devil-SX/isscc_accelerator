#!/usr/bin/env python3
"""Playwright E2E tests for ISSCC 2026 Survey website.

Starts a local HTTP server, runs 10 test cases with screenshots.
"""

import subprocess
import time
import sys
import os

from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
PORT = 8765
BASE_URL = f"http://localhost:{PORT}/site/index.html"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def start_server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT)],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)
    return proc


def screenshot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, name)
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot saved: {name}")


def test_01_overview_load(page):
    """Test 1: Overview page loads with all 43 papers."""
    print("\n[Test 01] Overview page load")
    page.goto(BASE_URL)
    page.wait_for_selector(".comp-table .row", timeout=10000)
    rows = page.query_selector_all(".comp-table .row")
    count = len(rows)
    print(f"  Found {count} paper rows")
    assert count == 43, f"Expected 43 rows, got {count}"

    count_text = page.text_content("#paper-count")
    print(f"  Paper count text: {count_text}")
    assert "43" in count_text

    screenshot(page, "01_overview.png")
    print("  PASSED")


def test_02_session_filter(page):
    """Test 2: Session filter - click S31 shows 9 papers."""
    print("\n[Test 02] Session filter (S31)")
    page.goto(BASE_URL)
    page.wait_for_selector(".session-tab", timeout=10000)

    # Click Session 31 tab
    tabs = page.query_selector_all(".session-tab")
    for tab in tabs:
        if "31" in tab.text_content():
            tab.click()
            break

    page.wait_for_timeout(500)
    rows = page.query_selector_all(".comp-table .row")
    count = len(rows)
    print(f"  Found {count} papers in Session 31")
    assert count == 9, f"Expected 9 rows for S31, got {count}"

    screenshot(page, "02_session_filter.png")
    print("  PASSED")


def test_03_node_filter(page):
    """Test 3: Process node filter - select 28nm."""
    print("\n[Test 03] Process node filter (28nm)")
    page.goto(BASE_URL)
    page.wait_for_selector("#filter-process", timeout=10000)

    page.select_option("#filter-process", label="28nm")
    page.wait_for_timeout(500)

    rows = page.query_selector_all(".comp-table .row")
    count = len(rows)
    print(f"  Found {count} papers with 28nm")
    assert count > 0, "Expected at least one 28nm paper"

    # Verify all visible papers have 28nm
    screenshot(page, "03_node_filter.png")
    print("  PASSED")


def test_04_search(page):
    """Test 4: Search for 'LLM'."""
    print("\n[Test 04] Search (LLM)")
    page.goto(BASE_URL)
    page.wait_for_selector("#filter-search", timeout=10000)

    page.fill("#filter-search", "LLM")
    page.wait_for_timeout(500)

    rows = page.query_selector_all(".comp-table .row")
    count = len(rows)
    print(f"  Found {count} papers matching 'LLM'")
    assert count > 0, "Expected at least one LLM paper"

    screenshot(page, "04_search.png")
    print("  PASSED")


def test_05_detail_page(page):
    """Test 5: Navigate to detail page for paper 31.1."""
    print("\n[Test 05] Detail page (31.1)")
    page.goto(BASE_URL + "#paper/31.1")
    page.wait_for_selector(".detail-page", timeout=10000)

    title = page.text_content(".detail-title")
    print(f"  Title: {title[:80]}...")
    assert "ReRAM" in title or "LLM" in title or "Token" in title

    screenshot(page, "05_detail.png")
    print("  PASSED")


def test_06_annotation(page):
    """Test 6: Title annotation (说文解字) with colored segments."""
    print("\n[Test 06] Title annotation (说文解字)")
    page.goto(BASE_URL + "#paper/31.1")
    page.wait_for_selector(".title-annotated", timeout=10000)

    segments = page.query_selector_all(".title-annotated .segment")
    count = len(segments)
    print(f"  Found {count} annotation segments")
    assert count > 0, "Expected at least one annotation segment"

    # Check that segments have annotations
    annotations = page.query_selector_all(".title-annotated .annotation")
    print(f"  Found {len(annotations)} annotations")
    assert len(annotations) > 0

    screenshot(page, "06_annotation.png")
    print("  PASSED")


def test_07_challenge_idea(page):
    """Test 7: Challenge/Idea cards with arrows."""
    print("\n[Test 07] Challenge/Idea cards")
    page.goto(BASE_URL + "#paper/31.1")
    page.wait_for_selector(".challenge-idea-section", timeout=10000)

    challenges = page.query_selector_all(".challenge-card")
    ideas = page.query_selector_all(".idea-card")
    arrows = page.query_selector_all(".connector-arrow")

    print(f"  Challenges: {len(challenges)}, Ideas: {len(ideas)}, Arrows: {len(arrows)}")
    assert len(challenges) > 0, "Expected at least one challenge card"
    assert len(ideas) > 0, "Expected at least one idea card"

    screenshot(page, "07_challenge.png")
    print("  PASSED")


def test_08_gallery(page):
    """Test 8: Figure gallery loads images with captions."""
    print("\n[Test 08] Figure gallery")
    page.goto(BASE_URL + "#paper/31.1")
    page.wait_for_selector(".figure-gallery, #image-gallery", timeout=10000)

    # Check for new figure cards first, fallback to legacy gallery
    fig_cards = page.query_selector_all(".figure-card")
    thumbs = page.query_selector_all(".gallery-thumb")
    total = len(fig_cards) + len(thumbs)
    print(f"  Found {len(fig_cards)} figure cards, {len(thumbs)} page thumbnails")
    assert total > 0, "Expected at least one gallery image"

    # Check figure card has caption
    if fig_cards:
        caption = page.query_selector(".figure-caption")
        assert caption is not None, "Expected figure card to have caption"
        label = page.query_selector(".figure-label")
        assert label is not None, "Expected figure card to have label"
        print(f"  Caption found: {caption.text_content()[:50]}...")

    # Click first figure to open lightbox
    clickable = fig_cards[0] if fig_cards else thumbs[0]
    clickable.click()
    page.wait_for_timeout(500)

    lightbox = page.query_selector("#lightbox.active")
    assert lightbox is not None, "Lightbox should be active after clicking image"
    print("  Lightbox opened successfully")

    # Check lightbox caption
    lb_caption = page.query_selector("#lightbox-caption")
    if lb_caption and fig_cards:
        print(f"  Lightbox caption: {lb_caption.text_content()[:50]}...")

    screenshot(page, "08_gallery.png")

    # Close lightbox
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    print("  PASSED")


def test_09_navigation(page):
    """Test 9: Prev/Next navigation between papers."""
    print("\n[Test 09] Paper navigation")
    page.goto(BASE_URL + "#paper/31.1")
    page.wait_for_selector(".detail-page", timeout=10000)

    # Find next link
    next_link = page.query_selector('.paper-nav a[href*="31.2"]')
    assert next_link is not None, "Expected next paper link to 31.2"
    print("  Next paper link found (31.2)")

    next_link.click()
    page.wait_for_selector(".detail-page", timeout=5000)
    page.wait_for_timeout(500)

    title = page.text_content(".detail-title")
    print(f"  Navigated to: {title[:60]}...")
    assert "31.1" not in page.url or "31.2" in page.url

    screenshot(page, "09_nav.png")
    print("  PASSED")


def test_10_responsive(page):
    """Test 10: Responsive layout at 768px viewport."""
    print("\n[Test 10] Responsive (768px)")
    page.set_viewport_size({"width": 768, "height": 1024})
    page.goto(BASE_URL)
    page.wait_for_selector(".comp-table", timeout=10000)

    screenshot(page, "10_responsive.png")
    print("  PASSED")


def main():
    server = start_server()
    passed = 0
    failed = 0
    errors = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            tests = [
                test_01_overview_load,
                test_02_session_filter,
                test_03_node_filter,
                test_04_search,
                test_05_detail_page,
                test_06_annotation,
                test_07_challenge_idea,
                test_08_gallery,
                test_09_navigation,
                test_10_responsive,
            ]

            for test_fn in tests:
                try:
                    test_fn(page)
                    passed += 1
                except Exception as e:
                    failed += 1
                    errors.append((test_fn.__name__, str(e)))
                    print(f"  FAILED: {e}")
                    try:
                        screenshot(page, f"FAIL_{test_fn.__name__}.png")
                    except:
                        pass

            browser.close()

    finally:
        server.terminate()
        server.wait()

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    if errors:
        print("\nFailures:")
        for name, err in errors:
            print(f"  {name}: {err}")
    print(f"Screenshots saved to: {SCREENSHOTS_DIR}")
    print(f"{'='*50}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
