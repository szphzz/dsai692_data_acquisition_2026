# Complete the function retrieve_ul_children(url) 
# that takes a URL as a string and 
# returns a list of all direct children 
# text (NavigableString) of every <ul> tag.
import requests
from bs4 import BeautifulSoup

def retrieve_ul_children(url):
    html_text = requests.get(url).content
    soup = BeautifulSoup(html_text, "html.parser")
    output = list()
    # soup.select("ul .fruit[id='1']").string
    for li in soup.select("ul .fruit[id='1']"):
        output.append(li.string)
        # print(li.string)
    return output

url = "http://127.0.0.1:5500/2026_MSDS692/dsai692_data_acquisition_2026/StudySession/2026_10_07/bs_html.html"
# print(retrieve_ul_children(url))


def traverse(url):
    html_text = requests.get(url).content
    soup = BeautifulSoup(html_text, "html.parser")
    output = []
    for fruit in soup.select("ul"):
        print(list(fruit.descendants))
        for item in list(fruit.descendants):
            if item != "\n":
                output.append(item)
    return output
print(traverse(url))