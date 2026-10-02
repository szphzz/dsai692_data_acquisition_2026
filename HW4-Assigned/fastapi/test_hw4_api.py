import asyncio
import datetime
import inspect
import subprocess

import pytest
import requests

import qualification_parser
from qualification_parser import retreive_qualification
from anthropic_search import retrieve_anthropic_jobs
from gemini_summarizer import return_gemini_summaries


OPENAI_URL = "https://openai.com/careers/software-engineer-research-human-data-san-francisco/"
GOOGLE_URL = "https://www.google.com/about/careers/applications/jobs/results/75076499224306374-data-engineer-data-architecture-and-engineering-gtech-strategy-and-operations"
ANTHROPIC_URL = "https://www.anthropic.com/careers/jobs"
ROLE = "data engineer"
JOB_KEYS = {"title", "link", "date", "qualification", "skills"}


# ---------------------------------------------------------------------
# qualification_parser -- live tests.
# ---------------------------------------------------------------------
@pytest.fixture
def live_fetch(monkeypatch):
    """
    Return a function that runs retreive_qualification() against a live
    URL and skips the test if the site blocked the request.
    """
    real_get = qualification_parser.requests.get
    statuses = []

    def recording_get(url, **kwargs):
        response = real_get(url, **kwargs)
        statuses.append(response.status_code)
        return response

    monkeypatch.setattr(qualification_parser.requests, "get", recording_get)

    def _fetch(url):
        statuses.clear()
        try:
            result = retreive_qualification(url)
        except requests.RequestException as exc:
            pytest.skip(f"{url} is unreachable: {exc}")
        blocked = [status for status in statuses if status != 200]
        if blocked:
            pytest.skip(f"{url} returned {blocked[0]} -- the site is "
                        f"blocking scripted requests right now. Not a code "
                        f"issue; try again later or from another network.")
        return result

    return _fetch


def test_retreive_qualification_openai(live_fetch):
    result = live_fetch(OPENAI_URL)
    assert isinstance(result, dict)
    assert len(result) > 0
    for heading, bullets in result.items():
        assert isinstance(heading, str) and heading
        assert isinstance(bullets, list) and len(bullets) > 0
        assert all(isinstance(b, str) and b for b in bullets)


def test_retreive_qualification_google(live_fetch):
    result = live_fetch(GOOGLE_URL)
    assert isinstance(result, dict)
    assert len(result) > 0
    for heading, bullets in result.items():
        assert isinstance(heading, str) and heading
        assert isinstance(bullets, list) and len(bullets) > 0


def test_retreive_qualification_unrelated_page_returns_empty(live_fetch):
    """
    A page with no qualifications-shaped <ul> should return an empty
    dict, not raise.
    """
    # live_fetch skips on a challenge page, so a green result here always
    # means the parser really did read the page and find nothing --
    # rather than passing because it was handed a 403 body.
    result = live_fetch("https://openai.com/careers/")
    assert result == {}


# ---------------------------------------------------------------------
# qualification_parser -- offline parsing tests.
# ---------------------------------------------------------------------
class FakeResponse:
    """The bare minimum of requests.Response that the parser reads."""

    def __init__(self, text):
        self.text = text
        self.status_code = 200


@pytest.fixture
def parse_html(monkeypatch):
    """
    Return a function that runs retreive_qualification() against a fixed
    HTML string instead of a live page, by swapping out requests.get.
    """
    def _parse(html):
        def fake_get(url, headers=None, **kwargs):
            # The User-Agent header is what keeps real career pages from
            # answering with a 403, so check it survived the refactor.
            assert headers and "User-Agent" in headers, (
                "retreive_qualification() must send a browser-like "
                "User-Agent header -- some career pages 403 without one.")
            return FakeResponse(html)

        monkeypatch.setattr(qualification_parser.requests, "get", fake_get)
        return retreive_qualification("https://example.com/jobs/1")

    return _parse


def normalized(result):
    """Strip whitespace so these tests check the rules, not get_text()."""
    return {heading.strip(): [bullet.strip() for bullet in bullets]
            for heading, bullets in result.items()}


def test_retreive_qualification_collects_heading_and_bullets(parse_html):
    """A real heading tag whose text contains a keyword is the dict key,
    and its following <ul>'s <li>s are the value."""
    result = parse_html(
        "<h3>Minimum qualifications:</h3>"
        "<ul><li>Python</li><li>SQL</li></ul>")
    assert normalized(result) == {
        "Minimum qualifications:": ["Python", "SQL"]}


