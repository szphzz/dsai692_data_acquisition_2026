import json
import time

from google import genai
from google.genai import types

from user_definition import gemini_key

MODEL_NAME = "models/gemini-3.5-flash-lite"

SYSTEM_INSTRUCTION = """
From the given dictionary formatted string,
summarize technical skills in the values as a noun.
For example,
{"Minimum Qualification":
["7 years of experience leading technical project strategy,
ML design, and optimizing ML infrastructure
(e.g., model deployment, model evaluation, data processing,
debugging, fine tuning).",
"5 years of experience with one or more of the following:
Speech/audio (e.g., technology duplicating and responding
to the human voice), reinforcement learning
(e.g., sequential decision making),...,
ML infrastructure, or specialization in another ML field."]}
should become
["Python", "Machine Learning Engineering", "MLOps", "MLFlow",
"Generative AI", "Langchain", "Pinecone", "Machine Learning",
"Reinforcement Learning"]
"""

# Batch jobs are queued and run asynchronously
# Poll until the job reaches one of the following states.
DONE_STATES = {
    "JOB_STATE_SUCCEEDED",
    "JOB_STATE_PARTIALLY_SUCCEEDED",
    "JOB_STATE_FAILED",
    "JOB_STATE_CANCELLED",
    "JOB_STATE_EXPIRED",
}
POLL_SECONDS = 10
MAX_WAIT_SECONDS = 15 * 60


def parse_skills(response) -> list:
    """
    Pull the JSON array of skills out of a batch response,
    or return None.
    """
    try:
        return json.loads(response.response.text)
    except Exception as e:
        print(f"Gemini summary failed, skipping skill summary for this job: "
              f"{response.error or e}")
        return None


def return_gemini_summaries(qualifications: list) -> list:
    """
    Summarize many qualification dictionaries (each one the output of
    retreive_qualification()) in a single Gemini batch job, using a
    system instruction that asks for a list of concrete technical
    skills.

    Returns one list of skills per input qualification, e.g.
    [["Python", "SQL"], ["Machine Learning"]], in the same order as
    `qualifications`. An entry is None (rather than raising) if that
    request failed, so one job's failure doesn't take down the batch.
    """
    if not qualifications:
        return []

    client = genai.Client(api_key=gemini_key)
    # response_schema makes Gemini return a bare JSON array of strings,
    # so the response never has to be stripped of ```json fences.
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=list[str],
    )
    try:
        job = client.batches.create(
            model=MODEL_NAME,
            src=[types.InlinedRequest(contents=str(qualification),
                                      config=config)
                 for qualification in qualifications],
        )

        waited = 0
        while job.state.name not in DONE_STATES:
            if waited >= MAX_WAIT_SECONDS:
                print(f"Gemini batch {job.name} is still {job.state.name}"
                      f" after {waited}s -- skipping these jobs' skills.")
                return [None] * len(qualifications)
            time.sleep(POLL_SECONDS)
            waited += POLL_SECONDS
            job = client.batches.get(name=job.name)
    except Exception as e:
        # The Batch API needs a billing-enabled key -- a free-tier key
        # gets 429 RESOURCE_EXHAUSTED from batches.create(). Drop the
        # skills rather than failing the whole search request.
        print(f"Gemini batch failed, skipping skills for these jobs: {e}")
        return [None] * len(qualifications)

    responses = (job.dest.inlined_responses if job.dest else None) or []
    if len(responses) != len(qualifications):
        print(f"Gemini batch {job.name} ended as {job.state.name} with "
              f"{len(responses)} of {len(qualifications)} responses.")

    summaries = [parse_skills(response) for response in responses]
    # Pad so the result always lines up with the input list.
    return summaries + [None] * (len(qualifications) - len(summaries))


def return_gemini_summary(qualification: dict) -> list:
    """
    Summarize a single qualification dictionary -- a one-item batch.
    """
    return return_gemini_summaries([qualification])[0]
