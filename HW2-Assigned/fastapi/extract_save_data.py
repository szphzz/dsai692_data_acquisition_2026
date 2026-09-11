from user_definition import *
from pydantic import BaseModel
from google.cloud import storage
from google.oauth2 import service_account
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.protobuf.json_format import MessageToDict

from fastapi.responses import JSONResponse
from fastapi import FastAPI
import json
import datetime
import re

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
    location: str = "global"  # Values: "global", "us", "eu", etc.


class GcsStringUpload(BaseModel):
    service_account_key: str
    gcp_project_id: str
    bucket_name: str
    file_name: str
    data: str


def parse_google_search_results(search_results: dict,
                                job_list: list) -> None:
    """
    Extend job_list to be a list of dictionaries.
    Each dictionary should include title, link, snippet and date.
    title, link, and snippet come from each result's
    "document"->"derivedStructData". date is based on the snippet's
    "xx days ago" -- use the current date and xx days to calculate an
    actual date (if no "xx days ago" pattern is found, use today's date).

    Args:
        search_results (dict): a list of raw search result documents.
        job_list (list): a list of dictionaries with title, link,
                         snippet and date. Extended in place.
    """
    for job in search_results:  # TODO: implement.
        pass


def call_google_search(search_param: GoogleSearch):
    """
    Use Vertex AI Search (Discovery Engine) to search for job postings
    restricted to the sites in search_param.company_dictionary, and
    return them as a plain dict shaped like:
    {"company_dict": ..., "job_title": ..., "results": [...]}.
    On failure, return a JSONResponse with status_code=500 instead.
    """
    # TODO: implement.
    api_endpoint = f"{search_param.location}-discoveryengine.googleapis.com"
    client_options = (
        ClientOptions(api_endpoint=api_endpoint)
        if search_param.location != "global"
        else None
    )
    # Build credentials
    credentials = service_account.Credentials.from_service_account_file(
        search_param.service_account_key)
    # Build a discoveryengine.SearchServiceClient with credentials.
    client = discoveryengine.SearchServiceClient(
        client_options=client_options,
        credentials=credentials)
    # The serving_config path has the form:
    #  projects/{project}/locations/{location}/collections/default_collection
    #  /engines/{engine}/servingConfigs/default_config
    serving_config = (
        f"projects/{search_param.vertex_ai_project_id}/"
        f"locations/{search_param.location}/"
        "collections/default_collection/"
        f"engines/{search_param.search_engine_id}/"
        "servingConfigs/default_config"
    )
    try:
        company_links = search_param.company_dictionary.values()
        # Hint : Restrict the search to specific sites by adding
        # "(site:url1 OR site:url2 OR ...)" to the company_links.
        site_restrict =  # TODO : COMPLETE THIS
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
        # response is a SearchPager backed by protobuf messages and not
        # directly JSON-serializable. 
        # Convert each result to a plain dict before returning it.
        results = [MessageToDict(result._pb) for result in response]
        # TODO : Call parse_google_search_results()
        # on the converted results to build the final "results" list.
        job_list = []
    except Exception as e:
        # TODO : Complete the error message.
        return JSONResponse(
            status_code=,
            content={"message": },
        )


def save_to_gcs(gcs_upload_param: GcsStringUpload):
    """
    Access the bucket with service_account_key, and upload the object
    (blob) to the storage.
    Return a dict with "message" as a key, and add message as a value.
    """
    # TODO: implement.


# TODO : Provide the proper route.
def search_and_save_jobs(search_input: SearchModel):
    """
    Combine call_google_search() and save_to_gcs() to search for jobs and
    save the results as a JSON blob in GCS, at
    f'{file_name_prefix}/{today's date}.json'.
    """
    # TODO: implement.
    # file_name stored in GCS should be'{file_name_prefix}/{datetime.date.today()}.json'
    pass
