import datetime

from playwright.sync_api import sync_playwright

from qualification_parser import retreive_qualification
from gemini_summarizer import return_gemini_summaries


def retrieve_anthropic_jobs(url: str, role: str) -> list:
    """
    Anthropic's careers page is a client-rendered React app: the job list
    isn't in the initial HTML response at all (unlike Google/OpenAI, which
    are server-rendered), and typing into its search box filters the list
    live via JavaScript with no page navigation. requests+BeautifulSoup
    can't see any of that - this is why HW4 needs a real browser
    (Playwright) instead of the requests/BeautifulSoup approach from HW3.

    TODO:
    Returns a list of {"title", "link", "date"} dicts for jobs matching
    `role`, each further annotated with "qualification" and "skills" the
    same way HW3's add_qualification() does for the Google Search path.
    Note: "date" could be added via datetime.date.today().strftime("%Y-%m-%d")
    """
    if not url.startswith("https://"):
        url = "https://" + url

    output = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context()
        page = context.new_page()
        page.goto(url)

        page.wait_for_selector("main")
        page.get_by_placeholder("Search roles").fill(role)

        page.wait_for_selector("a[class*='jobItem']")
        page.wait_for_timeout(2000)

        today = datetime.date.today().strftime("%Y-%m-%d")
        job_links = page.locator("a[class*='jobItem']").all()
        for job in job_links:
            href = job.get_attribute("href")
            output.append({
                "title": job.inner_text(),
                "link": href,
                "date": today,
                "qualification": retreive_qualification(href)
            })

        skills = return_gemini_summaries([job["qualification"] for job in output])
        for job, job_skills in zip(output, skills):
            job["skills"] = job_skills

        browser.close()

    return output