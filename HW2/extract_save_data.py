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
    today = datetime.date.today()

    for job in search_results:
        result = job["document"]["derivedStructData"]
        snippet = result["snippets"][0]["snippet"]

        match = re.search(r"(\d+)\s*days?\s*ago", snippet)
        if match:
            date = today - datetime.timedelta(days=int(match.group(1)))
        else:
            date = today

        output = {"title": result.get("title", ""),
                  "link": result.get("link", ""),
                  "snippet": snippet,
                  "date": date.isoformat()}
        job_list.append(output)


def call_google_search(search_param: GoogleSearch):
    """
    Use Vertex AI Search (Discovery Engine) to search for job postings
    restricted to the sites in search_param.company_dictionary, and
    return them as a plain dict shaped like:
    {"company_dict": ..., "job_title": ..., "results": [...]}.
    On failure, return a JSONResponse with status_code=500 instead.
    """
    api_endpoint = f"{search_param.location}-discoveryengine.googleapis.com"
    client_options = (
        ClientOptions(api_endpoint=api_endpoint)
        if search_param.location != "global"
        else None
    )
    credentials = service_account.Credentials.from_service_account_file(
        search_param.service_account_key)
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
        company_links = search_param.company_dictionary.values()
        sites = " OR ".join(f"site:{re.sub(r'^https?://', '', link)}"
                            for link in company_links)  # keep consistent
        site_restrict = f"({sites})"
        SpellCorrectionSpec = discoveryengine.SearchRequest.SpellCorrectionSpec
        spell_correction_spec = SpellCorrectionSpec(
            mode=SpellCorrectionSpec.Mode.AUTO
        )
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=f"{search_param.job_title} {site_restrict}",
            page_size=10,  # increased from 1 to 10
            spell_correction_spec=spell_correction_spec,
        )
        response = client.search(request)
        # response is a SearchPager backed by protobuf messages and not
        # directly JSON-serializable.
        # Convert each result to a plain dict before returning it.
        results = [MessageToDict(result._pb) for result in response]
        job_list = []
        parse_google_search_results(results, job_list)
        return {"company_dict": search_param.company_dictionary,
                "job_title": search_param.job_title,
                "results": job_list}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Vertex AI Search failed: {e}"},
        )


def save_to_gcs(gcs_upload_param: GcsStringUpload):
    """
    Access the bucket with service_account_key, and upload the object
    (blob) to the storage.
    Return a dict with "message" as a key, and add message as a value.
    """
    credentials = service_account.Credentials.from_service_account_file(
        gcs_upload_param.service_account_key)
    client = storage.Client(project=gcs_upload_param.gcp_project_id,
                            credentials=credentials)
    bucket = client.bucket(gcs_upload_param.bucket_name)
    blob = bucket.blob(gcs_upload_param.file_name)
    blob.upload_from_string(gcs_upload_param.data)
    return {"message": f"{gcs_upload_param.file_name} is saved"}


@app.post("/search_and_save/jobs")
def search_and_save_jobs(search_input: SearchModel):
    """
    Combine call_google_search() and save_to_gcs() to search for jobs and
    save the results as a JSON blob in GCS, at
    f'{file_name_prefix}/{today's date}.json'.
    """
    search_param = GoogleSearch(
        vertex_ai_project_id=vertex_ai_project_id,
        search_engine_id=search_engine_id,
        job_title=search_input.job_title,
        company_dictionary=search_input.company_dict,
        service_account_key=service_account_file_path
    )
    result = call_google_search(search_param)
    if isinstance(result, JSONResponse):  # hint
        return result

    file_name = f"{file_name_prefix}/{datetime.date.today()}.json"
    gcs_upload_param = GcsStringUpload(
        service_account_key=service_account_file_path,
        gcp_project_id=project_id,
        bucket_name=bucket_name,
        file_name=file_name,
        data=json.dumps(result)
    )
    return save_to_gcs(gcs_upload_param)
