import json
import re

import pandas as pd
import streamlit as st

from google.cloud import storage

from user_definition import GCP_BUCKET_NAME, GCP_FILE_NAME


def retrieve_data_from_gcs(bucket_name: str,
                           file_name: str
                           ) -> dict:
    """
    TODO: Retrieve file, called `file_name` from `bucket_name`
        and returns a dictionary including "results",
        "job_title", and "company_dict"

        Args:
            bucket_name (str) : bucket name
            file_name (str) : file_name to retrieve data.

        Returns:
            retrieves file in dictionary format

    Hint :
    The `file_name` is a public file, which does not require
    authentification and you can create an anonymous client via
    storage.Client.create_anonymous_client()
    """
    client = storage.Client.create_anonymous_client()
    bucket = client.bucket(bucket_name)
    file = bucket.blob(file_name)
    data = file.download_as_bytes()
    return json.loads(data)


def summarize_distribution(df: pd.DataFrame,
                           column_name: str,
                           top_n: int = 10) -> dict:
    """
    TODO:
    df[column_name] has a list per row (e.g. skills per job).
    Explode using pandas .explode() from a list into individual items first,
    then count how many rows each item appears in across the whole column.
    Return the top_n most frequent items.
    Ex. [['a','b','c'], ['a','d']], top_n=2 -> {'a': 2, 'b': 1}
    """
    df_exploded = df.explode(column_name)
    top_n_dict = df_exploded[column_name].value_counts()[:top_n].to_dict()
    return top_n_dict


if __name__ == '__main__':
    results = retrieve_data_from_gcs(GCP_BUCKET_NAME,
                                     GCP_FILE_NAME)

    company_dictionary = results["company_dict"]
    job_title = results["job_title"]
    data = pd.DataFrame(results["results"])

    st.title(f'{job_title} Listings and Skills')

    sorted_companies = sorted(company_dictionary)

    selected_companies = []
    with st.sidebar:
        st.write("Filter by Company")
        for company in sorted_companies:
            if st.checkbox(company, value=True):
                selected_companies.append(company)

    # Regex pattern built with help from Anthropic Claude Opus 5
    # (via Claude Code): asked how to filter a pandas string column for
    # rows containing any value from a list, case insensitively.
    # -> escape each value and join them with "|" to form an OR pattern.
    if selected_companies:  # not an empty list, something has been selected
        pattern = "|".join(re.escape(company)
                           for company in selected_companies)
        matches_company = data["link"].str.contains(pattern,
                                                    case=False,
                                                    regex=True,
                                                    na=False)  # boolean mask
    else:
        # No company checked -> keep nothing, rather than everything.
        matches_company = pd.Series(False, index=data.index)

    # separate df for each step to be safe
    selected_df = data[matches_company][["date", "title", "skills", "link"]]
    unique_df = selected_df.drop_duplicates(subset="link")
    filtered_df = unique_df.sort_values(by=["date", "title"],
                                        ascending=[False, True])

    st.dataframe(filtered_df,  # create this dataframe by conditions.
                 hide_index=True,
                 column_config={
                     "link": st.column_config.LinkColumn()})

    skill_counts = pd.DataFrame.from_dict(
        summarize_distribution(filtered_df, "skills"),
        orient='index')
    st.bar_chart(skill_counts)
