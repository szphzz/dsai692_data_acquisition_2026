import json
import re

from google.oauth2 import service_account
from google.cloud import storage
import streamlit as st
import pandas as pd

from user_definition import (bucket_name, file_name_prefix, project_id,
                             service_account_file_path)


def retrieve_data_from_gcs(service_account_key: str,
                           project_id: str,
                           bucket_name: str,
                           file_name_prefix: str
                           ) -> dict:
    credentials = service_account.Credentials.from_service_account_file(
        service_account_key)
    client = storage.Client(project=project_id,
                            credentials=credentials)
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=file_name_prefix)

    content = []
    job_titles = set()  # changed from list to set for unique
    company_dict = dict()

    for blob in blobs:
        if not blob.name.endswith(".json"):
            continue
        data = json.loads(blob.download_as_text())
        content.extend(data.get("results", []))  # iterable version of append
        job_titles.add(data.get("job_title", ""))
        company_dict.update(data.get("company_dict", {}))

    return {"results": content,
            "job_titles": sorted(job_titles),
            "company_dict": company_dict}


if __name__ == '__main__':
    gcs_data = retrieve_data_from_gcs(service_account_file_path,
                                      project_id,
                                      bucket_name,
                                      file_name_prefix)
    role_name = ", ".join(gcs_data["job_titles"])
    company_dictionary = gcs_data["company_dict"]
    data = pd.DataFrame(gcs_data["results"])

    st.title(f"{role_name} Job Listings")
    with st.sidebar:
        st.write("Filter by Company")
        unique_categories = list(company_dictionary.keys())
        unique_categories.sort()
        selected_categories = []

        for category in unique_categories:
            if st.checkbox(f"{category}",
                           value=True,
                           key=f"checkbox_{category}"):
                selected_categories.append(category.lower())

        pattern = "|".join(re.escape(category)
                           for category in selected_categories)
        if pattern:
            filtered_df = data[data["link"].str.contains(pattern)]
        else:
            filtered_df = data.iloc[0:0]
        print(filtered_df)
        filtered_df = filtered_df[["date", "title", "link"]]
        filtered_df = filtered_df.drop_duplicates(subset=["link"])
        filtered_df = filtered_df.sort_values(
            by=["date", "title"], ascending=[False, True])

    st.dataframe(filtered_df,
                 hide_index=True,
                 column_config={
                     "link": st.column_config.LinkColumn()})
