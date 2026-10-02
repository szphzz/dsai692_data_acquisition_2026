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
    # TODO : COMPLETE THIS TO RETURN A DICTIONARY