def test_retreive_qualification_uses_bold_text_of_paragraph_heading(
        parse_html):
    """
    Some pages use <p><strong>...</strong></p> instead of a real
    heading tag. The bold child's text becomes the key.
    """
    result = parse_html(
        "<p><strong>Responsibilities</strong></p>"
        "<ul><li>Build data pipelines</li></ul>")
    assert normalized(result) == {
        "Responsibilities": ["Build data pipelines"]}


def test_retreive_qualification_skips_paragraph_without_bold(parse_html):
    """
    A plain <p> that happens to sit above a <ul> is body copy, not a
    heading.
    """
    result = parse_html(
        "<p>You will love our team</p>"
        "<ul><li>Free lunch</li></ul>")
    assert result == {}


def test_retreive_qualification_skips_list_with_no_items(parse_html):
    """
    An empty <ul> under a perfectly good heading contributes
    nothing.
    """
    result = parse_html("<h3>Qualifications</h3><ul></ul>")
    assert result == {}


def test_retreive_qualification_skips_heading_without_keyword(parse_html):
    """
    Nav menus and footers are <ul>s too.
    """
    result = parse_html(
        "<h3>Office locations</h3>"
        "<ul><li>San Francisco</li><li>New York</li></ul>")
    assert result == {}


def test_retreive_qualification_keyword_match_is_case_insensitive(
        parse_html):
    result = parse_html(
        "<h2>MINIMUM QUALIFICATIONS</h2><ul><li>Python</li></ul>")
    assert list(normalized(result)) == ["MINIMUM QUALIFICATIONS"]


def test_retreive_qualification_collects_every_matching_section(parse_html):
    """
    A posting usually has several qualification sections, and the
    unrelated lists around them must not be added.
    """
    result = parse_html(
        "<ul><li>Careers</li><li>About</li></ul>"
        "<h3>Minimum qualifications</h3>"
        "<ul><li>Python</li></ul>"
        "<h3>Preferred qualifications</h3>"
        "<ul><li>Kubernetes</li><li>Terraform</li></ul>"
        "<h3>Our offices</h3>"
        "<ul><li>San Francisco</li></ul>")
    assert normalized(result) == {
        "Minimum qualifications": ["Python"],
        "Preferred qualifications": ["Kubernetes", "Terraform"],
    }


def test_retreive_qualification_returns_empty_dict_not_none(parse_html):
    """
    Nothing found is an empty dict.
    """
    result = parse_html("<html><body><p>No lists here.</p></body></html>")
    assert result == {}


# ---------------------------------------------------------------------
# anthropic_search -- live Playwright tests.
# ---------------------------------------------------------------------
async def _resolve(awaitable):
    return await awaitable


def call_retrieve_anthropic_jobs(url: str, role: str) -> list:
    """
    Call retrieve_anthropic_jobs() without caring whether it was written
    as a plain function or as a coroutine function.
    """
    jobs = retrieve_anthropic_jobs(url, role)
    if inspect.isawaitable(jobs):
        jobs = asyncio.run(_resolve(jobs))
    return jobs


@pytest.fixture(scope="module")
def anthropic_jobs():
    """
    Scrape once and share the result across every test in this module.
    """
    return call_retrieve_anthropic_jobs(ANTHROPIC_URL, ROLE)


def test_retrieve_anthropic_jobs_accepts_url_and_role():
    """
    Both the sync and the async implementation must take (url, role)
    positionally.
    """
    assert callable(retrieve_anthropic_jobs)
    inspect.signature(retrieve_anthropic_jobs).bind(ANTHROPIC_URL, ROLE)


def test_retrieve_anthropic_jobs(anthropic_jobs):
    """
    The scrape returns real postings shaped like the search results.
    """
    assert isinstance(anthropic_jobs, list)
    assert len(anthropic_jobs) > 0
    today = datetime.date.today().strftime("%Y-%m-%d")
    for job in anthropic_jobs:
        assert set(job.keys()) >= JOB_KEYS
        assert isinstance(job["title"], str) and job["title"]
        assert job["link"].startswith("https://")
        assert "greenhouse.io/anthropic" in job["link"]
        assert job["date"] == today


def test_retrieve_anthropic_jobs_matches_role(anthropic_jobs):
    """
    Typing into the search box filters the list client-side.
    """
    titles = [job["title"].lower() for job in anthropic_jobs]
    assert any("engineer" in title for title in titles), titles


