import requests

from bs4 import BeautifulSoup

QUALIFICATION_KEYWORDS = ["team", "role", "responsibilities", "qualifications",
                          "skills", "you will", "thrive", "looking for",
                          "background", "responsible", "nice to have",
                          "good fit", "may also have", "technologies"]


def retreive_qualification(url: str) -> dict:
    """
    TODO:
    For the given URL, this function finds unordered lists (<ul>),
    where the preceding element is either a header (ex. <h2>, <h3>) or a
    paragraph <p> with <b> or <strong> font.
    In addition, the header string (h2, h3 and p) should 
    include one of QUALIFICATION_KEYWORDS in its lower case string.
    This will create a dictionary of {header_string1: [list_of_qualification],
    header_string2: [list_of_qualification], ...}.

    Example output:
    {'In this role, you will:': ['Currently enrolled in or graduated from
    a degree program within Product Management, Computer Science,
    Engineering, Data Science, Mathematics, Statistics, or a related
    technical field, or equivalent practical experience.', ...],
    'You might thrive in this role if you:': ['Experience with
    methodologies aimed to drive product development and delivery.', ...]}
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        # Add a header to avoid 403 errors - some pages block requests without a browser-like User-Agent.
    }

    response = requests.get(url, headers=headers)
    html_text = response.text
    soup = BeautifulSoup(html_text, "html.parser")

    output = {}
    for ul in soup.select("ul"):
        prev = ul.find_previous_sibling()  # to skip whitespace

        if prev is None:
            continue

        if prev.name in ["h2", "h3"]:
            heading = prev.text.strip()
        elif prev.name == "p":
            bold_parts = prev.find_all(["strong", "b"])
            if not bold_parts:
                continue
            heading = "".join(part.text for part in bold_parts).strip()
        else:
            continue

        if not any(keyword in heading.lower() for keyword in QUALIFICATION_KEYWORDS):
            continue

        quals = [li.text.strip() for li in ul.select("li")]
        if not quals:
            continue
        output[heading] = quals
    
    return output
