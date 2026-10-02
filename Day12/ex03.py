from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    # Launching a Browser
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.allrecipes.com/")

    # Waiting for Elements
    page.wait_for_selector(".feed")  # Wait Until the <feed> appears
    page.locator('.feed [data-ordinal="3"]').click()
    time.sleep(3)

    # Wheel to go 150 pxl, 1000 pxl
    page.mouse.wheel(150, 1000)
    time.sleep(3)
