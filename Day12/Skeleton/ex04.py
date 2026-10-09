from playwright.sync_api import sync_playwright
import time


with sync_playwright() as p:
    # Launching a Browser
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://reddit.com")

    # Click the login button and enter id and password.
    page.locator("#login-button").click()
    page.locator("input[name='username']").fill("spchung@dons.usfca.edu")
    page.locator("#login-username").click()
    page.keyboard.insert_text("student@usfca.edu")
    page.keyboard.press("Tab")
    time.sleep(3)
    page.keyboard.press("Tab")
    page.keyboard.insert_text("p@ssW0rld")
