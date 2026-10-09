from dotenv import load_dotenv
import os

import streamlit as st
from google import genai

load_dotenv()
model_name = "gemini-3.5-flash"
if "chat" not in st.session_state:
    st.session_state.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    st.session_state.chat = st.session_state.client.chats.create(model=model_name)
chat = st.session_state.chat

if "messages" not in st.session_state:
    st.session_state.messages = []

st.set_page_config(page_title="Chatbot")
st.title("Interactive Chatbot with Google GenAI")
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
