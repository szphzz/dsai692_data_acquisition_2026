from dotenv import load_dotenv
import os

import streamlit as st
from google import genai

from user_definition import *
from job_posting import retrieve_data_from_gcs

load_dotenv()

st.set_page_config(page_title="Chatbot")
st.title("Job Assistant Chatbot")
model_name = "gemini-3.5-flash"
# This is for maintaining the chat history
if "chat" not in st.session_state:
    gcs_data = retrieve_data_from_gcs(service_account_key=service_account_file_path,
                                      project_id=project_id,
                                      bucket_name=bucket_name,
                                      file_name_prefix=file_name_prefix)
    system_message = f"""
    Assume that you are a helpful job search assistant. 
    You have access to the following job postings data:
    {gcs_data}. 
    Based on this information, help the user with their job search related questions.
    """
    st.session_state.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    st.session_state.chat = st.session_state.client.chats.create(model=model_name,
                                                                 config={"system_instruction": system_message})                                               
chat = st.session_state.chat


if "messages" not in st.session_state:
    st.session_state.messages = []


# Display existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


prompt = st.chat_input("Ask me something...")
if prompt:
    # Save user message
    st.session_state.messages.append({"role": "user",
                                      "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""

        # Streaming from API
        response = chat.send_message_stream(prompt)

    for chunk in response:
        response_text += chunk.text
        placeholder.markdown(response_text)

    # Save assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": response_text})
