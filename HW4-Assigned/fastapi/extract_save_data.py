import asyncio
import json
import datetime
import re

from fastapi import FastAPI, HTTPException

from google.cloud import storage
from google.oauth2 import service_account
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.protobuf.json_format import MessageToDict

from pydantic import BaseModel

from qualification_parser import retreive_qualification
from gemini_summarizer import return_gemini_summaries

from user_definition import *
from anthropic_search import retrieve_anthropic_jobs

app = FastAPI()


class SearchModel(BaseModel):
    # Query parameters for '/search_and_save/jobs'
    job_title: str
    no_days_to_search: int = 1
    company_dict: dict


class GoogleSearch(BaseModel):
    vertex_ai_project_id: str
    search_engine_id: str
    job_title: str
    company_dictionary: dict
    service_account_key: str
    location: str = "global"  # Values: "global", "us", "eu"


class GcsStringUpload(BaseModel):
    service_account_key: str
    gcp_project_id: str
    bucket_name: str
    file_name: str
    data: str


def add_qualification(results: list) -> None:
    """
    Extend each result in `results` (in place) with "qualification" and
    "skills" keys, scraped/summarized from that result's job posting link.
    All the qualifications are summarized by Gemini.
    """
    for result in results:
        info = result["document"]["derivedStructData"]
        link = info["link"]
        result["qualification"] = retreive_qualification(link)

    skills = return_gemini_summaries([result["qualification"]
                                      for result in results])
    for result, result_skills in zip(results, skills):
        result["skills"] = result_skills


def parse_google_search_results(search_results: dict,
                                job_list: list) -> None:
    """
    Extend job_list to be a list of dictionaries with title, link,
    snippet, date and skills. (Same as HW3.)
    """
    for job in search_results:
        info = job["document"]["derivedStructData"]
        title = info["title"]
        link = info["link"]
        snippet = info["snippets"][0]["snippet"]
        day_diff_match = re.search(r"(\d+)\s*days?\s*ago", snippet.lower())
        day_diff = int(day_diff_match.group(1)) if day_diff_match else 0
        date = datetime.date.today() - datetime.timedelta(days=day_diff)
        job_list.append({"title": title,
                         "link": link,
                         "snippet": snippet,
                         "date": date.strftime('%Y-%m-%d'),
                         "skills": job.get("skills")})


def call_google_search(search_param: GoogleSearch):
    """
    Use Vertex AI Search to search for job postings restricted to the
    sites in search_param.company_dictionary, scrape and summarize each
    result's qualifications, and return {"company_dict", "job_title",
    "results"} or HTTPException.
    (Same as HW3.)
    """
    api_endpoint = f"{search_param.location}-discoveryengine.googleapis.com"
    client_options = (
        ClientOptions(api_endpoint=api_endpoint)
        if search_param.location != "global"
        else None
    )

    credentials = service_account.Credentials.from_service_account_file(
        search_param.service_account_key
    )
    client = discoveryengine.SearchServiceClient(
        client_options=client_options,
        credentials=credentials)

    serving_config = (
        f"projects/{search_param.vertex_ai_project_id}/"
        f"locations/{search_param.location}/"
        "collections/default_collection/"
        f"engines/{search_param.search_engine_id}/"
        "servingConfigs/default_config"
    )
    try:
        # Restrict results to the sites in company_dictionary using
        # (site:url1 OR site:url2 OR ...) search-operator syntax.
        company_links = search_param.company_dictionary.values()
        site_list = [f"site:{link} " for link in company_links]
        site_list_str = " OR ".join(site_list)
        site_restrict = f"({site_list_str})"
        SpellCorrectionSpec = discoveryengine.SearchRequest.SpellCorrectionSpec
        spell_correction_spec = SpellCorrectionSpec(
            mode=SpellCorrectionSpec.Mode.AUTO
        )
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=f"{search_param.job_title} {site_restrict}",
            page_size=1,
            spell_correction_spec=spell_correction_spec,
        )
        response = client.search(request)
        # response is a SearchPager backed by protobuf messages.
        # It's not JSON-serializable, so convert each to a plain dict.
        results = [MessageToDict(result._pb) for result in response]
        add_qualification(results)
        job_list = []
        parse_google_search_results(results, job_list)
        return {"company_dict": search_param.company_dictionary,
                "job_title": search_param.job_title,
                "results": job_list}
    except Exception as e:
        print(f"Error making API request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error making API request: {e}"
        )


def save_to_gcs(gcs_upload_param: GcsStringUpload):
    """
    Access the bucket with service_account_key, and upload the object
    (blob) to the storage. Returns a dict with a status message.
    (Same as HW3.)
    """
    credentials = service_account.Credentials.\
        from_service_account_file(gcs_upload_param.service_account_key)
    client = storage.Client(project=gcs_upload_param.gcp_project_id,
                            credentials=credentials)
    bucket = client.bucket(gcs_upload_param.bucket_name)
    file = bucket.blob(gcs_upload_param.file_name)
    file.upload_from_string(gcs_upload_param.data)
    return {"message": f"file {gcs_upload_param.file_name} has been uploaded "
            f"to {gcs_upload_param.bucket_name} successfully."}


@app.post("/search_and_save/jobs")
def search_and_save_jobs(search_input: SearchModel):
    """
    Combine Anthropic's dynamic (Playwright) scrape and a Vertex AI
    Search-based static search into one saved result set.

    Anthropic needs to be special-cased and routed to
    `retrieve_anthropic_jobs()` instead of `call_google_search()` - see
    anthropic_search.py's docstring for why.
    Other companies in company_dict should go through the VertexAI Search.

    TODO:
    1. Split search_input.company_dict into two groups: the "Anthropic"
       entry (if present) and everything else.
    2. For Anthropic, the code should go to the corresponding value of
       `company_dictionary`, and search roles by typing `role_name`
       using Playwright.
       Extract the information including title, and URL,
       and call qualification_parser to get qualification.
       (optional) To improve performance you can try the asynchronous version.
    3. Build up a single search_response dict incrementally: start it
       empty, add Anthropic results first (if any), then call
       call_google_search() for the remaining companies.
    5. Save the combined search_response to GCS the same way HW3 did.
    """
    pass