def test_retrieve_anthropic_jobs_qualifications_parsed(anthropic_jobs):
    """
    Each posting must be run through qualification_parser.
    """
    for job in anthropic_jobs:
        qualification = job["qualification"]
        assert isinstance(qualification, dict)
        for heading, bullets in qualification.items():
            assert isinstance(heading, str) and heading
            assert isinstance(bullets, list) and len(bullets) > 0
            assert all(isinstance(b, str) and b for b in bullets)

    assert any(job["qualification"] for job in anthropic_jobs)


def test_retrieve_anthropic_jobs_skills_summarized(anthropic_jobs):
    """
    Every posting's qualifications must be summarized into skills.
    """
    for job in anthropic_jobs:
        skills = job["skills"]
        assert skills is None or isinstance(skills, list)
        if skills:
            assert all(isinstance(skill, str) and skill for skill in skills)

    if all(job["skills"] is None for job in anthropic_jobs):
        pytest.skip("No skills came back -- the Gemini Batch API needs a "
                    "billing-enabled key, and a free-tier key has no batch "
                    "quota. Not a code issue.")
    assert any(job["skills"] for job in anthropic_jobs)


def test_retrieve_anthropic_jobs_summarizes_in_one_batch(monkeypatch):
    """
    The summarizer must be called once.
    """
    import anthropic_search

    calls = []

    def fake_qualification(url):
        return {"Minimum Qualifications": [f"Experience with Python ({url})"]}

    def fake_summaries(qualifications):
        calls.append(list(qualifications))
        return [["Python"] for _ in qualifications]

    monkeypatch.setattr(anthropic_search, "retreive_qualification",
                        fake_qualification)
    monkeypatch.setattr(anthropic_search, "return_gemini_summaries",
                        fake_summaries)

    jobs = call_retrieve_anthropic_jobs(ANTHROPIC_URL, ROLE)

    assert len(jobs) > 0
    assert len(calls) == 1, (f"return_gemini_summaries() was called "
                             f"{len(calls)} times -- call it once, after "
                             f"the loop, with every qualification.")
    assert len(calls[0]) == len(jobs)
    assert all(job["skills"] == ["Python"] for job in jobs)


def test_retrieve_anthropic_jobs_adds_scheme():
    """
    company_dict values are stored without a scheme elsewhere in the app.
    """
    jobs = call_retrieve_anthropic_jobs(
        "www.anthropic.com/careers/jobs",
        "zzz-role-that-does-not-exist-zzz")
    assert jobs == []


# ---------------------------------------------------------------------
# gemini_summarizer -- the batch contract both callers rely on.
# ---------------------------------------------------------------------
def test_return_gemini_summaries_keeps_input_order():
    """
    retrieve_anthropic_jobs() zips the summaries back onto the jobs by
    position.
    """
    qualifications = [
        {"Minimum Qualifications": [
            "5+ years of experience with Python and SQL",
            "Experience with Apache Spark and distributed data processing",
        ]},
        {"Minimum Qualifications": [
            "Deep experience with Kubernetes and Terraform",
        ]},
    ]
    summaries = return_gemini_summaries(qualifications)

    assert isinstance(summaries, list)
    assert len(summaries) == len(qualifications)
    if all(summary is None for summary in summaries):
        pytest.skip("return_gemini_summaries returned all None -- the "
                    "Gemini Batch API needs a billing-enabled key, and a "
                    "free-tier key has no batch quota. Not a code issue.")
    assert all(summary is None or isinstance(summary, list)
               for summary in summaries)
    if summaries[0]:
        assert any("python" in skill.lower() for skill in summaries[0])
    if summaries[1]:
        assert any("kubernetes" in skill.lower() for skill in summaries[1])


def test_return_gemini_summaries_empty_input():
    """
    No postings found means no batch job to submit.
    """
    assert return_gemini_summaries([]) == []


# ---------------------------------------------------------------------
# PEP8 checks on the files you wrote.
# ---------------------------------------------------------------------
def test_qualification_parser_pep8():
    result = subprocess.run(
        ["pycodestyle", "qualification_parser.py"],
        capture_output=True,
        text=True,
    )
    errors = result.stdout.strip().splitlines()
    assert len(errors) < 5, f"Too many PEP8 issues:\n{errors}"


def test_anthropic_search_pep8():
    result = subprocess.run(
        ["pycodestyle", "anthropic_search.py"],
        capture_output=True,
        text=True,
    )
    errors = result.stdout.strip().splitlines()
    assert len(errors) < 5, f"Too many PEP8 issues:\n{errors}"
