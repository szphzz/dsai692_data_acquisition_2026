from collections import defaultdict
import json

import asyncio

from playwright.async_api import async_playwright, Playwright
from playwright_stealth import Stealth


async def retrieve_content(playwright: Playwright, website_url: str) -> dict:
    """
    Goto nytimes.com/books/best-sellers/
    and retrieve Date, Genre, Book Name, Author, Applebook URL as a dictionary,
    with Genre as keys.
    """


async def retrieve_applebook_price(url) -> float or None:
    """
    Retrieve the price of book_type from applebooks
    A valid url should include a applebooks
    """


async def main():
    async with async_playwright() as playwright:
        h2_li_data = await retrieve_content(playwright,
                                            "https://www.nytimes.com/books/best-sellers/")

    for key, value in h2_li_data.items():
        if key != "Date":
            for item in value:
                url = item["applebook_url"]
                applebook_ebook_price = await retrieve_applebook_price(url)
                item["applebook_ebook_price"] = applebook_ebook_price

    with open("output.json", "w") as f:
        json.dump(h2_li_data, f, indent=4)


data = asyncio.run(main())
