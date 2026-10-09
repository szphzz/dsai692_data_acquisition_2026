from playwright.sync_api import sync_playwright
import time

# p = sync_playwright()

with sync_playwright() as p:
# Step 1. Create a browser
# Can use chromium/firefox/webkit, chromium is free ver of chrome
# head is the graphic user interface, want it enabled during development so browser launches
# can set headless=True once deploying
    browser = p.chromium.launch(headless=False)

# Step 2. Create a new BrowserContext (optional)
# isolated, incognito-like session within a browser instance
    context = browser.new_context()

# Step 3. Open a page
    page = context.new_page()
    page.goto("https://medium.com/tag/artificial-intelligence")
    page.wait_for_selector("article.al")
    # page.wait_for_select("article[class='al']")
    # time.sleep(5)  # to pause for 5 sec

    # list of JSHandles (playwright objects)
    all_articles = page.query_selector_all("article")
    for article in all_articles:
        # print(article.inner_text())
        print(article.get_attribute("aria-label"))

    # article with class al, children with tag a (anchor) accessed after space
    all_article = page.query_selector_all("article.al a")
    for article_a in all_article:
        print(article_a.get_attribute("href"))

    browser.close()  # optional since "with" block will automatically close, but will be asked to explicitly close during quiz

# playwright is not only for scraping but also for user interface testing
# run with "python ex01.py"