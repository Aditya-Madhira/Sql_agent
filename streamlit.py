# streamlit_app.py

import streamlit as st
import requests
import json
import time
from datetime import datetime

# Define the base URL for the FastAPI backend
BASE_URL = "http://localhost:8000"

# Page configuration with dark theme
st.set_page_config(
    page_title="HR Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme UI
st.markdown("""
<style>
    /* Dark theme base colors */
    :root {
        --background-color: #121212;
        --card-bg-color: #1e1e1e;
        --primary-color: #7C4DFF;
        --secondary-color: #03DAC6;
        --text-color: #E0E0E0;
        --muted-color: #9E9E9E;
        --user-message-bg: #2D3748;
        --user-message-border: #4A5568;
        --bot-message-bg: #1A365D;
        --bot-message-border: #2C5282;
        --highlight-color: #7C4DFF;
    }

    /* Override Streamlit's theme */
    .reportview-container {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 7rem;
        max-width: 800px;
    }

    /* Chat message containers */
    .chat-message {
        display: flex;
        margin-bottom: 1.5rem;
        align-items: flex-start;
        border-radius: 1rem;
        padding: 1.2rem;
        position: relative;
        animation: fadeIn 0.3s ease-in-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .chat-message.user {
        background-color: var(--user-message-bg);
        border-left: 4px solid var(--user-message-border);
        margin-left: 30px;
        margin-right: 80px;
    }

    .chat-message.assistant {
        background-color: var(--bot-message-bg);
        border-left: 4px solid var(--bot-message-border);
        margin-right: 30px;
        margin-left: 80px;
    }

    /* Avatar styling */
    .chat-message .avatar {
        width: 48px;
        min-width: 48px;
        margin-right: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .chat-message .avatar img {
        max-width: 100%;
        max-height: 100%;
        border-radius: 50%;
        object-fit: cover;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        border: 2px solid var(--highlight-color);
    }

    /* Message content */
    .chat-message .message {
        flex-grow: 1;
        word-break: break-word;
        overflow-wrap: break-word;
        line-height: 1.6;
    }

    /* Timestamp styling */
    .timestamp {
        position: absolute;
        bottom: 8px;
        right: 12px;
        font-size: 0.7rem;
        color: var(--muted-color);
        font-style: italic;
    }

    /* Input area styling */
    .chat-input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        padding: 1rem 1.5rem;
        background-color: rgba(18, 18, 18, 0.9);
        backdrop-filter: blur(10px);
        border-top: 1px solid #333;
        z-index: 100;
        display: flex;
        flex-direction: column;
    }

    .stTextInput > div > div {
        background-color: #2D3748;
        border-radius: 25px;
        border: 1px solid #4A5568;
        padding-left: 15px;
        color: white;
    }

    .stTextInput > div > div:focus-within {
        border-color: var(--highlight-color);
    }

    /* Header & Title */
    .main-title {
        text-align: center;
        color: var(--highlight-color);
        font-size: 2.5rem;
        font-weight: 600;
        margin: 1rem 0 2rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--secondary-color);
    }

    .header-subtitle {
        text-align: center;
        color: var(--muted-color);
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Reasoning steps */
    .expander-header {
        color: var(--highlight-color);
        font-weight: 600;
    }

    .steps-expander {
        background-color: #1A1A1A;
        border-radius: 0.5rem;
        border: 1px solid #333;
        padding: 1rem;
        margin-top: 0.5rem;
    }

    .steps-expander h4 {
        color: var(--secondary-color);
        border-bottom: 1px solid #333;
        padding-bottom: 0.5rem;
    }

    /* Initial greeting message */
    .greeting-container {
        text-align: center;
        padding: 3rem 1rem;
        background-color: rgba(30, 30, 30, 0.7);
        border-radius: 1rem;
        margin: 2rem 0;
        border: 1px solid #333;
    }

    .greeting-container h3 {
        color: var(--highlight-color);
        margin-bottom: 1rem;
    }

    .greeting-container p {
        color: var(--text-color);
        font-size: 1.1rem;
        line-height: 1.6;
    }

    /* Remove padding from spinner */
    div.stSpinner > div {
        text-align: center;
        color: var(--highlight-color);
        padding-top: 0;
    }

    /* Sidebar styling */
    .css-1d391kg, .css-163ttbj, .css-1fcdlhc {
        background-color: #1A1A1A;
    }

    /* Make sure other Streamlit elements match the theme */
    button, .stButton>button {
        background-color: var(--highlight-color);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }

    button:hover, .stButton>button:hover {
        background-color: #9161FF;
        box-shadow: 0 0 10px rgba(124, 77, 255, 0.5);
    }

    /* JSON styling */
    pre {
        background-color: #2D3748;
        border-radius: 5px;
        padding: 0.75rem;
        border-left: 3px solid var(--secondary-color);
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #1e1e1e;
    }

    ::-webkit-scrollbar-thumb {
        background: #424242;
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize conversation ID
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")


# Function to display a chat message
def display_message(role, content, timestamp=None):
    if role == "user":
        avatar_url = "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix&backgroundColor=b6e3f4"
        bg_class = "user"
    else:
        avatar_url = "https://api.dicebear.com/7.x/bottts/svg?seed=Dusty&backgroundColor=7C4DFF"
        bg_class = "assistant"

    timestamp_str = f'<div class="timestamp">{timestamp}</div>' if timestamp else ""

    st.markdown(f"""
    <div class="chat-message {bg_class}">
        <div class="avatar">
            <img src="{avatar_url}">
        </div>
        <div class="message">
            {content}
            {timestamp_str}
        </div>
    </div>
    """, unsafe_allow_html=True)


# Main title and header
st.markdown("<h1 class='main-title'>Employee Database Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p class='header-subtitle'>Ask questions about employees, departments, salaries, and more</p>",
            unsafe_allow_html=True)

# Chat container to hold messages
chat_container = st.container()

# Display initial greeting if no messages
if not st.session_state.messages:
    with chat_container:
        st.markdown("""
        <div class="greeting-container">
            <h3>👋 Welcome to the Employee Database Assistant</h3>
            <p>
                I can help you find information about employees, departments, salaries, and more.
                Try asking me questions like:
                <ul>
                    <li>Who works in the Engineering department?</li>
                    <li>What's the average salary by department?</li>
                    <li>How many years of service does Jane Smith have?</li>
                    <li>Who is the highest paid employee?</li>
                </ul>
            </p>
        </div>
        """, unsafe_allow_html=True)

# Display previous messages
with chat_container:
    for message in st.session_state.messages:
        display_message(message["role"], message["content"], message.get("timestamp"))

# Chat input area at bottom
with st.container():
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)

    placeholder = "Ask about employees, departments, salaries, or positions..."
    query = st.text_input("", placeholder=placeholder, key="chat_input", label_visibility="collapsed")

    # Help text
    st.markdown("""
    <div style="font-size: 0.8rem; color: var(--muted-color); margin-top: 0.5rem;">
    Type a question and press Enter to send
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# Process the query when submitted
if query:
    # Add timestamp to the message
    current_time = datetime.now().strftime("%H:%M:%S")

    # Add user message to chat history
    st.session_state.messages.append({
        "role": "user",
        "content": query,
        "timestamp": current_time
    })

    # Display the user message (this will be appended to the existing messages)
    display_message("user", query, current_time)

    # Placeholder for bot response while waiting
    with chat_container:
        with st.spinner("Thinking..."):
            try:
                # Append conversation ID to help with context tracking
                params = {
                    "query": query,
                    "conversation_id": st.session_state.conversation_id
                }

                # Send request to backend
                response = requests.get(f"{BASE_URL}/query", params=params)

                if response.status_code == 200:
                    result = response.json()
                    assistant_response = result["response"]

                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response,
                        "timestamp": current_time,
                        "steps": result.get("steps", [])  # Store steps for debugging
                    })

                    # Display assistant response
                    display_message("assistant", assistant_response, current_time)

                    # Show reasoning steps in an expander
                    if "steps" in result and result["steps"]:
                        with st.expander("🔍 View Reasoning Process", expanded=False):
                            st.markdown('<div class="steps-expander">', unsafe_allow_html=True)

                            for i, step in enumerate(result["steps"]):
                                st.markdown(f"<h4>Step {i + 1}: {step['tool']}</h4>", unsafe_allow_html=True)
                                st.markdown(f"**Input**: `{step['input']}`")
                                st.markdown("**Result**:")

                                # Format SQL results better
                                if isinstance(step['output'], str) and step['tool'] == 'sql_db_query':
                                    try:
                                        if step['output'].strip().startswith('[') or step['output'].strip().startswith(
                                                '{'):
                                            data = json.loads(step['output'])
                                            st.json(data)
                                        else:
                                            st.text(step['output'])
                                    except:
                                        st.text(step['output'])
                                else:
                                    st.text(step['output'])

                                if i < len(result["steps"]) - 1:
                                    st.markdown("<hr style='margin: 1.5rem 0; border-color: #333;'>",
                                                unsafe_allow_html=True)

                            st.markdown("</div>", unsafe_allow_html=True)

                else:
                    st.error(f"Error from backend: {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Automatically scroll to the bottom
    st.markdown(
        """
        <script>
            document.getElementsByClassName('main')[0].scrollTo(0, document.getElementsByClassName('main')[0].scrollHeight);
        </script>
        """,
        unsafe_allow_html=True
    )

# Sidebar options
with st.sidebar:
    st.markdown("<h3 style='color: #7C4DFF;'>Options</h3>", unsafe_allow_html=True)

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")
        st.rerun()

    st.markdown("---")
    st.markdown("<h4 style='color: #03DAC6;'>About</h4>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='color: #E0E0E0; font-size: 0.9rem;'>
        This assistant uses AI to query an employee database using natural language.
        </div>
        """,
        unsafe_allow_html=True
    )