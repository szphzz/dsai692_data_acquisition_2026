from dotenv import load_dotenv
import os

import streamlit as st
import google.generativeai as genai

load_dotenv()
model_name = "gemini-3.5-flash"
if "chat" not in st.session_state:
    st.session_state.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    st.session_state.chat = st.session_state.client.chats.create(model="gemini-3.5-flash")
chat = st.session_state.chat

if "messages" not in st.session_state:
    st.session_state.messages = []

st.set_page_config(page_title="Chatbot")
st.title("Interactive Chatbot with Google GenAI")

# Display existing messages

# Save user message
